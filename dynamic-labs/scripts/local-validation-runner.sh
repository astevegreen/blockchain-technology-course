#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DYNAMIC_LABS_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd -- "${DYNAMIC_LABS_DIR}/.." && pwd)"

VALIDATION_CONTAINER_IMAGE="${VALIDATION_CONTAINER_IMAGE:-dynamic-labs-validation:local}"
VALIDATION_CONTAINER_DOCKERFILE="${VALIDATION_CONTAINER_DOCKERFILE:-${SCRIPT_DIR}/validation-container.Dockerfile}"
VALIDATION_CONTAINER_BUILD_CONTEXT="${VALIDATION_CONTAINER_BUILD_CONTEXT:-${SCRIPT_DIR}}"
BITCOIN_LAB_IMAGE="${BITCOIN_LAB_IMAGE:-ghcr.io/bja2142/bitcoin-lab:latest}"
BITCOIN_MEMPOOL_IMAGE="${BITCOIN_MEMPOOL_IMAGE:-ghcr.io/bja2142/bitcoin-mempool:latest}"
HLF_IMAGE_TAG="${HLF_IMAGE_TAG:-2.5.15}"
HLF_CA_IMAGE_TAG="${HLF_CA_IMAGE_TAG:-1.5.17}"
HLF_NODEENV_IMAGE_TAG="${HLF_NODEENV_IMAGE_TAG:-2.5}"
HLF_COUCHDB_IMAGE="${HLF_COUCHDB_IMAGE:-couchdb:3.4.2}"
HLF_FABRIC_SAMPLES_REF="${HLF_FABRIC_SAMPLES_REF:-bf7e75c6c159dc1959f3bb8979ed739171673b4d}"
BUNDLE_PRUNE_AFTER_SAVE="${BUNDLE_PRUNE_AFTER_SAVE:-0}"
VALIDATION_REFRESH_GHCR="${VALIDATION_REFRESH_GHCR:-0}"

log() {
  printf '[validation] %s\n' "$*"
}

usage() {
  cat <<'EOF'
Usage:
  scripts/local-validation-runner.sh build-image
  scripts/local-validation-runner.sh shell
  scripts/local-validation-runner.sh refresh-ghcr
  scripts/local-validation-runner.sh phase0
  scripts/local-validation-runner.sh phase1
  scripts/local-validation-runner.sh phase2
  scripts/local-validation-runner.sh phase3
  scripts/local-validation-runner.sh phase4
  scripts/local-validation-runner.sh all

Notes:
  - Run this from the host. It launches a repo-owned validation container automatically.
  - The default image is built locally from scripts/validation-container.Dockerfile.
  - Validation phases execute inside the container with /var/run/docker.sock mounted.
  - Set VALIDATION_REFRESH_GHCR=1 to force-refresh bitcoin GHCR images before
    phase2/phase4. This matters because prepare-docker-image-bundles.sh only
    pulls those images when they are absent locally.
  - Set BUNDLE_PRUNE_AFTER_SAVE=1 if you want local validation to match CI's
    aggressive image/builder cleanup behavior.
EOF
}

require_host_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf 'Missing required host command: %s\n' "$cmd" >&2
    exit 1
  fi
}

have_container_command() {
  command -v "$1" >/dev/null 2>&1
}

have_docker_compose() {
  docker compose version >/dev/null 2>&1
}

have_python_yaml() {
  python3 - <<'PY' >/dev/null 2>&1
import yaml
PY
}

ensure_basic_dependencies() {
  local missing=()

  have_container_command bash || missing+=("bash")
  have_container_command python3 || missing+=("python3")
  have_python_yaml || missing+=("python3 yaml")

  if [ "${#missing[@]}" -eq 0 ]; then
    return 0
  fi

  printf 'Missing container tools: %s\n' "${missing[*]}" >&2
  exit 1
}

ensure_docker_dependencies() {
  local missing=()

  ensure_basic_dependencies
  have_container_command curl || missing+=("curl")
  have_container_command git || missing+=("git")
  have_container_command docker || missing+=("docker")
  have_docker_compose || missing+=("docker compose")

  if [ "${#missing[@]}" -eq 0 ]; then
    return 0
  fi

  printf 'Missing container tools: %s\n' "${missing[*]}" >&2
  exit 1
}

ensure_full_dependencies() {
  local missing=()

  ensure_docker_dependencies
  have_container_command packer || missing+=("packer")
  have_container_command qemu-system-x86_64 || missing+=("qemu-system-x86_64")
  have_container_command qemu-img || missing+=("qemu-img")
  have_container_command xorriso || missing+=("xorriso")

  if [ "${#missing[@]}" -eq 0 ]; then
    return 0
  fi

  printf 'Missing container tools: %s\n' "${missing[*]}" >&2
  exit 1
}

build_validation_image() {
  require_host_command docker
  log "Building validation image ${VALIDATION_CONTAINER_IMAGE}"
  docker build \
    -t "${VALIDATION_CONTAINER_IMAGE}" \
    -f "${VALIDATION_CONTAINER_DOCKERFILE}" \
    "${VALIDATION_CONTAINER_BUILD_CONTEXT}"
}

ensure_validation_image() {
  require_host_command docker
  if docker image inspect "${VALIDATION_CONTAINER_IMAGE}" >/dev/null 2>&1; then
    return 0
  fi
  build_validation_image
}

maybe_refresh_ghcr() {
  if [ "${VALIDATION_REFRESH_GHCR}" != "1" ]; then
    return 0
  fi
  refresh_ghcr
}

refresh_ghcr() {
  log "Refreshing bitcoin GHCR images"
  docker pull "${BITCOIN_LAB_IMAGE}"
  docker pull "${BITCOIN_MEMPOOL_IMAGE}"
}

phase0() {
  log "Running Phase 0 read-only sanity checks"
  cd "${REPO_ROOT}"
  bash -n dynamic-labs/deploy-cloud.sh
  bash -n dynamic-labs/lab-manager.sh
  bash -n vm-build/prepare-docker-image-bundles.sh
  bash -n vm-build/prepare-hlf-runtime-assets.sh
  python3 - <<'PY'
import yaml
from pathlib import Path

yaml.safe_load(Path('.github/workflows/build-and-package.yml').read_text())
print('workflow yaml ok')
PY
}

phase1() {
  log "Running Phase 1 HLF runtime asset staging"
  cd "${REPO_ROOT}"
  bash vm-build/prepare-hlf-runtime-assets.sh
  test -x dynamic-labs/hlf/runtime/fabric-samples/test-network/network.sh
  test -f dynamic-labs/hlf/runtime/fabric-samples/test-network/organizations/fabric-ca/registerEnroll.sh
  test -f dynamic-labs/hlf/runtime/fabric-samples/test-network/compose/compose-test-net.yaml
}

phase2() {
  local expected=(
    course-site.tar
    router.tar
    instructor_auth_service.tar
    lane-service.tar
    bitcoin.tar
    consensus.tar
    cryptography.tar
    p2p_trust.tar
    quiz-engine-v2.tar
    exercises.tar
    ethereum_lab.tar
    hlf.tar
  )

  log "Running Phase 2 Docker image bundle generation"
  maybe_refresh_ghcr
  cd "${REPO_ROOT}"
  bash vm-build/prepare-docker-image-bundles.sh
  for tarball in "${expected[@]}"; do
    test -f "vm-build/docker-image-bundles/${tarball}"
  done
  ls -lh vm-build/docker-image-bundles
}

phase3() {
  log "Running Phase 3 Packer init and validate"
  cd "${REPO_ROOT}"
  packer init vm-build/ubuntu-lab.pkr.hcl
  packer validate vm-build/ubuntu-lab.pkr.hcl
}

phase4() {
  local server_pid=""

  cleanup() {
    if [ -n "${server_pid}" ]; then
      kill "${server_pid}" >/dev/null 2>&1 || true
    fi
  }

  log "Running Phase 4 workflow simulation"
  maybe_refresh_ghcr
  trap cleanup EXIT
  cd "${REPO_ROOT}"
  bash vm-build/prepare-hlf-runtime-assets.sh
  bash vm-build/prepare-docker-image-bundles.sh
  cd vm-build/docker-image-bundles
  ls -1 *.tar > manifest.txt
  python3 -m http.server 8000 >/tmp/docker-bundles-http.log 2>&1 &
  server_pid="$!"
  cd "${REPO_ROOT}"
  packer build -var "accelerator=none" vm-build/ubuntu-lab.pkr.hcl
}

run_all() {
  phase0
  phase1
  phase2
  phase3
  phase4
}

launch_container() {
  local subcommand="${1:-shell}"
  local tty_args=(-i)
  local docker_args=()

  require_host_command docker
  ensure_validation_image

  if [ -t 0 ] && [ -t 1 ]; then
    tty_args=(-it)
  fi

  if [ -n "${VALIDATION_CONTAINER_NAME:-}" ]; then
    docker_args+=(--name "${VALIDATION_CONTAINER_NAME}")
  fi

  if [ "${subcommand}" = "shell" ]; then
    exec docker run --rm "${tty_args[@]}" \
      "${docker_args[@]}" \
      -e BITCOIN_LAB_IMAGE="${BITCOIN_LAB_IMAGE}" \
      -e BITCOIN_MEMPOOL_IMAGE="${BITCOIN_MEMPOOL_IMAGE}" \
      -e HLF_IMAGE_TAG="${HLF_IMAGE_TAG}" \
      -e HLF_CA_IMAGE_TAG="${HLF_CA_IMAGE_TAG}" \
      -e HLF_NODEENV_IMAGE_TAG="${HLF_NODEENV_IMAGE_TAG}" \
      -e HLF_COUCHDB_IMAGE="${HLF_COUCHDB_IMAGE}" \
      -e HLF_FABRIC_SAMPLES_REF="${HLF_FABRIC_SAMPLES_REF}" \
      -e BUNDLE_PRUNE_AFTER_SAVE="${BUNDLE_PRUNE_AFTER_SAVE}" \
      -e VALIDATION_REFRESH_GHCR="${VALIDATION_REFRESH_GHCR}" \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v "${REPO_ROOT}:/workspace" \
      -w /workspace \
      "${VALIDATION_CONTAINER_IMAGE}" \
      bash
  fi

  exec docker run --rm "${tty_args[@]}" \
    "${docker_args[@]}" \
    -e BITCOIN_LAB_IMAGE="${BITCOIN_LAB_IMAGE}" \
    -e BITCOIN_MEMPOOL_IMAGE="${BITCOIN_MEMPOOL_IMAGE}" \
    -e HLF_IMAGE_TAG="${HLF_IMAGE_TAG}" \
    -e HLF_CA_IMAGE_TAG="${HLF_CA_IMAGE_TAG}" \
    -e HLF_NODEENV_IMAGE_TAG="${HLF_NODEENV_IMAGE_TAG}" \
    -e HLF_COUCHDB_IMAGE="${HLF_COUCHDB_IMAGE}" \
    -e HLF_FABRIC_SAMPLES_REF="${HLF_FABRIC_SAMPLES_REF}" \
    -e BUNDLE_PRUNE_AFTER_SAVE="${BUNDLE_PRUNE_AFTER_SAVE}" \
    -e VALIDATION_REFRESH_GHCR="${VALIDATION_REFRESH_GHCR}" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${REPO_ROOT}:/workspace" \
    -w /workspace \
    "${VALIDATION_CONTAINER_IMAGE}" \
    bash /workspace/dynamic-labs/scripts/local-validation-runner.sh --inside "${subcommand}"
}

run_inside() {
  local subcommand="${1:-}"

  case "${subcommand}" in
    refresh-ghcr)
      ensure_docker_dependencies
      refresh_ghcr
      ;;
    phase0)
      ensure_basic_dependencies
      phase0
      ;;
    phase1)
      ensure_docker_dependencies
      phase1
      ;;
    phase2)
      ensure_docker_dependencies
      phase2
      ;;
    phase3)
      ensure_full_dependencies
      phase3
      ;;
    phase4)
      ensure_full_dependencies
      phase4
      ;;
    all)
      ensure_full_dependencies
      run_all
      ;;
    help|-h|--help|"")
      usage
      ;;
    *)
      printf 'Unknown subcommand: %s\n\n' "${subcommand}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main() {
  if [ "${1:-}" = "--inside" ]; then
    shift
    run_inside "${1:-}"
    return
  fi

  case "${1:-}" in
    help|-h|--help|"")
      usage
      ;;
    build-image)
      build_validation_image
      ;;
    shell|refresh-ghcr|phase0|phase1|phase2|phase3|phase4|all)
      launch_container "${1}"
      ;;
    *)
      printf 'Unknown subcommand: %s\n\n' "${1}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "${@}"
