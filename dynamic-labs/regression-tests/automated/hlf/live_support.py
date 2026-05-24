from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid as uuid_lib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse, urlunparse

import requests

try:
    import docker as docker_sdk
    from docker.errors import DockerException, NotFound
except ImportError:  # pragma: no cover
    docker_sdk = None

    class DockerException(Exception):
        pass

    class NotFound(Exception):
        pass

try:
    from websocket import ABNF, WebSocketTimeoutException, create_connection
except ImportError:  # pragma: no cover
    ABNF = None
    create_connection = None

    class WebSocketTimeoutException(TimeoutError):
        pass


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_URL = os.environ.get("HLF_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("HLF_REGRESSION_TIMEOUT", "180"))
DEFAULT_CLAIM_READY_TIMEOUT_SECONDS = int(
    os.environ.get("HLF_REGRESSION_CLAIM_READY_TIMEOUT", "120")
)
DEFAULT_STARTUP_READY_TIMEOUT_SECONDS = int(
    os.environ.get("HLF_REGRESSION_STARTUP_READY_TIMEOUT", "900")
)
DEFAULT_CLAIM_RETRY_ATTEMPTS = int(
    os.environ.get("HLF_REGRESSION_CLAIM_RETRY_ATTEMPTS", "3")
)
DEFAULT_CLAIM_RETRY_DELAY_SECONDS = float(
    os.environ.get("HLF_REGRESSION_CLAIM_RETRY_DELAY_SECONDS", "5.0")
)
DEFAULT_CLAIM_SETTLE_SECONDS = float(
    os.environ.get("HLF_REGRESSION_CLAIM_SETTLE_SECONDS", "3.0")
)
DEFAULT_TTYD_READY_TIMEOUT_SECONDS = int(
    os.environ.get("HLF_REGRESSION_TTYD_READY_TIMEOUT", "60")
)
DEFAULT_TTYD_CONNECT_SETTLE_SECONDS = float(
    os.environ.get("HLF_REGRESSION_TTYD_CONNECT_SETTLE_SECONDS", "1.5")
)
DEFAULT_TTYD_COMMAND_SETTLE_SECONDS = float(
    os.environ.get("HLF_REGRESSION_TTYD_COMMAND_SETTLE_SECONDS", "1.0")
)
DEFAULT_TTYD_MULTILINE_EXTRA_SECONDS = float(
    os.environ.get("HLF_REGRESSION_TTYD_MULTILINE_EXTRA_SECONDS", "0.25")
)
DEFAULT_TTYD_KEYSTROKE_DELAY_SECONDS = float(
    os.environ.get("HLF_REGRESSION_TTYD_KEYSTROKE_DELAY_SECONDS", "0.02")
)
DEFAULT_TTYD_LINE_SETTLE_SECONDS = float(
    os.environ.get("HLF_REGRESSION_TTYD_LINE_SETTLE_SECONDS", "0.1")
)
DEFAULT_CREDENTIALS_FILE = Path(
    os.environ.get(
        "HLF_REGRESSION_CREDENTIALS_FILE",
        str(ROOT / ".runtime" / "instructor-credentials.txt"),
    )
)
DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE = Path(
    os.environ.get(
        "HLF_REGRESSION_INSTRUCTOR_COOKIE_CACHE_FILE",
        str(ROOT / ".runtime" / "hlf-regression-instructor-cookie.json"),
    )
)
INSTRUCTOR_COOKIE_NAME = "hlf_instructor"

RUNNER_CONTAINER = os.environ.get("HLF_REGRESSION_RUNNER_CONTAINER", "hlf-hlf-runner-1")

_USERNAME_RE = re.compile(r"^Username:\s*(.+)$", re.MULTILINE)
_PASSWORD_RE = re.compile(r"^Password:\s*(.+)$", re.MULTILINE)
_UUID_RE = re.compile(r"/labs/hlf/c/([0-9a-f-]{36})/")
_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_OSC_RE = re.compile(r"\x1B\].*?(?:\x07|\x1B\\)")


class RegressionFailure(RuntimeError):
    pass


@dataclass
class ClaimContext:
    uuid: str
    station: str
    wrapper_html: str

    @property
    def peer_container(self) -> str:
        n = self.station[1:]
        return f"peer0.student{n}.example.com"

    @property
    def short_id(self) -> str:
        return self.uuid[:8]


@dataclass
class CommandResult:
    command: str
    output: str
    exit_code: int
    raw_output: str


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def _cookie_header(session: requests.Session) -> str:
    cookies = session.cookies.get_dict()
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def clear_cookie(session: requests.Session, cookie_name: str) -> None:
    for cookie in list(session.cookies):
        if cookie.name == cookie_name:
            session.cookies.clear(domain=cookie.domain, path=cookie.path, name=cookie.name)


def _to_websocket_url(http_url: str) -> str:
    parsed = urlparse(http_url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse(parsed._replace(scheme=ws_scheme))


def _decode_terminal_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def strip_terminal_artifacts(text: str) -> str:
    text = _OSC_RE.sub("", text)
    text = _ANSI_RE.sub("", text)
    text = text.replace("\r", "")
    return text


def parse_instructor_credentials(path: Path = DEFAULT_CREDENTIALS_FILE) -> tuple[str, str]:
    if not path.exists():
        raise RegressionFailure(
            f"instructor credentials file not found: {path}. "
            "Run deploy first or point HLF_REGRESSION_CREDENTIALS_FILE at a valid file."
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
    interval_seconds: float = 2.0,
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
            f"timed out waiting for {description}: "
            f"last status={last_response.status_code} url={last_response.url}"
        )
    raise RegressionFailure(f"timed out waiting for {description}: last error={last_error}")


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
            _acquire_csrf_token(session, base_url)
            if not _session_has_valid_instructor_cookie(session, base_url):
                raise RegressionFailure(
                    "instructor login did not yield a usable instructor session"
                )
            _persist_instructor_cookie(session, base_url)
            return
        if response.status_code == 429 and attempt < max_retries:
            time.sleep(retry_delay * attempt)
            continue
        raise RegressionFailure(
            f"instructor login failed: status={response.status_code} body={response.text[:300]}"
        )


def _acquire_csrf_token(session: requests.Session, base_url: str = DEFAULT_BASE_URL) -> None:
    resp = session.post(f"{base_url}/api/instructor/csrf", timeout=10)
    if resp.status_code != 200:
        return
    token = resp.json().get("token", "")
    if token:
        session.headers["X-CSRFToken"] = token


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
        cookie_value = (payload.get("cookie_value") or "").strip()
        if not cookie_value:
            continue
        session.cookies.set(INSTRUCTOR_COOKIE_NAME, cookie_value, path="/")
        if _session_has_valid_instructor_cookie(session, base_url):
            _acquire_csrf_token(session, base_url)
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


# ------------------------------------------------------------------
# HLF API helpers
# ------------------------------------------------------------------

def hlf_api_get(
    session: requests.Session,
    path: str,
    base_url: str = DEFAULT_BASE_URL,
    **kwargs,
) -> dict:
    url = f"{base_url}/labs/hlf{path}"
    resp = session.get(url, timeout=kwargs.pop("timeout", 30), **kwargs)
    if resp.status_code != 200:
        raise RegressionFailure(
            f"GET {path} failed: status={resp.status_code} body={resp.text[:300]}"
        )
    return resp.json()


def hlf_api_post(
    session: requests.Session,
    path: str,
    base_url: str = DEFAULT_BASE_URL,
    json_body: dict | None = None,
    **kwargs,
) -> dict:
    url = f"{base_url}/labs/hlf{path}"
    resp = session.post(url, json=json_body, timeout=kwargs.pop("timeout", 30), **kwargs)
    if resp.status_code not in (200, 201):
        raise RegressionFailure(
            f"POST {path} failed: status={resp.status_code} body={resp.text[:300]}"
        )
    return resp.json()


def get_hlf_status(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/status", base_url)


def wait_for_hlf_startup_complete(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_seconds: int = DEFAULT_STARTUP_READY_TIMEOUT_SECONDS,
    interval_seconds: float = 5.0,
    require_student_overlay: bool = False,
) -> dict:
    """Wait for the managed HLF startup task to finish.

    The HLF status API flips to `running` as soon as the consortium peers are
    up, but a clean boot still has background work left: channel creation,
    chaincode deployment, and student overlay enrollment. Claim- and
    network-dependent tests must wait for `background_task` to clear or they
    race half-built student lanes.
    """
    deadline = time.time() + timeout_seconds
    last_status: dict | None = None
    artifacts_root = ROOT / "hlf" / "runtime" / "fabric-samples" / "test-network"
    compose_students = artifacts_root / "compose" / "compose-students.yaml"
    channel_block = artifacts_root / "channel-artifacts" / "diplomas.block"

    while time.time() < deadline:
        try:
            last_status = get_hlf_status(session, base_url)
        except RegressionFailure:
            time.sleep(interval_seconds)
            continue

        ready = (
            last_status.get("status") == "running"
            and not last_status.get("background_task")
        )
        if ready:
            if not require_student_overlay:
                return last_status
            if compose_students.is_file() and channel_block.is_file():
                return last_status
        time.sleep(interval_seconds)

    raise RegressionFailure(
        "timed out waiting for HLF startup to finish: "
        f"last_status={json.dumps(last_status or {}, sort_keys=True)[:800]}"
    )


def get_hlf_health(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/health", base_url)


def get_hlf_exercises(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    *,
    via_claim: str | None = None,
) -> dict:
    if via_claim:
        path = f"/c/{via_claim}/api/hlf/exercises"
        url = f"{base_url}/labs/hlf{path}"
    else:
        url = f"{base_url}/labs/hlf/api/hlf/exercises"
    resp = session.get(url, timeout=30)
    if resp.status_code != 200:
        raise RegressionFailure(
            f"exercises API failed: status={resp.status_code} body={resp.text[:300]}"
        )
    return resp.json()


def get_hlf_explorer(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/explorer", base_url)


def get_hlf_explorer_view(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/explorer-view", base_url)


def get_hlf_chaincode(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 60,
) -> dict:
    return hlf_api_get(session, "/api/hlf/chaincode", base_url, timeout=timeout)


def get_hlf_governance(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 60,
) -> dict:
    return hlf_api_get(session, "/api/hlf/governance", base_url, timeout=timeout)


def get_instructor_snapshot(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/instructor-snapshot", base_url)


def list_hlf_claims(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/claims", base_url)


def release_hlf_claim(
    session: requests.Session,
    claim_uuid: str,
    *,
    wipe: bool = True,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    url = f"{base_url}/labs/hlf/api/hlf/claims/{claim_uuid}"
    resp = session.delete(url, params={"wipe": "1" if wipe else "0"}, timeout=30)
    if resp.status_code not in (200, 404):
        raise RegressionFailure(
            f"claim release failed: status={resp.status_code} body={resp.text[:300]}"
        )


def hlf_execute(
    session: requests.Session,
    verb: str,
    action: str,
    args: list[str] | None = None,
    org: str = "org1",
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    body = {"verb": verb, "action": action, "args": args or [], "org": org}
    url = f"{base_url}/labs/hlf/api/hlf/execute"
    resp = session.post(url, json=body, timeout=30)
    if resp.status_code >= 500:
        raise RegressionFailure(
            f"execute API server error: status={resp.status_code} body={resp.text[:300]}"
        )
    return resp.json()


def hlf_seed(
    session: requests.Session,
    preset: str = "sample",
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    url = f"{base_url}/labs/hlf/api/hlf/seed"
    resp = session.post(url, json={"preset": preset}, timeout=60)
    return resp.json()


def hlf_fault(
    session: requests.Session,
    target: str,
    action: str,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    url = f"{base_url}/labs/hlf/api/hlf/fault"
    resp = session.post(url, json={"target": target, "action": action}, timeout=30)
    return resp.json()


def get_hlf_chaincode_source(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/chaincode/source", base_url)


def get_hlf_logs(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    lines: int = 15,
) -> dict:
    return hlf_api_get(session, f"/api/hlf/logs?lines={lines}", base_url)


def get_hlf_logs_download(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> requests.Response:
    url = f"{base_url}/labs/hlf/api/hlf/logs/download"
    resp = session.get(url, timeout=30)
    if resp.status_code != 200:
        raise RegressionFailure(
            f"GET /api/hlf/logs/download failed: status={resp.status_code}"
        )
    return resp


def get_hlf_node_context(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    node: str = "org1",
) -> dict:
    return hlf_api_get(session, f"/api/hlf/node-context?node={node}", base_url)


def get_hlf_transaction(
    session: requests.Session,
    tx_id: str,
    base_url: str = DEFAULT_BASE_URL,
) -> requests.Response:
    url = f"{base_url}/labs/hlf/api/hlf/transactions/{tx_id}"
    return session.get(url, timeout=30)


def get_hlf_asset(
    session: requests.Session,
    asset_id: str,
    base_url: str = DEFAULT_BASE_URL,
) -> requests.Response:
    url = f"{base_url}/labs/hlf/api/hlf/assets/{asset_id}"
    return session.get(url, timeout=30)


def get_hlf_lanes(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/lanes", base_url)


def get_hlf_claims_policy(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/claims/policy", base_url)


def get_hlf_claims_pool(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/claims/pool", base_url)


def pause_hlf_claims(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_post(session, "/api/hlf/claims/pause", base_url)


def resume_hlf_claims(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_post(session, "/api/hlf/claims/resume", base_url)


def touch_hlf_progress(
    session: requests.Session,
    route_id: str,
    base_url: str = DEFAULT_BASE_URL,
    via_claim: str | None = None,
) -> dict:
    if via_claim:
        path = f"/c/{via_claim}/api/hlf/progress/touch"
    else:
        path = "/api/hlf/progress/touch"
    return hlf_api_post(session, path, base_url, json_body={"route_id": route_id})


def get_hlf_progress(
    session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, "/api/hlf/progress", base_url)


def get_hlf_progress_detail(
    session: requests.Session,
    uuid: str,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    return hlf_api_get(session, f"/api/hlf/progress/{uuid}", base_url)


# ------------------------------------------------------------------
# claim flow
# ------------------------------------------------------------------

def claim_hlf_station(
    student_session: requests.Session,
    instructor_session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    *,
    fresh: bool = False,
    require_terminal_ready: bool = False,
    ready_timeout_seconds: int = DEFAULT_CLAIM_READY_TIMEOUT_SECONDS,
    retry_attempts: int = DEFAULT_CLAIM_RETRY_ATTEMPTS,
    retry_delay_seconds: float = DEFAULT_CLAIM_RETRY_DELAY_SECONDS,
    settle_seconds: float = DEFAULT_CLAIM_SETTLE_SECONDS,
) -> ClaimContext:
    last_error: Exception | None = None

    wait_for_hlf_startup_complete(
        instructor_session,
        base_url,
        timeout_seconds=DEFAULT_STARTUP_READY_TIMEOUT_SECONDS,
        require_student_overlay=True,
    )

    for attempt in range(1, retry_attempts + 1):
        if fresh or attempt > 1:
            clear_cookie(student_session, "hlf_session")

        claim_resp = student_session.get(
            f"{base_url}/labs/hlf/claim",
            timeout=15,
        )
        if claim_resp.status_code != 200:
            raise RegressionFailure(
                f"claim failed: status={claim_resp.status_code} url={claim_resp.url} body={claim_resp.text[:300]}"
            )

        uuid = student_session.cookies.get("hlf_session")
        if not uuid:
            match = _UUID_RE.search(claim_resp.url)
            uuid = match.group(1) if match else ""
        if not uuid:
            raise RegressionFailure("claim did not issue hlf_session cookie or UUID in URL")

        wrapper_url = f"{base_url}/labs/hlf/c/{uuid}/"
        try:
            wrapper_resp = wait_for_http(
                student_session,
                wrapper_url,
                lambda resp: resp.status_code == 200,
                timeout_seconds=30,
                description="hlf student wrapper page",
            )
        except RegressionFailure as exc:
            last_error = exc
            clear_cookie(student_session, "hlf_session")
            if attempt < retry_attempts:
                time.sleep(retry_delay_seconds)
            continue

        claims_data = list_hlf_claims(instructor_session, base_url)
        station = ""
        for claim in claims_data.get("claims", []):
            if claim.get("uuid") == uuid:
                station = claim.get("station", "").strip()
                break

        if not station:
            raise RegressionFailure(f"could not resolve station for claimed UUID {uuid}")

        claim_ctx = ClaimContext(uuid=uuid, station=station, wrapper_html=wrapper_resp.text)

        if settle_seconds > 0:
            time.sleep(settle_seconds)

        if not require_terminal_ready:
            return claim_ctx

        try:
            wait_for_container_running(
                claim_ctx.peer_container,
                timeout_seconds=ready_timeout_seconds,
                interval_seconds=2.0,
            )
            wait_for_docker_exec_ready(
                claim_ctx.peer_container,
                timeout_seconds=ready_timeout_seconds,
                interval_seconds=2.0,
            )
            wait_for_http(
                student_session,
                f"{base_url}/labs/hlf/c/{uuid}/api/hlf/my-term",
                lambda resp: resp.status_code == 200,
                timeout_seconds=ready_timeout_seconds,
                interval_seconds=3.0,
                description=f"my-term ready for {station}",
            )
            wait_for_http(
                student_session,
                f"{base_url}/labs/hlf/s/{station}/term/",
                lambda resp: resp.status_code == 200,
                timeout_seconds=ready_timeout_seconds,
                interval_seconds=3.0,
                description=f"ttyd HTML ready for {station}",
            )
            return claim_ctx
        except RegressionFailure as exc:
            last_error = exc
            try:
                release_hlf_claim(instructor_session, uuid, wipe=True, base_url=base_url)
            except Exception:
                pass
            clear_cookie(student_session, "hlf_session")
            if attempt < retry_attempts:
                time.sleep(retry_delay_seconds)

    raise RegressionFailure(
        f"could not obtain a ready HLF claim after {retry_attempts} attempts: {last_error}"
    )


# ------------------------------------------------------------------
# docker helpers
# ------------------------------------------------------------------

def _docker_client():
    if docker_sdk is None:
        return None
    return docker_sdk.from_env()


def wait_for_container_running(
    container: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    interval_seconds: float = 2.0,
) -> None:
    deadline = time.time() + timeout_seconds
    client = _docker_client()
    if client is not None:
        while time.time() < deadline:
            try:
                obj = client.containers.get(container)
                obj.reload()
                if bool(obj.attrs.get("State", {}).get("Running")):
                    return
            except NotFound:
                pass
            except DockerException as exc:
                raise RegressionFailure(f"docker inspect failed for {container}: {exc}") from exc
            time.sleep(interval_seconds)
        raise RegressionFailure(f"container did not become ready: {container}")

    while time.time() < deadline:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip() == "true":
            return
        time.sleep(interval_seconds)
    raise RegressionFailure(f"container did not become ready: {container}")


def docker_exec(
    container: str,
    command: str,
    *,
    timeout_seconds: int = 60,
    user: str | None = None,
) -> subprocess.CompletedProcess[str]:
    docker_command = ["docker", "exec"]
    if user:
        docker_command.extend(["--user", user])
    docker_command.extend(
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
        docker_command,
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
            f"docker exec failed for {container}: command={command!r} "
            f"stdout={result.stdout[-400:]} stderr={result.stderr[-400:]}"
        )
    return result.stdout


def docker_exec_json(container: str, command: str, *, timeout_seconds: int = 60) -> dict:
    output = docker_exec_checked(container, command, timeout_seconds=timeout_seconds).strip()
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RegressionFailure(f"expected JSON from {command!r}, got {output[:300]!r}") from exc


def wait_for_docker_output(
    container: str,
    command: str,
    predicate: Callable[[str], bool],
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    interval_seconds: float = 1.0,
    description: str,
) -> str:
    deadline = time.time() + timeout_seconds
    last_output = ""
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            per_attempt_timeout = max(5, min(timeout_seconds, 15))
            output = docker_exec_checked(
                container,
                command,
                timeout_seconds=per_attempt_timeout,
            ).strip()
            last_output = output
            if predicate(output):
                return output
        except (RegressionFailure, ValueError) as exc:
            last_error = exc
        time.sleep(interval_seconds)
    if last_output:
        raise RegressionFailure(
            f"timed out waiting for {description}: last_output={last_output!r}"
        )
    raise RegressionFailure(f"timed out waiting for {description}: last_error={last_error}")


def wait_for_docker_exec_ready(
    container: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    interval_seconds: float = 1.0,
) -> None:
    deadline = time.time() + timeout_seconds
    last_error: str | None = None
    while time.time() < deadline:
        try:
            result = docker_exec(container, "true", timeout_seconds=10)
        except (subprocess.TimeoutExpired, RegressionFailure) as exc:
            last_error = str(exc)
            time.sleep(interval_seconds)
            continue
        if result.returncode == 0:
            return
        last_error = (
            f"rc={result.returncode} stdout={result.stdout[-200:]} stderr={result.stderr[-200:]}"
        )
        time.sleep(interval_seconds)
    raise RegressionFailure(
        f"container did not become exec-ready: {container}; last_error={last_error}"
    )


# ------------------------------------------------------------------
# ttyd helpers
# ------------------------------------------------------------------

class TtydSession:
    def __init__(
        self,
        session: requests.Session,
        base_url: str,
        ttyd_path: str,
        *,
        columns: int = 120,
        rows: int = 40,
        connect_settle_seconds: float = DEFAULT_TTYD_CONNECT_SETTLE_SECONDS,
        post_command_settle_seconds: float = DEFAULT_TTYD_COMMAND_SETTLE_SECONDS,
        multiline_extra_settle_seconds: float = DEFAULT_TTYD_MULTILINE_EXTRA_SECONDS,
        keystroke_delay_seconds: float = DEFAULT_TTYD_KEYSTROKE_DELAY_SECONDS,
        line_settle_seconds: float = DEFAULT_TTYD_LINE_SETTLE_SECONDS,
    ) -> None:
        if create_connection is None or ABNF is None:
            raise RegressionFailure("websocket-client is not installed in the regression runner")
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.ttyd_path = ttyd_path
        self.columns = columns
        self.rows = rows
        self.connect_settle_seconds = connect_settle_seconds
        self.post_command_settle_seconds = post_command_settle_seconds
        self.multiline_extra_settle_seconds = multiline_extra_settle_seconds
        self.keystroke_delay_seconds = keystroke_delay_seconds
        self.line_settle_seconds = line_settle_seconds
        self.socket = None
        self.collected = ""

    def __enter__(self) -> TtydSession:
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def connect(self) -> None:
        ttyd_url = urljoin(f"{self.base_url}/", self.ttyd_path.lstrip("/"))
        ws_url = _to_websocket_url(ttyd_url.rstrip("/") + "/ws")
        token_url = ttyd_url.rstrip("/") + "/token"
        origin = f"{urlparse(self.base_url).scheme}://{urlparse(self.base_url).netloc}"
        cookie_header = _cookie_header(self.session)
        headers = [f"Cookie: {cookie_header}"] if cookie_header else []
        auth_token = ""

        try:
            token_response = self.session.get(token_url, timeout=10, allow_redirects=False)
        except requests.RequestException as exc:
            raise RegressionFailure(f"ttyd token request failed for {token_url}: {exc}") from exc
        if token_response.status_code == 200:
            auth_token = token_response.text.strip()
        elif token_response.status_code not in (401, 404):
            raise RegressionFailure(
                f"unexpected ttyd token response: "
                f"status={token_response.status_code} body={token_response.text[:300]}"
            )

        self.socket = create_connection(
            ws_url,
            subprotocols=["tty"],
            header=headers,
            origin=origin,
            timeout=10,
        )
        self.socket.settimeout(1)
        init_payload = json.dumps(
            {"AuthToken": auth_token, "columns": self.columns, "rows": self.rows}
        ).encode("utf-8")
        self.socket.send(init_payload, opcode=ABNF.OPCODE_BINARY)
        self._warm()
        self._wait_for_prompt()

    def close(self) -> None:
        if self.socket is None:
            return
        try:
            self.socket.close()
        except Exception:
            pass
        self.socket = None

    @property
    def prompt_ready(self) -> bool:
        return self._prompt_ready

    def _wait_for_prompt(self) -> None:
        _PROMPT_RE = re.compile(r"[$#]\s*$", re.MULTILINE)
        _CONNECTED_RE = re.compile(r"Connected to ")
        self._prompt_ready = False
        saw_banner = False
        deadline = time.time() + self.connect_settle_seconds
        while time.time() < deadline:
            self._recv_once()
            cleaned = strip_terminal_artifacts(self.collected)
            if _PROMPT_RE.search(cleaned):
                time.sleep(0.5)
                self._prompt_ready = True
                return
            if _CONNECTED_RE.search(cleaned) and not saw_banner:
                saw_banner = True
                self._send_input("\r")
                time.sleep(0.25)
        self._send_input("\r")
        extra_deadline = time.time() + 5
        while time.time() < extra_deadline:
            self._recv_once()
            cleaned = strip_terminal_artifacts(self.collected)
            if _PROMPT_RE.search(cleaned):
                time.sleep(0.5)
                self._prompt_ready = True
                return

    def _warm(self) -> None:
        deadline = time.time() + 3
        while time.time() < deadline:
            if self._recv_once():
                return

    def _recv_once(self) -> bool:
        if self.socket is None:
            raise RegressionFailure("ttyd websocket is not connected")
        try:
            frame = self.socket.recv()
        except WebSocketTimeoutException:
            return False
        if not frame:
            return False
        raw = frame.encode("utf-8") if isinstance(frame, str) else frame
        if not raw:
            return False
        if chr(raw[0]) != "0":
            return False
        self.collected += _decode_terminal_text(raw[1:])
        return True

    def _send_input(self, text: str) -> None:
        if self.socket is None:
            raise RegressionFailure("ttyd websocket is not connected")
        if not text:
            return
        self.socket.send(b"0" + text.encode("utf-8"), opcode=ABNF.OPCODE_BINARY)

    def _send_line(self, text: str) -> None:
        if text:
            for char in text:
                self._send_input(char)
                if self.keystroke_delay_seconds > 0:
                    time.sleep(self.keystroke_delay_seconds)
        self._send_input("\r")
        if self.line_settle_seconds > 0:
            time.sleep(self.line_settle_seconds)

    def run_command(self, command: str, *, timeout_seconds: int = 20) -> CommandResult:
        if self.socket is None:
            raise RegressionFailure("ttyd websocket is not connected")

        marker = f"__hlf_regression_{uuid_lib.uuid4().hex}__"
        ttyd_command = command.strip("\r\n").replace("\r\n", "\n").replace("\r", "\n")
        ttyd_lines = [line.strip() for line in ttyd_command.split("\n") if line.strip()]
        transmit_command = "; ".join(ttyd_lines)
        start_idx = len(self.collected)
        marker_command = f"{transmit_command}; printf '{marker}:%s\\n' \"$?\""
        self._send_line(marker_command)

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            segment = strip_terminal_artifacts(self.collected[start_idx:])
            exit_matches = list(re.finditer(re.escape(marker) + r":(\d+)", segment))
            if exit_matches:
                exit_match = exit_matches[-1]
                extra_lines = max(len(ttyd_lines) - 1, 0)
                settle_seconds = self.post_command_settle_seconds + (
                    extra_lines * self.multiline_extra_settle_seconds
                )
                if settle_seconds > 0:
                    time.sleep(settle_seconds)
                return CommandResult(
                    command=command,
                    output=segment[:exit_match.start()].strip(),
                    exit_code=int(exit_match.group(1)),
                    raw_output=segment.strip(),
                )
            self._recv_once()

        raise RegressionFailure(
            f"timed out waiting for ttyd command completion: command={command!r} "
            f"last_output={strip_terminal_artifacts(self.collected[start_idx:])[-600:]!r}"
        )


def ttyd_session(
    session: requests.Session,
    base_url: str,
    ttyd_path: str,
    **kwargs,
) -> TtydSession:
    return TtydSession(session, base_url, ttyd_path, **kwargs)


def ttyd_command_round_trip(
    session: requests.Session,
    base_url: str,
    ttyd_path: str,
    command: str,
    *,
    expected_fragment: str,
    timeout_seconds: int = 20,
    columns: int = 120,
    rows: int = 40,
    connect_settle_seconds: float = DEFAULT_TTYD_CONNECT_SETTLE_SECONDS,
) -> str:
    with ttyd_session(
        session, base_url, ttyd_path,
        columns=columns, rows=rows,
        connect_settle_seconds=connect_settle_seconds,
    ) as terminal:
        result = terminal.run_command(command, timeout_seconds=timeout_seconds)
        if expected_fragment not in result.raw_output:
            raise RegressionFailure(
                f"expected {expected_fragment!r} in ttyd output, "
                f"got: {result.raw_output[-500:]!r}"
            )
        return result.raw_output
