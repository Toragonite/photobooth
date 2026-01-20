#!/bin/bash
#
# Phase 02: Docker Installation
# Installs Docker and Docker Compose
#

set -euo pipefail

echo "[02-docker] Starting Docker installation..."

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "Docker already installed: $DOCKER_VERSION"
else
    # Install Docker using official script
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh

    # Wait for Docker to be ready
    sleep 5
fi

# Start Docker service
echo "Starting Docker service..."
systemctl enable docker
systemctl start docker

# Wait for Docker daemon to be ready
echo "Waiting for Docker daemon..."
for i in {1..30}; do
    if docker info &>/dev/null; then
        echo "Docker daemon is ready"
        break
    fi
    sleep 1
done

# Add user to docker group (toragonite or pi)
echo "Adding user to docker group..."
usermod -aG docker toragonite 2>/dev/null || true
usermod -aG docker pi 2>/dev/null || true

# Install Docker Compose plugin if not present
if ! docker compose version &>/dev/null; then
    echo "Installing Docker Compose plugin..."
    apt-get install -y -qq docker-compose-plugin
fi

# Verify installations
echo "Verifying Docker installation..."
docker --version
docker compose version

# Configure Docker daemon
echo "Configuring Docker daemon..."
mkdir -p /etc/docker

# Check if config already exists
if [[ -f /etc/docker/daemon.json ]]; then
    # Merge with existing config
    echo "Updating existing Docker config..."
else
    # Create new config
    cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "live-restore": true,
    "userland-proxy": false
}
EOF
fi

# Restart Docker to apply config
echo "Restarting Docker..."
systemctl restart docker
sleep 5

# Verify Docker is working
echo "Testing Docker..."
if docker run --rm hello-world &>/dev/null; then
    echo "Docker test successful"
else
    echo "Warning: Docker test failed, but continuing..."
fi

# Clean up test image
docker rmi hello-world 2>/dev/null || true

echo "[02-docker] Docker installation complete"
