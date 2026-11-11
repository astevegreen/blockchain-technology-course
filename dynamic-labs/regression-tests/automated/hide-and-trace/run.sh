#!/usr/bin/env bash
# The hide-and-trace team game's live suite: one whole game through the router, then the saved game. Options and
# steps: ../run-lab.sh (run with --help). The game runs from the instructor's machine only (lab.yaml
# student_local: false), so it has no student-launcher pass.

LAB_CREDENTIALS=1
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"

# The saved game (hide-and-trace/README.md, "The saved game"): start the lab on a fresh volume from the committed
# file, check it with fallback_check.py, then put the lab back on a fresh live chain so the next run can play.
saved_game_pass() {
  local saved="${ROOT_DIR}/hide-and-trace/quizes/fallback-game.json"
  if [[ ! -f "${saved}" ]]; then
    echo "${LAB_TAG} no saved game committed yet (${saved}): the saved-game pass is skipped"
    return 0
  fi
  echo "${LAB_TAG} starting the lab from the saved game"
  (cd "${ROOT_DIR}/hide-and-trace" && docker compose -p hide-and-trace down -v)
  (cd "${ROOT_DIR}" && HT_FALLBACK_FILE=/game-quizes/fallback-game.json bash ./lab-manager.sh start hide-and-trace)
  local rc=0
  LAB_TEST_FILE=fallback_check.py MATCH_PATTERN="" run_in_container || rc=$?
  echo "${LAB_TAG} putting the lab back on a fresh live chain"
  (cd "${ROOT_DIR}/hide-and-trace" && docker compose -p hide-and-trace down -v)
  (cd "${ROOT_DIR}" && bash ./lab-manager.sh start hide-and-trace)
  return "${rc}"
}

run_lab "$@"
if [[ "${SKIP_START}" != "1" && -z "${LAB_TEST_FILE}" && -z "${MATCH_PATTERN}" ]]; then
  saved_game_pass
fi
