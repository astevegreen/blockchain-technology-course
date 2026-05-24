import json
from dataclasses import dataclass

from .enums import enum_values


class SchemaValidationError(ValueError):
    pass


@dataclass(frozen=True)
class VersionedSchema:
    required_fields: dict
    validator: object = None


def _is_mapping(value):
    return isinstance(value, dict)


def _validate_string_list(field_name, values):
    if not isinstance(values, list) or not all(
        isinstance(item, str) for item in values
    ):
        raise SchemaValidationError(f"{field_name} must be a list of strings")


def _validate_int_list(field_name, values):
    if not isinstance(values, list) or not all(isinstance(item, int) for item in values):
        raise SchemaValidationError(f"{field_name} must be a list of integers")


def _validate_criteria(data):
    if data["tag_match_mode"] not in enum_values("tag_match_mode"):
        raise SchemaValidationError("tag_match_mode is not canonical")
    for field_name in (
        "lesson_ids",
        "topics",
        "tags",
        "excluded_topics",
        "excluded_tags",
        "hierarchy_sections",
        "hierarchy_lectures",
    ):
        _validate_string_list(field_name, data[field_name])
    for question_type in data["question_types"]:
        if question_type not in enum_values("question_type"):
            raise SchemaValidationError("question_types contains a non-canonical value")
    if not 1 <= data["difficulty_min"] <= data["difficulty_max"] <= 5:
        raise SchemaValidationError("difficulty range must be within 1..5")
    for quota_name in ("topics", "tags", "lesson_ids"):
        quota = data["quotas"].get(quota_name, {})
        if not isinstance(quota, dict):
            raise SchemaValidationError(f"quotas.{quota_name} must be an object")
        for key, value in quota.items():
            if not isinstance(key, str) or not key:
                raise SchemaValidationError(f"quotas.{quota_name} keys must be strings")
            if not isinstance(value, int) or value <= 0:
                raise SchemaValidationError(
                    f"quotas.{quota_name} values must be positive integers"
                )


def _validate_criteria_v2(data):
    _validate_criteria(data)
    if not isinstance(data["source_rules"], list):
        raise SchemaValidationError("source_rules must be a list")
    seen_lesson_ids = set()
    for index, rule in enumerate(data["source_rules"]):
        prefix = f"source_rules[{index}]"
        if not isinstance(rule, dict):
            raise SchemaValidationError(f"{prefix} must be an object")
        for field_name in ("lesson_id", "filter_mode", "question_count"):
            if field_name not in rule:
                raise SchemaValidationError(f"{prefix}.{field_name} is required")
        if not isinstance(rule["lesson_id"], str) or not rule["lesson_id"]:
            raise SchemaValidationError(f"{prefix}.lesson_id must be a string")
        if rule["lesson_id"] in seen_lesson_ids:
            raise SchemaValidationError(f"{prefix}.lesson_id must be unique")
        seen_lesson_ids.add(rule["lesson_id"])
        if rule["filter_mode"] not in {"inherit", "override"}:
            raise SchemaValidationError(f"{prefix}.filter_mode is not canonical")
        if not isinstance(rule["question_count"], int) or rule["question_count"] <= 0:
            raise SchemaValidationError(
                f"{prefix}.question_count must be a positive integer"
            )
        selection_policy = rule.get("selection_policy")
        if selection_policy is not None and selection_policy not in enum_values(
            "selection_policy"
        ):
            raise SchemaValidationError(f"{prefix}.selection_policy is not canonical")
        criteria = rule.get("criteria")
        if criteria is not None:
            if not isinstance(criteria, dict):
                raise SchemaValidationError(f"{prefix}.criteria must be an object")
            _validate_criteria(criteria)


def _validate_generation_snapshot(data):
    if data["eligible_pool_size"] < 0:
        raise SchemaValidationError("eligible_pool_size must be non-negative")
    _validate_int_list("bank_revision_ids", data["bank_revision_ids"])
    _validate_int_list("selected_question_ids", data["selected_question_ids"])


def _validate_order(data):
    _validate_int_list("order", data["order"])


def _validate_snapshot_tags(data):
    _validate_string_list("tags", data["tags"])


SCHEMAS = {
    "criteria_json": {
        1: VersionedSchema(
            {
                "lesson_ids": list,
                "topics": list,
                "tags": list,
                "excluded_topics": list,
                "excluded_tags": list,
                "tag_match_mode": str,
                "hierarchy_sections": list,
                "hierarchy_lectures": list,
                "difficulty_min": int,
                "difficulty_max": int,
                "question_types": list,
                "quotas": dict,
                "require_topic_coverage": bool,
            },
            _validate_criteria,
        ),
        2: VersionedSchema(
            {
                "lesson_ids": list,
                "topics": list,
                "tags": list,
                "excluded_topics": list,
                "excluded_tags": list,
                "tag_match_mode": str,
                "hierarchy_sections": list,
                "hierarchy_lectures": list,
                "difficulty_min": int,
                "difficulty_max": int,
                "question_types": list,
                "quotas": dict,
                "require_topic_coverage": bool,
                "source_rules": list,
            },
            _validate_criteria_v2,
        ),
    },
    "generation_snapshot_json": {
        1: VersionedSchema(
            {
                "criteria": dict,
                "eligible_pool_size": int,
                "quota_allocations": dict,
                "coverage_allocations": dict,
                "random_seed": str,
                "bank_revision_ids": list,
                "selected_question_ids": list,
            },
            _validate_generation_snapshot,
        )
    },
    "question_order_json": {1: VersionedSchema({"order": list}, _validate_order)},
    "option_order_json": {1: VersionedSchema({"order": list}, _validate_order)},
    "hierarchy_json": {
        1: VersionedSchema({"sections": list}),
    },
    "summary_json": {
        1: VersionedSchema({"successes": int, "failures": int}),
    },
    "details_json": {
        1: VersionedSchema({"details": dict}),
    },
    "snapshot_tags_json": {
        1: VersionedSchema({"tags": list}, _validate_snapshot_tags),
    },
}


def parse_json_object(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise SchemaValidationError("value must be valid JSON") from exc
    if not _is_mapping(value):
        raise SchemaValidationError("value must be a JSON object")
    return value


def validate_versioned_json(schema_name, value):
    if schema_name not in SCHEMAS:
        raise KeyError(f"Unknown JSON schema: {schema_name}")

    data = parse_json_object(value)
    if "schema_version" not in data:
        raise SchemaValidationError("schema_version is required")
    schema_version = data["schema_version"]
    versioned_schemas = SCHEMAS[schema_name]
    if schema_version not in versioned_schemas:
        raise SchemaValidationError(
            f"Unsupported schema_version {schema_version!r} for {schema_name}"
        )

    schema = versioned_schemas[schema_version]
    for field_name, expected_type in schema.required_fields.items():
        if field_name not in data:
            raise SchemaValidationError(f"{field_name} is required")
        if not isinstance(data[field_name], expected_type):
            raise SchemaValidationError(
                f"{field_name} must be {expected_type.__name__}"
            )

    if schema.validator:
        schema.validator(data)
    return data
