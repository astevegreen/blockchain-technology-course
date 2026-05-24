from ..db import get_db


def fetch_attempt_rows(*, conn=None):
    conn = conn or get_db()
    return conn.execute(
        """
        SELECT
            attempts.*,
            students.identifier AS student_identifier,
            students.status AS student_status,
            versions.title AS quiz_title,
            versions.visibility AS quiz_visibility,
            versions.archived_at AS quiz_archived_at
        FROM attempts
        JOIN students ON students.id = attempts.student_id
        JOIN quiz_versions versions ON versions.id = attempts.quiz_version_id
        ORDER BY versions.id, students.identifier, attempts.attempt_number, attempts.id
        """
    ).fetchall()


def fetch_quiz_versions(*, conn=None):
    conn = conn or get_db()
    return conn.execute(
        """
        SELECT
            versions.*,
            COUNT(questions.id) AS question_count
        FROM quiz_versions versions
        LEFT JOIN quiz_version_questions questions
          ON questions.quiz_version_id = versions.id
        GROUP BY versions.id
        ORDER BY versions.created_at, versions.id
        """
    ).fetchall()


def fetch_active_students(*, conn=None):
    conn = conn or get_db()
    return conn.execute(
        """
        SELECT id, identifier, status, source, cohort_id, created_at
        FROM students
        WHERE status = 'active'
        ORDER BY identifier
        """
    ).fetchall()


def fetch_student_by_identifier(identifier, *, conn=None):
    conn = conn or get_db()
    return conn.execute(
        """
        SELECT id, identifier, status, source, cohort_id, created_at
        FROM students
        WHERE identifier = ?
        """,
        (identifier,),
    ).fetchone()


def fetch_question_rows(attempt_ids, *, conn=None):
    conn = conn or get_db()
    attempt_ids = [int(attempt_id) for attempt_id in attempt_ids]
    if not attempt_ids:
        return []
    placeholders = ", ".join("?" for _ in attempt_ids)
    return conn.execute(
        f"""
        SELECT
            attempts.id AS attempt_id,
            attempts.quiz_version_id,
            attempts.student_id,
            attempts.attempt_number,
            attempts.status AS attempt_status,
            attempts.score AS attempt_score,
            attempts.max_score AS attempt_max_score,
            attempts.started_at,
            attempts.submitted_at,
            attempts.expired_at,
            attempts.voided_at,
            attempts.graded_at AS attempt_graded_at,
            students.identifier AS student_identifier,
            versions.title AS quiz_title,
            versions.visibility AS quiz_visibility,
            versions.archived_at AS quiz_archived_at,
            questions.id AS quiz_version_question_id,
            questions.source_question_id,
            questions.position,
            questions.points,
            questions.snapshot_source_qid,
            questions.snapshot_question_type,
            questions.snapshot_question_stem,
            questions.snapshot_explanation,
            questions.snapshot_difficulty_level,
            questions.snapshot_topic,
            questions.snapshot_tags_json,
            questions.snapshot_lesson_block,
            questions.snapshot_specific_source_lesson,
            questions.snapshot_specific_source_reading,
            answers.id AS answer_id,
            answers.selected_quiz_version_option_id,
            answers.written_response,
            answers.is_correct,
            answers.points_awarded,
            answers.points_possible,
            answers.answered_at,
            answers.saved_at,
            answers.graded_at AS answer_graded_at,
            answers.graded_by,
            selected.option_text AS selected_option_text,
            selected.is_correct AS selected_option_is_correct
        FROM attempts
        JOIN students ON students.id = attempts.student_id
        JOIN quiz_versions versions ON versions.id = attempts.quiz_version_id
        JOIN quiz_version_questions questions
          ON questions.quiz_version_id = attempts.quiz_version_id
        LEFT JOIN attempt_answers answers
          ON answers.attempt_id = attempts.id
         AND answers.quiz_version_question_id = questions.id
        LEFT JOIN quiz_version_options selected
          ON selected.id = answers.selected_quiz_version_option_id
        WHERE attempts.id IN ({placeholders})
        ORDER BY attempts.id, questions.position
        """,
        attempt_ids,
    ).fetchall()


def fetch_option_rows(question_ids, *, conn=None):
    conn = conn or get_db()
    question_ids = [int(question_id) for question_id in question_ids]
    if not question_ids:
        return []
    placeholders = ", ".join("?" for _ in question_ids)
    return conn.execute(
        f"""
        SELECT
            id,
            quiz_version_question_id,
            option_text,
            is_correct,
            snapshot_order
        FROM quiz_version_options
        WHERE quiz_version_question_id IN ({placeholders})
        ORDER BY quiz_version_question_id, snapshot_order
        """,
        question_ids,
    ).fetchall()

