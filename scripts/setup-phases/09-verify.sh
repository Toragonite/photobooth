#!/bin/bash
#
# Phase 09: Final Verification
# Verifies all components are working correctly
#

set -euo pipefail

echo "[09-verify] Starting final verification..."

PI_IP="${PI_IP:-192.168.4.1}"
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/toragonite/Documents/photobooth}"
WIFI_SSID="${WIFI_SSID:-photobooth}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Test functions
pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "  ${YELLOW}!${NC} $1"
    ((WARNINGS++))
}

# System checks
check_system() {
    echo ""
    echo "System Checks:"

    # Check hostname
    if [[ "$(hostname)" == "photobooth" ]]; then
        pass "Hostname is set to 'photobooth'"
    else
        warn "Hostname is '$(hostname)' (expected 'photobooth')"
    fi

    # Check timezone
    local tz
    tz=$(timedatectl show --property=Timezone --value)
    if [[ "$tz" == "Africa/Kigali" ]]; then
        pass "Timezone is set to Africa/Kigali"
    else
        warn "Timezone is '$tz'"
    fi

    # Check disk space
    local disk_usage
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    if [[ "$disk_usage" -lt 80 ]]; then
        pass "Disk usage is ${disk_usage}%"
    elif [[ "$disk_usage" -lt 90 ]]; then
        warn "Disk usage is ${disk_usage}% (consider cleanup)"
    else
        fail "Disk usage is ${disk_usage}% (critical)"
    fi

    # Check memory
    local mem_available
    mem_available=$(free -m | awk '/^Mem:/ {print $7}')
    if [[ "$mem_available" -gt 1000 ]]; then
        pass "Available memory: ${mem_available}MB"
    elif [[ "$mem_available" -gt 500 ]]; then
        warn "Available memory: ${mem_available}MB (low)"
    else
        fail "Available memory: ${mem_available}MB (critical)"
    fi
}

# Docker checks
check_docker() {
    echo ""
    echo "Docker Checks:"

    # Check Docker daemon
    if docker info &>/dev/null; then
        pass "Docker daemon is running"
    else
        fail "Docker daemon is not running"
        return
    fi

    # Check containers
    cd "$PHOTOBOOTH_DIR"
    local running_containers
    running_containers=$(docker compose ps --filter "status=running" -q 2>/dev/null | wc -l)

    if [[ "$running_containers" -gt 0 ]]; then
        pass "$running_containers container(s) running"
    else
        fail "No containers running"
    fi

    # Check for unhealthy containers
    local unhealthy
    unhealthy=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null)
    if [[ -z "$unhealthy" ]]; then
        pass "No unhealthy containers"
    else
        fail "Unhealthy containers: $unhealthy"
    fi
}

# Network checks
check_network() {
    echo ""
    echo "Network Checks:"

    # Check wlan0 IP
    if ip addr show wlan0 2>/dev/null | grep -q "$PI_IP"; then
        pass "wlan0 has IP $PI_IP"
    else
        fail "wlan0 does not have expected IP $PI_IP"
    fi

    # Check hostapd
    if systemctl is-active --quiet hostapd; then
        pass "hostapd is running"
    else
        fail "hostapd is not running"
    fi

    # Check dnsmasq
    if systemctl is-active --quiet dnsmasq; then
        pass "dnsmasq is running"
    else
        fail "dnsmasq is not running"
    fi

    # Check if AP is broadcasting
    # Note: This might not work from the same device
    warn "Cannot verify Wi-Fi broadcast from this device (test from client)"
}

# Service checks
check_services() {
    echo ""
    echo "Service Checks:"

    # Check CUPS
    if systemctl is-active --quiet cups; then
        pass "CUPS is running"
    else
        warn "CUPS is not running"
    fi

    # Check photobooth service
    if systemctl is-active --quiet photobooth; then
        pass "photobooth.service is active"
    else
        fail "photobooth.service is not active"
    fi

    # Check timers
    if systemctl is-active --quiet photobooth-watchdog.timer; then
        pass "photobooth-watchdog.timer is active"
    else
        warn "photobooth-watchdog.timer is not active"
    fi

    if systemctl is-active --quiet photobooth-backup.timer; then
        pass "photobooth-backup.timer is active"
    else
        warn "photobooth-backup.timer is not active"
    fi

    # Check welcome-print service
    if systemctl is-enabled --quiet photobooth-welcome-print 2>/dev/null; then
        pass "photobooth-welcome-print is enabled"
    else
        warn "photobooth-welcome-print is not enabled"
    fi
}

# Application checks
check_application() {
    echo ""
    echo "Application Checks:"

    # Check backend health
    local health_response
    health_response=$(curl -sf --max-time 10 "http://localhost:8000/api/health" 2>/dev/null || echo "")

    if [[ -n "$health_response" ]]; then
        local status
        status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        if [[ "$status" == "healthy" || "$status" == "ok" ]]; then
            pass "Backend API is healthy"
        else
            warn "Backend API status: $status"
        fi
    else
        fail "Backend API is not responding"
    fi

    # Check frontend
    if curl -sf --max-time 10 "http://localhost:80" &>/dev/null || \
       curl -sf --max-time 10 "http://localhost:3000" &>/dev/null; then
        pass "Frontend is responding"
    else
        fail "Frontend is not responding"
    fi

    # Check HTTPS
    if curl -sf --max-time 10 -k "https://localhost" &>/dev/null; then
        pass "HTTPS is working"
    else
        warn "HTTPS may not be configured"
    fi
}

# Printer checks
check_printer() {
    echo ""
    echo "Printer Checks:"

    local PRINTER_NAME="${PRINTER_NAME:-SelphyCP1500}"

    # Check usblp is blacklisted
    if [[ -f /etc/modprobe.d/blacklist-usblp.conf ]]; then
        pass "usblp module is blacklisted"
    else
        fail "usblp module NOT blacklisted (printer won't work!)"
    fi

    # Check usblp is not loaded
    if ! lsmod | grep -q usblp; then
        pass "usblp module is not loaded"
    else
        warn "usblp module is loaded (unplug/replug USB or reboot)"
    fi

    # Check if printer is configured
    if lpstat -p "$PRINTER_NAME" &>/dev/null; then
        pass "$PRINTER_NAME is configured"

        # Check printer status
        local printer_status
        printer_status=$(lpstat -p "$PRINTER_NAME" 2>/dev/null | head -1)
        if echo "$printer_status" | grep -qi "idle\|ready"; then
            pass "Printer is ready"
        elif echo "$printer_status" | grep -qi "enabled"; then
            pass "Printer is enabled"
        else
            warn "Printer status: $printer_status"
        fi
    else
        warn "Printer $PRINTER_NAME not configured (connect Canon Selphy CP1500 to complete)"
    fi
}

# Security checks
check_security() {
    echo ""
    echo "Security Checks:"

    # Check firewall
    if ufw status 2>/dev/null | grep -q "Status: active"; then
        pass "Firewall (ufw) is active"
    else
        warn "Firewall is not active"
    fi

    # Check SSH root login
    if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config 2>/dev/null; then
        pass "SSH root login is disabled"
    else
        warn "SSH root login may be enabled"
    fi

    # Check .env permissions
    if [[ -f "$PHOTOBOOTH_DIR/.env" ]]; then
        local perms
        perms=$(stat -c %a "$PHOTOBOOTH_DIR/.env" 2>/dev/null || echo "unknown")
        if [[ "$perms" == "600" ]]; then
            pass ".env file has secure permissions (600)"
        else
            warn ".env file permissions: $perms (should be 600)"
        fi
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "Verification Summary"
    echo "=========================================="
    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""

    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}All critical checks passed!${NC}"
        echo ""
        echo "PhotoBooth is ready to use."
        echo ""
        echo "To connect:"
        echo "  1. Connect to Wi-Fi network: $WIFI_SSID"
        echo "  2. Open browser: https://$PI_IP"
        echo "  3. Accept the SSL certificate warning"
        echo ""
    else
        echo -e "${RED}Some checks failed. Please review and fix issues above.${NC}"
        echo ""
    fi

    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}Note: Some warnings may require attention.${NC}"
        echo ""
    fi
}

# Main
main() {
    check_system
    check_docker
    check_network
    check_services
    check_application
    check_printer
    check_security
    print_summary

    echo "[09-verify] Verification complete"

    # Exit with appropriate code
    if [[ $FAILED -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
