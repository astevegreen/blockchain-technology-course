"""The bitcoin lab's live-suite settings and its own helpers. The shared helpers live in ../live_common.py.

What differs from the other lane labs is set as options here: the instructor login retries a rate limit and reuses
any lab's cached cookie; a fresh claim resets and restarts its lane, and a failed one readies another unclaimed lane
before the retry; the lane must stay running 2 s; and the ttyd socket has a background reader, because the tests mine
through docker exec while a terminal sits idle.
"""
from __future__ import annotations

import json
import os
import shlex
import sys
import time
from pathlib import Path

import requests

_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ENV_PREFIX = "BITCOIN_REGRESSION"
SUPPORT = live_common.LaneLabSupport(
    # The wrapper page is ready once it links the mempool panel.
    live_common.LaneLab(
        slug="bitcoin", container_prefix="bitcoin-lab-student", wrapper_marker="/labs/bitcoin/mempool/"
    ),
    env_prefix=ENV_PREFIX,
    root=ROOT,
    cookie_cache_filename="bitcoin-regression-instructor-cookie.json",
    catalog_module="bitcoin_catalog",
    claim_settings=live_common.ClaimSettings.from_env(
        ENV_PREFIX, retry_attempts=3, retry_delay_seconds=3.0, settle_seconds=2.0, lane_stable_seconds=2.0
    ),
    ttyd_timing=live_common.TtydTiming.from_env(
        ENV_PREFIX, connect_settle_seconds=1.0, post_command_settle_seconds=0.75, line_settle_seconds=0.1
    ),
    http_interval_seconds=2.0,
    login_retries=5,
    login_retry_delay=5.0,
    share_cookie_caches=True,
    ttyd_background_reader=True,
)

DEFAULT_BASE_URL = SUPPORT.base_url
DEFAULT_LANE_BUSY_RETRY_ATTEMPTS = int(os.environ.get(f"{ENV_PREFIX}_LANE_BUSY_RETRY_ATTEMPTS", "6"))
DEFAULT_LANE_BUSY_RETRY_DELAY_SECONDS = float(os.environ.get(f"{ENV_PREFIX}_LANE_BUSY_RETRY_DELAY_SECONDS", "1.0"))
DEFAULT_CLASSNET_MAX_START_HEIGHT = int(os.environ.get(f"{ENV_PREFIX}_CLASSNET_MAX_START_HEIGHT", "11"))
DEFAULT_ALLOW_CLASSNET_RESEED = os.environ.get(f"{ENV_PREFIX}_ALLOW_CLASSNET_RESEED", "1").lower() not in {
    "0",
    "false",
    "no",
}
# A lane being reset or started waits this long to report running.
LANE_START_TIMEOUT_SECONDS = 30

RegressionFailure = live_common.RegressionFailure
ClaimContext = live_common.ClaimContext
CommandResult = live_common.CommandResult
new_session = live_common.new_session
clear_cookie = live_common.clear_cookie
strip_terminal_artifacts = live_common.strip_terminal_artifacts
docker_exec = live_common.docker_exec
docker_exec_checked = live_common.docker_exec_checked
docker_exec_json = live_common.docker_exec_json
docker_exec_int = live_common.docker_exec_int
docker_inspect = live_common.docker_inspect
wait_for_http = SUPPORT.wait_for_http
login_instructor = SUPPORT.login_instructor
list_bitcoin_claims = SUPPORT.list_claims
list_bitcoin_lanes = SUPPORT.list_lanes
release_claim = SUPPORT.release_claim
ttyd_session = SUPPORT.ttyd_session
ttyd_command_round_trip = SUPPORT.ttyd_command_round_trip
require_catalog_student_steps_contain = SUPPORT.require_catalog_student_steps_contain


def load_bitcoin_catalog() -> dict:
    return live_common.load_lane_service_catalog(ROOT, SUPPORT.catalog_module)


def wait_for_lane_running(
    instructor_session: requests.Session,
    lane_id: str,
    *,
    timeout_seconds: int = LANE_START_TIMEOUT_SECONDS,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    SUPPORT.wait_for_lane_running(instructor_session, lane_id, timeout_seconds=timeout_seconds, base_url=base_url)


def _lane_action(instructor_session: requests.Session, lane_id: str, action: str, base_url: str) -> None:
    """POST /api/bitcoin/lanes/<lane>/<action>, retrying while the lane reports itself busy."""
    for attempt in range(1, DEFAULT_LANE_BUSY_RETRY_ATTEMPTS + 1):
        response = instructor_session.post(f"{base_url}/api/bitcoin/lanes/{lane_id}/{action}", timeout=30)
        if response.status_code == 200:
            return
        if response.status_code == 400 and "busy" in response.text.lower():
            if attempt < DEFAULT_LANE_BUSY_RETRY_ATTEMPTS:
                time.sleep(DEFAULT_LANE_BUSY_RETRY_DELAY_SECONDS)
                continue
        raise RegressionFailure(
            f"lane {action} failed: lane={lane_id} status={response.status_code} body={response.text[:300]}"
        )


def start_bitcoin_lane(instructor_session: requests.Session, lane_id: str, base_url: str = DEFAULT_BASE_URL) -> None:
    _lane_action(instructor_session, lane_id, "start", base_url)


def reset_bitcoin_lane(instructor_session: requests.Session, lane_id: str, base_url: str = DEFAULT_BASE_URL) -> None:
    _lane_action(instructor_session, lane_id, "reset", base_url)


def _restart_lane(instructor_session: requests.Session, lane_id: str, base_url: str) -> None:
    reset_bitcoin_lane(instructor_session, lane_id, base_url)
    start_bitcoin_lane(instructor_session, lane_id, base_url)
    wait_for_lane_running(instructor_session, lane_id, base_url=base_url)


def prewarm_unclaimed_lane(
    instructor_session: requests.Session,
    *,
    avoid_stations: set[str],
    base_url: str = DEFAULT_BASE_URL,
) -> str | None:
    """Reset and start the first unclaimed, healthy lane not in avoid_stations, so the next claim gets a ready one."""
    claimed_stations = {
        claim.get("station", "").strip()
        for claim in list_bitcoin_claims(instructor_session, base_url)
        if claim.get("station")
    }
    candidates: list[str] = []
    for lane in list_bitcoin_lanes(instructor_session, base_url):
        lane_id = (lane.get("id") or "").strip()
        status = (lane.get("status") or "").strip().lower()
        if not lane_id or lane_id in claimed_stations or lane_id in avoid_stations or status == "error":
            continue
        candidates.append(lane_id)

    last_error: Exception | None = None
    for lane_id in sorted(candidates):
        try:
            _restart_lane(instructor_session, lane_id, base_url)
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
) -> ClaimContext:
    return SUPPORT.claim_student_lane(
        student_session,
        instructor_session,
        base_url,
        fresh=fresh,
        prepare_fresh_lane=lambda station: _restart_lane(instructor_session, station, base_url),
        # prewarm adds each lane it cannot ready to the failed set, so a later retry skips it too.
        before_retry=lambda failed: prewarm_unclaimed_lane(
            instructor_session, avoid_stations=failed, base_url=base_url
        ),
    )


def wait_for_container_running(container: str, *, timeout_seconds: int, interval_seconds: float = 1.0) -> None:
    live_common.wait_for_container_running(
        [container], timeout_seconds=timeout_seconds, interval_seconds=interval_seconds
    )


def wait_for_docker_output(
    container: str,
    command: str,
    predicate,
    *,
    timeout_seconds: int = SUPPORT.timeout_seconds,
    interval_seconds: float = 1.0,
    description: str,
) -> str:
    return live_common.wait_for_docker_output(
        container,
        command,
        predicate,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        description=description,
    )


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


def nuke_bitcoin_lab(instructor_session: requests.Session, *, base_url: str = DEFAULT_BASE_URL) -> None:
    response = instructor_session.post(f"{base_url}/api/bitcoin/nuke", timeout=180)
    if response.status_code != 200:
        raise RegressionFailure(f"bitcoin nuke failed: status={response.status_code} body={response.text[:300]}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RegressionFailure(f"bitcoin nuke returned invalid JSON: {response.text[:300]!r}") from exc
    if not payload.get("success"):
        raise RegressionFailure(f"bitcoin nuke reported failure: {payload}")

    wait_for_container_running("bitcoin-instructor-1", timeout_seconds=120)
    wait_for_container_running("bitcoin-mempool-1", timeout_seconds=120)
    wait_for_docker_output(
        "bitcoin-instructor-1",
        "bitcoin-cli getblockcount",
        lambda output: int(output) >= 1,
        timeout_seconds=60,
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
    """The claim if its chain is still near the seed height; otherwise reseed the lab (if allowed) and claim again."""
    current_height = docker_exec_int(claim.container_name, "bitcoin-cli getblockcount")
    if current_height <= max_start_height:
        return claim

    if not allow_lab_reseed:
        raise RegressionFailure(
            f"classnet test requires a fresh bitcoin chain, but {claim.station} started at "
            f"height {current_height} (max allowed {max_start_height})"
        )

    nuke_bitcoin_lab(instructor_session, base_url=base_url)
    clear_cookie(student_session, SUPPORT.lab.cookie_name)
    fresh_claim = claim_student_lane(student_session, instructor_session, base_url, fresh=True)
    fresh_height = docker_exec_int(fresh_claim.container_name, "bitcoin-cli getblockcount")
    if fresh_height > max_start_height:
        raise RegressionFailure(
            f"classnet claim still drifted after bitcoin nuke: station={fresh_claim.station} "
            f"height={fresh_height} max_allowed={max_start_height}"
        )
    return fresh_claim


def wallet_setup_round_trip(container: str, wallet_name: str, share_filename: str) -> str:
    blockchain_info = docker_exec_json(container, "bitcoin-cli getblockchaininfo")
    if "blocks" not in blockchain_info:
        raise RegressionFailure("bitcoin-cli getblockchaininfo did not return a blocks field")

    create_output = docker_exec_checked(container, f"bitcoin-cli createwallet {shlex.quote(wallet_name)}").strip()
    create_payload = json.loads(create_output)
    if create_payload.get("name") != wallet_name:
        raise RegressionFailure(f"wallet creation returned unexpected payload: {create_payload}")

    address = docker_exec_checked(
        container,
        f"bitcoin-cli -rpcwallet={shlex.quote(wallet_name)} getnewaddress",
    ).strip()
    if not address or len(address) < 20:
        raise RegressionFailure(f"unexpected address output: {address!r}")

    wallet_info = docker_exec_json(container, f"bitcoin-cli -rpcwallet={shlex.quote(wallet_name)} getwalletinfo")
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
