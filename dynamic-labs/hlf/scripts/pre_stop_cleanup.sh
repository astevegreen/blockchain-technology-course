#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HLF_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${HLF_DIR}"
echo "[hlf pre-stop] running lab.sh down..."
bash ./lab.sh down || true
