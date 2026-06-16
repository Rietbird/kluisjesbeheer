#!/bin/bash
# enable-git-update.sh
# Zet een tar/handmatig-gedeployede kluisjesbeheer-install om naar een
# git-checkout, zodat de update-knop (Beheer -> Onderhoud) werkt.
#
# BRANDING-VEILIG: de database (*.db), backend/uploads/ (logo) en
# backend/config.json blijven staan -- die zijn .gitignored/untracked en
# worden door 'git checkout -f' niet aangeraakt. Er wordt sowieso eerst een
# backup gemaakt.
#
# Gebruik (als root):
#   curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/install/enable-git-update.sh -o /tmp/eg.sh
#   sudo bash /tmp/eg.sh                 # detecteert zelf de install-map
#   sudo bash /tmp/eg.sh /pad/naar/app   # of geef de map expliciet mee
set -euo pipefail

REPO_URL="https://github.com/Rietbird/kluisjesbeheer.git"
BRANCH="master"

[[ $EUID -eq 0 ]] || { echo "FOUT: draai als root (sudo bash ...)."; exit 1; }

# --- 1) Install-map bepalen (argument, anders auto-detect via backend/app.py) ---
APP_DIR="${1:-}"
if [[ -z "$APP_DIR" ]]; then
  hit="$(find /opt /root /srv /home /var/www -maxdepth 4 -type f -path '*/backend/app.py' 2>/dev/null | head -1 || true)"
  [[ -n "$hit" ]] && APP_DIR="$(dirname "$(dirname "$hit")")"
fi
[[ -n "${APP_DIR:-}" && -f "$APP_DIR/backend/app.py" ]] || {
  echo "FOUT: kon de install-map niet vinden. Geef 'm mee: sudo bash $0 /root/kluisjesbeheer"; exit 1; }
echo ">> Install-map: $APP_DIR"

# --- 2) Benodigdheden ---
command -v git >/dev/null || { echo "FOUT: git ontbreekt (apt install git)."; exit 1; }
command -v npm >/dev/null || { echo "FOUT: Node.js/npm ontbreekt. Updates bouwen de frontend op de server, dus Node 18+ is nodig."; exit 1; }

# --- 3) Service / app-user / venv detecteren ---
SERVICE="$(grep -rls "$APP_DIR" /etc/systemd/system/ 2>/dev/null | grep -i kluis | head -1 | xargs -r basename || true)"
[[ -n "${SERVICE:-}" ]] || SERVICE="kluisjesbeheer"
APP_USER="$(systemctl show -p User --value "$SERVICE" 2>/dev/null || true)"
[[ -n "${APP_USER:-}" ]] || APP_USER="$(stat -c '%U' "$APP_DIR")"
if   [[ -x "$APP_DIR/.venv/bin/pip" ]]; then VENV="$APP_DIR/.venv"
elif [[ -x "$APP_DIR/venv/bin/pip"  ]]; then VENV="$APP_DIR/venv"
else echo "FOUT: geen Python-venv (.venv of venv) in $APP_DIR"; exit 1; fi
echo ">> SERVICE=$SERVICE  APP_USER=$APP_USER  VENV=$VENV"

# --- 4) Database vinden (data/ heeft voorrang, dan legacy) ---
DB=""
for cand in "$APP_DIR/backend/data/kluisjesbeheer.db" "$APP_DIR/backend/kluisjesbeheer.db"; do
  [[ -f "$cand" ]] && DB="$cand" && break
done
echo ">> Database: ${DB:-(geen gevonden -- verse install?)}"

# --- 5) Backup (DB + logo + config) ---
TS="$(date +%Y%m%d-%H%M%S)"; BK="/root/kluisjes-pre-gitconvert-$TS"; mkdir -p "$BK"
[[ -n "$DB" ]]                              && cp -a "$DB" "$BK/"
[[ -d "$APP_DIR/backend/uploads" ]]         && cp -a "$APP_DIR/backend/uploads" "$BK/uploads"
[[ -f "$APP_DIR/backend/config.json" ]]     && cp -a "$APP_DIR/backend/config.json" "$BK/"
echo ">> Backup in $BK:"; ls -la "$BK"

# --- 6) Omzetten naar git-checkout (forceert code naar origin/$BRANCH) ---
GIT="git -c safe.directory=$APP_DIR -C $APP_DIR"
if [[ ! -d "$APP_DIR/.git" ]]; then
  $GIT init -q
  $GIT remote add origin "$REPO_URL" 2>/dev/null || $GIT remote set-url origin "$REPO_URL"
fi
$GIT fetch -q origin "$BRANCH"
$GIT checkout -f -B "$BRANCH" "origin/$BRANCH"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# --- 7) Root-helper voor de update-knop (detecteert DB net als hierboven) ---
cat > /usr/local/sbin/kluisjes-update <<HELPER
#!/bin/bash
set -euo pipefail
APP_DIR="$APP_DIR"
APP_USER="$APP_USER"
BRANCH="$BRANCH"
GIT="git -c safe.directory=\$APP_DIR -C \$APP_DIR"
if [[ ! -d "\$APP_DIR/.git" ]]; then echo "ERROR: \$APP_DIR is geen git-checkout" >&2; exit 1; fi
DB=""
for cand in "\$APP_DIR/backend/data/kluisjesbeheer.db" "\$APP_DIR/backend/kluisjesbeheer.db"; do
  [[ -f "\$cand" ]] && DB="\$cand" && break
done
if [[ -n "\$DB" ]]; then
    BACKUP_DIR="\$(dirname "\$DB")/backups"
    install -d -o "\$APP_USER" -g "\$APP_USER" "\$BACKUP_DIR"
    TS=\$(date +%Y%m%d-%H%M%S)
    sqlite3 "\$DB" ".backup '\$BACKUP_DIR/pre-update-\$TS.db'" 2>/dev/null || cp -a "\$DB" "\$BACKUP_DIR/pre-update-\$TS.db"
fi
OLD=\$(\$GIT rev-parse --short HEAD)
\$GIT pull --ff-only origin "\$BRANCH"
NEW=\$(\$GIT rev-parse --short HEAD)
CHANGED=\$(\$GIT diff --name-only "\$OLD" "\$NEW" || true)
if grep -q 'backend/requirements.txt' <<<"\$CHANGED"; then "$VENV/bin/pip" install -q -r "\$APP_DIR/backend/requirements.txt"; fi
if grep -qE '^frontend/' <<<"\$CHANGED"; then ( cd "\$APP_DIR/frontend" && npm ci --silent && npm run build ); fi
chown -R "\$APP_USER:\$APP_USER" "\$APP_DIR"
echo "OK: \$OLD -> \$NEW (herstart volgt)"
nohup bash -c 'sleep 2; systemctl restart $SERVICE' >/dev/null 2>&1 &
exit 0
HELPER
chmod 0755 /usr/local/sbin/kluisjes-update

# --- 8) sudoers: app-user mag de helper als root draaien (zonder wachtwoord) ---
echo "$APP_USER ALL=(root) NOPASSWD: /usr/local/sbin/kluisjes-update" > /etc/sudoers.d/kluisjes-update
chmod 0440 /etc/sudoers.d/kluisjes-update
visudo -cf /etc/sudoers.d/kluisjes-update

# --- 9) Frontend bouwen + service herstarten ---
( cd "$APP_DIR/frontend" && npm ci --silent && npm run build )
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
systemctl restart "$SERVICE"

# --- 10) Verificatie ---
sleep 3
echo "== HEAD:    $($GIT rev-parse --short HEAD)"
echo "== service: $(systemctl is-active "$SERVICE")"
echo ">> Klaar. De update-knop in Beheer -> Onderhoud werkt nu (branding-veilig)."
echo ">> Backup van DB/logo/config staat in: $BK"
