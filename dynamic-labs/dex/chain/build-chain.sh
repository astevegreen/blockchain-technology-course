#!/usr/bin/env bash
# Rebuilds the day-4 course chains and everything made from them:
#   course-chain.json      the frozen L1 chain Anvil loads (blocks 0-18): the exchange and the bridge's L1 half
#   course-chain-l2.json   the frozen L2 chain (blocks 0-105): the bridge's L2 half and the bridged token
#   addresses.env          the accounts and contracts the worksheet names
#   sourcify/              the contracts' source, laid out as Sourcify stores it, for both Otterscans
#   ../gateway/static/fallback/index.html   the saved explorer pages, read from the new chains
# Needs only Docker. Run from anywhere: bash dynamic-labs/dex/chain/build-chain.sh
# The block-by-block steps are in ../quizes/build-steps.sh (instructor only: its comments are
# the answers). The chains' hashes change on every rebuild, so refresh the worksheet's worked
# example and quizes/INSTRUCTOR_ANSWERS.md after one; the regression tests check them.
set -euo pipefail
export MSYS_NO_PATHCONV=1

here=$(cd "$(dirname "$0")" && pwd)
lab=$(cd "$here/.." && pwd)
explorer=$(cd "$lab/../explorer" && pwd)
FOUNDRY=ghcr.io/foundry-rs/foundry:v1.8.6
PY=python:3.12-alpine
tag="dex-build-$$"

cleanup() {
    docker rm -f "${tag}-l1" "${tag}-l2" >/dev/null 2>&1 || true
    docker network rm "${tag}" >/dev/null 2>&1 || true
    rm -rf "$here/out"
}
trap cleanup EXIT

rm -rf "$here/out"
docker run --rm -e HOME=/tmp -v "$lab:/lab" "$FOUNDRY" "bash /lab/quizes/build-steps.sh"
# shellcheck disable=SC1091
. "$here/out/addresses.env"

# The explorer lab's script lays out the source; this lab reuses it, once per chain.
rm -rf "$here/sourcify"
docker run --rm -v "$here:/chain" -v "$explorer/chain:/explorer:ro" "$PY" python /explorer/make_sourcify_copy.py \
    /chain /chain/out/forge-out /chain/sourcify 31337 \
    "CourseDollar=$DOLLAR" "WETH=$WETH" "CoursePair=$PAIR" "CourseRouter=$ROUTER" "CourseBridgeL1=$BRIDGE_L1"
docker run --rm -v "$here:/chain" -v "$explorer/chain:/explorer:ro" "$PY" python /explorer/make_sourcify_copy.py \
    /chain /chain/out/forge-out /chain/sourcify 31338 \
    "CourseBridgeL2=$BRIDGE_L2" "BridgedDollar=$BCUSD"
cp "$here/out/course-chain.json" "$here/course-chain.json"
cp "$here/out/course-chain-l2.json" "$here/course-chain-l2.json"
cp "$here/out/addresses.env" "$here/addresses.env"

docker network create "$tag" >/dev/null
docker run -d --name "${tag}-l1" --network "$tag" -v "$here:/chain:ro" "$FOUNDRY" \
    "anvil --host 0.0.0.0 --port 8545 --load-state /chain/course-chain.json" >/dev/null
docker run -d --name "${tag}-l2" --network "$tag" -v "$here:/chain:ro" "$FOUNDRY" \
    "anvil --host 0.0.0.0 --port 8545 --chain-id 31338 --load-state /chain/course-chain-l2.json" >/dev/null
docker run --rm --network "$tag" -v "$lab:/lab" "$PY" python /lab/chain/capture_pages.py \
    "http://${tag}-l1:8545" "http://${tag}-l2:8545" /lab/chain/addresses.env /lab/gateway/static/fallback/index.html
echo "rebuilt: course-chain.json, course-chain-l2.json, addresses.env, sourcify/, gateway/static/fallback/index.html"
