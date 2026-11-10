"""The p2p_trust lab's live-suite settings. The helpers live in ../live_common.py, shared by every lab."""
from __future__ import annotations

import functools
import re
import sys
from pathlib import Path

_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

ENV_PREFIX = "P2P_TRUST_REGRESSION"
# This lab's container shell is interactive (bash -ic), which prints job-control warnings into the output.
_SHELL_NOISE_RE = re.compile(
    r"^bash: (?:cannot set terminal process group.*|no job control in this shell)\n?",
    re.MULTILINE,
)


def strip_terminal_artifacts(text: str) -> str:
    return _SHELL_NOISE_RE.sub("", live_common.strip_terminal_artifacts(text))


SUPPORT = live_common.LaneLabSupport(
    live_common.LaneLab(slug="p2p_trust", container_prefix="p2p-trust-lab-student"),
    env_prefix=ENV_PREFIX,
    root=Path(__file__).resolve().parents[3],
    cookie_cache_filename="p2p-trust-regression-instructor-cookie.json",
    catalog_module="p2p_trust_catalog",
    claim_settings=live_common.ClaimSettings.from_env(ENV_PREFIX),
    ttyd_timing=live_common.TtydTiming.from_env(ENV_PREFIX),
    strip=strip_terminal_artifacts,
)

DEFAULT_BASE_URL = SUPPORT.base_url
RegressionFailure = live_common.RegressionFailure
STUDENT_LAUNCHER = live_common.STUDENT_LAUNCHER
NO_INSTRUCTOR = live_common.NO_INSTRUCTOR
ClaimContext = live_common.ClaimContext
new_session = live_common.new_session
clear_cookie = live_common.clear_cookie
docker_exec = functools.partial(live_common.docker_exec, shell_flag="-ic")
docker_exec_checked = functools.partial(live_common.docker_exec_checked, shell_flag="-ic")
docker_inspect = live_common.docker_inspect
wait_for_http = SUPPORT.wait_for_http
login_instructor = SUPPORT.login_instructor
list_p2p_trust_claims = SUPPORT.list_claims
claim_student_lane = SUPPORT.claim_student_lane
release_claim = SUPPORT.release_claim
ttyd_session = SUPPORT.ttyd_session
ttyd_command_round_trip = SUPPORT.ttyd_command_round_trip
require_catalog_student_steps_contain = SUPPORT.require_catalog_student_steps_contain
