import json
from collections import defaultdict
from statistics import median

from .filters import METRIC_STATUS_ORDER, MetricsFilters
from .queries import (
    fetch_active_students,
    fetch_attempt_rows,
    fetch_option_rows,
    fetch_question_rows,
    fetch_quiz_versions,
    fetch_student_by_identifier,
)


COMPLETED_STATUSES = frozenset({"submitted", "needs_grading", "graded"})
SCORE_BUCKETS = (
    ("0-59", 0, 60),
    ("60-69", 60, 70),
    ("70-79", 70, 80),
    ("80-89", 80, 90),
    ("90-100", 90, 101),
)


def build_dashboard_metrics(filters: MetricsFilters, *, conn=None):
    attempts = [_dict(row) for row in fetch_attempt_rows(conn=conn)]
    quiz_versions = [_dict(row) for row in fetch_quiz_versions(conn=conn)]
    active_students = [_dict(row) for row in fetch_active_students(conn=conn)]

    if filters.quiz_version_ids:
        attempts = [
            attempt
            for attempt in attempts
            if attempt["quiz_version_id"] in filters.quiz_version_ids
        ]
        quiz_versions = [
            version
            for version in quiz_versions
            if version["id"] in filters.quiz_version_ids
        ]

    rollup_attempts = _rollup_attempts(attempts, filters)
    selected_attempts = [
        attempt
        for attempt in rollup_attempts
        if attempt["status"] in filters.attempt_statuses
    ]
    missing_pairs = _missing_pairs(active_students, quiz_versions, rollup_attempts)

    question_rows = [
        _dict(row)
        for row in fetch_question_rows(
            [attempt["id"] for attempt in selected_attempts],
            conn=conn,
        )
    ]
    option_rows = [
        _dict(row)
        for row in fetch_option_rows(
            sorted({row["quiz_version_question_id"] for row in question_rows}),
            conn=conn,
        )
    ]
    (
        topic_rollups,
        tag_rollups,
        source_rollups,
        difficulty_rollups,
        question_type_rollups,
    ) = _answer_dimension_rollups(question_rows)
    student_summary = _student_summary(
        selected_attempts,
        rollup_attempts,
        active_students,
        quiz_versions,
        filters,
    )
    class_summary = _class_summary(
        selected_attempts,
        active_students,
        quiz_versions,
        missing_pairs,
        filters,
    )
    quiz_summary = _quiz_summary(
        selected_attempts,
        rollup_attempts,
        active_students,
        quiz_versions,
        filters,
    )
    item_analysis = _item_analysis(question_rows, option_rows)

    return {
        "filters": filters.to_payload(),
        "class_summary": class_summary,
        "quiz_summary": quiz_summary,
        "student_summary": student_summary,
        "strongest_students": _strongest_students(student_summary),
        "weakest_students": _weakest_students(student_summary),
        "topic_rollups": topic_rollups,
        "tag_rollups": tag_rollups,
        "difficulty_rollups": difficulty_rollups,
        "question_type_rollups": question_type_rollups,
        "strongest_topics": _strongest_dimensions(topic_rollups),
        "weakest_topics": _weakest_dimensions(topic_rollups),
        "strongest_tags": _strongest_dimensions(tag_rollups),
        "weakest_tags": _weakest_dimensions(tag_rollups),
        "source_rollups": source_rollups,
        "strengths_weaknesses": _strengths_weaknesses(
            topic_rollups,
            tag_rollups,
            source_rollups,
            difficulty_rollups,
            question_type_rollups,
            item_analysis,
        ),
        "item_analysis": item_analysis,
        "visualizations": _visualization_metrics(
            class_summary,
            quiz_summary,
            student_summary,
            topic_rollups,
            tag_rollups,
            item_analysis,
        ),
        "metric_catalog": _metric_catalog(
            attempts,
            selected_attempts,
            rollup_attempts,
            active_students,
            quiz_versions,
            student_summary,
            topic_rollups,
            tag_rollups,
            source_rollups,
            difficulty_rollups,
            question_type_rollups,
            item_analysis,
            filters,
        ),
    }


def get_student_detail(identifier, filters: MetricsFilters, *, conn=None):
    student = fetch_student_by_identifier(identifier, conn=conn)
    if student is None:
        return None
    student = _dict(student)
    attempts = [
        _dict(row)
        for row in fetch_attempt_rows(conn=conn)
        if row["student_id"] == student["id"]
    ]
    if filters.quiz_version_ids:
        attempts = [
            attempt
            for attempt in attempts
            if attempt["quiz_version_id"] in filters.quiz_version_ids
        ]
    attempts = _rollup_attempts(attempts, filters)
    attempts = [
        attempt
        for attempt in attempts
        if attempt["status"] in filters.attempt_statuses
    ]
    question_rows = [
        _dict(row)
        for row in fetch_question_rows([attempt["id"] for attempt in attempts], conn=conn)
    ]
    option_rows = [
        _dict(row)
        for row in fetch_option_rows(
            [row["quiz_version_question_id"] for row in question_rows],
            conn=conn,
        )
    ]
    options_by_question = defaultdict(list)
    for option in option_rows:
        options_by_question[option["quiz_version_question_id"]].append(option)

    (
        topic_rollups,
        tag_rollups,
        source_rollups,
        difficulty_rollups,
        question_type_rollups,
    ) = _answer_dimension_rollups(question_rows)
    item_analysis = _item_analysis(question_rows, option_rows)

    questions_by_attempt = defaultdict(list)
    for row in question_rows:
        questions_by_attempt[row["attempt_id"]].append(
            _student_detail_question(
                row,
                options_by_question.get(row["quiz_version_question_id"], []),
            )
        )

    return {
        "student_identifier": student["identifier"],
        "student_status": student["status"],
        "filters": filters.to_payload(),
        "attempt_count": len(attempts),
        "strengths_weaknesses": _strengths_weaknesses(
            topic_rollups,
            tag_rollups,
            source_rollups,
            difficulty_rollups,
            question_type_rollups,
            item_analysis,
        ),
        "attempts": [
            _student_detail_attempt(
                attempt,
                questions_by_attempt.get(attempt["id"], []),
            )
            for attempt in sorted(
                attempts,
                key=lambda attempt: (
                    attempt["quiz_version_id"],
                    attempt["attempt_number"],
                    attempt["id"],
                ),
            )
        ],
    }


def _rollup_attempts(attempts, filters):
    candidates = [
        attempt
        for attempt in attempts
        if filters.include_voided or attempt["status"] != "voided"
    ]
    if filters.mode == "all":
        return candidates

    latest = {}
    for attempt in candidates:
        key = (attempt["student_id"], attempt["quiz_version_id"])
        previous = latest.get(key)
        if previous is None or (
            int(attempt["attempt_number"]),
            int(attempt["id"]),
        ) > (
            int(previous["attempt_number"]),
            int(previous["id"]),
        ):
            latest[key] = attempt
    return list(latest.values())


def _missing_pairs(active_students, quiz_versions, rollup_attempts):
    attempted_pairs = {
        (attempt["student_id"], attempt["quiz_version_id"])
        for attempt in rollup_attempts
    }
    return {
        (student["id"], quiz_version["id"])
        for student in active_students
        for quiz_version in quiz_versions
        if (student["id"], quiz_version["id"]) not in attempted_pairs
    }


def _class_summary(
    selected_attempts,
    active_students,
    quiz_versions,
    missing_pairs,
    filters,
):
    score_stats = _attempt_score_stats(selected_attempts)
    status_counts = _status_counts(selected_attempts)
    if filters.includes_missing:
        status_counts["missing"] = len(missing_pairs)
    return {
        "active_student_count": len(active_students),
        "quiz_version_count": len(quiz_versions),
        "expected_student_quiz_pairs": len(active_students) * len(quiz_versions),
        "selected_attempt_count": len(selected_attempts),
        "completion_count": _completion_count(selected_attempts),
        "missing_count": len(missing_pairs) if filters.includes_missing else 0,
        "status_counts": status_counts,
        "score_stats": score_stats,
    }


def _quiz_summary(
    selected_attempts,
    rollup_attempts,
    active_students,
    quiz_versions,
    filters,
):
    selected_by_quiz = _group_by(selected_attempts, "quiz_version_id")
    rollup_by_quiz = _group_by(rollup_attempts, "quiz_version_id")
    active_student_ids = {student["id"] for student in active_students}
    summaries = []
    for version in quiz_versions:
        quiz_id = version["id"]
        selected = selected_by_quiz.get(quiz_id, [])
        attempted_student_ids = {
            attempt["student_id"] for attempt in rollup_by_quiz.get(quiz_id, [])
        }
        missing_count = len(active_student_ids - attempted_student_ids)
        status_counts = _status_counts(selected)
        if filters.includes_missing:
            status_counts["missing"] = missing_count
        summaries.append(
            {
                "quiz_version_id": quiz_id,
                "title": version["title"],
                "visibility": version["visibility"],
                "archived": version["archived_at"] is not None,
                "question_count": version["question_count"],
                "attempt_count": len(selected),
                "completion_count": _completion_count(selected),
                "missing_count": missing_count if filters.includes_missing else 0,
                "status_counts": status_counts,
                "score_stats": _attempt_score_stats(selected),
            }
        )
    return summaries


def _student_summary(
    selected_attempts,
    rollup_attempts,
    active_students,
    quiz_versions,
    filters,
):
    selected_by_student = _group_by(selected_attempts, "student_id")
    rollup_by_student = _group_by(rollup_attempts, "student_id")
    students_by_id = {
        student["id"]: student for student in active_students
    }
    for attempt in selected_attempts + rollup_attempts:
        students_by_id.setdefault(
            attempt["student_id"],
            {
                "id": attempt["student_id"],
                "identifier": attempt["student_identifier"],
                "status": attempt["student_status"],
            },
        )

    quiz_version_ids = {version["id"] for version in quiz_versions}
    summaries = []
    for student_id, student in sorted(
        students_by_id.items(),
        key=lambda item: item[1]["identifier"],
    ):
        selected = selected_by_student.get(student_id, [])
        attempted_quiz_ids = {
            attempt["quiz_version_id"]
            for attempt in rollup_by_student.get(student_id, [])
        }
        missing_count = (
            len(quiz_version_ids - attempted_quiz_ids)
            if student["status"] == "active" and filters.includes_missing
            else 0
        )
        status_counts = _status_counts(selected)
        if filters.includes_missing:
            status_counts["missing"] = missing_count
        completed_quiz_ids = {
            attempt["quiz_version_id"]
            for attempt in selected
            if attempt["status"] in COMPLETED_STATUSES
        }
        score_stats = _attempt_score_stats(selected)
        summaries.append(
            {
                "student_identifier": student["identifier"],
                "student_status": student["status"],
                "attempt_count": len(selected),
                "completion_count": _completion_count(selected),
                "completion_rate": _percent(
                    len(completed_quiz_ids),
                    len(quiz_version_ids),
                ),
                "missing_count": missing_count,
                "status_counts": status_counts,
                "average_score_percent": score_stats["average_percent"],
                "score_stats": score_stats,
            }
        )
    return summaries


def _item_analysis(question_rows, option_rows):
    options_by_question = defaultdict(list)
    for option in option_rows:
        options_by_question[option["quiz_version_question_id"]].append(option)

    items = {}
    selected_counts = defaultdict(lambda: defaultdict(int))
    for row in question_rows:
        question_id = row["quiz_version_question_id"]
        item = items.setdefault(question_id, _empty_item(row))
        item["attempt_count"] += 1
        if row["answer_id"] is None:
            item["unanswered_count"] += 1
        if row["snapshot_question_type"] == "multiple_choice":
            if row["is_correct"]:
                item["correct_count"] += 1
            selected_option_id = row["selected_quiz_version_option_id"]
            if selected_option_id is not None:
                selected_counts[question_id][selected_option_id] += 1
        if row["snapshot_question_type"] == "written":
            response = (row["written_response"] or "").strip()
            if response:
                item["written_grading_status"]["saved_count"] += 1
            if row["answer_id"] is not None and row["points_awarded"] is None:
                item["written_grading_status"]["ungraded_count"] += 1
                if row["attempt_status"] == "expired":
                    item["written_grading_status"]["expired_ungraded_count"] += 1
            if row["points_awarded"] is not None:
                item["written_grading_status"]["graded_count"] += 1

    for question_id, item in items.items():
        item["percent_correct"] = _percent(
            item["correct_count"],
            item["attempt_count"],
        )
        item["distractor_counts"] = [
            {
                "option_id": option["id"],
                "option_text": option["option_text"],
                "is_correct": bool(option["is_correct"]),
                "selected_count": selected_counts[question_id].get(option["id"], 0),
            }
            for option in options_by_question.get(question_id, [])
        ]

    return sorted(
        items.values(),
        key=_item_performance_sort_key,
    )


def _item_performance_sort_key(item):
    percent_correct = item["percent_correct"]
    return (
        percent_correct is None,
        percent_correct if percent_correct is not None else 101,
        -item["unanswered_count"],
        -item["attempt_count"],
        item["quiz_title"],
        item["position"],
    )


def _answer_dimension_rollups(question_rows):
    topics = defaultdict(_empty_dimension)
    tags = defaultdict(_empty_dimension)
    lesson_blocks = defaultdict(_empty_dimension)
    source_lessons = defaultdict(_empty_dimension)
    source_readings = defaultdict(_empty_dimension)
    difficulties = defaultdict(_empty_dimension)
    question_types = defaultdict(_empty_dimension)

    for row in question_rows:
        points_possible = _float_or_none(row["points_possible"])
        points_awarded = _float_or_none(row["points_awarded"])
        if points_possible is None or points_possible <= 0 or points_awarded is None:
            continue
        _add_dimension(topics[row["snapshot_topic"] or "unspecified"], row)
        _add_dimension(
            difficulties[str(row["snapshot_difficulty_level"] or "unspecified")],
            row,
        )
        _add_dimension(
            question_types[row["snapshot_question_type"] or "unspecified"],
            row,
        )
        for tag in _snapshot_tags(row["snapshot_tags_json"]):
            _add_dimension(tags[tag], row)
        _add_dimension(
            lesson_blocks[row["snapshot_lesson_block"] or "unspecified"],
            row,
        )
        _add_dimension(
            source_lessons[
                row["snapshot_specific_source_lesson"] or "unspecified"
            ],
            row,
        )
        _add_dimension(
            source_readings[
                row["snapshot_specific_source_reading"] or "unspecified"
            ],
            row,
        )

    return (
        _dimension_records(topics, "topic"),
        _dimension_records(tags, "tag"),
        {
            "lesson_blocks": _dimension_records(lesson_blocks, "lesson_block"),
            "specific_source_lessons": _dimension_records(
                source_lessons,
                "specific_source_lesson",
            ),
            "specific_source_readings": _dimension_records(
                source_readings,
                "specific_source_reading",
            ),
        },
        _dimension_records(difficulties, "difficulty_level"),
        _dimension_records(question_types, "question_type"),
    )


def _add_dimension(bucket, row):
    bucket["answer_count"] += 1
    bucket["points_awarded"] += float(row["points_awarded"])
    bucket["points_possible"] += float(row["points_possible"])


def _dimension_records(buckets, value_key):
    records = []
    for value, bucket in buckets.items():
        points_possible = bucket["points_possible"]
        records.append(
            {
                value_key: value,
                "answer_count": bucket["answer_count"],
                "points_awarded": _rounded(bucket["points_awarded"]),
                "points_possible": _rounded(points_possible),
                "average_percent": _percent(
                    bucket["points_awarded"],
                    points_possible,
                ),
            }
        )
    return sorted(records, key=lambda row: (row["average_percent"] is None, row[value_key]))


def _strongest_dimensions(rows):
    return sorted(
        rows,
        key=lambda row: (
            row["average_percent"] is not None,
            row["average_percent"] or -1,
            row["answer_count"],
        ),
        reverse=True,
    )[:5]


def _weakest_dimensions(rows):
    return sorted(
        rows,
        key=lambda row: (
            row["average_percent"] if row["average_percent"] is not None else -1,
            -row["answer_count"],
        ),
    )[:5]


def _strengths_weaknesses(
    topic_rollups,
    tag_rollups,
    source_rollups,
    difficulty_rollups,
    question_type_rollups,
    item_analysis,
):
    return {
        "dimension_groups": [
            _dimension_strength_group("Topics", "topic", topic_rollups),
            _dimension_strength_group("Tags", "tag", tag_rollups),
            _dimension_strength_group(
                "Source lessons",
                "specific_source_lesson",
                source_rollups["specific_source_lessons"],
            ),
            _dimension_strength_group(
                "Source readings",
                "specific_source_reading",
                source_rollups["specific_source_readings"],
            ),
            _dimension_strength_group(
                "Difficulty levels",
                "difficulty_level",
                difficulty_rollups,
            ),
            _dimension_strength_group(
                "Question types",
                "question_type",
                question_type_rollups,
            ),
        ],
        "item_strengths": _strongest_items(item_analysis),
        "item_weaknesses": _weakest_items(item_analysis),
    }


def _dimension_strength_group(label, value_key, rows):
    return {
        "label": label,
        "value_key": value_key,
        "strengths": _strongest_dimensions(rows),
        "weaknesses": _weakest_dimensions(rows),
    }


def _strongest_items(items):
    return sorted(
        items,
        key=lambda item: (
            item["percent_correct"] is not None,
            item["percent_correct"] or -1,
            item["attempt_count"],
        ),
        reverse=True,
    )[:5]


def _weakest_items(items):
    return sorted(
        items,
        key=lambda item: (
            item["percent_correct"] if item["percent_correct"] is not None else -1,
            -item["attempt_count"],
            item["quiz_title"],
            item["position"],
        ),
    )[:5]


def _strongest_students(summaries):
    return sorted(
        summaries,
        key=lambda row: (
            row["average_score_percent"] is not None,
            row["average_score_percent"] or -1,
            row["completion_rate"] or 0,
        ),
        reverse=True,
    )[:5]


def _weakest_students(summaries):
    return sorted(
        summaries,
        key=lambda row: (
            row["average_score_percent"]
            if row["average_score_percent"] is not None
            else -1,
            row["completion_rate"] or 0,
        ),
    )[:5]


def _visualization_metrics(
    class_summary,
    quiz_summary,
    student_summary,
    topic_rollups,
    tag_rollups,
    item_analysis,
):
    return {
        "status_by_quiz": [
            {
                "quiz_version_id": quiz["quiz_version_id"],
                "title": quiz["title"],
                "status_counts": quiz["status_counts"],
            }
            for quiz in quiz_summary
        ],
        "score_distribution": class_summary["score_stats"]["distribution"],
        "quiz_average_bars": sorted(
            [
                {
                    "quiz_version_id": quiz["quiz_version_id"],
                    "title": quiz["title"],
                    "average_percent": quiz["score_stats"]["average_percent"],
                    "attempt_count": quiz["attempt_count"],
                }
                for quiz in quiz_summary
            ],
            key=lambda row: (
                row["average_percent"] is None,
                row["average_percent"] if row["average_percent"] is not None else 101,
                row["title"],
            ),
        ),
        "completion_funnel": [
            {
                "stage": "assigned",
                "count": class_summary["expected_student_quiz_pairs"],
            },
            {"stage": "started", "count": class_summary["selected_attempt_count"]},
            {"stage": "completed", "count": class_summary["completion_count"]},
            {
                "stage": "graded",
                "count": class_summary["status_counts"].get("graded", 0),
            },
            {"stage": "missing", "count": class_summary["missing_count"]},
        ],
        "topic_heatmap": topic_rollups,
        "tag_heatmap": tag_rollups,
        "item_difficulty_scatter": [
            {
                "quiz_version_question_id": item["quiz_version_question_id"],
                "quiz_title": item["quiz_title"],
                "source_qid": item["snapshot_source_qid"],
                "question_type": item["question_type"],
                "question_stem": item["question_stem"],
                "attempt_count": item["attempt_count"],
                "percent_correct": item["percent_correct"],
                "unanswered_count": item["unanswered_count"],
                "options": item["distractor_counts"],
                "written_grading_status": item["written_grading_status"],
            }
            for item in item_analysis
        ],
        "distractor_charts": [
            {
                "quiz_version_question_id": item["quiz_version_question_id"],
                "source_qid": item["snapshot_source_qid"],
                "options": item["distractor_counts"],
            }
            for item in item_analysis
            if item["distractor_counts"]
        ],
        "written_grading_status": _written_grading_status(item_analysis),
        "student_progress_matrix": _student_progress_matrix(student_summary),
        "attempt_timing_by_quiz": [
            {
                "quiz_version_id": quiz["quiz_version_id"],
                "title": quiz["title"],
                "in_progress": quiz["status_counts"].get("in_progress", 0),
                "expired": quiz["status_counts"].get("expired", 0),
                "completed": quiz["completion_count"],
                "missing": quiz["missing_count"],
            }
            for quiz in quiz_summary
        ],
    }


def _metric_catalog(
    attempts,
    selected_attempts,
    rollup_attempts,
    active_students,
    quiz_versions,
    student_summary,
    topic_rollups,
    tag_rollups,
    source_rollups,
    difficulty_rollups,
    question_type_rollups,
    item_analysis,
    filters,
):
    active_student_ids = {student["id"] for student in active_students}
    repeated_expirations = [
        {
            "student_identifier": student["student_identifier"],
            "expired_count": student["status_counts"].get("expired", 0),
        }
        for student in student_summary
        if student["status_counts"].get("expired", 0) > 1
    ]
    missing_clusters = [
        {
            "student_identifier": student["student_identifier"],
            "missing_count": student["missing_count"],
        }
        for student in student_summary
        if student["missing_count"] > 0
    ]
    return {
        "completion": {
            "active_student_count": len(active_students),
            "quiz_version_count": len(quiz_versions),
            "selected_attempt_count": len(selected_attempts),
            "missing_count": sum(
                student["missing_count"] for student in student_summary
            ),
            "in_progress_count": _count_status(selected_attempts, "in_progress"),
            "expired_count": _count_status(selected_attempts, "expired"),
            "needs_grading_count": _count_status(selected_attempts, "needs_grading"),
        },
        "score_statistics": _attempt_score_stats(selected_attempts),
        "retakes": _retake_metrics(attempts, filters),
        "per_student": {
            "strongest": _strongest_students(student_summary),
            "weakest": _weakest_students(student_summary),
            "missing_clusters": missing_clusters,
            "repeated_expirations": repeated_expirations,
            "outliers": _student_outliers(student_summary),
        },
        "per_dimension": {
            "topics": topic_rollups,
            "tags": tag_rollups,
            "source_lessons": source_rollups["specific_source_lessons"],
            "source_readings": source_rollups["specific_source_readings"],
            "lesson_blocks": source_rollups["lesson_blocks"],
            "difficulty_levels": difficulty_rollups,
            "question_types": question_type_rollups,
        },
        "per_item": {
            "blank_rate": _item_blank_rates(item_analysis),
            "distractors": [
                item for item in item_analysis if item["distractor_counts"]
            ],
            "written_grading_status": _written_grading_status(item_analysis),
        },
        "templates": _template_metrics(quiz_versions, selected_attempts),
        "source_material_coverage": {
            "lesson_block_count": len(source_rollups["lesson_blocks"]),
            "source_lesson_count": len(source_rollups["specific_source_lessons"]),
            "source_reading_count": len(source_rollups["specific_source_readings"]),
            "lesson_blocks": source_rollups["lesson_blocks"],
            "source_lessons": source_rollups["specific_source_lessons"],
            "source_readings": source_rollups["specific_source_readings"],
        },
        "operational": {
            "ungraded_written_answers": _written_grading_status(item_analysis)[
                "ungraded_count"
            ],
            "expired_ungraded_written_answers": _written_grading_status(item_analysis)[
                "expired_ungraded_count"
            ],
            "stale_in_progress_attempts": _count_status(
                selected_attempts,
                "in_progress",
            ),
            "voided_attempts": _count_status(attempts, "voided"),
            "result_release": _result_release_metrics(quiz_versions),
            "active_students_with_attempts": len(
                {
                    attempt["student_id"]
                    for attempt in rollup_attempts
                    if attempt["student_id"] in active_student_ids
                }
            ),
        },
    }


def _written_grading_status(item_analysis):
    totals = {
        "saved_count": 0,
        "graded_count": 0,
        "ungraded_count": 0,
        "expired_ungraded_count": 0,
    }
    for item in item_analysis:
        for key, value in item["written_grading_status"].items():
            totals[key] += value
    return totals


def _student_progress_matrix(student_summary):
    return [
        {
            "student_identifier": student["student_identifier"],
            "status_counts": student["status_counts"],
            "completion_rate": student["completion_rate"],
            "average_score_percent": student["average_score_percent"],
        }
        for student in student_summary
    ]


def _retake_metrics(attempts, filters):
    candidates = [
        attempt
        for attempt in attempts
        if (filters.include_voided or attempt["status"] != "voided")
        and (not filters.quiz_version_ids or attempt["quiz_version_id"] in filters.quiz_version_ids)
    ]
    grouped = defaultdict(list)
    for attempt in candidates:
        grouped[(attempt["student_id"], attempt["quiz_version_id"])].append(attempt)
    retake_groups = [
        sorted(group, key=lambda attempt: (attempt["attempt_number"], attempt["id"]))
        for group in grouped.values()
        if len(group) > 1
    ]
    improvements = []
    for group in retake_groups:
        scored = [
            _attempt_percent(attempt)
            for attempt in group
            if _attempt_percent(attempt) is not None
        ]
        if len(scored) >= 2:
            improvements.append(scored[-1] - scored[0])
    return {
        "retake_pair_count": len(retake_groups),
        "retake_attempt_count": sum(len(group) - 1 for group in retake_groups),
        "average_improvement_percent": (
            _rounded(sum(improvements) / len(improvements)) if improvements else None
        ),
    }


def _student_outliers(student_summary):
    scored = [
        student["average_score_percent"]
        for student in student_summary
        if student["average_score_percent"] is not None
    ]
    if not scored:
        return []
    average = sum(scored) / len(scored)
    return [
        {
            "student_identifier": student["student_identifier"],
            "average_score_percent": student["average_score_percent"],
            "completion_rate": student["completion_rate"],
        }
        for student in student_summary
        if student["average_score_percent"] is not None
        and (
            student["average_score_percent"] < average - 20
            or student["average_score_percent"] > average + 20
        )
    ]


def _item_blank_rates(item_analysis):
    return [
        {
            "quiz_version_question_id": item["quiz_version_question_id"],
            "source_qid": item["snapshot_source_qid"],
            "question_type": item["question_type"],
            "blank_rate": _percent(item["unanswered_count"], item["attempt_count"]),
            "unanswered_count": item["unanswered_count"],
            "attempt_count": item["attempt_count"],
        }
        for item in item_analysis
    ]


def _template_metrics(quiz_versions, selected_attempts):
    attempts_by_quiz = _group_by(selected_attempts, "quiz_version_id")
    grouped = defaultdict(lambda: {"generated_version_count": 0, "attempts": []})
    for version in quiz_versions:
        template_id = version["template_id"] or "none"
        grouped[template_id]["template_id"] = template_id
        grouped[template_id]["generated_version_count"] += 1
        grouped[template_id]["attempts"].extend(attempts_by_quiz.get(version["id"], []))
    rows = []
    for template_id, bucket in grouped.items():
        rows.append(
            {
                "template_id": template_id,
                "generated_version_count": bucket["generated_version_count"],
                "attempt_count": len(bucket["attempts"]),
                "score_stats": _attempt_score_stats(bucket["attempts"]),
            }
        )
    return sorted(rows, key=lambda row: str(row["template_id"]))


def _result_release_metrics(quiz_versions):
    return {
        "released_count": sum(1 for version in quiz_versions if version["results_released_at"]),
        "not_released_count": sum(
            1 for version in quiz_versions if not version["results_released_at"]
        ),
    }


def _count_status(attempts, status):
    return sum(1 for attempt in attempts if attempt["status"] == status)


def _attempt_score_stats(attempts):
    percents = []
    raw_scores = []
    for attempt in attempts:
        score = _float_or_none(attempt["score"])
        max_score = _float_or_none(attempt["max_score"])
        if score is None or max_score is None or max_score <= 0:
            continue
        raw_scores.append(score)
        percents.append(score / max_score * 100)

    stats = _score_stats(percents)
    stats["average_score"] = _rounded(sum(raw_scores) / len(raw_scores)) if raw_scores else None
    return stats


def _attempt_percent(attempt):
    score = _float_or_none(attempt["score"])
    max_score = _float_or_none(attempt["max_score"])
    if score is None or max_score is None or max_score <= 0:
        return None
    return score / max_score * 100


def _score_stats(values):
    distribution = {label: 0 for label, _minimum, _maximum in SCORE_BUCKETS}
    for value in values:
        for label, minimum, maximum in SCORE_BUCKETS:
            if minimum <= value < maximum:
                distribution[label] += 1
                break
    return {
        "scored_count": len(values),
        "average_percent": _rounded(sum(values) / len(values)) if values else None,
        "median_percent": _rounded(median(values)) if values else None,
        "min_percent": _rounded(min(values)) if values else None,
        "max_percent": _rounded(max(values)) if values else None,
        "distribution": distribution,
    }


def _status_counts(attempts):
    counts = {status: 0 for status in METRIC_STATUS_ORDER}
    for attempt in attempts:
        counts[attempt["status"]] += 1
    return counts


def _completion_count(attempts):
    return sum(1 for attempt in attempts if attempt["status"] in COMPLETED_STATUSES)


def _group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def _empty_item(row):
    return {
        "quiz_version_question_id": row["quiz_version_question_id"],
        "quiz_version_id": row["quiz_version_id"],
        "quiz_title": row["quiz_title"],
        "position": row["position"],
        "source_question_id": row["source_question_id"],
        "snapshot_source_qid": row["snapshot_source_qid"],
        "question_type": row["snapshot_question_type"],
        "question_stem": row["snapshot_question_stem"],
        "topic": row["snapshot_topic"],
        "tags": _snapshot_tags(row["snapshot_tags_json"]),
        "lesson_block": row["snapshot_lesson_block"],
        "specific_source_lesson": row["snapshot_specific_source_lesson"],
        "specific_source_reading": row["snapshot_specific_source_reading"],
        "attempt_count": 0,
        "unanswered_count": 0,
        "correct_count": 0,
        "percent_correct": None,
        "distractor_counts": [],
        "written_grading_status": {
            "saved_count": 0,
            "graded_count": 0,
            "ungraded_count": 0,
            "expired_ungraded_count": 0,
        },
    }


def _student_detail_attempt(attempt, questions):
    return {
        "attempt_id": attempt["id"],
        "quiz_version_id": attempt["quiz_version_id"],
        "quiz_title": attempt["quiz_title"],
        "quiz_visibility": attempt["quiz_visibility"],
        "quiz_archived": attempt["quiz_archived_at"] is not None,
        "attempt_number": attempt["attempt_number"],
        "status": attempt["status"],
        "started_at": attempt["started_at"],
        "deadline_at": attempt["deadline_at"],
        "submitted_at": attempt["submitted_at"],
        "expired_at": attempt["expired_at"],
        "voided_at": attempt["voided_at"],
        "graded_at": attempt["graded_at"],
        "score": attempt["score"],
        "max_score": attempt["max_score"],
        "questions": questions,
    }


def _student_detail_question(row, options=None):
    options = options or []
    answer_options = [
        {
            "id": option["id"],
            "option_text": option["option_text"],
            "is_correct": bool(option["is_correct"]),
        }
        for option in options
    ]
    correct_option = next(
        (option for option in answer_options if option["is_correct"]),
        None,
    )
    answer = {
        "answer_id": row["answer_id"],
        "selected_option_id": row["selected_quiz_version_option_id"],
        "selected_option_text": row["selected_option_text"],
        "correct_option_id": correct_option["id"] if correct_option else None,
        "correct_option_text": correct_option["option_text"] if correct_option else None,
        "is_correct": bool(row["is_correct"]) if row["is_correct"] is not None else None,
        "written_response": row["written_response"],
        "points_awarded": row["points_awarded"],
        "points_possible": row["points_possible"],
        "saved_at": row["saved_at"],
        "graded_at": row["answer_graded_at"],
        "graded_by": row["graded_by"],
    }
    return {
        "quiz_version_question_id": row["quiz_version_question_id"],
        "position": row["position"],
        "source_question_id": row["source_question_id"],
        "snapshot_source_qid": row["snapshot_source_qid"],
        "question_type": row["snapshot_question_type"],
        "question_stem": row["snapshot_question_stem"],
        "topic": row["snapshot_topic"],
        "tags": _snapshot_tags(row["snapshot_tags_json"]),
        "lesson_block": row["snapshot_lesson_block"],
        "specific_source_lesson": row["snapshot_specific_source_lesson"],
        "specific_source_reading": row["snapshot_specific_source_reading"],
        "options": answer_options,
        "answer": answer,
    }


def _snapshot_tags(value):
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return []
    if isinstance(payload, dict):
        tags = payload.get("tags", [])
    else:
        tags = payload
    if not isinstance(tags, list):
        return []
    return [str(tag) for tag in tags]


def _empty_dimension():
    return {"answer_count": 0, "points_awarded": 0.0, "points_possible": 0.0}


def _percent(numerator, denominator):
    denominator = float(denominator or 0)
    if denominator <= 0:
        return None
    return _rounded(float(numerator) / denominator * 100)


def _float_or_none(value):
    if value is None:
        return None
    return float(value)


def _rounded(value):
    return round(float(value), 2)


def _dict(row):
    return dict(row)
