#!/usr/bin/env bash
# The HLF live suite against the student launcher stack (hlf/docker-compose.launcher.yml) instead of the
# classroom one: the runtime lives in the hlf-runtime volume and no host path reaches Docker. It runs the
# hlf suite's own tests (../hlf/test_hlf_live.py) with HLF_REGRESSION_LAUNCHER=1. Options: ../run-lab.sh.

LAB_STACK=hlf
LAB_ENV_PREFIX=HLF
LAB_CREDENTIALS=1
LAB_DOCKER_SOCKET=1
LAB_TEST_FILE=../hlf/test_hlf_live.py
LAB_FRESH_START_HELP="Wipe every lab and the hlf-runtime volume, redeploy the shared stack, build the launcher image and start the launcher stack."
LAB_START_NOTE="(the launcher stack, not lab-manager's)"
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"

LAUNCHER_IMAGE="${HLF_LAUNCHER_IMAGE:-hlf-launcher:local}"

launcher_compose() {
  (
    cd "${ROOT_DIR}/hlf"
    HLF_HLF_IMAGE="${LAUNCHER_IMAGE}" HLF_HLF_RUNNER_IMAGE="${LAUNCHER_IMAGE}" COURSE_RELEASE=regression \
      docker compose -p hlf --env-file "${ROOT_DIR}/.runtime/runtime-secrets.env" \
        -f docker-compose.launcher.yml "$@"
  )
}

build_launcher_image() {
  echo "${LAB_TAG} building ${LAUNCHER_IMAGE} from hlf/Dockerfile.launcher"
  docker build --network "${DOCKER_BUILD_NETWORK:-default}" -t "${LAUNCHER_IMAGE}" \
    -f "${ROOT_DIR}/hlf/Dockerfile.launcher" "${ROOT_DIR}/hlf"
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
  docker volume rm -f hlf-runtime >/dev/null 2>&1 || true
  rm -rf "${ROOT_DIR}/.runtime"
  rm -f "${ROOT_DIR}/.lab-manager.env"

  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh deploy --mode instructor --no-tls --max-student-capacity 2
  )
  build_launcher_image
  launcher_compose up -d
}

ensure_live_stack() {
  echo "${LAB_TAG} ensuring the HLF launcher stack is running"
  docker image inspect "${LAUNCHER_IMAGE}" >/dev/null 2>&1 || build_launcher_image
  launcher_compose up -d
}

lab_before_suite() {
  # The launcher stack must never fall back to a host path: no bind mount but the Docker socket.
  local binds
  binds="$(docker inspect hlf-hlf-runner-1 hlf-hlf-1 \
    --format '{{range .Mounts}}{{if eq .Type "bind"}}{{.Source}} {{end}}{{end}}')"
  binds="$(tr ' ' '\n' <<<"${binds}" | grep -v '^$' | grep -vx '/var/run/docker.sock' || true)"
  if [[ -n "${binds}" ]]; then
    echo "${LAB_TAG} the launcher stack bind-mounts host paths: ${binds}" >&2
    exit 1
  fi
  # The runner's output (lab.sh's startup) goes into this run's log, so a stalled start shows its cause.
  # The followers are stopped on exit, or they would hold the log pipe open after the suite ends.
  trap 'pkill -f "logs -f hlf-hlf-runner-1|exec hlf-hlf-runner-1 tail" 2>/dev/null; kill $(jobs -p) 2>/dev/null || true' EXIT
  docker logs -f hlf-hlf-runner-1 2>&1 | sed -u 's/^/[hlf-runner] /' &
  docker exec hlf-hlf-runner-1 tail -n +1 -F /opt/hlf/runtime/lifecycle.log /opt/hlf/runtime/debug.log 2>&1 \
    | sed -u 's/^/[hlf-lifecycle] /' &
}

# The hlf suite's runner image, and its settings plus the launcher flag.
build_runner_image() {
  echo "${LAB_TAG} building runner image ${RUNNER_IMAGE}"
  docker build --network "${DOCKER_BUILD_NETWORK:-default}" -t "${RUNNER_IMAGE}" \
    -f "${SCRIPT_DIR}/../hlf/runner.Dockerfile" "${SCRIPT_DIR}/../hlf"
}
eval "$(declare -f suite_env | sed '1s/^suite_env/_shared_suite_env/')"
suite_env() {
  _shared_suite_env "$@"
  SUITE_ENV+=("HLF_REGRESSION_LAUNCHER=1")
}

run_lab "$@"
