"""
HLF Lab API routes.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote as urlquote

import markdown
from flask import Blueprint, Response, abort, jsonify, redirect, request
from markupsafe import escape as html_escape

from hlf_service import HLFLabService
from lanes import get_lane_manager
from shared_auth import require_instructor
from student_context import get_student_context, templatize

hlf_bp = Blueprint("hlf", __name__)
_service: HLFLabService | None = None

_VALID_TX_ID = re.compile(r"^[0-9a-fA-F]{64}$")
_VALID_ASSET_ID = re.compile(r"^[a-zA-Z0-9_.\-]{1,128}$")


def get_service() -> HLFLabService:
    global _service
    if _service is None:
        _service = HLFLabService()
    return _service


@hlf_bp.route("/admin", methods=["GET"])
def hlf_admin_redirect():
    return redirect("/labs/hlf/instructor/", code=302)


@hlf_bp.route("/api/hlf/status", methods=["GET"])
def hlf_status():
    return jsonify(get_service().get_network_status())


@hlf_bp.route("/api/hlf/health", methods=["GET"])
def hlf_health():
    return jsonify(get_service().get_health_status())


@hlf_bp.route("/api/hlf/start", methods=["POST"])
@require_instructor
def hlf_start():
    success, message = get_service().start_network()
    return jsonify({"success": success, "message": message})


@hlf_bp.route("/api/hlf/stop", methods=["POST"])
@require_instructor
def hlf_stop():
    success, message = get_service().stop_network()
    return jsonify({"success": success, "message": message})


@hlf_bp.route("/api/hlf/reset", methods=["POST"])
@require_instructor
def hlf_reset():
    success, message = get_service().reset_network()
    return jsonify({"success": success, "message": message})


@hlf_bp.route("/api/hlf/lifecycle-log", methods=["GET"])
@require_instructor
def hlf_lifecycle_log():
    cursor = request.args.get("cursor", default=0, type=int)
    return jsonify(get_service().get_lifecycle_log(cursor))


@hlf_bp.route("/api/hlf/cancel", methods=["POST"])
@require_instructor
def hlf_cancel():
    success, message = get_service().cancel_lifecycle()
    return jsonify({"success": success, "message": message})


@hlf_bp.route("/api/hlf/execute", methods=["POST"])
@require_instructor
def hlf_execute():
    # Accept only structured input. Free-form `command` strings are
    # rejected explicitly so no legacy caller silently slips through
    # the eval-based path (which is now internal-only).
    data = request.get_json(force=True) or {}
    if "command" in data:
        return jsonify({
            "exit_code": 2,
            "stdout": "",
            "stderr": "Rejected: 'command' is no longer accepted; send {verb, action, args, org}.",
        }), 400
    verb = data.get("verb", "")
    action = data.get("action", "")
    args = data.get("args", []) or []
    org = data.get("org", "org1")
    if not isinstance(args, list):
        return jsonify({
            "exit_code": 2, "stdout": "",
            "stderr": "Rejected: 'args' must be a JSON array of strings.",
        }), 400
    exit_code, stdout, stderr = get_service().execute_structured(verb, action, args, org=org)
    return jsonify({
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    })


@hlf_bp.route("/api/hlf/guide", methods=["GET"])
def hlf_guide():
    docs_dir = Path(__file__).resolve().parent.parent / "docs"
    guide_md = docs_dir / "STUDENT_GUIDE.md"
    guide_html = docs_dir / "STUDENT_GUIDE.html"
    if guide_md.exists():
        md_content = guide_md.read_text(encoding="utf-8")
        # Strip YAML frontmatter (between leading --- fences) so it does not render as content.
        if md_content.startswith("---"):
            closing = md_content.find("\n---", 3)
            if closing != -1:
                md_content = md_content[closing + 4 :].lstrip("\n")
        html_content = markdown.markdown(md_content, extensions=["fenced_code", "tables", "codehilite"])
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HLF Lab - Student Guide</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; background: #0b0d10; color: #edf2f7; }}
    a {{ color: #d7e6f7; }}
    code {{ background: #151a20; padding: 2px 6px; border-radius: 3px; color: #d7e6f7; }}
    pre {{ background: #151a20; padding: 15px; border-radius: 0; overflow-x: auto; border: 1px solid #242c35; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
    th, td {{ border: 1px solid #242c35; padding: 12px; text-align: left; }}
    th {{ background-color: #1a2734; color: #d7e6f7; }}
    hr {{ border: none; border-top: 1px solid #242c35; margin: 24px 0; }}
  </style>
</head>
<body>
{html_content}
</body>
</html>"""
        return full_html, 200, {"Content-Type": "text/html"}
    if guide_html.exists():
        return guide_html.read_text(encoding="utf-8"), 200, {"Content-Type": "text/html"}
    return jsonify({"error": "Student guide not found"}), 404


@hlf_bp.route("/api/hlf/explorer", methods=["GET"])
def hlf_explorer():
    return jsonify(get_service().get_explorer_snapshot())


@hlf_bp.route("/api/hlf/explorer-view", methods=["GET"])
def hlf_explorer_view():
    return jsonify(get_service().get_explorer_view())


@hlf_bp.route("/api/hlf/transactions/<tx_id>", methods=["GET"])
def hlf_transaction_detail(tx_id: str):
    if not _VALID_TX_ID.match(tx_id):
        abort(400, description="tx_id must be a 64-character hex string")
    return jsonify(get_service().get_transaction_detail(tx_id))


@hlf_bp.route("/api/hlf/assets/<asset_id>", methods=["GET"])
def hlf_asset_provenance(asset_id: str):
    if not _VALID_ASSET_ID.match(asset_id):
        abort(400, description="asset_id must be alphanumeric (max 128 chars)")
    return jsonify(get_service().get_asset_provenance(asset_id))


@hlf_bp.route("/api/hlf/chaincode", methods=["GET"])
def hlf_chaincode_detail():
    return jsonify(get_service().get_chaincode_detail())


@hlf_bp.route("/api/hlf/chaincode/source", methods=["GET"])
def hlf_chaincode_source():
    return jsonify(get_service().get_chaincode_source())


@hlf_bp.route("/api/hlf/governance", methods=["GET"])
def hlf_governance_detail():
    return jsonify(get_service().get_governance_detail())


@hlf_bp.route("/api/hlf/logs", methods=["GET"])
def hlf_recent_logs():
    lines = request.args.get("lines", default=15, type=int)
    return jsonify(get_service().get_recent_logs(lines))


@hlf_bp.route("/api/hlf/instructor-snapshot", methods=["GET"])
@require_instructor
def hlf_instructor_snapshot():
    lines = request.args.get("lines", default=15, type=int)
    return jsonify(get_service().get_instructor_snapshot(lines))


@hlf_bp.route("/api/hlf/logs/download", methods=["GET"])
def hlf_logs_download():
    payload = get_service().get_full_logs_text()
    return Response(
        payload,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=hlf-network-logs.txt"},
    )


@hlf_bp.route("/api/hlf/exercises", methods=["GET"])
def hlf_exercises():
    ctx = get_student_context()
    catalog = get_service().get_exercise_catalog()
    # Apply per-student token substitution (safe no-op for preview
    # requests — unknown sids fall through to neutral defaults).
    catalog = templatize(catalog, ctx)
    # Rewrite embedded "/labs/hlf" hrefs so a student in a lane sees
    # /labs/hlf/s/<id>/... links throughout the UI. The raw catalog is
    # cached with the generic prefix; this keeps the cache key-free.
    if ctx.get("is_student") and ctx.get("base_prefix"):
        catalog = _retarget_hrefs(catalog, "/labs/hlf", ctx["base_prefix"])
    # Let the UI key off the resolved context (banner / linkouts).
    catalog["student_context"] = ctx
    return jsonify(catalog)


def _retarget_hrefs(value, old_prefix: str, new_prefix: str):
    if isinstance(value, str):
        # Only rewrite values that look like site-relative hrefs starting
        # with the old prefix. Avoid rewriting prose text that happens to
        # mention "/labs/hlf".
        if value == old_prefix or value.startswith(old_prefix + "/"):
            return new_prefix + value[len(old_prefix):]
        return value
    if isinstance(value, list):
        return [_retarget_hrefs(v, old_prefix, new_prefix) for v in value]
    if isinstance(value, dict):
        return {k: _retarget_hrefs(v, old_prefix, new_prefix) for k, v in value.items()}
    return value


@hlf_bp.route("/api/hlf/term-redirect", methods=["GET"],
              defaults={"rest": ""}, strict_slashes=False)
@hlf_bp.route("/api/hlf/term-redirect/<path:rest>", methods=["GET"])
def hlf_term_redirect(rest: str):
    """Phase 7.4 — render a full-viewport iframe wrapping ttyd.

    Nginx can proxy ttyd by station port (77NN) but not by session UUID
    — port arithmetic can only run against a captured $nn. Rather than
    redirect and leak the station ID in the URL, we render a tiny HTML
    shell whose single <iframe> src is the station URL. The browser's
    address bar stays at /labs/hlf/c/<uuid>/term/ and the station ID
    only appears if someone inspects the DOM.
    """
    ctx = get_student_context()
    sid = ctx.get("student_id")
    if not ctx.get("is_student") or not sid:
        return redirect("/labs/hlf/claim")
    # Build the inner path. Station id is controlled (s01..sNN) but rest
    # comes from the URL so it needs path-quoting; the whole thing also
    # gets HTML-escaped before embedding as an attribute value.
    inner_path = f"/labs/hlf/s/{sid}/term/"
    if rest:
        inner_path += urlquote(rest, safe="/")
    qs = request.query_string.decode() if request.query_string else ""
    if qs:
        inner_path += f"?{qs}"
    iframe_src = html_escape(inner_path)
    html = (
        "<!doctype html>"
        "<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>Console</title>"
        "<meta name=\"referrer\" content=\"same-origin\">"
        "<style>"
        "html,body{margin:0;padding:0;height:100%;width:100%;"
        "background:#000;overflow:hidden}"
        "iframe{border:0;width:100%;height:100vh;display:block}"
        "</style></head><body>"
        f"<iframe src=\"{iframe_src}\" "
        "allow=\"clipboard-read; clipboard-write\" "
        "title=\"Console\"></iframe>"
        "</body></html>"
    )
    # Flask appends "; charset=utf-8" automatically to text/html.
    return Response(html, mimetype="text/html")


@hlf_bp.route("/api/hlf/my-term", methods=["GET"])
def hlf_my_term():
    ctx = get_student_context()
    sid = ctx.get("student_id")
    if not ctx.get("is_student") or not sid:
        return jsonify({"error": "no station"}), 404
    lane_start = {"success": False, "message": "not attempted"}
    try:
        ok, message = get_lane_manager().start_lane(sid)
        lane_start = {"success": bool(ok), "message": message}
    except Exception as exc:  # noqa: BLE001 - keep session resume tolerant
        lane_start = {"success": False, "message": str(exc)[:300] or "lane start raised"}
    return jsonify({
        "url": f"/labs/hlf/s/{sid}/term/",
        "lane_start": lane_start,
    })


@hlf_bp.route("/api/hlf/node-context", methods=["GET"])
def hlf_node_context():
    node = request.args.get("node", "org1")
    return jsonify(get_service().get_node_console_context(node))


@hlf_bp.route("/api/hlf/fault", methods=["POST"])
@require_instructor
def hlf_fault():
    data = request.get_json(force=True)
    target = data.get("target", "")
    action = data.get("action", "")
    success, message = get_service().apply_fault_action(target, action)
    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message}), status_code


@hlf_bp.route("/api/hlf/seed", methods=["POST"])
@require_instructor
def hlf_seed():
    data = request.get_json(force=True) if request.data else {}
    preset = data.get("preset", "sample")
    success, message, details = get_service().seed_transactions(preset)
    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message, "details": details}), status_code
