import sqlite3

import pytest

from app.db import get_db


CORE_TABLES = {
    "app_settings",
    "attempt_answers",
    "attempt_grants",
    "attempts",
    "audit_events",
    "bank_revision_tags",
    "cohorts",
    "import_batches",
    "import_retirement_batches",
    "question_options",
    "question_edit_batches",
    "question_retirements",
    "question_tags",
    "questions",
    "quiz_bank_revisions",
    "quiz_banks",
    "quiz_templates",
    "quiz_version_options",
    "quiz_version_questions",
    "quiz_versions",
    "schema_migrations",
    "students",
}

EMPTY_ORDER_JSON = '{"schema_version": 1, "order": []}'
EMPTY_SNAPSHOT_JSON = (
    '{"schema_version": 1, "criteria": {}, "eligible_pool_size": 0, '
    '"quota_allocations": {}, "coverage_allocations": {}, "random_seed": "seed", '
    '"bank_revision_ids": [], "selected_question_ids": []}'
)
EMPTY_CRITERIA_JSON = (
    '{"schema_version": 1, "lesson_ids": [], "topics": [], "tags": [], '
    '"excluded_topics": [], "excluded_tags": [], '
    '"tag_match_mode": "any", "hierarchy_sections": [], "hierarchy_lectures": [], '
    '"difficulty_min": 1, "difficulty_max": 5, "question_types": ["multiple_choice"], '
    '"quotas": {}, "require_topic_coverage": false}'
)
EMPTY_HIERARCHY_JSON = '{"schema_version": 1, "sections": []}'
EMPTY_TAGS_JSON = '{"schema_version": 1, "tags": []}'


def _insert_student(conn, identifier="QZ-TEST-0001"):
    return conn.execute(
        """
        INSERT INTO students (identifier, status, source, created_at)
        VALUES (?, 'active', 'open_registration', CURRENT_TIMESTAMP)
        """,
        (identifier,),
    ).lastrowid


def _insert_quiz_version(conn):
    return conn.execute(
        """
        INSERT INTO quiz_versions (
            title,
            generation_snapshot_json,
            created_at
        )
        VALUES ('Phase 2 Quiz', ?, CURRENT_TIMESTAMP)
        """,
        (EMPTY_SNAPSHOT_JSON,),
    ).lastrowid


def _insert_bank_revision(conn, lesson_id="lesson-1"):
    bank_id = conn.execute(
        """
        INSERT INTO quiz_banks (
            lesson_id,
            lesson_title,
            topic,
            created_at,
            updated_at
        )
        VALUES (?, 'Lesson 1', 'blockchain', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (lesson_id,),
    ).lastrowid
    revision_id = conn.execute(
        """
        INSERT INTO quiz_bank_revisions (
            quiz_bank_id,
            lesson_title,
            topic,
            hierarchy_json,
            created_at
        )
        VALUES (?, 'Lesson 1', 'blockchain', ?, CURRENT_TIMESTAMP)
        """,
        (bank_id, EMPTY_HIERARCHY_JSON),
    ).lastrowid
    conn.execute(
        "UPDATE quiz_banks SET latest_revision_id = ? WHERE id = ?",
        (revision_id, bank_id),
    )
    return bank_id, revision_id


def _insert_question(conn, bank_id, revision_id, source_qid="q1", difficulty=3):
    return conn.execute(
        """
        INSERT INTO questions (
            quiz_bank_id,
            bank_revision_id,
            source_qid,
            question_type,
            question_stem,
            difficulty_level,
            topic,
            created_at
        )
        VALUES (?, ?, ?, 'multiple_choice', 'Question?', ?, 'blockchain', CURRENT_TIMESTAMP)
        """,
        (bank_id, revision_id, source_qid, difficulty),
    ).lastrowid


def _insert_snapshot_question(conn, quiz_version_id, question_id, position=1):
    return conn.execute(
        """
        INSERT INTO quiz_version_questions (
            quiz_version_id,
            source_question_id,
            position,
            snapshot_source_qid,
            snapshot_question_type,
            snapshot_question_stem,
            snapshot_difficulty_level,
            snapshot_topic,
            snapshot_tags_json
        )
        VALUES (?, ?, ?, 'q1', 'multiple_choice', 'Question?', 3, 'blockchain', ?)
        """,
        (quiz_version_id, question_id, position, EMPTY_TAGS_JSON),
    ).lastrowid


def _insert_attempt(conn, quiz_version_id, student_id, attempt_number, status):
    return conn.execute(
        """
        INSERT INTO attempts (
            quiz_version_id,
            student_id,
            attempt_number,
            status,
            started_at,
            question_order_json,
            option_order_json
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
        """,
        (quiz_version_id, student_id, attempt_number, status, EMPTY_ORDER_JSON, EMPTY_ORDER_JSON),
    ).lastrowid


def test_fresh_database_has_all_core_tables_and_migrations(app):
    with app.app_context():
        db = get_db()
        tables = {
            row["name"]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        versions = [
            row["version"]
            for row in db.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        ]

    assert CORE_TABLES <= tables
    assert versions == [1, 2, 3, 4, 5, 6, 7, 8]


def test_invalid_enum_values_are_rejected(app):
    with app.app_context():
        db = get_db()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO students (identifier, status, source, created_at)
                VALUES ('QZ-BAD-ENUM', 'paused', 'open_registration', CURRENT_TIMESTAMP)
                """
            )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO quiz_templates (
                    title,
                    criteria_json,
                    question_count,
                    selection_policy,
                    created_at,
                    updated_at
                )
                VALUES ('Template', ?, 1, 'manual', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (EMPTY_CRITERIA_JSON,),
            )


def test_invalid_difficulty_and_negative_counts_are_rejected(app):
    with app.app_context():
        db = get_db()
        bank_id, revision_id = _insert_bank_revision(db)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_question(db, bank_id, revision_id, difficulty=6)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO quiz_templates (
                    title,
                    criteria_json,
                    question_count,
                    created_at,
                    updated_at
                )
                VALUES ('Negative', ?, -1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (EMPTY_CRITERIA_JSON,),
            )


def test_broken_foreign_keys_are_rejected(app):
    with app.app_context():
        db = get_db()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO students (identifier, status, source, cohort_id, created_at)
                VALUES ('QZ-BAD-FK', 'active', 'open_registration', 999, CURRENT_TIMESTAMP)
                """
            )


def test_partial_unique_index_prevents_multiple_active_attempts(app):
    with app.app_context():
        db = get_db()
        student_id = _insert_student(db)
        quiz_version_id = _insert_quiz_version(db)
        _insert_attempt(db, quiz_version_id, student_id, 1, "in_progress")
        with pytest.raises(sqlite3.IntegrityError):
            _insert_attempt(db, quiz_version_id, student_id, 2, "in_progress")

        submitted_id = _insert_attempt(db, quiz_version_id, student_id, 2, "submitted")

    assert submitted_id > 0


def test_attempt_answer_selected_option_must_belong_to_question(app):
    with app.app_context():
        db = get_db()
        student_id = _insert_student(db, "QZ-ANSWER-0001")
        quiz_version_id = _insert_quiz_version(db)
        bank_id, revision_id = _insert_bank_revision(db)
        source_question_1 = _insert_question(db, bank_id, revision_id, "q1")
        source_question_2 = _insert_question(db, bank_id, revision_id, "q2")
        snapshot_question_1 = _insert_snapshot_question(
            db, quiz_version_id, source_question_1, 1
        )
        snapshot_question_2 = _insert_snapshot_question(
            db, quiz_version_id, source_question_2, 2
        )
        option_1 = db.execute(
            """
            INSERT INTO quiz_version_options (
                quiz_version_question_id,
                option_text,
                is_correct,
                snapshot_order
            )
            VALUES (?, 'A', 1, 1)
            """,
            (snapshot_question_1,),
        ).lastrowid
        attempt_id = _insert_attempt(db, quiz_version_id, student_id, 1, "in_progress")

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO attempt_answers (
                    attempt_id,
                    quiz_version_question_id,
                    selected_quiz_version_option_id,
                    points_possible
                )
                VALUES (?, ?, ?, 1)
                """,
                (attempt_id, snapshot_question_2, option_1),
            )


def test_question_revision_must_stay_in_same_quiz_bank(app):
    with app.app_context():
        db = get_db()
        bank_1, revision_1 = _insert_bank_revision(db, "lesson-a")
        bank_2, revision_2 = _insert_bank_revision(db, "lesson-b")
        original_question = _insert_question(db, bank_1, revision_1, "q1")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO questions (
                    quiz_bank_id,
                    bank_revision_id,
                    source_qid,
                    question_type,
                    question_stem,
                    difficulty_level,
                    topic,
                    revises_question_id,
                    created_at
                )
                VALUES (?, ?, 'q2', 'multiple_choice', 'Revision?', 3, 'blockchain', ?, CURRENT_TIMESTAMP)
                """,
                (bank_2, revision_2, original_question),
            )
