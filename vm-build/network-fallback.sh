#!/bin/bash
# network-fallback.sh — wait for DHCP, fall back to static IP if none arrives.
# Installed by provision.sh as a systemd oneshot (network-fallback.service).

set -euo pipefail

FALLBACK_IP="${FALLBACK_IP:-192.168.1.33/24}"
FALLBACK_GATEWAY="${FALLBACK_GATEWAY:-192.168.1.1}"
DHCP_WAIT="${DHCP_WAIT:-15}"

get_first_ethernet() {
    local iface
    for iface in /sys/class/net/*; do
        iface="$(basename "${iface}")"
        [[ "${iface}" == lo ]] && continue
        [[ "${iface}" == docker* ]] && continue
        [[ "${iface}" == br-* ]] && continue
        [[ "${iface}" == veth* ]] && continue
        [[ "${iface}" == wl* ]] && continue
        echo "${iface}"
        return 0
    done
    return 1
}

has_routable_ip() {
    local iface="$1"
    ip -4 addr show dev "${iface}" scope global 2>/dev/null | grep -q 'inet '
}

IFACE="$(get_first_ethernet)" || { echo "No ethernet interface found"; exit 1; }

if ! ip link show "${IFACE}" | grep -q 'state UP'; then
    echo "Bringing up ${IFACE}..."
    ip link set "${IFACE}" up
    sleep 2
fi

echo "Waiting up to ${DHCP_WAIT}s for DHCP lease on ${IFACE}..."
elapsed=0
while [ "${elapsed}" -lt "${DHCP_WAIT}" ]; do
    if has_routable_ip "${IFACE}"; then
        echo "DHCP lease acquired on ${IFACE}:"
        ip -4 addr show dev "${IFACE}" scope global
        exit 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
done

echo "No DHCP lease after ${DHCP_WAIT}s — assigning static fallback ${FALLBACK_IP} on ${IFACE}"
ip addr add "${FALLBACK_IP}" dev "${IFACE}" 2>/dev/null || true
if [ -n "${FALLBACK_GATEWAY}" ]; then
    ip route add default via "${FALLBACK_GATEWAY}" dev "${IFACE}" 2>/dev/null || true
fi
ip -4 addr show dev "${IFACE}" scope global
