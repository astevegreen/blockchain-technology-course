import pytest

from app.schema import (
    SNAPSHOT_TABLES,
    validate_snapshot_migration_statements,
)


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
