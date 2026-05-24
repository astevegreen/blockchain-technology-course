"""
Phase 7.3½b — Flask routes for session claim lifecycle.

Student-facing:
  GET  /api/hlf/claim           → claim or resume, set cookie, 302 to lane UI
  POST /api/hlf/claims/heartbeat → touch last_active for the cookie's session

Instructor-facing:
  GET    /api/hlf/claims                  → list + summary
  DELETE /api/hlf/claims/<uuid>           → force release (honors ?wipe=1)
  POST   /api/hlf/claims/pause            → freeze idle sweeper
  POST   /api/hlf/claims/resume           → resume sweeper
  GET    /api/hlf/claims/policy           → {policy}
  POST   /api/hlf/claims/policy           → body {"policy":"sticky"|"wipe"}

Cookie name: hlf_session. The UUID also appears in the URL
(/labs/hlf/c/<uuid>/...) so students can resume across devices.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, redirect, request

from claims import get_claim_manager, is_valid_uuid
from shared_auth import is_authenticated, require_instructor

claim_bp = Blueprint("claim", __name__)

COOKIE_NAME = "hlf_session"
COOKIE_MAX_AGE = 60 * 60 * 12  # 12 hours; idle sweeper is the real gate

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
  <p>All available workstations for the Hyperledger Fabric lab are currently in use.</p>
  <p class="meta">Claimed: CLAIMED_COUNT / TOTAL_COUNT workstations</p>
  <div class="hint">
    Please wait for a workstation to free up, or ask the instructor to release an active claim from the instructor console.
  </div>
</div>
"""


def _claim_unavailable_response(message: str, summary: dict):
    user_message = (
        "No available workstations for the Hyperledger Fabric lab. "
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
            .replace("CLAIMED_COUNT", str(summary.get("claimed", "?")))
            .replace("TOTAL_COUNT", str(summary.get("total_stations", "?")))
        )
        resp = make_response(html, 503)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp
    return jsonify(payload), 503


@claim_bp.route("/api/hlf/claim", methods=["GET"])
def claim_station():
    """Claim a station (or resume an existing claim) and redirect.

    If the caller already carries a valid hlf_session cookie or
    ?session=<uuid>, we resume that station. Otherwise we mint a new
    UUID and assign the lowest-numbered free station.

    Instructors hitting this endpoint (e.g. stale cookie from a prior
    session) get a fresh claim rather than an error — the claim is
    harmless and lets them see the student experience.
    """
    mgr = get_claim_manager()
    existing = request.cookies.get(COOKIE_NAME) or request.args.get("session")
    if existing and not is_valid_uuid(existing):
        existing = None
    uuid, station, message = mgr.claim(existing_uuid=existing)
    if uuid is None:
        return _claim_unavailable_response(message, mgr.summary())
    # Warm explorer/chaincode caches in the background so the first
    # click into the explorer doesn't wait on 12 serial peer CLI calls.
    # Import lazily to avoid a circular import at module load.
    try:
        from hlf_service import get_service  # type: ignore
        get_service().warm_explorer_caches()
    except Exception:
        pass
    # Redirect to the per-session lane surface. Nginx maps /c/<uuid>/*
    # to the runner with X-HLF-Session injected.
    resp = make_response(redirect(f"/labs/hlf/c/{uuid}/", code=302))
    resp.set_cookie(
        COOKIE_NAME,
        uuid,
        max_age=COOKIE_MAX_AGE,
        httponly=False,  # JS heartbeat reads it
        samesite="Lax",
        path="/",
    )
    return resp


@claim_bp.route("/api/hlf/claims/active", methods=["GET"])
def active_claims():
    """List of currently-claimed stations, for session-authenticated
    clients. Returns just the station ids + derived MSP ids — no uuids,
    no last_active timestamps, nothing a classmate could use to hijack
    another lane. This is the data the governance page uses to hide
    unclaimed student orgs.

    Gate: caller must present a valid session (cookie or
    X-HLF-Session header). That's the same "is this actually a student
    in the lab" check heartbeat uses. Instructor credentials are also
    accepted but not required.
    """
    mgr = get_claim_manager()
    uuid = (
        request.headers.get("X-HLF-Session")
        or request.cookies.get(COOKIE_NAME)
        or request.args.get("session")
    )
    session_ok = bool(uuid and is_valid_uuid(uuid) and mgr.touch(uuid))
    if not session_ok:
        # Fall back to instructor cookie: the instructor console's
        # governance view should also get the filtered list.
        if not is_authenticated():
            return jsonify({"ok": False, "message": "no session"}), 401

    claimed_stations = sorted(c["station"] for c in mgr.list_claims())
    # Station s07 → Student07MSP. Keeping the mapping server-side means
    # the UI doesn't need to know the naming convention.
    claimed_msps = [
        f"Student{station[1:]}MSP" for station in claimed_stations
    ]
    return jsonify({
        "ok": True,
        "claimed_stations": claimed_stations,
        "claimed_msps": claimed_msps,
    })


@claim_bp.route("/api/hlf/claims/heartbeat", methods=["POST"])
def heartbeat():
    mgr = get_claim_manager()
    uuid = (
        request.headers.get("X-HLF-Session")
        or request.cookies.get(COOKIE_NAME)
        or (request.get_json(silent=True) or {}).get("session")
    )
    if not uuid or not is_valid_uuid(uuid):
        return jsonify({"ok": False, "message": "no session"}), 400
    if mgr.touch(uuid):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "message": "unknown session"}), 404


# ----------------------------------------------------------------------
# instructor endpoints
# ----------------------------------------------------------------------
@claim_bp.route("/api/hlf/claims", methods=["GET"])
@require_instructor
def list_claims():
    mgr = get_claim_manager()
    return jsonify({
        "summary": mgr.summary(),
        "claims": mgr.list_claims(),
    })


@claim_bp.route("/api/hlf/claims/<uuid>", methods=["DELETE"])
@require_instructor
def release_claim(uuid: str):
    if not is_valid_uuid(uuid):
        return jsonify({"success": False, "message": "invalid uuid"}), 400
    wipe_param = request.args.get("wipe")
    wipe: bool | None
    if wipe_param is None:
        wipe = None
    else:
        wipe = wipe_param.lower() in ("1", "true", "yes")
    mgr = get_claim_manager()
    ok, message = mgr.release(uuid, wipe=wipe)
    return jsonify({"success": ok, "message": message}), (200 if ok else 404)


@claim_bp.route("/api/hlf/claims/pause", methods=["POST"])
@require_instructor
def pause_sweeper():
    get_claim_manager().pause()
    return jsonify({"success": True, "paused": True})


@claim_bp.route("/api/hlf/claims/resume", methods=["POST"])
@require_instructor
def resume_sweeper():
    get_claim_manager().resume()
    return jsonify({"success": True, "paused": False})


@claim_bp.route("/api/hlf/claims/policy", methods=["GET"])
@require_instructor
def get_policy():
    return jsonify({"policy": get_claim_manager().get_policy()})


@claim_bp.route("/api/hlf/claims/pool", methods=["GET"])
@require_instructor
def get_pool():
    mgr = get_claim_manager()
    return jsonify({
        "pool_size": mgr.get_pool_size(),
        "summary": mgr.summary(),
    })


@claim_bp.route("/api/hlf/claims/pool", methods=["POST"])
@require_instructor
def set_pool():
    data = request.get_json(silent=True) or {}
    size = data.get("size", data.get("pool_size"))
    if size is None:
        return jsonify({"success": False, "message": "missing 'size'"}), 400
    ok, message = get_claim_manager().set_pool_size(size)
    status = 200 if ok else 400
    return jsonify({"success": ok, "message": message}), status


@claim_bp.route("/api/hlf/claims/policy", methods=["POST"])
@require_instructor
def set_policy():
    data = request.get_json(silent=True) or {}
    policy = data.get("policy", "")
    ok, message = get_claim_manager().set_policy(policy)
    if ok:
        return jsonify({"success": True, "policy": message})
    return jsonify({"success": False, "message": message}), 400
