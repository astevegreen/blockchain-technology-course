import json
from html import unescape

from app import create_app
from app.db import get_db, init_db
from app.import_retirements import apply_import_retirement, preview_import_retirement
from app.ingest import ingest_json
from app.migrate import FULL_EXPORT_TABLES, export_full_engine, import_full_engine


HEADERS = {"X-Test-Instructor": "teacher"}


def _bank():
    return {
        "lesson_id": "retirement_api_lesson",
        "lesson_title": "Retirement API Lesson",
        "topic": "bitcoin",
        "tags": ["Retirement API"],
        "questions": [
            {
                "id": "q1",
                "question_stem": "Which content is retired?",
                "correct_answer": "Imported content",
                "incorrect_answers": ["Attempts"],
                "tags": ["Code Import"],
            },
            {
                "id": "q2",
                "question_stem": "Which content stays historical?",
                "correct_answer": "Generated snapshots",
                "incorrect_answers": ["Active pool rows"],
                "tags": ["History"],
            },
        ],
    }


def test_import_retirement_api_requires_auth_previews_and_applies(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

    unauthorized = client.post(
        "/instructor/api/import-retirements/preview",
        json={"mode": "lesson", "targets": ["retirement_api_lesson"]},
    )
    preview_response = client.post(
        "/instructor/api/import-retirements/preview",
        json={"mode": "lesson", "targets": ["retirement_api_lesson"]},
        headers=HEADERS,
    )
    preview = preview_response.get_json()["preview"]
    mismatch = client.post(
        "/instructor/api/import-retirements",
        json={
            "mode": "lesson",
            "targets": ["retirement_api_lesson"],
            "selection_hash": "wrong",
        },
        headers=HEADERS,
    )
    apply_response = client.post(
        "/instructor/api/import-retirements",
        json={
            "mode": "lesson",
            "targets": ["retirement_api_lesson"],
            "selection_hash": preview["selection_hash"],
            "reason": "integration cleanup",
        },
        headers=HEADERS,
    )
    banks_after = client.get("/instructor/api/banks", headers=HEADERS).get_json()
    questions_after = client.get(
        "/instructor/api/questions",
        query_string={"lesson_id": "retirement_api_lesson"},
        headers=HEADERS,
    ).get_json()

    assert unauthorized.status_code == 401
    assert preview_response.status_code == 200
    assert preview["counts"]["questions"] == 2
    assert mismatch.status_code == 400
    assert "selection changed" in mismatch.get_json()["error"]
    assert apply_response.status_code == 201
    assert apply_response.get_json()["result"]["status"] == "retired"
    assert not any(
        bank["lesson_id"] == "retirement_api_lesson"
        for bank in banks_after["banks"]
    )
    assert questions_after["total"] == 0


def test_import_retirement_html_preview_and_apply(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

    page = client.get("/instructor/import-retirements", headers=HEADERS)
    preview_page = client.post(
        "/instructor/import-retirements/preview",
        data={
            "mode": "tag",
            "targets": "Code Import",
            "reason": "HTML cleanup",
        },
        headers=HEADERS,
    )
    html = preview_page.get_data(as_text=True)
    marker = 'name="selection_hash" value="'
    selection_hash = html.split(marker, 1)[1].split('"', 1)[0]
    apply_page = client.post(
        "/instructor/import-retirements",
        data={
            "mode": "tag",
            "targets": "code-import",
            "selection_hash": selection_hash,
            "reason": "HTML cleanup",
        },
        headers=HEADERS,
    )

    assert page.status_code == 200
    assert "Delete Imported Content" in page.get_data(as_text=True)
    assert preview_page.status_code == 200
    assert "Which content is retired?" not in html
    assert "Questions</dt><dd>1</dd>" in html
    assert apply_page.status_code == 200
    assert "Retired 1 imported questions" in apply_page.get_data(as_text=True)


def test_import_retirement_html_target_dropdowns_and_repeated_targets(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

    page = client.get("/instructor/import-retirements", headers=HEADERS)
    html = page.get_data(as_text=True)
    repeated_preview = client.post(
        "/instructor/import-retirements/preview",
        data={
            "mode": "tag",
            "targets": ["Code Import", "History"],
            "reason": "multi-target preview",
        },
        headers=HEADERS,
    )

    assert page.status_code == 200
    assert 'data-retirement-mode' in html
    assert 'data-retirement-target-panel="lesson"' in html
    assert 'data-retirement-target-panel="tag"' in html
    assert 'data-retirement-select-all' in html
    assert 'data-retirement-select-none' in html
    assert 'data-retirement-target-filter' in html
    assert 'data-retirement-filter-status' in html
    assert 'data-retirement-search-text=' in html
    assert "Checked items stay selected when hidden by the filter." in html
    assert "visibleTargetRows(panel)" in html
    assert "tokens.every" in html
    assert 'value="retirement_api_lesson"' in html
    assert 'value="code-import"' in html
    assert repeated_preview.status_code == 200
    assert "Targets</dt><dd>code-import, history</dd>" in repeated_preview.get_data(
        as_text=True
    )
    assert "Questions</dt><dd>2</dd>" in repeated_preview.get_data(as_text=True)


def test_bank_browser_links_to_prefilled_import_retirement_flow(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

    banks_page = client.get("/instructor/banks", headers=HEADERS)
    banks_html = unescape(banks_page.get_data(as_text=True))
    prefilled_page = client.get(
        "/instructor/import-retirements",
        query_string={"mode": "lesson", "targets": "retirement_api_lesson"},
        headers=HEADERS,
    )
    prefilled_html = prefilled_page.get_data(as_text=True)

    assert banks_page.status_code == 200
    assert "Delete this bank" in banks_html
    assert (
        "/instructor/import-retirements?mode=lesson&targets=retirement_api_lesson"
        in banks_html
    )
    assert prefilled_page.status_code == 200
    assert 'value="lesson" selected' in prefilled_html
    assert 'value="retirement_api_lesson"\n                        checked' in (
        prefilled_html
    )


def test_full_export_import_preserves_retirement_state(app, tmp_path):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        preview = preview_import_retirement("tag", ["code-import"])
        apply_import_retirement(
            "tag",
            ["code-import"],
            selection_hash=preview["selection_hash"],
            actor_sub="teacher",
        )
        payload = export_full_engine()
        expected_counts = {
            table: len(payload["tables"][table])
            for table in FULL_EXPORT_TABLES
        }

    fresh_app = create_app(
        {
            "DATABASE_PATH": str(tmp_path / "retirement-roundtrip.sqlite"),
            "SECRET_KEY": "fresh-retirement-secret",
            "TESTING": True,
            "INSTRUCTOR_AUTH_MODE": "test-header",
            "TEST_INSTRUCTOR_HEADER": "X-Test-Instructor",
        }
    )
    with fresh_app.app_context():
        init_db()
        import_full_engine(payload)
        restored_counts = {
            table: get_db().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in FULL_EXPORT_TABLES
        }
        restored_retirements = get_db().execute(
            "SELECT COUNT(*) FROM question_retirements"
        ).fetchone()[0]

    assert payload["tables"]["import_retirement_batches"]
    assert payload["tables"]["question_retirements"]
    assert restored_counts == expected_counts
    assert restored_retirements == 1
