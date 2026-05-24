from dataclasses import asdict, dataclass
from functools import wraps

from flask import current_app, g, jsonify, redirect, request, session

from instructor_auth import (
    CSRF_HEADER,
    AuthConfig,
    AuthMode,
    csrf_blueprint,
    install_sliding_reissue,
    mint_csrf_token,
    standalone_blueprint,
    verify,
    verify_csrf_token,
)


@dataclass(frozen=True)
class InstructorContext:
    subject: str
    auth_mode: str


def current_instructor():
    return getattr(g, "instructor_context", None)


def _load_test_header_context():
    header_name = current_app.config["TEST_INSTRUCTOR_HEADER"]
    subject = request.headers.get(header_name)
    if not subject:
        return None
    return InstructorContext(subject=subject, auth_mode="test-header")


def _load_test_session_context():
    subject = session.get("test_instructor_subject")
    if not subject:
        return None
    return InstructorContext(subject=subject, auth_mode="test-session")


def _load_instructor_context():
    mode = current_app.config["INSTRUCTOR_AUTH_MODE"]
    if mode == "test-header":
        return _load_test_header_context() or _load_test_session_context()
    return _load_shared_context(mode)
    raise RuntimeError(f"Unsupported instructor auth mode: {mode}")


def _load_shared_context(mode):
    auth = current_app.config.get("INSTRUCTOR_AUTH")
    if auth is None:
        raise RuntimeError("shared instructor auth is not initialized")
    identity = verify(request, auth)
    if identity is None:
        return None
    g.instructor = identity
    return InstructorContext(
        subject=identity.sub or "instructor",
        auth_mode=mode,
    )


def _auth_failure_response():
    mode = current_app.config["INSTRUCTOR_AUTH_MODE"]
    if mode != "test-header":
        if request.method == "GET" and not _expects_json_response():
            auth = current_app.config.get("INSTRUCTOR_AUTH")
            login_url = auth.login_url() if auth is not None else "/instructor/"
            return redirect(login_url)
        return jsonify(error="instructor_auth_required"), 401
    return jsonify(error="instructor_auth_required"), 401


def _expects_json_response():
    accept = request.headers.get("Accept", "")
    return (
        request.path.startswith("/api/")
        or "/api/" in request.path
        or "application/json" in accept
    )


def instructor_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        context = _load_instructor_context()
        if context is None:
            return _auth_failure_response()
        g.instructor_context = context
        return view(*args, **kwargs)

    return wrapped


def instructor_context_dict():
    context = current_instructor()
    return asdict(context) if context is not None else None


def establish_test_instructor_session(subject):
    if current_app.config["INSTRUCTOR_AUTH_MODE"] != "test-header":
        raise RuntimeError("test instructor session is only available in test-header mode")
    session["test_instructor_subject"] = str(subject).strip() or "test-instructor"


def clear_test_instructor_session():
    session.pop("test_instructor_subject", None)


def init_shared_auth(app):
    mode = app.config["INSTRUCTOR_AUTH_MODE"]
    if mode == "test-header":
        return

    auth = AuthConfig.from_env()
    if auth.mode.value != mode:
        raise RuntimeError(
            "QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE and INSTRUCTOR_AUTH_MODE must match "
            f"for shared deployment; got {mode!r} and {auth.mode.value!r}"
        )
    app.config["INSTRUCTOR_AUTH"] = auth
    if auth.mode is AuthMode.STANDALONE:
        app.register_blueprint(standalone_blueprint(auth))
    app.register_blueprint(csrf_blueprint(auth))
    install_sliding_reissue(app)
    _install_quiz_engine_csrf_protection(app, auth)


def _install_quiz_engine_csrf_protection(app, auth):
    if app.config.get("_QUIZ_ENGINE_CSRF_INSTALLED"):
        return
    app.config["_QUIZ_ENGINE_CSRF_INSTALLED"] = True

    @app.before_request
    def _enforce_quiz_engine_instructor_csrf():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None
        if not request.path.startswith("/instructor"):
            return None
        if request.path in {
            "/instructor/login",
            "/instructor/logout",
            "/instructor/dev/login",
            "/instructor/dev/logout",
        }:
            return None
        identity = verify(request, auth)
        if identity is None:
            return None
        submitted = request.headers.get(CSRF_HEADER, "") or request.form.get(
            "_csrf_token", ""
        )
        if verify_csrf_token(auth, submitted, identity.jti):
            return None
        return jsonify({"success": False, "message": "csrf token required"}), 403


def csrf_token_for_current_instructor():
    auth = current_app.config.get("INSTRUCTOR_AUTH")
    identity = getattr(g, "instructor", None)
    if auth is None or identity is None:
        return ""
    return mint_csrf_token(auth, identity.jti)
