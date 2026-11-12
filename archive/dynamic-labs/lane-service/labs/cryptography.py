"""
Cryptography lab — progress-tracker only.

Cryptography is a Streamlit app with its own cookie-sticky pool
(`crypto_lab_session`) routed directly by the outer router. No
containers, lanes, or claims are managed by the lane-service for
this lab — but the shared progress tracker lives here so crypto
joins the per-lab Progress tab + cross-lab rollup.

Routes:
  GET  /api/cryptography/exercises             — canonical page catalog
  POST /api/cryptography/progress/touch        — beacon from Streamlit pages
  GET  /api/cryptography/progress              — instructor summary
  GET  /api/cryptography/progress/<session_id> — instructor detail

Session identity is the `crypto_lab_session` cookie (or `session` in
the body / `X-Session` header). The value is not a strict UUID so we
validate with a lenient regex.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from flask import Blueprint, jsonify, make_response, request

from exercises import get_catalog as get_exercise_catalog, register_catalog
from instructor_auth import require_instructor
from labs.cryptography_catalog import (
    CATALOG as CRYPTO_CATALOG,
    EXERCISE_IDS as CRYPTO_EXERCISE_IDS,
    SURFACE_IDS as CRYPTO_SURFACE_IDS,
)
from progress import get_tracker, register_tracker

LAB_NAME = "cryptography"
COOKIE_NAME = "crypto_lab_session"
_SESSION_RE = re.compile(r"^[A-Za-z0-9._-]{8,128}$")

STATE_DIR = Path(os.environ.get(
    "CRYPTOGRAPHY_STATE_DIR",
    "/app/runtime/cryptography",
))

_ADMIN_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "cryptography_admin.html"

# Bind-mounted (read-only) cryptography source dir. The instructor guide
# is read directly from disk; no cross-container HTTP call.
_CRYPTO_DIR = Path(os.environ.get("CRYPTOGRAPHY_SOURCE_DIR", "/app/cryptography")).resolve()
_GUIDE_PATH = (_CRYPTO_DIR / "solution.md").resolve()

register_catalog(LAB_NAME, CRYPTO_CATALOG)

_tracker = register_tracker(
    LAB_NAME,
    state_dir=STATE_DIR / "progress",
    exercise_ids=CRYPTO_EXERCISE_IDS,
    surface_ids=CRYPTO_SURFACE_IDS,
)


def _valid_session(s: str) -> bool:
    return bool(s) and bool(_SESSION_RE.match(s))


def _get_session_id() -> str:
    return (
        request.headers.get("X-Session")
        or request.cookies.get(COOKIE_NAME)
        or (request.get_json(silent=True) or {}).get("session")
        or request.args.get("session")
        or ""
    ).strip()


blueprint = Blueprint("cryptography_lab", __name__)


@blueprint.route("/api/cryptography/exercises", methods=["GET"])
def exercises_catalog():
    cat = get_exercise_catalog(LAB_NAME)
    if cat is None:
        return jsonify({"intro": {}, "exercises": []})
    return jsonify(cat)


@blueprint.route("/api/cryptography/progress/touch", methods=["POST"])
def progress_touch():
    session_id = _get_session_id()
    if not _valid_session(session_id):
        return jsonify({"ok": True, "recorded": False, "reason": "no session"})
    data = request.get_json(silent=True) or {}
    route_id = (data.get("route_id") or "").strip()
    tracker = get_tracker(LAB_NAME)
    if tracker is None or not route_id or not tracker.is_known_route(route_id):
        return jsonify({"ok": False, "recorded": False, "reason": "unknown route"}), 400
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    recorded = tracker.record(
        session_id, route_id, source="client", station=None, meta=meta,
    )
    return jsonify({"ok": True, "recorded": recorded})


@blueprint.route("/api/cryptography/progress", methods=["GET"])
@require_instructor
def progress_list():
    tracker = get_tracker(LAB_NAME)
    if tracker is None:
        return jsonify({"progress": {}})
    return jsonify({"progress": tracker.all_summaries()})


@blueprint.route("/labs/cryptography/admin", methods=["GET"])
@require_instructor
def admin_page():
    html = _ADMIN_TEMPLATE_PATH.read_text(encoding="utf-8")
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


@blueprint.route("/api/cryptography/instructor-guide", methods=["GET"])
@require_instructor
def instructor_guide():
    import markdown as md
    if _GUIDE_PATH.parent != _CRYPTO_DIR or not _GUIDE_PATH.is_file():
        return jsonify({"ok": False, "error": "solution.md not found"}), 404
    body = _GUIDE_PATH.read_text(encoding="utf-8")
    html = md.markdown(body, extensions=["fenced_code", "tables", "toc"])
    return jsonify({"ok": True, "html": html, "source": str(_GUIDE_PATH)})


@blueprint.route("/api/cryptography/progress/<session_id>", methods=["GET"])
@require_instructor
def progress_detail(session_id: str):
    session_id = (session_id or "").strip()
    if not _valid_session(session_id):
        return jsonify({"success": False, "message": "invalid session"}), 400
    tracker = get_tracker(LAB_NAME)
    if tracker is None:
        return jsonify({"success": False, "message": "progress disabled"}), 404
    detail = tracker.detail_for(session_id)
    if detail is None:
        return jsonify({"success": False, "message": "no progress recorded"}), 404
    return jsonify({"success": True, "detail": detail})


def start() -> None:
    # No sweepers — no lanes or claims owned by this lab.
    return None


def stop() -> None:
    return None
