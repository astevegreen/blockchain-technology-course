from __future__ import annotations

from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session, url_for
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from instructor_auth import (
    AuthConfig,
    AuthMode,
    csrf_blueprint,
    install_csrf_protection,
    install_login_rate_limit,
    install_sliding_reissue,
    require_instructor,
    standalone_blueprint,
    verify,
)

from .config import Config


socketio = SocketIO(async_mode=Config.SOCKETIO_ASYNC_MODE, cors_allowed_origins="*")


def _set_session_on_auth(auth: AuthConfig):
    """Preserve the pre-existing `session['is_instructor']` contract for
    Socket.IO event handlers. Called from a wrapped require_instructor
    so HTTP hits update the flag before any socket events fire."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if verify(request, auth):
                session["is_instructor"] = True
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    auth = AuthConfig.from_env()
    app.config["INSTRUCTOR_AUTH"] = auth
    if auth.mode is AuthMode.STANDALONE:
        app.register_blueprint(standalone_blueprint(auth))
    app.register_blueprint(csrf_blueprint(auth))
    install_sliding_reissue(app)
    install_csrf_protection(app, auth)
    if auth.mode is AuthMode.STANDALONE:
        try:
            install_login_rate_limit(
                app,
                login_endpoints=["instructor_auth_standalone.login"],
            )
        except Exception as _rl_err:
            import sys as _sys
            _sys.stderr.write(f"[bgp-game] WARNING: rate limiter not installed: {_rl_err}\n")

    socketio.init_app(app, manage_session=True)

    from .sockets.events import register_socket_events

    register_socket_events(socketio)

    def socketio_asset_url() -> str:
        vendor_path = Path(app.static_folder) / "vendor" / "socket.io.min.js"
        if vendor_path.exists():
            return url_for("static", filename="vendor/socket.io.min.js")
        return "https://cdn.socket.io/4.7.5/socket.io.min.js"

    def vis_network_asset_url() -> str:
        vendor_path = Path(app.static_folder) / "vendor" / "vis-network.min.js"
        if vendor_path.exists():
            return url_for("static", filename="vendor/vis-network.min.js")
        return "https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"

    @app.get("/")
    def index():
        session.setdefault("is_instructor", False)
        script_root = request.script_root or ""
        return render_template(
            "index.html",
            socketio_client_url=socketio_asset_url(),
            vis_network_url=vis_network_asset_url(),
            socketio_path=f"{script_root}/socket.io" if script_root else "/socket.io",
        )

    @app.get("/instructor")
    @require_instructor(auth)
    @_set_session_on_auth(auth)
    def instructor():
        script_root = request.script_root or ""
        return render_template(
            "instructor.html",
            socketio_client_url=socketio_asset_url(),
            vis_network_url=vis_network_asset_url(),
            socketio_path=f"{script_root}/socket.io" if script_root else "/socket.io",
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    return app
