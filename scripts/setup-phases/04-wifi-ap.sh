#!/bin/bash
#
# Phase 04: Wi-Fi Access Point Setup (NetworkManager version)
# Creates AP connection profile using NetworkManager
#

set -euo pipefail

echo "[04-wifi-ap] Starting Wi-Fi AP configuration..."

# Configuration from environment
WIFI_SSID="${WIFI_SSID:-photobooth}"
WIFI_PASSWORD="${WIFI_PASSWORD:-photobooth-1998}"
WIFI_CHANNEL="${WIFI_CHANNEL:-6}"
PI_IP="${PI_IP:-192.168.4.1}"
WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
AP_CONNECTION_NAME="photobooth-ap"
COUNTRY_CODE="${COUNTRY_CODE:-RW}"

echo "Configuration:"
echo "  SSID: $WIFI_SSID"
echo "  Password: $WIFI_PASSWORD"
echo "  Channel: $WIFI_CHANNEL"
echo "  Pi IP: $PI_IP"
echo "  Interface: $WIFI_INTERFACE"

# Check if NetworkManager is available
if ! command -v nmcli &>/dev/null; then
    echo "ERROR: NetworkManager (nmcli) not found"
    echo "Please install NetworkManager or use the legacy dhcpcd setup"
    exit 1
fi

# Unblock WiFi
echo "Unblocking WiFi..."
rfkill unblock wifi 2>/dev/null || true

# Set Wi-Fi regulatory domain
echo "Setting Wi-Fi country code to $COUNTRY_CODE..."
iw reg set "$COUNTRY_CODE" 2>/dev/null || true

# Remove existing AP connection if exists
if nmcli connection show "$AP_CONNECTION_NAME" &>/dev/null; then
    echo "Removing existing AP connection profile..."
    nmcli connection delete "$AP_CONNECTION_NAME" 2>/dev/null || true
fi

# Create AP connection profile
echo "Creating AP connection profile..."
nmcli connection add \
    type wifi \
    ifname "$WIFI_INTERFACE" \
    con-name "$AP_CONNECTION_NAME" \
    autoconnect no \
    ssid "$WIFI_SSID" \
    mode ap \
    ipv4.method shared \
    ipv4.addresses "$PI_IP/24" \
    wifi.band bg \
    wifi.channel "$WIFI_CHANNEL" \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "$WIFI_PASSWORD"

echo "AP connection profile created: $AP_CONNECTION_NAME"

# Configure dnsmasq for NetworkManager's shared mode (optional, NM handles it)
# But we can still install dnsmasq as a fallback
echo "Installing dnsmasq (fallback)..."
apt-get install -y -qq dnsmasq || true

# Disable standalone dnsmasq (NetworkManager handles DHCP in shared mode)
systemctl disable dnsmasq 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# Enable IP forwarding
echo "Enabling IP forwarding..."
if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf 2>/dev/null; then
    sed -i 's/^#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
    if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
        echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    fi
fi
sysctl -w net.ipv4.ip_forward=1 2>/dev/null || true

# Test AP mode (optional - don't activate by default to keep internet access)
echo ""
echo "AP connection profile is ready but NOT activated."
echo ""
echo "To activate AP mode manually:"
echo "  sudo nmcli connection up $AP_CONNECTION_NAME"
echo ""
echo "To return to client mode:"
echo "  sudo nmcli connection down $AP_CONNECTION_NAME"
echo "  sudo nmcli device connect $WIFI_INTERFACE"
echo ""
echo "Or use the auto-network script:"
echo "  sudo ./scripts/network/auto-network-mode.sh --force-ap"
echo "  sudo ./scripts/network/auto-network-mode.sh --force-client"
echo ""

# Show connection details
echo "AP Connection Details:"
nmcli connection show "$AP_CONNECTION_NAME" | grep -E "ssid|ipv4|wifi-sec" | head -10

echo ""
echo "[04-wifi-ap] Wi-Fi AP configuration complete"
echo ""
echo "Wi-Fi Network Details:"
echo "  SSID: $WIFI_SSID"
echo "  Password: $WIFI_PASSWORD"
echo "  Pi IP: $PI_IP (when AP is active)"
echo ""
echo "Clients can connect to the '$WIFI_SSID' network"
echo "and access the photo booth at https://$PI_IP"
