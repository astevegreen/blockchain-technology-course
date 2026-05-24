import json
from dataclasses import dataclass

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .enums import enum_values
from .ingest import effective_tags
from .json_validation import SchemaValidationError, validate_versioned_json
from .question_bank import _normalize_filter_tag


class TemplateError(ValueError):
    pass


@dataclass(frozen=True)
class TemplateFields:
    title: str
    description: str | None
    criteria: dict
    question_count: int
    selection_policy: str
    timer_minutes: int | None
    attempt_limit: int
    result_policy: str
    question_order_mode: str
    option_order_mode: str
    default_available_offset_minutes: int | None
    default_available_duration_minutes: int | None


DEFAULT_CRITERIA = {
    "schema_version": 1,
    "lesson_ids": [],
    "topics": [],
    "tags": [],
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

SOURCE_RULE_FILTER_MODES = {"inherit", "override"}
CRITERIA_BASE_KEYS = tuple(DEFAULT_CRITERIA.keys())


def normalize_criteria(value):
    raw = dict(DEFAULT_CRITERIA)
    if value:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise TemplateError("criteria must be valid JSON") from exc
        if not isinstance(value, dict):
            raise TemplateError("criteria must be an object")
        raw.update(value)

    raw["schema_version"] = int(raw.get("schema_version", 1))
    _normalize_base_criteria_fields(raw)
    if raw["schema_version"] == 2:
        raw["source_rules"] = _normalize_source_rules(raw.get("source_rules") or [])
    else:
        raw.pop("source_rules", None)

    try:
        return validate_versioned_json("criteria_json", raw)
    except SchemaValidationError as exc:
        raise TemplateError(str(exc)) from exc


def normalize_template_fields(payload, *, defaults=None):
    defaults = defaults or {}
    if not isinstance(payload, dict):
        raise TemplateError("template payload must be an object")

    title = _required_text(payload.get("title", defaults.get("title")), "title")
    description = _optional_text(
        payload.get("description", defaults.get("description")),
        "description",
    )
    criteria = normalize_criteria(payload.get("criteria", defaults.get("criteria")))
    question_count = _positive_int(
        payload.get("question_count", defaults.get("question_count", 10)),
        "question_count",
    )
    _validate_source_rule_total(criteria, question_count)
    selection_policy = str(
        payload.get("selection_policy", defaults.get("selection_policy", "random"))
    )
    if selection_policy not in enum_values("selection_policy"):
        raise TemplateError("selection_policy is not canonical")
    timer_minutes = _optional_positive_int(
        payload.get("timer_minutes", defaults.get("timer_minutes")),
        "timer_minutes",
    )
    attempt_limit = _positive_int(
        payload.get("attempt_limit", defaults.get("attempt_limit", 1)),
        "attempt_limit",
    )
    result_policy = str(
        payload.get("result_policy", defaults.get("result_policy", "score_after_grading"))
    )
    if result_policy not in enum_values("result_policy"):
        raise TemplateError("result_policy is not canonical")
    question_order_mode = _order_mode(
        payload,
        "question_order_mode",
        "question_order_policy",
        defaults,
    )
    option_order_mode = _order_mode(
        payload,
        "option_order_mode",
        "option_order_policy",
        defaults,
    )
    default_available_offset_minutes = _optional_int(
        payload.get(
            "default_available_offset_minutes",
            defaults.get("default_available_offset_minutes"),
        ),
        "default_available_offset_minutes",
    )
    default_available_duration_minutes = _optional_positive_int(
        payload.get(
            "default_available_duration_minutes",
            defaults.get("default_available_duration_minutes"),
        ),
        "default_available_duration_minutes",
    )

    return TemplateFields(
        title=title,
        description=description,
        criteria=criteria,
        question_count=question_count,
        selection_policy=selection_policy,
        timer_minutes=timer_minutes,
        attempt_limit=attempt_limit,
        result_policy=result_policy,
        question_order_mode=question_order_mode,
        option_order_mode=option_order_mode,
        default_available_offset_minutes=default_available_offset_minutes,
        default_available_duration_minutes=default_available_duration_minutes,
    )


def has_source_rules(criteria):
    return bool(normalize_criteria(criteria).get("source_rules"))


def criteria_without_source_rules(criteria):
    normalized = normalize_criteria(criteria)
    base = {key: normalized[key] for key in CRITERIA_BASE_KEYS if key in normalized}
    base["schema_version"] = 1
    return normalize_criteria(base)


def source_rule_effective_criteria(criteria, rule):
    normalized = normalize_criteria(criteria)
    if rule["filter_mode"] == "override":
        effective = dict(rule.get("criteria") or _normalize_embedded_criteria({}))
    else:
        effective = criteria_without_source_rules(normalized)
    effective["schema_version"] = 1
    effective["lesson_ids"] = [rule["lesson_id"]]
    return normalize_criteria(effective)


def source_rule_question_count_total(criteria):
    normalized = normalize_criteria(criteria)
    return sum(rule["question_count"] for rule in normalized.get("source_rules", []))


def _normalize_base_criteria_fields(raw):
    raw["lesson_ids"] = _string_list(raw.get("lesson_ids"), "lesson_ids")
    raw["topics"] = _string_list(raw.get("topics"), "topics")
    raw["tags"] = _dedupe(
        tag
        for tag in (_normalize_filter_tag(value) for value in raw.get("tags", []))
        if tag
    )
    raw["excluded_topics"] = _string_list(
        raw.get("excluded_topics"),
        "excluded_topics",
    )
    raw["excluded_tags"] = _dedupe(
        tag
        for tag in (
            _normalize_filter_tag(value) for value in raw.get("excluded_tags", [])
        )
        if tag
    )
    raw["tag_match_mode"] = str(raw.get("tag_match_mode") or "any")
    raw["hierarchy_sections"] = _string_list(
        raw.get("hierarchy_sections"),
        "hierarchy_sections",
    )
    raw["hierarchy_lectures"] = _string_list(
        raw.get("hierarchy_lectures"),
        "hierarchy_lectures",
    )
    raw["difficulty_min"] = _bounded_difficulty(raw.get("difficulty_min", 1))
    raw["difficulty_max"] = _bounded_difficulty(raw.get("difficulty_max", 5))
    raw["question_types"] = _string_list(
        raw.get("question_types") or ["multiple_choice"],
        "question_types",
    )
    raw["quotas"] = _normalize_quotas(raw.get("quotas") or {})
    raw["require_topic_coverage"] = bool(raw.get("require_topic_coverage"))


def _normalize_source_rules(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise TemplateError("source_rules must be a list")

    normalized = []
    seen_lesson_ids = set()
    for index, rule in enumerate(value):
        if not isinstance(rule, dict):
            raise TemplateError("source_rules entries must be objects")
        prefix = f"source_rules[{index}]"
        lesson_id = _required_text(rule.get("lesson_id"), f"{prefix}.lesson_id")
        if lesson_id in seen_lesson_ids:
            raise TemplateError(f"{prefix}.lesson_id must be unique")
        seen_lesson_ids.add(lesson_id)

        filter_mode = str(rule.get("filter_mode") or "inherit")
        if filter_mode not in SOURCE_RULE_FILTER_MODES:
            raise TemplateError(f"{prefix}.filter_mode is not canonical")

        question_count = _positive_int(
            rule.get("question_count"),
            f"{prefix}.question_count",
        )
        selection_policy = rule.get("selection_policy")
        if selection_policy is not None and str(selection_policy).strip():
            selection_policy = str(selection_policy).strip()
            if selection_policy not in enum_values("selection_policy"):
                raise TemplateError(f"{prefix}.selection_policy is not canonical")
        else:
            selection_policy = None

        criteria = rule.get("criteria")
        if filter_mode == "override":
            criteria = _normalize_embedded_criteria(criteria or {})
            _validate_quota_total(
                criteria,
                question_count,
                f"{prefix}.criteria.quotas",
            )
        elif criteria:
            criteria = _normalize_embedded_criteria(criteria)
        else:
            criteria = None

        normalized.append(
            {
                "lesson_id": lesson_id,
                "filter_mode": filter_mode,
                "question_count": question_count,
                "selection_policy": selection_policy,
                "criteria": criteria,
            }
        )
    return normalized


def _normalize_embedded_criteria(value):
    if not isinstance(value, dict):
        raise TemplateError("source_rules.criteria must be an object")
    raw = dict(DEFAULT_CRITERIA)
    raw.update(value)
    raw["schema_version"] = 1
    raw.pop("source_rules", None)
    _normalize_base_criteria_fields(raw)
    raw["lesson_ids"] = []
    try:
        return validate_versioned_json("criteria_json", raw)
    except SchemaValidationError as exc:
        raise TemplateError(str(exc)) from exc


def _validate_quota_total(criteria, question_count, field_name):
    quota_total = sum(sum(quota.values()) for quota in criteria["quotas"].values())
    if quota_total > question_count:
        raise TemplateError(
            f"{field_name} total {quota_total} exceeds source question_count {question_count}"
        )


def _validate_source_rule_total(criteria, question_count):
    total = sum(rule["question_count"] for rule in criteria.get("source_rules", []))
    if total and total != question_count:
        raise TemplateError(
            f"source_rules question_count total {total} must equal template question_count {question_count}"
        )


def _string_list(value, field_name):
    if value is None:
        return []
    if not isinstance(value, list):
        raise TemplateError(f"{field_name} must be a list")
    result = []
    for item in value:
        if not isinstance(item, str):
            raise TemplateError(f"{field_name} must be a list of strings")
        item = item.strip()
        if item and item not in result:
            result.append(item)
    return result


def _dedupe(values):
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _normalize_quotas(value):
    if not isinstance(value, dict):
        raise TemplateError("quotas must be an object")
    source = dict(value)
    if "lessons" in source and "lesson_ids" not in source:
        source["lesson_ids"] = source["lessons"]

    quotas = {}
    for quota_name in ("topics", "tags", "lesson_ids"):
        quota = source.get(quota_name, {})
        if quota is None:
            quota = {}
        if not isinstance(quota, dict):
            raise TemplateError(f"quotas.{quota_name} must be an object")
        normalized = {}
        for key, amount in quota.items():
            key = str(key).strip()
            if quota_name == "tags":
                key = _normalize_filter_tag(key) or ""
            if not key:
                raise TemplateError(f"quotas.{quota_name} keys must be non-empty")
            normalized[key] = _positive_int(
                amount,
                f"quotas.{quota_name}.{key}",
            )
        if normalized:
            quotas[quota_name] = normalized
    return quotas


def _required_text(value, field_name):
    value = _optional_text(value, field_name)
    if value is None:
        raise TemplateError(f"{field_name} is required")
    return value


def _optional_text(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise TemplateError(f"{field_name} must be text")
    value = value.strip()
    return value or None


def _positive_int(value, field_name):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TemplateError(f"{field_name} must be an integer") from exc
    if parsed <= 0:
        raise TemplateError(f"{field_name} must be positive")
    return parsed


def _optional_positive_int(value, field_name):
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TemplateError(f"{field_name} must be an integer") from exc
    if parsed < 1:
        return None
    return parsed


def _order_mode(payload, mode_field, legacy_field, defaults):
    value = payload.get(mode_field)
    if value is None or str(value).strip() == "":
        value = payload.get(legacy_field)
    if value is None or str(value).strip() == "":
        value = defaults.get(mode_field)
    if value is None or str(value).strip() == "":
        value = defaults.get(legacy_field)
    if value is None or str(value).strip() == "":
        value = "random_per_attempt"
    value = str(value).strip()
    if value not in enum_values("order_mode"):
        raise TemplateError(f"{mode_field} is not canonical")
    return value


def _optional_int(value, field_name):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TemplateError(f"{field_name} must be an integer") from exc


def _bounded_difficulty(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TemplateError("difficulty range must be within 1..5") from exc
    if not 1 <= parsed <= 5:
        raise TemplateError("difficulty range must be within 1..5")
    return parsed


def build_eligible_pool_query(criteria):
    criteria = normalize_criteria(criteria)
    conditions = [
        "question.status = 'active'",
        "question.superseded_at IS NULL",
        "bank.archived = 0",
        "revision.status = 'active'",
        """
        NOT EXISTS (
            SELECT 1
            FROM question_retirements retirement
            WHERE retirement.question_id = question.id
        )
        """,
    ]
    params = []

    _append_in_filter(conditions, params, "bank.lesson_id", criteria["lesson_ids"])
    _append_in_filter(conditions, params, "question.topic", criteria["topics"])
    _append_not_in_filter(
        conditions,
        params,
        "question.topic",
        criteria["excluded_topics"],
    )
    _append_in_filter(
        conditions,
        params,
        "question.content_section_id",
        criteria["hierarchy_sections"],
    )
    _append_in_filter(
        conditions,
        params,
        "question.content_lecture_id",
        criteria["hierarchy_lectures"],
    )
    _append_in_filter(conditions, params, "question.question_type", criteria["question_types"])
    conditions.append("question.difficulty_level BETWEEN ? AND ?")
    params.extend([criteria["difficulty_min"], criteria["difficulty_max"]])

    if criteria["tags"]:
        if criteria["tag_match_mode"] == "all":
            for tag in criteria["tags"]:
                conditions.append(_effective_tag_exists_sql())
                params.extend([tag, tag])
        else:
            placeholders = ", ".join("?" for _ in criteria["tags"])
            conditions.append(
                f"""
                (
                    EXISTS (
                        SELECT 1
                        FROM question_tags question_tag
                        WHERE question_tag.question_id = question.id
                          AND question_tag.tag IN ({placeholders})
                    )
                    OR EXISTS (
                        SELECT 1
                        FROM bank_revision_tags bank_tag
                        WHERE bank_tag.bank_revision_id = revision.id
                          AND bank_tag.tag IN ({placeholders})
                    )
                )
                """
            )
            params.extend(criteria["tags"])
            params.extend(criteria["tags"])

    if criteria["excluded_tags"]:
        placeholders = ", ".join("?" for _ in criteria["excluded_tags"])
        conditions.append(
            f"""
            NOT EXISTS (
                SELECT 1
                FROM question_tags question_tag
                WHERE question_tag.question_id = question.id
                  AND question_tag.tag IN ({placeholders})
            )
            """
        )
        conditions.append(
            f"""
            NOT EXISTS (
                SELECT 1
                FROM bank_revision_tags bank_tag
                WHERE bank_tag.bank_revision_id = revision.id
                  AND bank_tag.tag IN ({placeholders})
            )
            """
        )
        params.extend(criteria["excluded_tags"])
        params.extend(criteria["excluded_tags"])

    sql = f"""
        SELECT
            question.id,
            question.source_qid,
            question.question_type,
            question.question_stem,
            question.difficulty_level,
            question.topic,
            question.content_section_id,
            question.content_lecture_id,
            question.bank_revision_id,
            bank.id AS quiz_bank_id,
            bank.lesson_id,
            bank.lesson_title
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE {" AND ".join(conditions)}
        ORDER BY question.bank_revision_id, question.source_qid, question.id
    """
    return sql, params


def _append_in_filter(conditions, params, column, values):
    if not values:
        return
    placeholders = ", ".join("?" for _ in values)
    conditions.append(f"{column} IN ({placeholders})")
    params.extend(values)


def _append_not_in_filter(conditions, params, column, values):
    if not values:
        return
    placeholders = ", ".join("?" for _ in values)
    conditions.append(f"{column} NOT IN ({placeholders})")
    params.extend(values)


def _effective_tag_exists_sql():
    return """
        (
            EXISTS (
                SELECT 1
                FROM question_tags question_tag
                WHERE question_tag.question_id = question.id
                  AND question_tag.tag = ?
            )
            OR EXISTS (
                SELECT 1
                FROM bank_revision_tags bank_tag
                WHERE bank_tag.bank_revision_id = revision.id
                  AND bank_tag.tag = ?
            )
        )
    """


def preview_eligible_pool(criteria, question_count, *, conn=None):
    criteria = normalize_criteria(criteria)
    question_count = _positive_int(question_count, "question_count")
    conn = conn or get_db()
    if criteria.get("source_rules"):
        return _preview_source_rule_pool(criteria, question_count, conn)

    rows = _eligible_rows_for_preview(criteria, conn)
    warnings = _preview_warnings(criteria, question_count, rows)
    return _preview_payload(criteria, question_count, rows, warnings)


def _preview_source_rule_pool(criteria, question_count, conn):
    all_rows = []
    source_previews = []
    warnings = []
    total_requested = source_rule_question_count_total(criteria)
    if total_requested != question_count:
        warnings.append(
            {
                "code": "source_rule_total_mismatch",
                "source_rule_total": total_requested,
                "question_count": question_count,
                "filter_summary": _criteria_filter_summary(criteria),
            }
        )

    for index, rule in enumerate(criteria["source_rules"]):
        effective = source_rule_effective_criteria(criteria, rule)
        rows = _eligible_rows_for_preview(effective, conn)
        all_rows.extend(rows)
        rule_warnings = _preview_warnings(effective, rule["question_count"], rows)
        source_previews.append(
            {
                "index": index,
                "lesson_id": rule["lesson_id"],
                "filter_mode": rule["filter_mode"],
                "question_count": rule["question_count"],
                "selection_policy": rule["selection_policy"],
                "eligible_pool_size": len(rows),
                "warnings": rule_warnings,
                "counts": {
                    "by_topic": _count_by(rows, "topic"),
                    "by_lesson_id": _count_by(rows, "lesson_id"),
                    "by_difficulty": _count_by(rows, "difficulty_level"),
                    "by_question_type": _count_by(rows, "question_type"),
                },
                "question_ids": [row["id"] for row in rows],
                "bank_revision_ids": sorted(
                    {row["bank_revision_id"] for row in rows}
                ),
            }
        )
        warnings.extend(
            dict(warning, source_lesson_id=rule["lesson_id"], source_index=index)
            for warning in rule_warnings
        )

    return _preview_payload(
        criteria,
        question_count,
        all_rows,
        warnings,
        source_previews=source_previews,
    )


def _eligible_rows_for_preview(criteria, conn):
    sql, params = build_eligible_pool_query(criteria)
    rows = [dict(row) for row in conn.execute(sql, params).fetchall()]
    tags_by_question = _tags_by_question(conn, [row["id"] for row in rows])
    bank_tags_by_revision = _bank_tags_by_revision(
        conn,
        [row["bank_revision_id"] for row in rows],
    )
    for row in rows:
        row["question_tags"] = tags_by_question.get(row["id"], [])
        row["bank_tags"] = bank_tags_by_revision.get(row["bank_revision_id"], [])
        row["effective_tags"] = list(
            effective_tags(row["bank_tags"], row["question_tags"])
        )
    return rows


def _preview_payload(criteria, question_count, rows, warnings, *, source_previews=None):
    payload = {
        "eligible_pool_size": len(rows),
        "question_count": question_count,
        "warnings": warnings,
        "counts": {
            "by_topic": _count_by(rows, "topic"),
            "by_lesson_id": _count_by(rows, "lesson_id"),
            "by_difficulty": _count_by(rows, "difficulty_level"),
            "by_question_type": _count_by(rows, "question_type"),
        },
        "question_ids": [row["id"] for row in rows],
        "bank_revision_ids": sorted({row["bank_revision_id"] for row in rows}),
    }
    if source_previews is not None:
        payload["source_rules"] = source_previews
    return payload


def _preview_warnings(criteria, question_count, rows):
    warnings = []
    filter_summary = _criteria_filter_summary(criteria)
    if len(rows) < question_count:
        warnings.append(
            {
                "code": "insufficient_pool",
                "message": (
                    f"Eligible pool has {len(rows)} questions but "
                    f"{question_count} are requested."
                ),
                "eligible_pool_size": len(rows),
                "question_count": question_count,
                "shortfall": question_count - len(rows),
                "filter_summary": filter_summary,
            }
        )

    quota_total = 0
    for quota_type, quota in criteria["quotas"].items():
        for key, required in quota.items():
            quota_total += required
            available = _quota_available_count(rows, quota_type, key)
            if available < required:
                warnings.append(
                    {
                        "code": "unsatisfied_quota",
                        "quota_type": quota_type,
                        "quota": key,
                        "required": required,
                        "available": available,
                        "filter_summary": filter_summary,
                    }
                )
    if quota_total > question_count:
        warnings.append(
            {
                "code": "quota_total_exceeds_question_count",
                "required": quota_total,
                "question_count": question_count,
                "filter_summary": filter_summary,
            }
        )

    if criteria["require_topic_coverage"]:
        present_topics = sorted({row["topic"] for row in rows})
        required_topics = criteria["topics"] or present_topics
        missing_topics = [
            topic for topic in required_topics if topic not in set(present_topics)
        ]
        if missing_topics:
            warnings.append(
                {
                    "code": "unsatisfied_topic_coverage",
                    "missing_topics": missing_topics,
                    "filter_summary": filter_summary,
                }
            )
        if len(required_topics) > question_count:
            warnings.append(
                {
                    "code": "topic_coverage_requires_more_questions",
                    "required_topics": len(required_topics),
                    "question_count": question_count,
                    "filter_summary": filter_summary,
                }
            )
    return warnings


def _criteria_filter_summary(criteria):
    return {
        "lesson_ids": criteria.get("lesson_ids", []),
        "topics": criteria.get("topics", []),
        "tags": criteria.get("tags", []),
        "excluded_topics": criteria.get("excluded_topics", []),
        "excluded_tags": criteria.get("excluded_tags", []),
        "tag_match_mode": criteria.get("tag_match_mode", "any"),
        "difficulty_min": criteria.get("difficulty_min", 1),
        "difficulty_max": criteria.get("difficulty_max", 5),
        "question_types": criteria.get("question_types", []),
        "quotas": criteria.get("quotas", {}),
        "require_topic_coverage": criteria.get("require_topic_coverage", False),
    }


def _quota_available_count(rows, quota_type, key):
    if quota_type == "topics":
        return sum(1 for row in rows if row["topic"] == key)
    if quota_type == "lesson_ids":
        return sum(1 for row in rows if row["lesson_id"] == key)
    if quota_type == "tags":
        return sum(1 for row in rows if key in row["effective_tags"])
    return 0


def _count_by(rows, field_name):
    counts = {}
    for row in rows:
        key = str(row[field_name])
        counts[key] = counts.get(key, 0) + 1
    return counts


def _tags_by_question(conn, question_ids):
    if not question_ids:
        return {}
    placeholders = ", ".join("?" for _ in question_ids)
    rows = conn.execute(
        f"""
        SELECT question_id, tag
        FROM question_tags
        WHERE question_id IN ({placeholders})
        ORDER BY tag
        """,
        question_ids,
    ).fetchall()
    tags = {question_id: [] for question_id in question_ids}
    for row in rows:
        tags[row["question_id"]].append(row["tag"])
    return tags


def _bank_tags_by_revision(conn, bank_revision_ids):
    if not bank_revision_ids:
        return {}
    unique_ids = sorted(set(bank_revision_ids))
    placeholders = ", ".join("?" for _ in unique_ids)
    rows = conn.execute(
        f"""
        SELECT bank_revision_id, tag
        FROM bank_revision_tags
        WHERE bank_revision_id IN ({placeholders})
        ORDER BY tag
        """,
        unique_ids,
    ).fetchall()
    tags = {bank_revision_id: [] for bank_revision_id in unique_ids}
    for row in rows:
        tags[row["bank_revision_id"]].append(row["tag"])
    return tags


def create_template(payload, *, actor_sub=None, conn=None):
    fields = normalize_template_fields(payload)
    conn = conn or get_db()
    now = utc_now_iso()
    with conn:
        template_id = conn.execute(
            """
            INSERT INTO quiz_templates (
                title,
                description,
                criteria_json,
                question_count,
                selection_policy,
                timer_minutes,
                attempt_limit,
                result_policy,
                question_order_mode,
                option_order_mode,
                default_available_offset_minutes,
                default_available_duration_minutes,
                archived,
                created_by,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            _template_values(fields, actor_sub, now, now),
        ).lastrowid
        _record_template_audit(conn, "quiz_template.created", template_id, actor_sub)
    return get_template(template_id, conn=conn)


def update_template(template_id, payload, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    existing = get_template(template_id, conn=conn)
    if existing is None:
        raise TemplateError("template not found")
    fields = normalize_template_fields(payload, defaults=existing)
    now = utc_now_iso()
    with conn:
        conn.execute(
            """
            UPDATE quiz_templates
            SET title = ?,
                description = ?,
                criteria_json = ?,
                question_count = ?,
                selection_policy = ?,
                timer_minutes = ?,
                attempt_limit = ?,
                result_policy = ?,
                question_order_mode = ?,
                option_order_mode = ?,
                default_available_offset_minutes = ?,
                default_available_duration_minutes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                fields.title,
                fields.description,
                json.dumps(fields.criteria, sort_keys=True),
                fields.question_count,
                fields.selection_policy,
                fields.timer_minutes,
                fields.attempt_limit,
                fields.result_policy,
                fields.question_order_mode,
                fields.option_order_mode,
                fields.default_available_offset_minutes,
                fields.default_available_duration_minutes,
                now,
                template_id,
            ),
        )
        _record_template_audit(conn, "quiz_template.updated", template_id, actor_sub)
    return get_template(template_id, conn=conn)


def duplicate_template(template_id, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    existing = get_template(template_id, conn=conn)
    if existing is None:
        raise TemplateError("template not found")
    payload = dict(existing)
    payload["title"] = f"{existing['title']} Copy"
    created = create_template(payload, actor_sub=actor_sub, conn=conn)
    with conn:
        _record_template_audit(
            conn,
            "quiz_template.duplicated",
            created["id"],
            actor_sub,
            source_template_id=template_id,
        )
    return created


def archive_template(template_id, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    if get_template(template_id, include_archived=True, conn=conn) is None:
        raise TemplateError("template not found")
    with conn:
        conn.execute(
            """
            UPDATE quiz_templates
            SET archived = 1,
                updated_at = ?
            WHERE id = ?
            """,
            (utc_now_iso(), template_id),
        )
        _record_template_audit(conn, "quiz_template.archived", template_id, actor_sub)
    return get_template(template_id, include_archived=True, conn=conn)


def list_templates(*, include_archived=False, conn=None):
    conn = conn or get_db()
    conditions = []
    if not include_archived:
        conditions.append("archived = 0")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = conn.execute(
        f"""
        SELECT *
        FROM quiz_templates
        {where}
        ORDER BY updated_at DESC, id DESC
        """
    ).fetchall()
    return [_template_row_to_dict(row) for row in rows]


def get_template(template_id, *, include_archived=True, conn=None):
    conn = conn or get_db()
    conditions = ["id = ?"]
    params = [template_id]
    if not include_archived:
        conditions.append("archived = 0")
    row = conn.execute(
        f"""
        SELECT *
        FROM quiz_templates
        WHERE {" AND ".join(conditions)}
        """,
        params,
    ).fetchone()
    return _template_row_to_dict(row) if row else None


def _template_values(fields, created_by, created_at, updated_at):
    return (
        fields.title,
        fields.description,
        json.dumps(fields.criteria, sort_keys=True),
        fields.question_count,
        fields.selection_policy,
        fields.timer_minutes,
        fields.attempt_limit,
        fields.result_policy,
        fields.question_order_mode,
        fields.option_order_mode,
        fields.default_available_offset_minutes,
        fields.default_available_duration_minutes,
        created_by,
        created_at,
        updated_at,
    )


def _template_row_to_dict(row):
    if row is None:
        return None
    data = dict(row)
    data["criteria"] = json.loads(data.pop("criteria_json"))
    data["archived"] = bool(data["archived"])
    return data


def _record_template_audit(
    conn,
    event_type,
    template_id,
    actor_sub,
    *,
    source_template_id=None,
):
    details = {"template_id": template_id}
    if source_template_id is not None:
        details["source_template_id"] = source_template_id
    record_audit_event(
        event_type,
        actor_sub=actor_sub,
        object_type="quiz_template",
        object_id=template_id,
        details={"schema_version": 1, "details": details},
        db=conn,
    )
