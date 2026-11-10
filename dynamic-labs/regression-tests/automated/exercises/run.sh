#!/usr/bin/env bash
# The exercises lab's live suite. Options and steps: ../run-lab.sh (run with --help).

LAB_CREDENTIALS=1
# shellcheck source=../run-lab.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../run-lab.sh"
# shellcheck source=../launcher-stack.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../launcher-stack.sh"

# The image the student launcher's running container of a game uses. The launcher runs released images pulled by
# digest, so the classroom's exercises-<game>:latest tags do not exist on its stack.
launcher_game_image() {
  local game="$1" container
  container="$(docker ps -q \
    --filter "label=course.lab=${LAB_STACK}" \
    --filter "label=com.docker.compose.service=${game}" | head -n 1)"
  if [[ -z "${container}" ]]; then
    echo "${LAB_TAG} no running ${LAB_STACK} container for the ${game} game" >&2
    return 1
  fi
  docker inspect -f '{{.Image}}' "${container}"
}

lab_before_suite() {
  # The games pin eventlet 0.33.3, which imports distutils and so fails on Python 3.12 and later: the check
  # skips these contract tests on such hosts, so they run here, inside each game's own image (Python 3.11).
  local pair game image test_file
  for pair in "bgp:test_exercise_bgp_contract.py" \
              "insider:test_exercise_trust_game_shared_auth_contract.py"; do
    game="${pair%:*}"
    test_file="${pair##*:}"
    if [[ "${STUDENT_LAUNCHER}" == "1" ]]; then
      image="$(launcher_game_image "${game}")"
    else
      image="exercises-${game}:latest"
    fi
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
run_launcher_pass
