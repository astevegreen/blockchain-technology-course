#!/usr/bin/env bash
# The exercises lab's live suite. Options and steps: ../run-lab.sh (run with --help).

LAB_CREDENTIALS=1
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"

lab_before_suite() {
  # The games pin eventlet 0.33.3, which imports distutils and so fails on Python 3.12 and later: the check
  # skips these contract tests on such hosts, so they run here, inside each game's own image (Python 3.11).
  local pair image test_file
  for pair in "exercises-bgp:latest:test_exercise_bgp_contract.py" \
              "exercises-insider:latest:test_exercise_trust_game_shared_auth_contract.py"; do
    image="${pair%:*}"
    test_file="${pair##*:}"
    echo "${LAB_TAG} running tests/${test_file} inside ${image}"
    docker run --rm \
      -v "${ROOT_DIR}:/labs:ro" \
      -w /labs \
      -e PYTHONDONTWRITEBYTECODE=1 \
      -e EXERCISE_CONTRACT_TESTS_REQUIRED=1 \
      --entrypoint python \
      "${image}" \
      -m unittest -v "tests/${test_file}"
  done
}

run_lab "$@"
