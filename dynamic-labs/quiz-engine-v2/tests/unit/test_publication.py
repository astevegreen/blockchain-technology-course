import json

import pytest

from app.db import get_db
from app.generation import generate_quiz_version
from app.ingest import ingest_json
from app.publication import (
    PublicationError,
    is_quiz_available_to_start,
    list_student_quiz_listings,
    list_student_visible_quizzes,
    normalize_optional_timestamp,
    set_quiz_version_visibility,
    update_quiz_version_metadata,
)


def _bank():
    return {
        "lesson_id": "publication_lesson",
        "lesson_title": "Publication Lesson",
        "topic": "bitcoin",
        "questions": [
            {
                "id": "q1",
                "question_stem": "Which network state can be published?",
                "correct_answer": "A generated quiz version.",
                "incorrect_answers": ["A mutable template."],
                "difficulty_level": 1,
                "explanation": "Published versions are fixed snapshots.",
            },
            {
                "id": "q2",
                "question_stem": "Which quizzes are student visible?",
                "correct_answer": "Published and in-window quizzes.",
                "incorrect_answers": ["Hidden quizzes."],
                "difficulty_level": 2,
                "explanation": "Visibility and availability are both enforced.",
            },
        ],
    }


def _generate_version(title="Publication Quiz"):
    ingest_json(json.dumps(_bank()), actor_sub="teacher")
    return generate_quiz_version(
        {
            "title": title,
            "description": "Initial description",
            "criteria": {"lesson_ids": ["publication_lesson"]},
            "question_count": 1,
            "random_seed": title,
        },
        actor_sub="teacher",
    )


def test_metadata_update_allows_admin_fields_and_audits(app):
    with app.app_context():
        version = _generate_version()
        updated = update_quiz_version_metadata(
            version["id"],
            {
                "title": "Published Title",
                "description": "Updated description",
                "available_from": "2026-05-20T12:00:00Z",
                "available_until": "2026-05-20T13:00:00+00:00",
                "instructor_notes": "Room 101",
            },
            actor_sub="teacher",
        )
        audit = get_db().execute(
            """
            SELECT event_type, object_id
            FROM audit_events
            WHERE event_type = 'quiz_version.metadata_updated'
            """
        ).fetchone()

    assert updated["title"] == "Published Title"
    assert updated["description"] == "Updated description"
    assert updated["available_from"] == "2026-05-20T12:00:00+00:00"
    assert updated["available_until"] == "2026-05-20T13:00:00+00:00"
    assert updated["instructor_notes"] == "Room 101"
    assert dict(audit) == {
        "event_type": "quiz_version.metadata_updated",
        "object_id": version["id"],
    }


def test_metadata_update_rejects_immutable_unknown_and_bad_windows(app):
    with app.app_context():
        version = _generate_version()

        with pytest.raises(PublicationError, match="immutable"):
            update_quiz_version_metadata(
                version["id"],
                {"attempt_limit": 2},
                actor_sub="teacher",
            )

        with pytest.raises(PublicationError, match="unsupported"):
            update_quiz_version_metadata(
                version["id"],
                {"visibility": "published"},
                actor_sub="teacher",
            )

        with pytest.raises(PublicationError, match="after"):
            update_quiz_version_metadata(
                version["id"],
                {
                    "available_from": "2026-05-20T13:00:00+00:00",
                    "available_until": "2026-05-20T12:00:00+00:00",
                },
                actor_sub="teacher",
            )

        with pytest.raises(PublicationError, match="after"):
            update_quiz_version_metadata(
                version["id"],
                {
                    "available_from": "2026-05-20T12:00:00+00:00",
                    "available_until": "2026-05-20T12:00:00+00:00",
                },
                actor_sub="teacher",
            )


def test_visibility_transitions_and_student_visible_filter(app):
    with app.app_context():
        hidden = _generate_version("Hidden Quiz")
        visible = _generate_version("Visible Quiz")
        future = _generate_version("Future Quiz")
        expired = _generate_version("Expired Quiz")
        archived = _generate_version("Archived Quiz")

        set_quiz_version_visibility(visible["id"], "published", actor_sub="teacher")
        set_quiz_version_visibility(future["id"], "published", actor_sub="teacher")
        update_quiz_version_metadata(
            future["id"],
            {"available_from": "2026-05-20T13:00:00+00:00"},
            actor_sub="teacher",
        )
        set_quiz_version_visibility(expired["id"], "published", actor_sub="teacher")
        update_quiz_version_metadata(
            expired["id"],
            {"available_until": "2026-05-20T11:00:00+00:00"},
            actor_sub="teacher",
        )
        set_quiz_version_visibility(archived["id"], "published", actor_sub="teacher")
        archived = set_quiz_version_visibility(
            archived["id"],
            "archived",
            actor_sub="teacher",
        )
        visible_quizzes = list_student_visible_quizzes(
            now="2026-05-20T12:00:00+00:00"
        )
        listed_quizzes = list_student_quiz_listings(
            now="2026-05-20T12:00:00+00:00"
        )
        audit_count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM audit_events
            WHERE event_type IN (
                'quiz_version.published',
                'quiz_version.archived'
            )
            """
        ).fetchone()[0]

    titles = [quiz["title"] for quiz in visible_quizzes]
    assert titles == ["Visible Quiz"]
    assert hidden["title"] not in titles
    assert future["title"] not in titles
    assert expired["title"] not in titles
    listing_by_title = {quiz["title"]: quiz for quiz in listed_quizzes}
    assert list(listing_by_title) == ["Visible Quiz", "Future Quiz"]
    assert listing_by_title["Visible Quiz"]["availability_status"] == "available"
    assert listing_by_title["Future Quiz"]["availability_status"] == "scheduled"
    assert hidden["title"] not in listing_by_title
    assert expired["title"] not in listing_by_title
    assert archived["archived_at"] is not None
    assert audit_count == 5


def test_availability_start_helper_and_timestamp_normalization():
    version = {
        "visibility": "published",
        "available_from": "2026-05-20T12:00:00+00:00",
        "available_until": "2026-05-20T13:00:00+00:00",
    }

    assert normalize_optional_timestamp("2026-05-20T12:00:00Z", "time") == (
        "2026-05-20T12:00:00+00:00"
    )
    assert is_quiz_available_to_start(
        version,
        now="2026-05-20T12:30:00+00:00",
    )
    assert not is_quiz_available_to_start(
        version,
        now="2026-05-20T11:59:59+00:00",
    )
    assert not is_quiz_available_to_start(
        version,
        now="2026-05-20T13:00:01+00:00",
    )
    assert not is_quiz_available_to_start({**version, "visibility": "hidden"})
