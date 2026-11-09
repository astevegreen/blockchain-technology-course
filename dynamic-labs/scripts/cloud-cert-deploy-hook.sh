#!/bin/bash
# cloud-cert-deploy-hook.sh <domain> - hand the cloud host's Let's Encrypt certificate
# to the router.
#
# Copies /etc/letsencrypt/live/<domain>/{fullchain,privkey}.pem to the folder the cloud
# router mounts (router/docker-compose.cloud.yml) and, when the router is running, reloads
# nginx so new connections get the new certificate with no downtime. deploy-cloud.sh runs
# it after it gets or reuses the certificate, and installs it as certbot's deploy hook
# (/etc/letsencrypt/renewal-hooks/deploy/), which certbot runs after each renewal.

set -euo pipefail

DOMAIN="${1:?usage: cloud-cert-deploy-hook.sh <domain>}"
LIVE_DIR="${LETSENCRYPT_DIR:-/etc/letsencrypt}/live/${DOMAIN}"
ROUTER_CERT_DIR="${ROUTER_CERT_DIR:-/etc/course-labs/router-certs}"
ROUTER_CONTAINER="${ROUTER_CONTAINER:-router-router-1}"

# certbot runs every deploy hook for each certificate it renews and names that one in
# RENEWED_LINEAGE; only the lab certificate concerns the router.
if [[ -n "${RENEWED_LINEAGE:-}" && "${RENEWED_LINEAGE%/}" != "${LIVE_DIR}" ]]; then
    exit 0
fi

# Written beside the old files, then renamed over them, so the router never reads a
# half-written file. The key stays readable by root only (the nginx master runs as root).
umask 077
mkdir -p "${ROUTER_CERT_DIR}"
chmod 700 "${ROUTER_CERT_DIR}"
rm -f "${ROUTER_CERT_DIR}/.fullchain.pem.new" "${ROUTER_CERT_DIR}/.privkey.pem.new"
cp "${LIVE_DIR}/fullchain.pem" "${ROUTER_CERT_DIR}/.fullchain.pem.new"
cp "${LIVE_DIR}/privkey.pem" "${ROUTER_CERT_DIR}/.privkey.pem.new"
chmod 644 "${ROUTER_CERT_DIR}/.fullchain.pem.new"
mv -f "${ROUTER_CERT_DIR}/.fullchain.pem.new" "${ROUTER_CERT_DIR}/fullchain.pem"
mv -f "${ROUTER_CERT_DIR}/.privkey.pem.new" "${ROUTER_CERT_DIR}/privkey.pem"
echo "Router certificate for ${DOMAIN} copied to ${ROUTER_CERT_DIR}"

if command -v docker >/dev/null 2>&1 \
    && [[ -n "$(docker ps -q --filter "name=^${ROUTER_CONTAINER}$" 2>/dev/null || true)" ]]; then
    docker exec "${ROUTER_CONTAINER}" nginx -t -q
    docker exec "${ROUTER_CONTAINER}" nginx -s reload
    echo "Router reloaded"
fi
