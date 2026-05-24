from .db import get_db


def list_eligible_question_ids(*, lesson_ids=None, conn=None):
    conn = conn or get_db()
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
    if lesson_ids:
        placeholders = ", ".join("?" for _ in lesson_ids)
        conditions.append(f"bank.lesson_id IN ({placeholders})")
        params.extend(lesson_ids)

    rows = conn.execute(
        f"""
        SELECT question.id
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE {" AND ".join(conditions)}
        ORDER BY question.id
        """,
        params,
    ).fetchall()
    return [row["id"] for row in rows]
