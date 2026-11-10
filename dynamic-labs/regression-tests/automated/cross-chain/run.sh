#!/usr/bin/env bash
# The cross-chain lab's live suite. Options and steps: ../run-lab.sh (run with --help).

LAB_START_NOTE="(builds the page image the first time)"
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"
# shellcheck source=../launcher-stack.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../launcher-stack.sh"
run_lab "$@"
run_launcher_pass
