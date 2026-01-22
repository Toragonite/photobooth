#!/bin/bash
#
# PhotoBooth Network Reset Script (NetworkManager version)
# Restores network configuration to defaults
#

set -euo pipefail

WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
AP_CONNECTION_NAME="photobooth-ap"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}This script must be run as root (use sudo)${NC}"
        exit 1
    fi
}

echo -e "${RED}=========================================="
echo " PhotoBooth Network Reset"
echo "==========================================${NC}"
echo ""
echo "This will reset network configuration to defaults."
echo ""

if [[ "${1:-}" != "--force" ]]; then
    read -p "Are you sure? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        echo "Reset cancelled."
        exit 0
    fi
fi

check_root

echo ""
echo "Stopping AP mode if active..."
nmcli connection down "$AP_CONNECTION_NAME" 2>/dev/null || true

echo "Removing AP connection profile..."
nmcli connection delete "$AP_CONNECTION_NAME" 2>/dev/null || true

echo "Stopping legacy services..."
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true

echo "Re-enabling NetworkManager management of wlan0..."
nmcli device set "$WIFI_INTERFACE" managed yes 2>/dev/null || true

echo "Reconnecting to available networks..."
nmcli device connect "$WIFI_INTERFACE" 2>/dev/null || true

# Wait for connection
echo "Waiting for connection..."
sleep 5

# Show status
echo ""
echo "Current network status:"
nmcli device status
echo ""
nmcli connection show --active

echo ""
echo -e "${GREEN}=========================================="
echo " Reset Complete!"
echo "==========================================${NC}"
echo ""
echo "The Pi is now in normal Wi-Fi client mode."
echo ""
ip addr show "$WIFI_INTERFACE" | grep "inet " || echo "No IP assigned yet"
echo ""
