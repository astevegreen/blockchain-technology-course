import json
import hashlib
import random
from datetime import datetime, timedelta, timezone

from flask import current_app

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .json_validation import validate_versioned_json
from .publication import is_quiz_available_to_start
from .quiz_versions import get_quiz_version
from .students import get_student_by_identifier


class AttemptError(ValueError):
    pass


class AttemptIncompleteError(AttemptError):
    def __init__(self, missing_question_ids):
        self.missing_question_ids = [
            int(question_id)
            for question_id in missing_question_ids
        ]
        super().__init__("answer all questions before submitting")


def start_or_resume_attempt(quiz_version_id, student, *, conn=None):
    conn = conn or get_db()
    quiz_version_id = int(quiz_version_id)
    try:
        conn.execute("BEGIN IMMEDIATE")
        version = get_quiz_version(quiz_version_id, conn=conn)
        if version is None:
            raise AttemptError("quiz not found")

        now = utc_now_iso()
        existing = _active_attempt_row(conn, quiz_version_id, student.id)
        if existing is not None:
            if _finalize_expired_attempt_if_due(conn, existing, now=now):
                existing = None

        if existing is not None:
            if version["visibility"] != "published":
                raise AttemptError("quiz is not available")
            conn.commit()
            return get_student_attempt(existing["id"], student, conn=conn)

        if not is_quiz_available_to_start(version):
            raise AttemptError("quiz is not available")

        _ensure_attempt_allowed(conn, version, student.id)
        attempt_number = _next_attempt_number(conn, quiz_version_id, student.id)
        deadline_at = _deadline_at(now, version["timer_minutes"])
        empty_order_json = json.dumps({"schema_version": 1, "order": []})
        attempt_id = conn.execute(
            """
            INSERT INTO attempts (
                quiz_version_id,
                student_id,
                attempt_number,
                status,
                started_at,
                deadline_at,
                question_order_json,
                option_order_json
            )
            VALUES (?, ?, ?, 'in_progress', ?, ?, ?, ?)
            """,
            (
                quiz_version_id,
                student.id,
                attempt_number,
                now,
                deadline_at,
                empty_order_json,
                empty_order_json,
            ),
        ).lastrowid

        question_order = _question_order(version, attempt_id)
        option_order = _option_order(version, attempt_id, question_order)
        question_order_json = validate_versioned_json(
            "question_order_json",
            {"schema_version": 1, "order": question_order},
        )
        option_order_json = validate_versioned_json(
            "option_order_json",
            {"schema_version": 1, "order": option_order},
        )
        conn.execute(
            """
            UPDATE attempts
            SET question_order_json = ?, option_order_json = ?
            WHERE id = ?
            """,
            (
                json.dumps(question_order_json, sort_keys=True),
                json.dumps(option_order_json, sort_keys=True),
                attempt_id,
            ),
        )
        record_audit_event(
            "attempt.started",
            object_type="attempt",
            object_id=attempt_id,
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": quiz_version_id,
                    "student_id": student.id,
                    "attempt_number": attempt_number,
                },
            },
            db=conn,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return get_student_attempt(attempt_id, student, conn=conn)


def get_student_attempt(attempt_id, student, *, conn=None):
    conn = conn or get_db()
    row = _attempt_row(conn, int(attempt_id), student.id)
    if row is None:
        raise AttemptError("attempt not found")
    if row["status"] == "in_progress" and _deadline_has_passed(row["deadline_at"]):
        finalize_expired_attempt(row["id"], conn=conn)
        row = _attempt_row(conn, int(attempt_id), student.id)
    return _attempt_payload(conn, row, include_answers=True)


def save_answer(attempt_id, student, payload, *, conn=None):
    conn = conn or get_db()
    if not isinstance(payload, dict):
        raise AttemptError("answer payload must be an object")
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = _attempt_row(conn, int(attempt_id), student.id)
        if row is None:
            raise AttemptError("attempt not found")
        if _finalize_expired_attempt_if_due(conn, row):
            conn.commit()
            raise AttemptError("attempt is final")
        if row["status"] != "in_progress":
            raise AttemptError("attempt is final")
        answer = _normalize_answer_payload(payload)
        _upsert_answer(conn, row, answer)
        record_audit_event(
            "attempt.answer_saved",
            object_type="attempt",
            object_id=row["id"],
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": row["quiz_version_id"],
                    "question_id": answer["question_id"],
                },
            },
            db=conn,
        )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    return get_student_attempt(attempt_id, student, conn=conn)


def submit_attempt(attempt_id, student, *, answers=None, conn=None):
    conn = conn or get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = _attempt_row(conn, int(attempt_id), student.id)
        if row is None:
            raise AttemptError("attempt not found")
        if row["status"] != "in_progress":
            conn.commit()
            return _attempt_payload(conn, row, include_answers=True)
        if _finalize_expired_attempt_if_due(conn, row):
            conn.commit()
            return get_student_attempt(attempt_id, student, conn=conn)

        normalized_answers = _normalize_answers_payload(answers)
        missing_question_ids = _missing_required_answer_question_ids(
            conn,
            row,
            normalized_answers,
        )
        if missing_question_ids:
            raise AttemptIncompleteError(missing_question_ids)

        for answer in normalized_answers:
            _upsert_answer(conn, row, answer)

        now = utc_now_iso()
        status, score, max_score = _finalize_answers(
            conn,
            row,
            finalized_at=now,
            finalization_reason="submitted",
        )
        conn.execute(
            """
            UPDATE attempts
            SET status = ?,
                submitted_at = ?,
                graded_at = CASE WHEN ? = 'graded' THEN ? ELSE graded_at END,
                score = ?,
                max_score = ?
            WHERE id = ? AND status = 'in_progress'
            """,
            (status, now, status, now, score, max_score, row["id"]),
        )
        record_audit_event(
            "attempt.submitted",
            object_type="attempt",
            object_id=row["id"],
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": row["quiz_version_id"],
                    "student_id": student.id,
                    "status": status,
                },
            },
            db=conn,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return get_student_attempt(attempt_id, student, conn=conn)


def effective_attempt_allowance(quiz_version_id, student_id, *, conn=None):
    conn = conn or get_db()
    version = get_quiz_version(int(quiz_version_id), conn=conn)
    if version is None:
        raise AttemptError("quiz not found")
    row = conn.execute(
        """
        SELECT COALESCE(SUM(extra_attempts), 0) AS extra_attempts
        FROM attempt_grants
        WHERE quiz_version_id = ? AND student_id = ?
        """,
        (int(quiz_version_id), int(student_id)),
    ).fetchone()
    extra_attempts = int(row["extra_attempts"] or 0)
    base_limit = int(version["attempt_limit"])
    return {
        "quiz_version_id": int(quiz_version_id),
        "student_id": int(student_id),
        "base_limit": base_limit,
        "extra_attempts": extra_attempts,
        "allowance": base_limit + extra_attempts,
    }


def attempt_usage(quiz_version_id, student_id, *, conn=None):
    conn = conn or get_db()
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_attempts,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS active_attempts,
            SUM(CASE WHEN status = 'voided' THEN 1 ELSE 0 END) AS voided_attempts,
            SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) AS expired_attempts
        FROM attempts
        WHERE quiz_version_id = ? AND student_id = ?
        """,
        (int(quiz_version_id), int(student_id)),
    ).fetchone()
    return {
        "quiz_version_id": int(quiz_version_id),
        "student_id": int(student_id),
        "total_attempts": int(row["total_attempts"] or 0),
        "active_attempts": int(row["active_attempts"] or 0),
        "voided_attempts": int(row["voided_attempts"] or 0),
        "expired_attempts": int(row["expired_attempts"] or 0),
    }


def grant_extra_attempt(
    quiz_version_id,
    identifier,
    *,
    extra_attempts=1,
    reason=None,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    quiz_version_id = int(quiz_version_id)
    extra_attempts = int(extra_attempts)
    if extra_attempts <= 0:
        raise AttemptError("extra_attempts must be positive")
    reason = _optional_limited_text(reason, "reason")
    try:
        conn.execute("BEGIN IMMEDIATE")
        version = get_quiz_version(quiz_version_id, conn=conn)
        if version is None:
            raise AttemptError("quiz not found")
        student = get_student_by_identifier(identifier, conn=conn)
        if student is None:
            raise AttemptError("student not found")
        now = utc_now_iso()
        grant_id = conn.execute(
            """
            INSERT INTO attempt_grants (
                quiz_version_id,
                student_id,
                extra_attempts,
                reason,
                created_by,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                quiz_version_id,
                student.id,
                extra_attempts,
                reason,
                actor_sub,
                now,
            ),
        ).lastrowid
        record_audit_event(
            "attempt.grant_created",
            actor_sub=actor_sub,
            object_type="attempt_grant",
            object_id=grant_id,
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": quiz_version_id,
                    "student_id": student.id,
                    "extra_attempts": extra_attempts,
                },
            },
            db=conn,
        )
        allowance = effective_attempt_allowance(
            quiz_version_id,
            student.id,
            conn=conn,
        )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    return {
        "id": grant_id,
        "quiz_version_id": quiz_version_id,
        "student_id": student.id,
        "extra_attempts": extra_attempts,
        "reason": reason,
        "created_by": actor_sub,
        "created_at": now,
        "allowance": allowance,
    }


def void_attempt(attempt_id, *, reason=None, actor_sub=None, conn=None):
    conn = conn or get_db()
    reason = _optional_limited_text(reason, "reason")
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT attempts.*, students.identifier
            FROM attempts
            JOIN students ON students.id = attempts.student_id
            WHERE attempts.id = ?
            """,
            (int(attempt_id),),
        ).fetchone()
        if row is None:
            raise AttemptError("attempt not found")
        if row["status"] != "voided":
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE attempts
                SET status = 'voided',
                    voided_at = ?
                WHERE id = ? AND status <> 'voided'
                """,
                (now, row["id"]),
            )
            record_audit_event(
                "attempt.voided",
                actor_sub=actor_sub,
                object_type="attempt",
                object_id=row["id"],
                details={
                    "schema_version": 1,
                    "details": {
                        "quiz_version_id": row["quiz_version_id"],
                        "student_id": row["student_id"],
                        "previous_status": row["status"],
                        "has_reason": reason is not None,
                    },
                },
                db=conn,
            )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    return get_attempt_summary(attempt_id, conn=conn)


def get_attempt_summary(attempt_id, *, conn=None):
    conn = conn or get_db()
    row = conn.execute(
        """
        SELECT
            attempts.*,
            students.identifier,
            versions.title AS quiz_title
        FROM attempts
        JOIN students ON students.id = attempts.student_id
        JOIN quiz_versions versions ON versions.id = attempts.quiz_version_id
        WHERE attempts.id = ?
        """,
        (int(attempt_id),),
    ).fetchone()
    if row is None:
        raise AttemptError("attempt not found")
    return _attempt_summary_payload(row)


def list_quiz_version_attempts(quiz_version_id, *, conn=None):
    conn = conn or get_db()
    rows = conn.execute(
        """
        SELECT
            attempts.*,
            students.identifier,
            versions.title AS quiz_title,
            COUNT(answers.id) AS answer_count
        FROM attempts
        JOIN students ON students.id = attempts.student_id
        JOIN quiz_versions versions ON versions.id = attempts.quiz_version_id
        LEFT JOIN attempt_answers answers ON answers.attempt_id = attempts.id
        WHERE attempts.quiz_version_id = ?
        GROUP BY attempts.id
        ORDER BY students.identifier, attempts.attempt_number
        """,
        (int(quiz_version_id),),
    ).fetchall()
    return [_attempt_summary_payload(row) for row in rows]


def finalize_expired_attempt(attempt_id, *, now=None, conn=None):
    conn = conn or get_db()
    owns_transaction = not conn.in_transaction
    now = _coerce_now_iso(now)
    try:
        if owns_transaction:
            conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT *
            FROM attempts
            WHERE id = ?
            """,
            (int(attempt_id),),
        ).fetchone()
        expired = False
        if row is not None and row["status"] == "in_progress":
            expired = _finalize_expired_attempt_if_due(conn, row, now=now)
        if owns_transaction:
            conn.commit()
    except Exception:
        if owns_transaction and conn.in_transaction:
            conn.rollback()
        raise
    return expired


def finalize_expired_attempts(*, now=None, limit=None, conn=None):
    conn = conn or get_db()
    now = _coerce_now_iso(now)
    limit = int(limit or _expiration_worker_batch_size())
    cutoff = _expiration_cutoff_iso(now)
    rows = conn.execute(
        """
        SELECT id
        FROM attempts
        WHERE status = 'in_progress'
          AND deadline_at IS NOT NULL
          AND deadline_at <= ?
        ORDER BY deadline_at ASC, id ASC
        LIMIT ?
        """,
        (cutoff, limit),
    ).fetchall()

    expired_ids = []
    for row in rows:
        if finalize_expired_attempt(row["id"], now=now, conn=conn):
            expired_ids.append(row["id"])
    return {
        "scanned": len(rows),
        "expired": len(expired_ids),
        "attempt_ids": expired_ids,
    }


def _active_attempt_row(conn, quiz_version_id, student_id):
    return conn.execute(
        """
        SELECT *
        FROM attempts
        WHERE quiz_version_id = ?
          AND student_id = ?
          AND status = 'in_progress'
        ORDER BY attempt_number DESC
        LIMIT 1
        """,
        (quiz_version_id, student_id),
    ).fetchone()


def _ensure_attempt_allowed(conn, version, student_id):
    allowance = effective_attempt_allowance(version["id"], student_id, conn=conn)
    usage = attempt_usage(version["id"], student_id, conn=conn)
    if usage["total_attempts"] >= allowance["allowance"]:
        raise AttemptError("attempt limit reached")


def _attempt_row(conn, attempt_id, student_id):
    return conn.execute(
        """
        SELECT *
        FROM attempts
        WHERE id = ? AND student_id = ?
        """,
        (attempt_id, student_id),
    ).fetchone()


def _next_attempt_number(conn, quiz_version_id, student_id):
    row = conn.execute(
        """
        SELECT COALESCE(MAX(attempt_number), 0) + 1
        FROM attempts
        WHERE quiz_version_id = ? AND student_id = ?
        """,
        (quiz_version_id, student_id),
    ).fetchone()
    return int(row[0])


def _optional_limited_text(value, field_name, *, limit=1000):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    if len(value) > limit:
        raise AttemptError(f"{field_name} is too long")
    return value


def _deadline_at(started_at, timer_minutes):
    if timer_minutes is None:
        return None
    started = datetime.fromisoformat(started_at)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    deadline = started + timedelta(minutes=int(timer_minutes))
    return deadline.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _question_order(version, attempt_id):
    question_ids = [question["id"] for question in version["questions"]]
    if version["question_order_policy"] == "random_per_attempt":
        rng = random.Random(_stable_seed(f"question:{version['id']}:{attempt_id}"))
        rng.shuffle(question_ids)
    return question_ids


def _option_order(version, attempt_id, question_order):
    questions_by_id = {question["id"]: question for question in version["questions"]}
    option_ids = []
    for question_id in question_order:
        options = [option["id"] for option in questions_by_id[question_id]["options"]]
        if version["option_order_policy"] == "random_per_attempt":
            rng = random.Random(
                _stable_seed(f"option:{version['id']}:{attempt_id}:{question_id}")
            )
            rng.shuffle(options)
        option_ids.extend(options)
    return option_ids


def _stable_seed(seed):
    digest = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _normalize_answer_payload(payload):
    try:
        question_id = int(payload["question_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AttemptError("question_id is required") from exc
    selected_option_id = payload.get("selected_option_id")
    if selected_option_id in ("", None):
        selected_option_id = None
    else:
        try:
            selected_option_id = int(selected_option_id)
        except (TypeError, ValueError) as exc:
            raise AttemptError("selected_option_id must be an integer") from exc
    written_response = payload.get("written_response")
    if written_response is not None:
        if not isinstance(written_response, str):
            raise AttemptError("written_response must be text")
        written_response = written_response.strip()
    return {
        "question_id": question_id,
        "selected_option_id": selected_option_id,
        "written_response": written_response,
    }


def _normalize_answers_payload(answers):
    if answers is None:
        return []
    if not isinstance(answers, list):
        raise AttemptError("answers must be a list")
    return [_normalize_answer_payload(answer) for answer in answers]


def _missing_required_answer_question_ids(conn, attempt_row, answers):
    questions = _attempt_questions(conn, attempt_row)
    answers_by_question = {
        question_id: _answer_state_from_row(answer)
        for question_id, answer in _answers_by_question(conn, attempt_row["id"]).items()
    }

    for answer in answers:
        question = _attempt_question(conn, attempt_row, answer["question_id"])
        if question is None:
            raise AttemptError("question does not belong to this attempt")
        answers_by_question[question["id"]] = _answer_state_from_payload(
            question,
            answer,
        )

    return [
        question["id"]
        for question in questions
        if not _answer_state_is_complete(
            question["snapshot_question_type"],
            answers_by_question.get(question["id"], {}),
        )
    ]


def _answer_state_from_payload(question, answer):
    if question["snapshot_question_type"] == "multiple_choice":
        return {"selected_option_id": answer["selected_option_id"]}
    if question["snapshot_question_type"] == "written":
        return {"written_response": answer["written_response"] or ""}
    raise AttemptError("unsupported question type")


def _answer_state_from_row(answer):
    return {
        "selected_option_id": answer["selected_quiz_version_option_id"],
        "written_response": answer["written_response"] or "",
    }


def _answer_state_is_complete(question_type, answer):
    if question_type == "multiple_choice":
        return answer.get("selected_option_id") is not None
    if question_type == "written":
        return bool(str(answer.get("written_response") or "").strip())
    return False


def _upsert_answer(conn, attempt_row, answer):
    question = _attempt_question(conn, attempt_row, answer["question_id"])
    if question is None:
        raise AttemptError("question does not belong to this attempt")

    selected_option_id = answer["selected_option_id"]
    written_response = answer["written_response"]
    if question["snapshot_question_type"] == "multiple_choice":
        if selected_option_id is not None and not _option_belongs_to_question(
            conn,
            selected_option_id,
            question["id"],
        ):
            raise AttemptError("selected option does not belong to this question")
        written_response = None
    elif question["snapshot_question_type"] == "written":
        selected_option_id = None
        written_response = written_response or ""
    else:
        raise AttemptError("unsupported question type")

    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO attempt_answers (
            attempt_id,
            quiz_version_question_id,
            selected_quiz_version_option_id,
            written_response,
            points_possible,
            answered_at,
            saved_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(attempt_id, quiz_version_question_id) DO UPDATE SET
            selected_quiz_version_option_id = excluded.selected_quiz_version_option_id,
            written_response = excluded.written_response,
            answered_at = excluded.answered_at,
            saved_at = excluded.saved_at
        """,
        (
            attempt_row["id"],
            question["id"],
            selected_option_id,
            written_response,
            question["points"],
            now,
            now,
        ),
    )


def _attempt_question(conn, attempt_row, question_id):
    ordered_question_ids = set(_order_values(attempt_row["question_order_json"]))
    if question_id not in ordered_question_ids:
        return None
    return conn.execute(
        """
        SELECT *
        FROM quiz_version_questions
        WHERE id = ? AND quiz_version_id = ?
        """,
        (question_id, attempt_row["quiz_version_id"]),
    ).fetchone()


def _option_belongs_to_question(conn, option_id, question_id):
    row = conn.execute(
        """
        SELECT 1
        FROM quiz_version_options
        WHERE id = ? AND quiz_version_question_id = ?
        """,
        (option_id, question_id),
    ).fetchone()
    return row is not None


def _finalize_answers(conn, attempt_row, *, finalized_at=None, finalization_reason):
    questions = _attempt_questions(conn, attempt_row)
    answers_by_question = _answers_by_question(conn, attempt_row["id"])
    has_written = False
    score = 0.0
    max_score = 0.0
    now = finalized_at or utc_now_iso()

    for question in questions:
        max_score += question["points"]
        answer = answers_by_question.get(question["id"])
        if answer is None:
            conn.execute(
                """
                INSERT INTO attempt_answers (
                    attempt_id,
                    quiz_version_question_id,
                    points_possible,
                    saved_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (attempt_row["id"], question["id"], question["points"], now),
            )
            answer = conn.execute(
                """
                SELECT *
                FROM attempt_answers
                WHERE attempt_id = ? AND quiz_version_question_id = ?
                """,
                (attempt_row["id"], question["id"]),
            ).fetchone()

        if question["snapshot_question_type"] == "written":
            written_response = (answer["written_response"] or "").strip()
            if finalization_reason == "expired" and not written_response:
                conn.execute(
                    """
                    UPDATE attempt_answers
                    SET points_awarded = 0,
                        points_possible = ?,
                        graded_at = ?
                    WHERE id = ?
                    """,
                    (question["points"], now, answer["id"]),
                )
            else:
                has_written = True
            continue

        is_correct = _selected_option_is_correct(
            conn,
            answer["selected_quiz_version_option_id"],
            question["id"],
        )
        points_awarded = float(question["points"]) if is_correct else 0.0
        score += points_awarded
        conn.execute(
            """
            UPDATE attempt_answers
            SET is_correct = ?,
                points_awarded = ?,
                points_possible = ?,
                graded_at = ?
            WHERE id = ?
            """,
            (
                1 if is_correct else 0,
                points_awarded,
                question["points"],
                now,
                answer["id"],
            ),
        )

    if has_written:
        return "needs_grading", None, max_score
    return "graded", score, max_score


def _finalize_expired_attempt_if_due(conn, attempt_row, *, now=None):
    if not _deadline_has_passed(attempt_row["deadline_at"], now=now):
        return False
    now = _coerce_now_iso(now)
    _expire_attempt_row(conn, attempt_row, now=now)
    return True


def _expire_attempt_row(conn, attempt_row, *, now):
    _status, score, max_score = _finalize_answers(
        conn,
        attempt_row,
        finalized_at=now,
        finalization_reason="expired",
    )
    cursor = conn.execute(
        """
        UPDATE attempts
        SET status = 'expired',
            expired_at = ?,
            score = ?,
            max_score = ?,
            graded_at = CASE WHEN ? IS NOT NULL THEN ? ELSE graded_at END
        WHERE id = ? AND status = 'in_progress'
        """,
        (now, score, max_score, score, now, attempt_row["id"]),
    )
    if cursor.rowcount:
        record_audit_event(
            "attempt.expired",
            object_type="attempt",
            object_id=attempt_row["id"],
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": attempt_row["quiz_version_id"],
                    "student_id": attempt_row["student_id"],
                },
            },
            db=conn,
        )


def _deadline_has_passed(deadline_at, *, now=None):
    if deadline_at is None:
        return False
    deadline = _parse_utc(deadline_at)
    now_dt = _parse_utc(_coerce_now_iso(now))
    return now_dt >= deadline + timedelta(seconds=_timer_grace_seconds())


def _expiration_cutoff_iso(now):
    now_dt = _parse_utc(now)
    cutoff = now_dt - timedelta(seconds=_timer_grace_seconds())
    return cutoff.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _coerce_now_iso(now):
    if now is None:
        return utc_now_iso()
    if isinstance(now, datetime):
        value = now
    else:
        value = datetime.fromisoformat(str(now))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse_utc(value):
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timer_grace_seconds():
    try:
        return float(current_app.config.get("TIMER_GRACE_SECONDS", 0))
    except RuntimeError:
        return 0.0


def _expiration_worker_batch_size():
    try:
        return int(current_app.config.get("EXPIRATION_WORKER_BATCH_SIZE", 50))
    except RuntimeError:
        return 50


def _selected_option_is_correct(conn, option_id, question_id):
    if option_id is None:
        return False
    row = conn.execute(
        """
        SELECT is_correct
        FROM quiz_version_options
        WHERE id = ? AND quiz_version_question_id = ?
        """,
        (option_id, question_id),
    ).fetchone()
    return bool(row and row["is_correct"])


def _attempt_payload(conn, attempt_row, *, include_answers):
    version = get_quiz_version(attempt_row["quiz_version_id"], conn=conn)
    question_order = _order_values(attempt_row["question_order_json"])
    option_order = _order_values(attempt_row["option_order_json"])
    questions_by_id = {question["id"]: question for question in version["questions"]}
    answers_by_question = _answers_by_question(conn, attempt_row["id"]) if include_answers else {}

    questions = []
    for question_id in question_order:
        question = questions_by_id[question_id]
        answer = answers_by_question.get(question_id)
        option_ids = [
            option_id
            for option_id in option_order
            if any(option["id"] == option_id for option in question["options"])
        ]
        options_by_id = {option["id"]: option for option in question["options"]}
        questions.append(
            {
                "id": question["id"],
                "position": question["position"],
                "question_type": question["snapshot_question_type"],
                "question_stem": question["snapshot_question_stem"],
                "options": [
                    {
                        "id": option_id,
                        "option_text": options_by_id[option_id]["option_text"],
                    }
                    for option_id in option_ids
                ],
                "answer": _student_answer_payload(answer),
            }
        )

    return {
        "id": attempt_row["id"],
        "quiz_version_id": attempt_row["quiz_version_id"],
        "attempt_number": attempt_row["attempt_number"],
        "status": attempt_row["status"],
        "started_at": attempt_row["started_at"],
        "deadline_at": attempt_row["deadline_at"],
        "submitted_at": attempt_row["submitted_at"],
        "graded_at": attempt_row["graded_at"],
        "quiz": {
            "id": version["id"],
            "title": version["title"],
            "description": version["description"],
            "timer_minutes": version["timer_minutes"],
            "question_count": version["question_count"],
        },
        "question_order": question_order,
        "option_order": option_order,
        "questions": questions,
    }


def _attempt_summary_payload(row):
    payload = {
        "id": row["id"],
        "quiz_version_id": row["quiz_version_id"],
        "quiz_title": row["quiz_title"],
        "student_id": row["student_id"],
        "student_identifier": row["identifier"],
        "attempt_number": row["attempt_number"],
        "status": row["status"],
        "started_at": row["started_at"],
        "deadline_at": row["deadline_at"],
        "submitted_at": row["submitted_at"],
        "expired_at": row["expired_at"],
        "graded_at": row["graded_at"],
        "voided_at": row["voided_at"],
        "score": row["score"],
        "max_score": row["max_score"],
    }
    if "answer_count" in row.keys():
        payload["answer_count"] = row["answer_count"]
    return payload


def _student_answer_payload(answer):
    if answer is None:
        return None
    return {
        "selected_option_id": answer["selected_quiz_version_option_id"],
        "written_response": answer["written_response"],
        "saved_at": answer["saved_at"],
    }


def _attempt_questions(conn, attempt_row):
    question_order = _order_values(attempt_row["question_order_json"])
    if not question_order:
        return []
    placeholders = ",".join("?" for _ in question_order)
    rows = conn.execute(
        f"""
        SELECT *
        FROM quiz_version_questions
        WHERE id IN ({placeholders})
          AND quiz_version_id = ?
        """,
        (*question_order, attempt_row["quiz_version_id"]),
    ).fetchall()
    by_id = {row["id"]: row for row in rows}
    return [by_id[question_id] for question_id in question_order]


def _answers_by_question(conn, attempt_id):
    rows = conn.execute(
        """
        SELECT *
        FROM attempt_answers
        WHERE attempt_id = ?
        """,
        (attempt_id,),
    ).fetchall()
    return {row["quiz_version_question_id"]: row for row in rows}


def _order_values(order_json):
    return validate_versioned_json("question_order_json", order_json)["order"]
