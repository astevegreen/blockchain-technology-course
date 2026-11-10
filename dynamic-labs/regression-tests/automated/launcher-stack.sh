#!/usr/bin/env bash
# A second pass of a lab's live suite, against its student-launcher stack (docker-compose.launcher.yml,
# docs/student-launcher-design.md) instead of the classroom one. A lab's run.sh sources this after ../run-lab.sh and
# calls run_launcher_pass after run_lab "$@".
#
# It runs on GitHub's Lab Tests runners after a --fresh-start pass (never with --skip-start), or anywhere with
# LAB_LAUNCHER_PASS=1. It:
#   1. builds each image the launcher file's "# launcher-build: <VAR> <context> <dockerfile>" lines name (context
#      relative to the lab folder, dockerfile relative to the context), tags it locally and exports <VAR>;
#   2. stops the classroom stack and starts the launcher one, under the same project and container names, with the
#      same env file lab-manager uses;
#   3. checks every container carries course.lab=<lab> and this run's course.release, and has no bind mount;
#   4. runs the lab's suite again (not lab_before_suite: that checks the classroom images);
#   5. outside CI, puts the classroom stack back.
# The classroom docker-compose.yml, lab-manager.sh and run-lab.sh are untouched by it.

launcher_pass_wanted() {
  if [[ "${LAB_LAUNCHER_PASS:-0}" == "1" ]]; then
    return 0
  fi
  [[ "${GITHUB_ACTIONS:-}" == "true" && "${FRESH_START}" == "1" && "${SKIP_START}" != "1" ]]
}

launcher_compose() {
  local env_file="${ROOT_DIR}/.runtime/runtime-secrets.env" file="$1"
  shift
  if [[ -f "${env_file}" ]]; then
    docker compose -f "${file}" --env-file "${env_file}" "$@"
  else
    docker compose -f "${file}" "$@"
  fi
}

launcher_build_images() {
  local lab_dir="$1" var ctx dockerfile tag line count=0
  while read -r line; do
    read -r var ctx dockerfile <<<"${line#\# launcher-build:}"
    if [[ -z "${var}" || -z "${ctx}" || -z "${dockerfile}" ]]; then
      echo "${LAB_TAG} launcher: unreadable build line: ${line}" >&2
      return 1
    fi
    tag="course-labs-ci/$(tr 'A-Z_' 'a-z-' <<<"${var}"):ci"
    echo "${LAB_TAG} launcher: building ${var} from ${ctx}/${dockerfile}"
    docker build \
      --network "${DOCKER_BUILD_NETWORK:-default}" \
      -t "${tag}" \
      -f "${lab_dir}/${ctx}/${dockerfile}" \
      "${lab_dir}/${ctx}"
    export "${var}=${tag}"
    count=$((count + 1))
  done < <(grep '^# launcher-build:' "${lab_dir}/docker-compose.launcher.yml")
  if [[ "${count}" -eq 0 ]]; then
    echo "${LAB_TAG} launcher: docker-compose.launcher.yml names no images to build" >&2
    return 1
  fi
}

launcher_check_containers() {
  local lab="$1" project="$2" expected="$3" name labels mounts failed=0
  local -a names
  mapfile -t names < <(docker ps --filter "label=com.docker.compose.project=${project}" --format '{{.Names}}' | sort)
  if [[ "${#names[@]}" -ne "${expected}" ]]; then
    echo "${LAB_TAG} launcher: ${#names[@]} of ${expected} containers running: ${names[*]}" >&2
    docker ps -a --filter "label=com.docker.compose.project=${project}" >&2
    return 1
  fi
  for name in "${names[@]}"; do
    labels="$(docker inspect -f '{{index .Config.Labels "course.lab"}} {{index .Config.Labels "course.release"}}' "${name}")"
    mounts="$(docker inspect -f '{{range .Mounts}}{{if eq .Type "bind"}}{{.Source}} {{end}}{{end}}' "${name}")"
    if [[ "${labels}" != "${lab} ${COURSE_RELEASE}" ]]; then
      echo "${LAB_TAG} launcher: ${name} has labels '${labels}', not '${lab} ${COURSE_RELEASE}'" >&2
      failed=1
    fi
    if [[ -n "${mounts}" ]]; then
      echo "${LAB_TAG} launcher: ${name} bind-mounts ${mounts}" >&2
      failed=1
    fi
  done
  if [[ "${failed}" -ne 0 ]]; then
    return 1
  fi
  echo "${LAB_TAG} launcher: ${expected} containers labelled ${lab} ${COURSE_RELEASE}, none bind-mounted"
}

run_launcher_pass() {
  if ! launcher_pass_wanted; then
    return 0
  fi
  local lab="${LAB_STACK}" lab_dir="${ROOT_DIR}/${LAB_STACK}" project expected
  if [[ ! -f "${lab_dir}/docker-compose.launcher.yml" ]]; then
    echo "${LAB_TAG} launcher: ${lab} has no docker-compose.launcher.yml" >&2
    return 1
  fi
  echo "${LAB_TAG} launcher pass: the suite again, against docker-compose.launcher.yml"
  export COURSE_RELEASE="ci-${GITHUB_RUN_ID:-local}"
  launcher_build_images "${lab_dir}"

  project="$(cd "${lab_dir}" && launcher_compose docker-compose.launcher.yml config --format json \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])')"
  expected="$(cd "${lab_dir}" && launcher_compose docker-compose.launcher.yml config --services | wc -l)"
  (
    cd "${lab_dir}"
    launcher_compose docker-compose.yml down --remove-orphans
    launcher_compose docker-compose.launcher.yml up -d
  )
  launcher_check_containers "${lab}" "${project}" "${expected}"

  build_runner_image
  run_in_container

  if [[ "${GITHUB_ACTIONS:-}" != "true" ]]; then
    echo "${LAB_TAG} launcher: putting the classroom stack back"
    (
      cd "${lab_dir}"
      launcher_compose docker-compose.launcher.yml down --remove-orphans
    )
    ensure_live_stack
  fi
}
