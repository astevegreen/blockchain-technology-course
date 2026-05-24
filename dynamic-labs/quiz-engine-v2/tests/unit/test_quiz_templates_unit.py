import json

import pytest

from app.ingest import ingest_json
from app.quiz_templates import (
    TemplateError,
    archive_template,
    build_eligible_pool_query,
    create_template,
    duplicate_template,
    list_templates,
    normalize_criteria,
    preview_eligible_pool,
    update_template,
)


def _bank():
    return {
        "lesson_id": "l04_p1_hashing_merkle_trees",
        "lesson_title": "Hashing and Merkle Trees",
        "topic": "primitives",
        "tags": ["Hashing"],
        "questions": [
            {
                "id": "q1",
                "question_stem": "Which statement best describes hashing?",
                "correct_answer": "It maps data to a fixed-size digest.",
                "incorrect_answers": ["It decrypts ciphertext."],
                "difficulty_level": 2,
                "topic": "primitives",
                "tags": ["Merkle Trees"],
            },
            {
                "id": "q2",
                "question_stem": "Which statement best describes Bitcoin?",
                "correct_answer": "It uses proof-of-work consensus.",
                "incorrect_answers": ["It requires a central bank."],
                "difficulty_level": 4,
                "topic": "bitcoin",
                "tags": ["Proof of Work"],
            },
        ],
        "hierarchy": {
            "sections": [
                {
                    "id": "sec_hashing",
                    "title": "Hashing",
                    "lectures": [
                        {
                            "id": "lec_merkle",
                            "title": "Merkle trees",
                            "question_ids": ["q1", "q2"],
                        }
                    ],
                }
            ]
        },
    }


def _template_payload(**overrides):
    payload = {
        "title": "Hashing Template",
        "description": "Template description",
        "criteria": {
            "lesson_ids": ["l04_p1_hashing_merkle_trees"],
            "topics": ["primitives"],
            "tags": ["Merkle Trees"],
            "tag_match_mode": "any",
            "hierarchy_sections": ["sec_hashing"],
            "hierarchy_lectures": ["lec_merkle"],
            "difficulty_min": 1,
            "difficulty_max": 3,
            "question_types": ["multiple_choice"],
            "quotas": {"tags": {"Merkle Trees": 1}},
            "require_topic_coverage": True,
        },
        "question_count": 1,
        "selection_policy": "random",
        "timer_minutes": 20,
        "attempt_limit": 2,
        "result_policy": "score_after_grading",
        "question_order_mode": "random_per_attempt",
        "option_order_mode": "random_per_attempt",
        "default_available_offset_minutes": 15,
        "default_available_duration_minutes": 60,
    }
    payload.update(overrides)
    return payload


def test_normalize_criteria_validates_and_canonicalizes_values():
    criteria = normalize_criteria(
        {
            "tags": ["Merkle Trees", "merkle trees"],
            "excluded_topics": ["legacy", "legacy"],
            "excluded_tags": ["Draft Notes", "draft-notes"],
            "difficulty_min": "2",
            "difficulty_max": "4",
            "question_types": ["multiple_choice"],
            "quotas": {
                "topics": {"bitcoin": "1"},
                "tags": {"Proof of Work": 2},
                "lessons": {"l04_p1_hashing_merkle_trees": 1},
            },
        }
    )

    assert criteria["schema_version"] == 1
    assert criteria["tags"] == ["merkle-trees"]
    assert criteria["excluded_topics"] == ["legacy"]
    assert criteria["excluded_tags"] == ["draft-notes"]
    assert criteria["difficulty_min"] == 2
    assert criteria["difficulty_max"] == 4
    assert criteria["quotas"] == {
        "topics": {"bitcoin": 1},
        "tags": {"proof-of-work": 2},
        "lesson_ids": {"l04_p1_hashing_merkle_trees": 1},
    }


def test_normalize_criteria_accepts_source_rules_with_tag_quotas():
    criteria = normalize_criteria(
        {
            "schema_version": 2,
            "lesson_ids": ["l04_p1_hashing_merkle_trees"],
            "tags": ["fallback"],
            "excluded_tags": ["fallback-excluded"],
            "question_types": ["multiple_choice"],
            "source_rules": [
                {
                    "lesson_id": "l04_p1_hashing_merkle_trees",
                    "filter_mode": "override",
                    "question_count": "2",
                    "selection_policy": "random",
                    "criteria": {
                        "tags": ["Reading", "Slides"],
                        "excluded_topics": ["Deprecated"],
                        "excluded_tags": ["Draft"],
                        "tag_match_mode": "any",
                        "question_types": ["multiple_choice"],
                        "quotas": {"tags": {"Reading": "1", "Slides": 1}},
                    },
                }
            ],
        }
    )

    assert criteria["schema_version"] == 2
    assert criteria["excluded_tags"] == ["fallback-excluded"]
    assert criteria["source_rules"][0]["question_count"] == 2
    assert criteria["source_rules"][0]["criteria"]["tags"] == ["reading", "slides"]
    assert criteria["source_rules"][0]["criteria"]["excluded_topics"] == [
        "Deprecated"
    ]
    assert criteria["source_rules"][0]["criteria"]["excluded_tags"] == ["draft"]
    assert criteria["source_rules"][0]["criteria"]["quotas"]["tags"] == {
        "reading": 1,
        "slides": 1,
    }


def test_normalize_criteria_rejects_invalid_source_rule_quota_total():
    with pytest.raises(TemplateError, match="exceeds source question_count"):
        normalize_criteria(
            {
                "schema_version": 2,
                "lesson_ids": ["l04_p1_hashing_merkle_trees"],
                "question_types": ["multiple_choice"],
                "source_rules": [
                    {
                        "lesson_id": "l04_p1_hashing_merkle_trees",
                        "filter_mode": "override",
                        "question_count": 1,
                        "criteria": {
                            "question_types": ["multiple_choice"],
                            "quotas": {"tags": {"reading": 1, "slides": 1}},
                        },
                    }
                ],
            }
        )


def test_template_order_modes_are_persisted_and_validated(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        template = create_template(
            _template_payload(
                question_order_mode="random_once",
                option_order_mode="fixed",
            ),
            actor_sub="teacher",
        )

        updated = update_template(
            template["id"],
            _template_payload(
                title="Updated Order Modes",
                question_order_mode="fixed",
                option_order_mode="random_once",
            ),
            actor_sub="teacher",
        )

        with pytest.raises(TemplateError, match="question_order_mode"):
            create_template(
                _template_payload(question_order_mode="alphabetical"),
                actor_sub="teacher",
            )

    assert template["question_order_mode"] == "random_once"
    assert template["option_order_mode"] == "fixed"
    assert updated["question_order_mode"] == "fixed"
    assert updated["option_order_mode"] == "random_once"


@pytest.mark.parametrize(
    "criteria, message",
    (
        ({"tag_match_mode": "some"}, "tag_match_mode"),
        ({"difficulty_min": 5, "difficulty_max": 2}, "difficulty range"),
        ({"question_types": ["essay"]}, "question_types"),
        ({"quotas": {"topics": {"bitcoin": 0}}}, "quotas.topics"),
    ),
)
def test_normalize_criteria_rejects_invalid_values(criteria, message):
    with pytest.raises(TemplateError, match=message):
        normalize_criteria(criteria)


def test_template_timer_values_below_one_mean_no_timer(app):
    with app.app_context():
        negative = create_template(
            _template_payload(timer_minutes="-1"),
            actor_sub="teacher",
        )
        zero = create_template(
            _template_payload(title="Zero Timer Template", timer_minutes="0"),
            actor_sub="teacher",
        )
        blank = create_template(
            _template_payload(title="Blank Timer Template", timer_minutes=""),
            actor_sub="teacher",
        )

    assert negative["timer_minutes"] is None
    assert zero["timer_minutes"] is None
    assert blank["timer_minutes"] is None


def test_eligible_pool_query_includes_filters():
    criteria = normalize_criteria(
        {
            "lesson_ids": ["l04_p1_hashing_merkle_trees"],
            "topics": ["primitives"],
            "tags": ["Merkle Trees", "Hashing"],
            "excluded_topics": ["bitcoin"],
            "excluded_tags": ["Proof of Work"],
            "tag_match_mode": "all",
            "hierarchy_sections": ["sec_hashing"],
            "hierarchy_lectures": ["lec_merkle"],
            "difficulty_min": 1,
            "difficulty_max": 3,
            "question_types": ["multiple_choice"],
        }
    )

    sql, params = build_eligible_pool_query(criteria)

    assert "bank.lesson_id IN" in sql
    assert "question.topic IN" in sql
    assert "question.topic NOT IN" in sql
    assert "question.content_section_id IN" in sql
    assert "question.content_lecture_id IN" in sql
    assert "question.difficulty_level BETWEEN" in sql
    assert "ORDER BY question.bank_revision_id, question.source_qid, question.id" in sql
    assert params.count("merkle-trees") == 2
    assert params.count("hashing") == 2
    assert params.count("Proof of Work") == 0
    assert params.count("proof-of-work") == 2
    assert "bitcoin" in params


def test_preview_reports_counts_and_quota_coverage_warnings(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

        ok_preview = preview_eligible_pool(
            {
                "lesson_ids": ["l04_p1_hashing_merkle_trees"],
                "tags": ["Hashing"],
                "tag_match_mode": "any",
                "question_types": ["multiple_choice"],
                "quotas": {"topics": {"primitives": 1}},
                "require_topic_coverage": True,
            },
            2,
        )
        warning_preview = preview_eligible_pool(
            {
                "lesson_ids": ["l04_p1_hashing_merkle_trees"],
                "topics": ["primitives", "ethereum"],
                "question_types": ["multiple_choice"],
                "quotas": {"tags": {"missing-tag": 1}},
                "require_topic_coverage": True,
            },
            3,
        )
        excluded_preview = preview_eligible_pool(
            {
                "lesson_ids": ["l04_p1_hashing_merkle_trees"],
                "excluded_topics": ["bitcoin"],
                "excluded_tags": ["proof-of-work"],
                "question_types": ["multiple_choice"],
            },
            1,
        )

    assert ok_preview["eligible_pool_size"] == 2
    assert ok_preview["counts"]["by_topic"] == {"bitcoin": 1, "primitives": 1}
    assert ok_preview["warnings"] == []
    assert excluded_preview["eligible_pool_size"] == 1
    assert excluded_preview["counts"]["by_topic"] == {"primitives": 1}
    warning_codes = {warning["code"] for warning in warning_preview["warnings"]}
    assert "insufficient_pool" in warning_codes
    assert "unsatisfied_quota" in warning_codes
    assert "unsatisfied_topic_coverage" in warning_codes
    insufficient = next(
        warning
        for warning in warning_preview["warnings"]
        if warning["code"] == "insufficient_pool"
    )
    assert insufficient["eligible_pool_size"] == 1
    assert insufficient["question_count"] == 3
    assert insufficient["filter_summary"]["topics"] == ["primitives", "ethereum"]


def test_preview_source_warnings_identify_source_lesson(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        preview = preview_eligible_pool(
            {
                "schema_version": 2,
                "lesson_ids": ["l04_p1_hashing_merkle_trees"],
                "difficulty_min": 1,
                "difficulty_max": 5,
                "question_types": ["multiple_choice"],
                "source_rules": [
                    {
                        "lesson_id": "l04_p1_hashing_merkle_trees",
                        "filter_mode": "override",
                        "question_count": 1,
                        "criteria": {
                            "tags": ["missing-tag"],
                            "tag_match_mode": "any",
                            "difficulty_min": 1,
                            "difficulty_max": 5,
                            "question_types": ["multiple_choice"],
                        },
                    }
                ],
            },
            1,
        )

    assert preview["source_rules"][0]["eligible_pool_size"] == 0
    warning = preview["warnings"][0]
    assert warning["code"] == "insufficient_pool"
    assert warning["source_lesson_id"] == "l04_p1_hashing_merkle_trees"
    assert warning["eligible_pool_size"] == 0
    assert warning["question_count"] == 1
    assert warning["filter_summary"]["tags"] == ["missing-tag"]


def test_template_crud_duplicate_and_archive(app):
    with app.app_context():
        template = create_template(_template_payload(), actor_sub="teacher")
        updated = update_template(
            template["id"],
            {"title": "Updated Template", "question_count": 2},
            actor_sub="teacher",
        )
        duplicated = duplicate_template(template["id"], actor_sub="teacher")
        archive_template(template["id"], actor_sub="teacher")
        visible = list_templates()
        all_templates = list_templates(include_archived=True)

    assert template["title"] == "Hashing Template"
    assert updated["title"] == "Updated Template"
    assert updated["question_count"] == 2
    assert duplicated["title"] == "Updated Template Copy"
    assert [item["id"] for item in visible] == [duplicated["id"]]
    assert {item["id"] for item in all_templates} == {template["id"], duplicated["id"]}
