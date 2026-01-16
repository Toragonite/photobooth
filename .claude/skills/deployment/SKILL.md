---
description: Deployment, Docker, systemd, and Raspberry Pi 5 setup for PhotoBooth. Use for deployment issues, service management, container operations, and system configuration.
auto-activation-keywords:
  - deploy
  - deployment
  - docker
  - systemd
  - service
  - container
  - compose
  - production
  - boot
  - startup
  - install
  - setup
---

# Deployment Skill

Complete guide for deploying PhotoBooth on Raspberry Pi 5.

## Quick Reference

| Component | Technology |
|-----------|------------|
| Container | Docker + Docker Compose |
| Process Manager | systemd |
| Reverse Proxy | nginx (in container) |
| Database | SQLite (file-based) |
| Print Spooler | CUPS (host system) |
| Wi-Fi AP | hostapd + dnsmasq |

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Raspberry Pi 5                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Docker Host                           │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │   nginx      │  │   backend    │  │   frontend   │   │   │
│  │  │   :80/:443   │─>│   :8000      │  │   (static)   │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │         │                  │                             │   │
│  │         │                  ▼                             │   │
│  │         │          ┌──────────────┐                      │   │
│  │         │          │   SQLite     │                      │   │
│  │         │          │   /data/db   │                      │   │
│  │         │          └──────────────┘                      │   │
│  └─────────┼────────────────────────────────────────────────┘   │
│            │                                                    │
│  ┌─────────▼────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CUPS           │  │   hostapd    │  │   dnsmasq    │      │
│  │   (printer)      │  │   (Wi-Fi AP) │  │   (DHCP)     │      │
│  └──────────────────┘  └──────────────┘  └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Initial Pi Setup

### 1. Flash OS
```bash
# Use Raspberry Pi Imager
# Select: Raspberry Pi OS (64-bit)
# Configure: hostname, SSH, Wi-Fi (for initial setup)
```

### 2. First Boot Configuration
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Set timezone (Rwanda)
sudo timedatectl set-timezone Africa/Kigali

# Set locale
sudo raspi-config  # Localization Options
```

### 3. Install Dependencies
```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# CUPS
sudo apt install -y cups cups-bsd printer-driver-gutenprint
sudo usermod -aG lpadmin $USER

# hostapd & dnsmasq
sudo apt install -y hostapd dnsmasq

# Other utilities
sudo apt install -y git vim htop
```

## Wi-Fi AP Configuration

### /etc/hostapd/hostapd.conf
```conf
interface=wlan0
driver=nl80211
ssid=photobooth
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${WIFI_PASSWORD}  # Set via environment variable
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```

### /etc/dnsmasq.conf
```conf
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=photobooth.local
address=/photobooth.local/192.168.4.1
```

### /etc/dhcpcd.conf (append)
```conf
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
```

### Enable Services
```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

## Docker Compose Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - frontend_build:/usr/share/nginx/html:ro
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=sqlite:////data/photobooth.db
      - STORAGE_PATH=/data/photos
      - CUPS_SERVER=host.docker.internal:631
    volumes:
      - ./data:/data
      - /var/run/cups:/var/run/cups
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    volumes:
      - frontend_build:/app/dist

volumes:
  frontend_build:

networks:
  default:
    driver: bridge
```

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcups2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create data directories
RUN mkdir -p /data/photos

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM alpine:latest
COPY --from=builder /app/dist /app/dist
```

## systemd Services

### /etc/systemd/system/photobooth.service
```ini
[Unit]
Description=PhotoBooth Application
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/pi/photobooth
ExecStartPre=/usr/bin/docker compose pull
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always
RestartSec=10
User=pi
Group=docker

[Install]
WantedBy=multi-user.target
```

### Enable PhotoBooth Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable photobooth
sudo systemctl start photobooth
```

## Deployment Commands

### Full Deployment
```bash
# Clone repository (first time)
git clone https://github.com/your-repo/photobooth.git
cd photobooth

# Build and start
docker compose build
docker compose up -d

# Check logs
docker compose logs -f
```

### Update Deployment
```bash
cd /home/pi/photobooth

# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Rollback
```bash
# List recent commits
git log --oneline -10

# Rollback to specific commit
git checkout <commit-hash>
docker compose down
docker compose build
docker compose up -d
```

## Health Checks

### Service Status
```bash
# All services
sudo systemctl status photobooth hostapd dnsmasq cups

# Docker containers
docker compose ps
docker compose logs --tail=50

# Network
ip addr show wlan0
iw dev wlan0 station dump
```

### Application Health
```bash
# Backend health
curl http://localhost:8000/api/health

# Full status
curl http://localhost:8000/api/admin/status
```

## Backup & Recovery

### Backup Data
```bash
# Stop services
sudo systemctl stop photobooth

# Backup database and photos
tar -czvf photobooth-backup-$(date +%Y%m%d).tar.gz \
  /home/pi/photobooth/data/

# Restart services
sudo systemctl start photobooth
```

### Restore Data
```bash
# Stop services
sudo systemctl stop photobooth

# Restore from backup
tar -xzvf photobooth-backup-YYYYMMDD.tar.gz -C /

# Restart services
sudo systemctl start photobooth
```

## Troubleshooting

### Container Issues
```bash
# View container logs
docker compose logs backend
docker compose logs nginx

# Restart specific service
docker compose restart backend

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Network Issues
```bash
# Check AP status
sudo systemctl status hostapd

# Check DHCP leases
cat /var/lib/misc/dnsmasq.leases

# Restart network services
sudo systemctl restart hostapd dnsmasq
```

### Performance Issues
```bash
# Check resource usage
docker stats

# System resources
htop

# Temperature
vcgencmd measure_temp
```

## Production Checklist

- [ ] Pi OS updated to latest
- [ ] Docker installed and configured
- [ ] CUPS installed with printer configured
- [ ] Wi-Fi AP configured (hostapd + dnsmasq)
- [ ] SSL certificates generated (self-signed or Let's Encrypt)
- [ ] PhotoBooth service enabled (systemd)
- [ ] Backup strategy in place
- [ ] Admin PIN changed from default
- [ ] Test complete user flow
- [ ] Test print functionality
- [ ] Test auto-recovery on reboot

## Related Documentation

- `docs/DEPLOYMENT.md` - Full deployment guide
- `docs/use-cases/UC-109-reboot-system.md` - System reboot
- `docs/use-cases/UC-105-restart-service.md` - Service management
- `docs/use-cases/UC-205-health-check.md` - Health monitoring
