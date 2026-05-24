"""Phase 7.9 — revocation list + active-session ledger for the HLF runner.

Kept deliberately small: two JSON files on the runner's runtime volume,
guarded by a module-level lock, with a 10s in-memory cache on the
revocation check so the per-request hot path stays sub-ms. No SQLite
dependency, matching the rest of web_service/ (see progress_store.py).

Files live under `web_service/../runtime/auth/`:
  - revoked.json       → {jti: revoked_at_unix}
  - active.json        → {jti: {sub, iat, last_seen, ip}}

A jti stays in the revoked list until it ages past the hard ceiling
(24h from `iat`); the `_gc_revoked` helper trims on read.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Tuple

HARD_CEILING_SECONDS = 24 * 60 * 60
_CACHE_TTL_SECONDS = 10

_DIR = Path(__file__).resolve().parent.parent / "runtime" / "auth"
_REVOKED = _DIR / "revoked.json"
_ACTIVE = _DIR / "active.json"
_lock = threading.Lock()

_cache: Dict[str, Tuple[float, set]] = {"revoked": (0.0, set())}


def _ensure_dir() -> None:
    _DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data: dict) -> None:
    _ensure_dir()
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"))
    os.replace(tmp, path)


def _load_revoked_raw() -> Dict[str, float]:
    raw = _load_json(_REVOKED)
    return {k: float(v) for k, v in raw.items() if isinstance(k, str)}


def _gc_revoked(entries: Dict[str, float]) -> Dict[str, float]:
    """Drop entries older than the hard ceiling. They're naturally unusable."""
    cutoff = time.time() - HARD_CEILING_SECONDS
    return {k: v for k, v in entries.items() if v >= cutoff}


def is_revoked(jti: str) -> bool:
    """Hot-path check. Uses a 10s in-memory cache keyed on the revoked
    set to avoid a file read on every instructor request."""
    if not jti:
        return False
    now = time.time()
    cached_at, cached = _cache["revoked"]
    if (now - cached_at) > _CACHE_TTL_SECONDS:
        with _lock:
            cached_at2, cached2 = _cache["revoked"]
            if (now - cached_at2) > _CACHE_TTL_SECONDS:
                entries = _gc_revoked(_load_revoked_raw())
                _cache["revoked"] = (now, set(entries.keys()))
                cached = set(entries.keys())
            else:
                cached = cached2
    return jti in cached


def revoke(jti: str) -> None:
    if not jti:
        return
    with _lock:
        entries = _gc_revoked(_load_revoked_raw())
        entries[jti] = time.time()
        _save_json(_REVOKED, entries)
        _cache["revoked"] = (0.0, set())  # force refresh on next check


def record_issue(jti: str, sub: str, iat: int, ip: str) -> None:
    if not jti:
        return
    with _lock:
        active = _load_json(_ACTIVE)
        active[jti] = {"sub": sub, "iat": iat, "last_seen": int(time.time()), "ip": ip}
        _save_json(_ACTIVE, active)


def record_seen(jti: str, ip: str) -> None:
    if not jti:
        return
    with _lock:
        active = _load_json(_ACTIVE)
        entry = active.get(jti)
        if entry is None:
            return
        entry["last_seen"] = int(time.time())
        entry["ip"] = ip
        _save_json(_ACTIVE, active)


def list_active() -> list:
    """Return active sessions newest-first, pruning expired and revoked."""
    revoked = set(_gc_revoked(_load_revoked_raw()).keys())
    active = _load_json(_ACTIVE)
    cutoff = time.time() - HARD_CEILING_SECONDS
    out = []
    keep = {}
    for jti, meta in active.items():
        iat = int(meta.get("iat", 0) or 0)
        if iat < cutoff or jti in revoked:
            continue
        keep[jti] = meta
        out.append({"jti": jti, **meta})
    if len(keep) != len(active):
        with _lock:
            _save_json(_ACTIVE, keep)
    out.sort(key=lambda r: r.get("last_seen", 0), reverse=True)
    return out


def forget(jti: str) -> None:
    """Remove a session from the active ledger (e.g., on logout)."""
    if not jti:
        return
    with _lock:
        active = _load_json(_ACTIVE)
        if jti in active:
            active.pop(jti, None)
            _save_json(_ACTIVE, active)
