"""Instructor-only pretest results: upload the JSON that quizes/pretest/mark_pretest.py --json writes,
and show where each student starts each day's lab.

The marking aid: each written answer in the upload is shown beside its model answer (the bank's key points and
explanation, read from the mounted quizes folder). The instructor ticks the points the answer states; it is right
only when every point is ticked, and the marker still judges. A judgement is kept against the answer's text, so a
re-upload of the same answer keeps it, and it decides the day's start point by the marker's own rule (a day's
problem needs every gate item right).

Students never reach this: every route is @instructor_required, and the engine's CSRF hook covers the POSTs.
"""

import hashlib
import json
import re
from pathlib import Path

from flask import Blueprint, redirect, request, url_for

from ..audit import record_audit_event, utc_now_iso
from ..auth import current_instructor, instructor_required
from ..db import get_db
from ..theme import render_themed_template as render_template_string
from .dashboard import _quizes_dir

bp = Blueprint("pretest", __name__, url_prefix="/instructor/pretest")

RESULTS_FORMAT = "pretest-results-v1"
DAY_VALUES = frozenset({"problem", "worked example", "unmarked", "not taken"})
ITEM_VALUES = frozenset({"right", "wrong", "unmarked"})
MAX_UPLOAD_BYTES = 2_000_000
MAX_STUDENTS = 500
MAX_WRITTEN_CHARS = 10_000
PRETEST_GLOB = "pretest/pretest_week*-quiz-bank.json"


class PretestImportError(ValueError):
    pass


def parse_results(raw):
    """Check an uploaded results file and return (form, students), or raise PretestImportError."""
    try:
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PretestImportError("That file is not JSON.") from exc
    if not isinstance(data, dict) or data.get("format") != RESULTS_FORMAT:
        raise PretestImportError(
            "That is not a pretest results file. Make it with "
            "mark_pretest.py <folder> --json results.json."
        )
    form = data.get("form")
    students = data.get("students")
    if not isinstance(form, str) or not isinstance(students, list):
        raise PretestImportError("The results file is missing its form or its students.")
    if not students or len(students) > MAX_STUDENTS:
        raise PretestImportError(f"Expected between 1 and {MAX_STUDENTS} students.")
    seen = set()
    for student in students:
        if not isinstance(student, dict):
            raise PretestImportError("Each student must be an object.")
        name = student.get("name")
        days = student.get("days")
        items = student.get("items")
        if not isinstance(name, str) or not name.strip():
            raise PretestImportError("Every student needs a name.")
        if name.casefold() in seen:
            raise PretestImportError(f"{name} appears twice.")
        seen.add(name.casefold())
        if not isinstance(days, dict) or not all(
            re.fullmatch(r"\d{1,2}", str(k)) and v in DAY_VALUES for k, v in days.items()
        ):
            raise PretestImportError(f"{name}: the day results are not in the expected form.")
        if not isinstance(items, dict) or not all(
            re.fullmatch(r"q\d+", str(k)) and v in ITEM_VALUES for k, v in items.items()
        ):
            raise PretestImportError(f"{name}: the item results are not in the expected form.")
        written = student.get("written", {})
        if not isinstance(written, dict) or not all(
            re.fullmatch(r"q\d+", str(k)) and isinstance(v, str) and len(v) <= MAX_WRITTEN_CHARS
            for k, v in written.items()
        ):
            raise PretestImportError(f"{name}: the written answers are not in the expected form.")
    return form, students


def answer_digest(text):
    """The same digest as mark_pretest.answer_digest: an answer's text with its spacing evened out."""
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()[:12]


def load_pretest_bank(quizes_dir=None):
    """{"items": {id: item}, "gates": {day: [ids]}} from the pretest banks, or None when none is mounted."""
    quizes_dir = Path(quizes_dir) if quizes_dir else _quizes_dir()
    paths = sorted(quizes_dir.glob(PRETEST_GLOB)) if quizes_dir.is_dir() else []
    if not paths:
        return None
    items, gates = {}, {}
    for path in paths:
        try:
            bank = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        meta = bank.get("metadata", {})
        for q in bank.get("questions", []):
            items[q["id"]] = q
        for day, ids in meta.get("days", {}).items():
            gates[str(day)] = list(meta.get("lab_gates", {}).get(day, ids))
    return {"items": items, "gates": gates} if items else None


def day_entry(marks, gate):
    """mark_pretest.entry: "problem", "worked example", "unmarked" or "not taken" from {id: right/wrong/unmarked}."""
    held = [marks[g] for g in gate if g in marks]
    if not held:
        return "not taken"
    if len(held) < len(gate) or "wrong" in held:
        return "worked example"
    if "unmarked" in held:
        return "unmarked"
    return "problem"


def written_judgements(conn):
    """{(student key, item id, digest): "right" | "wrong"} as judged on this page."""
    return {
        (r["student_key"], r["item_id"], r["answer_digest"]): r["result"]
        for r in conn.execute("SELECT student_key, item_id, answer_digest, result FROM pretest_written_marks")
    }


def record_written_mark(student_name, item_id, ticked, *, actor_sub, conn=None, quizes_dir=None):
    """Judge one written answer: right only when every key point is ticked. Returns the result."""
    conn = conn or get_db()
    row = conn.execute(
        "SELECT student_name, written_json FROM pretest_results WHERE student_name = ?", (student_name,)
    ).fetchone()
    answer = json.loads(row["written_json"]).get(item_id) if row else None
    if not answer:
        raise PretestImportError("That written answer is not in the current import.")
    bank = load_pretest_bank(quizes_dir)
    item = (bank or {}).get("items", {}).get(item_id)
    if not item or not item.get("answer_key"):
        raise PretestImportError("No model answer for that item in the pretest bank.")
    points = range(len(item["answer_key"]))
    if not set(ticked) <= set(points):
        raise PretestImportError("Those key points are not in the model answer.")
    result = "right" if set(ticked) == set(points) else "wrong"
    key, digest = row["student_name"].casefold(), answer_digest(answer)
    with conn:
        conn.execute(
            """
            INSERT INTO pretest_written_marks (student_key, item_id, answer_digest, result, marked_at, marked_by)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (student_key, item_id, answer_digest) DO UPDATE SET
                result = excluded.result,
                marked_at = excluded.marked_at,
                marked_by = excluded.marked_by
            """,
            (key, item_id, digest, result, utc_now_iso(), actor_sub),
        )
        record_audit_event(
            "pretest.written_marked",
            actor_sub=actor_sub,
            object_type="pretest_item",
            object_id=item_id,
            details={"schema_version": 1, "details": {"student": key, "item_id": item_id, "result": result}},
            db=conn,
        )
    return result


def replace_pretest_results(form, students, *, imported_by=None, conn=None):
    """Store the students, replacing the previous import in one transaction."""
    conn = conn or get_db()
    now = utc_now_iso()
    with conn:
        conn.execute("DELETE FROM pretest_results")
        conn.executemany(
            """
            INSERT INTO pretest_results
                (student_name, bank_form, days_json, items_json, written_json, imported_at, imported_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    s["name"].strip(),
                    form,
                    json.dumps(s["days"], sort_keys=True),
                    json.dumps(s["items"], sort_keys=True),
                    json.dumps(s.get("written", {}), sort_keys=True),
                    now,
                    imported_by,
                )
                for s in students
            ],
        )
    return len(students)


def pretest_table(conn=None, quizes_dir=None):
    """The page's data: day columns, a row per student, and the written answers to judge.

    {"days": [...], "rows": [{"name", "cells"}], "written": [...], "bank_found": bool, "form", "imported_at"}.
    A judgement made here replaces the item's uploaded mark, and each day is worked out again from the items
    with the marker's rule; without the bank, the uploaded days stand as they are.
    """
    conn = conn or get_db()
    rows = conn.execute(
        "SELECT student_name, bank_form, days_json, items_json, written_json, imported_at FROM pretest_results "
        "ORDER BY student_name COLLATE NOCASE"
    ).fetchall()
    bank = load_pretest_bank(quizes_dir)
    judged = written_judgements(conn)
    parsed, written = [], []
    for r in rows:
        name = r["student_name"]
        cells = json.loads(r["days_json"])
        items = json.loads(r["items_json"])
        answers = json.loads(r["written_json"] or "{}")
        for qid, text in sorted(answers.items(), key=lambda kv: int(kv[0][1:])):
            mark = judged.get((name.casefold(), qid, answer_digest(text)))
            if mark:
                items[qid] = mark
            item = (bank or {}).get("items", {}).get(qid, {})
            written.append({
                "student": name,
                "item_id": qid,
                "answer": text,
                "mark": items.get(qid, "unmarked"),
                "judged_here": bool(mark),
                "day": item.get("day"),
                "stem": item.get("question_stem"),
                "answer_key": item.get("answer_key") or [],
                "explanation": item.get("explanation"),
            })
        if bank:
            cells = {d: day_entry(items, bank["gates"][d]) if d in bank["gates"] else v for d, v in cells.items()}
        parsed.append((name, cells))
    days = sorted({d for _, cells in parsed for d in cells}, key=int)
    written.sort(key=lambda w: (w["mark"] != "unmarked", w["student"].casefold(), int(w["item_id"][1:])))
    return {
        "days": days,
        "rows": [
            {"name": name, "cells": [cells.get(d, "not taken") for d in days]}
            for name, cells in parsed
        ],
        "written": written,
        "bank_found": bank is not None,
        "form": rows[0]["bank_form"] if rows else None,
        "imported_at": rows[0]["imported_at"] if rows else None,
    }


@bp.get("")
@bp.get("/")
@instructor_required
def pretest_page():
    return render_template_string(
        PRETEST_TEMPLATE, table=pretest_table(), message=request.args.get("message")
    )


@bp.post("")
@bp.post("/")
@instructor_required
def pretest_upload():
    upload = request.files.get("results_file")
    if upload is None or not upload.filename:
        return _page_with_error("Choose the results.json file first."), 400
    raw = upload.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        return _page_with_error("That file is too large to be a pretest results file."), 400
    try:
        form, students = parse_results(raw)
    except PretestImportError as exc:
        return _page_with_error(str(exc)), 400
    count = replace_pretest_results(
        form, students, imported_by=current_instructor().subject
    )
    return redirect(
        url_for("pretest.pretest_page", message=f"Imported {count} students; the earlier import was replaced.")
    )


@bp.post("/written")
@instructor_required
def pretest_mark_written():
    ticked = {int(v) for v in request.form.getlist("key_point") if v.isdigit()}
    try:
        result = record_written_mark(
            request.form.get("student_name", ""),
            request.form.get("item_id", ""),
            ticked,
            actor_sub=current_instructor().subject,
        )
    except PretestImportError as exc:
        return _page_with_error(str(exc)), 400
    word = "right" if result == "right" else "not right (a key point is missing)"
    return redirect(url_for("pretest.pretest_page", message=f"Marked {word}.") + "#written")


def _page_with_error(error):
    return render_template_string(PRETEST_TEMPLATE, table=pretest_table(), error=error)


PRETEST_TEMPLATE = """
<!doctype html>
<title>Pretest Results</title>
<main>
  <h1>Pretest results</h1>
  <p>Where each student starts each day's lab: the day's <strong>problem</strong> or its
  <strong>worked example</strong>. Instructor only.</p>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  {% if error %}<p role="alert">{{ error }}</p>{% endif %}
  <h2>Import</h2>
  <p>Mark the replies with <code>python quizes/pretest/mark_pretest.py &lt;folder&gt; --json results.json</code>,
  then upload <code>results.json</code>. A new upload replaces the previous one.</p>
  <form method="post" action="{{ url_for('pretest.pretest_upload') }}" enctype="multipart/form-data">
    <label>Results file
      <input type="file" name="results_file" accept="application/json,.json">
    </label>
    <button type="submit">Import</button>
  </form>
  <h2>Students</h2>
  {% if table.rows %}
    <p>{{ table.rows|length }} students, imported {{ table.imported_at }}.</p>
    <table id="pretest-table">
      <thead>
        <tr><th>Student</th>{% for d in table.days %}<th>Day {{ d }}</th>{% endfor %}</tr>
      </thead>
      <tbody>
        {% for row in table.rows %}
          <tr><td>{{ row.name }}</td>{% for cell in row.cells %}<td>{{ cell }}</td>{% endfor %}</tr>
        {% endfor %}
      </tbody>
    </table>
    <p>"unmarked" means a gate item has not been judged yet: judge it below, or in the marker, and re-upload.
    "not taken" means the student did not answer that day's items.</p>
  {% else %}
    <p>No pretest results imported yet.</p>
  {% endif %}
  <section id="written" aria-labelledby="written-title">
    <h2 id="written-title">Written answers</h2>
    <p>Each answer beside the model answer. Tick each key point the answer states, in any wording: it is right
    only when it states every point. You judge; the model answer is a guide. Unmarked answers come first.</p>
    {% if not table.bank_found %}
      <p>The pretest banks are not in the mounted quizzes folder, so the model answers cannot be shown and the days
      above are as uploaded.</p>
    {% elif not table.written %}
      <p>No written answers in this import. Uploads made before this page could judge them hold none: run the
      marker again with <code>--json</code> and re-upload.</p>
    {% else %}
      {% for w in table.written %}
        <form method="post" action="{{ url_for('pretest.pretest_mark_written') }}" class="pretest-written">
          <h3>{{ w.student }}: {{ w.item_id }}{% if w.day %} (day {{ w.day }}){% endif %}, {{ w.mark }}{% if w.judged_here %} (judged here){% endif %}</h3>
          <input type="hidden" name="student_name" value="{{ w.student }}">
          <input type="hidden" name="item_id" value="{{ w.item_id }}">
          {% if w.stem %}<p>{{ w.stem }}</p>{% endif %}
          <p><strong>Student's answer</strong></p>
          <blockquote style="white-space: pre-wrap">{{ w.answer }}</blockquote>
          {% if w.answer_key %}
            <fieldset><legend>Model answer: key points the answer states</legend>
            {% for point in w.answer_key %}
              <label><input type="checkbox" name="key_point" value="{{ loop.index0 }}"{% if w.judged_here and w.mark == "right" %} checked{% endif %}> {{ point }}</label><br>
            {% endfor %}
            </fieldset>
            {% if w.explanation %}<p><small>Why: {{ w.explanation }}</small></p>{% endif %}
            <button type="submit">Save mark</button>
          {% else %}
            <p>No model answer for {{ w.item_id }} in today's pretest banks.</p>
          {% endif %}
        </form>
      {% endfor %}
    {% endif %}
  </section>
  <p><a href="{{ url_for('instructor.instructor_dashboard') }}">Instructor home</a></p>
</main>
"""
