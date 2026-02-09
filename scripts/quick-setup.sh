#!/bin/bash
#
# PhotoBooth Quick Setup Script
# One-click setup for fresh Raspberry Pi installation
#
# Usage: curl -sSL <url>/quick-setup.sh | sudo bash
#    or: sudo ./quick-setup.sh
#
# This script:
#   1. Clones/updates the photobooth repository
#   2. Runs the full setup process
#   3. Configures all services
#
# Tested on: Raspberry Pi 5 (8GB), Raspberry Pi OS (64-bit)
#

set -euo pipefail

# ============================================
# Configuration
# ============================================
REPO_URL="https://github.com/toragonite/photobooth.git"
INSTALL_DIR="/home/toragonite/Documents/photobooth"
BRANCH="${BRANCH:-master}"
USER_NAME="${USER_NAME:-toragonite}"

# Wi-Fi AP settings
export WIFI_SSID="${WIFI_SSID:-photobooth}"
export WIFI_PASSWORD="${WIFI_PASSWORD:-photobooth-1998}"
export WIFI_CHANNEL="${WIFI_CHANNEL:-6}"
export PI_IP="${PI_IP:-192.168.4.1}"

# System settings
export TIMEZONE="${TIMEZONE:-Africa/Kigali}"
export COUNTRY_CODE="${COUNTRY_CODE:-RW}"
export PRINTER_NAME="${PRINTER_NAME:-SelphyCP1500}"

# ============================================
# Colors
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================
# Helper functions
# ============================================
log() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

header() {
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo ""
}

# ============================================
# Pre-flight checks
# ============================================
preflight_checks() {
    header "Pre-flight Checks"

    # Check root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    log_ok "Running as root"

    # Check Raspberry Pi
    if [[ -f /proc/cpuinfo ]] && grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        local model
        model=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs)
        log_ok "Detected: $model"
    else
        log_warn "Not detected as Raspberry Pi - some features may not work"
    fi

    # Check user exists
    if ! id "$USER_NAME" &>/dev/null; then
        log "Creating user $USER_NAME..."
        useradd -m -s /bin/bash "$USER_NAME"
        usermod -aG sudo "$USER_NAME"
    fi
    log_ok "User $USER_NAME exists"

    # Check internet (for initial setup)
    if ping -c 1 -W 3 8.8.8.8 &>/dev/null; then
        log_ok "Internet connection available"
    else
        log_warn "No internet - will use local files only"
    fi

    # Check disk space
    local free_space
    free_space=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
    if [[ $free_space -lt 5 ]]; then
        log_warn "Low disk space: ${free_space}GB free"
    else
        log_ok "Disk space: ${free_space}GB free"
    fi
}

# ============================================
# Get/Update repository
# ============================================
setup_repository() {
    header "Setting Up Repository"

    # Create parent directory
    mkdir -p "$(dirname "$INSTALL_DIR")"

    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log "Repository exists, updating..."
        cd "$INSTALL_DIR"

        # Stash any local changes
        git stash 2>/dev/null || true

        # Pull latest
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"

        log_ok "Repository updated"
    else
        log "Cloning repository..."

        if ping -c 1 -W 3 github.com &>/dev/null; then
            git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
            log_ok "Repository cloned"
        else
            log_error "Cannot clone repository - no internet"
            log "Please copy the photobooth directory to $INSTALL_DIR manually"
            exit 1
        fi
    fi

    # Set ownership
    chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR"
}

# ============================================
# Run main setup
# ============================================
run_setup() {
    header "Running Main Setup"

    cd "$INSTALL_DIR/scripts"

    # Make scripts executable
    chmod +x *.sh
    chmod +x setup-phases/*.sh 2>/dev/null || true
    chmod +x network/*.sh 2>/dev/null || true

    # Export variables for setup phases
    export PHOTOBOOTH_DIR="$INSTALL_DIR"

    # Run the master setup script
    if [[ -f "setup.sh" ]]; then
        log "Running setup.sh..."
        bash setup.sh
    else
        log_error "setup.sh not found!"
        exit 1
    fi
}

# ============================================
# Post-setup verification
# ============================================
verify_setup() {
    header "Verifying Setup"

    local errors=0

    # Check Docker
    if docker info &>/dev/null; then
        log_ok "Docker is running"
    else
        log_error "Docker is not running"
        ((errors++))
    fi

    # Check CUPS
    if systemctl is-active --quiet cups; then
        log_ok "CUPS is running"
    else
        log_warn "CUPS is not running"
    fi

    # Check usblp blacklist
    if [[ -f /etc/modprobe.d/blacklist-usblp.conf ]]; then
        log_ok "usblp blacklist configured"
    else
        log_warn "usblp blacklist not configured"
    fi

    # Check printer
    if lpstat -p "$PRINTER_NAME" &>/dev/null; then
        log_ok "Printer $PRINTER_NAME configured"
    else
        log_warn "Printer $PRINTER_NAME not configured"
        log "  Connect printer and run: sudo $INSTALL_DIR/scripts/setup.sh --phase 05-printer"
    fi

    # Check photobooth service
    if systemctl is-active --quiet photobooth; then
        log_ok "PhotoBooth service is running"
    else
        log_warn "PhotoBooth service is not running"
    fi

    # Check containers
    cd "$INSTALL_DIR"
    local running
    running=$(docker compose ps --format "{{.State}}" 2>/dev/null | grep -c "running" || echo "0")
    if [[ $running -gt 0 ]]; then
        log_ok "Docker containers running: $running"
    else
        log_warn "No Docker containers running"
    fi

    # Check welcome-print service
    if systemctl is-enabled --quiet photobooth-welcome-print 2>/dev/null; then
        log_ok "Welcome print service enabled"
    else
        log_warn "Welcome print service not enabled"
    fi

    return $errors
}

# ============================================
# Print summary
# ============================================
print_summary() {
    header "Setup Complete!"

    echo "PhotoBooth has been installed to: $INSTALL_DIR"
    echo ""
    echo "Network Configuration:"
    echo "  Wi-Fi SSID:     $WIFI_SSID"
    echo "  Wi-Fi Password: $WIFI_PASSWORD"
    echo "  Pi IP Address:  $PI_IP"
    echo ""
    echo "Access Points:"
    echo "  Web App:  https://$PI_IP"
    echo "  Admin:    https://$PI_IP/admin"
    echo "  CUPS:     http://$PI_IP:631"
    echo ""
    echo "Useful Commands:"
    echo "  Status:   sudo systemctl status photobooth"
    echo "  Logs:     journalctl -u photobooth -f"
    echo "  Restart:  sudo systemctl restart photobooth"
    echo "  Control:  $INSTALL_DIR/scripts/photobooth-ctl.sh"
    echo ""
    echo -e "${YELLOW}IMPORTANT:${NC}"
    echo "  1. Reboot the Raspberry Pi: sudo reboot"
    echo "  2. After reboot, connect to Wi-Fi: $WIFI_SSID"
    echo "  3. Open browser: https://$PI_IP"
    echo ""
    echo "  If printer was connected during setup, unplug and replug USB"
    echo "  for the usblp blacklist to take effect."
    echo ""
}

# ============================================
# Main
# ============================================
main() {
    header "PhotoBooth Quick Setup"
    echo "Version: 1.0"
    echo "Target:  $INSTALL_DIR"
    echo ""

    preflight_checks
    setup_repository
    run_setup

    if verify_setup; then
        print_summary
    else
        log_warn "Setup completed with warnings"
        print_summary
    fi
}

# Run main
main "$@"
