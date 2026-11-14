#!/usr/bin/env bash
# Wraps the mempool image's entrypoint. Once bitcoind answers, an empty node gets the frozen day-6
# chain (chain/blocks.hex) block by block; then the image's own entrypoint carries on as usual.
# The node keeps no volume and has no peers, so every restart starts empty and reloads the same chain.
set -euo pipefail
# The explorer's dashboard opens its websocket at "{network}/api/v1/ws", which the base image's path rewrite
# (bitcoin/mempool/configure-mempool-base-path.sh) misses until the base is rebuilt with its fix: put the prefix in
# front so the dashboard goes live instead of "Offline". A no-op once the prefix is there.
for js in /var/www/mempool/browser/*/main*.js; do
    sed -i "s|\"{network}/api/v1/ws|\"${MEMPOOL_BASE_PATH%/}{network}/api/v1/ws|g" "$js"
done
(
    cli() { bitcoin-cli -datadir=/home/user/.bitcoin "$@"; }
    until cli getblockcount >/dev/null 2>&1; do sleep 2; done
    if [ "$(cli getblockcount)" = 0 ]; then
        while read -r block; do
            result=$(cli submitblock "$block")
            [ -z "$result" ] || echo "load-chain: submitblock said: $result" >&2
        done < /chain/blocks.hex
    fi
    echo "load-chain: height $(cli getblockcount)"
) &
exec /usr/local/bin/mempool-entrypoint.sh "$@"
