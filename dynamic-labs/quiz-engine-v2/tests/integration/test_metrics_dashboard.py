import json

from app.attempts import get_student_attempt, save_answer, start_or_resume_attempt, submit_attempt, void_attempt
from app.db import get_db
from app.generation import generate_quiz_version
from app.grading import grade_written_answer, list_written_grading_queue
from app.ingest import ingest_json
from app.publication import set_quiz_version_visibility
from app.students import enroll_open_student


HEADERS = {"X-Test-Instructor": "teacher"}


def test_instructor_metrics_dashboard_routes_cover_latest_all_and_detail(app, client):
    with app.app_context():
        seeded = _seed_metrics_workflow()

    default_response = client.get("/instructor/api/metrics", headers=HEADERS)
    all_response = client.get(
        "/instructor/api/metrics?mode=all&include_voided=1",
        headers=HEADERS,
    )
    graded_response = client.get(
        "/instructor/api/metrics?statuses=graded",
        headers=HEADERS,
    )
    detail_response = client.get(
        f"/instructor/api/metrics/students/{seeded['student_one']}?mode=all&include_voided=1",
        headers=HEADERS,
    )
    html_response = client.get("/instructor/metrics", headers=HEADERS)

    default_metrics = default_response.get_json()["metrics"]
    all_metrics = all_response.get_json()["metrics"]
    graded_metrics = graded_response.get_json()["metrics"]
    detail = detail_response.get_json()["detail"]
    default_json = json.dumps(default_metrics)

    assert default_response.status_code == 200
    assert default_metrics["filters"]["rollup_attempts"].startswith("latest non-voided")
    assert default_metrics["class_summary"]["status_counts"]["graded"] == 1
    assert default_metrics["class_summary"]["status_counts"]["expired"] == 1
    assert default_metrics["class_summary"]["status_counts"]["voided"] == 0
    assert default_metrics["class_summary"]["missing_count"] == 1
    assert default_metrics["quiz_summary"][0]["completion_count"] == 1
    assert default_metrics["student_summary"][0]["student_identifier"].startswith("QZ-")
    assert default_metrics["difficulty_rollups"]
    assert default_metrics["question_type_rollups"]
    assert default_metrics["visualizations"]["completion_funnel"]
    assert default_metrics["visualizations"]["status_by_quiz"]
    assert default_metrics["visualizations"]["score_distribution"]
    assert default_metrics["visualizations"]["item_difficulty_scatter"]
    assert default_metrics["metric_catalog"]["completion"]["expired_count"] == 1
    assert "retake_pair_count" in default_metrics["metric_catalog"]["retakes"]
    assert default_metrics["metric_catalog"]["source_material_coverage"]["source_lesson_count"] == 1
    assert default_metrics["metric_catalog"]["operational"]["expired_ungraded_written_answers"] == 1
    assert '"student_id"' not in default_json
    assert "voided" not in default_metrics["filters"]["statuses"]
    assert all_metrics["class_summary"]["status_counts"]["voided"] == 1
    assert all_metrics["class_summary"]["selected_attempt_count"] == 3
    assert graded_metrics["class_summary"]["status_counts"]["expired"] == 0
    assert graded_metrics["class_summary"]["selected_attempt_count"] == 1
    assert detail["student_identifier"] == seeded["student_one"]
    assert detail["attempt_count"] == 2
    assert detail["attempts"][0]["quiz_archived"] is True
    assert detail["attempts"][0]["questions"][0]["specific_source_lesson"] == "Metrics Lesson"
    assert html_response.status_code == 200
    html = html_response.get_data(as_text=True)
    assert "Instructor Metrics" in html
    assert 'aria-label="Metrics report sections"' in html
    assert 'href="#item-analysis"' in html
    assert 'id="visualizations"' in html
    assert 'id="dimensions"' in html
    assert 'id="operations"' in html
    assert "Score Distribution" in html
    assert "Difficulty And Question Type" in html
    assert "Template Metrics" in html
    assert "Metric Ideas" not in html
    assert "Visualization Ideas" not in html
    assert '<select name="quiz_version_id">' in html
    assert f'value="{seeded["version_id"]}"' in html
    assert "Metrics Integration Quiz" in html


def _seed_metrics_workflow():
    ingest_json(json.dumps(_bank()), actor_sub="teacher")
    version = generate_quiz_version(
        {
            "title": "Metrics Integration Quiz",
            "criteria": {
                "lesson_ids": ["metrics_integration_lesson"],
                "question_types": ["multiple_choice", "written"],
            },
            "question_count": 2,
            "attempt_limit": 3,
            "random_seed": "metrics-integration-seed",
            "question_order_policy": "fixed",
            "option_order_policy": "fixed",
        },
        actor_sub="teacher",
    )
    set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")
    version_id = version["id"]

    student_one = enroll_open_student()
    student_two = enroll_open_student()
    enroll_open_student()

    first_attempt = start_or_resume_attempt(version_id, student_one)
    first_mc = next(
        question
        for question in first_attempt["questions"]
        if question["question_type"] == "multiple_choice"
    )
    first_written = next(
        question
        for question in first_attempt["questions"]
        if question["question_type"] == "written"
    )
    submit_attempt(
        first_attempt["id"],
        student_one,
        answers=[
            {
                "question_id": first_mc["id"],
                "selected_option_id": first_mc["options"][0]["id"],
            },
            {
                "question_id": first_written["id"],
                "written_response": "Confirmations add accumulated work.",
            },
        ],
    )
    queue_item = list_written_grading_queue()[0]
    grade_written_answer(queue_item["answer_id"], 0.5, actor_sub="teacher")

    voided_attempt = start_or_resume_attempt(version_id, student_one)
    voided_mc = next(
        question
        for question in voided_attempt["questions"]
        if question["question_type"] == "multiple_choice"
    )
    voided_written = next(
        question
        for question in voided_attempt["questions"]
        if question["question_type"] == "written"
    )
    submit_attempt(
        voided_attempt["id"],
        student_one,
        answers=[
            {
                "question_id": voided_mc["id"],
                "selected_option_id": voided_mc["options"][0]["id"],
            },
            {
                "question_id": voided_written["id"],
                "written_response": "Voided response.",
            },
        ],
    )
    void_attempt(voided_attempt["id"], reason="metrics integration", actor_sub="teacher")

    expired_attempt = start_or_resume_attempt(version_id, student_two)
    expired_written = next(
        question
        for question in expired_attempt["questions"]
        if question["question_type"] == "written"
    )
    save_answer(
        expired_attempt["id"],
        student_two,
        {
            "question_id": expired_written["id"],
            "written_response": "Saved before expiration.",
        },
    )
    get_db().execute(
        "UPDATE attempts SET deadline_at = ? WHERE id = ?",
        ("2000-01-01T00:00:00+00:00", expired_attempt["id"]),
    )
    get_db().commit()
    get_student_attempt(expired_attempt["id"], student_two)

    set_quiz_version_visibility(version_id, "archived", actor_sub="teacher")
    return {"student_one": student_one.identifier, "version_id": version_id}


def _bank():
    return {
        "lesson_id": "metrics_integration_lesson",
        "lesson_title": "Metrics Integration Lesson",
        "topic": "bitcoin",
        "tags": ["difficulty-core"],
        "questions": [
            {
                "id": "mc1",
                "question_stem": "Which block is valid?",
                "correct_answer": "The block with valid proof of work",
                "incorrect_answers": ["The block with an invalid transaction"],
                "difficulty_level": 2,
                "lesson_block": "Metrics Block",
                "specific_source_lesson": "Metrics Lesson",
                "specific_source_reading": "Metrics Reading",
                "tags": ["block-validation"],
                "explanation": "Valid blocks satisfy consensus rules.",
            },
            {
                "id": "wr1",
                "question_stem": "Explain confirmations.",
                "question_type": "written",
                "difficulty_level": 3,
                "lesson_block": "Metrics Block",
                "specific_source_lesson": "Metrics Lesson",
                "specific_source_reading": "Metrics Reading",
                "tags": ["confirmations"],
                "explanation": "Confirmations represent buried work.",
            },
        ],
    }
