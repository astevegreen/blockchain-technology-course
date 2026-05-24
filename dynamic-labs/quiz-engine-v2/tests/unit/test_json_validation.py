import pytest

from app.json_validation import SchemaValidationError, validate_versioned_json


VALID_CRITERIA = {
    "schema_version": 1,
    "lesson_ids": ["lesson-1"],
    "topics": ["blockchain"],
    "tags": ["consensus"],
    "excluded_topics": [],
    "excluded_tags": [],
    "tag_match_mode": "any",
    "hierarchy_sections": [],
    "hierarchy_lectures": [],
    "difficulty_min": 1,
    "difficulty_max": 5,
    "question_types": ["multiple_choice"],
    "quotas": {},
    "require_topic_coverage": False,
}


def test_versioned_json_validator_accepts_valid_payload():
    validated = validate_versioned_json("criteria_json", VALID_CRITERIA)
    assert validated == VALID_CRITERIA


def test_versioned_json_validator_accepts_json_text():
    validated = validate_versioned_json(
        "details_json", '{"schema_version": 1, "details": {"phase": 1}}'
    )
    assert validated["details"] == {"phase": 1}


def test_versioned_json_validator_rejects_unknown_schema_version():
    payload = dict(VALID_CRITERIA)
    payload["schema_version"] = 999
    with pytest.raises(SchemaValidationError, match="Unsupported schema_version"):
        validate_versioned_json("criteria_json", payload)


def test_versioned_json_validator_rejects_missing_required_field():
    payload = dict(VALID_CRITERIA)
    del payload["question_types"]
    with pytest.raises(SchemaValidationError, match="question_types is required"):
        validate_versioned_json("criteria_json", payload)


def test_versioned_json_validator_rejects_invalid_enum_value():
    payload = dict(VALID_CRITERIA)
    payload["tag_match_mode"] = "none"
    with pytest.raises(SchemaValidationError, match="tag_match_mode"):
        validate_versioned_json("criteria_json", payload)


@pytest.mark.parametrize(
    ("schema_name", "payload"),
    [
        (
            "generation_snapshot_json",
            {
                "schema_version": 1,
                "criteria": {},
                "eligible_pool_size": 3,
                "quota_allocations": {},
                "coverage_allocations": {},
                "random_seed": "seed",
                "bank_revision_ids": [1],
                "selected_question_ids": [10, 11],
            },
        ),
        ("question_order_json", {"schema_version": 1, "order": [10, 11]}),
        ("option_order_json", {"schema_version": 1, "order": [100, 101]}),
        ("hierarchy_json", {"schema_version": 1, "sections": []}),
        ("summary_json", {"schema_version": 1, "successes": 1, "failures": 0}),
        ("snapshot_tags_json", {"schema_version": 1, "tags": ["tag"]}),
    ],
)
def test_defined_versioned_json_schemas_accept_minimal_valid_payloads(
    schema_name, payload
):
    assert validate_versioned_json(schema_name, payload) == payload
