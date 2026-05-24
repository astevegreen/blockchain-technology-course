import json

import pytest

from app.db import get_db
from app.generation import (
    GenerationError,
    generate_quiz_version,
    generate_quiz_version_from_template,
)
from app.ingest import ingest_json
from app.quiz_templates import create_template
from app.quiz_versions import QuizVersionError, validate_admin_metadata_update


def _bank():
    return {
        "lesson_id": "generation_lesson",
        "lesson_title": "Generation Lesson",
        "topic": "mixed",
        "tags": ["Generation"],
        "questions": [
            _question("q1", "Primitive easy", 1, "primitives", ["hashing"]),
            _question("q2", "Primitive medium", 3, "primitives", ["hashing"]),
            _question("q3", "Primitive hard", 5, "primitives", ["trees"]),
            _question("q4", "Bitcoin easy", 2, "bitcoin", ["pow"]),
            _question("q5", "Bitcoin medium", 3, "bitcoin", ["pow"]),
            _question("q6", "Bitcoin hard", 4, "bitcoin", ["consensus"]),
        ],
    }


def _question(source_qid, stem, difficulty, topic, tags):
    return {
        "id": source_qid,
        "question_stem": stem,
        "correct_answer": f"{stem} correct",
        "incorrect_answers": [f"{stem} distractor"],
        "difficulty_level": difficulty,
        "topic": topic,
        "tags": tags,
        "lesson_block": f"Block {source_qid}",
        "specific_source_lesson": f"slides:{source_qid}",
        "specific_source_reading": f"reading:{source_qid}",
        "explanation": f"Explanation {source_qid}",
    }


def _criteria(**overrides):
    criteria = {
        "lesson_ids": ["generation_lesson"],
        "difficulty_min": 1,
        "difficulty_max": 5,
        "question_types": ["multiple_choice"],
    }
    criteria.update(overrides)
    return criteria


def _payload(**overrides):
    payload = {
        "title": "Generated Quiz",
        "criteria": _criteria(),
        "question_count": 3,
        "selection_policy": "random",
        "random_seed": "seed-1",
    }
    payload.update(overrides)
    return payload


def test_same_seed_selects_same_questions_and_writes_snapshots(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

        first = generate_quiz_version(_payload(random_seed="repeatable"), actor_sub="teacher")
        second = generate_quiz_version(_payload(random_seed="repeatable"), actor_sub="teacher")

    assert first["id"] != second["id"]
    assert first["visibility"] == "hidden"
    assert first["generation_snapshot"]["selected_question_ids"] == second[
        "generation_snapshot"
    ]["selected_question_ids"]
    assert [question["source_question_id"] for question in first["questions"]] == first[
        "generation_snapshot"
    ]["selected_question_ids"]
    assert first["questions"][0]["snapshot_question_stem"]
    assert first["questions"][0]["options"][0]["option_text"]


def test_default_generation_uses_per_attempt_order_modes_and_shuffles_snapshot_options(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        versions = [
            generate_quiz_version(
                _payload(random_seed=f"default-order-{index}"),
                actor_sub="teacher",
            )
            for index in range(8)
        ]

    first = versions[0]
    assert first["generation_snapshot"]["question_order_mode"] == "random_per_attempt"
    assert first["generation_snapshot"]["option_order_mode"] == "random_per_attempt"
    assert first["question_order_policy"] == "random_per_attempt"
    assert first["option_order_policy"] == "random_per_attempt"
    assert any(
        question["options"] and not question["options"][0]["is_correct"]
        for version in versions
        for question in version["questions"]
    )


def test_random_once_order_mode_maps_to_fixed_attempt_policy(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = generate_quiz_version(
            _payload(
                random_seed="random-once-order",
                question_order_mode="random_once",
                option_order_mode="random_once",
            ),
            actor_sub="teacher",
        )

    assert version["generation_snapshot"]["question_order_mode"] == "random_once"
    assert version["generation_snapshot"]["option_order_mode"] == "random_once"
    assert version["question_order_policy"] == "fixed"
    assert version["option_order_policy"] == "fixed"


def test_generation_failures_write_no_partial_rows(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        before = get_db().execute("SELECT COUNT(*) FROM quiz_versions").fetchone()[0]

        with pytest.raises(GenerationError, match="eligible pool"):
            generate_quiz_version(_payload(question_count=99), actor_sub="teacher")

        after_versions = get_db().execute("SELECT COUNT(*) FROM quiz_versions").fetchone()[0]
        after_questions = get_db().execute(
            "SELECT COUNT(*) FROM quiz_version_questions"
        ).fetchone()[0]
        after_options = get_db().execute(
            "SELECT COUNT(*) FROM quiz_version_options"
        ).fetchone()[0]

    assert after_versions == before
    assert after_questions == 0
    assert after_options == 0


def test_quota_and_topic_coverage_are_enforced(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

        with pytest.raises(GenerationError, match="unsatisfied quota"):
            generate_quiz_version(
                _payload(criteria=_criteria(quotas={"tags": {"missing": 1}})),
                actor_sub="teacher",
            )

        version = generate_quiz_version(
            _payload(
                question_count=2,
                criteria=_criteria(
                    topics=["bitcoin", "primitives"],
                    require_topic_coverage=True,
                ),
            ),
            actor_sub="teacher",
        )

    selected_topics = {
        question["snapshot_topic"] for question in version["questions"]
    }
    assert selected_topics == {"bitcoin", "primitives"}
    assert set(version["generation_snapshot"]["coverage_allocations"]) == {
        "bitcoin",
        "primitives",
    }


def test_generation_excludes_topics_and_effective_tags(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = generate_quiz_version(
            _payload(
                question_count=2,
                criteria=_criteria(
                    excluded_topics=["bitcoin"],
                    excluded_tags=["trees"],
                ),
            ),
            actor_sub="teacher",
        )

    selected = version["generation_snapshot"]["selected_questions"]
    assert {question["topic"] for question in selected} == {"primitives"}
    assert all("trees" not in question["effective_tags"] for question in selected)


def test_source_rules_select_tag_quotas_within_each_source(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        version = generate_quiz_version(
            _payload(
                question_count=2,
                criteria={
                    "schema_version": 2,
                    "lesson_ids": ["generation_lesson"],
                    "difficulty_min": 1,
                    "difficulty_max": 5,
                    "question_types": ["multiple_choice"],
                    "source_rules": [
                        {
                            "lesson_id": "generation_lesson",
                            "filter_mode": "override",
                            "question_count": 2,
                            "criteria": {
                                "tags": ["hashing", "trees"],
                                "tag_match_mode": "any",
                                "difficulty_min": 1,
                                "difficulty_max": 5,
                                "question_types": ["multiple_choice"],
                                "quotas": {
                                    "tags": {
                                        "hashing": 1,
                                        "trees": 1,
                                    }
                                },
                            },
                        }
                    ],
                },
            ),
            actor_sub="teacher",
        )

    snapshot = version["generation_snapshot"]
    selected_tags = {
        tag
        for question in snapshot["selected_questions"]
        for tag in question["effective_tags"]
    }
    source_allocation = snapshot["source_allocations"][0]
    assert selected_tags >= {"hashing", "trees"}
    assert source_allocation["lesson_id"] == "generation_lesson"
    assert set(source_allocation["quota_allocations"]["tags"]) == {"hashing", "trees"}


def test_source_rule_generation_error_identifies_empty_pool(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        with pytest.raises(GenerationError) as excinfo:
            generate_quiz_version(
                _payload(
                    question_count=1,
                    criteria={
                        "schema_version": 2,
                        "lesson_ids": ["generation_lesson"],
                        "difficulty_min": 1,
                        "difficulty_max": 5,
                        "question_types": ["multiple_choice"],
                        "source_rules": [
                            {
                                "lesson_id": "generation_lesson",
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
                ),
                actor_sub="teacher",
            )

    message = str(excinfo.value)
    assert "source pool generation_lesson" in message
    assert "eligible pool matched 0 questions but 1 are requested" in message
    assert "tags=missing-tag" in message


def test_balanced_and_focused_selection_policies_succeed_with_shortfalls(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        balanced = generate_quiz_version(
            _payload(question_count=5, selection_policy="balanced_difficulty"),
            actor_sub="teacher",
        )
        focused = generate_quiz_version(
            _payload(question_count=5, selection_policy="focused_difficulty"),
            actor_sub="teacher",
        )

    assert len(balanced["questions"]) == 5
    assert len(focused["questions"]) == 5
    assert balanced["generation_snapshot"]["selection_policy"] == "balanced_difficulty"
    assert focused["generation_snapshot"]["selection_policy"] == "focused_difficulty"


def test_generation_from_template_inherits_template_policies_and_audits(app):
    template_payload = {
        "title": "Template Quiz",
        "criteria": _criteria(tags=["Generation"]),
        "question_count": 2,
        "selection_policy": "balanced_difficulty",
        "timer_minutes": 15,
        "attempt_limit": 2,
        "result_policy": "hidden",
    }
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        template = create_template(template_payload, actor_sub="teacher")
        version = generate_quiz_version_from_template(
            template["id"],
            overrides={"random_seed": "template-seed"},
            actor_sub="teacher",
        )
        audit = get_db().execute(
            """
            SELECT event_type, object_id
            FROM audit_events
            WHERE event_type = 'quiz_version.generated'
            """
        ).fetchone()

    assert version["template_id"] == template["id"]
    assert version["timer_minutes"] == 15
    assert version["attempt_limit"] == 2
    assert version["result_policy"] == "hidden"
    assert version["generation_snapshot"]["random_seed"] == "template-seed"
    assert dict(audit) == {
        "event_type": "quiz_version.generated",
        "object_id": version["id"],
    }


def test_admin_metadata_validation_rejects_snapshot_mutation_fields():
    with pytest.raises(QuizVersionError, match="immutable"):
        validate_admin_metadata_update({"generation_snapshot_json": "{}"})
