#!/usr/bin/env bash
set -euo pipefail

normalize_base_path() {
  local raw_path="${1:-/}"
  if [[ -z "${raw_path}" || "${raw_path}" == "/" ]]; then
    echo ""
    return
  fi

  raw_path="/${raw_path#/}"
  raw_path="${raw_path%/}"
  echo "${raw_path}"
}

render_nginx_config() {
  local base_path="$1"
  local template_path="$2"
  local output_path="$3"
  local rewrite_line=""
  local exact_base_block=""

  if [[ -n "${base_path}" ]]; then
    rewrite_line=$'\t\trewrite ^'"${base_path}"'(/.*)$ $1 break;'
    exact_base_block=$'\tlocation = '"${base_path}"$' {\n\t\treturn 302 '"${base_path}"$'/;\n\t}\n'
  fi

  python3 - "${template_path}" "${output_path}" "${base_path}" "${rewrite_line}" "${exact_base_block}" <<'PY'
from pathlib import Path
import sys

template_path, output_path, base_path, rewrite_line, exact_base_block = sys.argv[1:6]
template = Path(template_path).read_text(encoding="utf-8")
rendered = (
    template
    .replace("__MEMPOOL_BASE_PATH__", base_path)
    .replace("__MEMPOOL_PREFIX_REWRITE__", rewrite_line)
    .replace("__MEMPOOL_EXACT_BASE_LOCATION__", exact_base_block.rstrip("\n"))
)
Path(output_path).write_text(rendered, encoding="utf-8")
PY
}

rewrite_frontend_paths() {
  local web_root="$1"
  local base_path="$2"
  local normalized_output_path="${base_path:-/}"

  python3 - "${web_root}" "${base_path}" "${normalized_output_path}" <<'PY'
from pathlib import Path
import sys

web_root = Path(sys.argv[1])
base_path = sys.argv[2]
normalized_output_path = sys.argv[3]

text_suffixes = {".html", ".js", ".css", ".json", ".xml", ".webmanifest"}
quoted_prefixes = [
    "/resources/",
    "/api/",
    "/docs/",
    "/services/",
    "/testnet4",
    "/testnet/",
    "/testnet",
    "/signet/",
    "/signet",
    "/regtest/",
    "/regtest",
    "/enterprise/",
    "/enterprise",
    "/mempool-block/",
    "/3rdpartylicenses.txt",
]

for path in web_root.rglob("*"):
    if not path.is_file() or path.suffix not in text_suffixes:
        continue

    content = path.read_text(encoding="utf-8")
    updated = content

    if path.suffix == ".html":
        updated = updated.replace('<base href="/', f'<base href="{base_path}/')

    for prefix in quoted_prefixes:
        for quote in ('"', "'", "`"):
            updated = updated.replace(f"{quote}{prefix}", f"{quote}{base_path}{prefix}")

    for prefix in ("/resources/",):
        for marker in ("url(", "url('", 'url("'):
            updated = updated.replace(f"{marker}{prefix}", f"{marker}{base_path}{prefix}")

    # The price service builds its URLs from a dynamic template literal
    # (`${apiBaseUrl}${apiBasePath}/api/v1/...`) where apiBasePath is empty, so the
    # quoted-prefix pass above misses them and they resolve against the site root
    # (ignoring <base href>), 404ing on prefixed deployments. Prefix the dynamic
    # occurrences explicitly — they are preceded by a `}` from the template literal,
    # which never matches the already-prefixed quoted strings. No-op when base_path == "".
    for svc in ("/api/v1/historical-price", "/api/v1/prices"):
        updated = updated.replace(f"}}{svc}", f"}}{base_path}{svc}")

    # The live-update websocket is built as host + port + "{network}/api/v1/ws" ({network} is "" on mainnet), so
    # the quoted-prefix pass misses it too and the dashboard connects to /api/v1/ws, off the prefix, and shows
    # "Offline". Put the prefix in front of {network}. No-op when base_path == "".
    for quote in ('"', "'", "`"):
        updated = updated.replace(f"{quote}{{network}}/api/v1/ws", f"{quote}{base_path}{{network}}/api/v1/ws")

    if updated != content:
        path.write_text(updated, encoding="utf-8")

config_path = web_root / "resources" / "config.js"
if config_path.exists():
    content = config_path.read_text(encoding="utf-8")
    marker = "window.__env.BASE_PATH = "
    if marker in content:
        lines = [line for line in content.splitlines() if marker not in line]
        content = "\n".join(lines).rstrip()
    snippet = (
        "\n(function (window) {\n"
        "  window.__env = window.__env || {};\n"
        f"  window.__env.BASE_PATH = '{normalized_output_path}';\n"
        "}((typeof global !== 'undefined') ? global : this));\n"
    )
    config_path.write_text(content + snippet, encoding="utf-8")
PY
}

main() {
  local base_path
  local requested_path="${MEMPOOL_BASE_PATH:-/}"
  local template_path="${MEMPOOL_NGINX_TEMPLATE:-/etc/nginx/sites-enabled/mempool.conf}"
  local output_path="${MEMPOOL_NGINX_OUTPUT:-/etc/nginx/sites-enabled/mempool.conf}"
  local web_root="${MEMPOOL_WEB_ROOT:-/var/www/mempool/browser}"
  local stamp_path="${MEMPOOL_BASE_PATH_STAMP:-${web_root}/.base-path-applied}"

  base_path="$(normalize_base_path "${requested_path}")"

  render_nginx_config "${base_path}" "${template_path}" "${output_path}"

  if [[ -f "${stamp_path}" ]]; then
    local applied_path
    applied_path="$(cat "${stamp_path}")"
    if [[ "${applied_path}" == "${base_path:-/}" ]]; then
      exit 0
    fi

    echo "mempool base path already applied as ${applied_path}; start a fresh container to change it" >&2
    exit 1
  fi

  rewrite_frontend_paths "${web_root}" "${base_path}"
  printf '%s' "${base_path:-/}" > "${stamp_path}"
}

main "$@"
