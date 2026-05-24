#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HLF_DIR="${ROOT_DIR}/dynamic-labs/hlf"
RUNTIME_DIR="${HLF_DIR}/runtime"
FABRIC_SAMPLES="${RUNTIME_DIR}/fabric-samples"
INSTALL_SCRIPT="${RUNTIME_DIR}/install-fabric.sh"

FABRIC_VERSION="${HLF_IMAGE_TAG:-2.5.15}"
CA_VERSION="${HLF_CA_IMAGE_TAG:-1.5.17}"

echo "Preparing offline HLF runtime assets in ${FABRIC_SAMPLES}"
rm -rf "${FABRIC_SAMPLES}"

if [[ ! -x "${INSTALL_SCRIPT}" ]]; then
  echo "ERROR: install-fabric.sh not found at ${INSTALL_SCRIPT}"
  exit 1
fi

cd "${RUNTIME_DIR}"
bash "${INSTALL_SCRIPT}" \
  --fabric-version "${FABRIC_VERSION}" \
  --ca-version "${CA_VERSION}" \
  samples binary

test -x "${FABRIC_SAMPLES}/test-network/network.sh"
test -f "${FABRIC_SAMPLES}/test-network/organizations/fabric-ca/registerEnroll.sh"
test -x "${FABRIC_SAMPLES}/bin/peer"
test -x "${FABRIC_SAMPLES}/bin/cryptogen"
test -f "${FABRIC_SAMPLES}/config/core.yaml"

OVERRIDE_SRC="${HLF_DIR}/chaincode_overrides/asset-transfer-basic/chaincode-javascript/lib/assetTransfer.js"
OVERRIDE_DST="${FABRIC_SAMPLES}/asset-transfer-basic/chaincode-javascript/lib/assetTransfer.js"
if [[ -f "${OVERRIDE_SRC}" ]]; then
  echo "Applying chaincode override: ${OVERRIDE_SRC} -> ${OVERRIDE_DST}"
  mkdir -p "$(dirname "${OVERRIDE_DST}")"
  cp -f "${OVERRIDE_SRC}" "${OVERRIDE_DST}"
else
  echo "WARNING: No chaincode override found at ${OVERRIDE_SRC}"
fi

echo "HLF runtime assets prepared."
