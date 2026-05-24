#!/usr/bin/env bash
set -euo pipefail


# Ensure Core datadir and minimal config exist
: "${BITCOIN_DATADIR:=/home/user/.bitcoin}"
mkdir -p "${BITCOIN_DATADIR}"

CONF="${BITCOIN_DATADIR}/bitcoin.conf"
if [[ ! -f "$CONF" ]]; then
  cat > "$CONF" <<EOF
server=1
listen=1
txindex=1
fallbackfee=0.0001
rpcbind=0.0.0.0
rpcallowip=0.0.0.0/0
EOF
fi

# Start bitcoind if it isn't already
if ! pgrep -x bitcoind >/dev/null 2>&1; then
  bitcoind -datadir="${BITCOIN_DATADIR}" -daemon=1 ${BITCOIN_EXTRA_ARGS:-}
fi

# Wait for bitcoind RPC to be responsive if it's in this same container
# (your base image already starts bitcoind in background)
if command -v bitcoin-cli >/dev/null 2>&1; then
  bitcoin-cli -rpcwait -datadir="${BITCOIN_DATADIR:-/home/user/.bitcoin}" getblockchaininfo >/dev/null || true
fi

# Prepare mempool backend config from sample
cd /opt/mempool/backend
if [ -f mempool-config.sample.json ]; then
  cp -f mempool-config.sample.json mempool-config.json
fi


# Add this block if using Electrum backend
if [ "${MEMPOOL_BACKEND_MODE}" = "electrum" ]; then
  if command -v jq >/dev/null 2>&1; then
    jq \
      --arg ehost "${ELECTRUM_HOST}" \
      --argjson eport "${ELECTRUM_PORT}" \
      --arg etls "${ELECTRUM_TLS_ENABLED}" '
      .ELECTRUM.HOST = $ehost
      | .ELECTRUM.PORT = $eport
      | .ELECTRUM.TLS_ENABLED = ( ($etls|test("(?i)true")) )
    ' mempool-config.json > mempool-config.json.tmp && mv mempool-config.json.tmp mempool-config.json
  fi
fi




# Patch config (jq if available; fall back to sed)
if command -v jq >/dev/null 2>&1; then

# Normalize STATS_ENABLED to a JSON boolean for jq
stats_bool="false"
case "${STATS_ENABLED:-true}" in
  [Tt][Rr][Uu][Ee] ) stats_bool="true" ;;
esac
    jq \
    --arg net "${MEMPOOL_NETWORK}" \
    --arg mode "${MEMPOOL_BACKEND_MODE}" \
    --argjson hp ${MEMPOOL_HTTP_PORT:-8999} \
    --arg host "${CORE_RPC_HOST}" \
    --argjson port ${CORE_RPC_PORT:-8332} \
    --arg user "${CORE_RPC_USERNAME}" \
    --arg pass "${CORE_RPC_PASSWORD}" \
    --argjson timeout ${CORE_RPC_TIMEOUT:-60000} \
    --arg dbhost "${DB_HOST}" \
    --argjson dbport ${DB_PORT:-3306} \
    --arg dbname "${DB_NAME}" \
    --arg dbuser "${DB_USER}" \
    --arg dbpass "${DB_PASS}" \
    --argjson stats ${stats_bool} '
        .MEMPOOL.NETWORK = $net
        | .MEMPOOL.BACKEND = $mode
        | .MEMPOOL.HTTP_PORT = $hp
        | .CORE_RPC.HOST = $host
        | .CORE_RPC.PORT = $port
        | .CORE_RPC.USERNAME = $user
        | .CORE_RPC.PASSWORD = $pass
        | .CORE_RPC.TIMEOUT = $timeout
        | .DATABASE.ENABLED = true
        | .DATABASE.HOST = $dbhost
        | .DATABASE.PORT = $dbport
        | .DATABASE.DATABASE = $dbname
        | .DATABASE.USERNAME = $dbuser
        | .DATABASE.PASSWORD = $dbpass
        | .STATISTICS.ENABLED = $stats
    ' mempool-config.json > mempool-config.json.tmp && mv mempool-config.json.tmp mempool-config.json
else
  # minimal sed fallback for the most important values
  sed -i "s/\"NETWORK\":.*/\"NETWORK\": \"${MEMPOOL_NETWORK}\"/g" mempool-config.json || true
  sed -i "s/\"BACKEND\":.*/\"BACKEND\": \"${MEMPOOL_BACKEND_MODE}\"/g" mempool-config.json || true
fi


COOKIE_PATH="/home/user/.bitcoin/.cookie"  # or /home/user/.bitcoin/regtest/.cookie
COOKIE="$(cat $COOKIE_PATH)"
jq \
  --arg p "${COOKIE}" \
  --arg c "${COOKIE_PATH}" '
  .CORE_RPC.COOKIE = $p       |
  .CORE_RPC.COOKIE_PATH = $c  |
  .CORE_RPC.USERNAME = ""     |
  .CORE_RPC.PASSWORD = ""     |
  .CORE_RPC.DEBUG_LOG_PATH = ""
' /opt/mempool/backend/mempool-config.json \
  > /tmp/m.json && mv /tmp/m.json /opt/mempool/backend/mempool-config.json

jq \
 ' .ELECTRUM.PORT = 50001 ' /opt/mempool/backend/mempool-config.json \
  > /tmp/m.json && mv /tmp/m.json /opt/mempool/backend/mempool-config.json



jq '
  .MEMPOOL.AUTOMATIC_POOLS_UPDATE = false
| .MEMPOOL.POOLS_JSON_URL = ""
| .MEMPOOL.POOLS_JSON_TREE_URL = ""
| .MEMPOOL.PRICE_UPDATES_PER_HOUR = 0
| .FIAT_PRICE.ENABLED = false
| .MEMPOOL_SERVICES.API = ""
| .MEMPOOL_SERVICES.ACCELERATIONS = false
| .EXTERNAL_DATA_SERVER.MEMPOOL_API = ""
| .EXTERNAL_DATA_SERVER.MEMPOOL_ONION = ""
| .EXTERNAL_DATA_SERVER.LIQUID_API = ""
| .EXTERNAL_DATA_SERVER.LIQUID_ONION = ""
' /opt/mempool/backend/mempool-config.json \
  > /opt/mempool/backend/mempool-config.offline.json && \
mv /opt/mempool/backend/mempool-config.offline.json /opt/mempool/backend/mempool-config.json




jq '
  .MEMPOOL.AUTOMATIC_POOLS_UPDATE = false
| .MEMPOOL.POOLS_JSON_URL = "http://127.0.0.1:8080/dummy/pools/pools-v2.json"
| .MEMPOOL.POOLS_JSON_TREE_URL = "http://127.0.0.1:8080/dummy/pools/tree.json"
| .FIAT_PRICE.ENABLED = false
| .MEMPOOL.PRICE_UPDATES_PER_HOUR = 0
' /opt/mempool/backend/mempool-config.json \
> /opt/mempool/backend/mempool-config.offline.json && \
mv /opt/mempool/backend/mempool-config.offline.json /opt/mempool/backend/mempool-config.json


mkdir -p /var/www/mempool/browser/dummy/pools

# pools-v2.json — use your own offline copy here.
# If you don't have one handy, create a minimal skeleton:

cat >/var/www/mempool/browser/dummy/pools/pools-v2.json <<'JSON'
[]
JSON


# tree.json — minimal GitHub-like tree with a sha for pools-v2.json
cat >/var/www/mempool/browser/dummy/pools/tree.json <<'JSON'

{
  "tree": [
    {
      "path": "pools-v2.json",
      "sha": "offline-local-sha"
    }
  ]
}
JSON

# Make sure Nginx can read them
chown -R www-data:www-data /var/www/mempool/browser/dummy/pools




jq \
      --arg hash "$(sha1sum /var/www/mempool/browser/dummy/pools/pools-v2.json | awk '{print $1}')" \
    '  .tree[0].sha = $hash
    ' /var/www/mempool/browser/dummy/pools/tree.json > tree.json.tmp && mv tree.json.tmp /var/www/mempool/browser/dummy/pools/tree.json



mkdir -p /var/run/mysql
ln -sf /run/mysqld/mysqld.sock /var/run/mysql/mysql.sock

# Start supervisor (MariaDB -> backend -> nginx)
exec "$@"
