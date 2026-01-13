#!/bin/bash
#
# SD Card Corruption Prevention for Raspberry Pi 5
# Reduces write operations to extend SD card life and prevent corruption
#
# Usage: sudo ./configure-sd-protection.sh
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

# Disable swap to reduce writes
disable_swap() {
    log "Disabling swap..."

    if command -v dphys-swapfile &> /dev/null; then
        dphys-swapfile swapoff 2>/dev/null || true
        dphys-swapfile uninstall 2>/dev/null || true
        systemctl disable dphys-swapfile 2>/dev/null || true
        success "Swap disabled"
    else
        warn "dphys-swapfile not found, skipping"
    fi
}

# Configure aggressive log rotation
configure_logrotate() {
    log "Configuring log rotation..."

    mkdir -p /etc/logrotate.d

    cat > /etc/logrotate.d/photobooth << 'EOF'
/var/log/photobooth-*.log {
    size 1M
    rotate 2
    missingok
    notifempty
    compress
    delaycompress
    copytruncate
}
EOF

    success "Log rotation configured"
}

# Configure journald for volatile storage
configure_journald() {
    log "Configuring journald for volatile storage..."

    mkdir -p /etc/systemd/journald.conf.d/

    cat > /etc/systemd/journald.conf.d/volatile.conf << 'EOF'
[Journal]
Storage=volatile
RuntimeMaxUse=30M
RuntimeMaxFileSize=5M
ForwardToSyslog=no
EOF

    systemctl restart systemd-journald 2>/dev/null || true
    success "Journald configured for volatile storage"
}

# Configure Docker logging
configure_docker_logging() {
    log "Configuring Docker log limits..."

    mkdir -p /etc/docker

    # Check if daemon.json exists and merge, or create new
    if [[ -f /etc/docker/daemon.json ]]; then
        # Backup existing
        cp /etc/docker/daemon.json /etc/docker/daemon.json.bak

        # Use jq if available, otherwise replace
        if command -v jq &> /dev/null; then
            jq '. + {"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' \
                /etc/docker/daemon.json.bak > /etc/docker/daemon.json
        else
            warn "jq not available, replacing daemon.json"
            cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF
        fi
    else
        cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF
    fi

    # Restart Docker if running
    if systemctl is-active --quiet docker 2>/dev/null; then
        systemctl restart docker 2>/dev/null || true
    fi

    success "Docker logging configured"
}

# Configure filesystem write behavior
configure_filesystem() {
    log "Configuring filesystem write behavior..."

    local sysctl_file="/etc/sysctl.d/99-sd-card.conf"

    cat > "$sysctl_file" << 'EOF'
# SD Card Protection Settings
# Increase dirty writeback time (default is 500 centisecs = 5 seconds)
# Set to 6000 centisecs = 60 seconds
vm.dirty_writeback_centisecs = 6000

# Increase dirty expire time (default is 3000 centisecs = 30 seconds)
# Set to 6000 centisecs = 60 seconds
vm.dirty_expire_centisecs = 6000

# Reduce swappiness (less swap usage even if swap exists)
vm.swappiness = 10
EOF

    # Apply immediately
    sysctl -p "$sysctl_file" 2>/dev/null || true

    success "Filesystem write behavior configured"
}

# Configure tmpfs mounts for temporary files
configure_tmpfs() {
    log "Configuring tmpfs mounts..."

    local fstab="/etc/fstab"
    local marker="# PhotoBooth SD Protection"

    # Check if already configured
    if grep -q "$marker" "$fstab" 2>/dev/null; then
        warn "tmpfs already configured in fstab, skipping"
        return
    fi

    # Backup fstab
    cp "$fstab" "${fstab}.bak"

    # Add tmpfs entries
    cat >> "$fstab" << 'EOF'

# PhotoBooth SD Protection - tmpfs mounts
tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100M 0 0
tmpfs /var/tmp tmpfs defaults,noatime,nosuid,size=50M 0 0
EOF

    success "tmpfs mounts configured (will take effect after reboot)"
}

# Configure noatime mount option
configure_noatime() {
    log "Checking noatime mount option..."

    local fstab="/etc/fstab"

    # Check if root filesystem already has noatime
    if grep -E "^\s*[^#].*\s+/\s+" "$fstab" | grep -q "noatime"; then
        success "Root filesystem already has noatime"
        return
    fi

    warn "Consider adding 'noatime' to root filesystem mount options manually"
    echo "  Edit /etc/fstab and add 'noatime' to the options for /"
}

# Print summary
print_summary() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo "SD Card Protection Configuration Complete"
    echo "==========================================${NC}"
    echo ""
    echo "Changes made:"
    echo "  - Swap disabled"
    echo "  - Log rotation configured (max 1MB, 2 rotations)"
    echo "  - Journald set to volatile storage (30MB max)"
    echo "  - Docker logs limited (10MB x 3 files)"
    echo "  - Filesystem writes delayed (60 second writeback)"
    echo "  - tmpfs configured for /tmp and /var/tmp"
    echo ""
    echo -e "${YELLOW}NOTE: Some changes require a reboot to take effect.${NC}"
    echo ""
    echo "To verify after reboot:"
    echo "  - Check swap: free -h"
    echo "  - Check mounts: df -h | grep tmpfs"
    echo "  - Check journald: journalctl --disk-usage"
    echo ""
}

# Main
main() {
    echo -e "${BLUE}=========================================="
    echo "SD Card Protection Configuration"
    echo "==========================================${NC}"
    echo ""

    check_root
    disable_swap
    configure_logrotate
    configure_journald
    configure_docker_logging
    configure_filesystem
    configure_tmpfs
    configure_noatime
    print_summary
}

main "$@"
