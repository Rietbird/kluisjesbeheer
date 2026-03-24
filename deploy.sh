#!/bin/bash
# Kluisjesbeheer deployment script for Proxmox LXC container
# Usage: scp this project to the container, then run: bash deploy.sh
set -e

APP_DIR="/opt/kluisjesbeheer"
APP_USER="kluisjes"
VENV_DIR="$APP_DIR/.venv"
SERVICE_NAME="kluisjesbeheer"

echo "=== Kluisjesbeheer Deploy ==="

# 1. System dependencies
echo "[1/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nodejs npm > /dev/null

# 2. Create app user if needed
if ! id "$APP_USER" &>/dev/null; then
    echo "[2/7] Creating app user..."
    useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
else
    echo "[2/7] App user exists."
fi

# 3. Copy project files
echo "[3/7] Copying project files..."
mkdir -p "$APP_DIR"
rsync -a --exclude='.venv' --exclude='node_modules' --exclude='*.db' --exclude='__pycache__' \
    --exclude='.git' --exclude='config.json' \
    . "$APP_DIR/"

# 4. Python venv + dependencies
echo "[4/7] Setting up Python venv..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"
"$VENV_DIR/bin/pip" install -q gunicorn

# 5. Build frontend
echo "[5/7] Building frontend..."
cd "$APP_DIR/frontend"
npm ci --silent
npm run build
cd "$APP_DIR"

# 6. Ensure config exists
if [ ! -f "$APP_DIR/backend/config.json" ]; then
    echo "[!] config.json not found — copying example. Edit it before starting!"
    cp "$APP_DIR/backend/config.example.json" "$APP_DIR/backend/config.json"
fi

# 7. Set permissions
echo "[6/7] Setting permissions..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# 8. Create systemd service
echo "[7/7] Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Kluisjesbeheer Web Application
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/backend
ExecStart=$VENV_DIR/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 "app:create_app()"
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "=== Deploy complete! ==="
echo "Service: systemctl status $SERVICE_NAME"
echo "Logs:    journalctl -u $SERVICE_NAME -f"
echo ""
echo "Next steps:"
echo "  1. Edit $APP_DIR/backend/config.json with Entra ID + Magister credentials"
echo "  2. Set up Cloudflare tunnel pointing to 127.0.0.1:5000"
echo "  3. systemctl restart $SERVICE_NAME"
