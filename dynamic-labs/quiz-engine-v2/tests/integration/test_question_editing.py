import json

from app import create_app
from app.db import get_db, init_db
from app.generation import generate_quiz_version
from app.ingest import ingest_json
from app.migrate import FULL_EXPORT_TABLES, export_full_engine, import_full_engine
from app.question_editing import QuestionEditError, edit_question
from app.question_pool import list_eligible_question_ids


HEADERS = {"X-Test-Instructor": "teacher"}


def _bank():
    return {
        "lesson_id": "editing_lesson",
        "lesson_title": "Editing Lesson",
        "topic": "bitcoin",
        "tags": ["Bank Tag"],
        "questions": [
            {
                "id": "q1",
                "question_stem": "What text is in the original question?",
                "correct_answer": "Original answer",
                "incorrect_answers": ["Wrong answer"],
                "explanation": "Original explanation",
                "difficulty_level": 2,
                "topic": "bitcoin",
                "tags": ["Original Tag"],
            }
        ],
    }


def _generation_payload(seed):
    return {
        "title": f"Editing Quiz {seed}",
        "criteria": {"lesson_ids": ["editing_lesson"]},
        "question_count": 1,
        "selection_policy": "random",
        "random_seed": seed,
    }


def _edit_payload(question_id):
    return {
        "expected_question_id": question_id,
        "question_stem": "What text is in the edited question?",
        "explanation": "Edited explanation",
        "difficulty_level": 3,
        "topic": "ethereum",
        "question_tags": ["Edited Tag", "original tag"],
        "options": [
            {"option_text": "Edited answer", "is_correct": True},
            {"option_text": "Still wrong", "is_correct": False},
        ],
        "reason": "fix wording",
    }


def test_question_edit_api_creates_forward_revision_and_preserves_snapshots(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        original_question_id = list_eligible_question_ids(
            lesson_ids=["editing_lesson"]
        )[0]
        before_version = generate_quiz_version(
            _generation_payload("before-edit"),
            actor_sub="teacher",
        )

    unauthorized = client.post(
        f"/instructor/api/questions/{original_question_id}/revisions",
        json=_edit_payload(original_question_id),
    )
    response = client.post(
        f"/instructor/api/questions/{original_question_id}/revisions",
        json=_edit_payload(original_question_id),
        headers=HEADERS,
    )
    result = response.get_json()["result"]

    with app.app_context():
        db = get_db()
        eligible_ids = list_eligible_question_ids(lesson_ids=["editing_lesson"])
        old_row = db.execute(
            "SELECT status, superseded_at FROM questions WHERE id = ?",
            (original_question_id,),
        ).fetchone()
        new_row = db.execute(
            """
            SELECT question_stem, revises_question_id, difficulty_level, topic
            FROM questions
            WHERE id = ?
            """,
            (result["new_question_id"],),
        ).fetchone()
        after_version = generate_quiz_version(
            _generation_payload("after-edit"),
            actor_sub="teacher",
        )
        old_snapshot = db.execute(
            """
            SELECT snapshot_question_stem, source_question_id
            FROM quiz_version_questions
            WHERE quiz_version_id = ?
            """,
            (before_version["id"],),
        ).fetchone()
        audit = db.execute(
            """
            SELECT details_json
            FROM audit_events
            WHERE event_type = 'question.edited'
            """
        ).fetchone()

    assert unauthorized.status_code == 401
    assert response.status_code == 201
    assert result["original_question_id"] == original_question_id
    assert result["new_question_id"] != original_question_id
    assert set(result["changed_fields"]) == {
        "question_stem",
        "explanation",
        "difficulty_level",
        "topic",
        "question_tags",
        "options",
    }
    assert old_row["status"] == "superseded"
    assert old_row["superseded_at"]
    assert new_row["revises_question_id"] == original_question_id
    assert new_row["question_stem"] == "What text is in the edited question?"
    assert new_row["difficulty_level"] == 3
    assert new_row["topic"] == "ethereum"
    assert eligible_ids == [result["new_question_id"]]
    assert after_version["questions"][0]["source_question_id"] == result[
        "new_question_id"
    ]
    assert (
        after_version["questions"][0]["snapshot_question_stem"]
        == "What text is in the edited question?"
    )
    assert old_snapshot["source_question_id"] == original_question_id
    assert old_snapshot["snapshot_question_stem"] == (
        "What text is in the original question?"
    )
    assert "What text is in the edited question?" not in audit["details_json"]
    assert "Edited answer" not in audit["details_json"]


def test_question_edit_html_form_posts_and_redirects_to_new_question(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        question_id = list_eligible_question_ids(lesson_ids=["editing_lesson"])[0]

    form = client.get(f"/instructor/questions/{question_id}/edit", headers=HEADERS)
    post = client.post(
        f"/instructor/questions/{question_id}/edit",
        data={
            "expected_question_id": str(question_id),
            "question_stem": "HTML edited question?",
            "explanation": "HTML explanation",
            "difficulty_level": "4",
            "topic": "forensics",
            "question_tags": "html-edit, revised",
            "option_text_0": "HTML correct",
            "option_text_1": "HTML wrong",
            "correct_option": "0",
            "reason": "html path",
        },
        headers=HEADERS,
    )

    assert form.status_code == 200
    assert "Publish new question version" in form.get_data(as_text=True)
    assert "Already generated quizzes and attempts keep their existing snapshots" in (
        form.get_data(as_text=True)
    )
    assert post.status_code == 302
    assert "/instructor/questions/" in post.headers["Location"]


def test_question_edit_rejects_noop_and_stale_edits(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        question_id = list_eligible_question_ids(lesson_ids=["editing_lesson"])[0]
        payload = {
            "expected_question_id": question_id,
            "question_stem": "What text is in the original question?",
            "explanation": "Original explanation",
            "difficulty_level": 2,
            "topic": "bitcoin",
            "question_tags": ["original-tag"],
            "options": [
                {"option_text": "Original answer", "is_correct": True},
                {"option_text": "Wrong answer", "is_correct": False},
            ],
        }
        try:
            edit_question(question_id, payload, actor_sub="teacher")
        except QuestionEditError as exc:
            noop_error = str(exc)
        stale_payload = _edit_payload(question_id + 1)
        try:
            edit_question(question_id, stale_payload, actor_sub="teacher")
        except QuestionEditError as exc:
            stale_error = str(exc)

    assert "does not change" in noop_error
    assert "stale question edit" in stale_error


def test_full_export_import_preserves_question_edit_batches(app, tmp_path):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        question_id = list_eligible_question_ids(lesson_ids=["editing_lesson"])[0]
        edit_question(question_id, _edit_payload(question_id), actor_sub="teacher")
        payload = export_full_engine()
        expected_counts = {
            table: len(payload["tables"][table])
            for table in FULL_EXPORT_TABLES
        }

    fresh_app = create_app(
        {
            "DATABASE_PATH": str(tmp_path / "question-edit-roundtrip.sqlite"),
            "SECRET_KEY": "fresh-question-edit-secret",
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
        restored_edit_count = get_db().execute(
            "SELECT COUNT(*) FROM question_edit_batches"
        ).fetchone()[0]

    assert payload["tables"]["question_edit_batches"]
    assert restored_counts == expected_counts
    assert restored_edit_count == 1
