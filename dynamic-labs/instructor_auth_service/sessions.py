from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Tuple


HARD_CEILING_SECONDS = 24 * 60 * 60
_CACHE_TTL_SECONDS = 10
_SEEN_WRITE_INTERVAL_SECONDS = int(os.environ.get("INSTRUCTOR_AUTH_SEEN_WRITE_INTERVAL", "30"))

_DIR = Path(
    os.environ.get(
        "INSTRUCTOR_AUTH_SESSION_DIR",
        str(Path(__file__).resolve().parent / "runtime" / "auth"),
    )
)
_REVOKED = _DIR / "revoked.json"
_ACTIVE = _DIR / "active.json"
_lock = threading.Lock()
_cache: Dict[str, Tuple[float, set]] = {"revoked": (0.0, set())}
_seen_cache: Dict[str, Tuple[int, str]] = {}


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
    fd, tmp_name = tempfile.mkstemp(
        prefix=f"{path.stem}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp = Path(tmp_name)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"))
    try:
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _load_revoked_raw() -> Dict[str, float]:
    raw = _load_json(_REVOKED)
    return {k: float(v) for k, v in raw.items() if isinstance(k, str)}


def _gc_revoked(entries: Dict[str, float]) -> Dict[str, float]:
    cutoff = time.time() - HARD_CEILING_SECONDS
    return {k: v for k, v in entries.items() if v >= cutoff}


def is_revoked(jti: str) -> bool:
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
        _cache["revoked"] = (0.0, set())


def record_issue(jti: str, sub: str, iat: int, ip: str) -> None:
    if not jti:
        return
    now = int(time.time())
    with _lock:
        active = _load_json(_ACTIVE)
        active[jti] = {"sub": sub, "iat": iat, "last_seen": now, "ip": ip}
        _save_json(_ACTIVE, active)
        _seen_cache[jti] = (now, ip)


def record_seen(jti: str, ip: str) -> None:
    if not jti:
        return
    now = int(time.time())
    with _lock:
        cached = _seen_cache.get(jti)
        if cached is not None:
            cached_at, cached_ip = cached
            if cached_ip == ip and (now - cached_at) < _SEEN_WRITE_INTERVAL_SECONDS:
                return
        active = _load_json(_ACTIVE)
        entry = active.get(jti)
        if entry is None:
            _seen_cache.pop(jti, None)
            return
        last_seen = int(entry.get("last_seen", 0) or 0)
        if str(entry.get("ip") or "") == ip and (now - last_seen) < _SEEN_WRITE_INTERVAL_SECONDS:
            _seen_cache[jti] = (now, ip)
            return
        entry["last_seen"] = now
        entry["ip"] = ip
        _save_json(_ACTIVE, active)
        _seen_cache[jti] = (now, ip)


def list_active() -> list:
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
    if not jti:
        return
    with _lock:
        _seen_cache.pop(jti, None)
        active = _load_json(_ACTIVE)
        if jti in active:
            active.pop(jti, None)
            _save_json(_ACTIVE, active)
