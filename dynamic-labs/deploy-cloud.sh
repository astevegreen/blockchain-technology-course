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
                                    explorer.DOMAIN, tokens.DOMAIN, dex.DOMAIN,
                                    dex-l2.DOMAIN and exploit.DOMAIN must each have an A record for this host
  --max-student-capacity N          Base capacity for claim-based labs (default 20, max 40)
  --bitcoin-student-capacity N      Override Bitcoin claim-lane capacity
  --consensus-student-capacity N    Override consensus claim-lane capacity
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

  The certificate renews itself: certbot's timer renews it through the
  running router (no downtime) and a deploy hook reloads the router. Rerun
  this script at any time, labs up or down.
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
        --max-student-capacity|--bitcoin-student-capacity|--consensus-student-capacity|--hlf-student-capacity)
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

# The explorer, token, exchange and exploit labs each answer on their own host name, so
# one certificate covers the course domain and these five names.
CERT_NAMES=("$DOMAIN" "explorer.$DOMAIN" "tokens.$DOMAIN" "dex.$DOMAIN" "dex-l2.$DOMAIN" "exploit.$DOMAIN")

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

# Let's Encrypt checks each name by fetching a token from
# http://<name>/.well-known/acme-challenge/. certbot --webroot writes the token into
# ACME_WEBROOT, which the cloud router serves on port 80 (router/https-redirect/on.conf),
# so the certificate is issued and renewed while the labs stay up.
ACME_WEBROOT="/var/www/course-labs-acme"
ACME_STANDIN="course-labs-acme-standin"
ROUTER_CONTAINER="router-router-1"
RENEWAL_CONF="/etc/letsencrypt/renewal/$DOMAIN.conf"
RENEW_HOOK="/etc/letsencrypt/renewal-hooks/deploy/course-labs-router.sh"
RENEW_CRON="/etc/cron.d/course-labs-certbot"

# certbot's renewal settings for this certificate name the webroot.
cert_renews_through_webroot() {
    grep -Eq '^authenticator *= *webroot' "$RENEWAL_CONF" 2>/dev/null \
        && grep -Fq "$ACME_WEBROOT" "$RENEWAL_CONF"
}

# 0 when port 80 on this host serves a file from ACME_WEBROOT for $DOMAIN.
webroot_answers() {
    local probe="deploy-cloud-probe" token answer
    token="$(openssl rand -hex 16)"
    printf '%s' "$token" > "$ACME_WEBROOT/.well-known/acme-challenge/$probe"
    answer="$(curl -fsS --max-time 5 -H "Host: $DOMAIN" \
        "http://127.0.0.1/.well-known/acme-challenge/$probe" 2>/dev/null || true)"
    rm -f "$ACME_WEBROOT/.well-known/acme-challenge/$probe"
    [[ "$answer" == "$token" ]]
}

# Something must serve ACME_WEBROOT on port 80 while certbot runs. A running cloud router
# already does. Before the first deploy nothing does, so a stand-in nginx serves it for
# the minute certbot needs; a router from before the challenge path existed is stopped
# for that minute (lab-manager.sh deploy, below, starts it again).
serve_acme_webroot() {
    local tries
    mkdir -p "$ACME_WEBROOT/.well-known/acme-challenge"
    if webroot_answers; then
        echo "The router serves the challenge path; the labs stay up."
        return 0
    fi
    if [[ -n "$(docker ps -q --filter "name=^${ROUTER_CONTAINER}$")" ]]; then
        echo "The running router does not serve the challenge path yet; stopping it while certbot runs."
        docker stop "$ROUTER_CONTAINER" >/dev/null
    fi
    docker rm -f "$ACME_STANDIN" >/dev/null 2>&1 || true
    docker run -d --rm --name "$ACME_STANDIN" -p 80:80 \
        -v "$ACME_WEBROOT:/usr/share/nginx/html:ro" nginx:alpine >/dev/null
    trap stop_acme_standin EXIT
    for tries in 1 2 3 4 5 6 7 8 9 10; do
        webroot_answers && return 0
        echo "Waiting for the stand-in web server on port 80 ($tries)..."
        sleep 1
    done
    echo "Port 80 on this host does not serve $ACME_WEBROOT; Let's Encrypt could not check the names." >&2
    exit 1
}

stop_acme_standin() {
    docker rm -f "$ACME_STANDIN" >/dev/null 2>&1 || true
}

# certbot runs every script in renewal-hooks/deploy/ after it renews a certificate.
# Distribution packages ship a systemd timer that runs `certbot renew` twice a day;
# without one, a cron entry does the same.
install_cert_renewal() {
    local timer
    mkdir -p "$(dirname "$RENEW_HOOK")"
    {
        echo '#!/bin/bash'
        echo '# Written by dynamic-labs/deploy-cloud.sh: after a renewal, copy the certificate to the'
        echo '# lab router and reload it. Rerun deploy-cloud.sh if the course folder moves.'
        printf 'exec /bin/bash %q %q\n' "${SCRIPT_DIR}/scripts/cloud-cert-deploy-hook.sh" "$DOMAIN"
    } > "$RENEW_HOOK"
    chmod 755 "$RENEW_HOOK"
    for timer in certbot.timer snap.certbot.renew.timer; do
        if systemctl cat "$timer" >/dev/null 2>&1; then
            systemctl enable --now "$timer" >/dev/null 2>&1 || true
            echo "Certificate renewal: $timer runs certbot renew; $RENEW_HOOK reloads the router."
            return 0
        fi
    done
    {
        echo '# Written by dynamic-labs/deploy-cloud.sh: certbot renews the lab certificate within'
        echo '# 30 days of expiry; its deploy hook reloads the router.'
        echo '17 3,15 * * * root certbot renew --quiet'
    } > "$RENEW_CRON"
    echo "Certificate renewal: $RENEW_CRON runs certbot renew; $RENEW_HOOK reloads the router."
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

if [ -f "$FULLCHAIN_PATH" ] && [ -f "$PRIVKEY_PATH" ] && openssl x509 -checkend 86400 -noout -in "$FULLCHAIN_PATH" >/dev/null 2>&1 && cert_covers_all_names && cert_renews_through_webroot; then
    echo "Reusing existing Let's Encrypt certificate for ${CERT_NAMES[*]}"
else
    check_dns_records || exit 1
    echo "Requesting Let's Encrypt certificate for ${CERT_NAMES[*]}..."
    certbot_domains=()
    for name in "${CERT_NAMES[@]}"; do
        certbot_domains+=(-d "$name")
    done
    serve_acme_webroot
    # --cert-name keeps the files in live/$DOMAIN; --expand adds the lab names to a
    # certificate issued for the domain alone; --force-renewal also replaces a valid
    # certificate that renews some other way (one an earlier deploy got with
    # --standalone), so its renewal settings become the webroot.
    certbot certonly --webroot -w "$ACME_WEBROOT" --cert-name "$DOMAIN" --expand --force-renewal \
        "${certbot_domains[@]}" --non-interactive --agree-tos --email admin@"$DOMAIN"
    stop_acme_standin
fi

# 3. Hand the certificate to the router, and keep it renewed: certbot's timer renews it
# through the same webroot within 30 days of expiry, and the deploy hook copies each new
# one to the router and reloads it.
bash "${SCRIPT_DIR}/scripts/cloud-cert-deploy-hook.sh" "$DOMAIN"
install_cert_renewal

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
    bash "${SCRIPT_DIR}/lab-manager.sh" build-images bitcoin consensus hlf

echo "Cloud deployment complete. The router is now serving on https://$DOMAIN"
echo "Instructor credentials written to ${INSTRUCTOR_CREDENTIALS_FILE}"
if [[ "${#CLASS_GATE_ARGS[@]}" -gt 0 ]]; then
    echo "Students enter the class code (in the same file and the instructor portal) before any lab page."
fi
echo "Start labs with: ./lab-manager.sh start all"
