"""The session, wait, login, docker, lane-claim and ttyd helpers the labs' live_support.py files share.

Each lab's live_support.py imports this module (as run-lab.sh is shared by the runners) and keeps what is its own:
its settings (base URL, timeouts, cookie cache file) and thin wrappers that hand those settings to the functions
here. Nothing here reads a lab's settings on import, so a wait, timeout or retry count is whatever the lab's
wrapper passes in; ClaimSettings.from_env and TtydTiming.from_env read them only when a lab asks, by its prefix.
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid as uuid_lib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse, urlunparse

import requests

try:
    from websocket import ABNF, WebSocketTimeoutException, create_connection
except ImportError:  # pragma: no cover - only the ttyd labs' runners install websocket-client
    ABNF = None
    create_connection = None

    class WebSocketTimeoutException(TimeoutError):
        pass

# The student launcher's own stack (student-launcher/: one student on their own PC) has no instructor pages or
# APIs. run-lab.sh sets this when --skip-start finds that stack. A suite then skips its instructor-only tests with
# NO_INSTRUCTOR as the reason, and the lane helpers below work from the student's side alone: the one lane is
# handed back to every claim and cannot be released, so a "fresh" claim is the same lane again.
STUDENT_LAUNCHER = os.environ.get("LAB_REGRESSION_STUDENT_LAUNCHER") == "1"
NO_INSTRUCTOR = "the student launcher has no instructor pages"

USERNAME_RE = re.compile(r"^Username:\s*(.+)$", re.MULTILINE)
PASSWORD_RE = re.compile(r"^Password:\s*(.+)$", re.MULTILINE)
ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
OSC_RE = re.compile(r"\x1B\].*?(?:\x07|\x1B\\)")


class RegressionFailure(RuntimeError):
    pass


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def clear_cookie(session: requests.Session, cookie_name: str) -> None:
    for cookie in list(session.cookies):
        if cookie.name == cookie_name:
            session.cookies.clear(domain=cookie.domain, path=cookie.path, name=cookie.name)


def cookie_header(session: requests.Session) -> str:
    cookies = session.cookies.get_dict()
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def to_websocket_url(http_url: str) -> str:
    parsed = urlparse(http_url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse(parsed._replace(scheme=ws_scheme))


def decode_terminal_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def strip_terminal_artifacts(text: str) -> str:
    text = OSC_RE.sub("", text)
    text = ANSI_RE.sub("", text)
    text = text.replace("\r", "")
    return text


def parse_instructor_credentials(path: Path, env_var: str) -> tuple[str, str]:
    """Read the instructor's Username/Password lines; env_var names the lab's setting for the file in the error."""
    if not path.exists():
        raise RegressionFailure(
            f"instructor credentials file not found: {path}. "
            f"Run deploy first or point {env_var} at a valid file."
        )
    content = path.read_text(encoding="utf-8")
    username = USERNAME_RE.search(content)
    password = PASSWORD_RE.search(content)
    if not username or not password:
        raise RegressionFailure(f"could not parse instructor credentials from {path}")
    return username.group(1).strip(), password.group(1).strip()


def wait_for_http(
    session: requests.Session,
    url: str,
    predicate: Callable[[requests.Response], bool],
    *,
    timeout_seconds: int,
    interval_seconds: float,
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


def session_has_valid_instructor_cookie(session: requests.Session, base_url: str) -> bool:
    try:
        response = session.get(f"{base_url}/api/instructor/whoami", timeout=10)
    except requests.RequestException:
        return False
    if response.status_code != 200:
        return False
    payload = response.json()
    return bool(payload.get("authenticated"))


def candidate_cookie_cache_paths(cache_path: Path, root: Path) -> list[Path]:
    """The lab's own cache file first, then every lab's cache file under <root>/.runtime."""
    candidates = [cache_path]
    runtime_dir = root / ".runtime"
    try:
        for path in sorted(runtime_dir.glob("*-regression-instructor-cookie.json")):
            if path not in candidates:
                candidates.append(path)
    except OSError:
        pass
    return candidates


def load_cached_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_paths: list[Path],
    cookie_name: str,
    *,
    match_base_url: bool = True,
    max_age_seconds: float | None = None,
    after_valid: Callable[[], None] | None = None,
) -> bool:
    """Try each cached cookie in turn; True once one passes the whoami probe."""
    for candidate in cache_paths:
        if not candidate.exists():
            continue
        try:
            # Instructor cookies expire 1 h after login, with no renewal; an older cached one passes the probe
            # and then expires mid-suite. Only labs that pass max_age_seconds skip stale files.
            if max_age_seconds is not None and time.time() - candidate.stat().st_mtime > max_age_seconds:
                continue
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if match_base_url and payload.get("base_url") != base_url:
            continue
        cookie_value = (payload.get("cookie_value") or "").strip()
        if not cookie_value:
            continue
        session.cookies.set(cookie_name, cookie_value, path="/")
        if session_has_valid_instructor_cookie(session, base_url):
            if after_valid is not None:
                after_valid()
            return True
        clear_cookie(session, cookie_name)
    return False


def persist_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path,
    cookie_name: str,
) -> None:
    cookie_value = session.cookies.get(cookie_name)
    if not cookie_value:
        return
    payload = {
        "base_url": base_url,
        "cookie_name": cookie_name,
        "cookie_value": cookie_value,
    }
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        return


def login_instructor(
    session: requests.Session,
    base_url: str,
    *,
    load_cached: Callable[[], bool],
    credentials: Callable[[], tuple[str, str]],
    persist: Callable[[], None],
    max_retries: int,
    retry_delay: float,
    after_login: Callable[[], None] | None = None,
) -> None:
    """Reuse a cached instructor cookie, else log in, retrying a 429 after retry_delay * attempt seconds.

    Most labs need only login_instructor_once; this form lets a lab add retries or its own cache rules.

    max_retries=1 means no retry. after_login runs after a 200 and before the cookie is probed.
    """
    if load_cached():
        return

    username, password = credentials()
    for attempt in range(1, max_retries + 1):
        response = session.post(
            f"{base_url}/api/instructor/login",
            json={"user": username, "key": password},
            timeout=10,
        )
        if response.status_code == 200:
            if after_login is not None:
                after_login()
            if not session_has_valid_instructor_cookie(session, base_url):
                raise RegressionFailure("instructor login did not yield a usable instructor session")
            persist()
            return
        if response.status_code == 429 and attempt < max_retries:
            time.sleep(retry_delay * attempt)
            continue
        raise RegressionFailure(
            f"instructor login failed: status={response.status_code} body={response.text[:300]}"
        )


def login_instructor_once(
    session: requests.Session,
    base_url: str,
    *,
    cache_path: Path,
    cookie_name: str,
    credentials: Callable[[], tuple[str, str]],
) -> None:
    """Reuse the lab's own cached instructor cookie, else log in once (no retry) and cache the new cookie."""
    login_instructor(
        session,
        base_url,
        load_cached=lambda: load_cached_instructor_cookie(session, base_url, [cache_path], cookie_name),
        credentials=credentials,
        persist=lambda: persist_instructor_cookie(session, base_url, cache_path, cookie_name),
        max_retries=1,
        retry_delay=0.0,
    )


# --- docker exec and inspect -------------------------------------------------------------------------------------


def docker_exec(
    container: str,
    command: str,
    *,
    timeout_seconds: int = 60,
    user: str | None = None,
    shell_flag: str = "-lc",
) -> subprocess.CompletedProcess[str]:
    """Run command in bash inside container, killed after timeout_seconds; shell_flag "-ic" makes it interactive."""
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
            shell_flag,
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
    shell_flag: str = "-lc",
) -> str:
    result = docker_exec(container, command, timeout_seconds=timeout_seconds, user=user, shell_flag=shell_flag)
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
    timeout_seconds: int,
    interval_seconds: float = 1.0,
    attempt_timeout_seconds: int = 60,
    description: str,
) -> str:
    """Rerun command in container until predicate accepts its stripped output; each try is killed after
    attempt_timeout_seconds. A failed try or a ValueError from predicate counts as not yet."""
    deadline = time.time() + timeout_seconds
    last_output = ""
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            output = docker_exec_checked(container, command, timeout_seconds=attempt_timeout_seconds).strip()
            last_output = output
            if predicate(output):
                return output
        except (RegressionFailure, ValueError) as exc:
            last_error = exc
        time.sleep(interval_seconds)
    if last_output:
        raise RegressionFailure(f"timed out waiting for {description}: last_output={last_output!r}")
    raise RegressionFailure(f"timed out waiting for {description}: last_error={last_error}")


def wait_for_container_running(
    candidates: list[str],
    *,
    timeout_seconds: int,
    interval_seconds: float = 1.0,
) -> str:
    """Wait until one of the candidate container names is running, and return that name."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        for candidate in candidates:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", candidate],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip() == "true":
                return candidate
        time.sleep(interval_seconds)
    raise RegressionFailure(f"container did not become ready: {candidates}")


# --- lane claims: labs that hand each student a lane (/api/<slug>/claim, then /labs/<slug>/c/<uuid>/) -------------

STATION_RE = re.compile(r'<span class="station">(s\d{2})</span>')


def _env_number(prefix: str, name: str, default: float, kind: type = float):
    return kind(os.environ.get(f"{prefix}_{name}", str(default)))


@dataclass(frozen=True)
class LaneLab:
    """A lab whose students claim lanes: slug is its URL and API segment, container_prefix names its containers.

    The claim waits for a wrapper page that contains wrapper_marker (the ttyd frame unless the lab names a link
    its own panel adds, which shows the lab's page rather than a bare one).
    """

    slug: str
    container_prefix: str
    wrapper_marker: str = "/ttyd/"

    @property
    def cookie_name(self) -> str:
        return f"{self.slug}_session"

    @property
    def uuid_re(self) -> re.Pattern[str]:
        return re.compile(rf"/labs/{re.escape(self.slug)}/c/([0-9a-f-]{{36}})/")

    def container_names(self, station: str) -> list[str]:
        """Lane container names for a station such as s01: "<prefix>01", then "<prefix>1"."""
        suffix = station[1:]
        variants = [suffix]
        try:
            normalized = str(int(suffix))
        except ValueError:
            normalized = suffix
        if normalized not in variants:
            variants.append(normalized)
        return [f"{self.container_prefix}{variant}" for variant in variants]


@dataclass(frozen=True)
class ClaimSettings:
    ready_timeout_seconds: int = 90
    retry_attempts: int = 4
    retry_delay_seconds: float = 2.0
    settle_seconds: float = 1.0
    ttyd_ready_timeout_seconds: int = 20
    # How long the lane must report "running" in a row before the claim trusts it.
    lane_stable_seconds: float = 1.0

    @classmethod
    def from_env(cls, prefix: str, **lab_defaults) -> ClaimSettings:
        """Read <prefix>_CLAIM_READY_TIMEOUT, _CLAIM_RETRY_ATTEMPTS, _CLAIM_RETRY_DELAY_SECONDS,
        _CLAIM_SETTLE_SECONDS and _TTYD_READY_TIMEOUT, falling back to lab_defaults, then the defaults above."""
        defaults = cls(**lab_defaults)
        return dataclasses.replace(
            defaults,
            ready_timeout_seconds=_env_number(prefix, "CLAIM_READY_TIMEOUT", defaults.ready_timeout_seconds, int),
            retry_attempts=_env_number(prefix, "CLAIM_RETRY_ATTEMPTS", defaults.retry_attempts, int),
            retry_delay_seconds=_env_number(prefix, "CLAIM_RETRY_DELAY_SECONDS", defaults.retry_delay_seconds),
            settle_seconds=_env_number(prefix, "CLAIM_SETTLE_SECONDS", defaults.settle_seconds),
            ttyd_ready_timeout_seconds=_env_number(
                prefix, "TTYD_READY_TIMEOUT", defaults.ttyd_ready_timeout_seconds, int
            ),
        )


@dataclass
class ClaimContext:
    uuid: str
    station: str
    wrapper_html: str
    container_name: str

    @property
    def short_id(self) -> str:
        return self.uuid[:8]


def _instructor_list(session: requests.Session, url: str, key: str) -> list[dict]:
    response = session.get(url, timeout=10)
    if response.status_code != 200:
        raise RegressionFailure(f"{key} API failed: status={response.status_code} body={response.text[:300]}")
    return response.json().get(key, [])


def list_claims(instructor_session: requests.Session, base_url: str, lab: LaneLab) -> list[dict]:
    if STUDENT_LAUNCHER:
        return []
    return _instructor_list(instructor_session, f"{base_url}/api/{lab.slug}/claims", "claims")


def list_lanes(instructor_session: requests.Session, base_url: str, lab: LaneLab) -> list[dict]:
    if STUDENT_LAUNCHER:
        return []
    return _instructor_list(instructor_session, f"{base_url}/api/{lab.slug}/lanes", "lanes")


def wait_for_lane_running(
    instructor_session: requests.Session,
    base_url: str,
    lab: LaneLab,
    lane_id: str,
    *,
    timeout_seconds: int,
    interval_seconds: float = 1.0,
    stable_seconds: float = 1.5,
) -> None:
    """Wait until the lane has reported "running" for stable_seconds in a row.

    The student launcher has no lanes API: the claim's wait for the lane's container stands in for this one."""
    if STUDENT_LAUNCHER:
        return
    deadline = time.time() + timeout_seconds
    running_since: float | None = None
    while time.time() < deadline:
        for lane in list_lanes(instructor_session, base_url, lab):
            if lane.get("id") != lane_id:
                continue
            if (lane.get("status") or "").lower() == "running":
                if running_since is None:
                    running_since = time.time()
                elif time.time() - running_since >= stable_seconds:
                    return
            else:
                running_since = None
            break
        time.sleep(interval_seconds)
    raise RegressionFailure(f"lane did not become ready: {lane_id}")


def release_claim(
    instructor_session: requests.Session,
    base_url: str,
    lab: LaneLab,
    claim_uuid: str,
    *,
    wipe: bool = True,
) -> None:
    if STUDENT_LAUNCHER:  # the student's one lane stays theirs
        return
    response = instructor_session.delete(
        f"{base_url}/api/{lab.slug}/claims/{claim_uuid}",
        params={"wipe": "1" if wipe else "0"},
        timeout=20,
    )
    if response.status_code not in (200, 404):
        raise RegressionFailure(
            f"claim release failed: status={response.status_code} body={response.text[:300]}"
        )


def _claim_station(
    instructor_session: requests.Session, base_url: str, lab: LaneLab, uuid: str, wrapper_html: str
) -> str:
    """The claim's station from the instructor claims list, else from the wrapper page."""
    for claim in list_claims(instructor_session, base_url, lab):
        if claim.get("uuid") == uuid:
            station = (claim.get("station") or "").strip()
            if station:
                return station
            break
    station_match = STATION_RE.search(wrapper_html)
    if station_match:
        return station_match.group(1)
    raise RegressionFailure(f"could not resolve station for claimed UUID {uuid}")


def claim_student_lane(
    student_session: requests.Session,
    instructor_session: requests.Session,
    base_url: str,
    lab: LaneLab,
    *,
    fresh: bool = False,
    settings: ClaimSettings = ClaimSettings(),
    prepare_fresh_lane: Callable[[str], None] | None = None,
    before_retry: Callable[[set[str]], None] | None = None,
) -> ClaimContext:
    """Claim a lane as a student and wait until its wrapper page, lane, container and ttyd route are ready.

    A 503 (no lane free) or a lane that never gets ready is retried up to settings.retry_attempts times, releasing
    the half-ready claim first; any other claim status fails at once. A lab may pass prepare_fresh_lane(station),
    run on a fresh claim before the waits (to reset and restart the lane), and before_retry(failed_stations), run
    before each retry after a lane failed (to ready another lane); a RegressionFailure from before_retry is added
    to the error reported if every attempt fails.
    """
    last_error: Exception | None = None
    failed_stations: set[str] = set()

    for attempt in range(1, settings.retry_attempts + 1):
        if fresh or attempt > 1:
            clear_cookie(student_session, lab.cookie_name)

        claim_response = student_session.get(f"{base_url}/api/{lab.slug}/claim", timeout=10)
        if claim_response.status_code == 503:
            last_error = RegressionFailure(
                f"claim unavailable: status={claim_response.status_code} body={claim_response.text[:300]}"
            )
            if attempt < settings.retry_attempts and settings.retry_delay_seconds > 0:
                time.sleep(settings.retry_delay_seconds)
            continue
        if claim_response.status_code != 200:
            raise RegressionFailure(
                f"claim failed: status={claim_response.status_code} body={claim_response.text[:300]}"
            )

        uuid = student_session.cookies.get(lab.cookie_name)
        if not uuid:
            match = lab.uuid_re.search(claim_response.text)
            uuid = match.group(1) if match else ""
        if not uuid:
            raise RegressionFailure(f"claim did not issue a {lab.cookie_name} cookie or landing UUID")

        wrapper_response = wait_for_http(
            student_session,
            f"{base_url}/labs/{lab.slug}/c/{uuid}/",
            lambda resp: (
                resp.status_code == 200 and f"/labs/{lab.slug}/c/" in resp.url and lab.wrapper_marker in resp.text
            ),
            timeout_seconds=settings.ready_timeout_seconds,
            interval_seconds=1.0,
            description=f"{lab.slug} wrapper page",
        )
        station = _claim_station(instructor_session, base_url, lab, uuid, wrapper_response.text)

        try:
            if fresh and prepare_fresh_lane is not None:
                prepare_fresh_lane(station)
            if settings.settle_seconds > 0:
                time.sleep(settings.settle_seconds)
            wait_for_lane_running(
                instructor_session,
                base_url,
                lab,
                station,
                timeout_seconds=settings.ready_timeout_seconds,
                stable_seconds=settings.lane_stable_seconds,
            )
            container_name = wait_for_container_running(
                lab.container_names(station),
                timeout_seconds=settings.ready_timeout_seconds,
            )
            wait_for_http(
                student_session,
                f"{base_url}/labs/{lab.slug}/c/{uuid}/ttyd/",
                lambda resp: resp.status_code == 200 and "ttyd" in resp.text.lower(),
                timeout_seconds=settings.ttyd_ready_timeout_seconds,
                interval_seconds=1.0,
                description=f"student ttyd route for {station}",
            )
            return ClaimContext(
                uuid=uuid,
                station=station,
                wrapper_html=wrapper_response.text,
                container_name=container_name,
            )
        except RegressionFailure as exc:
            last_error = exc
            failed_stations.add(station)
            try:
                release_claim(instructor_session, base_url, lab, uuid, wipe=True)
            except Exception:
                pass
            clear_cookie(student_session, lab.cookie_name)
            if attempt < settings.retry_attempts and before_retry is not None:
                try:
                    before_retry(failed_stations)
                except RegressionFailure as retry_exc:
                    last_error = RegressionFailure(f"{exc}; preparing a retry failed: {retry_exc}")
            if attempt < settings.retry_attempts and settings.retry_delay_seconds > 0:
                time.sleep(settings.retry_delay_seconds)

    raise RegressionFailure(
        f"could not obtain a ready {lab.slug} claim after {settings.retry_attempts} attempts: {last_error}"
    )


def load_lane_service_catalog(root: Path, module_name: str) -> dict:
    """CATALOG from lane-service/labs/<module_name>.py: the exercises and student steps the lab's pages show."""
    lane_service_root = str(root / "lane-service")
    if lane_service_root not in sys.path:
        sys.path.insert(0, lane_service_root)
    module = __import__(f"labs.{module_name}", fromlist=["CATALOG"])
    return module.CATALOG


def require_catalog_student_steps_contain(
    catalog: dict, lab_name: str, exercise_id: str, command_blocks: list[str]
) -> None:
    exercise = next((ex for ex in catalog.get("exercises", []) if ex.get("id") == exercise_id), None)
    if exercise is None:
        raise RegressionFailure(f"{lab_name} catalog exercise not found: {exercise_id}")
    combined_steps = "\n\n".join(exercise.get("student_steps", []))
    for block in command_blocks:
        if block not in combined_steps:
            raise RegressionFailure(
                f"catalog drift: expected command block not found in {exercise_id}: {block!r}"
            )


# --- ttyd (the students' browser terminal), driven over its websocket --------------------------------------------


@dataclass
class CommandResult:
    command: str
    output: str
    exit_code: int
    raw_output: str


@dataclass(frozen=True)
class TtydTiming:
    connect_settle_seconds: float = 0.75
    post_command_settle_seconds: float = 0.5
    multiline_extra_settle_seconds: float = 0.25
    keystroke_delay_seconds: float = 0.02
    line_settle_seconds: float = 0.08

    @classmethod
    def from_env(cls, prefix: str, **lab_defaults) -> TtydTiming:
        """Read <prefix>_TTYD_CONNECT_SETTLE_SECONDS, _TTYD_COMMAND_SETTLE_SECONDS, _TTYD_MULTILINE_EXTRA_SECONDS,
        _TTYD_KEYSTROKE_DELAY_SECONDS and _TTYD_LINE_SETTLE_SECONDS, falling back to lab_defaults, then the
        defaults above."""
        defaults = cls(**lab_defaults)
        return cls(
            connect_settle_seconds=_env_number(
                prefix, "TTYD_CONNECT_SETTLE_SECONDS", defaults.connect_settle_seconds
            ),
            post_command_settle_seconds=_env_number(
                prefix, "TTYD_COMMAND_SETTLE_SECONDS", defaults.post_command_settle_seconds
            ),
            multiline_extra_settle_seconds=_env_number(
                prefix, "TTYD_MULTILINE_EXTRA_SECONDS", defaults.multiline_extra_settle_seconds
            ),
            keystroke_delay_seconds=_env_number(
                prefix, "TTYD_KEYSTROKE_DELAY_SECONDS", defaults.keystroke_delay_seconds
            ),
            line_settle_seconds=_env_number(prefix, "TTYD_LINE_SETTLE_SECONDS", defaults.line_settle_seconds),
        )


# A shell prompt at the end of a line of terminal output.
_PROMPT_RE = re.compile(r"[$#]\s*$", re.MULTILINE)


class TtydSession:
    """A ttyd terminal opened as the student's browser opens it, that types commands and reads their output back.

    marker_prefix names the lab in the end-of-command marker; strip cleans terminal output before it is matched.
    background_reader=True gives the socket one reader thread for the session's life, as a browser tab has: it
    answers ttyd's pings and drains output while the test does slow work elsewhere (bitcoin mines through docker
    exec), where an idle session would miss its pongs and ttyd would drop it (broken pipe).
    wait_for_prompt=True makes connect wait for a shell prompt ($ or #) instead of sleeping, for up to
    timing.connect_settle_seconds and then 5 s more after pressing Enter (hlf's shell starts slowly); prompt_ready
    then says whether one appeared.
    """

    def __init__(
        self,
        session: requests.Session,
        base_url: str,
        ttyd_path: str,
        *,
        marker_prefix: str,
        timing: TtydTiming = TtydTiming(),
        strip: Callable[[str], str] = strip_terminal_artifacts,
        columns: int = 120,
        rows: int = 40,
        background_reader: bool = False,
        wait_for_prompt: bool = False,
    ) -> None:
        if create_connection is None or ABNF is None:
            raise RegressionFailure("websocket-client is not installed in the regression runner")
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.ttyd_path = ttyd_path
        self.marker_prefix = marker_prefix
        self.timing = timing
        self.strip = strip
        self.columns = columns
        self.rows = rows
        self.background_reader = background_reader
        self.wait_for_prompt = wait_for_prompt
        self._prompt_ready = False
        self.socket = None
        self.collected = ""
        self._reader: threading.Thread | None = None
        self._reader_stop = threading.Event()
        self._reader_error: BaseException | None = None

    def __enter__(self) -> TtydSession:
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def connect(self) -> None:
        ttyd_url = urljoin(f"{self.base_url}/", self.ttyd_path.lstrip("/"))
        ws_url = to_websocket_url(ttyd_url.rstrip("/") + "/ws")
        token_url = ttyd_url.rstrip("/") + "/token"
        origin = f"{urlparse(self.base_url).scheme}://{urlparse(self.base_url).netloc}"
        header_value = cookie_header(self.session)
        headers = [f"Cookie: {header_value}"] if header_value else []
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
            enable_multithread=self.background_reader,
        )
        self.socket.settimeout(1)
        init_payload = json.dumps(
            {"AuthToken": auth_token, "columns": self.columns, "rows": self.rows}
        ).encode("utf-8")
        self.socket.send(init_payload, opcode=ABNF.OPCODE_BINARY)
        if self.background_reader:
            self._reader_stop.clear()
            self._reader_error = None
            self._reader = threading.Thread(target=self._read_loop, name="ttyd-reader", daemon=True)
            self._reader.start()
        self._warm()
        if self.wait_for_prompt:
            self._wait_for_prompt()
        elif self.timing.connect_settle_seconds > 0:
            time.sleep(self.timing.connect_settle_seconds)

    def close(self) -> None:
        if self.socket is None:
            return
        self._reader_stop.set()
        if self._reader is not None:
            self._reader.join(timeout=5)
            self._reader = None
        try:
            self.socket.close()
        except Exception:
            pass
        self.socket = None

    @property
    def prompt_ready(self) -> bool:
        """True once connect saw a shell prompt (only checked with wait_for_prompt=True)."""
        return self._prompt_ready

    def _seen_prompt(self) -> bool:
        if _PROMPT_RE.search(self.strip(self.collected)):
            time.sleep(0.5)
            self._prompt_ready = True
        return self._prompt_ready

    def _wait_for_prompt(self) -> None:
        # Press Enter once after ttyd's "Connected to" banner, and again if no prompt shows by the deadline.
        self._prompt_ready = False
        saw_banner = False
        deadline = time.time() + self.timing.connect_settle_seconds
        while time.time() < deadline:
            self._receive()
            if self._seen_prompt():
                return
            if not saw_banner and "Connected to " in self.strip(self.collected):
                saw_banner = True
                self._send_input("\r")
                time.sleep(0.25)
        self._send_input("\r")
        extra_deadline = time.time() + 5
        while time.time() < extra_deadline:
            self._receive()
            if self._seen_prompt():
                return

    def _warm(self) -> None:
        deadline = time.time() + 3
        while time.time() < deadline:
            if self._receive():
                return

    def _receive(self) -> bool:
        """Take in output: read one frame, or with a reader thread, check it and wait a moment for it.
        True once some output has arrived (with a reader thread, in the session so far)."""
        if self._reader is None:
            return self._recv_once()
        if self._reader_error is not None:
            raise RegressionFailure(f"ttyd websocket reader stopped: {self._reader_error!r}")
        time.sleep(0.1)
        return bool(self.collected)

    def _read_loop(self) -> None:
        while not self._reader_stop.is_set():
            try:
                self._recv_once()
            except BaseException as exc:  # surfaced to the test by _receive
                if not self._reader_stop.is_set():
                    self._reader_error = exc
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
        if not raw or chr(raw[0]) != "0":
            return False
        self.collected += decode_terminal_text(raw[1:])
        return True

    def _send_input(self, text: str) -> None:
        if self.socket is None:
            raise RegressionFailure("ttyd websocket is not connected")
        if not text:
            return
        self.socket.send(b"0" + text.encode("utf-8"), opcode=ABNF.OPCODE_BINARY)

    def _send_line(self, text: str) -> None:
        # Paced keystrokes, as a student types, rather than one pasted blob.
        for char in text:
            self._send_input(char)
            if self.timing.keystroke_delay_seconds > 0:
                time.sleep(self.timing.keystroke_delay_seconds)
        self._send_input("\r")
        if self.timing.line_settle_seconds > 0:
            time.sleep(self.timing.line_settle_seconds)

    def run_command(self, command: str, *, timeout_seconds: int = 20) -> CommandResult:
        """Type command (its lines joined with "; ") and a marker that prints its exit code; wait for the marker."""
        if self.socket is None:
            raise RegressionFailure("ttyd websocket is not connected")

        marker = f"__{self.marker_prefix}_regression_{uuid_lib.uuid4().hex}__"
        ttyd_command = command.strip("\r\n").replace("\r\n", "\n").replace("\r", "\n")
        ttyd_lines = [line.strip() for line in ttyd_command.split("\n") if line.strip()]
        transmit_command = "; ".join(ttyd_lines)
        start_idx = len(self.collected)
        self._send_line(f"{transmit_command}; printf '{marker}:%s\\n' \"$?\"")

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            segment = self.strip(self.collected[start_idx:])
            exit_matches = list(re.finditer(re.escape(marker) + r":(\d+)", segment))
            if exit_matches:
                exit_match = exit_matches[-1]
                extra_lines = max(len(ttyd_lines) - 1, 0)
                settle_seconds = self.timing.post_command_settle_seconds + (
                    extra_lines * self.timing.multiline_extra_settle_seconds
                )
                if settle_seconds > 0:
                    time.sleep(settle_seconds)
                return CommandResult(
                    command=command,
                    output=segment[:exit_match.start()].strip(),
                    exit_code=int(exit_match.group(1)),
                    raw_output=segment.strip(),
                )
            self._receive()

        raise RegressionFailure(
            f"timed out waiting for ttyd command completion: command={command!r} "
            f"last_output={self.strip(self.collected[start_idx:])[-600:]!r}"
        )


def ttyd_command_round_trip(
    terminal: TtydSession,
    command: str,
    *,
    expected_fragment: str,
    timeout_seconds: int = 20,
) -> str:
    """Open terminal, run command once and return its raw output; fail unless expected_fragment appears in it."""
    with terminal:
        result = terminal.run_command(command, timeout_seconds=timeout_seconds)
        if expected_fragment not in result.raw_output:
            raise RegressionFailure(
                f"timed out waiting for ttyd command output: expected {expected_fragment!r}, "
                f"last_output={result.raw_output[-500:]!r}"
            )
        return result.raw_output



class LaneLabSupport:
    """What a lane-claiming lab's live suite calls, bound to that lab's settings.

    A lab's live_support.py builds one and exports its methods under the names its tests import. The base URL,
    timeout, credentials file and cookie cache file come from <prefix>_BASE_URL, _TIMEOUT, _CREDENTIALS_FILE and
    _INSTRUCTOR_COOKIE_CACHE_FILE, as each lab's own constants did.

    The options keep a lab's differences: http_interval_seconds is how often wait_for_http polls by default;
    login_retries and login_retry_delay retry a rate-limited (429) instructor login; share_cookie_caches lets the
    login reuse any lab's cached instructor cookie, not only this lab's; ttyd_background_reader is TtydSession's.
    """

    def __init__(
        self,
        lab: LaneLab,
        *,
        env_prefix: str,
        root: Path,
        cookie_cache_filename: str,
        catalog_module: str,
        claim_settings: ClaimSettings,
        ttyd_timing: TtydTiming,
        instructor_cookie_name: str = "hlf_instructor",
        strip: Callable[[str], str] = strip_terminal_artifacts,
        http_interval_seconds: float = 1.0,
        login_retries: int = 1,
        login_retry_delay: float = 0.0,
        share_cookie_caches: bool = False,
        ttyd_background_reader: bool = False,
    ) -> None:
        self.lab = lab
        self.env_prefix = env_prefix
        self.root = root
        self.base_url = os.environ.get(f"{env_prefix}_BASE_URL", "http://127.0.0.1").rstrip("/")
        self.timeout_seconds = int(os.environ.get(f"{env_prefix}_TIMEOUT", "180"))
        runtime = root / ".runtime"
        self.credentials_file = Path(
            os.environ.get(f"{env_prefix}_CREDENTIALS_FILE", str(runtime / "instructor-credentials.txt"))
        )
        self.cookie_cache_file = Path(
            os.environ.get(f"{env_prefix}_INSTRUCTOR_COOKIE_CACHE_FILE", str(runtime / cookie_cache_filename))
        )
        self.instructor_cookie_name = instructor_cookie_name
        self.catalog_module = catalog_module
        self.claim_settings = claim_settings
        self.ttyd_timing = ttyd_timing
        self.strip = strip
        self.http_interval_seconds = http_interval_seconds
        self.login_retries = login_retries
        self.login_retry_delay = login_retry_delay
        self.share_cookie_caches = share_cookie_caches
        self.ttyd_background_reader = ttyd_background_reader

    def wait_for_http(
        self,
        session: requests.Session,
        url: str,
        predicate: Callable[[requests.Response], bool],
        *,
        timeout_seconds: int | None = None,
        interval_seconds: float | None = None,
        description: str,
        allow_redirects: bool = True,
    ) -> requests.Response:
        return wait_for_http(
            session,
            url,
            predicate,
            timeout_seconds=self.timeout_seconds if timeout_seconds is None else timeout_seconds,
            interval_seconds=self.http_interval_seconds if interval_seconds is None else interval_seconds,
            description=description,
            allow_redirects=allow_redirects,
        )

    def parse_instructor_credentials(self, path: Path | None = None) -> tuple[str, str]:
        return parse_instructor_credentials(path or self.credentials_file, f"{self.env_prefix}_CREDENTIALS_FILE")

    def login_instructor(self, session: requests.Session, base_url: str | None = None) -> None:
        base_url = base_url or self.base_url
        cache_paths = (
            candidate_cookie_cache_paths(self.cookie_cache_file, self.root)
            if self.share_cookie_caches
            else [self.cookie_cache_file]
        )
        cookie_name = self.instructor_cookie_name
        login_instructor(
            session,
            base_url,
            load_cached=lambda: load_cached_instructor_cookie(session, base_url, cache_paths, cookie_name),
            credentials=self.parse_instructor_credentials,
            persist=lambda: persist_instructor_cookie(session, base_url, self.cookie_cache_file, cookie_name),
            max_retries=self.login_retries,
            retry_delay=self.login_retry_delay,
        )

    def list_claims(self, instructor_session: requests.Session, base_url: str | None = None) -> list[dict]:
        return list_claims(instructor_session, base_url or self.base_url, self.lab)

    def list_lanes(self, instructor_session: requests.Session, base_url: str | None = None) -> list[dict]:
        return list_lanes(instructor_session, base_url or self.base_url, self.lab)

    def wait_for_lane_running(
        self,
        instructor_session: requests.Session,
        lane_id: str,
        *,
        timeout_seconds: int | None = None,
        base_url: str | None = None,
    ) -> None:
        wait_for_lane_running(
            instructor_session,
            base_url or self.base_url,
            self.lab,
            lane_id,
            timeout_seconds=self.claim_settings.ready_timeout_seconds if timeout_seconds is None else timeout_seconds,
            stable_seconds=self.claim_settings.lane_stable_seconds,
        )

    def claim_student_lane(
        self,
        student_session: requests.Session,
        instructor_session: requests.Session,
        base_url: str | None = None,
        *,
        fresh: bool = False,
        prepare_fresh_lane: Callable[[str], None] | None = None,
        before_retry: Callable[[set[str]], None] | None = None,
    ) -> ClaimContext:
        return claim_student_lane(
            student_session,
            instructor_session,
            base_url or self.base_url,
            self.lab,
            fresh=fresh,
            settings=self.claim_settings,
            prepare_fresh_lane=prepare_fresh_lane,
            before_retry=before_retry,
        )

    def release_claim(
        self,
        instructor_session: requests.Session,
        claim_uuid: str,
        *,
        wipe: bool = True,
        base_url: str | None = None,
    ) -> None:
        release_claim(instructor_session, base_url or self.base_url, self.lab, claim_uuid, wipe=wipe)

    def ttyd_session(
        self, session: requests.Session, base_url: str, ttyd_path: str, *, columns: int = 120, rows: int = 40
    ) -> TtydSession:
        return TtydSession(
            session,
            base_url,
            ttyd_path,
            marker_prefix=self.lab.slug,
            timing=self.ttyd_timing,
            strip=self.strip,
            columns=columns,
            rows=rows,
            background_reader=self.ttyd_background_reader,
        )

    def ttyd_command_round_trip(
        self,
        session: requests.Session,
        base_url: str,
        ttyd_path: str,
        command: str,
        *,
        expected_fragment: str,
        timeout_seconds: int = 20,
    ) -> str:
        return ttyd_command_round_trip(
            self.ttyd_session(session, base_url, ttyd_path),
            command,
            expected_fragment=expected_fragment,
            timeout_seconds=timeout_seconds,
        )

    def require_catalog_student_steps_contain(self, exercise_id: str, command_blocks: list[str]) -> None:
        catalog = load_lane_service_catalog(self.root, self.catalog_module)
        require_catalog_student_steps_contain(catalog, self.lab.slug, exercise_id, command_blocks)
