from __future__ import annotations

import os


def env_int(*names: str, default: int) -> int:
    for name in names:
        value = os.environ.get(name)
        if value not in (None, ""):
            return int(value)
    return default
