#!/bin/bash
#
# Phase 07: Systemd Services Setup
# Installs and enables systemd services for auto-start
#

set -euo pipefail

echo "[07-services] Starting systemd services setup..."

SCRIPT_DIR="$(dirname "$0")/.."
SYSTEMD_DIR="/etc/systemd/system"
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/pi/photobooth}"

# List of service files
SERVICE_FILES=(
    "photobooth.service"
    "photobooth-watchdog.service"
    "photobooth-watchdog.timer"
    "photobooth-backup.service"
    "photobooth-backup.timer"
)

# Install service files
echo "Installing systemd service files..."

for service in "${SERVICE_FILES[@]}"; do
    src="$SCRIPT_DIR/systemd/$service"
    dst="$SYSTEMD_DIR/$service"

    if [[ -f "$src" ]]; then
        echo "  Installing $service..."
        cp "$src" "$dst"
        chmod 644 "$dst"
    else
        echo "  Warning: $src not found, skipping"
    fi
done

# Make scripts executable
echo "Setting script permissions..."
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true
chmod +x "$PHOTOBOOTH_DIR/scripts"/*.sh 2>/dev/null || true

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Stop running containers (will be managed by systemd)
echo "Stopping manually started containers..."
cd "$PHOTOBOOTH_DIR"
docker compose down 2>/dev/null || true

# Enable services
echo "Enabling services..."
systemctl enable photobooth.service
systemctl enable photobooth-watchdog.timer
systemctl enable photobooth-backup.timer

# Start services
echo "Starting services..."
systemctl start photobooth.service
sleep 5
systemctl start photobooth-watchdog.timer
systemctl start photobooth-backup.timer

# Check service status
echo ""
echo "Service status:"

for service in "photobooth.service" "photobooth-watchdog.timer" "photobooth-backup.timer"; do
    if systemctl is-active --quiet "$service"; then
        echo "  $service: active"
    else
        echo "  $service: inactive"
    fi
done

# Show timers
echo ""
echo "Active timers:"
systemctl list-timers --all 2>/dev/null | grep photobooth || echo "  No photobooth timers active"

# Show recent logs
echo ""
echo "Recent service logs:"
journalctl -u photobooth.service -n 5 --no-pager 2>/dev/null || true

echo ""
echo "[07-services] Systemd services setup complete"
echo ""
echo "Useful commands:"
echo "  View status:    sudo systemctl status photobooth"
echo "  View logs:      journalctl -u photobooth -f"
echo "  Restart:        sudo systemctl restart photobooth"
echo "  Stop:           sudo systemctl stop photobooth"
