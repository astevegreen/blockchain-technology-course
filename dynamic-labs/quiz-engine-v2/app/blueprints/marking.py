"""Instructor marking: the post-test's written items and the four graded lab points.

Rules (docs/build-spec.md, "Marking and assessment"; quizes/posttest/README.md, "Marking"):
- A post-test written item is right only when the answer states every point in its answer key, in any wording.
  The key is read from the post-test bank in the mounted quizes folder, never typed in here. Written items need
  marking only for a student whose multiple-choice score leaves the result open: one who has the pass mark on
  multiple choice alone passes, and one who cannot reach it even with every written item right cannot pass.
- Each graded lab point (days 6 to 9) is Meets or Not yet against the rubric in that lab's answer file, with one
  retry after the instructor says what was missing.
- The certificate needs the post-test passed and Meets on all four points; attendance is not tracked here.

Every route is @instructor_required, and the engine's CSRF hook covers the POSTs.
"""

import json
import math
from pathlib import Path

from flask import Blueprint, redirect, request, url_for

from ..audit import record_audit_event, utc_now_iso
from ..auth import current_instructor, instructor_required
from ..db import get_db
from ..grading import GradingError, grade_written_answer
from ..theme import render_themed_template as render_template_string
from .dashboard import _quizes_dir

bp = Blueprint("marking", __name__, url_prefix="/instructor/marking")

PASS_FRACTION = 0.7
POSTTEST_GLOB = "posttest/*-quiz-bank.json"
COUNTED_STATUSES = ("submitted", "needs_grading", "expired", "graded")

# The rubric itself stays in each lab's answer file; this names the point and says where to find it.
LAB_POINTS = (
    (1, 6, "Bitcoin trace: the annotated trace to the first service",
     "dynamic-labs/bitcoin-trace/quizes/INSTRUCTOR_ANSWERS.md, \"What the lab grades\""),
    (2, 7, "CoinJoin trace: the limits-of-tracing note (question 13)",
     "dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md, \"What the lab grades\""),
    (3, 8, "Cross-chain: the contract read, flow diagram and assessment (question 17)",
     "dynamic-labs/cross-chain/quizes/INSTRUCTOR_ANSWERS.md, \"What the lab grades\""),
    (4, 9, "Tron: the exposure summary (question 15)",
     "dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS_D9.md, \"Marking (question 15)\""),
)
POINT_NUMBERS = frozenset(p[0] for p in LAB_POINTS)
RESULTS = {"meets": "Meets", "not_yet": "Not yet"}
TRIES = {1: "First try", 2: "Retry"}


class MarkingError(ValueError):
    pass


# --- Post-test -------------------------------------------------------------------------------------------


def posttest_keys(quizes_dir=None):
    """{lesson_id: {item id: [key points]}} from the post-test bank files in the quizes folder."""
    quizes_dir = Path(quizes_dir) if quizes_dir else _quizes_dir()
    keys = {}
    if not quizes_dir.is_dir():
        return keys
    for path in sorted(quizes_dir.glob(POSTTEST_GLOB)):
        try:
            bank = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        lesson_id = bank.get("lesson_id") if isinstance(bank, dict) else None
        if not isinstance(lesson_id, str):
            continue
        keys[lesson_id] = {
            str(q.get("id")): [str(point) for point in q.get("answer_key") or []]
            for q in bank.get("questions") or []
            if isinstance(q, dict) and q.get("question_type") == "written"
        }
    return keys


def _posttest_answer_rows(conn, lesson_ids):
    """Every answer on the latest counted attempt of each student at each post-test quiz."""
    if not lesson_ids:
        return []
    marks = ",".join("?" for _ in lesson_ids)
    statuses = ",".join("?" for _ in COUNTED_STATUSES)
    return conn.execute(
        f"""
        WITH latest AS (
            SELECT attempts.quiz_version_id, attempts.student_id, MAX(attempts.attempt_number) AS n
            FROM attempts
            WHERE attempts.status IN ({statuses})
            GROUP BY attempts.quiz_version_id, attempts.student_id
        )
        SELECT
            attempts.id AS attempt_id,
            attempts.student_id,
            attempts.status AS attempt_status,
            students.identifier AS student_identifier,
            versions.id AS quiz_version_id,
            versions.title AS quiz_title,
            banks.lesson_id,
            questions.id AS question_id,
            questions.snapshot_source_qid AS item_id,
            questions.snapshot_question_type AS question_type,
            questions.snapshot_question_stem AS question_stem,
            questions.points,
            questions.position,
            answers.id AS answer_id,
            answers.written_response,
            answers.points_awarded
        FROM latest
        JOIN attempts
          ON attempts.quiz_version_id = latest.quiz_version_id
         AND attempts.student_id = latest.student_id
         AND attempts.attempt_number = latest.n
        JOIN students ON students.id = attempts.student_id
        JOIN quiz_versions versions ON versions.id = attempts.quiz_version_id
        JOIN quiz_version_questions questions ON questions.quiz_version_id = attempts.quiz_version_id
        JOIN questions source ON source.id = questions.source_question_id
        JOIN quiz_banks banks ON banks.id = source.quiz_bank_id
        LEFT JOIN attempt_answers answers
          ON answers.attempt_id = attempts.id
         AND answers.quiz_version_question_id = questions.id
        WHERE banks.lesson_id IN ({marks})
        ORDER BY students.identifier, versions.id, questions.position
        """,
        (*COUNTED_STATUSES, *lesson_ids),
    ).fetchall()


def posttest_overview(conn=None, quizes_dir=None):
    """One entry per post-test attempt: scores, what still needs marking, and the result so far."""
    conn = conn or get_db()
    keys = posttest_keys(quizes_dir)
    attempts = {}
    for row in _posttest_answer_rows(conn, tuple(keys)):
        entry = attempts.setdefault(
            row["attempt_id"],
            {
                "attempt_id": row["attempt_id"],
                "student_id": row["student_id"],
                "student": row["student_identifier"],
                "quiz_title": row["quiz_title"],
                "total": 0.0,
                "mc_score": 0.0,
                "mc_total": 0.0,
                "written_total": 0.0,
                "written_score": 0.0,
                "to_mark": [],
            },
        )
        points = float(row["points"])
        entry["total"] += points
        awarded = row["points_awarded"]
        if row["question_type"] == "multiple_choice":
            entry["mc_total"] += points
            entry["mc_score"] += float(awarded or 0)
            continue
        entry["written_total"] += points
        if awarded is not None:
            entry["written_score"] += float(awarded)
        elif row["answer_id"] is not None:
            entry["to_mark"].append(
                {
                    "answer_id": row["answer_id"],
                    "item_id": row["item_id"],
                    "question_stem": row["question_stem"],
                    "written_response": row["written_response"] or "",
                    "points": points,
                    "answer_key": keys.get(row["lesson_id"], {}).get(row["item_id"], []),
                }
            )
    return [_with_result(entry) for entry in attempts.values()]


def _with_result(entry):
    pass_mark = math.ceil(PASS_FRACTION * entry["total"] - 1e-9)
    unmarked = sum(item["points"] for item in entry["to_mark"])
    best = entry["mc_score"] + entry["written_score"] + unmarked
    reached = entry["mc_score"] + entry["written_score"]
    if reached >= pass_mark:
        result, needs_marking = "passed", False
    elif best < pass_mark:
        result, needs_marking = "not passed", False
    else:
        result, needs_marking = "still marking", True
    entry.update(
        pass_mark=pass_mark,
        result=result,
        needs_marking=needs_marking,
        score_so_far=reached,
    )
    return entry


def mark_posttest_answer(answer_id, ticked, *, actor_sub, conn=None, quizes_dir=None):
    """Right (full points) only when every key point is ticked; otherwise zero."""
    conn = conn or get_db()
    answer_id = int(answer_id)
    item = next(
        (
            item
            for entry in posttest_overview(conn, quizes_dir)
            for item in entry["to_mark"]
            if item["answer_id"] == answer_id
        ),
        None,
    )
    if item is None:
        raise MarkingError("That answer is not a post-test written answer waiting to be marked.")
    if not item["answer_key"]:
        raise MarkingError("No answer key was found for that item in the post-test bank.")
    wanted = set(range(len(item["answer_key"])))
    right = wanted <= set(ticked)
    try:
        grade_written_answer(answer_id, item["points"] if right else 0, actor_sub=actor_sub, conn=conn)
    except GradingError as exc:
        raise MarkingError(str(exc)) from exc
    return right


# --- Lab points ------------------------------------------------------------------------------------------


def record_lab_point(student_id, point, try_number, result, note, *, actor_sub, conn=None):
    """Store one mark. Saving the same try again corrects it; a retry needs a first try of Not yet."""
    conn = conn or get_db()
    point, try_number = int(point), int(try_number)
    note = (note or "").strip()
    if point not in POINT_NUMBERS:
        raise MarkingError("There are four graded lab points, numbered 1 to 4.")
    if try_number not in TRIES:
        raise MarkingError("A point has a first try and one retry.")
    if result not in RESULTS:
        raise MarkingError("Choose Meets or Not yet.")
    if result == "not_yet" and not note:
        raise MarkingError("Say what was missing: the student retries from it.")
    if len(note) > 2000:
        raise MarkingError("Keep the note under 2,000 characters.")
    with conn:
        student = conn.execute("SELECT id FROM students WHERE id = ?", (int(student_id),)).fetchone()
        if student is None:
            raise MarkingError("That student is not in the quiz engine.")
        tries = {
            row["try_number"]: row["result"]
            for row in conn.execute(
                "SELECT try_number, result FROM lab_point_marks WHERE student_id = ? AND point = ?",
                (student["id"], point),
            )
        }
        if try_number == 2 and tries.get(1) != "not_yet":
            raise MarkingError("A retry comes only after a first try marked Not yet.")
        if try_number == 1 and 2 in tries and result != "not_yet":
            raise MarkingError("This point already has a retry; correct the retry instead.")
        now = utc_now_iso()
        conn.execute(
            """
            INSERT INTO lab_point_marks (student_id, point, try_number, result, note, marked_at, marked_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (student_id, point, try_number) DO UPDATE SET
                result = excluded.result,
                note = excluded.note,
                marked_at = excluded.marked_at,
                marked_by = excluded.marked_by
            """,
            (student["id"], point, try_number, result, note or None, now, actor_sub),
        )
        record_audit_event(
            "lab_point.marked",
            actor_sub=actor_sub,
            object_type="student",
            object_id=student["id"],
            details={
                "schema_version": 1,
                "details": {"point": point, "try_number": try_number, "result": result},
            },
            db=conn,
        )


def lab_point_table(conn=None):
    """Each active student's four points and certificate status, with the post-test result."""
    conn = conn or get_db()
    students = conn.execute(
        "SELECT id, identifier FROM students WHERE status = 'active' ORDER BY identifier"
    ).fetchall()
    marks = {}
    for row in conn.execute(
        "SELECT student_id, point, try_number, result, note FROM lab_point_marks ORDER BY try_number"
    ):
        marks.setdefault((row["student_id"], row["point"]), {})[row["try_number"]] = dict(row)
    return [
        {
            "id": s["id"],
            "identifier": s["identifier"],
            "points": [_point_cell(marks.get((s["id"], number), {})) for number, *_ in LAB_POINTS],
        }
        for s in students
    ]


def _point_cell(tries):
    latest = tries.get(2) or tries.get(1)
    if latest is None:
        return {"text": "not marked", "meets": False, "note": None}
    label = RESULTS[latest["result"]]
    if 2 in tries:
        label = f"Not yet, then {label} on the retry"
    elif latest["result"] == "not_yet":
        label = "Not yet (retry left)"
    # Keep what was missing on the first try when the retry adds no note.
    note = latest["note"] or (tries.get(1) or {}).get("note")
    return {"text": label, "meets": latest["result"] == "meets", "note": note}


def certificate_rows(conn=None, quizes_dir=None):
    conn = conn or get_db()
    tests = {}
    for entry in posttest_overview(conn, quizes_dir):
        tests[entry["student_id"]] = entry["result"]
    rows = []
    for student in lab_point_table(conn):
        test = tests.get(student["id"], "not taken")
        all_meets = all(cell["meets"] for cell in student["points"])
        student["posttest"] = test
        student["certificate"] = "yes" if test == "passed" and all_meets else "not yet"
        rows.append(student)
    return rows


# --- Pages -----------------------------------------------------------------------------------------------


@bp.get("")
@bp.get("/")
@instructor_required
def marking_page():
    return _render(message=request.args.get("message"))


@bp.post("/posttest/<int:answer_id>")
@instructor_required
def mark_posttest_route(answer_id):
    ticked = {int(v) for v in request.form.getlist("key_point") if v.isdigit()}
    try:
        right = mark_posttest_answer(answer_id, ticked, actor_sub=current_instructor().subject)
    except MarkingError as exc:
        return _render(error=str(exc)), 400
    word = "right" if right else "not right (a key point is missing)"
    return redirect(url_for("marking.marking_page", message=f"Marked {word}.") + "#posttest")


@bp.post("/lab-point")
@instructor_required
def mark_lab_point_route():
    form = request.form
    try:
        record_lab_point(
            form.get("student_id", "0") or "0",
            form.get("point", "0") or "0",
            form.get("try_number", "1") or "1",
            form.get("result", ""),
            form.get("note"),
            actor_sub=current_instructor().subject,
        )
    except (MarkingError, ValueError) as exc:
        return _render(error=str(exc) if isinstance(exc, MarkingError) else "Choose a student and a point."), 400
    return redirect(url_for("marking.marking_page", message="Lab point saved.") + "#lab-points")


def _render(message=None, error=None):
    quizes_dir = _quizes_dir()
    overview = posttest_overview(quizes_dir=quizes_dir)
    overview.sort(key=lambda e: (not e["needs_marking"], e["student"]))
    return render_template_string(
        MARKING_TEMPLATE,
        message=message,
        error=error,
        quizes_found=quizes_dir.is_dir(),
        quizes_dir=str(quizes_dir),
        overview=overview,
        lab_points=LAB_POINTS,
        results=RESULTS,
        tries=TRIES,
        rows=certificate_rows(quizes_dir=quizes_dir),
    )


MARKING_TEMPLATE = """
<!doctype html>
<title>Marking</title>
<main>
  <h1>Marking</h1>
  <p>The post-test's written items and the four graded lab points, and who has earned the certificate.</p>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  {% if error %}<p role="alert">{{ error }}</p>{% endif %}

  <section id="posttest" aria-labelledby="posttest-title">
    <h2 id="posttest-title">Post-test written items</h2>
    <p>An answer is right only when it states every key point, in any wording: tick each point it states.
    Students whose multiple-choice score already decides the result need no marking.</p>
    {% if not quizes_found %}
      <p>The quizzes folder is not mounted at <code>{{ quizes_dir }}</code>, so the answer keys cannot be read.</p>
    {% elif not overview %}
      <p>No post-test attempts yet.</p>
    {% else %}
      <table>
        <thead><tr><th>Student</th><th>Multiple choice</th><th>Written marked</th><th>Pass mark</th><th>Result</th></tr></thead>
        <tbody>
        {% for e in overview %}
          <tr>
            <td><code>{{ e.student }}</code></td>
            <td>{{ e.mc_score|round|int }} of {{ e.mc_total|round|int }}</td>
            <td>{{ e.written_score|round|int }} of {{ e.written_total|round|int }}
              {% if e.to_mark %}({{ e.to_mark|length }} unmarked){% endif %}</td>
            <td>{{ e.pass_mark }} of {{ e.total|round|int }}</td>
            <td>{{ e.result }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
      {% for e in overview if e.needs_marking %}
        <h3>Mark <code>{{ e.student }}</code> ({{ e.quiz_title }})</h3>
        {% for item in e.to_mark %}
          <form method="post" action="{{ url_for('marking.mark_posttest_route', answer_id=item.answer_id) }}">
            <p><strong>{{ item.item_id }}.</strong> {{ item.question_stem }}</p>
            <blockquote>{{ item.written_response or '(no answer)' }}</blockquote>
            {% if item.answer_key %}
              <fieldset><legend>Key points the answer states</legend>
              {% for point in item.answer_key %}
                <label><input type="checkbox" name="key_point" value="{{ loop.index0 }}"> {{ point }}</label><br>
              {% endfor %}
              </fieldset>
              <button type="submit">Save mark</button>
            {% else %}
              <p>No answer key found for this item in the post-test bank.</p>
            {% endif %}
          </form>
        {% endfor %}
      {% else %}
        <p>No written answers need marking.</p>
      {% endfor %}
    {% endif %}
  </section>

  <section id="lab-points" aria-labelledby="lab-points-title">
    <h2 id="lab-points-title">Graded lab points</h2>
    <p>Each is Meets or Not yet against the rubric in that lab's answer file. After Not yet, say what was missing;
    the student has one retry, in lab time or day 10's review session.</p>
    <ol>
    {% for number, day, name, rubric in lab_points %}
      <li>Day {{ day }}: {{ name }}.<br><small>Rubric: {{ rubric }}</small></li>
    {% endfor %}
    </ol>
    {% if rows %}
      <form method="post" action="{{ url_for('marking.mark_lab_point_route') }}">
        <label>Student
          <select name="student_id">{% for r in rows %}<option value="{{ r.id }}">{{ r.identifier }}</option>{% endfor %}</select>
        </label>
        <label>Point
          <select name="point">{% for number, day, name, rubric in lab_points %}<option value="{{ number }}">{{ number }} (day {{ day }})</option>{% endfor %}</select>
        </label>
        <label>Try
          <select name="try_number">{% for n, label in tries.items() %}<option value="{{ n }}">{{ label }}</option>{% endfor %}</select>
        </label>
        <fieldset><legend>Result</legend>
          {% for value, label in results.items() %}
            <label><input type="radio" name="result" value="{{ value }}"> {{ label }}</label>
          {% endfor %}
        </fieldset>
        <label>What was missing (needed for Not yet)<br><textarea name="note" rows="2" cols="60"></textarea></label>
        <button type="submit">Save</button>
      </form>
      <h3 id="certificate">Points and certificate</h3>
      <p>The certificate needs the post-test passed and Meets on all four points by the end of day 10's review
      session, and attendance on all ten days, which this page does not track.</p>
      <table>
        <thead><tr><th>Student</th>{% for number, day, name, rubric in lab_points %}<th>Point {{ number }}</th>{% endfor %}<th>Post-test</th><th>Certificate</th></tr></thead>
        <tbody>
        {% for r in rows %}
          <tr>
            <td><code>{{ r.identifier }}</code></td>
            {% for cell in r.points %}<td>{{ cell.text }}{% if cell.note %}<br><small>{{ cell.note }}</small>{% endif %}</td>{% endfor %}
            <td>{{ r.posttest }}</td>
            <td>{{ r.certificate }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No students in the quiz engine yet.</p>
    {% endif %}
  </section>
  <p><a href="{{ url_for('dashboard.course_dashboard') }}">Run the course</a></p>
</main>
"""
