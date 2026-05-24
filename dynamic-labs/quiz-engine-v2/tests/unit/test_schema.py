import pytest

from app.enums import CANONICAL_ENUMS
from app.schema import (
    ENUM_CONSTRAINT_COVERAGE,
    SNAPSHOT_TABLES,
    bool_check,
    difficulty_check,
    enum_constraint,
    positive_check,
    validate_snapshot_migration_statements,
)


def test_schema_helper_functions_emit_expected_fragments():
    assert positive_check("attempt_limit") == "CHECK (attempt_limit > 0)"
    assert difficulty_check("difficulty_level") == (
        "CHECK (difficulty_level BETWEEN 1 AND 5)"
    )
    assert bool_check("archived") == "CHECK (archived IN (0, 1))"
    assert enum_constraint("status", "student_status") == (
        "CHECK (status IN ('inactive', 'active', 'revoked'))"
    )


def test_enum_constraint_coverage_mentions_every_canonical_enum():
    assert set(ENUM_CONSTRAINT_COVERAGE) == set(CANONICAL_ENUMS)
    for enum_name, locations in ENUM_CONSTRAINT_COVERAGE.items():
        assert locations, f"{enum_name} must have at least one validation location"


def test_snapshot_table_list_matches_phase_2_policy():
    assert SNAPSHOT_TABLES == {
        "quiz_version_questions",
        "quiz_version_options",
        "attempts",
        "attempt_answers",
        "audit_events",
    }


def test_snapshot_migration_policy_allows_additive_changes():
    validate_snapshot_migration_statements(
        [
            "ALTER TABLE attempts ADD COLUMN reviewed_at TEXT",
            "CREATE INDEX IF NOT EXISTS idx_attempts_reviewed_at ON attempts (reviewed_at)",
        ]
    )


@pytest.mark.parametrize(
    "statement",
    [
        "ALTER TABLE attempts RENAME COLUMN score TO total_score",
        "ALTER TABLE attempt_answers DROP COLUMN written_response",
        "DROP TABLE quiz_version_questions",
    ],
)
def test_snapshot_migration_policy_rejects_destructive_changes(statement):
    with pytest.raises(ValueError, match="Snapshot table"):
        validate_snapshot_migration_statements([statement])
