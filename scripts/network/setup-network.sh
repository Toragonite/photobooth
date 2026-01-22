#!/bin/bash
#
# PhotoBooth Network Setup Script (NetworkManager version)
# Configures Raspberry Pi 5 as a Wi-Fi Access Point
#
# Usage: sudo ./setup-network.sh [--dry-run] [--activate]
#

set -euo pipefail

# Configuration
WIFI_SSID="${WIFI_SSID:-photobooth}"
WIFI_PASSWORD="${WIFI_PASSWORD:-photobooth-1998}"
WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
WIFI_COUNTRY="${WIFI_COUNTRY:-RW}"
PI_IP="${PI_IP:-192.168.4.1}"
WIFI_CHANNEL="${WIFI_CHANNEL:-6}"
AP_CONNECTION_NAME="photobooth-ap"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=false
ACTIVATE=false

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
        --activate) ACTIVATE=true; shift ;;
        --help)
            echo "Usage: sudo $0 [--dry-run] [--activate]"
            echo ""
            echo "Options:"
            echo "  --dry-run   Show what would be done without making changes"
            echo "  --activate  Activate AP mode immediately after setup"
            exit 0
            ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

echo ""
echo -e "${BLUE}=========================================="
echo " PhotoBooth Network Setup (NetworkManager)"
echo "==========================================${NC}"
echo ""
echo "Configuration:"
echo "  SSID: $WIFI_SSID"
echo "  Password: $WIFI_PASSWORD"
echo "  Channel: $WIFI_CHANNEL"
echo "  Pi IP: $PI_IP"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    warn "DRY RUN MODE - No changes will be made"
else
    check_root
fi

# Check NetworkManager
if ! command -v nmcli &>/dev/null; then
    error "NetworkManager (nmcli) not found"
    exit 1
fi
success "NetworkManager available"

# Step 1: Unblock WiFi
log "Unblocking WiFi..."
run_cmd rfkill unblock wifi 2>/dev/null || true

# Step 2: Set country code
log "Setting Wi-Fi country code to $WIFI_COUNTRY..."
run_cmd iw reg set "$WIFI_COUNTRY" 2>/dev/null || true

# Step 3: Remove existing AP profile if exists
if nmcli connection show "$AP_CONNECTION_NAME" &>/dev/null; then
    log "Removing existing AP connection profile..."
    run_cmd nmcli connection delete "$AP_CONNECTION_NAME" 2>/dev/null || true
fi

# Step 4: Create AP connection profile
log "Creating AP connection profile..."
if [[ "$DRY_RUN" == false ]]; then
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
fi
success "AP connection profile created: $AP_CONNECTION_NAME"

# Step 5: Enable IP forwarding
log "Enabling IP forwarding..."
if [[ "$DRY_RUN" == false ]]; then
    if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf 2>/dev/null; then
        sed -i 's/^#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
        if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
            echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
        fi
    fi
    sysctl -w net.ipv4.ip_forward=1 2>/dev/null || true
fi
success "IP forwarding enabled"

# Step 6: Activate AP if requested
if [[ "$ACTIVATE" == true ]] && [[ "$DRY_RUN" == false ]]; then
    log "Activating AP mode..."
    nmcli device disconnect "$WIFI_INTERFACE" 2>/dev/null || true
    sleep 2
    if nmcli connection up "$AP_CONNECTION_NAME"; then
        success "AP mode activated"
    else
        error "Failed to activate AP mode"
    fi
fi

# Show status
echo ""
log "Connection profile details:"
if [[ "$DRY_RUN" == false ]]; then
    nmcli connection show "$AP_CONNECTION_NAME" | grep -E "ssid|ipv4.addresses|wifi-sec" | head -5
fi

echo ""
echo -e "${GREEN}=========================================="
echo " Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Wi-Fi Network (when AP is active):"
echo "  SSID:     $WIFI_SSID"
echo "  Password: $WIFI_PASSWORD"
echo "  Pi IP:    $PI_IP"
echo ""
echo "Commands:"
echo "  Activate AP:   sudo nmcli connection up $AP_CONNECTION_NAME"
echo "  Deactivate:    sudo nmcli connection down $AP_CONNECTION_NAME"
echo "  Auto-switch:   sudo ./auto-network-mode.sh --force-ap"
echo ""
echo "Connect devices to '$WIFI_SSID' and access:"
echo "  https://$PI_IP"
echo ""
