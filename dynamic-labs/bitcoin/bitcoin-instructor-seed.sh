#!/usr/bin/env bash
#
# Phase 9.3e: one-shot chain seed for the instructor bitcoin node.
#
# Gated by SEED_CLASSNET=1 so the shared student image (same
# Dockerfile) skips this entirely.
#
# Idempotent: if getblockcount > 0 we do nothing, so restarts /
# reboots of the instructor container don't stack blocks.
#
# Retry budget: up to 3 attempts with 15s sleep between. The
# upstream entrypoint waits for bitcoind RPC before invoking CMD,
# but the wallet subsystem + P2P can lag on cold boot, so we give
# this a little slack. After the budget we still exec into the
# CMD args — ttyd/zellij must come up even if seeding failed.

set -u

: "${BITCOIN_DATADIR:=/home/user/.bitcoin}"
: "${SEED_CLASSNET:=0}"
: "${SEED_WALLET:=instructor_seed}"
: "${SEED_MAX_ATTEMPTS:=3}"
: "${SEED_RETRY_SLEEP:=15}"

log() { echo "[seed] $*" >&2; }

if [[ "${SEED_CLASSNET}" != "1" ]]; then
  exec "$@"
fi

btc() { bitcoin-cli -datadir="${BITCOIN_DATADIR}" "$@"; }

attempt_seed() {
  local height
  height=$(btc getblockcount 2>/dev/null) || return 1
  # Only mine on a truly fresh chain (height exactly 0). Any other
  # value — including empty / non-numeric from a half-initialized RPC
  # — is treated as "not safe to mine" and we skip.
  if [[ "${height}" != "0" ]]; then
    log "chain at height '${height}', not seeding"
    return 0
  fi

  if ! btc listwallets 2>/dev/null | grep -q "\"${SEED_WALLET}\""; then
    btc createwallet "${SEED_WALLET}" >/dev/null 2>&1 \
      || btc loadwallet "${SEED_WALLET}" >/dev/null 2>&1 \
      || return 1
  fi

  local addr
  addr=$(btc -rpcwallet="${SEED_WALLET}" getnewaddress 2>/dev/null) || return 1
  [[ -z "${addr}" ]] && return 1

  btc -rpcwallet="${SEED_WALLET}" generatetoaddress 11 "${addr}" >/dev/null 2>&1 \
    || return 1
  log "mined 11 blocks to ${addr}"
  return 0
}

for attempt in $(seq 1 "${SEED_MAX_ATTEMPTS}"); do
  if attempt_seed; then
    break
  fi
  if [[ "${attempt}" -lt "${SEED_MAX_ATTEMPTS}" ]]; then
    log "attempt ${attempt} failed, retrying in ${SEED_RETRY_SLEEP}s"
    sleep "${SEED_RETRY_SLEEP}"
  else
    log "attempt ${attempt} failed; giving up — ttyd will still start"
  fi
done

exec "$@"
