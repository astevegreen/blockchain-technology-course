"""
p2p_trust lab lane configuration.

Uses docker-run mode: every student container is identical, created
from the pre-built p2p-trust-lab-student image on demand.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from exercises import register_catalog
from generic_claims import ClaimManager
from generic_lanes import LaneConfig, LaneManager
from labs.env_utils import env_int
from labs.p2p_trust_catalog import (
    CATALOG as P2P_TRUST_CATALOG,
    EXERCISE_IDS as P2P_TRUST_EXERCISE_IDS,
)
from lab_blueprint import make_lab_blueprint

IMAGE = os.environ.get("P2P_TRUST_IMAGE", "p2p-trust-lab-student")
NETWORK = os.environ.get("P2P_TRUST_NETWORK", "p2p-trust-student-net")
STUDENT_COUNT = max(
    1,
    env_int("P2P_TRUST_STUDENT_CAPACITY", "MAX_STUDENT_CAPACITY", "STUDENT_COUNT", default=20),
)
DEFAULT_WARM_POOL_SIZE = max(
    0,
    min(
        STUDENT_COUNT,
        env_int("P2P_TRUST_WARM_POOL_SIZE", "STUDENT_WARM_POOL_SIZE", default=0),
    ),
)
STUDENT_HOME_ROOT = (os.environ.get("P2P_TRUST_STUDENT_HOME_ROOT") or "").strip() or None
STUDENT_PIDS_LIMIT = max(
    0,
    env_int("P2P_TRUST_STUDENT_PIDS_LIMIT", "STUDENT_PIDS_LIMIT", default=256),
) or None
STUDENT_MEMORY_LIMIT = (
    os.environ.get("P2P_TRUST_STUDENT_MEMORY_LIMIT")
    or os.environ.get("STUDENT_MEMORY_LIMIT")
    or "512m"
)

STATE_DIR = Path(os.environ.get(
    "P2P_TRUST_STATE_DIR",
    "/app/runtime/p2p_trust",
))


def _container_name(lane_id: str) -> str:
    return f"p2p-trust-lab-student{lane_id[1:]}"


def _readiness_probe(lane_id: str, container: str) -> tuple[bool, str]:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "--user",
            "1000:1000",
            container,
            "bash",
            "-lc",
            (
                "test -d /home/student/lab/scripts "
                "&& test -f /home/student/lab/scripts/gossip_demo.py "
                "&& test -f /home/student/lab/scripts/dht_demo.py "
                "&& test -f /home/student/lab/scripts/ngo_sim.py"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0:
        return True, "student lab files ready"
    detail = (result.stderr or result.stdout or "student lab files not ready").strip()
    return False, detail[:300]


config = LaneConfig(
    lab_name="p2p_trust",
    container_name_fn=_container_name,
    state_dir=STATE_DIR,
    image=IMAGE,
    network=NETWORK,
    student_count=STUDENT_COUNT,
    user="1000:1000",
    pids_limit=STUDENT_PIDS_LIMIT,
    memory_limit=STUDENT_MEMORY_LIMIT,
    read_only_rootfs=bool(STUDENT_HOME_ROOT),
    tmpfs_mounts=["/tmp:size=64m,mode=1777", "/run:size=16m"] if STUDENT_HOME_ROOT else None,
    security_opt=["no-new-privileges:true"],
    cap_drop=["ALL"],
    docker_init=True,
    student_home_root=STUDENT_HOME_ROOT,
    student_home_seed_path="/opt/student-home-seed",
    readiness_probe=_readiness_probe,
    readiness_timeout_seconds=15.0,
)

lane_manager = LaneManager(config)
claim_manager = ClaimManager(config, lane_manager)

register_catalog("p2p_trust", P2P_TRUST_CATALOG)

PANEL_HTML = (
    '<span>P2P Trust Lab &middot; station <span class="station">{{STATION}}</span></span>'
    '<span class="grow"></span>'
)

blueprint = make_lab_blueprint(
    config, lane_manager, claim_manager,
    wrapper_panel_html=PANEL_HTML,
    enable_progress=True,
    progress_exercise_ids=P2P_TRUST_EXERCISE_IDS,
)


def start():
    if claim_manager.get_pool_size() <= 0 and DEFAULT_WARM_POOL_SIZE > 0:
        claim_manager.set_pool_size(DEFAULT_WARM_POOL_SIZE)
    lane_manager.start_sweeper()
    claim_manager.start_sweeper()


def stop():
    claim_manager.stop_sweeper()
    lane_manager.destroy_all("removed during lane-service shutdown")
