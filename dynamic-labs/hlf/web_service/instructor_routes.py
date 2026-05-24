"""HLF runner-only instructor asset routes.

The centralized instructor auth service now owns `/instructor/*` and
`/api/instructor/*`. The HLF runner still serves its own instructor
HTML/JS files and gates them locally using the shared cookie verifier
for defense in depth.
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, redirect, request, send_from_directory

from shared_auth import is_authenticated

instructor_assets_bp = Blueprint("instructor_assets", __name__)

# Served by the HLF runner's static web_ui dir, proxied under /instructor
# by the top-level router.
_WEB_UI = Path(__file__).resolve().parent.parent / "web_ui"


def _serve_gated(filename: str):
    if not is_authenticated():
        accept = request.headers.get("Accept", "")
        if "text/html" in accept:
            return redirect("/instructor/", code=302)
        return ("", 401)
    return send_from_directory(_WEB_UI, filename)


@instructor_assets_bp.route("/hlf_instructor.html", methods=["GET"])
def gated_instructor_html():
    return _serve_gated("hlf_instructor.html")


@instructor_assets_bp.route("/hlf_instructor.js", methods=["GET"])
def gated_instructor_js():
    return _serve_gated("hlf_instructor.js")
