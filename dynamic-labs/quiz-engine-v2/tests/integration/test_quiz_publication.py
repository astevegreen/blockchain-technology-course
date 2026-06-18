import json
import os
from pathlib import Path

from app.db import get_db
from app.ingest import ingest_json


HEADERS = {"X-Test-Instructor": "teacher"}


def _quiz_fixture_dir():
    configured = os.environ.get("QUIZ_ENGINE_SAMPLE_QUIZ_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[4] / "quizes"


def _bundle_path():
    return _quiz_fixture_dir() / "dist" / "blockchain-course-quiz-bank-bundle.json"


def _load_bundle():
    raw_json = _bundle_path().read_text(encoding="utf-8")
    return raw_json, json.loads(raw_json)


def _template_payload(source_bank, **overrides):
    payload = {
        "title": "Publication Browser Template",
        "description": "Publication integration template",
        "criteria": {
            "lesson_ids": [source_bank["lesson_id"]],
            "topics": [source_bank["topic"]],
            "tags": ["bitcoin-origins-and-mechanics"],
            "tag_match_mode": "any",
            "hierarchy_sections": [source_bank["hierarchy"]["sections"][0]["id"]],
            "hierarchy_lectures": [
                source_bank["hierarchy"]["sections"][0]["lectures"][0]["id"]
            ],
            "difficulty_min": 1,
            "difficulty_max": 5,
            "question_types": ["multiple_choice"],
            "require_topic_coverage": True,
        },
        "question_count": 5,
        "selection_policy": "balanced_difficulty",
        "timer_minutes": 30,
        "attempt_limit": 1,
        "result_policy": "score_after_grading",
    }
    payload.update(overrides)
    return payload


def _enroll_student(client):
    response = client.post("/student/enroll")
    text = response.get_data(as_text=True)
    marker = '<p id="student-identifier"><code>'
    start = text.index(marker) + len(marker)
    end = text.index("</code>", start)
    return text[start:end]


def _seed_generated_quiz(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]
    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    template = client.post(
        "/instructor/api/templates",
        json=_template_payload(source_bank),
        headers=HEADERS,
    ).get_json()["template"]
    response = client.post(
        f"/instructor/api/templates/{template['id']}/generate",
        json={"random_seed": "publication-seed"},
        headers=HEADERS,
    )
    return response.get_json()["quiz_version"]


def test_instructor_preview_publish_hide_archive_and_student_listing(app, client):
    version = _seed_generated_quiz(app, client)
    identifier = _enroll_student(client)

    hidden_html = client.get("/student/quizzes").get_data(as_text=True)
    preview_response = client.get(
        f"/instructor/api/quiz-versions/{version['id']}/preview",
        headers=HEADERS,
    )
    preview_html = client.get(
        f"/instructor/quiz-versions/{version['id']}/preview",
        headers=HEADERS,
    ).get_data(as_text=True)
    with app.app_context():
        attempt_count = get_db().execute("SELECT COUNT(*) FROM attempts").fetchone()[0]

    assert version["visibility"] == "hidden"
    assert version["title"] not in hidden_html
    assert preview_response.status_code == 200
    preview = preview_response.get_json()["quiz_version"]
    assert preview["questions"][0]["options"][0]["is_correct"] in {0, 1}
    assert any(
        option["is_correct"]
        for question in preview["questions"]
        for option in question["options"]
    )
    assert "correct" in preview_html
    assert "Explanation" in preview_html
    assert "Preview Publication Browser Template" in preview_html
    assert attempt_count == 0

    metadata_response = client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "title": "Published Bitcoin Quiz",
            "description": "Visible to students",
            "available_from": "2000-01-01T00:00:00+00:00",
            "available_until": "2999-01-01T00:00:00+00:00",
            "instructor_notes": "Use in class",
        },
        headers=HEADERS,
    )
    publish_response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/publish",
        headers=HEADERS,
    )
    student_html = client.get("/student/quizzes").get_data(as_text=True)
    student_api = client.get("/student/api/quizzes").get_json()

    assert metadata_response.status_code == 200
    assert publish_response.status_code == 200
    assert publish_response.get_json()["quiz_version"]["visibility"] == "published"
    assert "Published Bitcoin Quiz" in student_html
    assert "Visible to students" in student_html
    assert identifier in student_html
    assert "correct" not in student_html
    assert "Explanation" not in student_html
    assert "Source lesson" not in student_html
    assert student_api["quizzes"][0]["title"] == "Published Bitcoin Quiz"
    assert "questions" not in student_api["quizzes"][0]

    hide_response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/hide",
        headers=HEADERS,
    )
    hidden_again = client.get("/student/quizzes").get_data(as_text=True)
    publish_again = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/publish",
        headers=HEADERS,
    )
    archive_response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/archive",
        headers=HEADERS,
    )
    archived_html = client.get("/student/quizzes").get_data(as_text=True)

    assert hide_response.status_code == 200
    assert "Published Bitcoin Quiz" not in hidden_again
    assert publish_again.status_code == 200
    assert archive_response.status_code == 200
    assert archive_response.get_json()["quiz_version"]["visibility"] == "archived"
    assert "Published Bitcoin Quiz" not in archived_html


def test_availability_windows_filter_student_visible_quizzes(app, client):
    version = _seed_generated_quiz(app, client)
    _enroll_student(client)

    client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "title": "Scheduled Quiz",
            "available_from": "2999-01-01T00:00:00+00:00",
        },
        headers=HEADERS,
    )
    client.post(
        f"/instructor/api/quiz-versions/{version['id']}/publish",
        headers=HEADERS,
    )
    future_html = client.get("/student/quizzes").get_data(as_text=True)
    future_api = client.get("/student/api/quizzes").get_json()
    future_start = client.post(f"/student/api/quizzes/{version['id']}/start")

    client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "available_from": "",
            "available_until": "2000-01-01T00:00:00+00:00",
        },
        headers=HEADERS,
    )
    expired_html = client.get("/student/quizzes").get_data(as_text=True)

    assert "Scheduled Quiz" in future_html
    assert "Scheduled · opens" in future_html
    assert 'datetime="2999-01-01T00:00:00+00:00"' in future_html
    assert 'data-dynamic-labs-time="student">Local time</time>' in future_html
    assert "Locked until the scheduled start time." in future_html
    assert "Start quiz" not in future_html
    assert future_api["quizzes"][0]["title"] == "Scheduled Quiz"
    assert future_api["quizzes"][0]["availability_status"] == "scheduled"
    assert future_start.status_code == 400
    assert future_start.get_json()["error"] == "quiz is not available"
    assert "Scheduled Quiz" not in expired_html


def test_quiz_version_detail_uses_utc_picker_and_correct_answer_highlight(app, client):
    version = _seed_generated_quiz(app, client)
    client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "available_from": "2000-01-01T00:00:00+00:00",
            "available_until": "2999-01-01T00:00:00+00:00",
        },
        headers=HEADERS,
    )

    detail_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)
    preview_html = client.get(
        f"/instructor/quiz-versions/{version['id']}/preview",
        headers=HEADERS,
    ).get_data(as_text=True)
    bad_window_response = client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "available_from": "2026-05-20T12:00:00+00:00",
            "available_until": "2026-05-20T12:00:00+00:00",
        },
        headers=HEADERS,
    )

    assert "data-availability-form" in detail_html
    assert "<dt>Availability</dt><dd>" in detail_html
    assert 'datetime="2000-01-01T00:00:00+00:00"' in detail_html
    assert 'datetime="2999-01-01T00:00:00+00:00"' in detail_html
    assert 'data-dynamic-labs-time="instructor">2000-01-01 00:00 UTC</time>' in detail_html
    assert "data-server-utc-clock" in detail_html
    assert 'data-availability-calendar-button="from"' in detail_html
    assert 'data-availability-calendar-button="until"' in detail_html
    assert 'data-availability-hour="from"' in detail_html
    assert 'data-availability-minute="until"' in detail_html
    assert 'name="available_from"' in detail_html
    assert 'name="available_until"' in detail_html
    assert "Available until must be after available from." in detail_html
    assert "snapshot-option-correct" in detail_html
    assert 'class="snapshot-correct-label">correct</strong>' in detail_html
    assert "snapshot-option-correct" in preview_html
    assert bad_window_response.status_code == 400
    assert bad_window_response.get_json()["error"] == (
        "available_until must be after available_from"
    )


def test_publication_routes_require_instructor_and_student_auth(app, client):
    version = _seed_generated_quiz(app, client)

    assert client.get("/student/api/quizzes").status_code == 401
    assert client.get("/instructor/api/quiz-versions").status_code == 401
    assert client.post(
        f"/instructor/api/quiz-versions/{version['id']}/publish"
    ).status_code == 401
