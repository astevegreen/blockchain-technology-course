#!/usr/bin/env bash
# Instructor only. Mints one certificate NFT per passing student on the day-3 course chain.
# Usage, with the tokens lab running: bash dynamic-labs/tokens/quizes/mint-certificates.sh pass-list.txt
# (pass-list.txt: one address or "seat N" per line; see mint_certificates.py.)
# Run it at the end of day 10 and before restarting the tokens lab: a restart reloads the frozen
# chain, and every certificate (and every badge the class minted) is gone.
set -euo pipefail
export MSYS_NO_PATHCONV=1
list=${1:?usage: mint-certificates.sh <pass-list file>}
here=$(cd "$(dirname "$0")" && pwd)
dl=$(cd "$here/../.." && pwd)
badge=$(grep '^BADGE=' "$dl/tokens/chain/addresses.env" | cut -d= -f2)
reg="$dl/regression-tests/automated/tokens"
listfile="$(cd "$(dirname "$list")" && pwd)/$(basename "$list")"
docker build -q -t dynamic-labs-tokens-regression:local -f "$reg/runner.Dockerfile" "$reg" >/dev/null
docker run --rm --network router-net -v "$dl:/work:ro" -v "$listfile:/pass-list.txt:ro" \
    -w /work dynamic-labs-tokens-regression:local \
    python tokens/quizes/mint_certificates.py /pass-list.txt http://router-router-1/rpc tokens.localhost "$badge"
