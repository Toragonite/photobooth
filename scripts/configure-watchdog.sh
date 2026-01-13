#!/bin/bash
#
# Hardware Watchdog Configuration for Raspberry Pi 5
# Enables the hardware watchdog timer to automatically reboot on system hang
#
# Usage: sudo ./configure-watchdog.sh
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}This script must be run as root (use sudo)${NC}"
        exit 1
    fi
}

log() {
    echo -e "${BLUE}[CONFIG]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        warn "Not running on Raspberry Pi - some features may not work"
    fi
}

# Load watchdog kernel module
load_watchdog_module() {
    log "Loading watchdog kernel module..."

    # Add to modules for boot
    if ! grep -q "bcm2835_wdt" /etc/modules 2>/dev/null; then
        echo "bcm2835_wdt" >> /etc/modules
    fi

    # Load immediately
    modprobe bcm2835_wdt 2>/dev/null || true

    # Check if loaded
    if lsmod | grep -q bcm2835_wdt 2>/dev/null; then
        success "Watchdog module loaded"
    else
        warn "Could not verify watchdog module (may work after reboot)"
    fi
}

# Install watchdog daemon
install_watchdog() {
    log "Installing watchdog daemon..."

    apt-get update -qq
    apt-get install -y watchdog

    success "Watchdog daemon installed"
}

# Configure watchdog daemon
configure_watchdog() {
    log "Configuring watchdog daemon..."

    local config_file="/etc/watchdog.conf"

    # Backup original
    if [[ -f "$config_file" ]] && [[ ! -f "${config_file}.orig" ]]; then
        cp "$config_file" "${config_file}.orig"
    fi

    cat > "$config_file" << 'EOF'
# PhotoBooth Hardware Watchdog Configuration
#
# This configuration monitors system health and triggers a hardware
# reset if the system becomes unresponsive.

# Watchdog device
watchdog-device = /dev/watchdog

# Watchdog timeout in seconds
# If not reset within this time, hardware reboot occurs
watchdog-timeout = 15

# Check interval in seconds
interval = 10

# Maximum load average for 1 minute
# Reboot if load exceeds this for sustained period
max-load-1 = 24

# Minimum free memory in pages (1 page = 4KB)
# Reboot if free memory drops below this
min-memory = 1

# Ping test - check network connectivity (optional)
# Uncomment to enable
#ping = 192.168.4.1

# File to check for existence
# Reboot if file disappears
#file = /var/run/photobooth.pid

# Test binary to run
# Reboot if test returns non-zero
#test-binary = /home/pi/photobooth/scripts/watchdog-test.sh

# Repair binary to run before reboot
#repair-binary = /home/pi/photobooth/scripts/watchdog-repair.sh

# Log watchdog messages
log-dir = /var/log/watchdog

# Realtime scheduling priority
realtime = yes
priority = 1

# Allocate memory to lock into RAM
allocate-memory = yes
EOF

    # Create log directory
    mkdir -p /var/log/watchdog

    success "Watchdog configured"
}

# Enable and start watchdog service
enable_watchdog() {
    log "Enabling watchdog service..."

    systemctl daemon-reload
    systemctl enable watchdog
    systemctl start watchdog

    # Verify running
    if systemctl is-active --quiet watchdog; then
        success "Watchdog service started"
    else
        warn "Watchdog service may not be running"
        journalctl -u watchdog -n 10 --no-pager
    fi
}

# Test watchdog (optional)
test_watchdog() {
    log "Testing watchdog device..."

    if [[ -c /dev/watchdog ]]; then
        success "Watchdog device exists: /dev/watchdog"
    else
        warn "Watchdog device not found"
    fi

    # Check if watchdog is being serviced
    if [[ -f /var/run/watchdog.pid ]]; then
        success "Watchdog daemon is running (PID: $(cat /var/run/watchdog.pid))"
    fi
}

# Print summary
print_summary() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo "Hardware Watchdog Configuration Complete"
    echo "==========================================${NC}"
    echo ""
    echo "Configuration:"
    echo "  - Timeout: 15 seconds"
    echo "  - Check interval: 10 seconds"
    echo "  - Max load: 24"
    echo "  - Min memory: 4KB (1 page)"
    echo ""
    echo "The hardware watchdog will automatically reboot the system if:"
    echo "  - The watchdog daemon stops responding"
    echo "  - System load exceeds threshold for extended period"
    echo "  - Available memory drops critically low"
    echo ""
    echo "To check watchdog status:"
    echo "  systemctl status watchdog"
    echo ""
    echo -e "${YELLOW}WARNING: Do not manually write to /dev/watchdog${NC}"
    echo "  This could trigger an immediate reboot!"
    echo ""
}

# Main
main() {
    echo -e "${BLUE}=========================================="
    echo "Hardware Watchdog Configuration"
    echo "==========================================${NC}"
    echo ""

    check_root
    check_raspberry_pi
    load_watchdog_module
    install_watchdog
    configure_watchdog
    enable_watchdog
    test_watchdog
    print_summary
}

main "$@"
