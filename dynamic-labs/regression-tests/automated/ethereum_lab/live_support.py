from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse, urlunparse

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

_USERNAME_RE = re.compile(r"^Username:\s*(.+)$", re.MULTILINE)
_PASSWORD_RE = re.compile(r"^Password:\s*(.+)$", re.MULTILINE)
_UUID_RE = re.compile(r"^[0-9a-f-]{36}$")
_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_OSC_RE = re.compile(r"\x1B\].*?(?:\x07|\x1B\\)")


class RegressionFailure(RuntimeError):
    pass


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


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def clear_cookie(session: requests.Session, cookie_name: str) -> None:
    for cookie in list(session.cookies):
        if cookie.name == cookie_name:
            session.cookies.clear(domain=cookie.domain, path=cookie.path, name=cookie.name)


def _cookie_header(session: requests.Session) -> str:
    cookies = session.cookies.get_dict()
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def _to_websocket_url(http_url: str) -> str:
    parsed = urlparse(http_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse(parsed._replace(scheme=scheme))


def strip_terminal_artifacts(text: str) -> str:
    text = _OSC_RE.sub("", text)
    text = _ANSI_RE.sub("", text)
    return text.replace("\r", "")


def parse_instructor_credentials(path: Path = DEFAULT_CREDENTIALS_FILE) -> tuple[str, str]:
    if not path.exists():
        raise RegressionFailure(
            f"instructor credentials file not found: {path}. "
            "Run deploy first or point ETHEREUM_REGRESSION_CREDENTIALS_FILE at a valid file."
        )
    content = path.read_text(encoding="utf-8")
    username = _USERNAME_RE.search(content)
    password = _PASSWORD_RE.search(content)
    if not username or not password:
        raise RegressionFailure(f"could not parse instructor credentials from {path}")
    return username.group(1).strip(), password.group(1).strip()


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
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    last_response: requests.Response | None = None
    while time.time() < deadline:
        try:
            response = session.get(url, timeout=10, allow_redirects=allow_redirects)
            last_response = response
            if predicate(response):
                return response
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(interval_seconds)
    if last_response is not None:
        raise RegressionFailure(
            f"timed out waiting for {description}: last status={last_response.status_code} url={last_response.url}"
        )
    raise RegressionFailure(f"timed out waiting for {description}: last error={last_error}")


def _session_has_valid_instructor_cookie(
    session: requests.Session,
    base_url: str,
) -> bool:
    try:
        response = session.get(f"{base_url}/api/instructor/whoami", timeout=10)
    except requests.RequestException:
        return False
    if response.status_code != 200:
        return False
    payload = response.json()
    return bool(payload.get("authenticated"))


def _candidate_instructor_cookie_cache_paths(
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> list[Path]:
    candidates = [cache_path]
    runtime_dir = ROOT / ".runtime"
    try:
        for path in sorted(runtime_dir.glob("*-regression-instructor-cookie.json")):
            if path not in candidates:
                candidates.append(path)
    except OSError:
        pass
    return candidates


def _load_cached_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> bool:
    for candidate in _candidate_instructor_cookie_cache_paths(cache_path):
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("base_url") != base_url:
            continue
        cookie_value = (payload.get("cookie_value") or "").strip()
        if not cookie_value:
            continue
        session.cookies.set(INSTRUCTOR_COOKIE_NAME, cookie_value, path="/")
        if _session_has_valid_instructor_cookie(session, base_url):
            return True
        clear_cookie(session, INSTRUCTOR_COOKIE_NAME)
    return False


def _persist_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> None:
    cookie_value = session.cookies.get(INSTRUCTOR_COOKIE_NAME)
    if not cookie_value:
        return
    payload = {
        "base_url": base_url,
        "cookie_name": INSTRUCTOR_COOKIE_NAME,
        "cookie_value": cookie_value,
    }
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        return


def login_instructor(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    *,
    max_retries: int = 5,
    retry_delay: float = 5.0,
) -> None:
    if _load_cached_instructor_cookie(session, base_url):
        return

    username, password = parse_instructor_credentials()
    for attempt in range(1, max_retries + 1):
        response = session.post(
            f"{base_url}/api/instructor/login",
            json={"user": username, "key": password},
            timeout=10,
        )
        if response.status_code == 200:
            if not _session_has_valid_instructor_cookie(session, base_url):
                raise RegressionFailure("instructor login did not yield a usable instructor session")
            _persist_instructor_cookie(session, base_url)
            return
        if response.status_code == 429 and attempt < max_retries:
            time.sleep(retry_delay * attempt)
            continue
        raise RegressionFailure(
            f"instructor login failed: status={response.status_code} body={response.text[:300]}"
        )


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
