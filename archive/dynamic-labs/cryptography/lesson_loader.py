"""
Loads per-scenario lesson markdown from `lessons/<scenario-id>.md`.

Path resolution is locked to the `lessons/` directory: scenario ids
must match ``[a-z][a-z0-9-]*`` and the resolved file must sit
directly in that directory. That keeps a malformed id from escaping
into the rest of the filesystem.
"""

from __future__ import annotations

import re
from pathlib import Path

_LESSONS_DIR = (Path(__file__).resolve().parent / "lessons").resolve()
_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def load_lesson(scenario_id: str) -> str:
    if not _ID_RE.match(scenario_id):
        raise ValueError(f"invalid scenario id: {scenario_id!r}")
    path = (_LESSONS_DIR / f"{scenario_id}.md").resolve()
    if path.parent != _LESSONS_DIR or not path.is_file():
        raise FileNotFoundError(f"no lesson for {scenario_id}")
    return path.read_text(encoding="utf-8")
