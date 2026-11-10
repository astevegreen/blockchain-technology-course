from __future__ import annotations

import os
from typing import Optional

from generic_lanes import student_local_mode


def env_int(*names: str, default: int) -> int:
    for name in names:
        value = os.environ.get(name)
        if value not in (None, ""):
            return int(value)
    return default


def lane_capacity(*names: str, default: int) -> int:
    """How many lanes a lab runs: one on a student's own machine (LANE_MODE=student-local), else the first set
    variable of `names`, at least one."""
    if student_local_mode():
        return 1
    return max(1, env_int(*names, default=default))


def warm_pool_size(capacity: int, *names: str, default: int) -> int:
    """Lanes started before anyone claims one: none on a student's own machine, where the one lane starts when the
    student opens the lab."""
    if student_local_mode():
        return 0
    return max(0, min(capacity, env_int(*names, default=default)))


def student_home_root(name: str) -> Optional[str]:
    """The host folder that holds each lane's home disk, or None. Never one on a student's own machine: the launcher
    mounts no host folders, so a lane keeps its home inside its container."""
    if student_local_mode():
        return None
    return (os.environ.get(name) or "").strip() or None
