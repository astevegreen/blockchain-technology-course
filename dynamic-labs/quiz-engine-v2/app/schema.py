import re

from .enums import CANONICAL_ENUMS, sqlite_check


SNAPSHOT_TABLES = frozenset(
    {
        "quiz_version_questions",
        "quiz_version_options",
        "attempts",
        "attempt_answers",
        "audit_events",
    }
)

ENUM_CONSTRAINT_COVERAGE = {
    "attempt_status": (("attempts", "status"),),
    "quiz_visibility": (("quiz_versions", "visibility"),),
    "quiz_bank_revision_status": (("quiz_bank_revisions", "status"),),
    "question_status": (("questions", "status"),),
    "registration_mode": (("json:app_settings", "registration_mode"),),
    "identifier_style": (("json:app_settings", "open_registration_identifier_style"),),
    "student_status": (("students", "status"),),
    "student_source": (("students", "source"),),
    "selection_policy": (("quiz_templates", "selection_policy"),),
    "order_mode": (
        ("quiz_templates", "question_order_mode"),
        ("quiz_templates", "option_order_mode"),
    ),
    "question_order_policy": (("quiz_versions", "question_order_policy"),),
    "option_order_policy": (("quiz_versions", "option_order_policy"),),
    "result_policy": (
        ("quiz_templates", "result_policy"),
        ("quiz_versions", "result_policy"),
    ),
    "question_type": (
        ("questions", "question_type"),
        ("quiz_version_questions", "snapshot_question_type"),
        ("json:criteria_json", "question_types"),
    ),
    "tag_match_mode": (("json:criteria_json", "tag_match_mode"),),
}


def enum_constraint(column_name, enum_name):
    return sqlite_check(column_name, enum_name)


def positive_check(column_name):
    return f"CHECK ({column_name} > 0)"


def non_negative_check(column_name):
    return f"CHECK ({column_name} >= 0)"


def nullable_positive_check(column_name):
    return f"CHECK ({column_name} IS NULL OR {column_name} > 0)"


def nullable_non_negative_check(column_name):
    return f"CHECK ({column_name} IS NULL OR {column_name} >= 0)"


def difficulty_check(column_name="difficulty_level"):
    return f"CHECK ({column_name} BETWEEN 1 AND 5)"


def bool_check(column_name):
    return f"CHECK ({column_name} IN (0, 1))"


def _normalize_sql(statement):
    return " ".join(statement.strip().lower().split())


def _extract_table_after(pattern, normalized_statement):
    match = re.search(pattern, normalized_statement)
    if not match:
        return None
    return match.group(1).strip('"`[]')


def validate_snapshot_migration_statements(statements):
    errors = []
    for statement in statements:
        normalized = _normalize_sql(statement)
        if not normalized:
            continue

        altered_table = _extract_table_after(r"\balter\s+table\s+([^\s]+)", normalized)
        if altered_table in SNAPSHOT_TABLES:
            if " add column " not in normalized:
                errors.append(
                    f"Snapshot table {altered_table} migrations must be additive"
                )
                continue
            if any(
                forbidden in normalized
                for forbidden in (" drop column ", " rename column ", " rename to ")
            ):
                errors.append(
                    f"Snapshot table {altered_table} migrations cannot drop or rename"
                )

        dropped_table = _extract_table_after(
            r"\bdrop\s+table\s+(?:if\s+exists\s+)?([^\s;]+)", normalized
        )
        if dropped_table in SNAPSHOT_TABLES:
            errors.append(f"Snapshot table {dropped_table} cannot be dropped")

    if errors:
        raise ValueError("; ".join(errors))


FOUNDATION_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY,
        event_type TEXT NOT NULL CHECK (length(event_type) > 0),
        actor_sub TEXT,
        object_type TEXT,
        object_id INTEGER,
        details_json TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
    ON audit_events (created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_audit_events_object
    ON audit_events (object_type, object_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY CHECK (length(key) > 0),
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
]

CORE_SCHEMA_STATEMENTS = [
    f"""
    CREATE TABLE IF NOT EXISTS cohorts (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL CHECK (length(title) > 0),
        is_active INTEGER NOT NULL DEFAULT 1 {bool_check("is_active")},
        created_at TEXT NOT NULL,
        archived_at TEXT
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        identifier TEXT NOT NULL UNIQUE CHECK (length(identifier) > 0),
        status TEXT NOT NULL DEFAULT 'active' {enum_constraint("status", "student_status")},
        source TEXT NOT NULL DEFAULT 'open_registration' {enum_constraint("source", "student_source")},
        cohort_id INTEGER,
        created_at TEXT NOT NULL,
        first_used_at TEXT,
        last_seen_at TEXT,
        revoked_at TEXT,
        FOREIGN KEY (cohort_id) REFERENCES cohorts(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_students_status
    ON students (status)
    """,
    """
    CREATE TABLE IF NOT EXISTS import_batches (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        source_hash TEXT,
        status TEXT NOT NULL CHECK (length(status) > 0),
        created_at TEXT NOT NULL,
        completed_at TEXT,
        summary_json TEXT
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS quiz_banks (
        id INTEGER PRIMARY KEY,
        lesson_id TEXT NOT NULL UNIQUE CHECK (length(lesson_id) > 0),
        lesson_title TEXT NOT NULL CHECK (length(lesson_title) > 0),
        topic TEXT NOT NULL DEFAULT 'other' CHECK (length(topic) > 0),
        hidden INTEGER NOT NULL DEFAULT 1 {bool_check("hidden")},
        archived INTEGER NOT NULL DEFAULT 0 {bool_check("archived")},
        latest_revision_id INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (latest_revision_id) REFERENCES quiz_bank_revisions(id)
            DEFERRABLE INITIALLY DEFERRED
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_quiz_banks_topic
    ON quiz_banks (topic)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS quiz_bank_revisions (
        id INTEGER PRIMARY KEY,
        quiz_bank_id INTEGER NOT NULL,
        import_batch_id INTEGER,
        lesson_title TEXT NOT NULL CHECK (length(lesson_title) > 0),
        date_generated TEXT,
        topic TEXT NOT NULL DEFAULT 'other' CHECK (length(topic) > 0),
        hierarchy_json TEXT NOT NULL,
        source_hash TEXT,
        status TEXT NOT NULL DEFAULT 'active' {enum_constraint("status", "quiz_bank_revision_status")},
        created_at TEXT NOT NULL,
        archived_at TEXT,
        FOREIGN KEY (quiz_bank_id) REFERENCES quiz_banks(id),
        FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_quiz_bank_revisions_bank_status
    ON quiz_bank_revisions (quiz_bank_id, status)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        quiz_bank_id INTEGER NOT NULL,
        bank_revision_id INTEGER NOT NULL,
        source_qid TEXT NOT NULL CHECK (length(source_qid) > 0),
        question_type TEXT NOT NULL {enum_constraint("question_type", "question_type")},
        question_stem TEXT NOT NULL CHECK (length(question_stem) > 0),
        explanation TEXT,
        difficulty_level INTEGER NOT NULL DEFAULT 1 {difficulty_check("difficulty_level")},
        topic TEXT NOT NULL DEFAULT 'other' CHECK (length(topic) > 0),
        lesson_block TEXT,
        specific_source_lesson TEXT,
        specific_source_reading TEXT,
        content_section_id TEXT,
        content_lecture_id TEXT,
        status TEXT NOT NULL DEFAULT 'active' {enum_constraint("status", "question_status")},
        revises_question_id INTEGER,
        superseded_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (quiz_bank_id) REFERENCES quiz_banks(id),
        FOREIGN KEY (bank_revision_id) REFERENCES quiz_bank_revisions(id),
        FOREIGN KEY (revises_question_id) REFERENCES questions(id),
        UNIQUE (bank_revision_id, source_qid),
        CHECK (revises_question_id IS NULL OR revises_question_id <> id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_questions_filters
    ON questions (
        quiz_bank_id,
        bank_revision_id,
        topic,
        difficulty_level,
        question_type,
        status
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_questions_hierarchy
    ON questions (content_section_id, content_lecture_id)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS question_options (
        id INTEGER PRIMARY KEY,
        question_id INTEGER NOT NULL,
        option_text TEXT NOT NULL CHECK (length(option_text) > 0),
        is_correct INTEGER NOT NULL DEFAULT 0 {bool_check("is_correct")},
        ingest_order INTEGER NOT NULL {non_negative_check("ingest_order")},
        FOREIGN KEY (question_id) REFERENCES questions(id),
        UNIQUE (question_id, ingest_order)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_question_options_question
    ON question_options (question_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS bank_revision_tags (
        bank_revision_id INTEGER NOT NULL,
        tag TEXT NOT NULL CHECK (length(tag) > 0),
        PRIMARY KEY (bank_revision_id, tag),
        FOREIGN KEY (bank_revision_id) REFERENCES quiz_bank_revisions(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_bank_revision_tags_tag
    ON bank_revision_tags (tag)
    """,
    """
    CREATE TABLE IF NOT EXISTS question_tags (
        question_id INTEGER NOT NULL,
        tag TEXT NOT NULL CHECK (length(tag) > 0),
        PRIMARY KEY (question_id, tag),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_question_tags_tag
    ON question_tags (tag)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS quiz_templates (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL CHECK (length(title) > 0),
        description TEXT,
        criteria_json TEXT NOT NULL,
        question_count INTEGER NOT NULL {positive_check("question_count")},
        selection_policy TEXT NOT NULL DEFAULT 'random' {enum_constraint("selection_policy", "selection_policy")},
        timer_minutes INTEGER {nullable_positive_check("timer_minutes")},
        attempt_limit INTEGER NOT NULL DEFAULT 1 {positive_check("attempt_limit")},
        result_policy TEXT NOT NULL DEFAULT 'score_after_grading' {enum_constraint("result_policy", "result_policy")},
        default_available_offset_minutes INTEGER,
        default_available_duration_minutes INTEGER {nullable_positive_check("default_available_duration_minutes")},
        archived INTEGER NOT NULL DEFAULT 0 {bool_check("archived")},
        created_by TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_quiz_templates_archived
    ON quiz_templates (archived)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS quiz_versions (
        id INTEGER PRIMARY KEY,
        template_id INTEGER,
        title TEXT NOT NULL CHECK (length(title) > 0),
        description TEXT,
        generation_snapshot_json TEXT NOT NULL,
        visibility TEXT NOT NULL DEFAULT 'hidden' {enum_constraint("visibility", "quiz_visibility")},
        available_from TEXT,
        available_until TEXT,
        timer_minutes INTEGER {nullable_positive_check("timer_minutes")},
        attempt_limit INTEGER NOT NULL DEFAULT 1 {positive_check("attempt_limit")},
        result_policy TEXT NOT NULL DEFAULT 'score_after_grading' {enum_constraint("result_policy", "result_policy")},
        question_order_policy TEXT NOT NULL DEFAULT 'fixed' {enum_constraint("question_order_policy", "question_order_policy")},
        option_order_policy TEXT NOT NULL DEFAULT 'random_per_attempt' {enum_constraint("option_order_policy", "option_order_policy")},
        results_released_at TEXT,
        results_released_by TEXT,
        created_by TEXT,
        created_at TEXT NOT NULL,
        published_at TEXT,
        archived_at TEXT,
        FOREIGN KEY (template_id) REFERENCES quiz_templates(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_quiz_versions_visibility
    ON quiz_versions (visibility, available_from, available_until)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS quiz_version_questions (
        id INTEGER PRIMARY KEY,
        quiz_version_id INTEGER NOT NULL,
        source_question_id INTEGER NOT NULL,
        position INTEGER NOT NULL {positive_check("position")},
        points INTEGER NOT NULL DEFAULT 1 {positive_check("points")},
        snapshot_source_qid TEXT NOT NULL CHECK (length(snapshot_source_qid) > 0),
        snapshot_question_type TEXT NOT NULL {enum_constraint("snapshot_question_type", "question_type")},
        snapshot_question_stem TEXT NOT NULL CHECK (length(snapshot_question_stem) > 0),
        snapshot_explanation TEXT,
        snapshot_difficulty_level INTEGER NOT NULL DEFAULT 1 {difficulty_check("snapshot_difficulty_level")},
        snapshot_topic TEXT NOT NULL DEFAULT 'other' CHECK (length(snapshot_topic) > 0),
        snapshot_tags_json TEXT NOT NULL DEFAULT '[]',
        snapshot_lesson_block TEXT,
        snapshot_specific_source_lesson TEXT,
        snapshot_specific_source_reading TEXT,
        FOREIGN KEY (quiz_version_id) REFERENCES quiz_versions(id),
        FOREIGN KEY (source_question_id) REFERENCES questions(id),
        UNIQUE (quiz_version_id, position),
        UNIQUE (quiz_version_id, source_question_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_quiz_version_questions_version
    ON quiz_version_questions (quiz_version_id, position)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS quiz_version_options (
        id INTEGER PRIMARY KEY,
        quiz_version_question_id INTEGER NOT NULL,
        source_option_id INTEGER,
        option_text TEXT NOT NULL CHECK (length(option_text) > 0),
        is_correct INTEGER NOT NULL DEFAULT 0 {bool_check("is_correct")},
        snapshot_order INTEGER NOT NULL {positive_check("snapshot_order")},
        FOREIGN KEY (quiz_version_question_id) REFERENCES quiz_version_questions(id),
        FOREIGN KEY (source_option_id) REFERENCES question_options(id),
        UNIQUE (quiz_version_question_id, snapshot_order)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_quiz_version_options_question
    ON quiz_version_options (quiz_version_question_id)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS attempt_grants (
        id INTEGER PRIMARY KEY,
        quiz_version_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        extra_attempts INTEGER NOT NULL DEFAULT 1 {positive_check("extra_attempts")},
        reason TEXT,
        created_by TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (quiz_version_id) REFERENCES quiz_versions(id),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_attempt_grants_quiz_student
    ON attempt_grants (quiz_version_id, student_id)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY,
        quiz_version_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        attempt_number INTEGER NOT NULL {positive_check("attempt_number")},
        status TEXT NOT NULL {enum_constraint("status", "attempt_status")},
        started_at TEXT NOT NULL,
        deadline_at TEXT,
        submitted_at TEXT,
        expired_at TEXT,
        graded_at TEXT,
        voided_at TEXT,
        score REAL {nullable_non_negative_check("score")},
        max_score REAL {nullable_non_negative_check("max_score")},
        question_order_json TEXT NOT NULL,
        option_order_json TEXT NOT NULL,
        FOREIGN KEY (quiz_version_id) REFERENCES quiz_versions(id),
        FOREIGN KEY (student_id) REFERENCES students(id),
        UNIQUE (quiz_version_id, student_id, attempt_number)
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_attempts_one_in_progress
    ON attempts (quiz_version_id, student_id)
    WHERE status = 'in_progress'
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_attempts_quiz_student_status
    ON attempts (quiz_version_id, student_id, status)
    """,
    f"""
    CREATE TABLE IF NOT EXISTS attempt_answers (
        id INTEGER PRIMARY KEY,
        attempt_id INTEGER NOT NULL,
        quiz_version_question_id INTEGER NOT NULL,
        selected_quiz_version_option_id INTEGER,
        written_response TEXT,
        is_correct INTEGER {bool_check("is_correct")},
        points_awarded REAL {nullable_non_negative_check("points_awarded")},
        points_possible REAL NOT NULL DEFAULT 1 {positive_check("points_possible")},
        answered_at TEXT,
        saved_at TEXT,
        graded_at TEXT,
        graded_by TEXT,
        FOREIGN KEY (attempt_id) REFERENCES attempts(id),
        FOREIGN KEY (quiz_version_question_id) REFERENCES quiz_version_questions(id),
        FOREIGN KEY (selected_quiz_version_option_id) REFERENCES quiz_version_options(id),
        UNIQUE (attempt_id, quiz_version_question_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt
    ON attempt_answers (attempt_id)
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_questions_revision_same_bank_insert
    BEFORE INSERT ON questions
    WHEN NEW.revises_question_id IS NOT NULL
      AND EXISTS (
        SELECT 1
        FROM questions revised
        WHERE revised.id = NEW.revises_question_id
          AND revised.quiz_bank_id <> NEW.quiz_bank_id
      )
    BEGIN
        SELECT RAISE(ABORT, 'revised question must be in same quiz bank');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_questions_revision_same_bank_update
    BEFORE UPDATE OF revises_question_id, quiz_bank_id ON questions
    WHEN NEW.revises_question_id IS NOT NULL
      AND EXISTS (
        SELECT 1
        FROM questions revised
        WHERE revised.id = NEW.revises_question_id
          AND revised.quiz_bank_id <> NEW.quiz_bank_id
      )
    BEGIN
        SELECT RAISE(ABORT, 'revised question must be in same quiz bank');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_attempt_answers_option_matches_question_insert
    BEFORE INSERT ON attempt_answers
    WHEN NEW.selected_quiz_version_option_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1
        FROM quiz_version_options option
        WHERE option.id = NEW.selected_quiz_version_option_id
          AND option.quiz_version_question_id = NEW.quiz_version_question_id
      )
    BEGIN
        SELECT RAISE(ABORT, 'selected option must belong to answered question');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_attempt_answers_option_matches_question_update
    BEFORE UPDATE OF selected_quiz_version_option_id, quiz_version_question_id
    ON attempt_answers
    WHEN NEW.selected_quiz_version_option_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1
        FROM quiz_version_options option
        WHERE option.id = NEW.selected_quiz_version_option_id
          AND option.quiz_version_question_id = NEW.quiz_version_question_id
      )
    BEGIN
        SELECT RAISE(ABORT, 'selected option must belong to answered question');
    END
    """,
]

STUDENT_IDENTITY_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS roster_code_batches (
        id INTEGER PRIMARY KEY,
        code_count INTEGER NOT NULL CHECK (code_count > 0),
        activation_mode TEXT NOT NULL
            CHECK (activation_mode IN ('inactive_until_first_use', 'pre_active')),
        created_by TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    ALTER TABLE students
    ADD COLUMN roster_batch_id INTEGER REFERENCES roster_code_batches(id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_students_roster_batch
    ON students (roster_batch_id)
    """,
]

QUIZ_PUBLICATION_SCHEMA_STATEMENTS = [
    """
    ALTER TABLE quiz_versions
    ADD COLUMN instructor_notes TEXT
    """,
]

IMPORT_RETIREMENT_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS import_retirement_batches (
        id INTEGER PRIMARY KEY,
        mode TEXT NOT NULL CHECK (mode IN ('lesson', 'tag')),
        targets_json TEXT NOT NULL,
        selection_hash TEXT NOT NULL CHECK (length(selection_hash) > 0),
        summary_json TEXT NOT NULL,
        reason TEXT,
        created_by TEXT,
        created_at TEXT NOT NULL,
        completed_at TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_import_retirement_batches_created_at
    ON import_retirement_batches (created_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS question_retirements (
        question_id INTEGER PRIMARY KEY,
        retirement_batch_id INTEGER NOT NULL,
        retired_by TEXT,
        retired_at TEXT NOT NULL,
        reason TEXT,
        FOREIGN KEY (question_id) REFERENCES questions(id),
        FOREIGN KEY (retirement_batch_id) REFERENCES import_retirement_batches(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_question_retirements_batch
    ON question_retirements (retirement_batch_id)
    """,
]

QUESTION_EDITING_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS question_edit_batches (
        id INTEGER PRIMARY KEY,
        original_question_id INTEGER NOT NULL,
        new_question_id INTEGER NOT NULL,
        changed_fields_json TEXT NOT NULL,
        reason TEXT,
        created_by TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (original_question_id) REFERENCES questions(id),
        FOREIGN KEY (new_question_id) REFERENCES questions(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_question_edit_batches_original
    ON question_edit_batches (original_question_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_question_edit_batches_new
    ON question_edit_batches (new_question_id)
    """,
]

QUIZ_REVIEW_RELEASE_SCHEMA_STATEMENTS = [
    """
    ALTER TABLE quiz_versions
    ADD COLUMN review_released_at TEXT
    """,
    """
    ALTER TABLE quiz_versions
    ADD COLUMN review_released_by TEXT
    """,
]

QUIZ_TEMPLATE_ORDER_MODE_SCHEMA_STATEMENTS = [
    f"""
    ALTER TABLE quiz_templates
    ADD COLUMN question_order_mode TEXT NOT NULL DEFAULT 'random_per_attempt' {enum_constraint("question_order_mode", "order_mode")}
    """,
    f"""
    ALTER TABLE quiz_templates
    ADD COLUMN option_order_mode TEXT NOT NULL DEFAULT 'random_per_attempt' {enum_constraint("option_order_mode", "order_mode")}
    """,
]

DEFAULT_APP_SETTINGS = (
    ("registration_mode", "open"),
    ("open_registration_cap", "40"),
    ("open_registration_identifier_style", "code"),
    ("default_result_policy", "score_after_grading"),
)

SCHEMA_MIGRATIONS = (
    (1, "foundation_audit_settings", FOUNDATION_SCHEMA_STATEMENTS),
    (2, "core_schema", CORE_SCHEMA_STATEMENTS),
    (3, "student_identity_registration", STUDENT_IDENTITY_SCHEMA_STATEMENTS),
    (4, "quiz_publication_metadata", QUIZ_PUBLICATION_SCHEMA_STATEMENTS),
    (5, "import_retirements", IMPORT_RETIREMENT_SCHEMA_STATEMENTS),
    (6, "question_editing", QUESTION_EDITING_SCHEMA_STATEMENTS),
    (7, "quiz_review_release", QUIZ_REVIEW_RELEASE_SCHEMA_STATEMENTS),
    (8, "quiz_template_order_modes", QUIZ_TEMPLATE_ORDER_MODE_SCHEMA_STATEMENTS),
)


if set(ENUM_CONSTRAINT_COVERAGE) != set(CANONICAL_ENUMS):
    missing = sorted(set(CANONICAL_ENUMS) - set(ENUM_CONSTRAINT_COVERAGE))
    extra = sorted(set(ENUM_CONSTRAINT_COVERAGE) - set(CANONICAL_ENUMS))
    raise RuntimeError(
        f"Enum constraint coverage mismatch; missing={missing}, extra={extra}"
    )
