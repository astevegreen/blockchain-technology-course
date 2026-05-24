"""
Ethereum lab — on-demand per-student frontend lanes against a shared
instructor-run hardhat chain.

Architecture differs from bitcoin:
- The blockchain itself is shared. There's exactly one hardhat node,
  inside the long-running `ethereum-trainer-instructor` container, and
  every student SPA proxies JSON-RPC through the platform router at
  `/labs/ethereum_lab/rpc` (which hits the instructor's in-container
  nginx → :8545).
- Each student gets a thin lane container (same image, MODE=student)
  that serves the SPA + lab-API + ttyd PTY. No hardhat node per lane.
- A capacity-sized address pool, derived from the canonical hardhat mnemonic and
  pre-funded by the instructor on startup, is partitioned by station
  number. The lane's env carries ASSIGNED_ADDRESS / ASSIGNED_PRIVATE_KEY
  so the SPA can pre-load the wallet without a per-student race.

Routing (see router/routes/ethereum.conf):
  /labs/ethereum_lab/                — claim → cookie → resolve to lane :5173
  /labs/ethereum_lab/rpc             — ungated → instructor :8080/rpc
  /labs/ethereum_lab/instructor/...  — cookie-gated → instructor :8080
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional
from urllib.error import URLError
from urllib.request import urlopen

from exercises import register_catalog
from generic_claims import ClaimManager
from generic_lanes import LaneConfig, LaneManager
from lab_blueprint import make_lab_blueprint
from labs.ethereum_catalog import (
    CATALOG as ETH_CATALOG,
    EXERCISE_IDS as ETH_EXERCISE_IDS,
    SURFACE_IDS as ETH_SURFACE_IDS,
)
from labs.env_utils import env_int

LAB_NAME = "ethereum"

IMAGE = os.environ.get("ETHEREUM_IMAGE", "ethereum-trainer")
MGMT_NET = os.environ.get("ETHEREUM_MGMT_NET", "ethereum-student-mgmt-net")
STUDENT_COUNT = max(
    1,
    env_int("ETHEREUM_STUDENT_CAPACITY", "MAX_STUDENT_CAPACITY", "STUDENT_COUNT", default=20),
)
DEFAULT_WARM_POOL_SIZE = max(
    0,
    min(
        STUDENT_COUNT,
        env_int("ETHEREUM_WARM_POOL_SIZE", "STUDENT_WARM_POOL_SIZE", default=1),
    ),
)
INSTRUCTOR_HOST = os.environ.get(
    "ETHEREUM_INSTRUCTOR_HOST", "ethereum-trainer-instructor"
)
INSTRUCTOR_PORT = os.environ.get("ETHEREUM_INSTRUCTOR_PORT", "8080")
INSTRUCTOR_HTTP_URL = f"http://{INSTRUCTOR_HOST}:{INSTRUCTOR_PORT}"
POOL_URL = f"{INSTRUCTOR_HTTP_URL}/api/student-pool.json"
CONFIG_URL = f"{INSTRUCTOR_HTTP_URL}/api/config.json"
TERMINAL_RPC_URL = os.environ.get(
    "ETHEREUM_TERMINAL_RPC_URL",
    "http://router-router-1/labs/ethereum_lab/rpc",
)
STUDENT_HOME_ROOT = (os.environ.get("ETHEREUM_STUDENT_HOME_ROOT") or "").strip() or None
STUDENT_PIDS_LIMIT = max(
    0,
    env_int("ETHEREUM_STUDENT_PIDS_LIMIT", "STUDENT_PIDS_LIMIT", default=256),
) or None
STUDENT_MEMORY_LIMIT = (
    os.environ.get("ETHEREUM_STUDENT_MEMORY_LIMIT")
    or os.environ.get("STUDENT_MEMORY_LIMIT")
    or "512m"
)

STATE_DIR = Path(os.environ.get(
    "ETHEREUM_STATE_DIR",
    "/app/runtime/ethereum",
))


def _container_name(lane_id: str) -> str:
    return f"ethereum-lab-student{int(lane_id[1:])}"


# Pool cache: keyed by station id ("s01"..). Refreshed lazily on miss.
_pool_lock = threading.Lock()
_pool_cache: Dict[str, dict] = {}
_pool_fetched_at: float = 0.0
_POOL_TTL = 300  # re-pull every 5 min so re-funding picks up new keys
_config_lock = threading.Lock()
_config_cache: Dict[str, str] = {}
_config_fetched_at: float = 0.0
_CONFIG_TTL = 30


def _fetch_json(url: str) -> Optional[dict]:
    try:
        with urlopen(url, timeout=5) as r:
            doc = json.loads(r.read().decode("utf-8"))
    except (URLError, OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _refresh_pool() -> None:
    global _pool_fetched_at
    doc = _fetch_json(POOL_URL)
    if doc is None:
        return
    pool = doc.get("pool") or []
    new_cache: Dict[str, dict] = {}
    for entry in pool:
        st = entry.get("station")
        if st:
            new_cache[st] = entry
    if new_cache:
        with _pool_lock:
            _pool_cache.clear()
            _pool_cache.update(new_cache)
            _pool_fetched_at = time.time()


def _pool_entry(station: str) -> Optional[dict]:
    with _pool_lock:
        cached = _pool_cache.get(station)
        age = time.time() - _pool_fetched_at
    if cached and age < _POOL_TTL:
        return cached
    _refresh_pool()
    with _pool_lock:
        return _pool_cache.get(station)


def _refresh_runtime_config() -> None:
    global _config_fetched_at
    doc = _fetch_json(CONFIG_URL)
    if doc is None:
        return
    new_cache: Dict[str, str] = {}
    contract = str(doc.get("contractAddress") or "").strip()
    beacon = str(doc.get("beaconLabContractAddress") or "").strip()
    if contract:
        new_cache["contractAddress"] = contract
    if beacon:
        new_cache["beaconLabContractAddress"] = beacon
    with _config_lock:
        _config_cache.clear()
        _config_cache.update(new_cache)
        _config_fetched_at = time.time()


def _runtime_config() -> Dict[str, str]:
    with _config_lock:
        cached = dict(_config_cache)
        age = time.time() - _config_fetched_at
    if cached.get("contractAddress") and age < _CONFIG_TTL:
        return cached
    _refresh_runtime_config()
    with _config_lock:
        return dict(_config_cache)


def _metadata_ready() -> bool:
    with _pool_lock:
        pool_ready = bool(_pool_cache)
    config_ready = bool(_runtime_config().get("contractAddress"))
    return pool_ready and config_ready


def _wait_for_instructor_metadata(timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while True:
        _refresh_pool()
        _refresh_runtime_config()
        if _metadata_ready():
            return True
        if time.time() >= deadline:
            return False
        time.sleep(1)


def _lane_env(lane_id: str) -> Dict[str, str]:
    """Per-lane env injected at `docker run` time."""
    env: Dict[str, str] = {
        "MODE": "student",
        "FRONTEND_PORT": "5173",
        "TERMINAL_PORTS": "3002,3003,3004",
        "TERMINAL_CWD": "/home/student/workspace",
        "HOME": "/home/student",
        "USER": "student",
        "SHELL": "/bin/bash",
        "TERMINAL_UID": "1000",
        "TERMINAL_GID": "1000",
        "LAB_TERMINAL_ENABLED": "1",
        # Student CLI traffic reaches the shared instructor RPC through
        # the outer router, not by talking to the instructor container
        # directly over a shared Docker network.
        "INSTRUCTOR_RPC_URL": TERMINAL_RPC_URL,
        "TERMINAL_RPC_URL": TERMINAL_RPC_URL,
        # The browser must reach RPC via the public router path; the
        # terminal gets its own absolute RPC URL above.
        "RPC_URL_PUBLIC": "/rpc",
        "STATION": lane_id,
    }
    entry = _pool_entry(lane_id)
    if entry:
        env["ASSIGNED_ADDRESS"] = entry.get("address", "")
        env["ASSIGNED_PRIVATE_KEY"] = entry.get("privateKey", "")
    runtime_config = _runtime_config()
    contract = runtime_config.get("contractAddress", "")
    beacon = runtime_config.get("beaconLabContractAddress", "")
    if contract:
        env["CONTRACT_ADDRESS"] = contract
    if beacon:
        env["BEACON_LAB_ADDRESS"] = beacon
    return env


config = LaneConfig(
    lab_name=LAB_NAME,
    container_name_fn=_container_name,
    state_dir=STATE_DIR,
    image=IMAGE,
    network=MGMT_NET,
    student_count=STUDENT_COUNT,
    env_fn=_lane_env,
    idle_timeout=1200,
    user="1000:1000",
    pids_limit=STUDENT_PIDS_LIMIT,
    memory_limit=STUDENT_MEMORY_LIMIT,
    read_only_rootfs=True,
    tmpfs_mounts=[
        "/tmp:size=64m,mode=1777",
        "/run:size=16m,uid=1000,gid=1000,mode=0755",
        "/app/frontend/dist/api:size=1m,uid=1000,gid=1000,mode=0755",
        *([] if STUDENT_HOME_ROOT else ["/home/student:size=512m,uid=1000,gid=1000,mode=0755"]),
    ],
    security_opt=["no-new-privileges:true"],
    cap_drop=["ALL"],
    docker_init=True,
    student_home_root=STUDENT_HOME_ROOT,
    student_home_container_path="/home/student",
    student_home_seed_path="/opt/student-home-seed",
    student_home_uid=1000,
    student_home_gid=1000,
)

lane_manager = LaneManager(config)
claim_manager = ClaimManager(config, lane_manager)

register_catalog(LAB_NAME, ETH_CATALOG)

blueprint = make_lab_blueprint(
    config, lane_manager, claim_manager,
    enable_wrapper_page=False,
    claim_landing_template="/labs/ethereum_lab/",
    enable_progress=True,
    progress_exercise_ids=ETH_EXERCISE_IDS,
    progress_surface_ids=ETH_SURFACE_IDS,
    admin_instructor_href="/labs/ethereum_lab/?mode=instructor",
)


def start() -> None:
    # Student lanes need the instructor's wallet pool and deployed
    # contract metadata before they are started. Otherwise warm-pool
    # lanes can come up with empty ASSIGNED_* / CONTRACT_* env and stay
    # stale until manually reset.
    metadata_ready = _wait_for_instructor_metadata()
    if metadata_ready and claim_manager.get_pool_size() <= 0 and DEFAULT_WARM_POOL_SIZE > 0:
        claim_manager.set_pool_size(DEFAULT_WARM_POOL_SIZE)
    lane_manager.start_sweeper()
    claim_manager.start_sweeper()


def stop() -> None:
    claim_manager.stop_sweeper()
    lane_manager.destroy_all("removed during lane-service shutdown")
