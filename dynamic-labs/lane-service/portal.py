"""
Cross-lab instructor portal surfaces.

Exposes the `/api/portal/progress-rollup` JSON endpoint consumed by the
instructor portal's Labs Progress panel and the standalone progress page.
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, jsonify, make_response

from instructor_auth import require_instructor
from progress import all_trackers

portal_bp = Blueprint("portal", __name__)

_PROGRESS_HTML = Path(__file__).parent / "progress_summary.html"


@portal_bp.route("/api/portal/progress-rollup", methods=["GET"])
@require_instructor
def progress_rollup():
    labs = []
    for tracker in all_trackers().values():
        labs.append(tracker.rollup())
    labs.sort(key=lambda r: r["lab"])
    return jsonify({"labs": labs})


@portal_bp.route("/instructor/labs-progress/", methods=["GET"])
@portal_bp.route("/instructor/labs-progress", methods=["GET"])
@require_instructor
def progress_summary_page():
    html = _PROGRESS_HTML.read_text(encoding="utf-8")
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp
