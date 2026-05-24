CANONICAL_ENUMS = {
    "attempt_status": (
        "in_progress",
        "submitted",
        "expired",
        "needs_grading",
        "graded",
        "voided",
    ),
    "quiz_visibility": ("hidden", "published", "archived"),
    "quiz_bank_revision_status": ("active", "archived"),
    "question_status": ("active", "superseded"),
    "registration_mode": ("open", "disabled"),
    "identifier_style": ("code", "handle"),
    "student_status": ("inactive", "active", "revoked"),
    "student_source": ("open_registration", "roster_code"),
    "selection_policy": ("random", "balanced_difficulty", "focused_difficulty"),
    "order_mode": ("fixed", "random_once", "random_per_attempt"),
    "question_order_policy": ("fixed", "random_per_attempt"),
    "option_order_policy": ("fixed", "random_per_attempt"),
    "result_policy": (
        "score_after_grading",
        "score_and_answers_after_grading",
        "score_after_release",
        "score_and_answers_after_release",
        "hidden",
    ),
    "question_type": ("multiple_choice", "written"),
    "tag_match_mode": ("any", "all"),
}


def enum_values(enum_name):
    try:
        return CANONICAL_ENUMS[enum_name]
    except KeyError as exc:
        raise KeyError(f"Unknown canonical enum: {enum_name}") from exc


def is_valid_enum_value(enum_name, value):
    return value in enum_values(enum_name)


def _sql_string(value):
    return "'" + value.replace("'", "''") + "'"


def sqlite_check(column_name, enum_name):
    values = ", ".join(_sql_string(value) for value in enum_values(enum_name))
    return f"CHECK ({column_name} IN ({values}))"
