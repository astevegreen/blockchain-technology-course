import json

from app.attempts import save_answer
from app.db import get_db
from app.ingest import ingest_json
from app.students import get_student_by_identifier


HEADERS = {"X-Test-Instructor": "teacher"}


def _bank():
    return {
        "lesson_id": "grading_integration_lesson",
        "lesson_title": "Grading Integration Lesson",
        "topic": "bitcoin",
        "questions": [
            {
                "id": "written1",
                "question_stem": "Explain why confirmations matter.",
                "question_type": "written",
                "difficulty_level": 3,
                "explanation": "Confirmations increase the work required to reverse history.",
            }
        ],
    }


def _template_payload(result_policy="score_after_release", timer_minutes=None):
    return {
        "title": "Written Grading Template",
        "description": "Template for written grading",
        "criteria": {
            "lesson_ids": ["grading_integration_lesson"],
            "question_types": ["written"],
        },
        "question_count": 1,
        "selection_policy": "random",
        "timer_minutes": timer_minutes,
        "attempt_limit": 1,
        "result_policy": result_policy,
    }


def _seed_written_quiz(app, client, *, result_policy="score_after_release", timer_minutes=None):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
    template = client.post(
        "/instructor/api/templates",
        json=_template_payload(result_policy=result_policy, timer_minutes=timer_minutes),
        headers=HEADERS,
    ).get_json()["template"]
    version = client.post(
        f"/instructor/api/templates/{template['id']}/generate",
        json={"random_seed": f"integration-{result_policy}-{timer_minutes}"},
        headers=HEADERS,
    ).get_json()["quiz_version"]
    client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "title": f"Written {result_policy}",
            "available_from": "2000-01-01T00:00:00+00:00",
            "available_until": "2999-01-01T00:00:00+00:00",
        },
        headers=HEADERS,
    )
    return client.post(
        f"/instructor/api/quiz-versions/{version['id']}/publish",
        headers=HEADERS,
    ).get_json()["quiz_version"]


def _enroll_student(client):
    response = client.post("/student/enroll")
    text = response.get_data(as_text=True)
    marker = '<p id="student-identifier"><code>'
    start = text.index(marker) + len(marker)
    end = text.index("</code>", start)
    return text[start:end]


def test_instructor_grades_written_attempt_and_releases_results(app, client):
    version = _seed_written_quiz(app, client, result_policy="score_after_release")
    _enroll_student(client)
    attempt = client.post(
        f"/student/api/quizzes/{version['id']}/start"
    ).get_json()["attempt"]
    question_id = attempt["questions"][0]["id"]
    submit_response = client.post(
        f"/student/api/attempts/{attempt['id']}/submit",
        json={
            "answers": [
                {
                    "question_id": question_id,
                    "written_response": "Because each block adds more work.",
                }
            ]
        },
    )
    hidden_result = client.get(
        f"/student/api/attempts/{attempt['id']}/results"
    ).get_json()["result"]
    queue_response = client.get("/instructor/api/grading/written", headers=HEADERS)
    queue_item = queue_response.get_json()["items"][0]
    grade_response = client.post(
        f"/instructor/api/attempt-answers/{queue_item['answer_id']}/grade",
        json={"points_awarded": 0.5},
        headers=HEADERS,
    )
    graded_hidden_result = client.get(
        f"/student/api/attempts/{attempt['id']}/results"
    ).get_json()["result"]
    release_response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/release-results",
        headers=HEADERS,
    )
    visible_result = client.get(
        f"/student/api/attempts/{attempt['id']}/results"
    ).get_json()["result"]

    assert submit_response.get_json()["attempt"]["status"] == "needs_grading"
    assert hidden_result["score_visible"] is False
    assert queue_response.status_code == 200
    assert queue_item["written_response"] == "Because each block adds more work."
    assert grade_response.status_code == 200
    assert grade_response.get_json()["result"]["attempt"]["status"] == "graded"
    assert graded_hidden_result["score_visible"] is False
    assert release_response.get_json()["quiz_version"]["results_released_at"] is not None
    assert visible_result["score_visible"] is True
    assert visible_result["review_visible"] is False
    assert visible_result["score"] == 0.5


def test_score_and_answer_policy_exposes_review_after_grading(app, client):
    version = _seed_written_quiz(
        app,
        client,
        result_policy="score_and_answers_after_grading",
    )
    _enroll_student(client)
    attempt = client.post(
        f"/student/api/quizzes/{version['id']}/start"
    ).get_json()["attempt"]
    question_id = attempt["questions"][0]["id"]
    client.post(
        f"/student/api/attempts/{attempt['id']}/submit",
        json={
            "answers": [
                {
                    "question_id": question_id,
                    "written_response": "A written explanation",
                }
            ]
        },
    )
    queue_item = client.get(
        "/instructor/api/grading/written",
        headers=HEADERS,
    ).get_json()["items"][0]
    client.post(
        f"/instructor/api/attempt-answers/{queue_item['answer_id']}/grade",
        json={"points_awarded": 1},
        headers=HEADERS,
    )
    result = client.get(
        f"/student/api/attempts/{attempt['id']}/results"
    ).get_json()["result"]
    html = client.get(f"/student/attempts/{attempt['id']}/results").get_data(
        as_text=True
    )

    assert result["score_visible"] is True
    assert result["review_visible"] is True
    assert result["questions"][0]["written_response"] == "A written explanation"
    assert "Correct answer" not in html
    assert "A written explanation" in html


def test_expired_written_answer_can_be_graded_without_status_change(app, client):
    version = _seed_written_quiz(
        app,
        client,
        result_policy="score_after_grading",
        timer_minutes=1,
    )
    identifier = _enroll_student(client)
    attempt = client.post(
        f"/student/api/quizzes/{version['id']}/start"
    ).get_json()["attempt"]
    question_id = attempt["questions"][0]["id"]
    with app.app_context():
        student = get_student_by_identifier(identifier)
        save_answer(
            attempt["id"],
            student,
            {"question_id": question_id, "written_response": "Expired response"},
        )
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", attempt["id"]),
        )
        get_db().commit()

    expired = client.get(
        f"/student/api/attempts/{attempt['id']}"
    ).get_json()["attempt"]
    queue_item = client.get(
        "/instructor/api/grading/written",
        headers=HEADERS,
    ).get_json()["items"][0]
    graded = client.post(
        f"/instructor/api/attempt-answers/{queue_item['answer_id']}/grade",
        json={"points_awarded": 0.25},
        headers=HEADERS,
    ).get_json()["result"]["attempt"]

    assert expired["status"] == "expired"
    assert queue_item["attempt_status"] == "expired"
    assert graded["status"] == "expired"
    assert graded["score"] == 0.25
