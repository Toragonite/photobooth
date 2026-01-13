#!/bin/bash
#
# PhotoBooth Control Script
# Unified interface for common operations
#
# Usage: photobooth-ctl <command> [options]
#

set -euo pipefail

# Configuration
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/pi/photobooth}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Show usage
usage() {
    cat << EOF
${BLUE}PhotoBooth Control Script${NC}

Usage: $0 <command> [options]

Commands:
    ${GREEN}start${NC}       Start PhotoBooth services
    ${GREEN}stop${NC}        Stop PhotoBooth services
    ${GREEN}restart${NC}     Restart PhotoBooth services
    ${GREEN}status${NC}      Show service status
    ${GREEN}logs${NC}        Show container logs (use -f for follow)
    ${GREEN}health${NC}      Run health check
    ${GREEN}backup${NC}      Create backup
    ${GREEN}restore${NC}     Restore from backup
    ${GREEN}update${NC}      Pull latest and restart
    ${GREEN}reset${NC}       Full reset (containers + volumes)
    ${GREEN}shell${NC}       Open shell in backend container
    ${GREEN}db${NC}          Open SQLite database shell

Examples:
    $0 start
    $0 logs -f
    $0 logs backend -f
    $0 restore 20260113_030000
    $0 backup --full

EOF
    exit 1
}

# Start services
cmd_start() {
    echo -e "${BLUE}Starting PhotoBooth...${NC}"

    if command -v systemctl &> /dev/null && systemctl is-enabled --quiet photobooth 2>/dev/null; then
        sudo systemctl start photobooth
    else
        docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" up -d
    fi

    sleep 3
    cmd_status
}

# Stop services
cmd_stop() {
    echo -e "${BLUE}Stopping PhotoBooth...${NC}"

    if command -v systemctl &> /dev/null && systemctl is-active --quiet photobooth 2>/dev/null; then
        sudo systemctl stop photobooth
    else
        docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" down
    fi

    echo -e "${GREEN}PhotoBooth stopped${NC}"
}

# Restart services
cmd_restart() {
    echo -e "${BLUE}Restarting PhotoBooth...${NC}"

    if command -v systemctl &> /dev/null && systemctl is-enabled --quiet photobooth 2>/dev/null; then
        sudo systemctl restart photobooth
    else
        docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" restart
    fi

    sleep 5
    cmd_status
}

# Show status
cmd_status() {
    echo ""
    echo -e "${BLUE}=== System Services ===${NC}"

    if command -v systemctl &> /dev/null; then
        for service in photobooth hostapd dnsmasq cups; do
            if systemctl is-active --quiet "$service" 2>/dev/null; then
                echo -e "  ${GREEN}●${NC} ${service}: active"
            elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
                echo -e "  ${RED}●${NC} ${service}: inactive"
            else
                echo -e "  ${YELLOW}○${NC} ${service}: not installed"
            fi
        done
    else
        echo "  systemctl not available"
    fi

    echo ""
    echo -e "${BLUE}=== Docker Containers ===${NC}"
    docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" ps 2>/dev/null || echo "  Docker not available"

    echo ""
    echo -e "${BLUE}=== Health Check ===${NC}"
    local health_response
    health_response=$(curl -sf --max-time 5 "http://localhost:8000/api/health" 2>/dev/null || echo '{"status":"error"}')
    local status
    status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "error")

    if [[ "$status" == "healthy" || "$status" == "ok" ]]; then
        echo -e "  Backend: ${GREEN}healthy${NC}"
    else
        echo -e "  Backend: ${RED}${status}${NC}"
    fi

    echo ""
    echo -e "${BLUE}=== System Resources ===${NC}"

    # Disk usage
    local disk_usage
    disk_usage=$(df -h / 2>/dev/null | awk 'NR==2 {print $5}' || echo "unknown")
    echo "  Disk:   ${disk_usage} used"

    # Memory usage
    if [[ -f /proc/meminfo ]]; then
        local mem_available mem_total usage_percent
        mem_available=$(grep MemAvailable /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 0)
        mem_total=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 1)
        if [[ "$mem_total" -gt 0 ]]; then
            usage_percent=$(( (mem_total - mem_available) * 100 / mem_total ))
            echo "  Memory: ${usage_percent}% used"
        fi
    fi

    echo ""
}

# Show logs
cmd_logs() {
    docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" logs "$@"
}

# Run health check
cmd_health() {
    if [[ -f "${SCRIPT_DIR}/watchdog.sh" ]]; then
        bash "${SCRIPT_DIR}/watchdog.sh"
    else
        echo -e "${RED}Watchdog script not found${NC}"
        exit 1
    fi
}

# Create backup
cmd_backup() {
    if [[ -f "${SCRIPT_DIR}/backup.sh" ]]; then
        bash "${SCRIPT_DIR}/backup.sh" "$@"
    else
        echo -e "${RED}Backup script not found${NC}"
        exit 1
    fi
}

# Restore from backup
cmd_restore() {
    if [[ -f "${SCRIPT_DIR}/restore.sh" ]]; then
        bash "${SCRIPT_DIR}/restore.sh" "$@"
    else
        echo -e "${RED}Restore script not found${NC}"
        exit 1
    fi
}

# Update application
cmd_update() {
    echo -e "${BLUE}Updating PhotoBooth...${NC}"

    cd "${PHOTOBOOTH_DIR}"

    # Pull latest code if git repo
    if [[ -d .git ]]; then
        echo "Pulling latest code..."
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
    fi

    # Pull latest images
    echo "Pulling latest Docker images..."
    docker compose pull

    # Rebuild and restart
    echo "Rebuilding containers..."
    docker compose up -d --build

    echo ""
    echo -e "${GREEN}Update complete${NC}"
    cmd_status
}

# Full reset
cmd_reset() {
    echo -e "${RED}WARNING: This will remove all containers and volumes!${NC}"
    echo "Database and photos will be preserved."
    echo ""
    read -p "Are you sure? (yes/no): " confirm

    if [[ "$confirm" != "yes" ]]; then
        echo "Reset cancelled."
        exit 0
    fi

    echo ""
    echo -e "${BLUE}Resetting PhotoBooth...${NC}"

    # Stop services
    if command -v systemctl &> /dev/null && systemctl is-active --quiet photobooth 2>/dev/null; then
        sudo systemctl stop photobooth
    fi

    # Remove containers and volumes (but not bind mounts with data)
    docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" down -v --remove-orphans

    # Prune Docker
    docker system prune -f

    # Restart
    if command -v systemctl &> /dev/null && systemctl is-enabled --quiet photobooth 2>/dev/null; then
        sudo systemctl start photobooth
    else
        docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" up -d --build
    fi

    echo ""
    echo -e "${GREEN}Reset complete${NC}"
    cmd_status
}

# Open shell in backend container
cmd_shell() {
    echo -e "${BLUE}Opening shell in backend container...${NC}"
    docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" exec backend /bin/sh
}

# Open database shell
cmd_db() {
    local db_file="${PHOTOBOOTH_DIR}/data/photobooth.db"

    if [[ ! -f "$db_file" ]]; then
        echo -e "${RED}Database not found: $db_file${NC}"
        exit 1
    fi

    if command -v sqlite3 &> /dev/null; then
        echo -e "${BLUE}Opening SQLite shell...${NC}"
        echo "Type '.help' for help, '.quit' to exit"
        echo ""
        sqlite3 "$db_file"
    else
        echo -e "${RED}sqlite3 not installed${NC}"
        exit 1
    fi
}

# Main
main() {
    if [[ $# -lt 1 ]]; then
        usage
    fi

    local command="$1"
    shift

    case "$command" in
        start)   cmd_start "$@" ;;
        stop)    cmd_stop "$@" ;;
        restart) cmd_restart "$@" ;;
        status)  cmd_status "$@" ;;
        logs)    cmd_logs "$@" ;;
        health)  cmd_health "$@" ;;
        backup)  cmd_backup "$@" ;;
        restore) cmd_restore "$@" ;;
        update)  cmd_update "$@" ;;
        reset)   cmd_reset "$@" ;;
        shell)   cmd_shell "$@" ;;
        db)      cmd_db "$@" ;;
        -h|--help|help) usage ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo ""
            usage
            ;;
    esac
}

main "$@"
