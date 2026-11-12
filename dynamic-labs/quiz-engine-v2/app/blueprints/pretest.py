"""Instructor-only pretest results: upload the JSON that quizes/pretest/mark_pretest.py --json writes,
and show where each student starts each day's lab.

Students never reach this: every route is @instructor_required, and the engine's CSRF hook covers the POST.
"""

import json
import re

from flask import Blueprint, redirect, request, url_for

from ..audit import utc_now_iso
from ..auth import current_instructor, instructor_required
from ..db import get_db
from ..theme import render_themed_template as render_template_string

bp = Blueprint("pretest", __name__, url_prefix="/instructor/pretest")

RESULTS_FORMAT = "pretest-results-v1"
DAY_VALUES = frozenset({"problem", "worked example", "unmarked", "not taken"})
ITEM_VALUES = frozenset({"right", "wrong", "unmarked"})
MAX_UPLOAD_BYTES = 2_000_000
MAX_STUDENTS = 500


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
    return form, students


def replace_pretest_results(form, students, *, imported_by=None, conn=None):
    """Store the students, replacing the previous import in one transaction."""
    conn = conn or get_db()
    now = utc_now_iso()
    with conn:
        conn.execute("DELETE FROM pretest_results")
        conn.executemany(
            """
            INSERT INTO pretest_results
                (student_name, bank_form, days_json, items_json, imported_at, imported_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    s["name"].strip(),
                    form,
                    json.dumps(s["days"], sort_keys=True),
                    json.dumps(s["items"], sort_keys=True),
                    now,
                    imported_by,
                )
                for s in students
            ],
        )
    return len(students)


def pretest_table(conn=None):
    """Rows and day columns for the page: {"days": [...], "rows": [{"name", "cells"}], ...}."""
    conn = conn or get_db()
    rows = conn.execute(
        "SELECT student_name, bank_form, days_json, imported_at FROM pretest_results "
        "ORDER BY student_name COLLATE NOCASE"
    ).fetchall()
    parsed = [(r["student_name"], json.loads(r["days_json"])) for r in rows]
    days = sorted({d for _, cells in parsed for d in cells}, key=int)
    return {
        "days": days,
        "rows": [
            {"name": name, "cells": [cells.get(d, "not taken") for d in days]}
            for name, cells in parsed
        ],
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
    <p>"unmarked" means a gate item has not been judged yet; run the marker again and re-upload.
    "not taken" means the student did not answer that day's items.</p>
  {% else %}
    <p>No pretest results imported yet.</p>
  {% endif %}
  <p><a href="{{ url_for('instructor.instructor_dashboard') }}">Instructor home</a></p>
</main>
"""
