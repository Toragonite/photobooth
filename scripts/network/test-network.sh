#!/bin/bash
#
# PhotoBooth Network Diagnostic Script
# Tests Wi-Fi AP and network services
#

set -euo pipefail

WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
PI_IP="${PI_IP:-192.168.4.1}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo " PhotoBooth Network Diagnostics"
echo "==========================================${NC}"
echo ""
echo "Timestamp: $(date)"
echo ""

# Interface check
echo -e "${BLUE}--- Interface Status ---${NC}"
if ip link show "$WIFI_INTERFACE" &>/dev/null; then
    echo -e "${GREEN}[OK]${NC} Interface $WIFI_INTERFACE exists"

    local_ip=$(ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
    if [[ -n "$local_ip" ]]; then
        echo -e "${GREEN}[OK]${NC} IP Address: $local_ip"
    else
        echo -e "${RED}[FAIL]${NC} No IP address"
    fi
else
    echo -e "${RED}[FAIL]${NC} Interface $WIFI_INTERFACE not found"
fi

# hostapd check
echo ""
echo -e "${BLUE}--- hostapd Status ---${NC}"
if systemctl is-active --quiet hostapd 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} hostapd is running"
else
    echo -e "${RED}[FAIL]${NC} hostapd is NOT running"
    journalctl -u hostapd -n 5 --no-pager 2>/dev/null || true
fi

if [[ -f /etc/hostapd/hostapd.conf ]]; then
    ssid=$(grep "^ssid=" /etc/hostapd/hostapd.conf | cut -d'=' -f2)
    channel=$(grep "^channel=" /etc/hostapd/hostapd.conf | cut -d'=' -f2)
    echo "  SSID: $ssid"
    echo "  Channel: $channel"
fi

# dnsmasq check
echo ""
echo -e "${BLUE}--- dnsmasq Status ---${NC}"
if systemctl is-active --quiet dnsmasq 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} dnsmasq is running"
else
    echo -e "${RED}[FAIL]${NC} dnsmasq is NOT running"
    journalctl -u dnsmasq -n 5 --no-pager 2>/dev/null || true
fi

# DHCP leases
echo ""
echo -e "${BLUE}--- DHCP Leases ---${NC}"
if [[ -f /var/lib/misc/dnsmasq.leases ]]; then
    lease_count=$(wc -l < /var/lib/misc/dnsmasq.leases)
    echo "Active leases: $lease_count"
    if [[ "$lease_count" -gt 0 ]]; then
        cat /var/lib/misc/dnsmasq.leases
    fi
else
    echo "No lease file (no clients connected yet)"
fi

# Port check
echo ""
echo -e "${BLUE}--- Listening Ports ---${NC}"
echo "Port     Service     Status"
echo "----     -------     ------"

check_port() {
    local port=$1
    local name=$2
    if ss -tuln 2>/dev/null | grep -q ":${port} "; then
        echo -e "${port}      ${name}       ${GREEN}listening${NC}"
    else
        echo -e "${port}      ${name}       ${YELLOW}not listening${NC}"
    fi
}

check_port 53 "DNS"
check_port 67 "DHCP"
check_port 80 "HTTP"
check_port 443 "HTTPS"
check_port 8000 "FastAPI"

# Docker check
echo ""
echo -e "${BLUE}--- Docker Containers ---${NC}"
if command -v docker &>/dev/null && docker info &>/dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers"
else
    echo "Docker not available"
fi

# Summary
echo ""
echo -e "${BLUE}=========================================="
echo " Summary"
echo "==========================================${NC}"
echo ""
echo "Connect to Wi-Fi and access:"
echo "  http://$PI_IP:8000 (Backend)"
echo "  http://$PI_IP (Frontend)"
echo ""
