#!/bin/bash
#
# Phase 01: System Updates and Configuration
# Updates system packages, sets timezone and locale
#

set -euo pipefail

source "$(dirname "$0")/../setup-lib.sh" 2>/dev/null || true

echo "[01-system] Starting system configuration..."

# Update package lists
echo "Updating package lists..."
apt-get update -qq

# Upgrade installed packages
echo "Upgrading packages..."
apt-get upgrade -y -qq

# Install essential packages
echo "Installing essential packages..."
apt-get install -y -qq \
    curl \
    wget \
    git \
    vim \
    htop \
    jq \
    sqlite3 \
    ufw \
    unzip \
    rsync

# Set timezone
TIMEZONE="${TIMEZONE:-Africa/Kigali}"
echo "Setting timezone to $TIMEZONE..."
timedatectl set-timezone "$TIMEZONE"

# Set locale
echo "Configuring locale..."
if ! locale -a | grep -q "en_US.utf8"; then
    sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
    locale-gen
fi
update-locale LANG=en_US.UTF-8

# Set hostname
HOSTNAME="${HOSTNAME:-photobooth}"
echo "Setting hostname to $HOSTNAME..."
hostnamectl set-hostname "$HOSTNAME"

# Update /etc/hosts
if ! grep -q "$HOSTNAME" /etc/hosts; then
    echo "127.0.1.1 $HOSTNAME" >> /etc/hosts
fi

# Configure Wi-Fi country code
COUNTRY_CODE="${COUNTRY_CODE:-RW}"
echo "Setting Wi-Fi country code to $COUNTRY_CODE..."
raspi-config nonint do_wifi_country "$COUNTRY_CODE" 2>/dev/null || true

# Enable required interfaces
echo "Enabling required interfaces..."
raspi-config nonint do_i2c 0 2>/dev/null || true  # Enable I2C
raspi-config nonint do_camera 0 2>/dev/null || true  # Enable camera (legacy)

# Disable unnecessary services
echo "Disabling unnecessary services..."
systemctl disable bluetooth.service 2>/dev/null || true
systemctl stop bluetooth.service 2>/dev/null || true

# Configure kernel parameters for stability
echo "Configuring kernel parameters..."
cat > /etc/sysctl.d/99-photobooth.conf << 'EOF'
# PhotoBooth system optimizations

# Network
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 1024

# Memory
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2

# File system
fs.file-max = 65535
fs.inotify.max_user_watches = 524288
EOF

sysctl -p /etc/sysctl.d/99-photobooth.conf 2>/dev/null || true

echo "[01-system] System configuration complete"
