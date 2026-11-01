#!/usr/bin/env bash
# Rebuilds the Tron lab's snapshots from the network (day 5 in snapshot/, day 9 in snapshot/d9/), then the saved
# results pages.
#   bash build/build-snapshot.sh            (from dynamic-labs/tron; needs Node 20+, Python and duckdb==1.4.3)
# Reads TronGrid's public java-tron node (set TRON_NODE to use another). A rebuild re-reads the blacklist and
# balances as of a new block, so freeze.csv and meta.json change: update quizes/facts.json, the worksheet and
# quizes/INSTRUCTOR_ANSWERS.md (day 9: quizes/facts_d9.json, static/lab/d9/ and quizes/INSTRUCTOR_ANSWERS_D9.md)
# from the new output. Each labels.csv is written by hand, one cited line per address.
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

# Day 9: the deposit address OFAC listed for a Tren de Aragua designee, 1 Sep-30 Nov 2023. java-tron gives balances
# only at the latest block, so the balance it held on 1 Sep comes from its history since its first USDT in Mar 2022.
case=TDxZ1XTZCmqkJJW2eJT362z6omRchJyGBX
node tron-extract.mjs index "$work/part-d9" 2023-09-01T00:00:00Z 2023-12-01T00:00:00Z "$case"
node tron-extract.mjs index "$work/part-d9-history" 2022-03-01T00:00:00Z 2023-12-01T00:00:00Z "$case"
node tron-merge.mjs merge ../snapshot/d9 "$work/part-d9"
python opening_balance.py "$work/part-d9-history" ../snapshot/d9 "$case" 2023-09-01T00:00:00Z
# Tether's blacklist events on designation day, and the other six addresses the OFAC action lists.
node tron-freeze.mjs ../snapshot/d9 2026-09-30T16:14:00Z 2026-09-30T16:15:00Z   TJjRAn9kLiyh8h6gjBjaYjkfDkskgZfyW9 TCUmMCHQEbFFdGvfdg2LeS64QfzUKP2AgW THwbVuBBb26abe5TrAsYUpYz9mhWnBppdz   TBEmt7kPSwAv6NJTYKNdBVW524bUfPwJpJ TCifMAMwst3oEJx8GaNfqZw75dkFUa8vjG TWJmTGhquvdp1jhBmgeGxBBwefteGZUQYW
node tron-merge.mjs seal ../snapshot/d9 "opening_balance.csv: the case address's USDT on 1 Sep 2023, summed by opening_balance.py from an index extract of 1 Mar 2022-1 Dec 2023 (its first USDT movement is 20 Mar 2022)."
cd ..
python build/saved_results.py
