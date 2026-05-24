#!/usr/bin/env bash
# Phase 7 hybrid student overlay enroller.
#
# Assumes the 4-org consortium (+ Meridian Org5) is already up (brought
# up by lab.sh up → start_runtime_network_containers) and that the
# channel has been created with Student01..StudentNN as channel members
# (configtx-4org-students.yaml wired into lab.sh).
#
# What this script does:
#   1. Stages compose-students.yaml (idempotent).
#   2. For each configured student NN, briefly brings peer0.studentNN up,
#      joins the peer to the channel, installs the committed chaincode,
#      then stops the peer. Idempotent: already-joined / already-installed
#      peers are skipped.
#   3. Leaves all student peers STOPPED (cold rack). Lane manager owns
#      start/stop per-claim.
#
# Students are channel members but NOT endorsers — chaincode commit is
# already committed by lab.sh's deploy path with endorsement policy
# OutOf(3, Org1MSP.peer, Org2MSP.peer, Org3MSP.peer, Org4MSP.peer).
# Installing chaincode on student peers is needed so students can
# simulate/query locally; they just can't be part of the endorsement set.
#
# Required environment (set by lab.sh::enroll_student_overlay):
#   TEST_NETWORK                absolute path to fabric-samples/test-network
#   HOST_TEST_NETWORK           host-side path to fabric-samples/test-network
#                               (may equal TEST_NETWORK when running on host;
#                               differs when invoked from inside hlf-runner)
#   HOST_FABRIC_SAMPLES_PATH    docker mount source for above
#   IMAGE_TAG                   fabric version, e.g. 2.5.15
#   PLATFORM                    e.g. linux/amd64
#   CHANNEL                     channel name (default: diplomas)
#   CC_NAME, CC_VERSION, CC_SEQ chaincode lifecycle params
#   MANAGED_RUNTIME_DIR         path to dynamic-labs/hlf/managed_runtime

set -euo pipefail

: "${TEST_NETWORK:?}"
: "${HOST_TEST_NETWORK:=${TEST_NETWORK}}"
: "${HOST_FABRIC_SAMPLES_PATH:?}"
: "${IMAGE_TAG:?}"
if [[ -z "${PLATFORM:-}" ]]; then
  case "$(uname -m)" in
    x86_64) PLATFORM="linux/amd64" ;;
    aarch64|arm64) PLATFORM="linux/arm64" ;;
    *) PLATFORM="linux/amd64" ;;
  esac
fi
: "${TOOLS_PLATFORM:=${PLATFORM}}"
: "${CHANNEL:=diplomas}"
: "${CC_NAME:=basic}"
: "${CC_VERSION:=1.0}"
: "${CC_SEQ:=1}"
: "${MANAGED_RUNTIME_DIR:?}"

STUDENT_COUNT="${STUDENT_COUNT:-${HLF_STUDENT_COUNT:-${MAX_STUDENT_CAPACITY:-20}}}"

log() { printf '[student-overlay] %s\n' "$*" >&2; }
die() { printf '[student-overlay] ERROR: %s\n' "$*" >&2; exit 1; }

tools_run() {
  docker run --rm --platform "${TOOLS_PLATFORM}" \
    --network fabric_test \
    -v "${HOST_FABRIC_SAMPLES_PATH}:/fabric-samples" \
    -w /fabric-samples/test-network \
    "hyperledger/fabric-tools:${IMAGE_TAG}" \
    bash -lc "$*"
}

stage_compose_students() {
  log "Regenerating student overlay artifacts"
  python3 "${MANAGED_RUNTIME_DIR}/generate_student_overlay.py" --out "${MANAGED_RUNTIME_DIR}" >/dev/null
  mkdir -p "${TEST_NETWORK}/compose"
  cp -f "${MANAGED_RUNTIME_DIR}/compose-students.yaml" \
        "${TEST_NETWORK}/compose/compose-students.yaml"
}

compose_students() {
  # cd to the *host* path so docker compose embeds host-resolvable project
  # labels — otherwise the daemon can't resolve relative bind mounts like
  # ./docker/peercfg (they'd look for the runner-internal /opt/hlf/... view
  # on the host, which is not the same directory).
  (
    cd "${HOST_TEST_NETWORK}"
    docker compose -p hlf-students -f compose/compose-students.yaml "$@"
  )
}

_tcp_ready() {
  # usage: _tcp_ready <container> <port>
  docker exec "$1" bash -c "exec 3<>/dev/tcp/127.0.0.1/$2 && exec 3<&- 3>&-" >/dev/null 2>&1
}

wait_for_peer() {
  local container="$1" max="${2:-45}"
  local i=0
  while (( i < max )); do
    if _tcp_ready "${container}" 7051; then return 0; fi
    sleep 1
    i=$((i+1))
  done
  die "Timed out waiting for ${container}:7051"
}

peer_env_block_student() {
  local n="$1"
  local tn=/fabric-samples/test-network
  cat <<ENV
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=Student${n}MSP
export CORE_PEER_TLS_ROOTCERT_FILE=${tn}/organizations/peerOrganizations/student${n}.example.com/peers/peer0.student${n}.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${tn}/organizations/peerOrganizations/student${n}.example.com/users/Admin@student${n}.example.com/msp
export CORE_PEER_ADDRESS=peer0.student${n}.example.com:7051
ENV
}

start_student_peer() {
  local n="$1"
  compose_students --profile "s${n}" up -d "peer0.student${n}.example.com" >/dev/null
  wait_for_peer "peer0.student${n}.example.com"
}

stop_student_peer() {
  local n="$1"
  compose_students stop "peer0.student${n}.example.com" >/dev/null
}

STAMP_DIR="${TEST_NETWORK}/student-overlay"

stamp_path() {
  local n="$1"
  printf '%s/enrolled-student%s-%s-%s-%s.stamp' \
    "${STAMP_DIR}" "${n}" "${CHANNEL}" "${CC_NAME}" "${CC_VERSION}"
}

enroll_one_student() {
  local n="$1"
  local container="peer0.student${n}.example.com"
  local stamp
  stamp="$(stamp_path "${n}")"

  # Fast-skip: stamp encodes (channel, chaincode name+version) so a
  # rename or chaincode upgrade re-triggers enrollment automatically.
  if [[ -f "${stamp}" ]]; then
    return 0
  fi

  start_student_peer "${n}"

  local env_block
  env_block="$(peer_env_block_student "${n}")"

  # Join + verify. Bootstrap previously stamped the student as enrolled even
  # when the join tools_run returned non-zero, because the stamp is what
  # drives fast-skip on re-runs. That produced false-positive stamps whose
  # peers came up without the channel. Now we:
  #   1. run the join (idempotent via pre-check of `peer channel list`)
  #   2. re-query `peer channel list` and require the channel to appear
  #   3. return non-zero on failure so main()'s handler fires and no stamp
  #      is written.
  # Step 2 is not redundant with step 1: `peer channel join` submits a
  # proposal and returns 0 before the peer has necessarily committed the
  # block, so a race under orderer contention can look successful but
  # leave the peer unjoined. Verifying in a second CLI invocation catches
  # that class of silent failure.
  if ! tools_run "
set -e
${env_block}
if peer channel list 2>/dev/null | grep -q '^${CHANNEL}$'; then
  echo 'already-joined'
  exit 0
else
  peer channel join -b /fabric-samples/test-network/channel-artifacts/${CHANNEL}.block
fi
# Verify: the peer must now list the channel. Retry briefly to absorb the
# commit latency after the join proposal.
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if peer channel list 2>/dev/null | grep -q '^${CHANNEL}$'; then
    echo 'join-verified'
    exit 0
  fi
  sleep 1
done
echo 'join-verify-failed' >&2
exit 1
" 2>&1 | tee /dev/stderr | grep -q 'join-verified\|already-joined'; then
    log "ERROR student${n}: channel join did not verify — NOT stamping (will retry on next run)"
    return 1
  fi

  # Idempotent CaaS chaincode install. The package contains only a
  # connection.json pointing at the shared chaincode-basic container.
  tools_run "
set -e
${env_block}
PKG_FILE=/tmp/${CC_NAME}_${CC_VERSION}.tar.gz
if peer lifecycle chaincode queryinstalled 2>/dev/null | grep -q '${CC_NAME}_${CC_VERSION}'; then
  echo 'chaincode already installed on student${n}'
else
  if [ ! -f \$PKG_FILE ]; then
    mkdir -p /tmp/ccaas-pkg
    echo '{\"address\":\"chaincode-basic:7052\",\"dial_timeout\":\"10s\",\"tls_required\":false}' > /tmp/ccaas-pkg/connection.json
    tar czf /tmp/ccaas-pkg/code.tar.gz -C /tmp/ccaas-pkg connection.json
    echo '{\"type\":\"ccaas\",\"label\":\"${CC_NAME}_${CC_VERSION}\"}' > /tmp/ccaas-pkg/metadata.json
    tar czf \$PKG_FILE -C /tmp/ccaas-pkg metadata.json code.tar.gz
    rm -rf /tmp/ccaas-pkg
  fi
  peer lifecycle chaincode install \$PKG_FILE
fi
"

  stop_student_peer "${n}"
  mkdir -p "${STAMP_DIR}"
  touch "${stamp}"
}

main() {
  stage_compose_students
  mkdir -p "${STAMP_DIR:-${TEST_NETWORK}/student-overlay}"
  log "Enrolling ${STUDENT_COUNT} students into channel '${CHANNEL}'"
  for n in $(seq -w 01 "${STUDENT_COUNT}"); do
    log "  student${n}"
    if ! enroll_one_student "${n}"; then
      log "WARN student${n}: enrollment failed — leaving peer stopped"
      # Best effort stop in case start_student_peer ran but enrollment died.
      stop_student_peer "${n}" 2>/dev/null || true
    fi
  done
  log "Overlay enrollment complete. Student rack is cold (all peers stopped)."
}

main "$@"
