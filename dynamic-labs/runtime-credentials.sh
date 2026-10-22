#!/bin/bash

set -euo pipefail

if [[ -n "${DYNAMIC_LABS_ROOT:-}" ]]; then
    RUNTIME_BASE_DIR="${DYNAMIC_LABS_ROOT}"
else
    RUNTIME_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
    RUNTIME_BASE_DIR="${RUNTIME_SCRIPT_DIR}"
fi

RUNTIME_DIR="${RUNTIME_BASE_DIR}/.runtime"
RUNTIME_ENV_FILE="${RUNTIME_DIR}/runtime-secrets.env"
INSTRUCTOR_CREDENTIALS_FILE="${RUNTIME_DIR}/instructor-credentials.txt"

runtime_owner_spec() {
    if [[ "${EUID}" -ne 0 ]]; then
        return 1
    fi

    if [[ -n "${SUDO_UID:-}" && -n "${SUDO_GID:-}" ]]; then
        printf '%s:%s\n' "${SUDO_UID}" "${SUDO_GID}"
        return 0
    fi

    stat -c '%u:%g' "${RUNTIME_BASE_DIR}"
}

runtime_fix_path_ownership() {
    local owner

    if [[ "${EUID}" -ne 0 ]] || [[ "$#" -eq 0 ]]; then
        return 0
    fi

    owner="$(runtime_owner_spec)" || return 0
    chown -R "${owner}" "$@" 2>/dev/null || true
}

runtime_random_alnum() {
    python3 - "$1" <<'PY'
import secrets
import string
import sys

length = int(sys.argv[1])
alphabet = string.ascii_letters + string.digits
print("".join(secrets.choice(alphabet) for _ in range(length)))
PY
}

runtime_random_hex() {
    python3 - "$1" <<'PY'
import secrets
import sys

nbytes = int(sys.argv[1])
print(secrets.token_hex(nbytes))
PY
}

write_runtime_credentials_files() {
    local old_umask

    mkdir -p "${RUNTIME_DIR}"
    old_umask="$(umask)"
    umask 077
    cat > "${RUNTIME_ENV_FILE}" <<EOF
QUIZ_ENGINE_SECRET_KEY=${QUIZ_ENGINE_SECRET_KEY}
QUIZ_ENGINE_INSTRUCTOR_PASSWORD=${QUIZ_ENGINE_INSTRUCTOR_PASSWORD}
BGP_GAME_SECRET_KEY=${BGP_GAME_SECRET_KEY}
BGP_GAME_INSTRUCTOR_USER=${BGP_GAME_INSTRUCTOR_USER}
BGP_GAME_INSTRUCTOR_PASS=${BGP_GAME_INSTRUCTOR_PASS}
TRUST_GAME_SECRET_KEY=${TRUST_GAME_SECRET_KEY}
TRUST_GAME_INSTRUCTOR_USERNAME=${TRUST_GAME_INSTRUCTOR_USERNAME}
TRUST_GAME_INSTRUCTOR_PASSWORD=${TRUST_GAME_INSTRUCTOR_PASSWORD}
INSTRUCTOR_AUTH_USER=${INSTRUCTOR_AUTH_USER}
INSTRUCTOR_AUTH_KEY=${INSTRUCTOR_AUTH_KEY}
HLF_WEB_SECRET_KEY=${HLF_WEB_SECRET_KEY}
EOF
    chmod 600 "${RUNTIME_ENV_FILE}"

    cat > "${INSTRUCTOR_CREDENTIALS_FILE}" <<EOF
Dynamic Labs Instructor Credentials
==================================

Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Runtime env file: ${RUNTIME_ENV_FILE}

Central Instructor Auth
-----------------------
URL: /instructor/
Username: ${INSTRUCTOR_AUTH_USER}
Password: ${INSTRUCTOR_AUTH_KEY}

Notes
-----
- These credentials persist across restarts until rotated.
- To rotate them, rerun deploy with ROTATE_RUNTIME_CREDENTIALS=1.
- One login gates all instructor surfaces routed through nginx.
- The quiz engine also issues per-student access codes inside the app; those are not listed here.
EOF
    chmod 600 "${INSTRUCTOR_CREDENTIALS_FILE}"
    umask "${old_umask}"
    runtime_fix_path_ownership "${RUNTIME_DIR}"
}

ensure_runtime_credentials() {
    local rotate="${1:-${ROTATE_RUNTIME_CREDENTIALS:-0}}"

    mkdir -p "${RUNTIME_DIR}"

    if [[ -f "${RUNTIME_ENV_FILE}" && "${rotate}" != "1" && "${rotate}" != "true" && "${rotate}" != "yes" ]]; then
        # shellcheck disable=SC1090
        source "${RUNTIME_ENV_FILE}"
        if [[ -z "${INSTRUCTOR_AUTH_USER:-}" ]]; then
            INSTRUCTOR_AUTH_USER="${TRUST_GAME_INSTRUCTOR_USERNAME:-instructor}"
        fi
        if [[ -z "${INSTRUCTOR_AUTH_KEY:-}" ]]; then
            INSTRUCTOR_AUTH_KEY="${TRUST_GAME_INSTRUCTOR_PASSWORD:-$(runtime_random_alnum 20)}"
        fi
        write_runtime_credentials_files
        return 0
    fi

    QUIZ_ENGINE_SECRET_KEY="$(runtime_random_hex 32)"
    QUIZ_ENGINE_INSTRUCTOR_PASSWORD="$(runtime_random_alnum 24)"
    BGP_GAME_SECRET_KEY="$(runtime_random_hex 32)"
    BGP_GAME_INSTRUCTOR_USER="instructor"
    BGP_GAME_INSTRUCTOR_PASS="$(runtime_random_alnum 20)"
    TRUST_GAME_SECRET_KEY="$(runtime_random_hex 32)"
    TRUST_GAME_INSTRUCTOR_USERNAME="instructor"
    TRUST_GAME_INSTRUCTOR_PASSWORD="$(runtime_random_alnum 20)"
    INSTRUCTOR_AUTH_USER="${TRUST_GAME_INSTRUCTOR_USERNAME}"
    INSTRUCTOR_AUTH_KEY="${TRUST_GAME_INSTRUCTOR_PASSWORD}"
    HLF_WEB_SECRET_KEY="$(runtime_random_hex 32)"

    write_runtime_credentials_files
}

export_runtime_credentials() {
    ensure_runtime_credentials "${1:-0}"
    set -a
    # shellcheck disable=SC1090
    source "${RUNTIME_ENV_FILE}"
    set +a
}
