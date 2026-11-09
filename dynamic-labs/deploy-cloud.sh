#!/bin/bash
# deploy-cloud.sh - Cloud Deployment Script with Let's Encrypt support

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/runtime-credentials.sh"

DOMAIN=""
LAB_MANAGER_DEPLOY_ARGS=()
# A cloud host is on the open internet: students enter the class code first.
CLASS_GATE_ARGS=(--class-gate)

usage() {
    cat <<'EOF'
Usage:
  ./deploy-cloud.sh --domain <your-domain.com> [capacity options]

Options:
  --domain DOMAIN                   Public DNS name for Let's Encrypt and router TLS; DOMAIN,
                                    explorer.DOMAIN, tokens.DOMAIN, dex.DOMAIN and
                                    dex-l2.DOMAIN must each have an A record for this host
  --max-student-capacity N          Base capacity for claim-based labs (default 20, max 40)
  --bitcoin-student-capacity N      Override Bitcoin claim-lane capacity
  --consensus-student-capacity N    Override consensus claim-lane capacity
  --p2p-trust-student-capacity N    Override P2P trust claim-lane capacity
  --ethereum-student-capacity N     Override Ethereum claim-lane capacity
  --hlf-student-capacity N          Override Hyperledger Fabric claim-lane capacity
  --no-class-gate                   Leave the lab pages open to anyone who finds the host
                                    (the class gate is on by default)
  -h, --help                        Show this help

Notes:
  Capacity options are forwarded to:
    ./lab-manager.sh deploy --mode instructor --class-gate

  Students enter the class code before any lab page. The code is in
  .runtime/instructor-credentials.txt and in the instructor portal, where the
  instructor can change it; changing it signs every student out of the labs.

  Instructor deployments default to 20 claimable lanes and accept up to 40 when
  the host has enough CPU, RAM, and disk for the selected labs.

  Cloud deploy persists the domain in .runtime/cloud-domain.txt, enables HLF
  runtime asset downloads for cloud builds, and prebuilds on-demand lane images.
EOF
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --domain)
            if [[ -z "${2:-}" ]]; then
                echo "--domain requires a value"
                usage
                exit 1
            fi
            DOMAIN="$2"
            shift
            ;;
        --max-student-capacity|--bitcoin-student-capacity|--consensus-student-capacity|--p2p-trust-student-capacity|--ethereum-student-capacity|--hlf-student-capacity)
            if [[ -z "${2:-}" ]]; then
                echo "$1 requires a value"
                exit 1
            fi
            LAB_MANAGER_DEPLOY_ARGS+=("$1" "$2")
            shift
            ;;
        --no-class-gate)
            CLASS_GATE_ARGS=()
            ;;
        --students)
            echo "--students is no longer supported. Shared labs use singleton containers; use --max-student-capacity for claim-based labs."
            exit 1
            ;;
        *)
            echo "Unknown parameter passed: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

if [ -z "$DOMAIN" ]; then
    usage
    exit 1
fi

deploy_args=(deploy --mode instructor "${CLASS_GATE_ARGS[@]}" "${LAB_MANAGER_DEPLOY_ARGS[@]}")

if [[ "${DEPLOY_CLOUD_PRINT_LAB_MANAGER_ARGS_ONLY:-0}" == "1" ]]; then
    printf '%q ' "${deploy_args[@]}"
    printf '\n'
    exit 0
fi

echo "Deploying cloud environment for domain: $DOMAIN"
export_runtime_credentials "${ROTATE_RUNTIME_CREDENTIALS:-0}"

CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
FULLCHAIN_PATH="$CERT_DIR/fullchain.pem"
PRIVKEY_PATH="$CERT_DIR/privkey.pem"

# The explorer, token and exchange labs each answer on their own host name, so
# one certificate covers the course domain and these four names.
CERT_NAMES=("$DOMAIN" "explorer.$DOMAIN" "tokens.$DOMAIN" "dex.$DOMAIN" "dex-l2.$DOMAIN")

# Every name must resolve to this host before certbot runs, or Let's Encrypt
# refuses the certificate. The records are created by whoever deploys, at their
# DNS provider; this only checks them and prints what is missing.
check_dns_records() {
    local public_ip="${PUBLIC_IP:-}" name addrs missing=()
    if [[ -z "$public_ip" ]]; then
        public_ip="$(curl -4 -fsS --max-time 10 https://api.ipify.org 2>/dev/null || true)"
    fi
    for name in "${CERT_NAMES[@]}"; do
        addrs="$(getent ahostsv4 "$name" 2>/dev/null | awk '{print $1}' | sort -u | tr '
' ' ')"
        if [[ -z "$addrs" ]]; then
            missing+=("$name (does not resolve)")
        elif [[ -n "$public_ip" && " $addrs" != *" $public_ip "* ]]; then
            missing+=("$name (resolves to ${addrs% }, not $public_ip)")
        fi
    done
    if [[ "${#missing[@]}" -eq 0 ]]; then
        echo "DNS records found for: ${CERT_NAMES[*]}"
        return 0
    fi
    echo "These names do not point at this host yet:"
    printf '  %s
' "${missing[@]}"
    echo
    echo "Create these records at your DNS provider, wait for them to resolve, and run this script again:"
    for name in "${CERT_NAMES[@]}"; do
        printf '  %-40s A     %s
' "$name" "${public_ip:-<public IPv4 address of this host>}"
    done
    echo "Remove any AAAA record for these names unless it also points at this host."
    echo "Set PUBLIC_IP=<address> if this host's public address was not detected correctly."
    return 1
}

cert_covers_all_names() {
    local sans name
    sans="$(openssl x509 -noout -ext subjectAltName -in "$FULLCHAIN_PATH" 2>/dev/null)" || return 1
    for name in "${CERT_NAMES[@]}"; do
        [[ "$sans" == *"DNS:$name"* ]] || return 1
    done
}

# 1. Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

# 2. Setup Let's Encrypt using Certbot
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update && apt-get install -y certbot
fi

if [ -f "$FULLCHAIN_PATH" ] && [ -f "$PRIVKEY_PATH" ] && openssl x509 -checkend 86400 -noout -in "$FULLCHAIN_PATH" >/dev/null 2>&1 && cert_covers_all_names; then
    echo "Reusing existing Let's Encrypt certificate for ${CERT_NAMES[*]}"
else
    check_dns_records || exit 1
    echo "Requesting Let's Encrypt certificate for ${CERT_NAMES[*]}..."
    certbot_domains=()
    for name in "${CERT_NAMES[@]}"; do
        certbot_domains+=(-d "$name")
    done
    # Make sure port 80 is free before running standalone certbot. --cert-name
    # keeps the files in live/$DOMAIN, where the router mounts them; --expand
    # adds the lab names to a certificate issued for the domain alone.
    certbot certonly --standalone --cert-name "$DOMAIN" --expand "${certbot_domains[@]}"         --non-interactive --agree-tos --email admin@"$DOMAIN"
fi

# Ensure certificates are readable by docker (nginx)
chmod -R 755 /etc/letsencrypt/live/
chmod -R 755 /etc/letsencrypt/archive/

# Persist the cloud domain before handing off so lab-manager.sh starts
# the router with the TLS overlay and can later restart it consistently.
echo "$DOMAIN" > "${RUNTIME_DIR}/cloud-domain.txt"
chmod 644 "${RUNTIME_DIR}/cloud-domain.txt"
runtime_fix_path_ownership "${RUNTIME_DIR}"

echo "Handing off shared deployment to lab-manager.sh..."
LAB_MANAGER_CLOUD_MODE=1 HLF_ALLOW_RUNTIME_DOWNLOADS=1 \
    bash "${SCRIPT_DIR}/lab-manager.sh" "${deploy_args[@]}"

echo "Prebuilding on-demand student images via lab-manager.sh..."
LAB_MANAGER_CLOUD_MODE=1 HLF_ALLOW_RUNTIME_DOWNLOADS=1 \
    bash "${SCRIPT_DIR}/lab-manager.sh" build-images bitcoin consensus p2p_trust ethereum_lab hlf

echo "Cloud deployment complete. The router is now serving on https://$DOMAIN"
echo "Instructor credentials written to ${INSTRUCTOR_CREDENTIALS_FILE}"
if [[ "${#CLASS_GATE_ARGS[@]}" -gt 0 ]]; then
    echo "Students enter the class code (in the same file and the instructor portal) before any lab page."
fi
echo "Start labs with: ./lab-manager.sh start all"
