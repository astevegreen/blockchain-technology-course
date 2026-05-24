#!/usr/bin/env bash
set -euo pipefail

DATADIR="${1:-/home/user/.bitcoin}"
SCAN_NET="${2:-auto}"

# Find a sane /24 to probe (keeps it fast in a lab)
if [[ "${SCAN_NET}" == "auto" ]]; then
  # Prefer a robust one-liner: IPv4/CIDR on eth0, then truncate to /24
  CIDR=$(ip -4 -o addr show dev eth0 | awk '{print $4}')
  BASE=$(echo "$CIDR" | cut -d/ -f1 | awk -F. '{print $1"."$2"."$3}')
else
  # Accept explicit "10.10.42" (no /24 suffix) or "10.10.42.0/24"
  BASE=$(echo "$SCAN_NET" | sed -E 's@/.*$@@' | awk -F. '{print $1"."$2"."$3}')
fi

# Small delay so bitcoind is fully ready
sleep 3

while true; do 

    for i in $(seq 1 254); do
    IP="${BASE}.${i}"
    # Skip self
    if ip -4 -o addr show dev eth0 | grep -q " ${IP}/"; then
        continue
    fi
    # Lightweight TCP check on 8333 (Bitcoin P2P)
    if nc -z -w1 "${IP}" 8333 2>/dev/null; then
        # Try a one-shot connection to populate addrman and let Core handle the rest
        bitcoin-cli -datadir="${DATADIR}" addnode "${IP}:8333" onetry || true
    fi
    done

    sleep 300

done