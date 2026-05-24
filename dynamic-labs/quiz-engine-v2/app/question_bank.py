import re
from dataclasses import dataclass

from .db import get_db
from .enums import enum_values
from .ingest import effective_tags


MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


class QuestionBankFilterError(ValueError):
    pass


@dataclass(frozen=True)
class QuestionFilters:
    lesson_id: str | None = None
    lesson_title: str | None = None
    topic: str | None = None
    tag: str | None = None
    hierarchy_section: str | None = None
    hierarchy_lecture: str | None = None
    difficulty_level: int | None = None
    question_type: str | None = None
    source: str | None = None
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


def parse_question_filters(args):
    difficulty = _optional_int(args.get("difficulty_level") or args.get("difficulty"))
    if difficulty is not None and not 1 <= difficulty <= 5:
        raise QuestionBankFilterError("difficulty_level must be between 1 and 5")

    question_type = _optional_text(args.get("question_type"))
    if question_type and question_type not in enum_values("question_type"):
        raise QuestionBankFilterError("question_type is not canonical")

    return QuestionFilters(
        lesson_id=_optional_text(args.get("lesson_id")),
        lesson_title=_optional_text(args.get("lesson_title")),
        topic=_optional_text(args.get("topic")),
        tag=_normalize_filter_tag(args.get("tag"))
        if _optional_text(args.get("tag"))
        else None,
        hierarchy_section=_optional_text(
            args.get("hierarchy_section") or args.get("section")
        ),
        hierarchy_lecture=_optional_text(
            args.get("hierarchy_lecture") or args.get("lecture")
        ),
        difficulty_level=difficulty,
        question_type=question_type,
        source=_optional_text(args.get("source")),
        limit=_bounded_limit(args.get("limit")),
        offset=_non_negative_int(args.get("offset")),
    )


def _optional_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _normalize_filter_tag(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-") or None


def _optional_int(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise QuestionBankFilterError("difficulty_level must be an integer") from exc


def _bounded_limit(value):
    if value is None or str(value).strip() == "":
        return DEFAULT_PAGE_SIZE
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise QuestionBankFilterError("limit must be an integer") from exc
    if parsed <= 0:
        raise QuestionBankFilterError("limit must be positive")
    return min(parsed, MAX_PAGE_SIZE)


def _non_negative_int(value):
    if value is None or str(value).strip() == "":
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise QuestionBankFilterError("offset must be an integer") from exc
    if parsed < 0:
        raise QuestionBankFilterError("offset must be non-negative")
    return parsed


def build_question_query(filters, *, count=False):
    select = (
        "COUNT(DISTINCT question.id) AS count"
        if count
        else """
        question.id,
        question.source_qid,
        question.question_type,
        question.question_stem,
        question.explanation,
        question.difficulty_level,
        question.topic,
        question.lesson_block,
        question.specific_source_lesson,
        question.specific_source_reading,
        question.content_section_id,
        question.content_lecture_id,
        question.status,
        question.revises_question_id,
        question.superseded_at,
        question.created_at,
        bank.id AS bank_id,
        bank.lesson_id,
        bank.lesson_title,
        revision.id AS bank_revision_id,
        revision.source_hash
        """
    )
    sql = f"""
        SELECT {select}
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        """
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

    if filters.lesson_id:
        conditions.append("bank.lesson_id = ?")
        params.append(filters.lesson_id)
    if filters.lesson_title:
        conditions.append("bank.lesson_title LIKE ?")
        params.append(f"%{filters.lesson_title}%")
    if filters.topic:
        conditions.append("question.topic = ?")
        params.append(filters.topic)
    if filters.tag:
        conditions.append(
            """
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
        )
        params.extend([filters.tag, filters.tag])
    if filters.hierarchy_section:
        conditions.append("question.content_section_id = ?")
        params.append(filters.hierarchy_section)
    if filters.hierarchy_lecture:
        conditions.append("question.content_lecture_id = ?")
        params.append(filters.hierarchy_lecture)
    if filters.difficulty_level is not None:
        conditions.append("question.difficulty_level = ?")
        params.append(filters.difficulty_level)
    if filters.question_type:
        conditions.append("question.question_type = ?")
        params.append(filters.question_type)
    if filters.source:
        conditions.append(
            """
            (
                question.specific_source_lesson LIKE ?
                OR question.specific_source_reading LIKE ?
            )
            """
        )
        source = f"%{filters.source}%"
        params.extend([source, source])

    sql += " WHERE " + " AND ".join(conditions)
    if not count:
        sql += " ORDER BY bank.lesson_id, question.id LIMIT ? OFFSET ?"
        params.extend([filters.limit, filters.offset])
    return sql, params


def list_banks(*, conn=None):
    conn = conn or get_db()
    rows = conn.execute(
        """
        SELECT
            bank.id,
            bank.lesson_id,
            bank.lesson_title,
            bank.topic,
            bank.hidden,
            bank.archived,
            bank.latest_revision_id,
            COUNT(question.id) AS question_count,
            SUM(CASE WHEN question.status = 'superseded' THEN 1 ELSE 0 END)
                AS superseded_question_count
        FROM quiz_banks bank
        LEFT JOIN questions question
          ON question.quiz_bank_id = bank.id
         AND question.status = 'active'
         AND question.superseded_at IS NULL
         AND EXISTS (
             SELECT 1
             FROM quiz_bank_revisions revision
             WHERE revision.id = question.bank_revision_id
               AND revision.status = 'active'
         )
         AND NOT EXISTS (
             SELECT 1
             FROM question_retirements retirement
             WHERE retirement.question_id = question.id
         )
        WHERE bank.archived = 0
        GROUP BY bank.id
        ORDER BY bank.lesson_id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def search_questions(filters, *, conn=None):
    conn = conn or get_db()
    sql, params = build_question_query(filters)
    count_sql, count_params = build_question_query(filters, count=True)
    rows = [dict(row) for row in conn.execute(sql, params).fetchall()]
    total = conn.execute(count_sql, count_params).fetchone()["count"]
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
    return {"questions": rows, "total": total}


def get_question_detail(question_id, *, conn=None):
    conn = conn or get_db()
    row = conn.execute(
        """
        SELECT
            question.id,
            question.source_qid,
            question.question_type,
            question.question_stem,
            question.explanation,
            question.difficulty_level,
            question.topic,
            question.lesson_block,
            question.specific_source_lesson,
            question.specific_source_reading,
            question.content_section_id,
            question.content_lecture_id,
            question.status,
            question.revises_question_id,
            question.superseded_at,
            question.created_at,
            bank.id AS bank_id,
            bank.lesson_id,
            bank.lesson_title,
            revision.id AS bank_revision_id,
            revision.source_hash
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
    if row is None:
        return None

    detail = dict(row)
    detail["options"] = [
        dict(option)
        for option in conn.execute(
            """
            SELECT id, option_text, is_correct, ingest_order
            FROM question_options
            WHERE question_id = ?
            ORDER BY ingest_order
            """,
            (question_id,),
        ).fetchall()
    ]
    detail["question_tags"] = _tags_by_question(conn, [question_id]).get(question_id, [])
    detail["bank_tags"] = _bank_tags_by_revision(
        conn,
        [detail["bank_revision_id"]],
    ).get(detail["bank_revision_id"], [])
    detail["effective_tags"] = list(
        effective_tags(detail["bank_tags"], detail["question_tags"])
    )
    return detail


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
