#!/bin/bash
#
# PhotoBooth Network Reset Script
# Restores network configuration to defaults
#

set -euo pipefail

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
echo "Stopping services..."
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

echo "Disabling services..."
systemctl disable hostapd 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true
systemctl mask hostapd 2>/dev/null || true

echo "Restoring dnsmasq config..."
if [[ -f /etc/dnsmasq.conf.orig ]]; then
    mv /etc/dnsmasq.conf.orig /etc/dnsmasq.conf
    echo -e "${GREEN}[OK]${NC} Original dnsmasq.conf restored"
fi

echo "Removing hostapd config..."
rm -f /etc/hostapd/hostapd.conf
sed -i 's|^DAEMON_CONF=.*|#DAEMON_CONF=""|' /etc/default/hostapd 2>/dev/null || true

echo "Removing static IP from dhcpcd..."
sed -i '/# PhotoBooth Wi-Fi AP/,/nohook wpa_supplicant/d' /etc/dhcpcd.conf

echo "Restarting networking..."
systemctl restart dhcpcd
systemctl restart wpa_supplicant 2>/dev/null || true

echo ""
echo -e "${GREEN}=========================================="
echo " Reset Complete!"
echo "==========================================${NC}"
echo ""
echo "The Pi is now in normal Wi-Fi client mode."
echo "You may need to reboot: sudo reboot"
echo ""
