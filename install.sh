#!/bin/bash
# Kluisjesbeheer installatiescript
# Voor verse Debian 12 of 13 server (LXC of VM).
# Idempotent: opnieuw draaien is veilig.
#
# Gebruik:
#   sudo bash install.sh
#
# Vereist: dit script + de aangeleverde tarball uitgepakt in dezelfde map
# (backend/ en frontend/ moeten naast dit script staan).

set -euo pipefail

# ============================================================
# Configuratie
# ============================================================
APP_DIR="/opt/kluisjesbeheer"
APP_USER="kluisjes"
VENV_DIR="$APP_DIR/.venv"
SERVICE_NAME="kluisjesbeheer"
CRON_LOG="/var/log/kluisjes-sync.log"
APP_PORT="5000"

# ============================================================
# Helpers
# ============================================================
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

step()   { echo -e "\n${GREEN}==>${NC} $*"; }
info()   { echo -e "    $*"; }
warn()   { echo -e "${YELLOW}!!  $*${NC}"; }
err()    { echo -e "${RED}xx  $*${NC}" >&2; }

require_root() {
    if [[ $EUID -ne 0 ]]; then
        err "Draai als root: sudo bash install.sh"
        exit 1
    fi
}

# ============================================================
# Pre-flight checks
# ============================================================
preflight() {
    step "Pre-flight checks"

    # Debian-versie
    if [[ ! -f /etc/debian_version ]]; then
        err "Dit script vereist Debian. Gevonden: niet-Debian systeem."
        exit 1
    fi
    local deb_ver
    deb_ver=$(cut -d. -f1 /etc/debian_version)
    if [[ "$deb_ver" != "12" && "$deb_ver" != "13" ]]; then
        warn "Debian $deb_ver gedetecteerd; getest op 12 en 13."
        read -rp "    Toch doorgaan? [j/N] " ans
        [[ "$ans" =~ ^[jJyY]$ ]] || exit 1
    else
        info "Debian $deb_ver OK"
    fi

    # Bundle aanwezig
    local here
    here=$(cd "$(dirname "$0")" && pwd)
    if [[ ! -d "$here/backend" || ! -d "$here/frontend" ]]; then
        err "backend/ en frontend/ niet gevonden naast install.sh."
        err "Pak eerst de bundel uit en draai het script vanuit die map."
        exit 1
    fi
    info "Bundle gevonden in $here"
    BUNDLE_DIR="$here"

    # Internet (apt + npm + pip). curl is hier nog niet per se geïnstalleerd
    # op een verse Debian-base — we doen alleen een check als het bestaat.
    if command -v curl >/dev/null 2>&1; then
        if ! curl -sf -m 5 -o /dev/null https://deb.debian.org/; then
            warn "Geen verbinding met deb.debian.org — apt installs kunnen falen."
        fi
    else
        info "curl nog niet aanwezig — wordt zo via apt geïnstalleerd"
    fi
}

# ============================================================
# Systeem-packages
# ============================================================
install_packages() {
    step "Systeem-packages installeren"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq \
        python3 python3-venv python3-pip \
        nodejs npm \
        curl ca-certificates rsync sudo \
        cron sqlite3
    info "Pakketten OK"
}

# ============================================================
# App-user
# ============================================================
create_user() {
    step "App-gebruiker $APP_USER"
    if id "$APP_USER" &>/dev/null; then
        info "Gebruiker bestaat al"
    else
        useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
        info "Aangemaakt"
    fi
}

# ============================================================
# Code uitrollen (idempotent — overschrijft alleen code, geen DB/config)
# ============================================================
deploy_code() {
    step "Code uitrollen naar $APP_DIR"

    mkdir -p "$APP_DIR"

    # Backend: alle .py + tests + requirements
    rsync -a --delete \
        --exclude='__pycache__' \
        --exclude='*.db' \
        --exclude='*.db-journal' \
        --exclude='config.json' \
        --exclude='backups/' \
        --exclude='.venv/' \
        --exclude='venv/' \
        "$BUNDLE_DIR/backend/" "$APP_DIR/backend/"

    # Frontend: bronbestanden (wordt zo gebuild)
    rsync -a --delete \
        --exclude='node_modules' \
        --exclude='dist' \
        "$BUNDLE_DIR/frontend/" "$APP_DIR/frontend/"

    # CRLF -> LF op alle text-files (voor het geval bundel van Windows komt)
    find "$APP_DIR" -type f \( \
        -name '*.py' -o -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' \
        -o -name '*.css' -o -name '*.html' -o -name '*.json' -o -name '*.md' \
        -o -name '*.sh' -o -name '*.sql' -o -name '*.txt' -o -name '*.cfg' \
        -o -name '*.toml' -o -name '*.yml' -o -name '*.yaml' \
        \) -exec sed -i 's/\r$//' {} +

    info "Code OK"
}

# ============================================================
# Python venv + dependencies
# ============================================================
setup_python() {
    step "Python-omgeving"
    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
        info "venv aangemaakt"
    else
        info "venv bestaat"
    fi
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"
    "$VENV_DIR/bin/pip" install --quiet gunicorn
    info "Python-dependencies OK"
}

# ============================================================
# Frontend build
# ============================================================
build_frontend() {
    step "Frontend bouwen (Vite)"
    cd "$APP_DIR/frontend"
    npm ci --silent --no-audit --no-fund
    npm run build --silent
    cd - >/dev/null
    info "dist/ klaar in $APP_DIR/frontend/dist"
}

# ============================================================
# config.json — alleen aanmaken als hij nog niet bestaat
# ============================================================
ensure_config() {
    step "Configuratiebestand"
    local cfg="$APP_DIR/backend/config.json"
    if [[ -f "$cfg" ]]; then
        info "config.json bestaat al — laten staan"
        return
    fi

    # Genereer een random SecretKey (64 hex chars). Cruciaal voor Fernet-encryptie.
    local secret
    secret=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')

    cat > "$cfg" <<EOF
{
  "TenantId": "VUL_IN_TENANT_ID",
  "ClientId": "VUL_IN_CLIENT_ID",
  "ClientSecret": "VUL_IN_CLIENT_SECRET",
  "DashboardGroupId": "VUL_IN_ENTRA_GROUP_ID",
  "RedirectUri": "VUL_IN_REDIRECT_URI",
  "SecretKey": "$secret",
  "SchoolNaam": "Mijn School",
  "SchoolSubtitel": "",
  "SchoolLogo": "/img/logo.png",
  "SchoolKleur": "#FF8200",
  "AllowedOrigins": []
}
EOF
    chmod 600 "$cfg"
    info "Nieuwe config.json aangemaakt met willekeurige SecretKey"
    warn "Vul de VUL_IN_*-velden zo nog in (Entra-credentials + RedirectUri)."
}

# ============================================================
# Permissies
# ============================================================
set_permissions() {
    step "Permissies zetten"
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    # config.json strikt: alleen kluisjes mag het lezen (bevat SecretKey)
    chmod 600 "$APP_DIR/backend/config.json"
    info "Eigenaar = $APP_USER; config.json = 600"
}

# ============================================================
# systemd-service
# ============================================================
install_service() {
    step "systemd-service installeren"
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Kluisjesbeheer Web Application
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/backend
ExecStart=$VENV_DIR/bin/gunicorn --bind 0.0.0.0:$APP_PORT --workers 2 "app:create_app()"
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" >/dev/null
    info "Service ingeschakeld (start automatisch bij boot)"
}

# ============================================================
# Cron-job voor dagelijkse leerling-sync
# ============================================================
install_cron() {
    step "Cron-job voor dagelijkse leerling-sync"

    # Logbestand met juiste rechten (anders blijft het wereld-leesbaar als cron het zelf maakt)
    touch "$CRON_LOG"
    chown root:root "$CRON_LOG"
    chmod 640 "$CRON_LOG"

    # Idempotente cron-installatie via /etc/cron.d
    cat > "/etc/cron.d/kluisjesbeheer-sync" <<EOF
# Dagelijkse Magister leerling-sync voor kluisjesbeheer
# Beheerd door install.sh — niet handmatig bewerken.
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 6 * * * $APP_USER $VENV_DIR/bin/python $APP_DIR/backend/cron_sync.py >> $CRON_LOG 2>&1
EOF
    chmod 644 "/etc/cron.d/kluisjesbeheer-sync"
    info "Cron-job 06:00 → $CRON_LOG (rechten 640)"
}

# ============================================================
# Service (her)starten
# ============================================================
start_service() {
    step "Service starten"
    systemctl restart "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        info "Service draait"
    else
        err "Service start niet — check: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

# ============================================================
# Smoketest
# ============================================================
smoketest() {
    step "Smoketest"
    local code
    code=$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$APP_PORT/" || true)
    if [[ "$code" =~ ^(200|302)$ ]]; then
        info "HTTP $code op poort $APP_PORT — OK"
    else
        warn "HTTP $code op poort $APP_PORT — controleer config.json en logs"
    fi
}

# ============================================================
# Eindrapport
# ============================================================
final_report() {
    local ip
    ip=$(curl -sS -m 5 https://ifconfig.me 2>/dev/null || echo "(kon niet bepalen)")
    # Note: bash heredoc does not interpret \e escape sequences, so we echo
    # the colored header separately and then the plain body.
    echo ""
    echo "================================================================"
    echo -e "${GREEN}Kluisjesbeheer installatie afgerond${NC}"
    echo "================================================================"
    cat <<EOF

Service:        systemctl status $SERVICE_NAME
App-logs:       journalctl -u $SERVICE_NAME -f
Cron-logs:      tail -f $CRON_LOG
Database:       $APP_DIR/backend/kluisjesbeheer.db
Config:         $APP_DIR/backend/config.json
Backups:        $APP_DIR/backend/backups/

App draait op:  http://0.0.0.0:$APP_PORT
Server uitgaand IP (voor SWP-whitelist):
                $ip

================================================================
Volgende stappen (handmatig):

  1. Bewerk $APP_DIR/backend/config.json:
     - TenantId, ClientId, ClientSecret, DashboardGroupId (Entra)
     - RedirectUri (productie-URL incl. /auth/callback)
     - AllowedOrigins (intern frontend-adres)
     - SchoolNaam / SchoolSubtitel / SchoolLogo / SchoolKleur
     LET OP: SecretKey is al automatisch ingevuld — NIET wijzigen na
     gebruik (versleutelt Magister-wachtwoord in DB).

  2. systemctl restart $SERVICE_NAME

  3. Open de app in de browser → log in met je beheerderaccount.
     Eerste login = automatisch beheerder.

  4. Vul Magister-koppeling in via Beheer → Import:
     URL (https://<jouwschool>.swp.nl:8800/doc), account, wachtwoord.
     Wordt versleuteld in de database opgeslagen.

  5. Vraag bij de Magister-/SWP-beheerder een IP-whitelist aan voor
     bovenstaand uitgaand IP-adres op poort 8800.

  6. Test de leerling-sync:
     sudo -u $APP_USER $VENV_DIR/bin/python $APP_DIR/backend/cron_sync.py
================================================================
EOF
}

# ============================================================
# Main
# ============================================================
main() {
    require_root
    preflight
    install_packages
    create_user
    deploy_code
    setup_python
    build_frontend
    ensure_config
    set_permissions
    install_service
    install_cron
    start_service
    smoketest
    final_report
}

main "$@"
