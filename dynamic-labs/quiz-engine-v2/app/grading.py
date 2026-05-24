from .attempts import AttemptError, get_student_attempt
from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .json_validation import validate_versioned_json
from .quiz_versions import get_quiz_version


class GradingError(ValueError):
    pass


def list_written_grading_queue(*, conn=None):
    conn = conn or get_db()
    rows = conn.execute(
        """
        SELECT
            answers.id AS answer_id,
            answers.attempt_id,
            answers.quiz_version_question_id,
            answers.written_response,
            answers.points_awarded,
            answers.points_possible,
            answers.saved_at,
            attempts.quiz_version_id,
            attempts.student_id,
            attempts.attempt_number,
            attempts.status AS attempt_status,
            students.identifier AS student_identifier,
            versions.title AS quiz_title,
            questions.snapshot_question_stem,
            questions.snapshot_explanation
        FROM attempt_answers answers
        JOIN attempts ON attempts.id = answers.attempt_id
        JOIN students ON students.id = attempts.student_id
        JOIN quiz_versions versions ON versions.id = attempts.quiz_version_id
        JOIN quiz_version_questions questions
          ON questions.id = answers.quiz_version_question_id
        WHERE questions.snapshot_question_type = 'written'
          AND attempts.status IN ('needs_grading', 'expired')
          AND answers.points_awarded IS NULL
        ORDER BY attempts.started_at ASC, answers.id ASC
        """
    ).fetchall()
    return [_queue_row(row) for row in rows]


def grade_written_answer(answer_id, points_awarded, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    points_awarded = _points(points_awarded)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = _gradeable_answer_row(conn, int(answer_id))
        if row is None:
            raise GradingError("written answer not found")
        if row["snapshot_question_type"] != "written":
            raise GradingError("answer is not written")
        if row["attempt_status"] in {"in_progress", "voided"}:
            raise GradingError("attempt is not gradeable")
        if points_awarded > float(row["points_possible"]):
            raise GradingError("points_awarded exceeds points_possible")

        now = utc_now_iso()
        conn.execute(
            """
            UPDATE attempt_answers
            SET points_awarded = ?,
                points_possible = ?,
                graded_at = ?,
                graded_by = ?
            WHERE id = ?
            """,
            (
                points_awarded,
                row["points_possible"],
                now,
                actor_sub,
                row["answer_id"],
            ),
        )
        attempt = _recalculate_attempt_score(conn, row["attempt_id"], graded_at=now)
        record_audit_event(
            "written_answer.graded",
            actor_sub=actor_sub,
            object_type="attempt_answer",
            object_id=row["answer_id"],
            details={
                "schema_version": 1,
                "details": {
                    "attempt_id": row["attempt_id"],
                    "quiz_version_id": row["quiz_version_id"],
                    "quiz_version_question_id": row["quiz_version_question_id"],
                    "student_id": row["student_id"],
                    "points_awarded": points_awarded,
                },
            },
            db=conn,
        )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    graded = _gradeable_answer_row(conn, int(answer_id))
    return {"answer": _graded_answer_payload(graded), "attempt": attempt}


def release_quiz_results(quiz_version_id, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    quiz_version_id = int(quiz_version_id)
    try:
        conn.execute("BEGIN IMMEDIATE")
        version = get_quiz_version(quiz_version_id, conn=conn)
        if version is None:
            raise GradingError("quiz version not found")
        if version["results_released_at"] is None:
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE quiz_versions
                SET results_released_at = ?,
                    results_released_by = ?
                WHERE id = ? AND results_released_at IS NULL
                """,
                (now, actor_sub, quiz_version_id),
            )
            record_audit_event(
                "quiz_results.released",
                actor_sub=actor_sub,
                object_type="quiz_version",
                object_id=quiz_version_id,
                details={
                    "schema_version": 1,
                    "details": {
                        "quiz_version_id": quiz_version_id,
                        "result_policy": version["result_policy"],
                    },
                },
                db=conn,
            )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    return get_quiz_version(quiz_version_id, conn=conn)


def release_quiz_review(quiz_version_id, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    quiz_version_id = int(quiz_version_id)
    try:
        conn.execute("BEGIN IMMEDIATE")
        version = get_quiz_version(quiz_version_id, conn=conn)
        if version is None:
            raise GradingError("quiz version not found")
        if version["review_released_at"] is None:
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE quiz_versions
                SET review_released_at = ?,
                    review_released_by = ?
                WHERE id = ? AND review_released_at IS NULL
                """,
                (now, actor_sub, quiz_version_id),
            )
            record_audit_event(
                "quiz_review.released",
                actor_sub=actor_sub,
                object_type="quiz_version",
                object_id=quiz_version_id,
                details={
                    "schema_version": 1,
                    "details": {
                        "quiz_version_id": quiz_version_id,
                        "result_policy": version["result_policy"],
                    },
                },
                db=conn,
            )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    return get_quiz_version(quiz_version_id, conn=conn)


def get_student_result(attempt_id, student, *, conn=None):
    conn = conn or get_db()
    try:
        get_student_attempt(attempt_id, student, conn=conn)
    except AttemptError as exc:
        raise GradingError(str(exc)) from exc

    row = conn.execute(
        """
        SELECT
            attempts.*,
            versions.title,
            versions.description,
            versions.result_policy,
            versions.results_released_at,
            versions.results_released_by,
            versions.review_released_at,
            versions.review_released_by
        FROM attempts
        JOIN quiz_versions versions ON versions.id = attempts.quiz_version_id
        WHERE attempts.id = ? AND attempts.student_id = ?
        """,
        (int(attempt_id), student.id),
    ).fetchone()
    if row is None:
        raise GradingError("attempt not found")

    policy = row["result_policy"]
    grading_complete = _grading_complete(row)
    released = row["results_released_at"] is not None
    review_released = row["review_released_at"] is not None
    score_visible = _score_visible(policy, grading_complete, released)
    review_visible = _review_visible(
        policy,
        grading_complete,
        released,
        review_released,
    )
    return {
        "attempt_id": row["id"],
        "quiz_version_id": row["quiz_version_id"],
        "attempt_number": row["attempt_number"],
        "status": row["status"],
        "result_policy": policy,
        "results_released_at": row["results_released_at"],
        "review_released_at": row["review_released_at"],
        "score_visible": score_visible,
        "review_visible": review_visible,
        "score": row["score"] if score_visible else None,
        "max_score": row["max_score"] if score_visible else None,
        "quiz": {
            "title": row["title"],
            "description": row["description"],
        },
        "questions": _result_questions(conn, row) if review_visible else [],
    }


def _points(value):
    try:
        points = float(value)
    except (TypeError, ValueError) as exc:
        raise GradingError("points_awarded must be a number") from exc
    if points < 0:
        raise GradingError("points_awarded must be non-negative")
    return points


def _gradeable_answer_row(conn, answer_id):
    return conn.execute(
        """
        SELECT
            answers.id AS answer_id,
            answers.attempt_id,
            answers.quiz_version_question_id,
            answers.written_response,
            answers.points_awarded,
            answers.points_possible,
            answers.graded_at,
            answers.graded_by,
            attempts.quiz_version_id,
            attempts.student_id,
            attempts.status AS attempt_status,
            attempts.score,
            attempts.max_score,
            questions.snapshot_question_type,
            questions.snapshot_question_stem,
            questions.snapshot_explanation
        FROM attempt_answers answers
        JOIN attempts ON attempts.id = answers.attempt_id
        JOIN quiz_version_questions questions
          ON questions.id = answers.quiz_version_question_id
        WHERE answers.id = ?
        """,
        (answer_id,),
    ).fetchone()


def _recalculate_attempt_score(conn, attempt_id, *, graded_at):
    attempt = conn.execute(
        "SELECT * FROM attempts WHERE id = ?",
        (attempt_id,),
    ).fetchone()
    rows = conn.execute(
        """
        SELECT
            questions.id AS question_id,
            questions.snapshot_question_type,
            questions.points,
            answers.points_awarded
        FROM quiz_version_questions questions
        LEFT JOIN attempt_answers answers
          ON answers.quiz_version_question_id = questions.id
         AND answers.attempt_id = ?
        WHERE questions.quiz_version_id = ?
        ORDER BY questions.position
        """,
        (attempt_id, attempt["quiz_version_id"]),
    ).fetchall()
    max_score = float(sum(float(row["points"]) for row in rows))
    has_ungraded_written = any(
        row["snapshot_question_type"] == "written" and row["points_awarded"] is None
        for row in rows
    )
    if has_ungraded_written:
        conn.execute(
            """
            UPDATE attempts
            SET score = NULL,
                max_score = ?
            WHERE id = ?
            """,
            (max_score, attempt_id),
        )
    else:
        score = sum(float(row["points_awarded"] or 0) for row in rows)
        next_status = "graded" if attempt["status"] == "needs_grading" else attempt["status"]
        conn.execute(
            """
            UPDATE attempts
            SET status = ?,
                score = ?,
                max_score = ?,
                graded_at = ?
            WHERE id = ?
            """,
            (next_status, score, max_score, graded_at, attempt_id),
        )

    row = conn.execute(
        "SELECT * FROM attempts WHERE id = ?",
        (attempt_id,),
    ).fetchone()
    return {
        "id": row["id"],
        "quiz_version_id": row["quiz_version_id"],
        "student_id": row["student_id"],
        "attempt_number": row["attempt_number"],
        "status": row["status"],
        "score": row["score"],
        "max_score": row["max_score"],
        "graded_at": row["graded_at"],
        "expired_at": row["expired_at"],
    }


def _grading_complete(row):
    if row["status"] == "graded":
        return row["score"] is not None and row["max_score"] is not None
    if row["status"] == "expired":
        return row["score"] is not None and row["max_score"] is not None
    return False


def _score_visible(policy, grading_complete, released):
    if not grading_complete or policy == "hidden":
        return False
    if policy in {"score_after_grading", "score_and_answers_after_grading"}:
        return True
    if policy in {"score_after_release", "score_and_answers_after_release"}:
        return released
    return False


def _review_visible(policy, grading_complete, released, review_released=False):
    if not _score_visible(policy, grading_complete, released):
        return False
    if review_released and policy != "hidden":
        return True
    return policy in {
        "score_and_answers_after_grading",
        "score_and_answers_after_release",
    }


def _result_questions(conn, attempt_row):
    question_order = validate_versioned_json(
        "question_order_json",
        attempt_row["question_order_json"],
    )["order"]
    option_order = validate_versioned_json(
        "option_order_json",
        attempt_row["option_order_json"],
    )["order"]
    if not question_order:
        return []

    questions = conn.execute(
        f"""
        SELECT
            questions.*,
            answers.selected_quiz_version_option_id,
            answers.written_response,
            answers.is_correct,
            answers.points_awarded,
            answers.points_possible,
            answers.saved_at,
            answers.graded_at
        FROM quiz_version_questions questions
        LEFT JOIN attempt_answers answers
          ON answers.quiz_version_question_id = questions.id
         AND answers.attempt_id = ?
        WHERE questions.id IN ({",".join("?" for _ in question_order)})
          AND questions.quiz_version_id = ?
        """,
        (attempt_row["id"], *question_order, attempt_row["quiz_version_id"]),
    ).fetchall()
    by_id = {row["id"]: row for row in questions}
    return [
        _result_question_payload(conn, by_id[question_id], option_order)
        for question_id in question_order
    ]


def _result_question_payload(conn, question, option_order):
    options = conn.execute(
        """
        SELECT *
        FROM quiz_version_options
        WHERE quiz_version_question_id = ?
        """,
        (question["id"],),
    ).fetchall()
    options_by_id = {row["id"]: row for row in options}
    ordered_options = [
        options_by_id[option_id]
        for option_id in option_order
        if option_id in options_by_id
    ]
    correct_option = next(
        (option for option in ordered_options if option["is_correct"]),
        None,
    )
    selected_option = options_by_id.get(question["selected_quiz_version_option_id"])
    payload = {
        "id": question["id"],
        "question_type": question["snapshot_question_type"],
        "question_stem": question["snapshot_question_stem"],
        "explanation": question["snapshot_explanation"],
        "points_awarded": question["points_awarded"],
        "points_possible": question["points_possible"],
    }
    if question["snapshot_question_type"] == "multiple_choice":
        payload.update(
            {
                "is_correct": bool(question["is_correct"]),
                "selected_option_id": question["selected_quiz_version_option_id"],
                "selected_option_text": selected_option["option_text"]
                if selected_option
                else None,
                "correct_option_id": correct_option["id"] if correct_option else None,
                "correct_option_text": correct_option["option_text"]
                if correct_option
                else None,
                "options": [
                    {
                        "id": option["id"],
                        "option_text": option["option_text"],
                        "is_correct": bool(option["is_correct"]),
                    }
                    for option in ordered_options
                ],
            }
        )
    else:
        payload["written_response"] = question["written_response"]
    return payload


def _queue_row(row):
    return {
        "answer_id": row["answer_id"],
        "attempt_id": row["attempt_id"],
        "quiz_version_id": row["quiz_version_id"],
        "quiz_version_question_id": row["quiz_version_question_id"],
        "quiz_title": row["quiz_title"],
        "student_id": row["student_id"],
        "student_identifier": row["student_identifier"],
        "attempt_number": row["attempt_number"],
        "attempt_status": row["attempt_status"],
        "question_stem": row["snapshot_question_stem"],
        "explanation": row["snapshot_explanation"],
        "written_response": row["written_response"],
        "points_awarded": row["points_awarded"],
        "points_possible": row["points_possible"],
        "saved_at": row["saved_at"],
    }


def _graded_answer_payload(row):
    return {
        "answer_id": row["answer_id"],
        "attempt_id": row["attempt_id"],
        "quiz_version_id": row["quiz_version_id"],
        "quiz_version_question_id": row["quiz_version_question_id"],
        "attempt_status": row["attempt_status"],
        "question_type": row["snapshot_question_type"],
        "question_stem": row["snapshot_question_stem"],
        "written_response": row["written_response"],
        "points_awarded": row["points_awarded"],
        "points_possible": row["points_possible"],
        "graded_at": row["graded_at"],
        "graded_by": row["graded_by"],
    }
