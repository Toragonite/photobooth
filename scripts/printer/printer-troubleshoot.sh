#!/bin/bash
#
# PhotoBooth Printer Troubleshooter
# Comprehensive diagnostic and auto-recovery for Canon Selphy CP1500 printers
#
# Designed for offline operation on Raspberry Pi 5
# Supports multiple printers (multi-printer setup)
#
# Usage: ./printer-troubleshoot.sh [--auto-fix] [--verbose] [--printer NAME]
#

set -uo pipefail

# ============================================
# CONFIGURATION
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/photobooth/printer-troubleshoot.log"
PRINTER_CONFIG_DIR="/etc/cups/ppd"
CANON_VENDOR_ID="04a9"
SELPHY_CP1500_PRODUCT_ID="3302"
GUTENPRINT_DRIVER="gutenprint.5.3://canon-cp1300/expert"

# Default options
AUTO_FIX=false
VERBOSE=false
SPECIFIC_PRINTER=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================
# UTILITY FUNCTIONS
# ============================================
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Log to file
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE" 2>/dev/null || true

    # Display based on level
    case $level in
        INFO)  echo -e "${GREEN}[INFO]${NC} $message" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $message" ;;
        DEBUG) [[ "$VERBOSE" == true ]] && echo -e "${BLUE}[DEBUG]${NC} $message" ;;
        *)     echo "$message" ;;
    esac
}

print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}${BOLD}       PhotoBooth Printer Troubleshooter v2.0           ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}        Canon Selphy CP1500 Multi-Printer Support        ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================
# DIAGNOSTIC FUNCTIONS
# ============================================

# Check 1: USB Device Detection
check_usb_devices() {
    print_section "1. USB Device Detection"

    local usb_printers=()
    local issues=()

    # Check if lsusb is available
    if ! command -v lsusb &>/dev/null; then
        log ERROR "lsusb command not found. Install usbutils."
        issues+=("lsusb not available")
        return 1
    fi

    # Find all Canon Selphy CP1500 printers
    log DEBUG "Scanning USB bus for Canon printers..."

    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local bus=$(echo "$line" | grep -oP 'Bus \K\d+')
            local device=$(echo "$line" | grep -oP 'Device \K\d+')
            usb_printers+=("Bus${bus}-Dev${device}")
            log INFO "Found Canon printer: $line"
        fi
    done < <(lsusb 2>/dev/null | grep -i "${CANON_VENDOR_ID}:${SELPHY_CP1500_PRODUCT_ID}")

    local count=${#usb_printers[@]}

    if [[ $count -eq 0 ]]; then
        log WARN "No Canon Selphy CP1500 detected on USB"
        echo ""
        echo -e "${YELLOW}Possible causes:${NC}"
        echo "  - Printer not connected or powered off"
        echo "  - USB cable issue (use data cable, not charge-only)"
        echo "  - USB port problem"
        echo ""
        issues+=("No USB printer detected")
        return 1
    else
        log INFO "Detected $count Canon Selphy CP1500 printer(s)"
        echo ""

        # Show detailed USB info
        echo -e "${BOLD}USB Printers Detected:${NC}"
        lsusb -v 2>/dev/null | grep -A 15 "${CANON_VENDOR_ID}:${SELPHY_CP1500_PRODUCT_ID}" | \
            grep -E "idVendor|idProduct|iManufacturer|iProduct|iSerial|Bus|Device" | head -20
    fi

    # Check USB tree for driver assignment
    echo ""
    echo -e "${BOLD}USB Driver Status:${NC}"
    lsusb -t 2>/dev/null | grep -A 2 "Printer" || echo "  No printer class devices in USB tree"

    return 0
}

# Check 2: USB Driver Status
check_usb_driver() {
    print_section "2. USB Driver Status"

    local issues=()

    # Check if ipp-usb is running (may conflict)
    if systemctl is-active --quiet ipp-usb 2>/dev/null; then
        log WARN "ipp-usb service is running - may conflict with direct USB access"
        issues+=("ipp-usb running")

        if [[ "$AUTO_FIX" == true ]]; then
            log INFO "Auto-fix: Stopping ipp-usb service..."
            sudo systemctl stop ipp-usb 2>/dev/null || true
            sleep 1
        fi
    else
        log INFO "ipp-usb service is not running (good)"
    fi

    # Check usblp module
    if lsmod | grep -q "^usblp"; then
        log INFO "usblp kernel module is loaded"

        # Check if /dev/usb/lp* exists
        if ls /dev/usb/lp* &>/dev/null; then
            log INFO "USB printer devices found:"
            ls -la /dev/usb/lp* 2>/dev/null
        else
            log WARN "usblp loaded but no /dev/usb/lp* devices"
            issues+=("No lp devices")

            if [[ "$AUTO_FIX" == true ]]; then
                log INFO "Auto-fix: Reloading usblp module..."
                sudo rmmod usblp 2>/dev/null || true
                sleep 1
                sudo modprobe usblp
                sleep 2

                if ls /dev/usb/lp* &>/dev/null; then
                    log INFO "Auto-fix successful: /dev/usb/lp* devices created"
                fi
            fi
        fi
    else
        log WARN "usblp kernel module is not loaded"
        issues+=("usblp not loaded")

        if [[ "$AUTO_FIX" == true ]]; then
            log INFO "Auto-fix: Loading usblp module..."
            sudo modprobe usblp
            sleep 2

            if lsmod | grep -q "^usblp"; then
                log INFO "Auto-fix successful: usblp module loaded"
            fi
        fi
    fi

    # Check if USB device is claimed by correct driver
    echo ""
    echo -e "${BOLD}USB Device Driver Assignment:${NC}"
    for bus_dev in $(lsusb | grep -i "${CANON_VENDOR_ID}:${SELPHY_CP1500_PRODUCT_ID}" | sed 's/Bus \([0-9]*\) Device \([0-9]*\).*/\1-\2/'); do
        local bus=$(echo "$bus_dev" | cut -d'-' -f1)
        local port_info=$(lsusb -t 2>/dev/null | grep -A 5 "Bus $bus" | grep -i printer)

        if echo "$port_info" | grep -q "usblp"; then
            log INFO "Printer on Bus $bus: Driver=usblp (correct)"
        elif echo "$port_info" | grep -q "usbfs"; then
            log WARN "Printer on Bus $bus: Driver=usbfs (ipp-usb may be using it)"
            issues+=("usbfs driver")
        else
            log WARN "Printer on Bus $bus: Driver unknown"
        fi
    done

    [[ ${#issues[@]} -eq 0 ]] && return 0 || return 1
}

# Check 3: CUPS Service Status
check_cups_service() {
    print_section "3. CUPS Service Status"

    local issues=()

    # Check CUPS service
    if systemctl is-active --quiet cups; then
        log INFO "CUPS service is running"
    else
        log ERROR "CUPS service is not running"
        issues+=("CUPS not running")

        if [[ "$AUTO_FIX" == true ]]; then
            log INFO "Auto-fix: Starting CUPS service..."
            sudo systemctl start cups
            sleep 2

            if systemctl is-active --quiet cups; then
                log INFO "Auto-fix successful: CUPS started"
            else
                log ERROR "Auto-fix failed: Could not start CUPS"
            fi
        fi
    fi

    # Check CUPS is enabled
    if systemctl is-enabled --quiet cups; then
        log INFO "CUPS service is enabled on boot"
    else
        log WARN "CUPS service is not enabled on boot"

        if [[ "$AUTO_FIX" == true ]]; then
            log INFO "Auto-fix: Enabling CUPS on boot..."
            sudo systemctl enable cups
        fi
    fi

    # Check CUPS error log for recent errors
    echo ""
    echo -e "${BOLD}Recent CUPS Errors (last 10):${NC}"
    if [[ -f /var/log/cups/error_log ]]; then
        tail -10 /var/log/cups/error_log 2>/dev/null | grep -i "error\|warn" | tail -5 || echo "  No recent errors"
    else
        echo "  CUPS error log not found"
    fi

    [[ ${#issues[@]} -eq 0 ]] && return 0 || return 1
}

# Check 4: Registered Printers
check_registered_printers() {
    print_section "4. Registered Printers in CUPS"

    local issues=()

    # Get list of all printers
    echo -e "${BOLD}Configured Printers:${NC}"
    lpstat -p 2>/dev/null || echo "  No printers configured"

    echo ""
    echo -e "${BOLD}Printer URIs:${NC}"
    lpstat -v 2>/dev/null || echo "  No printer URIs"

    echo ""
    echo -e "${BOLD}Default Printer:${NC}"
    lpstat -d 2>/dev/null || echo "  No default printer set"

    # Check each registered Selphy printer
    echo ""
    echo -e "${BOLD}Selphy Printer Status:${NC}"

    while IFS= read -r printer_line; do
        local printer_name=$(echo "$printer_line" | awk '{print $1}')
        [[ -z "$printer_name" ]] && continue

        # Skip if specific printer requested and this isn't it
        if [[ -n "$SPECIFIC_PRINTER" && "$printer_name" != "$SPECIFIC_PRINTER" ]]; then
            continue
        fi

        echo ""
        echo -e "  ${CYAN}Printer: $printer_name${NC}"

        # Get URI
        local uri=$(lpstat -v "$printer_name" 2>/dev/null | awk '{print $NF}')
        echo "    URI: $uri"

        # Get status
        local status=$(lpstat -p "$printer_name" 2>/dev/null)
        if echo "$status" | grep -qi "idle"; then
            echo -e "    Status: ${GREEN}Idle (Ready)${NC}"
        elif echo "$status" | grep -qi "printing"; then
            echo -e "    Status: ${YELLOW}Printing${NC}"
        elif echo "$status" | grep -qi "disabled"; then
            echo -e "    Status: ${RED}Disabled${NC}"
            issues+=("$printer_name disabled")

            if [[ "$AUTO_FIX" == true ]]; then
                log INFO "Auto-fix: Enabling printer $printer_name..."
                sudo cupsenable "$printer_name" 2>/dev/null
            fi
        else
            echo -e "    Status: ${YELLOW}Unknown${NC}"
        fi

        # Check if URI matches connected USB device
        if [[ "$uri" == usb://* ]]; then
            local serial=$(echo "$uri" | grep -oP 'serial=\K[^&]+')
            if [[ -n "$serial" ]]; then
                # Check if this serial is currently connected
                if lsusb -v 2>/dev/null | grep -q "$serial"; then
                    echo -e "    USB: ${GREEN}Connected (Serial: $serial)${NC}"
                else
                    echo -e "    USB: ${RED}Not Connected (Serial: $serial)${NC}"
                    issues+=("$printer_name USB disconnected")
                fi
            fi
        fi

    done < <(lpstat -p 2>/dev/null | grep -i selphy | awk '{print $2}')

    [[ ${#issues[@]} -eq 0 ]] && return 0 || return 1
}

# Check 5: Print Queue Status
check_print_queue() {
    print_section "5. Print Queue Status"

    local issues=()

    # Get queue status
    echo -e "${BOLD}Current Print Queue:${NC}"
    local queue=$(lpstat -o 2>/dev/null)

    if [[ -z "$queue" ]]; then
        echo "  Queue is empty (good)"
    else
        echo "$queue"

        # Count jobs
        local job_count=$(echo "$queue" | wc -l)
        log INFO "Found $job_count job(s) in queue"

        # Check for stuck jobs
        local stuck_jobs=$(lpstat -o 2>/dev/null | grep -i "waiting\|held" | wc -l)
        if [[ $stuck_jobs -gt 0 ]]; then
            log WARN "Found $stuck_jobs stuck/waiting job(s)"
            issues+=("Stuck print jobs")

            if [[ "$AUTO_FIX" == true ]]; then
                echo ""
                log INFO "Auto-fix: Cancelling stuck jobs..."
                sudo cancel -a 2>/dev/null || true
                log INFO "Auto-fix: Jobs cancelled"
            fi
        fi
    fi

    [[ ${#issues[@]} -eq 0 ]] && return 0 || return 1
}

# Check 6: Printer Communication Test
check_printer_communication() {
    print_section "6. Printer Communication Test"

    local issues=()

    # Test each connected printer
    while IFS= read -r printer_line; do
        local printer_name=$(echo "$printer_line" | awk '{print $2}')
        [[ -z "$printer_name" ]] && continue

        # Skip if specific printer requested and this isn't it
        if [[ -n "$SPECIFIC_PRINTER" && "$printer_name" != "$SPECIFIC_PRINTER" ]]; then
            continue
        fi

        echo ""
        echo -e "${BOLD}Testing: $printer_name${NC}"

        # Get URI
        local uri=$(lpstat -v "$printer_name" 2>/dev/null | awk '{print $NF}')

        if [[ "$uri" == usb://* ]]; then
            # For USB printers, check device file
            if ls /dev/usb/lp* &>/dev/null; then
                # Try to get device status
                for dev in /dev/usb/lp*; do
                    if [[ -w "$dev" ]] || sudo test -w "$dev"; then
                        echo -e "  Device $dev: ${GREEN}Writable${NC}"
                    else
                        echo -e "  Device $dev: ${RED}Not writable${NC}"
                        issues+=("$dev not writable")
                    fi
                done
            else
                echo -e "  ${RED}No USB printer devices found${NC}"
                issues+=("No USB devices")
            fi
        fi

        # Try CUPS lpstat -l for detailed status
        echo ""
        echo "  Detailed status:"
        lpstat -l -p "$printer_name" 2>/dev/null | sed 's/^/    /' || echo "    Unable to get status"

    done < <(lpstat -p 2>/dev/null | grep -i selphy)

    [[ ${#issues[@]} -eq 0 ]] && return 0 || return 1
}

# ============================================
# AUTO-RECOVERY SCENARIOS
# ============================================

# Scenario 1: Printer not detected on USB
recover_usb_not_detected() {
    log INFO "Running recovery: USB not detected"

    echo "Step 1: Unbind and rebind USB devices..."

    # Find USB bus/port for Canon devices
    for usb_path in /sys/bus/usb/devices/*/idVendor; do
        local dir=$(dirname "$usb_path")
        local vendor=$(cat "$usb_path" 2>/dev/null)

        if [[ "$vendor" == "$CANON_VENDOR_ID" ]]; then
            local dev_name=$(basename "$dir")
            echo "  Rebinding USB device: $dev_name"

            echo "$dev_name" | sudo tee /sys/bus/usb/drivers/usb/unbind 2>/dev/null || true
            sleep 2
            echo "$dev_name" | sudo tee /sys/bus/usb/drivers/usb/bind 2>/dev/null || true
            sleep 2
        fi
    done

    echo "Step 2: Reload USB modules..."
    sudo modprobe -r usblp 2>/dev/null || true
    sleep 1
    sudo modprobe usblp
    sleep 2

    echo "Step 3: Verify detection..."
    if lsusb | grep -qi "${CANON_VENDOR_ID}:${SELPHY_CP1500_PRODUCT_ID}"; then
        log INFO "Recovery successful: Printer detected"
        return 0
    else
        log ERROR "Recovery failed: Printer still not detected"
        echo ""
        echo "Manual steps to try:"
        echo "  1. Unplug the USB cable from the printer"
        echo "  2. Power off the printer"
        echo "  3. Wait 10 seconds"
        echo "  4. Power on the printer"
        echo "  5. Plug the USB cable back in"
        echo "  6. Run this script again"
        return 1
    fi
}

# Scenario 2: ipp-usb conflict
recover_ipp_usb_conflict() {
    log INFO "Running recovery: ipp-usb conflict"

    echo "Step 1: Stop ipp-usb service..."
    sudo systemctl stop ipp-usb 2>/dev/null || true

    echo "Step 2: Kill any remaining ipp-usb processes..."
    sudo pkill -9 ipp-usb 2>/dev/null || true
    sleep 1

    echo "Step 3: Prevent ipp-usb from auto-starting..."
    # Create a mask to prevent udev from starting it
    sudo systemctl mask ipp-usb 2>/dev/null || true

    echo "Step 4: Rebind USB device to usblp..."
    recover_usb_not_detected

    echo ""
    log INFO "ipp-usb has been disabled. To re-enable later:"
    echo "  sudo systemctl unmask ipp-usb"
    echo "  sudo systemctl start ipp-usb"
}

# Scenario 3: CUPS printer disabled/error state
recover_cups_printer_state() {
    local printer_name="${1:-}"

    log INFO "Running recovery: CUPS printer state for $printer_name"

    if [[ -z "$printer_name" ]]; then
        # Recover all Selphy printers
        while IFS= read -r line; do
            printer_name=$(echo "$line" | awk '{print $2}')
            [[ -n "$printer_name" ]] && recover_cups_printer_state "$printer_name"
        done < <(lpstat -p 2>/dev/null | grep -i selphy)
        return
    fi

    echo "Step 1: Cancel all jobs for $printer_name..."
    sudo cancel -a "$printer_name" 2>/dev/null || true

    echo "Step 2: Disable and re-enable printer..."
    sudo cupsdisable "$printer_name" 2>/dev/null || true
    sleep 1
    sudo cupsenable "$printer_name" 2>/dev/null || true

    echo "Step 3: Accept print jobs..."
    sudo cupsaccept "$printer_name" 2>/dev/null || true

    echo "Step 4: Verify status..."
    lpstat -p "$printer_name" 2>/dev/null

    log INFO "Recovery complete for $printer_name"
}

# Scenario 4: Register new printer
register_new_printer() {
    log INFO "Running: Register new printer"

    # Find unregistered USB printers
    echo "Scanning for unregistered Canon Selphy CP1500 printers..."

    local registered_serials=()

    # Get serials of already registered printers
    while IFS= read -r uri; do
        local serial=$(echo "$uri" | grep -oP 'serial=\K[^&\s]+')
        [[ -n "$serial" ]] && registered_serials+=("$serial")
    done < <(lpstat -v 2>/dev/null | grep -i selphy | awk '{print $NF}')

    # Find all connected USB serials
    local connected_serials=()
    while IFS= read -r serial; do
        [[ -n "$serial" ]] && connected_serials+=("$serial")
    done < <(lsusb -v 2>/dev/null | grep -A 20 "${CANON_VENDOR_ID}:${SELPHY_CP1500_PRODUCT_ID}" | grep iSerial | awk '{print $3}')

    # Find unregistered
    local new_count=0
    for serial in "${connected_serials[@]}"; do
        local is_registered=false
        for reg_serial in "${registered_serials[@]}"; do
            [[ "$serial" == "$reg_serial" ]] && is_registered=true && break
        done

        if [[ "$is_registered" == false ]]; then
            ((new_count++))
            echo ""
            log INFO "Found unregistered printer with serial: $serial"

            # Generate printer name
            local printer_num=$(lpstat -p 2>/dev/null | grep -ci selphy || echo 0)
            ((printer_num++))

            local new_name="SelphyCP1500"
            [[ $printer_num -gt 1 ]] && new_name="SelphyCP1500-$printer_num"

            echo "Registering as: $new_name"

            # Get PPD from existing printer or use driver
            local ppd_source=""
            if [[ -f "$PRINTER_CONFIG_DIR/SelphyCP1500.ppd" ]]; then
                ppd_source="-P $PRINTER_CONFIG_DIR/SelphyCP1500.ppd"
                echo "  Using existing PPD configuration"
            else
                ppd_source="-m $GUTENPRINT_DRIVER"
                echo "  Using Gutenprint driver"
            fi

            # Register the printer
            local uri="usb://Canon/SELPHY%20CP1500?serial=$serial"

            sudo lpadmin -p "$new_name" \
                -E \
                -v "$uri" \
                $ppd_source \
                -D "Canon Selphy CP1500 (Serial: $serial)" \
                -L "PhotoBooth" \
                2>/dev/null

            if lpstat -p "$new_name" &>/dev/null; then
                log INFO "Successfully registered: $new_name"
                sudo cupsenable "$new_name" 2>/dev/null || true
                sudo cupsaccept "$new_name" 2>/dev/null || true
            else
                log ERROR "Failed to register: $new_name"
            fi
        fi
    done

    if [[ $new_count -eq 0 ]]; then
        echo "No unregistered printers found."
        echo ""
        echo "All connected printers are already registered, or no printers are connected."
    fi
}

# ============================================
# COMPREHENSIVE AUTO-FIX
# ============================================
run_auto_fix() {
    print_section "Running Comprehensive Auto-Fix"

    local fixed=0

    # Step 1: Handle ipp-usb if running
    if systemctl is-active --quiet ipp-usb 2>/dev/null; then
        log INFO "Step 1: Handling ipp-usb conflict..."
        recover_ipp_usb_conflict
        ((fixed++))
        sleep 2
    else
        log INFO "Step 1: ipp-usb not running (OK)"
    fi

    # Step 2: Ensure usblp module
    if ! lsmod | grep -q "^usblp"; then
        log INFO "Step 2: Loading usblp module..."
        sudo modprobe usblp
        sleep 2
        ((fixed++))
    else
        log INFO "Step 2: usblp module loaded (OK)"
    fi

    # Step 3: Ensure CUPS running
    if ! systemctl is-active --quiet cups; then
        log INFO "Step 3: Starting CUPS..."
        sudo systemctl start cups
        sleep 2
        ((fixed++))
    else
        log INFO "Step 3: CUPS running (OK)"
    fi

    # Step 4: Clear stuck print jobs
    local stuck=$(lpstat -o 2>/dev/null | wc -l)
    if [[ $stuck -gt 0 ]]; then
        log INFO "Step 4: Clearing $stuck print job(s)..."
        sudo cancel -a 2>/dev/null || true
        ((fixed++))
    else
        log INFO "Step 4: Print queue empty (OK)"
    fi

    # Step 5: Re-enable all Selphy printers
    log INFO "Step 5: Re-enabling all Selphy printers..."
    while IFS= read -r printer_name; do
        [[ -z "$printer_name" ]] && continue
        sudo cupsenable "$printer_name" 2>/dev/null || true
        sudo cupsaccept "$printer_name" 2>/dev/null || true
        ((fixed++))
    done < <(lpstat -p 2>/dev/null | grep -i selphy | awk '{print $2}')

    # Step 6: Register any unregistered printers
    log INFO "Step 6: Checking for unregistered printers..."
    register_new_printer

    echo ""
    log INFO "Auto-fix complete. $fixed issue(s) addressed."
}

# ============================================
# SUMMARY REPORT
# ============================================
generate_summary() {
    print_section "Summary Report"

    echo ""
    echo -e "${BOLD}System Status:${NC}"

    # USB Printers
    local usb_count=$(lsusb 2>/dev/null | grep -ci "${CANON_VENDOR_ID}:${SELPHY_CP1500_PRODUCT_ID}" || echo 0)
    echo -e "  USB Printers Connected: ${BOLD}$usb_count${NC}"

    # CUPS Printers
    local cups_count=$(lpstat -p 2>/dev/null | grep -ci selphy || echo 0)
    echo -e "  CUPS Printers Registered: ${BOLD}$cups_count${NC}"

    # Ready Printers
    local ready_count=$(lpstat -p 2>/dev/null | grep -i selphy | grep -ci idle || echo 0)
    echo -e "  Printers Ready: ${BOLD}$ready_count${NC}"

    # Print Queue
    local queue_count=$(lpstat -o 2>/dev/null | wc -l || echo 0)
    echo -e "  Jobs in Queue: ${BOLD}$queue_count${NC}"

    # Services
    echo ""
    echo -e "${BOLD}Service Status:${NC}"

    for svc in cups ipp-usb; do
        if systemctl is-active --quiet $svc 2>/dev/null; then
            echo -e "  $svc: ${GREEN}Running${NC}"
        else
            echo -e "  $svc: ${YELLOW}Stopped${NC}"
        fi
    done

    # Overall health
    echo ""
    if [[ $usb_count -gt 0 && $ready_count -gt 0 && $usb_count -eq $cups_count ]]; then
        echo -e "${GREEN}${BOLD}Overall Status: HEALTHY${NC}"
        echo "  All printers are connected and ready."
    elif [[ $usb_count -gt $cups_count ]]; then
        echo -e "${YELLOW}${BOLD}Overall Status: ACTION NEEDED${NC}"
        echo "  Some connected printers are not registered in CUPS."
        echo "  Run with --auto-fix to register them."
    elif [[ $usb_count -lt $cups_count ]]; then
        echo -e "${YELLOW}${BOLD}Overall Status: WARNING${NC}"
        echo "  Some registered printers are not connected."
    elif [[ $ready_count -lt $cups_count ]]; then
        echo -e "${YELLOW}${BOLD}Overall Status: WARNING${NC}"
        echo "  Some printers are not in ready state."
        echo "  Run with --auto-fix to attempt recovery."
    else
        echo -e "${RED}${BOLD}Overall Status: CRITICAL${NC}"
        echo "  No printers detected or configured."
    fi

    echo ""
}

# ============================================
# INTERACTIVE MENU
# ============================================
show_menu() {
    while true; do
        clear
        print_header

        echo -e "${BOLD}Troubleshooting Menu${NC}"
        echo ""
        echo "  1. Run full diagnostic"
        echo "  2. Check USB devices only"
        echo "  3. Check CUPS status only"
        echo "  4. Check print queue"
        echo ""
        echo "  5. Auto-fix all issues"
        echo "  6. Register new printer"
        echo "  7. Reset printer state"
        echo "  8. Disable ipp-usb service"
        echo ""
        echo "  9. Print test page"
        echo ""
        echo "  0. Exit"
        echo ""
        echo -n "Select [0-9]: "
        read -r choice

        case $choice in
            1)
                clear
                run_full_diagnostic
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            2)
                clear
                check_usb_devices
                check_usb_driver
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            3)
                clear
                check_cups_service
                check_registered_printers
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            4)
                clear
                check_print_queue
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            5)
                clear
                AUTO_FIX=true
                run_auto_fix
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            6)
                clear
                register_new_printer
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            7)
                clear
                recover_cups_printer_state
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            8)
                clear
                recover_ipp_usb_conflict
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            9)
                clear
                print_test_page
                echo ""
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
            0)
                echo ""
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
        esac
    done
}

# Print test page
print_test_page() {
    print_section "Print Test Page"

    # List available printers
    echo -e "${BOLD}Available Printers:${NC}"
    local printers=()
    local i=1

    while IFS= read -r printer; do
        [[ -z "$printer" ]] && continue
        printers+=("$printer")
        local status=$(lpstat -p "$printer" 2>/dev/null | grep -oP '(idle|printing|disabled)' || echo "unknown")
        echo "  $i. $printer ($status)"
        ((i++))
    done < <(lpstat -p 2>/dev/null | grep -i selphy | awk '{print $2}')

    if [[ ${#printers[@]} -eq 0 ]]; then
        echo "  No Selphy printers found."
        return 1
    fi

    echo ""
    echo -n "Select printer [1-${#printers[@]}]: "
    read -r selection

    if [[ $selection -ge 1 && $selection -le ${#printers[@]} ]]; then
        local selected="${printers[$((selection-1))]}"
        echo ""
        echo "Sending test page to $selected..."

        if [[ -f /usr/share/cups/data/testprint ]]; then
            lp -d "$selected" /usr/share/cups/data/testprint 2>/dev/null
            echo -e "${GREEN}Test page sent!${NC}"
        else
            echo "Creating and sending test image..."

            local test_file="/tmp/photobooth_test_$(date +%s).jpg"

            if command -v convert &>/dev/null; then
                convert -size 1200x1800 \
                    -background white \
                    -fill black \
                    -pointsize 48 \
                    -gravity center \
                    label:"PhotoBooth Test\n\n$(date '+%Y-%m-%d %H:%M:%S')\n\nPrinter: $selected" \
                    "$test_file" 2>/dev/null

                lp -d "$selected" "$test_file" 2>/dev/null
                rm -f "$test_file"

                echo -e "${GREEN}Test page sent!${NC}"
            else
                echo -e "${RED}ImageMagick not installed. Cannot create test image.${NC}"
            fi
        fi
    else
        echo "Invalid selection."
    fi
}

# ============================================
# FULL DIAGNOSTIC
# ============================================
run_full_diagnostic() {
    print_header

    local total_issues=0

    check_usb_devices || ((total_issues++))
    check_usb_driver || ((total_issues++))
    check_cups_service || ((total_issues++))
    check_registered_printers || ((total_issues++))
    check_print_queue || ((total_issues++))
    check_printer_communication || ((total_issues++))

    generate_summary

    if [[ $total_issues -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}Found issues in $total_issues check(s).${NC}"
        echo "Run with --auto-fix to attempt automatic recovery."
    fi
}

# ============================================
# MAIN
# ============================================
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto-fix|-a)
                AUTO_FIX=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --printer|-p)
                SPECIFIC_PRINTER="$2"
                shift 2
                ;;
            --menu|-m)
                show_menu
                exit 0
                ;;
            --help|-h)
                echo "PhotoBooth Printer Troubleshooter"
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --auto-fix, -a     Automatically fix detected issues"
                echo "  --verbose, -v      Show detailed debug output"
                echo "  --printer, -p NAME Check specific printer only"
                echo "  --menu, -m         Show interactive menu"
                echo "  --help, -h         Show this help"
                echo ""
                echo "Examples:"
                echo "  $0                  Run full diagnostic"
                echo "  $0 --auto-fix       Run diagnostic and fix issues"
                echo "  $0 --menu           Interactive troubleshooting menu"
                echo "  $0 -p SelphyCP1500  Check specific printer"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Check if running as root for certain operations
    if [[ $EUID -ne 0 && "$AUTO_FIX" == true ]]; then
        log WARN "Some auto-fix operations require root. Consider running with sudo."
    fi

    # Run diagnostic
    run_full_diagnostic

    # Auto-fix if requested
    if [[ "$AUTO_FIX" == true ]]; then
        run_auto_fix
        echo ""
        echo "Re-running diagnostic after auto-fix..."
        echo ""
        run_full_diagnostic
    fi
}

main "$@"
