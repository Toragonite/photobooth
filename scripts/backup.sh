#!/bin/bash
#
# PhotoBooth Backup Script
# Backs up database and configuration
#
# Usage: ./backup.sh [--full]
#   --full: Include photos in backup (large)
#

set -euo pipefail

# Configuration
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/pi/photobooth}"
BACKUP_DIR="${BACKUP_DIR:-/home/pi/backups}"
DATA_DIR="${PHOTOBOOTH_DIR}/data"
MAX_BACKUPS="${MAX_BACKUPS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/photobooth-backup.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
FULL_BACKUP=false
if [[ "${1:-}" == "--full" ]]; then
    FULL_BACKUP=true
fi

# Logging
log() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} - ${message}" >> "$LOG_FILE" 2>/dev/null || true
    echo -e "${message}"
}

# Create backup directory
setup() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
}

# Backup SQLite database
backup_database() {
    local db_file="${DATA_DIR}/photobooth.db"
    local backup_file="${BACKUP_DIR}/photobooth-${DATE}.db"

    if [[ ! -f "$db_file" ]]; then
        log "${YELLOW}[WARNING]${NC} Database not found: $db_file"
        return 1
    fi

    log "Backing up database..."

    # Use SQLite backup command for consistency (handles locks properly)
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$db_file" ".backup '$backup_file'"
    else
        # Fallback to copy if sqlite3 not available
        cp "$db_file" "$backup_file"
    fi

    if [[ -f "$backup_file" ]]; then
        local size
        size=$(du -h "$backup_file" | cut -f1)
        log "${GREEN}[OK]${NC} Database backed up: photobooth-${DATE}.db (${size})"
        return 0
    else
        log "${RED}[ERROR]${NC} Database backup failed"
        return 1
    fi
}

# Backup configuration files
backup_config() {
    local config_backup="${BACKUP_DIR}/config-${DATE}.tar.gz"

    log "Backing up configuration..."

    local files_to_backup=()

    # Add files that exist
    [[ -f "${PHOTOBOOTH_DIR}/.env" ]] && files_to_backup+=("${PHOTOBOOTH_DIR}/.env")
    [[ -f "${PHOTOBOOTH_DIR}/docker-compose.yml" ]] && files_to_backup+=("${PHOTOBOOTH_DIR}/docker-compose.yml")
    [[ -f "${PHOTOBOOTH_DIR}/docker-compose.override.yml" ]] && files_to_backup+=("${PHOTOBOOTH_DIR}/docker-compose.override.yml")

    if [[ ${#files_to_backup[@]} -eq 0 ]]; then
        log "${YELLOW}[WARNING]${NC} No configuration files to backup"
        return 0
    fi

    tar -czf "$config_backup" "${files_to_backup[@]}" 2>/dev/null || true

    if [[ -f "$config_backup" ]]; then
        local size
        size=$(du -h "$config_backup" | cut -f1)
        log "${GREEN}[OK]${NC} Config backed up: config-${DATE}.tar.gz (${size})"
        return 0
    else
        log "${YELLOW}[WARNING]${NC} Config backup may have failed"
        return 0
    fi
}

# Backup photos (optional, can be large)
backup_photos() {
    local photos_dir="${DATA_DIR}/photos"
    local photos_backup="${BACKUP_DIR}/photos-${DATE}.tar.gz"

    if [[ ! -d "$photos_dir" ]]; then
        log "${YELLOW}[WARNING]${NC} Photos directory not found"
        return 0
    fi

    local photo_count
    photo_count=$(find "$photos_dir" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$photo_count" -eq 0 ]]; then
        log "No photos to backup"
        return 0
    fi

    log "Backing up ${photo_count} photos (this may take a while)..."

    tar -czf "$photos_backup" -C "$(dirname "$photos_dir")" "$(basename "$photos_dir")" 2>/dev/null

    if [[ -f "$photos_backup" ]]; then
        local size
        size=$(du -h "$photos_backup" | cut -f1)
        log "${GREEN}[OK]${NC} Photos backed up: photos-${DATE}.tar.gz (${size})"
        return 0
    else
        log "${RED}[ERROR]${NC} Photos backup failed"
        return 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up old backups (keeping last ${MAX_BACKUPS})..."

    local deleted=0

    # Remove old database backups
    while IFS= read -r file; do
        rm -f "$file"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "photobooth-*.db" -type f -mtime +${MAX_BACKUPS} 2>/dev/null || true)

    # Remove old config backups
    while IFS= read -r file; do
        rm -f "$file"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "config-*.tar.gz" -type f -mtime +${MAX_BACKUPS} 2>/dev/null || true)

    # Remove old photo backups (if any)
    while IFS= read -r file; do
        rm -f "$file"
        ((deleted++))
    done < <(find "$BACKUP_DIR" -name "photos-*.tar.gz" -type f -mtime +${MAX_BACKUPS} 2>/dev/null || true)

    if [[ "$deleted" -gt 0 ]]; then
        log "Removed ${deleted} old backup file(s)"
    fi
}

# List existing backups
list_backups() {
    echo ""
    echo "Existing backups in ${BACKUP_DIR}:"
    echo "----------------------------------------"

    if [[ -d "$BACKUP_DIR" ]]; then
        ls -lh "$BACKUP_DIR"/*.db "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
    else
        echo "Backup directory does not exist"
    fi

    echo "----------------------------------------"
}

# Print summary
print_summary() {
    local backup_size
    backup_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "unknown")

    echo ""
    echo "=========================================="
    echo "PhotoBooth Backup Complete"
    echo "=========================================="
    echo "Timestamp:    $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Backup ID:    ${DATE}"
    echo "Backup Dir:   ${BACKUP_DIR}"
    echo "Total Size:   ${backup_size}"
    echo "Full Backup:  ${FULL_BACKUP}"
    echo "=========================================="
}

# Main
main() {
    log "Starting PhotoBooth backup..."

    setup
    backup_database
    backup_config

    if [[ "$FULL_BACKUP" == true ]]; then
        backup_photos
    fi

    cleanup_old_backups
    list_backups
    print_summary

    log "${GREEN}Backup completed successfully${NC}"
}

main "$@"
