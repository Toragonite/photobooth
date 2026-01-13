#!/bin/bash
#
# Phase 03: CUPS Print Server Installation
# Installs and configures CUPS for printing
#

set -euo pipefail

echo "[03-cups] Starting CUPS installation..."

# Install CUPS and related packages
echo "Installing CUPS packages..."
apt-get install -y -qq \
    cups \
    cups-client \
    cups-bsd \
    libcups2-dev \
    printer-driver-gutenprint

# Enable CUPS service
echo "Enabling CUPS service..."
systemctl enable cups
systemctl start cups

# Wait for CUPS to be ready
echo "Waiting for CUPS to be ready..."
for i in {1..30}; do
    if lpstat -r &>/dev/null; then
        echo "CUPS is ready"
        break
    fi
    sleep 1
done

# Configure CUPS
echo "Configuring CUPS..."

# Backup original config
if [[ ! -f /etc/cups/cupsd.conf.orig ]]; then
    cp /etc/cups/cupsd.conf /etc/cups/cupsd.conf.orig
fi

# Allow remote administration (temporarily for setup)
cupsctl --remote-admin

# Allow access from local network
cupsctl --share-printers

# Add pi user to lpadmin group for printer management
echo "Adding pi user to lpadmin group..."
usermod -aG lpadmin pi 2>/dev/null || true

# Configure CUPS to listen on all interfaces
cat > /etc/cups/cupsd.conf << 'EOF'
# PhotoBooth CUPS Configuration

# Log settings
LogLevel warn
PageLogFormat

# Server settings
MaxLogSize 1m
Listen /run/cups/cups.sock
Listen 0.0.0.0:631

# Browsing
Browsing Off
BrowseLocalProtocols

# Access restrictions
<Location />
  Order allow,deny
  Allow @LOCAL
</Location>

<Location /admin>
  Order allow,deny
  Allow @LOCAL
</Location>

<Location /admin/conf>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow @LOCAL
</Location>

<Location /admin/log>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow @LOCAL
</Location>

# Policy settings
<Policy default>
  JobPrivateAccess default
  JobPrivateValues default
  SubscriptionPrivateAccess default
  SubscriptionPrivateValues default

  <Limit Create-Job Print-Job Print-URI Validate-Job>
    Order deny,allow
  </Limit>

  <Limit Send-Document Send-URI Hold-Job Release-Job Restart-Job Purge-Jobs Set-Job-Attributes Create-Job-Subscription Renew-Subscription Cancel-Subscription Get-Notifications Reprocess-Job Cancel-Current-Job Suspend-Current-Job Resume-Job Cancel-My-Jobs Close-Job CUPS-Move-Job CUPS-Get-Document>
    Require user @OWNER @SYSTEM
    Order deny,allow
  </Limit>

  <Limit CUPS-Add-Modify-Printer CUPS-Delete-Printer CUPS-Add-Modify-Class CUPS-Delete-Class CUPS-Set-Default CUPS-Get-Devices>
    AuthType Default
    Require user @SYSTEM
    Order deny,allow
  </Limit>

  <Limit Pause-Printer Resume-Printer Enable-Printer Disable-Printer Pause-Printer-After-Current-Job Hold-New-Jobs Release-Held-New-Jobs Deactivate-Printer Activate-Printer Restart-Printer Shutdown-Printer Startup-Printer Promote-Job Schedule-Job-After Cancel-Jobs CUPS-Accept-Jobs CUPS-Reject-Jobs>
    AuthType Default
    Require user @SYSTEM
    Order deny,allow
  </Limit>

  <Limit Cancel-Job CUPS-Authenticate-Job>
    Require user @OWNER @SYSTEM
    Order deny,allow
  </Limit>

  <Limit All>
    Order deny,allow
  </Limit>
</Policy>

# SSL/TLS
ServerAlias *
DefaultEncryption Never
EOF

# Restart CUPS to apply configuration
echo "Restarting CUPS..."
systemctl restart cups

# Verify CUPS is running
if systemctl is-active --quiet cups; then
    echo "CUPS is running"
else
    echo "Warning: CUPS may not be running properly"
fi

# Show CUPS status
echo "CUPS status:"
lpstat -s 2>/dev/null || echo "No printers configured yet"

echo "[03-cups] CUPS installation complete"
echo ""
echo "Note: The printer will be configured in phase 05-printer"
echo "      after the Canon Selphy CP1500 is connected via USB"
