#!/bin/sh
# Init-container voor kluisjesbeheer Docker-stack.
# Schrijft een config.json-template met random SecretKey naar het data-
# volume bij eerste start. Bestaande config.json blijft ongemoeid.
set -e

DATA_DIR="/opt/kluisjesbeheer/backend/data"
CFG="$DATA_DIR/config.json"

mkdir -p "$DATA_DIR/backups"

if [ -f "$CFG" ]; then
    echo "==> config.json bestaat al -- laten staan"
    exit 0
fi

echo "==> config.json niet gevonden -- template aanmaken met random SecretKey"

SECRET=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')

cat > "$CFG" <<EOF
{
  "TenantId": "VUL_IN_TENANT_ID",
  "ClientId": "VUL_IN_CLIENT_ID",
  "ClientSecret": "VUL_IN_CLIENT_SECRET",
  "RedirectUri": "VUL_IN_REDIRECT_URI",
  "SecretKey": "$SECRET",
  "SchoolNaam": "Mijn School",
  "SchoolSubtitel": "",
  "SchoolLogo": "/img/logo.png",
  "SchoolKleur": "#FF8200",
  "AllowedOrigins": []
}
EOF

# Niet wereld-leesbaar (bevat SecretKey)
chmod 600 "$CFG"
chown 1001:1001 "$CFG"   # = kluisjes-user uit Dockerfile

echo "==> Klaar. Bewerk $CFG (volume), dan: docker compose restart app"
