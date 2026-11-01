#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

RUNNER_IMAGE="${COINJOIN_TRACE_REGRESSION_RUNNER_IMAGE:-dynamic-labs-coinjoin-trace-regression:local}"
CONTAINER_BASE_URL="${COINJOIN_TRACE_REGRESSION_CONTAINER_BASE_URL:-http://router-router-1}"
HOST_BASE_URL="${COINJOIN_TRACE_REGRESSION_HOST_BASE_URL:-http://127.0.0.1}"

FRESH_START=0
SKIP_START=0
DIRECT_HOST=0
MATCH_PATTERN=""

usage() {
  cat <<'EOF'
Usage:
  regression-tests/automated/coinjoin-trace/run.sh [options]

Options:
  --fresh-start  Wipe runtime state and recreate the stack before running tests.
  --skip-start   Do not call lab-manager before running the suite.
  --direct-host  Run the unittest suite directly on the host instead of in the router-net runner container.
  --match TEXT   Run only tests whose unittest id/name contains TEXT.

Default behavior:
  - does not wipe the environment
  - non-destructively runs ./lab-manager.sh start coinjoin-trace
  - builds the regression runner image
  - runs the live suite in a container attached to router-net
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fresh-start)
      FRESH_START=1
      ;;
    --skip-start)
      SKIP_START=1
      ;;
    --direct-host)
      DIRECT_HOST=1
      ;;
    --match)
      if [[ $# -lt 2 ]]; then
        echo "--match requires an argument" >&2
        usage >&2
        exit 1
      fi
      MATCH_PATTERN="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

fresh_start() {
  echo "[coinjoin-trace-regression] performing optional fresh-start reset"
  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh stop all || true
  )

  local project
  for project in \
    router \
    course-site \
    instructor_auth_service \
    lane-service \
    bitcoin \
    consensus \
    cryptography \
    p2p_trust \
    ethereum_lab \
    exercises \
    explorer \
    wallet \
    bitcoin-trace \
    coinjoin-trace \
    tokens \
    dex \
    tron \
    quiz-engine-v2 \
    hlf
  do
    (
      cd "${ROOT_DIR}/${project}"
      docker compose down -v --remove-orphans || true
    )
  done

  find "${ROOT_DIR}/lane-service/runtime" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
  rm -rf "${ROOT_DIR}/.runtime"
  rm -f "${ROOT_DIR}/.lab-manager.env"

  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh deploy --mode instructor --no-tls --max-student-capacity 2
    bash ./lab-manager.sh start coinjoin-trace
  )
}

ensure_live_stack() {
  echo "[coinjoin-trace-regression] ensuring coinjoin-trace stack is running"
  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh start coinjoin-trace
  )
}

build_runner_image() {
  echo "[coinjoin-trace-regression] building runner image ${RUNNER_IMAGE}"
  docker build \
    --network "${DOCKER_BUILD_NETWORK:-default}" \
    -t "${RUNNER_IMAGE}" \
    -f "${SCRIPT_DIR}/runner.Dockerfile" \
    "${SCRIPT_DIR}"
}

run_in_container() {
  echo "[coinjoin-trace-regression] running suite in router-net attached container"
  local -a cmd=(python -m unittest discover -s regression-tests/automated/coinjoin-trace -p 'test_*.py' -v)
  if [[ -n "${MATCH_PATTERN}" ]]; then
    cmd+=(-k "${MATCH_PATTERN}")
  fi
  docker run --rm \
    --network router-net \
    -v "${ROOT_DIR}:/work" \
    -w /work \
    -e COINJOIN_TRACE_REGRESSION_BASE_URL="${CONTAINER_BASE_URL}" \
    "${RUNNER_IMAGE}" \
    "${cmd[@]}"
}

run_on_host() {
  echo "[coinjoin-trace-regression] running suite directly on host"
  local -a cmd=(python3 -m unittest discover -s regression-tests/automated/coinjoin-trace -p 'test_*.py' -v)
  if [[ -n "${MATCH_PATTERN}" ]]; then
    cmd+=(-k "${MATCH_PATTERN}")
  fi
  (
    cd "${ROOT_DIR}"
    COINJOIN_TRACE_REGRESSION_BASE_URL="${HOST_BASE_URL}" "${cmd[@]}"
  )
}

if [[ "${SKIP_START}" != "1" ]]; then
  if [[ "${FRESH_START}" == "1" ]]; then
    fresh_start
  else
    ensure_live_stack
  fi
fi

if [[ "${DIRECT_HOST}" == "1" ]]; then
  run_on_host
else
  build_runner_image
  run_in_container
fi
