"""
Shared loader for per-lab YAML catalogs.

Each lab keeps its content in `labs/<lab>_catalog.yaml`. The matching
`labs/<lab>_catalog.py` is a 4-line shim that calls `load_catalog`.

Path resolution is locked to this directory: the lab name must match
``[a-z][a-z0-9_]*`` and the resolved file must sit directly in
`labs/`. That keeps a malformed name from escaping into the rest of
the filesystem.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import yaml

_LABS_DIR = Path(__file__).resolve().parent
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def load_catalog(lab_name: str) -> Dict[str, Any]:
    if not _NAME_RE.match(lab_name):
        raise ValueError(f"invalid lab name: {lab_name!r}")
    path = (_LABS_DIR / f"{lab_name}_catalog.yaml").resolve()
    if path.parent != _LABS_DIR or not path.is_file():
        raise FileNotFoundError(f"no catalog for {lab_name}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
