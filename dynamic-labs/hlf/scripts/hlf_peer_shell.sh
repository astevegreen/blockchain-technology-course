#!/usr/bin/env bash
# Per-peer terminal shell. Runs INSIDE the peer container (not hlf-ttyd).
#
# Reads HLF_* environment variables set by the compose file to configure
# the peer CLI environment. Cross-org TLS CAs are resolved from the
# organizations tree mounted at /opt/hlf-orgs.
set -euo pipefail

ORGS_DIR="${HLF_ORGS_DIR:-/opt/hlf-orgs}"
HELPERS="${HLF_HELPERS:-/opt/hlf-scripts/hlf_cli_helpers.sh}"

: "${HLF_MSP_ID:?}"
: "${HLF_ORG_DOMAIN:?}"
: "${HLF_PEER_ADDRESS:?}"
: "${HLF_PROMPT:=peer}"
: "${HLF_TITLE:=${HLF_ORG_DOMAIN}}"
: "${HLF_ADMIN_USER:=Admin@${HLF_ORG_DOMAIN}}"
: "${HLF_CHANNEL:=diplomas}"
: "${HLF_CC_NAME:=basic}"
: "${HLF_HOME_DIR:=/home/student}"

ADMIN_MSP="${ORGS_DIR}/peerOrganizations/${HLF_ORG_DOMAIN}/users/${HLF_ADMIN_USER}/msp"

ORDERER_CA="${ORGS_DIR}/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"
ORG1_CA="${ORGS_DIR}/peerOrganizations/cascadiastate.example.com/peers/peer0.cascadiastate.example.com/tls/ca.crt"
ORG2_CA="${ORGS_DIR}/peerOrganizations/chesapeakecanoe.example.com/peers/peer0.chesapeakecanoe.example.com/tls/ca.crt"
ORG3_CA="${ORGS_DIR}/peerOrganizations/southhudson.example.com/peers/peer0.southhudson.example.com/tls/ca.crt"
ORG4_CA="${ORGS_DIR}/peerOrganizations/mapleleaf.example.com/peers/peer0.mapleleaf.example.com/tls/ca.crt"

inject_helpers=""
if [[ -f "${HELPERS}" ]]; then
  inject_helpers="source ${HELPERS} 2>/dev/null || true"
fi

student_extra_env=""
if [[ "${HLF_NODE_TYPE:-}" == "student" ]]; then
  EMPLOYER_CA="${ORGS_DIR}/peerOrganizations/meridian.example.com/peers/peer0.meridian.example.com/tls/ca.crt"
  OWN_CA="${ORGS_DIR}/peerOrganizations/${HLF_ORG_DOMAIN}/peers/peer0.${HLF_ORG_DOMAIN}/tls/ca.crt"
  student_extra_env="export EMPLOYER_CA=\"${EMPLOYER_CA}\"
export PEER0_EMPLOYER_CA=\"${EMPLOYER_CA}\"
export OWN_CA=\"${OWN_CA}\"
export EMPLOYER_PEER=\"peer0.meridian.example.com:15051\"
export STUDENT_ID=\"${HLF_STUDENT_ID:-}\"
export STUDENT_MSP=\"${HLF_MSP_ID}\""
fi

mkdir -p "${HLF_HOME_DIR}"

cat > /tmp/hlf-shell-rc <<RC
export TERM=xterm-256color
export SHELL=/bin/bash
export PS1='${HLF_PROMPT}\$ '
export HOME="${HLF_HOME_DIR}"
export HISTFILE="${HLF_HOME_DIR}/.bash_history"

export ORDERER_CA_FILE="${ORDERER_CA}"
export ORDERER_CA="${ORDERER_CA}"
export PEER0_ORG1_CA="${ORG1_CA}"
export PEER0_ORG2_CA="${ORG2_CA}"
export PEER0_ORG3_CA="${ORG3_CA}"
export PEER0_ORG4_CA="${ORG4_CA}"

if [[ -d "${ADMIN_MSP}" ]]; then
  export CORE_PEER_MSPCONFIGPATH="${ADMIN_MSP}"
fi
export CORE_PEER_LOCALMSPID="${HLF_MSP_ID}"
export CORE_PEER_ADDRESS="${HLF_PEER_ADDRESS}"
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt
export CHANNEL="${HLF_CHANNEL}"
export CC_NAME="${HLF_CC_NAME}"

${student_extra_env}
${inject_helpers}
hlf-peerenv() {
  (printenv | sort | egrep '^(CORE_PEER|ORDERER|FABRIC|CHANNEL|CC_NAME)') || true
}
echo "Connected to ${HLF_TITLE}"
RC

if [[ "${HLF_SHELL_RC_ONLY:-0}" == "1" ]]; then
  exit 0
fi

cd "${HLF_HOME_DIR}" 2>/dev/null || cd /
exec bash --rcfile /tmp/hlf-shell-rc -i
