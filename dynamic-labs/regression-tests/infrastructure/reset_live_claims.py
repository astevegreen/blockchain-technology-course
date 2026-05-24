#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

DEFAULT_BASE_URL = "http://127.0.0.1"
DEFAULT_CREDENTIALS = Path(__file__).resolve().parents[2] / ".runtime" / "instructor-credentials.txt"
LAB_ENDPOINTS = {
    "bitcoin": {
        "list": "/api/bitcoin/claims",
        "delete_prefix": "/api/bitcoin/claims/",
    },
    "consensus": {
        "list": "/api/consensus/claims",
        "delete_prefix": "/api/consensus/claims/",
    },
    "p2p_trust": {
        "list": "/api/p2p_trust/claims",
        "delete_prefix": "/api/p2p_trust/claims/",
    },
    "ethereum_lab": {
        "list": "/api/ethereum/claims",
        "delete_prefix": "/api/ethereum/claims/",
    },
    "hlf": {
        "list": "/labs/hlf/api/hlf/claims",
        "delete_prefix": "/labs/hlf/api/hlf/claims/",
    },
}

_USERNAME_RE = re.compile(r"Username:\s*(.+)")
_PASSWORD_RE = re.compile(r"Password:\s*(.+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Release active lab claims before MCP/browser phases.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for the live lab environment.")
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=DEFAULT_CREDENTIALS,
        help="Path to .runtime/instructor-credentials.txt",
    )
    parser.add_argument(
        "--lab",
        action="append",
        choices=sorted(LAB_ENDPOINTS.keys()),
        help="Limit claim reset to one or more labs. Defaults to all claim-managed labs.",
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Request wipe=1 when releasing claims.",
    )
    return parser.parse_args()


def parse_credentials(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    username = _USERNAME_RE.search(content)
    password = _PASSWORD_RE.search(content)
    if not username or not password:
        raise RuntimeError(f"could not parse instructor credentials from {path}")
    return username.group(1).strip(), password.group(1).strip()


def build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def request_json(
    opener: urllib.request.OpenerDirector,
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with opener.open(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


def login(opener: urllib.request.OpenerDirector, base_url: str, credentials_file: Path) -> None:
    username, password = parse_credentials(credentials_file)
    status, payload = request_json(
        opener,
        "POST",
        f"{base_url}/api/instructor/login",
        {"user": username, "key": password},
    )
    if status != 200:
        raise RuntimeError(f"instructor login failed: status={status} body={payload}")


def acquire_csrf_headers(opener: urllib.request.OpenerDirector, base_url: str) -> dict[str, str]:
    status, payload = request_json(opener, "POST", f"{base_url}/api/instructor/csrf")
    if status != 200:
        return {}
    token = str(payload.get("token", "")).strip()
    header = str(payload.get("header", "")).strip()
    if not token or not header:
        return {}
    return {header: token}


def release_claims_for_lab(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    lab_name: str,
    endpoint_config: dict[str, str],
    wipe: bool,
    headers: dict[str, str],
) -> tuple[int, int]:
    list_url = f"{base_url}{endpoint_config['list']}"
    status, payload = request_json(opener, "GET", list_url)
    if status != 200:
        print(f"{lab_name}: skipped (claims endpoint returned {status})")
        return 0, 0
    claims = payload.get("claims", [])
    released = 0
    failed = 0
    query = "?wipe=1" if wipe else ""
    for entry in claims:
        claim_uuid = entry.get("uuid")
        if not claim_uuid:
            continue
        delete_url = f"{base_url}{endpoint_config['delete_prefix']}{claim_uuid}{query}"
        delete_status, delete_payload = request_json(
            opener,
            "DELETE",
            delete_url,
            headers=headers,
        )
        if delete_status == 200 and delete_payload.get("success", True):
            released += 1
        else:
            failed += 1
            print(
                f"{lab_name}: failed to release {claim_uuid}: "
                f"status={delete_status} body={delete_payload}"
            )
    print(f"{lab_name}: released {released} claim(s), failed {failed}")
    return released, failed


def main() -> int:
    args = parse_args()
    opener = build_opener()
    base_url = args.base_url.rstrip("/")
    login(opener, base_url, args.credentials_file)
    csrf_headers = acquire_csrf_headers(opener, base_url)
    labs = args.lab or list(LAB_ENDPOINTS.keys())
    total_released = 0
    total_failed = 0
    for lab_name in labs:
        released, failed = release_claims_for_lab(
            opener,
            base_url,
            lab_name,
            LAB_ENDPOINTS[lab_name],
            wipe=args.wipe,
            headers=csrf_headers,
        )
        total_released += released
        total_failed += failed
    print(f"total: released {total_released}, failed {total_failed}")
    return 1 if total_failed else 0


if __name__ == "__main__":
    sys.exit(main())
