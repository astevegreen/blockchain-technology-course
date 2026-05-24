import json

from app.attempts import start_or_resume_attempt, submit_attempt
from app.exports import (
    CLASS_CSV_HEADERS,
    QUIZ_VERSION_CSV_HEADERS,
    STUDENT_CSV_HEADERS,
    TEMPLATE_CSV_HEADERS,
    build_report,
    ingest_compatible_bank_export,
    printable_roster_sheet,
    render_report_csv,
)
from app.grading import grade_written_answer, list_written_grading_queue
from app.ingest import ingest_json
from app.metrics.filters import parse_metrics_filters
from app.publication import set_quiz_version_visibility
from app.quiz_templates import create_template
from app.generation import generate_quiz_version_from_template
from app.students import create_roster_code_batch, enroll_open_student


def test_report_csv_headers_are_stable_for_all_scopes(app):
    with app.app_context():
        fixture = _seed_export_fixture()
        filters = parse_metrics_filters({"mode": "all", "include_voided": "1"})

        class_csv = render_report_csv("class", filters)
        student_csv = render_report_csv(
            "student",
            filters,
            student_identifier=fixture["student_identifier"],
        )
        quiz_csv = render_report_csv(
            "quiz-version",
            filters,
            quiz_version_id=fixture["quiz_version_id"],
        )
        template_csv = render_report_csv(
            "template",
            filters,
            template_id=fixture["template_id"],
        )

    assert class_csv.splitlines()[0] == ",".join(CLASS_CSV_HEADERS)
    assert student_csv.splitlines()[0] == ",".join(STUDENT_CSV_HEADERS)
    assert quiz_csv.splitlines()[0] == ",".join(QUIZ_VERSION_CSV_HEADERS)
    assert template_csv.splitlines()[0] == ",".join(TEMPLATE_CSV_HEADERS)
    assert fixture["student_identifier"] in student_csv
    assert "Export Unit Template" in template_csv


def test_json_reports_and_bank_roster_exports(app):
    with app.app_context():
        fixture = _seed_export_fixture()
        filters = parse_metrics_filters({})

        class_report = build_report("class", filters)
        student_report = build_report(
            "student",
            filters,
            student_identifier=fixture["student_identifier"],
        )
        quiz_report = build_report(
            "quiz_version",
            filters,
            quiz_version_id=fixture["quiz_version_id"],
        )
        template_report = build_report(
            "template",
            filters,
            template_id=fixture["template_id"],
        )
        bank_export = ingest_compatible_bank_export(fixture["bank_id"])
        roster = printable_roster_sheet()

    assert class_report["schema_version"] == 1
    assert class_report["scope"] == "class"
    assert student_report["data"]["student_identifier"] == fixture["student_identifier"]
    assert quiz_report["quiz_version_id"] == fixture["quiz_version_id"]
    assert template_report["data"]["template"]["title"] == "Export Unit Template"
    assert bank_export["lesson_id"] == "export_unit_lesson"
    assert bank_export["questions"][0]["correct_answer"]
    assert roster and all(identifier.startswith("QZ-") for identifier in roster)
    assert '"student_id"' not in json.dumps(class_report)


def _seed_export_fixture():
    bank_result = ingest_json(json.dumps(_bank()), actor_sub="teacher")
    create_roster_code_batch(2, activation_mode="pre_active", actor_sub="teacher")
    template = create_template(
        {
            "title": "Export Unit Template",
            "criteria": {
                "lesson_ids": ["export_unit_lesson"],
                "question_types": ["multiple_choice", "written"],
            },
            "question_count": 2,
            "attempt_limit": 1,
            "selection_policy": "random",
            "result_policy": "score_after_grading",
        },
        actor_sub="teacher",
    )
    version = generate_quiz_version_from_template(
        template["id"],
        overrides={
            "random_seed": "export-unit",
            "question_order_policy": "fixed",
            "option_order_policy": "fixed",
        },
        actor_sub="teacher",
    )
    set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")
    student = enroll_open_student()
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
    submit_attempt(
        attempt["id"],
        student,
        answers=[
            {
                "question_id": mc_question["id"],
                "selected_option_id": mc_question["options"][0]["id"],
            },
            {
                "question_id": written_question["id"],
                "written_response": "A reportable written answer.",
            },
        ],
    )
    queue = list_written_grading_queue()
    grade_written_answer(queue[0]["answer_id"], 0.5, actor_sub="teacher")
    return {
        "student_identifier": student.identifier,
        "template_id": template["id"],
        "quiz_version_id": version["id"],
        "bank_id": bank_result.bank_results[0].bank_id,
    }


def _bank():
    return {
        "lesson_id": "export_unit_lesson",
        "lesson_title": "Export Unit Lesson",
        "topic": "bitcoin",
        "tags": ["export-unit"],
        "questions": [
            {
                "id": "mc1",
                "question_stem": "Which export is for spreadsheets?",
                "correct_answer": "CSV",
                "incorrect_answers": ["SQLite WAL", "Browser local storage"],
                "difficulty_level": 1,
                "lesson_block": "Exports",
                "specific_source_lesson": "Export Lesson",
                "specific_source_reading": "Export Reading",
            },
            {
                "id": "wr1",
                "question_stem": "Explain why JSON is canonical.",
                "question_type": "written",
                "difficulty_level": 2,
                "lesson_block": "Exports",
                "specific_source_lesson": "Export Lesson",
                "specific_source_reading": "Export Reading",
            },
        ],
    }
