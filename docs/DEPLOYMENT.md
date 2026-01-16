# Deployment Guide

> Complete deployment guide for PhotoBooth on Raspberry Pi 5

---

## Hardware Requirements

### Raspberry Pi 5

| Component | Specification |
|-----------|---------------|
| Model | Raspberry Pi 5 |
| RAM | 8GB |
| Storage | 256GB microSD (A2 class recommended) |
| Power | USB-C 5V/5A (27W) official power supply |
| Cooling | Active cooler recommended |

### Peripherals

| Device | Model | Connection |
|--------|-------|------------|
| Printer | Canon Selphy CP1500 | USB-A |
| Wi-Fi | Built-in (AP mode) | N/A |

### Client Device

| Device | Requirements |
|--------|--------------|
| iPad Air | Safari browser, connected to photobooth Wi-Fi |

---

## Software Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        Host OS                              │
│                   Raspberry Pi OS Lite                      │
│                      (64-bit, Bookworm)                     │
├─────────────────────────────────────────────────────────────┤
│  hostapd  │  dnsmasq  │  CUPS  │  Docker + Compose         │
├───────────┴───────────┴────────┴────────────────────────────┤
│                     Docker Containers                       │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │    Frontend     │  │          Backend                │   │
│  │  (Nginx + SPA)  │  │    (FastAPI + Python 3.11)      │   │
│  │    Port: 80     │  │         Port: 8000              │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
│                              │                              │
│                      ┌───────┴───────┐                      │
│                      │    SQLite     │                      │
│                      │   /data/*.db  │                      │
│                      └───────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Initial Pi Setup

### 1. Flash Raspberry Pi OS

```bash
# Use Raspberry Pi Imager
# Select: Raspberry Pi OS Lite (64-bit)
# Configure:
#   - Hostname: photobooth
#   - Enable SSH
#   - Set username/password
#   - Configure Wi-Fi (for initial setup only)
```

### 2. First Boot Configuration

```bash
# SSH into Pi
ssh pi@photobooth.local

# Update system
sudo apt update && sudo apt upgrade -y

# Set timezone
sudo timedatectl set-timezone Africa/Kigali

# Enable required interfaces
sudo raspi-config nonint do_wifi_country RW
```

### 3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

---

## Wi-Fi Access Point Setup

### 1. Install Required Packages

```bash
sudo apt install -y hostapd dnsmasq
```

### 2. Configure Static IP

```bash
# /etc/dhcpcd.conf
sudo tee -a /etc/dhcpcd.conf << 'EOF'

# Wi-Fi AP configuration
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF
```

### 3. Configure hostapd

```bash
# /etc/hostapd/hostapd.conf
sudo tee /etc/hostapd/hostapd.conf << 'EOF'
interface=wlan0
driver=nl80211
ssid=photobooth
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=\${WIFI_PASSWORD}  # Set via environment variable
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Enable hostapd
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
```

### 4. Configure dnsmasq

```bash
# Backup original config
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig

# /etc/dnsmasq.conf
sudo tee /etc/dnsmasq.conf << 'EOF'
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=local
address=/photobooth.local/192.168.4.1
EOF
```

### 5. Enable IP Forwarding (if needed)

```bash
# /etc/sysctl.conf
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
```

### 6. Start Services

```bash
sudo systemctl restart dhcpcd
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

---

## CUPS Printer Setup

### 1. Install CUPS

```bash
sudo apt install -y cups cups-client
```

### 2. Configure CUPS

```bash
# Allow remote admin (for initial setup)
sudo cupsctl --remote-admin

# Add pi user to lpadmin group
sudo usermod -aG lpadmin pi
```

### 3. Add Printer

```bash
# Connect Canon Selphy CP1500 via USB

# List available printers
lpinfo -v

# Add printer (adjust device URI as needed)
sudo lpadmin -p Canon_Selphy_CP1500 \
    -v usb://Canon/SELPHY%20CP1500 \
    -m everywhere \
    -o media=na_index-4x6_4x6in

# Set as default
sudo lpadmin -d Canon_Selphy_CP1500

# Enable printer
sudo cupsenable Canon_Selphy_CP1500
sudo cupsaccept Canon_Selphy_CP1500
```

### 4. Test Print

```bash
# Print test page
lp -d Canon_Selphy_CP1500 /usr/share/cups/data/testprint
```

---

## Application Deployment

### Directory Structure

```
/home/pi/photobooth/
├── docker-compose.yml
├── .env
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── dist/           # Built frontend
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
└── data/
    ├── photobooth.db
    ├── photos/
    ├── composites/
    └── logs/
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - photobooth

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - /var/run/cups:/var/run/cups:ro
    environment:
      - DATABASE_URL=sqlite:///data/photobooth.db
      - STORAGE_PATH=/data
      - LOG_LEVEL=${LOG_LEVEL:-error}
      - JWT_SECRET=${JWT_SECRET}
      - ADMIN_PIN_HASH=${ADMIN_PIN_HASH}
    restart: unless-stopped
    networks:
      - photobooth

networks:
  photobooth:
    driver: bridge
```

### Environment File

```bash
# .env
# REQUIRED: Generate with: openssl rand -base64 32
SECRET_KEY=

# REQUIRED: Set your admin PIN (4-8 digits)
ADMIN_PIN=

LOG_LEVEL=error
TZ=Africa/Kigali
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Frontend Nginx Config

```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name photobooth.local;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        client_max_body_size 10M;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcups2-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deploy Application

```bash
# Clone/copy project to Pi
cd /home/pi/photobooth

# Create data directories
mkdir -p data/photos data/composites data/logs

# Set permissions
chmod 755 data
chmod 777 data/photos data/composites data/logs

# Build and start
docker compose build
docker compose up -d

# Check status
docker compose ps
docker compose logs -f
```

---

## Systemd Services

### Auto-start on Boot

```bash
# /etc/systemd/system/photobooth.service
sudo tee /etc/systemd/system/photobooth.service << 'EOF'
[Unit]
Description=PhotoBooth Application
Requires=docker.service
After=docker.service cups.service hostapd.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/photobooth
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=pi

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable photobooth
```

### Service Management

```bash
# Start
sudo systemctl start photobooth

# Stop
sudo systemctl stop photobooth

# Restart
sudo systemctl restart photobooth

# Status
sudo systemctl status photobooth

# Logs
journalctl -u photobooth -f
```

---

## Health Monitoring

### Watchdog Script

```bash
# /home/pi/scripts/watchdog.sh
#!/bin/bash

# Check if backend is responding
if ! curl -sf http://localhost:8000/api/health > /dev/null; then
    echo "$(date): Backend unhealthy, restarting..."
    docker compose -f /home/pi/photobooth/docker-compose.yml restart backend
fi

# Check if CUPS is running
if ! systemctl is-active --quiet cups; then
    echo "$(date): CUPS not running, restarting..."
    sudo systemctl restart cups
fi

# Check disk space
USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$USAGE" -gt 90 ]; then
    echo "$(date): Disk usage critical: ${USAGE}%"
fi
```

### Cron Job

```bash
# Add to crontab
crontab -e

# Add line:
*/5 * * * * /home/pi/scripts/watchdog.sh >> /home/pi/logs/watchdog.log 2>&1
```

---

## Backup & Recovery

### Automated Backup Script

```bash
# /home/pi/scripts/backup.sh
#!/bin/bash

BACKUP_DIR="/home/pi/backups"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /home/pi/photobooth/data/photobooth.db $BACKUP_DIR/photobooth-$DATE.db

# Backup photos (optional - large)
# tar -czf $BACKUP_DIR/photos-$DATE.tar.gz /home/pi/photobooth/data/photos

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "$(date): Backup completed"
```

### Recovery Steps

```bash
# Stop services
sudo systemctl stop photobooth

# Restore database
cp /home/pi/backups/photobooth-20240113.db /home/pi/photobooth/data/photobooth.db

# Start services
sudo systemctl start photobooth
```

---

## Troubleshooting

### Common Issues

#### Wi-Fi AP Not Starting

```bash
# Check hostapd status
sudo systemctl status hostapd

# Check for conflicts
sudo rfkill list

# Unblock if needed
sudo rfkill unblock wifi
```

#### Printer Not Found

```bash
# List USB devices
lsusb

# Check CUPS
lpstat -p -d

# Restart CUPS
sudo systemctl restart cups
```

#### Docker Issues

```bash
# Check container logs
docker compose logs backend
docker compose logs frontend

# Rebuild containers
docker compose build --no-cache
docker compose up -d
```

#### Database Locked

```bash
# Check for stale locks
fuser /home/pi/photobooth/data/photobooth.db

# If needed, restart backend
docker compose restart backend
```

### Log Locations

| Log | Location |
|-----|----------|
| Docker logs | `docker compose logs` |
| System logs | `journalctl -xe` |
| CUPS logs | `/var/log/cups/` |
| Application logs | `/home/pi/photobooth/data/logs/` |
| hostapd logs | `journalctl -u hostapd` |

---

## Security Checklist

- [ ] Change default Pi password
- [ ] Set ADMIN_PIN in .env (no default - required)
- [ ] Set SECRET_KEY in .env (generate with: openssl rand -base64 32)
- [ ] Set WIFI_PASSWORD environment variable before setup
- [ ] Disable SSH password auth (use keys)
- [ ] Restrict CUPS admin access
- [ ] Enable firewall (ufw)

### Firewall Rules

```bash
sudo apt install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (for maintenance)
sudo ufw allow ssh

# Allow HTTP (for app)
sudo ufw allow 80/tcp

# Enable firewall
sudo ufw enable
```

---

## Performance Tuning

### Pi Configuration

```bash
# /boot/config.txt additions
sudo tee -a /boot/config.txt << 'EOF'

# Performance
gpu_mem=128
arm_freq=2400
over_voltage=4

# USB power
max_usb_current=1
EOF
```

### Docker Resource Limits

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
