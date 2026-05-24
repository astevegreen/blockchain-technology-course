"""
Consensus lab lane configuration.

Uses docker-run mode: every student container is identical, created
from the pre-built consensus-lab-student image on demand.
No per-student crypto, enrollment, or unique config.
"""

from __future__ import annotations

import os
from pathlib import Path

from exercises import register_catalog
from generic_claims import ClaimManager
from generic_lanes import LaneConfig, LaneManager
from labs.consensus_catalog import (
    CATALOG as CONSENSUS_CATALOG,
    EXERCISE_IDS as CONSENSUS_EXERCISE_IDS,
)
from labs.env_utils import env_int
from lab_blueprint import make_lab_blueprint

IMAGE = os.environ.get("CONSENSUS_IMAGE", "consensus-lab-student")
NETWORK = os.environ.get("CONSENSUS_NETWORK", "consensus-student-net")
STUDENT_COUNT = max(
    1,
    env_int("CONSENSUS_STUDENT_CAPACITY", "MAX_STUDENT_CAPACITY", "STUDENT_COUNT", default=20),
)
DEFAULT_WARM_POOL_SIZE = max(
    0,
    min(
        STUDENT_COUNT,
        env_int("CONSENSUS_WARM_POOL_SIZE", "STUDENT_WARM_POOL_SIZE", default=0),
    ),
)
STUDENT_HOME_ROOT = (os.environ.get("CONSENSUS_STUDENT_HOME_ROOT") or "").strip() or None
STUDENT_PIDS_LIMIT = max(
    0,
    env_int("CONSENSUS_STUDENT_PIDS_LIMIT", "STUDENT_PIDS_LIMIT", default=256),
) or None
STUDENT_MEMORY_LIMIT = (
    os.environ.get("CONSENSUS_STUDENT_MEMORY_LIMIT")
    or os.environ.get("STUDENT_MEMORY_LIMIT")
    or "512m"
)

STATE_DIR = Path(os.environ.get(
    "CONSENSUS_STATE_DIR",
    "/app/runtime/consensus",
))


def _container_name(lane_id: str) -> str:
    return f"consensus-lab-student{lane_id[1:]}"


config = LaneConfig(
    lab_name="consensus",
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
)

lane_manager = LaneManager(config)
claim_manager = ClaimManager(config, lane_manager)

register_catalog("consensus", CONSENSUS_CATALOG)

PANEL_HTML = (
    '<span>Consensus Lab &middot; station <span class="station">{{STATION}}</span></span>'
    '<span class="grow"></span>'
)

blueprint = make_lab_blueprint(
    config, lane_manager, claim_manager,
    wrapper_panel_html=PANEL_HTML,
    enable_progress=True,
    progress_exercise_ids=CONSENSUS_EXERCISE_IDS,
)


def start():
    if claim_manager.get_pool_size() <= 0 and DEFAULT_WARM_POOL_SIZE > 0:
        claim_manager.set_pool_size(DEFAULT_WARM_POOL_SIZE)
    lane_manager.start_sweeper()
    claim_manager.start_sweeper()


def stop():
    claim_manager.stop_sweeper()
    lane_manager.destroy_all("removed during lane-service shutdown")
