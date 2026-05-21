#!/bin/sh
# Genereer self-signed cert als die nog niet bestaat, start dan nginx.
# Cert wordt opgeslagen in een named volume zodat hij re-creates overleeft.
set -e

CERT_DIR="/etc/nginx/ssl"
CERT="$CERT_DIR/self.crt"
KEY="$CERT_DIR/self.key"

mkdir -p "$CERT_DIR"

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    # nginx:alpine heeft geen openssl-binary standaard -- eenmalig
    # installeren voor cert-generatie. Geen restart nodig na install.
    if ! command -v openssl >/dev/null 2>&1; then
        echo "==> openssl installeren (eenmalig, voor cert-generatie)..."
        apk add --no-cache openssl >/dev/null 2>&1
    fi
    echo "==> Self-signed cert genereren (10 jaar geldig)..."
    openssl req -x509 -nodes -newkey rsa:2048 \
        -days 3650 \
        -subj "/CN=kluisjesbeheer.local" \
        -keyout "$KEY" -out "$CERT" 2>&1 | tail -3
    chmod 644 "$CERT"
    chmod 600 "$KEY"
    echo "==> Cert: $CERT"
else
    echo "==> TLS-cert bestaat al ($CERT)"
fi

exec nginx -g 'daemon off;'
