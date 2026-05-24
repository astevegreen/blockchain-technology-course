#!/usr/bin/env bash
set -euo pipefail

# Hyperledger Fabric standalone lab launcher
#
# Usage:
#   ./lab.sh doctor
#   ./lab.sh bootstrap
#   ./lab.sh up
#   ./lab.sh enter org1|org2
#   ./lab.sh watch logs|blocks|state
#   ./lab.sh down
#   ./lab.sh reset
#
# Notes:
# - This lab uses the upstream 'fabric-samples/test-network' scripts.
# - For the most reliable experience on Windows, use WSL or Git Bash.

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEBUG_LOG_PATH="${HERE}/runtime/debug.log"
DEBUG_LOG_DIR="$(dirname "${DEBUG_LOG_PATH}")"
DEBUG_ENABLED="${HLF_DEBUG:-0}"
DEBUG_LOG_PATH_CONTAINER="/fabric-samples/test-network/runtime-debug.log"
BOOTSTRAP_LOG_PATH="${HERE}/runtime/bootstrap.log"

# Load .env if present (simple KEY=VALUE lines; ignores comments/blank lines)
load_dotenv() {
  local f="${HERE}/.env"
  [[ -f "${f}" ]] || return 0
  while IFS='=' read -r k v; do
    [[ -z "${k}" ]] && continue
    [[ "${k}" =~ ^[[:space:]]*# ]] && continue
    k="$(echo "${k}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    v="$(echo "${v}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "${k}" ]] && continue
    # Only allow valid shell variable names; skip anything malformed to avoid surprising behavior
    if [[ ! "${k}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
      echo "[hlf] WARN: Skipping invalid .env key: ${k}" >&2
      continue
    fi

    # Strip surrounding single/double quotes (common .env style)
    if [[ "${v}" =~ ^\".*\"$ ]]; then
      v="${v:1:${#v}-2}"
    elif [[ "${v}" =~ ^\'.*\'$ ]]; then
      v="${v:1:${#v}-2}"
    fi

    # Reject values with newlines/control characters (defense-in-depth)
    if [[ "${v}" == *$'\n'* || "${v}" == *$'\r'* || "${v}" == *$'\t'* ]]; then
      echo "[hlf] WARN: Skipping .env key with control characters: ${k}" >&2
      continue
    fi

    export "${k}=${v}"
  done < <(grep -vE '^[[:space:]]*(#|$)' "${f}" || true)
}
load_dotenv

# Ensure debug log directory exists (instrumentation writes here)
ensure_debug_log_dir() {
  if [[ "${DEBUG_ENABLED}" == "1" ]]; then
    mkdir -p "${DEBUG_LOG_DIR}" >/dev/null 2>&1 || true
    : > "${DEBUG_LOG_PATH}" || true
  else
    DEBUG_LOG_PATH="/dev/null"
    DEBUG_LOG_PATH_CONTAINER="/dev/null"
  fi
}
ensure_debug_log_dir

bootstrap_should_stream_stdout() {
  [[ -t 1 || "${HLF_BOOTSTRAP_VERBOSE:-0}" == "1" ]]
}

run_logged_command() {
  local label="$1"
  shift

  if bootstrap_should_stream_stdout; then
    "$@"
    return $?
  fi

  mkdir -p "$(dirname "${BOOTSTRAP_LOG_PATH}")"
  if "$@" >>"${BOOTSTRAP_LOG_PATH}" 2>&1; then
    return 0
  fi

  local rc=$?
  echo "[hlf] ERROR: ${label} failed. Last 50 log lines from ${BOOTSTRAP_LOG_PATH}:" >&2
  tail -n 50 "${BOOTSTRAP_LOG_PATH}" >&2 || true
  return "${rc}"
}

HOST_HLF_DIR="${HLF_HOST_HLF_DIR:-}"
FABRIC_SAMPLES_DEFAULT="${HERE}/runtime/fabric-samples"

# Paths
export FABRIC_SAMPLES_PATH="${FABRIC_SAMPLES_PATH:-${FABRIC_SAMPLES_DEFAULT}}"
TEST_NETWORK="${FABRIC_SAMPLES_PATH}/test-network"
FABRIC_DIR="$(dirname "${FABRIC_SAMPLES_PATH}")"
if [[ -n "${HOST_HLF_DIR}" ]]; then
  HOST_FABRIC_SAMPLES_PATH="${HOST_HLF_DIR}/runtime/fabric-samples"
  HOST_TEST_NETWORK="${HOST_FABRIC_SAMPLES_PATH}/test-network"
else
  HOST_FABRIC_SAMPLES_PATH="${FABRIC_SAMPLES_PATH}"
  HOST_TEST_NETWORK="${TEST_NETWORK}"
fi
CHAINCODE_OVERRIDE_PATH="${HERE}/chaincode_overrides/asset-transfer-basic/chaincode-javascript"
CLI_HELPERS_FILE="${HERE}/scripts/hlf_cli_helpers.sh"
CLI_HELPERS_B64=""

# Defaults
CHANNEL="${HLF_CHANNEL:-diplomas}"
CC_NAME="${HLF_CC_NAME:-basic}"
CC_VERSION="${HLF_CC_VERSION:-1.0}"
CC_SEQUENCE="${HLF_CC_SEQUENCE:-1}"
CHAINCODE_QUERY_READY_TIMEOUT_SECONDS="${HLF_CHAINCODE_QUERY_READY_TIMEOUT_SECONDS:-75}"
CHAINCODE_QUERY_READY_INTERVAL_SECONDS="${HLF_CHAINCODE_QUERY_READY_INTERVAL_SECONDS:-1}"

# Default to JavaScript chaincode so students do not need a local Go toolchain
CC_LANG="${HLF_CC_LANG:-javascript}"
CC_REL_PATH="${HLF_CC_REL_PATH:-../asset-transfer-basic/chaincode-javascript}"

# Pin image tags to the Fabric release installed by install-fabric.sh (override if desired)
IMAGE_TAG="${HLF_IMAGE_TAG:-2.5.15}"
CA_IMAGE_TAG="${HLF_CA_IMAGE_TAG:-1.5.17}"
# fabric-samples no longer publishes v2.5.x tags, so pin a known-good commit
# instead of silently drifting to main.
FABRIC_SAMPLES_REPO="${HLF_FABRIC_SAMPLES_REPO:-https://github.com/hyperledger/fabric-samples.git}"
FABRIC_SAMPLES_REF="${HLF_FABRIC_SAMPLES_REF:-bf7e75c6c159dc1959f3bb8979ed739171673b4d}"

host_arch_to_platform() {
  case "$(uname -m)" in
    x86_64) echo "linux/amd64" ;;
    aarch64|arm64) echo "linux/arm64" ;;
    *) echo "linux/amd64" ;;
  esac
}

platform_to_ttyd_arch() {
  case "$1" in
    linux/amd64) echo "x86_64" ;;
    linux/arm64) echo "aarch64" ;;
    *) echo "x86_64" ;;
  esac
}

PLATFORM="${HLF_PLATFORM:-$(host_arch_to_platform)}"
TTYD_ARCH="${HLF_TTYD_ARCH:-$(platform_to_ttyd_arch "${PLATFORM}")}"
# The tools container only runs CLI commands over gRPC — safe to run natively.
_native_arch="$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')"
TOOLS_PLATFORM="${HLF_TOOLS_PLATFORM:-linux/${_native_arch}}"
USE_COUCHDB="${HLF_USE_COUCHDB:-1}"
DEPLOY_CHAINCODE="${HLF_DEPLOY_CHAINCODE:-1}"

TOOLS_NAME="${HLF_TOOLS_CONTAINER_NAME:-hlf-tools}"

# Web UI configuration
AUTO_LAUNCH_WEB_UI="${HLF_AUTO_LAUNCH_WEB_UI:-1}"
WEB_UI_PORT="${HLF_WEB_UI_PORT:-8080}"
WEB_UI_SCRIPT="${HLF_WEB_UI_SCRIPT:-web_service/app.py}"

print_usage() {
  cat <<'USAGE'
Hyperledger Fabric Standalone Lab Launcher

Commands:
  doctor                 Check prerequisites and paths
  bootstrap              Download fabric-samples and bootstrap binaries/images
  prepare-build-assets   Refresh vendored chaincode assets before Docker builds
  up                     Start Fabric network, create channel, (optionally) deploy chaincode
  health                 Check network and chaincode deployment status
  deploy                 Deploy/upgrade chaincode without restarting the network
  enter org1|org2         Open an interactive tools shell set to Org1 or Org2
  query                  Query chaincode state (all, asset, price)
  watch logs             Tail Fabric network logs
  watch blocks           Print a summary when new blocks are committed
  watch state            Re-query chaincode and print when results change
  web-ui                 Launch the web UI (Flask application)
  down                   Tear down Fabric network
  reset                  Tear down and remove test-network artifacts + tools container

Environment variables:
  FABRIC_SAMPLES_PATH      Path to fabric-samples (default: ./fabric/fabric-samples)
  HLF_CHANNEL              Channel name (default: diplomas)
  HLF_CC_NAME              Chaincode name (default: basic)
  HLF_CC_VERSION           Chaincode version (default: 1.0)
  HLF_CC_SEQUENCE          Chaincode sequence (default: 1)
  HLF_CC_LANG              Chaincode language (default: javascript)
  HLF_CC_REL_PATH          Chaincode path relative to test-network (default: ../asset-transfer-basic/chaincode-javascript)
  HLF_IMAGE_TAG             Fabric docker image tag (default: 2.5.15)
  HLF_CA_IMAGE_TAG          Fabric CA docker image tag (default: 1.5.17)
  HLF_FABRIC_SAMPLES_REF    fabric-samples git ref or commit (default: pinned known-good commit)
  HLF_USE_COUCHDB          1 (default) uses CouchDB, 0 uses LevelDB
  HLF_FABRIC_TOOLS_IMAGE   Override tools image (auto-detected if unset)
  HLF_TOOLS_CONTAINER_NAME Tools container name (default: hlf-tools)
  HLF_DEPLOY_CHAINCODE     1 (default) deploys sample chaincode if available; 0 skips deploy
USAGE
}

die()  { echo "[hlf] ERROR: $*" >&2; exit 1; }
info() { echo "[hlf] $*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

# --- Input validation / hardening ---

is_safe_token() {
  # Reject whitespace and shell metacharacters that could lead to injection if interpolated
  local s="$1"
  [[ -n "$s" ]] || return 1
  [[ "$s" =~ ^[A-Za-z0-9._:/@+-]+$ ]]
}

validate_channel_name() {
  # Fabric channel names: typically lowercase alnum with dots/hyphens (keep strict to prevent injection)
  local ch="$1"
  [[ "$ch" =~ ^[a-z][a-z0-9.-]{2,249}$ ]] || die "Invalid channel name: '${ch}'. Use lowercase letters, digits, '.' or '-', length 3-250."
}

validate_cc_name() {
  local n="$1"
  [[ "$n" =~ ^[A-Za-z0-9._-]{1,64}$ ]] || die "Invalid chaincode name: '${n}'. Allowed: letters, digits, '.', '_', '-', length 1-64."
}

validate_cc_lang() {
  local l="$1"
  case "$l" in
    javascript) return 0 ;;
    go|golang) die "CC_LANG=go requires a Go toolchain; this lab is designed to be self-contained. Use CC_LANG=javascript." ;;
    *) die "Invalid CC_LANG: '${l}'. Allowed: javascript (default)." ;;
  esac
}

validate_image_tag() {
  local t="$1"
  [[ "$t" =~ ^[A-Za-z0-9._-]{1,128}$ ]] || die "Invalid image tag: '${t}'."
}

validate_image_ref() {
  local r="$1"
  is_safe_token "$r" || die "Invalid docker image reference: '${r}'."
}

validate_path_no_ctrl() {
  local p="$1"
  [[ -n "$p" ]] || die "Empty path is not allowed."
  if [[ "$p" == *$'\n'* || "$p" == *$'\r'* || "$p" == *$'\t'* ]]; then
    die "Path contains control characters (refusing): '$p'"
  fi
}

validate_all_inputs() {
  validate_path_no_ctrl "${FABRIC_SAMPLES_PATH}"
  validate_channel_name "${CHANNEL}"
  validate_cc_name "${CC_NAME}"
  validate_cc_lang "${CC_LANG}"
  validate_image_tag "${IMAGE_TAG}"
  validate_image_tag "${CA_IMAGE_TAG}"
  if [[ -n "${HLF_FABRIC_TOOLS_IMAGE:-}" ]]; then
    validate_image_ref "${HLF_FABRIC_TOOLS_IMAGE}"
  fi
  if [[ -n "${TOOLS_NAME}" ]]; then
    [[ "${TOOLS_NAME}" =~ ^[A-Za-z0-9._-]{1,128}$ ]] || die "Invalid tools container name: '${TOOLS_NAME}'."
  fi
}

refresh_cli_helpers_b64() {
  CLI_HELPERS_B64=""
  if [[ -f "${CLI_HELPERS_FILE}" ]] && command -v base64 >/dev/null 2>&1; then
    CLI_HELPERS_B64="$(base64 < "${CLI_HELPERS_FILE}" | tr -d '\n')"
  fi
}

orderer_container_running() {
  docker ps --format '{{.Names}}' | grep -q '^orderer\.example\.com$'
}

# Return 0 if the named container is running. Used to probe peer liveness
# before assembling --peerAddresses so the 3-of-4 endorsement policy can
# succeed when exactly one org is offline, and fail cleanly with
# ENDORSEMENT_POLICY_FAILURE (not a DNS error) when two are.
peer_container_running() {
  local name="$1"
  docker ps --format '{{.Names}}' | grep -qx "${name}"
}

# Print a space-separated list of live peer org short names (org1..org4).
# When scenario logic has stopped a peer for a fault demo, that org is
# omitted here so the invoke never tries to dial it.
live_peer_orgs() {
  local out=""
  peer_container_running "peer0.cascadiastate.example.com" && out+="org1 "
  peer_container_running "peer0.chesapeakecanoe.example.com"      && out+="org2 "
  peer_container_running "peer0.southhudson.example.com"   && out+="org3 "
  peer_container_running "peer0.mapleleaf.example.com"     && out+="org4 "
  echo "${out% }"
}

deploy_chaincode_manual() {
  # Deploy chaincode manually from inside tools container to avoid host connectivity issues
  # This is a workaround for ENDORSEMENT_POLICY_FAILURE when network.sh deployCC runs from host
  
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H3","location":"lab.sh:deploy_chaincode_manual","message":"Starting manual chaincode deployment","data":{"cc_name":"'${CC_NAME}'","cc_version":"'${CC_VERSION}'","cc_sequence":"'${CC_SEQUENCE}'","channel":"'${CHANNEL}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  ensure_tools_container || {
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H4","location":"lab.sh:deploy_chaincode_manual","message":"ensure_tools_container failed","data":{"result":"failed"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    return 1
  }

  info "Deploying chaincode (CaaS) from tools container..."

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H3","location":"lab.sh:deploy_chaincode_manual","message":"Building CaaS deployment command","data":{"cc_name":"'${CC_NAME}'","mode":"ccaas"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  # Execute deployment inside tools container
  local deploy_cmd="
    set -euo pipefail
    cd /fabric-samples/test-network
    # Set variables expected by envVar.sh to avoid unbound variable errors
    export OVERRIDE_ORG=\"\"
    export VERBOSE=\"false\"
    source ./scripts/envVar.sh || {
      echo 'Failed to source envVar.sh' >&2
      exit 1
    }
    
    # CaaS package: peers dial the chaincode gRPC server instead of launching Docker containers.
    mkdir -p /tmp/ccaas-pkg
    echo '{\"address\":\"chaincode-basic:7052\",\"dial_timeout\":\"10s\",\"tls_required\":false}' > /tmp/ccaas-pkg/connection.json
    tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner \
      -cf - -C /tmp/ccaas-pkg connection.json | gzip -n > /tmp/ccaas-pkg/code.tar.gz
    echo '{\"type\":\"ccaas\",\"label\":\"${CC_NAME}_${CC_VERSION}\"}' > /tmp/ccaas-pkg/metadata.json
    tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner \
      -cf - -C /tmp/ccaas-pkg metadata.json code.tar.gz | gzip -n > ${CC_NAME}.tar.gz
    rm -rf /tmp/ccaas-pkg
    PACKAGE_ID=\$(peer lifecycle chaincode calculatepackageid ${CC_NAME}.tar.gz)
    echo \"CCAAS_PACKAGE_ID=\${PACKAGE_ID}\"
    
    # Check approval status for all 5 orgs (no 'local' in heredoc).
    # Org5 (Meridian) is a read-only channel member: we still install and
    # approve the chaincode on its peer so it can query world state, but its
    # approval does not contribute to LifecycleEndorsement, which is
    # explicitly OutOf(3, Org1MSP.peer, Org2MSP.peer, Org3MSP.peer, Org4MSP.peer).
    org1_approved=false
    org2_approved=false
    org3_approved=false
    org4_approved=false
    org5_approved=false
    setGlobals 1
    export CORE_PEER_ADDRESS=peer0.cascadiastate.example.com:7051
    readiness1=\$(peer lifecycle chaincode checkcommitreadiness \
      -C ${CHANNEL} -n ${CC_NAME} -v ${CC_VERSION} --sequence ${CC_SEQUENCE} \
      --peerAddresses peer0.cascadiastate.example.com:7051 \
      --tlsRootCertFiles \"\$PEER0_ORG1_CA\" \
      --output json 2>/dev/null || echo '{}')
    if echo \"\$readiness1\" | jq -r '.approvals.Org1MSP // false' 2>/dev/null | grep -q 'true'; then
      org1_approved=true
    fi
    if echo \"\$readiness1\" | jq -r '.approvals.Org2MSP // false' 2>/dev/null | grep -q 'true'; then
      org2_approved=true
    fi
    if echo \"\$readiness1\" | jq -r '.approvals.Org3MSP // false' 2>/dev/null | grep -q 'true'; then
      org3_approved=true
    fi
    if echo \"\$readiness1\" | jq -r '.approvals.Org4MSP // false' 2>/dev/null | grep -q 'true'; then
      org4_approved=true
    fi
    if echo \"\$readiness1\" | jq -r '.approvals.Org5MSP // false' 2>/dev/null | grep -q 'true'; then
      org5_approved=true
    fi

    # Install on all 5 orgs (use explicit peer addresses for container network)
    setGlobals 1
    peer lifecycle chaincode install ${CC_NAME}.tar.gz \
      --peerAddresses peer0.cascadiastate.example.com:7051 \
      --tlsRootCertFiles \"\$PEER0_ORG1_CA\" || true
    setGlobals 2
    peer lifecycle chaincode install ${CC_NAME}.tar.gz \
      --peerAddresses peer0.chesapeakecanoe.example.com:9051 \
      --tlsRootCertFiles \"\$PEER0_ORG2_CA\" || true
    setGlobals 3
    peer lifecycle chaincode install ${CC_NAME}.tar.gz \
      --peerAddresses peer0.southhudson.example.com:11051 \
      --tlsRootCertFiles \"\$PEER0_ORG3_CA\" || true
    setGlobals 4
    peer lifecycle chaincode install ${CC_NAME}.tar.gz \
      --peerAddresses peer0.mapleleaf.example.com:13051 \
      --tlsRootCertFiles \"\$PEER0_ORG4_CA\" || true
    setGlobals 5
    peer lifecycle chaincode install ${CC_NAME}.tar.gz \
      --peerAddresses peer0.meridian.example.com:15051 \
      --tlsRootCertFiles \"\$PEER0_ORG5_CA\" || true

    # If the definition is already committed at our target sequence, this
    # deploy is a no-op — installation above covered any missing peers. For
    # upgrades (target sequence > committed sequence) we must still approve
    # + commit below, so gate the early-exit on sequence equality, not on
    # mere presence of a prior commit.
    setGlobals 1
    export CORE_PEER_ADDRESS=peer0.cascadiastate.example.com:7051
    committed_json=\$(peer lifecycle chaincode querycommitted -C ${CHANNEL} -n ${CC_NAME} \
      --peerAddresses peer0.cascadiastate.example.com:7051 \
      --tlsRootCertFiles \"\$PEER0_ORG1_CA\" --output json 2>/dev/null || echo '{}')
    committed_seq=\$(echo \"\$committed_json\" | jq -r '.sequence // 0' 2>/dev/null || echo 0)
    if [ \"\$committed_seq\" = \"${CC_SEQUENCE}\" ]; then
      echo \"Chaincode ${CC_NAME} v${CC_VERSION} seq ${CC_SEQUENCE} already committed; install ensured on peers.\" >&2
      exit 0
    fi
    
    # Approve from org1 only if not already approved
    if [ \"\$org1_approved\" != \"true\" ]; then
      setGlobals 1
      export CORE_PEER_ADDRESS=peer0.cascadiastate.example.com:7051
      peer lifecycle chaincode approveformyorg \
        -o orderer.example.com:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --tls --cafile \"\$ORDERER_CA\" \
        --channelID ${CHANNEL} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id \"\$PACKAGE_ID\" \
        --sequence ${CC_SEQUENCE} || {
          echo 'Org1 approval failed' >&2
          exit 1
        }
    else
      echo 'Org1 already approved, skipping...'
    fi
    
    # Approve from org2 only if not already approved
    if [ \"\$org2_approved\" != \"true\" ]; then
      setGlobals 2
      export CORE_PEER_ADDRESS=peer0.chesapeakecanoe.example.com:9051
      peer lifecycle chaincode approveformyorg \
        -o orderer.example.com:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --tls --cafile \"\$ORDERER_CA\" \
        --channelID ${CHANNEL} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id \"\$PACKAGE_ID\" \
        --sequence ${CC_SEQUENCE} || {
          echo 'Org2 approval failed' >&2
          exit 1
        }
    else
      echo 'Org2 already approved, skipping...'
    fi

    # Approve from org3 only if not already approved
    if [ \"\$org3_approved\" != \"true\" ]; then
      setGlobals 3
      export CORE_PEER_ADDRESS=peer0.southhudson.example.com:11051
      peer lifecycle chaincode approveformyorg \
        -o orderer.example.com:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --tls --cafile \"\$ORDERER_CA\" \
        --channelID ${CHANNEL} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id \"\$PACKAGE_ID\" \
        --sequence ${CC_SEQUENCE} || {
          echo 'Org3 approval failed' >&2
          exit 1
        }
    else
      echo 'Org3 already approved, skipping...'
    fi

    # Approve from org4 only if not already approved
    if [ \"\$org4_approved\" != \"true\" ]; then
      setGlobals 4
      export CORE_PEER_ADDRESS=peer0.mapleleaf.example.com:13051
      peer lifecycle chaincode approveformyorg \
        -o orderer.example.com:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --tls --cafile \"\$ORDERER_CA\" \
        --channelID ${CHANNEL} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id \"\$PACKAGE_ID\" \
        --sequence ${CC_SEQUENCE} || {
          echo 'Org4 approval failed' >&2
          exit 1
        }
    else
      echo 'Org4 already approved, skipping...'
    fi

    # Approve from org5 (Meridian) only if not already approved. Org5's
    # approval is not required for LifecycleEndorsement (OutOf(3, Org1..Org4))
    # but the peer needs a local approval to resolve the committed chaincode
    # when queryinstalled / queryCommitted is run later. A failed approval
    # here is logged but non-fatal — commit can still succeed on the four
    # consortium approvals.
    if [ \"\$org5_approved\" != \"true\" ]; then
      setGlobals 5
      export CORE_PEER_ADDRESS=peer0.meridian.example.com:15051
      peer lifecycle chaincode approveformyorg \
        -o orderer.example.com:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --tls --cafile \"\$ORDERER_CA\" \
        --channelID ${CHANNEL} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id \"\$PACKAGE_ID\" \
        --sequence ${CC_SEQUENCE} || {
          echo 'Org5 approval failed (non-fatal; Meridian is read-only)' >&2
        }
    else
      echo 'Org5 already approved, skipping...'
    fi

    # Commit (LifecycleEndorsement is OutOf(3, Org1..Org4) => needs 3-of-4
    # consortium approvals; Org5/Meridian is deliberately excluded).
    setGlobals 1
    export CORE_PEER_ADDRESS=peer0.cascadiastate.example.com:7051
    PEER_CONN_PARMS=(
      --peerAddresses peer0.cascadiastate.example.com:7051
      --tlsRootCertFiles \"\$PEER0_ORG1_CA\"
      --peerAddresses peer0.chesapeakecanoe.example.com:9051
      --tlsRootCertFiles \"\$PEER0_ORG2_CA\"
      --peerAddresses peer0.southhudson.example.com:11051
      --tlsRootCertFiles \"\$PEER0_ORG3_CA\"
      --peerAddresses peer0.mapleleaf.example.com:13051
      --tlsRootCertFiles \"\$PEER0_ORG4_CA\"
    )
    peer lifecycle chaincode commit \
      -o orderer.example.com:7050 \
      --ordererTLSHostnameOverride orderer.example.com \
      --tls --cafile \"\$ORDERER_CA\" \
      \"\${PEER_CONN_PARMS[@]}\" \
      --channelID ${CHANNEL} \
      --name ${CC_NAME} \
      --version ${CC_VERSION} \
      --sequence ${CC_SEQUENCE} || {
        echo 'Commit failed' >&2
        exit 1
      }
    
    echo 'Chaincode deployment completed successfully'
  "

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"E","location":"lab.sh:deploy_chaincode_manual","message":"Executing deployment in tools container","data":{},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  local deploy_output
  deploy_output=$(docker exec -i "${TOOLS_NAME}" bash -lc "$deploy_cmd" 2>&1)
  local deploy_rc=$?

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H3","location":"lab.sh:deploy_chaincode_manual","message":"Manual deployment completed","data":{"exit_code":'$deploy_rc',"output_length":'${#deploy_output}',"has_error":'$(echo "$deploy_output" | grep -qiE "error|failed" && echo "true" || echo "false")',"has_override_org_error":'$(echo "$deploy_output" | grep -q "OVERRIDE_ORG.*unbound" && echo "true" || echo "false")',"has_endorsement_error":'$(echo "$deploy_output" | grep -q "ENDORSEMENT_POLICY_FAILURE" && echo "true" || echo "false")'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion


  if [[ $deploy_rc -ne 0 ]]; then
    echo "[hlf] Manual deployment failed:" >&2
    echo "$deploy_output" | sed 's/^/[hlf]   /' >&2
    return 1
  fi

  echo "$deploy_output" | sed 's/^/[hlf]   /'

  # Extract PACKAGE_ID from deploy output and start the CaaS chaincode container.
  local pkg_id
  pkg_id=$(echo "$deploy_output" | sed -n 's/^CCAAS_PACKAGE_ID=//p' | head -1)
  if [[ -z "${pkg_id}" ]]; then
    echo "[hlf] ERROR: Could not extract PACKAGE_ID from deploy output" >&2
    return 1
  fi

  info "Starting chaincode-basic CaaS container (CHAINCODE_ID=${pkg_id:0:12}...)"
  docker rm -f chaincode-basic >/dev/null 2>&1 || true
  docker run -d \
    --name chaincode-basic \
    --network fabric_test \
    --platform "${PLATFORM}" \
    --restart unless-stopped \
    chaincode-basic:latest \
      npx fabric-chaincode-node server \
      --chaincode-address 0.0.0.0:7052 \
      --chaincode-id "${pkg_id}" >/dev/null

  if ! wait_for_chaincode_query_ready; then
    echo "[hlf] ERROR: chaincode-basic failed to become query-ready after startup" >&2
    return 1
  fi
}

wait_for_chaincode_query_ready() {
  local timeout_seconds="${1:-${CHAINCODE_QUERY_READY_TIMEOUT_SECONDS}}"
  local interval_seconds="${2:-${CHAINCODE_QUERY_READY_INTERVAL_SECONDS}}"
  local elapsed=0
  local out=""

  if ! ensure_tools_container 2>/dev/null; then
    echo "[hlf] ERROR: Cannot create tools container while waiting for chaincode readiness" >&2
    return 1
  fi

  info "Waiting for chaincode query preflight to succeed..."
  while [[ ${elapsed} -lt ${timeout_seconds} ]]; do
    out="$(tools_exec_noninteractive 1 "peer chaincode query -C ${CHANNEL} -n ${CC_NAME} -c '{\"Args\":[\"GetAllAssets\"]}'" 2>&1)" && {
      info "Chaincode query preflight passed."
      return 0
    }

    sleep "${interval_seconds}"
    elapsed=$((elapsed + interval_seconds))
  done

  echo "[hlf] ERROR: Chaincode query preflight did not succeed within ${timeout_seconds}s" >&2
  echo "${out}" >&2
  docker logs --tail 40 chaincode-basic 2>&1 | sed 's/^/[hlf]   /' >&2 || true
  return 1
}

check_chaincode_health() {
  # Check if chaincode is properly deployed and committed
  info "Checking chaincode deployment status..."

  # Check if tools container exists and is healthy
  if ! ensure_tools_container 2>/dev/null; then
    echo "[hlf] ERROR: Cannot create tools container for health check" >&2
    return 1
  fi

  # Check if chaincode is installed on peers (4 consortium + Org5/Meridian).
  # Meridian is a read-only channel member: its install/approval state is
  # surfaced for visibility but does not gate the success return — the lab
  # can operate correctly even if Meridian's peer is lagging.
  local installed_org1 installed_org2 installed_org3 installed_org4 installed_org5
  installed_org1=$(tools_exec_noninteractive 1 "peer lifecycle chaincode queryinstalled" 2>/dev/null | grep -c "${CC_NAME}" || echo "0")
  installed_org2=$(tools_exec_noninteractive 2 "peer lifecycle chaincode queryinstalled" 2>/dev/null | grep -c "${CC_NAME}" || echo "0")
  installed_org3=$(tools_exec_noninteractive 3 "peer lifecycle chaincode queryinstalled" 2>/dev/null | grep -c "${CC_NAME}" || echo "0")
  installed_org4=$(tools_exec_noninteractive 4 "peer lifecycle chaincode queryinstalled" 2>/dev/null | grep -c "${CC_NAME}" || echo "0")
  installed_org5=$(tools_exec_noninteractive 5 "peer lifecycle chaincode queryinstalled" 2>/dev/null | grep -c "${CC_NAME}" || echo "0")

  # Check if chaincode is approved (use jq for reliable JSON parsing)
  local approved_org1 approved_org2 approved_org3 approved_org4 approved_org5
  local readiness_json
  readiness_json=$(tools_exec_noninteractive 1 "peer lifecycle chaincode checkcommitreadiness -C ${CHANNEL} -n ${CC_NAME} -v ${CC_VERSION} --sequence ${CC_SEQUENCE} --output json" 2>/dev/null || echo "{}")

  approved_org1=$(echo "$readiness_json" | jq -r '.approvals.Org1MSP // false' 2>/dev/null | grep -q "true" && echo "1" || echo "0")
  approved_org2=$(echo "$readiness_json" | jq -r '.approvals.Org2MSP // false' 2>/dev/null | grep -q "true" && echo "1" || echo "0")
  approved_org3=$(echo "$readiness_json" | jq -r '.approvals.Org3MSP // false' 2>/dev/null | grep -q "true" && echo "1" || echo "0")
  approved_org4=$(echo "$readiness_json" | jq -r '.approvals.Org4MSP // false' 2>/dev/null | grep -q "true" && echo "1" || echo "0")
  approved_org5=$(echo "$readiness_json" | jq -r '.approvals.Org5MSP // false' 2>/dev/null | grep -q "true" && echo "1" || echo "0")

  # Check if chaincode is committed
  local committed
  committed=$(tools_exec_noninteractive 1 "peer lifecycle chaincode querycommitted -C ${CHANNEL}" 2>/dev/null | grep -c "${CC_NAME}" || echo "0")

  installed_org1=$(echo "$installed_org1" | tr -d '[:space:]')
  installed_org2=$(echo "$installed_org2" | tr -d '[:space:]')
  installed_org3=$(echo "$installed_org3" | tr -d '[:space:]')
  installed_org4=$(echo "$installed_org4" | tr -d '[:space:]')
  installed_org5=$(echo "$installed_org5" | tr -d '[:space:]')
  approved_org1=$(echo "$approved_org1" | tr -d '[:space:]')
  approved_org2=$(echo "$approved_org2" | tr -d '[:space:]')
  approved_org3=$(echo "$approved_org3" | tr -d '[:space:]')
  approved_org4=$(echo "$approved_org4" | tr -d '[:space:]')
  approved_org5=$(echo "$approved_org5" | tr -d '[:space:]')
  committed=$(echo "$committed" | tr -d '[:space:]')

  echo "[hlf] Chaincode health check results:" >&2
  echo "[hlf]   Installed - Org1: ${installed_org1}, Org2: ${installed_org2}, Org3: ${installed_org3}, Org4: ${installed_org4}, Org5(read-only): ${installed_org5}" >&2
  echo "[hlf]   Approved  - Org1: ${approved_org1}, Org2: ${approved_org2}, Org3: ${approved_org3}, Org4: ${approved_org4}, Org5(read-only): ${approved_org5}" >&2
  echo "[hlf]   Committed: ${committed}" >&2

  # Return success if the four consortium orgs are fully deployed. Org5
  # (Meridian) is read-only, so a lagging install/approval on it does not
  # block lab functionality.
  if [[ "$installed_org1" -gt 0 && "$installed_org2" -gt 0 && "$installed_org3" -gt 0 && "$installed_org4" -gt 0 \
     && "$approved_org1" -gt 0 && "$approved_org2" -gt 0 && "$approved_org3" -gt 0 && "$approved_org4" -gt 0 \
     && "$committed" -gt 0 ]]; then
    info "✓ Chaincode is properly deployed and committed"
    return 0
  else
    echo "[hlf] ✗ Chaincode deployment is incomplete" >&2
    return 1
  fi
}

mirror_dev_peer_images_across_peers() {
  # Fabric 2.5's install-time build for node chaincode can silently skip on one
  # peer while succeeding on another (observed on cascadia when chesapeakecanoe built
  # fine — identical package, same docker.sock, same env). When Launch later
  # fires on the "unbuilt" peer, the dockercontroller jumps straight to create
  # container and fails with "No such image: dev-peer0.<fqdn>-<pkg>-<buildhash>".
  #
  # Since the chaincode bits are identical across peers (only the tag's
  # build-hash suffix differs per peer MSP), we provoke a launch on each peer,
  # parse the expected image name from the error, and retag any existing
  # dev-peer image for the same ccname+version under the missing name. The
  # chaincode then launches normally for every subsequent invoke.
  info "Verifying dev-peer chaincode images exist on all peers..."

  local -a orgs=(1 2)
  local org probe_out expected src_img
  local did_mirror=0

  for org in "${orgs[@]}"; do
    probe_out=$(tools_exec_noninteractive "${org}" \
      "peer chaincode query -C ${CHANNEL} -n ${CC_NAME} -c '{\"function\":\"GetAllAssets\",\"Args\":[]}' 2>&1 || true" 2>/dev/null || true)

    # Look for "No such image: dev-peer0.<...>:latest"
    expected=$(echo "${probe_out}" | grep -oE 'dev-peer0\.[a-zA-Z0-9._-]+:latest' | head -n1)
    [[ -z "${expected}" ]] && continue

    if docker image inspect "${expected}" >/dev/null 2>&1; then
      continue
    fi

    # Find any existing dev-peer image for the same chaincode+version to mirror
    src_img=$(docker images --format '{{.Repository}}:{{.Tag}}' \
      | grep -E "^dev-peer0\.[^:]+-${CC_NAME}_${CC_VERSION}-" \
      | grep -v "^${expected}$" \
      | head -n1 || true)

    if [[ -z "${src_img}" ]]; then
      echo "[hlf] WARN: Peer org${org} needs image '${expected}' but no source dev-peer image is available to mirror from." >&2
      continue
    fi

    info "Mirroring chaincode image for org${org}: ${src_img} -> ${expected}"
    docker tag "${src_img}" "${expected}" >/dev/null 2>&1 || true
    did_mirror=1
  done

  if [[ "${did_mirror}" -eq 1 ]]; then
    info "✓ Dev-peer chaincode images mirrored where needed"
  fi
  return 0
}

deploy_chaincode_with_retry() {
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:deploy_chaincode_with_retry","message":"Starting chaincode deployment","data":{"max_retries":3},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  local max_retries=3
  local retry_count=0

  while [[ $retry_count -lt $max_retries ]]; do
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:deploy_chaincode_with_retry","message":"Deployment attempt","data":{"attempt":'$(($retry_count + 1))',"max_retries":'$max_retries'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion

    info "Chaincode deployment attempt $((retry_count + 1))/${max_retries}..."

    # Try the standard deployment
    # Capture full output for debugging
    local deploy_output
    deploy_output=$(cd "${TEST_NETWORK}" && ./network.sh deployCC \
      -ccn "${CC_NAME}" \
      -ccp "${CC_REL_PATH}" \
      -ccl "${CC_LANG}" \
      -ccv "${CC_VERSION}" \
      -ccs "${CC_SEQUENCE}" 2>&1)
    local deploy_rc=$?

    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"E","location":"lab.sh:deploy_chaincode_with_retry","message":"Deployment command completed","data":{"attempt":'$(($retry_count + 1))',"exit_code":'$deploy_rc',"output_length":'${#deploy_output}',"has_endorsement_error":'$(echo "$deploy_output" | grep -q "ENDORSEMENT_POLICY_FAILURE" && echo "true" || echo "false")'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion

    if [[ $deploy_rc -eq 0 ]]; then
      #region agent log
      echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:deploy_chaincode_with_retry","message":"Deployment command succeeded","data":{"attempt":'$(($retry_count + 1))'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
      #endregion

      # Check if deployment was successful
      if check_chaincode_health; then
        #region agent log
        echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:deploy_chaincode_with_retry","message":"Health check passed","data":{"result":"success"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
        #endregion

        mirror_dev_peer_images_across_peers || true
        info "✓ Chaincode deployment successful"
        return 0
      else
        #region agent log
        echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:deploy_chaincode_with_retry","message":"Health check failed","data":{"result":"failed"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
        #endregion

        info "Chaincode deployment completed but health check failed, retrying..."
      fi
    else
      #region agent log
      echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:deploy_chaincode_with_retry","message":"Deployment command failed","data":{"result":"command_failed"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
      #endregion

      # Check for specific endorsement policy failure
      if echo "$deploy_output" | grep -q "ENDORSEMENT_POLICY_FAILURE"; then
        #region agent log
        echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"E","location":"lab.sh:deploy_chaincode_with_retry","message":"ENDORSEMENT_POLICY_FAILURE detected","data":{"attempt":'$(($retry_count + 1))',"error_snippet":"'$(echo "$deploy_output" | grep -A 2 "ENDORSEMENT_POLICY_FAILURE" | head -3 | tr '\n' ';')'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
        #endregion

        echo "[hlf] ERROR: Chaincode approval failed due to endorsement policy" >&2
        echo "[hlf] This usually means the channel's LifecycleEndorsement policy requires both orgs" >&2
        echo "[hlf] but the approval is only getting one org's signature." >&2
        echo "[hlf]" >&2
        echo "[hlf] Attempting workaround: deploying chaincode manually from tools container..." >&2
        
        # Try manual deployment from tools container as workaround
        if deploy_chaincode_manual; then
          #region agent log
          echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"E","location":"lab.sh:deploy_chaincode_with_retry","message":"Manual deployment succeeded","data":{"result":"success"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
          #endregion
          mirror_dev_peer_images_across_peers || true
          info "✓ Chaincode deployment successful (manual method)"
          return 0
        else
          #region agent log
          echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"E","location":"lab.sh:deploy_chaincode_with_retry","message":"Manual deployment also failed","data":{"result":"failed"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
          #endregion
          info "Manual deployment also failed, retrying standard method..."
        fi
      else
        info "Chaincode deployment command failed, retrying..."
      fi
    fi

    retry_count=$((retry_count + 1))
    if [[ $retry_count -lt $max_retries ]]; then
      info "Waiting 5 seconds before retry..."
      sleep 5
    fi
  done

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:deploy_chaincode_with_retry","message":"All attempts failed","data":{"total_attempts":'$max_retries'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  echo "[hlf] ERROR: Chaincode deployment failed after ${max_retries} attempts" >&2
  echo "[hlf] Try running: ./lab.sh deploy" >&2
  echo "[hlf] Or manually check: ./lab.sh enter org1" >&2
  echo "[hlf] Then run: peer lifecycle chaincode querycommitted -C diplomas" >&2
  return 1
}

select_org_num() {
  # Accept: 1..5 or org1..org5 (default org1). Org5 (Meridian) is read-only
  # at the endorsement-policy layer but can still query and — for the
  # forgery-check demo — attempt writes that the chaincode rejects.
  local in="${1:-org1}"
  case "${in}" in
    1|org1) echo "1" ;;
    2|org2) echo "2" ;;
    3|org3) echo "3" ;;
    4|org4) echo "4" ;;
    5|org5) echo "5" ;;
    *) die "Invalid org selector '${in}'. Use '1'..'5' or 'org1'..'org5'." ;;
  esac
}

peer_addr_for_org() {
  local org_num="$1"
  case "${org_num}" in
    1) echo "peer0.cascadiastate.example.com:7051" ;;
    2) echo "peer0.chesapeakecanoe.example.com:9051" ;;
    3) echo "peer0.southhudson.example.com:11051" ;;
    4) echo "peer0.mapleleaf.example.com:13051" ;;
    5) echo "peer0.meridian.example.com:15051" ;;
    *) die "Internal error: unknown org_num '${org_num}'" ;;
  esac
}

invoke_diagnose() {
  # Input: full output text (stdout+stderr)
  local out="$1"

  if echo "$out" | grep -qiE 'first record does not look like a TLS handshake'; then
    cat <<-'EOF'
    Diagnosis: TLS mismatch to the orderer.
    - This usually occurs when a plaintext client hits a TLS-enabled orderer port.
    - Using this helper should prevent it. If it persists:
      - Confirm the orderer is configured for TLS on :7050
      - Confirm ORDERER_CA points to the orderer's TLS CA cert inside the tools container
	EOF
    return 0
  fi

  if echo "$out" | grep -qiE 'context deadline exceeded|i/o timeout|deadline exceeded'; then
    cat <<-'EOF'
  Diagnosis: Orderer unreachable or not responding.
  - Check that orderer.example.com is running and on the same Docker network.
  - Check container health/status and logs:
      docker ps | grep orderer.example.com
      docker logs orderer.example.com --tail 80
	EOF
    return 0
  fi

  if echo "$out" | grep -qiE 'connect: connection refused|connection refused'; then
    cat <<-'EOF'
  Diagnosis: Connection refused.
  - The endpoint is reachable but nothing is listening on that port.
  - Most common causes: orderer container not running, crashed, or wrong port.
	EOF
    return 0
  fi

  if echo "$out" | grep -qiE 'x509: certificate signed by unknown authority|unknown authority'; then
    cat <<-'EOF'
  Diagnosis: TLS CA trust failure.
  - The cafile provided does not match the orderer's TLS CA.
  - Verify ORDERER_CA inside the tools container points to the orderer TLS CA cert.
	EOF
    return 0
  fi

  if echo "$out" | grep -qiE 'cannot find chaincode|chaincode .* not found|not found in channel|could not find chaincode'; then
    cat <<-'EOF'
  Diagnosis: Chaincode not deployed/approved on this channel.
  - Ensure your lab deployed the 'basic' chaincode (or run the deploy step).
	EOF
    return 0
  fi

  if echo "$out" | grep -qiE 'access denied|permission denied|MSP|identity|creator'; then
    cat <<-'EOF'
  Diagnosis: Identity / MSP / endorsement issue.
  - Ensure you are invoking as the intended org (org1 vs org2).
  - Ensure setGlobals loaded the correct MSPCONFIGPATH and TLS root cert.
	EOF
    return 0
  fi

  # Default: no match
  return 1
}

invoke_raw() {
  # Usage: invoke_raw <org_num> <json_payload>
  local org_num="$1"
  local payload="$2"

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"B","location":"lab.sh:invoke_raw","message":"Function called","data":{"org_num":"'$org_num'","payload":"'$payload'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  validate_all_inputs
  validate_cc_name "${CC_NAME}"
  validate_channel_name "${CHANNEL}"

  # Ensure tools container is ready for invoke
  ensure_tools_container || {
    echo "[hlf] ERROR: Tools container not available. Try: ./lab.sh up" >&2
    return 1
  }

  # Basic payload safety: reject control characters/newlines
  if [[ "$payload" == *$'\n'* || "$payload" == *$'\r'* || "$payload" == *$'\t'* ]]; then
    die "Payload contains control characters; refusing."
  fi

  local peer_addr
  peer_addr="$(peer_addr_for_org "${org_num}")"

  # Probe which of the four peer orgs are actually running right now. We
  # only include live peers in --peerAddresses so a single peer outage
  # (fault scenario) still lets 3-of-4 MAJORITY endorsement succeed, and
  # a 2-peer outage fails cleanly with ENDORSEMENT_POLICY_FAILURE rather
  # than a DNS/connect error.
  local live_orgs
  live_orgs="$(live_peer_orgs)"
  local live_count
  live_count="$(echo "${live_orgs}" | wc -w | tr -d ' ')"
  if [[ "${live_count}" -lt 3 ]]; then
    echo "[hlf] WARNING: only ${live_count} of 4 peer orgs are live (${live_orgs})." >&2
    echo "[hlf] The MAJORITY (3-of-4) endorsement policy cannot be satisfied; this invoke will fail with ENDORSEMENT_POLICY_FAILURE." >&2
  fi

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"B","location":"lab.sh:invoke_raw","message":"Peer liveness probe","data":{"live_orgs":"'${live_orgs}'","live_count":'${live_count}'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"B","location":"lab.sh:invoke_raw","message":"Peer address resolved","data":{"peer_addr":"'$peer_addr'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  # Fast preflight on host: orderer container existence
  if ! orderer_container_running; then
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"B","location":"lab.sh:invoke_raw","message":"Orderer container check failed","data":{"result":"not_running"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion

    echo "[hlf] ERROR: orderer.example.com container is not running." >&2
    echo "[hlf] This usually means the network is not started." >&2
    echo "[hlf]" >&2
    echo "[hlf] Try these steps:" >&2
    echo "[hlf]   1) ./lab.sh up          # Start the network" >&2
    echo "[hlf]   2) ./lab.sh watch logs  # Check for errors" >&2
    echo "[hlf]   3) docker ps            # Verify containers are running" >&2
    return 21
  fi

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"B","location":"lab.sh:invoke_raw","message":"Orderer container check passed","data":{"result":"running"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  # Execute inside tools container; pass variables via -e to avoid shell interpolation
  # Use -i (no TTY) for stable capturing of output; always return a classified error on failure

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"B","location":"lab.sh:invoke_raw","message":"About to execute docker command","data":{"tools_name":"'$TOOLS_NAME'","org_num":"'$org_num'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  local out rc
  set +e
  out="$(
    docker exec -i \
      -e ORG_NUM="${org_num}" \
      -e CHANNEL="${CHANNEL}" \
      -e CC_NAME="${CC_NAME}" \
      -e PAYLOAD="${payload}" \
      -e PEER_ADDR="${peer_addr}" \
      -e LIVE_ORGS="${live_orgs}" \
      -e DEBUG_LOG_PATH_CONTAINER="${DEBUG_LOG_PATH_CONTAINER}" \
      "${TOOLS_NAME}" bash -lc '
        set -euo pipefail
        cd /fabric-samples/test-network
        mkdir -p /fabric-samples/test-network >/dev/null 2>&1 || true
        export OVERRIDE_ORG=""
        export VERBOSE="false"
        source ./scripts/envVar.sh
        setGlobals "${ORG_NUM}" >/dev/null 2>&1
        : "${PEER_ADDR:?PEER_ADDR not set}"
        export CORE_PEER_ADDRESS="${PEER_ADDR}"
        : "${ORDERER_CA:?ORDERER_CA is not set by setGlobals}"
        : "${CORE_PEER_LOCALMSPID:?CORE_PEER_LOCALMSPID not set}"
        : "${CORE_PEER_MSPCONFIGPATH:?CORE_PEER_MSPCONFIGPATH not set}"
        : "${CORE_PEER_TLS_ROOTCERT_FILE:?CORE_PEER_TLS_ROOTCERT_FILE not set}"

        #region agent log
        echo "{\"sessionId\":\"debug-session\",\"runId\":\"initial\",\"hypothesisId\":\"B\",\"location\":\"lab.sh:invoke_raw:inner\",\"message\":\"Environment check\",\"data\":{\"orderer_ca\":\"${ORDERER_CA}\",\"peer_msp\":\"${CORE_PEER_LOCALMSPID}\",\"peer_address\":\"${CORE_PEER_ADDRESS}\"},\"timestamp\":'$(date +%s%3N)'}" >> "${DEBUG_LOG_PATH_CONTAINER:-/dev/null}" || true
        #endregion

        [[ -f "${ORDERER_CA}" ]] || { echo "ORDERER_CA file missing: ${ORDERER_CA}" >&2; exit 31; }

        # Set up peer connection parameters for endorsement.
        # 4-org MAJORITY (3-of-4): include only peers that the host probe
        # (LIVE_ORGS) found running. If a scenario has stopped a peer for a
        # fault demo, excluding it here means:
        #   * 3 live peers -> policy satisfied, invoke succeeds
        #   * 2 live peers -> fabric returns ENDORSEMENT_POLICY_FAILURE
        #     cleanly, instead of the CLI aborting with a DNS error.
        PEER_CONN_PARMS=()
        for live_org in ${LIVE_ORGS:-org1 org2 org3 org4}; do
          case "${live_org}" in
            org1)
              PEER_CONN_PARMS+=(--peerAddresses peer0.cascadiastate.example.com:7051 --tlsRootCertFiles "${PEER0_ORG1_CA}")
              ;;
            org2)
              PEER_CONN_PARMS+=(--peerAddresses peer0.chesapeakecanoe.example.com:9051 --tlsRootCertFiles "${PEER0_ORG2_CA}")
              ;;
            org3)
              PEER_CONN_PARMS+=(--peerAddresses peer0.southhudson.example.com:11051 --tlsRootCertFiles "${PEER0_ORG3_CA}")
              ;;
            org4)
              PEER_CONN_PARMS+=(--peerAddresses peer0.mapleleaf.example.com:13051 --tlsRootCertFiles "${PEER0_ORG4_CA}")
              ;;
          esac
        done

        #region agent log
        echo "{\"sessionId\":\"debug-session\",\"runId\":\"initial\",\"hypothesisId\":\"B\",\"location\":\"lab.sh:invoke_raw:inner\",\"message\":\"About to invoke\",\"data\":{\"channel\":\"${CHANNEL}\",\"cc_name\":\"${CC_NAME}\",\"payload\":\"${PAYLOAD}\",\"peer_conn_parms\":\"${PEER_CONN_PARMS[*]}\"},\"timestamp\":'$(date +%s%3N)'}" >> "${DEBUG_LOG_PATH_CONTAINER:-/dev/null}" || true
        #endregion

        peer chaincode invoke \
          -o orderer.example.com:7050 \
          --ordererTLSHostnameOverride orderer.example.com \
          --tls --cafile "${ORDERER_CA}" \
          "${PEER_CONN_PARMS[@]}" \
          -C "${CHANNEL}" -n "${CC_NAME}" \
          -c "${PAYLOAD}"
      ' 2>&1
  )"
  rc=$?
  # Ensure we always have something to print on failure
  if [[ -z "${out}" && ${rc} -ne 0 ]]; then
    out="(no output from tools exec; likely failed very early)"
  fi
  set -e

  #region agent log
  echo '{"sessionId":"debug-session","runId":"stability","hypothesisId":"INVOKE","location":"lab.sh:invoke_raw","message":"Invoke result captured","data":{"exit_code":'${rc}',"output_length":'${#out}',"has_error":'$(echo "$out" | grep -qiE "error|failed|invalid|ENDORSEMENT_POLICY_FAILURE" && echo "true" || echo "false")',"output_preview":"'${out:0:160}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  # Clean summary output
  if [[ $rc -eq 0 ]]; then
    echo "[hlf] INVOKE: SUCCESS"
    # Fabric often prints a status line; keep output but indent
    echo "$out" | sed 's/\t/  /g' | sed 's/^/[hlf]   /'
    return 0
  fi

  echo "[hlf] INVOKE: FAILED (exit=$rc)" >&2
  echo "$out" | sed 's/\t/  /g' | sed 's/^/[hlf]   /' >&2

  # Additional diagnostics for connection issues
  if echo "$out" | grep -q "context deadline exceeded\|connection refused\|dial unix"; then
    echo "[hlf]   Network diagnostic:" >&2
    echo "[hlf]   - Checking if orderer container is running..." >&2
    if docker ps --format '{{.Names}}' | grep -q '^orderer\.example\.com$'; then
      echo "[hlf]   ✓ Orderer container is running" >&2
    else
      echo "[hlf]   ✗ Orderer container not found" >&2
    fi

    echo "[hlf]   - Checking tools container network..." >&2
    tools_net=$(docker ps --filter "name=^${TOOLS_NAME}$" --format '{{.Networks}}' 2>/dev/null | head -n 1 || echo "unknown")
    echo "[hlf]   - Tools container network: ${tools_net}" >&2

    orderer_net=$(docker ps --filter "name=^orderer.example.com$" --format '{{.Networks}}' 2>/dev/null | head -n 1 || echo "unknown")
    echo "[hlf]   - Orderer container network: ${orderer_net}" >&2

    if [[ "${tools_net}" != "${orderer_net}" ]]; then
      echo "[hlf]   ✗ Network mismatch! Tools and orderer are on different networks." >&2
      echo "[hlf]   Try: ./lab.sh reset && ./lab.sh up" >&2
    fi
  fi

  if invoke_diagnose "$out" >/dev/null; then
    invoke_diagnose "$out" | sed 's/^/[hlf]   /' >&2
  else
    echo "[hlf]   Diagnosis: Unclassified error. Review the output above and orderer/peer logs." >&2
  fi

  return $rc
}

invoke_cmd() {
  # Student-friendly wrapper
  # Usage:
  #   ./lab.sh invoke init-ledger [--org 1|2]
  #   ./lab.sh invoke transfer <assetId> <newOwner> [--org 1|2]
  #   ./lab.sh invoke create <assetId> <color> <size> <owner> <appraisedValue> [--org 1|2]
  #   ./lab.sh invoke --raw '<json>' [--org 1|2]

  validate_all_inputs

  local org_sel="org1"
  local raw=""
  local -a pos=()

  # Parse options anywhere on the command line; collect positionals.
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --org)
        shift
        [[ $# -gt 0 ]] || die "--org requires a value (1|2|org1|org2)"
        org_sel="$1"
        shift
        ;;
      --raw)
        shift
        [[ $# -gt 0 ]] || die "--raw requires a JSON payload"
        raw="$1"
        shift
        ;;
      -h|--help)
        {
          echo "Usage:"
          echo "  ./lab.sh invoke init-ledger [--org 1|2]"
          echo "  ./lab.sh invoke create <assetId> <type> <level> <owner> <value> [fieldOfStudy] [degreeType] [issuer] [--org 1|2]"
          echo "  ./lab.sh invoke transfer <assetId> <newOwner> [--org 1|2]"
          echo "  ./lab.sh invoke update <assetId> <type> <level> <owner> <value> [fieldOfStudy] [degreeType] [--org 1|2]"
          echo "  ./lab.sh invoke delete <assetId> [--org 1|2]"
          echo "  ./lab.sh invoke --raw '<json>' [--org 1|2]"
          echo ""
          echo "Helper examples:"
          echo "  ./lab.sh invoke create diploma-001 credential 4 JohnDoe 2024 \"Computer Science\" \"Master of Science\""
          echo "  ./lab.sh invoke transfer diploma-001 Chesapeake CanoeVerified"
          echo "  ./lab.sh invoke create shipment-001 cargo 10 Cascadia-Exporter 50000"
          echo ""
          echo "Advanced (raw payload) examples:"
          echo "  ./lab.sh invoke --raw '{\"Args\":[\"CreateAsset\",\"diploma-001\",\"credential\",\"4\",\"George Washington\",\"2024\"]}'"
          echo "  ./lab.sh invoke --raw '{\"Args\":[\"TransferAsset\",\"diploma-001\",\"Chesapeake Canoe-Verified\"]}'"
          echo ""
          echo "Peer equivalents:"
          echo "  peer chaincode invoke -C ${CHANNEL} -n ${CC_NAME} -c '{\"Args\":[\"InitLedger\"]}'"
          echo "  peer chaincode invoke -C ${CHANNEL} -n ${CC_NAME} -c '{\"Args\":[\"CreateAsset\",\"diploma-001\",\"credential\",\"4\",\"George Washington\",\"2024\"]}'"
          echo "  peer chaincode invoke -C ${CHANNEL} -n ${CC_NAME} -c '{\"Args\":[\"TransferAsset\",\"diploma-001\",\"Chesapeake Canoe-Verified\"]}'"
          echo "  peer chaincode query  -C ${CHANNEL} -n ${CC_NAME} -c '{\"Args\":[\"ReadAsset\",\"diploma-001\"]}'"
          echo ""
          echo "Defaults:"
          echo "  org: org1"
          echo "  channel: ${CHANNEL}"
          echo "  chaincode: ${CC_NAME}"
        }
        return 0
        ;;
      --)
        shift
        pos+=("$@")
        break
        ;;
      *)
        pos+=("$1")
        shift
        ;;
    esac
  done

  local org_num
  org_num="$(select_org_num "${org_sel}")"

  if [[ -n "${raw}" ]]; then
    invoke_raw "${org_num}" "${raw}"
    return $?
  fi

  (( ${#pos[@]} > 0 )) || die "Missing invoke action. Try: ./lab.sh invoke --help"

  local action="${pos[0]}"
  # Remaining args after action
  local -a args=("${pos[@]:1}")

  local payload=""
  case "${action}" in
    init-ledger)
      payload='{"Args":["InitLedger"]}'
      ;;
    transfer)
      (( ${#args[@]} >= 2 )) || die "Usage: ./lab.sh invoke transfer <assetId> <newOwner> [--org 1|2]"
      is_safe_token "${args[0]}" || die "Unsafe assetId: '${args[0]}'"
      is_safe_token "${args[1]}" || die "Unsafe newOwner: '${args[1]}'"
      payload="{\"Args\":[\"TransferAsset\",\"${args[0]}\",\"${args[1]}\"]}"
      ;;
    create)
      (( ${#args[@]} >= 5 )) || die "Usage: ./lab.sh invoke create <assetId> <type> <level> <owner> <value> [fieldOfStudy] [degreeType] [issuer] [--org 1|2]"
      is_safe_token "${args[0]}" || die "Unsafe assetId: '${args[0]}'"
      is_safe_token "${args[1]}" || die "Unsafe type: '${args[1]}'"
      is_safe_token "${args[2]}" || die "Unsafe level: '${args[2]}'"
      is_safe_token "${args[3]}" || die "Unsafe owner: '${args[3]}'"
      is_safe_token "${args[4]}" || die "Unsafe value: '${args[4]}'"
      # CreateAsset is declared with 8 positional args (id, type, level,
      # owner, value, fieldOfStudy, degreeType, issuer). fabric-contract-api
      # enforces exact arity, so we always pad trailing slots with empty
      # strings when the caller omits them.
      local fos="" dtype="" iss=""
      if (( ${#args[@]} >= 6 )); then
        [[ "${args[5]}" != *\"* && "${args[5]}" != *\\* ]] || die "Unsafe fieldOfStudy: '${args[5]}'"
        fos="${args[5]}"
      fi
      if (( ${#args[@]} >= 7 )); then
        [[ "${args[6]}" != *\"* && "${args[6]}" != *\\* ]] || die "Unsafe degreeType: '${args[6]}'"
        dtype="${args[6]}"
      fi
      if (( ${#args[@]} >= 8 )); then
        [[ "${args[7]}" != *\"* && "${args[7]}" != *\\* ]] || die "Unsafe issuer: '${args[7]}'"
        iss="${args[7]}"
      fi
      payload="{\"Args\":[\"CreateAsset\",\"${args[0]}\",\"${args[1]}\",\"${args[2]}\",\"${args[3]}\",\"${args[4]}\",\"${fos}\",\"${dtype}\",\"${iss}\"]}"
      ;;
    update)
      (( ${#args[@]} >= 5 )) || die "Usage: ./lab.sh invoke update <assetId> <type> <level> <owner> <value> [fieldOfStudy] [degreeType] [--org 1|2]"
      is_safe_token "${args[0]}" || die "Unsafe assetId: '${args[0]}'"
      is_safe_token "${args[1]}" || die "Unsafe type: '${args[1]}'"
      is_safe_token "${args[2]}" || die "Unsafe level: '${args[2]}'"
      is_safe_token "${args[3]}" || die "Unsafe owner: '${args[3]}'"
      is_safe_token "${args[4]}" || die "Unsafe value: '${args[4]}'"
      # UpdateAsset is declared with 7 positional args; pad trailing slots
      # with empty strings so fabric-contract-api's strict arity check
      # accepts calls that omit fieldOfStudy/degreeType.
      local u_fos="" u_dtype=""
      if (( ${#args[@]} >= 6 )); then
        [[ "${args[5]}" != *\"* && "${args[5]}" != *\\* ]] || die "Unsafe fieldOfStudy: '${args[5]}'"
        u_fos="${args[5]}"
      fi
      if (( ${#args[@]} >= 7 )); then
        [[ "${args[6]}" != *\"* && "${args[6]}" != *\\* ]] || die "Unsafe degreeType: '${args[6]}'"
        u_dtype="${args[6]}"
      fi
      payload="{\"Args\":[\"UpdateAsset\",\"${args[0]}\",\"${args[1]}\",\"${args[2]}\",\"${args[3]}\",\"${args[4]}\",\"${u_fos}\",\"${u_dtype}\"]}"
      ;;
    delete)
      (( ${#args[@]} >= 1 )) || die "Usage: ./lab.sh invoke delete <assetId> [--org 1|2]"
      is_safe_token "${args[0]}" || die "Unsafe assetId: '${args[0]}'"
      payload="{\"Args\":[\"DeleteAsset\",\"${args[0]}\"]}"
      ;;
    help|-h|--help)
      invoke_cmd --help
      return 0
      ;;
    *)
      die "Unknown action '${action}'. Try: ./lab.sh invoke --help"
      ;;
  esac

  #region agent log
  echo '{"sessionId":"debug-session","runId":"stability","hypothesisId":"INVOKE","location":"lab.sh:invoke_cmd","message":"Prepared invoke payload","data":{"action":"'"${action}"'","org_num":"'"${org_num}"'","payload_preview":"'"${payload:0:120}"'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  invoke_raw "${org_num}" "${payload}"
  local invoke_rc=$?

  #region agent log
  echo '{"sessionId":"debug-session","runId":"stability","hypothesisId":"INVOKE","location":"lab.sh:invoke_cmd","message":"Invoke completed","data":{"action":"'"${action}"'","org_num":"'"${org_num}"'","exit_code":'${invoke_rc}'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  return "${invoke_rc}"
}

query_cmd() {
  # Student-friendly query wrapper
  # Usage:
  #   ./lab.sh query all [--org 1|2]
  #   ./lab.sh query <assetId> [--org 1|2]
  #   ./lab.sh query price <assetId> [--org 1|2]

  validate_all_inputs

  local org_sel="org1"
  local -a pos=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --org)
        shift
        [[ $# -gt 0 ]] || die "--org requires a value (1|2|org1|org2)"
        org_sel="$1"
        shift
        ;;
      -h|--help)
        {
          echo "Usage:"
          echo "  ./lab.sh query all [--org 1|2]"
          echo "  ./lab.sh query <assetId> [--org 1|2]"
        }
        return 0
        ;;
      --)
        shift
        pos+=("$@")
        break
        ;;
      *)
        pos+=("$1")
        shift
        ;;
    esac
  done

  (( ${#pos[@]} > 0 )) || die "Missing query target. Try: ./lab.sh query --help"

  local org_num
  org_num="$(select_org_num "${org_sel}")"

  local payload=""
  case "${pos[0]}" in
    all)
      payload='{"Args":["GetAllAssets"]}'
      ;;
    *)
      is_safe_token "${pos[0]}" || die "Unsafe assetId: '${pos[0]}'"
      payload="{\"Args\":[\"ReadAsset\",\"${pos[0]}\"]}"
      ;;
  esac

  local out rc
  set +e
  out="$(tools_exec_noninteractive "${org_num}" "peer chaincode query -C ${CHANNEL} -n ${CC_NAME} -c '${payload}'" 2>&1)"
  rc=$?
  set -e
  echo "$out" | sed 's/\t/  /g'
  return $rc
}

validate_test_network_layout() {
  [[ -x "${TEST_NETWORK}/network.sh" ]] || die "test-network not found. Expected: ${TEST_NETWORK}/network.sh. Run: ./lab.sh bootstrap"

  local -a missing=()
  local -a required=(
    "${TEST_NETWORK}/scripts/envVar.sh"
    "${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh"
    "${TEST_NETWORK}/organizations/ccp-generate.sh"
  )

  local f
  for f in "${required[@]}"; do
    [[ -f "$f" ]] || missing+=("$f")
  done

  if (( ${#missing[@]} > 0 )); then
    info "Detected incomplete or incompatible fabric-samples/test-network layout."
    for f in "${missing[@]}"; do
      info "Missing: $f"
    done
    die "Re-bootstrap required. Remove '${FABRIC_SAMPLES_PATH}' and run: ./lab.sh bootstrap (or set HLF_BOOTSTRAP_FORCE=1)."
  fi
}

apply_chaincode_overrides() {
  local override_src="${CHAINCODE_OVERRIDE_PATH}/lib/assetTransfer.js"
  local target_dst="${FABRIC_SAMPLES_PATH}/asset-transfer-basic/chaincode-javascript/lib/assetTransfer.js"

  if [[ -f "${override_src}" ]]; then
    info "Applying chaincode override: ${override_src} -> ${target_dst}"
    mkdir -p "$(dirname "${target_dst}")"
    cp -f "${override_src}" "${target_dst}"
  else
    info "No chaincode override found at ${override_src} (skipping)"
  fi

  local schools_json="${HERE}/managed_runtime/schools.json"
  local mapping_dst="${FABRIC_SAMPLES_PATH}/asset-transfer-basic/chaincode-javascript/lib/schoolMapping.json"
  if [[ -f "${schools_json}" ]]; then
    info "Generating schoolMapping.json from schools.json"
    python3 - "${schools_json}" "${mapping_dst}" <<'PYMAP'
import json, sys, re
schools_path, out_path = sys.argv[1], sys.argv[2]
consortium = [
    {"msp": "Org1MSP", "school": "Cascadia State", "prefixes": ["cascadia"]},
    {"msp": "Org2MSP", "school": "Chesapeake Canoe University", "prefixes": ["chesapeake", "canoe"]},
    {"msp": "Org3MSP", "school": "South Hudson Institute", "prefixes": ["south hudson", "southhudson"]},
    {"msp": "Org4MSP", "school": "Maple Leaf Academy", "prefixes": ["maple leaf", "mapleleaf"]},
]
with open(schools_path) as f:
    schools = json.load(f)
mapping = list(consortium)
for sid in sorted(schools):
    entry = schools[sid]
    msp = entry.get("msp_id", "")
    name = entry.get("default_school_name", "")
    if not msp or not name:
        continue
    prefix = re.sub(r"\s+(university|college|institute|polytechnic|academy)$", "", name.lower()).strip()
    mapping.append({"msp": msp, "school": name, "prefixes": [prefix]})
with open(out_path, "w") as f:
    json.dump(mapping, f, indent=2)
PYMAP
  fi
}

prepare_build_assets() {
  local need_samples_checkout=0
  local fabric_dir

  fabric_dir="$(dirname "${FABRIC_SAMPLES_PATH}")"

  if [[ ! -d "${FABRIC_SAMPLES_PATH}" ]]; then
    info "fabric-samples assets not found; restoring them before build prep"
    need_samples_checkout=1
  elif [[ \
    ! -x "${TEST_NETWORK}/network.sh" || \
    ! -f "${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh" || \
    ! -f "${TEST_NETWORK}/organizations/ccp-generate.sh" || \
    ! -x "${FABRIC_SAMPLES_PATH}/bin/peer" || \
    ! -x "${FABRIC_SAMPLES_PATH}/bin/cryptogen" || \
    ! -f "${FABRIC_SAMPLES_PATH}/config/core.yaml" \
  ]]; then
    info "Vendored fabric-samples assets appear incomplete; restoring them before build prep"
    need_samples_checkout=1
  fi

  if [[ "${need_samples_checkout}" == "1" ]]; then
    prepare_fabric_samples_repo "${fabric_dir}"
  fi

  if [[ -d "${FABRIC_SAMPLES_PATH}" ]] && find "${FABRIC_SAMPLES_PATH}" -maxdepth 0 ! -writable -print -quit | grep -q .; then
    info "Fixing ownership on fabric-samples tree (was root-owned)"
    if sudo -n true 2>/dev/null; then
      sudo chown -R "$(id -u):$(id -g)" "${FABRIC_SAMPLES_PATH}"
    else
      docker run --rm -v "${FABRIC_SAMPLES_PATH}:/fix" alpine chown -R "$(id -u):$(id -g)" /fix
    fi
  fi

  validate_test_network_layout
  apply_chaincode_overrides
  info "Build assets prepared."
}

render_managed_runtime_template() {
  local template_path="$1"
  local output_path="$2"
  python3 - <<'PY' "${template_path}" "${output_path}" "${IMAGE_TAG}" "${CA_IMAGE_TAG}" "${PLATFORM}"
from pathlib import Path
import sys

template_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
image_tag = sys.argv[3]
ca_image_tag = sys.argv[4]
platform = sys.argv[5]

text = template_path.read_text()
text = text.replace("__IMAGE_TAG__", image_tag)
text = text.replace("__CA_IMAGE_TAG__", ca_image_tag)
text = text.replace("__PLATFORM__", platform)
output_path.write_text(text)
PY
}

patch_managed_test_network() {
  local register_enroll="${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh"
  local compose_ca="${TEST_NETWORK}/compose/compose-ca.yaml"
  local compose_test="${TEST_NETWORK}/compose/compose-test-net.yaml"
  local compose_couch="${TEST_NETWORK}/compose/compose-couch.yaml"
  local network_script="${TEST_NETWORK}/network.sh"
  local env_script="${TEST_NETWORK}/scripts/envVar.sh"
  local orderer_script="${TEST_NETWORK}/scripts/orderer.sh"
  local config_update_script="${TEST_NETWORK}/scripts/configUpdate.sh"
  local set_anchor_script="${TEST_NETWORK}/scripts/setAnchorPeer.sh"
  local ccutils_script="${TEST_NETWORK}/scripts/ccutils.sh"
  local managed_runtime_dir="${HERE}/managed_runtime"
  [[ -f "${register_enroll}" ]] || return 0

  info "Patching staged Fabric CA enroll script for managed-container networking"
  sed -i \
    -e 's#@localhost:7054#@ca_org1:7054#g' \
    -e 's@cacerts/localhost-7054-ca-org1.pem@cacerts/ca_org1-7054-ca-org1.pem@g' \
    -e 's#@localhost:8054#@ca_org2:8054#g' \
    -e 's@cacerts/localhost-8054-ca-org2.pem@cacerts/ca_org2-8054-ca-org2.pem@g' \
    -e 's#@localhost:9054#@ca_orderer:9054#g' \
    -e 's@cacerts/localhost-9054-ca-orderer.pem@cacerts/ca_orderer-9054-ca-orderer.pem@g' \
    "${register_enroll}"

  if [[ -f "${compose_ca}" ]]; then
    info "Rendering managed Fabric CA compose file from repo template"
    render_managed_runtime_template "${managed_runtime_dir}/compose-ca.yaml.tmpl" "${compose_ca}"
  fi

  if [[ -f "${compose_test}" ]]; then
    info "Rendering managed Fabric test-net compose file from repo template"
    render_managed_runtime_template "${managed_runtime_dir}/compose-test-net.yaml.tmpl" "${compose_test}"
  fi

  if [[ -f "${compose_couch}" || "${USE_COUCHDB}" == "1" ]]; then
    info "Rendering managed Fabric CouchDB compose file from repo template"
    render_managed_runtime_template "${managed_runtime_dir}/compose-couch.yaml.tmpl" "${compose_couch}"
  fi

  if [[ -f "${network_script}" ]]; then
    info "Patching staged Fabric network readiness probe for managed-container networking"
    sed -i \
      -e 's#@localhost:7054#@ca_org1:7054#g' \
      "${network_script}"
  fi

  if [[ -f "${env_script}" ]]; then
    sed -i \
      -e 's#CORE_PEER_ADDRESS=localhost:7051#CORE_PEER_ADDRESS=peer0.cascadiastate.example.com:7051#g' \
      -e 's#CORE_PEER_ADDRESS=localhost:9051#CORE_PEER_ADDRESS=peer0.chesapeakecanoe.example.com:9051#g' \
      "${env_script}"
  fi

  if [[ -f "${orderer_script}" ]]; then
    sed -i \
      -e 's#^export PATH=.*#export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin#g' \
      -e 's#-o localhost:7053#-o orderer.example.com:7053#g' \
      "${orderer_script}"
  fi

  if [[ -f "${config_update_script}" ]]; then
    sed -i \
      -e 's#-o localhost:7050#-o orderer.example.com:7050#g' \
      "${config_update_script}"
  fi

  if [[ -f "${set_anchor_script}" ]]; then
    sed -i \
      -e 's#-o localhost:7050#-o orderer.example.com:7050#g' \
      -e 's#peer0\.org3\.example\.com#peer0.southhudson.example.com#g' \
      "${set_anchor_script}"
    # Add Org4 branch if missing (upstream only knows Org1-3).
    if ! grep -q 'peer0.mapleleaf.example.com' "${set_anchor_script}"; then
      sed -i \
        -e '/HOST="peer0.southhudson.example.com"/,/PORT=11051/{
              /PORT=11051/a\
  elif [ $ORG -eq 4 ]; then\
    HOST="peer0.mapleleaf.example.com"\
    PORT=13051
            }' \
        "${set_anchor_script}"
    fi
    # Add Org5 branch if missing (Meridian read-only member still needs an
    # anchor peer entry so gossip membership advertises it on the channel).
    if ! grep -q 'peer0.meridian.example.com' "${set_anchor_script}"; then
      sed -i \
        -e '/HOST="peer0.mapleleaf.example.com"/,/PORT=13051/{
              /PORT=13051/a\
  elif [ $ORG -eq 5 ]; then\
    HOST="peer0.meridian.example.com"\
    PORT=15051
            }' \
        "${set_anchor_script}"
    fi
  fi

  if [[ -f "${ccutils_script}" ]]; then
    sed -i \
      -e 's#-o localhost:7050#-o orderer.example.com:7050#g' \
      -e 's#--peerAddresses localhost:7051#--peerAddresses peer0.cascadiastate.example.com:7051#g' \
      -e 's#--peerAddresses localhost:9051#--peerAddresses peer0.chesapeakecanoe.example.com:9051#g' \
      "${ccutils_script}"
  fi

  # Rename default fabric-samples org domains to lab-specific domains so that
  # container names, certificates, and directory paths use meaningful names
  # that students can follow.  This must run AFTER all other patches so it
  # catches every remaining reference.
  info "Renaming fabric-samples org domains to lab-specific domains"
  local domain_files=(
    "${register_enroll}"
    "${env_script}"
    "${network_script}"
    "${ccutils_script}"
    "${orderer_script}"
    "${config_update_script}"
    "${set_anchor_script}"
  )
  local ccp_gen="${TEST_NETWORK}/organizations/ccp-generate.sh"
  [[ -f "${ccp_gen}" ]] && domain_files+=("${ccp_gen}")
  local create_ch="${TEST_NETWORK}/scripts/createChannel.sh"
  [[ -f "${create_ch}" ]] && domain_files+=("${create_ch}")
  local configtx_yaml="${TEST_NETWORK}/configtx/configtx.yaml"
  [[ -f "${configtx_yaml}" ]] && domain_files+=("${configtx_yaml}")
  # Upstream compose files not covered by managed templates
  for extra in \
    "${TEST_NETWORK}/compose/compose-bft-test-net.yaml" \
    "${TEST_NETWORK}/compose/docker/docker-compose-test-net.yaml" \
    "${TEST_NETWORK}/compose/docker/docker-compose-couch.yaml" \
    "${TEST_NETWORK}/compose/podman/podman-compose-test-net.yaml" \
  ; do
    [[ -f "${extra}" ]] && domain_files+=("${extra}")
  done
  for f in "${domain_files[@]}"; do
    [[ -f "$f" ]] || continue
    sed -i \
      -e 's/org1\.example\.com/cascadiastate.example.com/g' \
      -e 's/org2\.example\.com/chesapeakecanoe.example.com/g' \
      "$f"
  done

  # ---- 4-org extension ------------------------------------------------------
  # Stage Org3 (South Hudson Institute of Technology), Org4 (Maple Leaf
  # Academy), and Org5 (Meridian Industries — read-only channel member)
  # alongside Cascadia State and Chesapeake Canoe University so cryptogen,
  # configtxgen, and docker compose all see a 5-org network.
  info "Staging Org3/Org4/Org5 crypto-config files"
  cp -f "${managed_runtime_dir}/crypto-config-org3.yaml" \
        "${TEST_NETWORK}/organizations/cryptogen/crypto-config-org3.yaml"
  cp -f "${managed_runtime_dir}/crypto-config-org4.yaml" \
        "${TEST_NETWORK}/organizations/cryptogen/crypto-config-org4.yaml"
  cp -f "${managed_runtime_dir}/crypto-config-org5.yaml" \
        "${TEST_NETWORK}/organizations/cryptogen/crypto-config-org5.yaml"

  # ---- Student overlay (Phase 7 hybrid) -------------------------------------
  local hlf_student_count
  hlf_student_count="${HLF_STUDENT_COUNT:-${MAX_STUDENT_CAPACITY:-20}}"

  # Regenerate student overlay artifacts (configtx-4org-students.yaml,
  # compose-students.yaml, crypto-config-studentNN.yaml) so the
  # 4-org channel genesis includes Student01..StudentNN as channel members and
  # the lane manager has a compose file pointing at student peer
  # services. Students are NOT endorsers — the channel-level
  # Application.Endorsement policy remains OutOf(3, Org1..4).
  info "Regenerating student overlay configs via managed_runtime/generate_student_overlay.py"
  python3 "${managed_runtime_dir}/generate_student_overlay.py" --out "${managed_runtime_dir}" >/dev/null

  info "Staging ${hlf_student_count} x crypto-config-studentNN.yaml"
  for _sn in $(seq -w 01 "${hlf_student_count}"); do
    cp -f "${managed_runtime_dir}/crypto-config-student${_sn}.yaml" \
          "${TEST_NETWORK}/organizations/cryptogen/crypto-config-student${_sn}.yaml"
  done

  info "Staging compose-students.yaml (profile-gated, external fabric_test network)"
  mkdir -p "${TEST_NETWORK}/compose"
  cp -f "${managed_runtime_dir}/compose-students.yaml" \
        "${TEST_NETWORK}/compose/compose-students.yaml"

  info "Installing 4-org+students configtx.yaml profile"
  cp -f "${managed_runtime_dir}/configtx-4org-students.yaml" \
        "${TEST_NETWORK}/configtx/configtx.yaml"

  # Patch network.sh createOrgs() so cryptogen also generates Org3/Org4/Org5
  # material.  We inject three new cryptogen invocations right before the
  # "Creating Orderer Org Identities" block, mirroring the Org1/Org2 calls.
  if [[ -f "${network_script}" ]] \
     && ! grep -q "crypto-config-org3.yaml" "${network_script}"; then
    info "Patching network.sh to generate Org3/Org4/Org5 crypto material"
    python3 - "${network_script}" <<'PY'
import sys, pathlib
path = pathlib.Path(sys.argv[1])
text = path.read_text()
marker = 'infoln "Creating Orderer Org Identities"'
insert = (
    'infoln "Creating Org3 Identities"\n\n'
    '    set -x\n'
    '    cryptogen generate --config=./organizations/cryptogen/crypto-config-org3.yaml --output="organizations"\n'
    '    res=$?\n'
    '    { set +x; } 2>/dev/null\n'
    '    if [ $res -ne 0 ]; then\n'
    '      fatalln "Failed to generate certificates..."\n'
    '    fi\n\n'
    '    infoln "Creating Org4 Identities"\n\n'
    '    set -x\n'
    '    cryptogen generate --config=./organizations/cryptogen/crypto-config-org4.yaml --output="organizations"\n'
    '    res=$?\n'
    '    { set +x; } 2>/dev/null\n'
    '    if [ $res -ne 0 ]; then\n'
    '      fatalln "Failed to generate certificates..."\n'
    '    fi\n\n'
    '    infoln "Creating Org5 Identities (Meridian — read-only channel member)"\n\n'
    '    set -x\n'
    '    cryptogen generate --config=./organizations/cryptogen/crypto-config-org5.yaml --output="organizations"\n'
    '    res=$?\n'
    '    { set +x; } 2>/dev/null\n'
    '    if [ $res -ne 0 ]; then\n'
    '      fatalln "Failed to generate certificates..."\n'
    '    fi\n\n'
    '    '
)
if marker not in text:
    print("marker not found; skipping", file=sys.stderr)
    sys.exit(0)
text = text.replace(marker, insert + marker, 1)
path.write_text(text)
PY
  fi

  # Patch envVar.sh so setGlobals knows about Org3 (South Hudson), Org4
  # (Maple Leaf), and Org5 (Meridian, read-only channel member) branches,
  # each with correct domain/port. Also export PEER0_ORG3_CA /
  # PEER0_ORG4_CA / PEER0_ORG5_CA with lab-specific domains.
  if [[ -f "${env_script}" ]] \
     && ! grep -q "meridian.example.com" "${env_script}"; then
    info "Patching envVar.sh for 5-org (Org3 South Hudson, Org4 Maple Leaf, Org5 Meridian read-only)"
    python3 - "${env_script}" <<'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1])
t = p.read_text()

# Replace the stale PEER0_ORG3_CA export (org3.example.com) with southhudson,
# and insert PEER0_ORG4_CA / PEER0_ORG5_CA on the following lines.
t = re.sub(
    r'export PEER0_ORG3_CA=.*\n',
    ('export PEER0_ORG3_CA=${TEST_NETWORK_HOME}/organizations/peerOrganizations/'
     'southhudson.example.com/tlsca/tlsca.southhudson.example.com-cert.pem\n'
     'export PEER0_ORG4_CA=${TEST_NETWORK_HOME}/organizations/peerOrganizations/'
     'mapleleaf.example.com/tlsca/tlsca.mapleleaf.example.com-cert.pem\n'
     'export PEER0_ORG5_CA=${TEST_NETWORK_HOME}/organizations/peerOrganizations/'
     'meridian.example.com/tlsca/tlsca.meridian.example.com-cert.pem\n'),
    t, count=1,
)

# Rewrite the Org3 branch (wrong domain upstream) and append Org4 + Org5 branches.
old_org3_block = (
    '  elif [ $USING_ORG -eq 3 ]; then\n'
    '    export CORE_PEER_LOCALMSPID=Org3MSP\n'
    '    export CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_ORG3_CA\n'
    '    export CORE_PEER_MSPCONFIGPATH=${TEST_NETWORK_HOME}/organizations/peerOrganizations/org3.example.com/users/Admin@org3.example.com/msp\n'
    '    export CORE_PEER_ADDRESS=localhost:11051\n'
)
new_orgs_block = (
    '  elif [ $USING_ORG -eq 3 ]; then\n'
    '    export CORE_PEER_LOCALMSPID=Org3MSP\n'
    '    export CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_ORG3_CA\n'
    '    export CORE_PEER_MSPCONFIGPATH=${TEST_NETWORK_HOME}/organizations/peerOrganizations/southhudson.example.com/users/Admin@southhudson.example.com/msp\n'
    '    export CORE_PEER_ADDRESS=peer0.southhudson.example.com:11051\n'
    '  elif [ $USING_ORG -eq 4 ]; then\n'
    '    export CORE_PEER_LOCALMSPID=Org4MSP\n'
    '    export CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_ORG4_CA\n'
    '    export CORE_PEER_MSPCONFIGPATH=${TEST_NETWORK_HOME}/organizations/peerOrganizations/mapleleaf.example.com/users/Admin@mapleleaf.example.com/msp\n'
    '    export CORE_PEER_ADDRESS=peer0.mapleleaf.example.com:13051\n'
    '  elif [ $USING_ORG -eq 5 ]; then\n'
    '    export CORE_PEER_LOCALMSPID=Org5MSP\n'
    '    export CORE_PEER_TLS_ROOTCERT_FILE=$PEER0_ORG5_CA\n'
    '    export CORE_PEER_MSPCONFIGPATH=${TEST_NETWORK_HOME}/organizations/peerOrganizations/meridian.example.com/users/Admin@meridian.example.com/msp\n'
    '    export CORE_PEER_ADDRESS=peer0.meridian.example.com:15051\n'
)
if old_org3_block not in t:
    print("org3 block not found; aborting patch", file=sys.stderr)
    sys.exit(1)
t = t.replace(old_org3_block, new_orgs_block, 1)
p.write_text(t)
PY
  fi

  # Patch createChannel.sh so all 5 peers join the channel and all 5 orgs set
  # their anchor peer. Meridian (Org5) is a read-only channel member but must
  # still join the channel + set an anchor peer so its gossip membership is
  # visible and its peer can receive blocks. Idempotent.
  if [[ -f "${create_ch}" ]] \
     && ! grep -q "joinChannel 5" "${create_ch}"; then
    info "Patching createChannel.sh to join Org3/Org4/Org5 peers + set anchor peers"
    python3 - "${create_ch}" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
t = p.read_text()
old = (
    'infoln "Joining org2 peer to the channel..."\n'
    'joinChannel 2\n'
)
new = (
    'infoln "Joining org2 peer to the channel..."\n'
    'joinChannel 2\n'
    'infoln "Joining org3 peer to the channel..."\n'
    'joinChannel 3\n'
    'infoln "Joining org4 peer to the channel..."\n'
    'joinChannel 4\n'
    'infoln "Joining org5 peer to the channel (Meridian — read-only)..."\n'
    'joinChannel 5\n'
)
if old in t:
    t = t.replace(old, new, 1)

old2 = (
    'infoln "Setting anchor peer for org2..."\n'
    'setAnchorPeer 2\n'
)
new2 = (
    'infoln "Setting anchor peer for org2..."\n'
    'setAnchorPeer 2\n'
    'infoln "Setting anchor peer for org3..."\n'
    'setAnchorPeer 3\n'
    'infoln "Setting anchor peer for org4..."\n'
    'setAnchorPeer 4\n'
    'infoln "Setting anchor peer for org5..."\n'
    'setAnchorPeer 5\n'
)
if old2 in t:
    t = t.replace(old2, new2, 1)
p.write_text(t)
PY
  fi
}

prepare_ttyd_build_context() {
  local ctx_dir="$1"
  mkdir -p "${ctx_dir}/scripts"
  cp -f "${HERE}/Dockerfile.ttyd" "${ctx_dir}/Dockerfile.ttyd"
  cp -f "${HERE}/scripts/hlf_ttyd_wrapper.sh" "${ctx_dir}/scripts/hlf_ttyd_wrapper.sh"
  cp -f "${HERE}/scripts/hlf_peer_shell.sh" "${ctx_dir}/scripts/hlf_peer_shell.sh"
  cp -f "${HERE}/scripts/hlf_cli_helpers.sh" "${ctx_dir}/scripts/hlf_cli_helpers.sh"
  local zellij_config="${HERE}/../zellij-config.kdl"
  if [[ -f "${zellij_config}" ]]; then
    cp -f "${zellij_config}" "${ctx_dir}/zellij-config.kdl"
  fi
}

prepare_chaincode_build_context() {
  local ctx_dir="$1"
  local chaincode_src="${HERE}/runtime/fabric-samples/asset-transfer-basic/chaincode-javascript"

  [[ -d "${chaincode_src}" ]] || die "Chaincode source not found at ${chaincode_src}. Run ./lab.sh bootstrap first."

  mkdir -p "${ctx_dir}/runtime/fabric-samples/asset-transfer-basic/chaincode-javascript"
  cp -f "${HERE}/Dockerfile.chaincode" "${ctx_dir}/Dockerfile.chaincode"
  cp -a "${chaincode_src}/." "${ctx_dir}/runtime/fabric-samples/asset-transfer-basic/chaincode-javascript/"
}

docker_build_network_available() {
  local candidate="${1:-}"
  [[ -n "${candidate}" ]] || return 1
  case "${candidate}" in
    default|bridge|host|none) return 0 ;;
  esac
  docker network inspect "${candidate}" >/dev/null 2>&1
}

resolve_docker_build_network() {
  local configured="${DOCKER_BUILD_NETWORK:-}"
  if docker_build_network_available "${configured}"; then
    echo "${configured}"
    return 0
  fi
  if [[ -n "${configured}" ]]; then
    info "Configured DOCKER_BUILD_NETWORK '${configured}' is unavailable; falling back."
  fi
  if docker_build_network_available "bridge"; then
    echo "bridge"
    return 0
  fi
  echo "default"
}

build_ttyd_images() {
  local _needed=()
  docker image inspect hlf-peer-ttyd:latest    >/dev/null 2>&1 || _needed+=(hlf-peer-ttyd)
  docker image inspect hlf-orderer-ttyd:latest  >/dev/null 2>&1 || _needed+=(hlf-orderer-ttyd)
  docker image inspect chaincode-basic:latest   >/dev/null 2>&1 || _needed+=(chaincode-basic)

  if [[ ${#_needed[@]} -eq 0 ]]; then
    info "HLF helper images already cached — skipping build."
    return 0
  fi

  info "Building ttyd-enabled Fabric images (${PLATFORM}, Fabric ${IMAGE_TAG})..."
  info "  Missing: ${_needed[*]}"
  local build_network=""
  local ttyd_ctx=""
  local chaincode_ctx=""
  local rc=0

  build_network="$(resolve_docker_build_network)"
  info "Using Docker build network '${build_network}' for inner image builds..."

  ttyd_ctx="$(mktemp -d "${TMPDIR:-/tmp}/hlf-ttyd-build.XXXXXX")"
  chaincode_ctx="$(mktemp -d "${TMPDIR:-/tmp}/hlf-chaincode-build.XXXXXX")"

  {
    prepare_ttyd_build_context "${ttyd_ctx}"
    prepare_chaincode_build_context "${chaincode_ctx}"
    docker build --network "${build_network}" --platform "${PLATFORM}" \
      --build-arg FABRIC_VERSION="${IMAGE_TAG}" \
      --build-arg TTYD_ARCH="${TTYD_ARCH}" \
      -t hlf-peer-ttyd:latest \
      -f "${ttyd_ctx}/Dockerfile.ttyd" "${ttyd_ctx}"
    docker build --network "${build_network}" --platform "${PLATFORM}" \
      --build-arg FABRIC_VERSION="${IMAGE_TAG}" \
      --build-arg FABRIC_ROLE=orderer \
      --build-arg TTYD_ARCH="${TTYD_ARCH}" \
      -t hlf-orderer-ttyd:latest \
      -f "${ttyd_ctx}/Dockerfile.ttyd" "${ttyd_ctx}"
    docker build --network "${build_network}" --platform "${PLATFORM}" \
      -t chaincode-basic:latest \
      -f "${chaincode_ctx}/Dockerfile.chaincode" "${chaincode_ctx}"
  } || rc=$?

  rm -rf "${ttyd_ctx}" "${chaincode_ctx}"
  return "${rc}"
}

runtime_compose() {
  (
    cd "${HOST_TEST_NETWORK}"
    export DOCKER_SOCK="${DOCKER_SOCK:-/var/run/docker.sock}"
    docker compose "$@"
  )
}

start_runtime_ca() {
  info "Starting Fabric CA containers..."
  runtime_compose -f compose/compose-ca.yaml up -d
}

generate_crypto_material_via_containers() {
  info "Generating org and orderer materials via Fabric CA container..."
  docker run --rm --platform ${TOOLS_PLATFORM} \
    --network fabric_test \
    -v "${HOST_FABRIC_SAMPLES_PATH}:/fabric-samples" \
    -w /fabric-samples/test-network \
    "hyperledger/fabric-ca:${CA_IMAGE_TAG}" \
    bash -lc '
      set -euo pipefail
      . scripts/utils.sh
      . organizations/fabric-ca/registerEnroll.sh
      while [ ! -f "organizations/fabric-ca/org1/ca-cert.pem" ]; do sleep 1; done
      export FABRIC_CA_CLIENT_HOME=${PWD}/organizations/peerOrganizations/cascadiastate.example.com/
      COUNTER=0
      rc=1
      while [ $rc -ne 0 ] && [ $COUNTER -lt 10 ]; do
        sleep 1
        if fabric-ca-client getcainfo -u https://admin:adminpw@ca_org1:7054 --caname ca-org1 --tls.certfiles "${PWD}/organizations/fabric-ca/org1/ca-cert.pem" >/dev/null 2>&1; then
          rc=0
          break
        fi
        COUNTER=$((COUNTER + 1))
      done
      [ $rc -eq 0 ]
      createOrg1
      createOrg2
      createOrderer
      ./organizations/ccp-generate.sh
    '

  local hlf_student_count
  hlf_student_count="${HLF_STUDENT_COUNT:-${MAX_STUDENT_CAPACITY:-20}}"

  info "Generating Org3/Org4/Org5 + Student01..Student${hlf_student_count} crypto material via cryptogen (fabric-tools)..."
  docker run --rm --platform ${TOOLS_PLATFORM} \
    --network fabric_test \
    -v "${HOST_FABRIC_SAMPLES_PATH}:/fabric-samples" \
    -w /fabric-samples/test-network \
    "hyperledger/fabric-tools:${IMAGE_TAG}" \
    bash -lc '
      set -euo pipefail
      which cryptogen >/dev/null
      cryptogen generate --config=./organizations/cryptogen/crypto-config-org3.yaml --output="organizations"
      cryptogen generate --config=./organizations/cryptogen/crypto-config-org4.yaml --output="organizations"
      cryptogen generate --config=./organizations/cryptogen/crypto-config-org5.yaml --output="organizations"
      for n in $(seq -w 01 '"${hlf_student_count}"'); do
        rm -rf "./organizations/peerOrganizations/student${n}.example.com"
        cryptogen generate --config=./organizations/cryptogen/crypto-config-student${n}.yaml --output="organizations"
      done
    '
}

start_runtime_network_containers() {
  info "Starting Fabric orderer, peers, and optional CouchDB..."
  local -a compose_args=(-f compose/compose-test-net.yaml)
  if [[ "${USE_COUCHDB}" == "1" ]]; then
    compose_args+=(-f compose/compose-couch.yaml)
  fi
  runtime_compose "${compose_args[@]}" up -d
}

create_channel_via_tools_container() {
  info "Creating channel and joining peers via Fabric tools container..."
  docker run --rm --platform ${TOOLS_PLATFORM} \
    --network fabric_test \
    -v "${HOST_FABRIC_SAMPLES_PATH}:/fabric-samples" \
    -w /fabric-samples/test-network \
    "hyperledger/fabric-tools:${IMAGE_TAG}" \
    bash -lc '
      set -euo pipefail
      ./scripts/createChannel.sh '"${CHANNEL}"' 3 5 false 0
    '
}

ensure_managed_control_plane_networking() {
  local network_name="fabric_test"
  local network_label="test"
  local self_name

  self_name="$(hostname)"
  if docker network inspect "${network_name}" >/dev/null 2>&1; then
    if ! docker network inspect "${network_name}" --format '{{ index .Labels "com.docker.compose.network" }}' 2>/dev/null | grep -qx "${network_label}"; then
      docker network rm "${network_name}" >/dev/null 2>&1 || true
    fi
  fi

  docker network inspect "${network_name}" >/dev/null 2>&1 || \
    docker network create \
      --label "com.docker.compose.network=${network_label}" \
      "${network_name}" >/dev/null
  docker network connect "${network_name}" "${self_name}" >/dev/null 2>&1 || true
}

prepare_fabric_samples_repo() {
  local _fabric_dir="$1"
  mkdir -p "${_fabric_dir}"

  if [[ \
    -x "${TEST_NETWORK}/network.sh" && \
    -f "${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh" && \
    -f "${TEST_NETWORK}/organizations/ccp-generate.sh" && \
    -x "${FABRIC_SAMPLES_PATH}/bin/peer" && \
    -x "${FABRIC_SAMPLES_PATH}/bin/cryptogen" && \
    -f "${FABRIC_SAMPLES_PATH}/config/core.yaml" \
  ]]; then
    info "Using vendored fabric-samples assets at ${FABRIC_SAMPLES_PATH}"
    return 0
  fi

  case "${HLF_ALLOW_RUNTIME_DOWNLOADS:-0}" in
    1|true|TRUE|yes|YES|on|ON)
      local install_script="${HERE}/runtime/install-fabric.sh"

      [[ -f "${install_script}" ]] || die "HLF runtime downloads are enabled, but install script is missing: ${install_script}"

      info "HLF runtime downloads enabled; fetching pinned fabric-samples and Fabric binaries into ${FABRIC_SAMPLES_PATH}"
      rm -rf "${FABRIC_SAMPLES_PATH}"
      mkdir -p "${_fabric_dir}"
      (
        cd "${_fabric_dir}"
        FABRIC_SAMPLES_REPO="${FABRIC_SAMPLES_REPO}" \
        FABRIC_SAMPLES_REF="${FABRIC_SAMPLES_REF}" \
          run_logged_command "HLF runtime asset download" \
            bash "${install_script}" \
              --fabric-version "${IMAGE_TAG}" \
              --ca-version "${CA_IMAGE_TAG}" \
              samples binary
      )
      return 0
      ;;
  esac

  die "Vendored fabric-samples assets are missing or incomplete at ${FABRIC_SAMPLES_PATH}. Runtime bootstrap no longer clones or downloads from the internet; restore the shipped hlf/runtime/fabric-samples tree and retry."
}

msp_has_signing_key() {
  # Usage: msp_has_signing_key <msp_dir>
  # Returns 0 if the MSP contains a private key in keystore/, else 1.
  local msp_dir="$1"
  [[ -d "${msp_dir}" ]] || return 1
  [[ -d "${msp_dir}/keystore" ]] || return 1
  # Fabric CA keystore filenames vary (randomized). Any file indicates key material.
  ls -1 "${msp_dir}/keystore"/* >/dev/null 2>&1
}

ensure_org_admin_msp_ready() {
  # This catches the common host-side peer lifecycle failure:
  #   "KeyMaterial not found in SigningIdentityInfo"
  # which happens when organizations/ is partial/corrupted from previous runs.
  local orgs=("cascadiastate.example.com" "chesapeakecanoe.example.com")
  local i=1

  for org in "${orgs[@]}"; do
    local msp_dir="${TEST_NETWORK}/organizations/peerOrganizations/${org}/users/Admin@${org}/msp"

    if [[ ! -d "${TEST_NETWORK}/organizations" ]]; then
      info "Organizations directory not found. This is expected on first run."
      return 0
    fi

    if ! msp_has_signing_key "${msp_dir}"; then
      echo "[hlf] ERROR: Org${i} Admin MSP key material is missing." >&2
      echo "[hlf]   Expected a private key under:" >&2
      echo "[hlf]     ${msp_dir}/keystore/" >&2
      echo "[hlf]" >&2
      echo "[hlf] This usually means the network was started previously but crypto material was left in a partial state." >&2
      echo "[hlf] Fix:" >&2
      echo "[hlf]   1) ./lab.sh reset" >&2
      echo "[hlf]   2) ./lab.sh up" >&2
      return $((50 + i))
    fi
    ((i++))
  done
  return 0
}

doctor() {
  info "Running checks..."
  validate_all_inputs
  need_cmd docker
  if ! docker info >/dev/null 2>&1; then
    die "Docker daemon not reachable. Start Docker Desktop / Docker Engine and try again."
  fi
  if [[ -d "${TEST_NETWORK}" ]]; then
    info "Found fabric-samples test-network: ${TEST_NETWORK}"
    validate_test_network_layout
  else
    info "fabric-samples not found at: ${FABRIC_SAMPLES_PATH}"
    info "Run: ./lab.sh bootstrap  (or pre-stage fabric-samples at FABRIC_SAMPLES_PATH)"
  fi
  info "OK"
}

status() {
  info "Environment status:"
  echo -n " Docker: "; docker version --format '{{.Server.Version}}' >/dev/null 2>&1 && echo "running" || echo "not running"
  echo " Fabric containers (orderer/peers):"
  docker ps --filter "name=orderer.example.com" --filter "name=peer0.cascadiastate.example.com" --filter "name=peer0.chesapeakecanoe.example.com" --format '  {{.Names}} - {{.Status}}' || true
  echo -n " Tools container (${TOOLS_NAME}): "
  docker ps --format '{{.Names}}' | grep -qx "${TOOLS_NAME}" && echo "running" || echo "not running"
  echo -n " Web GUI (http://localhost:${WEB_UI_PORT}): "
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H8","location":"lab.sh:status","message":"Web UI status check","data":{"web_ui_port":"'${WEB_UI_PORT}'","web_ui_script":"'${WEB_UI_SCRIPT}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  if command -v curl >/dev/null 2>&1 && curl -sSf --head "http://localhost:${WEB_UI_PORT}" >/dev/null 2>&1; then
    echo "responding"
  else
    echo "not detected"
  fi
}

health() {
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"D","location":"lab.sh:health","message":"Health check started","data":{},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  info "=== Network Health Check ==="
  echo ""

  # Check Docker
  echo -n "🐳 Docker: "
  if docker version --format '{{.Server.Version}}' >/dev/null 2>&1; then
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"D","location":"lab.sh:health","message":"Docker check passed","data":{"result":"running"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion

    echo "✅ running"
  else
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"D","location":"lab.sh:health","message":"Docker check failed","data":{"result":"not_running"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion

    echo "❌ not running"
    echo "   Fix: Start Docker Desktop or Docker daemon"
    return 1
  fi

  # Check containers
  echo -n "🏗️  Fabric containers: "

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"D","location":"lab.sh:health","message":"Starting container check","data":{},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  local containers=0
  local all_containers_list
  all_containers_list=$(docker ps --format '{{.Names}}' 2>/dev/null || echo "")

  # Check for exact container names (not partial matches)
  echo "$all_containers_list" | grep -q "^orderer\.example\.com$" && containers=$((containers + 1))
  echo "$all_containers_list" | grep -q "^peer0\.org1\.example\.com$" && containers=$((containers + 1))
  echo "$all_containers_list" | grep -q "^peer0\.org2\.example\.com$" && containers=$((containers + 1))

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"D","location":"lab.sh:health","message":"Container count check","data":{"expected":3,"actual":'$containers',"all_containers":"'$all_containers_list'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  if [[ "$containers" -eq 3 ]]; then
    echo "✅ all running"
  else
    echo "❌ $containers/3 running"
    echo "   Fix: Run ./lab.sh up to start the network"

    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"D","location":"lab.sh:health","message":"Container count mismatch","data":{"expected":3,"actual":'$containers'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion

    return 1
  fi

  # Check tools container
  echo -n "🔧 Tools container: "
  if docker ps --format '{{.Names}}' | grep -qx "${TOOLS_NAME}"; then
    echo "✅ running"
  else
    echo "❌ not running"
    echo "   Fix: Will be created automatically when needed"
  fi

  echo ""
  info "=== Chaincode Health Check ==="

  # Check chaincode status
  if check_chaincode_health 2>/dev/null; then
    echo "✅ Chaincode properly deployed and committed"
  else
    echo "❌ Chaincode deployment issues detected"
    echo ""
    echo "🔍 Detailed diagnostics:"
    check_chaincode_health
    echo ""
    echo "🛠️  Recovery options:"
    echo "   1. Try redeploying: ./lab.sh deploy"
    echo "   2. Check deployment logs: ./lab.sh watch logs"
    echo "   3. Reset and restart: ./lab.sh reset && ./lab.sh up"
    return 1
  fi

  echo ""
  info "=== Transaction Testing ==="

  # Test basic connectivity
  echo -n "🌐 Peer connectivity: "
  if tools_exec_noninteractive 1 "peer channel getinfo -c ${CHANNEL}" >/dev/null 2>&1; then
    echo "✅ working"
  else
    echo "❌ failed"
    echo "   Fix: Check network connectivity and MSP configuration"
    return 1
  fi

  # Test chaincode query
  echo -n "📊 Chaincode query: "
  if tools_exec_noninteractive 1 "peer chaincode query -C ${CHANNEL} -n ${CC_NAME} -c '{\"Args\":[\"GetAllAssets\"]}'" >/dev/null 2>&1; then
    echo "✅ working"
  else
    echo "❌ failed"
    echo "   Fix: Ensure chaincode is deployed and committed"
    return 1
  fi

  echo ""
  echo "🎉 Network is healthy and ready for lab exercises!"
  echo ""
  echo "💡 Quick start commands:"
  echo "   ./lab.sh enter org1     # Open interactive shell"
  echo "   ./lab.sh watch logs     # Monitor network activity"
  echo "   ./lab.sh watch blocks   # Watch new blocks"
  echo "   ./lab.sh watch state    # Monitor state changes"
}

bootstrap() {
  need_cmd docker
  validate_all_inputs

  if ! bootstrap_should_stream_stdout; then
    mkdir -p "$(dirname "${BOOTSTRAP_LOG_PATH}")"
    : > "${BOOTSTRAP_LOG_PATH}"
  fi

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H6","location":"lab.sh:bootstrap","message":"bootstrap() entry","data":{"fabric_samples_path":"'${FABRIC_SAMPLES_PATH}'","test_network":"'${TEST_NETWORK}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  if [[ "$(basename "${FABRIC_SAMPLES_PATH}")" != "fabric-samples" ]]; then
    die "FABRIC_SAMPLES_PATH must end with 'fabric-samples' (got: ${FABRIC_SAMPLES_PATH})"
  fi

  local fabric_dir
  fabric_dir="$(dirname "${FABRIC_SAMPLES_PATH}")"
  mkdir -p "${fabric_dir}"

  local need_samples_checkout=0
  if [[ "${HLF_BOOTSTRAP_FORCE:-0}" == "1" ]]; then
    info "HLF_BOOTSTRAP_FORCE=1 — revalidating vendored fabric-samples assets."
    need_samples_checkout=1
  fi

  if [[ ! -d "${FABRIC_SAMPLES_PATH}" ]]; then
    info "fabric-samples assets not found; expected shipped assets in ${FABRIC_SAMPLES_PATH}"
    need_samples_checkout=1
  else
    info "Using vendored fabric-samples at ${FABRIC_SAMPLES_PATH}"
    if [[ \
      ! -x "${TEST_NETWORK}/network.sh" || \
      ! -f "${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh" || \
      ! -f "${TEST_NETWORK}/organizations/ccp-generate.sh" || \
      ! -x "${FABRIC_SAMPLES_PATH}/bin/peer" || \
      ! -x "${FABRIC_SAMPLES_PATH}/bin/cryptogen" || \
      ! -f "${FABRIC_SAMPLES_PATH}/config/core.yaml" \
    ]]; then
      info "Vendored fabric-samples assets appear incomplete."
      need_samples_checkout=1
    fi
  fi

  if [[ "${need_samples_checkout}" == "1" ]]; then
    prepare_fabric_samples_repo "${fabric_dir}"
  fi

  validate_test_network_layout
  apply_chaincode_overrides
  patch_managed_test_network
  run_logged_command "Fabric helper image builds" build_ttyd_images
  info "Bootstrap complete."

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H6","location":"lab.sh:bootstrap","message":"bootstrap() complete","data":{"network_sh_exists":'$( [ -x "${TEST_NETWORK}/network.sh" ] && echo "true" || echo "false" )',"register_enroll_exists":'$( [ -f "${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh" ] && echo "true" || echo "false" )',"ccp_generate_exists":'$( [ -f "${TEST_NETWORK}/organizations/ccp-generate.sh" ] && echo "true" || echo "false" )'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
}

pick_fabric_tools_image() {
  if [[ -n "${HLF_FABRIC_TOOLS_IMAGE:-}" ]]; then
    validate_image_ref "${HLF_FABRIC_TOOLS_IMAGE}"
    echo "${HLF_FABRIC_TOOLS_IMAGE}"
    return 0
  fi

  # Prefer a tools image matching the pinned Fabric IMAGE_TAG when available.
  local preferred="hyperledger/fabric-tools:${IMAGE_TAG}"
  if docker image inspect "${preferred}" >/dev/null 2>&1; then
    echo "${preferred}"
    return 0
  fi

  local img
  img="$(docker images --format '{{.Repository}}:{{.Tag}}' | awk '/^hyperledger\/fabric-tools:/{print $0}' | head -n 1 || true)"
  if [[ -n "${img}" ]]; then
    echo "${img}"
    return 0
  fi

  # Fallback (may not exist; user can override with HLF_FABRIC_TOOLS_IMAGE)
  echo "hyperledger/fabric-tools:latest"
}

detect_orderer_network() {
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:detect_orderer_network","message":"Starting network detection","data":{},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  local net
  # First try to get network from orderer container
  net="$(docker ps --filter 'name=^orderer.example.com$' --format '{{.Networks}}' 2>/dev/null | head -n 1 | cut -d, -f1 || true)"

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:detect_orderer_network","message":"Orderer container network check","data":{"net":"'$net'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  # If that fails, try to find a fabric network
  if [[ -z "${net}" ]]; then
    net="$(docker network ls --format '{{.Name}}' | grep -E '(fabric|test)' | head -n 1 || true)"

    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:detect_orderer_network","message":"Fabric network search","data":{"net":"'$net'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
  fi

  # Default fallback - try common fabric network names
  if [[ -z "${net}" ]]; then
    for possible_net in "fabric_test" "bridge" "host"; do
      if docker network ls --format '{{.Name}}' | grep -q "^${possible_net}$"; then
        net="${possible_net}"

        #region agent log
        echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:detect_orderer_network","message":"Found network via fallback","data":{"net":"'$net'","source":"'$possible_net'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
        #endregion

        break
      fi
    done
  fi

  # Last resort
  if [[ -z "${net}" ]]; then
    net="bridge"
    info "Using bridge network as fallback: ${net}"

    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:detect_orderer_network","message":"Using last resort network","data":{"net":"'$net'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
  fi

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"lab.sh:detect_orderer_network","message":"Network detection complete","data":{"final_net":"'$net'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  echo "${net}"
}

ensure_tools_container() {
  local tools_img net current_net
  tools_img="$(pick_fabric_tools_image)"
  net="$(detect_orderer_network)"

  # Check if container exists
  if docker ps --format '{{.Names}}' | grep -qx "${TOOLS_NAME}"; then
    # Check if it's on the correct network
    current_net="$(docker ps --filter "name=^${TOOLS_NAME}$" --format '{{.Networks}}' 2>/dev/null | head -n 1 || true)"
    if [[ ",${current_net}," == *",${net},"* ]]; then
      # Ensure volume mount points to the current FABRIC_SAMPLES_PATH
      local mount_src
      mount_src="$(timeout 3 docker inspect -f '{{range .Mounts}}{{if eq .Destination "/fabric-samples"}}{{.Source}}{{end}}{{end}}' "${TOOLS_NAME}" 2>/dev/null || true)"
      if [[ -n "${mount_src}" && "${mount_src}" != "${HOST_FABRIC_SAMPLES_PATH}" ]]; then
        info "Tools container has stale fabric-samples mount (${mount_src}), recreating..."
        docker rm -f "${TOOLS_NAME}" >/dev/null 2>&1 || true
      else
      # Verify fabric-samples is mounted inside the tools container
      if docker exec "${TOOLS_NAME}" test -d /fabric-samples/test-network 2>/dev/null; then
    return 0
      fi
      info "Tools container missing /fabric-samples/test-network, recreating..."
      docker rm -f "${TOOLS_NAME}" >/dev/null 2>&1 || true
      fi
    else
      info "Tools container is on wrong network (${current_net}), recreating on ${net}..."
      docker rm -f "${TOOLS_NAME}" >/dev/null 2>&1 || true
    fi
  fi

  # Remove any existing container
  docker rm -f "${TOOLS_NAME}" >/dev/null 2>&1 || true

  info "Starting tools container '${TOOLS_NAME}' on network '${net}' using image '${tools_img}' (${TOOLS_PLATFORM})..."
  if ! docker run -d --name "${TOOLS_NAME}" \
    --platform ${TOOLS_PLATFORM} \
    --network "${net}" \
    -v "${HOST_FABRIC_SAMPLES_PATH}:/fabric-samples" \
    "${tools_img}" \
    bash -lc "trap : TERM INT; sleep infinity" >/dev/null 2>&1; then
    echo "[hlf] ERROR: Failed to start tools container" >&2
    return 1
  fi

  # Attach to instructor-term network if available (best-effort)
  docker network connect hlf-instructor-term "${TOOLS_NAME}" 2>/dev/null || true

  # Wait a moment for container to be ready
  sleep 2

  info "Tools container started."

  # Verify fabric-samples is mounted inside the tools container
  if ! docker exec "${TOOLS_NAME}" test -d /fabric-samples/test-network 2>/dev/null; then
    info "Tools container missing /fabric-samples/test-network, recreating..."
    docker rm -f "${TOOLS_NAME}" >/dev/null 2>&1 || true
    if ! docker run -d --name "${TOOLS_NAME}" \
      --platform ${TOOLS_PLATFORM} \
      --network "${net}" \
      -v "${HOST_FABRIC_SAMPLES_PATH}:/fabric-samples" \
      "${tools_img}" \
      bash -lc "trap : TERM INT; sleep infinity" >/dev/null 2>&1; then
      echo "[hlf] ERROR: Failed to start tools container" >&2
      return 1
    fi
    if ! docker exec "${TOOLS_NAME}" test -d /fabric-samples/test-network 2>/dev/null; then
      echo "[hlf] ERROR: tools container missing /fabric-samples/test-network. Check FABRIC_SAMPLES_PATH=${FABRIC_SAMPLES_PATH}" >&2
      return 1
    fi
  fi
}

tools_exec() {
  # tools_exec <org_num> <bash_snippet>
  local org_num="$1"; shift
  local snippet="$1"

  if [[ -z "${CLI_HELPERS_B64}" ]]; then
    refresh_cli_helpers_b64
  fi
  ensure_tools_container

  docker exec -it -e ORG_NUM="${org_num}" -e SNIPPET="${snippet}" -e CLI_HELPERS_B64="${CLI_HELPERS_B64}" "${TOOLS_NAME}" bash -c '
    set -euo pipefail
    cd /fabric-samples/test-network
    export OVERRIDE_ORG=""
    export VERBOSE="false"
    source ./scripts/envVar.sh
    setGlobals "${ORG_NUM}" >/dev/null 2>&1 || true
    if [[ -n "${CLI_HELPERS_B64:-}" ]] && command -v base64 >/dev/null 2>&1; then
      printf "%s" "${CLI_HELPERS_B64}" | base64 -d > /tmp/hlf_cli_helpers.sh
      chmod 0644 /tmp/hlf_cli_helpers.sh || true
      source /tmp/hlf_cli_helpers.sh 2>/dev/null || true
    fi

    if [[ -f /.dockerenv ]]; then
      if [[ "${ORG_NUM}" == "1" ]]; then
        export CORE_PEER_ADDRESS="peer0.cascadiastate.example.com:7051"
      elif [[ "${ORG_NUM}" == "2" ]]; then
        export CORE_PEER_ADDRESS="peer0.chesapeakecanoe.example.com:9051"
      fi
    fi

    eval "${SNIPPET}"
  '
}

tools_exec_noninteractive() {
  # tools_exec_noninteractive <org_num> <bash_snippet> [load_cli_helpers]
  # Same as tools_exec but without -t (TTY) for background/monitoring processes
  local org_num="$1"; shift
  local snippet="$1"
  local load_cli_helpers="${2:-0}"

  if [[ "${load_cli_helpers}" == "1" ]] && [[ -z "${CLI_HELPERS_B64}" ]]; then
    refresh_cli_helpers_b64
  fi

  ensure_tools_container

  local docker_output docker_exit docker_stderr
  # Capture both stdout and stderr separately
  docker_stderr=$(docker exec -i -e ORG_NUM="${org_num}" -e SNIPPET="${snippet}" -e CLI_HELPERS_B64="${CLI_HELPERS_B64}" -e LOAD_CLI_HELPERS="${load_cli_helpers}" "${TOOLS_NAME}" bash -c '
    set +e
    exec 2>&1
    cd /fabric-samples/test-network || { echo "ERROR: cd failed" >&2; exit 1; }
    export OVERRIDE_ORG=""
    export VERBOSE="false"
    source ./scripts/envVar.sh || { echo "ERROR: source envVar.sh failed" >&2; exit 1; }
    setGlobals "${ORG_NUM}" >/dev/null 2>&1 || true
    if [[ "${LOAD_CLI_HELPERS:-0}" == "1" ]] && [[ -n "${CLI_HELPERS_B64:-}" ]] && command -v base64 >/dev/null 2>&1; then
      printf "%s" "${CLI_HELPERS_B64}" | base64 -d > /tmp/hlf_cli_helpers.sh
      chmod 0644 /tmp/hlf_cli_helpers.sh >/dev/null 2>&1 || true
      source /tmp/hlf_cli_helpers.sh >/dev/null 2>&1 || true
    fi
    if [[ -f /.dockerenv ]]; then
      if [[ "${ORG_NUM}" == "1" ]]; then
        export CORE_PEER_ADDRESS="peer0.cascadiastate.example.com:7051"
      elif [[ "${ORG_NUM}" == "2" ]]; then
        export CORE_PEER_ADDRESS="peer0.chesapeakecanoe.example.com:9051"
      fi
    fi
    eval "${SNIPPET}"
    exit $?
  ' 2>&1)
  docker_exit=$?
  docker_output="$docker_stderr"

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"C","location":"lab.sh:tools_exec_noninteractive","message":"Docker exec output captured","data":{"exit_code":'$docker_exit',"output_length":'${#docker_output}',"output_preview":"'${docker_output:0:200}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  # Extract exit code from output if present
  if echo "$docker_output" | grep -q "EXIT_CODE:"; then
    docker_exit=$(echo "$docker_output" | grep "EXIT_CODE:" | sed 's/.*EXIT_CODE:\([0-9]*\).*/\1/')
    docker_output=$(echo "$docker_output" | sed '/EXIT_CODE:/d')
  fi

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"C","location":"lab.sh:tools_exec_noninteractive","message":"Final exit code","data":{"exit_code":'$docker_exit'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  echo "$docker_output"
  return $docker_exit
}

launch_web_ui() {
  # Launch the web UI in the background
  local web_ui_path="${HERE}/${WEB_UI_SCRIPT}"
  local web_ui_log="${HERE}/.web_ui.log"
  
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H8","location":"lab.sh:launch_web_ui","message":"Starting web UI launch","data":{"web_ui_path":"'${web_ui_path}'","web_ui_port":"'${WEB_UI_PORT}'","auto_launch":"'${AUTO_LAUNCH_WEB_UI}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  
  # Check if web UI script exists
  if [[ ! -f "${web_ui_path}" ]]; then
    echo "[hlf] WARNING: Web UI script not found at ${web_ui_path}" >&2
    echo "[hlf] Skipping web UI launch. Set HLF_WEB_UI_SCRIPT to the correct path." >&2
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Web UI script not found","data":{"web_ui_path":"'${web_ui_path}'","exists":false},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    return 1
  fi
  
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Web UI script found","data":{"web_ui_path":"'${web_ui_path}'","exists":true},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  
  # Check if web UI is already running
  local port_in_use=false
  if command -v lsof >/dev/null 2>&1; then
    if lsof -ti:${WEB_UI_PORT} >/dev/null 2>&1; then
      port_in_use=true
    fi
  elif command -v netstat >/dev/null 2>&1; then
    if netstat -an 2>/dev/null | grep -q ":${WEB_UI_PORT}.*LISTEN"; then
      port_in_use=true
    fi
  fi
  
  if [[ "${port_in_use}" == "true" ]]; then
    echo "[hlf] Web UI is already running on port ${WEB_UI_PORT}"
    echo "[hlf] Access it at: http://localhost:${WEB_UI_PORT}"
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Web UI already running","data":{"port":"'${WEB_UI_PORT}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    return 0
  fi
  
  # Check if Python virtual environment exists
  local venv_path="${HERE}/../../.venv"
  local python_cmd="python3"
  if [[ -d "${venv_path}" ]]; then
    if [[ -f "${venv_path}/bin/python" ]]; then
      python_cmd="${venv_path}/bin/python"
    elif [[ -f "${venv_path}/bin/python3" ]]; then
      python_cmd="${venv_path}/bin/python3"
    fi
  fi
  
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Using Python command","data":{"python_cmd":"'${python_cmd}'","venv_exists":'$([ -d "${venv_path}" ] && echo "true" || echo "false")'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  
  echo "[hlf] Launching web UI on port ${WEB_UI_PORT}..."
  echo "[hlf] Logs: ${web_ui_log}"
  
  # Launch in background
  nohup "${python_cmd}" "${web_ui_path}" > "${web_ui_log}" 2>&1 &
  local web_ui_pid=$!
  
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Web UI process started","data":{"pid":'${web_ui_pid}',"log_file":"'${web_ui_log}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  
  # Wait a moment to check if it started successfully
  sleep 2
  
  # Check if process is still running
  if ! kill -0 "${web_ui_pid}" 2>/dev/null; then
    echo "[hlf] ERROR: Web UI failed to start. Check logs: ${web_ui_log}" >&2
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Web UI process died","data":{"pid":'${web_ui_pid}'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    return 1
  fi
  
  # Wait for port to be available (up to 10 seconds)
  local max_wait=10
  local waited=0
  while [[ $waited -lt $max_wait ]]; do
    if command -v lsof >/dev/null 2>&1; then
      if lsof -ti:${WEB_UI_PORT} >/dev/null 2>&1; then
        break
      fi
    elif command -v netstat >/dev/null 2>&1; then
      if netstat -an 2>/dev/null | grep -q ":${WEB_UI_PORT}.*LISTEN"; then
        break
      fi
    fi
    sleep 1
    waited=$((waited + 1))
  done
  
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Port check completed","data":{"port":"'${WEB_UI_PORT}'","waited":'${waited}',"max_wait":'${max_wait}'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  
  if [[ $waited -ge $max_wait ]]; then
    echo "[hlf] WARNING: Web UI may not have started. Check logs: ${web_ui_log}" >&2
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Port not available after wait","data":{"port":"'${WEB_UI_PORT}'","waited":'${waited}'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    return 1
  fi
  
  echo "[hlf] ✓ Web UI started successfully"
  echo "[hlf] Access at: http://localhost:${WEB_UI_PORT}"
  echo "[hlf] Process ID: ${web_ui_pid}"
  echo "[hlf] To stop: kill ${web_ui_pid} or ./lab.sh down"
  
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:launch_web_ui","message":"Web UI launch successful","data":{"pid":'${web_ui_pid}',"port":"'${WEB_UI_PORT}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  
  # Try to open browser (platform-specific)
  if command -v open >/dev/null 2>&1; then
    # macOS
    sleep 1
    open "http://localhost:${WEB_UI_PORT}" 2>/dev/null || true
  elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    sleep 1
    xdg-open "http://localhost:${WEB_UI_PORT}" 2>/dev/null || true
  elif command -v start >/dev/null 2>&1; then
    # Windows (Git Bash)
    sleep 1
    start "http://localhost:${WEB_UI_PORT}" 2>/dev/null || true
  fi
}

restart_web_ui() {
  local did_kill=false
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -ti:${WEB_UI_PORT} 2>/dev/null || true)
    if [[ -n "${pids}" ]]; then
      echo "[hlf] Stopping web UI on port ${WEB_UI_PORT}..."
      kill ${pids} >/dev/null 2>&1 || true
      sleep 1
      if lsof -ti:${WEB_UI_PORT} >/dev/null 2>&1; then
        kill -9 ${pids} >/dev/null 2>&1 || true
      fi
      did_kill=true
    fi
  else
    echo "[hlf] WARNING: lsof not available; cannot auto-stop web UI." >&2
  fi

  if [[ "${did_kill}" == "true" ]]; then
    echo "[hlf] Restarting web UI..."
  fi
  launch_web_ui
}

preflight_cli_helpers() {
  refresh_cli_helpers_b64

  if [[ -z "${CLI_HELPERS_B64}" ]]; then
    echo "[hlf] ERROR: CLI helper definitions not found at ${CLI_HELPERS_FILE}" >&2
    return 1
  fi

  local out rc missing_helpers=0
  out="$(tools_exec_noninteractive 1 "invoke help" 1 2>&1)"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "[hlf] ERROR: invoke help failed during preflight" >&2
    echo "$out" >&2
    return 1
  fi

  for token in "init-ledger" "create" "transfer" "delete"; do
    if ! echo "$out" | grep -q "${token}"; then
      missing_helpers=1
    fi
  done

  if [[ "${missing_helpers}" -ne 0 ]]; then
    echo "[hlf] ERROR: helper subcommands missing; restarting web UI to refresh helper definitions." >&2
    if [[ "${AUTO_LAUNCH_WEB_UI}" == "1" ]]; then
      restart_web_ui
    fi
    return 1
  fi

  out="$(tools_exec_noninteractive 1 "peer chaincode query -C ${CHANNEL} -n ${CC_NAME} -c '{\"Args\":[\"GetAllAssets\"]}'" 2>&1)"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "[hlf] ERROR: GetAllAssets failed during preflight" >&2
    echo "$out" >&2
    return 1
  fi

  echo "[hlf] Preflight checks passed."
  return 0
}

fix_bind_mount_permissions() {
  # Student peer containers run with cap_drop: ALL, stripping DAC_OVERRIDE.
  # Without that capability even root cannot traverse 700 directories owned
  # by another uid. Ensure every directory under fabric-samples (crypto,
  # peercfg, channel-artifacts) and the scripts dir is world-readable so
  # bind mounts work. Also restore execute bits on scripts and binaries
  # that git checkout with a restrictive umask may have stripped.
  info "Fixing bind-mount permissions for capability-restricted student containers..."
  local fabric_dir
  fabric_dir="$(dirname "${TEST_NETWORK}")"
  find "${fabric_dir}" -type d -exec chmod 755 {} +
  find "${fabric_dir}" -type f ! -perm -044 -exec chmod a+r {} +
  find "${fabric_dir}" -name '*.sh' -exec chmod 755 {} +
  if [[ -d "${fabric_dir}/bin" ]]; then
    chmod 755 "${fabric_dir}"/bin/*
  fi
  local scripts_dir
  scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts"
  chmod 755 "${scripts_dir}"
  find "${scripts_dir}" -type f -name '*.sh' -exec chmod 755 {} +
}

enroll_student_overlay() {
  # Phase 7 hybrid student overlay: assumes 4-org consortium + channel +
  # chaincode are up. Loops Student01..StudentNN: start peer → join
  # channel → install chaincode → stop peer. End state: the configured
  # student rack is cold and ready for lane manager hot-swap on claim.
  build_ttyd_images
  local hlf_student_count
  hlf_student_count="${HLF_STUDENT_COUNT:-${MAX_STUDENT_CAPACITY:-20}}"
  info "Enrolling ${hlf_student_count} student peers (join + install chaincode, leave cold)"
  local managed_runtime_dir
  managed_runtime_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/managed_runtime"
  STUDENT_COUNT="${hlf_student_count}" \
  HLF_STUDENT_COUNT="${hlf_student_count}" \
  MANAGED_RUNTIME_DIR="${managed_runtime_dir}" \
  TEST_NETWORK="${TEST_NETWORK}" \
  HOST_TEST_NETWORK="${HOST_TEST_NETWORK}" \
  HOST_FABRIC_SAMPLES_PATH="${HOST_FABRIC_SAMPLES_PATH}" \
  IMAGE_TAG="${IMAGE_TAG}" \
  PLATFORM="${PLATFORM}" \
  TOOLS_PLATFORM="${TOOLS_PLATFORM}" \
  CHANNEL="${CHANNEL:-diplomas}" \
  CC_NAME="${CC_NAME}" \
  CC_VERSION="${CC_VERSION}" \
  CC_SEQ="${CC_SEQUENCE}" \
    bash "$(dirname "${BASH_SOURCE[0]}")/scripts/bootstrap-classroom.sh"
}

up() {
  validate_all_inputs
  validate_test_network_layout
  patch_managed_test_network
  build_ttyd_images

  info "🚀 Starting Fabric test network..."
  echo "[hlf] Step 1/4: Cleaning up any existing network..."
  down >/dev/null 2>&1 || true

  echo "[hlf] Step 2/4: Starting network runtime containers..."
  ensure_managed_control_plane_networking
  start_runtime_ca

  # Regenerate crypto if any expected MSP cacerts dir is missing. Checking
  # only for the parent peerOrganizations dir is not enough: a failed prior
  # run (or a partial cleanup) can leave the skeleton in place with empty
  # peer subdirs but no MSP material, which causes configtxgen to fail with
  # "could not load a valid ca certificate from .../msp/cacerts" at channel
  # creation.
  local hlf_student_count
  hlf_student_count="${HLF_STUDENT_COUNT:-${MAX_STUDENT_CAPACITY:-20}}"
  local _msp_required=(
    "${TEST_NETWORK}/organizations/peerOrganizations/cascadiastate.example.com/msp/cacerts"
    "${TEST_NETWORK}/organizations/peerOrganizations/chesapeakecanoe.example.com/msp/cacerts"
    "${TEST_NETWORK}/organizations/peerOrganizations/southhudson.example.com/msp/cacerts"
    "${TEST_NETWORK}/organizations/peerOrganizations/mapleleaf.example.com/msp/cacerts"
    "${TEST_NETWORK}/organizations/peerOrganizations/meridian.example.com/msp/cacerts"
    "${TEST_NETWORK}/organizations/ordererOrganizations/example.com/msp/cacerts"
  )
  local _sn
  for _sn in $(seq -w 01 "${hlf_student_count}"); do
    _msp_required+=("${TEST_NETWORK}/organizations/peerOrganizations/student${_sn}.example.com/msp/cacerts")
  done
  local _need_crypto=0
  for _msp in "${_msp_required[@]}"; do
    if [[ ! -d "${_msp}" ]] || [[ -z "$(ls -A "${_msp}" 2>/dev/null)" ]]; then
      _need_crypto=1
      break
    fi
  done
  if [[ "${_need_crypto}" -eq 1 ]]; then
    info "MSP material missing or incomplete — wiping partial crypto/CA state and regenerating"
    # Stop CAs so we can wipe their on-disk state safely. Otherwise a
    # previous run's registrations survive and re-registering peer0/user1
    # fails with Fabric CA error code 74 ("Identity is already registered").
    runtime_compose -f compose/compose-ca.yaml down -v >/dev/null 2>&1 || true
    rm -rf \
      "${TEST_NETWORK}/organizations/peerOrganizations" \
      "${TEST_NETWORK}/organizations/ordererOrganizations" \
      "${TEST_NETWORK}/organizations/fabric-ca/org1"/{msp,tls-cert.pem,ca-cert.pem,IssuerPublicKey,IssuerRevocationPublicKey,fabric-ca-server.db,fabric-ca-server-config.yaml} \
      "${TEST_NETWORK}/organizations/fabric-ca/org2"/{msp,tls-cert.pem,ca-cert.pem,IssuerPublicKey,IssuerRevocationPublicKey,fabric-ca-server.db,fabric-ca-server-config.yaml} \
      "${TEST_NETWORK}/organizations/fabric-ca/ordererOrg"/{msp,tls-cert.pem,ca-cert.pem,IssuerPublicKey,IssuerRevocationPublicKey,fabric-ca-server.db,fabric-ca-server-config.yaml} \
      2>/dev/null || true
    start_runtime_ca
    generate_crypto_material_via_containers
  fi

  start_runtime_network_containers

  info "Waiting for all peer containers to become healthy..."
  local _peer_names=(
    peer0.cascadiastate.example.com
    peer0.chesapeakecanoe.example.com
    peer0.southhudson.example.com
    peer0.mapleleaf.example.com
    peer0.meridian.example.com
  )
  local _max_wait=30
  local _waited=0
  local _all_running=0
  while [[ ${_waited} -lt ${_max_wait} ]]; do
    _all_running=1
    for _pn in "${_peer_names[@]}"; do
      local _state
      _state=$(docker inspect --format '{{.State.Running}}' "${_pn}" 2>/dev/null || echo "false")
      if [[ "${_state}" != "true" ]]; then
        _all_running=0
        break
      fi
    done
    if [[ ${_all_running} -eq 1 ]]; then
      break
    fi
    sleep 2
    _waited=$((_waited + 2))
  done
  if [[ ${_all_running} -eq 0 ]]; then
    echo "[hlf] ERROR: Not all peer containers are running after ${_max_wait}s." >&2
    echo "[hlf] Check 'docker ps -a' and 'docker logs <peer>' for crashed peers." >&2
    echo "[hlf] Common cause: CouchDB credential mismatch from stale volumes." >&2
    echo "[hlf] Fix: docker volume prune -f && ./lab.sh reset && ./lab.sh up" >&2
    return 1
  fi
  info "All peer containers are running."

  echo "[hlf] Step 3/4: Creating channel..."
  if ! create_channel_via_tools_container; then
    echo "[hlf] ERROR: Failed to create Fabric channel" >&2
    return 1
  fi

  echo "[hlf] Step 4/4: Verifying MSP materials..."
  # Guardrail: ensure org admin MSPs are complete before running lifecycle operations
  if ! ensure_org_admin_msp_ready; then
    echo "[hlf] ERROR: MSP material incomplete. This usually happens on first run." >&2
    echo "[hlf] The network started but crypto materials weren't generated properly." >&2
    echo "[hlf] Fix: Run ./lab.sh reset && ./lab.sh up" >&2
    return 1
  fi

  if [[ "${DEPLOY_CHAINCODE}" == "1" ]]; then
    # Allow override via env, but default to JS chaincode (no host installs)
    local cc_lang="${CC_LANG}"
    local cc_rel="${CC_REL_PATH}"
    local cc_abs="${TEST_NETWORK}/${cc_rel}"

    # Guardrail: this lab is meant to be self-contained for web delivery.
    if [[ "${cc_lang}" == "go" ]]; then
      die "CC_LANG=go requires a Go toolchain. For this self-contained lab, use CC_LANG=javascript (default)."
    fi

    if [[ -d "${cc_abs}" ]]; then
      info "Deploying sample chaincode '${CC_NAME}' (asset-transfer-basic, lang=${cc_lang})..."
      if ! deploy_chaincode_manual; then
        echo "[hlf] WARNING: Chaincode deployment failed during network startup." >&2
        echo "[hlf] You can try to deploy it manually later with: ./lab.sh deploy" >&2
        echo "[hlf] Or check the deployment status with: ./lab.sh enter org1" >&2
        echo "[hlf] Then run: peer lifecycle chaincode querycommitted -C diplomas" >&2
      fi
    else
      info "Skipping chaincode deploy: expected chaincode directory at ${cc_abs}"
      info "If you have your own chaincode, deploy it from ${TEST_NETWORK} with ./network.sh deployCC ..."
    fi
  else
    info "HLF_DEPLOY_CHAINCODE=0 — skipping chaincode deploy."
  fi

  ensure_tools_container

  if ! preflight_cli_helpers; then
    echo "[hlf] Preflight failed. Attempting auto-fix (re-apply overrides + deploy)..." >&2
    apply_chaincode_overrides
    if ! deploy; then
      echo "[hlf] ERROR: Auto-fix deploy failed." >&2
      return 1
    fi
    if ! preflight_cli_helpers; then
      echo "[hlf] ERROR: Preflight failed after auto-fix. Review logs and helper definitions." >&2
      return 1
    fi
  fi

  fix_bind_mount_permissions

  if ! enroll_student_overlay; then
    echo "[hlf] WARNING: student overlay enrollment failed — students may not be able to claim stations." >&2
    echo "[hlf] Re-run: ./lab.sh enroll-students" >&2
  fi

  echo "[hlf] Network is up."

  # Auto-launch web UI if enabled
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:up","message":"Auto-launch check","data":{"auto_launch":"'${AUTO_LAUNCH_WEB_UI}'","web_ui_port":"'${WEB_UI_PORT}'","web_ui_script":"'${WEB_UI_SCRIPT}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
  if [[ "${AUTO_LAUNCH_WEB_UI}" == "1" ]]; then
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:up","message":"Auto-launch enabled","data":{},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    launch_web_ui
  else
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"WEB_UI","location":"lab.sh:up","message":"Auto-launch disabled","data":{},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    echo ""
    echo "Recommended workflow (3 terminals):"
    echo ""
    echo "  Terminal 1 (interactive):"
    echo "    ./lab.sh enter org1"
    echo ""
    echo "  Terminal 2 (network activity):"
    echo "    ./lab.sh watch logs"
    echo ""
    echo "  Terminal 3 (ledger visibility):"
    echo "    ./lab.sh watch blocks"
    echo "    ./lab.sh watch state"
    echo ""
    echo "Or launch the web UI with:"
    echo "    ./lab.sh web-ui"
    echo ""
    echo "Or set HLF_AUTO_LAUNCH_WEB_UI=1 to auto-launch on network start"
  fi
}

deploy() {
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H1","location":"lab.sh:deploy","message":"deploy() function entry","data":{"cc_lang":"'${CC_LANG}'","cc_name":"'${CC_NAME}'","cc_version":"'${CC_VERSION}'","cc_sequence":"'${CC_SEQUENCE}'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  validate_all_inputs
  apply_chaincode_overrides

  # Deploy/upgrade chaincode WITHOUT tearing the network down.
  local cc_lang="${CC_LANG}"
  local cc_rel="${CC_REL_PATH}"
  local cc_abs="${TEST_NETWORK}/${cc_rel}"

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H1","location":"lab.sh:deploy","message":"After validate_all_inputs","data":{"cc_abs":"'$cc_abs'","cc_rel":"'$cc_rel'","cc_lang":"'$cc_lang'"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  if [[ "${cc_lang}" == "go" ]]; then
    die "CC_LANG=go requires a Go toolchain. For this self-contained lab, use CC_LANG=javascript (default)."
  fi

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H1","location":"lab.sh:deploy","message":"Before calling package_and_install_chaincode","data":{"function_exists":'$(type package_and_install_chaincode 2>/dev/null && echo "true" || echo "false")'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  # Use the robust deployment process - try deploy_chaincode_with_retry first, fallback to manual
  if deploy_chaincode_with_retry; then
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H2","location":"lab.sh:deploy","message":"deploy_chaincode_with_retry succeeded","data":{"result":"success"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    info "Chaincode deployment completed successfully!"
    return 0
  else
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H2","location":"lab.sh:deploy","message":"deploy_chaincode_with_retry failed, trying manual","data":{"result":"failed"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    info "Standard deployment failed, attempting manual deployment..."
    if deploy_chaincode_manual; then
      #region agent log
      echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H3","location":"lab.sh:deploy","message":"deploy_chaincode_manual succeeded","data":{"result":"success"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
      #endregion
      info "Chaincode deployment completed successfully (manual method)!"
      return 0
    else
      #region agent log
      echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H3","location":"lab.sh:deploy","message":"Both deployment methods failed","data":{"result":"failed"},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
      #endregion
      echo "[hlf] ERROR: Chaincode deployment failed with both standard and manual methods" >&2
      return 1
    fi
  fi
}

down() {
  local hlf_student_count
  hlf_student_count="${HLF_STUDENT_COUNT:-${MAX_STUDENT_CAPACITY:-20}}"
  if [[ -f "${TEST_NETWORK}/compose/compose-students.yaml" ]]; then
    info "Tearing down student overlay compose stack..."
    # All profiles must be included so `down` reaches stopped student peers.
    local -a s_profiles=()
    for n in $(seq -w 01 "${hlf_student_count}"); do s_profiles+=(--profile "s${n}"); done
    (cd "${TEST_NETWORK}" && docker compose -p hlf-students -f compose/compose-students.yaml \
      "${s_profiles[@]}" down --volumes --remove-orphans) || true
  fi
  # Legacy Phase 7-pure compose (orderer+Employer+student peers). Harmless
  # if absent; present only on machines that ran the old flow.
  if [[ -f "${TEST_NETWORK}/compose/compose-classroom.yaml" ]]; then
    info "Tearing down legacy Phase 7-pure compose stack..."
    local -a p7_profiles=()
    for n in $(seq -w 01 "${hlf_student_count}"); do p7_profiles+=(--profile "s${n}"); done
    (cd "${TEST_NETWORK}" && docker compose -f compose/compose-classroom.yaml \
      "${p7_profiles[@]}" down --volumes --remove-orphans) || true
  fi
  if [[ -d "${TEST_NETWORK}/compose" ]]; then
    info "Tearing down managed compose stack (orderer/peers/couch/CAs)..."
    # Bring down our managed compose stack directly. network.sh's `down` targets
    # the upstream compose-bft-test-net.yaml which we don't render, so volumes
    # leak across resets and chaincode ends up "already installed" after reset.
    local -a managed_args=()
    [[ -f "${TEST_NETWORK}/compose/compose-test-net.yaml" ]] && managed_args+=(-f compose/compose-test-net.yaml)
    [[ -f "${TEST_NETWORK}/compose/compose-couch.yaml" ]] && managed_args+=(-f compose/compose-couch.yaml)
    [[ -f "${TEST_NETWORK}/compose/compose-ca.yaml" ]] && managed_args+=(-f compose/compose-ca.yaml)
    if [[ ${#managed_args[@]} -gt 0 ]]; then
      (cd "${TEST_NETWORK}" && docker compose "${managed_args[@]}" down --volumes --remove-orphans) || true
    fi
    # Remove dev-peer chaincode images so new peers rebuild from scratch.
    local -a dev_imgs
    mapfile -t dev_imgs < <(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^dev-peer0\.' || true)
    if [[ ${#dev_imgs[@]} -gt 0 ]]; then
      info "Removing ${#dev_imgs[@]} dev-peer chaincode image(s)..."
      docker rmi -f "${dev_imgs[@]}" >/dev/null 2>&1 || true
    fi
  elif [[ -x "${TEST_NETWORK}/network.sh" ]]; then
    info "Tearing down Fabric test network via network.sh..."
    (cd "${TEST_NETWORK}" && ./network.sh down) || true
  else
    info "Nothing to tear down (test-network not present)."
  fi

  docker rm -f "${TOOLS_NAME}" >/dev/null 2>&1 || true
  docker rm -f chaincode-basic >/dev/null 2>&1 || true

  # Backstop sweep: remove any stray student-lane peer containers that
  # escaped the compose teardown above. This happens when a peer was
  # created by a prior compose project whose name no longer matches
  # (e.g. after a regen of compose-students.yaml), so `compose down`
  # can't find it. Matching is by container name, which lanes.py
  # guarantees is `peer0.student<NN>.example.com`.
  local _stray_students
  _stray_students=$(docker ps -a --format '{{.Names}}' \
    | grep -E '^peer0\.student[0-9]+\.example\.com$' || true)
  if [[ -n "${_stray_students}" ]]; then
    local _stray_count
    _stray_count=$(echo "${_stray_students}" | wc -l | tr -d ' ')
    info "Sweeping ${_stray_count} stray student-lane peer container(s)..."
    # shellcheck disable=SC2086
    docker rm -fv ${_stray_students} >/dev/null 2>&1 || true
  fi

  info "Done."
}

reset() {
  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H7","location":"lab.sh:reset","message":"reset() entry","data":{"network_sh_exists":'$( [ -x "${TEST_NETWORK}/network.sh" ] && echo "true" || echo "false" )',"register_enroll_exists":'$( [ -f "${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh" ] && echo "true" || echo "false" )',"ccp_generate_exists":'$( [ -f "${TEST_NETWORK}/organizations/ccp-generate.sh" ] && echo "true" || echo "false" )'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion

  down
  if [[ -d "${TEST_NETWORK}" ]]; then
    info "Removing generated test-network artifacts while preserving vendored scaffold..."
    rm -rf \
      "${TEST_NETWORK}/channel-artifacts" \
      "${TEST_NETWORK}/system-genesis-block" \
      "${TEST_NETWORK}/student-overlay" \
      "${TEST_NETWORK}/organizations/peerOrganizations" \
      "${TEST_NETWORK}/organizations/ordererOrganizations" \
      "${TEST_NETWORK}/organizations/fabric-ca/org1" \
      "${TEST_NETWORK}/organizations/fabric-ca/org2" \
      "${TEST_NETWORK}/organizations/fabric-ca/ordererOrg" \
      2>/dev/null || true
    rm -f "${TEST_NETWORK}"/*.block "${TEST_NETWORK}"/*.tx 2>/dev/null || true
    # Also drop student peer volumes so re-enrollment starts from empty
    # ledger. Volumes are named peer0.studentNN.example.com (from
    # compose-students.yaml). docker volume rm is idempotent with `-f`.
    local _svols
    _svols=$(docker volume ls -q --filter 'name=peer0.student' 2>/dev/null || true)
    if [[ -n "${_svols}" ]]; then
      # shellcheck disable=SC2086
      docker volume rm -f ${_svols} >/dev/null 2>&1 || true
    fi
  fi
  # If the core layout is missing (not just generated artifacts), re-bootstrap.
  # Check network.sh and rendered compose — these survive reset but wouldn't
  # exist if fabric-samples was never bootstrapped.
  if [[ ! -x "${TEST_NETWORK}/network.sh" || ! -f "${TEST_NETWORK}/compose/compose-test-net.yaml" ]]; then
    #region agent log
    echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H7","location":"lab.sh:reset","message":"reset() triggering bootstrap","data":{},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
    #endregion
    info "Reset removed required fabric-samples layout; re-bootstrapping..."
    bootstrap
  fi
  info "Reset complete."

  #region agent log
  echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H7","location":"lab.sh:reset","message":"reset() complete","data":{"network_sh_exists":'$( [ -x "${TEST_NETWORK}/network.sh" ] && echo "true" || echo "false" )',"register_enroll_exists":'$( [ -f "${TEST_NETWORK}/organizations/fabric-ca/registerEnroll.sh" ] && echo "true" || echo "false" )',"ccp_generate_exists":'$( [ -f "${TEST_NETWORK}/organizations/ccp-generate.sh" ] && echo "true" || echo "false" )'},"timestamp":'$(date +%s%3N)'}' >> ${DEBUG_LOG_PATH}
  #endregion
}

enter_org() {
  local org="$1"
  local org_num=""
  case "${org}" in
    org1) org_num="1" ;;
    org2) org_num="2" ;;
    *) die "enter expects org1 or org2" ;;
  esac

  local peer_addr=""
  case "${org_num}" in
    1) peer_addr="peer0.cascadiastate.example.com:7051" ;;
    2) peer_addr="peer0.chesapeakecanoe.example.com:9051" ;;
    *) die "Internal error: unknown org_num ${org_num}" ;;
  esac

  ensure_tools_container
  info "Opening tools shell in '${TOOLS_NAME}' as ${org}..."
  # Propagate terminal settings so bash stays interactive
  local cols rows term
  cols="$(tput cols 2>/dev/null || echo 120)"
  rows="$(tput lines 2>/dev/null || echo 40)"
  term="${TERM:-xterm-256color}"

  if [[ -z "${CLI_HELPERS_B64}" ]]; then
    refresh_cli_helpers_b64
  fi

  docker exec -it \
    -e ORG_NUM="${org_num}" \
    -e ORG_LABEL="${org}" \
    -e CHANNEL="${CHANNEL}" \
    -e PEER_ADDR="${peer_addr}" \
    -e CLI_HELPERS_B64="${CLI_HELPERS_B64}" \
    -e TERM="${term}" -e COLUMNS="${cols}" -e LINES="${rows}" \
    "${TOOLS_NAME}" bash -lc "$(cat <<'INVOKE_SETUP'
      # Avoid -u: envVar.sh may read unset vars during init
      set -Ee -o pipefail
      cd /fabric-samples/test-network
      source ./scripts/envVar.sh

      if ! setGlobals "${ORG_NUM}" >/dev/null 2>&1; then
        echo "[hlf] ERROR: Failed to set org globals (ORG_NUM=${ORG_NUM})." >&2
        echo "[hlf] This usually means fabric-samples layout changed or organizations are missing." >&2
        exit 40
      fi

      : "${PEER_ADDR:?PEER_ADDR not set}"
      export CORE_PEER_ADDRESS="${PEER_ADDR}"

      # Export variables needed for invoke commands
      export ORDERER_ADDRESS="orderer.example.com:7050"
      export ORDERER_TLS_HOSTNAME="orderer.example.com"
      : "${ORDERER_CA:?ORDERER_CA not set by setGlobals}"
      export ORDERER_CA_FILE="${ORDERER_CA}"

      # Set up peer connection parameters for invoke commands
      # These are set by envVar.sh, but we need to ensure they're available
      export PEER0_ORG1_ADDR="peer0.cascadiastate.example.com:7051"
      export PEER0_ORG2_ADDR="peer0.chesapeakecanoe.example.com:9051"
      # PEER0_ORG1_CA and PEER0_ORG2_CA are already set by envVar.sh

      if [[ -n "${CLI_HELPERS_B64:-}" ]] && command -v base64 >/dev/null 2>&1; then
        printf "%s" "${CLI_HELPERS_B64}" | base64 -d > /tmp/hlf_cli_helpers.sh
        chmod 0644 /tmp/hlf_cli_helpers.sh || true
        printf '%s\n' 'source /tmp/hlf_cli_helpers.sh 2>/dev/null || true' > /tmp/hlf_enter_rc
      else
        echo "[hlf] WARNING: CLI helper definitions not available." >&2
        echo "[hlf] invoke/query helpers will be missing in this shell." >&2
        printf '%s\n' ':' > /tmp/hlf_enter_rc
      fi

      echo
      echo "[hlf] Tools shell ready for ${ORG_LABEL}."
      echo "[hlf] MSP: ${CORE_PEER_LOCALMSPID}"
      echo "[hlf] Peer: ${CORE_PEER_ADDRESS}"
      echo "[hlf] Channel: ${CHANNEL}"
      echo "[hlf]"
      echo "[hlf] Helper functions available: invoke, query"
      echo "[hlf] Usage: invoke <action> ... or invoke --raw '<json>'"
      echo "[hlf] Usage: query all | query <assetId> | query price <assetId>"
      echo "[hlf] See STUDENT_GUIDE.md for examples"
      echo "[hlf]"
      echo "[hlf] Try: peer channel getinfo -c ${CHANNEL}"
      echo

      bash --rcfile /tmp/hlf_enter_rc -i
INVOKE_SETUP
    )"
  local rc=$?
  # Exiting the interactive shell can return a non-zero status depending on the last command.
  # Only treat our explicit setup failure as fatal.
  if [[ ${rc} -eq 40 ]]; then
    die "Failed to set org globals inside tools shell (ORG_NUM=${org_num})."
  fi
  return 0
}

watch_logs() {
  info "Tailing logs for Fabric network (Ctrl+C to stop)..."

  local container_list
  container_list=$(docker ps --format '{{.Names}}' 2>/dev/null || echo "")
  if ! echo "$container_list" | grep -q "orderer.example.com" || \
     ! echo "$container_list" | grep -q "peer0.cascadiastate.example.com" || \
     ! echo "$container_list" | grep -q "peer0.chesapeakecanoe.example.com"; then
    die "Fabric containers not detected. Run: ./lab.sh up"
  fi

  # Prefer docker compose logs against the compose files used by fabric-samples test-network.
  # NOTE: fabric-samples has changed file layouts over time (docker/ vs compose/ and different filenames),
  # so we dynamically locate the compose files and fall back to multiplexed `docker logs` if needed.
  local -a compose_args=()
  local test_file=""
  local ca_file=""
  local couch_file=""

  # Find compose files (must be done outside subshell for array operations)
  cd "${TEST_NETWORK}" || exit 1
    # Known compose file names across fabric-samples versions
    for f in \
      docker/docker-compose-test-net.yaml docker/docker-compose-test-net.yml \
      compose/compose-test-net.yaml      compose/compose-test-net.yml \
      compose/docker-compose-test-net.yaml compose/docker-compose-test-net.yml \
      docker/compose-test-net.yaml       docker/compose-test-net.yml \
      compose-test-net.yaml              compose-test-net.yml \
      docker-compose-test-net.yaml       docker-compose-test-net.yml \
      docker-compose-test-net-2org.yaml  docker-compose-test-net-2org.yml
    do
      if [[ -f "$f" ]]; then test_file="$f"; break; fi
    done

    if [[ -n "$test_file" ]]; then
      compose_args+=( -f "$test_file" )
      local d
      d=$(dirname "$test_file")
      [[ "$d" == "." ]] && d=""

      for f in \
        "${d:+$d/}docker-compose-ca.yaml" "${d:+$d/}docker-compose-ca.yml" \
        "${d:+$d/}compose-ca.yaml"        "${d:+$d/}compose-ca.yml"
      do
        if [[ -f "$f" ]]; then ca_file="$f"; break; fi
      done
      [[ -n "$ca_file" ]] && compose_args+=( -f "$ca_file" )

      if [[ "${USE_COUCHDB}" == "1" ]]; then
        for f in \
          "${d:+$d/}docker-compose-couch.yaml" "${d:+$d/}docker-compose-couch.yml" \
          "${d:+$d/}compose-couch.yaml"        "${d:+$d/}compose-couch.yml"
        do
          if [[ -f "$f" ]]; then couch_file="$f"; break; fi
        done
        [[ -n "$couch_file" ]] && compose_args+=( -f "$couch_file" )
      fi
    fi
  cd - >/dev/null

  if (( ${#compose_args[@]} > 0 )); then
    if (cd "${TEST_NETWORK}" && docker compose "${compose_args[@]}" logs -f --tail=200); then
      return 0
    fi
    info "docker compose logs failed; falling back to multiplexed docker logs."
  fi

  info "Could not locate test-network compose files under: ${TEST_NETWORK}. Falling back to multiplexed docker logs."
  local -a containers=()
  local container_list
  container_list=$(docker ps --format '{{.Names}}' 2>/dev/null || echo "")
  while IFS= read -r name; do
    case "$name" in
      orderer.example.com|peer0.cascadiastate.example.com|peer0.chesapeakecanoe.example.com|ca_org1|ca_org2|ca_orderer|couchdb0|couchdb1)
        containers+=("$name")
        ;;
    esac
  done <<< "$container_list"

  if (( ${#containers[@]} == 0 )); then
    die "No Fabric containers found to tail. Run: ./lab.sh up"
  fi

  local -a pids=()
  cleanup_logs() {
    for pid in "${pids[@]}"; do
      kill "$pid" 2>/dev/null || true
    done
  }
  trap cleanup_logs INT TERM
  for c in "${containers[@]}"; do
    docker logs -f --tail=200 "$c" &
    pids+=("$!")
  done
  wait
}

watch_blocks() {
  info "Watching for new blocks on channel ${CHANNEL} (Ctrl+C to stop)..."

  # Check if network is running
  if ! orderer_container_running; then
    echo "[blocks] ERROR: Orderer container not running. Start the network first with: ./lab.sh up" >&2
    return 1
  fi

  echo "[blocks] Starting block height monitoring... (press Ctrl+C to stop)"
  local last_height=0
  while true; do
    # Use tools_exec_noninteractive to run the command in the container
    local out height
    out=$(tools_exec_noninteractive 1 "peer channel getinfo -c ${CHANNEL}" 2>/dev/null || echo "")
    height=$(echo "$out" | sed -n 's/.*"height":\([0-9]*\).*/\1/p' | head -n1)
    if [[ -z "$height" ]]; then
      height=$(echo "$out" | grep -o "height: [0-9]*" | cut -d" " -f2 | head -n1 || echo "")
    fi

    if [[ -z "$height" ]]; then
      #region agent log
      echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H2","location":"lab.sh:watch_blocks","message":"Empty block height","data":{"height":"'${height}'","out_len":'${#out}'},"timestamp":'$(date +%s%3N)'}' >> "${DEBUG_LOG_PATH}"
      #endregion
    sleep 2
    continue
  fi

    if [[ "$last_height" -eq 0 ]]; then
    last_height="$height"
      echo "[blocks] Current height: $height"
    elif [[ "$height" -gt "$last_height" ]]; then
      echo "[blocks] NEW BLOCK - Height: $height (was: $last_height)"
    last_height="$height"
  fi

  sleep 2
  done
}

watch_state() {
  info "Watching chaincode query output for changes (channel=${CHANNEL}, cc=${CC_NAME}) (Ctrl+C to stop)..."

  # Check if network is running
  if ! orderer_container_running; then
    echo "[state] ERROR: Orderer container not running. Start the network first with: ./lab.sh up" >&2
    return 1
  fi

  echo "[state] Starting chaincode state monitoring... (press Ctrl+C to stop)"
  local prev=""
  while true; do
    local cur
    cur=$(tools_exec_noninteractive 1 "payload='{\"Args\":[\"GetAllAssets\"]}'; peer chaincode query -C ${CHANNEL} -n ${CC_NAME} -c \"\${payload}\"" 2>/dev/null || echo "")
    local has_error="false"
    if echo "$cur" | grep -q "Error:"; then
      has_error="true"
    fi

    if [[ -n "$cur" ]] && [[ "$cur" != "$prev" ]]; then
      echo "[state] $(date +%H:%M:%S) State changed:"
    echo "$cur"
      echo "[state] ----"
    prev="$cur"
  fi

    if [[ -z "$cur" || "$has_error" == "true" ]]; then
      #region agent log
      echo '{"sessionId":"debug-session","runId":"initial","hypothesisId":"H3","location":"lab.sh:watch_state","message":"State query empty or error","data":{"cur_len":'${#cur}',"has_error":"'${has_error}'"},"timestamp":'$(date +%s%3N)'}' >> "${DEBUG_LOG_PATH}"
      #endregion
  fi

  sleep 2
  done
}

main() {
  local cmd="${1:-}"
  case "${cmd}" in
    ""|-h|--help) print_usage ;;
    doctor) doctor ;;
    status) status ;;
    bootstrap) bootstrap ;;
    prepare-build-assets) prepare_build_assets ;;
    ensure-tools) ensure_tools_container ;;
    up) up ;;
    health) health ;;
    invoke) shift; invoke_cmd "$@" ;;
    query) shift; query_cmd "$@" ;;
    deploy) deploy ;;
    down) down ;;
    reset) reset ;;
    enroll-students) fix_bind_mount_permissions; enroll_student_overlay ;;
    enter) shift || true; enter_org "${1:-}" ;;
    web-ui) launch_web_ui ;;
    watch) shift || true; case "${1:-}" in logs) watch_logs ;; blocks) watch_blocks ;; state) watch_state ;; *) die "watch expects logs|blocks|state" ;; esac ;;
    *) die "Unknown command: ${cmd}. Run ./lab.sh --help" ;;
  esac
}

main "$@"
