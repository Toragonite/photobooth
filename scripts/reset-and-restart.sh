#!/bin/bash
#
# PhotoBooth Reset and Restart Script
# Quick reset for already-installed systems
#
# Usage: sudo ./reset-and-restart.sh [OPTIONS]
#
# Options:
#   --soft       Restart services only (no container rebuild)
#   --hard       Full rebuild (rebuild containers, reset DB)
#   --printer    Reconfigure printer only
#   --network    Reconfigure Wi-Fi AP only
#   --all        Full reset (default)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/toragonite/Documents/photobooth}"
PRINTER_NAME="${PRINTER_NAME:-SelphyCP1500}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[RESET]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================
# Soft reset - just restart services
# ============================================
soft_reset() {
    log "Performing soft reset..."

    # Restart Docker containers
    log "Restarting containers..."
    cd "$PHOTOBOOTH_DIR"
    docker compose restart

    # Wait for health
    log "Waiting for services..."
    sleep 10

    # Check health
    if curl -sf http://localhost:8000/api/health &>/dev/null; then
        log_ok "Backend healthy"
    else
        log_warn "Backend may not be ready"
    fi

    log_ok "Soft reset complete"
}

# ============================================
# Hard reset - rebuild everything
# ============================================
hard_reset() {
    log "Performing hard reset..."

    cd "$PHOTOBOOTH_DIR"

    # Stop and remove containers
    log "Stopping containers..."
    docker compose down -v

    # Rebuild
    log "Rebuilding containers..."
    docker compose build --no-cache

    # Start
    log "Starting containers..."
    docker compose up -d

    # Wait for health
    log "Waiting for services..."
    sleep 15

    if curl -sf http://localhost:8000/api/health &>/dev/null; then
        log_ok "Backend healthy"
    else
        log_warn "Backend may not be ready"
    fi

    log_ok "Hard reset complete"
}

# ============================================
# Printer reset
# ============================================
printer_reset() {
    log "Resetting printer configuration..."

    # Check usblp
    if lsmod | grep -q usblp; then
        log "Removing usblp module..."
        rmmod usblp 2>/dev/null || true
    fi

    # Ensure blacklist exists
    if [[ ! -f /etc/modprobe.d/blacklist-usblp.conf ]]; then
        log "Creating usblp blacklist..."
        echo "blacklist usblp" > /etc/modprobe.d/blacklist-usblp.conf
        update-initramfs -u 2>/dev/null || true
    fi

    # Restart CUPS
    log "Restarting CUPS..."
    systemctl restart cups
    sleep 3

    # Check if printer exists
    if lpstat -p "$PRINTER_NAME" &>/dev/null; then
        log "Printer $PRINTER_NAME found, re-enabling..."
        cupsenable "$PRINTER_NAME" 2>/dev/null || true
        cupsaccept "$PRINTER_NAME" 2>/dev/null || true
    else
        log_warn "Printer $PRINTER_NAME not configured"
        log "Run: sudo $SCRIPT_DIR/setup.sh --phase 05-printer"
    fi

    # Show status
    log "Printer status:"
    lpstat -p 2>/dev/null || echo "  No printers"

    log_ok "Printer reset complete"
    log ""
    log "If printer still not working, try:"
    log "  1. Unplug and replug USB cable"
    log "  2. Power cycle the printer"
}

# ============================================
# Network reset
# ============================================
network_reset() {
    log "Resetting network configuration..."

    if [[ -f "$SCRIPT_DIR/network/reset-network.sh" ]]; then
        bash "$SCRIPT_DIR/network/reset-network.sh"
    else
        log "Restarting network services..."
        systemctl restart hostapd 2>/dev/null || log_warn "hostapd not installed"
        systemctl restart dnsmasq 2>/dev/null || log_warn "dnsmasq not installed"
    fi

    log_ok "Network reset complete"
}

# ============================================
# Full reset
# ============================================
full_reset() {
    log "Performing full reset..."

    # Update from git if possible
    cd "$PHOTOBOOTH_DIR"
    if [[ -d .git ]] && ping -c 1 -W 2 github.com &>/dev/null; then
        log "Updating from git..."
        git stash 2>/dev/null || true
        git pull origin master 2>/dev/null || true
    fi

    # Printer
    printer_reset

    # Hard reset containers
    hard_reset

    # Restart systemd services
    log "Reloading systemd..."
    systemctl daemon-reload
    systemctl restart photobooth 2>/dev/null || true

    # Network
    network_reset

    log_ok "Full reset complete"
}

# ============================================
# Show status
# ============================================
show_status() {
    echo ""
    echo "=== PhotoBooth Status ==="
    echo ""

    # Docker
    echo "Docker containers:"
    cd "$PHOTOBOOTH_DIR"
    docker compose ps 2>/dev/null || echo "  Not running"
    echo ""

    # Services
    echo "Systemd services:"
    for svc in photobooth cups hostapd dnsmasq; do
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            echo "  $svc: active"
        else
            echo "  $svc: inactive"
        fi
    done
    echo ""

    # Printer
    echo "Printer:"
    lpstat -p "$PRINTER_NAME" 2>/dev/null || echo "  $PRINTER_NAME not configured"
    echo ""

    # Network
    echo "Network:"
    ip addr show wlan0 2>/dev/null | grep "inet " || echo "  wlan0 not configured"
    echo ""
}

# ============================================
# Usage
# ============================================
usage() {
    cat << EOF
PhotoBooth Reset and Restart Script

Usage: sudo $0 [OPTIONS]

Options:
    --soft       Restart services only (quick)
    --hard       Rebuild containers completely
    --printer    Reset printer configuration
    --network    Reset Wi-Fi AP configuration
    --all        Full reset (default)
    --status     Show current status
    -h, --help   Show this help

Examples:
    sudo $0              # Full reset
    sudo $0 --soft       # Quick restart
    sudo $0 --printer    # Fix printer issues
    sudo $0 --status     # Check status

EOF
    exit 0
}

# ============================================
# Main
# ============================================
main() {
    # Check root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi

    # Parse arguments
    local mode="all"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --soft)     mode="soft"; shift ;;
            --hard)     mode="hard"; shift ;;
            --printer)  mode="printer"; shift ;;
            --network)  mode="network"; shift ;;
            --all)      mode="all"; shift ;;
            --status)   show_status; exit 0 ;;
            -h|--help)  usage ;;
            *)          log_error "Unknown option: $1"; usage ;;
        esac
    done

    echo ""
    echo "=== PhotoBooth Reset ==="
    echo "Mode: $mode"
    echo ""

    case "$mode" in
        soft)    soft_reset ;;
        hard)    hard_reset ;;
        printer) printer_reset ;;
        network) network_reset ;;
        all)     full_reset ;;
    esac

    echo ""
    show_status
}

main "$@"
