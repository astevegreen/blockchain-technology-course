#!/usr/bin/env bash
# The steps every lab's live suite shares: options, starting the stack, the runner image and the suite run.
# Each lab's run.sh sets what differs, sources this file and calls run_lab "$@".
#
# Settings a run.sh may make before sourcing:
#   LAB_STACK             the lab-manager name, when it differs from the test folder's (quiz-engine-v2)
#   LAB_ENV_PREFIX        the prefix of the suite's settings, as in <PREFIX>_REGRESSION_BASE_URL
#                         (default: the folder name in capitals, - as _)
#   LAB_CREDENTIALS=1     give the suite the instructor credentials file
#   LAB_DOCKER_SOCKET=1   mount the Docker socket into the runner container
#   LAB_LANE=1            a lane-service lab: re-read .lab-manager.env before and after the start, pass the claim
#                         settings, and run --match through run_unittest_subset.py
#   LAB_TEST_FILE         run this one test file instead of discovering test_*.py
#   LAB_FRESH_START_HELP  the --fresh-start line of --help, for a lab with its own lab_fresh_start
#   LAB_START_NOTE        a note after the start command in --help
# Functions a run.sh may define after sourcing:
#   lab_fresh_start       replaces the default fresh start (stop every lab, wipe every project, redeploy)
#   lab_before_suite      runs once the stack is up, before the suite (also with --skip-start)

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[1]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
LAB_NAME="$(basename -- "${SCRIPT_DIR}")"
LAB_STACK="${LAB_STACK:-${LAB_NAME}}"
LAB_ENV_PREFIX="${LAB_ENV_PREFIX:-$(tr 'a-z-' 'A-Z_' <<<"${LAB_NAME}")}"
LAB_SLUG="$(tr 'A-Z_' 'a-z-' <<<"${LAB_ENV_PREFIX}")"
LAB_TAG="[${LAB_SLUG}-regression]"
LAB_CREDENTIALS="${LAB_CREDENTIALS:-0}"
LAB_DOCKER_SOCKET="${LAB_DOCKER_SOCKET:-0}"
LAB_LANE="${LAB_LANE:-0}"
LAB_TEST_FILE="${LAB_TEST_FILE:-}"
DEFAULT_FRESH_START_HELP="Wipe runtime state, rebuild the lab's images and recreate the stack before running tests."
LAB_FRESH_START_HELP="${LAB_FRESH_START_HELP:-${DEFAULT_FRESH_START_HELP}}"
LAB_START_NOTE="${LAB_START_NOTE:+ ${LAB_START_NOTE}}"

# Every compose project the default fresh start takes down, volumes and all.
LAB_PROJECTS=(
  router course-site instructor_auth_service lane-service bitcoin consensus cryptography
  exercises explorer wallet bitcoin-trace coinjoin-trace hide-and-trace tokens dex tron cross-chain final-trace quiz-engine-v2 hlf
)

FRESH_START=0
SKIP_START=0
# 1 when --skip-start finds the student launcher's own stack: see student_launcher_running.
STUDENT_LAUNCHER=0
DIRECT_HOST=0
MATCH_PATTERN=""

reload_lab_manager_env() {
  if [[ -f "${ROOT_DIR}/.lab-manager.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.lab-manager.env"
    set +a
  fi
}

# The student launcher's own stack (student-launcher/, started by its wrapper) is running: its control container
# is up and the router carries the course.release label, which only the launcher's compose files set. That stack
# has no instructor pages, no lab-manager files and no local image tags, so with --skip-start the suite gets
# LAB_REGRESSION_STUDENT_LAUNCHER=1 (live_common.STUDENT_LAUNCHER) and skips what the launcher leaves out. The
# classroom stack, and the launcher passes that swap one lab under the classroom router (launcher-stack.sh,
# hlf-launcher), never match.
student_launcher_running() {
  local release
  [[ "$(docker inspect -f '{{.State.Running}}' course-launcher 2>/dev/null)" == "true" ]] || return 1
  release="$(docker inspect -f '{{index .Config.Labels "course.release"}}' router-router-1 2>/dev/null)" || return 1
  [[ -n "${release}" ]]
}

# A setting of this lab's suite, read from the environment: lab_setting REGRESSION_RUNNER_IMAGE <default>.
lab_setting() {
  local name="${LAB_ENV_PREFIX}_$1"
  printf '%s' "${!name:-$2}"
}

usage() {
  cat <<EOF
Usage:
  regression-tests/automated/${LAB_NAME}/run.sh [options]

Options:
  --fresh-start  ${LAB_FRESH_START_HELP}
  --skip-start   Do not call lab-manager before running the suite.
  --direct-host  Run the unittest suite directly on the host instead of in the router-net runner container.
  --match TEXT   Run only tests whose unittest id/name contains TEXT.

Default behavior:
  - does not wipe the environment
  - non-destructively runs ./lab-manager.sh start ${LAB_STACK}${LAB_START_NOTE}
  - builds the regression runner image
  - runs the live suite in a container attached to router-net
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --fresh-start) FRESH_START=1 ;;
      --skip-start) SKIP_START=1 ;;
      --direct-host) DIRECT_HOST=1 ;;
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
}

lab_fresh_start() {
  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh stop all || true
  )

  local project
  for project in "${LAB_PROJECTS[@]}"; do
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
    bash ./lab-manager.sh build-images "${LAB_STACK}"
    bash ./lab-manager.sh start "${LAB_STACK}"
  )
}

lab_before_suite() { :; }

ensure_live_stack() {
  echo "${LAB_TAG} ensuring ${LAB_NAME} stack is running"
  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh start "${LAB_STACK}"
  )
}

build_runner_image() {
  echo "${LAB_TAG} building runner image ${RUNNER_IMAGE}"
  docker build \
    --network "${DOCKER_BUILD_NETWORK:-default}" \
    -t "${RUNNER_IMAGE}" \
    -f "${SCRIPT_DIR}/runner.Dockerfile" \
    "${SCRIPT_DIR}"
}

# The suite's command, for the given python (python in the runner image, python3 on the host), into SUITE_CMD.
suite_command() {
  local py="$1" test_dir="regression-tests/automated/${LAB_NAME}"
  if [[ -n "${LAB_TEST_FILE}" ]]; then
    SUITE_CMD=("${py}" "${test_dir}/${LAB_TEST_FILE}" -v)
  elif [[ "${LAB_LANE}" == "1" && -n "${MATCH_PATTERN}" ]]; then
    SUITE_CMD=(
      "${py}" regression-tests/infrastructure/run_unittest_subset.py
      --start-dir "${test_dir}"
      --pattern 'test_*.py'
      --match "${MATCH_PATTERN}"
      -v 2
    )
    return
  else
    SUITE_CMD=("${py}" -m unittest discover -s "${test_dir}" -p 'test_*.py' -v)
  fi
  if [[ -n "${MATCH_PATTERN}" ]]; then
    SUITE_CMD+=(-k "${MATCH_PATTERN}")
  fi
}

# The suite's settings as NAME=value lines into SUITE_ENV, with the credentials file under the given root.
suite_env() {
  local base_url="$1" root="$2" p="${LAB_ENV_PREFIX}"
  SUITE_ENV=("${p}_REGRESSION_BASE_URL=${base_url}")
  if [[ "${LAB_CREDENTIALS}" == "1" ]]; then
    SUITE_ENV+=("${p}_REGRESSION_CREDENTIALS_FILE=${root}/.runtime/instructor-credentials.txt")
  fi
  if [[ "${LAB_LANE}" == "1" ]]; then
    SUITE_ENV+=(
      "${p}_REGRESSION_RELEASE_EXISTING_CLAIMS=$(lab_setting REGRESSION_RELEASE_EXISTING_CLAIMS 1)"
      "${p}_STUDENT_HOME_ROOT=$(lab_setting STUDENT_HOME_ROOT '')"
    )
  fi
  if [[ "${STUDENT_LAUNCHER}" == "1" ]]; then
    SUITE_ENV+=("LAB_REGRESSION_STUDENT_LAUNCHER=1")
  fi
}

run_in_container() {
  echo "${LAB_TAG} running suite in router-net attached container"
  suite_command python
  suite_env "${CONTAINER_BASE_URL}" /work
  local -a args=(--rm --network router-net -v "${ROOT_DIR}:/work" -w /work)
  if [[ "${LAB_DOCKER_SOCKET}" == "1" ]]; then
    args+=(-v /var/run/docker.sock:/var/run/docker.sock)
  fi
  local setting
  for setting in "${SUITE_ENV[@]}"; do
    args+=(-e "${setting}")
  done
  docker run "${args[@]}" "${RUNNER_IMAGE}" "${SUITE_CMD[@]}"
}

run_on_host() {
  echo "${LAB_TAG} running suite directly on host"
  suite_command python3
  suite_env "${HOST_BASE_URL}" "${ROOT_DIR}"
  (
    cd "${ROOT_DIR}"
    env "${SUITE_ENV[@]}" "${SUITE_CMD[@]}"
  )
}

run_lab() {
  if [[ "${LAB_LANE}" == "1" ]]; then
    reload_lab_manager_env
  fi
  RUNNER_IMAGE="$(lab_setting REGRESSION_RUNNER_IMAGE "dynamic-labs-${LAB_SLUG}-regression:local")"
  CONTAINER_BASE_URL="$(lab_setting REGRESSION_CONTAINER_BASE_URL http://router-router-1)"
  HOST_BASE_URL="$(lab_setting REGRESSION_HOST_BASE_URL http://127.0.0.1)"

  parse_args "$@"

  if [[ "${SKIP_START}" == "1" ]] && student_launcher_running; then
    STUDENT_LAUNCHER=1
    echo "${LAB_TAG} the student launcher's stack is running: instructor-only tests are skipped"
  fi

  if [[ "${SKIP_START}" != "1" ]]; then
    if [[ "${FRESH_START}" == "1" ]]; then
      echo "${LAB_TAG} performing optional fresh-start reset"
      lab_fresh_start
    else
      ensure_live_stack
    fi
  fi

  if [[ "${LAB_LANE}" == "1" ]]; then
    reload_lab_manager_env
  fi
  lab_before_suite

  if [[ "${DIRECT_HOST}" == "1" ]]; then
    run_on_host
  else
    build_runner_image
    run_in_container
  fi
}
