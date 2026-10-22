#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
STATE_DIR="/etc/dynamic-labs"
STATE_FILE="${STATE_DIR}/classroom-network.env"
DNSMASQ_CONF="/etc/dnsmasq.d/dynamic-labs.conf"
HOSTAPD_CONF="/etc/hostapd/hostapd.conf"
HOSTAPD_DEFAULT="/etc/default/hostapd"
SYSCTL_CONF="/etc/sysctl.d/99-dynamic-labs-forwarding.conf"
SERVICE_FILE="/etc/systemd/system/dynamic-labs-classroom-network.service"
SERVICE_NAME="dynamic-labs-classroom-network.service"
IPTABLES_COMMENT="dynamic-labs-classroom"

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

reset_defaults() {
    WIFI_IFACE=""
    WIFI_SSID="${DEFAULT_WIFI_SSID}"
    WIFI_PASSPHRASE="${DEFAULT_WIFI_PASSPHRASE}"
    WIFI_CHANNEL="${DEFAULT_WIFI_CHANNEL}"
    WIFI_GATEWAY="${DEFAULT_WIFI_GATEWAY}"
    WIFI_CIDR="${DEFAULT_WIFI_CIDR}"
    WIFI_DHCP_START="${DEFAULT_WIFI_DHCP_START}"
    WIFI_DHCP_END="${DEFAULT_WIFI_DHCP_END}"
    WIFI_NETMASK="${DEFAULT_WIFI_NETMASK}"
    WIFI_LEASE="${DEFAULT_WIFI_LEASE}"

    ETHERNET_IFACE=""
    ETHERNET_GATEWAY="${DEFAULT_ETHERNET_GATEWAY}"
    ETHERNET_CIDR="${DEFAULT_ETHERNET_CIDR}"
    ETHERNET_DHCP_START="${DEFAULT_ETHERNET_DHCP_START}"
    ETHERNET_DHCP_END="${DEFAULT_ETHERNET_DHCP_END}"
    ETHERNET_NETMASK="${DEFAULT_ETHERNET_NETMASK}"
    ETHERNET_LEASE="${DEFAULT_ETHERNET_LEASE}"

    UPLINK_IFACE=""
}

reset_saved_state() {
    SAVED_WIFI_IFACE=""
    SAVED_WIFI_SSID=""
    SAVED_WIFI_PASSPHRASE=""
    SAVED_WIFI_CHANNEL=""
    SAVED_WIFI_GATEWAY=""
    SAVED_WIFI_CIDR=""
    SAVED_WIFI_DHCP_START=""
    SAVED_WIFI_DHCP_END=""
    SAVED_WIFI_NETMASK=""
    SAVED_WIFI_LEASE=""

    SAVED_ETHERNET_IFACE=""
    SAVED_ETHERNET_GATEWAY=""
    SAVED_ETHERNET_CIDR=""
    SAVED_ETHERNET_DHCP_START=""
    SAVED_ETHERNET_DHCP_END=""
    SAVED_ETHERNET_NETMASK=""
    SAVED_ETHERNET_LEASE=""

    SAVED_UPLINK_IFACE=""
}

usage() {
    cat <<'EOF'
Usage:
  sudo ./scripts/classroom-network-helper.sh apply [options]
  sudo ./scripts/classroom-network-helper.sh disable
  sudo ./scripts/classroom-network-helper.sh status

Apply options:
  --wifi-iface <iface>
  --wifi-ssid <ssid>
  --wifi-passphrase <passphrase>
  --wifi-channel <channel>
  --wifi-gateway <ip>
  --wifi-cidr <cidr>
  --wifi-dhcp-start <ip>
  --wifi-dhcp-end <ip>
  --wifi-netmask <netmask>
  --wifi-lease <lease>
  --ethernet-iface <iface>
  --ethernet-gateway <ip>
  --ethernet-cidr <cidr>
  --ethernet-dhcp-start <ip>
  --ethernet-dhcp-end <ip>
  --ethernet-netmask <netmask>
  --ethernet-lease <lease>
  --uplink-iface <iface>

Examples:
  sudo ./scripts/classroom-network-helper.sh apply \
    --wifi-iface wlan0 \
    --wifi-ssid CourseLabs \
    --wifi-passphrase YOUR_PASSPHRASE

  sudo ./scripts/classroom-network-helper.sh apply \
    --ethernet-iface enp2s0 \
    --uplink-iface wlan0

  sudo ./scripts/classroom-network-helper.sh disable
  sudo ./scripts/classroom-network-helper.sh status
EOF
}

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        echo "This operation requires root privileges."
        exit 1
    fi
}

require_command() {
    local cmd="$1"
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        echo "${cmd} is required."
        exit 1
    fi
}

load_saved_state() {
    reset_saved_state
    if [[ -f "${STATE_FILE}" ]]; then
        # shellcheck disable=SC1090
        source "${STATE_FILE}"
    fi
}

save_state() {
    mkdir -p "${STATE_DIR}"
    {
        printf 'SAVED_WIFI_IFACE=%q\n' "${WIFI_IFACE}"
        printf 'SAVED_WIFI_SSID=%q\n' "${WIFI_SSID}"
        printf 'SAVED_WIFI_PASSPHRASE=%q\n' "${WIFI_PASSPHRASE}"
        printf 'SAVED_WIFI_CHANNEL=%q\n' "${WIFI_CHANNEL}"
        printf 'SAVED_WIFI_GATEWAY=%q\n' "${WIFI_GATEWAY}"
        printf 'SAVED_WIFI_CIDR=%q\n' "${WIFI_CIDR}"
        printf 'SAVED_WIFI_DHCP_START=%q\n' "${WIFI_DHCP_START}"
        printf 'SAVED_WIFI_DHCP_END=%q\n' "${WIFI_DHCP_END}"
        printf 'SAVED_WIFI_NETMASK=%q\n' "${WIFI_NETMASK}"
        printf 'SAVED_WIFI_LEASE=%q\n' "${WIFI_LEASE}"
        printf 'SAVED_ETHERNET_IFACE=%q\n' "${ETHERNET_IFACE}"
        printf 'SAVED_ETHERNET_GATEWAY=%q\n' "${ETHERNET_GATEWAY}"
        printf 'SAVED_ETHERNET_CIDR=%q\n' "${ETHERNET_CIDR}"
        printf 'SAVED_ETHERNET_DHCP_START=%q\n' "${ETHERNET_DHCP_START}"
        printf 'SAVED_ETHERNET_DHCP_END=%q\n' "${ETHERNET_DHCP_END}"
        printf 'SAVED_ETHERNET_NETMASK=%q\n' "${ETHERNET_NETMASK}"
        printf 'SAVED_ETHERNET_LEASE=%q\n' "${ETHERNET_LEASE}"
        printf 'SAVED_UPLINK_IFACE=%q\n' "${UPLINK_IFACE}"
    } > "${STATE_FILE}"
}

install_service_unit() {
    cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Dynamic Labs classroom network
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=${SCRIPT_PATH} restore
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}" >/dev/null
}

remove_service_unit() {
    systemctl disable --now "${SERVICE_NAME}" >/dev/null 2>&1 || true
    rm -f "${SERVICE_FILE}"
    systemctl daemon-reload
}

parse_apply_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --wifi-iface)
                WIFI_IFACE="${2:-}"
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
            --wifi-channel)
                WIFI_CHANNEL="${2:-}"
                shift 2
                ;;
            --wifi-gateway)
                WIFI_GATEWAY="${2:-}"
                shift 2
                ;;
            --wifi-cidr)
                WIFI_CIDR="${2:-}"
                shift 2
                ;;
            --wifi-dhcp-start)
                WIFI_DHCP_START="${2:-}"
                shift 2
                ;;
            --wifi-dhcp-end)
                WIFI_DHCP_END="${2:-}"
                shift 2
                ;;
            --wifi-netmask)
                WIFI_NETMASK="${2:-}"
                shift 2
                ;;
            --wifi-lease)
                WIFI_LEASE="${2:-}"
                shift 2
                ;;
            --ethernet-iface)
                ETHERNET_IFACE="${2:-}"
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
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

default_route_iface() {
    ip route show default 2>/dev/null | awk 'NR == 1 { print $5 }'
}

validate_iface() {
    local iface="$1"
    if [[ -z "${iface}" ]]; then
        return
    fi
    if ! ip link show "${iface}" >/dev/null 2>&1; then
        echo "Interface '${iface}' does not exist."
        exit 1
    fi
}

validate_downstream_iface() {
    local iface="$1"
    local name="$2"
    local default_iface

    validate_iface "${iface}"
    [[ -z "${iface}" ]] && return

    if [[ -n "${UPLINK_IFACE}" && "${iface}" == "${UPLINK_IFACE}" ]]; then
        echo "${name} interface '${iface}' cannot also be the uplink."
        exit 1
    fi

    default_iface="$(default_route_iface)"
    if [[ -n "${default_iface}" && "${iface}" == "${default_iface}" ]]; then
        echo "${name} interface '${iface}' is the current default-route interface. Refusing to repurpose it as a classroom LAN."
        exit 1
    fi
}

validate_config() {
    if [[ -z "${WIFI_IFACE}" && -z "${ETHERNET_IFACE}" ]]; then
        echo "apply requires at least one downstream interface."
        exit 1
    fi

    require_command iptables
    require_command dnsmasq

    if [[ -n "${WIFI_IFACE}" ]]; then
        require_command hostapd
        if [[ "${#WIFI_PASSPHRASE}" -lt 8 || "${#WIFI_PASSPHRASE}" -gt 63 ]]; then
            echo "--wifi-passphrase must be between 8 and 63 characters."
            exit 1
        fi
        validate_downstream_iface "${WIFI_IFACE}" "WiFi"
    fi

    if [[ -n "${ETHERNET_IFACE}" ]]; then
        validate_downstream_iface "${ETHERNET_IFACE}" "Ethernet"
    fi

    if [[ -n "${UPLINK_IFACE}" ]]; then
        validate_iface "${UPLINK_IFACE}"
    fi
}

write_hostapd_config() {
    [[ -n "${WIFI_IFACE}" ]] || return

    cat > "${HOSTAPD_CONF}" <<EOF
interface=${WIFI_IFACE}
driver=nl80211
ssid=${WIFI_SSID}
hw_mode=g
channel=${WIFI_CHANNEL}
country_code=US
ieee80211n=1
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=${WIFI_PASSPHRASE}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

    if [[ -f "${HOSTAPD_DEFAULT}" ]]; then
        if grep -q '^DAEMON_CONF=' "${HOSTAPD_DEFAULT}"; then
            sed -i 's|^DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' "${HOSTAPD_DEFAULT}"
        else
            echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> "${HOSTAPD_DEFAULT}"
        fi
    fi
}

write_dnsmasq_config() {
    cat > "${DNSMASQ_CONF}" <<EOF
bind-interfaces
# Scope DNS to classroom interfaces only. This avoids colliding with
# systemd-resolved on loopback while still allowing students to use http://lab/.
except-interface=lo
EOF

    if [[ -n "${WIFI_IFACE}" ]]; then
        cat >> "${DNSMASQ_CONF}" <<EOF
interface=${WIFI_IFACE}
listen-address=${WIFI_GATEWAY}
host-record=lab,${WIFI_GATEWAY}
dhcp-range=set:wifi,${WIFI_DHCP_START},${WIFI_DHCP_END},${WIFI_NETMASK},${WIFI_LEASE}
dhcp-option=tag:wifi,option:router,${WIFI_GATEWAY}
dhcp-option=tag:wifi,option:dns-server,${WIFI_GATEWAY}
EOF
    fi

    if [[ -n "${ETHERNET_IFACE}" ]]; then
        cat >> "${DNSMASQ_CONF}" <<EOF
interface=${ETHERNET_IFACE}
listen-address=${ETHERNET_GATEWAY}
host-record=lab,${ETHERNET_GATEWAY}
dhcp-range=set:ethernet,${ETHERNET_DHCP_START},${ETHERNET_DHCP_END},${ETHERNET_NETMASK},${ETHERNET_LEASE}
dhcp-option=tag:ethernet,option:router,${ETHERNET_GATEWAY}
dhcp-option=tag:ethernet,option:dns-server,${ETHERNET_GATEWAY}
EOF
    fi
}

configure_interface_address() {
    local iface="$1"
    local cidr="$2"

    [[ -n "${iface}" ]] || return

    ip link set "${iface}" down || true
    ip addr flush dev "${iface}" || true
    ip addr add "${cidr}" dev "${iface}"
    ip link set "${iface}" up
}

remove_interface_address() {
    local iface="$1"
    local cidr="$2"

    [[ -n "${iface}" && -n "${cidr}" ]] || return 0
    if ip link show "${iface}" >/dev/null 2>&1; then
        ip addr del "${cidr}" dev "${iface}" 2>/dev/null || true
    fi
}

set_ip_forwarding() {
    local enabled="$1"

    if [[ "${enabled}" == "1" ]]; then
        sysctl -w net.ipv4.ip_forward=1 >/dev/null
        mkdir -p /etc/sysctl.d
        cat > "${SYSCTL_CONF}" <<EOF
net.ipv4.ip_forward=1
EOF
    else
        sysctl -w net.ipv4.ip_forward=0 >/dev/null || true
        rm -f "${SYSCTL_CONF}"
    fi
}

add_nat_rules() {
    local downstream

    [[ -n "${UPLINK_IFACE}" ]] || return

    set_ip_forwarding 1

    iptables -t nat -C POSTROUTING -o "${UPLINK_IFACE}" -m comment --comment "${IPTABLES_COMMENT}" -j MASQUERADE 2>/dev/null \
        || iptables -t nat -A POSTROUTING -o "${UPLINK_IFACE}" -m comment --comment "${IPTABLES_COMMENT}" -j MASQUERADE

    for downstream in "${WIFI_IFACE}" "${ETHERNET_IFACE}"; do
        [[ -n "${downstream}" ]] || continue
        iptables -C FORWARD -i "${UPLINK_IFACE}" -o "${downstream}" -m conntrack --ctstate RELATED,ESTABLISHED -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT 2>/dev/null \
            || iptables -A FORWARD -i "${UPLINK_IFACE}" -o "${downstream}" -m conntrack --ctstate RELATED,ESTABLISHED -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT
        iptables -C FORWARD -i "${downstream}" -o "${UPLINK_IFACE}" -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT 2>/dev/null \
            || iptables -A FORWARD -i "${downstream}" -o "${UPLINK_IFACE}" -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT
    done
}

remove_nat_rules() {
    local uplink="$1"
    shift || true
    local downstream

    [[ -n "${uplink}" ]] || return 0

    while iptables -t nat -C POSTROUTING -o "${uplink}" -m comment --comment "${IPTABLES_COMMENT}" -j MASQUERADE 2>/dev/null; do
        iptables -t nat -D POSTROUTING -o "${uplink}" -m comment --comment "${IPTABLES_COMMENT}" -j MASQUERADE
    done

    for downstream in "$@"; do
        [[ -n "${downstream}" ]] || continue
        while iptables -C FORWARD -i "${uplink}" -o "${downstream}" -m conntrack --ctstate RELATED,ESTABLISHED -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT 2>/dev/null; do
            iptables -D FORWARD -i "${uplink}" -o "${downstream}" -m conntrack --ctstate RELATED,ESTABLISHED -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT
        done
        while iptables -C FORWARD -i "${downstream}" -o "${uplink}" -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT 2>/dev/null; do
            iptables -D FORWARD -i "${downstream}" -o "${uplink}" -m comment --comment "${IPTABLES_COMMENT}" -j ACCEPT
        done
    done
}

stop_services() {
    systemctl stop dnsmasq >/dev/null 2>&1 || true
    systemctl disable dnsmasq >/dev/null 2>&1 || true
    systemctl stop hostapd >/dev/null 2>&1 || true
    systemctl disable hostapd >/dev/null 2>&1 || true
}

cleanup_saved_configuration() {
    load_saved_state

    stop_services
    remove_nat_rules "${SAVED_UPLINK_IFACE}" "${SAVED_WIFI_IFACE}" "${SAVED_ETHERNET_IFACE}"
    remove_interface_address "${SAVED_WIFI_IFACE}" "${SAVED_WIFI_CIDR}"
    remove_interface_address "${SAVED_ETHERNET_IFACE}" "${SAVED_ETHERNET_CIDR}"

    rm -f "${DNSMASQ_CONF}" "${STATE_FILE}" "${SYSCTL_CONF}"

    if [[ -n "${SAVED_UPLINK_IFACE}" ]]; then
        set_ip_forwarding 0
    fi
}

apply_configuration() {
    validate_config

    cleanup_saved_configuration

    if [[ -n "${WIFI_IFACE}" ]]; then
        write_hostapd_config
    fi
    write_dnsmasq_config

    if [[ -n "${WIFI_IFACE}" ]]; then
        systemctl unmask hostapd >/dev/null 2>&1 || true
        configure_interface_address "${WIFI_IFACE}" "${WIFI_CIDR}"
    fi
    if [[ -n "${ETHERNET_IFACE}" ]]; then
        configure_interface_address "${ETHERNET_IFACE}" "${ETHERNET_CIDR}"
    fi

    add_nat_rules

    systemctl enable dnsmasq >/dev/null
    systemctl restart dnsmasq

    if [[ -n "${WIFI_IFACE}" ]]; then
        systemctl enable hostapd >/dev/null
        systemctl restart hostapd
    fi

    save_state

    echo "Classroom network is ready."
    if [[ -n "${WIFI_IFACE}" ]]; then
        echo "  wifi iface:    ${WIFI_IFACE}"
        echo "  wifi ssid:     ${WIFI_SSID}"
        echo "  wifi gateway:  ${WIFI_GATEWAY}"
    fi
    if [[ -n "${ETHERNET_IFACE}" ]]; then
        echo "  ethernet iface:${ETHERNET_IFACE}"
        echo "  ethernet gw:   ${ETHERNET_GATEWAY}"
    fi
    if [[ -n "${UPLINK_IFACE}" ]]; then
        echo "  uplink iface:  ${UPLINK_IFACE}"
    fi

    install_service_unit
}

restore_configuration() {
    require_root
    load_saved_state

    if [[ -z "${SAVED_WIFI_IFACE}" && -z "${SAVED_ETHERNET_IFACE}" ]]; then
        echo "No saved classroom network configuration to restore."
        exit 1
    fi

    WIFI_IFACE="${SAVED_WIFI_IFACE}"
    WIFI_SSID="${SAVED_WIFI_SSID:-${DEFAULT_WIFI_SSID}}"
    WIFI_PASSPHRASE="${SAVED_WIFI_PASSPHRASE:-${DEFAULT_WIFI_PASSPHRASE}}"
    WIFI_CHANNEL="${SAVED_WIFI_CHANNEL:-${DEFAULT_WIFI_CHANNEL}}"
    WIFI_GATEWAY="${SAVED_WIFI_GATEWAY:-${DEFAULT_WIFI_GATEWAY}}"
    WIFI_CIDR="${SAVED_WIFI_CIDR:-${DEFAULT_WIFI_CIDR}}"
    WIFI_DHCP_START="${SAVED_WIFI_DHCP_START:-${DEFAULT_WIFI_DHCP_START}}"
    WIFI_DHCP_END="${SAVED_WIFI_DHCP_END:-${DEFAULT_WIFI_DHCP_END}}"
    WIFI_NETMASK="${SAVED_WIFI_NETMASK:-${DEFAULT_WIFI_NETMASK}}"
    WIFI_LEASE="${SAVED_WIFI_LEASE:-${DEFAULT_WIFI_LEASE}}"

    ETHERNET_IFACE="${SAVED_ETHERNET_IFACE}"
    ETHERNET_GATEWAY="${SAVED_ETHERNET_GATEWAY:-${DEFAULT_ETHERNET_GATEWAY}}"
    ETHERNET_CIDR="${SAVED_ETHERNET_CIDR:-${DEFAULT_ETHERNET_CIDR}}"
    ETHERNET_DHCP_START="${SAVED_ETHERNET_DHCP_START:-${DEFAULT_ETHERNET_DHCP_START}}"
    ETHERNET_DHCP_END="${SAVED_ETHERNET_DHCP_END:-${DEFAULT_ETHERNET_DHCP_END}}"
    ETHERNET_NETMASK="${SAVED_ETHERNET_NETMASK:-${DEFAULT_ETHERNET_NETMASK}}"
    ETHERNET_LEASE="${SAVED_ETHERNET_LEASE:-${DEFAULT_ETHERNET_LEASE}}"

    UPLINK_IFACE="${SAVED_UPLINK_IFACE}"

    apply_configuration
}

show_status() {
    load_saved_state

    if [[ -z "${SAVED_WIFI_IFACE}" && -z "${SAVED_ETHERNET_IFACE}" ]]; then
        echo "Classroom network is not configured."
        return
    fi

    echo "Configured classroom network:"
    if [[ -n "${SAVED_WIFI_IFACE}" ]]; then
        echo "  wifi iface:    ${SAVED_WIFI_IFACE}"
        echo "  wifi ssid:     ${SAVED_WIFI_SSID}"
        echo "  wifi gateway:  ${SAVED_WIFI_GATEWAY}"
    fi
    if [[ -n "${SAVED_ETHERNET_IFACE}" ]]; then
        echo "  ethernet iface:${SAVED_ETHERNET_IFACE}"
        echo "  ethernet gw:   ${SAVED_ETHERNET_GATEWAY}"
    fi
    if [[ -n "${SAVED_UPLINK_IFACE}" ]]; then
        echo "  uplink iface:  ${SAVED_UPLINK_IFACE}"
    fi

    echo "Service state:"
    systemctl is-enabled "${SERVICE_NAME}" 2>/dev/null | sed 's/^/  restore enabled: /' || true
    systemctl is-active "${SERVICE_NAME}" 2>/dev/null | sed 's/^/  restore active:  /' || true
    systemctl is-enabled dnsmasq 2>/dev/null | sed 's/^/  dnsmasq enabled: /' || true
    systemctl is-active dnsmasq 2>/dev/null | sed 's/^/  dnsmasq active:  /' || true
    if [[ -n "${SAVED_WIFI_IFACE}" ]]; then
        systemctl is-enabled hostapd 2>/dev/null | sed 's/^/  hostapd enabled: /' || true
        systemctl is-active hostapd 2>/dev/null | sed 's/^/  hostapd active:  /' || true
    fi
}

main() {
    local command="${1:-}"
    shift || true

    reset_defaults

    case "${command}" in
        apply)
            require_root
            parse_apply_args "$@"
            apply_configuration
            ;;
        disable)
            require_root
            cleanup_saved_configuration
            remove_service_unit
            echo "Classroom network disabled."
            ;;
        restore)
            restore_configuration
            ;;
        status)
            show_status
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
