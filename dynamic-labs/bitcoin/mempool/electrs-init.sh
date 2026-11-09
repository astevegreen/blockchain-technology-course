#!/bin/bash


set -euo pipefail
COOKIE_FILE="${BITCOIN_DATADIR:-/home/user/.bitcoin}/.cookie"
COOKIE="$(cat "$COOKIE_FILE")"   # read the content (e.g., user:longhash)
exec /usr/local/bin/electrs \
  --daemon-dir "${BITCOIN_DATADIR:-/home/user/.bitcoin}" \
  --cookie "${COOKIE}" \
  --electrum-rpc-addr 127.0.0.1:50001 \
  --http-addr 127.0.0.1:3000 \
  --lightmode
