from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

import requests

# The session, login, docker exec and ttyd helpers live in ../live_common.py, shared by every lab's live_support.py.
# This file keeps the lab's own settings, its API and claim flow, and the thin wrappers that pass them in.
_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ENV_PREFIX = "HLF_REGRESSION"
DEFAULT_BASE_URL = os.environ.get("HLF_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("HLF_REGRESSION_TIMEOUT", "180"))
DEFAULT_STARTUP_READY_TIMEOUT_SECONDS = int(
    os.environ.get("HLF_REGRESSION_STARTUP_READY_TIMEOUT", "900")
)
# HLF_REGRESSION_CLAIM_* and HLF_REGRESSION_TTYD_* override these (live_common's from_env names them).
CLAIM_SETTINGS = live_common.ClaimSettings.from_env(
    ENV_PREFIX,
    ready_timeout_seconds=120,
    retry_attempts=3,
    retry_delay_seconds=5.0,
    settle_seconds=3.0,
    ttyd_ready_timeout_seconds=60,
)
DEFAULT_CLAIM_READY_TIMEOUT_SECONDS = CLAIM_SETTINGS.ready_timeout_seconds
DEFAULT_CLAIM_RETRY_ATTEMPTS = CLAIM_SETTINGS.retry_attempts
DEFAULT_CLAIM_RETRY_DELAY_SECONDS = CLAIM_SETTINGS.retry_delay_seconds
DEFAULT_CLAIM_SETTLE_SECONDS = CLAIM_SETTINGS.settle_seconds
# The peer CLI shell takes a while to print its prompt, so connect waits for the prompt for up to
# connect_settle_seconds rather than sleeping that long (TtydSession's wait_for_prompt).
TTYD_TIMING = live_common.TtydTiming.from_env(
    ENV_PREFIX,
    connect_settle_seconds=1.5,
    post_command_settle_seconds=1.0,
    line_settle_seconds=0.1,
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

_UUID_RE = re.compile(r"/labs/hlf/c/([0-9a-f-]{36})/")

RegressionFailure = live_common.RegressionFailure
CommandResult = live_common.CommandResult
TtydSession = live_common.TtydSession
new_session = live_common.new_session
clear_cookie = live_common.clear_cookie
strip_terminal_artifacts = live_common.strip_terminal_artifacts
docker_exec = live_common.docker_exec
docker_exec_checked = live_common.docker_exec_checked


def parse_instructor_credentials(path: Path = DEFAULT_CREDENTIALS_FILE) -> tuple[str, str]:
    return live_common.parse_instructor_credentials(path, "HLF_REGRESSION_CREDENTIALS_FILE")


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


# Instructor cookies expire 1 h after login, with no renewal; an older cached one passes the probe
# and then expires mid-suite.
_COOKIE_CACHE_MAX_AGE = 30 * 60


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
        match_base_url=False,
        max_age_seconds=_COOKIE_CACHE_MAX_AGE,
        after_valid=lambda: _acquire_csrf_token(session, base_url),
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
        after_login=lambda: _acquire_csrf_token(session, base_url),
    )


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


def _acquire_csrf_token(session: requests.Session, base_url: str = DEFAULT_BASE_URL) -> None:
    resp = session.post(f"{base_url}/api/instructor/csrf", timeout=10)
    if resp.status_code != 200:
        return
    token = resp.json().get("token", "")
    if token:
        session.headers["X-CSRFToken"] = token


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

def wait_for_container_running(
    container: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    interval_seconds: float = 2.0,
) -> None:
    live_common.wait_for_container_running(
        [container], timeout_seconds=timeout_seconds, interval_seconds=interval_seconds
    )


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

def ttyd_session(
    session: requests.Session,
    base_url: str,
    ttyd_path: str,
    *,
    columns: int = 120,
    rows: int = 40,
    connect_settle_seconds: float | None = None,
) -> TtydSession:
    """A ttyd terminal whose connect waits for the shell prompt, for up to connect_settle_seconds
    (TTYD_TIMING's by default); check prompt_ready after connect."""
    timing = TTYD_TIMING
    if connect_settle_seconds is not None:
        timing = replace(TTYD_TIMING, connect_settle_seconds=connect_settle_seconds)
    return TtydSession(
        session,
        base_url,
        ttyd_path,
        marker_prefix="hlf",
        timing=timing,
        columns=columns,
        rows=rows,
        wait_for_prompt=True,
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
    connect_settle_seconds: float | None = None,
) -> str:
    return live_common.ttyd_command_round_trip(
        ttyd_session(
            session, base_url, ttyd_path,
            columns=columns, rows=rows, connect_settle_seconds=connect_settle_seconds,
        ),
        command,
        expected_fragment=expected_fragment,
        timeout_seconds=timeout_seconds,
    )
