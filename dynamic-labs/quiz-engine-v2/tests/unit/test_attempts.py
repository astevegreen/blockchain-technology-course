import json

import pytest

from app.attempts import (
    AttemptError,
    AttemptIncompleteError,
    attempt_usage,
    effective_attempt_allowance,
    finalize_expired_attempt,
    finalize_expired_attempts,
    get_student_attempt,
    grant_extra_attempt,
    save_answer,
    start_or_resume_attempt,
    submit_attempt,
    void_attempt,
)
from app.db import get_db
from app.generation import generate_quiz_version
from app.ingest import ingest_json
from app.publication import (
    set_quiz_version_visibility,
    update_quiz_version_metadata,
)
from app.students import enroll_open_student


def _bank():
    return {
        "lesson_id": "attempt_lesson",
        "lesson_title": "Attempt Lesson",
        "topic": "bitcoin",
        "questions": [
            {
                "id": "mc1",
                "question_stem": "Which answer is correct?",
                "correct_answer": "Correct answer",
                "incorrect_answers": ["Wrong answer", "Also wrong"],
                "difficulty_level": 1,
                "explanation": "The correct answer is marked only for instructors.",
            },
            {
                "id": "mc2",
                "question_stem": "Which answer is second?",
                "correct_answer": "Second correct answer",
                "incorrect_answers": ["Second wrong answer"],
                "difficulty_level": 2,
                "explanation": "Second explanation.",
            },
            {
                "id": "written1",
                "question_stem": "Explain the concept.",
                "question_type": "written",
                "difficulty_level": 3,
                "explanation": "Written explanation.",
            },
        ],
    }


def _student():
    return enroll_open_student()


def _version(question_types=None, **overrides):
    question_types = question_types or ["multiple_choice"]
    payload = {
        "title": "Attempt Quiz",
        "criteria": {
            "lesson_ids": ["attempt_lesson"],
            "question_types": question_types,
        },
        "question_count": 1,
        "random_seed": "attempt-seed",
        "question_order_policy": "random_per_attempt",
        "option_order_policy": "random_per_attempt",
    }
    payload.update(overrides)
    return generate_quiz_version(payload, actor_sub="teacher")


def _published_version(question_types=None, **overrides):
    version = _version(question_types=question_types, **overrides)
    return set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")


def _correct_option_id(question_id):
    return get_db().execute(
        """
        SELECT id
        FROM quiz_version_options
        WHERE quiz_version_question_id = ? AND is_correct = 1
        """,
        (question_id,),
    ).fetchone()["id"]


def _incorrect_option_id(question_id):
    return get_db().execute(
        """
        SELECT id
        FROM quiz_version_options
        WHERE quiz_version_question_id = ? AND is_correct = 0
        ORDER BY id
        """,
        (question_id,),
    ).fetchone()["id"]


def test_start_resume_records_order_and_redacts_student_payload(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(question_count=2)
        student = _student()

        attempt = start_or_resume_attempt(version["id"], student)
        resumed = start_or_resume_attempt(version["id"], student)

    payload = json.dumps(attempt)
    assert attempt["id"] == resumed["id"]
    assert attempt["status"] == "in_progress"
    assert len(attempt["question_order"]) == 2
    assert len(attempt["option_order"]) >= 4
    assert "is_correct" not in payload
    assert "snapshot_explanation" not in payload
    assert "Correct answer" in payload


def test_random_once_order_is_shared_across_students(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(
            question_count=2,
            question_order_mode="random_once",
            option_order_mode="random_once",
        )
        first = start_or_resume_attempt(version["id"], _student())
        second = start_or_resume_attempt(version["id"], _student())

    assert version["question_order_policy"] == "fixed"
    assert version["option_order_policy"] == "fixed"
    assert first["question_order"] == second["question_order"]
    assert first["option_order"] == second["option_order"]


def test_default_order_is_randomized_per_attempt(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(question_count=2)
        attempts = [
            start_or_resume_attempt(version["id"], _student())
            for _index in range(5)
        ]

    assert version["question_order_policy"] == "random_per_attempt"
    assert version["option_order_policy"] == "random_per_attempt"
    assert (
        len({tuple(attempt["question_order"]) for attempt in attempts}) > 1
        or len({tuple(attempt["option_order"]) for attempt in attempts}) > 1
    )


def test_answer_save_validates_and_upserts_per_question(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version()
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        question_id = attempt["questions"][0]["id"]
        correct_option_id = _correct_option_id(question_id)
        incorrect_option_id = _incorrect_option_id(question_id)

        save_answer(
            attempt["id"],
            student,
            {"question_id": question_id, "selected_option_id": incorrect_option_id},
        )
        updated = save_answer(
            attempt["id"],
            student,
            {"question_id": question_id, "selected_option_id": correct_option_id},
        )
        answer_count = get_db().execute(
            "SELECT COUNT(*) FROM attempt_answers WHERE attempt_id = ?",
            (attempt["id"],),
        ).fetchone()[0]

        with pytest.raises(AttemptError, match="question"):
            save_answer(
                attempt["id"],
                student,
                {"question_id": 999999, "selected_option_id": correct_option_id},
            )

        with pytest.raises(AttemptError, match="selected option"):
            save_answer(
                attempt["id"],
                student,
                {"question_id": question_id, "selected_option_id": 999999},
            )

    assert answer_count == 1
    assert updated["questions"][0]["answer"]["selected_option_id"] == correct_option_id


def test_submit_multiple_choice_attempt_is_graded_and_idempotent(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version()
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        question_id = attempt["questions"][0]["id"]
        correct_option_id = _correct_option_id(question_id)

        submitted = submit_attempt(
            attempt["id"],
            student,
            answers=[
                {
                    "question_id": question_id,
                    "selected_option_id": correct_option_id,
                }
            ],
        )
        duplicate = submit_attempt(
            attempt["id"],
            student,
            answers=[
                {
                    "question_id": question_id,
                    "selected_option_id": _incorrect_option_id(question_id),
                }
            ],
        )
        stored = get_db().execute(
            "SELECT status, score, max_score FROM attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()

    assert submitted["status"] == "graded"
    assert duplicate["status"] == "graded"
    assert stored["status"] == "graded"
    assert stored["score"] == 1.0
    assert stored["max_score"] == 1.0


def test_submit_written_attempt_needs_grading(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(question_types=["written"])
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        question_id = attempt["questions"][0]["id"]

        submitted = submit_attempt(
            attempt["id"],
            student,
            answers=[
                {
                    "question_id": question_id,
                    "written_response": "My written answer",
                }
            ],
        )
        stored_answer = get_db().execute(
            """
            SELECT written_response, points_awarded
            FROM attempt_answers
            WHERE attempt_id = ?
            """,
            (attempt["id"],),
        ).fetchone()

    assert submitted["status"] == "needs_grading"
    assert stored_answer["written_response"] == "My written answer"
    assert stored_answer["points_awarded"] is None


def test_submit_requires_every_question_before_finalizing(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(
            question_types=["multiple_choice", "written"],
            question_count=2,
        )
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        mc_question = next(
            question
            for question in attempt["questions"]
            if question["question_type"] == "multiple_choice"
        )
        written_question = next(
            question
            for question in attempt["questions"]
            if question["question_type"] == "written"
        )

        with pytest.raises(AttemptIncompleteError) as exc:
            submit_attempt(
                attempt["id"],
                student,
                answers=[
                    {
                        "question_id": mc_question["id"],
                        "selected_option_id": _correct_option_id(mc_question["id"]),
                    },
                    {
                        "question_id": written_question["id"],
                        "written_response": "   ",
                    },
                ],
            )

        stored = get_db().execute(
            "SELECT status, submitted_at, score, max_score FROM attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()
        answer_count = get_db().execute(
            "SELECT COUNT(*) FROM attempt_answers WHERE attempt_id = ?",
            (attempt["id"],),
        ).fetchone()[0]

    assert exc.value.missing_question_ids == [written_question["id"]]
    assert stored["status"] == "in_progress"
    assert stored["submitted_at"] is None
    assert stored["score"] is None
    assert stored["max_score"] is None
    assert answer_count == 0


def test_submit_allows_existing_saved_answers_to_complete_attempt(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(question_count=2)
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        first_question = attempt["questions"][0]
        second_question = attempt["questions"][1]
        save_answer(
            attempt["id"],
            student,
            {
                "question_id": first_question["id"],
                "selected_option_id": _correct_option_id(first_question["id"]),
            },
        )

        submitted = submit_attempt(
            attempt["id"],
            student,
            answers=[
                {
                    "question_id": second_question["id"],
                    "selected_option_id": _correct_option_id(second_question["id"]),
                }
            ],
        )

    assert submitted["status"] == "graded"
    assert submitted["questions"][0]["answer"] is not None
    assert submitted["questions"][1]["answer"] is not None


def test_start_rejects_unavailable_and_archived_quizzes(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        hidden = _version()
        future = _published_version()
        archived = _published_version(random_seed="archived")
        update_quiz_version_metadata(
            future["id"],
            {"available_from": "2999-01-01T00:00:00+00:00"},
            actor_sub="teacher",
        )
        set_quiz_version_visibility(archived["id"], "archived", actor_sub="teacher")
        student = _student()

        with pytest.raises(AttemptError, match="available"):
            start_or_resume_attempt(hidden["id"], student)
        with pytest.raises(AttemptError, match="available"):
            start_or_resume_attempt(future["id"], student)
        with pytest.raises(AttemptError, match="available"):
            start_or_resume_attempt(archived["id"], student)


def test_student_cannot_access_another_students_attempt(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version()
        owner = _student()
        other = _student()
        attempt = start_or_resume_attempt(version["id"], owner)

        with pytest.raises(AttemptError, match="not found"):
            get_student_attempt(attempt["id"], other)


def test_attempt_limit_grant_and_attempt_number_allocation(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(attempt_limit=1)
        student = _student()
        first = start_or_resume_attempt(version["id"], student)
        first_question_id = first["questions"][0]["id"]

        submit_attempt(
            first["id"],
            student,
            answers=[
                {
                    "question_id": first_question_id,
                    "selected_option_id": _correct_option_id(first_question_id),
                }
            ],
        )
        with pytest.raises(AttemptError, match="attempt limit reached"):
            start_or_resume_attempt(version["id"], student)

        allowance_before = effective_attempt_allowance(version["id"], student.id)
        grant = grant_extra_attempt(
            version["id"],
            student.identifier,
            extra_attempts=2,
            reason="retake",
            actor_sub="teacher",
        )
        allowance_after = effective_attempt_allowance(version["id"], student.id)
        second = start_or_resume_attempt(version["id"], student)

    assert allowance_before["allowance"] == 1
    assert grant["allowance"]["allowance"] == 3
    assert allowance_after["extra_attempts"] == 2
    assert second["attempt_number"] == 2


def test_void_attempt_records_state_usage_and_audit(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version()
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)

        voided = void_attempt(attempt["id"], reason="administrative", actor_sub="teacher")
        duplicate = void_attempt(attempt["id"], actor_sub="teacher")
        usage = attempt_usage(version["id"], student.id)
        audit_count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM audit_events
            WHERE event_type = 'attempt.voided'
              AND object_id = ?
            """,
            (attempt["id"],),
        ).fetchone()[0]
        stored = get_db().execute(
            "SELECT status, voided_at FROM attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()

    assert voided["status"] == "voided"
    assert duplicate["status"] == "voided"
    assert stored["status"] == "voided"
    assert stored["voided_at"] is not None
    assert usage["total_attempts"] == 1
    assert usage["voided_attempts"] == 1
    assert audit_count == 1


def test_lazy_expiration_scores_saved_multiple_choice_and_is_idempotent(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(timer_minutes=1)
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        question_id = attempt["questions"][0]["id"]
        save_answer(
            attempt["id"],
            student,
            {"question_id": question_id, "selected_option_id": _correct_option_id(question_id)},
        )
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", attempt["id"]),
        )
        get_db().commit()

        expired = get_student_attempt(attempt["id"], student)
        duplicate = finalize_expired_attempt(attempt["id"])
        audit_count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM audit_events
            WHERE event_type = 'attempt.expired'
              AND object_id = ?
            """,
            (attempt["id"],),
        ).fetchone()[0]
        stored = get_db().execute(
            "SELECT status, score, max_score, expired_at FROM attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()

    assert expired["status"] == "expired"
    assert duplicate is False
    assert stored["score"] == 1.0
    assert stored["max_score"] == 1.0
    assert stored["expired_at"] is not None
    assert audit_count == 1


def test_expiration_blocks_late_save_and_submit_returns_expired(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(timer_minutes=1)
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        question_id = attempt["questions"][0]["id"]
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", attempt["id"]),
        )
        get_db().commit()

        with pytest.raises(AttemptError, match="final"):
            save_answer(
                attempt["id"],
                student,
                {
                    "question_id": question_id,
                    "selected_option_id": _correct_option_id(question_id),
                },
            )
        submitted = submit_attempt(attempt["id"], student)

    assert submitted["status"] == "expired"


def test_expired_unanswered_written_is_zero_but_saved_written_needs_grading(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        unanswered_version = _published_version(
            question_types=["written"],
            timer_minutes=1,
        )
        saved_version = _published_version(
            question_types=["written"],
            timer_minutes=1,
            random_seed="saved-written",
        )
        student = _student()
        unanswered = start_or_resume_attempt(unanswered_version["id"], student)
        saved = start_or_resume_attempt(saved_version["id"], student)
        saved_question_id = saved["questions"][0]["id"]
        save_answer(
            saved["id"],
            student,
            {"question_id": saved_question_id, "written_response": "Saved response"},
        )
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id IN (?, ?)",
            ("2000-01-01T00:00:00+00:00", unanswered["id"], saved["id"]),
        )
        get_db().commit()

        finalize_expired_attempt(unanswered["id"])
        finalize_expired_attempt(saved["id"])
        unanswered_row = get_db().execute(
            "SELECT status, score, max_score FROM attempts WHERE id = ?",
            (unanswered["id"],),
        ).fetchone()
        unanswered_answer = get_db().execute(
            "SELECT points_awarded FROM attempt_answers WHERE attempt_id = ?",
            (unanswered["id"],),
        ).fetchone()
        saved_row = get_db().execute(
            "SELECT status, score, max_score FROM attempts WHERE id = ?",
            (saved["id"],),
        ).fetchone()
        saved_answer = get_db().execute(
            "SELECT written_response, points_awarded FROM attempt_answers WHERE attempt_id = ?",
            (saved["id"],),
        ).fetchone()

    assert unanswered_row["status"] == "expired"
    assert unanswered_row["score"] == 0.0
    assert unanswered_row["max_score"] == 1.0
    assert unanswered_answer["points_awarded"] == 0.0
    assert saved_row["status"] == "expired"
    assert saved_row["score"] is None
    assert saved_answer["written_response"] == "Saved response"
    assert saved_answer["points_awarded"] is None


def test_expiration_grace_period_defers_finalization(app_factory):
    app = app_factory(TIMER_GRACE_SECONDS=30)
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(timer_minutes=1)
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id = ?",
            ("2026-05-20T11:59:50+00:00", attempt["id"]),
        )
        get_db().commit()

        expired = finalize_expired_attempt(
            attempt["id"],
            now="2026-05-20T12:00:00+00:00",
        )
        stored = get_db().execute(
            "SELECT status FROM attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()

    assert expired is False
    assert stored["status"] == "in_progress"


def test_worker_tick_finalizes_bounded_expired_attempt_batch(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(timer_minutes=1, attempt_limit=2)
        first_student = _student()
        second_student = _student()
        first = start_or_resume_attempt(version["id"], first_student)
        second = start_or_resume_attempt(version["id"], second_student)
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id IN (?, ?)",
            ("2000-01-01T00:00:00+00:00", first["id"], second["id"]),
        )
        get_db().commit()

        first_tick = finalize_expired_attempts(limit=1)
        second_tick = finalize_expired_attempts(limit=5)
        statuses = [
            row["status"]
            for row in get_db().execute(
                "SELECT status FROM attempts ORDER BY id"
            ).fetchall()
        ]

    assert first_tick["expired"] == 1
    assert second_tick["expired"] == 1
    assert statuses == ["expired", "expired"]
