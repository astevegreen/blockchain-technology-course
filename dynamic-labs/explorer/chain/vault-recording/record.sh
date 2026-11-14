#!/usr/bin/env bash
# Records the vault lab's two transactions on a fresh Anvil and writes what its page
# (blockchain-course/assets/labs/the-vault-that-paid-twice/) shows:
#   recording.js     the call trees, logs, internal transfers and balances, read back from the node
#   saved/*.png      the same transactions in Otterscan 2.11.0, saved as pictures
# This kit is instructor-only (dynamic-labs/student-exclude.txt): its notes say what each contract does.
# Needs Docker; the pictures also need Chrome or Edge on this machine (set CHROME to its path if it
# is not found). Run from anywhere: bash dynamic-labs/explorer/chain/vault-recording/record.sh
# A rerun gives the same addresses and hashes: the accounts come from Anvil's public test phrase and
# every block's time is set (steps.sh).
set -euo pipefail
export MSYS_NO_PATHCONV=1

winpath() { pwd -W 2>/dev/null || pwd; }   # Git Bash: give Docker Desktop and Chrome C:/... paths
here=$(cd "$(dirname "$0")" && winpath)
page=$(cd "$here/../../../../blockchain-course/assets/labs/the-vault-that-paid-twice" && winpath)
explorer=$(cd "$here/../.." && winpath)
FOUNDRY=ghcr.io/foundry-rs/foundry:v1.8.6
OTTERSCAN=otterscan/otterscan:v2.11.0
PY=python:3.12-alpine
RPC_PORT=28545
WEB_PORT=28080
tag="vault-record-$$"

cleanup() {
    docker rm -f "${tag}-anvil" "${tag}-otterscan" >/dev/null 2>&1 || true
    docker network rm "$tag" >/dev/null 2>&1 || true
    rm -rf "$here/out"
}
trap cleanup EXIT
rm -rf "$here/out"

docker network create "$tag" >/dev/null
docker run -d --name "${tag}-anvil" --network "$tag" -p "127.0.0.1:${RPC_PORT}:8545" "$FOUNDRY" \
    "anvil --host 0.0.0.0 --port 8545 --accounts 10 --balance 100 --timestamp 1789999200 --no-mining" >/dev/null
docker run --rm --network "$tag" -e HOME=/tmp -v "$here:/rec" "$FOUNDRY" "bash /rec/steps.sh http://${tag}-anvil:8545"
docker run --rm --network "$tag" -v "$here:/rec" "$PY" python /rec/record.py \
    "http://${tag}-anvil:8545" /rec/out/recording.env /rec/recording.js
mv "$here/recording.js" "$page/recording.js"
# shellcheck disable=SC1091
. "$here/out/recording.env"

chrome=${CHROME:-}
for c in "/c/Program Files/Google/Chrome/Application/chrome.exe" "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
         "$(command -v google-chrome || true)" "$(command -v chromium || true)"; do
    [ -z "$chrome" ] && [ -n "$c" ] && [ -x "$c" ] && chrome=$c
done
if [ -z "$chrome" ]; then
    echo "recording.js written; no Chrome or Edge found, so the Otterscan pictures in saved/ were not retaken" >&2
    exit 0
fi

# Otterscan, pointed at the node and given the two vaults' source so it names their functions. The callers
# stay unverified, as an attacker's contract usually is: the page must not name the answer.
docker run --rm -v "$here:/rec" -v "$explorer/chain:/explorer:ro" "$PY" python /explorer/make_sourcify_copy.py \
    /rec /rec/out/forge-out /rec/out/sourcify 31337 \
    "VaultA=$QUIET" "VaultB=$CAREFUL" >/dev/null
cat > "$here/out/config.json" <<EOF
{"erigonURL": "http://127.0.0.1:${RPC_PORT}", "assetsURLPrefix": "", "experimental": "",
 "chainInfo": {"name": "Course chain (recording)", "faucets": [],
               "nativeCurrency": {"name": "Ether", "symbol": "ETH", "decimals": 18}},
 "externalDataSources": {"kleros": {"enabled": false}, "ccip": {"ensLookups": false}},
 "sourcify": {"localContractVerification": {"enabled": false},
              "sources": {"Course copy": {"url": "http://127.0.0.1:${WEB_PORT}/sourcify", "backendFormat": "RepositoryV1"}}}}
EOF
docker run -d --name "${tag}-otterscan" -p "127.0.0.1:${WEB_PORT}:80" -e DISABLE_CONFIG_OVERWRITE=1 \
    -v "$explorer/otterscan/default.conf:/etc/nginx/conf.d/default.conf:ro" \
    -v "$here/out/config.json:/usr/share/nginx/html/config.json:ro" \
    -v "$here/out/sourcify:/usr/share/nginx/html/sourcify:ro" "$OTTERSCAN" >/dev/null
for _ in $(seq 1 30); do curl -fs "http://127.0.0.1:${WEB_PORT}/config.json" >/dev/null && break; sleep 0.5; done

mkdir -p "$page/saved"
shot() {  # shot <file> <path on Otterscan> <height>
    local out="$page/saved/$1" profile
    profile=$(mktemp -d)
    command -v cygpath >/dev/null && profile=$(cygpath -w "$profile")
    "$chrome" --headless=new --disable-gpu --hide-scrollbars --no-first-run --user-data-dir="$profile" \
        --window-size=1280,"$3" --virtual-time-budget=20000 --screenshot="$out" "http://127.0.0.1:${WEB_PORT}$2" 2>/dev/null
}
shot drain-overview.png "/tx/$DRAIN_TX" 900
shot drain-logs.png "/tx/$DRAIN_TX/logs" 460
shot drain-trace.png "/tx/$DRAIN_TX/trace" 900
shot twist-trace.png "/tx/$TWIST_TX/trace" 900
echo "recorded: recording.js and saved/ (drain $DRAIN_TX, twist $TWIST_TX)"
