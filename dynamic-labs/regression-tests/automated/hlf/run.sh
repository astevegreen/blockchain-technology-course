#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

RUNNER_IMAGE="${HLF_REGRESSION_RUNNER_IMAGE:-dynamic-labs-hlf-regression:local}"
CONTAINER_BASE_URL="${HLF_REGRESSION_CONTAINER_BASE_URL:-http://router-router-1}"
HOST_BASE_URL="${HLF_REGRESSION_HOST_BASE_URL:-http://127.0.0.1}"
CLEANUP_IMAGE="${HLF_REGRESSION_CLEANUP_IMAGE:-alpine:3.20}"

FRESH_START=0
SKIP_START=0
DIRECT_HOST=0
MATCH_PATTERN=""

usage() {
  cat <<'EOF'
Usage:
  regression-tests/automated/hlf/run.sh [options]

Options:
  --fresh-start  Wipe HLF runtime state and recreate the lab before running tests.
  --skip-start   Do not call lab-manager before running the suite.
  --direct-host  Run the unittest suite directly on the host instead of in the router-net runner container.
  --match TEXT   Run only tests whose unittest id/name contains TEXT.

Default behavior:
  - does not wipe the environment
  - non-destructively runs ./lab-manager.sh start hlf
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

cleanup_runtime_dir() {
  echo "[hlf-regression] removing generated HLF runtime state"
  docker run --rm \
    -v "${ROOT_DIR}/hlf/runtime:/runtime" \
    "${CLEANUP_IMAGE}" \
    sh -lc '
      find /runtime -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
      touch /runtime/.gitkeep
    '
}

fresh_start() {
  echo "[hlf-regression] performing optional fresh-start reset"
  (
    cd "${ROOT_DIR}"
    ./lab-manager.sh stop hlf || true
  )

  (
    cd "${ROOT_DIR}/hlf"
    bash ./lab.sh down || true
    docker compose -p hlf -f docker-compose.yml down -v --remove-orphans || true
  )

  cleanup_runtime_dir

  (
    cd "${ROOT_DIR}"
    ./lab-manager.sh start hlf
  )
}

ensure_live_stack() {
  echo "[hlf-regression] ensuring hlf stack is running"
  (
    cd "${ROOT_DIR}"
    ./lab-manager.sh start hlf
  )
}

build_runner_image() {
  echo "[hlf-regression] building runner image ${RUNNER_IMAGE}"
  docker build \
    --network "${DOCKER_BUILD_NETWORK:-bridge}" \
    -t "${RUNNER_IMAGE}" \
    -f "${SCRIPT_DIR}/runner.Dockerfile" \
    "${SCRIPT_DIR}"
}

run_in_container() {
  echo "[hlf-regression] running suite in router-net attached container"
  local test_dir="regression-tests/automated/hlf"
  local -a cmd=(python "${test_dir}/test_hlf_live.py" -v)
  if [[ -n "${MATCH_PATTERN}" ]]; then
    cmd+=(-k "${MATCH_PATTERN}")
  fi
  docker run --rm \
    --network router-net \
    -v "${ROOT_DIR}:/work" \
    -w /work \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e HLF_REGRESSION_BASE_URL="${CONTAINER_BASE_URL}" \
    -e HLF_REGRESSION_CREDENTIALS_FILE="/work/.runtime/instructor-credentials.txt" \
    "${RUNNER_IMAGE}" \
    "${cmd[@]}"
}

run_on_host() {
  echo "[hlf-regression] running suite directly on host"
  local test_dir="regression-tests/automated/hlf"
  local -a cmd=(python3 "${test_dir}/test_hlf_live.py" -v)
  if [[ -n "${MATCH_PATTERN}" ]]; then
    cmd+=(-k "${MATCH_PATTERN}")
  fi
  (
    cd "${ROOT_DIR}"
    HLF_REGRESSION_BASE_URL="${HOST_BASE_URL}" \
    HLF_REGRESSION_CREDENTIALS_FILE="${ROOT_DIR}/.runtime/instructor-credentials.txt" \
    "${cmd[@]}"
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
