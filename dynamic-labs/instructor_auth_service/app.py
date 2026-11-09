from __future__ import annotations

import os
import sys
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, Response, g, jsonify, make_response, redirect, request, send_from_directory
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.middleware.proxy_fix import ProxyFix


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))

from instructor_auth import (  # noqa: E402
    AuthConfig,
    AuthMode,
    audit_write,
    csrf_blueprint,
    install_csrf_protection,
    install_login_rate_limit,
    install_sliding_reissue,
    log_auth_event,
    verify,
)
from instructor_auth.auth import COOKIE_NAME, build_payload, _serializer  # noqa: E402

from . import class_gate, sessions  # noqa: E402


UI_DIR = ROOT / "hlf" / "web_ui"
CLASS_PAGE_DIR = Path(__file__).resolve().parent
DEFAULT_USER = "admin"
RETURN_TO_COOKIE_NAME = "hlf_instructor_return_to"
RETURN_TO_COOKIE_SALT = "hlf-instructor-return-to-v1"
RETURN_TO_COOKIE_MAX_AGE = 5 * 60
RETURN_TO_MAX_LENGTH = 2048


def _configured_user() -> str:
    return (
        os.environ.get("INSTRUCTOR_AUTH_USER")
        or os.environ.get("HLF_INSTRUCTOR_USER")
        or DEFAULT_USER
    )


def _configured_key() -> str:
    return (
        os.environ.get("INSTRUCTOR_AUTH_KEY")
        or os.environ.get("HLF_INSTRUCTOR_KEY")
        or ""
    )


def _using_default_credentials() -> bool:
    # There is no built-in password any more; create_app() refuses to start without one.
    return False


def _auth_bypassed(config: AuthConfig) -> bool:
    return config.mode is AuthMode.DISABLED


def _client_ip() -> str:
    # ProxyFix(x_for=1) has already set remote_addr to the address the router saw.
    # The first X-Forwarded-For entry is whatever the client chose to send.
    return request.remote_addr or "-"


def _ct_equals(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= ord(x) ^ ord(y)
    return diff == 0


def _check_credentials(user: str, key: str) -> bool:
    if not _configured_key():
        return False
    return _ct_equals(user or "", _configured_user()) and _ct_equals(key or "", _configured_key())


def _return_to_serializer(config: AuthConfig) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(config.secret, salt=RETURN_TO_COOKIE_SALT)


def _safe_return_to(raw: str, *, method: str = "GET") -> str | None:
    target = (raw or "").strip()
    if method.upper() not in {"GET", "HEAD"}:
        return None
    if not target or len(target) > RETURN_TO_MAX_LENGTH:
        return None
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in target):
        return None
    if not target.startswith("/") or target.startswith("//"):
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    path = parsed.path or "/"
    if path in {"/instructor", "/instructor/"}:
        return None
    if path.startswith("/api/"):
        return None
    if path.startswith("/instructor/logout") or path.startswith("/api/instructor/"):
        return None
    return target


def _clear_return_to_cookie(response) -> None:
    response.delete_cookie(RETURN_TO_COOKIE_NAME, path="/")


def _set_return_to_cookie(response, config: AuthConfig, target: str) -> None:
    token = _return_to_serializer(config).dumps({"path": target})
    response.set_cookie(
        RETURN_TO_COOKIE_NAME,
        token,
        max_age=RETURN_TO_COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
        path="/",
    )


def _consume_return_to(config: AuthConfig) -> str | None:
    token = request.cookies.get(RETURN_TO_COOKIE_NAME)
    if not token:
        return None
    try:
        data = _return_to_serializer(config).loads(
            token, max_age=RETURN_TO_COOKIE_MAX_AGE
        )
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict):
        return None
    return _safe_return_to(str(data.get("path") or ""), method="GET")


def _mint_cookie(config: AuthConfig, *, sub: str) -> tuple[str, dict]:
    payload = build_payload(sub=(sub or "instructor").strip()[:64])
    token = _serializer(config).dumps(payload)
    return token, payload


def _issue_cookie(response, config: AuthConfig, *, sub: str) -> dict:
    token, payload = _mint_cookie(config, sub=sub)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=config.max_age,
        httponly=True,
        samesite="Lax",
        path="/",
    )
    return payload


def _authenticated_identity(config: AuthConfig):
    identity = verify(request, config)
    if identity is None:
        return None
    g.instructor = identity
    sessions.record_seen(identity.jti, _client_ip())
    return identity


def _require_api_instructor(config: AuthConfig):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            identity = _authenticated_identity(config)
            if identity is None:
                return jsonify({"success": False, "message": "unauthorized"}), 401
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _serve_gated_page(config: AuthConfig, filename: str):
    if _authenticated_identity(config) is None:
        return redirect("/instructor/", code=302)
    return send_from_directory(UI_DIR, filename)


def create_app() -> Flask:
    app = Flask(__name__)
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY is not set. Run ./lab-manager.sh deploy, which generates it "
            "(as INSTRUCTOR_AUTH_SERVICE_SECRET_KEY) into .runtime/runtime-secrets.env, "
            "or set SECRET_KEY yourself."
        )
    app.config["SECRET_KEY"] = secret_key
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1, x_prefix=1)  # type: ignore[assignment]

    config = AuthConfig.from_env()
    if config.mode is not AuthMode.DISABLED and not _configured_key():
        raise RuntimeError(
            "INSTRUCTOR_AUTH_KEY is not set. Run ./lab-manager.sh deploy, which "
            "generates it into .runtime/runtime-secrets.env, or set it yourself."
        )
    app.config["INSTRUCTOR_AUTH"] = config

    app.register_blueprint(csrf_blueprint(config))
    install_sliding_reissue(app)
    # Entering the class code needs no CSRF token, even from a browser that also
    # holds an instructor cookie: a forged entry only hands that browser a pass.
    install_csrf_protection(app, config, extra_exempt_paths=["/api/class/enter"])
    install_login_rate_limit(app, login_endpoints=["instructor_auth_service.login"])
    class_failures = class_gate.FailureLimiter()

    def _has_class_pass() -> bool:
        code, _source = class_gate.current_code()
        return class_gate.pass_is_valid(
            secret_key, request.cookies.get(class_gate.PASS_COOKIE_NAME), code
        )

    @app.get("/instructor")
    def instructor_landing_bare():
        return redirect("/instructor/", code=301)

    @app.get("/instructor/")
    def instructor_landing():
        return send_from_directory(UI_DIR, "instructor_login.html")

    @app.get("/instructor/sessions")
    def instructor_sessions_page():
        return _serve_gated_page(config, "instructor_sessions.html")

    @app.get("/api/instructor/return-to")
    def capture_return_to():
        target = _safe_return_to(
            request.headers.get("X-Original-URI", ""),
            method=request.headers.get("X-Original-Method", "GET"),
        )
        resp = make_response(redirect("/instructor/", code=302))
        if target:
            _set_return_to_cookie(resp, config, target)
        else:
            _clear_return_to_cookie(resp)
        return resp

    @app.post("/api/instructor/login")
    def login():
        data = request.get_json(silent=True) or {}
        user = data.get("user", data.get("username", ""))
        submitted = data.get("key", data.get("password", ""))
        redirect_to = _consume_return_to(config)
        if _auth_bypassed(config):
            log_auth_event("login", outcome="bypassed", sub=user or "")
            body = {"success": True, "message": "auth bypassed"}
            if redirect_to:
                body["redirect_to"] = redirect_to
            resp = make_response(jsonify(body))
            _clear_return_to_cookie(resp)
            return resp
        if not _check_credentials(user, submitted):
            log_auth_event("login", outcome="fail", reason="bad_credentials", sub=user or "")
            return jsonify({"success": False, "message": "invalid credentials"}), 401
        body = {"success": True}
        if redirect_to:
            body["redirect_to"] = redirect_to
        resp = make_response(jsonify(body))
        payload = _issue_cookie(resp, config, sub=user)
        _clear_return_to_cookie(resp)
        sessions.record_issue(payload["jti"], payload["sub"], int(payload["iat"]), _client_ip())
        log_auth_event("login", outcome="ok", sub=user or "", jti=payload["jti"])
        return resp

    @app.post("/api/instructor/logout")
    def logout():
        identity = _authenticated_identity(config)
        resp = make_response(jsonify({"success": True}))
        resp.delete_cookie(COOKIE_NAME, path="/")
        if identity is not None:
            sessions.forget(identity.jti)
            log_auth_event("logout", outcome="ok", jti=identity.jti)
        else:
            log_auth_event("logout", outcome="ok")
        return resp

    @app.get("/instructor/logout")
    def logout_redirect():
        identity = _authenticated_identity(config)
        resp = make_response(redirect("/instructor/?msg=logged_out"))
        resp.delete_cookie(COOKIE_NAME, path="/")
        if identity is not None:
            sessions.forget(identity.jti)
            log_auth_event("logout", outcome="ok", jti=identity.jti)
        else:
            log_auth_event("logout", outcome="ok")
        return resp

    @app.get("/api/instructor/verify")
    def verify_endpoint():
        identity = _authenticated_identity(config)
        if identity is None:
            return ("", 401)
        return ("", 200)

    @app.get("/api/instructor/whoami")
    def whoami():
        identity = _authenticated_identity(config)
        payload = {
            "authenticated": identity is not None,
            "auth_enabled": config.mode is not AuthMode.DISABLED,
            "auth_bypassed": _auth_bypassed(config),
        }
        if identity is not None or _auth_bypassed(config):
            payload["using_default_credentials"] = _using_default_credentials()
        if identity is not None:
            payload["sub"] = identity.sub
        return jsonify(payload)

    @app.get("/api/instructor/sessions")
    @_require_api_instructor(config)
    def list_sessions():
        return jsonify({"sessions": sessions.list_active()})

    @app.post("/api/instructor/sessions/revoke")
    @_require_api_instructor(config)
    def revoke_session():
        data = request.get_json(silent=True) or {}
        target_jti = (data.get("jti") or "").strip()
        if not target_jti:
            return jsonify({"success": False, "message": "jti required"}), 400
        sessions.revoke(target_jti)
        sessions.forget(target_jti)
        audit_write("session.revoke", extra={"target_jti": target_jti})
        return jsonify({"success": True})

    @app.get("/class")
    def class_page_bare():
        return redirect("/class/", code=301)

    @app.get("/class/")
    def class_page():
        return send_from_directory(CLASS_PAGE_DIR, "class_pass.html")

    @app.get("/api/class/return-to")
    def class_return_to():
        target = class_gate.safe_return_to(
            request.headers.get("X-Original-URI", ""),
            method=request.headers.get("X-Original-Method", "GET"),
        )
        resp = make_response(redirect("/class/", code=302))
        if target:
            resp.set_cookie(
                class_gate.RETURN_TO_COOKIE_NAME,
                class_gate.mint_return_to(secret_key, target),
                max_age=class_gate.RETURN_TO_MAX_AGE,
                httponly=True,
                samesite="Lax",
                path="/",
            )
        else:
            resp.delete_cookie(class_gate.RETURN_TO_COOKIE_NAME, path="/")
        return resp

    @app.get("/api/class/status")
    def class_status():
        code, _source = class_gate.current_code()
        return jsonify(
            {
                "gate_on": class_gate.gate_enabled(),
                "code_set": bool(code),
                "has_pass": _has_class_pass(),
            }
        )

    @app.post("/api/class/enter")
    def class_enter():
        ip = _client_ip()
        wait = class_failures.retry_after(ip)
        if wait:
            resp = jsonify(
                {"success": False, "message": "Too many wrong codes. Wait a minute and try again."}
            )
            resp.status_code = 429
            resp.headers["Retry-After"] = str(wait)
            return resp
        data = request.get_json(silent=True) or {}
        code, _source = class_gate.current_code()
        if not class_gate.codes_match(str(data.get("code") or ""), code):
            class_failures.record_failure(ip)
            log_auth_event("class_enter", outcome="fail", reason="wrong_code")
            return jsonify({"success": False, "message": "That is not the class code."}), 401
        redirect_to = class_gate.read_return_to(
            secret_key, request.cookies.get(class_gate.RETURN_TO_COOKIE_NAME)
        )
        resp = make_response(jsonify({"success": True, "redirect_to": redirect_to or "/"}))
        resp.set_cookie(
            class_gate.PASS_COOKIE_NAME,
            class_gate.mint_pass(secret_key, code),
            max_age=class_gate.PASS_MAX_AGE,
            httponly=True,
            secure=request.is_secure,
            samesite="Lax",
            path="/",
            domain=class_gate.cookie_domain(request.host),
        )
        resp.delete_cookie(class_gate.RETURN_TO_COOKIE_NAME, path="/")
        log_auth_event("class_enter", outcome="ok")
        return resp

    @app.get("/api/class/verify")
    def class_verify():
        # The router's auth_request and the lane-service ask this on every gated request.
        if _has_class_pass() or verify(request, config) is not None:
            return ("", 200)
        return ("", 403)

    @app.get("/api/instructor/class-code")
    @_require_api_instructor(config)
    def get_class_code():
        code, source = class_gate.current_code()
        return jsonify({"code": code, "source": source, "gate_on": class_gate.gate_enabled()})

    @app.post("/api/instructor/class-code")
    @_require_api_instructor(config)
    def change_class_code():
        data = request.get_json(silent=True) or {}
        if data.get("generate"):
            new_code = class_gate.generate_code()
        else:
            new_code = class_gate.normalize_code(str(data.get("code") or ""))
            problem = class_gate.code_problem(new_code)
            if problem:
                return jsonify({"success": False, "message": problem}), 400
        try:
            class_gate.set_code(new_code)
        except OSError:
            return jsonify({"success": False, "message": "could not save the class code"}), 500
        audit_write("class_code.change", extra={"generated": bool(data.get("generate"))})
        return jsonify(
            {"success": True, "code": new_code, "source": "portal", "gate_on": class_gate.gate_enabled()}
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
