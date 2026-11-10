#!/usr/bin/env bash
# Rebuilds the day-10 final trace: the Bitcoin leg's frozen chain (blocks.hex here, facts.json in ../quizes/), the
# invented Tron leg (../snapshot/), the saved pages (../static/fallback/ for Bitcoin, ../static/fallback/tron/ for
# Tron), the worksheet (../static/lab/index.html) and the instructor answers (../quizes/INSTRUCTOR_ANSWERS.md).
# Run from anywhere on a Docker host (in Git Bash, MSYS_NO_PATHCONV=1 is set below). The last step runs on the host
# and needs Python with duckdb 1.4.3, the query page's engine (PYTHON picks the interpreter).
#
# A rebuild changes every block hash, transaction ID, address and time on both legs. The worksheet and the instructor
# answers are rendered from templates and facts.json, so they follow; the tests read facts.json, so they follow too.
set -euo pipefail
export MSYS_NO_PATHCONV=1
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${BITCOIN_MEMPOOL_IMAGE:-ghcr.io/astevegreen/course-labs:base-bitcoin-mempool}"
LAB="$(cd -- "$HERE/.." && pwd)"
MOUNT="$HERE"
LABMOUNT="$LAB"
command -v cygpath >/dev/null && MOUNT="$(cygpath -w "$HERE")" && LABMOUNT="$(cygpath -w "$LAB")"
in_image() { docker run --rm --user root --entrypoint python3 -v "$LABMOUNT:/lab" "$IMAGE" "$@"; }

rm -rf "$HERE/out"
docker run --rm --user root --entrypoint python3 -v "$MOUNT:/chain" -v "$LABMOUNT/quizes:/steps:ro" \
  "$IMAGE" /steps/build-steps.py
cp "$HERE/out/blocks.hex" "$HERE/"
cp "$HERE/out/facts.json" "$LAB/quizes/"
in_image /lab/quizes/invent_tron.py /lab
in_image /lab/chain/capture_pages.py /lab/chain/out /lab/static/fallback/index.html
in_image /lab/chain/render.py /lab
rm -rf "$HERE/out"
HOSTLAB="$LAB"
command -v cygpath >/dev/null && HOSTLAB="$(cygpath -m "$LAB")"
"${PYTHON:-python}" "$HOSTLAB/build/saved_results.py"
