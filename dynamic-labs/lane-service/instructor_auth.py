"""
Instructor authentication — delegates to the centralized auth service.
"""

from __future__ import annotations

import os
import threading
import time
from functools import wraps

import requests
from flask import jsonify, request

VERIFY_URL = os.environ.get(
    "INSTRUCTOR_AUTH_URL",
    "http://instructor-auth-service:8080/api/instructor/verify",
)
VERIFY_TIMEOUT = 5

# Tiny TTL cache so per-asset auth fan-out does not translate into N
# round-trips to the centralized auth service per page load.
_CACHE_TTL = 5.0
_cache_lock = threading.Lock()
_cache: dict[str, tuple[float, bool]] = {}


def _verify_cookie(cookie: str) -> bool:
    if not cookie:
        return False
    now = time.time()
    with _cache_lock:
        hit = _cache.get(cookie)
        if hit and (now - hit[0]) < _CACHE_TTL:
            return hit[1]
    try:
        r = requests.get(
            VERIFY_URL,
            cookies={"hlf_instructor": cookie},
            timeout=VERIFY_TIMEOUT,
        )
        ok = r.status_code == 200
    except requests.RequestException:
        ok = False
    with _cache_lock:
        _cache[cookie] = (now, ok)
        # Hard cap so a flood of bogus cookies can't pin memory.
        if len(_cache) > 256:
            cutoff = now - _CACHE_TTL
            for k in [k for k, (t, _) in _cache.items() if t < cutoff]:
                _cache.pop(k, None)
    return ok


def is_authenticated() -> bool:
    return _verify_cookie(request.cookies.get("hlf_instructor", ""))


def require_instructor(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper
