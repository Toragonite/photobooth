#!/bin/bash
#
# PhotoBooth Manager - Interactive Management Script
# Designed for easy use via smartphone SSH
#
# Usage: ./photobooth-manager.sh
#

set -euo pipefail

# Configuration
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/toragonite/Documents/photobooth}"
PRINTER_NAME="${PRINTER_NAME:-SelphyCP1500}"
AP_CONNECTION_NAME="photobooth-ap"
WIFI_INTERFACE="wlan0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Helper functions
clear_screen() {
    clear 2>/dev/null || printf '\033[2J\033[H'
}

print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}${BOLD}       PhotoBooth Manager v1.0         ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
    echo ""
}

print_status_bar() {
    local docker_status network_mode printer_status

    # Docker status
    if docker ps &>/dev/null && docker ps | grep -q photobooth; then
        docker_status="${GREEN}Running${NC}"
    else
        docker_status="${RED}Stopped${NC}"
    fi

    # Network mode
    if nmcli connection show --active 2>/dev/null | grep -q "$AP_CONNECTION_NAME"; then
        network_mode="${YELLOW}AP Mode${NC}"
    else
        network_mode="${GREEN}Client${NC}"
    fi

    # Printer status - check USB connection first
    if ! lsusb 2>/dev/null | grep -qi "canon"; then
        printer_status="${RED}Disconnected${NC}"
    elif lpstat -p "$PRINTER_NAME" 2>/dev/null | grep -qi "idle"; then
        printer_status="${GREEN}Ready${NC}"
    elif lpstat -p "$PRINTER_NAME" 2>/dev/null | grep -qi "printing"; then
        printer_status="${YELLOW}Printing${NC}"
    elif lpstat -p "$PRINTER_NAME" &>/dev/null; then
        printer_status="${YELLOW}Configured${NC}"
    else
        printer_status="${RED}Not Setup${NC}"
    fi

    echo -e "${BOLD}Status:${NC} Docker: $docker_status | Network: $network_mode | Printer: $printer_status"
    echo ""
}

press_enter() {
    echo ""
    echo -e "${CYAN}Press Enter to continue...${NC}"
    read -r
}

confirm_action() {
    local message="$1"
    echo ""
    echo -e "${YELLOW}$message${NC}"
    echo -n "Continue? (y/n): "
    read -r confirm
    [[ "$confirm" == "y" || "$confirm" == "Y" ]]
}

select_option() {
    local prompt="$1"
    shift
    local options=("$@")
    local selected=0
    local key

    echo -e "${BOLD}$prompt${NC}"
    echo ""

    for i in "${!options[@]}"; do
        echo "  $((i+1)). ${options[$i]}"
    done
    echo "  0. Back"
    echo ""
    echo -n "Select [0-${#options[@]}]: "
    read -r selected

    echo "$selected"
}

# ============================================
# MAIN MENU
# ============================================
main_menu() {
    while true; do
        clear_screen
        print_header
        print_status_bar

        echo -e "${BOLD}Main Menu${NC}"
        echo ""
        echo "  1. Service Management"
        echo "  2. Network Management"
        echo "  3. Printer Management"
        echo "  4. System Information"
        echo "  5. Maintenance"
        echo "  6. Quick Actions"
        echo ""
        echo "  0. Exit"
        echo ""
        echo -n "Select [0-6]: "
        read -r choice

        case $choice in
            1) service_menu ;;
            2) network_menu ;;
            3) printer_menu ;;
            4) system_info_menu ;;
            5) maintenance_menu ;;
            6) quick_actions_menu ;;
            0)
                clear_screen
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *) ;;
        esac
    done
}

# ============================================
# SERVICE MANAGEMENT
# ============================================
service_menu() {
    while true; do
        clear_screen
        print_header

        echo -e "${BOLD}Service Management${NC}"
        echo ""
        echo "  1. View service status"
        echo "  2. Start PhotoBooth"
        echo "  3. Stop PhotoBooth"
        echo "  4. Restart PhotoBooth"
        echo "  5. View logs (live)"
        echo "  6. View recent logs"
        echo "  7. Rebuild containers"
        echo ""
        echo "  0. Back to Main Menu"
        echo ""
        echo -n "Select [0-7]: "
        read -r choice

        case $choice in
            1) service_status ;;
            2) service_start ;;
            3) service_stop ;;
            4) service_restart ;;
            5) service_logs_live ;;
            6) service_logs_recent ;;
            7) service_rebuild ;;
            0) return ;;
            *) ;;
        esac
    done
}

service_status() {
    clear_screen
    echo -e "${BOLD}Service Status${NC}"
    echo ""

    echo -e "${CYAN}=== Systemd Services ===${NC}"
    for service in photobooth.service photobooth-watchdog.timer photobooth-backup.timer photobooth-welcome-print.service photobooth-network.service; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo -e "  $service: ${GREEN}active${NC}"
        elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo -e "  $service: ${YELLOW}enabled (inactive)${NC}"
        else
            echo -e "  $service: ${RED}disabled${NC}"
        fi
    done

    echo ""
    echo -e "${CYAN}=== Docker Containers ===${NC}"
    cd "$PHOTOBOOTH_DIR" 2>/dev/null && docker compose ps 2>/dev/null || echo "  Unable to get container status"

    press_enter
}

service_start() {
    clear_screen
    echo -e "${BOLD}Starting PhotoBooth...${NC}"
    echo ""

    sudo systemctl start photobooth.service
    sleep 3

    if systemctl is-active --quiet photobooth.service; then
        echo -e "${GREEN}PhotoBooth started successfully!${NC}"
    else
        echo -e "${RED}Failed to start PhotoBooth${NC}"
        echo ""
        echo "Recent logs:"
        journalctl -u photobooth.service -n 10 --no-pager
    fi

    press_enter
}

service_stop() {
    if confirm_action "This will stop the PhotoBooth service."; then
        clear_screen
        echo -e "${BOLD}Stopping PhotoBooth...${NC}"
        echo ""

        sudo systemctl stop photobooth.service

        echo -e "${GREEN}PhotoBooth stopped.${NC}"
    fi

    press_enter
}

service_restart() {
    clear_screen
    echo -e "${BOLD}Restarting PhotoBooth...${NC}"
    echo ""

    sudo systemctl restart photobooth.service
    sleep 3

    if systemctl is-active --quiet photobooth.service; then
        echo -e "${GREEN}PhotoBooth restarted successfully!${NC}"
    else
        echo -e "${RED}Failed to restart PhotoBooth${NC}"
    fi

    press_enter
}

service_logs_live() {
    clear_screen
    echo -e "${BOLD}Live Logs (Press Ctrl+C to exit)${NC}"
    echo ""

    journalctl -u photobooth.service -f
}

service_logs_recent() {
    clear_screen
    echo -e "${BOLD}Recent Logs (last 50 lines)${NC}"
    echo ""

    journalctl -u photobooth.service -n 50 --no-pager

    press_enter
}

service_rebuild() {
    if confirm_action "This will rebuild Docker containers. Service will be temporarily unavailable."; then
        clear_screen
        echo -e "${BOLD}Rebuilding containers...${NC}"
        echo ""

        cd "$PHOTOBOOTH_DIR"
        sudo systemctl stop photobooth.service
        docker compose build --no-cache
        sudo systemctl start photobooth.service

        echo ""
        echo -e "${GREEN}Rebuild complete!${NC}"
    fi

    press_enter
}

# ============================================
# NETWORK MANAGEMENT
# ============================================
network_menu() {
    while true; do
        clear_screen
        print_header

        # Show current mode
        local current_mode
        if nmcli connection show --active 2>/dev/null | grep -q "$AP_CONNECTION_NAME"; then
            current_mode="${YELLOW}AP Mode (photobooth WiFi)${NC}"
        else
            current_mode="${GREEN}Client Mode (connected to router)${NC}"
        fi

        echo -e "${BOLD}Network Management${NC}"
        echo -e "Current: $current_mode"
        echo ""
        echo "  1. View network status"
        echo "  2. Switch to AP Mode (offline)"
        echo "  3. Switch to Client Mode (online)"
        echo "  4. Auto-detect mode"
        echo "  5. View connected devices (AP mode)"
        echo "  6. Show WiFi credentials"
        echo ""
        echo "  0. Back to Main Menu"
        echo ""
        echo -n "Select [0-6]: "
        read -r choice

        case $choice in
            1) network_status ;;
            2) network_ap_mode ;;
            3) network_client_mode ;;
            4) network_auto_mode ;;
            5) network_connected_devices ;;
            6) network_show_credentials ;;
            0) return ;;
            *) ;;
        esac
    done
}

network_status() {
    clear_screen
    echo -e "${BOLD}Network Status${NC}"
    echo ""

    echo -e "${CYAN}=== Device Status ===${NC}"
    nmcli device status

    echo ""
    echo -e "${CYAN}=== Active Connections ===${NC}"
    nmcli connection show --active

    echo ""
    echo -e "${CYAN}=== IP Addresses ===${NC}"
    ip addr show "$WIFI_INTERFACE" 2>/dev/null | grep "inet " || echo "  No IP assigned"

    echo ""
    echo -e "${CYAN}=== Internet Connectivity ===${NC}"
    if ping -c 1 -W 3 8.8.8.8 &>/dev/null; then
        echo -e "  ${GREEN}Internet is available${NC}"
    else
        echo -e "  ${RED}No internet connection${NC}"
    fi

    press_enter
}

network_ap_mode() {
    if confirm_action "Switch to AP Mode? You'll need to connect to 'photobooth' WiFi."; then
        clear_screen
        echo -e "${BOLD}Switching to AP Mode...${NC}"
        echo ""

        sudo "$PHOTOBOOTH_DIR/scripts/network/auto-network-mode.sh" --force-ap

        echo ""
        echo -e "${GREEN}AP Mode activated!${NC}"
        echo ""
        echo "Connect to:"
        echo "  SSID: photobooth"
        echo "  Password: photobooth-1998"
        echo "  Pi IP: 192.168.4.1"
    fi

    press_enter
}

network_client_mode() {
    if confirm_action "Switch to Client Mode? Pi will connect to available WiFi."; then
        clear_screen
        echo -e "${BOLD}Switching to Client Mode...${NC}"
        echo ""

        sudo "$PHOTOBOOTH_DIR/scripts/network/auto-network-mode.sh" --force-client

        echo ""
        echo -e "${GREEN}Client Mode activated!${NC}"
        echo ""
        echo "Checking connection..."
        sleep 3
        ip addr show "$WIFI_INTERFACE" | grep "inet " || echo "Waiting for IP..."
    fi

    press_enter
}

network_auto_mode() {
    clear_screen
    echo -e "${BOLD}Auto-detecting network mode...${NC}"
    echo ""

    sudo "$PHOTOBOOTH_DIR/scripts/network/auto-network-mode.sh" --auto

    press_enter
}

network_connected_devices() {
    clear_screen
    echo -e "${BOLD}Connected Devices (AP Mode)${NC}"
    echo ""

    if ! nmcli connection show --active 2>/dev/null | grep -q "$AP_CONNECTION_NAME"; then
        echo -e "${YELLOW}Not in AP mode. Switch to AP mode first.${NC}"
    else
        echo -e "${CYAN}=== DHCP Leases ===${NC}"
        cat /var/lib/NetworkManager/dnsmasq-*.leases 2>/dev/null || echo "  No leases found"

        echo ""
        echo -e "${CYAN}=== ARP Table ===${NC}"
        arp -a 2>/dev/null | grep -v "incomplete" || echo "  No devices found"
    fi

    press_enter
}

network_show_credentials() {
    clear_screen
    echo -e "${BOLD}WiFi Credentials${NC}"
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  SSID:     ${BOLD}photobooth${NC}                  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  Password: ${BOLD}photobooth-1998${NC}             ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  Pi IP:    ${BOLD}192.168.4.1${NC}                 ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "Web Access: https://192.168.4.1"

    press_enter
}

# ============================================
# PRINTER MANAGEMENT
# ============================================
printer_menu() {
    while true; do
        clear_screen
        print_header

        echo -e "${BOLD}Printer Management${NC}"
        echo ""
        echo "  1. View printer status"
        echo "  2. View print queue"
        echo "  3. Cancel all print jobs"
        echo "  4. Print test page"
        echo "  5. Clear printer errors"
        echo "  6. Restart CUPS service"
        echo ""
        echo "  0. Back to Main Menu"
        echo ""
        echo -n "Select [0-6]: "
        read -r choice

        case $choice in
            1) printer_status ;;
            2) printer_queue ;;
            3) printer_cancel_all ;;
            4) printer_test_page ;;
            5) printer_clear_errors ;;
            6) printer_restart_cups ;;
            0) return ;;
            *) ;;
        esac
    done
}

printer_status() {
    clear_screen
    echo -e "${BOLD}Printer Status${NC}"
    echo ""

    echo -e "${CYAN}=== Printer Info ===${NC}"
    lpstat -p "$PRINTER_NAME" 2>/dev/null || echo "  Printer not configured"

    echo ""
    echo -e "${CYAN}=== CUPS Status ===${NC}"
    systemctl status cups --no-pager -l 2>/dev/null | head -10 || echo "  CUPS not running"

    echo ""
    echo -e "${CYAN}=== USB Devices ===${NC}"
    lsusb 2>/dev/null | grep -i "canon\|selphy" || echo "  No Canon printer detected"

    echo ""
    echo -e "${CYAN}=== usblp Module ===${NC}"
    if lsmod | grep -q usblp; then
        echo -e "  ${RED}usblp is loaded (may cause issues)${NC}"
    else
        echo -e "  ${GREEN}usblp is not loaded (good)${NC}"
    fi

    press_enter
}

printer_queue() {
    clear_screen
    echo -e "${BOLD}Print Queue${NC}"
    echo ""

    lpq -P "$PRINTER_NAME" 2>/dev/null || echo "No jobs in queue"

    echo ""
    echo -e "${CYAN}=== All Queues ===${NC}"
    lpstat -o 2>/dev/null || echo "No pending jobs"

    press_enter
}

printer_cancel_all() {
    if confirm_action "Cancel all print jobs?"; then
        clear_screen
        echo -e "${BOLD}Cancelling all jobs...${NC}"
        echo ""

        cancel -a 2>/dev/null || true
        lprm - 2>/dev/null || true

        echo -e "${GREEN}All print jobs cancelled.${NC}"
    fi

    press_enter
}

printer_test_page() {
    if confirm_action "Print a test page? This will use paper and ink."; then
        clear_screen
        echo -e "${BOLD}Printing test page...${NC}"
        echo ""

        # Create simple test file
        echo "PhotoBooth Test Print - $(date)" | lp -d "$PRINTER_NAME" 2>/dev/null

        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}Test page sent to printer.${NC}"
        else
            echo -e "${RED}Failed to send test page.${NC}"
        fi
    fi

    press_enter
}

printer_clear_errors() {
    clear_screen
    echo -e "${BOLD}Clearing printer errors...${NC}"
    echo ""

    sudo cupsenable "$PRINTER_NAME" 2>/dev/null || true
    sudo cupsdisable "$PRINTER_NAME" 2>/dev/null || true
    sudo cupsenable "$PRINTER_NAME" 2>/dev/null || true

    echo -e "${GREEN}Printer errors cleared.${NC}"

    press_enter
}

printer_restart_cups() {
    if confirm_action "Restart CUPS service?"; then
        clear_screen
        echo -e "${BOLD}Restarting CUPS...${NC}"
        echo ""

        sudo systemctl restart cups
        sleep 2

        if systemctl is-active --quiet cups; then
            echo -e "${GREEN}CUPS restarted successfully.${NC}"
        else
            echo -e "${RED}Failed to restart CUPS.${NC}"
        fi
    fi

    press_enter
}

# ============================================
# SYSTEM INFORMATION
# ============================================
system_info_menu() {
    while true; do
        clear_screen
        print_header

        echo -e "${BOLD}System Information${NC}"
        echo ""
        echo "  1. System overview"
        echo "  2. Disk usage"
        echo "  3. Memory usage"
        echo "  4. CPU temperature"
        echo "  5. Network interfaces"
        echo "  6. Docker stats"
        echo ""
        echo "  0. Back to Main Menu"
        echo ""
        echo -n "Select [0-6]: "
        read -r choice

        case $choice in
            1) system_overview ;;
            2) system_disk ;;
            3) system_memory ;;
            4) system_temperature ;;
            5) system_network ;;
            6) system_docker_stats ;;
            0) return ;;
            *) ;;
        esac
    done
}

system_overview() {
    clear_screen
    echo -e "${BOLD}System Overview${NC}"
    echo ""

    echo -e "${CYAN}=== Hostname ===${NC}"
    hostname

    echo ""
    echo -e "${CYAN}=== Uptime ===${NC}"
    uptime

    echo ""
    echo -e "${CYAN}=== OS ===${NC}"
    cat /etc/os-release 2>/dev/null | grep "PRETTY_NAME" | cut -d'"' -f2

    echo ""
    echo -e "${CYAN}=== Kernel ===${NC}"
    uname -r

    echo ""
    echo -e "${CYAN}=== CPU ===${NC}"
    cat /proc/cpuinfo 2>/dev/null | grep "Model" | head -1 || lscpu | grep "Model name"

    press_enter
}

system_disk() {
    clear_screen
    echo -e "${BOLD}Disk Usage${NC}"
    echo ""

    df -h | grep -E "^/dev|Filesystem"

    echo ""
    echo -e "${CYAN}=== PhotoBooth Directory ===${NC}"
    du -sh "$PHOTOBOOTH_DIR" 2>/dev/null || echo "  Unable to calculate"

    echo ""
    echo -e "${CYAN}=== Docker ===${NC}"
    docker system df 2>/dev/null || echo "  Unable to get Docker disk usage"

    press_enter
}

system_memory() {
    clear_screen
    echo -e "${BOLD}Memory Usage${NC}"
    echo ""

    free -h

    echo ""
    echo -e "${CYAN}=== Top Memory Processes ===${NC}"
    ps aux --sort=-%mem | head -6

    press_enter
}

system_temperature() {
    clear_screen
    echo -e "${BOLD}CPU Temperature${NC}"
    echo ""

    if [[ -f /sys/class/thermal/thermal_zone0/temp ]]; then
        local temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        local temp_c=$((temp / 1000))

        if [[ $temp_c -lt 50 ]]; then
            echo -e "  Temperature: ${GREEN}${temp_c}°C${NC} (Cool)"
        elif [[ $temp_c -lt 70 ]]; then
            echo -e "  Temperature: ${YELLOW}${temp_c}°C${NC} (Warm)"
        else
            echo -e "  Temperature: ${RED}${temp_c}°C${NC} (Hot!)"
        fi
    else
        vcgencmd measure_temp 2>/dev/null || echo "  Unable to read temperature"
    fi

    press_enter
}

system_network() {
    clear_screen
    echo -e "${BOLD}Network Interfaces${NC}"
    echo ""

    ip addr show

    press_enter
}

system_docker_stats() {
    clear_screen
    echo -e "${BOLD}Docker Stats (Press Ctrl+C to exit)${NC}"
    echo ""

    docker stats --no-stream 2>/dev/null || echo "Docker not running"

    press_enter
}

# ============================================
# MAINTENANCE
# ============================================
maintenance_menu() {
    while true; do
        clear_screen
        print_header

        echo -e "${BOLD}Maintenance${NC}"
        echo ""
        echo "  1. Update from Git"
        echo "  2. Clean Docker resources"
        echo "  3. Clear old photos"
        echo "  4. Backup database"
        echo "  5. View system logs"
        echo "  6. Run verification"
        echo ""
        echo -e "  ${RED}7. Reboot Pi${NC}"
        echo -e "  ${RED}8. Shutdown Pi${NC}"
        echo ""
        echo "  0. Back to Main Menu"
        echo ""
        echo -n "Select [0-8]: "
        read -r choice

        case $choice in
            1) maintenance_git_update ;;
            2) maintenance_docker_clean ;;
            3) maintenance_clear_photos ;;
            4) maintenance_backup_db ;;
            5) maintenance_system_logs ;;
            6) maintenance_verify ;;
            7) maintenance_reboot ;;
            8) maintenance_shutdown ;;
            0) return ;;
            *) ;;
        esac
    done
}

maintenance_git_update() {
    if confirm_action "Pull latest changes from Git?"; then
        clear_screen
        echo -e "${BOLD}Updating from Git...${NC}"
        echo ""

        cd "$PHOTOBOOTH_DIR"
        git fetch origin
        git status

        echo ""
        echo -n "Proceed with pull? (y/n): "
        read -r confirm

        if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
            git pull
            echo ""
            echo -e "${GREEN}Update complete!${NC}"
            echo ""
            echo "You may need to restart services for changes to take effect."
        fi
    fi

    press_enter
}

maintenance_docker_clean() {
    if confirm_action "Clean unused Docker resources?"; then
        clear_screen
        echo -e "${BOLD}Cleaning Docker resources...${NC}"
        echo ""

        docker system prune -f

        echo ""
        echo -e "${GREEN}Cleanup complete!${NC}"
    fi

    press_enter
}

maintenance_clear_photos() {
    clear_screen
    echo -e "${BOLD}Clear Old Photos${NC}"
    echo ""

    local photo_dir="$PHOTOBOOTH_DIR/data/photos"

    if [[ -d "$photo_dir" ]]; then
        local count=$(find "$photo_dir" -type f -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l)
        local size=$(du -sh "$photo_dir" 2>/dev/null | cut -f1)

        echo "Photos directory: $photo_dir"
        echo "Total photos: $count"
        echo "Total size: $size"
        echo ""

        echo "Options:"
        echo "  1. Delete photos older than 7 days"
        echo "  2. Delete photos older than 30 days"
        echo "  3. Delete ALL photos"
        echo "  0. Cancel"
        echo ""
        echo -n "Select: "
        read -r opt

        case $opt in
            1)
                if confirm_action "Delete photos older than 7 days?"; then
                    find "$photo_dir" -type f \( -name "*.jpg" -o -name "*.png" \) -mtime +7 -delete
                    echo -e "${GREEN}Old photos deleted.${NC}"
                fi
                ;;
            2)
                if confirm_action "Delete photos older than 30 days?"; then
                    find "$photo_dir" -type f \( -name "*.jpg" -o -name "*.png" \) -mtime +30 -delete
                    echo -e "${GREEN}Old photos deleted.${NC}"
                fi
                ;;
            3)
                if confirm_action "DELETE ALL PHOTOS? This cannot be undone!"; then
                    rm -rf "$photo_dir"/*
                    echo -e "${GREEN}All photos deleted.${NC}"
                fi
                ;;
        esac
    else
        echo "Photos directory not found."
    fi

    press_enter
}

maintenance_backup_db() {
    clear_screen
    echo -e "${BOLD}Backup Database${NC}"
    echo ""

    local db_file="$PHOTOBOOTH_DIR/data/photobooth.db"
    local backup_dir="$PHOTOBOOTH_DIR/backups"
    local backup_file="$backup_dir/photobooth_$(date +%Y%m%d_%H%M%S).db"

    mkdir -p "$backup_dir"

    if [[ -f "$db_file" ]]; then
        cp "$db_file" "$backup_file"
        echo -e "${GREEN}Database backed up to:${NC}"
        echo "  $backup_file"

        echo ""
        echo "Existing backups:"
        ls -lh "$backup_dir"/*.db 2>/dev/null | tail -5
    else
        echo -e "${RED}Database file not found.${NC}"
    fi

    press_enter
}

maintenance_system_logs() {
    clear_screen
    echo -e "${BOLD}System Logs${NC}"
    echo ""

    echo "Select log:"
    echo "  1. PhotoBooth service"
    echo "  2. Network service"
    echo "  3. CUPS (printer)"
    echo "  4. System boot"
    echo "  5. All errors (today)"
    echo "  0. Cancel"
    echo ""
    echo -n "Select: "
    read -r opt

    clear_screen

    case $opt in
        1) journalctl -u photobooth.service -n 100 --no-pager ;;
        2) journalctl -u photobooth-network.service -n 50 --no-pager ;;
        3) journalctl -u cups -n 50 --no-pager ;;
        4) journalctl -b -n 100 --no-pager ;;
        5) journalctl -p err --since today --no-pager ;;
    esac

    press_enter
}

maintenance_verify() {
    clear_screen
    echo -e "${BOLD}Running System Verification...${NC}"
    echo ""

    if [[ -f "$PHOTOBOOTH_DIR/scripts/setup-phases/09-verify.sh" ]]; then
        sudo "$PHOTOBOOTH_DIR/scripts/setup-phases/09-verify.sh" || true
    else
        echo "Verification script not found."
    fi

    press_enter
}

maintenance_reboot() {
    if confirm_action "REBOOT the Raspberry Pi?"; then
        echo ""
        echo -e "${YELLOW}Rebooting in 5 seconds...${NC}"
        sleep 5
        sudo reboot
    fi
}

maintenance_shutdown() {
    if confirm_action "SHUTDOWN the Raspberry Pi?"; then
        echo ""
        echo -e "${RED}Shutting down in 5 seconds...${NC}"
        sleep 5
        sudo shutdown now
    fi
}

# ============================================
# QUICK ACTIONS
# ============================================
quick_actions_menu() {
    while true; do
        clear_screen
        print_header

        echo -e "${BOLD}Quick Actions${NC}"
        echo ""
        echo "  1. Full restart (containers + services)"
        echo "  2. Emergency stop all"
        echo "  3. Reset to AP mode + restart"
        echo "  4. Health check"
        echo "  5. Fix common issues"
        echo ""
        echo "  0. Back to Main Menu"
        echo ""
        echo -n "Select [0-5]: "
        read -r choice

        case $choice in
            1) quick_full_restart ;;
            2) quick_emergency_stop ;;
            3) quick_reset_ap ;;
            4) quick_health_check ;;
            5) quick_fix_issues ;;
            0) return ;;
            *) ;;
        esac
    done
}

quick_full_restart() {
    if confirm_action "Perform full restart of PhotoBooth?"; then
        clear_screen
        echo -e "${BOLD}Full Restart...${NC}"
        echo ""

        echo "1. Stopping services..."
        sudo systemctl stop photobooth.service

        echo "2. Stopping containers..."
        cd "$PHOTOBOOTH_DIR"
        docker compose down 2>/dev/null || true

        echo "3. Starting services..."
        sudo systemctl start photobooth.service

        sleep 5

        echo ""
        if systemctl is-active --quiet photobooth.service; then
            echo -e "${GREEN}Full restart complete!${NC}"
        else
            echo -e "${RED}Service may have issues. Check logs.${NC}"
        fi
    fi

    press_enter
}

quick_emergency_stop() {
    if confirm_action "EMERGENCY STOP - Stop all PhotoBooth services?"; then
        clear_screen
        echo -e "${RED}${BOLD}EMERGENCY STOP${NC}"
        echo ""

        echo "Stopping systemd service..."
        sudo systemctl stop photobooth.service 2>/dev/null || true

        echo "Stopping Docker containers..."
        cd "$PHOTOBOOTH_DIR"
        docker compose down 2>/dev/null || true
        docker stop $(docker ps -q) 2>/dev/null || true

        echo ""
        echo -e "${YELLOW}All services stopped.${NC}"
    fi

    press_enter
}

quick_reset_ap() {
    if confirm_action "Reset to AP mode and restart PhotoBooth?"; then
        clear_screen
        echo -e "${BOLD}Reset to AP Mode...${NC}"
        echo ""

        echo "1. Switching to AP mode..."
        sudo "$PHOTOBOOTH_DIR/scripts/network/auto-network-mode.sh" --force-ap

        echo "2. Restarting PhotoBooth..."
        sudo systemctl restart photobooth.service

        sleep 3

        echo ""
        echo -e "${GREEN}Done!${NC}"
        echo ""
        echo "Connect to WiFi: photobooth"
        echo "Password: photobooth-1998"
        echo "Access: https://192.168.4.1"
    fi

    press_enter
}

quick_health_check() {
    clear_screen
    echo -e "${BOLD}Health Check${NC}"
    echo ""

    local issues=0

    # Check Docker
    echo -n "Docker service: "
    if systemctl is-active --quiet docker; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}NOT RUNNING${NC}"
        ((issues++))
    fi

    # Check PhotoBooth service
    echo -n "PhotoBooth service: "
    if systemctl is-active --quiet photobooth.service; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}NOT RUNNING${NC}"
        ((issues++))
    fi

    # Check containers
    echo -n "Docker containers: "
    if docker ps 2>/dev/null | grep -q photobooth; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}NOT RUNNING${NC}"
        ((issues++))
    fi

    # Check CUPS
    echo -n "CUPS service: "
    if systemctl is-active --quiet cups; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}NOT RUNNING${NC}"
        ((issues++))
    fi

    # Check printer
    echo -n "Printer: "
    if lpstat -p "$PRINTER_NAME" &>/dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}NOT CONFIGURED${NC}"
    fi

    # Check disk space
    echo -n "Disk space: "
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    if [[ $disk_usage -lt 80 ]]; then
        echo -e "${GREEN}OK (${disk_usage}% used)${NC}"
    elif [[ $disk_usage -lt 90 ]]; then
        echo -e "${YELLOW}WARNING (${disk_usage}% used)${NC}"
    else
        echo -e "${RED}CRITICAL (${disk_usage}% used)${NC}"
        ((issues++))
    fi

    # Check memory
    echo -n "Memory: "
    local mem_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    if [[ $mem_usage -lt 80 ]]; then
        echo -e "${GREEN}OK (${mem_usage}% used)${NC}"
    else
        echo -e "${YELLOW}HIGH (${mem_usage}% used)${NC}"
    fi

    # Check temperature
    echo -n "CPU temperature: "
    if [[ -f /sys/class/thermal/thermal_zone0/temp ]]; then
        local temp=$(($(cat /sys/class/thermal/thermal_zone0/temp) / 1000))
        if [[ $temp -lt 70 ]]; then
            echo -e "${GREEN}OK (${temp}°C)${NC}"
        else
            echo -e "${RED}HOT (${temp}°C)${NC}"
            ((issues++))
        fi
    else
        echo -e "${YELLOW}Unknown${NC}"
    fi

    echo ""
    if [[ $issues -eq 0 ]]; then
        echo -e "${GREEN}All checks passed!${NC}"
    else
        echo -e "${YELLOW}$issues issue(s) found.${NC}"
    fi

    press_enter
}

quick_fix_issues() {
    clear_screen
    echo -e "${BOLD}Fix Common Issues${NC}"
    echo ""

    echo "Select issue to fix:"
    echo "  1. Printer not working"
    echo "  2. Cannot connect to WiFi"
    echo "  3. Docker containers not starting"
    echo "  4. Service keeps crashing"
    echo "  5. Out of disk space"
    echo "  0. Cancel"
    echo ""
    echo -n "Select: "
    read -r opt

    clear_screen

    case $opt in
        1)
            echo -e "${BOLD}Fixing Printer Issues...${NC}"
            echo ""
            echo "1. Restarting CUPS..."
            sudo systemctl restart cups
            echo "2. Clearing print queue..."
            cancel -a 2>/dev/null || true
            echo "3. Re-enabling printer..."
            sudo cupsenable "$PRINTER_NAME" 2>/dev/null || true
            echo "4. Checking usblp module..."
            if lsmod | grep -q usblp; then
                echo "   Removing usblp module..."
                sudo rmmod usblp 2>/dev/null || true
            fi
            echo ""
            echo -e "${GREEN}Done. Try printing again.${NC}"
            echo "If still not working, unplug and replug the printer USB."
            ;;
        2)
            echo -e "${BOLD}Fixing WiFi Issues...${NC}"
            echo ""
            echo "1. Restarting NetworkManager..."
            sudo systemctl restart NetworkManager
            sleep 2
            echo "2. Scanning for networks..."
            nmcli device wifi rescan 2>/dev/null || true
            sleep 2
            echo "3. Current connections:"
            nmcli connection show
            echo ""
            echo -e "${GREEN}Done.${NC}"
            ;;
        3)
            echo -e "${BOLD}Fixing Docker Issues...${NC}"
            echo ""
            echo "1. Restarting Docker..."
            sudo systemctl restart docker
            sleep 3
            echo "2. Cleaning up..."
            docker system prune -f
            echo "3. Restarting PhotoBooth..."
            sudo systemctl restart photobooth.service
            echo ""
            echo -e "${GREEN}Done.${NC}"
            ;;
        4)
            echo -e "${BOLD}Fixing Service Crash Issues...${NC}"
            echo ""
            echo "1. Checking logs..."
            journalctl -u photobooth.service -n 20 --no-pager
            echo ""
            echo "2. Rebuilding containers..."
            cd "$PHOTOBOOTH_DIR"
            docker compose down
            docker compose build
            echo "3. Restarting service..."
            sudo systemctl restart photobooth.service
            echo ""
            echo -e "${GREEN}Done.${NC}"
            ;;
        5)
            echo -e "${BOLD}Freeing Disk Space...${NC}"
            echo ""
            echo "Current usage:"
            df -h /
            echo ""
            echo "1. Cleaning Docker..."
            docker system prune -af
            echo "2. Cleaning apt cache..."
            sudo apt-get clean
            echo "3. Cleaning journal logs..."
            sudo journalctl --vacuum-time=7d
            echo ""
            echo "New usage:"
            df -h /
            echo ""
            echo -e "${GREEN}Done.${NC}"
            ;;
    esac

    press_enter
}

# ============================================
# ENTRY POINT
# ============================================

# Check if running on Pi
if [[ ! -d "$PHOTOBOOTH_DIR" ]]; then
    # Try alternative paths
    if [[ -d "/home/pi/Documents/photobooth" ]]; then
        PHOTOBOOTH_DIR="/home/pi/Documents/photobooth"
    elif [[ -d "$(pwd)" ]] && [[ -f "$(pwd)/docker-compose.yml" ]]; then
        PHOTOBOOTH_DIR="$(pwd)"
    fi
fi

# Run main menu
main_menu
