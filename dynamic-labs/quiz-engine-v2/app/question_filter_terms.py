import hashlib
import json
import threading

from flask import current_app

from .audit import utc_now_iso
from .db import get_db
from .enums import enum_values
from .ingest import normalize_tag


CACHE_KEY = "question_filter_terms_cache"
STALE_KEY = "question_filter_terms_stale"
SCHEMA_VERSION = 2
TERM_FIELDS = (
    "lesson_id",
    "lesson_title",
    "topic",
    "tag",
    "hierarchy_section",
    "hierarchy_lecture",
    "difficulty_level",
    "question_type",
)
MAX_LABEL_LENGTH = 160


def mark_question_filter_terms_stale(*, conn=None):
    conn = conn or get_db()
    _write_settings(conn, ((STALE_KEY, "1"),))


def queue_question_filter_terms_refresh(app=None):
    app = app or current_app._get_current_object()
    if app.config.get("TESTING"):
        with app.app_context():
            refresh_question_filter_terms()
        return {"queued": False}

    thread = threading.Thread(
        target=_refresh_in_background,
        args=(app,),
        name="question-filter-terms-refresh",
        daemon=True,
    )
    thread.start()
    return {"queued": True}


def get_question_filter_terms(*, conn=None):
    conn = conn or get_db()
    cached = _get_setting(conn, CACHE_KEY)
    stale = _get_setting(conn, STALE_KEY)
    if cached is None or stale == "1":
        return refresh_question_filter_terms(conn=conn)
    try:
        payload = json.loads(cached)
    except json.JSONDecodeError:
        return refresh_question_filter_terms(conn=conn)
    if payload.get("schema_version") != SCHEMA_VERSION:
        return refresh_question_filter_terms(conn=conn)
    return payload


def refresh_question_filter_terms(*, conn=None):
    conn = conn or get_db()
    payload = build_question_filter_terms(conn=conn)
    _write_settings(
        conn,
        (
            (CACHE_KEY, json.dumps(payload, sort_keys=True, separators=(",", ":"))),
            (STALE_KEY, "0"),
        ),
    )
    return payload


def build_question_filter_terms(*, conn=None):
    conn = conn or get_db()
    buckets = {field: {} for field in TERM_FIELDS}
    bank_buckets = {}
    question_rows = _question_metadata_rows(conn)

    for row in question_rows:
        bank_bucket = _bank_bucket(bank_buckets, row)
        _add_term(buckets, "lesson_id", row["lesson_id"])
        _add_term(buckets, "lesson_title", row["lesson_title"])
        _add_term(buckets, "topic", row["topic"])
        _add_term(buckets, "hierarchy_section", row["content_section_id"])
        _add_term(buckets, "hierarchy_lecture", row["content_lecture_id"])
        _add_term(buckets, "difficulty_level", row["difficulty_level"])
        _add_term(buckets, "question_type", row["question_type"])
        _add_term(bank_bucket["buckets"], "lesson_id", row["lesson_id"])
        _add_term(bank_bucket["buckets"], "lesson_title", row["lesson_title"])
        _add_term(bank_bucket["buckets"], "topic", row["topic"])
        _add_term(
            bank_bucket["buckets"],
            "hierarchy_section",
            row["content_section_id"],
        )
        _add_term(
            bank_bucket["buckets"],
            "hierarchy_lecture",
            row["content_lecture_id"],
        )
        _add_term(bank_bucket["buckets"], "difficulty_level", row["difficulty_level"])
        _add_term(bank_bucket["buckets"], "question_type", row["question_type"])

    for field, values in _canonical_values().items():
        for value in values:
            if str(value) in buckets[field]:
                continue
            _add_term(buckets, field, value, count=0)

    seen_question_tags = set()
    seen_bank_question_tags = set()
    for row in _tag_rows(conn):
        key = (row["question_id"], row["tag"])
        if key in seen_question_tags:
            pass
        else:
            seen_question_tags.add(key)
            _add_term(buckets, "tag", row["tag"])
        bank_key = (row["lesson_id"], row["question_id"], row["tag"])
        if bank_key in seen_bank_question_tags:
            continue
        seen_bank_question_tags.add(bank_key)
        bank_bucket = _bank_bucket(bank_buckets, row)
        _add_term(bank_bucket["buckets"], "tag", row["tag"])

    fields = {
        field: _sorted_terms(buckets[field])
        for field in TERM_FIELDS
    }
    banks = {
        lesson_id: {
            "quiz_bank_id": bank["quiz_bank_id"],
            "lesson_id": lesson_id,
            "lesson_title": bank["lesson_title"],
            "fields": {
                field: _sorted_terms(bank["buckets"][field])
                for field in TERM_FIELDS
            },
        }
        for lesson_id, bank in sorted(bank_buckets.items())
    }
    revision = _revision({"fields": fields, "banks": banks})
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "revision": revision,
        "fields": fields,
        "banks": banks,
    }


def _refresh_in_background(app):
    try:
        with app.app_context():
            refresh_question_filter_terms()
    except Exception:
        app.logger.exception("Failed to refresh question filter autocomplete terms")


def _question_metadata_rows(conn):
    return conn.execute(
        """
        SELECT
            question.id,
            question.quiz_bank_id,
            question.topic,
            question.content_section_id,
            question.content_lecture_id,
            question.difficulty_level,
            question.question_type,
            bank.lesson_id,
            bank.lesson_title
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE bank.archived = 0
          AND revision.status = 'active'
          AND question.status = 'active'
          AND question.superseded_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM question_retirements retirement
              WHERE retirement.question_id = question.id
          )
        """
    ).fetchall()


def _tag_rows(conn):
    return conn.execute(
        """
        SELECT
            question.id AS question_id,
            question.quiz_bank_id,
            bank.lesson_id,
            bank.lesson_title,
            question_tag.tag
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN question_tags question_tag
          ON question_tag.question_id = question.id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE bank.archived = 0
          AND revision.status = 'active'
          AND question.status = 'active'
          AND question.superseded_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM question_retirements retirement
              WHERE retirement.question_id = question.id
          )
        UNION
        SELECT
            question.id AS question_id,
            question.quiz_bank_id,
            bank.lesson_id,
            bank.lesson_title,
            bank_tag.tag
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        JOIN bank_revision_tags bank_tag
          ON bank_tag.bank_revision_id = revision.id
        WHERE bank.archived = 0
          AND revision.status = 'active'
          AND question.status = 'active'
          AND question.superseded_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM question_retirements retirement
              WHERE retirement.question_id = question.id
          )
        """
    ).fetchall()


def _canonical_values():
    return {
        "difficulty_level": [str(level) for level in range(1, 6)],
        "question_type": list(enum_values("question_type")),
    }


def _bank_bucket(bank_buckets, row):
    lesson_id = str(row["lesson_id"])
    return bank_buckets.setdefault(
        lesson_id,
        {
            "quiz_bank_id": row["quiz_bank_id"],
            "lesson_title": row["lesson_title"],
            "buckets": {field: {} for field in TERM_FIELDS},
        },
    )


def _add_term(buckets, field, value, *, count=1):
    if value is None:
        return
    value = str(value).strip()
    if not value:
        return
    if field == "tag":
        value = normalize_tag(value)
        if not value:
            return
    label = value[:MAX_LABEL_LENGTH]
    term = buckets[field].setdefault(
        value,
        {"value": value, "label": label, "count": 0},
    )
    term["count"] += int(count)


def _sorted_terms(bucket):
    terms = list(bucket.values())
    terms.sort(key=lambda term: (-term["count"], term["label"].lower(), term["value"]))
    return terms


def _revision(fields):
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get_setting(conn, key):
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return None if row is None else row["value"]


def _write_settings(conn, entries):
    if conn.in_transaction:
        for key, value in entries:
            _set_setting(conn, key, value)
        return

    with conn:
        for key, value in entries:
            _set_setting(conn, key, value)


def _set_setting(conn, key, value):
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO app_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (key, value, now),
    )
