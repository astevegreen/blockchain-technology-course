import copy
import json

import pytest

from app.db import connect_database, get_db, run_migrations
from app.ingest import ingest_json
from app.migrate import (
    FULL_EXPORT_TABLES,
    MigrationError,
    backup_path_info,
    export_full_engine,
    import_full_engine,
    validate_full_export,
)


def test_full_export_serializer_and_validator(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        payload = export_full_engine()
        validate_full_export(payload)
        info = backup_path_info(app)

    assert payload["schema_version"] == 1
    assert payload["exported_at"]
    assert set(payload["tables"]) == set(FULL_EXPORT_TABLES)
    assert payload["tables"]["quiz_banks"][0]["lesson_id"] == "migration_unit_lesson"
    assert info["environment_variable"] == "QUIZ_ENGINE_DB_PATH"
    assert "quiz_engine_data" in info["compose_volume"]


def test_full_export_validator_rejects_bad_references(app):
    with pytest.raises(MigrationError, match="schema_version"):
        validate_full_export({"schema_version": 999, "tables": {}})

    payload = _empty_payload()
    payload["tables"]["students"].append(
        {
            "id": 1,
            "identifier": "QZ-TEST-0001",
            "status": "active",
            "source": "open_registration",
            "cohort_id": 404,
            "created_at": "2026-05-20T00:00:00+00:00",
        }
    )
    with pytest.raises(MigrationError, match="students.cohort_id"):
        validate_full_export(payload)


def test_import_rolls_back_on_database_failure(app, tmp_path):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        payload = export_full_engine()

    bad_payload = copy.deepcopy(payload)
    bad_payload["tables"]["students"].append(
        {
            "id": 99,
            "identifier": "QZ-BADA-DATA",
            "status": "not_canonical",
            "source": "open_registration",
            "cohort_id": None,
            "created_at": "2026-05-20T00:00:00+00:00",
        }
    )

    conn = connect_database(str(tmp_path / "fresh.sqlite"))
    run_migrations(conn)
    try:
        with pytest.raises(Exception):
            import_full_engine(bad_payload, conn=conn)
        assert conn.execute("SELECT COUNT(*) FROM quiz_banks").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0
    finally:
        conn.close()


def test_full_import_requires_fresh_instance(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        payload = export_full_engine()
        with pytest.raises(MigrationError, match="fresh"):
            import_full_engine(payload, conn=get_db())


def _empty_payload():
    return {
        "schema_version": 1,
        "exported_at": "2026-05-20T00:00:00+00:00",
        "tables": {table: [] for table in FULL_EXPORT_TABLES},
    }


def _bank():
    return {
        "lesson_id": "migration_unit_lesson",
        "lesson_title": "Migration Unit Lesson",
        "topic": "bitcoin",
        "questions": [
            {
                "id": "mc1",
                "question_stem": "What is exported?",
                "correct_answer": "Canonical rows",
                "incorrect_answers": ["Only rendered HTML"],
                "difficulty_level": 1,
            }
        ],
    }

