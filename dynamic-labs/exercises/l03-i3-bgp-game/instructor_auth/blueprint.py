"""Flask blueprint providing /instructor/login + /instructor/logout in standalone mode.

Not registered in shared mode — the centralized instructor auth service owns those routes.
"""

from __future__ import annotations

from flask import Blueprint, make_response, redirect, render_template_string, request

from .auth import (
    COOKIE_NAME,
    AuthConfig,
    AuthMode,
    issue,
    log_auth_event,
)

_LOGIN_TEMPLATE = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Instructor Login</title>
<style>
body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0;
       display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.card { background: #1e293b; padding: 2rem; border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4); min-width: 320px; }
h1 { margin: 0 0 1rem; font-size: 1.25rem; }
input[type=password] { width: 100%; padding: 0.5rem; background: #0f172a;
       border: 1px solid #334155; color: #e2e8f0; border-radius: 4px; }
button { margin-top: 1rem; padding: 0.5rem 1rem; background: #2563eb;
         color: white; border: 0; border-radius: 4px; cursor: pointer; }
.err { color: #fca5a5; margin-top: 0.5rem; font-size: 0.9rem; }
.ok { color: #86efac; margin-top: 0.5rem; font-size: 0.9rem; }
</style></head>
<body><div class="card">
<h1>Instructor Login</h1>
<form method="post">
<input type="text" name="username" autofocus required placeholder="Username" style="margin-bottom: 0.5rem;">
<input type="password" name="password" required placeholder="Password">
<button type="submit">Sign in</button>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
{% if message %}<div class="ok">{{ message }}</div>{% endif %}
</form></div></body></html>
"""


def standalone_blueprint(config: AuthConfig) -> Blueprint:
    """Return a Flask blueprint with /instructor/login + /logout.

    Only meaningful in standalone mode. Raises in shared mode — callers
    should guard registration with `if config.mode is AuthMode.STANDALONE`.
    """
    if config.mode is not AuthMode.STANDALONE:
        raise RuntimeError(
            "standalone_blueprint() is only valid in standalone mode."
        )

    bp = Blueprint("instructor_auth_standalone", __name__)

    @bp.route("/instructor/login", methods=["GET", "POST"])
    def login():
        error = None
        message = None
        if request.method == "POST":
            submitted = request.form.get("password", "")
            username = (request.form.get("username", "") or "").strip()[:64]
            if _ct_equals(submitted, config.standalone_password or ""):
                resp = make_response(redirect("/instructor/"))
                issue(resp, config, sub=username or "instructor")
                log_auth_event("login", outcome="ok", sub=username)
                return resp
            error = "Invalid credentials"
            log_auth_event("login", outcome="fail", reason="bad_password", sub=username)
        elif request.args.get("msg") == "logged_out":
            message = "You have been logged out."
        return render_template_string(_LOGIN_TEMPLATE, error=error, message=message)

    @bp.route("/instructor/logout", methods=["GET", "POST"])
    def logout():
        resp = make_response(redirect("/instructor/login?msg=logged_out"))
        resp.delete_cookie(COOKIE_NAME, path="/")
        log_auth_event("logout", outcome="ok")
        return resp

    return bp


def _ct_equals(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= ord(x) ^ ord(y)
    return diff == 0
