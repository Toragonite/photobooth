#!/bin/bash
#
# Generate self-signed SSL certificates for PhotoBooth
# These certificates are for development/local network use only
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_DIR/docker/nginx/ssl"

# Create SSL directory
mkdir -p "$SSL_DIR"

# Certificate details
DAYS=365
COUNTRY="RW"
STATE="Kigali"
LOCALITY="Kigali"
ORGANIZATION="PhotoBooth"
COMMON_NAME="photobooth.local"

echo "Generating SSL certificates..."
echo "  Output directory: $SSL_DIR"
echo "  Common Name: $COMMON_NAME"
echo "  Valid for: $DAYS days"

# Generate private key
openssl genrsa -out "$SSL_DIR/server.key" 2048

# Generate certificate signing request
openssl req -new \
    -key "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.csr" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$LOCALITY/O=$ORGANIZATION/CN=$COMMON_NAME"

# Generate self-signed certificate
openssl x509 -req \
    -days "$DAYS" \
    -in "$SSL_DIR/server.csr" \
    -signkey "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.crt" \
    -extfile <(printf "subjectAltName=DNS:$COMMON_NAME,DNS:localhost,IP:127.0.0.1,IP:192.168.4.1")

# Clean up CSR
rm -f "$SSL_DIR/server.csr"

# Set permissions
chmod 600 "$SSL_DIR/server.key"
chmod 644 "$SSL_DIR/server.crt"

echo ""
echo "SSL certificates generated successfully!"
echo ""
echo "Files created:"
echo "  - $SSL_DIR/server.key (private key)"
echo "  - $SSL_DIR/server.crt (certificate)"
echo ""
echo "Note: These are self-signed certificates."
echo "Browsers will show a security warning - this is expected."
echo "To proceed, accept the certificate in your browser."
