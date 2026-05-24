import json

import pytest

from app.attempts import get_student_attempt, save_answer, start_or_resume_attempt, submit_attempt
from app.db import get_db
from app.generation import generate_quiz_version
from app.grading import (
    GradingError,
    get_student_result,
    grade_written_answer,
    list_written_grading_queue,
    release_quiz_review,
    release_quiz_results,
)
from app.ingest import ingest_json
from app.publication import set_quiz_version_visibility
from app.students import enroll_open_student


def _bank():
    return {
        "lesson_id": "grading_lesson",
        "lesson_title": "Grading Lesson",
        "topic": "bitcoin",
        "questions": [
            {
                "id": "mc1",
                "question_stem": "Which answer is correct?",
                "correct_answer": "Correct answer",
                "incorrect_answers": ["Wrong answer", "Also wrong"],
                "difficulty_level": 1,
                "explanation": "Multiple-choice explanation.",
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


def _published_version(question_types, **overrides):
    payload = {
        "title": "Grading Quiz",
        "criteria": {
            "lesson_ids": ["grading_lesson"],
            "question_types": question_types,
        },
        "question_count": len(question_types),
        "random_seed": "grading-seed-" + "-".join(question_types),
        "question_order_policy": "fixed",
        "option_order_policy": "fixed",
    }
    payload.update(overrides)
    version = generate_quiz_version(payload, actor_sub="teacher")
    return set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")


def _student():
    return enroll_open_student()


def _correct_option_id(question_id):
    return get_db().execute(
        """
        SELECT id
        FROM quiz_version_options
        WHERE quiz_version_question_id = ? AND is_correct = 1
        """,
        (question_id,),
    ).fetchone()["id"]


def _submit_written_attempt(version, student, response="Student response"):
    attempt = start_or_resume_attempt(version["id"], student)
    question_id = attempt["questions"][0]["id"]
    submitted = submit_attempt(
        attempt["id"],
        student,
        answers=[{"question_id": question_id, "written_response": response}],
    )
    answer = get_db().execute(
        """
        SELECT *
        FROM attempt_answers
        WHERE attempt_id = ?
        """,
        (attempt["id"],),
    ).fetchone()
    return submitted, answer


def test_manual_written_grading_finalizes_score_and_preserves_response(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(["written"])
        student = _student()
        attempt, answer = _submit_written_attempt(version, student)

        before_result = get_student_result(attempt["id"], student)
        queue = list_written_grading_queue()
        graded = grade_written_answer(
            answer["id"],
            0.75,
            actor_sub="teacher",
        )
        after_result = get_student_result(attempt["id"], student)
        queue_after = list_written_grading_queue()
        stored_answer = get_db().execute(
            """
            SELECT written_response, points_awarded, graded_by
            FROM attempt_answers
            WHERE id = ?
            """,
            (answer["id"],),
        ).fetchone()

    assert attempt["status"] == "needs_grading"
    assert before_result["score_visible"] is False
    assert queue[0]["answer_id"] == answer["id"]
    assert graded["attempt"]["status"] == "graded"
    assert graded["attempt"]["score"] == 0.75
    assert stored_answer["written_response"] == "Student response"
    assert stored_answer["points_awarded"] == 0.75
    assert stored_answer["graded_by"] == "teacher"
    assert after_result["score_visible"] is True
    assert after_result["score"] == 0.75
    assert queue_after == []


def test_written_grading_rejects_points_above_possible(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(["written"])
        student = _student()
        _attempt, answer = _submit_written_attempt(version, student)

        with pytest.raises(GradingError, match="exceeds"):
            grade_written_answer(answer["id"], 2)


def test_expired_written_grading_preserves_expired_status(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(["written"], timer_minutes=1)
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        question_id = attempt["questions"][0]["id"]
        save_answer(
            attempt["id"],
            student,
            {"question_id": question_id, "written_response": "Saved written response"},
        )
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", attempt["id"]),
        )
        get_db().commit()

        expired = get_student_attempt(attempt["id"], student)
        queue = list_written_grading_queue()
        graded = grade_written_answer(queue[0]["answer_id"], 0.5, actor_sub="teacher")
        result = get_student_result(attempt["id"], student)

    assert expired["status"] == "expired"
    assert queue[0]["attempt_status"] == "expired"
    assert graded["attempt"]["status"] == "expired"
    assert graded["attempt"]["score"] == 0.5
    assert result["status"] == "expired"
    assert result["score_visible"] is True
    assert result["score"] == 0.5


def test_student_result_visibility_policy_matrix(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        student = _student()
        policies = [
            "score_after_grading",
            "score_and_answers_after_grading",
            "score_after_release",
            "score_and_answers_after_release",
            "hidden",
        ]
        results = {}
        for policy in policies:
            version = _published_version(
                ["multiple_choice"],
                title=f"Policy {policy}",
                result_policy=policy,
                random_seed=f"policy-{policy}",
            )
            attempt = start_or_resume_attempt(version["id"], student)
            question_id = attempt["questions"][0]["id"]
            submit_attempt(
                attempt["id"],
                student,
                answers=[
                    {
                        "question_id": question_id,
                        "selected_option_id": _correct_option_id(question_id),
                    }
                ],
            )
            before_release = get_student_result(attempt["id"], student)
            release_quiz_results(version["id"], actor_sub="teacher")
            after_release = get_student_result(attempt["id"], student)
            results[policy] = (before_release, after_release)

    assert results["score_after_grading"][0]["score_visible"] is True
    assert results["score_after_grading"][0]["review_visible"] is False
    assert results["score_and_answers_after_grading"][0]["score_visible"] is True
    assert results["score_and_answers_after_grading"][0]["review_visible"] is True
    assert results["score_and_answers_after_grading"][0]["questions"][0][
        "correct_option_text"
    ] == "Correct answer"
    assert results["score_after_release"][0]["score_visible"] is False
    assert results["score_after_release"][1]["score_visible"] is True
    assert results["score_after_release"][1]["review_visible"] is False
    assert results["score_and_answers_after_release"][0]["review_visible"] is False
    assert results["score_and_answers_after_release"][1]["review_visible"] is True
    assert results["hidden"][0]["score_visible"] is False
    assert results["hidden"][1]["score_visible"] is False


def test_quiz_review_can_be_revealed_after_score_only_policy(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = _published_version(
            ["multiple_choice"],
            title="Review release policy",
            result_policy="score_after_grading",
            random_seed="review-release-policy",
        )
        student = _student()
        attempt = start_or_resume_attempt(version["id"], student)
        question_id = attempt["questions"][0]["id"]
        submit_attempt(
            attempt["id"],
            student,
            answers=[
                {
                    "question_id": question_id,
                    "selected_option_id": _correct_option_id(question_id),
                }
            ],
        )

        before_release = get_student_result(attempt["id"], student)
        released_version = release_quiz_review(version["id"], actor_sub="teacher")
        after_release = get_student_result(attempt["id"], student)

    assert before_release["score_visible"] is True
    assert before_release["review_visible"] is False
    assert before_release["questions"] == []
    assert released_version["review_released_at"] is not None
    assert after_release["review_released_at"] == released_version["review_released_at"]
    assert after_release["score_visible"] is True
    assert after_release["review_visible"] is True
    assert after_release["questions"][0]["correct_option_text"] == "Correct answer"
