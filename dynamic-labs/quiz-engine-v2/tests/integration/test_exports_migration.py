import copy
import json

import pytest

from app import create_app
from app.attempts import grant_extra_attempt, start_or_resume_attempt, submit_attempt
from app.db import get_db, init_db
from app.generation import generate_quiz_version_from_template
from app.grading import release_quiz_results
from app.ingest import ingest_json
from app.migrate import FULL_EXPORT_TABLES, MigrationError, export_full_engine, import_full_engine
from app.publication import set_quiz_version_visibility
from app.quiz_templates import create_template
from app.students import create_roster_code_batch, enroll_open_student


HEADERS = {"X-Test-Instructor": "teacher"}


def test_instructor_report_export_routes_and_backup_info(app, client):
    with app.app_context():
        fixture = _seed_migration_fixture()

    assert client.get("/instructor/api/exports/full.json").status_code == 401

    class_json = client.get("/instructor/api/exports/reports/class.json", headers=HEADERS)
    class_csv = client.get("/instructor/api/exports/reports/class.csv", headers=HEADERS)
    student_json = client.get(
        "/instructor/api/exports/reports/student.json"
        f"?student_identifier={fixture['student_identifier']}",
        headers=HEADERS,
    )
    quiz_csv = client.get(
        "/instructor/api/exports/reports/quiz-version.csv"
        f"?quiz_version_id={fixture['quiz_version_id']}",
        headers=HEADERS,
    )
    template_json = client.get(
        "/instructor/api/exports/reports/template.json"
        f"?template_id={fixture['template_id']}",
        headers=HEADERS,
    )
    bank_json = client.get(
        f"/instructor/api/exports/quiz-banks/{fixture['bank_id']}.json",
        headers=HEADERS,
    )
    full_json = client.get("/instructor/api/exports/full.json", headers=HEADERS)
    backup_info = client.get("/instructor/api/backup-info", headers=HEADERS)
    roster_html = client.get("/instructor/roster-codes/print", headers=HEADERS)
    exports_html = client.get("/instructor/exports", headers=HEADERS)

    assert class_json.status_code == 200
    assert class_json.get_json()["scope"] == "class"
    assert class_csv.status_code == 200
    assert class_csv.get_data(as_text=True).splitlines()[0].startswith("record_type")
    assert student_json.get_json()["data"]["student_identifier"] == fixture["student_identifier"]
    assert '"student_id"' not in json.dumps(student_json.get_json())
    assert quiz_csv.status_code == 200
    assert "item_analysis" in quiz_csv.get_data(as_text=True)
    assert template_json.get_json()["data"]["template"]["id"] == fixture["template_id"]
    assert bank_json.get_json()["lesson_id"] == "export_integration_lesson"
    assert full_json.get_json()["schema_version"] == 1
    assert full_json.get_json()["tables"]["attempts"]
    assert backup_info.get_json()["backup"]["database_path"]
    assert fixture["roster_identifier"] in roster_html.get_data(as_text=True)
    assert "Instructor Exports" in exports_html.get_data(as_text=True)


def test_full_export_import_round_trip_into_fresh_database(app, tmp_path):
    with app.app_context():
        fixture = _seed_migration_fixture()
        payload = export_full_engine()
        expected_counts = {
            table: len(payload["tables"][table])
            for table in FULL_EXPORT_TABLES
        }

    fresh_app = _fresh_app(tmp_path / "roundtrip.sqlite")
    with fresh_app.app_context():
        result = import_full_engine(payload)
        restored_counts = {
            table: get_db().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in FULL_EXPORT_TABLES
        }
        restored_attempt = get_db().execute(
            "SELECT status, score FROM attempts WHERE id = ?",
            (fixture["attempt_id"],),
        ).fetchone()
        restored_version = get_db().execute(
            """
            SELECT results_released_at
            FROM quiz_versions
            WHERE id = ?
            """,
            (fixture["quiz_version_id"],),
        ).fetchone()

    assert result["schema_version"] == 1
    assert restored_counts == expected_counts
    assert restored_attempt["status"] == "graded"
    assert restored_attempt["score"] is not None
    assert restored_version["results_released_at"] is not None


def test_bad_full_import_fails_without_partial_rows(app, tmp_path):
    with app.app_context():
        _seed_migration_fixture()
        payload = export_full_engine()

    bad_payload = copy.deepcopy(payload)
    bad_payload["tables"]["attempts"][0]["student_id"] = 999999
    fresh_app = _fresh_app(tmp_path / "bad-import.sqlite")

    with fresh_app.app_context():
        with pytest.raises(MigrationError, match="attempts.student_id"):
            import_full_engine(bad_payload)
        assert get_db().execute("SELECT COUNT(*) FROM quiz_banks").fetchone()[0] == 0
        assert get_db().execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def _fresh_app(database_path):
    app = create_app(
        {
            "DATABASE_PATH": str(database_path),
            "SECRET_KEY": "fresh-test-secret",
            "TESTING": True,
            "INSTRUCTOR_AUTH_MODE": "test-header",
            "TEST_INSTRUCTOR_HEADER": "X-Test-Instructor",
        }
    )
    with app.app_context():
        init_db()
    return app


def _seed_migration_fixture():
    bank_result = ingest_json(json.dumps(_bank()), actor_sub="teacher")
    roster = create_roster_code_batch(
        1,
        activation_mode="pre_active",
        actor_sub="teacher",
    )
    template = create_template(
        {
            "title": "Export Integration Template",
            "criteria": {
                "lesson_ids": ["export_integration_lesson"],
                "question_types": ["multiple_choice"],
            },
            "question_count": 1,
            "attempt_limit": 1,
            "result_policy": "score_after_release",
        },
        actor_sub="teacher",
    )
    version = generate_quiz_version_from_template(
        template["id"],
        overrides={
            "random_seed": "export-integration",
            "question_order_policy": "fixed",
            "option_order_policy": "fixed",
        },
        actor_sub="teacher",
    )
    set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")
    student = enroll_open_student()
    grant_extra_attempt(
        version["id"],
        student.identifier,
        extra_attempts=1,
        reason="migration export coverage",
        actor_sub="teacher",
    )
    attempt = start_or_resume_attempt(version["id"], student)
    question = attempt["questions"][0]
    submitted = submit_attempt(
        attempt["id"],
        student,
        answers=[
            {
                "question_id": question["id"],
                "selected_option_id": question["options"][0]["id"],
            }
        ],
    )
    release_quiz_results(version["id"], actor_sub="teacher")
    return {
        "bank_id": bank_result.bank_results[0].bank_id,
        "template_id": template["id"],
        "quiz_version_id": version["id"],
        "student_identifier": student.identifier,
        "roster_identifier": roster["identifiers"][0],
        "attempt_id": submitted["id"],
    }


def _bank():
    return {
        "lesson_id": "export_integration_lesson",
        "lesson_title": "Export Integration Lesson",
        "topic": "bitcoin",
        "tags": ["export-integration"],
        "questions": [
            {
                "id": "mc1",
                "question_stem": "Which route exports the full engine?",
                "correct_answer": "Full JSON export",
                "incorrect_answers": ["Student login", "Static health check"],
                "difficulty_level": 1,
                "lesson_block": "Migration",
                "specific_source_lesson": "Migration Lesson",
                "specific_source_reading": "Migration Reading",
            }
        ],
    }
