#!/bin/bash
#
# Phase 08: Security Hardening
# Configures firewall and security settings
#

set -euo pipefail

echo "[08-security] Starting security hardening..."

PI_IP="${PI_IP:-192.168.4.1}"
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/toragonite/Documents/photobooth}"

# Configure UFW firewall
configure_firewall() {
    echo "Configuring firewall (ufw)..."

    # Install ufw if not present
    if ! command -v ufw &>/dev/null; then
        apt-get install -y -qq ufw
    fi

    # Reset UFW to defaults
    ufw --force reset

    # Default policies
    ufw default deny incoming
    ufw default allow outgoing

    # Allow SSH (for remote management)
    echo "  Allowing SSH (port 22)..."
    ufw allow ssh

    # Allow HTTP and HTTPS for web interface
    echo "  Allowing HTTP (port 80)..."
    ufw allow 80/tcp

    echo "  Allowing HTTPS (port 443)..."
    ufw allow 443/tcp

    # Allow DNS for dnsmasq
    echo "  Allowing DNS (port 53)..."
    ufw allow 53/udp
    ufw allow 53/tcp

    # Allow DHCP for dnsmasq
    echo "  Allowing DHCP (port 67)..."
    ufw allow 67/udp

    # Allow CUPS for local printing (if needed)
    echo "  Allowing CUPS (port 631) from local network..."
    ufw allow from 192.168.4.0/24 to any port 631

    # Enable firewall
    echo "  Enabling firewall..."
    ufw --force enable

    # Show status
    echo ""
    ufw status verbose
}

# Configure fail2ban (optional)
configure_fail2ban() {
    echo "Configuring fail2ban..."

    # Install fail2ban
    if ! command -v fail2ban-client &>/dev/null; then
        apt-get install -y -qq fail2ban
    fi

    # Create local configuration
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

    # Enable and start fail2ban
    systemctl enable fail2ban
    systemctl restart fail2ban

    echo "  fail2ban configured and enabled"
}

# Secure SSH configuration
secure_ssh() {
    echo "Securing SSH configuration..."

    # Backup original config
    if [[ ! -f /etc/ssh/sshd_config.orig ]]; then
        cp /etc/ssh/sshd_config /etc/ssh/sshd_config.orig
    fi

    # Apply security settings
    sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^#MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
    sed -i 's/^#LoginGraceTime.*/LoginGraceTime 60/' /etc/ssh/sshd_config

    # Restart SSH
    systemctl restart sshd

    echo "  SSH secured (root login disabled, max 3 auth tries)"
}

# Set proper file permissions
secure_permissions() {
    echo "Setting secure file permissions..."

    # Determine user (toragonite or pi)
    local OWNER="toragonite"
    if ! id "$OWNER" &>/dev/null; then
        OWNER="pi"
    fi

    # Secure .env file
    if [[ -f "$PHOTOBOOTH_DIR/.env" ]]; then
        chmod 600 "$PHOTOBOOTH_DIR/.env"
        chown "$OWNER:$OWNER" "$PHOTOBOOTH_DIR/.env"
        echo "  .env file secured"
    fi

    # Secure SSL certificates
    if [[ -d "$PHOTOBOOTH_DIR/certs" ]]; then
        chmod 600 "$PHOTOBOOTH_DIR/certs"/*.key 2>/dev/null || true
        chmod 644 "$PHOTOBOOTH_DIR/certs"/*.crt 2>/dev/null || true
        chown -R "$OWNER:$OWNER" "$PHOTOBOOTH_DIR/certs"
        echo "  SSL certificates secured"
    fi

    # Secure scripts
    chmod 700 "$PHOTOBOOTH_DIR/scripts"/*.sh 2>/dev/null || true
    chown -R "$OWNER:$OWNER" "$PHOTOBOOTH_DIR/scripts"
    echo "  Scripts secured"
}

# Generate strong secrets if needed
generate_secrets() {
    echo "Checking secrets..."

    local env_file="$PHOTOBOOTH_DIR/.env"

    if [[ -f "$env_file" ]]; then
        # Check JWT_SECRET
        if grep -q "^JWT_SECRET=$\|^JWT_SECRET=change" "$env_file"; then
            echo "  Generating JWT_SECRET..."
            local jwt_secret
            jwt_secret=$(openssl rand -base64 32)
            sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$jwt_secret|" "$env_file"
        fi
    fi
}

# Security reminders
print_reminders() {
    echo ""
    echo "=========================================="
    echo "Security Checklist"
    echo "=========================================="
    echo ""
    echo "IMPORTANT: Please complete these steps manually:"
    echo ""
    echo "1. Change default password for 'pi' user:"
    echo "   passwd pi"
    echo ""
    echo "2. Set admin PIN in $PHOTOBOOTH_DIR/.env:"
    echo "   - Generate hash: python3 -c \"import bcrypt; print(bcrypt.hashpw(b'YOUR_PIN', bcrypt.gensalt()).decode())\""
    echo "   - Update ADMIN_PIN_HASH in .env"
    echo ""
    echo "3. Change Wi-Fi password (currently: photobooth-1998):"
    echo "   - Edit /etc/hostapd/hostapd.conf"
    echo "   - Update wpa_passphrase"
    echo "   - Restart hostapd: sudo systemctl restart hostapd"
    echo ""
    echo "4. Consider setting up SSH key authentication:"
    echo "   - Copy your public key to ~/.ssh/authorized_keys"
    echo "   - Disable password authentication in /etc/ssh/sshd_config"
    echo ""
}

# Main
main() {
    configure_firewall
    configure_fail2ban
    secure_ssh
    secure_permissions
    generate_secrets
    print_reminders

    echo ""
    echo "[08-security] Security hardening complete"
}

main "$@"
