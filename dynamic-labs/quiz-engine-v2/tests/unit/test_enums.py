import pytest

from app.enums import CANONICAL_ENUMS, enum_values, sqlite_check


def test_canonical_enums_include_requirements_values():
    assert enum_values("attempt_status") == (
        "in_progress",
        "submitted",
        "expired",
        "needs_grading",
        "graded",
        "voided",
    )
    assert enum_values("quiz_visibility") == ("hidden", "published", "archived")
    assert enum_values("identifier_style") == ("code", "handle")
    assert enum_values("question_type") == ("multiple_choice", "written")
    assert enum_values("tag_match_mode") == ("any", "all")


def test_sqlite_check_clause_is_generated_from_canonical_values():
    clause = sqlite_check("status", "student_status")
    assert clause == "CHECK (status IN ('inactive', 'active', 'revoked'))"
    for value in CANONICAL_ENUMS["student_status"]:
        assert value in clause


def test_unknown_enum_name_is_rejected():
    with pytest.raises(KeyError, match="Unknown canonical enum"):
        enum_values("not_real")
