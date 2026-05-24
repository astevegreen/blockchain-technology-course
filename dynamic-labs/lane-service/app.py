#!/usr/bin/env python3
"""
Lane Service — shared on-demand container management for all labs.
"""

import atexit
import os
import signal
import threading

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("LANE_SERVICE_SECRET", "lane-service-dev")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1, x_prefix=1)

from labs import bitcoin, consensus, cryptography, ethereum, p2p_trust
app.register_blueprint(consensus.blueprint)
consensus.start()
app.register_blueprint(p2p_trust.blueprint)
p2p_trust.start()
app.register_blueprint(bitcoin.blueprint)
bitcoin.start()
app.register_blueprint(cryptography.blueprint)
cryptography.start()
app.register_blueprint(ethereum.blueprint)
ethereum.start()

from portal import portal_bp
app.register_blueprint(portal_bp)

_shutdown_once = threading.Event()


def _cleanup_runtime() -> None:
    if _shutdown_once.is_set():
        return
    _shutdown_once.set()
    for module in (bitcoin, consensus, p2p_trust, ethereum, cryptography):
        stop = getattr(module, "stop", None)
        if callable(stop):
            try:
                stop()
            except Exception:
                pass


def _handle_shutdown_signal(signum, _frame) -> None:
    _cleanup_runtime()
    raise SystemExit(0)


atexit.register(_cleanup_runtime)
signal.signal(signal.SIGTERM, _handle_shutdown_signal)
signal.signal(signal.SIGINT, _handle_shutdown_signal)


@app.route("/healthz")
def healthz():
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("LANE_SERVICE_PORT", "8090"))
    app.run(host="0.0.0.0", port=port, threaded=True)
