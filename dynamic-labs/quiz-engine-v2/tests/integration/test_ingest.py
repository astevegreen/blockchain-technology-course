import json
import os
from pathlib import Path

import pytest

from app.db import get_db
from app.ingest import IngestError, ingest_json
from app.question_pool import list_eligible_question_ids


def _quiz_fixture_dir():
    configured = os.environ.get("QUIZ_ENGINE_SAMPLE_QUIZ_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[4] / "quizes"


def _single_bank_path():
    return (
        _quiz_fixture_dir()
        / "quiz_json"
        / "bitcoin_01-BF-bitcoin_origins_and_mechanics-quiz-bank.json"
    )


def _bundle_path():
    return _quiz_fixture_dir() / "dist" / "blockchain-course-quiz-bank-bundle.json"


def _option_count(bank):
    total = 0
    for question in bank["questions"]:
        question_type = question.get("question_type", "multiple_choice")
        if question_type != "multiple_choice":
            continue
        if "correct_answer" in question or "incorrect_answers" in question:
            total += 1 + len(question.get("incorrect_answers", []))
        else:
            total += len(question.get("options", []))
    return total


def _extract_identifier(response):
    text = response.get_data(as_text=True)
    marker = '<p id="student-identifier"><code>'
    start = text.index(marker) + len(marker)
    end = text.index("</code>", start)
    return text[start:end]


def _minimal_bank(lesson_id="l04_p1_hashing_merkle_trees", questions=None):
    return {
        "lesson_id": lesson_id,
        "lesson_title": "Hashing and Merkle Trees",
        "topic": "primitives",
        "tags": ["Hashing"],
        "questions": questions
        or [
            {
                "id": "q1",
                "question_stem": "Which statement best describes hashing?",
                "correct_answer": "It maps data to a fixed-size digest.",
                "incorrect_answers": ["It decrypts ciphertext."],
                "tags": ["Merkle Trees"],
            }
        ],
    }


def _two_question_bank(lesson_id="l04_p1_hashing_merkle_trees"):
    return _minimal_bank(
        lesson_id,
        questions=[
            {
                "id": "q1",
                "question_stem": "Which statement best describes hashing?",
                "correct_answer": "It maps data to a fixed-size digest.",
                "incorrect_answers": ["It decrypts ciphertext."],
            },
            {
                "id": "q2",
                "question_stem": "Which statement best describes a Merkle tree?",
                "correct_answer": "It commits to many leaves with a root hash.",
                "incorrect_answers": ["It hides every transaction from validators."],
            },
        ],
    )


def test_real_single_bank_ingest_persists_normalized_rows_and_stays_hidden(app, client):
    raw_json = _single_bank_path().read_text(encoding="utf-8")
    source_bank = json.loads(raw_json)

    with app.app_context():
        result = ingest_json(raw_json, filename=_single_bank_path().name, actor_sub="teacher")
        db = get_db()
        bank = db.execute(
            """
            SELECT bank.*, revision.hierarchy_json, revision.source_hash
            FROM quiz_banks bank
            JOIN quiz_bank_revisions revision
              ON revision.id = bank.latest_revision_id
            WHERE bank.lesson_id = ?
            """,
            (source_bank["lesson_id"],),
        ).fetchone()
        question_count = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        option_count = db.execute("SELECT COUNT(*) FROM question_options").fetchone()[0]
        bank_tag_count = db.execute("SELECT COUNT(*) FROM bank_revision_tags").fetchone()[0]
        question_tag_count = db.execute("SELECT COUNT(*) FROM question_tags").fetchone()[0]
        audit_event = db.execute(
            """
            SELECT details_json
            FROM audit_events
            WHERE event_type = 'quiz_bank.ingested'
            """
        ).fetchone()

    assert result.status == "completed"
    assert result.successes == 1
    assert result.failures == 0
    assert bank["hidden"] == 1
    assert bank["lesson_title"] == source_bank["lesson_title"]
    assert len(bank["source_hash"]) == 64
    assert json.loads(bank["hierarchy_json"])["sections"][0]["lectures"]
    assert question_count == len(source_bank["questions"])
    assert option_count == _option_count(source_bank)
    assert bank_tag_count == len(set(source_bank["tags"]))
    assert question_tag_count > 0
    assert "question_stem" not in audit_event["details_json"]
    assert source_bank["questions"][0]["question_stem"] not in audit_event["details_json"]

    enrollment = client.post("/student/enroll")
    assert enrollment.status_code == 200
    assert _extract_identifier(enrollment).startswith("QZ-")
    response = client.get("/student/quizzes")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "No published quizzes are available" in text
    assert source_bank["lesson_title"] not in text


def test_real_bundle_ingest_creates_expected_counts_and_summary(app):
    raw_json = _bundle_path().read_text(encoding="utf-8")
    source_banks = json.loads(raw_json)
    expected_questions = sum(len(bank["questions"]) for bank in source_banks)
    expected_options = sum(_option_count(bank) for bank in source_banks)

    with app.app_context():
        result = ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")
        db = get_db()
        import_batch = db.execute(
            "SELECT status, summary_json FROM import_batches WHERE id = ?",
            (result.import_batch_id,),
        ).fetchone()
        bank_count = db.execute("SELECT COUNT(*) FROM quiz_banks").fetchone()[0]
        revision_count = db.execute("SELECT COUNT(*) FROM quiz_bank_revisions").fetchone()[0]
        question_count = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        option_count = db.execute("SELECT COUNT(*) FROM question_options").fetchone()[0]
        tagged_bank_count = db.execute(
            "SELECT COUNT(DISTINCT bank_revision_id) FROM bank_revision_tags"
        ).fetchone()[0]
        hierarchy_count = db.execute(
            """
            SELECT COUNT(*)
            FROM quiz_bank_revisions
            WHERE hierarchy_json LIKE '%"sections"%'
            """
        ).fetchone()[0]

    assert result.status == "completed"
    assert result.successes == len(source_banks)
    assert result.failures == 0
    assert len(result.bank_results) == len(source_banks)
    assert import_batch["status"] == "completed"
    assert json.loads(import_batch["summary_json"]) == {
        "schema_version": 1,
        "successes": len(source_banks),
        "failures": 0,
        "revised_questions": 0,
    }
    assert bank_count == len(source_banks)
    assert revision_count == len(source_banks)
    assert question_count == expected_questions
    assert option_count == expected_options
    assert tagged_bank_count == len(source_banks)
    assert hierarchy_count == len(source_banks)


def test_malformed_and_invalid_ingest_do_not_create_quiz_rows(app):
    with app.app_context():
        db = get_db()
        with pytest.raises(IngestError, match="Malformed JSON"):
            ingest_json("{", actor_sub="teacher")
        assert db.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0] == 0

        result = ingest_json(
            json.dumps(
                {
                    "lesson_id": "invalid_bank",
                    "lesson_title": "Invalid Bank",
                    "questions": [],
                }
            ),
            actor_sub="teacher",
        )
        assert result.status == "failed"
        assert result.successes == 0
        assert result.failures == 1
        assert db.execute("SELECT COUNT(*) FROM import_batches").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM quiz_banks").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM questions").fetchone()[0] == 0


def test_bundle_reports_per_bank_success_and_failure_without_invalid_rows(app):
    bundle = [
        _minimal_bank("l04_p1_hashing_merkle_trees"),
        {
            "lesson_id": "invalid_bank",
            "lesson_title": "Invalid Bank",
            "questions": [],
        },
    ]

    with app.app_context():
        result = ingest_json(json.dumps(bundle), actor_sub="teacher")
        db = get_db()
        lesson_ids = [
            row["lesson_id"]
            for row in db.execute("SELECT lesson_id FROM quiz_banks").fetchall()
        ]

    assert result.status == "partial_failure"
    assert result.successes == 1
    assert result.failures == 1
    assert result.bank_results[0].success is True
    assert result.bank_results[1].success is False
    assert lesson_ids == ["l04_p1_hashing_merkle_trees"]


def test_reingesting_same_lesson_is_additive_by_default(app):
    with app.app_context():
        first_result = ingest_json(json.dumps(_minimal_bank()), actor_sub="teacher")
        second_result = ingest_json(
            json.dumps(
                _minimal_bank(
                    questions=[
                        {
                            "id": "q1",
                            "question_stem": "Which updated statement best describes hashing?",
                            "correct_answer": "It maps data to a fixed-size digest.",
                            "incorrect_answers": ["It decrypts ciphertext."],
                        }
                    ]
                )
            ),
            actor_sub="teacher",
        )
        db = get_db()
        rows = db.execute(
            """
            SELECT id, source_qid, status, revises_question_id
            FROM questions
            ORDER BY id
            """
        ).fetchall()
        revision_count = db.execute(
            "SELECT COUNT(*) FROM quiz_bank_revisions"
        ).fetchone()[0]
        latest_revision_id = db.execute(
            "SELECT latest_revision_id FROM quiz_banks WHERE lesson_id = ?",
            ("l04_p1_hashing_merkle_trees",),
        ).fetchone()[0]

    assert first_result.bank_results[0].revised_question_count == 0
    assert second_result.bank_results[0].revised_question_count == 0
    assert revision_count == 2
    assert latest_revision_id == second_result.bank_results[0].revision_id
    assert [row["source_qid"] for row in rows] == ["q1", "q1"]
    assert [row["status"] for row in rows] == ["active", "active"]
    assert [row["revises_question_id"] for row in rows] == [None, None]


def test_accept_all_additive_bundle_commits_without_per_question_review(app):
    lesson_a = "l04_p1_hashing_merkle_trees"
    lesson_b = "l05_p1_more_hashing"

    with app.app_context():
        ingest_json(json.dumps([_minimal_bank(lesson_a), _minimal_bank(lesson_b)]))
        result = ingest_json(
            json.dumps(
                [
                    _minimal_bank(
                        lesson_a,
                        questions=[
                            {
                                "id": "q1",
                                "question_stem": "Updated hashing question",
                                "correct_answer": "Digest",
                                "incorrect_answers": ["Ciphertext"],
                            }
                        ],
                    ),
                    _minimal_bank(
                        lesson_b,
                        questions=[
                            {
                                "id": "q1",
                                "question_stem": "Updated second hashing question",
                                "correct_answer": "Digest",
                                "incorrect_answers": ["Ciphertext"],
                            }
                        ],
                    ),
                ]
            ),
            revision_mappings={},
        )
        db = get_db()
        active_question_count = db.execute(
            "SELECT COUNT(*) FROM questions WHERE status = 'active'"
        ).fetchone()[0]
        revision_count = db.execute(
            "SELECT COUNT(*) FROM quiz_bank_revisions"
        ).fetchone()[0]

    assert result.status == "completed"
    assert result.successes == 2
    assert result.failures == 0
    assert [bank.revised_question_count for bank in result.bank_results] == [0, 0]
    assert active_question_count == 4
    assert revision_count == 4


def test_explicit_revision_mapping_supersedes_only_mapped_question(app):
    lesson_id = "l04_p1_hashing_merkle_trees"

    with app.app_context():
        ingest_json(json.dumps(_two_question_bank(lesson_id)), actor_sub="teacher")
        db = get_db()
        original_rows = db.execute(
            """
            SELECT id, source_qid
            FROM questions
            ORDER BY id
            """
        ).fetchall()
        original_q1_id = original_rows[0]["id"]
        original_q2_id = original_rows[1]["id"]

        result = ingest_json(
            json.dumps(
                _minimal_bank(
                    lesson_id,
                    questions=[
                        {
                            "id": "q1",
                            "question_stem": "Updated hashing question",
                            "correct_answer": "Digest",
                            "incorrect_answers": ["Ciphertext"],
                        },
                        {
                            "id": "q3",
                            "question_stem": "New additive question",
                            "correct_answer": "New answer",
                            "incorrect_answers": ["Old answer"],
                        },
                    ],
                )
            ),
            actor_sub="teacher",
            revision_mappings={lesson_id: {"q1": original_q1_id}},
        )
        rows = db.execute(
            """
            SELECT id, source_qid, status, revises_question_id, superseded_at
            FROM questions
            ORDER BY id
            """
        ).fetchall()
        eligible_ids = list_eligible_question_ids(lesson_ids=[lesson_id])

    assert result.status == "completed"
    assert result.bank_results[0].revised_question_count == 1
    assert rows[0]["id"] == original_q1_id
    assert rows[0]["status"] == "superseded"
    assert rows[0]["superseded_at"] is not None
    assert rows[1]["id"] == original_q2_id
    assert rows[1]["status"] == "active"
    assert rows[2]["source_qid"] == "q1"
    assert rows[2]["status"] == "active"
    assert rows[2]["revises_question_id"] == original_q1_id
    assert rows[3]["source_qid"] == "q3"
    assert rows[3]["revises_question_id"] is None
    assert original_q1_id not in eligible_ids
    assert original_q2_id in eligible_ids
    assert rows[2]["id"] in eligible_ids
    assert rows[3]["id"] in eligible_ids


def test_revision_mapping_must_target_same_logical_bank(app):
    lesson_a = "l04_p1_hashing_merkle_trees"
    lesson_b = "l05_p1_more_hashing"

    with app.app_context():
        ingest_json(json.dumps(_minimal_bank(lesson_a)), actor_sub="teacher")
        ingest_json(json.dumps(_minimal_bank(lesson_b)), actor_sub="teacher")
        db = get_db()
        other_bank_question_id = db.execute(
            """
            SELECT question.id
            FROM questions question
            JOIN quiz_banks bank
              ON bank.id = question.quiz_bank_id
            WHERE bank.lesson_id = ?
            """,
            (lesson_b,),
        ).fetchone()[0]

        result = ingest_json(
            json.dumps(
                _minimal_bank(
                    lesson_a,
                    questions=[
                        {
                            "id": "q1",
                            "question_stem": "Updated hashing question",
                            "correct_answer": "Digest",
                            "incorrect_answers": ["Ciphertext"],
                        }
                    ],
                )
            ),
            actor_sub="teacher",
            revision_mappings={lesson_a: {"q1": other_bank_question_id}},
        )
        lesson_a_revision_count = db.execute(
            """
            SELECT COUNT(*)
            FROM quiz_bank_revisions revision
            JOIN quiz_banks bank
              ON bank.id = revision.quiz_bank_id
            WHERE bank.lesson_id = ?
            """,
            (lesson_a,),
        ).fetchone()[0]

    assert result.status == "failed"
    assert result.successes == 0
    assert result.failures == 1
    assert "different quiz bank" in result.bank_results[0].error
    assert lesson_a_revision_count == 1


def test_historical_quiz_snapshots_and_attempts_survive_reingest(app):
    lesson_id = "l04_p1_hashing_merkle_trees"
    snapshot_json = (
        '{"schema_version": 1, "criteria": {}, "eligible_pool_size": 1, '
        '"quota_allocations": {}, "coverage_allocations": {}, "random_seed": "seed", '
        '"bank_revision_ids": [], "selected_question_ids": []}'
    )
    order_json = '{"schema_version": 1, "order": [1]}'
    tags_json = '{"schema_version": 1, "tags": []}'

    with app.app_context():
        ingest_json(json.dumps(_minimal_bank(lesson_id)), actor_sub="teacher")
        db = get_db()
        original_question = db.execute(
            "SELECT id, question_stem FROM questions WHERE source_qid = 'q1'"
        ).fetchone()
        student_id = db.execute(
            """
            INSERT INTO students (identifier, status, source, created_at)
            VALUES ('QZ-HISTORY-0001', 'active', 'open_registration', CURRENT_TIMESTAMP)
            """
        ).lastrowid
        quiz_version_id = db.execute(
            """
            INSERT INTO quiz_versions (
                title,
                generation_snapshot_json,
                created_at
            )
            VALUES ('Historical Quiz', ?, CURRENT_TIMESTAMP)
            """,
            (snapshot_json,),
        ).lastrowid
        quiz_version_question_id = db.execute(
            """
            INSERT INTO quiz_version_questions (
                quiz_version_id,
                source_question_id,
                position,
                snapshot_source_qid,
                snapshot_question_type,
                snapshot_question_stem,
                snapshot_difficulty_level,
                snapshot_topic,
                snapshot_tags_json
            )
            VALUES (?, ?, 1, 'q1', 'multiple_choice', ?, 1, 'primitives', ?)
            """,
            (quiz_version_id, original_question["id"], original_question["question_stem"], tags_json),
        ).lastrowid
        attempt_id = db.execute(
            """
            INSERT INTO attempts (
                quiz_version_id,
                student_id,
                attempt_number,
                status,
                started_at,
                question_order_json,
                option_order_json
            )
            VALUES (?, ?, 1, 'in_progress', CURRENT_TIMESTAMP, ?, ?)
            """,
            (quiz_version_id, student_id, order_json, order_json),
        ).lastrowid
        answer_id = db.execute(
            """
            INSERT INTO attempt_answers (
                attempt_id,
                quiz_version_question_id,
                written_response,
                points_possible
            )
            VALUES (?, ?, 'historical answer', 1)
            """,
            (attempt_id, quiz_version_question_id),
        ).lastrowid

        ingest_json(
            json.dumps(
                _minimal_bank(
                    lesson_id,
                    questions=[
                        {
                            "id": "q1",
                            "question_stem": "Updated hashing question",
                            "correct_answer": "Digest",
                            "incorrect_answers": ["Ciphertext"],
                        }
                    ],
                )
            ),
            actor_sub="teacher",
            revision_mappings={lesson_id: {"q1": original_question["id"]}},
        )
        historical_snapshot = db.execute(
            """
            SELECT source_question_id, snapshot_question_stem
            FROM quiz_version_questions
            WHERE id = ?
            """,
            (quiz_version_question_id,),
        ).fetchone()
        historical_answer = db.execute(
            "SELECT attempt_id, written_response FROM attempt_answers WHERE id = ?",
            (answer_id,),
        ).fetchone()
        original_after_reingest = db.execute(
            "SELECT question_stem, status FROM questions WHERE id = ?",
            (original_question["id"],),
        ).fetchone()

    assert historical_snapshot["source_question_id"] == original_question["id"]
    assert historical_snapshot["snapshot_question_stem"] == original_question["question_stem"]
    assert historical_answer["attempt_id"] == attempt_id
    assert historical_answer["written_response"] == "historical answer"
    assert original_after_reingest["question_stem"] == original_question["question_stem"]
    assert original_after_reingest["status"] == "superseded"


def test_instructor_ingest_routes_require_auth_and_accept_json_body(app, client):
    source_bank = json.loads(_single_bank_path().read_text(encoding="utf-8"))

    unauthorized = client.get("/instructor/ingest")
    assert unauthorized.status_code == 401

    response = client.post(
        "/instructor/api/ingest",
        json=source_bank,
        headers={"X-Test-Instructor": "teacher"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "completed"
    assert payload["successes"] == 1
    assert payload["failures"] == 0
    assert payload["banks"][0]["lesson_id"] == source_bank["lesson_id"]

    plan_response = client.post(
        "/instructor/api/ingest/plan",
        json={"quiz_json": source_bank},
        headers={"X-Test-Instructor": "teacher"},
    )
    plan_payload = plan_response.get_json()
    assert plan_response.status_code == 200
    assert plan_payload["banks"][0]["existing_bank_id"] is not None
    assert plan_payload["banks"][0]["questions"][0]["candidates"]

    form_response = client.post(
        "/instructor/ingest",
        data={"quiz_json": json.dumps(_minimal_bank("l05_p1_more_hashing"))},
        headers={"X-Test-Instructor": "teacher"},
    )
    assert form_response.status_code == 200
    assert "Import batch" in form_response.get_data(as_text=True)

    malformed = client.post(
        "/instructor/api/ingest",
        data="{",
        content_type="application/json",
        headers={"X-Test-Instructor": "teacher"},
    )
    assert malformed.status_code == 400
    assert malformed.get_json()["error"] == "Malformed JSON"
