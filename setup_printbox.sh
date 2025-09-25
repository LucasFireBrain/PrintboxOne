#!/bin/bash
set -e

# === CONFIG ===
APPDIR="/home/lucas/printbox"
PYTHON=python3

echo "[INFO] Creating directories..."
mkdir -p $APPDIR/tmp

echo "[INFO] Creating empty JSON DBs if missing..."
[ -f "$APPDIR/whitelist.json" ]    || echo '{}' > "$APPDIR/whitelist.json"
[ -f "$APPDIR/quotas.json" ]       || echo '{}' > "$APPDIR/quotas.json"
[ -f "$APPDIR/printbox_log.json" ] || echo '[]' > "$APPDIR/printbox_log.json"

echo "[INFO] Installing dependencies..."
sudo apt update
sudo apt install -y $PYTHON-pip
pip3 install --upgrade pip
pip3 install PyPDF2

echo "[INFO] Setup complete."
echo "---------------------------------------------"
echo "Now copy these files into $APPDIR:"
echo "  - config.py"
echo "  - printbox_core.py"
echo "  - admin_panel.py"
echo "---------------------------------------------"
echo "Run the admin panel with:"
echo "  $PYTHON $APPDIR/admin_panel.py"
