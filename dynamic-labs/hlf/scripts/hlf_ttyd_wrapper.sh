#!/bin/sh
# Bitcoin-pattern entrypoint: start main process in background, do any
# setup (student channel join), then exec ttyd as PID 1.
#
# Baked into hlf-peer-ttyd / hlf-orderer-ttyd images via Dockerfile.ttyd.
# Channel join only runs for HLF_NODE_TYPE=student when the channel block
# and admin MSP are volume-mounted.
set -e

TTYD_PORT="${HLF_TTYD_PORT:-7681}"
SHELL_SCRIPT="${HLF_SHELL_SCRIPT:-/opt/hlf-scripts/hlf_peer_shell.sh}"
TTYD_USER="${HLF_TTYD_USER:-hlf}"
MAIN_USER="${HLF_MAIN_USER:-}"
RUNTIME_DIR="${HLF_RUNTIME_TMP:-/tmp/hlf-runtime}"
PEER_RUNTIME_DIR="${RUNTIME_DIR}/peer-config"
ADMIN_RUNTIME_DIR="${RUNTIME_DIR}/admin-msp"
ZELLIJ_SESSION="${HLF_ZELLIJ_SESSION:-hlf}"
ZELLIJ_BIN="${HLF_ZELLIJ_BIN:-}"

if [ -z "${ZELLIJ_BIN}" ]; then
    ZELLIJ_BIN="$(command -v zellij 2>/dev/null || true)"
fi

if [ -z "${MAIN_USER}" ] && [ "${HLF_NODE_TYPE:-}" = "student" ]; then
    MAIN_USER="${TTYD_USER}"
fi

run_as_user() {
    if [ "$(id -u)" = "0" ] && command -v runuser >/dev/null 2>&1 && id "${1}" >/dev/null 2>&1; then
        user="$1"
        shift
        exec runuser -u "${user}" -m -- "$@"
    fi
    shift
    exec "$@"
}

run_cmd_as_user() {
    if [ "$(id -u)" = "0" ] && command -v runuser >/dev/null 2>&1 && id "${1}" >/dev/null 2>&1; then
        user="$1"
        shift
        runuser -u "${user}" -m -- "$@"
        return $?
    fi
    shift
    "$@"
}

stage_tree_for_user() {
    src="$1"
    dst="$2"
    if [ ! -d "$src" ]; then
        return 1
    fi
    rm -rf "$dst"
    mkdir -p "$dst"
    cp -a "$src"/. "$dst"/
    chown -R 1000:1000 "$dst" 2>/dev/null || true
    return 0
}

# --- Ensure writable mounts stay owned by the student user ---
# The student shell and student peer both write here. With CAP_DAC_OVERRIDE
# dropped, a root-launched peer cannot rely on Unix superuser bypasses, so
# ownership must actually match the runtime uid.
for writable_dir in "${HLF_HOME_DIR:-/home/student}" /var/hyperledger/production; do
    if [ -d "${writable_dir}" ]; then
        chown -R 1000:1000 "${writable_dir}" 2>/dev/null || true
    fi
done

# --- Stage read-only mounted crypto material into a student-readable runtime dir ---
# Student peers run as the unprivileged `hlf` user. Their bind-mounted MSP/TLS trees
# come from cryptogen/fabric-samples and are typically root-owned with restrictive
# file modes (e.g. 600 private keys, 700 parent directories). Copy only the needed
# peer/admin material into /tmp so the peer process can read its own keys without
# relaxing host-side permissions or exposing the whole organizations tree.
if [ "${HLF_NODE_TYPE:-}" = "student" ] && [ "${1:-}" = "peer" ] && [ "$(id -u)" = "0" ]; then
    if stage_tree_for_user /etc/hyperledger/fabric "${PEER_RUNTIME_DIR}"; then
        export CORE_PEER_MSPCONFIGPATH="${PEER_RUNTIME_DIR}/msp"
        export CORE_PEER_TLS_CERT_FILE="${PEER_RUNTIME_DIR}/tls/server.crt"
        export CORE_PEER_TLS_KEY_FILE="${PEER_RUNTIME_DIR}/tls/server.key"
        export CORE_PEER_TLS_ROOTCERT_FILE="${PEER_RUNTIME_DIR}/tls/ca.crt"
    fi
fi

# --- Start main process (peer/orderer) in background ---
if [ -n "${MAIN_USER}" ]; then
    runuser -u "${MAIN_USER}" -m -- "$@" &
else
    "$@" &
fi

# --- Wait for peer to accept connections (skip for orderer) ---
if [ "${1:-}" = "peer" ]; then
    timeout=${HLF_PEER_READY_TIMEOUT:-90}
    elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if grep -q ':1B8B' /proc/net/tcp /proc/net/tcp6 2>/dev/null; then
            break
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
fi

# --- Student channel join (if materials are volume-mounted) ---
if [ "${HLF_NODE_TYPE:-}" = "student" ] && [ "${1:-}" = "peer" ]; then
    CHANNEL="${HLF_CHANNEL:-diplomas}"
    BLOCK="/opt/hlf-channel/${CHANNEL}.block"
    ADMIN_MSP_SRC="/opt/hlf-orgs/peerOrganizations/${HLF_ORG_DOMAIN}/users/${HLF_ADMIN_USER}/msp"
    ADMIN_MSP="${ADMIN_MSP_SRC}"
    if [ "$(id -u)" = "0" ] && stage_tree_for_user "${ADMIN_MSP_SRC}" "${ADMIN_RUNTIME_DIR}"; then
        ADMIN_MSP="${ADMIN_RUNTIME_DIR}"
    fi
    if [ -f "$BLOCK" ] && [ -d "$ADMIN_MSP" ]; then
        if ! runuser -u "${TTYD_USER}" -m -- peer channel list 2>/dev/null | grep -q "^${CHANNEL}$"; then
            CORE_PEER_MSPCONFIGPATH="$ADMIN_MSP" \
                runuser -u "${TTYD_USER}" -m -- peer channel join -b "$BLOCK" 2>&1 || true
        fi
    fi
fi

# --- Discover bind IP for ttyd (terminal network isolation) ---
bind_ip=""
if command -v ttyd >/dev/null 2>&1 && [ -f "${SHELL_SCRIPT}" ]; then
    router_ip="$(getent hosts router-router-1 2>/dev/null | awk '{print $1; exit}')" || true
    if [ -n "$router_ip" ] && command -v ip >/dev/null 2>&1; then
        bind_ip="$(ip -4 route get "$router_ip" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1); exit}')" || true
    fi
    # Set HOME to the ttyd user's actual home so bash doesn't try /root/.bashrc
    ttyd_home="$(getent passwd "${TTYD_USER}" 2>/dev/null | cut -d: -f6)" || true
    [ -n "${ttyd_home}" ] && export HOME="${ttyd_home}"

    if [ -n "${ZELLIJ_BIN}" ] && [ -x "${ZELLIJ_BIN}" ]; then
        if ! HLF_SHELL_RC_ONLY=1 bash "${SHELL_SCRIPT}"; then
            echo "[hlf ttyd] WARNING: failed to prepare HLF shell rc; helpers may be unavailable" >&2
        fi
        export SHELL="/bin/bash"
        if [ "$(id -u)" = "0" ] && command -v runuser >/dev/null 2>&1 && id "${TTYD_USER}" >/dev/null 2>&1; then
            exec ttyd -i "${bind_ip:-0.0.0.0}" -W -p "${TTYD_PORT}" \
                runuser -u "${TTYD_USER}" -m -- \
                "${ZELLIJ_BIN}" attach --create "${ZELLIJ_SESSION}"
        fi
        exec ttyd -i "${bind_ip:-0.0.0.0}" -W -p "${TTYD_PORT}" \
            "${ZELLIJ_BIN}" attach --create "${ZELLIJ_SESSION}"
    fi
    if [ "$(id -u)" = "0" ] && command -v runuser >/dev/null 2>&1 && id "${TTYD_USER}" >/dev/null 2>&1; then
        exec ttyd -i "${bind_ip:-0.0.0.0}" -W -p "${TTYD_PORT}" \
            runuser -u "${TTYD_USER}" -m -- \
            bash "${SHELL_SCRIPT}"
    fi
    exec ttyd -i "${bind_ip:-0.0.0.0}" -W -p "${TTYD_PORT}" \
        bash "${SHELL_SCRIPT}"
fi

# Fallback if no ttyd: wait on main process
wait
