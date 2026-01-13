#!/bin/bash
#
# PhotoBooth Raspberry Pi 5 Master Setup Script
# Idempotent, resumable setup for fresh installations
#
# Usage: sudo ./setup.sh [--resume] [--phase <phase-name>] [--dry-run]
#
# Options:
#   --resume     Resume from last checkpoint
#   --phase      Run only specified phase
#   --dry-run    Show what would be done without making changes
#   --help       Show this help message
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/pi/photobooth}"
CHECKPOINT_FILE="${PHOTOBOOTH_DIR}/.setup-checkpoint"
LOG_FILE="/var/log/photobooth-setup.log"
PHASES_DIR="${SCRIPT_DIR}/setup-phases"

# Default values from environment or defaults
export WIFI_SSID="${WIFI_SSID:-photobooth}"
export WIFI_PASSWORD="${WIFI_PASSWORD:-photobooth-1998}"
export WIFI_CHANNEL="${WIFI_CHANNEL:-6}"
export PI_IP="${PI_IP:-192.168.4.1}"
export TIMEZONE="${TIMEZONE:-Africa/Kigali}"
export COUNTRY_CODE="${COUNTRY_CODE:-RW}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Phase definitions (in order)
PHASES=(
    "01-system"
    "02-docker"
    "03-cups"
    "04-wifi-ap"
    "05-printer"
    "06-deploy"
    "07-services"
    "08-security"
    "09-verify"
)

# State
DRY_RUN=false
RESUME=false
SINGLE_PHASE=""

# Logging
log() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$1" | tee -a "$LOG_FILE" 2>/dev/null || echo -e "$1"
}

log_header() {
    log ""
    log "${BLUE}=========================================="
    log "$1"
    log "==========================================${NC}"
    log ""
}

log_phase() {
    log "${CYAN}[PHASE]${NC} $1"
}

log_ok() {
    log "${GREEN}[OK]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

# Show usage
usage() {
    cat << EOF
PhotoBooth Raspberry Pi 5 Setup Script

Usage: sudo $0 [OPTIONS]

Options:
    --resume        Resume from last checkpoint
    --phase NAME    Run only the specified phase
    --dry-run       Show what would be done without making changes
    --list-phases   List all available phases
    --status        Show current setup status
    --reset         Reset checkpoint (start from beginning)
    -h, --help      Show this help message

Phases:
    01-system       System updates, timezone, locale
    02-docker       Docker and Docker Compose installation
    03-cups         CUPS print server installation
    04-wifi-ap      Wi-Fi Access Point setup (hostapd, dnsmasq)
    05-printer      Canon Selphy CP1500 printer configuration
    06-deploy       Application deployment
    07-services     Systemd services setup
    08-security     Security hardening
    09-verify       Final verification

Examples:
    sudo $0                     # Run full setup
    sudo $0 --resume            # Resume from last checkpoint
    sudo $0 --phase 04-wifi-ap  # Run only Wi-Fi AP setup
    sudo $0 --dry-run           # Show what would be done

Environment Variables:
    WIFI_SSID        Wi-Fi network name (default: photobooth)
    WIFI_PASSWORD    Wi-Fi password (default: photobooth-1998)
    WIFI_CHANNEL     Wi-Fi channel (default: 6)
    PI_IP            Raspberry Pi IP address (default: 192.168.4.1)
    TIMEZONE         System timezone (default: Africa/Kigali)
    COUNTRY_CODE     Wi-Fi country code (default: RW)

EOF
    exit 0
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --resume)
                RESUME=true
                shift
                ;;
            --phase)
                SINGLE_PHASE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --list-phases)
                list_phases
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            --reset)
                reset_checkpoint
                exit 0
                ;;
            -h|--help)
                usage
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_warn "This does not appear to be a Raspberry Pi"
        log_warn "Some features may not work correctly"
        read -p "Continue anyway? (y/n): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Initialize
init() {
    # Create directories
    mkdir -p "$PHOTOBOOTH_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$PHASES_DIR"

    # Start logging
    log_header "PhotoBooth Setup Script"
    log_info "Started at $(date)"
    log_info "Photobooth directory: $PHOTOBOOTH_DIR"
    log_info "Dry run: $DRY_RUN"

    if [[ "$DRY_RUN" == true ]]; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi
}

# Checkpoint management
get_checkpoint() {
    if [[ -f "$CHECKPOINT_FILE" ]]; then
        cat "$CHECKPOINT_FILE"
    else
        echo ""
    fi
}

set_checkpoint() {
    local phase="$1"
    if [[ "$DRY_RUN" == false ]]; then
        echo "$phase" > "$CHECKPOINT_FILE"
        log_info "Checkpoint saved: $phase"
    fi
}

clear_checkpoint() {
    rm -f "$CHECKPOINT_FILE"
}

reset_checkpoint() {
    if [[ -f "$CHECKPOINT_FILE" ]]; then
        rm -f "$CHECKPOINT_FILE"
        log_ok "Checkpoint reset. Next run will start from beginning."
    else
        log_info "No checkpoint to reset."
    fi
}

# Should we run this phase?
should_run_phase() {
    local phase="$1"
    local checkpoint
    checkpoint=$(get_checkpoint)

    # If running single phase, only run that phase
    if [[ -n "$SINGLE_PHASE" ]]; then
        [[ "$phase" == "$SINGLE_PHASE" ]] && return 0 || return 1
    fi

    # If no checkpoint, run all phases
    if [[ -z "$checkpoint" ]]; then
        return 0
    fi

    # If not resuming, run all phases
    if [[ "$RESUME" == false ]]; then
        return 0
    fi

    # Find if we've passed the checkpoint
    local found_checkpoint=false
    for p in "${PHASES[@]}"; do
        if [[ "$p" == "$checkpoint" ]]; then
            found_checkpoint=true
            continue
        fi
        if [[ "$found_checkpoint" == true && "$p" == "$phase" ]]; then
            return 0
        fi
    done

    return 1
}

# List phases
list_phases() {
    echo "Available phases:"
    echo ""
    for phase in "${PHASES[@]}"; do
        local script="${PHASES_DIR}/${phase}.sh"
        local status="[not found]"
        if [[ -f "$script" ]]; then
            status="[ready]"
        fi
        echo "  ${phase}  ${status}"
    done
    echo ""
    echo "Current checkpoint: $(get_checkpoint || echo 'none')"
}

# Show status
show_status() {
    log_header "Setup Status"

    local checkpoint
    checkpoint=$(get_checkpoint)

    echo "Checkpoint: ${checkpoint:-none}"
    echo ""
    echo "Phase Status:"

    local passed_checkpoint=false
    for phase in "${PHASES[@]}"; do
        local status_icon
        local status_text

        if [[ -z "$checkpoint" ]]; then
            status_icon="${YELLOW}○${NC}"
            status_text="pending"
        elif [[ "$phase" == "$checkpoint" ]]; then
            status_icon="${GREEN}●${NC}"
            status_text="completed (checkpoint)"
            passed_checkpoint=true
        elif [[ "$passed_checkpoint" == false ]]; then
            status_icon="${GREEN}●${NC}"
            status_text="completed"
        else
            status_icon="${YELLOW}○${NC}"
            status_text="pending"
        fi

        echo -e "  ${status_icon} ${phase}: ${status_text}"
    done
}

# Run a phase
run_phase() {
    local phase="$1"
    local script="${PHASES_DIR}/${phase}.sh"

    log_phase "Running phase: $phase"

    if [[ ! -f "$script" ]]; then
        log_warn "Phase script not found: $script"
        log_info "Creating placeholder for $phase..."

        # Create placeholder script
        if [[ "$DRY_RUN" == false ]]; then
            create_phase_placeholder "$phase"
        fi
        return 0
    fi

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would execute: $script"
        return 0
    fi

    # Make script executable
    chmod +x "$script"

    # Run the phase script
    if bash "$script"; then
        log_ok "Phase $phase completed successfully"
        set_checkpoint "$phase"
    else
        log_error "Phase $phase failed"
        exit 1
    fi
}

# Create placeholder phase script
create_phase_placeholder() {
    local phase="$1"
    local script="${PHASES_DIR}/${phase}.sh"

    cat > "$script" << 'PLACEHOLDER'
#!/bin/bash
# Placeholder phase script
# This will be implemented with actual setup logic

set -euo pipefail

echo "Phase placeholder - not yet implemented"
echo "Please implement this phase or skip it"

# Exit successfully to allow setup to continue
exit 0
PLACEHOLDER

    chmod +x "$script"
}

# Main setup routine
main() {
    parse_args "$@"
    check_root
    check_raspberry_pi
    init

    log_header "Starting Setup"

    local phases_run=0
    local phases_skipped=0

    for phase in "${PHASES[@]}"; do
        if should_run_phase "$phase"; then
            run_phase "$phase"
            ((phases_run++))
        else
            log_info "Skipping phase: $phase"
            ((phases_skipped++))
        fi
    done

    # Clear checkpoint on successful completion
    if [[ -z "$SINGLE_PHASE" ]]; then
        clear_checkpoint
    fi

    log_header "Setup Complete"
    log_info "Phases run: $phases_run"
    log_info "Phases skipped: $phases_skipped"
    log_info "Completed at $(date)"

    if [[ "$DRY_RUN" == false ]]; then
        echo ""
        echo "=========================================="
        echo "PhotoBooth Setup Complete!"
        echo "=========================================="
        echo ""
        echo "Next steps:"
        echo "  1. Reboot the Raspberry Pi: sudo reboot"
        echo "  2. Connect to Wi-Fi: $WIFI_SSID"
        echo "  3. Open browser: https://$PI_IP or https://photobooth.local"
        echo ""
        echo "For troubleshooting:"
        echo "  - Check logs: journalctl -u photobooth -f"
        echo "  - Run diagnostics: ${SCRIPT_DIR}/network/test-network.sh"
        echo "  - View status: ${SCRIPT_DIR}/photobooth-ctl.sh status"
        echo ""
    fi
}

# Run main
main "$@"
