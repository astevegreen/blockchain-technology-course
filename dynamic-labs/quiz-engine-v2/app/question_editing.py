import hashlib
import json

from flask import current_app

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .ingest import VALID_TOPICS, effective_tags, normalize_tag
from .question_filter_terms import (
    mark_question_filter_terms_stale,
    queue_question_filter_terms_refresh,
)
from .quiz_templates import build_eligible_pool_query, list_templates


MAX_EDIT_TAGS = 25
MAX_REASON_CHARS = 500


class QuestionEditError(ValueError):
    pass


def get_question_edit_context(question_id, *, conn=None):
    conn = conn or get_db()
    question = _editable_question(conn, question_id)
    if question is None:
        raise QuestionEditError("question is not editable")
    question["options"] = _options(conn, question_id)
    question["question_tags"] = _question_tags(conn, question_id)
    question["bank_tags"] = _bank_tags(conn, question["bank_revision_id"])
    question["effective_tags"] = list(
        effective_tags(question["bank_tags"], question["question_tags"])
    )
    return {
        "question": question,
        "impact": _impact_summary(conn, question_id),
        "revision_chain": _revision_chain(conn, question_id),
    }


def edit_question(question_id, payload, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    expected_question_id = _optional_int(payload.get("expected_question_id"))
    if expected_question_id is not None and expected_question_id != int(question_id):
        raise QuestionEditError("stale question edit; reopen the current version")

    owns_transaction = not conn.in_transaction
    if owns_transaction:
        conn.execute("BEGIN IMMEDIATE")
    try:
        current = get_question_edit_context(question_id, conn=conn)["question"]
        fields = _normalize_edit_payload(current, payload)
        changed_fields = _changed_fields(current, fields)
        if not changed_fields:
            raise QuestionEditError("edit does not change the active question")

        now = utc_now_iso()
        revision_id = _insert_manual_revision(conn, current, fields, now)
        new_question_id = _insert_question_revision(conn, current, fields, revision_id, now)
        cursor = conn.execute(
            """
            UPDATE questions
            SET status = 'superseded',
                superseded_at = ?
            WHERE id = ?
              AND status = 'active'
              AND superseded_at IS NULL
            """,
            (now, question_id),
        )
        if cursor.rowcount != 1:
            raise QuestionEditError("stale question edit; reopen the current version")

        reason = _optional_text(payload.get("reason"), "reason", max_chars=MAX_REASON_CHARS)
        edit_batch_id = conn.execute(
            """
            INSERT INTO question_edit_batches (
                original_question_id,
                new_question_id,
                changed_fields_json,
                reason,
                created_by,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                question_id,
                new_question_id,
                json.dumps(
                    {"schema_version": 1, "fields": changed_fields},
                    sort_keys=True,
                ),
                reason,
                actor_sub,
                now,
            ),
        ).lastrowid
        conn.execute(
            "UPDATE quiz_banks SET updated_at = ? WHERE id = ?",
            (now, current["quiz_bank_id"]),
        )
        impact = _impact_summary(conn, question_id)
        record_audit_event(
            "question.edited",
            actor_sub=actor_sub,
            object_type="question_edit_batch",
            object_id=edit_batch_id,
            details={
                "schema_version": 1,
                "details": {
                    "original_question_id": question_id,
                    "new_question_id": new_question_id,
                    "bank_id": current["quiz_bank_id"],
                    "source_revision_id": current["bank_revision_id"],
                    "manual_revision_id": revision_id,
                    "changed_fields": changed_fields,
                    "generated_quiz_snapshot_count": impact[
                        "generated_quiz_snapshot_count"
                    ],
                    "attempt_count": impact["attempt_count"],
                },
            },
            db=conn,
        )
        mark_question_filter_terms_stale(conn=conn)
        if owns_transaction:
            conn.commit()
    except Exception:
        if owns_transaction and conn.in_transaction:
            conn.rollback()
        raise

    queue_question_filter_terms_refresh()
    return {
        "schema_version": 1,
        "edit_batch_id": edit_batch_id,
        "original_question_id": question_id,
        "new_question_id": new_question_id,
        "manual_revision_id": revision_id,
        "changed_fields": changed_fields,
    }


def _editable_question(conn, question_id):
    row = conn.execute(
        """
        SELECT
            question.*,
            bank.lesson_id,
            bank.lesson_title AS bank_lesson_title,
            bank.topic AS bank_topic,
            bank.archived AS bank_archived,
            revision.lesson_title AS revision_lesson_title,
            revision.date_generated AS revision_date_generated,
            revision.topic AS revision_topic,
            revision.hierarchy_json AS revision_hierarchy_json,
            revision.source_hash AS revision_source_hash,
            revision.status AS revision_status
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE question.id = ?
          AND question.status = 'active'
          AND question.superseded_at IS NULL
          AND bank.archived = 0
          AND revision.status = 'active'
          AND NOT EXISTS (
              SELECT 1
              FROM question_retirements retirement
              WHERE retirement.question_id = question.id
          )
        """,
        (question_id,),
    ).fetchone()
    return dict(row) if row else None


def _normalize_edit_payload(current, payload):
    fields = {
        "question_stem": _required_text(payload.get("question_stem"), "question_stem"),
        "explanation": _optional_text(payload.get("explanation"), "explanation"),
        "difficulty_level": _difficulty_level(payload.get("difficulty_level")),
        "topic": _topic(payload.get("topic"), current["topic"]),
        "question_tags": _tags(payload.get("question_tags", [])),
        "options": (),
    }
    if current["question_type"] == "multiple_choice":
        fields["options"] = tuple(_multiple_choice_options(payload.get("options", [])))
    elif payload.get("options"):
        raise QuestionEditError("written questions cannot include answer options")
    return fields


def _required_text(value, field_name):
    value = _optional_text(value, field_name)
    if value is None:
        raise QuestionEditError(f"{field_name} is required")
    return value


def _optional_text(value, field_name, *, max_chars=None):
    if value is None:
        return None
    if not isinstance(value, str):
        raise QuestionEditError(f"{field_name} must be text")
    value = value.strip()
    if not value:
        return None
    limit = max_chars or current_app.config["INGEST_MAX_FIELD_CHARS"]
    if len(value) > limit:
        raise QuestionEditError(f"{field_name} exceeds configured field length limit")
    return value


def _difficulty_level(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise QuestionEditError("difficulty_level must be an integer from 1 to 5") from exc
    if not 1 <= parsed <= 5:
        raise QuestionEditError("difficulty_level must be an integer from 1 to 5")
    return parsed


def _topic(value, fallback):
    topic = str(value or fallback or "other").strip().lower()
    if topic not in VALID_TOPICS:
        raise QuestionEditError("topic is not canonical")
    return topic


def _tags(value):
    if isinstance(value, str):
        raw_values = value.replace(",", "\n").splitlines()
    elif isinstance(value, (list, tuple)):
        raw_values = value
    else:
        raise QuestionEditError("question_tags must be text or a list")
    tags = []
    seen = set()
    for raw_value in raw_values:
        tag = normalize_tag(raw_value)
        if not tag or tag in seen:
            continue
        tags.append(tag)
        seen.add(tag)
    if len(tags) > MAX_EDIT_TAGS:
        raise QuestionEditError(f"question_tags are limited to {MAX_EDIT_TAGS} tags")
    return tuple(tags)


def _multiple_choice_options(value):
    if not isinstance(value, list):
        raise QuestionEditError("options must be a list")
    options = []
    seen_text = set()
    correct_count = 0
    for index, option in enumerate(value):
        if not isinstance(option, dict):
            raise QuestionEditError("options must be objects")
        text = _required_text(option.get("option_text"), "option_text")
        key = text.casefold()
        if key in seen_text:
            raise QuestionEditError("option text must be unique")
        seen_text.add(key)
        is_correct = bool(option.get("is_correct"))
        if is_correct:
            correct_count += 1
        options.append(
            {
                "option_text": text,
                "is_correct": is_correct,
                "ingest_order": index,
            }
        )
    if len(options) < 2:
        raise QuestionEditError("multiple_choice requires at least two options")
    if correct_count != 1:
        raise QuestionEditError("multiple_choice requires exactly one correct option")
    return options


def _optional_int(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise QuestionEditError("expected_question_id must be an integer") from exc


def _changed_fields(current, fields):
    changes = []
    for field_name in (
        "question_stem",
        "explanation",
        "difficulty_level",
        "topic",
    ):
        if (current.get(field_name) or None) != fields[field_name]:
            changes.append(field_name)
    if tuple(current["question_tags"]) != tuple(fields["question_tags"]):
        changes.append("question_tags")
    current_options = tuple(
        {
            "option_text": option["option_text"],
            "is_correct": bool(option["is_correct"]),
            "ingest_order": index,
        }
        for index, option in enumerate(current["options"])
    )
    if current_options != tuple(fields["options"]):
        changes.append("options")
    return changes


def _insert_manual_revision(conn, current, fields, now):
    source_hash = _source_hash(
        {
            "schema_version": 1,
            "operation": "manual_question_edit",
            "original_question_id": current["id"],
            "question_stem": fields["question_stem"],
            "explanation": fields["explanation"],
            "difficulty_level": fields["difficulty_level"],
            "topic": fields["topic"],
            "question_tags": fields["question_tags"],
            "options": fields["options"],
        }
    )
    revision_id = conn.execute(
        """
        INSERT INTO quiz_bank_revisions (
            quiz_bank_id,
            import_batch_id,
            lesson_title,
            date_generated,
            topic,
            hierarchy_json,
            source_hash,
            status,
            created_at
        )
        VALUES (?, NULL, ?, ?, ?, ?, ?, 'active', ?)
        """,
        (
            current["quiz_bank_id"],
            current["revision_lesson_title"],
            current["revision_date_generated"],
            current["revision_topic"],
            current["revision_hierarchy_json"],
            source_hash,
            now,
        ),
    ).lastrowid
    conn.executemany(
        """
        INSERT INTO bank_revision_tags (bank_revision_id, tag)
        VALUES (?, ?)
        """,
        [(revision_id, tag) for tag in current["bank_tags"]],
    )
    return revision_id


def _insert_question_revision(conn, current, fields, revision_id, now):
    question_id = conn.execute(
        """
        INSERT INTO questions (
            quiz_bank_id,
            bank_revision_id,
            source_qid,
            question_type,
            question_stem,
            explanation,
            difficulty_level,
            topic,
            lesson_block,
            specific_source_lesson,
            specific_source_reading,
            content_section_id,
            content_lecture_id,
            status,
            revises_question_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """,
        (
            current["quiz_bank_id"],
            revision_id,
            current["source_qid"],
            current["question_type"],
            fields["question_stem"],
            fields["explanation"],
            fields["difficulty_level"],
            fields["topic"],
            current["lesson_block"],
            current["specific_source_lesson"],
            current["specific_source_reading"],
            current["content_section_id"],
            current["content_lecture_id"],
            current["id"],
            now,
        ),
    ).lastrowid
    conn.executemany(
        """
        INSERT INTO question_tags (question_id, tag)
        VALUES (?, ?)
        """,
        [(question_id, tag) for tag in fields["question_tags"]],
    )
    conn.executemany(
        """
        INSERT INTO question_options (
            question_id,
            option_text,
            is_correct,
            ingest_order
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                question_id,
                option["option_text"],
                1 if option["is_correct"] else 0,
                option["ingest_order"],
            )
            for option in fields["options"]
        ],
    )
    return question_id


def _source_hash(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _options(conn, question_id):
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT id, option_text, is_correct, ingest_order
            FROM question_options
            WHERE question_id = ?
            ORDER BY ingest_order
            """,
            (question_id,),
        ).fetchall()
    ]


def _question_tags(conn, question_id):
    return [
        row["tag"]
        for row in conn.execute(
            "SELECT tag FROM question_tags WHERE question_id = ? ORDER BY tag",
            (question_id,),
        ).fetchall()
    ]


def _bank_tags(conn, revision_id):
    return [
        row["tag"]
        for row in conn.execute(
            """
            SELECT tag
            FROM bank_revision_tags
            WHERE bank_revision_id = ?
            ORDER BY tag
            """,
            (revision_id,),
        ).fetchall()
    ]


def _impact_summary(conn, question_id):
    snapshot_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM quiz_version_questions
        WHERE source_question_id = ?
        """,
        (question_id,),
    ).fetchone()[0]
    attempt_count = conn.execute(
        """
        SELECT COUNT(DISTINCT attempt.id)
        FROM attempts attempt
        JOIN quiz_version_questions version_question
          ON version_question.quiz_version_id = attempt.quiz_version_id
        WHERE version_question.source_question_id = ?
        """,
        (question_id,),
    ).fetchone()[0]
    return {
        "generated_quiz_snapshot_count": snapshot_count,
        "attempt_count": attempt_count,
        "active_template_references": _active_template_references(conn, question_id),
    }


def _active_template_references(conn, question_id):
    references = []
    for template in list_templates(include_archived=False, conn=conn):
        sql, params = build_eligible_pool_query(template["criteria"])
        wrapped_sql = f"SELECT 1 FROM ({sql}) eligible WHERE eligible.id = ? LIMIT 1"
        if conn.execute(wrapped_sql, [*params, question_id]).fetchone():
            references.append(
                {
                    "id": template["id"],
                    "title": template["title"],
                    "question_count": template["question_count"],
                }
            )
    return references


def _revision_chain(conn, question_id):
    ancestors = []
    current_id = question_id
    while True:
        row = conn.execute(
            """
            SELECT id, revises_question_id, status, superseded_at, created_at
            FROM questions
            WHERE id = ?
            """,
            (current_id,),
        ).fetchone()
        if row is None or row["revises_question_id"] is None:
            break
        prior = conn.execute(
            """
            SELECT id, source_qid, status, superseded_at, created_at
            FROM questions
            WHERE id = ?
            """,
            (row["revises_question_id"],),
        ).fetchone()
        if prior is None:
            break
        ancestors.append(dict(prior))
        current_id = prior["id"]
    ancestors.reverse()
    return {
        "previous_versions": ancestors,
        "current_question_id": question_id,
    }
