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

run_lab "$@"
