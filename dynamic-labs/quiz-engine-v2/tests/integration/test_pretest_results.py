import io
import json

from app.db import get_db

HEADERS = {"X-Test-Instructor": "teacher"}


def _results(*names, form="abc123"):
    return {
        "format": "pretest-results-v1",
        "form": form,
        "students": [
            {
                "name": name,
                "days": {"1": "problem", "2": "worked example"},
                "items": {"q91": "right", "q92": "wrong"},
            }
            for name in names
        ],
    }


def _upload(client, payload, headers=HEADERS):
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return client.post(
        "/instructor/pretest",
        data={"results_file": (io.BytesIO(raw), "results.json")},
        headers=headers,
        content_type="multipart/form-data",
    )


def test_pretest_page_requires_instructor(client):
    assert client.get("/instructor/pretest").status_code in {302, 401, 403}
    assert _upload(client, _results("Ana"), headers={}).status_code in {302, 401, 403}


def test_empty_page_then_upload_shows_one_row_per_student(client):
    empty = client.get("/instructor/pretest", headers=HEADERS)
    assert empty.status_code == 200
    assert "No pretest results imported yet" in empty.get_data(as_text=True)

    response = _upload(client, _results("Ana Analyst", "Bo <b>"))
    assert response.status_code == 302

    html = client.get("/instructor/pretest", headers=HEADERS).get_data(as_text=True)
    assert "<th>Day 1</th>" in html and "<th>Day 2</th>" in html
    assert "<td>Ana Analyst</td><td>problem</td><td>worked example</td>" in html
    assert "Bo &lt;b&gt;" in html


def test_reupload_replaces_the_previous_import(app, client):
    _upload(client, _results("Ana", "Bo"))
    _upload(client, _results("Cy"))
    with app.app_context():
        names = [r["student_name"] for r in get_db().execute("SELECT student_name FROM pretest_results")]
    assert names == ["Cy"]


def test_bad_uploads_are_refused_and_keep_the_old_import(app, client):
    _upload(client, _results("Ana"))
    for bad in (b"not json", json.dumps({"format": "other"}).encode(), json.dumps(_results("Ana", "ana")).encode()):
        assert _upload(client, bad).status_code == 400
    broken = _results("Dee")
    broken["students"][0]["days"]["1"] = "maybe"
    assert _upload(client, broken).status_code == 400
    assert client.post("/instructor/pretest", headers=HEADERS).status_code == 400
    with app.app_context():
        names = [r["student_name"] for r in get_db().execute("SELECT student_name FROM pretest_results")]
    assert names == ["Ana"]


def test_pretest_results_are_in_the_full_export(app):
    from app.migrate import FULL_EXPORT_TABLES, export_full_engine

    assert "pretest_results" in FULL_EXPORT_TABLES
    with app.app_context():
        assert export_full_engine()["tables"]["pretest_results"] == []


PRETEST_BANK = {
    "metadata": {"days": {"1": ["q90", "q91"], "2": ["q92"]}, "lab_gates": {"1": ["q91"], "2": ["q92"]}},
    "questions": [
        {"id": "q90", "day": 1, "question_type": "multiple_choice", "question_stem": "Pick one."},
        {"id": "q91", "day": 1, "question_type": "written", "question_stem": "Placeholder written item.",
         "answer_key": ["Point one: the alpha part.", "Point two: the beta part."],
         "explanation": "Placeholder explanation."},
        {"id": "q92", "day": 2, "question_type": "multiple_choice", "question_stem": "Pick one."},
    ],
}


def _with_written(answer="It covers alpha and; beta too."):
    payload = _results("Ana Analyst")
    payload["students"][0]["days"] = {"1": "unmarked", "2": "problem"}
    payload["students"][0]["items"] = {"q90": "right", "q91": "unmarked", "q92": "right"}
    payload["students"][0]["written"] = {"q91": answer}
    return payload


def _pretest_app(app_factory, tmp_path, with_bank=True):
    quizes = tmp_path / "quizes"
    (quizes / "pretest").mkdir(parents=True)
    if with_bank:
        (quizes / "pretest" / "pretest_week1-quiz-bank.json").write_text(json.dumps(PRETEST_BANK), encoding="utf-8")
    return app_factory(QUIZES_DIR=str(quizes))


def _judge(client, ticked, name="Ana Analyst", item="q91"):
    return client.post(
        "/instructor/pretest/written",
        data={"student_name": name, "item_id": item, "key_point": [str(i) for i in ticked]},
        headers=HEADERS,
    )


def test_written_answer_shows_beside_the_model_answer(app_factory, tmp_path):
    app = _pretest_app(app_factory, tmp_path)
    client = app.test_client()
    assert _upload(client, _with_written()).status_code == 302
    page = client.get("/instructor/pretest", headers=HEADERS).get_data(as_text=True)
    assert "It covers alpha and; beta too." in page
    assert "Point one: the alpha part." in page and "Point two: the beta part." in page
    assert "Placeholder explanation." in page
    assert "Placeholder written item." in page


def test_judging_every_point_right_opens_the_problem_and_survives_a_reupload(app_factory, tmp_path):
    from app.blueprints.pretest import pretest_table

    app = _pretest_app(app_factory, tmp_path)
    client = app.test_client()
    _upload(client, _with_written())
    assert _judge(client, [0]).status_code == 302  # one point missing: not right
    with app.app_context():
        table = pretest_table()
    assert table["rows"][0]["cells"] == ["worked example", "problem"]
    assert _judge(client, [0, 1]).status_code == 302
    with app.app_context():
        table = pretest_table()
    assert table["rows"][0]["cells"] == ["problem", "problem"]
    assert table["written"][0]["mark"] == "right" and table["written"][0]["judged_here"]
    # The same answer, spaced differently, keeps its judgement; a changed answer is unmarked again.
    _upload(client, _with_written("It covers alpha  and;\nbeta too."))
    with app.app_context():
        assert pretest_table()["rows"][0]["cells"] == ["problem", "problem"]
    _upload(client, _with_written("A different answer."))
    with app.app_context():
        assert pretest_table()["rows"][0]["cells"] == ["unmarked", "problem"]
    with app.app_context():
        events = get_db().execute(
            "SELECT COUNT(*) AS n FROM audit_events WHERE event_type = 'pretest.written_marked'"
        ).fetchone()["n"]
    assert events == 2


def test_judging_refuses_unknown_answers_and_points(app_factory, tmp_path):
    app = _pretest_app(app_factory, tmp_path)
    client = app.test_client()
    _upload(client, _with_written())
    assert _judge(client, [0, 1], name="Nobody").status_code == 400
    assert _judge(client, [0, 1], item="q90").status_code == 400  # no written answer for q90
    assert _judge(client, [0, 5]).status_code == 400
    assert app.test_client().post("/instructor/pretest/written", data={}).status_code in (302, 401, 403)


def test_without_the_bank_the_uploaded_days_stand(app_factory, tmp_path):
    app = _pretest_app(app_factory, tmp_path, with_bank=False)
    client = app.test_client()
    _upload(client, _with_written())
    page = client.get("/instructor/pretest", headers=HEADERS).get_data(as_text=True)
    assert "pretest banks are not in the mounted quizzes folder" in page
    assert _judge(client, [0, 1]).status_code == 400


def test_bad_written_answers_are_refused(client):
    payload = _with_written()
    payload["students"][0]["written"] = {"q91": 3}
    assert _upload(client, payload).status_code == 400
    payload["students"][0]["written"] = {"q91": "x" * 10_001}
    assert _upload(client, payload).status_code == 400


def test_written_marks_are_in_the_full_export(app):
    from app.migrate import FULL_EXPORT_TABLES

    assert "pretest_written_marks" in FULL_EXPORT_TABLES
