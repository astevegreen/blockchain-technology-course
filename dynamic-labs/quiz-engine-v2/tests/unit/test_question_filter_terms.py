import json

from app.db import get_db
from app.ingest import ingest_json
from app.question_filter_terms import (
    CACHE_KEY,
    STALE_KEY,
    build_question_filter_terms,
    get_question_filter_terms,
    mark_question_filter_terms_stale,
    refresh_question_filter_terms,
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


def _terms(payload, field):
    return {term["value"]: term for term in payload["fields"][field]}


def test_build_question_filter_terms_extracts_known_filter_values(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        payload = build_question_filter_terms()

    assert payload["schema_version"] == 2
    assert payload["revision"]
    assert set(payload["fields"]) == {
        "lesson_id",
        "lesson_title",
        "topic",
        "tag",
        "hierarchy_section",
        "hierarchy_lecture",
        "difficulty_level",
        "question_type",
    }
    assert _terms(payload, "lesson_id")["l04_p1_hashing_merkle_trees"]["count"] == 1
    assert _terms(payload, "lesson_title")["Hashing and Merkle Trees"]["count"] == 1
    assert _terms(payload, "topic")["primitives"]["count"] == 1
    assert _terms(payload, "tag")["hashing"]["count"] == 1
    assert _terms(payload, "tag")["merkle-trees"]["count"] == 1
    assert _terms(payload, "hierarchy_section")["sec_hashing"]["count"] == 1
    assert _terms(payload, "hierarchy_lecture")["lec_merkle"]["count"] == 1
    assert _terms(payload, "difficulty_level")["3"]["count"] == 1
    assert _terms(payload, "question_type")["multiple_choice"]["count"] == 1
    bank_terms = payload["banks"]["l04_p1_hashing_merkle_trees"]["fields"]
    assert {term["value"] for term in bank_terms["tag"]} == {
        "hashing",
        "merkle-trees",
    }
    assert bank_terms["tag"][0]["count"] == 1


def test_question_filter_terms_cache_refresh_and_stale_fallback(app):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")
        conn = get_db()

        payload = refresh_question_filter_terms(conn=conn)
        stored = json.loads(
            conn.execute(
                "SELECT value FROM app_settings WHERE key = ?",
                (CACHE_KEY,),
            ).fetchone()["value"]
        )
        stale = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (STALE_KEY,),
        ).fetchone()["value"]

        mark_question_filter_terms_stale(conn=conn)
        marked_stale = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (STALE_KEY,),
        ).fetchone()["value"]
        refreshed = get_question_filter_terms(conn=conn)
        final_stale = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (STALE_KEY,),
        ).fetchone()["value"]

    assert stored["revision"] == payload["revision"]
    assert stale == "0"
    assert marked_stale == "1"
    assert refreshed["revision"] == payload["revision"]
    assert final_stale == "0"
