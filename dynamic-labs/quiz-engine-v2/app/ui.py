from .attempts import attempt_usage, effective_attempt_allowance
from .db import get_db
from .grading import list_written_grading_queue
from .metrics.filters import parse_metrics_filters
from .metrics.rollups import build_dashboard_metrics
from .publication import list_student_quiz_listings


FINAL_ATTEMPT_STATUSES = ("submitted", "needs_grading", "graded", "expired")


def answers_from_attempt_form(attempt, form):
    answers = []
    for question in attempt["questions"]:
        answer = {"question_id": question["id"]}
        if question["question_type"] == "multiple_choice":
            answer["selected_option_id"] = form.get(
                f"question_{question['id']}_option"
            )
        else:
            answer["written_response"] = form.get(
                f"question_{question['id']}_written",
                "",
            )
        answers.append(answer)
    return answers


def build_student_quiz_list(student, *, conn=None):
    conn = conn or get_db()
    quizzes = list_student_quiz_listings(conn=conn)
    quiz_ids = [quiz["id"] for quiz in quizzes]
    active_attempts = _attempts_by_quiz(
        conn,
        student.id,
        quiz_ids,
        statuses=("in_progress",),
    )
    result_attempts = _attempts_by_quiz(
        conn,
        student.id,
        quiz_ids,
        statuses=FINAL_ATTEMPT_STATUSES,
        latest_only=True,
    )

    cards = []
    current_cards = []
    completed_cards = []
    for quiz in quizzes:
        active_attempt = active_attempts.get(quiz["id"])
        result_attempt = result_attempts.get(quiz["id"])
        allowance = effective_attempt_allowance(quiz["id"], student.id, conn=conn)
        usage = attempt_usage(quiz["id"], student.id, conn=conn)
        attempts_remaining = max(allowance["allowance"] - usage["total_attempts"], 0)
        card = dict(quiz)
        card["active_attempt"] = active_attempt
        card["result_attempt"] = result_attempt
        card["attempt_allowance"] = allowance
        card["attempt_usage"] = usage
        card["attempts_remaining"] = attempts_remaining
        card["primary_action"] = (
            "resume"
            if active_attempt
            else "limit_reached"
            if attempts_remaining == 0
            else "start"
        )
        cards.append(card)
        if _is_completed_quiz_card(card):
            completed_cards.append(card)
        else:
            current_cards.append(card)

    return {
        "student_identifier": student.identifier,
        "quizzes": cards,
        "current_quizzes": current_cards,
        "completed_quizzes": completed_cards,
    }


def build_instructor_dashboard(*, conn=None):
    conn = conn or get_db()
    metrics = build_dashboard_metrics(parse_metrics_filters({}), conn=conn)
    written_queue = list_written_grading_queue(conn=conn)
    counts = {
        "active_students": _count(
            conn,
            "SELECT COUNT(*) FROM students WHERE status = 'active'",
        ),
        "quiz_banks": _count(
            conn,
            "SELECT COUNT(*) FROM quiz_banks WHERE archived = 0",
        ),
        "active_questions": _count(
            conn,
            "SELECT COUNT(*) FROM questions WHERE status = 'active'",
        ),
        "templates": _count(
            conn,
            "SELECT COUNT(*) FROM quiz_templates WHERE archived = 0",
        ),
        "generated_quizzes": _count(conn, "SELECT COUNT(*) FROM quiz_versions"),
        "published_quizzes": _count(
            conn,
            "SELECT COUNT(*) FROM quiz_versions WHERE visibility = 'published'",
        ),
        "attempts": _count(conn, "SELECT COUNT(*) FROM attempts"),
        "in_progress_attempts": _count(
            conn,
            "SELECT COUNT(*) FROM attempts WHERE status = 'in_progress'",
        ),
        "needs_grading_attempts": _count(
            conn,
            "SELECT COUNT(*) FROM attempts WHERE status = 'needs_grading'",
        ),
        "expired_attempts": _count(
            conn,
            "SELECT COUNT(*) FROM attempts WHERE status = 'expired'",
        ),
        "written_grading_queue": len(written_queue),
    }
    return {
        "counts": counts,
        "class_summary": metrics["class_summary"],
        "status_counts": metrics["class_summary"]["status_counts"],
        "weakest_students": metrics["weakest_students"],
        "weakest_topics": metrics["weakest_topics"],
        "weakest_tags": metrics["weakest_tags"],
        "confusing_questions": _confusing_questions(metrics["item_analysis"]),
        "recent_quizzes": _recent_quizzes(conn),
    }


def _count(conn, query, params=()):
    return int(conn.execute(query, params).fetchone()[0])


def _attempts_by_quiz(conn, student_id, quiz_ids, *, statuses, latest_only=False):
    if not quiz_ids:
        return {}
    quiz_placeholders = ", ".join("?" for _ in quiz_ids)
    status_placeholders = ", ".join("?" for _ in statuses)
    rows = conn.execute(
        f"""
        SELECT
            id,
            quiz_version_id,
            attempt_number,
            status,
            started_at,
            deadline_at,
            submitted_at,
            expired_at,
            graded_at,
            score,
            max_score
        FROM attempts
        WHERE student_id = ?
          AND quiz_version_id IN ({quiz_placeholders})
          AND status IN ({status_placeholders})
        ORDER BY quiz_version_id, attempt_number DESC, id DESC
        """,
        (student_id, *quiz_ids, *statuses),
    ).fetchall()
    attempts = {}
    for row in rows:
        quiz_id = row["quiz_version_id"]
        if latest_only and quiz_id in attempts:
            continue
        attempts[quiz_id] = dict(row)
    return attempts


def _is_completed_quiz_card(card):
    return (
        card["active_attempt"] is None
        and card["result_attempt"] is not None
        and card["attempts_remaining"] == 0
    )


def _confusing_questions(items):
    return sorted(
        items,
        key=lambda item: (
            item["percent_correct"] is None,
            item["percent_correct"] if item["percent_correct"] is not None else 101,
            -item["unanswered_count"],
            -item["attempt_count"],
        ),
    )[:8]


def _recent_quizzes(conn):
    rows = conn.execute(
        """
        SELECT
            versions.id,
            versions.title,
            versions.visibility,
            versions.created_at,
            COUNT(questions.id) AS question_count
        FROM quiz_versions versions
        LEFT JOIN quiz_version_questions questions
          ON questions.quiz_version_id = versions.id
        GROUP BY versions.id
        ORDER BY versions.created_at DESC, versions.id DESC
        LIMIT 8
        """
    ).fetchall()
    return [dict(row) for row in rows]
