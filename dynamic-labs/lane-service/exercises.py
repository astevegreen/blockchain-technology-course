"""
Shared exercise-catalog registry.

Each lab calls register_catalog(lab_name, catalog) at import time. The
make_lab_blueprint helper then serves GET /api/<lab>/exercises from this
registry.

Catalog shape (same as the HLF reference implementation — kept loose so
client-side renderers can fall back gracefully on missing sections):

  {
    "intro": {"title": str, "summary": str, "chapters": [{"id","title","summary"}]},
    "exercises": [
      {
        "id": str,                        # matches progress exercise_id
        "chapter": str,                   # references intro.chapters[].id
        "title": str,
        "goal": str,                      # markdown
        "student_steps": [str],
        "expected_observations": [str],
        "meaning": [str],                 # optional
        "surfaces": [{"label","href"}],   # optional
        "transition": str,                # optional
      }, ...
    ],
  }

Placeholders like {{station}} can live in the strings — the server does
not substitute them. The client pager may do per-session substitution.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional, Union

CatalogProvider = Union[Dict[str, Any], Callable[[], Dict[str, Any]]]

_lock = threading.Lock()
_catalogs: Dict[str, CatalogProvider] = {}


def register_catalog(lab_name: str, catalog: CatalogProvider) -> None:
    with _lock:
        _catalogs[lab_name] = catalog


def get_catalog(lab_name: str) -> Optional[Dict[str, Any]]:
    with _lock:
        provider = _catalogs.get(lab_name)
    if provider is None:
        return None
    if callable(provider):
        return provider()
    return provider


def exercise_ids(lab_name: str) -> List[str]:
    cat = get_catalog(lab_name)
    if not cat:
        return []
    return [e.get("id") for e in cat.get("exercises", []) if e.get("id")]
