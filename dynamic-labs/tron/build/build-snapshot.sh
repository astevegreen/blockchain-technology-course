#!/usr/bin/env bash
# Rebuilds the Tron lab's snapshot from the network, then the saved results page.
#   bash build/build-snapshot.sh            (from dynamic-labs/tron; needs Node 20+, Python and duckdb==1.4.3)
# Reads TronGrid's public java-tron node (set TRON_NODE to use another). A rebuild re-reads the blacklist and
# balances as of a new block, so freeze.csv and meta.json change: update quizes/facts.json, the worksheet and
# quizes/INSTRUCTOR_ANSWERS.md from the new output. labels.csv is written by hand, one cited line per address.
set -euo pipefail
cd "$(dirname "$0")"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# The worked example: a Binance deposit address in Sep-Oct 2023. The problem: an unnamed one in Sep-Oct 2026.
node tron-extract.mjs index "$work/part-binance" 2023-09-09T00:00:00Z 2023-10-17T00:00:00Z TXLhMxzterktHm9z27XamgXz2EL9EfoBnR
node tron-extract.mjs index "$work/part-2026" 2026-09-15T00:00:00Z 2026-10-20T00:00:00Z TY4zRAJbq9ZEZvWDHQfJh2AcsiJRPKLeVt
node tron-merge.mjs merge ../snapshot "$work/part-binance" "$work/part-2026"

# The freeze: USDT's blacklist events on 23 Apr 2026, and the two wallets The Block names.
node tron-freeze.mjs ../snapshot 2026-04-23T00:00:00Z 2026-04-24T00:00:00Z \
  TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81 TTiDLWE6fZK8okMJv6ijg42yrH6W2pjSr9

node tron-merge.mjs seal ../snapshot
cd ..
python build/saved_results.py
