#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd -- "$(dirname -- "${SCRIPT_PATH}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
SERVICE="vm"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
HOST_RUNTIME_DIR="${REPO_ROOT}/.runtime"
STUDENT_PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
STUDENT_FORWARD_ENV=(
    "DOCKER_BUILD_NETWORK"
    "LAB_MANAGER_DEFAULT_MAX_STUDENT_CAPACITY"
    "LAB_MANAGER_DEFAULT_STUDENT_WARM_POOL_SIZE"
    "HLF_CLAIM_WARM_POOL_SIZE"
)

compose() {
    docker compose -f "${COMPOSE_FILE}" "$@"
}

ensure_running() {
    if ! compose ps --status running --services 2>/dev/null | grep -qx "${SERVICE}"; then
        echo "student-home-vm is not running. Start it with:"
        echo "  ${SCRIPT_DIR}/run.sh up"
        exit 1
    fi
}

wait_for_inner_docker() {
    local tries=0

    ensure_running
    until compose exec -T "${SERVICE}" sh -lc 'docker info >/dev/null 2>&1'; do
        tries=$((tries + 1))
        if (( tries >= 60 )); then
            echo "Nested Docker daemon did not become ready inside the VM harness." >&2
            compose logs --tail=200 "${SERVICE}" >&2 || true
            exit 1
        fi
        sleep 1
    done
}

exec_student() {
    local quoted_command
    local -a env_flags=()
    local -a sudo_env=()
    local var value

    wait_for_inner_docker
    printf -v quoted_command '%q' "$*"
    for var in "${STUDENT_FORWARD_ENV[@]}"; do
        value="$(compose exec -T "${SERVICE}" sh -lc "printenv ${var} 2>/dev/null || true" | tail -n 1)"
        env_flags+=("-e" "${var}=${value}")
        sudo_env+=("${var}=${value}")
    done
    compose exec -T -e PATH="${STUDENT_PATH}" "${env_flags[@]}" "${SERVICE}" bash -lc "sudo -n -u student env PATH='${STUDENT_PATH}' ${sudo_env[*]} bash -lc ${quoted_command}"
}

exec_root() {
    wait_for_inner_docker
    compose exec -T "${SERVICE}" bash -lc "$*"
}

sync_runtime_credentials_from_vm() {
    local host_env="${HOST_RUNTIME_DIR}/runtime-secrets.env"
    local host_creds="${HOST_RUNTIME_DIR}/instructor-credentials.txt"
    local tmp_env=""
    local tmp_creds=""

    ensure_running
    mkdir -p "${HOST_RUNTIME_DIR}"

    if compose exec -T "${SERVICE}" bash -lc 'test -f /workspace/dynamic-labs/.runtime/runtime-secrets.env'; then
        tmp_env="$(mktemp)"
        if compose exec -T "${SERVICE}" bash -lc 'cat /workspace/dynamic-labs/.runtime/runtime-secrets.env' > "${tmp_env}"; then
            mv "${tmp_env}" "${host_env}"
            chmod 600 "${host_env}"
        else
            rm -f "${tmp_env}"
        fi
    fi

    if compose exec -T "${SERVICE}" bash -lc 'test -f /workspace/dynamic-labs/.runtime/instructor-credentials.txt'; then
        tmp_creds="$(mktemp)"
        if compose exec -T "${SERVICE}" bash -lc 'cat /workspace/dynamic-labs/.runtime/instructor-credentials.txt' > "${tmp_creds}"; then
            mv "${tmp_creds}" "${host_creds}"
            chmod 644 "${host_creds}"
        else
            rm -f "${tmp_creds}"
        fi
    fi
}

discover_harness_base_url() {
    exec_student '
        python3 - <<'"'"'PY'"'"'
import subprocess
import urllib.request

candidates = []

try:
    result = subprocess.run(
        "ip route | awk \"/default/ {print \\$3; exit}\"",
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    gateway = result.stdout.strip()
    if gateway:
        candidates.append(f"http://{gateway}:8080")
except Exception:
    pass

for extra in ("http://10.0.2.15:8080", "http://172.17.0.1:8080", "http://172.19.0.1:8080"):
    if extra not in candidates:
        candidates.append(extra)

for url in candidates:
    try:
        with urllib.request.urlopen(f"{url}/", timeout=5) as response:
            if response.status == 200:
                print(url)
                raise SystemExit(0)
    except Exception:
        continue

raise SystemExit("Could not find a reachable nested router base URL for reset-claims.")
PY
    '
}

smoke() {
    compose down >/dev/null 2>&1 || true
    compose up -d --build
    wait_for_inner_docker
    exec_student 'test "$(whoami)" = "student"'
    exec_student 'sudo -n true'
    exec_student 'docker info >/dev/null'
    exec_student 'docker compose version >/dev/null'
    exec_root 'test -d /src/dynamic-labs'
    exec_student 'test -f /workspace/dynamic-labs/lab-manager.sh'
    exec_student 'touch /workspace/dynamic-labs/.vm-harness-isolated'
    exec_root 'test ! -e /src/dynamic-labs/.vm-harness-isolated'
    exec_student 'rm -f /workspace/dynamic-labs/.vm-harness-isolated'
    exec_student '
        set -euo pipefail
        workdir="$(mktemp -d)"
        img="${workdir}/smoke.img"
        mount_dir="${workdir}/mnt"
        mkdir -p "${mount_dir}"
        truncate -s 32M "${img}"
        sudo -n mkfs.ext4 -q -F "${img}"
        sudo -n mount -o loop,nosuid,nodev "${img}" "${mount_dir}"
        sudo -n chown student:student "${mount_dir}"
        echo ok > "${mount_dir}/probe.txt"
        test -f "${mount_dir}/probe.txt"
        sudo -n umount "${mount_dir}"
        rm -rf "${workdir}"
    '
    echo "student-home-vm smoke check passed."
}

usage() {
    cat <<EOF
Usage:
  ./run.sh build
  ./run.sh up
  ./run.sh down
  ./run.sh logs
  ./run.sh sync
  ./run.sh reset-claims [--wipe] [--lab <name> ...]
  ./run.sh shell
  ./run.sh root-shell
  ./run.sh exec <command>
  ./run.sh exec-root <command>
  ./run.sh smoke

Examples:
  ./run.sh up
  ./run.sh sync
  ./run.sh reset-claims --wipe
  ./run.sh exec 'sudo -n true && docker info | head'
  ./run.sh exec 'cd /workspace/dynamic-labs && bash ./lab-manager.sh deploy --mode student'
  ./run.sh down
EOF
}

sync_workspace() {
    ensure_running
    if compose exec -T "${SERVICE}" sh -lc 'docker ps --format "{{.Names}}" | grep -Eq "^(lane-service-lane-service-1|.*-lab-.*)$"'; then
        echo "Refusing to sync while nested lab services are running." >&2
        echo "Stop the inner labs first, for example:" >&2
        echo "  ./run.sh exec-root 'cd /workspace/dynamic-labs && bash ./lab-manager.sh stop all'" >&2
        echo "or tear the harness down with:" >&2
        echo "  ./run.sh down" >&2
        exit 1
    fi
    compose exec -T "${SERVICE}" bash -lc '
        rm -rf /workspace/dynamic-labs/.runtime /workspace/dynamic-labs/lane-service/runtime /workspace/dynamic-labs/hlf/runtime
        rsync -a --delete \
            --exclude ".git/" \
            --exclude ".runtime/" \
            --exclude "dynamic-labs/.runtime/" \
            --exclude "dynamic-labs/lane-service/runtime/" \
            --exclude "dynamic-labs/hlf/runtime/" \
            --exclude "**/__pycache__/" \
            /src/ /workspace/
        mkdir -p /workspace/dynamic-labs/hlf/runtime/fabric-samples
        for rel in bin config test-network asset-transfer-basic; do
            rsync -a --delete --exclude ".git/" \
                "/src/dynamic-labs/hlf/runtime/fabric-samples/${rel}/" \
                "/workspace/dynamic-labs/hlf/runtime/fabric-samples/${rel}/"
        done
        chown -R student:student /workspace
    '
}

command="${1:-}"
shift || true

case "${command}" in
    build)
        compose build
        ;;
    up)
        compose up -d --build
        wait_for_inner_docker
        ;;
    down)
        compose down -v
        ;;
    logs)
        compose logs -f "${SERVICE}"
        ;;
    sync)
        sync_workspace
        ;;
    shell)
        wait_for_inner_docker
        compose exec "${SERVICE}" bash -lc "sudo -n -iu student env PATH='${STUDENT_PATH}' bash -l"
        ;;
    root-shell)
        ensure_running
        compose exec "${SERVICE}" bash -l
        ;;
    exec)
        if [[ $# -eq 0 ]]; then
            echo "exec requires a command"
            exit 1
        fi
        if exec_student "$*"; then
            sync_runtime_credentials_from_vm
        else
            rc=$?
            sync_runtime_credentials_from_vm || true
            exit "${rc}"
        fi
        ;;
    exec-root)
        if [[ $# -eq 0 ]]; then
            echo "exec-root requires a command"
            exit 1
        fi
        if exec_root "$*"; then
            sync_runtime_credentials_from_vm
        else
            rc=$?
            sync_runtime_credentials_from_vm || true
            exit "${rc}"
        fi
        ;;
    smoke)
        smoke
        ;;
    reset-claims)
        wait_for_inner_docker
        base_url="$(discover_harness_base_url | tail -n 1)"
        exec_student "python3 /src/dynamic-labs/regression-tests/infrastructure/reset_live_claims.py --base-url ${base_url} --credentials-file /workspace/dynamic-labs/.runtime/instructor-credentials.txt $*"
        sync_runtime_credentials_from_vm
        ;;
    ""|-h|--help|help)
        usage
        ;;
    *)
        echo "Unknown command: ${command}"
        usage
        exit 1
        ;;
esac
