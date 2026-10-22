#!/bin/bash
# network-fallback.sh — wait for DHCP, fall back to static IP if none arrives.
# Installed by provision.sh as a systemd oneshot (network-fallback.service).

set -euo pipefail

# With no FALLBACK_IP set, each VM works out its own 192.168.1.x address from its MAC,
# so a classroom of VMs that all miss DHCP does not fight over one address.
FALLBACK_IP="${FALLBACK_IP:-}"
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

# Host number 10-249 from the last two MAC bytes; $2 steps to the next number when taken.
pick_fallback_ip() {
    local iface="$1" step="${2:-0}" mac b1 b2
    mac="$(cat "/sys/class/net/${iface}/address")"
    b1="${mac:12:2}"
    b2="${mac:15:2}"
    echo "192.168.1.$(( (16#${b1}${b2} + step) % 240 + 10 ))/24"
}

# True when another machine already answers for the address (needs arping; absent = assume free).
address_in_use() {
    local iface="$1" ip="${2%/*}"
    command -v arping >/dev/null 2>&1 || return 1
    ! arping -D -q -c 2 -w 3 -I "${iface}" "${ip}"
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

if [ -z "${FALLBACK_IP}" ]; then
    for step in 0 1 2 3 4; do
        FALLBACK_IP="$(pick_fallback_ip "${IFACE}" "${step}")"
        address_in_use "${IFACE}" "${FALLBACK_IP}" || break
        echo "${FALLBACK_IP} is already in use, trying the next one"
    done
fi

echo "No DHCP lease after ${DHCP_WAIT}s — assigning static fallback ${FALLBACK_IP} on ${IFACE}"
ip addr add "${FALLBACK_IP}" dev "${IFACE}" 2>/dev/null || true
if [ -n "${FALLBACK_GATEWAY}" ]; then
    ip route add default via "${FALLBACK_GATEWAY}" dev "${IFACE}" 2>/dev/null || true
fi
ip -4 addr show dev "${IFACE}" scope global
