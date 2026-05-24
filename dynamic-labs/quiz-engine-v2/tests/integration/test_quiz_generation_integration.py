import json
import os
from pathlib import Path

from app.db import get_db
from app.ingest import ingest_json


HEADERS = {"X-Test-Instructor": "teacher"}


def _quiz_fixture_dir():
    configured = os.environ.get("QUIZ_ENGINE_SAMPLE_QUIZ_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[4] / "quizes"


def _bundle_path():
    return _quiz_fixture_dir() / "dist" / "blockchain-course-quiz-bank-bundle.json"


def _load_bundle():
    raw_json = _bundle_path().read_text(encoding="utf-8")
    return raw_json, json.loads(raw_json)


def _template_payload(source_bank, **overrides):
    payload = {
        "title": "Generated Bitcoin Origins",
        "description": "Generation integration template",
        "criteria": {
            "lesson_ids": [source_bank["lesson_id"]],
            "topics": [source_bank["topic"]],
            "tags": ["bitcoin-origins-and-mechanics"],
            "tag_match_mode": "any",
            "hierarchy_sections": [source_bank["hierarchy"]["sections"][0]["id"]],
            "hierarchy_lectures": [
                source_bank["hierarchy"]["sections"][0]["lectures"][0]["id"]
            ],
            "difficulty_min": 1,
            "difficulty_max": 5,
            "question_types": ["multiple_choice"],
            "quotas": {"topics": {source_bank["topic"]: 2}},
            "require_topic_coverage": True,
        },
        "question_count": 5,
        "selection_policy": "balanced_difficulty",
        "timer_minutes": 30,
        "attempt_limit": 2,
        "result_policy": "score_after_grading",
    }
    payload.update(overrides)
    return payload


def test_generate_hidden_quiz_from_real_bundle_template_and_regenerate(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]
    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    create_response = client.post(
        "/instructor/api/templates",
        json=_template_payload(source_bank),
        headers=HEADERS,
    )
    template = create_response.get_json()["template"]
    generate_response = client.post(
        f"/instructor/api/templates/{template['id']}/generate",
        json={"random_seed": "browser-seed"},
        headers=HEADERS,
    )
    regenerate_response = client.post(
        f"/instructor/api/templates/{template['id']}/generate",
        json={"random_seed": "browser-seed"},
        headers=HEADERS,
    )

    assert generate_response.status_code == 201
    version = generate_response.get_json()["quiz_version"]
    regenerated = regenerate_response.get_json()["quiz_version"]
    assert regenerate_response.status_code == 201
    assert version["id"] != regenerated["id"]
    assert version["visibility"] == "hidden"
    assert version["question_count"] == 5
    assert version["template_id"] == template["id"]
    assert version["attempt_limit"] == 2
    assert version["timer_minutes"] == 30
    assert version["generation_snapshot"]["random_seed"] == "browser-seed"
    assert version["generation_snapshot"]["selected_question_ids"] == regenerated[
        "generation_snapshot"
    ]["selected_question_ids"]
    assert len(version["questions"]) == 5
    assert all(question["options"] for question in version["questions"])
    assert any(
        option["is_correct"]
        for question in version["questions"]
        for option in question["options"]
    )

    list_response = client.get("/instructor/api/quiz-versions", headers=HEADERS)
    detail_response = client.get(
        f"/instructor/api/quiz-versions/{version['id']}",
        headers=HEADERS,
    )
    html_list = client.get("/instructor/quiz-versions", headers=HEADERS).get_data(
        as_text=True
    )
    html_detail = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert version["title"] in html_list
    assert "Snapshot Questions" in html_detail
    assert "correct" in html_detail


def test_reingest_after_generation_does_not_mutate_snapshot_content(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]
    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    create_response = client.post(
        "/instructor/api/templates",
        json=_template_payload(source_bank, question_count=5),
        headers=HEADERS,
    )
    template = create_response.get_json()["template"]
    generate_response = client.post(
        f"/instructor/api/templates/{template['id']}/generate",
        json={"random_seed": "immutable-seed"},
        headers=HEADERS,
    )
    version = generate_response.get_json()["quiz_version"]
    version_question = version["questions"][0]
    original_snapshot_stem = version_question["snapshot_question_stem"]

    changed_bank = dict(source_bank)
    changed_bank["questions"] = [dict(question) for question in source_bank["questions"]]
    for question in changed_bank["questions"]:
        question["question_stem"] = f"Changed after generation: {question['id']}"
    with app.app_context():
        ingest_json(json.dumps(changed_bank), filename="changed.json", actor_sub="teacher")

    detail_response = client.get(
        f"/instructor/api/quiz-versions/{version['id']}",
        headers=HEADERS,
    )
    detail = detail_response.get_json()["quiz_version"]
    stored_question = next(
        question
        for question in detail["questions"]
        if question["id"] == version_question["id"]
    )

    assert generate_response.status_code == 201
    assert detail_response.status_code == 200
    assert stored_question["snapshot_question_stem"] == original_snapshot_stem


def test_generation_failure_leaves_no_partial_quiz_version_rows(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]
    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")
        before_versions = get_db().execute(
            "SELECT COUNT(*) FROM quiz_versions"
        ).fetchone()[0]

    response = client.post(
        "/instructor/api/quiz-versions",
        json={
            "title": "Impossible generation",
            "criteria": {
                "lesson_ids": [source_bank["lesson_id"]],
                "topics": ["missing-topic"],
                "question_types": ["multiple_choice"],
            },
            "question_count": 2,
            "random_seed": "failure",
        },
        headers=HEADERS,
    )

    with app.app_context():
        after_versions = get_db().execute(
            "SELECT COUNT(*) FROM quiz_versions"
        ).fetchone()[0]
        after_questions = get_db().execute(
            "SELECT COUNT(*) FROM quiz_version_questions"
        ).fetchone()[0]
        after_options = get_db().execute(
            "SELECT COUNT(*) FROM quiz_version_options"
        ).fetchone()[0]

    assert response.status_code == 400
    assert "eligible pool" in response.get_json()["error"]
    assert after_versions == before_versions
    assert after_questions == 0
    assert after_options == 0
