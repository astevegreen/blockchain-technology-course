#!/usr/bin/env bash
# Copy-vendor the shared instructor_auth package into each lab's build context.
# Run from repo root (or let lab compose files invoke it as a pre-build hook).
#
# Usage:
#   ./dynamic-labs/scripts/sync-shared.sh
#
# Idempotent. Overwrites per-lab copies. The source of truth is
# dynamic-labs/shared/instructor_auth/; per-lab copies live next to each
# lab's app code so Docker build contexts can access them without
# cross-directory bind mounts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="$REPO_ROOT/dynamic-labs/shared/instructor_auth"

if [[ ! -d "$SRC" ]]; then
  echo "source missing: $SRC" >&2
  exit 1
fi

# Labs that consume the shared auth package. Format: "build_ctx:dest_relpath".
# dest_relpath is interpreted relative to build_ctx.
TARGETS=(
  "dynamic-labs/quiz-engine-v2:instructor_auth"
  "dynamic-labs/exercises/l03-i3-trust-game:instructor_auth"
  "dynamic-labs/exercises/l03-i3-bgp-game:instructor_auth"
  "dynamic-labs/hlf:shared_instructor_auth"
)

for target in "${TARGETS[@]}"; do
  ctx="${target%%:*}"
  rel="${target##*:}"
  dest="$REPO_ROOT/$ctx/$rel"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  cp -a "$SRC" "$dest"
  # Mark the copy as generated so humans don't edit it in place.
  cat > "$dest/VENDORED" <<EOF
This directory is a copy of dynamic-labs/shared/instructor_auth/.
Regenerate by running dynamic-labs/scripts/sync-shared.sh from the repo root.
Do not edit in place — changes will be overwritten on the next sync.
EOF
  echo "synced -> $dest"
done
