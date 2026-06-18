import json

import pytest

from app.db import get_db
from app.metrics.filters import MetricsFilterError, parse_metrics_filters
from app.metrics.rollups import build_dashboard_metrics, get_student_detail


def test_parse_metrics_filters_defaults_and_explicit_controls():
    default_filters = parse_metrics_filters({})
    explicit_filters = parse_metrics_filters(
        {
            "mode": "all",
            "statuses": "graded,expired,needs-grading,voided",
            "quiz_version_id": "7",
        }
    )

    assert default_filters.mode == "latest"
    assert "voided" not in default_filters.statuses
    assert default_filters.include_voided is False
    assert explicit_filters.mode == "all"
    assert explicit_filters.include_voided is True
    assert explicit_filters.quiz_version_id == 7
    assert explicit_filters.quiz_version_ids == (7,)
    assert explicit_filters.statuses == (
        "expired",
        "voided",
        "needs_grading",
        "graded",
    )
    multi_quiz_filters = parse_metrics_filters(
        {"quiz_version_id": ["7", "9"], "statuses": "graded"}
    )
    assert multi_quiz_filters.quiz_version_id is None
    assert multi_quiz_filters.quiz_version_ids == (7, 9)


def test_parse_metrics_filters_rejects_unknown_status():
    with pytest.raises(MetricsFilterError, match="unknown status"):
        parse_metrics_filters({"status": "done"})


def test_latest_dashboard_rollup_excludes_voided_and_counts_missing(app):
    with app.app_context():
        fixture = _seed_metrics_fixture(get_db())
        metrics = build_dashboard_metrics(parse_metrics_filters({}))
        all_metrics = build_dashboard_metrics(
            parse_metrics_filters({"mode": "all", "include_voided": "1"})
        )

    assert metrics["class_summary"]["selected_attempt_count"] == 2
    assert metrics["class_summary"]["missing_count"] == 1
    assert metrics["class_summary"]["status_counts"]["graded"] == 1
    assert metrics["class_summary"]["status_counts"]["expired"] == 1
    assert metrics["class_summary"]["status_counts"]["voided"] == 0
    assert metrics["class_summary"]["score_stats"]["average_percent"] == 75.0
    assert metrics["class_summary"]["score_stats"]["distribution"]["70-79"] == 1
    assert metrics["quiz_summary"][0]["completion_count"] == 1
    assert metrics["student_summary"][0]["student_identifier"] == fixture["student_one"]
    assert metrics["student_summary"][0]["average_score_percent"] == 75.0
    assert all_metrics["class_summary"]["selected_attempt_count"] == 4
    assert all_metrics["class_summary"]["status_counts"]["voided"] == 1


def test_item_topic_tag_source_rollups_and_student_detail(app):
    with app.app_context():
        fixture = _seed_metrics_fixture(get_db())
        metrics = build_dashboard_metrics(parse_metrics_filters({}))
        detail = get_student_detail(
            fixture["student_one"],
            parse_metrics_filters({"mode": "all", "include_voided": "1"}),
        )

    mc_item = next(
        item for item in metrics["item_analysis"] if item["question_type"] == "multiple_choice"
    )
    written_item = next(
        item for item in metrics["item_analysis"] if item["question_type"] == "written"
    )

    assert mc_item["attempt_count"] == 2
    assert mc_item["correct_count"] == 1
    assert mc_item["percent_correct"] == 50.0
    assert mc_item["distractor_counts"][0]["is_correct"] is True
    assert written_item["written_grading_status"]["graded_count"] == 1
    assert written_item["written_grading_status"]["ungraded_count"] == 1
    assert written_item["written_grading_status"]["expired_ungraded_count"] == 1
    assert metrics["topic_rollups"][0]["topic"] == "bitcoin"
    assert metrics["topic_rollups"][0]["average_percent"] == 50.0
    assert metrics["difficulty_rollups"][0]["difficulty_level"] == "2"
    assert metrics["question_type_rollups"][0]["question_type"] == "multiple_choice"
    assert {row["tag"] for row in metrics["tag_rollups"]} == {
        "block-validation",
        "difficulty-core",
    }
    assert metrics["source_rollups"]["lesson_blocks"][0]["lesson_block"] == "Block A"
    assert metrics["strengths_weaknesses"]["dimension_groups"]
    assert metrics["strengths_weaknesses"]["item_weaknesses"]
    assert metrics["visualizations"]["completion_funnel"][0]["stage"] == "assigned"
    assert metrics["visualizations"]["score_distribution"]["70-79"] == 1
    assert metrics["visualizations"]["written_grading_status"]["expired_ungraded_count"] == 1
    assert metrics["metric_catalog"]["completion"]["expired_count"] == 1
    assert metrics["metric_catalog"]["per_item"]["blank_rate"][0]["blank_rate"] == 0.0
    assert metrics["metric_catalog"]["source_material_coverage"]["source_lesson_count"] == 1
    assert metrics["metric_catalog"]["operational"]["expired_ungraded_written_answers"] == 1
    assert detail["student_identifier"] == fixture["student_one"]
    assert detail["attempt_count"] == 3
    assert detail["strengths_weaknesses"]["dimension_groups"]
    assert detail["attempts"][0]["quiz_archived"] is True
    assert detail["attempts"][0]["questions"][0]["source_question_id"] == fixture["mc_source_question_id"]


def test_item_analysis_sorts_worst_first_and_scatter_includes_preview_payload(app):
    with app.app_context():
        _seed_item_sorting_fixture(get_db())
        metrics = build_dashboard_metrics(parse_metrics_filters({}))

    assert [item["snapshot_source_qid"] for item in metrics["item_analysis"]] == [
        "hard",
        "easy",
    ]
    assert [item["percent_correct"] for item in metrics["item_analysis"]] == [0.0, 100.0]
    scatter = metrics["visualizations"]["item_difficulty_scatter"]
    assert [row["source_qid"] for row in scatter] == ["hard", "easy"]
    assert scatter[0]["question_stem"] == "Hard sorting question."
    assert scatter[0]["options"][1]["option_text"] == "Tempting miss"
    assert scatter[0]["options"][1]["selected_count"] == 2


def _seed_metrics_fixture(conn):
    now = "2026-05-20T00:00:00+00:00"
    student_one = "QZ-MET-0001"
    student_two = "QZ-MET-0002"
    student_three = "QZ-MET-0003"
    student_ids = {}
    for identifier in (student_one, student_two, student_three):
        student_ids[identifier] = conn.execute(
            """
            INSERT INTO students (identifier, status, source, created_at)
            VALUES (?, 'active', 'open_registration', ?)
            """,
            (identifier, now),
        ).lastrowid

    bank_id = conn.execute(
        """
        INSERT INTO quiz_banks (
            lesson_id,
            lesson_title,
            topic,
            created_at,
            updated_at
        )
        VALUES ('metrics_lesson', 'Metrics Lesson', 'bitcoin', ?, ?)
        """,
        (now, now),
    ).lastrowid
    revision_id = conn.execute(
        """
        INSERT INTO quiz_bank_revisions (
            quiz_bank_id,
            lesson_title,
            topic,
            hierarchy_json,
            status,
            created_at
        )
        VALUES (?, 'Metrics Lesson', 'bitcoin', ?, 'active', ?)
        """,
        (bank_id, json.dumps({"schema_version": 1, "sections": []}), now),
    ).lastrowid
    conn.execute(
        "UPDATE quiz_banks SET latest_revision_id = ? WHERE id = ?",
        (revision_id, bank_id),
    )
    mc_source_question_id = _insert_source_question(
        conn,
        bank_id,
        revision_id,
        "mc1",
        "multiple_choice",
        "Pick the valid block.",
        now,
    )
    written_source_question_id = _insert_source_question(
        conn,
        bank_id,
        revision_id,
        "wr1",
        "written",
        "Explain confirmations.",
        now,
    )

    version_id = conn.execute(
        """
        INSERT INTO quiz_versions (
            title,
            generation_snapshot_json,
            visibility,
            result_policy,
            question_order_policy,
            option_order_policy,
            created_at,
            archived_at
        )
        VALUES (
            'Metrics Fixture Quiz',
            ?,
            'archived',
            'score_after_grading',
            'fixed',
            'fixed',
            ?,
            ?
        )
        """,
        (json.dumps({"schema_version": 1}), now, now),
    ).lastrowid
    tags_json = json.dumps(
        {"schema_version": 1, "tags": ["difficulty-core", "block-validation"]}
    )
    mc_question_id = _insert_version_question(
        conn,
        version_id,
        mc_source_question_id,
        1,
        "mc1",
        "multiple_choice",
        "Pick the valid block.",
        tags_json,
    )
    written_question_id = _insert_version_question(
        conn,
        version_id,
        written_source_question_id,
        2,
        "wr1",
        "written",
        "Explain confirmations.",
        tags_json,
    )
    correct_option_id = conn.execute(
        """
        INSERT INTO quiz_version_options (
            quiz_version_question_id,
            option_text,
            is_correct,
            snapshot_order
        )
        VALUES (?, 'Valid block', 1, 1)
        """,
        (mc_question_id,),
    ).lastrowid
    wrong_option_id = conn.execute(
        """
        INSERT INTO quiz_version_options (
            quiz_version_question_id,
            option_text,
            is_correct,
            snapshot_order
        )
        VALUES (?, 'Invalid block', 0, 2)
        """,
        (mc_question_id,),
    ).lastrowid

    question_order_json = json.dumps(
        {"schema_version": 1, "order": [mc_question_id, written_question_id]}
    )
    option_order_json = json.dumps(
        {"schema_version": 1, "order": [correct_option_id, wrong_option_id]}
    )
    attempt_one = _insert_attempt(
        conn,
        version_id,
        student_ids[student_one],
        1,
        "graded",
        0,
        2,
        question_order_json,
        option_order_json,
        now,
    )
    _insert_mc_answer(conn, attempt_one, mc_question_id, wrong_option_id, 0, 1)
    _insert_written_answer(conn, attempt_one, written_question_id, "weak", 0, 1)

    attempt_two = _insert_attempt(
        conn,
        version_id,
        student_ids[student_one],
        2,
        "graded",
        1.5,
        2,
        question_order_json,
        option_order_json,
        now,
    )
    _insert_mc_answer(conn, attempt_two, mc_question_id, correct_option_id, 1, 1)
    _insert_written_answer(conn, attempt_two, written_question_id, "solid", 0.5, 1)

    attempt_three = _insert_attempt(
        conn,
        version_id,
        student_ids[student_one],
        3,
        "voided",
        2,
        2,
        question_order_json,
        option_order_json,
        now,
    )
    _insert_mc_answer(conn, attempt_three, mc_question_id, correct_option_id, 1, 1)
    _insert_written_answer(conn, attempt_three, written_question_id, "voided", 1, 1)

    expired_attempt = _insert_attempt(
        conn,
        version_id,
        student_ids[student_two],
        1,
        "expired",
        None,
        2,
        question_order_json,
        option_order_json,
        now,
    )
    _insert_mc_answer(conn, expired_attempt, mc_question_id, None, 0, 0)
    _insert_written_answer(
        conn,
        expired_attempt,
        written_question_id,
        "saved before expiration",
        None,
        1,
    )
    conn.commit()
    return {
        "student_one": student_one,
        "student_two": student_two,
        "student_three": student_three,
        "mc_source_question_id": mc_source_question_id,
    }


def _seed_item_sorting_fixture(conn):
    now = "2026-05-20T00:00:00+00:00"
    student_ids = {}
    for identifier in ("QZ-SORT-0001", "QZ-SORT-0002"):
        student_ids[identifier] = conn.execute(
            """
            INSERT INTO students (identifier, status, source, created_at)
            VALUES (?, 'active', 'open_registration', ?)
            """,
            (identifier, now),
        ).lastrowid

    bank_id = conn.execute(
        """
        INSERT INTO quiz_banks (
            lesson_id,
            lesson_title,
            topic,
            created_at,
            updated_at
        )
        VALUES ('sorting_lesson', 'Sorting Lesson', 'bitcoin', ?, ?)
        """,
        (now, now),
    ).lastrowid
    revision_id = conn.execute(
        """
        INSERT INTO quiz_bank_revisions (
            quiz_bank_id,
            lesson_title,
            topic,
            hierarchy_json,
            status,
            created_at
        )
        VALUES (?, 'Sorting Lesson', 'bitcoin', ?, 'active', ?)
        """,
        (bank_id, json.dumps({"schema_version": 1, "sections": []}), now),
    ).lastrowid
    conn.execute(
        "UPDATE quiz_banks SET latest_revision_id = ? WHERE id = ?",
        (revision_id, bank_id),
    )
    hard_source_question_id = _insert_source_question(
        conn,
        bank_id,
        revision_id,
        "hard",
        "multiple_choice",
        "Hard sorting question.",
        now,
    )
    easy_source_question_id = _insert_source_question(
        conn,
        bank_id,
        revision_id,
        "easy",
        "multiple_choice",
        "Easy sorting question.",
        now,
    )

    version_id = conn.execute(
        """
        INSERT INTO quiz_versions (
            title,
            generation_snapshot_json,
            visibility,
            result_policy,
            question_order_policy,
            option_order_policy,
            created_at
        )
        VALUES ('Sorting Fixture Quiz', ?, 'published', 'score_after_grading', 'fixed', 'fixed', ?)
        """,
        (json.dumps({"schema_version": 1}), now),
    ).lastrowid
    tags_json = json.dumps({"schema_version": 1, "tags": ["sorting"]})
    hard_question_id = _insert_version_question(
        conn,
        version_id,
        hard_source_question_id,
        1,
        "hard",
        "multiple_choice",
        "Hard sorting question.",
        tags_json,
    )
    easy_question_id = _insert_version_question(
        conn,
        version_id,
        easy_source_question_id,
        2,
        "easy",
        "multiple_choice",
        "Easy sorting question.",
        tags_json,
    )
    hard_correct_id = conn.execute(
        """
        INSERT INTO quiz_version_options (
            quiz_version_question_id,
            option_text,
            is_correct,
            snapshot_order
        )
        VALUES (?, 'Hard correct', 1, 1)
        """,
        (hard_question_id,),
    ).lastrowid
    hard_wrong_id = conn.execute(
        """
        INSERT INTO quiz_version_options (
            quiz_version_question_id,
            option_text,
            is_correct,
            snapshot_order
        )
        VALUES (?, 'Tempting miss', 0, 2)
        """,
        (hard_question_id,),
    ).lastrowid
    easy_correct_id = conn.execute(
        """
        INSERT INTO quiz_version_options (
            quiz_version_question_id,
            option_text,
            is_correct,
            snapshot_order
        )
        VALUES (?, 'Easy correct', 1, 1)
        """,
        (easy_question_id,),
    ).lastrowid
    easy_wrong_id = conn.execute(
        """
        INSERT INTO quiz_version_options (
            quiz_version_question_id,
            option_text,
            is_correct,
            snapshot_order
        )
        VALUES (?, 'Easy miss', 0, 2)
        """,
        (easy_question_id,),
    ).lastrowid

    question_order_json = json.dumps(
        {"schema_version": 1, "order": [hard_question_id, easy_question_id]}
    )
    option_order_json = json.dumps(
        {
            "schema_version": 1,
            "order": [hard_correct_id, hard_wrong_id, easy_correct_id, easy_wrong_id],
        }
    )
    for student_id in student_ids.values():
        attempt_id = _insert_attempt(
            conn,
            version_id,
            student_id,
            1,
            "graded",
            1,
            2,
            question_order_json,
            option_order_json,
            now,
        )
        _insert_mc_answer(conn, attempt_id, hard_question_id, hard_wrong_id, 0, 0)
        _insert_mc_answer(conn, attempt_id, easy_question_id, easy_correct_id, 1, 1)
    conn.commit()


def _insert_source_question(
    conn,
    bank_id,
    revision_id,
    source_qid,
    question_type,
    stem,
    now,
):
    return conn.execute(
        """
        INSERT INTO questions (
            quiz_bank_id,
            bank_revision_id,
            source_qid,
            question_type,
            question_stem,
            difficulty_level,
            topic,
            lesson_block,
            specific_source_lesson,
            specific_source_reading,
            content_section_id,
            content_lecture_id,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, 2, 'bitcoin', 'Block A', 'Lesson A', 'Reading A', 'sec', 'lec', 'active', ?)
        """,
        (bank_id, revision_id, source_qid, question_type, stem, now),
    ).lastrowid


def _insert_version_question(
    conn,
    version_id,
    source_question_id,
    position,
    source_qid,
    question_type,
    stem,
    tags_json,
):
    return conn.execute(
        """
        INSERT INTO quiz_version_questions (
            quiz_version_id,
            source_question_id,
            position,
            points,
            snapshot_source_qid,
            snapshot_question_type,
            snapshot_question_stem,
            snapshot_explanation,
            snapshot_difficulty_level,
            snapshot_topic,
            snapshot_tags_json,
            snapshot_lesson_block,
            snapshot_specific_source_lesson,
            snapshot_specific_source_reading
        )
        VALUES (?, ?, ?, 1, ?, ?, ?, 'Explanation', 2, 'bitcoin', ?, 'Block A', 'Lesson A', 'Reading A')
        """,
        (
            version_id,
            source_question_id,
            position,
            source_qid,
            question_type,
            stem,
            tags_json,
        ),
    ).lastrowid


def _insert_attempt(
    conn,
    version_id,
    student_id,
    attempt_number,
    status,
    score,
    max_score,
    question_order_json,
    option_order_json,
    now,
):
    return conn.execute(
        """
        INSERT INTO attempts (
            quiz_version_id,
            student_id,
            attempt_number,
            status,
            started_at,
            submitted_at,
            expired_at,
            voided_at,
            graded_at,
            score,
            max_score,
            question_order_json,
            option_order_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_id,
            student_id,
            attempt_number,
            status,
            now,
            now if status in {"graded", "needs_grading", "submitted"} else None,
            now if status == "expired" else None,
            now if status == "voided" else None,
            now if score is not None else None,
            score,
            max_score,
            question_order_json,
            option_order_json,
        ),
    ).lastrowid


def _insert_mc_answer(conn, attempt_id, question_id, option_id, is_correct, points):
    conn.execute(
        """
        INSERT INTO attempt_answers (
            attempt_id,
            quiz_version_question_id,
            selected_quiz_version_option_id,
            is_correct,
            points_awarded,
            points_possible,
            saved_at,
            graded_at
        )
        VALUES (?, ?, ?, ?, ?, 1, '2026-05-20T00:00:00+00:00', '2026-05-20T00:00:00+00:00')
        """,
        (attempt_id, question_id, option_id, is_correct, points),
    )


def _insert_written_answer(conn, attempt_id, question_id, response, points, possible):
    conn.execute(
        """
        INSERT INTO attempt_answers (
            attempt_id,
            quiz_version_question_id,
            written_response,
            points_awarded,
            points_possible,
            saved_at,
            graded_at
        )
        VALUES (?, ?, ?, ?, ?, '2026-05-20T00:00:00+00:00', ?)
        """,
        (
            attempt_id,
            question_id,
            response,
            points,
            possible,
            "2026-05-20T00:00:00+00:00" if points is not None else None,
        ),
    )
