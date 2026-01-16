#!/bin/bash
#
# PhotoBooth Network Setup Script
# Configures Raspberry Pi 5 as a Wi-Fi Access Point
#
# Usage: sudo ./setup-network.sh [--dry-run] [--2.4ghz]
#

set -euo pipefail

# Configuration
# WIFI_PASSWORD is REQUIRED - must be set before running
WIFI_SSID="${WIFI_SSID:-photobooth}"
WIFI_PASSWORD="${WIFI_PASSWORD:?WIFI_PASSWORD is required. Set via: export WIFI_PASSWORD=your-secure-password}"
WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
WIFI_COUNTRY="${WIFI_COUNTRY:-RW}"
PI_IP="${PI_IP:-192.168.4.1}"
DHCP_RANGE_START="${DHCP_RANGE_START:-192.168.4.10}"
DHCP_RANGE_END="${DHCP_RANGE_END:-192.168.4.50}"

# Default to 2.4GHz for better compatibility
WIFI_HW_MODE="g"
WIFI_CHANNEL="6"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=false

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

run_cmd() {
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would execute: $*"
    else
        "$@"
    fi
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --5ghz) WIFI_HW_MODE="a"; WIFI_CHANNEL="36"; shift ;;
        --2.4ghz) WIFI_HW_MODE="g"; WIFI_CHANNEL="6"; shift ;;
        --help)
            echo "Usage: sudo $0 [--dry-run] [--2.4ghz] [--5ghz]"
            exit 0
            ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

echo ""
echo -e "${BLUE}=========================================="
echo " PhotoBooth Network Setup"
echo "==========================================${NC}"
echo ""
echo "Configuration:"
echo "  SSID: $WIFI_SSID"
echo "  Password: (set via WIFI_PASSWORD environment variable)"
echo "  Band: $WIFI_HW_MODE (channel $WIFI_CHANNEL)"
echo "  Pi IP: $PI_IP"
echo "  DHCP Range: $DHCP_RANGE_START - $DHCP_RANGE_END"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    warn "DRY RUN MODE - No changes will be made"
else
    check_root
fi

# Step 1: Install packages
log "Installing hostapd and dnsmasq..."
run_cmd apt-get update -qq
run_cmd apt-get install -y -qq hostapd dnsmasq

# Step 2: Stop services
log "Stopping services..."
run_cmd systemctl stop hostapd 2>/dev/null || true
run_cmd systemctl stop dnsmasq 2>/dev/null || true

# Step 3: Unblock WiFi
log "Unblocking WiFi..."
run_cmd rfkill unblock wifi 2>/dev/null || true

# Step 4: Configure static IP
log "Configuring static IP..."
if ! grep -q "# PhotoBooth Wi-Fi AP" /etc/dhcpcd.conf 2>/dev/null; then
    if [[ "$DRY_RUN" == false ]]; then
        cat >> /etc/dhcpcd.conf << EOF

# PhotoBooth Wi-Fi AP Static IP Configuration
interface ${WIFI_INTERFACE}
    static ip_address=${PI_IP}/24
    nohook wpa_supplicant
EOF
    fi
    success "Static IP configured"
else
    log "Static IP already configured"
fi

# Step 5: Configure hostapd
log "Configuring hostapd..."
if [[ "$DRY_RUN" == false ]]; then
    cat > /etc/hostapd/hostapd.conf << EOF
# PhotoBooth Wi-Fi Access Point Configuration
interface=${WIFI_INTERFACE}
driver=nl80211
ssid=${WIFI_SSID}
hw_mode=${WIFI_HW_MODE}
channel=${WIFI_CHANNEL}
country_code=${WIFI_COUNTRY}
ieee80211n=1
wmm_enabled=0
auth_algs=1
wpa=2
wpa_passphrase=${WIFI_PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
ignore_broadcast_ssid=0
max_num_sta=10
EOF
    chmod 600 /etc/hostapd/hostapd.conf
fi
success "hostapd configured"

# Point hostapd daemon to config
if [[ "$DRY_RUN" == false ]]; then
    sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd 2>/dev/null || true
fi

# Step 6: Configure dnsmasq
log "Configuring dnsmasq..."
if [[ "$DRY_RUN" == false ]]; then
    # Backup original
    [[ -f /etc/dnsmasq.conf ]] && [[ ! -f /etc/dnsmasq.conf.orig ]] && \
        cp /etc/dnsmasq.conf /etc/dnsmasq.conf.orig

    cat > /etc/dnsmasq.conf << EOF
# PhotoBooth DHCP and DNS Configuration
interface=${WIFI_INTERFACE}
bind-interfaces
dhcp-range=${DHCP_RANGE_START},${DHCP_RANGE_END},255.255.255.0,24h
dhcp-option=option:router,${PI_IP}
dhcp-option=option:dns-server,${PI_IP}
domain=photobooth.local
local=/photobooth.local/
address=/photobooth.local/${PI_IP}
address=/#/${PI_IP}
dhcp-leasefile=/var/lib/misc/dnsmasq.leases
log-dhcp
no-resolv
no-poll
cache-size=1000
EOF
fi
success "dnsmasq configured"

# Step 7: Enable and start services
log "Enabling services..."
run_cmd systemctl unmask hostapd 2>/dev/null || true
run_cmd systemctl enable hostapd
run_cmd systemctl enable dnsmasq

log "Restarting dhcpcd..."
run_cmd systemctl restart dhcpcd
sleep 3

log "Starting hostapd..."
run_cmd systemctl start hostapd
sleep 2

log "Starting dnsmasq..."
run_cmd systemctl start dnsmasq

# Step 8: Verify
echo ""
log "Verifying setup..."

if [[ "$DRY_RUN" == false ]]; then
    if systemctl is-active --quiet hostapd; then
        success "hostapd is running"
    else
        error "hostapd is NOT running"
    fi

    if systemctl is-active --quiet dnsmasq; then
        success "dnsmasq is running"
    else
        error "dnsmasq is NOT running"
    fi

    if ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep -q "$PI_IP"; then
        success "Interface has IP $PI_IP"
    else
        warn "Interface may not have expected IP"
    fi
fi

echo ""
echo -e "${GREEN}=========================================="
echo " Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Wi-Fi Network:"
echo "  SSID:     $WIFI_SSID"
echo "  Password: (set via WIFI_PASSWORD environment variable)"
echo ""
echo "Connect devices to '$WIFI_SSID' and access:"
echo "  https://$PI_IP"
echo "  https://photobooth.local"
echo ""
