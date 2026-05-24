"""
Flask blueprint for Phase 7 lane management.

Routes (instructor-gated via the shared /instructor cookie; `touch` is
open because students call it from lane UIs):
  GET    /api/hlf/lanes                 -> list all lanes          [auth]
  POST   /api/hlf/lanes/<id>/start      -> start a student's peer  [auth]
  POST   /api/hlf/lanes/<id>/stop       -> stop a student's peer   [auth]
  POST   /api/hlf/lanes/<id>/reset      -> reset (rm + drop volume) [auth]
  POST   /api/hlf/lanes/<id>/touch      -> mark lane active        [open]
"""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from shared_auth import require_instructor
from lanes import get_lane_manager, lane_ids

lane_bp = Blueprint("hlf_lanes", __name__)


@lane_bp.before_request
def _guard_lane_id() -> None:
    valid_lane_ids = set(lane_ids())
    candidates = []
    if request.view_args:
        candidates.append(request.view_args.get("lane_id"))
    body = request.get_json(silent=True) or {}
    if isinstance(body, dict):
        candidates.append(body.get("lane_id"))
    candidates.append(request.args.get("lane_id"))
    for value in candidates:
        if value is None:
            continue
        if not isinstance(value, str) or value not in valid_lane_ids:
            abort(400, description="invalid lane id")


@lane_bp.route("/api/hlf/lanes", methods=["GET"])
@require_instructor
def lanes_list():
    return jsonify({"lanes": get_lane_manager().list_lanes()})


@lane_bp.route("/api/hlf/lanes/<lane_id>/start", methods=["POST"])
@require_instructor
def lane_start(lane_id: str):
    ok, msg = get_lane_manager().start_lane(lane_id)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@lane_bp.route("/api/hlf/lanes/<lane_id>/stop", methods=["POST"])
@require_instructor
def lane_stop(lane_id: str):
    ok, msg = get_lane_manager().stop_lane(lane_id)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@lane_bp.route("/api/hlf/lanes/<lane_id>/reset", methods=["POST"])
@require_instructor
def lane_reset(lane_id: str):
    ok, msg = get_lane_manager().reset_lane(lane_id)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@lane_bp.route("/api/hlf/lanes/<lane_id>/touch", methods=["POST"])
def lane_touch(lane_id: str):
    get_lane_manager().touch(lane_id)
    return jsonify({"success": True})
