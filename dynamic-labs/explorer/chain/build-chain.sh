#!/usr/bin/env bash
# Rebuilds the day-1 course chain and everything made from it:
#   course-chain.json   the frozen chain Anvil loads (blocks 0-10)
#   addresses.env       the accounts and contracts the worksheet names
#   sourcify/           the contracts' source, laid out as Sourcify stores it, for Otterscan
#   ../gateway/static/fallback/index.html   the saved explorer pages (the lab's fallback)
# Needs only Docker. Run from anywhere: bash dynamic-labs/explorer/chain/build-chain.sh
# The chain's hashes change on every rebuild, so the worksheet answers must be refreshed after
# one (INSTRUCTOR_ANSWERS.md lists them; the regression tests check them).
set -euo pipefail
export MSYS_NO_PATHCONV=1

here=$(cd "$(dirname "$0")" && pwd)
lab=$(cd "$here/.." && pwd)
FOUNDRY=ghcr.io/foundry-rs/foundry:v1.8.6
PY=python:3.12-alpine
tag="explorer-build-$$"

cleanup() {
    docker rm -f "${tag}-anvil" >/dev/null 2>&1 || true
    docker network rm "${tag}" >/dev/null 2>&1 || true
    rm -rf "$here/out"
}
trap cleanup EXIT

rm -rf "$here/out"
docker run --rm -e HOME=/tmp -v "$here:/chain" "$FOUNDRY" "bash /chain/build-steps.sh"
# shellcheck disable=SC1091
. "$here/out/addresses.env"

rm -rf "$here/sourcify"
docker run --rm -v "$here:/chain" "$PY" python /chain/make_sourcify_copy.py \
    /chain /chain/out/forge-out /chain/sourcify 31337 "CourseToken=$TOKEN" "Splitter=$SPLITTER"
cp "$here/out/course-chain.json" "$here/course-chain.json"
cp "$here/out/addresses.env" "$here/addresses.env"

docker network create "$tag" >/dev/null
docker run -d --name "${tag}-anvil" --network "$tag" -v "$here:/chain:ro" "$FOUNDRY" \
    "anvil --host 0.0.0.0 --port 8545 --load-state /chain/course-chain.json" >/dev/null
docker run --rm --network "$tag" -v "$lab:/lab" "$PY" python /lab/chain/capture_pages.py \
    "http://${tag}-anvil:8545" /lab/chain/addresses.env /lab/gateway/static/fallback/index.html
echo "rebuilt: course-chain.json, addresses.env, sourcify/, gateway/static/fallback/index.html"
