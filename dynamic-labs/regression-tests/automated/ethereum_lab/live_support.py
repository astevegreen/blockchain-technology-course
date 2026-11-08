from __future__ import annotations

import json
import os
import re
import sys
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import requests

try:
    from websocket import WebSocketTimeoutException, create_connection
except ImportError:  # pragma: no cover
    create_connection = None

    class WebSocketTimeoutException(TimeoutError):
        pass


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_URL = os.environ.get("ETHEREUM_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("ETHEREUM_REGRESSION_TIMEOUT", "180"))
DEFAULT_CLAIM_READY_TIMEOUT_SECONDS = int(
    os.environ.get("ETHEREUM_REGRESSION_CLAIM_READY_TIMEOUT", "120")
)
DEFAULT_CLAIM_RETRY_ATTEMPTS = int(
    os.environ.get("ETHEREUM_REGRESSION_CLAIM_RETRY_ATTEMPTS", "4")
)
DEFAULT_CLAIM_RETRY_DELAY_SECONDS = float(
    os.environ.get("ETHEREUM_REGRESSION_CLAIM_RETRY_DELAY_SECONDS", "2.0")
)
DEFAULT_CLAIM_SETTLE_SECONDS = float(
    os.environ.get("ETHEREUM_REGRESSION_CLAIM_SETTLE_SECONDS", "1.0")
)
DEFAULT_TERMINAL_READY_TIMEOUT_SECONDS = int(
    os.environ.get("ETHEREUM_REGRESSION_TERMINAL_READY_TIMEOUT", "30")
)
DEFAULT_TERMINAL_CONNECT_SETTLE_SECONDS = float(
    os.environ.get("ETHEREUM_REGRESSION_TERMINAL_CONNECT_SETTLE_SECONDS", "0.75")
)
DEFAULT_TERMINAL_COMMAND_SETTLE_SECONDS = float(
    os.environ.get("ETHEREUM_REGRESSION_TERMINAL_COMMAND_SETTLE_SECONDS", "0.5")
)
DEFAULT_TERMINAL_KEYSTROKE_DELAY_SECONDS = float(
    os.environ.get("ETHEREUM_REGRESSION_TERMINAL_KEYSTROKE_DELAY_SECONDS", "0.02")
)
DEFAULT_TERMINAL_LINE_SETTLE_SECONDS = float(
    os.environ.get("ETHEREUM_REGRESSION_TERMINAL_LINE_SETTLE_SECONDS", "0.08")
)
DEFAULT_CREDENTIALS_FILE = Path(
    os.environ.get(
        "ETHEREUM_REGRESSION_CREDENTIALS_FILE",
        str(ROOT / ".runtime" / "instructor-credentials.txt"),
    )
)
DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE = Path(
    os.environ.get(
        "ETHEREUM_REGRESSION_INSTRUCTOR_COOKIE_CACHE_FILE",
        str(ROOT / ".runtime" / "ethereum-regression-instructor-cookie.json"),
    )
)
INSTRUCTOR_COOKIE_NAME = "hlf_instructor"

_UUID_RE = re.compile(r"^[0-9a-f-]{36}$")
_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_OSC_RE = re.compile(r"\x1B\].*?(?:\x07|\x1B\\)")


# The session, wait and login helpers live in ../live_common.py, shared by every lab's live_support.py.
# This file keeps the lab's own settings and the thin wrappers that pass them in.
_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

RegressionFailure = live_common.RegressionFailure
new_session = live_common.new_session
clear_cookie = live_common.clear_cookie
_cookie_header = live_common.cookie_header
_to_websocket_url = live_common.to_websocket_url
_session_has_valid_instructor_cookie = live_common.session_has_valid_instructor_cookie


def parse_instructor_credentials(path: Path = DEFAULT_CREDENTIALS_FILE) -> tuple[str, str]:
    return live_common.parse_instructor_credentials(path, "ETHEREUM_REGRESSION_CREDENTIALS_FILE")


def wait_for_http(
    session: requests.Session,
    url: str,
    predicate: Callable[[requests.Response], bool],
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    interval_seconds: float = 1.0,
    description: str,
    allow_redirects: bool = True,
) -> requests.Response:
    return live_common.wait_for_http(
        session,
        url,
        predicate,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        description=description,
        allow_redirects=allow_redirects,
    )


def _candidate_instructor_cookie_cache_paths(
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> list[Path]:
    return live_common.candidate_cookie_cache_paths(cache_path, ROOT)


def _load_cached_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> bool:
    return live_common.load_cached_instructor_cookie(
        session,
        base_url,
        _candidate_instructor_cookie_cache_paths(cache_path),
        INSTRUCTOR_COOKIE_NAME,
    )


def _persist_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> None:
    live_common.persist_instructor_cookie(session, base_url, cache_path, INSTRUCTOR_COOKIE_NAME)


def login_instructor(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    *,
    max_retries: int = 5,
    retry_delay: float = 5.0,
) -> None:
    live_common.login_instructor(
        session,
        base_url,
        load_cached=lambda: _load_cached_instructor_cookie(session, base_url),
        credentials=parse_instructor_credentials,
        persist=lambda: _persist_instructor_cookie(session, base_url),
        max_retries=max_retries,
        retry_delay=retry_delay,
    )


@dataclass
class ClaimContext:
    uuid: str
    station: str
    config: dict

    @property
    def container_name(self) -> str:
        return f"ethereum-lab-student{int(self.station[1:])}"

    @property
    def assigned_address(self) -> str:
        return self.config.get("assignedAddress", "")


def strip_terminal_artifacts(text: str) -> str:
    text = _OSC_RE.sub("", text)
    text = _ANSI_RE.sub("", text)
    return text.replace("\r", "")


def _container_running(container: str) -> bool:
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def wait_for_container_running(
    container: str,
    *,
    timeout_seconds: int = DEFAULT_CLAIM_READY_TIMEOUT_SECONDS,
    interval_seconds: float = 1.0,
) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _container_running(container):
            return
        time.sleep(interval_seconds)
    raise RegressionFailure(f"timed out waiting for container {container} to be running")


def docker_exec(
    container: str,
    command: str,
    *,
    timeout_seconds: int = 60,
    user: str | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "exec"]
    if user:
        cmd.extend(["-u", user])
    cmd.extend(
        [
            container,
            "timeout",
            "--signal=TERM",
            "--kill-after=5",
            f"{timeout_seconds}s",
            "bash",
            "-lc",
            command,
        ]
    )
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 10,
    )


def docker_exec_checked(
    container: str,
    command: str,
    *,
    timeout_seconds: int = 60,
    user: str | None = None,
) -> str:
    result = docker_exec(container, command, timeout_seconds=timeout_seconds, user=user)
    if result.returncode != 0:
        raise RegressionFailure(
            "docker exec failed for "
            f"{container}: command={command!r} stdout={result.stdout[-400:]} stderr={result.stderr[-400:]}"
        )
    return result.stdout


def docker_inspect(container: str) -> dict:
    result = subprocess.run(
        ["docker", "inspect", container],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        raise RegressionFailure(
            "docker inspect failed for "
            f"{container}: stdout={result.stdout[-400:]} stderr={result.stderr[-400:]}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RegressionFailure(f"docker inspect returned invalid JSON for {container}") from exc
    if not payload or not isinstance(payload, list) or not isinstance(payload[0], dict):
        raise RegressionFailure(f"docker inspect returned unexpected payload for {container}: {payload!r}")
    return payload[0]


def list_claims(
    instructor_session: requests.Session,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    response = instructor_session.get(f"{base_url}/api/ethereum/claims", timeout=10)
    if response.status_code != 200:
        raise RegressionFailure(
            f"claims list failed: status={response.status_code} body={response.text[:300]}"
        )
    return response.json()


def release_claim(
    instructor_session: requests.Session,
    claim_uuid: str,
    *,
    wipe: bool = True,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    response = instructor_session.delete(
        f"{base_url}/api/ethereum/claims/{claim_uuid}",
        params={"wipe": "1" if wipe else "0"},
        timeout=20,
    )
    if response.status_code not in (200, 404):
        raise RegressionFailure(
            f"claim release failed: status={response.status_code} body={response.text[:300]}"
        )


def claim_student_lane(
    student_session: requests.Session,
    instructor_session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    *,
    fresh: bool = True,
    retry_attempts: int = DEFAULT_CLAIM_RETRY_ATTEMPTS,
    ready_timeout_seconds: int = DEFAULT_CLAIM_READY_TIMEOUT_SECONDS,
    retry_delay_seconds: float = DEFAULT_CLAIM_RETRY_DELAY_SECONDS,
    settle_seconds: float = DEFAULT_CLAIM_SETTLE_SECONDS,
) -> ClaimContext:
    existing_uuid = (student_session.cookies.get("ethereum_session") or "").strip().lower()
    if fresh and existing_uuid and _UUID_RE.match(existing_uuid):
        try:
            release_claim(instructor_session, existing_uuid, wipe=True, base_url=base_url)
        except Exception:
            pass
        clear_cookie(student_session, "ethereum_session")

    last_error: Exception | None = None

    for attempt in range(1, retry_attempts + 1):
        response = student_session.get(
            f"{base_url}/api/ethereum/claim",
            timeout=20,
        )
        if response.status_code != 200:
            last_error = RegressionFailure(
                f"claim endpoint failed: status={response.status_code} body={response.text[:300]}"
            )
            if attempt < retry_attempts and retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)
            continue

        uuid = (student_session.cookies.get("ethereum_session") or "").strip().lower()
        if not _UUID_RE.match(uuid):
            raise RegressionFailure("ethereum claim did not yield a valid session cookie")

        try:
            if settle_seconds > 0:
                time.sleep(settle_seconds)

            config = wait_for_student_config(
                student_session,
                base_url=base_url,
                timeout_seconds=ready_timeout_seconds,
            )
            station = (config.get("station") or "").strip()
            if not station:
                claims = list_claims(instructor_session, base_url=base_url).get("claims", [])
                for claim in claims:
                    if claim.get("uuid") == uuid:
                        station = (claim.get("station") or "").strip()
                        break
            if not station:
                raise RegressionFailure(f"could not resolve station for ethereum claim {uuid}")

            claim = ClaimContext(uuid=uuid, station=station, config=config)
            wait_for_container_running(
                claim.container_name,
                timeout_seconds=ready_timeout_seconds,
            )
            wait_for_http(
                student_session,
                f"{base_url}/labs/ethereum_lab/lab-api/health",
                lambda resp: resp.status_code == 200 and resp.json().get("status") == "ok",
                timeout_seconds=ready_timeout_seconds,
                interval_seconds=1.0,
                description=f"ethereum lab-api health for {station}",
            )
            wait_for_http(
                student_session,
                f"{base_url}/labs/ethereum_lab/",
                lambda resp: resp.status_code == 200 and "Ethereum Immersive Trainer" in resp.text,
                timeout_seconds=ready_timeout_seconds,
                interval_seconds=1.0,
                description=f"ethereum student SPA for {station}",
            )
            return claim
        except RegressionFailure as exc:
            last_error = exc
            try:
                release_claim(instructor_session, uuid, wipe=True, base_url=base_url)
            except Exception:
                pass
            clear_cookie(student_session, "ethereum_session")
            if attempt < retry_attempts and retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)

    raise RegressionFailure(
        f"could not obtain a ready ethereum claim after {retry_attempts} attempts: {last_error}"
    )


def wait_for_student_config(
    student_session: requests.Session,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: int = DEFAULT_CLAIM_READY_TIMEOUT_SECONDS,
) -> dict:
    url = f"{base_url}/labs/ethereum_lab/api/config.json"
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    last_response: requests.Response | None = None

    while time.time() < deadline:
        try:
            response = student_session.get(url, timeout=10)
            last_response = response
            if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    payload = response.json()
                except ValueError as exc:
                    last_error = exc
                else:
                    if payload.get("mode") == "student":
                        if (
                            payload.get("contractAddress")
                            and payload.get("assignedAddress")
                            and len(payload.get("assignedPrivateKey", "")) == 66
                        ):
                            return payload
                        last_error = RegressionFailure(
                            f"incomplete ethereum student config: {payload}"
                        )
                    else:
                        last_error = RegressionFailure(
                            f"unexpected ethereum student config mode: {payload}"
                        )
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(1.0)

    if last_response is not None:
        raise RegressionFailure(
            "timed out waiting for ethereum student config: "
            f"last status={last_response.status_code} body={last_response.text[:300]!r} error={last_error}"
        )
    raise RegressionFailure(f"timed out waiting for ethereum student config: last error={last_error}")


def get_progress_summary(
    instructor_session: requests.Session,
    claim_uuid: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    response = instructor_session.get(f"{base_url}/api/ethereum/progress", timeout=10)
    if response.status_code != 200:
        raise RegressionFailure(
            f"ethereum progress summary failed: status={response.status_code} body={response.text[:300]}"
        )
    progress = response.json().get("progress", {})
    if claim_uuid not in progress:
        raise RegressionFailure(f"ethereum progress summary missing session {claim_uuid}")
    return progress[claim_uuid]


def get_progress_detail(
    instructor_session: requests.Session,
    claim_uuid: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    response = instructor_session.get(
        f"{base_url}/api/ethereum/progress/{claim_uuid}",
        timeout=10,
    )
    if response.status_code != 200:
        raise RegressionFailure(
            f"ethereum progress detail failed: status={response.status_code} body={response.text[:300]}"
        )
    payload = response.json()
    if not payload.get("success", True) and "detail" not in payload:
        raise RegressionFailure(f"ethereum progress detail missing payload for {claim_uuid}")
    return payload.get("detail", payload)


def _recv_all(ws, *, duration_seconds: float) -> str:
    chunks: list[str] = []
    deadline = time.time() + duration_seconds
    while time.time() < deadline:
        timeout = max(0.05, min(0.25, deadline - time.time()))
        ws.settimeout(timeout)
        try:
            data = ws.recv()
        except WebSocketTimeoutException:
            break
        if isinstance(data, bytes):
            chunks.append(data.decode("utf-8", errors="replace"))
        else:
            chunks.append(data)
    return "".join(chunks)


def terminal_command_round_trip(
    student_session: requests.Session,
    base_url: str,
    command: str,
    *,
    expected_fragment: str,
    terminal_path: str = "/labs/ethereum_lab/ws/terminal",
    ready_timeout_seconds: int = DEFAULT_TERMINAL_READY_TIMEOUT_SECONDS,
    connect_settle_seconds: float = DEFAULT_TERMINAL_CONNECT_SETTLE_SECONDS,
    command_settle_seconds: float = DEFAULT_TERMINAL_COMMAND_SETTLE_SECONDS,
    keystroke_delay_seconds: float = DEFAULT_TERMINAL_KEYSTROKE_DELAY_SECONDS,
    line_settle_seconds: float = DEFAULT_TERMINAL_LINE_SETTLE_SECONDS,
) -> str:
    if create_connection is None:
        raise RegressionFailure("websocket-client is not installed in this environment")

    wait_for_http(
        student_session,
        f"{base_url}/labs/ethereum_lab/terminal",
        lambda resp: resp.status_code == 200 and "Ethereum Immersive Trainer" in resp.text,
        timeout_seconds=ready_timeout_seconds,
        interval_seconds=1.0,
        description="ethereum terminal page",
    )

    ws_url = _to_websocket_url(f"{base_url}{terminal_path}")
    headers = []
    cookie_header = _cookie_header(student_session)
    if cookie_header:
        headers.append(f"Cookie: {cookie_header}")

    ws = create_connection(
        ws_url,
        header=headers,
        timeout=10,
        http_proxy_host=None,
        http_proxy_port=None,
    )
    try:
        ws.send("resize:120:30")
        time.sleep(connect_settle_seconds)
        output = _recv_all(ws, duration_seconds=1.0)

        for char in command:
            ws.send(char)
            time.sleep(keystroke_delay_seconds)
        ws.send("\r")
        time.sleep(command_settle_seconds)

        deadline = time.time() + ready_timeout_seconds
        while time.time() < deadline:
            output += _recv_all(ws, duration_seconds=line_settle_seconds)
            stripped = strip_terminal_artifacts(output)
            if expected_fragment in stripped:
                return stripped
            time.sleep(line_settle_seconds)

        stripped = strip_terminal_artifacts(output)
        raise RegressionFailure(
            f"ethereum terminal did not emit expected fragment {expected_fragment!r}: output={stripped[-800:]}"
        )
    finally:
        try:
            ws.close()
        except Exception:
            pass
