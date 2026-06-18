from datetime import datetime, timezone

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .enums import enum_values
from .quiz_versions import (
    QuizVersionError,
    get_quiz_version,
    validate_admin_metadata_update,
)


class PublicationError(ValueError):
    pass


ADMIN_METADATA_FIELDS = {
    "title",
    "description",
    "available_from",
    "available_until",
    "instructor_notes",
}


def update_quiz_version_metadata(version_id, payload, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    if not isinstance(payload, dict):
        raise PublicationError("metadata payload must be an object")
    try:
        validate_admin_metadata_update(payload)
    except QuizVersionError as exc:
        raise PublicationError(str(exc)) from exc

    unknown = sorted(set(payload) - ADMIN_METADATA_FIELDS)
    if unknown:
        raise PublicationError("unsupported metadata fields: " + ", ".join(unknown))

    existing = get_quiz_version(int(version_id), conn=conn)
    if existing is None:
        raise PublicationError("quiz version not found")

    fields = {}
    for field_name in ADMIN_METADATA_FIELDS:
        if field_name in payload:
            if field_name == "title":
                fields[field_name] = _required_text(payload[field_name], "title")
            elif field_name in {"available_from", "available_until"}:
                fields[field_name] = normalize_optional_timestamp(
                    payload[field_name],
                    field_name,
                )
            else:
                fields[field_name] = _optional_text(payload[field_name], field_name)

    available_from = fields.get("available_from", existing.get("available_from"))
    available_until = fields.get("available_until", existing.get("available_until"))
    validate_availability_window(available_from, available_until)

    if not fields:
        return existing

    assignments = ", ".join(f"{field_name} = ?" for field_name in sorted(fields))
    values = [fields[field_name] for field_name in sorted(fields)]
    values.append(int(version_id))
    with conn:
        conn.execute(
            f"UPDATE quiz_versions SET {assignments} WHERE id = ?",
            values,
        )
        record_audit_event(
            "quiz_version.metadata_updated",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "fields": sorted(fields),
                },
            },
            db=conn,
        )
    return get_quiz_version(int(version_id), conn=conn)


def set_quiz_version_visibility(version_id, visibility, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    visibility = str(visibility or "").strip()
    if visibility not in enum_values("quiz_visibility"):
        raise PublicationError("visibility is not canonical")

    existing = get_quiz_version(int(version_id), conn=conn)
    if existing is None:
        raise PublicationError("quiz version not found")

    now = utc_now_iso()
    published_at = existing.get("published_at")
    archived_at = existing.get("archived_at")
    if visibility == "published":
        published_at = now
        archived_at = None
    elif visibility == "hidden":
        archived_at = None
    elif visibility == "archived":
        archived_at = now

    with conn:
        conn.execute(
            """
            UPDATE quiz_versions
            SET visibility = ?, published_at = ?, archived_at = ?
            WHERE id = ?
            """,
            (visibility, published_at, archived_at, int(version_id)),
        )
        record_audit_event(
            f"quiz_version.{visibility}",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "previous_visibility": existing["visibility"],
                    "visibility": visibility,
                },
            },
            db=conn,
        )
    return get_quiz_version(int(version_id), conn=conn)


def preview_quiz_version(version_id, *, conn=None):
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise PublicationError("quiz version not found")
    return version


def list_student_visible_quizzes(*, now=None, conn=None):
    conn = conn or get_db()
    now_iso = normalize_optional_timestamp(now, "now") if now is not None else utc_now_iso()
    rows = conn.execute(
        """
        SELECT
            version.id,
            version.title,
            version.description,
            version.available_from,
            version.available_until,
            version.timer_minutes,
            version.attempt_limit,
            version.result_policy,
            COUNT(question.id) AS question_count
        FROM quiz_versions version
        LEFT JOIN quiz_version_questions question
          ON question.quiz_version_id = version.id
        WHERE version.visibility = 'published'
          AND (version.available_from IS NULL OR version.available_from <= ?)
          AND (version.available_until IS NULL OR version.available_until >= ?)
        GROUP BY version.id
        ORDER BY version.available_from IS NULL, version.available_from, version.created_at, version.id
        """,
        (now_iso, now_iso),
    ).fetchall()
    return [dict(row) for row in rows]


def list_student_quiz_listings(*, now=None, conn=None):
    conn = conn or get_db()
    now_iso = normalize_optional_timestamp(now, "now") if now is not None else utc_now_iso()
    rows = conn.execute(
        """
        SELECT
            version.id,
            version.title,
            version.description,
            version.available_from,
            version.available_until,
            version.timer_minutes,
            version.attempt_limit,
            version.result_policy,
            COUNT(question.id) AS question_count
        FROM quiz_versions version
        LEFT JOIN quiz_version_questions question
          ON question.quiz_version_id = version.id
        WHERE version.visibility = 'published'
          AND (version.available_until IS NULL OR version.available_until >= ?)
        GROUP BY version.id
        ORDER BY
          CASE
            WHEN version.available_from IS NOT NULL AND version.available_from > ? THEN 1
            ELSE 0
          END,
          version.created_at DESC,
          version.id DESC
        """,
        (now_iso, now_iso),
    ).fetchall()
    quizzes = []
    for row in rows:
        quiz = dict(row)
        available_from = quiz.get("available_from")
        quiz["availability_status"] = (
            "scheduled" if available_from and available_from > now_iso else "available"
        )
        quizzes.append(quiz)
    return quizzes


def is_quiz_available_to_start(version, *, now=None):
    if version is None or version.get("visibility") != "published":
        return False
    now_iso = normalize_optional_timestamp(now, "now") if now is not None else utc_now_iso()
    available_from = version.get("available_from")
    available_until = version.get("available_until")
    if available_from and available_from > now_iso:
        return False
    if available_until and available_until < now_iso:
        return False
    return True


def validate_availability_window(available_from, available_until):
    if available_from and available_until and available_from >= available_until:
        raise PublicationError("available_until must be after available_from")


def normalize_optional_timestamp(value, field_name):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        parse_value = value[:-1] + "+00:00" if value.endswith("Z") else value
    elif isinstance(value, datetime):
        parsed = value
        return _to_utc_iso(parsed)
    else:
        raise PublicationError(f"{field_name} must be an ISO timestamp")

    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as exc:
        raise PublicationError(f"{field_name} must be an ISO timestamp") from exc
    return _to_utc_iso(parsed)


def _to_utc_iso(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _required_text(value, field_name):
    value = _optional_text(value, field_name)
    if value is None:
        raise PublicationError(f"{field_name} is required")
    return value


def _optional_text(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise PublicationError(f"{field_name} must be text")
    value = value.strip()
    return value or None
