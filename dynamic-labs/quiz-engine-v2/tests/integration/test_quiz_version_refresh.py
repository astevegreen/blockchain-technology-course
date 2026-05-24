import json

from app.attempts import start_or_resume_attempt
from app.db import get_db
from app.generation import generate_quiz_version
from app.ingest import ingest_json
from app.publication import set_quiz_version_visibility
from app.question_editing import edit_question
from app.question_pool import list_eligible_question_ids
from app.quiz_versions import refresh_hidden_quiz_version_questions
from app.students import enroll_open_student


HEADERS = {"X-Test-Instructor": "teacher"}


def _bank():
    return {
        "lesson_id": "refresh_lesson",
        "lesson_title": "Refresh Lesson",
        "topic": "bitcoin",
        "questions": [
            {
                "id": "q1",
                "question_stem": "Original refresh question?",
                "correct_answer": "Original correct",
                "incorrect_answers": ["Original wrong"],
                "explanation": "Original explanation",
                "difficulty_level": 2,
                "tags": ["refresh"],
            }
        ],
    }


def _generate(seed):
    return generate_quiz_version(
        {
            "title": f"Refresh Quiz {seed}",
            "criteria": {"lesson_ids": ["refresh_lesson"]},
            "question_count": 1,
            "random_seed": seed,
            "question_order_policy": "fixed",
            "option_order_policy": "fixed",
        },
        actor_sub="teacher",
    )


def _edit_payload(question_id):
    return {
        "expected_question_id": question_id,
        "question_stem": "Edited refresh question?",
        "explanation": "Edited explanation",
        "difficulty_level": 3,
        "topic": "ethereum",
        "question_tags": ["refresh-edited"],
        "options": [
            {"option_text": "Edited correct", "is_correct": True},
            {"option_text": "Edited wrong", "is_correct": False},
        ],
    }


def test_hidden_quiz_refresh_updates_snapshots_to_latest_question_revision(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        original_question_id = list_eligible_question_ids(
            lesson_ids=["refresh_lesson"]
        )[0]
        version = _generate("before-edit")
        edit = edit_question(
            original_question_id,
            _edit_payload(original_question_id),
            actor_sub="teacher",
        )

    page = client.get(f"/instructor/quiz-versions/{version['id']}", headers=HEADERS)
    unauthorized = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/refresh-question-revisions"
    )
    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/refresh-question-revisions",
        headers=HEADERS,
    )
    refreshed = response.get_json()["result"]["quiz_version"]

    with app.app_context():
        audit = get_db().execute(
            """
            SELECT details_json
            FROM audit_events
            WHERE event_type = 'quiz_version.questions_refreshed'
            """
        ).fetchone()

    assert page.status_code == 200
    assert "Refresh question revisions" in page.get_data(as_text=True)
    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert response.get_json()["result"]["refreshed_question_count"] == 1
    assert response.get_json()["result"]["replacements"] == [
        {
            "old_source_question_id": original_question_id,
            "new_source_question_id": edit["new_question_id"],
            "position": 1,
        }
    ]
    assert refreshed["generation_snapshot"]["selected_question_ids"] == [
        edit["new_question_id"]
    ]
    assert refreshed["questions"][0]["source_question_id"] == edit["new_question_id"]
    assert refreshed["questions"][0]["snapshot_question_stem"] == (
        "Edited refresh question?"
    )
    assert refreshed["questions"][0]["options"][0]["option_text"] == "Edited correct"
    assert "Edited refresh question?" not in audit["details_json"]
    assert "Edited correct" not in audit["details_json"]


def test_published_quiz_refresh_is_rejected(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        question_id = list_eligible_question_ids(lesson_ids=["refresh_lesson"])[0]
        version = _generate("published")
        edit_question(question_id, _edit_payload(question_id), actor_sub="teacher")
        set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")

    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/refresh-question-revisions",
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert "only hidden quiz versions" in response.get_json()["error"]


def test_hidden_quiz_with_attempts_refresh_is_rejected(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        question_id = list_eligible_question_ids(lesson_ids=["refresh_lesson"])[0]
        version = _generate("attempted")
        set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")
        identifier = enroll_open_student()
        start_or_resume_attempt(version["id"], identifier)
        set_quiz_version_visibility(version["id"], "hidden", actor_sub="teacher")
        edit_question(question_id, _edit_payload(question_id), actor_sub="teacher")

    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/refresh-question-revisions",
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert "with attempts cannot refresh" in response.get_json()["error"]
