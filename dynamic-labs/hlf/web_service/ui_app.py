#!/usr/bin/env python3
"""
HLF UI service.
Serves the static managed-lab frontend without owning Fabric orchestration.
"""

from pathlib import Path

from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

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
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1, x_prefix=1)  # type: ignore[assignment]


@app.route("/")
def index():
    return app.send_static_file("hlf_lab.html")


@app.route("/explorer/")
def explorer():
    return app.send_static_file("hlf_explorer.html")


@app.route("/explorer/transactions/<tx_id>/")
def explorer_transaction(tx_id: str):
    return app.send_static_file("hlf_transaction.html")


@app.route("/explorer/assets/<asset_id>/")
def explorer_asset(asset_id: str):
    return app.send_static_file("hlf_asset.html")


@app.route("/explorer/chaincode/")
def explorer_chaincode():
    return app.send_static_file("hlf_chaincode.html")


@app.route("/explorer/governance/")
def explorer_governance():
    return app.send_static_file("hlf_governance.html")


@app.route("/exercises/")
def exercises():
    return app.send_static_file("hlf_exercises.html")


@app.route("/instructor/")
def instructor():
    return app.send_static_file("hlf_instructor.html")


@app.route("/peer/org1/")
def peer_org1():
    return app.send_static_file("hlf_node.html")


@app.route("/peer/org2/")
def peer_org2():
    return app.send_static_file("hlf_node.html")


@app.route("/peer/org3/")
def peer_org3():
    return app.send_static_file("hlf_node.html")


@app.route("/peer/org4/")
def peer_org4():
    return app.send_static_file("hlf_node.html")


@app.route("/peer/org5/")
def peer_org5():
    # Meridian employer console — gated at the nginx layer via
    # auth_request /_auth/instructor; Flask just serves the static
    # page.
    return app.send_static_file("hlf_node.html")


@app.route("/orderer/")
def orderer_view():
    return app.send_static_file("hlf_node.html")


@app.route("/peer/org1/console/")
def peer_org1_console():
    return app.send_static_file("hlf_console.html")


@app.route("/peer/org2/console/")
def peer_org2_console():
    return app.send_static_file("hlf_console.html")


@app.route("/peer/org3/console/")
def peer_org3_console():
    return app.send_static_file("hlf_console.html")


@app.route("/peer/org4/console/")
def peer_org4_console():
    return app.send_static_file("hlf_console.html")


@app.route("/peer/org5/console/")
def peer_org5_console():
    return app.send_static_file("hlf_console.html")


@app.route("/orderer/console/")
def orderer_console():
    return app.send_static_file("hlf_console.html")


@app.route("/vendor/<path:filename>")
def vendor(filename: str):
    return send_from_directory(VENDOR_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
