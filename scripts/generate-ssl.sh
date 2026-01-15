#!/bin/bash
#
# Generate SSL certificates for PhotoBooth using mkcert
# mkcert creates locally-trusted certificates that browsers accept without warnings
#
# Usage:
#   ./generate-ssl.sh              # Generate certificates
#   ./generate-ssl.sh --clean      # Remove existing certificates
#   ./generate-ssl.sh --show-ca    # Show CA certificate location for iPad installation
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_DIR/docker/nginx/ssl"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Clean existing certificates
clean_ssl() {
    log_info "Cleaning existing SSL certificates..."

    if [[ -d "$SSL_DIR" ]]; then
        rm -rf "$SSL_DIR"
        log_ok "Removed: $SSL_DIR"
    else
        log_info "No SSL directory found, nothing to clean"
    fi
}

# Show CA certificate location
show_ca() {
    if ! command -v mkcert &> /dev/null; then
        log_error "mkcert is not installed"
        exit 1
    fi

    local ca_root
    ca_root=$(mkcert -CAROOT)

    echo ""
    echo "=========================================="
    echo "  mkcert CA Certificate Location"
    echo "=========================================="
    echo ""
    echo "CA Root directory: $ca_root"
    echo ""
    echo "Files:"
    echo "  - ${ca_root}/rootCA.pem (install this on iPad)"
    echo "  - ${ca_root}/rootCA-key.pem (keep private!)"
    echo ""
    echo "=========================================="
    echo "  iPad Installation Steps"
    echo "=========================================="
    echo ""
    echo "1. Transfer rootCA.pem to iPad (AirDrop, email, etc.)"
    echo ""
    echo "2. On iPad, tap the file to download the profile"
    echo ""
    echo "3. Go to: Settings > General > VPN & Device Management"
    echo "   - Find the downloaded profile"
    echo "   - Tap 'Install' and enter your passcode"
    echo ""
    echo "4. Go to: Settings > General > About > Certificate Trust Settings"
    echo "   - Enable full trust for mkcert root certificate"
    echo ""
    echo "After these steps, Safari will trust certificates from this CA."
    echo ""
}

# Check if mkcert is installed
check_mkcert() {
    if ! command -v mkcert &> /dev/null; then
        log_error "mkcert is not installed!"
        echo ""
        echo "Install mkcert first:"
        echo ""
        echo "  macOS:   brew install mkcert && mkcert -install"
        echo ""
        echo "  Linux:   sudo apt install libnss3-tools"
        echo "           curl -L https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-arm64 -o mkcert"
        echo "           chmod +x mkcert && sudo mv mkcert /usr/local/bin/"
        echo "           mkcert -install"
        echo ""
        echo "  Windows: choco install mkcert && mkcert -install"
        echo ""
        exit 1
    fi
}

# Generate certificates
generate_ssl() {
    check_mkcert

    # Clean existing certificates first
    if [[ -d "$SSL_DIR" ]]; then
        log_warn "Existing SSL certificates found"
        read -p "Remove and regenerate? (y/n): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            clean_ssl
        else
            log_info "Keeping existing certificates"
            exit 0
        fi
    fi

    # Create SSL directory
    mkdir -p "$SSL_DIR"

    log_info "Generating SSL certificates with mkcert..."
    echo ""

    # Domains and IPs to include
    local domains=(
        "photobooth.local"
        "localhost"
        "127.0.0.1"
        "192.168.4.1"      # Default Pi AP IP
        "::1"
    )

    # Ask for additional IPs
    echo "Default domains/IPs: ${domains[*]}"
    read -p "Add additional IP addresses? (comma-separated, or press Enter to skip): " -r additional_ips

    if [[ -n "$additional_ips" ]]; then
        IFS=',' read -ra extra_ips <<< "$additional_ips"
        for ip in "${extra_ips[@]}"; do
            ip=$(echo "$ip" | xargs)  # trim whitespace
            if [[ -n "$ip" ]]; then
                domains+=("$ip")
            fi
        done
    fi

    log_info "Generating certificates for: ${domains[*]}"

    # Generate certificates
    cd "$SSL_DIR"
    mkcert -cert-file cert.pem -key-file key.pem "${domains[@]}"

    # Set permissions
    chmod 600 key.pem
    chmod 644 cert.pem

    echo ""
    log_ok "SSL certificates generated successfully!"
    echo ""
    echo "=========================================="
    echo "  Generated Files"
    echo "=========================================="
    echo ""
    echo "  Certificate: $SSL_DIR/cert.pem"
    echo "  Private Key: $SSL_DIR/key.pem"
    echo ""
    echo "=========================================="
    echo "  Next Steps"
    echo "=========================================="
    echo ""
    echo "1. Install CA certificate on iPad:"
    echo "   Run: $0 --show-ca"
    echo ""
    echo "2. If deploying to Raspberry Pi, copy SSL files:"
    echo "   scp -r $SSL_DIR pi@<PI_IP>:~/photobooth/docker/nginx/"
    echo ""
    echo "3. Start the application:"
    echo "   docker compose up -d"
    echo ""
}

# Main
case "${1:-}" in
    --clean|-c)
        clean_ssl
        ;;
    --show-ca|--ca)
        show_ca
        ;;
    --help|-h)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  (none)      Generate SSL certificates using mkcert"
        echo "  --clean     Remove existing SSL certificates"
        echo "  --show-ca   Show CA certificate location for iPad installation"
        echo "  --help      Show this help message"
        echo ""
        ;;
    *)
        generate_ssl
        ;;
esac
