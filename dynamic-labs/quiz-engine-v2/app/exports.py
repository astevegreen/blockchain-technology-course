import csv
import json
from io import StringIO

from .audit import utc_now_iso
from .db import get_db
from .metrics.filters import MetricsFilters
from .metrics.rollups import build_dashboard_metrics, get_student_detail


REPORT_SCHEMA_VERSION = 1

CLASS_CSV_HEADERS = (
    "record_type",
    "student_identifier",
    "quiz_version_id",
    "quiz_title",
    "topic",
    "tag",
    "source_type",
    "source_value",
    "question_id",
    "question_stem",
    "question_type",
    "status",
    "attempt_count",
    "completion_count",
    "missing_count",
    "average_percent",
    "median_percent",
    "min_percent",
    "max_percent",
    "correct_count",
    "percent_correct",
    "graded_count",
    "ungraded_count",
)

STUDENT_CSV_HEADERS = (
    "student_identifier",
    "attempt_id",
    "quiz_version_id",
    "quiz_title",
    "quiz_archived",
    "attempt_number",
    "status",
    "score",
    "max_score",
    "question_position",
    "question_id",
    "source_question_id",
    "question_type",
    "question_stem",
    "topic",
    "tags",
    "lesson_block",
    "specific_source_lesson",
    "specific_source_reading",
    "selected_option_text",
    "is_correct",
    "written_response",
    "points_awarded",
    "points_possible",
)

QUIZ_VERSION_CSV_HEADERS = (
    "record_type",
    "quiz_version_id",
    "quiz_title",
    "question_id",
    "question_stem",
    "question_type",
    "option_text",
    "is_correct_option",
    "selected_count",
    "attempt_count",
    "completion_count",
    "missing_count",
    "average_percent",
    "median_percent",
    "min_percent",
    "max_percent",
    "correct_count",
    "percent_correct",
    "graded_count",
    "ungraded_count",
    "expired_ungraded_count",
)

TEMPLATE_CSV_HEADERS = (
    "template_id",
    "template_title",
    "quiz_version_id",
    "quiz_title",
    "visibility",
    "archived",
    "question_count",
    "attempt_count",
    "completion_count",
    "missing_count",
    "average_percent",
    "median_percent",
    "min_percent",
    "max_percent",
)


class ExportError(ValueError):
    pass


def build_report(scope, filters: MetricsFilters, *, conn=None, **params):
    conn = conn or get_db()
    scope = _normalize_scope(scope)
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "exported_at": utc_now_iso(),
        "scope": scope,
        "filters": filters.to_payload(),
    }
    if scope == "class":
        payload["data"] = build_dashboard_metrics(filters, conn=conn)
    elif scope == "student":
        identifier = _required_param(params, "student_identifier")
        detail = get_student_detail(identifier, filters, conn=conn)
        if detail is None:
            raise ExportError("student not found")
        payload["student_identifier"] = identifier
        payload["data"] = detail
    elif scope == "quiz_version":
        quiz_version_id = _required_int_param(params, "quiz_version_id")
        scoped_filters = _filters_for_quiz(filters, quiz_version_id)
        payload["quiz_version_id"] = quiz_version_id
        payload["filters"] = scoped_filters.to_payload()
        payload["data"] = build_dashboard_metrics(scoped_filters, conn=conn)
    elif scope == "template":
        template_id = _required_int_param(params, "template_id")
        payload["template_id"] = template_id
        payload["data"] = _template_report(template_id, filters, conn=conn)
    else:
        raise ExportError("unsupported report scope")
    return payload


def render_report_csv(scope, filters: MetricsFilters, *, conn=None, **params):
    report = build_report(scope, filters, conn=conn, **params)
    scope = report["scope"]
    if scope == "class":
        return render_csv(CLASS_CSV_HEADERS, _class_csv_rows(report["data"]))
    if scope == "student":
        return render_csv(STUDENT_CSV_HEADERS, _student_csv_rows(report["data"]))
    if scope == "quiz_version":
        return render_csv(
            QUIZ_VERSION_CSV_HEADERS,
            _quiz_version_csv_rows(report["data"]),
        )
    if scope == "template":
        return render_csv(TEMPLATE_CSV_HEADERS, _template_csv_rows(report["data"]))
    raise ExportError("unsupported report scope")


def render_csv(headers, rows):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(headers), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: _csv_value(row.get(header)) for header in headers})
    return output.getvalue()


def printable_roster_sheet(*, conn=None):
    conn = conn or get_db()
    return [
        row["identifier"]
        for row in conn.execute(
            """
            SELECT identifier
            FROM students
            WHERE source = 'roster_code'
              AND status != 'revoked'
            ORDER BY id
            """
        ).fetchall()
    ]


def ingest_compatible_bank_export(quiz_bank_id, *, revision_id=None, conn=None):
    conn = conn or get_db()
    bank = conn.execute(
        """
        SELECT *
        FROM quiz_banks
        WHERE id = ?
        """,
        (int(quiz_bank_id),),
    ).fetchone()
    if bank is None:
        raise ExportError("quiz bank not found")
    revision = _bank_revision(conn, bank, revision_id)
    bank_tags = [
        row["tag"]
        for row in conn.execute(
            """
            SELECT tag
            FROM bank_revision_tags
            WHERE bank_revision_id = ?
            ORDER BY tag
            """,
            (revision["id"],),
        ).fetchall()
    ]
    questions = [
        _bank_question_payload(conn, row)
        for row in conn.execute(
            """
            SELECT *
            FROM questions
            WHERE bank_revision_id = ?
            ORDER BY id
            """,
            (revision["id"],),
        ).fetchall()
    ]
    return {
        "lesson_id": bank["lesson_id"],
        "lesson_title": revision["lesson_title"],
        "date_generated": revision["date_generated"],
        "topic": revision["topic"],
        "tags": bank_tags,
        "hierarchy": json.loads(revision["hierarchy_json"]),
        "questions": questions,
    }


def _template_report(template_id, filters, *, conn):
    template = conn.execute(
        """
        SELECT *
        FROM quiz_templates
        WHERE id = ?
        """,
        (template_id,),
    ).fetchone()
    if template is None:
        raise ExportError("template not found")
    versions = conn.execute(
        """
        SELECT
            versions.*,
            COUNT(questions.id) AS question_count
        FROM quiz_versions versions
        LEFT JOIN quiz_version_questions questions
          ON questions.quiz_version_id = versions.id
        WHERE versions.template_id = ?
        GROUP BY versions.id
        ORDER BY versions.created_at, versions.id
        """,
        (template_id,),
    ).fetchall()
    version_reports = []
    for version in versions:
        scoped_filters = _filters_for_quiz(filters, version["id"])
        metrics = build_dashboard_metrics(scoped_filters, conn=conn)
        version_reports.append(
            {
                "quiz_version_id": version["id"],
                "title": version["title"],
                "visibility": version["visibility"],
                "archived": version["archived_at"] is not None,
                "question_count": version["question_count"],
                "metrics": metrics["quiz_summary"][0]
                if metrics["quiz_summary"]
                else None,
            }
        )
    return {
        "template": {
            "id": template["id"],
            "title": template["title"],
            "description": template["description"],
            "archived": bool(template["archived"]),
        },
        "quiz_versions": version_reports,
    }


def _class_csv_rows(metrics):
    summary = metrics["class_summary"]
    stats = summary["score_stats"]
    rows = [
        {
            "record_type": "class_summary",
            "attempt_count": summary["selected_attempt_count"],
            "completion_count": summary["completion_count"],
            "missing_count": summary["missing_count"],
            "average_percent": stats["average_percent"],
            "median_percent": stats["median_percent"],
            "min_percent": stats["min_percent"],
            "max_percent": stats["max_percent"],
        }
    ]
    for quiz in metrics["quiz_summary"]:
        rows.append(
            {
                "record_type": "quiz_summary",
                "quiz_version_id": quiz["quiz_version_id"],
                "quiz_title": quiz["title"],
                "attempt_count": quiz["attempt_count"],
                "completion_count": quiz["completion_count"],
                "missing_count": quiz["missing_count"],
                "average_percent": quiz["score_stats"]["average_percent"],
                "median_percent": quiz["score_stats"]["median_percent"],
                "min_percent": quiz["score_stats"]["min_percent"],
                "max_percent": quiz["score_stats"]["max_percent"],
            }
        )
    for student in metrics["student_summary"]:
        rows.append(
            {
                "record_type": "student_summary",
                "student_identifier": student["student_identifier"],
                "attempt_count": student["attempt_count"],
                "completion_count": student["completion_count"],
                "missing_count": student["missing_count"],
                "average_percent": student["average_score_percent"],
            }
        )
    for topic in metrics["topic_rollups"]:
        rows.append(
            {
                "record_type": "topic_rollup",
                "topic": topic["topic"],
                "attempt_count": topic["answer_count"],
                "average_percent": topic["average_percent"],
            }
        )
    for tag in metrics["tag_rollups"]:
        rows.append(
            {
                "record_type": "tag_rollup",
                "tag": tag["tag"],
                "attempt_count": tag["answer_count"],
                "average_percent": tag["average_percent"],
            }
        )
    for source_type, source_key in (
        ("lesson_block", "lesson_blocks"),
        ("specific_source_lesson", "specific_source_lessons"),
        ("specific_source_reading", "specific_source_readings"),
    ):
        for source in metrics["source_rollups"][source_key]:
            rows.append(
                {
                    "record_type": "source_rollup",
                    "source_type": source_type,
                    "source_value": source[source_type],
                    "attempt_count": source["answer_count"],
                    "average_percent": source["average_percent"],
                }
            )
    for item in metrics["item_analysis"]:
        rows.append(_item_csv_row(item, "item_analysis"))
    return rows


def _student_csv_rows(detail):
    rows = []
    for attempt in detail["attempts"]:
        if not attempt["questions"]:
            rows.append(_student_attempt_row(detail, attempt, None))
            continue
        for question in attempt["questions"]:
            rows.append(_student_attempt_row(detail, attempt, question))
    return rows


def _quiz_version_csv_rows(metrics):
    rows = []
    for quiz in metrics["quiz_summary"]:
        stats = quiz["score_stats"]
        rows.append(
            {
                "record_type": "quiz_summary",
                "quiz_version_id": quiz["quiz_version_id"],
                "quiz_title": quiz["title"],
                "attempt_count": quiz["attempt_count"],
                "completion_count": quiz["completion_count"],
                "missing_count": quiz["missing_count"],
                "average_percent": stats["average_percent"],
                "median_percent": stats["median_percent"],
                "min_percent": stats["min_percent"],
                "max_percent": stats["max_percent"],
            }
        )
    for item in metrics["item_analysis"]:
        rows.append(_item_csv_row(item, "item_analysis"))
        for option in item["distractor_counts"]:
            rows.append(
                {
                    "record_type": "distractor",
                    "quiz_version_id": item["quiz_version_id"],
                    "quiz_title": item["quiz_title"],
                    "question_id": item["quiz_version_question_id"],
                    "question_stem": item["question_stem"],
                    "question_type": item["question_type"],
                    "option_text": option["option_text"],
                    "is_correct_option": option["is_correct"],
                    "selected_count": option["selected_count"],
                }
            )
    return rows


def _template_csv_rows(data):
    template = data["template"]
    rows = []
    for version in data["quiz_versions"]:
        metrics = version["metrics"] or {}
        stats = metrics.get("score_stats") or {}
        rows.append(
            {
                "template_id": template["id"],
                "template_title": template["title"],
                "quiz_version_id": version["quiz_version_id"],
                "quiz_title": version["title"],
                "visibility": version["visibility"],
                "archived": version["archived"],
                "question_count": version["question_count"],
                "attempt_count": metrics.get("attempt_count"),
                "completion_count": metrics.get("completion_count"),
                "missing_count": metrics.get("missing_count"),
                "average_percent": stats.get("average_percent"),
                "median_percent": stats.get("median_percent"),
                "min_percent": stats.get("min_percent"),
                "max_percent": stats.get("max_percent"),
            }
        )
    return rows


def _item_csv_row(item, record_type):
    return {
        "record_type": record_type,
        "quiz_version_id": item["quiz_version_id"],
        "quiz_title": item["quiz_title"],
        "question_id": item["quiz_version_question_id"],
        "question_stem": item["question_stem"],
        "question_type": item["question_type"],
        "topic": item["topic"],
        "attempt_count": item["attempt_count"],
        "correct_count": item["correct_count"],
        "percent_correct": item["percent_correct"],
        "graded_count": item["written_grading_status"]["graded_count"],
        "ungraded_count": item["written_grading_status"]["ungraded_count"],
        "source_type": "lesson_block",
        "source_value": item["lesson_block"],
    }


def _student_attempt_row(detail, attempt, question):
    row = {
        "student_identifier": detail["student_identifier"],
        "attempt_id": attempt["attempt_id"],
        "quiz_version_id": attempt["quiz_version_id"],
        "quiz_title": attempt["quiz_title"],
        "quiz_archived": attempt["quiz_archived"],
        "attempt_number": attempt["attempt_number"],
        "status": attempt["status"],
        "score": attempt["score"],
        "max_score": attempt["max_score"],
    }
    if question is None:
        return row
    answer = question["answer"]
    row.update(
        {
            "question_position": question["position"],
            "question_id": question["quiz_version_question_id"],
            "source_question_id": question["source_question_id"],
            "question_type": question["question_type"],
            "question_stem": question["question_stem"],
            "topic": question["topic"],
            "tags": question["tags"],
            "lesson_block": question["lesson_block"],
            "specific_source_lesson": question["specific_source_lesson"],
            "specific_source_reading": question["specific_source_reading"],
            "selected_option_text": answer["selected_option_text"],
            "is_correct": answer["is_correct"],
            "written_response": answer["written_response"],
            "points_awarded": answer["points_awarded"],
            "points_possible": answer["points_possible"],
        }
    )
    return row


def _bank_revision(conn, bank, revision_id):
    target_revision_id = revision_id or bank["latest_revision_id"]
    row = conn.execute(
        """
        SELECT *
        FROM quiz_bank_revisions
        WHERE id = ? AND quiz_bank_id = ?
        """,
        (int(target_revision_id), bank["id"]),
    ).fetchone()
    if row is None:
        raise ExportError("quiz bank revision not found")
    return row


def _bank_question_payload(conn, row):
    tags = [
        tag["tag"]
        for tag in conn.execute(
            """
            SELECT tag
            FROM question_tags
            WHERE question_id = ?
            ORDER BY tag
            """,
            (row["id"],),
        ).fetchall()
    ]
    payload = {
        "id": row["source_qid"],
        "question_stem": row["question_stem"],
        "question_type": row["question_type"],
        "difficulty_level": row["difficulty_level"],
        "topic": row["topic"],
        "tags": tags,
        "lesson_block": row["lesson_block"],
        "specific_source_lesson": row["specific_source_lesson"],
        "specific_source_reading": row["specific_source_reading"],
        "explanation": row["explanation"],
    }
    if row["question_type"] == "multiple_choice":
        options = conn.execute(
            """
            SELECT option_text, is_correct
            FROM question_options
            WHERE question_id = ?
            ORDER BY ingest_order
            """,
            (row["id"],),
        ).fetchall()
        correct = next((option for option in options if option["is_correct"]), None)
        payload["correct_answer"] = correct["option_text"] if correct else ""
        payload["incorrect_answers"] = [
            option["option_text"] for option in options if not option["is_correct"]
        ]
    return payload


def _filters_for_quiz(filters, quiz_version_id):
    return MetricsFilters(
        mode=filters.mode,
        statuses=filters.statuses,
        include_voided=filters.include_voided,
        quiz_version_id=int(quiz_version_id),
    )


def _normalize_scope(scope):
    scope = str(scope or "").strip().lower().replace("-", "_")
    if scope == "quiz":
        return "quiz_version"
    if scope not in {"class", "student", "quiz_version", "template"}:
        raise ExportError("unsupported report scope")
    return scope


def _required_param(params, key):
    value = params.get(key)
    if value is None or str(value).strip() == "":
        raise ExportError(f"{key} is required")
    return str(value).strip()


def _required_int_param(params, key):
    value = _required_param(params, key)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ExportError(f"{key} must be an integer") from exc
    if parsed <= 0:
        raise ExportError(f"{key} must be positive")
    return parsed


def _csv_value(value):
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value
