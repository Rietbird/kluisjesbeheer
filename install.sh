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

# Voer een commando uit met een draaiende spinner op stderr; output van het
# commando wordt opgeslagen in een tmp-file en alleen getoond bij een fout.
# Gebruik: run_with_spinner "label" some-command --args
run_with_spinner() {
    local label="$1"; shift
    local log
    log=$(mktemp)
    # Spinner-subshell
    (
        local i=0
        local frames='|/-\'
        while :; do
            printf "\r    %s [%s] " "$label" "${frames:i++%${#frames}:1}" >&2
            sleep 0.15
        done
    ) &
    local spin_pid=$!
    # disown om "Terminated"-melding te onderdrukken bij kill
    disown "$spin_pid" 2>/dev/null || true

    # Werkelijk commando — exit-code vasthouden
    local rc=0
    "$@" >"$log" 2>&1 || rc=$?

    # Spinner stoppen en regel opschonen — extra spaties om "[X] " (4 chars)
    # van de laatste spinner-frame te overschrijven.
    kill "$spin_pid" 2>/dev/null || true
    wait "$spin_pid" 2>/dev/null || true
    printf "\r    %s     " "$label" >&2
    printf "\r    %s " "$label" >&2

    if [[ $rc -eq 0 ]]; then
        printf "${GREEN}OK${NC}\n" >&2
        rm -f "$log"
    else
        printf "${RED}FOUT (exit %d)${NC}\n" "$rc" >&2
        echo "    --- output van mislukt commando: ---" >&2
        sed 's/^/    /' "$log" >&2
        rm -f "$log"
        return "$rc"
    fi
}

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
    # Check tegen een echte pad (de root van deb.debian.org/ geeft 404,
    # gebruik /debian/dists/ die altijd 200 geeft).
    if command -v curl >/dev/null 2>&1; then
        if ! curl -sf -m 5 -o /dev/null https://deb.debian.org/debian/dists/; then
            warn "Geen verbinding met deb.debian.org — apt installs kunnen falen."
        fi
    else
        info "curl nog niet aanwezig — wordt zo via apt geïnstalleerd"
    fi

    # Locale-check: install_packages() lost dit zelf op door en_US.UTF-8 te
    # genereren. We melden alleen dát het gaat gebeuren, niet hoe (anders
    # leest de gebruiker een fix-recept dat hij niet hoeft uit te voeren).
    if ! locale 2>/dev/null | grep -q '^LANG=.*UTF-8'; then
        info "Locale nog niet ingesteld -- wordt zo automatisch gegenereerd (en_US.UTF-8)"
    fi
}

# ============================================================
# Systeem-packages
# ============================================================
install_packages() {
    step "Systeem-packages installeren"
    export DEBIAN_FRONTEND=noninteractive
    run_with_spinner "apt-get update" \
        apt-get update -qq

    # Locale fixen vóór andere installs — anders schermt perl onze
    # output vol met "Setting locale failed"-warnings tijdens elke
    # apt-aanroep.
    if ! locale 2>/dev/null | grep -q '^LANG=.*UTF-8'; then
        run_with_spinner "locale (en_US.UTF-8) genereren" bash -c "
            apt-get install -y -qq locales >/dev/null 2>&1
            sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
            locale-gen >/dev/null 2>&1
            update-locale LANG=en_US.UTF-8
        "
        export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
    fi

    run_with_spinner "apt-get install (python, node, nginx, ...)" \
        apt-get install -y -qq \
            python3 python3-venv python3-pip \
            nodejs npm \
            curl ca-certificates rsync sudo \
            cron sqlite3 \
            nginx
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
        run_with_spinner "venv aanmaken" \
            python3 -m venv "$VENV_DIR"
    else
        info "venv bestaat al"
    fi
    run_with_spinner "pip upgraden" \
        "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    run_with_spinner "pip install (Flask, MSAL, cryptography, ...)" \
        "$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"
    run_with_spinner "pip install gunicorn" \
        "$VENV_DIR/bin/pip" install --quiet gunicorn
}

# ============================================================
# Frontend build
# ============================================================
build_frontend() {
    step "Frontend bouwen (Vite)"
    # Als frontend/dist al bestaat én frontend/src ontbreekt, is dit een
    # deploy-tarball zonder bron — niet bouwen, gewoon hergebruiken.
    if [[ -d "$APP_DIR/frontend/dist" && ! -d "$APP_DIR/frontend/src" ]]; then
        info "dist/ aanwezig zonder src/ — frontend al gebouwd, sla npm build over"
        return
    fi
    cd "$APP_DIR/frontend"
    run_with_spinner "npm ci (dependencies downloaden)" \
        npm ci --silent --no-audit --no-fund
    run_with_spinner "npm run build (Vite-build)" \
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

    # umask 077 vóór de heredoc voorkomt race: file wordt direct 600 gecreëerd
    # i.p.v. eerst 644 en daarna chmod (klein, maar er kan in dat venster een
    # andere user de file openen).
    (
        umask 077
        cat > "$cfg" <<EOF
{
  "TenantId": "VUL_IN_TENANT_ID",
  "ClientId": "VUL_IN_CLIENT_ID",
  "ClientSecret": "VUL_IN_CLIENT_SECRET",
  "RedirectUri": "VUL_IN_REDIRECT_URI",
  "SecretKey": "$secret",
  "SchoolNaam": "Mijn School",
  "SchoolSubtitel": "",
  "SchoolLogo": "/img/logo.png",
  "SchoolKleur": "#FF8200",
  "AllowedOrigins": []
}
EOF
    )
    chmod 600 "$cfg"   # defensief — umask zou 'm al op 600 gezet hebben
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
ExecStart=$VENV_DIR/bin/gunicorn --bind 127.0.0.1:$APP_PORT --workers 2 "app:create_app()"
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
# Self-signed TLS-cert genereren (idempotent)
# ============================================================
ensure_tls_cert() {
    local cert_dir="/etc/nginx/ssl"
    local cert="$cert_dir/self.crt"
    local key="$cert_dir/self.key"
    mkdir -p "$cert_dir"

    if [[ -f "$cert" && -f "$key" ]]; then
        info "TLS-cert bestaat al ($cert)"
        return
    fi

    # umask 077 voorkomt race: zonder umask creëert openssl de key tijdelijk
    # met 644 (world-readable) tussen creatie en de chmod hieronder. Met
    # umask 077 is de file vanaf moment 0 600.
    run_with_spinner "self-signed TLS-cert genereren (10 jaar)" \
        bash -c "umask 077 && openssl req -x509 -nodes -newkey rsa:2048 \
            -days 3650 \
            -subj '/CN=kluisjesbeheer.local' \
            -keyout '$key' -out '$cert'"
    chmod 644 "$cert"   # public cert mag wel readable zijn
    chmod 600 "$key"    # private key blijft 600
    info "Self-signed cert: $cert"
    info "(Vervang door officieel cert+key wanneer beschikbaar -- zelfde bestandsnamen.)"
}

# ============================================================
# Helper script + sudoers regel zodat de app via één gericht
# commando een nieuw TLS-cert kan installeren via Beheer -> Certificaat
# ============================================================
install_cert_helper() {
    step "Cert-install helper (voor Beheer -> Certificaat)"

    local helper="/usr/local/sbin/kluisjes-install-cert"
    local staging="/var/lib/kluisjesbeheer/cert-staging"

    # Staging-map waar de app uploads neerzet voordat dit script ze installeert.
    # Eigendom van de kluisjes-user; helper-script (als root) leest hier uit.
    install -d -o "$APP_USER" -g "$APP_USER" -m 700 "$staging"

    # Helper-script zelf — root-owned, niet schrijfbaar voor kluisjes.
    cat > "$helper" <<'HELPER_EOF'
#!/bin/bash
# Installeer een nieuw TLS-cert+key voor kluisjesbeheer/nginx.
# Aangeroepen door de app via:  sudo /usr/local/sbin/kluisjes-install-cert
# Leest uit /var/lib/kluisjesbeheer/cert-staging/{cert.pem,key.pem}
# Schrijft naar /etc/nginx/ssl/self.{crt,key}, reload nginx bij succes.
set -euo pipefail

STAGING="/var/lib/kluisjesbeheer/cert-staging"
TARGET_CERT="/etc/nginx/ssl/self.crt"
TARGET_KEY="/etc/nginx/ssl/self.key"
SRC_CERT="$STAGING/cert.pem"
SRC_KEY="$STAGING/key.pem"

if [[ ! -f "$SRC_CERT" || ! -f "$SRC_KEY" ]]; then
    echo "ERROR: staging-bestanden ontbreken in $STAGING" >&2
    exit 1
fi

# Security: Voorkom symlink-aanval (TOCTOU) vanuit de kluisjes-user
if [[ -L "$SRC_CERT" || -L "$SRC_KEY" ]]; then
    echo "ERROR: staging-bestanden mogen geen symlinks zijn" >&2
    exit 1
fi

# Valideer dat het cert en de key bij elkaar horen (modulus-vergelijking)
cert_mod=$(openssl x509 -noout -modulus -in "$SRC_CERT" 2>/dev/null | openssl md5)
key_mod=$(openssl rsa  -noout -modulus -in "$SRC_KEY" 2>/dev/null | openssl md5)
if [[ "$cert_mod" != "$key_mod" || -z "$cert_mod" ]]; then
    echo "ERROR: cert en key horen niet bij elkaar (modulus mismatch)" >&2
    exit 2
fi

# Backup van het bestaande cert+key (één rollende kopie)
[[ -f "$TARGET_CERT" ]] && cp -a "$TARGET_CERT" "$TARGET_CERT.bak"
[[ -f "$TARGET_KEY"  ]] && cp -a "$TARGET_KEY"  "$TARGET_KEY.bak"

# Installeer nieuwe bestanden met juiste permissies
install -o root -g root -m 644 "$SRC_CERT" "$TARGET_CERT"
install -o root -g root -m 600 "$SRC_KEY"  "$TARGET_KEY"

# Test nginx-config; bij fout: rollback en exit
if ! nginx -t >/dev/null 2>&1; then
    echo "ERROR: nginx -t faalde, rollback uitgevoerd" >&2
    [[ -f "$TARGET_CERT.bak" ]] && mv "$TARGET_CERT.bak" "$TARGET_CERT"
    [[ -f "$TARGET_KEY.bak"  ]] && mv "$TARGET_KEY.bak"  "$TARGET_KEY"
    exit 3
fi

systemctl reload nginx

# Opruimen: backup behouden voor 1 generatie, staging leegmaken
rm -f "$SRC_CERT" "$SRC_KEY"

echo "OK: cert geïnstalleerd en nginx reloaded"
HELPER_EOF
    chown root:root "$helper"
    chmod 750 "$helper"
    info "Helper-script: $helper"

    # Sudoers-regel: alleen dit ene commando, zonder wachtwoord, niets anders.
    local sudoers="/etc/sudoers.d/kluisjesbeheer-cert"
    cat > "$sudoers" <<EOF
# Sta de kluisjes-user toe om uitsluitend het cert-install helper script te
# draaien als root. Geen andere commandos. Beheerd door install.sh.
$APP_USER ALL=(root) NOPASSWD: /usr/local/sbin/kluisjes-install-cert
EOF
    chmod 440 "$sudoers"
    # visudo -c valideert syntax; faalt het, dan removen we het bestand weer.
    if ! visudo -c -f "$sudoers" >/dev/null 2>&1; then
        rm -f "$sudoers"
        err "sudoers-regel afgewezen door visudo; cert-upload werkt niet via UI"
        return 1
    fi
    info "Sudoers-regel: $sudoers (alleen 1 commando toegestaan)"
}

# ============================================================
# NGINX reverse-proxy (HTTP 80 -> HTTPS 443 -> 127.0.0.1:5000)
# ============================================================
install_nginx() {
    step "NGINX reverse-proxy met TLS"

    ensure_tls_cert

    # Verwijder default site als die nog actief is (conflict op :80)
    if [[ -L /etc/nginx/sites-enabled/default ]]; then
        rm -f /etc/nginx/sites-enabled/default
        info "default-site uitgeschakeld"
    fi

    cat > "/etc/nginx/sites-available/${SERVICE_NAME}" <<EOF
# Kluisjesbeheer reverse-proxy met TLS
# Beheerd door install.sh -- niet handmatig bewerken.
#
# Standaard: self-signed cert (genereert in ensure_tls_cert). Vervang
# /etc/nginx/ssl/self.{crt,key} door echte cert+key bestanden voor productie
# (zelfde bestandsnamen -> geen nginx-config-wijziging nodig).

# HTTP -> HTTPS redirect
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://\$host\$request_uri;
}

# HTTPS-server
server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;

    ssl_certificate     /etc/nginx/ssl/self.crt;
    ssl_certificate_key /etc/nginx/ssl/self.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    client_max_body_size 16M;

    # Grote proxy-buffers nodig: na Entra-login stuurt Flask een Set-Cookie
    # header met de sessie + access_token; samen >8KB. Default nginx-buffer
    # is te klein -> "upstream sent too big header" -> Bad Gateway.
    proxy_buffer_size       16k;
    proxy_buffers           8 16k;
    proxy_busy_buffers_size 32k;

    # Statische frontend-assets (img) direct serveren
    location /img/ {
        root $APP_DIR/frontend/dist;
        expires 1h;
        add_header Cache-Control "public";
    }

    # Alles overig -> Gunicorn
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }
}
EOF

    # Symlink naar sites-enabled (idempotent)
    ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" \
           "/etc/nginx/sites-enabled/${SERVICE_NAME}"

    # Config testen voor we (her)laden
    run_with_spinner "nginx -t (configtest)" nginx -t
    # LANG/LC_ALL explicit zetten — anders klaagt invoke-rc.d/perl
    LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 systemctl enable nginx >/dev/null 2>&1
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    info "NGINX luistert op 80 (redirect) + 443 (TLS) -> 127.0.0.1:$APP_PORT"
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
    # Test backend direct
    local backend_code
    backend_code=$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$APP_PORT/" || true)
    if [[ "$backend_code" =~ ^(200|302|500)$ ]]; then
        info "Backend (gunicorn :$APP_PORT) -> HTTP $backend_code"
    else
        warn "Backend op :$APP_PORT geeft HTTP $backend_code -- check journalctl"
    fi
    # Test via nginx — HTTP poort 80 (verwacht 301 redirect naar HTTPS)
    local http_code
    http_code=$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1/" || true)
    if [[ "$http_code" == "301" ]]; then
        info "NGINX (poort 80) -> HTTP 301 (redirect naar HTTPS) -- OK"
    else
        warn "NGINX op poort 80 geeft HTTP $http_code -- verwacht 301"
    fi
    # Test via nginx — HTTPS poort 443 (self-signed, dus -k)
    local https_code
    https_code=$(curl -sS -k -o /dev/null -w '%{http_code}' "https://127.0.0.1/" || true)
    if [[ "$https_code" =~ ^(200|302|500)$ ]]; then
        info "NGINX (poort 443, self-signed) -> HTTP $https_code"
    else
        warn "NGINX op poort 443 geeft HTTP $https_code -- check 'nginx -t' en journalctl -u nginx"
    fi
    # Een 500 bij een verse install is verwacht (config.json bevat nog VUL_IN_*).
    # We willen alleen dat de stack reageert; de Entra-config komt in stap 4 van de README.
    if [[ "$backend_code" == "500" || "$https_code" == "500" ]]; then
        info "(HTTP 500 is normaal voor een verse install -- config.json staat nog op VUL_IN_*)"
    fi
}

# ============================================================
# Eindrapport
# ============================================================
final_report() {
    local ip lan_ip
    ip=$(curl -sS -m 5 https://ifconfig.me 2>/dev/null || echo "(kon niet bepalen)")
    lan_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    [[ -z "$lan_ip" ]] && lan_ip="<server-ip>"

    echo ""
    echo "================================================================"
    echo -e "${GREEN}Kluisjesbeheer installatie afgerond${NC}"
    echo "================================================================"
    cat <<EOF

Service:        systemctl status $SERVICE_NAME
App-logs:       journalctl -u $SERVICE_NAME -f
NGINX-logs:     tail -f /var/log/nginx/access.log /var/log/nginx/error.log
Cron-logs:      tail -f $CRON_LOG
Database:       $APP_DIR/backend/kluisjesbeheer.db
Config:         $APP_DIR/backend/config.json
Backups:        $APP_DIR/backend/backups/

App bereikbaar op:    https://$lan_ip/   (self-signed cert -- browser geeft 1x
                      "Niet beveiligd"-waarschuwing, dan "Geavanceerd ->
                      Doorgaan")
HTTP poort 80:        redirect naar HTTPS
Backend (intern):     http://127.0.0.1:$APP_PORT (alleen lokaal, niet vanaf LAN)
Uitgaand IP voor SWP-whitelist:
                      $ip

================================================================
Volgende stappen:

  1. Open https://$lan_ip/ in de browser.
     Je krijgt automatisch een setup-scherm waar je de Entra-gegevens
     invult (TenantId, ClientId, ClientSecret, RedirectUri).
     Tip: stel de RedirectUri in Entra in op:
       https://$lan_ip/auth/callback

  2. Na opslaan word je doorgestuurd naar de inlogpagina. Log in met je
     Microsoft-account. De eerste gebruiker wordt automatisch beheerder.

  3. Vul de Magister-koppeling in via Beheer -> Instellingen:
     URL (https://<jouwschool>.swp.nl:8800/doc), account, wachtwoord.
     Wordt versleuteld in de database opgeslagen.

  4. Test de leerling-sync:
     sudo -u $APP_USER $VENV_DIR/bin/python $APP_DIR/backend/cron_sync.py

  5. (Later, voor productie) Vervang het self-signed cert door een echt
     cert: overschrijf /etc/nginx/ssl/self.crt en /etc/nginx/ssl/self.key
     met de echte bestanden (zelfde bestandsnamen). Daarna:
     nginx -t && systemctl reload nginx

LET OP: SecretKey in config.json is automatisch ingevuld -- NIET wijzigen
na gebruik (versleutelt Magister-wachtwoord in DB).
Toegangscontrole gaat via Entra "Assignment required: Yes" op de
Enterprise App -- niet via een groep in config.json.
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
    install_cert_helper
    install_nginx
    install_cron
    start_service
    smoketest
    final_report
}

main "$@"
