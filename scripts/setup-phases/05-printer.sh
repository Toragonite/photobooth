#!/bin/bash
#
# Phase 05: Canon Selphy CP1500 Printer Setup
# Configures the printer in CUPS
#

set -euo pipefail

echo "[05-printer] Starting printer configuration..."

PRINTER_NAME="${PRINTER_NAME:-Canon_Selphy_CP1500}"
PRINTER_DESCRIPTION="Canon Selphy CP1500 Photo Printer"

# Function to wait for printer to be detected
wait_for_printer() {
    echo "Waiting for Canon Selphy CP1500 to be detected..."
    echo "(Make sure the printer is connected via USB and powered on)"

    for i in {1..60}; do
        if lsusb 2>/dev/null | grep -qi "canon.*selphy\|canon.*cp1500\|04a9:"; then
            echo "Printer detected!"
            lsusb | grep -i canon || true
            return 0
        fi
        echo "  Attempt $i/60: Printer not detected, waiting..."
        sleep 2
    done

    echo ""
    echo "WARNING: Printer not detected after 2 minutes"
    echo "You can manually configure the printer later using:"
    echo "  sudo lpadmin -p $PRINTER_NAME -v <device-uri> -m everywhere"
    echo ""
    return 1
}

# Function to find printer URI
find_printer_uri() {
    echo "Searching for printer device URI..."

    # Wait a moment for USB to settle
    sleep 2

    # Try lpinfo to find the printer
    local uri=""
    uri=$(lpinfo -v 2>/dev/null | grep -i "selphy\|cp1500\|04a9:" | head -1 | awk '{print $2}')

    if [[ -n "$uri" ]]; then
        echo "Found printer URI: $uri"
        echo "$uri"
        return 0
    fi

    # Fallback: construct URI from lsusb
    local usb_info
    usb_info=$(lsusb 2>/dev/null | grep -i "canon" | head -1)

    if [[ -n "$usb_info" ]]; then
        echo "Constructing URI from USB info: $usb_info"
        # Try common URI format
        echo "usb://Canon/SELPHY%20CP1500"
        return 0
    fi

    echo ""
    return 1
}

# Function to add printer
add_printer() {
    local uri="$1"

    echo "Adding printer to CUPS..."

    # Remove existing printer with same name if present
    if lpstat -p "$PRINTER_NAME" &>/dev/null; then
        echo "Removing existing printer configuration..."
        lpadmin -x "$PRINTER_NAME" 2>/dev/null || true
    fi

    # Add the printer
    echo "Adding printer: $PRINTER_NAME"
    echo "  URI: $uri"

    lpadmin -p "$PRINTER_NAME" \
        -E \
        -v "$uri" \
        -m everywhere \
        -D "$PRINTER_DESCRIPTION" \
        -L "PhotoBooth" \
        -o media=na_index-4x6_4x6in \
        -o print-quality=5 \
        -o ColorModel=RGB

    # Set as default printer
    echo "Setting as default printer..."
    lpadmin -d "$PRINTER_NAME"

    # Enable the printer
    echo "Enabling printer..."
    cupsenable "$PRINTER_NAME"
    cupsaccept "$PRINTER_NAME"
}

# Function to test print
test_printer() {
    echo ""
    read -p "Would you like to print a test page? (y/n): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Printing test page..."
        lp -d "$PRINTER_NAME" /usr/share/cups/data/testprint 2>/dev/null || \
        echo "Test page command sent (may require manual verification)"
    fi
}

# Function to show printer status
show_status() {
    echo ""
    echo "Printer Configuration:"
    echo "  Name: $PRINTER_NAME"
    echo ""
    echo "Printer Status:"
    lpstat -p "$PRINTER_NAME" 2>/dev/null || echo "  Status unavailable"
    echo ""
    echo "Default Printer:"
    lpstat -d 2>/dev/null || echo "  No default printer set"
}

# Main
main() {
    # Check if CUPS is running
    if ! systemctl is-active --quiet cups; then
        echo "Starting CUPS service..."
        systemctl start cups
        sleep 3
    fi

    # Check if printer is already configured
    if lpstat -p "$PRINTER_NAME" &>/dev/null; then
        echo "Printer '$PRINTER_NAME' is already configured"
        show_status

        read -p "Reconfigure printer? (y/n): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Keeping existing configuration"
            return 0
        fi
    fi

    # Wait for printer detection
    if wait_for_printer; then
        # Find printer URI
        PRINTER_URI=$(find_printer_uri)

        if [[ -n "$PRINTER_URI" ]]; then
            add_printer "$PRINTER_URI"
            show_status
            test_printer
        else
            echo "Could not determine printer URI"
            echo "Please configure manually using CUPS web interface:"
            echo "  http://localhost:631/admin"
        fi
    else
        echo ""
        echo "Printer not detected. Skipping automatic configuration."
        echo ""
        echo "To configure manually later:"
        echo "  1. Connect the Canon Selphy CP1500 via USB"
        echo "  2. Power on the printer"
        echo "  3. Run: sudo lpadmin -p $PRINTER_NAME -v usb://Canon/SELPHY%20CP1500 -m everywhere -E"
        echo "  4. Run: sudo lpadmin -d $PRINTER_NAME"
        echo ""
        echo "Or use the CUPS web interface:"
        echo "  http://localhost:631/admin"
    fi

    echo ""
    echo "[05-printer] Printer configuration phase complete"
}

main "$@"
