import json

import pytest

from app.db import get_db
from app.generation import generate_quiz_version
from app.import_retirements import (
    ImportRetirementError,
    apply_import_retirement,
    normalize_import_retirement_request,
    preview_import_retirement,
)
from app.ingest import ingest_json
from app.question_pool import list_eligible_question_ids
from app.quiz_templates import create_template


def _bank(lesson_id="retirement_lesson", questions=None, tags=None):
    return {
        "lesson_id": lesson_id,
        "lesson_title": "Retirement Lesson",
        "topic": "bitcoin",
        "tags": tags or ["Retirement Bank"],
        "questions": questions
        or [
            {
                "id": "q1",
                "question_stem": "Question one?",
                "correct_answer": "One",
                "incorrect_answers": ["Two"],
                "tags": ["Retire Me"],
            },
            {
                "id": "q2",
                "question_stem": "Question two?",
                "correct_answer": "Two",
                "incorrect_answers": ["One"],
                "tags": ["Keep Me"],
            },
        ],
    }


def test_normalize_import_retirement_request_dedupes_and_normalizes_tags():
    request = normalize_import_retirement_request(
        "tag",
        " Retire Me,\nretire-me,,Keep Me ",
        reason="  code import cleanup  ",
    )

    assert request.mode == "tag"
    assert request.targets == ("retire-me", "keep-me")
    assert request.reason == "code import cleanup"


def test_preview_by_lesson_reports_banks_templates_and_hash(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        template = create_template(
            {
                "title": "Retirement Template",
                "criteria": {
                    "lesson_ids": ["retirement_lesson"],
                    "question_types": ["multiple_choice"],
                },
                "question_count": 2,
            },
            actor_sub="teacher",
        )

        preview = preview_import_retirement("lesson", ["retirement_lesson"])

    assert preview["mode"] == "lesson"
    assert preview["targets"] == ["retirement_lesson"]
    assert preview["selection_hash"]
    assert preview["counts"]["questions"] == 2
    assert preview["counts"]["banks"] == 1
    assert preview["counts"]["revisions"] == 1
    assert preview["banks"][0]["will_archive"] is True
    assert preview["revisions"][0]["will_archive"] is True
    assert preview["active_template_references"][0]["id"] == template["id"]
    assert preview["active_template_references"][0]["would_drop_below_question_count"]
    assert "Question one" not in json.dumps(preview)


def test_apply_by_tag_retires_partial_revision_without_archiving_bank(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        db = get_db()
        q1_id = db.execute(
            "SELECT id FROM questions WHERE source_qid = 'q1'"
        ).fetchone()["id"]
        q2_id = db.execute(
            "SELECT id FROM questions WHERE source_qid = 'q2'"
        ).fetchone()["id"]
        preview = preview_import_retirement("tag", ["retire-me"])

        result = apply_import_retirement(
            "tag",
            ["retire-me"],
            selection_hash=preview["selection_hash"],
            reason="replace generated source",
            actor_sub="teacher",
        )
        eligible_ids = list_eligible_question_ids(lesson_ids=["retirement_lesson"])
        bank = db.execute(
            "SELECT archived FROM quiz_banks WHERE lesson_id = 'retirement_lesson'"
        ).fetchone()
        revision = db.execute("SELECT status FROM quiz_bank_revisions").fetchone()
        retirement = db.execute(
            "SELECT reason FROM question_retirements WHERE question_id = ?",
            (q1_id,),
        ).fetchone()
        audit = db.execute(
            """
            SELECT details_json
            FROM audit_events
            WHERE event_type = 'quiz_bank_import.retired'
            """
        ).fetchone()

    assert result["status"] == "retired"
    assert result["preview"]["counts"]["questions"] == 1
    assert q1_id not in eligible_ids
    assert q2_id in eligible_ids
    assert bank["archived"] == 0
    assert revision["status"] == "active"
    assert retirement["reason"] == "replace generated source"
    assert "Question one" not in audit["details_json"]


def test_lesson_retirement_is_idempotent_and_reingest_reactivates_bank(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        db = get_db()
        original_question_ids = set(list_eligible_question_ids(lesson_ids=["retirement_lesson"]))
        preview = preview_import_retirement("lesson", ["retirement_lesson"])

        first = apply_import_retirement(
            "lesson",
            ["retirement_lesson"],
            selection_hash=preview["selection_hash"],
            actor_sub="teacher",
        )
        second = apply_import_retirement(
            "lesson",
            ["retirement_lesson"],
            selection_hash=preview["selection_hash"],
            actor_sub="teacher",
        )
        after_retirement_ids = list_eligible_question_ids(
            lesson_ids=["retirement_lesson"]
        )
        archived_bank = db.execute(
            "SELECT archived FROM quiz_banks WHERE lesson_id = 'retirement_lesson'"
        ).fetchone()["archived"]
        archived_revision_count = db.execute(
            "SELECT COUNT(*) FROM quiz_bank_revisions WHERE status = 'archived'"
        ).fetchone()[0]
        retirement_count = db.execute(
            "SELECT COUNT(*) FROM question_retirements"
        ).fetchone()[0]

        ingest_json(
            json.dumps(
                _bank(
                    questions=[
                        {
                            "id": "q3",
                            "question_stem": "Replacement question?",
                            "correct_answer": "Replacement",
                            "incorrect_answers": ["Original"],
                            "tags": ["Replacement"],
                        }
                    ]
                )
            ),
            actor_sub="teacher",
        )
        reactivated_bank = db.execute(
            "SELECT archived FROM quiz_banks WHERE lesson_id = 'retirement_lesson'"
        ).fetchone()["archived"]
        reingested_eligible_ids = set(
            list_eligible_question_ids(lesson_ids=["retirement_lesson"])
        )

    assert first["status"] == "retired"
    assert second["status"] == "no_op"
    assert original_question_ids
    assert after_retirement_ids == []
    assert archived_bank == 1
    assert archived_revision_count == 1
    assert retirement_count == len(original_question_ids)
    assert reactivated_bank == 0
    assert reingested_eligible_ids
    assert not (original_question_ids & reingested_eligible_ids)


def test_retirement_hash_mismatch_is_rejected(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

        with pytest.raises(ImportRetirementError, match="selection changed"):
            apply_import_retirement(
                "lesson",
                ["retirement_lesson"],
                selection_hash="not-the-preview-hash",
                actor_sub="teacher",
            )


def test_retired_source_question_keeps_generated_snapshot_readable(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = generate_quiz_version(
            {
                "title": "Snapshot Before Retirement",
                "criteria": {
                    "lesson_ids": ["retirement_lesson"],
                    "question_types": ["multiple_choice"],
                },
                "question_count": 1,
                "random_seed": "retirement-snapshot",
            },
            actor_sub="teacher",
        )
        snapshot_stem = version["questions"][0]["snapshot_question_stem"]
        source_question_id = version["questions"][0]["source_question_id"]
        preview = preview_import_retirement("lesson", ["retirement_lesson"])
        apply_import_retirement(
            "lesson",
            ["retirement_lesson"],
            selection_hash=preview["selection_hash"],
            actor_sub="teacher",
        )
        stored_snapshot = get_db().execute(
            """
            SELECT source_question_id, snapshot_question_stem
            FROM quiz_version_questions
            WHERE quiz_version_id = ?
            """,
            (version["id"],),
        ).fetchone()

    assert stored_snapshot["source_question_id"] == source_question_id
    assert stored_snapshot["snapshot_question_stem"] == snapshot_stem
