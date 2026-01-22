#!/bin/bash
#
# PhotoBooth Auto Network Mode
# Automatically switches between AP mode (offline) and Client mode (online)
#
# Usage:
#   ./auto-network-mode.sh          # Check and switch if needed
#   ./auto-network-mode.sh --force-ap    # Force AP mode
#   ./auto-network-mode.sh --force-client # Force client mode
#   ./auto-network-mode.sh --status      # Show current mode
#
# This script is designed to run:
#   1. On boot (via systemd)
#   2. Periodically (via cron or timer)
#

set -euo pipefail

# Configuration
WIFI_SSID="${WIFI_SSID:-photobooth}"
WIFI_PASSWORD="${WIFI_PASSWORD:-photobooth-1998}"
PI_IP="${PI_IP:-192.168.4.1}"
CHECK_HOSTS="8.8.8.8 1.1.1.1 google.com"
PING_TIMEOUT=3
PING_COUNT=1

# State file to track mode
STATE_FILE="/tmp/photobooth-network-mode"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[NET]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if we have internet connectivity
check_internet() {
    for host in $CHECK_HOSTS; do
        if ping -c $PING_COUNT -W $PING_TIMEOUT "$host" &>/dev/null; then
            return 0
        fi
    done
    return 1
}

# Get current network mode
get_current_mode() {
    if systemctl is-active --quiet hostapd && systemctl is-active --quiet dnsmasq; then
        echo "ap"
    elif ip addr show wlan0 2>/dev/null | grep -q "inet.*192.168.4.1"; then
        echo "ap"
    else
        echo "client"
    fi
}

# Switch to AP mode (offline/on-premise mode)
enable_ap_mode() {
    log "Switching to AP mode..."

    # Stop wpa_supplicant if running
    systemctl stop wpa_supplicant 2>/dev/null || true

    # Configure static IP for wlan0 if not already
    if ! grep -q "# PhotoBooth Wi-Fi AP" /etc/dhcpcd.conf 2>/dev/null; then
        log "Configuring static IP..."
        cat >> /etc/dhcpcd.conf << EOF

# PhotoBooth Wi-Fi AP Static IP Configuration
interface wlan0
    static ip_address=${PI_IP}/24
    nohook wpa_supplicant
EOF
    fi

    # Restart dhcpcd to apply static IP
    systemctl restart dhcpcd
    sleep 3

    # Start AP services
    log "Starting hostapd..."
    systemctl unmask hostapd 2>/dev/null || true
    systemctl start hostapd

    log "Starting dnsmasq..."
    systemctl start dnsmasq

    # Wait for services to stabilize
    sleep 2

    # Verify
    if systemctl is-active --quiet hostapd && systemctl is-active --quiet dnsmasq; then
        log_ok "AP mode enabled"
        log_ok "SSID: $WIFI_SSID"
        log_ok "IP: $PI_IP"
        echo "ap" > "$STATE_FILE"
        return 0
    else
        log_error "Failed to enable AP mode"
        systemctl status hostapd --no-pager -l 2>/dev/null | head -10 || true
        return 1
    fi
}

# Switch to client mode (online/development mode)
enable_client_mode() {
    log "Switching to client mode..."

    # Stop AP services
    systemctl stop hostapd 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true

    # Remove static IP configuration (comment it out)
    if grep -q "# PhotoBooth Wi-Fi AP" /etc/dhcpcd.conf 2>/dev/null; then
        log "Removing static IP configuration..."
        sed -i '/# PhotoBooth Wi-Fi AP/,/nohook wpa_supplicant/d' /etc/dhcpcd.conf
    fi

    # Restart dhcpcd to get DHCP
    systemctl restart dhcpcd

    # Start wpa_supplicant
    systemctl start wpa_supplicant 2>/dev/null || true

    # Wait for IP assignment
    log "Waiting for IP assignment..."
    for i in {1..30}; do
        if ip addr show wlan0 2>/dev/null | grep -q "inet " && \
           ! ip addr show wlan0 2>/dev/null | grep -q "192.168.4.1"; then
            local ip
            ip=$(ip addr show wlan0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
            log_ok "Client mode enabled"
            log_ok "IP: $ip"
            echo "client" > "$STATE_FILE"
            return 0
        fi
        sleep 1
    done

    log_warn "Could not get IP in client mode"
    return 1
}

# Show current status
show_status() {
    local mode
    mode=$(get_current_mode)

    echo ""
    echo "=== Network Mode Status ==="
    echo ""
    echo "Current mode: $mode"
    echo ""

    if [[ "$mode" == "ap" ]]; then
        echo "AP Mode Settings:"
        echo "  SSID: $WIFI_SSID"
        echo "  IP: $PI_IP"
        echo ""
        echo "Services:"
        echo "  hostapd: $(systemctl is-active hostapd 2>/dev/null || echo 'inactive')"
        echo "  dnsmasq: $(systemctl is-active dnsmasq 2>/dev/null || echo 'inactive')"
    else
        echo "Client Mode:"
        local ip
        ip=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1 || echo "none")
        echo "  IP: $ip"
        echo "  Internet: $(check_internet && echo 'available' || echo 'not available')"
    fi
    echo ""

    echo "Interface wlan0:"
    ip addr show wlan0 2>/dev/null | grep -E "inet|state" || echo "  not found"
    echo ""
}

# Auto-detect and switch mode
auto_switch() {
    local current_mode
    current_mode=$(get_current_mode)

    log "Current mode: $current_mode"
    log "Checking internet connectivity..."

    if check_internet; then
        log_ok "Internet available"

        if [[ "$current_mode" == "ap" ]]; then
            log "Internet detected but in AP mode"
            log "Keeping AP mode (manual switch required to change)"
            # Don't auto-switch from AP to client to avoid disrupting connected devices
        else
            log_ok "Already in client mode with internet"
        fi
    else
        log_warn "No internet"

        if [[ "$current_mode" == "client" ]]; then
            log "No internet in client mode, switching to AP mode..."
            enable_ap_mode
        else
            log_ok "Already in AP mode"
        fi
    fi
}

# Main
main() {
    # Check root for mode changes
    if [[ "${1:-}" != "--status" ]] && [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi

    case "${1:-}" in
        --force-ap)
            enable_ap_mode
            ;;
        --force-client)
            enable_client_mode
            ;;
        --status)
            show_status
            ;;
        --auto|"")
            auto_switch
            ;;
        -h|--help)
            echo "Usage: $0 [--force-ap|--force-client|--status|--auto]"
            echo ""
            echo "Options:"
            echo "  --force-ap      Force AP mode (offline)"
            echo "  --force-client  Force client mode (needs existing Wi-Fi config)"
            echo "  --status        Show current network status"
            echo "  --auto          Auto-detect and switch (default)"
            echo ""
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
}

main "$@"
