#!/bin/bash
# lab-manager.sh - deployment and lifecycle helper for dynamic-labs

set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd -- "$(dirname -- "${SCRIPT_PATH}")" && pwd)"

if [[ -n "${DYNAMIC_LABS_ROOT:-}" ]]; then
    BASE_DIR="${DYNAMIC_LABS_ROOT}"
elif [[ -f "${SCRIPT_DIR}/README.md" && -d "${SCRIPT_DIR}/router" ]]; then
    BASE_DIR="${SCRIPT_DIR}"
elif [[ -f "/opt/dynamic-labs/README.md" && -d "/opt/dynamic-labs/router" ]]; then
    BASE_DIR="/opt/dynamic-labs"
else
    BASE_DIR="${SCRIPT_DIR}"
fi

STATE_FILE="${BASE_DIR}/.lab-manager.env"
RUNTIME_CREDENTIALS_HELPER="${BASE_DIR}/runtime-credentials.sh"
CLASSROOM_NETWORK_HELPER="${BASE_DIR}/scripts/classroom-network-helper.sh"

if [[ -f "${RUNTIME_CREDENTIALS_HELPER}" ]]; then
    # shellcheck disable=SC1090
    source "${RUNTIME_CREDENTIALS_HELPER}"
fi

DEFAULT_WIFI_SSID="BlockchainLab"
DEFAULT_WIFI_PASSPHRASE="blockchainlab"
DEFAULT_WIFI_CHANNEL=6
DEFAULT_WIFI_GATEWAY="10.13.37.1"
DEFAULT_WIFI_CIDR="10.13.37.1/24"
DEFAULT_WIFI_DHCP_START="10.13.37.50"
DEFAULT_WIFI_DHCP_END="10.13.37.200"
DEFAULT_WIFI_NETMASK="255.255.255.0"
DEFAULT_WIFI_LEASE="12h"
DEFAULT_ETHERNET_GATEWAY="10.13.38.1"
DEFAULT_ETHERNET_CIDR="10.13.38.1/24"
DEFAULT_ETHERNET_DHCP_START="10.13.38.50"
DEFAULT_ETHERNET_DHCP_END="10.13.38.200"
DEFAULT_ETHERNET_NETMASK="255.255.255.0"
DEFAULT_ETHERNET_LEASE="12h"
DEFAULT_STUDENT_PIDS_LIMIT=256
MAX_STUDENT_CAPACITY_LIMIT="${LAB_MANAGER_MAX_STUDENT_CAPACITY_LIMIT:-40}"
DEFAULT_INSTRUCTOR_MAX_STUDENT_CAPACITY="${LAB_MANAGER_DEFAULT_INSTRUCTOR_MAX_STUDENT_CAPACITY:-20}"
DEFAULT_STUDENT_MAX_STUDENT_CAPACITY="${LAB_MANAGER_DEFAULT_STUDENT_MAX_STUDENT_CAPACITY:-5}"
DEFAULT_STUDENT_MODE_WARM_POOL_SIZE="${LAB_MANAGER_DEFAULT_STUDENT_WARM_POOL_SIZE:-3}"
DEFAULT_STUDENT_HOME_DISKS_MODE="auto"
DEFAULT_BITCOIN_STUDENT_HOME_SIZE_MB=512
DEFAULT_CONSENSUS_STUDENT_HOME_SIZE_MB=128
DEFAULT_P2P_TRUST_STUDENT_HOME_SIZE_MB=128
DEFAULT_ETHEREUM_STUDENT_HOME_SIZE_MB=256
DEFAULT_HLF_STUDENT_DISK_SIZE_MB=256
DEFAULT_STUDENT_HOME_DISK_RESERVE_MB=2048

CONFIG_LOADED=0

usage() {
    cat <<'EOF'
Usage:
  ./lab-manager.sh deploy --mode <instructor|student> [options]
  ./lab-manager.sh start <target|all>
  ./lab-manager.sh build-images <target|all> [target ...]
  ./lab-manager.sh stop <target|all>
  ./lab-manager.sh status [target|all]
  ./lab-manager.sh cleanup <student-home-disks>
  ./lab-manager.sh list

Managed targets:
  router, course-site, instructor-auth-service, ethereum_lab, bitcoin, consensus, cryptography, p2p_trust, exercises, quiz-engine-v2, hlf

Deploy options:
  --mode <instructor|student>
  --max-student-capacity N   Base lane capacity for claim-based labs (default instructor: 20, max: 40)
  --bitcoin-student-capacity N
  --consensus-student-capacity N
  --p2p-trust-student-capacity N
  --ethereum-student-capacity N
  --hlf-student-capacity N
  --no-tls
  --wifi-bridge <iface>
  --wifi-ssid <ssid>
  --wifi-passphrase <passphrase>
  --ethernet-lan <iface>
  --ethernet-gateway <ip>
  --ethernet-cidr <cidr>
  --ethernet-dhcp-start <ip>
  --ethernet-dhcp-end <ip>
  --clear-classroom-network
  --uplink-iface <iface>

Examples:
  ./lab-manager.sh deploy --mode instructor --max-student-capacity 20
  ./lab-manager.sh deploy --mode student --no-tls
  ./lab-manager.sh deploy --mode student --bitcoin-student-capacity 2 --consensus-student-capacity 8
  sudo ./lab-manager.sh deploy --mode instructor --wifi-bridge wlan0 --wifi-ssid CourseLabs --wifi-passphrase changeme123
  sudo ./lab-manager.sh deploy --mode instructor --ethernet-lan enp2s0 --uplink-iface wlan0
  ./lab-manager.sh start bitcoin
  ./lab-manager.sh start hlf
  ./lab-manager.sh start all
  ./lab-manager.sh build-images bitcoin consensus p2p_trust
  ./lab-manager.sh stop bitcoin
  ./lab-manager.sh status all
  ./lab-manager.sh cleanup student-home-disks
EOF
}

reset_defaults() {
    MODE=""
    HLF_STUDENT_COUNT=""
    MAX_STUDENT_CAPACITY="${MAX_STUDENT_CAPACITY:-}"
    BITCOIN_STUDENT_CAPACITY="${BITCOIN_STUDENT_CAPACITY:-}"
    CONSENSUS_STUDENT_CAPACITY="${CONSENSUS_STUDENT_CAPACITY:-}"
    P2P_TRUST_STUDENT_CAPACITY="${P2P_TRUST_STUDENT_CAPACITY:-}"
    ETHEREUM_STUDENT_CAPACITY="${ETHEREUM_STUDENT_CAPACITY:-}"
    STUDENT_PIDS_LIMIT="${STUDENT_PIDS_LIMIT:-${DEFAULT_STUDENT_PIDS_LIMIT}}"
    STUDENT_HOME_DISKS_MODE="${STUDENT_HOME_DISKS_MODE:-${DEFAULT_STUDENT_HOME_DISKS_MODE}}"
    BITCOIN_STUDENT_HOME_SIZE_MB="${BITCOIN_STUDENT_HOME_SIZE_MB:-${DEFAULT_BITCOIN_STUDENT_HOME_SIZE_MB}}"
    CONSENSUS_STUDENT_HOME_SIZE_MB="${CONSENSUS_STUDENT_HOME_SIZE_MB:-${DEFAULT_CONSENSUS_STUDENT_HOME_SIZE_MB}}"
    P2P_TRUST_STUDENT_HOME_SIZE_MB="${P2P_TRUST_STUDENT_HOME_SIZE_MB:-${DEFAULT_P2P_TRUST_STUDENT_HOME_SIZE_MB}}"
    ETHEREUM_STUDENT_HOME_SIZE_MB="${ETHEREUM_STUDENT_HOME_SIZE_MB:-${DEFAULT_ETHEREUM_STUDENT_HOME_SIZE_MB}}"
    HLF_STUDENT_DISK_SIZE_MB="${HLF_STUDENT_DISK_SIZE_MB:-${DEFAULT_HLF_STUDENT_DISK_SIZE_MB}}"
    STUDENT_HOME_DISK_RESERVE_MB="${STUDENT_HOME_DISK_RESERVE_MB:-${DEFAULT_STUDENT_HOME_DISK_RESERVE_MB}}"
    BITCOIN_STUDENT_HOME_ROOT=""
    CONSENSUS_STUDENT_HOME_ROOT=""
    P2P_TRUST_STUDENT_HOME_ROOT=""
    ETHEREUM_STUDENT_HOME_ROOT=""
    HLF_STUDENT_DISK_ROOT=""
    USE_TLS="true"
    HOST_BIND="0.0.0.0"
    WIFI_BRIDGE=""
    WIFI_SSID="${DEFAULT_WIFI_SSID}"
    WIFI_PASSPHRASE="${DEFAULT_WIFI_PASSPHRASE}"
    WIFI_CHANNEL="${DEFAULT_WIFI_CHANNEL}"
    WIFI_GATEWAY="${DEFAULT_WIFI_GATEWAY}"
    WIFI_CIDR="${DEFAULT_WIFI_CIDR}"
    WIFI_DHCP_START="${DEFAULT_WIFI_DHCP_START}"
    WIFI_DHCP_END="${DEFAULT_WIFI_DHCP_END}"
    WIFI_NETMASK="${DEFAULT_WIFI_NETMASK}"
    WIFI_LEASE="${DEFAULT_WIFI_LEASE}"
    CLEAR_CLASSROOM_NETWORK=0
    ETHERNET_LAN_IFACE=""
    ETHERNET_GATEWAY="${DEFAULT_ETHERNET_GATEWAY}"
    ETHERNET_CIDR="${DEFAULT_ETHERNET_CIDR}"
    ETHERNET_DHCP_START="${DEFAULT_ETHERNET_DHCP_START}"
    ETHERNET_DHCP_END="${DEFAULT_ETHERNET_DHCP_END}"
    ETHERNET_NETMASK="${DEFAULT_ETHERNET_NETMASK}"
    ETHERNET_LEASE="${DEFAULT_ETHERNET_LEASE}"
    UPLINK_IFACE=""
}

load_state() {
    reset_defaults
    if [[ -f "${STATE_FILE}" ]]; then
        # shellcheck disable=SC1090
        source "${STATE_FILE}"
        CONFIG_LOADED=1
    fi
}

save_state() {
    {
        printf 'MODE=%q\n' "${MODE}"
        printf 'HLF_STUDENT_COUNT=%q\n' "${HLF_STUDENT_COUNT}"
        printf 'MAX_STUDENT_CAPACITY=%q\n' "${MAX_STUDENT_CAPACITY}"
        printf 'BITCOIN_STUDENT_CAPACITY=%q\n' "${BITCOIN_STUDENT_CAPACITY}"
        printf 'CONSENSUS_STUDENT_CAPACITY=%q\n' "${CONSENSUS_STUDENT_CAPACITY}"
        printf 'P2P_TRUST_STUDENT_CAPACITY=%q\n' "${P2P_TRUST_STUDENT_CAPACITY}"
        printf 'ETHEREUM_STUDENT_CAPACITY=%q\n' "${ETHEREUM_STUDENT_CAPACITY}"
        printf 'STUDENT_PIDS_LIMIT=%q\n' "${STUDENT_PIDS_LIMIT}"
        printf 'STUDENT_HOME_DISKS_MODE=%q\n' "${STUDENT_HOME_DISKS_MODE}"
        printf 'BITCOIN_STUDENT_HOME_SIZE_MB=%q\n' "${BITCOIN_STUDENT_HOME_SIZE_MB}"
        printf 'CONSENSUS_STUDENT_HOME_SIZE_MB=%q\n' "${CONSENSUS_STUDENT_HOME_SIZE_MB}"
        printf 'P2P_TRUST_STUDENT_HOME_SIZE_MB=%q\n' "${P2P_TRUST_STUDENT_HOME_SIZE_MB}"
        printf 'ETHEREUM_STUDENT_HOME_SIZE_MB=%q\n' "${ETHEREUM_STUDENT_HOME_SIZE_MB}"
        printf 'HLF_STUDENT_DISK_SIZE_MB=%q\n' "${HLF_STUDENT_DISK_SIZE_MB}"
        printf 'STUDENT_HOME_DISK_RESERVE_MB=%q\n' "${STUDENT_HOME_DISK_RESERVE_MB}"
        printf 'BITCOIN_STUDENT_HOME_ROOT=%q\n' "${BITCOIN_STUDENT_HOME_ROOT}"
        printf 'CONSENSUS_STUDENT_HOME_ROOT=%q\n' "${CONSENSUS_STUDENT_HOME_ROOT}"
        printf 'P2P_TRUST_STUDENT_HOME_ROOT=%q\n' "${P2P_TRUST_STUDENT_HOME_ROOT}"
        printf 'ETHEREUM_STUDENT_HOME_ROOT=%q\n' "${ETHEREUM_STUDENT_HOME_ROOT}"
        printf 'HLF_STUDENT_DISK_ROOT=%q\n' "${HLF_STUDENT_DISK_ROOT}"
        printf 'USE_TLS=%q\n' "${USE_TLS}"
        printf 'HOST_BIND=%q\n' "${HOST_BIND}"
        printf 'WIFI_BRIDGE=%q\n' "${WIFI_BRIDGE}"
        printf 'WIFI_SSID=%q\n' "${WIFI_SSID}"
        printf 'WIFI_PASSPHRASE=%q\n' "${WIFI_PASSPHRASE}"
        printf 'WIFI_CHANNEL=%q\n' "${WIFI_CHANNEL}"
        printf 'WIFI_GATEWAY=%q\n' "${WIFI_GATEWAY}"
        printf 'WIFI_CIDR=%q\n' "${WIFI_CIDR}"
        printf 'WIFI_DHCP_START=%q\n' "${WIFI_DHCP_START}"
        printf 'WIFI_DHCP_END=%q\n' "${WIFI_DHCP_END}"
        printf 'WIFI_NETMASK=%q\n' "${WIFI_NETMASK}"
        printf 'WIFI_LEASE=%q\n' "${WIFI_LEASE}"
        printf 'ETHERNET_LAN_IFACE=%q\n' "${ETHERNET_LAN_IFACE}"
        printf 'ETHERNET_GATEWAY=%q\n' "${ETHERNET_GATEWAY}"
        printf 'ETHERNET_CIDR=%q\n' "${ETHERNET_CIDR}"
        printf 'ETHERNET_DHCP_START=%q\n' "${ETHERNET_DHCP_START}"
        printf 'ETHERNET_DHCP_END=%q\n' "${ETHERNET_DHCP_END}"
        printf 'ETHERNET_NETMASK=%q\n' "${ETHERNET_NETMASK}"
        printf 'ETHERNET_LEASE=%q\n' "${ETHERNET_LEASE}"
        printf 'UPLINK_IFACE=%q\n' "${UPLINK_IFACE}"
    } > "${STATE_FILE}"

    if declare -F runtime_fix_path_ownership >/dev/null 2>&1; then
        runtime_fix_path_ownership "${STATE_FILE}"
    fi
}

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        echo "This operation requires root privileges."
        exit 1
    fi
}

load_runtime_credentials() {
    if ! declare -F export_runtime_credentials >/dev/null 2>&1; then
        # shellcheck disable=SC1090
        source "${RUNTIME_CREDENTIALS_HELPER}"
    fi
    export_runtime_credentials "${ROTATE_RUNTIME_CREDENTIALS:-0}"
}

compose_up_cmd() {
    local dir="$1"
    shift
    (
        cd "${dir}"
        local hlf_platform hlf_ttyd_arch
        hlf_platform="$(default_hlf_platform)"
        hlf_ttyd_arch="$(hlf_platform_to_ttyd_arch "${hlf_platform}")"
        export HLF_STUDENT_COUNT
        export MAX_STUDENT_CAPACITY
        export BITCOIN_STUDENT_CAPACITY
        export CONSENSUS_STUDENT_CAPACITY
        export P2P_TRUST_STUDENT_CAPACITY
        export ETHEREUM_STUDENT_CAPACITY
        export STUDENT_PIDS_LIMIT
        export BITCOIN_STUDENT_HOME_ROOT
        export CONSENSUS_STUDENT_HOME_ROOT
        export P2P_TRUST_STUDENT_HOME_ROOT
        export ETHEREUM_STUDENT_HOME_ROOT
        export HLF_STUDENT_DISK_ROOT
        export HLF_PLATFORM="${HLF_PLATFORM:-${hlf_platform}}"
        export HLF_TTYD_ARCH="${HLF_TTYD_ARCH:-${hlf_ttyd_arch}}"
        if [[ -z "${STUDENT_WARM_POOL_SIZE:-}" && "${MODE:-}" == "student" ]]; then
            export STUDENT_WARM_POOL_SIZE="$(default_student_mode_warm_pool_size)"
        fi
        if [[ -z "${HLF_CLAIM_WARM_POOL_SIZE:-}" && "${MODE:-}" == "student" ]]; then
            export HLF_CLAIM_WARM_POOL_SIZE="$(default_hlf_mode_warm_pool_size)"
        fi
        if [[ -f "${BASE_DIR}/.runtime/runtime-secrets.env" ]]; then
            docker compose --env-file "${BASE_DIR}/.runtime/runtime-secrets.env" "$@"
        else
            docker compose "$@"
        fi
    )
}

default_hlf_platform() {
    case "$(uname -m)" in
        x86_64) echo "linux/amd64" ;;
        aarch64|arm64) echo "linux/arm64" ;;
        *) echo "linux/amd64" ;;
    esac
}

hlf_platform_to_ttyd_arch() {
    case "$1" in
        linux/amd64) echo "x86_64" ;;
        linux/arm64) echo "aarch64" ;;
        *) echo "x86_64" ;;
    esac
}

default_max_student_capacity_for_mode() {
    case "${1:-student}" in
        instructor) echo "${DEFAULT_INSTRUCTOR_MAX_STUDENT_CAPACITY}" ;;
        student) echo "${DEFAULT_STUDENT_MAX_STUDENT_CAPACITY}" ;;
        *) echo "${DEFAULT_STUDENT_MAX_STUDENT_CAPACITY}" ;;
    esac
}

normalize_capacity() {
    local value="$1"
    local fallback="$2"

    if [[ ! "${value}" =~ ^[0-9]+$ ]] || [[ "${value}" -lt 1 ]] || [[ "${value}" -gt "${MAX_STUDENT_CAPACITY_LIMIT}" ]]; then
        echo "${fallback}"
    else
        echo "${value}"
    fi
}

effective_lab_capacity() {
    local lab="$1"
    local base_capacity override_var override_value

    base_capacity="$(effective_lane_capacity)"
    case "${lab}" in
        bitcoin) override_var="BITCOIN_STUDENT_CAPACITY" ;;
        consensus) override_var="CONSENSUS_STUDENT_CAPACITY" ;;
        p2p_trust) override_var="P2P_TRUST_STUDENT_CAPACITY" ;;
        ethereum_lab) override_var="ETHEREUM_STUDENT_CAPACITY" ;;
        hlf)
            echo "$(hlf_effective_student_count)"
            return
            ;;
        *)
            echo "${base_capacity}"
            return
            ;;
    esac

    override_value="${!override_var:-}"
    echo "$(normalize_capacity "${override_value:-${base_capacity}}" "${base_capacity}")"
}

report_runtime_mode() {
    local capacity mode_default

    capacity="$(effective_lane_capacity)"
    mode_default="$(default_max_student_capacity_for_mode "${MODE:-student}")"
    echo "Lab manager mode: ${MODE:-student} (default lane capacity: ${mode_default}, active base capacity: ${capacity}, pids_limit: ${STUDENT_PIDS_LIMIT}, student_home_disks: ${STUDENT_HOME_DISKS_MODE}, router_bind: $(effective_host_bind))"
}

cloud_runtime_mode() {
    case "${LAB_MANAGER_CLOUD_MODE:-0}" in
        1|true|TRUE|yes|YES|on|ON)
            return 0
            ;;
    esac

    [[ -f "${RUNTIME_DIR}/cloud-domain.txt" ]]
}

report_lane_capacity_config() {
    echo "Claim-based lab capacities:"
    echo "  bitcoin: $(effective_lab_capacity "bitcoin")"
    echo "  consensus: $(effective_lab_capacity "consensus")"
    echo "  p2p_trust: $(effective_lab_capacity "p2p_trust")"
    echo "  ethereum_lab: $(effective_lab_capacity "ethereum_lab")"
    echo "  hlf: $(effective_lab_capacity "hlf")"
}

report_student_home_config() {
    local bitcoin_count consensus_count p2p_count ethereum_count
    local required_mb
    local hlf_count
    local hlf_required_mb

    bitcoin_count="$(effective_lab_capacity "bitcoin")"
    consensus_count="$(effective_lab_capacity "consensus")"
    p2p_count="$(effective_lab_capacity "p2p_trust")"
    ethereum_count="$(effective_lab_capacity "ethereum_lab")"
    required_mb="$(student_home_required_capacity_mb)"
    hlf_count="$(hlf_effective_student_count)"
    hlf_required_mb="$(hlf_student_disk_required_capacity_mb)"

    echo "Student home disk sizing:"
    echo "  bitcoin: ${BITCOIN_STUDENT_HOME_SIZE_MB}MB per lane"
    echo "  consensus: ${CONSENSUS_STUDENT_HOME_SIZE_MB}MB per lane"
    echo "  p2p_trust: ${P2P_TRUST_STUDENT_HOME_SIZE_MB}MB per lane"
    echo "  ethereum_lab: ${ETHEREUM_STUDENT_HOME_SIZE_MB}MB per lane"
    echo "  hlf: ${HLF_STUDENT_DISK_SIZE_MB}MB per lane"
    echo "  reserve: ${STUDENT_HOME_DISK_RESERVE_MB}MB"
    echo "  estimated required free space for claim lanes (bitcoin=${bitcoin_count}, consensus=${consensus_count}, p2p_trust=${p2p_count}, ethereum_lab=${ethereum_count}): ${required_mb}MB"
    echo "  estimated required free space for hlf (${hlf_count} lanes): ${hlf_required_mb}MB"
    if student_home_feature_requested; then
        echo "  roots:"
        echo "    bitcoin: ${BITCOIN_STUDENT_HOME_ROOT:-disabled}"
        echo "    consensus: ${CONSENSUS_STUDENT_HOME_ROOT:-disabled}"
        echo "    p2p_trust: ${P2P_TRUST_STUDENT_HOME_ROOT:-disabled}"
        echo "    ethereum_lab: ${ETHEREUM_STUDENT_HOME_ROOT:-disabled}"
        echo "    hlf: ${HLF_STUDENT_DISK_ROOT:-disabled}"
    else
        echo "  roots: disabled by STUDENT_HOME_DISKS_MODE=${STUDENT_HOME_DISKS_MODE}"
    fi
}

student_home_feature_requested() {
    case "${STUDENT_HOME_DISKS_MODE}" in
        0|false|False|FALSE|off|OFF|disabled|DISABLED|no|NO)
            return 1
            ;;
        *)
            return 0
            ;;
    esac
}

student_home_lab_root() {
    local lab="$1"
    echo "${RUNTIME_DIR}/student-disks/${lab}/mounts"
}

student_home_lab_images_dir() {
    local lab="$1"
    echo "${RUNTIME_DIR}/student-disks/${lab}/images"
}

student_home_required_capacity_mb() {
    local bitcoin_count consensus_count p2p_count ethereum_count
    bitcoin_count="$(effective_lab_capacity "bitcoin")"
    consensus_count="$(effective_lab_capacity "consensus")"
    p2p_count="$(effective_lab_capacity "p2p_trust")"
    ethereum_count="$(effective_lab_capacity "ethereum_lab")"
    echo $(( bitcoin_count * BITCOIN_STUDENT_HOME_SIZE_MB + consensus_count * CONSENSUS_STUDENT_HOME_SIZE_MB + p2p_count * P2P_TRUST_STUDENT_HOME_SIZE_MB + ethereum_count * ETHEREUM_STUDENT_HOME_SIZE_MB + STUDENT_HOME_DISK_RESERVE_MB ))
}

hlf_effective_student_count() {
    local hlf_count
    hlf_count="${HLF_STUDENT_COUNT:-$(effective_lane_capacity)}"
    echo "$(normalize_capacity "${hlf_count}" "$(effective_lane_capacity)")"
}

hlf_student_disk_required_capacity_mb() {
    local count
    count="$(hlf_effective_student_count)"
    echo $(( count * HLF_STUDENT_DISK_SIZE_MB + STUDENT_HOME_DISK_RESERVE_MB ))
}

disable_student_home_disks() {
    local reason="$1"
    BITCOIN_STUDENT_HOME_ROOT=""
    CONSENSUS_STUDENT_HOME_ROOT=""
    P2P_TRUST_STUDENT_HOME_ROOT=""
    ETHEREUM_STUDENT_HOME_ROOT=""
    HLF_STUDENT_DISK_ROOT=""
    echo "Student home disks disabled: ${reason}"
}

disable_hlf_student_disks() {
    local reason="$1"
    HLF_STUDENT_DISK_ROOT=""
    echo "HLF student disks disabled: ${reason}"
}

prepare_student_home_lab() {
    local lab="$1"
    local size_mb="$2"
    local count="$3"
    local mounts_dir images_dir lane img mount created=0 reused=0

    mounts_dir="$(student_home_lab_root "${lab}")"
    images_dir="$(student_home_lab_images_dir "${lab}")"

    printf "  %-14s %d × %dMB ... " "${lab}:" "${count}" "${size_mb}"
    sudo -n mkdir -p "${RUNTIME_DIR}/student-disks"
    sudo -n chown "$(id -u):$(id -g)" "${RUNTIME_DIR}/student-disks"
    mkdir -p "${mounts_dir}" "${images_dir}"
    for ((i = 1; i <= count; i++)); do
        printf -v lane 's%02d' "${i}"
        img="${images_dir}/${lane}.img"
        mount="${mounts_dir}/${lane}"
        mkdir -p "${mount}"
        if ! sudo -n test -f "${img}"; then
            sudo -n truncate -s "${size_mb}M" "${img}"
            sudo -n mkfs.ext4 -q -F -L "${lab}-${lane}" "${img}"
            ((created+=1))
        else
            ((reused+=1))
        fi
        if ! mountpoint -q "${mount}"; then
            sudo -n mount -o loop,nosuid,nodev "${img}" "${mount}"
        fi
    done
    if ((created > 0)); then
        echo "created ${created}, reused ${reused}"
    else
        echo "all ${reused} reused"
    fi
}

configure_student_home_disks() {
    local free_mb required_mb bitcoin_count consensus_count p2p_count ethereum_count

    BITCOIN_STUDENT_HOME_ROOT=""
    CONSENSUS_STUDENT_HOME_ROOT=""
    P2P_TRUST_STUDENT_HOME_ROOT=""
    ETHEREUM_STUDENT_HOME_ROOT=""
    HLF_STUDENT_DISK_ROOT=""

    if ! student_home_feature_requested; then
        disable_hlf_student_disks "disabled by STUDENT_HOME_DISKS_MODE=${STUDENT_HOME_DISKS_MODE}"
        return
    fi

    mkdir -p "${RUNTIME_DIR}"

    if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true >/dev/null 2>&1; then
        disable_hlf_student_disks "passwordless sudo is unavailable"
        return
    fi

    required_mb="$(student_home_required_capacity_mb)"
    free_mb="$(df -Pm "${RUNTIME_DIR}" | awk 'NR==2 {print $4}')"
    echo "Student home disks: mode=${STUDENT_HOME_DISKS_MODE}, need ${required_mb}MB, available ${free_mb:-unknown}MB"
    if [[ -z "${free_mb}" ]] || (( free_mb < required_mb )); then
        disable_hlf_student_disks "need ${required_mb}MB free under ${RUNTIME_DIR}, found ${free_mb:-unknown}MB"
        return
    fi

    bitcoin_count="$(effective_lab_capacity "bitcoin")"
    consensus_count="$(effective_lab_capacity "consensus")"
    p2p_count="$(effective_lab_capacity "p2p_trust")"
    ethereum_count="$(effective_lab_capacity "ethereum_lab")"
    prepare_student_home_lab "bitcoin" "${BITCOIN_STUDENT_HOME_SIZE_MB}" "${bitcoin_count}"
    prepare_student_home_lab "consensus" "${CONSENSUS_STUDENT_HOME_SIZE_MB}" "${consensus_count}"
    prepare_student_home_lab "p2p_trust" "${P2P_TRUST_STUDENT_HOME_SIZE_MB}" "${p2p_count}"
    prepare_student_home_lab "ethereum_lab" "${ETHEREUM_STUDENT_HOME_SIZE_MB}" "${ethereum_count}"
    BITCOIN_STUDENT_HOME_ROOT="$(student_home_lab_root "bitcoin")"
    CONSENSUS_STUDENT_HOME_ROOT="$(student_home_lab_root "consensus")"
    P2P_TRUST_STUDENT_HOME_ROOT="$(student_home_lab_root "p2p_trust")"
    ETHEREUM_STUDENT_HOME_ROOT="$(student_home_lab_root "ethereum_lab")"
    echo "Student home disks: all labs provisioned"
}

configure_hlf_student_disks() {
    local free_mb required_mb count

    HLF_STUDENT_DISK_ROOT=""

    if ! student_home_feature_requested; then
        disable_student_home_disks "disabled by STUDENT_HOME_DISKS_MODE=${STUDENT_HOME_DISKS_MODE}"
        return
    fi

    mkdir -p "${RUNTIME_DIR}"

    if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true >/dev/null 2>&1; then
        disable_student_home_disks "passwordless sudo is unavailable"
        return
    fi

    required_mb="$(hlf_student_disk_required_capacity_mb)"
    free_mb="$(df -Pm "${RUNTIME_DIR}" | awk 'NR==2 {print $4}')"
    echo "HLF student disks: need ${required_mb}MB, available ${free_mb:-unknown}MB"
    if [[ -z "${free_mb}" ]] || (( free_mb < required_mb )); then
        disable_student_home_disks "need ${required_mb}MB free under ${RUNTIME_DIR}, found ${free_mb:-unknown}MB"
        return
    fi

    count="$(hlf_effective_student_count)"
    prepare_student_home_lab "hlf" "${HLF_STUDENT_DISK_SIZE_MB}" "${count}"
    HLF_STUDENT_DISK_ROOT="$(student_home_lab_root "hlf")"
}

teardown_student_home_disks() {
    local root mount

    if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true >/dev/null 2>&1; then
        return
    fi

    for root in "$(student_home_lab_root "bitcoin")" "$(student_home_lab_root "consensus")" "$(student_home_lab_root "p2p_trust")" "$(student_home_lab_root "ethereum_lab")" "$(student_home_lab_root "hlf")"; do
        [[ -d "${root}" ]] || continue
        while IFS= read -r mount; do
            if mountpoint -q "${mount}"; then
                sudo -n umount "${mount}" || true
            fi
        done < <(find "${root}" -mindepth 1 -maxdepth 1 -type d | sort -r)
    done
}

teardown_student_home_lab_disks() {
    local lab="$1"
    local root mount

    if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true >/dev/null 2>&1; then
        return
    fi

    root="$(student_home_lab_root "${lab}")"
    [[ -d "${root}" ]] || return
    while IFS= read -r mount; do
        if mountpoint -q "${mount}"; then
            sudo -n umount "${mount}" || true
        fi
    done < <(find "${root}" -mindepth 1 -maxdepth 1 -type d | sort -r)
}

cleanup_student_home_artifacts() {
    local root images_dir mount failed=0

    if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true >/dev/null 2>&1; then
        echo "cleanup student-home-disks requires passwordless sudo."
        exit 1
    fi

    for root in "$(student_home_lab_root "bitcoin")" "$(student_home_lab_root "consensus")" "$(student_home_lab_root "p2p_trust")" "$(student_home_lab_root "ethereum_lab")" "$(student_home_lab_root "hlf")"; do
        [[ -d "${root}" ]] || continue
        while IFS= read -r mount; do
            if mountpoint -q "${mount}"; then
                if ! sudo -n umount "${mount}"; then
                    echo "Failed to unmount ${mount}. Stop lane-service and any containers using it, then retry." >&2
                    failed=1
                fi
            fi
        done < <(find "${root}" -mindepth 1 -maxdepth 1 -type d | sort -r)
    done

    if (( failed != 0 )); then
        exit 1
    fi

    for root in "$(student_home_lab_root "bitcoin")" "$(student_home_lab_root "consensus")" "$(student_home_lab_root "p2p_trust")" "$(student_home_lab_root "ethereum_lab")" "$(student_home_lab_root "hlf")"; do
        images_dir="${root%/mounts}/images"
        [[ -d "${root}" ]] && sudo -n rm -rf "${root}"
        [[ -d "${images_dir}" ]] && sudo -n rm -rf "${images_dir}"
        sudo -n rmdir --ignore-fail-on-non-empty "$(dirname "${root}")" 2>/dev/null || true
        sudo -n rmdir --ignore-fail-on-non-empty "$(dirname "$(dirname "${root}")")" 2>/dev/null || true
    done
}

ensure_networks() {
    # Shared networks used by the outer router + per-lab split networks.
    # Phase 8.x consolidation: each lab's student/instructor containers
    # live on isolated nets (instructor net is internal-only so a student
    # shell cannot reach the instructor backend). The outer router joins
    # both and is the only auth boundary.
    # Format: "<name>:<flags>". Instructor nets are --internal so a
    # student ttyd shell cannot reach the instructor backend by
    # hostname/IP even on the same Docker host.
    local nets=(
        "router-net:"
        "consensus-student-net:--internal"
        "consensus-instructor-net:--internal"
        "p2p-trust-student-net:--internal"
        "p2p-trust-instructor-net:--internal"
        # Bitcoin uses two --internal nets. bitcoind P2P gossip over
        # bitcoin-p2p-net; ttyd/static-web/mempool-UI via router on
        # bitcoin-mgmt-net. ttyd-bind-mgmt.sh (in the wrapper image)
        # binds ttyd to the mgmt-net interface only.
        "bitcoin-p2p-net:--internal"
        "bitcoin-student-mgmt-net:--internal"
        "bitcoin-instructor-mgmt-net:--internal"
        # Phase 8.5
        "crypto-student-net:--internal"
        "crypto-instructor-net:--internal"
        # Ethereum: shared instructor + on-demand lanes (mirrors bitcoin
        # split). rpc-net carries hardhat JSON-RPC + pool fetch between
        # lanes and instructor; mgmt nets are router-facing.
        "ethereum-rpc-net:--internal"
        "ethereum-student-mgmt-net:--internal"
        "ethereum-instructor-mgmt-net:--internal"
        # HLF: per-peer ttyd terminal networks. Students and instructor
        # consoles are on separate internal nets so students cannot
        # reach consortium/orderer ttyd ports.
        "hlf-student-term:--internal"
        "hlf-instructor-term:--internal"
        # HLF: Fabric test-network creates this, but student/classroom
        # compose files declare it external. Pre-creating avoids a race
        # when consoles start before Fabric bootstrap finishes.
        "fabric_test:"
    )
    local entry name flags
    for entry in "${nets[@]}"; do
        name="${entry%%:*}"
        flags="${entry#*:}"
        if ! docker network inspect "${name}" >/dev/null 2>&1; then
            # shellcheck disable=SC2086
            docker network create ${flags} "${name}" >/dev/null
        fi
    done
}

router_dir() {
    echo "${BASE_DIR}/router"
}

target_dir() {
    case "$1" in
        router) echo "${BASE_DIR}/router" ;;
        course-site|course_site) echo "${BASE_DIR}/course-site" ;;
        instructor-auth-service|instructor_auth_service|auth-service|auth_service) echo "${BASE_DIR}/instructor_auth_service" ;;
        ethereum|ethereum_lab) echo "${BASE_DIR}/ethereum_lab" ;;
        bitcoin) echo "${BASE_DIR}/bitcoin" ;;
        consensus) echo "${BASE_DIR}/consensus" ;;
        cryptography) echo "${BASE_DIR}/cryptography" ;;
        p2p_trust|p2p-trust) echo "${BASE_DIR}/p2p_trust" ;;
        exercises) echo "${BASE_DIR}/exercises" ;;
        quiz|quiz-engine-v2) echo "${BASE_DIR}/quiz-engine-v2" ;;
        hlf) echo "${BASE_DIR}/hlf" ;;
        lane-service|lane_service) echo "${BASE_DIR}/lane-service" ;;
        *)
            echo "Unknown target: $1" >&2
            exit 1
            ;;
    esac
}

list_targets() {
    cat <<'EOF'
router
course-site
lane-service
instructor-auth-service
ethereum_lab
bitcoin
consensus
cryptography
p2p_trust
exercises
quiz-engine-v2
hlf
EOF
}

effective_lane_capacity() {
    local fallback
    fallback="$(default_max_student_capacity_for_mode "${MODE:-student}")"
    echo "$(normalize_capacity "${MAX_STUDENT_CAPACITY:-${fallback}}" "${fallback}")"
}

default_student_mode_warm_pool_size() {
    local capacity warm_pool

    capacity="$(effective_lane_capacity)"
    warm_pool="${DEFAULT_STUDENT_MODE_WARM_POOL_SIZE}"
    if (( warm_pool < capacity )); then
        echo "${warm_pool}"
    else
        echo "${capacity}"
    fi
}

default_hlf_mode_warm_pool_size() {
    local capacity warm_pool

    capacity="$(hlf_effective_student_count)"
    warm_pool="${DEFAULT_STUDENT_MODE_WARM_POOL_SIZE}"
    if (( warm_pool < capacity )); then
        echo "${warm_pool}"
    else
        echo "${capacity}"
    fi
}

configure_tls() {
    local certs_dir
    certs_dir="$(router_dir)/certs"

    if [[ "${USE_TLS}" == "true" ]]; then
        export NGINX_CONF="nginx-ssl.conf"
        mkdir -p "${certs_dir}"
        if [[ ! -f "${certs_dir}/fullchain.pem" || ! -f "${certs_dir}/privkey.pem" ]]; then
            echo "Generating self-signed certificate for local testing..."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "${certs_dir}/privkey.pem" \
                -out "${certs_dir}/fullchain.pem" \
                -subj "/C=US/ST=State/L=City/O=Courseware/CN=localhost"
        fi
        if declare -F runtime_fix_path_ownership >/dev/null 2>&1; then
            runtime_fix_path_ownership "${certs_dir}"
        fi
    else
        export NGINX_CONF="nginx-http.conf"
    fi
}

classroom_network_requested() {
    [[ -n "${WIFI_BRIDGE}" || -n "${ETHERNET_LAN_IFACE}" ]]
}

effective_host_bind() {
    if classroom_network_requested; then
        echo "0.0.0.0"
    else
        echo "${HOST_BIND}"
    fi
}

configure_classroom_network() {
    local helper_cmd=()

    if ! classroom_network_requested; then
        if [[ "${CLEAR_CLASSROOM_NETWORK}" == "1" ]]; then
            require_root
            if [[ -x "${CLASSROOM_NETWORK_HELPER}" ]]; then
                "${CLASSROOM_NETWORK_HELPER}" disable
            fi
        fi
        return 0
    fi

    require_root

    if [[ ! -x "${CLASSROOM_NETWORK_HELPER}" ]]; then
        echo "Classroom network helper is missing or not executable: ${CLASSROOM_NETWORK_HELPER}"
        exit 1
    fi

    helper_cmd=("${CLASSROOM_NETWORK_HELPER}" apply)

    if [[ -n "${WIFI_BRIDGE}" ]]; then
        helper_cmd+=(
            --wifi-iface "${WIFI_BRIDGE}"
            --wifi-ssid "${WIFI_SSID}"
            --wifi-passphrase "${WIFI_PASSPHRASE}"
            --wifi-channel "${WIFI_CHANNEL}"
            --wifi-gateway "${WIFI_GATEWAY}"
            --wifi-cidr "${WIFI_CIDR}"
            --wifi-dhcp-start "${WIFI_DHCP_START}"
            --wifi-dhcp-end "${WIFI_DHCP_END}"
            --wifi-netmask "${WIFI_NETMASK}"
            --wifi-lease "${WIFI_LEASE}"
        )
    fi

    if [[ -n "${ETHERNET_LAN_IFACE}" ]]; then
        helper_cmd+=(
            --ethernet-iface "${ETHERNET_LAN_IFACE}"
            --ethernet-gateway "${ETHERNET_GATEWAY}"
            --ethernet-cidr "${ETHERNET_CIDR}"
            --ethernet-dhcp-start "${ETHERNET_DHCP_START}"
            --ethernet-dhcp-end "${ETHERNET_DHCP_END}"
            --ethernet-netmask "${ETHERNET_NETMASK}"
            --ethernet-lease "${ETHERNET_LEASE}"
        )
    fi

    if [[ -n "${UPLINK_IFACE}" ]]; then
        helper_cmd+=(--uplink-iface "${UPLINK_IFACE}")
    fi

    "${helper_cmd[@]}"
}

report_classroom_network_config() {
    if ! classroom_network_requested; then
        return
    fi

    echo "Classroom access:"
    if [[ -n "${WIFI_BRIDGE}" ]]; then
        echo "  wifi AP: ${WIFI_BRIDGE} (${WIFI_GATEWAY}, ssid=${WIFI_SSID})"
    fi
    if [[ -n "${ETHERNET_LAN_IFACE}" ]]; then
        echo "  ethernet LAN: ${ETHERNET_LAN_IFACE} (${ETHERNET_GATEWAY})"
    fi
    if [[ -n "${UPLINK_IFACE}" ]]; then
        echo "  uplink NAT: ${UPLINK_IFACE}"
    fi
    echo "  router bind: $(effective_host_bind)"
}

start_router() {
    load_runtime_credentials
    ensure_networks
    local router_bind

    local cloud_domain_file="${RUNTIME_DIR}/cloud-domain.txt"
    if [[ -f "${cloud_domain_file}" ]]; then
        local cloud_domain
        cloud_domain="$(cat "${cloud_domain_file}")"
        echo "Starting router in cloud mode (${cloud_domain})..."
        (
            cd "$(router_dir)"
            export STUDENT_PIDS_LIMIT
            HOST_BIND="0.0.0.0" DOMAIN="${cloud_domain}" docker compose \
                --env-file "${BASE_DIR}/.runtime/runtime-secrets.env" \
                -f docker-compose.yml -f docker-compose.cloud.yml up -d
        )
        return
    fi

    configure_tls
    router_bind="$(effective_host_bind)"
    echo "Starting router on ${router_bind}..."
    (
        cd "$(router_dir)"
        export STUDENT_PIDS_LIMIT
        if [[ -f "${BASE_DIR}/.runtime/runtime-secrets.env" ]]; then
            HOST_BIND="${router_bind}" HTTP_PORT=80 TLS_PORT=443 docker compose --env-file "${BASE_DIR}/.runtime/runtime-secrets.env" up -d
        else
            HOST_BIND="${router_bind}" HTTP_PORT=80 TLS_PORT=443 docker compose up -d
        fi
    )
}

start_lane_service() {
    local dir
    dir="$(target_dir "lane-service")"
    echo "Starting lane-service..."
    compose_up_cmd "${dir}" up -d
}

fix_bind_mount_permissions() {
    # Containers with cap_drop: ALL lose DAC_OVERRIDE, so root inside them
    # cannot traverse 700 directories owned by the host uid. Ensure every
    # directory under BASE_DIR is at least 755 so bind-mounted paths work.
    find "${BASE_DIR}" -type d -perm 700 ! -path '*/lost+found' \
        -exec chmod 755 {} + 2>/dev/null || true
}

start_shared_infra() {
    report_runtime_mode
    fix_bind_mount_permissions
    start_router
    start_project "course-site"
    start_project "instructor-auth-service"
    configure_student_home_disks
    save_state
}

build_lane_images() {
    local dir="$1"
    local zellij_config="${BASE_DIR}/zellij-config.kdl"
    if [[ -f "${zellij_config}" ]] && [[ ! -f "${dir}/zellij-config.kdl" ]]; then
        cp -f "${zellij_config}" "${dir}/zellij-config.kdl"
    fi
    (
        cd "${dir}"
        local hlf_platform hlf_ttyd_arch
        local force_rebuild="false"
        hlf_platform="$(default_hlf_platform)"
        hlf_ttyd_arch="$(hlf_platform_to_ttyd_arch "${hlf_platform}")"
        export HLF_PLATFORM="${HLF_PLATFORM:-${hlf_platform}}"
        export HLF_TTYD_ARCH="${HLF_TTYD_ARCH:-${hlf_ttyd_arch}}"
        if [[ "$(basename "${dir}")" == "hlf" ]]; then
            echo "  Preparing HLF build assets..."
            if cloud_runtime_mode; then
                export HLF_ALLOW_RUNTIME_DOWNLOADS="${HLF_ALLOW_RUNTIME_DOWNLOADS:-1}"
            fi
            bash ./lab.sh prepare-build-assets
        fi
        local -a _profile_services _default_services _lane_only_services
        mapfile -t _profile_services < <(docker compose --profile build-only config --services 2>/dev/null)
        mapfile -t _default_services < <(docker compose config --services 2>/dev/null)
        _lane_only_services=()
        for _svc in "${_profile_services[@]}"; do
            printf '%s\n' "${_default_services[@]}" | grep -qxF "${_svc}" || _lane_only_services+=("${_svc}")
        done
        if [[ ${#_lane_only_services[@]} -gt 0 ]]; then
            local -a _build_services=()
            local _svc_image
            if [[ "${force_rebuild}" == "true" ]]; then
                _build_services=("${_lane_only_services[@]}")
            else
                for _svc in "${_lane_only_services[@]}"; do
                    _svc_image="$(docker compose --profile build-only config --format json 2>/dev/null \
                        | python3 -c "import sys,json; s=json.load(sys.stdin)['services'].get('${_svc}',{}); print(s.get('image',''))" 2>/dev/null)" || true
                    if [[ -n "${_svc_image}" ]] && docker image inspect "${_svc_image}" >/dev/null 2>&1; then
                        continue
                    fi
                    _build_services+=("${_svc}")
                done
            fi
            if [[ ${#_build_services[@]} -eq 0 ]]; then
                echo "  Lane images already cached: ${_lane_only_services[*]}"
            else
                if [[ "${force_rebuild}" == "true" ]]; then
                    echo "  Rebuilding lane images (build-only profile): ${_build_services[*]}"
                else
                    echo "  Building lane images (build-only profile): ${_build_services[*]}"
                fi
                local build_output build_rc=0
                build_output="$(docker compose --profile build-only build "${_build_services[@]}" 2>&1)" || build_rc=$?
                echo "${build_output}" | tail -3
                if [[ ${build_rc} -ne 0 ]]; then
                    echo "  WARNING: Image build failed (exit code ${build_rc}). Some student lanes may not start."
                    echo "  Build output:"
                    echo "${build_output}" | tail -20 | sed 's/^/    /'
                fi
            fi
        fi
    )
}

start_project() {
    local target="$1"
    local dir
    local -a cmd

    dir="$(target_dir "${target}")"
    cmd=(up -d)
    load_runtime_credentials

    if [[ "${target}" == "hlf" ]]; then
        configure_hlf_student_disks
        save_state
    fi

    echo "Starting ${target}..."
    build_lane_images "${dir}"
    if [[ "${target}" == "quiz" || "${target}" == "quiz-engine-v2" ]]; then
        QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=shared INSTRUCTOR_AUTH_MODE=shared compose_up_cmd "${dir}" "${cmd[@]}"
    else
        compose_up_cmd "${dir}" "${cmd[@]}"
    fi
}

stop_project() {
    local target="$1"
    local dir

    dir="$(target_dir "${target}")"
    echo "Stopping ${target}..."
    compose_up_cmd "${dir}" down
}

status_project() {
    local target="$1"
    local dir

    dir="$(target_dir "${target}")"
    echo "=== ${target} ==="
    compose_up_cmd "${dir}" ps || true
    echo
}

parse_integer() {
    if [[ ! "$1" =~ ^[0-9]+$ ]] || [[ "$1" -lt 1 ]]; then
        echo "Expected a positive integer, got: $1"
        exit 1
    fi
}

parse_capacity() {
    parse_integer "$1"
    if [[ "$1" -gt "${MAX_STUDENT_CAPACITY_LIMIT}" ]]; then
        echo "Capacity must be ${MAX_STUDENT_CAPACITY_LIMIT} or less, got: $1"
        exit 1
    fi
}

parse_deploy_args() {
    local provided_mode=""
    local provided_capacity=""
    local provided_bitcoin_capacity=""
    local provided_consensus_capacity=""
    local provided_p2p_capacity=""
    local provided_ethereum_capacity=""
    local provided_hlf_capacity=""
    local mode_default_capacity=""
    local previous_mode=""
    local previous_base_capacity=""
    local carry_forward_capacities=1

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --mode)
                provided_mode="${2:-}"
                shift 2
                ;;
            --students)
                echo "--students is no longer supported. Shared labs use singleton containers; use --max-student-capacity for claim-based labs."
                exit 1
                ;;
            --max-student-capacity)
                provided_capacity="${2:-}"
                parse_capacity "${provided_capacity}"
                shift 2
                ;;
            --bitcoin-student-capacity)
                provided_bitcoin_capacity="${2:-}"
                parse_capacity "${provided_bitcoin_capacity}"
                shift 2
                ;;
            --consensus-student-capacity)
                provided_consensus_capacity="${2:-}"
                parse_capacity "${provided_consensus_capacity}"
                shift 2
                ;;
            --p2p-trust-student-capacity)
                provided_p2p_capacity="${2:-}"
                parse_capacity "${provided_p2p_capacity}"
                shift 2
                ;;
            --ethereum-student-capacity)
                provided_ethereum_capacity="${2:-}"
                parse_capacity "${provided_ethereum_capacity}"
                shift 2
                ;;
            --hlf-student-capacity)
                provided_hlf_capacity="${2:-}"
                parse_capacity "${provided_hlf_capacity}"
                shift 2
                ;;
            --no-tls)
                USE_TLS="false"
                shift
                ;;
            --wifi-bridge)
                WIFI_BRIDGE="${2:-}"
                shift 2
                ;;
            --wifi-ssid)
                WIFI_SSID="${2:-}"
                shift 2
                ;;
            --wifi-passphrase)
                WIFI_PASSPHRASE="${2:-}"
                shift 2
                ;;
            --ethernet-lan)
                ETHERNET_LAN_IFACE="${2:-}"
                shift 2
                ;;
            --ethernet-gateway)
                ETHERNET_GATEWAY="${2:-}"
                shift 2
                ;;
            --ethernet-cidr)
                ETHERNET_CIDR="${2:-}"
                shift 2
                ;;
            --ethernet-dhcp-start)
                ETHERNET_DHCP_START="${2:-}"
                shift 2
                ;;
            --ethernet-dhcp-end)
                ETHERNET_DHCP_END="${2:-}"
                shift 2
                ;;
            --clear-classroom-network)
                CLEAR_CLASSROOM_NETWORK=1
                WIFI_BRIDGE=""
                ETHERNET_LAN_IFACE=""
                UPLINK_IFACE=""
                shift
                ;;
            --ethernet-netmask)
                ETHERNET_NETMASK="${2:-}"
                shift 2
                ;;
            --ethernet-lease)
                ETHERNET_LEASE="${2:-}"
                shift 2
                ;;
            --uplink-iface)
                UPLINK_IFACE="${2:-}"
                shift 2
                ;;
            *)
                echo "Unknown deploy option: $1"
                exit 1
                ;;
        esac
    done

    if [[ -z "${provided_mode}" ]]; then
        echo "deploy requires --mode <instructor|student>"
        exit 1
    fi

    previous_mode="${MODE:-}"
    if [[ -n "${previous_mode}" ]]; then
        previous_base_capacity="$(normalize_capacity "${MAX_STUDENT_CAPACITY:-$(default_max_student_capacity_for_mode "${previous_mode}")}" "$(default_max_student_capacity_for_mode "${previous_mode}")")"
    fi
    MODE="${provided_mode}"
    mode_default_capacity="$(default_max_student_capacity_for_mode "${MODE}")"
    if [[ -z "${previous_mode}" || "${previous_mode}" != "${MODE}" ]]; then
        carry_forward_capacities=0
    fi

    case "${MODE}" in
        instructor)
            HOST_BIND="0.0.0.0"
            ;;
        student)
            HOST_BIND="0.0.0.0"
            if [[ -n "${WIFI_BRIDGE}" ]]; then
                echo "--wifi-bridge is only valid in instructor mode."
                exit 1
            fi
            if [[ -n "${ETHERNET_LAN_IFACE}" ]]; then
                echo "--ethernet-lan is only valid in instructor mode."
                exit 1
            fi
            ;;
        *)
            echo "Invalid mode: ${MODE}. Choose instructor or student."
            exit 1
            ;;
    esac

    if [[ "${carry_forward_capacities}" == "1" ]]; then
        MAX_STUDENT_CAPACITY="$(normalize_capacity "${provided_capacity:-${MAX_STUDENT_CAPACITY:-${mode_default_capacity}}}" "${mode_default_capacity}")"
        if [[ -n "${provided_bitcoin_capacity}" ]]; then
            BITCOIN_STUDENT_CAPACITY="$(normalize_capacity "${provided_bitcoin_capacity}" "${MAX_STUDENT_CAPACITY}")"
        elif [[ -n "${BITCOIN_STUDENT_CAPACITY:-}" && -n "${previous_base_capacity}" && "${BITCOIN_STUDENT_CAPACITY}" != "${previous_base_capacity}" ]]; then
            BITCOIN_STUDENT_CAPACITY="$(normalize_capacity "${BITCOIN_STUDENT_CAPACITY}" "${MAX_STUDENT_CAPACITY}")"
        else
            BITCOIN_STUDENT_CAPACITY="${MAX_STUDENT_CAPACITY}"
        fi
        if [[ -n "${provided_consensus_capacity}" ]]; then
            CONSENSUS_STUDENT_CAPACITY="$(normalize_capacity "${provided_consensus_capacity}" "${MAX_STUDENT_CAPACITY}")"
        elif [[ -n "${CONSENSUS_STUDENT_CAPACITY:-}" && -n "${previous_base_capacity}" && "${CONSENSUS_STUDENT_CAPACITY}" != "${previous_base_capacity}" ]]; then
            CONSENSUS_STUDENT_CAPACITY="$(normalize_capacity "${CONSENSUS_STUDENT_CAPACITY}" "${MAX_STUDENT_CAPACITY}")"
        else
            CONSENSUS_STUDENT_CAPACITY="${MAX_STUDENT_CAPACITY}"
        fi
        if [[ -n "${provided_p2p_capacity}" ]]; then
            P2P_TRUST_STUDENT_CAPACITY="$(normalize_capacity "${provided_p2p_capacity}" "${MAX_STUDENT_CAPACITY}")"
        elif [[ -n "${P2P_TRUST_STUDENT_CAPACITY:-}" && -n "${previous_base_capacity}" && "${P2P_TRUST_STUDENT_CAPACITY}" != "${previous_base_capacity}" ]]; then
            P2P_TRUST_STUDENT_CAPACITY="$(normalize_capacity "${P2P_TRUST_STUDENT_CAPACITY}" "${MAX_STUDENT_CAPACITY}")"
        else
            P2P_TRUST_STUDENT_CAPACITY="${MAX_STUDENT_CAPACITY}"
        fi
        if [[ -n "${provided_ethereum_capacity}" ]]; then
            ETHEREUM_STUDENT_CAPACITY="$(normalize_capacity "${provided_ethereum_capacity}" "${MAX_STUDENT_CAPACITY}")"
        elif [[ -n "${ETHEREUM_STUDENT_CAPACITY:-}" && -n "${previous_base_capacity}" && "${ETHEREUM_STUDENT_CAPACITY}" != "${previous_base_capacity}" ]]; then
            ETHEREUM_STUDENT_CAPACITY="$(normalize_capacity "${ETHEREUM_STUDENT_CAPACITY}" "${MAX_STUDENT_CAPACITY}")"
        else
            ETHEREUM_STUDENT_CAPACITY="${MAX_STUDENT_CAPACITY}"
        fi
        if [[ -n "${provided_hlf_capacity}" ]]; then
            HLF_STUDENT_COUNT="$(normalize_capacity "${provided_hlf_capacity}" "${MAX_STUDENT_CAPACITY}")"
        elif [[ -n "${HLF_STUDENT_COUNT:-}" && -n "${previous_base_capacity}" && "${HLF_STUDENT_COUNT}" != "${previous_base_capacity}" ]]; then
            HLF_STUDENT_COUNT="$(normalize_capacity "${HLF_STUDENT_COUNT}" "${MAX_STUDENT_CAPACITY}")"
        else
            HLF_STUDENT_COUNT="${MAX_STUDENT_CAPACITY}"
        fi
    else
        MAX_STUDENT_CAPACITY="$(normalize_capacity "${provided_capacity:-${mode_default_capacity}}" "${mode_default_capacity}")"
        BITCOIN_STUDENT_CAPACITY="$(normalize_capacity "${provided_bitcoin_capacity:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
        CONSENSUS_STUDENT_CAPACITY="$(normalize_capacity "${provided_consensus_capacity:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
        P2P_TRUST_STUDENT_CAPACITY="$(normalize_capacity "${provided_p2p_capacity:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
        ETHEREUM_STUDENT_CAPACITY="$(normalize_capacity "${provided_ethereum_capacity:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
        HLF_STUDENT_COUNT="$(normalize_capacity "${provided_hlf_capacity:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
    fi

    if [[ -n "${UPLINK_IFACE}" && -z "${WIFI_BRIDGE}" && -z "${ETHERNET_LAN_IFACE}" ]]; then
        echo "--uplink-iface requires --wifi-bridge and/or --ethernet-lan."
        exit 1
    fi
}

parse_start_args() {
    local target="${1:-}"

    if [[ -z "${target}" ]]; then
        echo "start requires a target or 'all'"
        exit 1
    fi
    shift || true

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --students)
                echo "--students is no longer supported. Shared labs use singleton containers; use --max-student-capacity at deploy time for claim-based labs."
                exit 1
                ;;
            *)
                echo "Unknown start option: $1"
                exit 1
                ;;
        esac
    done

    MAX_STUDENT_CAPACITY="$(normalize_capacity "${MAX_STUDENT_CAPACITY:-$(default_max_student_capacity_for_mode "${MODE:-student}")}" "$(default_max_student_capacity_for_mode "${MODE:-student}")")"
    BITCOIN_STUDENT_CAPACITY="$(normalize_capacity "${BITCOIN_STUDENT_CAPACITY:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
    CONSENSUS_STUDENT_CAPACITY="$(normalize_capacity "${CONSENSUS_STUDENT_CAPACITY:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
    P2P_TRUST_STUDENT_CAPACITY="$(normalize_capacity "${P2P_TRUST_STUDENT_CAPACITY:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
    ETHEREUM_STUDENT_CAPACITY="$(normalize_capacity "${ETHEREUM_STUDENT_CAPACITY:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"
    HLF_STUDENT_COUNT="$(normalize_capacity "${HLF_STUDENT_COUNT:-${MAX_STUDENT_CAPACITY}}" "${MAX_STUDENT_CAPACITY}")"

    start_shared_infra
    if [[ "${target}" == "all" ]]; then
        while read -r managed_target; do
            [[ "${managed_target}" == "router" || "${managed_target}" == "course-site" || "${managed_target}" == "instructor-auth-service" || "${managed_target}" == "lane-service" ]] && continue
            start_project "${managed_target}"
        done < <(list_targets)
        start_lane_service
    else
        if [[ "${target}" == "lane-service" ]]; then
            start_lane_service
        elif [[ "${target}" != "router" && "${target}" != "course-site" && "${target}" != "instructor-auth-service" ]]; then
            start_project "${target}"
            start_lane_service
        fi
    fi
}

parse_stop_args() {
    local target="${1:-all}"

    if [[ "${target}" == "all" ]]; then
        while read -r managed_target; do
            stop_project "${managed_target}"
        done < <(list_targets | tac)
        teardown_student_home_disks
    else
        stop_project "${target}"
        if [[ "${target}" == "lane-service" || "${target}" == "lane_service" ]]; then
            teardown_student_home_disks
        elif [[ "${target}" == "hlf" ]]; then
            teardown_student_home_lab_disks "hlf"
        fi
    fi
}

parse_build_images_args() {
    local targets=("$@")
    local target

    if [[ "${#targets[@]}" -eq 0 ]]; then
        echo "build-images requires one or more targets or 'all'"
        exit 1
    fi

    load_runtime_credentials

    if [[ "${#targets[@]}" -eq 1 && "${targets[0]}" == "all" ]]; then
        while read -r target; do
            [[ "${target}" == "router" || "${target}" == "course-site" || "${target}" == "lane-service" || "${target}" == "instructor-auth-service" ]] && continue
            build_lane_images "$(target_dir "${target}")"
        done < <(list_targets)
        return
    fi

    for target in "${targets[@]}"; do
        build_lane_images "$(target_dir "${target}")"
    done
}

parse_status_args() {
    local target="${1:-all}"

    report_runtime_mode
    report_lane_capacity_config
    report_classroom_network_config
    report_student_home_config
    echo

    if [[ "${target}" == "all" ]]; then
        while read -r managed_target; do
            status_project "${managed_target}"
        done < <(list_targets)
    else
        status_project "${target}"
    fi
}

parse_cleanup_args() {
    local target="${1:-}"

    case "${target}" in
        student-home-disks|student-disks)
            cleanup_student_home_artifacts
            ;;
        *)
            echo "cleanup requires a supported target: student-home-disks"
            exit 1
            ;;
    esac
}

main() {
    local command="${1:-}"
    shift || true

    load_state

    case "${command}" in
        deploy)
            load_runtime_credentials
            parse_deploy_args "$@"
            configure_classroom_network
            save_state
            start_shared_infra
            echo "Deployment config saved to ${STATE_FILE}."
            echo "Instructor credentials written to ${INSTRUCTOR_CREDENTIALS_FILE}."
            echo "Start labs with: ./lab-manager.sh start <target|all>"
            ;;
        start)
            if [[ "${CONFIG_LOADED}" -eq 0 ]]; then
                MODE="student"
                MAX_STUDENT_CAPACITY="$(default_max_student_capacity_for_mode "student")"
            fi
            parse_start_args "$@"
            ;;
        build-images)
            parse_build_images_args "$@"
            ;;
        stop)
            parse_stop_args "$@"
            ;;
        status)
            parse_status_args "$@"
            ;;
        cleanup)
            parse_cleanup_args "$@"
            ;;
        list)
            list_targets
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
}

main "$@"
