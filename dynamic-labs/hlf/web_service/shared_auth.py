from __future__ import annotations

import sys
from pathlib import Path

from flask import current_app, g, request


BASE_DIR = Path(__file__).resolve().parent
HLF_DIR = BASE_DIR.parent
if str(HLF_DIR) not in sys.path:
    sys.path.insert(0, str(HLF_DIR))

from shared_instructor_auth import (  # noqa: E402
    AuthConfig,
    AuthMode,
    audit_write,
    install_csrf_protection as _install_csrf_protection,
    install_sliding_reissue as _install_sliding_reissue,
    is_recently_authenticated as _is_recently_authenticated,
    log_auth_event,
    require_instructor as _require_instructor,
    verify as _verify,
)

_HLF_STUDENT_CSRF_EXEMPT_PATHS = (
    "/api/hlf/claims/heartbeat",
    "/api/hlf/progress/touch",
)


def init_shared_auth(app) -> AuthConfig:
    config = AuthConfig.from_env()
    app.config["INSTRUCTOR_AUTH"] = config
    _install_sliding_reissue(app)
    _install_csrf_protection(
        app,
        config,
        extra_exempt_paths=_HLF_STUDENT_CSRF_EXEMPT_PATHS,
    )
    return config


def verify_request():
    config = current_app.config["INSTRUCTOR_AUTH"]
    identity = _verify(request, config)
    if identity is not None:
        g.instructor = identity
    return identity


def is_authenticated() -> bool:
    return verify_request() is not None


def require_instructor(fn):
    return _require_instructor()(fn)


def is_recently_authenticated(window_seconds: int | None = None) -> bool:
    config = current_app.config["INSTRUCTOR_AUTH"]
    if window_seconds is None:
        return _is_recently_authenticated(request, config)
    return _is_recently_authenticated(request, config, window_seconds=window_seconds)


__all__ = [
    "AuthConfig",
    "AuthMode",
    "audit_write",
    "init_shared_auth",
    "is_authenticated",
    "is_recently_authenticated",
    "log_auth_event",
    "require_instructor",
    "verify_request",
]
