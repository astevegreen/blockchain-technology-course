"""Lab hosting: /instructor/hosting shows each lab's status, with Start and Stop buttons.

Every button is a POST behind the instructor login and the engine's CSRF check (app/auth.py). The page never runs
anything itself: it asks the host-side runner (app/hosting_runner.py), which runs `lab-manager.sh` for an allowlist
of verbs and labs. Why a runner and not the Docker socket: README.md, "Lab hosting".
"""

import os
import re

from flask import Blueprint, current_app, redirect, request, url_for

from .. import hosting_runner
from ..auth import instructor_required
from ..theme import render_themed_template as render_template_string

bp = Blueprint("hosting", __name__, url_prefix="/instructor/hosting")

DEFAULT_SOCKET = "/run/hosting-runner/runner.sock"
STATUS_HEADER = re.compile(r"^=== (?P<name>[a-z0-9-]+) ===$")
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
# The run sheet's cold start ("Before day 1"), from dynamic-labs/ on the lab host.
COLD_START = (
    "./lab-manager.sh deploy --mode instructor --max-student-capacity 20",
    "./lab-manager.sh start quiz-engine-v2",
)


def _setting(name, env_name, default=""):
    value = current_app.config.get(name)
    if value:
        return value
    return os.environ.get(env_name, default)


def call_runner(payload):
    """Send one request to the runner with the shared secret. Tests replace this function."""
    secret = _setting("HOSTING_RUNNER_SECRET", "QUIZ_ENGINE_HOSTING_RUNNER_SECRET")
    if not secret:
        raise hosting_runner.RunnerUnavailable(
            "the quiz engine has no HOSTING_RUNNER_SECRET: start it with ./lab-manager.sh start quiz-engine-v2"
        )
    socket_path = _setting("HOSTING_RUNNER_SOCKET", "QUIZ_ENGINE_HOSTING_RUNNER_SOCKET", DEFAULT_SOCKET)
    return hosting_runner.call(socket_path, dict(payload, secret=secret))


def status_sections(output):
    """Split `lab-manager.sh status all` output into {lab: lines of its `docker compose ps`}."""
    sections, current = {}, None
    for line in ANSI.sub("", output or "").splitlines():
        match = STATUS_HEADER.match(line.strip())
        if match:
            current = match.group("name")
            sections[current] = []
        elif current is not None and line.strip():
            sections[current].append(line)
    return sections


def summarize(lines):
    """'running (N containers)' or 'not running', from a section's lines: the first is compose's header row."""
    if lines is None:
        return "not checked"
    rows = [line for line in lines[1:] if not line.startswith(("WARN", "time="))] if lines else []
    if lines and not lines[0].startswith("NAME"):
        return "could not read"
    if not rows:
        return "not running"
    return f"running ({len(rows)} container{'s' if len(rows) != 1 else ''})"


HOSTING_TEMPLATE = """
<!doctype html>
<title>Lab Hosting</title>
{% if state and state.running %}<meta http-equiv="refresh" content="5">{% endif %}
<main>
  <h1>Lab hosting</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  <p>Each button runs <code>./lab-manager.sh</code> on the lab host, as you would at its shell, and shows what it
  printed. One command runs at a time; a start or stop is followed by a status check.</p>
  <p><strong>Starting from cold is not on this page.</strong> This page is part of the quiz engine, which runs only
  while the labs are hosted. To start from nothing, on the lab host from <code>dynamic-labs/</code>
  (run sheet, <code>quizes/run-sheet/RUN_SHEET.md</code>, "Before day 1"):</p>
  <pre>{% for line in cold_start %}{{ line }}
{% endfor %}</pre>
  <p>Deploy is once per machine; the start brings up the quiz engine and this page.</p>

  {% if error %}
    <h2>The hosting runner is not answering</h2>
    <p role="alert">{{ error }}</p>
    <p>The runner starts with <code>./lab-manager.sh start quiz-engine-v2</code> and logs to
    <code>dynamic-labs/.runtime/hosting-runner/runner.log</code>. Until it answers, use the same commands at the
    host's shell: <code>./lab-manager.sh start &lt;lab&gt;</code>, <code>stop &lt;lab&gt;</code>,
    <code>status all</code>.</p>
  {% else %}
    {% if state.running %}
      <h2>Running now</h2>
      <p><code>{{ state.running.command }}</code>, started {{ state.running.started }}. This page refreshes every
      5 seconds until it finishes.</p>
      <pre>{{ state.running.output }}</pre>
    {% endif %}

    <h2>All labs</h2>
    <form method="post" action="{{ url_for('hosting.run') }}">
      <input type="hidden" name="verb" value="start"><input type="hidden" name="target" value="all">
      <button type="submit" {% if state.running %}disabled{% endif %}>Start all</button>
    </form>
    <form method="post" action="{{ url_for('hosting.run') }}">
      <input type="hidden" name="verb" value="status"><input type="hidden" name="target" value="all">
      <button type="submit" {% if state.running %}disabled{% endif %}>Check status</button>
    </form>
    <form method="post" action="{{ url_for('hosting.run') }}">
      <input type="hidden" name="verb" value="stop"><input type="hidden" name="target" value="all">
      <label><input type="checkbox" name="confirm" value="yes" required>
        Stop all also stops the quiz engine and this page; start them again from the host</label>
      <button type="submit" {% if state.running %}disabled{% endif %}>Stop all</button>
    </form>

    <h2>Labs</h2>
    {% if state.last_status %}
      <p>Status as of {{ state.last_status.finished or state.last_status.started }}.</p>
    {% else %}
      <p>No status read yet: press Check status.</p>
    {% endif %}
    <table>
      <thead><tr><th>Lab</th><th>Status</th><th></th><th></th></tr></thead>
      <tbody>
      {% for lab in state.labs %}
        <tr>
          <td>{{ lab }}</td>
          <td>{{ summaries[lab] }}</td>
          <td><form method="post" action="{{ url_for('hosting.run') }}">
            <input type="hidden" name="verb" value="start"><input type="hidden" name="target" value="{{ lab }}">
            <button type="submit" {% if state.running %}disabled{% endif %}>Start</button></form></td>
          <td><form method="post" action="{{ url_for('hosting.run') }}">
            <input type="hidden" name="verb" value="stop"><input type="hidden" name="target" value="{{ lab }}">
            <button type="submit" {% if state.running %}disabled{% endif %}>Stop</button></form></td>
        </tr>
      {% endfor %}
      </tbody>
    </table>

    <h2>Shared services</h2>
    <p>Started with every lab (or, for the quiz engine, from the host), so they have no buttons here.</p>
    <ul>
      {% for name in state.no_buttons %}<li>{{ name }}: {{ summaries[name] }}</li>{% endfor %}
    </ul>

    {% if state.last_action %}
      <h2>Last command</h2>
      <p><code>{{ state.last_action.command }}</code>, started {{ state.last_action.started }},
      {% if state.last_action.exit_code == 0 %}finished without error{% else %}ended with exit code
      {{ state.last_action.exit_code }}{% endif %}
      at {{ state.last_action.finished }}.</p>
      <pre>{{ state.last_action.output }}</pre>
    {% endif %}
    {% if state.last_status %}
      <details>
        <summary>Full status output</summary>
        <pre>{{ state.last_status.output }}</pre>
      </details>
    {% endif %}
  {% endif %}
</main>
"""


@bp.get("")
@bp.get("/")
@instructor_required
def hosting_page():
    error, state = None, None
    try:
        state = call_runner({"action": "state"})
        if not state.get("ok"):
            error, state = f"The runner refused: {state.get('error', 'no reason given')}", None
    except hosting_runner.RunnerUnavailable as exc:
        error = str(exc)
    summaries = {}
    if state:
        last = state.get("last_status") or {}
        sections = status_sections(last.get("output", "")) if last else {}
        for name in [*state.get("labs", []), *state.get("no_buttons", [])]:
            summaries[name] = summarize(sections.get(name)) if last else "not checked"
        for key in ("running", "last_action", "last_status"):
            if state.get(key):
                state[key]["output"] = ANSI.sub("", state[key].get("output", ""))
    return render_template_string(
        HOSTING_TEMPLATE,
        state=state,
        error=error,
        summaries=summaries,
        message=request.args.get("message"),
        cold_start=COLD_START,
    )


@bp.post("/run")
@instructor_required
def run():
    verb = request.form.get("verb", "")
    target = request.form.get("target", "")
    if verb == "stop" and target == "all" and request.form.get("confirm") != "yes":
        return _back("Stop all was not run: tick the box to confirm it.")
    if hosting_runner.refusal(verb, target, [target]) is not None:
        return _back("That is not a hosting command this page runs.")
    try:
        answer = call_runner({"action": "run", "verb": verb, "target": target})
    except hosting_runner.RunnerUnavailable as exc:
        return _back(f"Not run: {exc}")
    if not answer.get("ok"):
        return _back(f"Not run: {answer.get('error', 'the runner refused')}")
    return _back(f"Started ./lab-manager.sh {verb} {target}.")


def _back(message):
    return redirect(url_for("hosting.hosting_page", message=message))
