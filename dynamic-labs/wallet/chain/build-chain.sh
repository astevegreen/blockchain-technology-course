#!/usr/bin/env bash
# Rebuilds the wallet lab's frozen chain: blocks.hex here, facts.json in ../quizes/ (answers stay fenced), and the saved pages in
# gateway/static/fallback/. Run from anywhere on a Docker host (in Git Bash, MSYS_NO_PATHCONV=1 is set below).
#
# A rebuild changes every block hash, transaction ID and time, so the worksheet, INSTRUCTOR_ANSWERS.md and the
# tests must be updated from the new facts.json. Addresses and keys stay the same (they come from the phrases).
set -euo pipefail
export MSYS_NO_PATHCONV=1
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${BITCOIN_MEMPOOL_IMAGE:-ghcr.io/blockchain-course-2026/bitcoin-mempool:latest}"
MOUNT="$HERE"
command -v cygpath >/dev/null && MOUNT="$(cygpath -w "$HERE")"

rm -rf "$HERE/out"
docker run --rm --user root --entrypoint bash -v "$MOUNT:/chain" "$IMAGE" /chain/build-steps.sh
cp "$HERE/out/blocks.hex" "$HERE/"
cp "$HERE/out/facts.json" "$HERE/../quizes/"
docker run --rm --user root --entrypoint python3 -v "$MOUNT:/chain" -v "$MOUNT/../gateway/static/fallback:/fallback" \
  "$IMAGE" /chain/capture_pages.py /chain/out /fallback/index.html
rm -rf "$HERE/out"
