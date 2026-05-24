#!/usr/bin/env bash

hlf_is_safe_token() {
  local s="$1"
  [[ -n "$s" ]] || return 1
  [[ "$s" =~ ^[A-Za-z0-9._:/@+-]+$ ]]
}

: "${CHANNEL:=diplomas}"
: "${CC_NAME:=basic}"
: "${ORDERER_ADDRESS:=orderer.example.com:7050}"
: "${ORDERER_TLS_HOSTNAME:=orderer.example.com}"
if [[ -z "${ORDERER_CA_FILE:-}" && -n "${ORDERER_CA:-}" ]]; then
  ORDERER_CA_FILE="${ORDERER_CA}"
fi

: "${PEER0_ORG1_ADDR:=peer0.cascadiastate.example.com:7051}"
: "${PEER0_ORG2_ADDR:=peer0.chesapeakecanoe.example.com:9051}"
: "${PEER0_ORG3_ADDR:=peer0.southhudson.example.com:11051}"
: "${PEER0_ORG4_ADDR:=peer0.mapleleaf.example.com:13051}"

hlf-help() {
  cat <<'EOF'
Available HLF helper commands:
  hlf-help                  Show this command summary
  hlf-files                 List key directories: home, MSP, TLS, ledger storage
  hlf-peerenv               Show peer identity and channel-related environment
  query all                 List all assets on the shared ledger
  query <assetId>           Read a specific asset
  list-assets               Alias for `query all`
  invoke create ...         Submit a new asset transaction
  invoke transfer ...       Transfer an existing asset
  invoke update ...         Update an existing asset
  invoke delete ...         Delete an asset
EOF
}

hlf-files() {
  local label path
  while IFS='|' read -r label path; do
    [[ -n "${path}" ]] || continue
    [[ -e "${path}" ]] || continue
    printf '%s\n' "${label}: ${path}"
    ls -la "${path}" 2>/dev/null | sed 's/^/  /'
    printf '\n'
  done <<EOF
home|${HOME:-/home/student}
msp|${CORE_PEER_MSPCONFIGPATH:-}
tls|/etc/hyperledger/fabric/tls
fabric|/etc/hyperledger/fabric
ledger|/var/hyperledger/production
channel|/opt/hlf-channel
orgs|${HLF_ORGS_DIR:-/opt/hlf-orgs}
EOF
}

list-assets() {
  query all "$@"
}

# Probe which peers look reachable by TCP so that the 3-of-4 endorsement policy
# can still be satisfied after an instructor-triggered peer outage (stopping
# org2 should still allow invokes because org1/org3/org4 remain).
_hlf_peer_live() {
  local addr="$1"
  local host="${addr%%:*}"
  local port="${addr##*:}"
  # bash's /dev/tcp works without extra tools; timeout caps the probe.
  (timeout 1 bash -c "exec 3<>/dev/tcp/${host}/${port}" 2>/dev/null) && return 0
  return 1
}

_hlf_build_peer_conn_parms() {
  PEER_CONN_PARMS=()
  local pairs=(
    "${PEER0_ORG1_ADDR}|${PEER0_ORG1_CA:-}"
    "${PEER0_ORG2_ADDR}|${PEER0_ORG2_CA:-}"
    "${PEER0_ORG3_ADDR}|${PEER0_ORG3_CA:-}"
    "${PEER0_ORG4_ADDR}|${PEER0_ORG4_CA:-}"
  )
  local entry addr ca
  for entry in "${pairs[@]}"; do
    addr="${entry%%|*}"
    ca="${entry##*|}"
    [[ -z "${addr}" || -z "${ca}" ]] && continue
    if _hlf_peer_live "${addr}"; then
      PEER_CONN_PARMS+=(--peerAddresses "${addr}" --tlsRootCertFiles "${ca}")
    fi
  done
}

_hlf_pick_query_peer() {
  QUERY_PEER_ADDR=""
  QUERY_PEER_CA=""
  local pairs=(
    "${PEER0_ORG1_ADDR}|${PEER0_ORG1_CA:-}"
    "${PEER0_ORG2_ADDR}|${PEER0_ORG2_CA:-}"
    "${PEER0_ORG3_ADDR}|${PEER0_ORG3_CA:-}"
    "${PEER0_ORG4_ADDR}|${PEER0_ORG4_CA:-}"
  )
  local entry addr ca
  for entry in "${pairs[@]}"; do
    addr="${entry%%|*}"
    ca="${entry##*|}"
    [[ -z "${addr}" || -z "${ca}" ]] && continue
    if _hlf_peer_live "${addr}"; then
      QUERY_PEER_ADDR="${addr}"
      QUERY_PEER_CA="${ca}"
      return 0
    fi
  done
  return 1
}

invoke() {
  local cmd="${1:-}"
  shift || true

  if [[ -z "${cmd}" || "${cmd}" == "help" || "${cmd}" == "-h" || "${cmd}" == "--help" ]]; then
    echo "Invoke commands:"
    echo "  hlf-help"
    echo "  hlf-files"
    echo "  init-ledger"
    echo "  create <id> <type> <level> <owner> <value> [fieldOfStudy] [degreeType] [issuer]"
    echo "  transfer <id> <newOwner>"
    echo "  update <id> <type> <level> <owner> <value> [fieldOfStudy] [degreeType]"
    echo "  delete <id>"
    echo ""
    echo "Examples:"
    echo "  invoke create diploma-001 credential 4 \"George Washington\" 2024 \"Computer Science\" \"Master of Science\" \"My School\""
    echo "  invoke transfer diploma-001 \"Chesapeake Canoe-Verified\""
    echo "  invoke create shipment-001 cargo 10 \"Cascadia-Exporter\" 50000"
    echo ""
    echo "Forgery check: if <issuer> names any registered school (consortium or peer)"
    echo "but your peer does not belong to that school, the chaincode will reject the"
    echo "transaction — each school can only sign diplomas under its own MSP."
    echo ""
    echo "Vehicle commands (Westview Used-Car Exchange):"
    echo "  seed-westview"
    echo "  create-vehicle <id> <vin> <year> <make> <model> <color> <mileage> <value>"
    echo "  add-service <vehicleId> <serviceCode> <description>"
    echo "  set-title <vehicleId> <status> <detail>              (DMV only)"
    echo "  report-claim <vehicleId> <claimType> <detail>        (Insurance only)"
    echo "  set-inspection <vehicleId> <result> <detail>         (Inspection only)"
    echo "  flag-discrepancy <vehicleId> <flag> <detail>         (AutoFax only)"
    echo "  transfer-vehicle <vehicleId> <newOwner>"
    return 0
  fi

  local payload=""
  if [[ "${cmd}" == "--raw" ]]; then
    payload="${1:-}"
  elif [[ "${cmd}" == \{* ]]; then
    payload="${cmd}"
  elif [[ "${cmd}" == "init-ledger" ]]; then
    payload='{"Args":["InitLedger"]}'
  elif [[ "${cmd}" == "seed-westview" ]]; then
    payload='{"Args":["SeedWestviewInventory"]}'
  elif [[ "${cmd}" == "create" ]]; then
    payload=$(printf '{"Args":["CreateAsset","%s","%s","%s","%s","%s","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}" "${4:-}" "${5:-}" "${6:-}" "${7:-}" "${8:-}")
  elif [[ "${cmd}" == "create-vehicle" ]]; then
    payload=$(printf '{"Args":["CreateVehicle","%s","%s","%s","%s","%s","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}" "${4:-}" "${5:-}" "${6:-}" "${7:-}" "${8:-}")
  elif [[ "${cmd}" == "add-service" ]]; then
    payload=$(printf '{"Args":["AddServiceRecord","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}")
  elif [[ "${cmd}" == "set-title" ]]; then
    payload=$(printf '{"Args":["SetTitleStatus","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}")
  elif [[ "${cmd}" == "report-claim" ]]; then
    payload=$(printf '{"Args":["ReportInsuranceClaim","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}")
  elif [[ "${cmd}" == "set-inspection" ]]; then
    payload=$(printf '{"Args":["SetInspectionResult","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}")
  elif [[ "${cmd}" == "flag-discrepancy" ]]; then
    payload=$(printf '{"Args":["FlagDiscrepancy","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}")
  elif [[ "${cmd}" == "transfer-vehicle" ]]; then
    payload=$(printf '{"Args":["TransferVehicle","%s","%s"]}' "${1:-}" "${2:-}")
  elif [[ "${cmd}" == "transfer" ]]; then
    payload=$(printf '{"Args":["TransferAsset","%s","%s"]}' "$1" "$2")
  elif [[ "${cmd}" == "update" ]]; then
    payload=$(printf '{"Args":["UpdateAsset","%s","%s","%s","%s","%s","%s","%s"]}' "${1:-}" "${2:-}" "${3:-}" "${4:-}" "${5:-}" "${6:-}" "${7:-}")
  elif [[ "${cmd}" == "delete" ]]; then
    payload=$(printf '{"Args":["DeleteAsset","%s"]}' "$1")
  else
    echo "Unknown invoke command: ${cmd}" >&2
    return 2
  fi

  _hlf_build_peer_conn_parms
  # Each live peer contributes 4 array elements: --peerAddresses <addr> --tlsRootCertFiles <ca>
  local live_peers=$(( ${#PEER_CONN_PARMS[@]} / 4 ))
  if (( live_peers < 3 )); then
    echo "[hlf] Only ${live_peers} of 4 peers are reachable." >&2
    echo "[hlf] The channel endorsement policy requires 3-of-4 peers to sign, so this transaction would fail at commit validation." >&2
    echo "[hlf] Refusing to submit. Ask the instructor to recover at least one more peer, then retry." >&2
    echo "ENDORSEMENT_POLICY_FAILURE: insufficient live peers (${live_peers}/4, need 3)"
    return 1
  fi
  # Wait for commit visibility so back-to-back helper commands do not race the ledger.
  peer chaincode invoke -o "${ORDERER_ADDRESS}" \
    --ordererTLSHostnameOverride "${ORDERER_TLS_HOSTNAME}" \
    --tls --cafile "${ORDERER_CA_FILE}" \
    --waitForEvent \
    --waitForEventTimeout "${HLF_WAIT_FOR_EVENT_TIMEOUT:-30s}" \
    "${PEER_CONN_PARMS[@]}" \
    -C "${CHANNEL}" -n "${CC_NAME}" -c "${payload}" 2>&1 | sed $'s/\t/  /g'
  local rc=${PIPESTATUS[0]}
  if (( rc == 0 )); then
    sleep "${HLF_INVOKE_SETTLE_SECONDS:-2}"
  fi
  return "${rc}"
}

query() {
  local cmd="${1:-}"
  shift || true

  if [[ -z "${cmd}" || "${cmd}" == "help" || "${cmd}" == "-h" || "${cmd}" == "--help" ]]; then
    echo "Query commands:"
    echo "  hlf-help"
    echo "  hlf-files"
    echo "  all"
    echo "  <assetId>"
    echo ""
    echo "Examples:"
    echo "  list-assets"
    echo "  query all"
    echo "  query diploma-001"
    return 0
  fi

  local payload=""
  if [[ "${cmd}" == "all" ]]; then
    payload='{"Args":["GetAllAssets"]}'
  else
    payload=$(printf '{"Args":["ReadAsset","%s"]}' "${cmd}")
  fi

  if ! _hlf_pick_query_peer; then
    echo "[hlf] No live consortium peers are reachable for query." >&2
    echo "[hlf] Reads are proxied through a live consortium peer to avoid stale or half-joined student peer state." >&2
    return 1
  fi

  local output
  output=$(peer chaincode query \
    --peerAddresses "${QUERY_PEER_ADDR}" \
    --tlsRootCertFiles "${QUERY_PEER_CA}" \
    -C "${CHANNEL}" -n "${CC_NAME}" -c "${payload}" 2>&1)
  local rc=$?
  if [[ $rc -eq 0 ]] && command -v jq >/dev/null 2>&1; then
    echo "${output}" | jq . 2>/dev/null || echo "${output}"
  else
    echo "${output}" | sed $'s/\t/  /g'
  fi
  return $rc
}
