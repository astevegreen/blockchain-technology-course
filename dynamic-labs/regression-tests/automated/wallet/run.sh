#!/usr/bin/env bash
# The wallet lab's live suite. Options and steps: ../run-lab.sh (run with --help).

# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"

# The wallet page's derivation code, run in node against the frozen chain's facts.json.
lab_before_suite() {
  echo "${LAB_TAG} checking the wallet page's addresses against facts.json"
  docker run --rm \
    -v "${ROOT_DIR}:/work" \
    -w /work \
    node:24-alpine \
    node regression-tests/automated/wallet/derive_check.cjs
}

run_lab "$@"
