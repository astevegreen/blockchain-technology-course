import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.attempts import finalize_expired_attempts, start_or_resume_attempt
from app.db import get_db
from app.ingest import ingest_json
from app.students import get_student_by_identifier


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
        "title": "Student Attempt Template",
        "description": "Attempt integration template",
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
        },
        "question_count": 3,
        "selection_policy": "random",
        "timer_minutes": None,
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


def _seed_published_quiz(app, client, *, template_overrides=None, title=None):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]
    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    template_payload = _template_payload(source_bank, **(template_overrides or {}))
    template = client.post(
        "/instructor/api/templates",
        json=template_payload,
        headers=HEADERS,
    ).get_json()["template"]
    version = client.post(
        f"/instructor/api/templates/{template['id']}/generate",
        json={"random_seed": "student-attempt-seed"},
        headers=HEADERS,
    ).get_json()["quiz_version"]
    client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "title": title or "Student Visible Attempt Quiz",
            "description": "Answerable quiz",
            "available_from": "2000-01-01T00:00:00+00:00",
            "available_until": "2999-01-01T00:00:00+00:00",
        },
        headers=HEADERS,
    )
    return client.post(
        f"/instructor/api/quiz-versions/{version['id']}/publish",
        headers=HEADERS,
    ).get_json()["quiz_version"]


def test_student_starts_saves_resumes_and_submits_quiz(app, client):
    version = _seed_published_quiz(app, client)
    identifier = _enroll_student(client)

    list_response = client.get("/student/api/quizzes")
    start_response = client.post(f"/student/api/quizzes/{version['id']}/start")
    attempt = start_response.get_json()["attempt"]
    resume_response = client.post(f"/student/api/quizzes/{version['id']}/start")
    html_attempt = client.get(f"/student/attempts/{attempt['id']}").get_data(
        as_text=True
    )

    assert list_response.status_code == 200
    assert list_response.get_json()["quizzes"][0]["title"] == (
        "Student Visible Attempt Quiz"
    )
    assert start_response.status_code == 201
    assert resume_response.get_json()["attempt"]["id"] == attempt["id"]
    assert attempt["status"] == "in_progress"
    assert identifier in client.get("/student/quizzes").get_data(as_text=True)
    assert "correct" not in json.dumps(attempt)
    assert "Explanation" not in json.dumps(attempt)
    assert "Source lesson" not in html_attempt
    expected_option_rows = sum(
        len(question["options"])
        for question in attempt["questions"]
        if question["question_type"] == "multiple_choice"
    )
    assert html_attempt.count('class="quiz-answer-options"') == len(
        attempt["questions"]
    )
    assert html_attempt.count('class="quiz-answer-option-row"') == (
        expected_option_rows
    )
    assert html_attempt.count('class="quiz-answer-option-input"') == (
        expected_option_rows
    )
    assert html_attempt.count('class="quiz-answer-option-text"') == (
        expected_option_rows
    )

    first_question = attempt["questions"][0]
    second_question = attempt["questions"][1]
    first_option = first_question["options"][0]["id"]
    second_option = first_question["options"][1]["id"]
    other_question_option = second_question["options"][0]["id"]

    save_response = client.post(
        f"/student/api/attempts/{attempt['id']}/answers/{first_question['id']}",
        json={"selected_option_id": first_option},
    )
    duplicate_save_response = client.put(
        f"/student/api/attempts/{attempt['id']}/answers/{first_question['id']}",
        json={"selected_option_id": second_option},
    )
    html_after_auto_save = client.get(
        f"/student/attempts/{attempt['id']}"
    ).get_data(as_text=True)
    tampered_response = client.post(
        f"/student/api/attempts/{attempt['id']}/answers/{first_question['id']}",
        json={"selected_option_id": other_question_option},
    )
    submit_response = client.post(
        f"/student/api/attempts/{attempt['id']}/submit",
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_option_id": question["options"][0]["id"],
                }
                for question in attempt["questions"]
            ]
        },
    )
    duplicate_submit_response = client.post(
        f"/student/api/attempts/{attempt['id']}/submit",
        json={
            "answers": [
                {
                    "question_id": first_question["id"],
                    "selected_option_id": first_option,
                }
            ]
        },
    )

    with app.app_context():
        answer_count = get_db().execute(
            "SELECT COUNT(*) FROM attempt_answers WHERE attempt_id = ?",
            (attempt["id"],),
        ).fetchone()[0]
        attempt_row = get_db().execute(
            "SELECT status, max_score FROM attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()

    assert save_response.status_code == 200
    assert duplicate_save_response.status_code == 200
    saved_attempt = duplicate_save_response.get_json()["attempt"]
    assert saved_attempt["questions"][0]["answer"]["selected_option_id"] == (
        second_option
    )
    assert saved_attempt["questions"][0]["answer"]["saved_at"] is not None
    assert 'id="quiz-save-toast"' in html_after_auto_save
    assert 'data-auto-save-attempt="' in html_after_auto_save
    assert (
        f'data-save-url="/student/api/attempts/{attempt["id"]}/answers/'
        in html_after_auto_save
    )
    assert f'value="{second_option}"' in html_after_auto_save
    assert html_after_auto_save.count(" checked") == 1
    assert tampered_response.status_code == 400
    assert "selected option" in tampered_response.get_json()["error"]
    assert submit_response.status_code == 200
    assert submit_response.get_json()["attempt"]["status"] == "graded"
    assert duplicate_submit_response.status_code == 200
    assert duplicate_submit_response.get_json()["attempt"]["status"] == "graded"
    assert answer_count == len(attempt["questions"])
    assert attempt_row["status"] == "graded"
    assert attempt_row["max_score"] == len(attempt["questions"])


def test_student_results_highlight_correct_and_incorrect_answers(app, client):
    version = _seed_published_quiz(
        app,
        client,
        template_overrides={
            "result_policy": "score_and_answers_after_grading",
        },
        title="Highlighted Result Quiz",
    )
    _enroll_student(client)
    attempt = client.post(f"/student/api/quizzes/{version['id']}/start").get_json()[
        "attempt"
    ]

    with app.app_context():
        answers_by_question = {}
        for question in attempt["questions"]:
            rows = get_db().execute(
                """
                SELECT id, is_correct
                FROM quiz_version_options
                WHERE quiz_version_question_id = ?
                ORDER BY snapshot_order
                """,
                (question["id"],),
            ).fetchall()
            answers_by_question[question["id"]] = {
                "correct": next(row["id"] for row in rows if row["is_correct"]),
                "incorrect": next(row["id"] for row in rows if not row["is_correct"]),
            }

    answers = []
    for index, question in enumerate(attempt["questions"]):
        selected_key = "incorrect" if index == 1 else "correct"
        answers.append(
            {
                "question_id": question["id"],
                "selected_option_id": answers_by_question[question["id"]][selected_key],
            }
        )

    submit_response = client.post(
        f"/student/api/attempts/{attempt['id']}/submit",
        json={"answers": answers},
    )
    result_html = client.get(
        f"/student/attempts/{attempt['id']}/results"
    ).get_data(as_text=True)
    locked_attempt_html = client.get(
        f"/student/attempts/{attempt['id']}"
    ).get_data(as_text=True)

    assert submit_response.status_code == 200
    assert submit_response.get_json()["attempt"]["status"] == "graded"
    assert 'id="result-status">Graded</p>' in result_html
    assert "Status: graded" not in result_html
    assert "quiz-result-options" in result_html
    assert "quiz-result-option-correct" in result_html
    assert "quiz-result-option-selected-incorrect" in result_html
    assert "Your answer - correct" in result_html
    assert 'class="quiz-attempt-readonly" aria-label="Locked quiz response"' in locked_attempt_html
    assert 'class="quiz-answer-option-input"' in locked_attempt_html
    assert " disabled" in locked_attempt_html
    assert "quiz-result-option-correct" not in locked_attempt_html
    assert "quiz-result-option-selected-incorrect" not in locked_attempt_html


def test_incomplete_submit_keeps_attempt_open_and_marks_questions(app, client):
    version = _seed_published_quiz(app, client, title="Incomplete Guard Quiz")
    _enroll_student(client)
    attempt = client.post(f"/student/api/quizzes/{version['id']}/start").get_json()[
        "attempt"
    ]
    first_question = attempt["questions"][0]
    missing_question_ids = [question["id"] for question in attempt["questions"][1:]]

    api_response = client.post(
        f"/student/api/attempts/{attempt['id']}/submit",
        json={
            "answers": [
                {
                    "question_id": first_question["id"],
                    "selected_option_id": first_question["options"][0]["id"],
                }
            ]
        },
    )
    html_response = client.post(
        f"/student/attempts/{attempt['id']}/submit",
        data={
            f"question_{first_question['id']}_option": first_question["options"][0][
                "id"
            ],
        },
    )
    html = html_response.get_data(as_text=True)

    with app.app_context():
        stored = get_db().execute(
            "SELECT status, submitted_at, score, max_score FROM attempts WHERE id = ?",
            (attempt["id"],),
        ).fetchone()
        answer_count = get_db().execute(
            "SELECT COUNT(*) FROM attempt_answers WHERE attempt_id = ?",
            (attempt["id"],),
        ).fetchone()[0]

    assert api_response.status_code == 422
    assert api_response.get_json() == {
        "error": "answer all questions before submitting",
        "missing_question_ids": missing_question_ids,
    }
    assert html_response.status_code == 400
    assert "answer all questions before submitting" in html
    assert html.count("quiz-question-incomplete") == len(missing_question_ids)
    assert html.count("Answer required.") == len(missing_question_ids)
    for question_id in missing_question_ids:
        assert f'id="question-{question_id}"' in html
    assert stored["status"] == "in_progress"
    assert stored["submitted_at"] is None
    assert stored["score"] is None
    assert stored["max_score"] is None
    assert answer_count == 0


def test_student_attempt_routes_require_owner_and_auth(app, client, app_factory):
    version = _seed_published_quiz(app, client)
    _enroll_student(client)
    attempt = client.post(
        f"/student/api/quizzes/{version['id']}/start"
    ).get_json()["attempt"]

    other_client = app.test_client()
    _enroll_student(other_client)
    question = attempt["questions"][0]
    option_id = question["options"][0]["id"]

    assert other_client.get(f"/student/api/attempts/{attempt['id']}").status_code == 404
    assert other_client.put(
        f"/student/api/attempts/{attempt['id']}/answers/{question['id']}",
        json={"selected_option_id": option_id},
    ).status_code == 400
    assert other_client.post(
        f"/student/api/attempts/{attempt['id']}/submit"
    ).status_code == 400

    anonymous = app.test_client()
    assert anonymous.get(f"/student/api/attempts/{attempt['id']}").status_code == 401
    assert anonymous.put(
        f"/student/api/attempts/{attempt['id']}/answers/{question['id']}",
        json={"selected_option_id": option_id},
    ).status_code == 401


def test_unavailable_quiz_cannot_be_started(app, client):
    version = _seed_published_quiz(app, client)
    _enroll_student(client)
    client.post(
        f"/instructor/api/quiz-versions/{version['id']}/hide",
        headers=HEADERS,
    )

    response = client.post(f"/student/api/quizzes/{version['id']}/start")

    assert response.status_code == 400
    assert response.get_json()["error"] == "quiz is not available"


def test_attempt_limit_grant_and_void_routes(app, client):
    version = _seed_published_quiz(app, client, title="Attempt Grant Route Quiz")
    identifier = _enroll_student(client)
    first = client.post(f"/student/api/quizzes/{version['id']}/start").get_json()[
        "attempt"
    ]
    submit_response = client.post(
        f"/student/api/attempts/{first['id']}/submit",
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_option_id": question["options"][0]["id"],
                }
                for question in first["questions"]
            ]
        },
    )
    limit_html = client.get("/student/quizzes").get_data(as_text=True)
    blocked_response = client.post(f"/student/api/quizzes/{version['id']}/start")
    grant_response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/attempt-grants",
        json={
            "identifier": identifier,
            "extra_attempts": 1,
            "reason": "route-level retake",
        },
        headers=HEADERS,
    )
    second_response = client.post(f"/student/api/quizzes/{version['id']}/start")
    void_response = client.post(
        f"/instructor/api/attempts/{first['id']}/void",
        json={"reason": "route-level void"},
        headers=HEADERS,
    )
    detail_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)

    with app.app_context():
        stored = get_db().execute(
            """
            SELECT status, voided_at
            FROM attempts
            WHERE id = ?
            """,
            (first["id"],),
        ).fetchone()

    assert submit_response.status_code == 200
    assert 'data-completed-quizzes-toggle' in limit_html
    assert 'aria-expanded="false"' in limit_html
    assert "Show completed quizzes (1)" in limit_html
    assert 'data-completed-quizzes-panel hidden' in limit_html
    assert "Attempt limit reached." in limit_html
    assert "Start quiz" not in limit_html
    assert blocked_response.status_code == 400
    assert blocked_response.get_json()["error"] == "attempt limit reached"
    assert grant_response.status_code == 201
    assert grant_response.get_json()["grant"]["allowance"]["allowance"] == 2
    assert second_response.status_code == 201
    assert second_response.get_json()["attempt"]["attempt_number"] == 2
    assert void_response.status_code == 200
    assert void_response.get_json()["attempt"]["status"] == "voided"
    assert stored["status"] == "voided"
    assert stored["voided_at"] is not None
    assert "Attempt Access" in detail_html
    assert identifier in detail_html


def test_concurrent_start_requests_resume_one_active_attempt(app, client):
    version = _seed_published_quiz(app, client, title="Concurrent Start Quiz")
    identifier = _enroll_student(client)

    def start_in_thread():
        with app.app_context():
            student = get_student_by_identifier(identifier)
            return start_or_resume_attempt(version["id"], student)["id"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempt_ids = list(executor.map(lambda _index: start_in_thread(), range(2)))

    with app.app_context():
        attempt_count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM attempts
            WHERE quiz_version_id = ?
            """,
            (version["id"],),
        ).fetchone()[0]

    assert len(set(attempt_ids)) == 1
    assert attempt_count == 1


def test_timed_attempt_lazy_and_worker_expiration_routes(app, client):
    lazy_version = _seed_published_quiz(
        app,
        client,
        template_overrides={"timer_minutes": 1},
        title="Lazy Timer Quiz",
    )
    identifier = _enroll_student(client)
    lazy_attempt = client.post(
        f"/student/api/quizzes/{lazy_version['id']}/start"
    ).get_json()["attempt"]
    timed_attempt_html = client.get(
        f"/student/attempts/{lazy_attempt['id']}"
    ).get_data(as_text=True)
    first_question = lazy_attempt["questions"][0]
    save_response = client.post(
        f"/student/api/attempts/{lazy_attempt['id']}/answers/{first_question['id']}",
        json={"selected_option_id": first_question["options"][0]["id"]},
    )
    with app.app_context():
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", lazy_attempt["id"]),
        )
        get_db().commit()

    lazy_expired = client.get(
        f"/student/api/attempts/{lazy_attempt['id']}"
    ).get_json()["attempt"]
    blocked_after_expiration = client.post(
        f"/student/api/quizzes/{lazy_version['id']}/start"
    )
    client.post(
        f"/instructor/api/quiz-versions/{lazy_version['id']}/attempt-grants",
        json={"identifier": identifier, "extra_attempts": 1},
        headers=HEADERS,
    )
    retry_after_grant = client.post(
        f"/student/api/quizzes/{lazy_version['id']}/start"
    )

    worker_version = _seed_published_quiz(
        app,
        client,
        template_overrides={"timer_minutes": 1},
        title="Worker Timer Quiz",
    )
    worker_attempt = client.post(
        f"/student/api/quizzes/{worker_version['id']}/start"
    ).get_json()["attempt"]
    with app.app_context():
        get_db().execute(
            "UPDATE attempts SET deadline_at = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", worker_attempt["id"]),
        )
        get_db().commit()
        tick = finalize_expired_attempts(limit=10)
    worker_expired = client.get(
        f"/student/api/attempts/{worker_attempt['id']}"
    ).get_json()["attempt"]

    assert save_response.status_code == 200
    assert 'id="quiz-time-remaining"' in timed_attempt_html
    assert 'class="quiz-timer quiz-timer-topbar"' in timed_attempt_html
    assert f'data-deadline-at="{lazy_attempt["deadline_at"]}"' in timed_attempt_html
    assert 'id="quiz-time-remaining-value"' in timed_attempt_html
    assert "Time Remaining" in timed_attempt_html
    assert lazy_expired["status"] == "expired"
    assert blocked_after_expiration.status_code == 400
    assert blocked_after_expiration.get_json()["error"] == "attempt limit reached"
    assert retry_after_grant.status_code == 201
    assert retry_after_grant.get_json()["attempt"]["attempt_number"] == 2
    assert tick["expired"] >= 1
    assert worker_expired["status"] == "expired"
