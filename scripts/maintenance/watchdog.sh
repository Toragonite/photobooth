#!/bin/bash
#
# PhotoBooth Health Watchdog
# Checks system health and auto-recovers from failures
#
# Usage: ./watchdog.sh
#

set -euo pipefail

# Configuration
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/toragonite/Documents/photobooth}"
LOG_FILE="${LOG_FILE:-/var/log/photobooth-watchdog.log}"
HEALTH_URL="http://localhost:8000/api/health"
MAX_LOG_SIZE=1048576  # 1MB

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Log to file
    echo "${timestamp} [${level}] ${message}" >> "$LOG_FILE" 2>/dev/null || true

    # Also output to terminal if running interactively
    if [[ -t 1 ]]; then
        case "$level" in
            ERROR)   echo -e "${RED}[${level}]${NC} ${message}" ;;
            WARNING) echo -e "${YELLOW}[${level}]${NC} ${message}" ;;
            OK)      echo -e "${GREEN}[${level}]${NC} ${message}" ;;
            *)       echo "[${level}] ${message}" ;;
        esac
    fi
}

# Rotate log if too large
rotate_log() {
    if [[ -f "$LOG_FILE" ]]; then
        local size
        size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [[ "$size" -gt "$MAX_LOG_SIZE" ]]; then
            mv "$LOG_FILE" "${LOG_FILE}.1"
            log "INFO" "Log rotated"
        fi
    fi
}

# Check if Docker containers are healthy
check_docker() {
    log "INFO" "Checking Docker containers..."

    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker not installed"
        return 1
    fi

    if ! docker info &> /dev/null; then
        log "ERROR" "Docker daemon not running"
        return 1
    fi

    # Check for unhealthy containers
    local unhealthy
    unhealthy=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null || true)

    if [[ -n "$unhealthy" ]]; then
        log "WARNING" "Unhealthy containers: $unhealthy"
        for container in $unhealthy; do
            log "INFO" "Restarting container: $container"
            docker restart "$container" 2>/dev/null || true
        done
        return 1
    fi

    # Check for exited containers that should be running
    local exited
    exited=$(docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" ps --filter "status=exited" --format "{{.Name}}" 2>/dev/null || true)

    if [[ -n "$exited" ]]; then
        log "WARNING" "Exited containers detected, restarting compose stack"
        docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" up -d 2>/dev/null || true
        return 1
    fi

    log "OK" "Docker containers healthy"
    return 0
}

# Check backend health endpoint
check_backend() {
    log "INFO" "Checking backend health..."

    local response
    local status

    response=$(curl -sf --max-time 10 "$HEALTH_URL" 2>/dev/null || echo '{"status":"error"}')
    status=$(echo "$response" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "error")

    if [[ "$status" == "healthy" || "$status" == "ok" ]]; then
        log "OK" "Backend is healthy"
        return 0
    fi

    log "WARNING" "Backend unhealthy (status: $status), restarting..."
    docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" restart backend 2>/dev/null || true
    return 1
}

# Check CUPS service
check_cups() {
    log "INFO" "Checking CUPS service..."

    if ! command -v systemctl &> /dev/null; then
        log "WARNING" "systemctl not available, skipping CUPS check"
        return 0
    fi

    if ! systemctl is-active --quiet cups 2>/dev/null; then
        log "WARNING" "CUPS not running, attempting restart..."
        sudo systemctl restart cups 2>/dev/null || true
        sleep 2

        if systemctl is-active --quiet cups 2>/dev/null; then
            log "OK" "CUPS restarted successfully"
            return 0
        else
            log "ERROR" "Failed to restart CUPS"
            return 1
        fi
    fi

    log "OK" "CUPS is running"
    return 0
}

# Check disk space
check_disk() {
    log "INFO" "Checking disk space..."

    local usage
    usage=$(df -h / 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%' || echo 0)

    if [[ "$usage" -gt 95 ]]; then
        log "ERROR" "CRITICAL: Disk usage at ${usage}%"
        # Trigger cleanup via API if available
        curl -sf -X POST "http://localhost:8000/api/admin/cleanup" --max-time 30 2>/dev/null || true
        return 1
    elif [[ "$usage" -gt 90 ]]; then
        log "WARNING" "Disk usage high at ${usage}%"
        return 0
    fi

    log "OK" "Disk usage: ${usage}%"
    return 0
}

# Check Wi-Fi AP (hostapd)
check_wifi_ap() {
    log "INFO" "Checking Wi-Fi AP..."

    if ! command -v systemctl &> /dev/null; then
        log "WARNING" "systemctl not available, skipping Wi-Fi AP check"
        return 0
    fi

    if ! systemctl is-active --quiet hostapd 2>/dev/null; then
        log "WARNING" "hostapd not running, attempting restart..."
        sudo systemctl restart hostapd 2>/dev/null || true
        sleep 2

        if systemctl is-active --quiet hostapd 2>/dev/null; then
            log "OK" "hostapd restarted successfully"
            return 0
        else
            log "ERROR" "Failed to restart hostapd"
            return 1
        fi
    fi

    log "OK" "Wi-Fi AP is running"
    return 0
}

# Check memory usage
check_memory() {
    log "INFO" "Checking memory..."

    local mem_available
    local mem_total
    local usage_percent

    if [[ -f /proc/meminfo ]]; then
        mem_available=$(grep MemAvailable /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 0)
        mem_total=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 1)

        if [[ "$mem_total" -gt 0 ]]; then
            usage_percent=$(( (mem_total - mem_available) * 100 / mem_total ))

            if [[ "$usage_percent" -gt 95 ]]; then
                log "ERROR" "CRITICAL: Memory usage at ${usage_percent}%"
                return 1
            elif [[ "$usage_percent" -gt 85 ]]; then
                log "WARNING" "Memory usage high at ${usage_percent}%"
                return 0
            fi

            log "OK" "Memory usage: ${usage_percent}%"
            return 0
        fi
    fi

    log "WARNING" "Could not determine memory usage"
    return 0
}

# Print summary
print_summary() {
    local issues="$1"

    echo ""
    echo "=========================================="
    echo "PhotoBooth Health Check Summary"
    echo "=========================================="
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

    if [[ "$issues" -eq 0 ]]; then
        echo -e "Status: ${GREEN}HEALTHY${NC}"
    else
        echo -e "Status: ${YELLOW}${issues} ISSUE(S) DETECTED${NC}"
    fi
    echo "=========================================="
}

# Main health check routine
main() {
    # Create log directory if needed
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

    rotate_log
    log "INFO" "Starting health check..."

    local issues=0

    check_docker   || ((issues++))
    check_backend  || ((issues++))
    check_cups     || ((issues++))
    check_disk     || ((issues++))
    check_wifi_ap  || ((issues++))
    check_memory   || ((issues++))

    if [[ -t 1 ]]; then
        print_summary "$issues"
    fi

    if [[ "$issues" -gt 0 ]]; then
        log "WARNING" "Health check completed with $issues issue(s)"
        exit 1
    else
        log "OK" "Health check completed - all systems healthy"
        exit 0
    fi
}

main "$@"
