"""File-backed audit log for instructor write actions.

Phase 7.8: one JSON line per instructor mutation, keyed by `jti` + `sub`
so incident review can attribute every write to a specific session and
user. Rotated nightly; retained 14 days by default.

Path and retention come from env (`INSTRUCTOR_AUDIT_LOG_PATH`,
`INSTRUCTOR_AUDIT_LOG_RETENTION_DAYS`). Silent fallback to stderr if
the configured path can't be opened — audit should never take down the
request path.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

from flask import g, request

from .auth import Identity

_DEFAULT_PATH = "/var/log/instructor-audit.log"
_LOGGER_NAME = "instructor_audit"
_configured = False


def _configure(path: str, retention_days: int) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    # Remove any prior handlers (idempotent reconfig in tests).
    for h in list(logger.handlers):
        logger.removeHandler(h)
    try:
        handler: logging.Handler = TimedRotatingFileHandler(
            path, when="midnight", backupCount=retention_days, encoding="utf-8"
        )
    except (OSError, PermissionError) as exc:
        sys.stderr.write(
            f"[instructor-audit] WARNING: cannot open {path} ({exc}); "
            "falling back to stderr.\n"
        )
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def _ensure_configured() -> logging.Logger:
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        return logger
    path = os.environ.get("INSTRUCTOR_AUDIT_LOG_PATH", _DEFAULT_PATH)
    try:
        retention = int(os.environ.get("INSTRUCTOR_AUDIT_LOG_RETENTION_DAYS", "14"))
    except ValueError:
        retention = 14
    logger = _configure(path, retention)
    _configured = True
    return logger


def audit_write(action: str, *, outcome: str = "ok", extra: Optional[dict] = None) -> None:
    """Record one instructor-write event. Reads identity from `g.instructor`
    (set by `require_instructor`) and request metadata from Flask globals.
    Callers pass a short action verb — e.g. `"factory_reset"`,
    `"quiz.edit"`, `"student.access_code.update"`.
    """
    logger = _ensure_configured()
    identity: Optional[Identity] = getattr(g, "instructor", None) if _has_request_context() else None
    try:
        ip = request.headers.get(
            "X-Forwarded-For", request.remote_addr or "-"
        ).split(",")[0].strip()
        method = request.method
        path = request.path
    except RuntimeError:
        ip, method, path = "-", "-", "-"
    record = {
        "ts": int(time.time()),
        "action": action,
        "outcome": outcome,
        "sub": identity.sub if identity else "",
        "jti": identity.jti if identity else "",
        "ip": ip,
        "method": method,
        "path": path,
    }
    if extra:
        record.update(extra)
    logger.info(json.dumps(record, separators=(",", ":")))


def _has_request_context() -> bool:
    try:
        request.path  # noqa: B018
        return True
    except RuntimeError:
        return False
