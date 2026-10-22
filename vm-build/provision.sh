#!/bin/bash
set -euo pipefail

# Wait for cloud-init to finish
echo "Waiting for cloud-init to complete..."
cloud-init status --wait || true

# Update and install dependencies
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
apt-get install -y \
    arping \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    hostapd \
    dnsmasq \
    isc-dhcp-server \
    iptables \
    git \
    unzip \
    vim \
    nano

# Install Docker
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Add student to docker group
usermod -aG docker student

# Reassert passwordless sudo explicitly in the image, even though
# cloud-init already grants it in user-data. This makes the final VM
# less dependent on cloud-init semantics and gives us one canonical
# sudoers drop-in to validate during the build.
install -d -m 0755 /etc/sudoers.d
cat > /etc/sudoers.d/90-student-nopasswd <<'EOF'
student ALL=(ALL) NOPASSWD:ALL
EOF
chmod 0440 /etc/sudoers.d/90-student-nopasswd
visudo -cf /etc/sudoers.d/90-student-nopasswd

# Network fallback: try DHCP, assign static IP if no lease arrives
install -m 755 /tmp/network-fallback.sh /usr/local/bin/network-fallback.sh
install -m 644 /tmp/network-fallback.service /etc/systemd/system/network-fallback.service
systemctl daemon-reload
systemctl enable network-fallback.service

# Make sure the classroom-network services are stopped by default
systemctl disable hostapd || true
systemctl disable dnsmasq || true
systemctl disable isc-dhcp-server || true
systemctl stop hostapd || true
systemctl stop dnsmasq || true
systemctl stop isc-dhcp-server || true

echo "Provisioning complete."
