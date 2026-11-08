"""The consensus lab's live-suite settings. The helpers live in ../live_common.py, shared by every lab."""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

ENV_PREFIX = "CONSENSUS_REGRESSION"
_claim_settings = live_common.ClaimSettings.from_env(ENV_PREFIX)
SUPPORT = live_common.LaneLabSupport(
    live_common.LaneLab(slug="consensus", container_prefix="consensus-lab-student"),
    env_prefix=ENV_PREFIX,
    root=Path(__file__).resolve().parents[3],
    cookie_cache_filename="consensus-regression-instructor-cookie.json",
    catalog_module="consensus_catalog",
    # This lab waits for the ttyd route as long as for the lane itself.
    claim_settings=dataclasses.replace(
        _claim_settings, ttyd_ready_timeout_seconds=_claim_settings.ready_timeout_seconds
    ),
    ttyd_timing=live_common.TtydTiming.from_env(ENV_PREFIX),
)

DEFAULT_BASE_URL = SUPPORT.base_url
RegressionFailure = live_common.RegressionFailure
ClaimContext = live_common.ClaimContext
new_session = live_common.new_session
clear_cookie = live_common.clear_cookie
strip_terminal_artifacts = live_common.strip_terminal_artifacts
docker_exec = live_common.docker_exec
docker_exec_checked = live_common.docker_exec_checked
docker_inspect = live_common.docker_inspect
wait_for_http = SUPPORT.wait_for_http
login_instructor = SUPPORT.login_instructor
list_consensus_claims = SUPPORT.list_claims
claim_student_lane = SUPPORT.claim_student_lane
release_claim = SUPPORT.release_claim
ttyd_session = SUPPORT.ttyd_session
ttyd_command_round_trip = SUPPORT.ttyd_command_round_trip
require_catalog_student_steps_contain = SUPPORT.require_catalog_student_steps_contain
