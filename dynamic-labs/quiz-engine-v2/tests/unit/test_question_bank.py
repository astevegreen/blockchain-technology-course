import json

import pytest

from app.ingest import ingest_json
from app.question_bank import (
    QuestionBankFilterError,
    build_question_query,
    get_question_detail,
    parse_question_filters,
    search_questions,
)


def _bank():
    return {
        "lesson_id": "l04_p1_hashing_merkle_trees",
        "lesson_title": "Hashing and Merkle Trees",
        "topic": "primitives",
        "tags": ["Hashing"],
        "hierarchy": {
            "sections": [
                {
                    "id": "sec_hashing",
                    "title": "Hashing",
                    "lectures": [
                        {
                            "id": "lec_merkle",
                            "title": "Merkle trees",
                            "question_ids": ["q1"],
                        }
                    ],
                }
            ]
        },
        "questions": [
            {
                "id": "q1",
                "question_type": "multiple_choice",
                "question_stem": "Which statement best describes a Merkle tree?",
                "correct_answer": "It commits to many leaves with a root hash.",
                "incorrect_answers": ["It hides every transaction from validators."],
                "difficulty_level": 3,
                "topic": "primitives",
                "tags": ["Merkle Trees"],
                "lesson_block": "Merkle trees",
                "specific_source_lesson": "slides: merkle trees",
                "specific_source_reading": "reading: hashing",
                "explanation": "The root hash commits to the leaves.",
            }
        ],
    }


def test_parse_question_filters_normalizes_inputs():
    filters = parse_question_filters(
        {
            "lesson_id": " l04_p1_hashing_merkle_trees ",
            "lesson_title": "Hashing",
            "topic": "primitives",
            "tag": "Merkle Trees!",
            "section": "sec_hashing",
            "lecture": "lec_merkle",
            "difficulty": "3",
            "question_type": "multiple_choice",
            "source": "merkle",
            "limit": "500",
            "offset": "2",
        }
    )

    assert filters.lesson_id == "l04_p1_hashing_merkle_trees"
    assert filters.lesson_title == "Hashing"
    assert filters.topic == "primitives"
    assert filters.tag == "merkle-trees"
    assert filters.hierarchy_section == "sec_hashing"
    assert filters.hierarchy_lecture == "lec_merkle"
    assert filters.difficulty_level == 3
    assert filters.question_type == "multiple_choice"
    assert filters.source == "merkle"
    assert filters.limit == 100
    assert filters.offset == 2


@pytest.mark.parametrize(
    "args, message",
    (
        ({"difficulty": "hard"}, "difficulty_level"),
        ({"difficulty": "6"}, "difficulty_level"),
        ({"question_type": "essay"}, "question_type"),
        ({"limit": "0"}, "limit"),
        ({"offset": "-1"}, "offset"),
    ),
)
def test_parse_question_filters_rejects_invalid_values(args, message):
    with pytest.raises(QuestionBankFilterError, match=message):
        parse_question_filters(args)


def test_query_builder_uses_effective_tag_and_hierarchy_filters():
    filters = parse_question_filters(
        {
            "tag": "Merkle Trees",
            "hierarchy_section": "sec_hashing",
            "hierarchy_lecture": "lec_merkle",
            "source": "slides",
        }
    )

    sql, params = build_question_query(filters)

    assert "question_tags" in sql
    assert "bank_revision_tags" in sql
    assert "question.content_section_id = ?" in sql
    assert "question.content_lecture_id = ?" in sql
    assert "specific_source_lesson LIKE" in sql
    assert params[:5] == [
        "merkle-trees",
        "merkle-trees",
        "sec_hashing",
        "lec_merkle",
        "%slides%",
    ]


def test_effective_tag_and_hierarchy_filters_query_rows(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

        by_bank_tag = search_questions(parse_question_filters({"tag": "Hashing"}))
        by_question_tag = search_questions(
            parse_question_filters({"tag": "Merkle Trees"})
        )
        by_section = search_questions(
            parse_question_filters({"hierarchy_section": "sec_hashing"})
        )
        by_lecture = search_questions(
            parse_question_filters({"hierarchy_lecture": "lec_merkle"})
        )
        by_source = search_questions(parse_question_filters({"source": "slides"}))
        detail = get_question_detail(by_question_tag["questions"][0]["id"])

    assert by_bank_tag["total"] == 1
    assert by_question_tag["total"] == 1
    assert by_question_tag["questions"][0]["effective_tags"] == [
        "hashing",
        "merkle-trees",
    ]
    assert by_section["total"] == 1
    assert by_lecture["total"] == 1
    assert by_source["total"] == 1
    assert detail["options"][0]["is_correct"] == 1
    assert detail["explanation"] == "The root hash commits to the leaves."
