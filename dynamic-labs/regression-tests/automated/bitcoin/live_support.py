from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
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
DEFAULT_BASE_URL = os.environ.get("BITCOIN_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("BITCOIN_REGRESSION_TIMEOUT", "180"))
DEFAULT_CLAIM_READY_TIMEOUT_SECONDS = int(
    os.environ.get("BITCOIN_REGRESSION_CLAIM_READY_TIMEOUT", "90")
)
DEFAULT_CLAIM_RETRY_ATTEMPTS = int(
    os.environ.get("BITCOIN_REGRESSION_CLAIM_RETRY_ATTEMPTS", "3")
)
DEFAULT_CLAIM_RETRY_DELAY_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_CLAIM_RETRY_DELAY_SECONDS", "3.0")
)
DEFAULT_CLAIM_SETTLE_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_CLAIM_SETTLE_SECONDS", "2.0")
)
DEFAULT_LANE_BUSY_RETRY_ATTEMPTS = int(
    os.environ.get("BITCOIN_REGRESSION_LANE_BUSY_RETRY_ATTEMPTS", "6")
)
DEFAULT_LANE_BUSY_RETRY_DELAY_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_LANE_BUSY_RETRY_DELAY_SECONDS", "1.0")
)
DEFAULT_TTYD_READY_TIMEOUT_SECONDS = int(
    os.environ.get("BITCOIN_REGRESSION_TTYD_READY_TIMEOUT", "20")
)
DEFAULT_TTYD_CONNECT_SETTLE_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_TTYD_CONNECT_SETTLE_SECONDS", "1.0")
)
DEFAULT_TTYD_COMMAND_SETTLE_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_TTYD_COMMAND_SETTLE_SECONDS", "0.75")
)
DEFAULT_TTYD_MULTILINE_EXTRA_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_TTYD_MULTILINE_EXTRA_SECONDS", "0.25")
)
DEFAULT_TTYD_KEYSTROKE_DELAY_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_TTYD_KEYSTROKE_DELAY_SECONDS", "0.02")
)
DEFAULT_TTYD_LINE_SETTLE_SECONDS = float(
    os.environ.get("BITCOIN_REGRESSION_TTYD_LINE_SETTLE_SECONDS", "0.1")
)
DEFAULT_CLASSNET_MAX_START_HEIGHT = int(
    os.environ.get("BITCOIN_REGRESSION_CLASSNET_MAX_START_HEIGHT", "11")
)
DEFAULT_ALLOW_CLASSNET_RESEED = os.environ.get(
    "BITCOIN_REGRESSION_ALLOW_CLASSNET_RESEED",
    "1",
).lower() not in {"0", "false", "no"}
DEFAULT_CREDENTIALS_FILE = Path(
    os.environ.get(
        "BITCOIN_REGRESSION_CREDENTIALS_FILE",
        str(ROOT / ".runtime" / "instructor-credentials.txt"),
    )
)
DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE = Path(
    os.environ.get(
        "BITCOIN_REGRESSION_INSTRUCTOR_COOKIE_CACHE_FILE",
        str(ROOT / ".runtime" / "bitcoin-regression-instructor-cookie.json"),
    )
)
INSTRUCTOR_COOKIE_NAME = "hlf_instructor"

_USERNAME_RE = re.compile(r"^Username:\s*(.+)$", re.MULTILINE)
_PASSWORD_RE = re.compile(r"^Password:\s*(.+)$", re.MULTILINE)
_STATION_RE = re.compile(r'<span class="station">(s\d{2})</span>')
_UUID_RE = re.compile(r"/labs/bitcoin/c/([0-9a-f-]{36})/")
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
    def container_name(self) -> str:
        return f"bitcoin-lab-student{int(self.station[1:])}"

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
            "Run deploy first or point BITCOIN_REGRESSION_CREDENTIALS_FILE at a valid file."
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


def login_instructor(session: requests.Session, base_url: str = DEFAULT_BASE_URL) -> None:
    if _load_cached_instructor_cookie(session, base_url):
        return

    username, password = parse_instructor_credentials()
    for attempt in range(1, 6):
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
        if response.status_code == 429 and attempt < 5:
            time.sleep(5.0 * attempt)
            continue
        raise RegressionFailure(
            f"instructor login failed: status={response.status_code} body={response.text[:300]}"
        )


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


def list_bitcoin_claims(
    instructor_session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> list[dict]:
    claims_response = instructor_session.get(f"{base_url}/api/bitcoin/claims", timeout=10)
    if claims_response.status_code != 200:
        raise RegressionFailure(
            f"claims API failed: status={claims_response.status_code} body={claims_response.text[:300]}"
        )
    claims_payload = claims_response.json()
    return claims_payload.get("claims", [])


def list_bitcoin_lanes(
    instructor_session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
) -> list[dict]:
    lanes_response = instructor_session.get(f"{base_url}/api/bitcoin/lanes", timeout=10)
    if lanes_response.status_code != 200:
        raise RegressionFailure(
            f"lanes API failed: status={lanes_response.status_code} body={lanes_response.text[:300]}"
        )
    lanes_payload = lanes_response.json()
    return lanes_payload.get("lanes", [])


def start_bitcoin_lane(
    instructor_session: requests.Session,
    lane_id: str,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    for attempt in range(1, DEFAULT_LANE_BUSY_RETRY_ATTEMPTS + 1):
        response = instructor_session.post(f"{base_url}/api/bitcoin/lanes/{lane_id}/start", timeout=30)
        if response.status_code == 200:
            return
        if response.status_code == 400 and "busy" in response.text.lower():
            if attempt < DEFAULT_LANE_BUSY_RETRY_ATTEMPTS:
                time.sleep(DEFAULT_LANE_BUSY_RETRY_DELAY_SECONDS)
                continue
        raise RegressionFailure(
            "lane start failed: "
            f"lane={lane_id} status={response.status_code} body={response.text[:300]}"
        )


def reset_bitcoin_lane(
    instructor_session: requests.Session,
    lane_id: str,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    for attempt in range(1, DEFAULT_LANE_BUSY_RETRY_ATTEMPTS + 1):
        response = instructor_session.post(f"{base_url}/api/bitcoin/lanes/{lane_id}/reset", timeout=30)
        if response.status_code == 200:
            return
        if response.status_code == 400 and "busy" in response.text.lower():
            if attempt < DEFAULT_LANE_BUSY_RETRY_ATTEMPTS:
                time.sleep(DEFAULT_LANE_BUSY_RETRY_DELAY_SECONDS)
                continue
        raise RegressionFailure(
            "lane reset failed: "
            f"lane={lane_id} status={response.status_code} body={response.text[:300]}"
        )


def wait_for_lane_running(
    instructor_session: requests.Session,
    lane_id: str,
    *,
    timeout_seconds: int = 30,
    interval_seconds: float = 1.0,
    stable_seconds: float = 2.0,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    deadline = time.time() + timeout_seconds
    running_since: float | None = None
    while time.time() < deadline:
        lanes = list_bitcoin_lanes(instructor_session, base_url)
        for lane in lanes:
            if lane.get("id") != lane_id:
                continue
            if lane.get("status") == "running":
                if running_since is None:
                    running_since = time.time()
                elif time.time() - running_since >= stable_seconds:
                    return
            else:
                running_since = None
            break
        time.sleep(interval_seconds)
    raise RegressionFailure(f"lane did not become ready: {lane_id}")


def prewarm_unclaimed_lane(
    instructor_session: requests.Session,
    *,
    avoid_stations: set[str],
    base_url: str = DEFAULT_BASE_URL,
) -> str | None:
    claims = list_bitcoin_claims(instructor_session, base_url)
    claimed_stations = {
        claim.get("station", "").strip()
        for claim in claims
        if claim.get("station")
    }
    lanes = list_bitcoin_lanes(instructor_session, base_url)

    candidates: list[str] = []
    for lane in lanes:
        lane_id = (lane.get("id") or "").strip()
        status = (lane.get("status") or "").strip().lower()
        if not lane_id or lane_id in claimed_stations or lane_id in avoid_stations:
            continue
        if status == "error":
            continue
        candidates.append(lane_id)

    if not candidates:
        return None

    last_error: Exception | None = None
    for lane_id in sorted(candidates):
        try:
            reset_bitcoin_lane(instructor_session, lane_id, base_url)
            start_bitcoin_lane(instructor_session, lane_id, base_url)
            wait_for_lane_running(instructor_session, lane_id, base_url=base_url)
            return lane_id
        except RegressionFailure as exc:
            last_error = exc
            avoid_stations.add(lane_id)

    if last_error is not None:
        raise RegressionFailure(f"could not prepare a clean unclaimed lane: {last_error}")
    return None


def claim_student_lane(
    student_session: requests.Session,
    instructor_session: requests.Session,
    base_url: str = DEFAULT_BASE_URL,
    *,
    fresh: bool = False,
    ready_timeout_seconds: int = DEFAULT_CLAIM_READY_TIMEOUT_SECONDS,
    retry_attempts: int = DEFAULT_CLAIM_RETRY_ATTEMPTS,
    retry_delay_seconds: float = DEFAULT_CLAIM_RETRY_DELAY_SECONDS,
    settle_seconds: float = DEFAULT_CLAIM_SETTLE_SECONDS,
) -> ClaimContext:
    last_error: Exception | None = None
    failed_stations: set[str] = set()

    for attempt in range(1, retry_attempts + 1):
        if fresh or attempt > 1:
            clear_cookie(student_session, "bitcoin_session")

        claim_response = student_session.get(f"{base_url}/api/bitcoin/claim", timeout=10)
        if claim_response.status_code != 200:
            raise RegressionFailure(
                f"claim failed: status={claim_response.status_code} body={claim_response.text[:300]}"
            )

        uuid = student_session.cookies.get("bitcoin_session")
        if not uuid:
            match = _UUID_RE.search(claim_response.text)
            uuid = match.group(1) if match else ""
        if not uuid:
            raise RegressionFailure("claim did not issue a bitcoin_session cookie or landing UUID")

        wrapper_url = f"{base_url}/labs/bitcoin/c/{uuid}/"
        wrapper_response = wait_for_http(
            student_session,
            wrapper_url,
            lambda resp: resp.status_code == 200 and "/labs/bitcoin/mempool/" in resp.text,
            description="bitcoin wrapper page",
        )

        claims = list_bitcoin_claims(instructor_session, base_url)
        station = ""
        for claim in claims:
            if claim.get("uuid") == uuid:
                station = claim.get("station", "").strip()
                if station:
                    break

        if not station:
            station_match = _STATION_RE.search(wrapper_response.text)
            if station_match:
                station = station_match.group(1)
        if not station:
            raise RegressionFailure(f"could not resolve station for claimed UUID {uuid}")

        claim_context = ClaimContext(uuid=uuid, station=station, wrapper_html=wrapper_response.text)
        try:
            if fresh:
                reset_bitcoin_lane(instructor_session, station, base_url)
                start_bitcoin_lane(instructor_session, station, base_url)
                wait_for_lane_running(instructor_session, station, base_url=base_url)
            if settle_seconds > 0:
                time.sleep(settle_seconds)
            wait_for_container_running(
                claim_context.container_name,
                timeout_seconds=ready_timeout_seconds,
                interval_seconds=1.0,
            )
            wait_for_http(
                student_session,
                f"{base_url}/labs/bitcoin/c/{uuid}/ttyd/",
                lambda resp: resp.status_code == 200 and "ttyd" in resp.text.lower(),
                timeout_seconds=min(ready_timeout_seconds, DEFAULT_TTYD_READY_TIMEOUT_SECONDS),
                interval_seconds=1.0,
                description=f"student ttyd route for {station}",
            )
            return claim_context
        except RegressionFailure as exc:
            last_error = exc
            failed_stations.add(station)
            try:
                release_claim(instructor_session, uuid, wipe=True, base_url=base_url)
            except Exception:
                pass
            clear_cookie(student_session, "bitcoin_session")
            if attempt < retry_attempts:
                try:
                    prewarm_unclaimed_lane(
                        instructor_session,
                        avoid_stations=failed_stations,
                        base_url=base_url,
                    )
                except RegressionFailure as prewarm_exc:
                    last_error = RegressionFailure(f"{exc}; prewarm failed: {prewarm_exc}")
            if attempt < retry_attempts and retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)

    raise RegressionFailure(
        f"could not obtain a ready bitcoin claim after {retry_attempts} attempts: {last_error}"
    )


def release_claim(
    instructor_session: requests.Session,
    claim_uuid: str,
    *,
    wipe: bool = True,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    response = instructor_session.delete(
        f"{base_url}/api/bitcoin/claims/{claim_uuid}",
        params={"wipe": "1" if wipe else "0"},
        timeout=20,
    )
    if response.status_code not in (200, 404):
        raise RegressionFailure(
            f"claim release failed: status={response.status_code} body={response.text[:300]}"
        )


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
    while time.time() < deadline:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True,
            text=True,
            timeout=10,
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


def docker_exec_checked(container: str, command: str, *, timeout_seconds: int = 60) -> str:
    result = docker_exec(container, command, timeout_seconds=timeout_seconds)
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


def docker_exec_json(container: str, command: str, *, timeout_seconds: int = 60) -> dict:
    output = docker_exec_checked(container, command, timeout_seconds=timeout_seconds).strip()
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RegressionFailure(f"expected JSON from {command!r}, got {output[:300]!r}") from exc


def docker_exec_int(container: str, command: str, *, timeout_seconds: int = 60) -> int:
    output = docker_exec_checked(container, command, timeout_seconds=timeout_seconds).strip()
    try:
        return int(output)
    except ValueError as exc:
        raise RegressionFailure(f"expected integer from {command!r}, got {output[:300]!r}") from exc


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
            output = docker_exec_checked(container, command).strip()
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


def wait_for_wallet_balance(
    container: str,
    wallet_name: str,
    expected_balance: float,
    *,
    timeout_seconds: int = 30,
    interval_seconds: float = 1.0,
) -> str:
    command = f"bitcoin-cli -rpcwallet={shlex.quote(wallet_name)} getbalance"
    return wait_for_docker_output(
        container,
        command,
        lambda output: abs(float(output) - expected_balance) < 1e-9,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        description=f"{wallet_name} balance {expected_balance}",
    )


def nuke_bitcoin_lab(
    instructor_session: requests.Session,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    response = instructor_session.post(f"{base_url}/api/bitcoin/nuke", timeout=180)
    if response.status_code != 200:
        raise RegressionFailure(
            f"bitcoin nuke failed: status={response.status_code} body={response.text[:300]}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise RegressionFailure(f"bitcoin nuke returned invalid JSON: {response.text[:300]!r}") from exc
    if not payload.get("success"):
        raise RegressionFailure(f"bitcoin nuke reported failure: {payload}")

    wait_for_container_running("bitcoin-instructor-1", timeout_seconds=120, interval_seconds=1.0)
    wait_for_container_running("bitcoin-mempool-1", timeout_seconds=120, interval_seconds=1.0)
    wait_for_docker_output(
        "bitcoin-instructor-1",
        "bitcoin-cli getblockcount",
        lambda output: int(output) >= 1,
        timeout_seconds=60,
        interval_seconds=1.0,
        description="fresh instructor seed chain",
    )


def ensure_classnet_claim(
    student_session: requests.Session,
    instructor_session: requests.Session,
    claim: ClaimContext,
    *,
    base_url: str = DEFAULT_BASE_URL,
    max_start_height: int = DEFAULT_CLASSNET_MAX_START_HEIGHT,
    allow_lab_reseed: bool = DEFAULT_ALLOW_CLASSNET_RESEED,
) -> ClaimContext:
    current_height = docker_exec_int(claim.container_name, "bitcoin-cli getblockcount")
    if current_height <= max_start_height:
        return claim

    if not allow_lab_reseed:
        raise RegressionFailure(
            f"classnet test requires a fresh bitcoin chain, but {claim.station} started at "
            f"height {current_height} (max allowed {max_start_height})"
        )

    nuke_bitcoin_lab(instructor_session, base_url=base_url)
    clear_cookie(student_session, "bitcoin_session")
    fresh_claim = claim_student_lane(
        student_session,
        instructor_session,
        base_url,
        fresh=True,
    )
    fresh_height = docker_exec_int(fresh_claim.container_name, "bitcoin-cli getblockcount")
    if fresh_height > max_start_height:
        raise RegressionFailure(
            f"classnet claim still drifted after bitcoin nuke: station={fresh_claim.station} "
            f"height={fresh_height} max_allowed={max_start_height}"
        )
    return fresh_claim


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
                "unexpected ttyd token response: "
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
        if self.connect_settle_seconds > 0:
            time.sleep(self.connect_settle_seconds)

    def close(self) -> None:
        if self.socket is None:
            return
        try:
            self.socket.close()
        except Exception:
            pass
        self.socket = None

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
        # zellij-backed ttyd sessions behave more like a student terminal when
        # commands arrive as paced keystrokes instead of one large paste blob.
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

        marker = f"__bitcoin_regression_{uuid_lib.uuid4().hex}__"
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
    *,
    columns: int = 120,
    rows: int = 40,
    connect_settle_seconds: float = DEFAULT_TTYD_CONNECT_SETTLE_SECONDS,
    post_command_settle_seconds: float = DEFAULT_TTYD_COMMAND_SETTLE_SECONDS,
    multiline_extra_settle_seconds: float = DEFAULT_TTYD_MULTILINE_EXTRA_SECONDS,
    keystroke_delay_seconds: float = DEFAULT_TTYD_KEYSTROKE_DELAY_SECONDS,
    line_settle_seconds: float = DEFAULT_TTYD_LINE_SETTLE_SECONDS,
) -> TtydSession:
    return TtydSession(
        session,
        base_url,
        ttyd_path,
        columns=columns,
        rows=rows,
        connect_settle_seconds=connect_settle_seconds,
        post_command_settle_seconds=post_command_settle_seconds,
        multiline_extra_settle_seconds=multiline_extra_settle_seconds,
        keystroke_delay_seconds=keystroke_delay_seconds,
        line_settle_seconds=line_settle_seconds,
    )


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
) -> str:
    with ttyd_session(session, base_url, ttyd_path, columns=columns, rows=rows) as terminal:
        result = terminal.run_command(command, timeout_seconds=timeout_seconds)
        if expected_fragment not in result.raw_output:
            raise RegressionFailure(
                f"timed out waiting for ttyd command output: expected {expected_fragment!r}, "
                f"last_output={result.raw_output[-500:]!r}"
            )
        return result.raw_output


def load_bitcoin_catalog() -> dict:
    lane_service_root = ROOT / "lane-service"
    if str(lane_service_root) not in sys.path:
        sys.path.insert(0, str(lane_service_root))
    from labs.bitcoin_catalog import CATALOG

    return CATALOG


def require_catalog_student_steps_contain(exercise_id: str, command_blocks: list[str]) -> None:
    catalog = load_bitcoin_catalog()
    exercise = next((ex for ex in catalog.get("exercises", []) if ex.get("id") == exercise_id), None)
    if exercise is None:
        raise RegressionFailure(f"bitcoin catalog exercise not found: {exercise_id}")
    combined_steps = "\n\n".join(exercise.get("student_steps", []))
    for block in command_blocks:
        if block not in combined_steps:
            raise RegressionFailure(
                f"catalog drift: expected command block not found in {exercise_id}: {block!r}"
            )


def wallet_setup_round_trip(container: str, wallet_name: str, share_filename: str) -> str:
    blockchain_info = docker_exec_json(container, "bitcoin-cli getblockchaininfo")
    if "blocks" not in blockchain_info:
        raise RegressionFailure("bitcoin-cli getblockchaininfo did not return a blocks field")

    create_output = docker_exec_checked(
        container,
        f"bitcoin-cli createwallet {shlex.quote(wallet_name)}",
    ).strip()
    create_payload = json.loads(create_output)
    if create_payload.get("name") != wallet_name:
        raise RegressionFailure(f"wallet creation returned unexpected payload: {create_payload}")

    address = docker_exec_checked(
        container,
        f"bitcoin-cli -rpcwallet={shlex.quote(wallet_name)} getnewaddress",
    ).strip()
    if not address or len(address) < 20:
        raise RegressionFailure(f"unexpected address output: {address!r}")

    wallet_info = docker_exec_json(
        container,
        f"bitcoin-cli -rpcwallet={shlex.quote(wallet_name)} getwalletinfo",
    )
    if wallet_info.get("walletname") != wallet_name:
        raise RegressionFailure(f"wallet info did not match wallet name: {wallet_info}")

    written = docker_exec_checked(
        container,
        "set -euo pipefail; "
        f"printf '%s\\n' {shlex.quote(address)} > \"$HOME/share/{share_filename}\"; "
        f"cat \"$HOME/share/{share_filename}\"",
    ).strip()
    if written != address:
        raise RegressionFailure(f"share file round-trip mismatch: expected {address!r}, got {written!r}")
    return address
