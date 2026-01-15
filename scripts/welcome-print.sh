#!/bin/bash
#
# PhotoBooth Welcome Print Script
# Prints a welcome/test image on system startup
#
# This script prints once per boot to verify the printer is working.
# The print is skipped if:
#   - Printer is not available
#   - Already printed in this boot session
#   - SKIP_WELCOME_PRINT=true is set
#   - Internet is available (on-premise/offline mode only)
#

set -euo pipefail

# Configuration
PHOTOBOOTH_DIR="${PHOTOBOOTH_DIR:-/home/toragonite/Documents/photobooth}"
WELCOME_IMAGE="${PHOTOBOOTH_DIR}/assets/image.jpg"
PRINTER_NAME="${PRINTER_NAME:-SelphyCP1500}"
LOCK_FILE="/tmp/photobooth-welcome-printed"
LOG_FILE="/var/log/photobooth-welcome.log"

# Logging
log() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} - ${message}" | tee -a "$LOG_FILE" 2>/dev/null || echo "${timestamp} - ${message}"
}

# Check if we should skip
if [[ "${SKIP_WELCOME_PRINT:-false}" == "true" ]]; then
    log "Welcome print disabled (SKIP_WELCOME_PRINT=true)"
    exit 0
fi

# Check if internet is available (skip welcome print if online)
# This ensures welcome print only runs in offline/on-premise mode
check_internet() {
    # Try to ping common DNS servers (timeout 3 seconds)
    ping -c 1 -W 3 8.8.8.8 &>/dev/null || ping -c 1 -W 3 1.1.1.1 &>/dev/null
}

if check_internet; then
    log "Internet available - skipping welcome print (development mode)"
    exit 0
fi

log "Offline mode detected - proceeding with welcome print"

# Check if already printed this boot
if [[ -f "$LOCK_FILE" ]]; then
    log "Welcome print already done this boot session"
    exit 0
fi

# Check if image exists
if [[ ! -f "$WELCOME_IMAGE" ]]; then
    log "ERROR: Welcome image not found: $WELCOME_IMAGE"
    exit 1
fi

# Check if printer is available
if ! lpstat -p "$PRINTER_NAME" &>/dev/null; then
    log "ERROR: Printer '$PRINTER_NAME' not found"
    log "Available printers:"
    lpstat -p 2>/dev/null || log "No printers configured"
    exit 1
fi

# Check printer status
printer_status=$(lpstat -p "$PRINTER_NAME" 2>/dev/null | head -1)
if echo "$printer_status" | grep -qi "disabled\|offline"; then
    log "WARNING: Printer may be offline: $printer_status"
    log "Attempting to enable printer..."
    cupsenable "$PRINTER_NAME" 2>/dev/null || true
    sleep 2
fi

# Print the welcome image
log "Printing welcome image to $PRINTER_NAME..."
log "Image: $WELCOME_IMAGE"

# Use lp to print with appropriate options for photo paper
# Options:
#   media=w288h432  : 4x6 inch postcard size
#   fit-to-page     : Scale to fit while maintaining aspect ratio
#   position=center : Center the image on the page
if lp -d "$PRINTER_NAME" \
    -o media=w288h432 \
    -o fit-to-page \
    -o position=center \
    "$WELCOME_IMAGE" 2>&1 | tee -a "$LOG_FILE"; then

    log "Welcome print job submitted successfully"

    # Create lock file to prevent duplicate prints
    touch "$LOCK_FILE"

    # Show job status
    sleep 2
    lpstat -o "$PRINTER_NAME" 2>/dev/null | tee -a "$LOG_FILE" || true

    exit 0
else
    log "ERROR: Failed to submit print job"
    exit 1
fi
