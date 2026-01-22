#!/bin/bash
#
# PhotoBooth Auto Network Mode (NetworkManager version)
# Automatically switches between AP mode (offline) and Client mode (online)
#
# Usage:
#   ./auto-network-mode.sh          # Check and switch if needed
#   ./auto-network-mode.sh --force-ap    # Force AP mode
#   ./auto-network-mode.sh --force-client # Force client mode
#   ./auto-network-mode.sh --status      # Show current mode
#

set -euo pipefail

# Configuration
WIFI_SSID="${WIFI_SSID:-photobooth}"
WIFI_PASSWORD="${WIFI_PASSWORD:-photobooth-1998}"
PI_IP="${PI_IP:-192.168.4.1}"
WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
AP_CONNECTION_NAME="photobooth-ap"
CHECK_HOSTS="8.8.8.8 1.1.1.1"
PING_TIMEOUT=3
PING_COUNT=1

# State file
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
    # Check if AP mode connection is active
    if nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null | grep -q "$AP_CONNECTION_NAME"; then
        echo "ap"
    elif systemctl is-active --quiet hostapd 2>/dev/null; then
        echo "ap"
    elif ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep -q "inet $PI_IP"; then
        echo "ap"
    else
        echo "client"
    fi
}

# Create AP connection profile if not exists
create_ap_profile() {
    # Check if profile already exists
    if nmcli connection show "$AP_CONNECTION_NAME" &>/dev/null; then
        log "AP profile already exists"
        return 0
    fi

    log "Creating AP connection profile..."

    nmcli connection add \
        type wifi \
        ifname "$WIFI_INTERFACE" \
        con-name "$AP_CONNECTION_NAME" \
        autoconnect no \
        ssid "$WIFI_SSID" \
        mode ap \
        ipv4.method shared \
        ipv4.addresses "$PI_IP/24" \
        wifi-sec.key-mgmt wpa-psk \
        wifi-sec.psk "$WIFI_PASSWORD"

    log_ok "AP profile created"
}

# Switch to AP mode (offline/on-premise mode)
enable_ap_mode() {
    log "Switching to AP mode..."

    # Create AP profile if needed
    create_ap_profile

    # Stop any existing wifi connection
    log "Disconnecting current wifi..."
    nmcli device disconnect "$WIFI_INTERFACE" 2>/dev/null || true
    sleep 2

    # Bring up AP connection
    log "Starting AP mode..."
    if nmcli connection up "$AP_CONNECTION_NAME" 2>/dev/null; then
        log_ok "AP mode enabled via NetworkManager"
    else
        log_warn "NetworkManager AP failed, trying hostapd fallback..."
        enable_ap_hostapd
        return $?
    fi

    # Start dnsmasq for DHCP if not using NM's shared mode
    # NetworkManager's "shared" mode handles DHCP automatically

    sleep 3

    # Verify
    if ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep -q "$PI_IP"; then
        log_ok "AP mode active"
        log_ok "SSID: $WIFI_SSID"
        log_ok "IP: $PI_IP"
        echo "ap" > "$STATE_FILE"
        return 0
    else
        log_error "Failed to enable AP mode"
        return 1
    fi
}

# Fallback: Use hostapd directly
enable_ap_hostapd() {
    log "Using hostapd fallback..."

    # Check if hostapd config exists
    if [[ ! -f /etc/hostapd/hostapd.conf ]]; then
        log_error "hostapd.conf not found. Run setup first."
        return 1
    fi

    # Disconnect NetworkManager from wlan0
    nmcli device set "$WIFI_INTERFACE" managed no 2>/dev/null || true
    sleep 1

    # Set static IP
    ip addr flush dev "$WIFI_INTERFACE" 2>/dev/null || true
    ip addr add "$PI_IP/24" dev "$WIFI_INTERFACE" 2>/dev/null || true
    ip link set "$WIFI_INTERFACE" up

    # Start hostapd
    systemctl unmask hostapd 2>/dev/null || true
    systemctl start hostapd

    # Start dnsmasq
    systemctl start dnsmasq 2>/dev/null || true

    sleep 2

    if systemctl is-active --quiet hostapd; then
        log_ok "AP mode enabled via hostapd"
        echo "ap" > "$STATE_FILE"
        return 0
    else
        log_error "hostapd failed to start"
        systemctl status hostapd --no-pager -l 2>/dev/null | head -10 || true
        return 1
    fi
}

# Switch to client mode (online/development mode)
enable_client_mode() {
    log "Switching to client mode..."

    # Stop hostapd if running
    systemctl stop hostapd 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true

    # Disconnect AP connection
    nmcli connection down "$AP_CONNECTION_NAME" 2>/dev/null || true

    # Re-enable NetworkManager management of wlan0
    nmcli device set "$WIFI_INTERFACE" managed yes 2>/dev/null || true
    sleep 1

    # Let NetworkManager auto-connect to known networks
    log "Reconnecting to available networks..."
    nmcli device connect "$WIFI_INTERFACE" 2>/dev/null || true

    # Wait for connection
    log "Waiting for IP assignment..."
    for i in {1..30}; do
        if ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep -q "inet " && \
           ! ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep -q "$PI_IP"; then
            local ip
            ip=$(ip addr show "$WIFI_INTERFACE" | grep "inet " | awk '{print $2}' | cut -d/ -f1)
            log_ok "Client mode enabled"
            log_ok "IP: $ip"
            echo "client" > "$STATE_FILE"
            return 0
        fi
        sleep 1
    done

    log_warn "Could not get IP in client mode"
    log "Tip: Check if a wifi network is saved with 'nmcli connection show'"
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

    echo "NetworkManager connections:"
    nmcli connection show 2>/dev/null | head -10
    echo ""

    echo "Active connections:"
    nmcli connection show --active 2>/dev/null
    echo ""

    echo "Device status:"
    nmcli device status 2>/dev/null
    echo ""

    if [[ "$mode" == "ap" ]]; then
        echo "AP Mode Settings:"
        echo "  SSID: $WIFI_SSID"
        echo "  Password: $WIFI_PASSWORD"
        echo "  IP: $PI_IP"
    else
        echo "Client Mode:"
        local ip
        ip=$(ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1 || echo "none")
        echo "  IP: $ip"
        echo "  Internet: $(check_internet && echo 'available' || echo 'not available')"
    fi
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
            log "Internet detected but in AP mode - keeping AP mode"
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
            echo "  --force-client  Force client mode (needs saved Wi-Fi)"
            echo "  --status        Show current network status"
            echo "  --auto          Auto-detect and switch (default)"
            echo ""
            echo "AP Settings:"
            echo "  SSID: $WIFI_SSID"
            echo "  Password: $WIFI_PASSWORD"
            echo "  IP: $PI_IP"
            echo ""
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
}

main "$@"
