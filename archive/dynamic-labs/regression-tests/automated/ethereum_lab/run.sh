#!/usr/bin/env bash
# The ethereum_lab lab's live suite. Options and steps: ../run-lab.sh (run with --help).

LAB_ENV_PREFIX=ETHEREUM
LAB_CREDENTIALS=1
LAB_DOCKER_SOCKET=1
LAB_LANE=1
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"
run_lab "$@"
