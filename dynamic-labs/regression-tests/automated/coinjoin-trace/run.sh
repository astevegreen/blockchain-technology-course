#!/usr/bin/env bash
# The coinjoin-trace lab's live suite. Options and steps: ../run-lab.sh (run with --help).

# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"
run_lab "$@"
