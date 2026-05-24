"""
Blueprint factory — generates a full set of claim/lane/resolve routes
for any lab given its LaneConfig + managers.

Usage in a lab module:

    bp = make_lab_blueprint(config, lane_manager, claim_manager)
    # Registers routes at /api/{lab_name}/claim, /api/{lab_name}/lanes, etc.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from flask import Blueprint, Response, jsonify, make_response, redirect, request

_ADMIN_TEMPLATE_PATH = Path(__file__).parent / "admin.html"
_WRAPPER_TEMPLATE_PATH = Path(__file__).parent / "wrapper.html"

from generic_claims import ClaimManager, is_valid_uuid
from generic_lanes import LaneConfig, LaneManager
from instructor_auth import is_authenticated as _instructor_authenticated, require_instructor
from exercises import get_catalog as get_exercise_catalog
from progress import (
    all_trackers,
    get_tracker,
    register_tracker,
)

_SHORT_RE = re.compile(r"^[0-9a-f]{8}$")

_STAGING_HTML = """\
<!doctype html><meta charset=utf-8>
<title>Starting lab…</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f172a;color:#e2e8f0;font:16px/1.5 system-ui,sans-serif;
     display:flex;flex-direction:column;align-items:center;justify-content:center;
     height:100vh;text-align:center}
.spinner{width:48px;height:48px;border:4px solid #334155;border-top-color:#60a5fa;
         border-radius:50%;animation:spin .8s linear infinite;margin-bottom:1.5rem}
@keyframes spin{to{transform:rotate(360deg)}}
h1{font-size:1.4rem;margin-bottom:.5rem}
p{color:#94a3b8;font-size:.9rem}
.fail{color:#fca5a5;margin-top:1rem;display:none}
</style>
<div class="spinner" id="sp"></div>
<h1>Preparing your lab environment…</h1>
<p id="msg">Launching container</p>
<p class="fail" id="fail">Taking longer than expected — <a href="" style="color:#60a5fa">retry</a></p>
<script>
(function(){
  var dest = "LANDING_URL";
  var attempts = 0, max = 30, delay = 1000;
  function poll(){
    attempts++;
    document.getElementById("msg").textContent =
      attempts <= 3 ? "Launching container" :
      attempts <= 10 ? "Waiting for services…" : "Almost there…";
    fetch(dest, {method:"HEAD", redirect:"manual"}).then(function(r){
      if(r.status < 500){location.href = dest; return}
      if(attempts >= max){
        document.getElementById("fail").style.display = "block";
        document.querySelector("#fail a").href = dest;
        return;
      }
      setTimeout(poll, delay);
    }).catch(function(){
      if(attempts >= max){
        document.getElementById("fail").style.display = "block";
        document.querySelector("#fail a").href = dest;
        return;
      }
      setTimeout(poll, delay);
    });
  }
  setTimeout(poll, 800);
})();
</script>
"""

_CLAIM_UNAVAILABLE_HTML = """\
<!doctype html><meta charset=utf-8>
<title>No Available Workstations</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f172a;color:#e2e8f0;font:16px/1.6 system-ui,sans-serif;
     display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}
.card{max-width:680px;width:100%;background:#111827;border:1px solid #334155;
      border-radius:16px;padding:28px 24px;box-shadow:0 20px 50px rgba(0,0,0,.35)}
h1{font-size:1.45rem;margin-bottom:.75rem}
p{color:#cbd5e1;margin-bottom:.9rem}
.meta{color:#94a3b8;font-size:.95rem}
.hint{margin-top:1rem;padding:12px 14px;border-radius:10px;background:#0b1220;border:1px solid #233248}
</style>
<div class="card">
  <h1>No available workstations</h1>
  <p>All available workstations for the LAB_TITLE are currently in use.</p>
  <p class="meta">Claimed: CLAIMED_COUNT / TOTAL_COUNT workstations</p>
  <div class="hint">
    Please wait for a workstation to free up, or ask the instructor to release an active claim from the instructor console.
  </div>
</div>
"""

def _render_wrapper(**kwargs: str) -> str:
    html = _WRAPPER_TEMPLATE_PATH.read_text(encoding="utf-8")
    # Inline panel HTML/script first so placeholders inside them
    # (e.g. {{STATION}}) get resolved by the value pass below.
    for panel_key in ("PANEL_HTML", "PANEL_SCRIPT"):
        if panel_key in kwargs:
            html = html.replace("{{" + panel_key + "}}", kwargs.pop(panel_key))
    for k, v in kwargs.items():
        html = html.replace("{{" + k + "}}", v)
    return html


def _claim_unavailable_response(lab_title: str, message: str, claim_manager: ClaimManager):
    summary = claim_manager.summary()
    user_message = (
        f"No available workstations for the {lab_title}. "
        "Please wait for a workstation to free up or ask the instructor to release an active claim."
        if message == "no free stations"
        else message
    )
    payload = {
        "success": False,
        "reason": "no_available_workstations",
        "message": user_message,
        "summary": summary,
    }
    wants_html = request.accept_mimetypes.best_match(["text/html", "application/json"]) == "text/html"
    if wants_html:
        html = (
            _CLAIM_UNAVAILABLE_HTML
            .replace("LAB_TITLE", lab_title)
            .replace("CLAIMED_COUNT", str(summary.get("claimed", "?")))
            .replace("TOTAL_COUNT", str(summary.get("total_stations", "?")))
        )
        resp = make_response(html, 503)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp
    return jsonify(payload), 503


def make_lab_blueprint(
    config: LaneConfig,
    lane_manager: LaneManager,
    claim_manager: ClaimManager,
    *,
    wrapper_panel_html: str = "",
    wrapper_panel_script: str = "",
    enable_peers: bool = False,
    static_port: Optional[int] = None,
    enable_progress: bool = False,
    progress_exercise_ids: Optional[list] = None,
    progress_surface_ids: Optional[list] = None,
    claim_landing_template: Optional[str] = None,
    enable_wrapper_page: bool = True,
    admin_instructor_href: Optional[str] = None,
) -> Blueprint:
    name = config.lab_name
    prefix = f"/api/{name}"
    cookie_name = f"{name}_session"
    cookie_max_age = 60 * 60 * 12

    def _lane_id_value(lane: object) -> str:
        if isinstance(lane, dict):
            return str(lane["id"])
        return str(lane.id)

    valid_lane_ids: Optional[set[str]]
    if hasattr(lane_manager, "list_lanes"):
        valid_lane_ids = set(_lane_id_value(lane) for lane in lane_manager.list_lanes())
    elif hasattr(config, "student_count"):
        valid_lane_ids = {f"s{i:02d}" for i in range(1, config.student_count + 1)}
    else:
        valid_lane_ids = None

    def _valid_lane_id(lane_id: str) -> bool:
        if valid_lane_ids is not None:
            return lane_id in valid_lane_ids
        return bool(re.fullmatch(r"s\d{2}", lane_id))

    bp = Blueprint(f"{name}_lanes", __name__)

    if enable_progress:
        register_tracker(
            name,
            state_dir=config.state_dir / "progress",
            exercise_ids=progress_exercise_ids or [],
            surface_ids=progress_surface_ids or [],
        )

    def _get_session_uuid() -> Optional[str]:
        return (
            request.headers.get("X-Session-UUID")
            or request.cookies.get(cookie_name)
            or request.args.get("session")
        )

    def _ensure_lane_ready(station: str, *, busy_wait_seconds: float = 15.0) -> tuple[bool, str]:
        container = config.container_name_fn(station)
        ready, _ = lane_manager.wait_until_ready(station, timeout_seconds=0.0)
        if ready:
            return True, container

        ok, message = lane_manager.start_lane(station)
        if ok:
            ready, _ = lane_manager.wait_until_ready(
                station,
                timeout_seconds=busy_wait_seconds,
            )
            return (ready, container)

        if "busy" in message.lower():
            ready, _ = lane_manager.wait_until_ready(
                station,
                timeout_seconds=busy_wait_seconds,
            )
            if ready:
                return True, container
            return False, container

        # One last readiness check absorbs races where another starter won after
        # the first attempt but before the error reached resolve.
        ready, _ = lane_manager.wait_until_ready(station, timeout_seconds=0.0)
        if ready:
            return True, container
        return False, container

    # ------------------------------------------------------------------
    # student-facing
    # ------------------------------------------------------------------
    landing_tpl = claim_landing_template or f"/labs/{name}/c/{{uuid}}/"

    @bp.route(f"{prefix}/claim", methods=["GET"])
    def claim_station():
        existing = request.cookies.get(cookie_name) or request.args.get("session")
        uuid, station, message = claim_manager.claim(existing_uuid=existing)
        if uuid is None:
            return _claim_unavailable_response(name.replace("_", " ").title(), message, claim_manager)
        landing = landing_tpl.format(uuid=uuid, station=station)
        html = _STAGING_HTML.replace("LANDING_URL", landing)
        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.set_cookie(
            cookie_name, uuid,
            max_age=cookie_max_age,
            httponly=False,
            samesite="Lax",
            path="/",
        )
        return resp

    @bp.route(f"{prefix}/claims/heartbeat", methods=["POST"])
    def heartbeat():
        uuid = (
            request.headers.get("X-Session-UUID")
            or request.cookies.get(cookie_name)
            or (request.get_json(silent=True) or {}).get("session")
        )
        if not uuid or not is_valid_uuid(uuid):
            return jsonify({"ok": False, "message": "no session"}), 400
        if claim_manager.touch(uuid):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "message": "unknown session"}), 404

    # ------------------------------------------------------------------
    # resolve (called by nginx auth_request)
    # ------------------------------------------------------------------
    @bp.route(f"{prefix}/resolve", methods=["GET"])
    def resolve():
        uuid = request.headers.get("X-Session-UUID") or _get_session_uuid()
        if not uuid or not is_valid_uuid(uuid):
            return Response("no session", status=401)
        station = claim_manager.resolve(uuid)
        if station is None:
            return Response("unknown session", status=401)
        ready, container = _ensure_lane_ready(station)
        if not ready:
            return Response("container starting", status=503)
        resp = Response("ok", status=200)
        resp.headers["X-Lane-Host"] = container
        # Phase 9.4: piggyback the instructor-cookie verdict so the
        # router can forward it to lane-api as `X-Instructor: 1|0`,
        # eliminating the in-container IP allowlist. nginx only allows
        # one auth_request per location and the catch-all already
        # uses this resolve subrequest, so we bundle the second check
        # into its response. _verify_cookie has a 5s TTL cache to
        # absorb the per-asset fan-out.
        verified = _instructor_authenticated()
        resp.headers["X-Instructor-Verified"] = "1" if verified else "0"
        return resp

    # ------------------------------------------------------------------
    # wrapper page (ttyd iframe + heartbeat). Disabled for labs whose
    # student UI is a full SPA proxied directly by the router.
    # ------------------------------------------------------------------
    if enable_wrapper_page:
        @bp.route(f"/labs/{name}/c/<uuid>/", methods=["GET"])
        def wrapper_page(uuid: str):
            if not is_valid_uuid(uuid):
                return "invalid session", 400
            station = claim_manager.resolve(uuid)
            if station is None:
                return redirect(f"/api/{name}/claim", code=302)
            ready, _ = _ensure_lane_ready(station)
            if not ready:
                # Let the claim staging page keep polling instead of loading the
                # wrapper while ttyd auth_request is still racing startup.
                return Response("container starting", status=503)
            panel_script_tag = (
                f"<script>{wrapper_panel_script}</script>" if wrapper_panel_script else ""
            )
            html = _render_wrapper(
                TITLE=f"{name.title()} Lab",
                TTYD_URL=f"/labs/{name}/c/{uuid}/ttyd/",
                UUID=uuid,
                LAB=name,
                STATION=station,
                PANEL_HTML=wrapper_panel_html,
                PANEL_SCRIPT=panel_script_tag,
                GUIDE_ENABLED="1" if enable_progress else "",
            )
            resp = make_response(html)
            resp.headers["Content-Type"] = "text/html; charset=utf-8"
            resp.set_cookie(
                cookie_name, uuid,
                max_age=cookie_max_age,
                httponly=False,
                samesite="Lax",
                path="/",
            )
            return resp

    # ------------------------------------------------------------------
    # instructor: admin console (HTML)
    # ------------------------------------------------------------------
    @bp.route(f"/labs/{name}/admin", methods=["GET"])
    @require_instructor
    def admin_page():
        html = _ADMIN_TEMPLATE_PATH.read_text(encoding="utf-8")
        html = html.replace("{{LAB_NAME}}", name)
        html = html.replace("{{TITLE}}", f"{name.title()} — Instructor Console")
        href = admin_instructor_href or f"/labs/{name}/instructor/"
        html = html.replace("{{INSTRUCTOR_HREF}}", href)
        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp

    # ------------------------------------------------------------------
    # instructor: claims
    # ------------------------------------------------------------------
    @bp.route(f"{prefix}/claims", methods=["GET"])
    @require_instructor
    def list_claims():
        return jsonify({
            "summary": claim_manager.summary(),
            "claims": claim_manager.list_claims(),
        })

    @bp.route(f"{prefix}/claims/<claim_uuid>", methods=["DELETE"])
    @require_instructor
    def release_claim(claim_uuid: str):
        if not is_valid_uuid(claim_uuid):
            return jsonify({"success": False, "message": "invalid uuid"}), 400
        wipe_param = request.args.get("wipe")
        wipe: bool | None = None
        if wipe_param is not None:
            wipe = wipe_param.lower() in ("1", "true", "yes")
        ok, message = claim_manager.release(claim_uuid, wipe=wipe)
        return jsonify({"success": ok, "message": message}), (200 if ok else 404)

    @bp.route(f"{prefix}/claims/pause", methods=["POST"])
    @require_instructor
    def pause_sweeper():
        claim_manager.pause()
        return jsonify({"success": True, "paused": True})

    @bp.route(f"{prefix}/claims/resume", methods=["POST"])
    @require_instructor
    def resume_sweeper():
        claim_manager.resume()
        return jsonify({"success": True, "paused": False})

    @bp.route(f"{prefix}/claims/policy", methods=["GET"])
    @require_instructor
    def get_policy():
        return jsonify({"policy": claim_manager.get_policy()})

    @bp.route(f"{prefix}/claims/policy", methods=["POST"])
    @require_instructor
    def set_policy():
        data = request.get_json(silent=True) or {}
        policy = data.get("policy", "")
        ok, message = claim_manager.set_policy(policy)
        if ok:
            return jsonify({"success": True, "policy": message})
        return jsonify({"success": False, "message": message}), 400

    @bp.route(f"{prefix}/claims/pool", methods=["GET"])
    @require_instructor
    def get_pool():
        return jsonify({
            "pool_size": claim_manager.get_pool_size(),
            "summary": claim_manager.summary(),
        })

    @bp.route(f"{prefix}/claims/pool", methods=["POST"])
    @require_instructor
    def set_pool():
        data = request.get_json(silent=True) or {}
        size = data.get("size", data.get("pool_size"))
        if size is None:
            return jsonify({"success": False, "message": "missing 'size'"}), 400
        ok, message = claim_manager.set_pool_size(size)
        return jsonify({"success": ok, "message": message}), (200 if ok else 400)

    # ------------------------------------------------------------------
    # instructor: lanes
    # ------------------------------------------------------------------
    @bp.route(f"{prefix}/lanes", methods=["GET"])
    @require_instructor
    def lanes_list():
        return jsonify({"lanes": lane_manager.list_lanes()})

    @bp.route(f"{prefix}/lanes/<lane_id>/start", methods=["POST"])
    @require_instructor
    def lane_start(lane_id: str):
        if not _valid_lane_id(lane_id):
            return jsonify({"success": False, "message": "invalid lane id"}), 400
        ok, msg = lane_manager.start_lane(lane_id)
        return jsonify({"success": ok, "message": msg}), (200 if ok else 400)

    @bp.route(f"{prefix}/lanes/<lane_id>/stop", methods=["POST"])
    @require_instructor
    def lane_stop(lane_id: str):
        if not _valid_lane_id(lane_id):
            return jsonify({"success": False, "message": "invalid lane id"}), 400
        ok, msg = lane_manager.stop_lane(lane_id)
        return jsonify({"success": ok, "message": msg}), (200 if ok else 400)

    @bp.route(f"{prefix}/lanes/<lane_id>/reset", methods=["POST"])
    @require_instructor
    def lane_reset(lane_id: str):
        if not _valid_lane_id(lane_id):
            return jsonify({"success": False, "message": "invalid lane id"}), 400
        ok, msg = lane_manager.reset_lane(lane_id, preserve_state=True)
        return jsonify({"success": ok, "message": msg}), (200 if ok else 400)

    @bp.route(f"{prefix}/lanes/<lane_id>/touch", methods=["POST"])
    def lane_touch(lane_id: str):
        if not _valid_lane_id(lane_id):
            return jsonify({"success": False, "message": "invalid lane id"}), 400
        lane_manager.touch(lane_id)
        return jsonify({"success": True})

    # ------------------------------------------------------------------
    # peer discovery (bitcoin-style shared-static-web labs)
    # ------------------------------------------------------------------
    if enable_peers:

        @bp.route(f"{prefix}/peers", methods=["GET"])
        def peers_list():
            my_uuid = _get_session_uuid()
            return jsonify({"peers": claim_manager.list_peers(exclude_uuid=my_uuid)})

        @bp.route(f"{prefix}/resolve-short", methods=["GET"])
        def resolve_short():
            short = request.headers.get("X-Peer-Short", "").lower()
            if not _SHORT_RE.match(short):
                return Response("invalid short id", status=401)
            station = claim_manager.resolve_short(short)
            if station is None:
                return Response("unknown short id", status=401)
            container = config.container_name_fn(station)
            resp = Response("ok", status=200)
            resp.headers["X-Lane-Host"] = container
            if static_port is not None:
                resp.headers["X-Lane-Port"] = str(static_port)
            return resp

    # ------------------------------------------------------------------
    # exercise catalog + progress (9.3a)
    # ------------------------------------------------------------------
    @bp.route(f"{prefix}/exercises", methods=["GET"])
    def exercises_catalog():
        cat = get_exercise_catalog(name)
        if cat is None:
            return jsonify({"intro": {}, "exercises": []})
        return jsonify(cat)

    if enable_progress:

        @bp.route(f"{prefix}/progress/touch", methods=["POST"])
        def progress_touch():
            uuid = _get_session_uuid()
            if not uuid or not is_valid_uuid(uuid):
                return jsonify({"ok": True, "recorded": False, "reason": "no session"})
            data = request.get_json(silent=True) or {}
            route_id = (data.get("route_id") or "").strip()
            tracker = get_tracker(name)
            if tracker is None or not route_id or not tracker.is_known_route(route_id):
                return jsonify({"ok": False, "recorded": False, "reason": "unknown route"}), 400
            station = claim_manager.resolve(uuid)
            if not station:
                return jsonify({"ok": True, "recorded": False, "reason": "no station"})
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            recorded = tracker.record(
                uuid, route_id, source="client", station=station, meta=meta,
            )
            return jsonify({"ok": True, "recorded": recorded})

        @bp.route(f"{prefix}/progress", methods=["GET"])
        @require_instructor
        def progress_list():
            tracker = get_tracker(name)
            if tracker is None:
                return jsonify({"progress": {}})
            return jsonify({"progress": tracker.all_summaries()})

        @bp.route(f"{prefix}/progress/<claim_uuid>", methods=["GET"])
        @require_instructor
        def progress_detail(claim_uuid: str):
            claim_uuid = (claim_uuid or "").strip().lower()
            if not is_valid_uuid(claim_uuid):
                return jsonify({"success": False, "message": "invalid uuid"}), 400
            tracker = get_tracker(name)
            if tracker is None:
                return jsonify({"success": False, "message": "progress disabled"}), 404
            detail = tracker.detail_for(claim_uuid)
            if detail is None:
                return jsonify({"success": False, "message": "no progress recorded"}), 404
            return jsonify({"success": True, "detail": detail})

    return bp
