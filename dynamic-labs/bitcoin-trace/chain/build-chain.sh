#!/usr/bin/env bash
# Rebuilds the Bitcoin trace lab's frozen chain: blocks.hex here, facts.json in ../quizes/ (answers stay fenced),
# the saved pages in gateway/static/fallback/, the worksheet in gateway/static/lab/index.html and the instructor
# answers in ../quizes/INSTRUCTOR_ANSWERS.md. Run from anywhere on a Docker host (in Git Bash, MSYS_NO_PATHCONV=1
# is set below).
#
# A rebuild changes every block hash, transaction ID, address and time. The worksheet and the instructor answers are
# rendered from templates and facts.json, so they follow; the tests read facts.json, so they follow too.
set -euo pipefail
export MSYS_NO_PATHCONV=1
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${BITCOIN_MEMPOOL_IMAGE:-ghcr.io/blockchain-course-2026/bitcoin-mempool:latest}"
LAB="$(cd -- "$HERE/.." && pwd)"
MOUNT="$HERE"
LABMOUNT="$LAB"
command -v cygpath >/dev/null && MOUNT="$(cygpath -w "$HERE")" && LABMOUNT="$(cygpath -w "$LAB")"

rm -rf "$HERE/out"
docker run --rm --user root --entrypoint python3 -v "$MOUNT:/chain" -v "$LABMOUNT/quizes:/steps:ro" \
  "$IMAGE" /steps/build-steps.py
cp "$HERE/out/blocks.hex" "$HERE/"
cp "$HERE/out/facts.json" "$LAB/quizes/"
docker run --rm --user root --entrypoint python3 -v "$LABMOUNT:/lab" "$IMAGE" /lab/chain/capture_pages.py /lab/chain/out /lab/gateway/static/fallback/index.html
docker run --rm --user root --entrypoint python3 -v "$LABMOUNT:/lab" "$IMAGE" /lab/chain/render.py /lab
rm -rf "$HERE/out"
