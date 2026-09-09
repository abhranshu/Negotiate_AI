#!/usr/bin/env bash
#
# NegotiateAI — Ubuntu VM once-off setup
# Run as root/sudo on the target box.
#
# This prepares:
#   - /opt/negotiateai        app + venv
#   - /var/lib/negotiateai    SQLite DB + uploads
#   - /etc/negotiateai        .env
#   - negotiateai system user
#
set -euo pipefail

APP_ROOT="/opt/negotiateai"
DATA_ROOT="/var/lib/negotiateai"
ENV_DIR="/etc/negotiateai"
SERVICE_FILE="$(dirname "$0")/../scripts/negotiateai.service"

if [ "$EUID" -ne 0 ]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

if [ ! -f requirements_api.txt ]; then
  echo "This script expects to run from the repo root where requirements_api.txt exists." >&2
  exit 1
fi

echo "[1/6] Creating system user 'negotiateai'..."
if ! id -u negotiateai >/dev/null 2>&1; then
  useradd --system --no-create-home --shell /usr/sbin/nologin negotiateai
fi

echo "[2/6] Creating directories..."
mkdir -p "$APP_ROOT"
mkdir -p "$DATA_ROOT/uploads"
mkdir -p "$ENV_DIR"
chown -R negotiateai:negotiateai "$DATA_ROOT"
chmod 750 "$DATA_ROOT"
chmod 750 "$DATA_ROOT/uploads"

echo "[3/6] Copying app code into $APP_ROOT..."
# Copy everything except venvs, caches, and local secrets.
rsync -a --exclude '.venv' --exclude '.venv-1' --exclude 'venv' \
  --exclude '__pycache__' --exclude '*.pyc' \
  --exclude '.env' \
  --exclude '.env.vm.example' \
  --exclude 'scripts/negotiateai.service' \
  --exclude 'scripts/setup-vm.sh' \
  --exclude '.git' \
  . "$APP_ROOT"

echo "[4/6] Creating Python venv and installing backend deps..."
if [ -d "$APP_ROOT/.venv" ]; then
  echo "  venv already exists at $APP_ROOT/.venv, skipping creation."
else
  python3 -m venv "$APP_ROOT/.venv"
fi

"$APP_ROOT/.venv/bin/pip" install --upgrade pip
"$APP_ROOT/.venv/bin/pip" install -r requirements_api.txt

echo "[5/6] Placing env file template..."
if [ ! -f "$ENV_DIR/.env" ]; then
  cp .env.vm.example "$ENV_DIR/.env"
  chown negotiateai:negotiateai "$ENV_DIR/.env"
  chmod 640 "$ENV_DIR/.env"
  echo "  Wrote placeholder $ENV_DIR/.env."
  echo "  Edit it with the real values before starting the service."
else
  echo "  $ENV_DIR/.env already exists, leaving it alone."
fi

echo "[6/6] Installing systemd service..."
if [ -f "$SERVICE_FILE" ]; then
  cp "$SERVICE_FILE" /etc/systemd/system/negotiateai.service
  systemctl daemon-reload
  systemctl enable negotiateai.service
  echo "  Service installed."
else
  echo "  WARNING: could not find scripts/negotiateai.service next to this script." >&2
fi

echo ""
echo "Done."
echo ""
echo "Next steps:"
echo "  1. Edit $ENV_DIR/.env with the real DATABASE_URL, SECRET_KEY, and Supabase values."
echo "  2. Start the service:"
echo "       sudo systemctl start negotiateai"
echo "  3. Watch logs:"
echo "       sudo journalctl -u negotiateai -f"
echo "  4. Checkhealth:"
echo "       curl -fsS http://localhost:8000/health"
