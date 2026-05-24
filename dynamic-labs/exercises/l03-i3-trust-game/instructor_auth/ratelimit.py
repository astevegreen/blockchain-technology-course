"""Rate limiting for instructor login endpoints.

In-process per-IP sliding-window counter. 5 attempts/min (burst) and
5 attempts/15-min (lockout) run together, so a spammer who empties
the burst is still locked out for the full 15-minute window.

Kept as a small hand-rolled counter rather than Flask-Limiter because
Flask-Limiter's per-view limit registration keys on qualname, which
has a tendency to silently misfire when view functions are wrapped
by other decorators. Classroom traffic is tiny and storage is in
process memory — Redis/Flask-Limiter would be overkill.
"""

from __future__ import annotations

import threading
import time
from typing import Iterable

from flask import jsonify, request

from .audit import audit_write
from .auth import log_auth_event

# (window_seconds, max_attempts). Both apply — exhausting either locks
# the IP until entries age out.
DEFAULT_LIMITS = ((60, 5), (15 * 60, 5))


def _client_ip() -> str:
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "-"


def install_login_rate_limit(
    app,
    *,
    login_endpoints: Iterable[str],
    login_paths: Iterable[str] = ("/instructor/login", "/api/instructor/login"),
    limits=DEFAULT_LIMITS,
) -> None:
    """Install a before_request hook that rate-limits login POSTs.

    ``login_endpoints`` is accepted for API compatibility but the hook
    matches on ``request.path`` instead — a path set is cheaper to
    check and survives blueprint renames.
    """
    if app.config.get("_INSTRUCTOR_LOGIN_RL_INSTALLED"):
        return
    app.config["_INSTRUCTOR_LOGIN_RL_INSTALLED"] = True

    paths = frozenset(login_paths)
    lock = threading.Lock()
    attempts: dict[str, list[float]] = {}
    longest = max(w for w, _ in limits)

    def _limited(ip: str) -> bool:
        now = time.time()
        with lock:
            hits = [t for t in attempts.get(ip, []) if now - t <= longest]
            for window, cap in limits:
                if sum(1 for t in hits if now - t <= window) >= cap:
                    attempts[ip] = hits
                    return True
            hits.append(now)
            attempts[ip] = hits
            return False

    @app.before_request
    def _enforce():
        if request.path not in paths or request.method != "POST":
            return None
        ip = _client_ip()
        if _limited(ip):
            try:
                log_auth_event("login", outcome="rate_limited",
                               reason="too_many_attempts")
                audit_write("login.rate_limited", outcome="fail",
                            extra={"ip": ip, "path": request.path})
            except Exception:
                pass
            return jsonify({
                "success": False,
                "message": "too many attempts, try again later",
            }), 429
        return None
