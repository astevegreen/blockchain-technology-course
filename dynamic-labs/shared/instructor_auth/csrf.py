"""CSRF protection for instructor mutation endpoints.

Token model: itsdangerous-signed payload ``{jti, nonce}`` with a
CSRF-specific salt. Token issuance (``POST /api/instructor/csrf``) is
gated behind the instructor cookie — you must already be authenticated
to mint a CSRF token. Tokens bind to the instructor session's ``jti``,
so a revoked/logged-out session's tokens stop working the moment the
cookie is rejected.

Enforcement is global via an ``before_request`` hook installed by
``install_csrf_protection(app, config)``. For any authenticated
mutating request (POST/PUT/PATCH/DELETE) not on the exempt list
(login, logout, the CSRF mint endpoint itself), a valid
``X-CSRFToken`` header is required. Missing/invalid → 403.

CSRF tokens carry their own short TTL (``CSRF_TOKEN_MAX_AGE``)
independent of the cookie — a stale page can fetch a fresh token
without re-logging-in.
"""

from __future__ import annotations

import secrets
import time
from typing import Iterable, Optional

from flask import Blueprint, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .audit import audit_write
from .auth import AuthConfig, log_auth_event, require_instructor, verify

CSRF_SALT = "hlf-instructor-csrf-v1"
CSRF_HEADER = "X-CSRFToken"
CSRF_TOKEN_MAX_AGE = 60 * 60  # 1h — matches cookie active window.

# Paths that never require a CSRF token even under an authenticated
# cookie. Login has no prior session; logout should succeed even if
# the page's token is stale; CSRF mint is the bootstrap itself.
DEFAULT_EXEMPT_PATHS = frozenset({
    "/api/instructor/login",
    "/api/instructor/logout",
    "/api/instructor/csrf",
    "/instructor/login",
    "/instructor/logout",
})

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _serializer(config: AuthConfig) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(config.secret, salt=CSRF_SALT)


def mint_csrf_token(config: AuthConfig, jti: str) -> str:
    """Sign a CSRF token bound to an instructor session's ``jti``."""
    payload = {"jti": jti or "", "nonce": secrets.token_urlsafe(16)}
    return _serializer(config).dumps(payload)


def verify_csrf_token(config: AuthConfig, token: str, expected_jti: str) -> bool:
    if not token:
        return False
    try:
        data = _serializer(config).loads(token, max_age=CSRF_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return False
    if not isinstance(data, dict):
        return False
    # jti binding: a token minted for session A cannot be replayed
    # against session B, even if both sessions share the same secret.
    return str(data.get("jti") or "") == (expected_jti or "")


def install_csrf_protection(
    app,
    config: AuthConfig,
    *,
    extra_exempt_paths: Optional[Iterable[str]] = None,
) -> None:
    """Register before_request hook enforcing CSRF on authed mutations.

    Idempotent. Should be called after ``AuthConfig`` is placed in
    ``app.config['INSTRUCTOR_AUTH']``.
    """
    if app.config.get("_INSTRUCTOR_CSRF_INSTALLED"):
        return
    app.config["_INSTRUCTOR_CSRF_INSTALLED"] = True

    exempt = set(DEFAULT_EXEMPT_PATHS)
    if extra_exempt_paths:
        exempt.update(extra_exempt_paths)
    app.config["_INSTRUCTOR_CSRF_EXEMPT"] = exempt

    @app.before_request
    def _enforce_csrf():
        if request.method not in MUTATING_METHODS:
            return None
        if request.path in exempt:
            return None
        # Inspect the cookie directly: `require_instructor` runs at
        # route-call time, so `g.instructor` isn't populated yet in
        # before_request. CSRF only matters when a cookie is present —
        # a forged request from an attacker's page rides along the
        # victim's cookie, so that's the branch to gate.
        identity = verify(request, config)
        if identity is None:
            return None
        submitted = request.headers.get(CSRF_HEADER, "")
        if verify_csrf_token(config, submitted, identity.jti):
            return None
        log_auth_event(
            "csrf",
            outcome="fail",
            reason="missing_or_invalid_token",
            sub=identity.sub,
            jti=identity.jti,
        )
        try:
            audit_write("csrf.reject", outcome="fail",
                        extra={"reason": "missing_or_invalid_token"})
        except Exception:
            pass
        return jsonify({"success": False, "message": "csrf token required"}), 403


_CSRF_SHIM_JS = """\
(function () {
  const MUTATING = new Set(['POST','PUT','PATCH','DELETE']);
  const EXEMPT = new Set([
    '/api/instructor/login','/api/instructor/logout','/api/instructor/csrf',
  ]);
  let tokenPromise = null;
  function fetchToken() {
    if (tokenPromise) return tokenPromise;
    tokenPromise = window.__origFetch('/api/instructor/csrf',
      { method:'POST', credentials:'same-origin' })
      .then(r => r.ok ? r.json() : Promise.reject(new Error('csrf '+r.status)))
      .then(j => j.token)
      .catch(e => { tokenPromise = null; throw e; });
    return tokenPromise;
  }
  window.__origFetch = window.fetch.bind(window);
  window.fetch = async function(input, init) {
    init = init || {};
    const method = (init.method ||
      (typeof input === 'object' ? input.method : 'GET') || 'GET').toUpperCase();
    if (!MUTATING.has(method)) return window.__origFetch(input, init);
    let url;
    try { url = new URL(typeof input === 'string' ? input : input.url,
                        window.location.origin); }
    catch (_) { return window.__origFetch(input, init); }
    if (url.origin !== window.location.origin) return window.__origFetch(input, init);
    if (EXEMPT.has(url.pathname)) return window.__origFetch(input, init);
    try {
      const token = await fetchToken();
      const headers = new Headers(init.headers || {});
      if (!headers.has('X-CSRFToken')) headers.set('X-CSRFToken', token);
      init = { ...init, headers, credentials: init.credentials || 'same-origin' };
    } catch (_) {}
    return window.__origFetch(input, init);
  };
  fetchToken().catch(() => {});
})();
"""


def csrf_blueprint(config: AuthConfig) -> Blueprint:
    """Blueprint exposing ``POST /api/instructor/csrf`` + shim JS.

    ``GET /instructor/csrf.js`` serves a public fetch-wrapper shim
    (no secrets) that pages can include to auto-attach the CSRF
    header on mutating requests.
    """
    bp = Blueprint("instructor_csrf", __name__)

    @bp.route("/api/instructor/csrf", methods=["POST"])
    @require_instructor(config)
    def mint():
        identity = g.instructor
        token = mint_csrf_token(config, identity.jti)
        return jsonify({
            "token": token,
            "header": CSRF_HEADER,
            "expires_in": CSRF_TOKEN_MAX_AGE,
            "issued_at": int(time.time()),
        })

    @bp.route("/instructor/csrf.js", methods=["GET"])
    def shim():
        from flask import Response
        return Response(_CSRF_SHIM_JS, mimetype="application/javascript")

    return bp
