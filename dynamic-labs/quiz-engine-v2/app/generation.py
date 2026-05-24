import hashlib
import json
import random
import secrets
from dataclasses import dataclass

from .db import get_db
from .enums import enum_values
from .ingest import effective_tags
from .quiz_templates import (
    TemplateError,
    build_eligible_pool_query,
    criteria_without_source_rules,
    get_template,
    has_source_rules,
    normalize_criteria,
    source_rule_effective_criteria,
    source_rule_question_count_total,
)
from .quiz_versions import create_quiz_version_snapshot


class GenerationError(ValueError):
    pass


@dataclass(frozen=True)
class GenerationFields:
    template_id: int | None
    title: str
    description: str | None
    criteria: dict
    question_count: int
    selection_policy: str
    random_seed: str
    timer_minutes: int | None
    attempt_limit: int
    result_policy: str
    question_order_mode: str
    option_order_mode: str
    question_order_policy: str
    option_order_policy: str


def generate_quiz_version_from_template(
    template_id,
    *,
    overrides=None,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    template = get_template(int(template_id), include_archived=False, conn=conn)
    if template is None:
        raise GenerationError("template not found")
    payload = dict(overrides or {})
    payload.setdefault("title", template["title"])
    payload.setdefault("description", template["description"])
    payload.setdefault("criteria", template["criteria"])
    payload.setdefault("question_count", template["question_count"])
    payload.setdefault("selection_policy", template["selection_policy"])
    payload.setdefault("timer_minutes", template["timer_minutes"])
    payload.setdefault("attempt_limit", template["attempt_limit"])
    payload.setdefault("result_policy", template["result_policy"])
    if "question_order_mode" not in payload and "question_order_policy" not in payload:
        payload["question_order_mode"] = template.get(
            "question_order_mode",
            "random_per_attempt",
        )
    if "option_order_mode" not in payload and "option_order_policy" not in payload:
        payload["option_order_mode"] = template.get(
            "option_order_mode",
            "random_per_attempt",
        )
    payload["template_id"] = template["id"]
    return generate_quiz_version(payload, actor_sub=actor_sub, conn=conn)


def generate_quiz_version(payload, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    fields = normalize_generation_fields(payload)
    if has_source_rules(fields.criteria):
        (
            rows,
            selected_rows,
            quota_allocations,
            coverage_allocations,
            source_allocations,
        ) = _select_source_rule_questions(fields, conn)
    else:
        rows = _eligible_rows(fields.criteria, conn)
        try:
            selected_rows, quota_allocations, coverage_allocations = select_questions(
                rows,
                fields.criteria,
                fields.question_count,
                fields.selection_policy,
                fields.random_seed,
            )
        except GenerationError as exc:
            raise _selection_context_error(
                exc,
                label="overall quiz",
                criteria=fields.criteria,
                question_count=fields.question_count,
                eligible_count=len(rows),
            ) from exc
        source_allocations = []
    selected_rows = _ordered_selected_rows(selected_rows, fields)
    selected_question_ids = [row["id"] for row in selected_rows]
    snapshot = _generation_snapshot(
        fields,
        rows,
        selected_rows,
        quota_allocations,
        coverage_allocations,
        source_allocations,
    )
    try:
        return create_quiz_version_snapshot(
            template_id=fields.template_id,
            title=fields.title,
            description=fields.description,
            generation_snapshot=snapshot,
            source_question_ids=selected_question_ids,
            timer_minutes=fields.timer_minutes,
            attempt_limit=fields.attempt_limit,
            result_policy=fields.result_policy,
            question_order_policy=fields.question_order_policy,
            option_order_policy=fields.option_order_policy,
            option_order_mode=fields.option_order_mode,
            option_order_seed=fields.random_seed,
            actor_sub=actor_sub,
            conn=conn,
        )
    except ValueError as exc:
        raise GenerationError(str(exc)) from exc


def normalize_generation_fields(payload):
    if not isinstance(payload, dict):
        raise GenerationError("generation payload must be an object")
    try:
        criteria = normalize_criteria(payload.get("criteria", {}))
    except TemplateError as exc:
        raise GenerationError(str(exc)) from exc

    selection_policy = str(payload.get("selection_policy", "random"))
    if selection_policy not in enum_values("selection_policy"):
        raise GenerationError("selection_policy is not canonical")
    result_policy = str(payload.get("result_policy", "score_after_grading"))
    if result_policy not in enum_values("result_policy"):
        raise GenerationError("result_policy is not canonical")
    question_order_mode = _order_mode(
        payload,
        "question_order_mode",
        "question_order_policy",
    )
    option_order_mode = _order_mode(
        payload,
        "option_order_mode",
        "option_order_policy",
    )
    question_order_policy = _attempt_order_policy(question_order_mode)
    option_order_policy = _attempt_order_policy(option_order_mode)

    question_count = _positive_int(payload.get("question_count", 10), "question_count")
    _validate_source_rule_total(criteria, question_count)

    return GenerationFields(
        template_id=_optional_int(payload.get("template_id"), "template_id"),
        title=_required_text(payload.get("title"), "title"),
        description=_optional_text(payload.get("description"), "description"),
        criteria=criteria,
        question_count=question_count,
        selection_policy=selection_policy,
        random_seed=_seed(payload.get("random_seed")),
        timer_minutes=_optional_positive_int(payload.get("timer_minutes"), "timer_minutes"),
        attempt_limit=_positive_int(payload.get("attempt_limit", 1), "attempt_limit"),
        result_policy=result_policy,
        question_order_mode=question_order_mode,
        option_order_mode=option_order_mode,
        question_order_policy=question_order_policy,
        option_order_policy=option_order_policy,
    )


def _validate_source_rule_total(criteria, question_count):
    total = source_rule_question_count_total(criteria)
    if total and total != question_count:
        raise GenerationError(
            f"source_rules question_count total {total} must equal requested question_count {question_count}"
        )


def _order_mode(payload, mode_field, legacy_field):
    value = payload.get(mode_field)
    if value is None or str(value).strip() == "":
        value = payload.get(legacy_field)
    if value is None or str(value).strip() == "":
        value = "random_per_attempt"
    value = str(value).strip()
    if value not in enum_values("order_mode"):
        raise GenerationError(f"{mode_field} is not canonical")
    return value


def _attempt_order_policy(order_mode):
    return "random_per_attempt" if order_mode == "random_per_attempt" else "fixed"


def _ordered_selected_rows(selected_rows, fields):
    ordered = list(selected_rows)
    if fields.question_order_mode == "fixed":
        return ordered
    rng = random.Random(_stable_seed(f"question-order:{fields.random_seed}"))
    rng.shuffle(ordered)
    return ordered


def select_questions(rows, criteria, question_count, selection_policy, random_seed):
    if len(rows) < question_count:
        raise GenerationError(
            f"eligible pool has {len(rows)} questions but {question_count} are requested"
        )

    quota_total = sum(sum(quota.values()) for quota in criteria["quotas"].values())
    if quota_total > question_count:
        raise GenerationError(
            f"quota total {quota_total} exceeds requested question_count {question_count}"
        )

    rng = random.Random(_stable_seed(random_seed))
    selected = []
    selected_ids = set()
    quota_allocations = {}
    for quota_type in ("topics", "tags", "lesson_ids"):
        quota = criteria["quotas"].get(quota_type, {})
        if not quota:
            continue
        quota_allocations[quota_type] = {}
        for key in sorted(quota):
            required = quota[key]
            candidates = [
                row
                for row in rows
                if row["id"] not in selected_ids and _matches_quota(row, quota_type, key)
            ]
            if len(candidates) < required:
                raise GenerationError(
                    f"unsatisfied quota {quota_type}.{key}: "
                    f"required {required}, available {len(candidates)}"
                )
            picked = _sample(rng, candidates, required)
            selected.extend(picked)
            selected_ids.update(row["id"] for row in picked)
            quota_allocations[quota_type][key] = [row["id"] for row in picked]

    coverage_allocations = {}
    if criteria["require_topic_coverage"]:
        required_topics = criteria["topics"] or sorted({row["topic"] for row in rows})
        if len(required_topics) > question_count:
            raise GenerationError(
                f"topic coverage requires {len(required_topics)} questions but "
                f"question_count is {question_count}"
            )
        for topic in sorted(required_topics):
            already = next((row for row in selected if row["topic"] == topic), None)
            if already is not None:
                coverage_allocations[topic] = already["id"]
                continue
            candidates = [
                row
                for row in rows
                if row["id"] not in selected_ids and row["topic"] == topic
            ]
            if not candidates:
                raise GenerationError(f"unsatisfied topic coverage: {topic}")
            if len(selected) >= question_count:
                raise GenerationError(f"unsatisfied topic coverage: {topic}")
            picked = _sample(rng, candidates, 1)[0]
            selected.append(picked)
            selected_ids.add(picked["id"])
            coverage_allocations[topic] = picked["id"]

    remaining_slots = question_count - len(selected)
    if remaining_slots < 0:
        raise GenerationError("quota and coverage allocations exceed question_count")
    if remaining_slots:
        remaining = [row for row in rows if row["id"] not in selected_ids]
        selected.extend(_fill_remaining(remaining, remaining_slots, selection_policy, rng, criteria))

    return selected, quota_allocations, coverage_allocations


def _fill_remaining(rows, count, selection_policy, rng, criteria):
    if selection_policy == "random":
        return _sample(rng, rows, count)
    if selection_policy == "balanced_difficulty":
        return _balanced_difficulty(rows, count, rng)
    if selection_policy == "focused_difficulty":
        return _focused_difficulty(rows, count, rng, criteria)
    raise GenerationError("selection_policy is not canonical")


def _balanced_difficulty(rows, count, rng):
    by_level = _rows_by_difficulty(rows)
    levels = sorted(by_level)
    if not levels:
        return []
    base = count // len(levels)
    remainder = count % len(levels)
    allocations = {
        level: base + (1 if index < remainder else 0)
        for index, level in enumerate(levels)
    }

    selected = []
    selected_ids = set()
    shortfalls = []
    for level in levels:
        available = [row for row in by_level[level] if row["id"] not in selected_ids]
        needed = allocations[level]
        picked = _sample(rng, available, min(needed, len(available)))
        selected.extend(picked)
        selected_ids.update(row["id"] for row in picked)
        if len(picked) < needed:
            shortfalls.extend([level] * (needed - len(picked)))

    for preferred_level in shortfalls:
        if len(selected) >= count:
            break
        available = [row for row in rows if row["id"] not in selected_ids]
        if not available:
            break
        distances = sorted({abs(row["difficulty_level"] - preferred_level) for row in available})
        candidates = [
            row
            for row in available
            if abs(row["difficulty_level"] - preferred_level) == distances[0]
        ]
        picked = _sample(rng, candidates, 1)[0]
        selected.append(picked)
        selected_ids.add(picked["id"])

    if len(selected) < count:
        selected.extend(_sample(rng, [row for row in rows if row["id"] not in selected_ids], count - len(selected)))
    return selected


def _focused_difficulty(rows, count, rng, criteria):
    midpoint = (criteria["difficulty_min"] + criteria["difficulty_max"]) / 2
    grouped = {}
    for row in rows:
        distance = abs(row["difficulty_level"] - midpoint)
        grouped.setdefault(distance, []).append(row)
    selected = []
    for distance in sorted(grouped):
        if len(selected) >= count:
            break
        selected.extend(_sample(rng, grouped[distance], min(count - len(selected), len(grouped[distance]))))
    return selected


def _eligible_rows(criteria, conn):
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


def _select_source_rule_questions(fields, conn):
    source_total = source_rule_question_count_total(fields.criteria)
    if source_total != fields.question_count:
        raise GenerationError(
            f"source_rules question_count total {source_total} must equal requested question_count {fields.question_count}"
        )

    all_rows = []
    selected_rows = []
    selected_ids = set()
    source_allocations = []
    quota_allocations = {"source_rules": []}
    coverage_allocations = {"source_rules": []}
    for index, rule in enumerate(fields.criteria["source_rules"]):
        effective = source_rule_effective_criteria(fields.criteria, rule)
        source_rows = [
            row for row in _eligible_rows(effective, conn) if row["id"] not in selected_ids
        ]
        all_rows.extend(source_rows)
        source_seed = f"{fields.random_seed}:{index}:{rule['lesson_id']}"
        source_policy = rule["selection_policy"] or fields.selection_policy
        try:
            picked, source_quotas, source_coverage = select_questions(
                source_rows,
                effective,
                rule["question_count"],
                source_policy,
                source_seed,
            )
        except GenerationError as exc:
            raise _selection_context_error(
                exc,
                label=f"source pool {rule['lesson_id']}",
                criteria=effective,
                question_count=rule["question_count"],
                eligible_count=len(source_rows),
            ) from exc
        selected_rows.extend(picked)
        selected_ids.update(row["id"] for row in picked)
        quota_allocations["source_rules"].append(
            {
                "lesson_id": rule["lesson_id"],
                "allocations": source_quotas,
            }
        )
        coverage_allocations["source_rules"].append(
            {
                "lesson_id": rule["lesson_id"],
                "allocations": source_coverage,
            }
        )
        source_allocations.append(
            {
                "lesson_id": rule["lesson_id"],
                "filter_mode": rule["filter_mode"],
                "question_count": rule["question_count"],
                "eligible_pool_size": len(source_rows),
                "selection_policy": source_policy,
                "selected_question_ids": [row["id"] for row in picked],
                "quota_allocations": source_quotas,
                "coverage_allocations": source_coverage,
                "criteria": effective,
            }
        )

    return (
        all_rows,
        selected_rows,
        quota_allocations,
        coverage_allocations,
        source_allocations,
    )


def _generation_snapshot(
    fields,
    eligible_rows,
    selected_rows,
    quota_allocations,
    coverage_allocations,
    source_allocations,
):
    selected_ids = [row["id"] for row in selected_rows]
    snapshot = {
        "schema_version": 1,
        "criteria": fields.criteria,
        "eligible_pool_size": len(eligible_rows),
        "quota_allocations": quota_allocations,
        "coverage_allocations": coverage_allocations,
        "random_seed": fields.random_seed,
        "bank_revision_ids": sorted({row["bank_revision_id"] for row in selected_rows}),
        "selected_question_ids": selected_ids,
        "selection_policy": fields.selection_policy,
        "question_order_mode": fields.question_order_mode,
        "option_order_mode": fields.option_order_mode,
        "question_order_policy": fields.question_order_policy,
        "option_order_policy": fields.option_order_policy,
        "selected_questions": [
            {
                "question_id": row["id"],
                "source_qid": row["source_qid"],
                "bank_revision_id": row["bank_revision_id"],
                "lesson_id": row["lesson_id"],
                "topic": row["topic"],
                "difficulty_level": row["difficulty_level"],
                "effective_tags": row["effective_tags"],
            }
            for row in selected_rows
        ],
    }
    if source_allocations:
        snapshot["source_allocations"] = source_allocations
        snapshot["fallback_criteria"] = criteria_without_source_rules(fields.criteria)
    return snapshot


def _matches_quota(row, quota_type, key):
    if quota_type == "topics":
        return row["topic"] == key
    if quota_type == "lesson_ids":
        return row["lesson_id"] == key
    if quota_type == "tags":
        return key in row["effective_tags"]
    return False


def _selection_context_error(exc, *, label, criteria, question_count, eligible_count):
    return GenerationError(
        f"{label}: eligible pool matched {eligible_count} questions but "
        f"{question_count} are requested. Filters: {_criteria_summary(criteria)}. "
        f"Underlying issue: {exc}"
    )


def _criteria_summary(criteria):
    parts = []
    if criteria.get("lesson_ids"):
        parts.append("lessons=" + ",".join(criteria["lesson_ids"]))
    if criteria.get("topics"):
        parts.append("topics=" + ",".join(criteria["topics"]))
    if criteria.get("tags"):
        parts.append(
            "tags="
            + ",".join(criteria["tags"])
            + f" ({criteria.get('tag_match_mode', 'any')})"
        )
    if criteria.get("excluded_topics"):
        parts.append("excluded_topics=" + ",".join(criteria["excluded_topics"]))
    if criteria.get("excluded_tags"):
        parts.append("excluded_tags=" + ",".join(criteria["excluded_tags"]))
    parts.append(
        "difficulty="
        + str(criteria.get("difficulty_min", 1))
        + "-"
        + str(criteria.get("difficulty_max", 5))
    )
    if criteria.get("question_types"):
        parts.append("types=" + ",".join(criteria["question_types"]))
    if criteria.get("quotas"):
        parts.append("quotas=" + json.dumps(criteria["quotas"], sort_keys=True))
    if criteria.get("require_topic_coverage"):
        parts.append("requires_topic_coverage=true")
    return "; ".join(parts)


def _sample(rng, rows, count):
    ordered = list(rows)
    rng.shuffle(ordered)
    return ordered[:count]


def _rows_by_difficulty(rows):
    by_level = {}
    for row in rows:
        by_level.setdefault(row["difficulty_level"], []).append(row)
    return by_level


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


def _stable_seed(seed):
    digest = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _seed(value):
    if value is None or str(value).strip() == "":
        return secrets.token_hex(16)
    return str(value).strip()


def _required_text(value, field_name):
    value = _optional_text(value, field_name)
    if value is None:
        raise GenerationError(f"{field_name} is required")
    return value


def _optional_text(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise GenerationError(f"{field_name} must be text")
    value = value.strip()
    return value or None


def _positive_int(value, field_name):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise GenerationError(f"{field_name} must be an integer") from exc
    if parsed <= 0:
        raise GenerationError(f"{field_name} must be positive")
    return parsed


def _optional_positive_int(value, field_name):
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise GenerationError(f"{field_name} must be an integer") from exc
    if parsed < 1:
        return None
    return parsed


def _optional_int(value, field_name):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise GenerationError(f"{field_name} must be an integer") from exc
