#!/usr/bin/env python3
"""
HLF Lab Web Service App
Serves the web UI and API routes.
"""

import atexit
import os
import signal
import threading
from pathlib import Path
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from claim_routes import claim_bp
from claims import get_claim_manager
from hlf_router import get_service, hlf_bp
from instructor_routes import instructor_assets_bp
from lane_routes import lane_bp
from lanes import get_lane_manager
from progress_routes import progress_bp, register_surface_middleware
from progress_store import get_tracker
from shared_auth import init_shared_auth

BASE_DIR = Path(__file__).resolve().parent
HLF_DIR = BASE_DIR.parent
WEB_UI_DIR = HLF_DIR / "web_ui"
VENDOR_DIR = Path("/opt/hlf_vendor")

app = Flask(
    __name__,
    template_folder=str(WEB_UI_DIR),
    static_folder=str(WEB_UI_DIR),
    static_url_path="",
)
app.config["SECRET_KEY"] = os.environ.get("HLF_WEB_SECRET_KEY", os.environ.get("SECRET_KEY", "hlf_lab_secret"))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1, x_prefix=1)  # type: ignore[assignment]

init_shared_auth(app)

app.register_blueprint(hlf_bp)
app.register_blueprint(lane_bp)
app.register_blueprint(claim_bp)
app.register_blueprint(instructor_assets_bp)
app.register_blueprint(progress_bp)

# Installs a before_request hook that logs student visits to coarse
# surfaces (explorer, console, exercises index) into the progress store.
register_surface_middleware(app)

# Kick off the lane manager (and its idle sweeper) at boot.
get_lane_manager()
# Kick off the claim manager (rehydrates from disk + starts sweeper).
get_claim_manager()
# Hydrate the progress tracker from runtime/progress/*.jsonl on start.
get_tracker()

_shutdown_once = threading.Event()


def _env_enabled(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _cleanup_runtime() -> None:
    if _shutdown_once.is_set():
        return
    _shutdown_once.set()
    try:
        get_claim_manager().stop_sweeper()
    except Exception:
        pass
    try:
        get_lane_manager().shutdown()
    except Exception:
        pass
    if _env_enabled("HLF_STOP_NETWORK_ON_EXIT", "1"):
        try:
            get_service().shutdown_runtime("runner exit")
        except Exception:
            pass


def _handle_shutdown_signal(signum, _frame) -> None:
    _cleanup_runtime()
    raise SystemExit(0)


def _maybe_auto_start_network() -> None:
    if not _env_enabled("HLF_AUTO_START_NETWORK", "1"):
        return
    svc = get_service()
    try:
        status = svc.get_network_status()
        if status.get("status") == "running":
            print("[hlf] auto-start: network already running, skipping lab.sh up")
            return
    except Exception:
        pass
    try:
        success, message = svc.start_network()
    except Exception as exc:
        print(f"[hlf] auto-start failed: {exc}")
        return
    print(f"[hlf] auto-start: {message}")


atexit.register(_cleanup_runtime)
signal.signal(signal.SIGTERM, _handle_shutdown_signal)
signal.signal(signal.SIGINT, _handle_shutdown_signal)

@app.route("/")
def index():
    return app.send_static_file("hlf_lab.html")


@app.route("/vendor/<path:filename>")
def vendor(filename: str):
    return send_from_directory(VENDOR_DIR, filename)

if __name__ == "__main__":
    _maybe_auto_start_network()
    print("HLF Lab Web UI running at http://localhost:8080")
    app.run(host="0.0.0.0", port=8080)
