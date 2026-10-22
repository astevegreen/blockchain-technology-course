from __future__ import annotations

from flask import Flask, jsonify, render_template, request, url_for
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config


socketio = SocketIO(async_mode=Config.SOCKETIO_ASYNC_MODE, cors_allowed_origins="*")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not set. Run ./lab-manager.sh deploy, which generates it "
            "(as BGP_GAME_SECRET_KEY) into .runtime/runtime-secrets.env, or set SECRET_KEY yourself."
        )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    socketio.init_app(app, manage_session=True)

    from .sockets.events import register_socket_events

    register_socket_events(socketio)

    def socketio_asset_url() -> str:
        return url_for("static", filename="vendor/socket.io.min.js")

    def vis_network_asset_url() -> str:
        return url_for("static", filename="vendor/vis-network.min.js")

    @app.get("/")
    def index():
        script_root = request.script_root or ""
        return render_template(
            "index.html",
            socketio_client_url=socketio_asset_url(),
            vis_network_url=vis_network_asset_url(),
            socketio_path=f"{script_root}/socket.io" if script_root else "/socket.io",
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    return app
