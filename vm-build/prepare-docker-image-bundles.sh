#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/vm-build/docker-image-bundles}"
BITCOIN_LAB_IMAGE="${BITCOIN_LAB_IMAGE:-ghcr.io/blockchain-course-2026/bitcoin-lab:latest}"
BITCOIN_MEMPOOL_IMAGE="${BITCOIN_MEMPOOL_IMAGE:-ghcr.io/blockchain-course-2026/bitcoin-mempool:latest}"
HLF_IMAGE_TAG="${HLF_IMAGE_TAG:-2.5.15}"
HLF_CA_IMAGE_TAG="${HLF_CA_IMAGE_TAG:-1.5.17}"
HLF_COUCHDB_IMAGE="${HLF_COUCHDB_IMAGE:-couchdb:3.4.2}"
BUNDLE_PRUNE_AFTER_SAVE="${BUNDLE_PRUNE_AFTER_SAVE:-1}"

projects=(
  "dynamic-labs/course-site"
  "dynamic-labs/router"
  "dynamic-labs/instructor_auth_service"
  "dynamic-labs/lane-service"
  "dynamic-labs/bitcoin"
  "dynamic-labs/consensus"
  "dynamic-labs/cryptography"
  "dynamic-labs/p2p_trust"
  "dynamic-labs/quiz-engine-v2"
  "dynamic-labs/exercises"
  "dynamic-labs/explorer"
  "dynamic-labs/ethereum_lab"
  "dynamic-labs/hlf"
)

compose_file_for() {
  local project_dir="$1"
  local candidate
  for candidate in \
    "$project_dir/docker-compose.yml" \
    "$project_dir/docker-compose.yaml" \
    "$project_dir/compose.yaml" \
    "$project_dir/compose.yml"
  do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  echo "No Docker Compose file found for $project_dir" >&2
  return 1
}

compose_args() {
  local project_dir="$1"
  local compose_file
  compose_file="$(compose_file_for "$project_dir")"
  echo --project-directory "$project_dir" --profile build-only -f "$compose_file"
}

append_extra_images() {
  local project_name="$1"
  case "$project_name" in
    bitcoin)
      printf '%s\n' \
        "$BITCOIN_LAB_IMAGE" \
        "$BITCOIN_MEMPOOL_IMAGE"
      ;;
    lane-service)
      printf '%s\n' "busybox:latest"
      ;;
    hlf)
      printf '%s\n' \
        "hyperledger/fabric-orderer:${HLF_IMAGE_TAG}" \
        "hyperledger/fabric-peer:${HLF_IMAGE_TAG}" \
        "hyperledger/fabric-tools:${HLF_IMAGE_TAG}" \
        "hyperledger/fabric-ca:${HLF_CA_IMAGE_TAG}" \
        "${HLF_COUCHDB_IMAGE}"
      ;;
  esac
}

ensure_image_present() {
  local image="$1"
  if docker image inspect "$image" >/dev/null 2>&1; then
    return 0
  fi
  docker pull "$image"
}

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

for project in "${projects[@]}"; do
  project_dir="$ROOT_DIR/$project"
  project_name="$(basename "$project")"

  echo "Preparing Docker images for $project_name"

  docker compose $(compose_args "$project_dir") pull --ignore-pull-failures || true
  docker compose $(compose_args "$project_dir") build

  mapfile -t images < <(
    {
      docker compose $(compose_args "$project_dir") config --images | awk 'NF'
      append_extra_images "$project_name"
    } | awk 'NF' | sort -u
  )

  if [ "${#images[@]}" -eq 0 ]; then
    echo "No images discovered for $project_name, skipping save"
    continue
  fi

  for image in "${images[@]}"; do
    ensure_image_present "$image"
  done

  docker save -o "$OUT_DIR/$project_name.tar" "${images[@]}"
  if [ "${BUNDLE_PRUNE_AFTER_SAVE}" = "1" ]; then
    docker image rm -f "${images[@]}" >/dev/null 2>&1 || true
    docker builder prune -af >/dev/null 2>&1 || true
  else
    echo "Preserving Docker image and builder cache after $project_name"
  fi
done
