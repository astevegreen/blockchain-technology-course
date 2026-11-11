#!/usr/bin/env bash
set -euo pipefail

# Mirrors mempool-entrypoint.sh: bring up our own bitcoind on the
# classroom chain, then hand off to supervisord (neo4j + graph-app).

: "${BITCOIN_DATADIR:=/home/user/.bitcoin}"
: "${GRAPH_RUN_DIR:=/run/graph}"
: "${GRAPH_PEER:=bitcoin-instructor-1}"

mkdir -p "${BITCOIN_DATADIR}"

CONF="${BITCOIN_DATADIR}/bitcoin.conf"
if [[ ! -f "$CONF" ]]; then
  cat > "$CONF" <<EOF
server=1
listen=1
txindex=1
fallbackfee=0.0001
addnode=${GRAPH_PEER}
EOF
fi

if ! pgrep -x bitcoind >/dev/null 2>&1; then
  bitcoind -datadir="${BITCOIN_DATADIR}" -daemon=1 ${BITCOIN_EXTRA_ARGS:-}
fi

bitcoin-cli -rpcwait -datadir="${BITCOIN_DATADIR}" getblockchaininfo >/dev/null || true

# Runtime state: gate flag (tool hidden from students until the
# instructor enables it) + build status. Container-lifetime only —
# a recreate resets the gate to the safe default (off).
mkdir -p "${GRAPH_RUN_DIR}"
[[ -f "${GRAPH_RUN_DIR}/enabled" ]] || echo "off" > "${GRAPH_RUN_DIR}/enabled"
if [[ ! -f "${GRAPH_RUN_DIR}/status.json" ]]; then
  echo '{"state": "empty"}' > "${GRAPH_RUN_DIR}/status.json"
fi
chmod 755 "${GRAPH_RUN_DIR}"
chmod 644 "${GRAPH_RUN_DIR}/enabled" "${GRAPH_RUN_DIR}/status.json"

# The neo4j data dir lives on a named volume; the debian package user
# must own it after a fresh volume mount.
chown -R neo4j:neo4j /var/lib/neo4j/data

exec "$@"
