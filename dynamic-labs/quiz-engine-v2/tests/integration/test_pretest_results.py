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
                "items": {"q6": "right", "q45": "wrong"},
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
