#!/bin/bash
#
# PhotoBooth Restore Script
# Restores database from backup
#
# Usage: ./restore.sh <backup-date>
#   backup-date: Date in YYYYMMDD_HHMMSS format
#
# Example: ./restore.sh 20260113_030000
#

set -euo pipefail

# Configuration
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/toragonite/Documents/photobooth}"
BACKUP_DIR="${BACKUP_DIR:-/home/toragonite/backups}"
DATA_DIR="${PHOTOBOOTH_DIR}/data"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Show usage
usage() {
    echo "PhotoBooth Restore Script"
    echo ""
    echo "Usage: $0 <backup-date>"
    echo "  backup-date: Date in YYYYMMDD_HHMMSS format"
    echo ""
    echo "Available backups:"

    if [[ -d "$BACKUP_DIR" ]]; then
        local backups
        backups=$(ls -1 "$BACKUP_DIR"/photobooth-*.db 2>/dev/null || true)

        if [[ -n "$backups" ]]; then
            echo "$backups" | while read -r file; do
                local basename
                basename=$(basename "$file")
                local date_str
                date_str=$(echo "$basename" | sed 's/photobooth-//' | sed 's/.db//')
                local size
                size=$(du -h "$file" | cut -f1)
                echo "  - ${date_str} (${size})"
            done
        else
            echo "  No backups found in ${BACKUP_DIR}"
        fi
    else
        echo "  Backup directory does not exist: ${BACKUP_DIR}"
    fi

    echo ""
    echo "Example: $0 20260113_030000"
    exit 1
}

# Validate backup exists
validate_backup() {
    local backup_date="$1"
    local db_backup="${BACKUP_DIR}/photobooth-${backup_date}.db"

    if [[ ! -f "$db_backup" ]]; then
        echo -e "${RED}[ERROR]${NC} Backup not found: $db_backup"
        echo ""
        usage
    fi

    echo -e "${GREEN}[OK]${NC} Found backup: photobooth-${backup_date}.db"
}

# Stop PhotoBooth service
stop_service() {
    echo "Stopping PhotoBooth service..."

    if command -v systemctl &> /dev/null && systemctl is-active --quiet photobooth 2>/dev/null; then
        sudo systemctl stop photobooth
        echo -e "${GREEN}[OK]${NC} PhotoBooth service stopped"
    elif [[ -f "${PHOTOBOOTH_DIR}/docker-compose.yml" ]]; then
        docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" down 2>/dev/null || true
        echo -e "${GREEN}[OK]${NC} Docker containers stopped"
    else
        echo -e "${YELLOW}[WARNING]${NC} No service to stop"
    fi
}

# Start PhotoBooth service
start_service() {
    echo "Starting PhotoBooth service..."

    if command -v systemctl &> /dev/null && systemctl is-enabled --quiet photobooth 2>/dev/null; then
        sudo systemctl start photobooth
        echo -e "${GREEN}[OK]${NC} PhotoBooth service started"
    elif [[ -f "${PHOTOBOOTH_DIR}/docker-compose.yml" ]]; then
        docker compose -f "${PHOTOBOOTH_DIR}/docker-compose.yml" up -d 2>/dev/null || true
        echo -e "${GREEN}[OK]${NC} Docker containers started"
    else
        echo -e "${YELLOW}[WARNING]${NC} No service to start"
    fi
}

# Restore database
restore_database() {
    local backup_date="$1"
    local db_backup="${BACKUP_DIR}/photobooth-${backup_date}.db"
    local db_file="${DATA_DIR}/photobooth.db"

    echo "Restoring database from backup..."

    # Create backup of current database before overwriting
    if [[ -f "$db_file" ]]; then
        local current_backup="${db_file}.pre-restore"
        cp "$db_file" "$current_backup"
        echo -e "${GREEN}[OK]${NC} Current database backed up to: photobooth.db.pre-restore"
    fi

    # Ensure data directory exists
    mkdir -p "$DATA_DIR"

    # Copy backup to database location
    cp "$db_backup" "$db_file"

    # Fix ownership (if running as root)
    if [[ $EUID -eq 0 ]] && id -u pi &>/dev/null; then
        chown pi:pi "$db_file"
    fi

    # Verify restore
    if [[ -f "$db_file" ]]; then
        local size
        size=$(du -h "$db_file" | cut -f1)
        echo -e "${GREEN}[OK]${NC} Database restored (${size})"
    else
        echo -e "${RED}[ERROR]${NC} Database restore failed!"
        exit 1
    fi
}

# Restore configuration (optional)
restore_config() {
    local backup_date="$1"
    local config_backup="${BACKUP_DIR}/config-${backup_date}.tar.gz"

    if [[ ! -f "$config_backup" ]]; then
        echo -e "${YELLOW}[INFO]${NC} No config backup found for this date"
        return 0
    fi

    echo ""
    read -p "Also restore configuration files? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        echo "Skipping configuration restore"
        return 0
    fi

    echo "Restoring configuration..."

    # Extract to temporary location first
    local temp_dir
    temp_dir=$(mktemp -d)
    tar -xzf "$config_backup" -C "$temp_dir" 2>/dev/null || true

    # Copy files back
    if [[ -f "${temp_dir}${PHOTOBOOTH_DIR}/.env" ]]; then
        cp "${temp_dir}${PHOTOBOOTH_DIR}/.env" "${PHOTOBOOTH_DIR}/.env"
        echo -e "${GREEN}[OK]${NC} .env restored"
    fi

    # Cleanup temp
    rm -rf "$temp_dir"
}

# Print summary
print_summary() {
    local backup_date="$1"

    echo ""
    echo "=========================================="
    echo "PhotoBooth Restore Complete"
    echo "=========================================="
    echo "Restored from:  photobooth-${backup_date}.db"
    echo "Timestamp:      $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo ""
    echo "The PhotoBooth service has been restarted."
    echo "Please verify the application is working correctly."
}

# Main
main() {
    # Check arguments
    if [[ $# -lt 1 ]]; then
        usage
    fi

    local backup_date="$1"

    echo "=========================================="
    echo "PhotoBooth Restore"
    echo "=========================================="
    echo ""

    # Validate
    validate_backup "$backup_date"

    # Confirm
    echo ""
    echo -e "${YELLOW}WARNING: This will replace the current database!${NC}"
    read -p "Are you sure you want to restore from ${backup_date}? (yes/no): " confirm

    if [[ "$confirm" != "yes" ]]; then
        echo "Restore cancelled."
        exit 0
    fi

    echo ""

    # Perform restore
    stop_service
    restore_database "$backup_date"
    restore_config "$backup_date"
    start_service
    print_summary "$backup_date"
}

main "$@"
