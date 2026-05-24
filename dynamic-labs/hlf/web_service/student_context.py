"""
Per-student request context for Phase 7.

The nginx router injects X-HLF-Student-Id: s01..sNN on any request that
came in via /labs/hlf/s/<id>/*. We resolve that header against the
generated managed_runtime/schools.json to build a {student_id, msp_id,
peer, school_name, domain, base_prefix} dict for downstream use.

Requests without the header (e.g. the legacy /labs/hlf/ surface) return
a neutral context so the UI and catalog keep working for "preview" mode
outside a specific student lane.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import re

from flask import has_request_context, request

_TOKEN_RE = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}")


def templatize(value: Any, ctx: Dict[str, Any]) -> Any:
    """Recursively substitute {{token}} in all strings inside value.

    Unknown tokens are left intact so broken templates are easy to
    spot in the UI rather than silently dropped.
    """
    if isinstance(value, str):
        def _sub(match: "re.Match[str]") -> str:
            key = match.group(1)
            if key in ctx and ctx[key] is not None:
                return str(ctx[key])
            return match.group(0)
        return _TOKEN_RE.sub(_sub, value)
    if isinstance(value, list):
        return [templatize(v, ctx) for v in value]
    if isinstance(value, dict):
        return {k: templatize(v, ctx) for k, v in value.items()}
    return value

HLF_DIR = Path(__file__).resolve().parent.parent
SCHOOLS_PATH = HLF_DIR / "managed_runtime" / "schools.json"

_cache_lock = threading.Lock()
_cache: Optional[Dict[str, Dict[str, Any]]] = None


def _load_schools() -> Dict[str, Dict[str, Any]]:
    global _cache
    with _cache_lock:
        if _cache is None:
            try:
                _cache = json.loads(SCHOOLS_PATH.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                _cache = {}
        return _cache


def invalidate_cache() -> None:
    global _cache
    with _cache_lock:
        _cache = None


def _valid_sid(sid: str) -> bool:
    if not (len(sid) == 3 and sid.startswith("s") and sid[1:].isdigit()):
        return False
    n = int(sid[1:])
    max_students = int(os.environ.get("HLF_STUDENT_COUNT") or os.environ.get("MAX_STUDENT_CAPACITY") or "20")
    return 1 <= n <= max_students


def _resolve_session_to_station(uuid: str) -> Optional[str]:
    """Deferred import to avoid circular deps at module load."""
    try:
        from claims import get_claim_manager, is_valid_uuid
    except ImportError:
        return None
    if not is_valid_uuid(uuid):
        return None
    return get_claim_manager().resolve(uuid)


def get_student_id() -> Optional[str]:
    """Return the current request's student id (s01..sNN) or None.

    Resolution order:
      1. X-HLF-Session header (set by /labs/hlf/c/<uuid>/* routes) →
         ClaimManager resolves to a station id.
      2. X-HLF-Student-Id header (set by /labs/hlf/s/<id>/* routes).
      3. ?session= or ?student= query params (testing fallback).
    """
    if not has_request_context():
        return None
    session_uuid = request.headers.get("X-HLF-Session") or request.args.get("session")
    if session_uuid:
        station = _resolve_session_to_station(session_uuid.strip().lower())
        if station and _valid_sid(station):
            return station
    sid = request.headers.get("X-HLF-Student-Id") or request.args.get("student")
    if not sid:
        return None
    sid = sid.strip().lower()
    return sid if _valid_sid(sid) else None


def get_student_context() -> Dict[str, Any]:
    """Build the per-student substitution dict for templating.

    Always returns a dict; fields fall back to generic "preview" values
    when no student id is present so the shared /labs/hlf/ surface
    keeps rendering.
    """
    sid = get_student_id()
    schools = _load_schools()
    if sid and _valid_sid(sid):
        entry = schools.get(sid, {})
        n = sid[1:]  # "07"
        # Prefer the nginx-injected X-Forwarded-Prefix so session-scoped
        # surfaces (/labs/hlf/c/<uuid>) retarget hrefs correctly. Fall
        # back to the station-scoped URL for /s/<id> routes.
        fwd_prefix = (
            request.headers.get("X-Forwarded-Prefix")
            if has_request_context() else None
        )
        base_prefix = fwd_prefix or f"/labs/hlf/s/{sid}"
        return {
            "student_id": sid,
            "sid_num": n,
            "msp": entry.get("msp_id", f"Student{n}MSP"),
            "domain": entry.get("domain", f"student{n}.example.com"),
            "peer": f"peer0.student{n}.example.com",
            "school": entry.get("default_school_name", f"Student {n}"),
            "base_prefix": base_prefix,
            "is_student": True,
        }
    # Preview-mode fallback: no session is claimed. Use the first entry
    # from the schools bank so narrative reads concretely ("you are at
    # North Ridge University") rather than leaking bracketed placeholders.
    # Students hitting a claimed URL replace these with their real values.
    preview = {}
    if schools:
        first_sid = sorted(schools.keys())[0]
        entry = schools[first_sid]
        n = first_sid[1:]
        preview = {
            "student_id": first_sid,
            "sid_num": n,
            "msp": entry.get("msp_id", f"Student{n}MSP"),
            "domain": entry.get("domain", f"student{n}.example.com"),
            "peer": f"peer0.student{n}.example.com",
            "school": entry.get("default_school_name", "Sample University"),
        }
    return {
        "student_id": preview.get("student_id", "s01"),
        "sid_num": preview.get("sid_num", "01"),
        "msp": preview.get("msp", "Student01MSP"),
        "domain": preview.get("domain", "student01.example.com"),
        "peer": preview.get("peer", "peer0.student01.example.com"),
        "school": preview.get("school", "Sample University"),
        "base_prefix": "/labs/hlf",
        "is_student": False,
    }
