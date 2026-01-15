#!/bin/bash
#
# Phase 05: Canon Selphy CP1500 Printer Setup
# Configures the printer in CUPS using Gutenprint driver (CP1300 compatible)
#
# Tested configuration (2026-01-16):
#   USB: Bus 001 Device 003: ID 04a9:3302 Canon, Inc. SELPHY CP1500
#   Driver: gutenprint.5.3://canon-cp1300/expert
#   Media: w288h432 (4x6 postcard)
#

set -euo pipefail

echo "[05-printer] Starting printer configuration..."

# Printer configuration - DO NOT use underscores in printer name
PRINTER_NAME="${PRINTER_NAME:-SelphyCP1500}"
PRINTER_DESCRIPTION="Canon Selphy CP1500 Photo Printer"
PRINTER_DRIVER="gutenprint.5.3://canon-cp1300/expert"
PRINTER_MEDIA="w288h432"

# Function to wait for printer to be detected
wait_for_printer() {
    echo "Waiting for Canon Selphy CP1500 to be detected..."
    echo "(Make sure the printer is connected via USB and powered on)"

    for i in {1..60}; do
        if lsusb 2>/dev/null | grep -qi "04a9:3302\|canon.*selphy\|canon.*cp1500"; then
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
    echo "  sudo lpadmin -p $PRINTER_NAME -E -v <device-uri> -m \"$PRINTER_DRIVER\" -o media=$PRINTER_MEDIA"
    echo ""
    return 1
}

# Function to find printer URI
find_printer_uri() {
    echo "Searching for printer device URI..."

    # Wait a moment for USB to settle
    sleep 2

    # Try lpinfo to find the printer (requires sudo)
    local uri=""
    uri=$(lpinfo -v 2>/dev/null | grep -i "selphy\|cp1500\|04a9:3302" | head -1 | awk '{print $2}')

    if [[ -n "$uri" ]]; then
        echo "Found printer URI: $uri"
        echo "$uri"
        return 0
    fi

    # Fallback: construct URI from lsusb serial number
    local usb_info
    usb_info=$(lsusb -v 2>/dev/null | grep -A 20 "04a9:3302" | grep iSerial | awk '{print $3}')

    if [[ -n "$usb_info" ]]; then
        local constructed_uri="usb://Canon/SELPHY%20CP1500?serial=$usb_info"
        echo "Constructed URI with serial: $constructed_uri"
        echo "$constructed_uri"
        return 0
    fi

    # Last fallback: basic URI without serial
    echo "Using fallback URI without serial number"
    echo "usb://Canon/SELPHY%20CP1500"
    return 0
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

    # Add the printer with Gutenprint driver (CP1300 is compatible with CP1500)
    echo "Adding printer: $PRINTER_NAME"
    echo "  URI: $uri"
    echo "  Driver: $PRINTER_DRIVER"
    echo "  Media: $PRINTER_MEDIA (4x6 postcard)"

    lpadmin -p "$PRINTER_NAME" \
        -E \
        -v "$uri" \
        -m "$PRINTER_DRIVER" \
        -D "$PRINTER_DESCRIPTION" \
        -L "PhotoBooth" \
        -o media="$PRINTER_MEDIA"

    # Set as default printer
    echo "Setting as default printer..."
    lpadmin -d "$PRINTER_NAME"

    # Enable the printer
    echo "Enabling printer..."
    cupsenable "$PRINTER_NAME" 2>/dev/null || true
    cupsaccept "$PRINTER_NAME" 2>/dev/null || true
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
        echo "  3. Find URI: sudo lpinfo -v | grep -i usb"
        echo "  4. Add printer:"
        echo "     sudo lpadmin -p $PRINTER_NAME -E \\"
        echo "       -v \"usb://Canon/SELPHY%20CP1500?serial=YOUR_SERIAL\" \\"
        echo "       -m \"$PRINTER_DRIVER\" \\"
        echo "       -o media=$PRINTER_MEDIA"
        echo "  5. Set default: sudo lpadmin -d $PRINTER_NAME"
        echo ""
        echo "Or use the CUPS web interface:"
        echo "  http://localhost:631/admin"
    fi

    echo ""
    echo "[05-printer] Printer configuration phase complete"
}

main "$@"
