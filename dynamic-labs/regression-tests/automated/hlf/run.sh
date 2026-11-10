#!/usr/bin/env bash
# The HLF lab's live suite. Options and steps: ../run-lab.sh (run with --help).

LAB_CREDENTIALS=1
LAB_DOCKER_SOCKET=1
LAB_TEST_FILE=test_hlf_live.py
LAB_FRESH_START_HELP="Wipe HLF runtime state, rebuild its images and recreate the lab before running tests."
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"

CLEANUP_IMAGE="${HLF_REGRESSION_CLEANUP_IMAGE:-alpine:3.20}"

cleanup_runtime_dir() {
  # Keeps the tracked files (.gitkeep, install-fabric.sh); everything else
  # under hlf/runtime is generated or downloaded.
  echo "${LAB_TAG} removing generated HLF runtime state"
  docker run --rm \
    -v "${ROOT_DIR}/hlf/runtime:/runtime" \
    "${CLEANUP_IMAGE}" \
    sh -lc '
      find /runtime -mindepth 1 -maxdepth 1 ! -name .gitkeep ! -name install-fabric.sh \
        -exec rm -rf {} + 2>/dev/null || true
      touch /runtime/.gitkeep
    '
}

# Only the HLF lab is reset: the other labs keep running.
lab_fresh_start() {
  (
    cd "${ROOT_DIR}"
    bash ./lab-manager.sh stop hlf || true
  )

  (
    cd "${ROOT_DIR}/hlf"
    bash ./lab.sh down || true
    docker compose -p hlf -f docker-compose.yml down -v --remove-orphans || true
  )

  cleanup_runtime_dir

  # The cleanup removed the downloaded fabric-samples tree, so the start must
  # be allowed to fetch the pinned release again.
  (
    cd "${ROOT_DIR}"
    HLF_ALLOW_RUNTIME_DOWNLOADS="${HLF_ALLOW_RUNTIME_DOWNLOADS:-1}" bash ./lab-manager.sh build-images hlf
    HLF_ALLOW_RUNTIME_DOWNLOADS="${HLF_ALLOW_RUNTIME_DOWNLOADS:-1}" bash ./lab-manager.sh start hlf
  )
}

# lab-manager only warns when a Fabric image fails to build (an apt mirror outage did this on 9 Nov 2026), and the
# suite then waits out its timeouts on a network that never started. Stop here with the cause instead.
lab_before_suite() {
  # The student launcher builds nothing: its Fabric runner pulls the release's images and gives them these tags
  # while it starts (hlf/lab.sh use_release_helper_images), after the launcher has said "running". A missing tag
  # there means the start has not got that far, and the suite waits for the start itself.
  if [[ "${STUDENT_LAUNCHER}" == "1" ]]; then
    return 0
  fi
  # The network's startup log (lab.sh up, run by the runner) goes into this run's log, as the hlf-launcher suite's
  # does: a start that fails shows its cause, not only the "Startup failed with exit code 1" the suite reports
  # (Lab Tests run 42837342011). The followers are stopped on exit, or they would hold the log pipe open.
  trap 'pkill -f "exec hlf-hlf-runner-1 tail" 2>/dev/null; kill $(jobs -p) 2>/dev/null || true' EXIT
  docker exec hlf-hlf-runner-1 tail -n +1 -F /opt/hlf/runtime/lifecycle.log /opt/hlf/runtime/debug.log 2>&1 \
    | sed -u 's/^/[hlf-lifecycle] /' &
  local image missing=()
  for image in hlf-peer-ttyd:latest hlf-orderer-ttyd:latest chaincode-basic:latest; do
    docker image inspect "${image}" >/dev/null 2>&1 || missing+=("${image}")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "${LAB_TAG} Fabric images missing after the start: ${missing[*]}." >&2
    echo "${LAB_TAG} Their build failed; its output is above (look for 'Image build failed')." >&2
    exit 1
  fi
}

run_lab "$@"
