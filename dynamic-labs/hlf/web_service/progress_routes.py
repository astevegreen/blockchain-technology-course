"""
Progress tracking endpoints + coarse-path middleware.

Student-facing:
  POST /api/hlf/progress/touch     body {"route_id": "exercise:peer-outage"}
      Records a visit for the session identified by the cookie / header.
      Silently no-ops in preview mode (no session) or on unknown routes.

Instructor-facing:
  GET  /api/hlf/progress           compact summaries of every tracked session
  GET  /api/hlf/progress/<uuid>    full drilldown (visited, unvisited, timeline)

Middleware:
  register_surface_middleware(app) installs a before_request that looks at
  HTML navigations to known student surfaces (explorer, console,
  governance) and records a "source=middleware" visit. This runs
  alongside the fine-grained client beacon, so both are captured.
"""

from __future__ import annotations

from typing import Optional

from flask import Blueprint, Flask, jsonify, request

from claims import get_claim_manager, is_valid_uuid
from shared_auth import require_instructor
from progress_store import get_tracker, is_known_route

progress_bp = Blueprint("progress", __name__)

COOKIE_NAME = "hlf_session"


def _session_uuid() -> Optional[str]:
    raw = (
        request.headers.get("X-HLF-Session")
        or request.cookies.get(COOKIE_NAME)
        or request.args.get("session")
    )
    if not raw:
        return None
    raw = raw.strip().lower()
    return raw if is_valid_uuid(raw) else None


def _station_for(uuid: str) -> Optional[str]:
    try:
        return get_claim_manager().resolve(uuid)
    except Exception:
        return None


# ----------------------------------------------------------------------
# student beacon
# ----------------------------------------------------------------------
@progress_bp.route("/api/hlf/progress/touch", methods=["POST"])
def progress_touch():
    uuid = _session_uuid()
    if not uuid:
        # Preview mode or an unauthenticated viewer. Silently accept so
        # the client doesn't spam a warning.
        return jsonify({"ok": True, "recorded": False, "reason": "no session"})
    data = request.get_json(silent=True) or {}
    route_id = (data.get("route_id") or "").strip()
    if not route_id or not is_known_route(route_id):
        return jsonify({"ok": False, "recorded": False, "reason": "unknown route"}), 400
    station = _station_for(uuid)
    if not station:
        return jsonify({"ok": True, "recorded": False, "reason": "no station"})
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    recorded = get_tracker().record(
        uuid,
        route_id,
        source="client",
        station=station,
        meta=meta,
    )
    return jsonify({"ok": True, "recorded": recorded})


# ----------------------------------------------------------------------
# instructor read endpoints
# ----------------------------------------------------------------------
@progress_bp.route("/api/hlf/progress", methods=["GET"])
@require_instructor
def progress_list():
    return jsonify({"progress": get_tracker().all_summaries()})


@progress_bp.route("/api/hlf/progress/<uuid>", methods=["GET"])
@require_instructor
def progress_detail(uuid: str):
    uuid = (uuid or "").strip().lower()
    if not is_valid_uuid(uuid):
        return jsonify({"success": False, "message": "invalid uuid"}), 400
    detail = get_tracker().detail_for(uuid)
    if detail is None:
        return jsonify({"success": False, "message": "no progress recorded"}), 404
    return jsonify({"success": True, "detail": detail})


# ----------------------------------------------------------------------
# middleware — coarse-path logging
# ----------------------------------------------------------------------
# Map nginx-rewritten paths (as seen by Flask) to our canonical surface
# route ids. The router strips /labs/hlf/c/<uuid> and /labs/hlf/s/<sid>
# prefixes when proxying, so we match against the tail paths Flask sees.
_SURFACE_MATCHERS = [
    # tuple of (exact_path_or_prefix, is_prefix, canonical route_id)
    # Order matters — /explorer/governance must come before /explorer.
    ("/explorer/governance", True, "surface:explorer/governance"),
    ("/explorer", True, "surface:explorer"),
    # Console launcher pages — ttyd itself is proxied past Flask, but the
    # launcher (hlf_console.html) at /peer/orgN/console/ and /orderer/console/
    # is Flask-served, so we catch visits here.
    ("/peer", True, "surface:term"),
    ("/orderer/console", True, "surface:term"),
]


def _classify_path(path: str) -> Optional[str]:
    # Only HTML navigations matter; static .js/.css/.png requests are
    # noise. We approximate "HTML navigation" as a path ending in / or
    # without an extension.
    if "." in path.rsplit("/", 1)[-1]:
        return None
    for needle, is_prefix, route_id in _SURFACE_MATCHERS:
        if is_prefix:
            if path == needle or path.startswith(needle + "/") or path == needle + "/":
                return route_id
        elif path == needle:
            return route_id
    return None


def register_surface_middleware(app: Flask) -> None:
    @app.before_request
    def _record_surface_visit():
        # Only look at GETs; POSTs/PUTs are API calls, not navigations.
        if request.method != "GET":
            return None
        # Skip our own /api surface entirely; touches come from the beacon.
        path = request.path or ""
        if path.startswith("/api/"):
            return None
        route_id = _classify_path(path)
        if route_id is None:
            return None
        uuid = _session_uuid()
        if not uuid:
            return None
        station = _station_for(uuid)
        if not station:
            return None
        get_tracker().record(
            uuid,
            route_id,
            source="middleware",
            station=station,
            meta={"path": path},
        )
        return None
