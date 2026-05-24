import json
import os
from pathlib import Path

import pytest

from app.ingest import (
    IngestError,
    effective_tags,
    ingest_json,
    infer_topic_from_lesson_id,
    normalize_bank,
    normalize_revision_mappings,
    normalize_tag,
    normalize_tags,
    plan_revision_candidates,
    parse_ingest_json,
    revision_plans_to_dict,
)


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


def _valid_mc_bank(**overrides):
    bank = {
        "lesson_id": "l04_p1_hashing_merkle_trees",
        "lesson_title": "Hashing and Merkle Trees",
        "topic": "primitives",
        "questions": [
            {
                "id": "q1",
                "question_stem": "Which statement best describes hashing?",
                "correct_answer": "It maps data to a fixed-size digest.",
                "incorrect_answers": ["It decrypts ciphertext."],
            }
        ],
    }
    bank.update(overrides)
    return bank


def test_parser_and_normalizer_accept_real_quiz_bank(app):
    raw_json = _single_bank_path().read_text(encoding="utf-8")

    with app.app_context():
        parsed = parse_ingest_json(raw_json)
        bank = normalize_bank(parsed[0])

    assert len(parsed) == 1
    assert bank.lesson_id == "bitcoin_01_bf_bitcoin_origins_and_mechanics"
    assert bank.lesson_title == "Bitcoin - Origins and Mechanics"
    assert bank.topic == "bitcoin"
    assert "proof-of-work" in bank.tags
    assert len(bank.source_hash) == 64
    assert len(bank.questions) == 13
    assert bank.questions[0].question_type == "multiple_choice"
    assert sum(option.is_correct for option in bank.questions[0].options) == 1
    assert len(bank.questions[0].options) == 4
    assert bank.questions[0].content_section_id == "sec_bitcoin"
    assert bank.questions[0].content_lecture_id.startswith(
        "lec_bitcoin_origins_and_mechanics"
    )
    assert bank.questions[0].specific_source_lesson


def test_parser_and_normalizer_accept_real_bundle(app):
    raw_json = _bundle_path().read_text(encoding="utf-8")

    with app.app_context():
        parsed = parse_ingest_json(raw_json)
        normalized = [normalize_bank(bank) for bank in parsed]

    assert len(normalized) >= 30
    assert sum(len(bank.questions) for bank in normalized) >= 400
    assert {bank.topic for bank in normalized} <= {
        "intro",
        "primitives",
        "bitcoin",
        "ethereum",
        "forensics",
        "conclusion",
        "other",
    }


def test_synthetic_written_legacy_topics_tags_and_provenance(app):
    raw_bank = {
        "lesson_id": "l04_p1_hashing_merkle_trees",
        "lesson_title": "Hashing and Merkle Trees",
        "topic": "not-a-topic",
        "tags": ["Merkle Trees", "merkle trees", "  "],
        "questions": [
            {
                "question_type": "written",
                "question_stem": "Explain why collision resistance matters.",
                "difficulty": 4,
                "tags": ["Written Response"],
                "specific_source": {
                    "lesson": "slides: hashing",
                    "reading": "reading: merkle trees",
                },
            },
            {
                "id": "legacy",
                "question_stem": "Which option is correct?",
                "options": ["Wrong", "Correct", "Also wrong"],
                "correct_index": 1,
                "topic": "ethereum",
                "specific_source_lesson": "flat lesson",
                "specific_source_reading": "flat reading",
            },
            {
                "id": "fallback-topic",
                "question_stem": "Which option uses the bank topic?",
                "correct_answer": "This one",
                "incorrect_answers": ["Not this one"],
                "topic": "invalid",
            },
        ],
        "hierarchy": {
            "sections": [
                {
                    "id": "sec_hashing",
                    "title": "Hashing",
                    "lectures": [
                        {
                            "id": "lec_collision",
                            "title": "Collision resistance",
                            "question_ids": ["q1", "legacy"],
                        }
                    ],
                }
            ]
        },
    }

    with app.app_context():
        bank = normalize_bank(raw_bank)

    assert bank.topic == "primitives"
    assert bank.tags == ("merkle-trees",)
    assert bank.questions[0].source_qid == "q1"
    assert bank.questions[0].question_type == "written"
    assert bank.questions[0].options == ()
    assert bank.questions[0].topic == "primitives"
    assert bank.questions[0].difficulty_level == 4
    assert bank.questions[0].tags == ("written-response",)
    assert bank.questions[0].specific_source_lesson == "slides: hashing"
    assert bank.questions[0].specific_source_reading == "reading: merkle trees"
    assert bank.questions[1].topic == "ethereum"
    assert [option.is_correct for option in bank.questions[1].options] == [
        False,
        True,
        False,
    ]
    assert bank.questions[1].specific_source_lesson == "flat lesson"
    assert bank.questions[2].topic == "primitives"
    assert bank.questions[2].content_lecture_id == "lec_collision"


def test_invalid_hierarchy_falls_back_to_default(app):
    raw_bank = _valid_mc_bank(
        hierarchy={
            "sections": [
                {
                    "id": "sec_bad",
                    "title": "Bad",
                    "lectures": [
                        {
                            "id": "lec_bad",
                            "title": "Bad",
                            "question_ids": ["not-a-real-question-id"],
                        }
                    ],
                }
            ]
        }
    )

    with app.app_context():
        bank = normalize_bank(raw_bank)

    assert bank.hierarchy_json["sections"][0]["id"] == "sec_all_content"
    assert bank.questions[0].content_section_id == "sec_all_content"
    assert bank.questions[0].content_lecture_id == "lec_all_questions"


def test_missing_fields_malformed_json_and_limits_fail(app, app_factory):
    with app.app_context():
        with pytest.raises(IngestError, match="Malformed JSON"):
            parse_ingest_json("{")
        with pytest.raises(IngestError, match="lesson_title"):
            normalize_bank({"lesson_id": "x", "questions": []})
        with pytest.raises(IngestError, match="correct_answer"):
            normalize_bank(
                _valid_mc_bank(
                    lesson_id="l04",
                    lesson_title="Hashing",
                    questions=[
                        {
                            "id": "q1",
                            "question_stem": "Missing answer fields",
                            "incorrect_answers": ["Wrong"],
                        }
                    ]
                )
            )

    limited_app = app_factory(INGEST_MAX_FIELD_CHARS=12)
    with limited_app.app_context():
        with pytest.raises(IngestError, match="question_stem"):
            normalize_bank(
                _valid_mc_bank(
                    lesson_id="l04",
                    lesson_title="Hashing",
                    questions=[
                        {
                            "id": "q1",
                            "question_stem": "This field is too long",
                            "correct_answer": "Correct",
                            "incorrect_answers": ["Wrong"],
                        }
                    ]
                )
            )


def test_bundle_duplicate_lesson_ids_are_rejected(app):
    bundle = [_valid_mc_bank(), _valid_mc_bank()]

    with app.app_context():
        with pytest.raises(IngestError, match="duplicate lesson_id"):
            parse_ingest_json(json.dumps(bundle))


def test_tag_and_topic_helpers(app):
    with app.app_context():
        assert normalize_tag("Merkle Trees!!") == "merkle-trees"
        assert normalize_tags(["Merkle Trees", "merkle_trees", "PoW"]) == (
            "merkle-trees",
            "pow",
        )

    assert effective_tags(("bank", "shared"), ("question", "shared")) == (
        "bank",
        "shared",
        "question",
    )
    assert infer_topic_from_lesson_id("introduction_01_in_course_welcome") == "intro"
    assert infer_topic_from_lesson_id("primitives_02_cp_hashing") == "primitives"
    assert infer_topic_from_lesson_id("permissioned_ledger_01_pc") == "primitives"


def test_revision_mapping_normalization():
    assert normalize_revision_mappings({"lesson": {"q1": "42"}}) == {
        "lesson": {"q1": 42}
    }

    with pytest.raises(IngestError, match="revision_mappings must be an object"):
        normalize_revision_mappings([])
    with pytest.raises(IngestError, match="target question IDs"):
        normalize_revision_mappings({"lesson": {"q1": "not-an-id"}})


def test_revision_candidate_planner_suggests_matches_without_committing(app):
    original_bank = _valid_mc_bank()
    revised_bank = _valid_mc_bank(
        questions=[
            {
                "id": "q1",
                "question_stem": "Which statement best describes hashing?",
                "correct_answer": "It maps data to a fixed-size digest.",
                "incorrect_answers": ["It decrypts ciphertext."],
            },
            {
                "id": "q2",
                "question_stem": "Which statement best describes encryption?",
                "correct_answer": "It transforms plaintext into ciphertext.",
                "incorrect_answers": ["It always creates a public ledger."],
            },
        ]
    )

    with app.app_context():
        ingest_json(json.dumps(original_bank), actor_sub="teacher")
        plans = plan_revision_candidates(json.dumps(revised_bank))
        payload = revision_plans_to_dict(plans)

    bank_plan = payload["banks"][0]
    assert bank_plan["lesson_id"] == "l04_p1_hashing_merkle_trees"
    assert bank_plan["existing_bank_id"] is not None
    assert bank_plan["existing_question_count"] == 1
    q1_candidates = bank_plan["questions"][0]["candidates"]
    q2_candidates = bank_plan["questions"][1]["candidates"]
    assert q1_candidates[0]["source_qid"] == "q1"
    assert "source_qid" in q1_candidates[0]["match_reasons"]
    assert "question_stem_exact" in q1_candidates[0]["match_reasons"]
    assert q2_candidates == []
