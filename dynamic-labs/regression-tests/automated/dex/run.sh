#!/usr/bin/env bash
# The dex lab's live suite. Options and steps: ../run-lab.sh (run with --help).

LAB_DOCKER_SOCKET=1  # Pool trading's live test plays the instructor's round with docker exec
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"
# shellcheck source=../launcher-stack.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../launcher-stack.sh"
run_lab "$@"
run_launcher_pass
