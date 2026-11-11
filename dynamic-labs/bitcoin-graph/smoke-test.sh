#!/usr/bin/env bash
# Smoke test for the bitcoin-graph container. Run on the lab host after
# `docker compose up -d graph`. Exercises: gate, status, rebuild, one
# real address query against the built graph.
set -uo pipefail

C="${GRAPH_CONTAINER:-bitcoin-graph-1}"
fail() { echo "FAIL: $*" >&2; exit 1; }
note() { echo "--- $*"; }

curl_app() { docker exec "$C" curl -fsS "http://127.0.0.1:8082$1"; }
# jq runs in the container (the image installs it); the host may not have it.
jq() { docker exec -i "$C" jq "$@"; }

note "container up?"
docker inspect -f '{{.State.Status}}' "$C" | grep -q running || fail "$C not running"

note "bitcoind synced?"
docker exec "$C" bitcoin-cli getblockcount || fail "bitcoind RPC dead"

note "status endpoint (gate off -> enabled:false, still served)"
curl_app /labs/bitcoin/graph/api/status | tee /tmp/graph-status.json | grep -q '"enabled"' \
  || fail "status endpoint broken"

note "gate off blocks the UI"
code=$(docker exec "$C" curl -s -o /dev/null -w '%{http_code}' \
        http://127.0.0.1:8082/labs/bitcoin/graph/)
[ "$code" = "403" ] || fail "expected 403 with gate off, got $code"

# Whatever happens below, leave the gate at its default (off).
trap 'docker exec "$C" graph-gate off >/dev/null 2>&1 || true' EXIT

note "enable gate"
docker exec "$C" graph-gate on || fail "graph-gate on failed"
code=$(docker exec "$C" curl -s -o /dev/null -w '%{http_code}' \
        http://127.0.0.1:8082/labs/bitcoin/graph/)
[ "$code" = "200" ] || fail "expected 200 with gate on, got $code"

state=$(jq -r '.state' < /tmp/graph-status.json 2>/dev/null || echo unknown)
if [ "$state" != "ready" ]; then
  note "graph not built (state=$state) — triggering rebuild and waiting"
  docker exec -d "$C" graph-rebuild --wait-sync
  for _ in $(seq 1 360); do
    state=$(curl_app /labs/bitcoin/graph/api/status | jq -r '.state')
    [ "$state" = "ready" ] && break
    [ "$state" = "error" ] && { curl_app /labs/bitcoin/graph/api/status; fail "rebuild errored"; }
    sleep 10
  done
  [ "$state" = "ready" ] || fail "rebuild did not finish in 60min"
fi

note "graph ready:"
curl_app /labs/bitcoin/graph/api/status | jq .

note "query round-trip: busiest address"
# The address prefix differs per chain (bcrt1 regtest, tb1 signet/testnet,
# bc1 mainnet, plus legacy 1/2/m/n): take the first prefix that matches.
addr=""
for prefix in bcrt1 tb1 bc1 m n 2 1; do
  addr=$(curl_app "/labs/bitcoin/graph/api/search?q=$prefix" | jq -r '.matches[0].id // empty')
  [ -n "$addr" ] && break
done
[ -n "$addr" ] || fail "search found no address under any known prefix"
nodes=$(curl_app "/labs/bitcoin/graph/api/address/$addr" | jq '.nodes | length')
[ "${nodes:-0}" -gt 0 ] || fail "address query returned no nodes"
echo "OK: $addr neighborhood -> $nodes nodes"

note "restore gate to default (off)"
docker exec "$C" graph-gate off

echo "ALL SMOKE TESTS PASSED"
