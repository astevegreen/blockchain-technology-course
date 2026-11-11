#!/usr/bin/env bash
# Wraps the mempool image's entrypoint: the game server (game/server.py) starts beside it and waits for bitcoind,
# then mines the game's chain and funds the crowd, the exchange and the mixer. The image's entrypoint carries on
# as usual (bitcoind, electrs and the mempool explorer). The chain and the game state live in the "chain" volume,
# so a restart keeps the game where it was.
set -euo pipefail
(
    until bitcoin-cli -datadir=/home/user/.bitcoin getblockcount >/dev/null 2>&1; do sleep 2; done
    exec python3 /game/server.py
) &
exec /usr/local/bin/mempool-entrypoint.sh "$@"
