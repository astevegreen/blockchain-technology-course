"""The instructor's course dashboard: one page of links and buttons for running the course.

Owner, 12 Nov 2026: "It does not need to be fancy, but links and buttons to run scripts
would be helpful." The page links to the engine's own instructor pages, the run sheet and
the lab hosting and pretest pages, shows the class code, and loads the course's quiz banks
from the `quizes/` folder mounted read-only into the engine (`QUIZ_ENGINE_QUIZES_DIR`,
default `/quizes`), so nobody edits or uploads JSON by hand.

The pretest is not loaded here: students take it on the public course site, so their
access does not depend on the lab host (docs/build-spec.md, "Instructor dashboard").
"""

import os
from pathlib import Path

from flask import Blueprint, Response, current_app, request, url_for
from werkzeug.routing import BuildError

from ..auth import current_instructor, instructor_required
from ..ingest import IngestError, ingest_json
from ..theme import render_themed_template as render_template_string

bp = Blueprint("dashboard", __name__, url_prefix="/instructor/dashboard")

DEFAULT_QUIZES_DIR = "/quizes"

# Each group is a set of buttons: one per bank, plus one that loads the whole group.
# Patterns are relative to the quizes folder; a bank is only ever loaded if it matches one.
BANK_GROUPS = (
    ("daily", "Daily quizzes (08:45, days 2 to 9)", ("quiz_json/daily_*-quiz-bank.json",)),
    ("checks", "Week checks (day 5 and day 10)", ("quiz_json/week*_check-quiz-bank.json",)),
    ("posttest", "Post-test (day 10)", ("posttest/*-quiz-bank.json",)),
    ("labs", "Lab quizzes", ("quiz_json/lab_*-quiz-bank.json",)),
    (
        "lessons",
        "Lesson banks (the question pool quizzes are generated from)",
        ("quiz_json/*-quiz-bank.json",),
    ),
)

DASHBOARD_TEMPLATE = """
<!doctype html>
<title>Run the course</title>
<main>
  <h1>Run the course</h1>
  <p>Everything an instructor does to run a class day, in one place.</p>

  {% if load_results %}
  <section aria-labelledby="load-result">
    <h2 id="load-result">Load result</h2>
    <ul>
    {% for item in load_results %}
      <li><strong>{{ item.path }}</strong>: {{ item.message }}</li>
    {% endfor %}
    </ul>
  </section>
  {% endif %}

  <section aria-labelledby="links">
    <h2 id="links">Pages</h2>
    <ul>
    {% for label, href, note in links %}
      <li>{% if href %}<a href="{{ href }}">{{ label }}</a>{% else %}{{ label }}: not built yet{% endif %}
        {% if note %}<br><small>{{ note }}</small>{% endif %}</li>
    {% endfor %}
    </ul>
  </section>

  <section aria-labelledby="class-code">
    <h2 id="class-code">Class code</h2>
    <p>Students type this before any lab page when the class gate is on.</p>
    <p><strong id="class-code-value">Open the instructor portal at /instructor/ to see it.</strong></p>
  </section>

  <section aria-labelledby="banks">
    <h2 id="banks">Load quiz banks</h2>
    {% if not quizes_found %}
    <p>The quizzes folder is not mounted at <code>{{ quizes_dir }}</code>, so there is nothing to load.
      Start the engine with <code>./lab-manager.sh start quiz-engine-v2</code>, which mounts it.</p>
    {% else %}
    <p>Loading a bank again is safe; the result shows what each load did.</p>
    {% for group in groups %}
    <h3>{{ group.title }}</h3>
    {% if group.banks %}
    <form method="post" action="{{ load_url }}">
      <button type="submit" name="group" value="{{ group.key }}">Load all {{ group.banks|length }}</button>
    </form>
    <form method="post" action="{{ load_url }}">
      <ul>
      {% for bank in group.banks %}
        <li><button type="submit" name="bank" value="{{ bank }}">Load</button> {{ bank }}</li>
      {% endfor %}
      </ul>
    </form>
    {% else %}
    <p>No banks found.</p>
    {% endif %}
    {% endfor %}
    {% endif %}
  </section>
</main>
<script>
  fetch('/api/instructor/class-code', {credentials: 'same-origin'})
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      if (!data || !data.code) { return; }
      var text = data.code + (data.gate_on ? ' (gate on)' : ' (gate off: students do not need it)');
      document.getElementById('class-code-value').textContent = text;
    })
    .catch(function () {});
</script>
"""


def _quizes_dir():
    configured = current_app.config.get("QUIZES_DIR") or os.environ.get(
        "QUIZ_ENGINE_QUIZES_DIR", DEFAULT_QUIZES_DIR
    )
    return Path(configured)


def _bank_groups(quizes_dir):
    """Each group's banks as paths relative to the quizes folder; a bank sits in its first group only."""
    claimed = set()
    groups = []
    for key, title, patterns in BANK_GROUPS:
        banks = []
        for pattern in patterns:
            for path in sorted(quizes_dir.glob(pattern)):
                relative = path.relative_to(quizes_dir).as_posix()
                if path.is_file() and relative not in claimed:
                    claimed.add(relative)
                    banks.append(relative)
        groups.append({"key": key, "title": title, "banks": banks})
    return groups


def _url_or_none(endpoint):
    try:
        return url_for(endpoint)
    except BuildError:
        return None


def _links():
    return [
        ("Run sheet", url_for("dashboard.run_sheet"), "The day-by-day timetable and what to load when."),
        (
            "Lab hosting",
            _url_or_none("hosting.hosting_page"),
            "Start, stop and check the labs and the quiz engine.",
        ),
        (
            "Pretest results",
            _url_or_none("pretest.pretest_page"),
            "Load the pretest marker's results and see each student's lab start points.",
        ),
        (
            "Marking",
            _url_or_none("marking.marking_page"),
            "Mark the post-test's written items and the four graded lab points; see who has the certificate.",
        ),
        ("Quiz engine home", url_for("instructor.instructor_dashboard"), None),
        ("Upload a quiz bank by hand", url_for("instructor.ingest_form"), None),
        ("Quiz templates and generated quizzes", url_for("instructor.template_list"), None),
        ("Grading queue", url_for("instructor.grading_queue"), None),
        ("Results and metrics", url_for("instructor.metrics_dashboard"), None),
        ("Roster codes", url_for("instructor.roster_codes"), None),
        ("Instructor portal (labs, class code)", "/instructor/", None),
    ]


def _render(load_results=None, status=200):
    quizes_dir = _quizes_dir()
    quizes_found = quizes_dir.is_dir()
    return (
        render_template_string(
            DASHBOARD_TEMPLATE,
            links=_links(),
            groups=_bank_groups(quizes_dir) if quizes_found else [],
            quizes_found=quizes_found,
            quizes_dir=str(quizes_dir),
            load_url=url_for("dashboard.load_banks"),
            load_results=load_results,
        ),
        status,
    )


@bp.get("")
@bp.get("/")
@instructor_required
def course_dashboard():
    return _render()


@bp.get("/run-sheet")
@instructor_required
def run_sheet():
    path = _quizes_dir() / "run-sheet" / "RUN_SHEET.md"
    if not path.is_file():
        return Response("The run sheet is not mounted.\n", status=404, mimetype="text/plain")
    return Response(path.read_text(encoding="utf-8"), mimetype="text/plain")


def _load_one(quizes_dir, relative):
    try:
        raw_json = (quizes_dir / relative).read_text(encoding="utf-8")
        result = ingest_json(
            raw_json,
            filename=relative,
            actor_sub=current_instructor().subject,
        )
    except (OSError, UnicodeDecodeError) as exc:
        return {"path": relative, "ok": False, "message": f"could not read it ({exc.__class__.__name__})"}
    except IngestError as exc:
        return {"path": relative, "ok": False, "message": f"not loaded: {exc}"}
    errors = [bank.error for bank in result.bank_results if bank.error]
    message = f"{result.status}, {result.successes} bank(s) loaded, {result.failures} failed"
    if errors:
        message += " (" + "; ".join(errors) + ")"
    return {"path": relative, "ok": bool(result.successes), "message": message}


@bp.post("/load")
@instructor_required
def load_banks():
    quizes_dir = _quizes_dir()
    if not quizes_dir.is_dir():
        return _render([{"path": str(quizes_dir), "message": "the quizzes folder is not mounted"}], 400)
    groups = _bank_groups(quizes_dir)
    wanted_group = request.form.get("group", "")
    wanted_bank = request.form.get("bank", "")
    if wanted_group:
        selected = next((g["banks"] for g in groups if g["key"] == wanted_group), [])
    else:
        # Only a bank the page offered: the form value is never used as a path on its own.
        offered = {bank for g in groups for bank in g["banks"]}
        selected = [wanted_bank] if wanted_bank in offered else []
    if not selected:
        return _render([{"path": wanted_bank or wanted_group or "(nothing)", "message": "not a bank this page offers"}], 400)
    results = [_load_one(quizes_dir, relative) for relative in selected]
    status = 200 if any(item["ok"] for item in results) else 400
    return _render(results, status)
