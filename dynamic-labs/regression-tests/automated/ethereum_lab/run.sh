#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

reload_lab_manager_env() {
  if [[ -f "${ROOT_DIR}/.lab-manager.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.lab-manager.env"
    set +a
  fi
}

reload_lab_manager_env

RUNNER_IMAGE="${ETHEREUM_REGRESSION_RUNNER_IMAGE:-dynamic-labs-ethereum-regression:local}"
CONTAINER_BASE_URL="${ETHEREUM_REGRESSION_CONTAINER_BASE_URL:-http://router-router-1}"
HOST_BASE_URL="${ETHEREUM_REGRESSION_HOST_BASE_URL:-http://127.0.0.1}"

FRESH_START=0
SKIP_START=0
DIRECT_HOST=0
MATCH_PATTERN=""

usage() {
  cat <<'EOF'
Usage:
  regression-tests/automated/ethereum_lab/run.sh [options]

Options:
  --fresh-start  Wipe runtime state and recreate the stack before running tests.
  --skip-start   Do not call lab-manager before running the suite.
  --direct-host  Run the unittest suite directly on the host instead of in the router-net runner container.
  --match TEXT   Run only tests whose unittest id/name contains TEXT.

Default behavior:
  - does not wipe the environment
  - non-destructively runs ./lab-manager.sh start ethereum_lab
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
  echo "[ethereum-regression] performing optional fresh-start reset"
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
    wallet \
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
    bash ./lab-manager.sh start ethereum_lab
  )
}

ensure_live_stack() {
  echo "[ethereum-regression] ensuring ethereum_lab stack is running"
  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh start ethereum_lab
  )
}

build_runner_image() {
  echo "[ethereum-regression] building runner image ${RUNNER_IMAGE}"
  docker build \
    --network "${DOCKER_BUILD_NETWORK:-default}" \
    -t "${RUNNER_IMAGE}" \
    -f "${SCRIPT_DIR}/runner.Dockerfile" \
    "${SCRIPT_DIR}"
}

run_in_container() {
  echo "[ethereum-regression] running suite in router-net attached container"
  local -a cmd
  if [[ -n "${MATCH_PATTERN}" ]]; then
    cmd=(
      python regression-tests/infrastructure/run_unittest_subset.py
      --start-dir regression-tests/automated/ethereum_lab
      --pattern 'test_*.py'
      --match "${MATCH_PATTERN}"
      -v 2
    )
  else
    cmd=(python -m unittest discover -s regression-tests/automated/ethereum_lab -p 'test_*.py' -v)
  fi
  docker run --rm \
    --network router-net \
    -v "${ROOT_DIR}:/work" \
    -w /work \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e ETHEREUM_REGRESSION_BASE_URL="${CONTAINER_BASE_URL}" \
    -e ETHEREUM_REGRESSION_CREDENTIALS_FILE="/work/.runtime/instructor-credentials.txt" \
    -e ETHEREUM_REGRESSION_RELEASE_EXISTING_CLAIMS="${ETHEREUM_REGRESSION_RELEASE_EXISTING_CLAIMS:-1}" \
    -e ETHEREUM_STUDENT_HOME_ROOT="${ETHEREUM_STUDENT_HOME_ROOT:-}" \
    "${RUNNER_IMAGE}" \
    "${cmd[@]}"
}

run_on_host() {
  echo "[ethereum-regression] running suite directly on host"
  local -a cmd
  if [[ -n "${MATCH_PATTERN}" ]]; then
    cmd=(
      python3 regression-tests/infrastructure/run_unittest_subset.py
      --start-dir regression-tests/automated/ethereum_lab
      --pattern 'test_*.py'
      --match "${MATCH_PATTERN}"
      -v 2
    )
  else
    cmd=(python3 -m unittest discover -s regression-tests/automated/ethereum_lab -p 'test_*.py' -v)
  fi
  (
    cd "${ROOT_DIR}"
    ETHEREUM_REGRESSION_BASE_URL="${HOST_BASE_URL}" \
    ETHEREUM_REGRESSION_CREDENTIALS_FILE="${ROOT_DIR}/.runtime/instructor-credentials.txt" \
    ETHEREUM_REGRESSION_RELEASE_EXISTING_CLAIMS="${ETHEREUM_REGRESSION_RELEASE_EXISTING_CLAIMS:-1}" \
    ETHEREUM_STUDENT_HOME_ROOT="${ETHEREUM_STUDENT_HOME_ROOT:-}" \
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

reload_lab_manager_env

if [[ "${DIRECT_HOST}" == "1" ]]; then
  run_on_host
else
  build_runner_image
  run_in_container
fi
