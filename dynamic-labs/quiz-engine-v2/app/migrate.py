from .audit import utc_now_iso
from .db import get_db, init_db, run_migrations


FULL_EXPORT_SCHEMA_VERSION = 1

FULL_EXPORT_TABLES = (
    "cohorts",
    "roster_code_batches",
    "students",
    "import_batches",
    "quiz_banks",
    "quiz_bank_revisions",
    "bank_revision_tags",
    "questions",
    "question_options",
    "question_tags",
    "question_edit_batches",
    "import_retirement_batches",
    "question_retirements",
    "quiz_templates",
    "quiz_versions",
    "quiz_version_questions",
    "quiz_version_options",
    "attempt_grants",
    "attempts",
    "attempt_answers",
    "audit_events",
    "app_settings",
)

IMPORT_ORDER = (
    "cohorts",
    "roster_code_batches",
    "students",
    "import_batches",
    "quiz_banks",
    "quiz_bank_revisions",
    "bank_revision_tags",
    "questions",
    "question_options",
    "question_tags",
    "question_edit_batches",
    "import_retirement_batches",
    "question_retirements",
    "quiz_templates",
    "quiz_versions",
    "quiz_version_questions",
    "quiz_version_options",
    "attempt_grants",
    "attempts",
    "attempt_answers",
    "audit_events",
    "app_settings",
)

NON_FRESH_DATA_TABLES = tuple(
    table for table in FULL_EXPORT_TABLES if table != "app_settings"
)


class MigrationError(ValueError):
    pass


def migrate_database(conn=None):
    if conn is not None:
        run_migrations(conn)
        return

    from . import create_app

    app = create_app()
    with app.app_context():
        init_db()


if __name__ == "__main__":
    migrate_database()


def export_full_engine(*, conn=None):
    conn = conn or get_db()
    return {
        "schema_version": FULL_EXPORT_SCHEMA_VERSION,
        "exported_at": utc_now_iso(),
        "tables": {
            table: _table_rows(conn, table)
            for table in FULL_EXPORT_TABLES
        },
    }


def import_full_engine(payload, *, conn=None):
    conn = conn or get_db()
    validate_full_export(payload)
    if _target_has_data(conn):
        raise MigrationError("full import requires a fresh instance")

    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("PRAGMA defer_foreign_keys = ON")
        for table in IMPORT_ORDER:
            rows = payload["tables"].get(table, [])
            _insert_rows(conn, table, rows)
        _validate_database_foreign_keys(conn)
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    return {
        "schema_version": payload["schema_version"],
        "imported_tables": {
            table: len(payload["tables"].get(table, []))
            for table in IMPORT_ORDER
        },
    }


def validate_full_export(payload):
    if not isinstance(payload, dict):
        raise MigrationError("full export payload must be an object")
    if payload.get("schema_version") != FULL_EXPORT_SCHEMA_VERSION:
        raise MigrationError("unsupported full export schema_version")
    tables = payload.get("tables")
    if not isinstance(tables, dict):
        raise MigrationError("full export payload must include tables")
    unknown_tables = sorted(set(tables) - set(FULL_EXPORT_TABLES))
    if unknown_tables:
        raise MigrationError("unknown export tables: " + ", ".join(unknown_tables))
    for table in FULL_EXPORT_TABLES:
        if table not in tables:
            raise MigrationError(f"missing export table: {table}")
        if not isinstance(tables[table], list):
            raise MigrationError(f"export table {table} must be a list")
        for row in tables[table]:
            if not isinstance(row, dict):
                raise MigrationError(f"export table {table} rows must be objects")
    _validate_export_references(tables)
    return True


def backup_path_info(app=None):
    if app is not None:
        database_path = app.config["DATABASE_PATH"]
    else:
        try:
            from flask import current_app

            database_path = current_app.config["DATABASE_PATH"]
        except RuntimeError:
            database_path = None
    return {
        "database_path": database_path,
        "environment_variable": "QUIZ_ENGINE_DB_PATH",
        "compose_volume": "quiz_engine_data",
        "note": (
            "Back up the SQLite file configured by QUIZ_ENGINE_DB_PATH. In the "
            "default Docker Compose app service this is /data/quiz-engine.sqlite "
            "inside the quiz_engine_data named volume."
        ),
        "retention_policy": (
            "The app does not silently delete attempts, audit events, generated "
            "quiz versions, or immutable question snapshots."
        ),
    }


def _table_rows(conn, table):
    order_by = _order_by(conn, table)
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_by}").fetchall()
    return [dict(row) for row in rows]


def _order_by(conn, table):
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    if "id" in columns:
        return "id"
    if "key" in columns:
        return "key"
    if table == "bank_revision_tags":
        return "bank_revision_id, tag"
    if table == "question_tags":
        return "question_id, tag"
    if table == "question_edit_batches":
        return "id"
    if table == "question_retirements":
        return "question_id"
    return ", ".join(columns)


def _insert_rows(conn, table, rows):
    if not rows:
        return
    allowed_columns = {
        row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    for row in rows:
        unknown_columns = sorted(set(row) - allowed_columns)
        if unknown_columns:
            raise MigrationError(
                f"unknown columns for {table}: " + ", ".join(unknown_columns)
            )
        columns = list(row.keys())
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(columns)
        values = [row[column] for column in columns]
        verb = "INSERT OR REPLACE" if table == "app_settings" else "INSERT"
        conn.execute(
            f"{verb} INTO {table} ({column_sql}) VALUES ({placeholders})",
            values,
        )


def _target_has_data(conn):
    for table in NON_FRESH_DATA_TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count:
            return True
    return False


def _validate_database_foreign_keys(conn):
    failures = conn.execute("PRAGMA foreign_key_check").fetchall()
    if failures:
        first = failures[0]
        raise MigrationError(
            "imported data failed foreign-key validation: "
            f"{first['table']} row {first['rowid']}"
        )


def _validate_export_references(tables):
    ids = {
        table: {row["id"] for row in tables[table] if "id" in row}
        for table in FULL_EXPORT_TABLES
    }
    _references(tables, "students", "cohort_id", ids["cohorts"])
    _references(tables, "students", "roster_batch_id", ids["roster_code_batches"])
    _references(tables, "quiz_banks", "latest_revision_id", ids["quiz_bank_revisions"])
    _references(tables, "quiz_bank_revisions", "quiz_bank_id", ids["quiz_banks"])
    _references(tables, "quiz_bank_revisions", "import_batch_id", ids["import_batches"])
    _references(tables, "bank_revision_tags", "bank_revision_id", ids["quiz_bank_revisions"])
    _references(tables, "questions", "quiz_bank_id", ids["quiz_banks"])
    _references(tables, "questions", "bank_revision_id", ids["quiz_bank_revisions"])
    _references(tables, "questions", "revises_question_id", ids["questions"])
    _references(tables, "question_options", "question_id", ids["questions"])
    _references(tables, "question_tags", "question_id", ids["questions"])
    _references(
        tables,
        "question_edit_batches",
        "original_question_id",
        ids["questions"],
    )
    _references(
        tables,
        "question_edit_batches",
        "new_question_id",
        ids["questions"],
    )
    _references(
        tables,
        "question_retirements",
        "question_id",
        ids["questions"],
    )
    _references(
        tables,
        "question_retirements",
        "retirement_batch_id",
        ids["import_retirement_batches"],
    )
    _references(tables, "quiz_versions", "template_id", ids["quiz_templates"])
    _references(tables, "quiz_version_questions", "quiz_version_id", ids["quiz_versions"])
    _references(tables, "quiz_version_questions", "source_question_id", ids["questions"])
    _references(
        tables,
        "quiz_version_options",
        "quiz_version_question_id",
        ids["quiz_version_questions"],
    )
    _references(
        tables,
        "quiz_version_options",
        "source_option_id",
        ids["question_options"],
    )
    _references(tables, "attempt_grants", "quiz_version_id", ids["quiz_versions"])
    _references(tables, "attempt_grants", "student_id", ids["students"])
    _references(tables, "attempts", "quiz_version_id", ids["quiz_versions"])
    _references(tables, "attempts", "student_id", ids["students"])
    _references(tables, "attempt_answers", "attempt_id", ids["attempts"])
    _references(
        tables,
        "attempt_answers",
        "quiz_version_question_id",
        ids["quiz_version_questions"],
    )
    _references(
        tables,
        "attempt_answers",
        "selected_quiz_version_option_id",
        ids["quiz_version_options"],
    )
    _validate_answer_options_belong_to_question(tables)


def _references(tables, table, column, valid_ids):
    for row in tables[table]:
        value = row.get(column)
        if value is None:
            continue
        if value not in valid_ids:
            raise MigrationError(
                f"{table}.{column} references missing id {value}"
            )


def _validate_answer_options_belong_to_question(tables):
    options_by_id = {
        row["id"]: row["quiz_version_question_id"]
        for row in tables["quiz_version_options"]
    }
    for row in tables["attempt_answers"]:
        option_id = row.get("selected_quiz_version_option_id")
        if option_id is None:
            continue
        if options_by_id.get(option_id) != row.get("quiz_version_question_id"):
            raise MigrationError(
                "attempt_answers.selected_quiz_version_option_id does not "
                "belong to quiz_version_question_id"
            )
