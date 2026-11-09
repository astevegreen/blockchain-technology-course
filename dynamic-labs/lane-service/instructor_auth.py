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


# Class gate (instructor_auth_service/class_gate.py). The router checks the
# class pass at server level, but locations with their own auth_request (the
# lane resolve subrequests) skip that check, so /claim and /resolve ask too.
CLASS_VERIFY_URL = os.environ.get(
    "CLASS_VERIFY_URL",
    "http://instructor-auth-service:8080/api/class/verify",
)
_class_cache: dict[tuple[str, str], tuple[float, bool]] = {}


def class_gate_enabled() -> bool:
    return (os.environ.get("CLASS_GATE") or "off").strip().lower() in {"1", "on", "true", "yes"}


def class_pass_ok() -> bool:
    """True when the gate is off, or the request has a class pass or instructor cookie.

    Fails closed: if the auth service does not answer, the student is sent to
    the code page rather than let through.
    """
    if not class_gate_enabled():
        return True
    key = (request.cookies.get("class_pass", ""), request.cookies.get("hlf_instructor", ""))
    if not any(key):
        return False
    now = time.time()
    with _cache_lock:
        hit = _class_cache.get(key)
        if hit and (now - hit[0]) < _CACHE_TTL:
            return hit[1]
    try:
        r = requests.get(
            CLASS_VERIFY_URL,
            cookies={name: value for name, value in zip(("class_pass", "hlf_instructor"), key) if value},
            timeout=VERIFY_TIMEOUT,
        )
        ok = r.status_code == 200
    except requests.RequestException:
        ok = False
    with _cache_lock:
        _class_cache[key] = (now, ok)
        if len(_class_cache) > 256:
            cutoff = now - _CACHE_TTL
            for k in [k for k, (t, _) in _class_cache.items() if t < cutoff]:
                _class_cache.pop(k, None)
    return ok


def require_instructor(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper
