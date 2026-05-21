#!/usr/bin/env bash
# Kluisjesbeheer Proxmox helper-script
# Maakt automatisch een Debian 12 LXC container aan op de Proxmox host
# en installeert kluisjesbeheer erin (klassiek of via Docker).
#
# Gebruik op de Proxmox host:
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/proxmox/install-ct.sh)"

set -euo pipefail

# ============================================================
# UI helpers
# ============================================================
# ANSI-C quoting ($'...') zodat de variabelen het ECHTE escape-char
# bevatten -- niet de letterlijke "\033"-string. Hierdoor renderen
# `cat <<EOF` met ${COLOR}-interpolatie ook netjes (geen `echo -e` nodig).
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
NC=$'\033[0m'

banner() {
    echo -e "${CYAN}${BOLD}"
    cat <<'EOF'
  _  ___       _      _           _         _
 | |/ / |_   _(_)___ (_) ___  ___| |__   ___| |__   ___  ___ _ __
 | ' /| | | | | / __|| |/ _ \/ __| '_ \ / _ \ '_ \ / _ \/ _ \ '__|
 | . \| | |_| | \__ \| |  __/\__ \ |_) |  __/ |_) |  __/  __/ |
 |_|\_\_|\__,_|_|___// |\___||___/_.__/ \___|_.__/ \___|\___|_|
                   |__/
EOF
    echo -e "  Proxmox helper-script — ${NC}${BOLD}install-ct.sh${NC}"
    echo ""
}

info()  { echo -e " ${BLUE}>${NC} $*"; }
ok()    { echo -e " ${GREEN}✓${NC} $*"; }
warn()  { echo -e " ${YELLOW}!${NC} $*"; }
err()   { echo -e " ${RED}✗${NC} $*" >&2; }
ask()   { read -rp "$(echo -e " ${CYAN}?${NC} $1 ${BOLD}[$2]${NC}: ")" "$3" || true; eval "$3=\${$3:-$2}"; }
askyn() { local default="$2"; read -rp "$(echo -e " ${CYAN}?${NC} $1 ${BOLD}[$default]${NC}: ")" answer || true; answer=${answer:-$default}; [[ "$answer" =~ ^[jJyY]$ ]]; }

die() { err "$1"; exit 1; }

# ============================================================
# Pre-flight
# ============================================================
preflight() {
    [[ $EUID -eq 0 ]] || die "Draai dit script als root op de Proxmox host."
    command -v pct >/dev/null 2>&1 || die "'pct' niet gevonden — draai je dit op een Proxmox host?"
    command -v pveam >/dev/null 2>&1 || die "'pveam' niet gevonden — Proxmox VE-tools ontbreken."
    ok "Draait op Proxmox host"
}

# ============================================================
# Template ophalen indien nodig
# ============================================================
ensure_template() {
    info "Debian 12 template controleren..."
    local template_pattern="debian-12-standard"
    local available
    available=$(pveam available --section system 2>/dev/null | grep "$template_pattern" | head -1 | awk '{print $2}')
    [[ -n "$available" ]] || die "Geen Debian 12 template beschikbaar via pveam. Update je template-lijst: 'pveam update'."

    local installed
    installed=$(pveam list local 2>/dev/null | grep "$template_pattern" | head -1 | awk '{print $1}')
    if [[ -z "$installed" ]]; then
        info "Template '$available' downloaden..."
        pveam download local "$available" >/dev/null
        installed="local:vztmpl/$available"
        ok "Template gedownload: $available"
    else
        ok "Template aanwezig: $(basename "$installed")"
    fi
    TEMPLATE="$installed"
}

# ============================================================
# Volgende vrije CT-ID vinden
# ============================================================
next_ctid() {
    local id=200
    while pct status "$id" >/dev/null 2>&1; do
        id=$((id + 1))
    done
    echo "$id"
}

# ============================================================
# Storage detecteren
# ============================================================
detect_storage() {
    local storages
    storages=$(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 {print $1}')
    [[ -n "$storages" ]] || die "Geen storage gevonden die 'rootdir' ondersteunt."
    # Voorkeur: local-lvm; anders eerste in lijst
    if echo "$storages" | grep -qx "local-lvm"; then
        echo "local-lvm"
    else
        echo "$storages" | head -1
    fi
}

# ============================================================
# Detect default bridge
# ============================================================
detect_bridge() {
    # vmbr0 heeft sterke voorkeur (management-bridge by convention).
    if ip link show vmbr0 >/dev/null 2>&1; then
        echo "vmbr0"
        return
    fi
    # Anders: deterministisch alfabetisch sorteren (eerste vmbrN).
    # NIET willekeurig "head -1" want awk-output volgorde is kernel-afhankelijk.
    local first
    first=$(ip -br link | awk '$1 ~ /^vmbr/ {print $1}' | sort | head -1)
    if [[ -n "$first" ]]; then
        echo "$first"
    else
        echo "vmbr0"   # laatste fallback, script faalt zo bij CT-create
    fi
}

# ============================================================
# Hoofdmenu
# ============================================================
main_menu() {
    echo ""
    echo -e "${BOLD}Kies installatie-modus:${NC}"
    echo "  1) Klassiek  — install.sh in de CT (Python + nginx direct op het OS)"
    echo "  2) Docker    — docker compose stack in de CT"
    echo "  Q) Stoppen"
    echo ""
    local choice
    read -rp " > " choice
    case "$choice" in
        1) MODE="classic" ;;
        2) MODE="docker"  ;;
        [Qq]) info "Gestopt."; exit 0 ;;
        *) die "Ongeldige keuze." ;;
    esac
    ok "Modus: $MODE"
}

# ============================================================
# CT-parameters vragen
# ============================================================
ask_params() {
    echo ""
    echo -e "${BOLD}Container-parameters${NC} ${YELLOW}(Enter = default)${NC}"
    local default_ctid; default_ctid=$(next_ctid)
    local default_bridge; default_bridge=$(detect_bridge)
    local default_storage; default_storage=$(detect_storage)

    # Defaults per modus (klassiek lichter dan Docker)
    local default_cores=2
    local default_memory default_disk
    if [[ "$MODE" == "docker" ]]; then
        default_memory=2048
        default_disk=12
    else
        default_memory=1024
        default_disk=8
    fi

    ask "CT-ID" "$default_ctid" CTID
    ask "Hostname" "kluisjesbeheer" HOSTNAME
    ask "Cores" "$default_cores" CORES
    ask "Memory (MB)" "$default_memory" MEMORY
    ask "Disk (GB)" "$default_disk" DISK
    ask "Bridge" "$default_bridge" BRIDGE
    ask "Storage" "$default_storage" STORAGE

    echo ""
    if askyn "DHCP gebruiken voor IP-adres?" "j"; then
        IP_CONFIG="dhcp"
    else
        ask "Statisch IP (CIDR, bv. 10.0.0.50/24)" "" STATIC_IP
        ask "Gateway" "${STATIC_IP%.*}.1" GATEWAY
        IP_CONFIG="${STATIC_IP},gw=${GATEWAY}"
    fi

    if askyn "Onprivileged container?" "j"; then PRIV_FLAG="--unprivileged 1"; else PRIV_FLAG="--unprivileged 0"; fi

    # Generate een random root-wachtwoord (gebruiker krijgt 'm aan eind getoond)
    ROOT_PW=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')

    echo ""
    echo -e "${BOLD}Samenvatting:${NC}"
    cat <<EOF
  CT-ID         : $CTID
  Hostname      : $HOSTNAME
  Modus         : $MODE
  Cores / RAM   : $CORES / ${MEMORY}MB
  Disk          : ${DISK}GB op $STORAGE
  Network       : $BRIDGE, $IP_CONFIG
  Template      : $(basename "$TEMPLATE")
EOF
    echo ""
    askyn "Doorgaan met aanmaken?" "j" || die "Geannuleerd."
}

# ============================================================
# Container aanmaken + starten
# ============================================================
create_ct() {
    info "Container $CTID aanmaken..."
    # shellcheck disable=SC2086
    pct create "$CTID" "$TEMPLATE" \
        --hostname "$HOSTNAME" \
        --cores "$CORES" --memory "$MEMORY" --swap 512 \
        --rootfs "${STORAGE}:${DISK}" \
        --net0 "name=eth0,bridge=${BRIDGE},firewall=1,ip=${IP_CONFIG},type=veth" \
        --nameserver "8.8.8.8" \
        $PRIV_FLAG --features "nesting=1$([[ $MODE == docker ]] && echo ',keyctl=1')" \
        --password "$ROOT_PW" \
        --onboot 1 \
        --start 1 >/dev/null

    ok "Container aangemaakt + gestart"
    info "Wachten tot netwerk up is..."
    local i=0
    # TCP-check ipv ping (veel enterprise/school-firewalls blokkeren ICMP egress).
    # deb.debian.org:443 is een gegarandeerde dependency voor apt straks; als die
    # niet reachable is heeft de hele install geen zin.
    while ! pct exec "$CTID" -- bash -c "timeout 2 bash -c '</dev/tcp/deb.debian.org/443' 2>/dev/null"; do
        i=$((i+1))
        [[ $i -gt 30 ]] && die "Netwerk komt niet up binnen 30s — check bridge/VLAN."
        sleep 1
    done
    ok "Netwerk werkt"

    CT_IP=$(pct exec "$CTID" -- hostname -I | awk '{print $1}')
    info "Container-IP: ${BOLD}$CT_IP${NC}"
}

# ============================================================
# Klassieke install via install.sh
# ============================================================
install_classic() {
    info "Klassieke installatie via install.sh (git clone vanaf GitHub)..."
    # CT heeft nog geen apt-update + geen git
    pct exec "$CTID" -- bash -c "
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq && apt-get install -y -qq git ca-certificates >/dev/null
        git clone --depth 1 https://github.com/Rietbird/kluisjesbeheer.git /root/kluisjesbeheer
        cd /root/kluisjesbeheer && bash install.sh
    " || die "install.sh in CT $CTID is gefaald — debug met 'pct enter $CTID'."
    ok "Klassieke installatie afgerond"
}

# ============================================================
# Docker-install via compose
# ============================================================
install_docker() {
    info "Docker + compose-stack installeren..."
    pct exec "$CTID" -- bash -c "
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq
        apt-get install -y -qq ca-certificates curl gnupg git >/dev/null
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
        echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable\" > /etc/apt/sources.list.d/docker.list
        apt-get update -qq
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null
        systemctl enable --now docker >/dev/null

        git clone --depth 1 https://github.com/Rietbird/kluisjesbeheer.git /opt/kluisjesbeheer
        cd /opt/kluisjesbeheer
        # Bouw lokaal (geen GHCR-publish yet) -- override schrijft 'build: .'
        cat > docker-compose.override.yml <<EOF
services:
  init:
    image: kluisjesbeheer:latest
    build: .
  app:
    image: kluisjesbeheer:latest
    build: .
EOF
        docker compose up -d --build
    " || die "Docker-install in CT $CTID is gefaald — debug met 'pct enter $CTID'."
    ok "Docker-stack draait"
}

# ============================================================
# Eindrapport
# ============================================================
final_report() {
    echo ""
    echo -e "${GREEN}${BOLD}================================================================"
    echo -e "  Kluisjesbeheer geïnstalleerd in CT $CTID"
    echo -e "================================================================${NC}"
    cat <<EOF

  ${BOLD}Container${NC}    : CT $CTID ($HOSTNAME)
  ${BOLD}IP-adres${NC}     : $CT_IP
  ${BOLD}Modus${NC}        : $MODE
  ${BOLD}Root-pw${NC}      : $ROOT_PW
                 (${YELLOW}noteer en bewaar veilig${NC} — wijzigbaar met 'passwd' in 'pct enter $CTID')

  ${BOLD}App-URL${NC}      : https://$CT_IP/
                 (self-signed cert — browser geeft 1× "Niet beveiligd"-waarschuwing,
                 dan "Geavanceerd → Doorgaan")

  ${BOLD}Console${NC}      : pct enter $CTID
  ${BOLD}Stop/start${NC}   : pct stop $CTID  |  pct start $CTID
  ${BOLD}Verwijderen${NC}  : pct stop $CTID && pct destroy $CTID --purge

${BOLD}Volgende stappen (eenmalig):${NC}
EOF
    if [[ "$MODE" == "classic" ]]; then
        cat <<EOF
  1. Vul Entra-credentials in:
     pct exec $CTID -- nano /opt/kluisjesbeheer/backend/config.json
  2. Restart de app:
     pct exec $CTID -- systemctl restart kluisjesbeheer
EOF
    else
        cat <<EOF
  1. Vul Entra-credentials in (config.json zit in docker volume):
     CFG=\$(pct exec $CTID -- docker volume inspect kluisjesbeheer_app-data --format '{{ .Mountpoint }}')/config.json
     pct exec $CTID -- nano "\$CFG"
  2. Restart de app-container:
     pct exec $CTID -- docker compose -f /opt/kluisjesbeheer/docker-compose.yml restart app
EOF
    fi
    cat <<EOF
  3. Open https://$CT_IP/ in de browser → log in met je Entra-account.
     De eerste user wordt automatisch beheerder.
  4. Vul Magister-koppeling in via Beheer → Import.
  5. Vraag bij SWP een IP-whitelist aan voor het uitgaande IP:
     pct exec $CTID -- curl -s https://ifconfig.me

Volledige docs: https://github.com/Rietbird/kluisjesbeheer
EOF
}

# ============================================================
# Main
# ============================================================
main() {
    banner
    preflight
    ensure_template
    main_menu
    ask_params
    create_ct
    if [[ "$MODE" == "classic" ]]; then
        install_classic
    else
        install_docker
    fi
    final_report
}

main "$@"
