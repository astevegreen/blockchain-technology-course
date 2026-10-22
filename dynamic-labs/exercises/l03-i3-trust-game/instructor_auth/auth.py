"""Core cookie issuance, verification, and decorator."""

from __future__ import annotations

import enum
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional

from flask import Response, current_app, g, jsonify, make_response, redirect, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

COOKIE_NAME = "hlf_instructor"
COOKIE_SALT = "hlf-instructor-v1"
COOKIE_MAX_AGE = 60 * 60  # Phase 7.9: 1h active window (was 12h).
HARD_CEILING_SECONDS = 24 * 60 * 60  # Phase 7.9: 24h absolute from `iat`.
SLIDING_REISSUE_THRESHOLD = COOKIE_MAX_AGE // 2  # re-sign past the halfway mark
RECENT_AUTH_WINDOW_SECONDS = 5 * 60
PAYLOAD_VERSION = 1  # Phase 7.8 schema; verify() rejects unknown versions.
SHARED_LOGIN_URL = "/instructor/"
SHARED_LOGOUT_URL = "/instructor/logout"
STANDALONE_LOGIN_URL = "/instructor/login"
DEV_FALLBACK_SECRET = "hlf_lab_secret"


class AuthMode(str, enum.Enum):
    SHARED = "shared"
    STANDALONE = "standalone"
    DISABLED = "disabled"


@dataclass(frozen=True)
class Identity:
    role: str
    issued_at: float
    sub: str = ""
    jti: str = ""
    recent_auth_at: float = 0.0


@dataclass(frozen=True)
class AuthConfig:
    """Runtime auth config derived from environment.

    `secret` signs and verifies cookies. In shared mode this must match
    the shared instructor-auth signing secret. In standalone mode this
    is the lab's own `INSTRUCTOR_AUTH_SECRET`.
    """
    mode: AuthMode
    secret: str
    standalone_password: Optional[str] = None
    max_age: int = COOKIE_MAX_AGE

    @staticmethod
    def from_env() -> "AuthConfig":
        mode = AuthMode(os.environ.get("INSTRUCTOR_AUTH_MODE", "shared").strip().lower())
        prod = _is_production()

        if mode is AuthMode.DISABLED:
            if prod:
                raise RuntimeError(
                    "INSTRUCTOR_AUTH_MODE=disabled refuses to run outside "
                    "FLASK_ENV=development. Set a real mode before deploying."
                )
            return AuthConfig(mode=mode, secret="")

        if mode is AuthMode.STANDALONE:
            secret = os.environ.get("INSTRUCTOR_AUTH_SECRET", "").strip()
            if not secret:
                if prod:
                    raise RuntimeError(
                        "INSTRUCTOR_AUTH_MODE=standalone requires "
                        "INSTRUCTOR_AUTH_SECRET when FLASK_ENV is not development."
                    )
                secret = DEV_FALLBACK_SECRET
            password = os.environ.get("INSTRUCTOR_PASSWORD", "").strip() or None
            if not password and prod:
                raise RuntimeError(
                    "INSTRUCTOR_AUTH_MODE=standalone requires INSTRUCTOR_PASSWORD "
                    "when FLASK_ENV is not development."
                )
            return AuthConfig(mode=mode, secret=secret, standalone_password=password or "admin")

        # SHARED (default)
        secret = (
            os.environ.get("INSTRUCTOR_AUTH_COOKIE_SECRET")
            or os.environ.get("HLF_INSTRUCTOR_COOKIE_SECRET")
            or os.environ.get("HLF_WEB_SECRET_KEY")
            or ""
        ).strip()
        if not secret:
            if prod:
                raise RuntimeError(
                    "INSTRUCTOR_AUTH_MODE=shared requires INSTRUCTOR_AUTH_COOKIE_SECRET, "
                    "HLF_INSTRUCTOR_COOKIE_SECRET, or HLF_WEB_SECRET_KEY when "
                    "FLASK_ENV is not development."
                )
            secret = DEV_FALLBACK_SECRET
        return AuthConfig(mode=mode, secret=secret)

    def login_url(self) -> str:
        if self.mode is AuthMode.STANDALONE:
            return STANDALONE_LOGIN_URL
        return SHARED_LOGIN_URL

    def logout_url(self) -> str:
        if self.mode is AuthMode.STANDALONE:
            return STANDALONE_LOGIN_URL + "?msg=logged_out"
        return SHARED_LOGOUT_URL


def _is_production() -> bool:
    # Fail closed: only an explicit development value turns the dev fallbacks on,
    # so a deployment that forgets FLASK_ENV is treated as production.
    env = os.environ.get("FLASK_ENV", "").strip().lower()
    return env not in ("development", "dev", "local")


def _serializer(config: AuthConfig) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(config.secret, salt=COOKIE_SALT)


def build_payload(*, sub: str = "", recent_auth_at: Optional[float] = None) -> dict:
    """Construct a v1 cookie payload. Callers outside `issue()` use this
    so the shared cookie schema stays in one place."""
    now = time.time()
    return {
        "v": PAYLOAD_VERSION,
        "role": "instructor",
        "sub": sub or "",
        "jti": uuid.uuid4().hex,
        "iat": int(now),
        "recent_auth_at": int(recent_auth_at if recent_auth_at is not None else now),
    }


def verify(req, config: AuthConfig) -> Optional[Identity]:
    """Return an Identity for a valid cookie, else None.

    `disabled` mode short-circuits to a synthetic identity so callers
    don't have to branch on mode. Payloads with an unknown ``v`` field
    (including the pre-7.8 ``{role}``-only shape) are rejected so clients
    are forced to re-login after a schema bump.
    """
    if config.mode is AuthMode.DISABLED:
        now = time.time()
        return Identity(role="instructor", issued_at=now, sub="dev", jti="dev", recent_auth_at=now)
    token = req.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data, ts = _serializer(config).loads(
            token, max_age=config.max_age, return_timestamp=True
        )
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("v") != PAYLOAD_VERSION or data.get("role") != "instructor":
        return None
    issued_at = float(data.get("iat") or ts.timestamp())
    now = time.time()
    # Hard ceiling: an original cookie older than 24h is rejected even
    # if itsdangerous-signed sliding reissues have kept ts fresh.
    if (now - issued_at) > HARD_CEILING_SECONDS:
        return None
    identity = Identity(
        role="instructor",
        issued_at=issued_at,
        sub=str(data.get("sub") or ""),
        jti=str(data.get("jti") or ""),
        recent_auth_at=float(data.get("recent_auth_at") or issued_at),
    )
    # Flag for the after_request hook to re-mint when we're past the
    # halfway mark of the active window. We stash the raw signing-age on
    # `g` so the hook knows it's not a fresh cookie.
    try:
        signed_age = now - ts.timestamp()
        if signed_age > SLIDING_REISSUE_THRESHOLD:
            g._instructor_should_reissue = True
    except RuntimeError:
        pass
    return identity


def _reissue_token(config: AuthConfig, identity: Identity) -> str:
    """Re-sign a cookie, preserving `iat`/`sub`/`jti`. Used by sliding
    reissue so the hard 24h ceiling survives activity bumps."""
    now = int(time.time())
    payload = {
        "v": PAYLOAD_VERSION,
        "role": "instructor",
        "sub": identity.sub,
        "jti": identity.jti,
        "iat": int(identity.issued_at),
        "recent_auth_at": now,
    }
    return _serializer(config).dumps(payload)


def install_sliding_reissue(app) -> None:
    """Register an after_request hook that re-mints the cookie on
    activity past the halfway mark of the active window. Idempotent."""
    if app.config.get("_INSTRUCTOR_AUTH_SLIDING_INSTALLED"):
        return
    app.config["_INSTRUCTOR_AUTH_SLIDING_INSTALLED"] = True

    @app.after_request
    def _reissue(response):
        if not getattr(g, "_instructor_should_reissue", False):
            return response
        identity = getattr(g, "instructor", None)
        cfg = app.config.get("INSTRUCTOR_AUTH")
        if identity is None or cfg is None:
            return response
        token = _reissue_token(cfg, identity)
        response.set_cookie(
            COOKIE_NAME,
            token,
            max_age=cfg.max_age,
            httponly=True,
            samesite="Lax",
            path="/",
        )
        return response


def is_recently_authenticated(req, config: AuthConfig, window_seconds: int = RECENT_AUTH_WINDOW_SECONDS) -> bool:
    identity = verify(req, config)
    if identity is None:
        return False
    return (time.time() - identity.issued_at) <= window_seconds


def issue(response: Response, config: AuthConfig, *, sub: str = "") -> Response:
    """Set the signed cookie on `response`. Use only in standalone mode.

    In shared mode, cookies are minted exclusively by the centralized
    instructor auth service; lab apps never call `issue()`.
    """
    if config.mode is not AuthMode.STANDALONE:
        raise RuntimeError(
            "issue() is only valid in standalone mode. Shared-mode cookies "
            "are minted by the centralized instructor auth service."
        )
    token = _serializer(config).dumps(build_payload(sub=sub))
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=config.max_age,
        httponly=True,
        samesite="Lax",
        path="/",
    )
    return response


def _resolve_config() -> AuthConfig:
    cfg = current_app.config.get("INSTRUCTOR_AUTH")
    if cfg is None:
        raise RuntimeError(
            "app.config['INSTRUCTOR_AUTH'] is unset. Call AuthConfig.from_env() "
            "and assign it before registering routes."
        )
    return cfg


def require_instructor(config: Optional[AuthConfig] = None) -> Callable:
    """Flask decorator. `config` may be omitted to look up from app.config."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            cfg = config or _resolve_config()
            identity = verify(request, cfg)
            if identity is None:
                log_auth_event("verify", outcome="fail", reason="no_or_bad_cookie")
                accept = request.headers.get("Accept", "")
                if "text/html" in accept or request.method == "GET":
                    return redirect(cfg.login_url())
                return jsonify({"success": False, "message": "unauthorized"}), 401
            g.instructor = identity
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def log_auth_event(event: str, *, outcome: str = "ok", reason: str = "", sub: str = "", jti: str = "") -> None:
    """Emit one JSON line to stderr describing an auth-related event."""
    try:
        ip = request.headers.get(
            "X-Forwarded-For", request.remote_addr or "-"
        ).split(",")[0].strip()
        ua = request.headers.get("User-Agent", "")[:200]
        path = request.path
    except RuntimeError:
        ip, ua, path = "-", "", "-"
    line = json.dumps({
        "ts": int(time.time()),
        "event": event,
        "outcome": outcome,
        "reason": reason,
        "sub": sub,
        "jti": jti,
        "ip": ip,
        "path": path,
        "ua": ua,
    }, separators=(",", ":"))
    sys.stderr.write(f"[instructor-auth] {line}\n")
    sys.stderr.flush()
