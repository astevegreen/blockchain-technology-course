import json

from app.attempts import start_or_resume_attempt, submit_attempt
from app.generation import generate_quiz_version
from app.ingest import ingest_json
from app.publication import set_quiz_version_visibility
from app.students import enroll_open_student
from app.ui import (
    answers_from_attempt_form,
    build_instructor_dashboard,
    build_student_quiz_list,
)


def test_answers_from_attempt_form_extracts_multiple_choice_and_written_values():
    attempt = {
        "questions": [
            {"id": 11, "question_type": "multiple_choice"},
            {"id": 12, "question_type": "written"},
        ]
    }
    form = {
        "question_11_option": "44",
        "question_12_written": "A short written answer.",
    }

    answers = answers_from_attempt_form(attempt, form)

    assert answers == [
        {"question_id": 11, "selected_option_id": "44"},
        {"question_id": 12, "written_response": "A short written answer."},
    ]


def test_student_quiz_list_marks_active_attempt_for_resume(app):
    with app.app_context():
        _seed_bank()
        version = _published_version(["multiple_choice"], question_count=1)
        student = enroll_open_student()
        attempt = start_or_resume_attempt(version["id"], student)

        view_model = build_student_quiz_list(student)

    assert view_model["student_identifier"] == student.identifier
    assert view_model["quizzes"][0]["title"] == "UI Test Quiz"
    assert view_model["quizzes"][0]["primary_action"] == "resume"
    assert view_model["quizzes"][0]["active_attempt"]["id"] == attempt["id"]
    assert "questions" not in view_model["quizzes"][0]


def test_student_quiz_list_links_latest_result_attempt(app):
    with app.app_context():
        _seed_bank()
        version = _published_version(["multiple_choice"], question_count=1)
        student = enroll_open_student()
        attempt = start_or_resume_attempt(version["id"], student)
        question = attempt["questions"][0]
        submit_attempt(
            attempt["id"],
            student,
            answers=[
                {
                    "question_id": question["id"],
                    "selected_option_id": question["options"][0]["id"],
                }
            ],
        )

        view_model = build_student_quiz_list(student)

    assert view_model["quizzes"][0]["primary_action"] == "start"
    assert view_model["quizzes"][0]["active_attempt"] is None
    assert view_model["quizzes"][0]["result_attempt"]["id"] == attempt["id"]


def test_instructor_dashboard_summarizes_operational_attention(app):
    with app.app_context():
        _seed_bank()
        version = _published_version(
            ["written"],
            question_count=1,
            title="Written UI Test Quiz",
        )
        student = enroll_open_student()
        attempt = start_or_resume_attempt(version["id"], student)
        submit_attempt(
            attempt["id"],
            student,
            answers=[
                {
                    "question_id": attempt["questions"][0]["id"],
                    "written_response": "Needs manual grading.",
                }
            ],
        )

        dashboard = build_instructor_dashboard()

    assert dashboard["counts"]["active_students"] == 1
    assert dashboard["counts"]["quiz_banks"] == 1
    assert dashboard["counts"]["templates"] == 0
    assert dashboard["counts"]["generated_quizzes"] == 1
    assert dashboard["counts"]["published_quizzes"] == 1
    assert dashboard["counts"]["needs_grading_attempts"] == 1
    assert dashboard["counts"]["written_grading_queue"] == 1
    assert dashboard["class_summary"]["selected_attempt_count"] == 1
    assert dashboard["recent_quizzes"][0]["title"] == "Written UI Test Quiz"


def _seed_bank():
    ingest_json(json.dumps(_bank()), actor_sub="teacher")


def _published_version(question_types, **overrides):
    payload = {
        "title": "UI Test Quiz",
        "criteria": {
            "lesson_ids": ["ui_lesson"],
            "question_types": question_types,
        },
        "question_count": len(question_types),
        "random_seed": "ui-test-seed-" + "-".join(question_types),
        "question_order_policy": "fixed",
        "option_order_policy": "fixed",
        "attempt_limit": 1,
        "result_policy": "score_after_grading",
    }
    payload.update(overrides)
    version = generate_quiz_version(payload, actor_sub="teacher")
    return set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")


def _bank():
    return {
        "lesson_id": "ui_lesson",
        "lesson_title": "UI Lesson",
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
