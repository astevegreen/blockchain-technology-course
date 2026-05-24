import json
import os
from pathlib import Path

from app.ingest import ingest_json, normalize_tag


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


def _get_json(client, path, **query):
    response = client.get(path, query_string=query, headers=HEADERS)
    assert response.status_code == 200
    return response.get_json()


def test_question_browser_filters_real_bundle(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]
    first_question = source_bank["questions"][0]
    first_lecture_id = source_bank["hierarchy"]["sections"][0]["lectures"][0]["id"]
    first_section_id = source_bank["hierarchy"]["sections"][0]["id"]
    expected_question_count = sum(len(bank["questions"]) for bank in source_banks)

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    banks_payload = _get_json(client, "/instructor/api/banks")
    all_questions = _get_json(client, "/instructor/api/questions", limit=100)
    by_lesson = _get_json(
        client,
        "/instructor/api/questions",
        lesson_id=source_bank["lesson_id"],
        limit=100,
    )
    by_title = _get_json(
        client,
        "/instructor/api/questions",
        lesson_title=source_bank["lesson_title"],
        limit=100,
    )
    by_topic = _get_json(
        client,
        "/instructor/api/questions",
        topic=source_bank["topic"],
        limit=100,
    )
    by_bank_tag = _get_json(
        client,
        "/instructor/api/questions",
        tag="bitcoin-origins-and-mechanics",
        limit=100,
    )
    by_question_tag = _get_json(
        client,
        "/instructor/api/questions",
        tag=first_question["tags"][4],
        limit=100,
    )
    by_section = _get_json(
        client,
        "/instructor/api/questions",
        hierarchy_section=first_section_id,
        limit=100,
    )
    by_lecture = _get_json(
        client,
        "/instructor/api/questions",
        hierarchy_lecture=first_lecture_id,
        limit=100,
    )
    by_difficulty = _get_json(
        client,
        "/instructor/api/questions",
        difficulty_level=first_question["difficulty_level"],
        limit=100,
    )
    by_type = _get_json(
        client,
        "/instructor/api/questions",
        question_type="multiple_choice",
        limit=100,
    )
    by_source = _get_json(
        client,
        "/instructor/api/questions",
        source="bitcoin_whitepaper",
        limit=100,
    )

    assert len(banks_payload["banks"]) == len(source_banks)
    assert all_questions["total"] == expected_question_count
    assert by_lesson["total"] == len(source_bank["questions"])
    assert by_title["total"] == len(source_bank["questions"])
    assert 0 < by_topic["total"] < expected_question_count
    assert by_bank_tag["total"] == len(source_bank["questions"])
    assert 0 < by_question_tag["total"] < expected_question_count
    assert 0 < by_section["total"] < expected_question_count
    assert by_lecture["total"] == len(
        source_bank["hierarchy"]["sections"][0]["lectures"][0]["question_ids"]
    )
    assert 0 < by_difficulty["total"] < expected_question_count
    assert by_type["total"] == expected_question_count
    assert 0 < by_source["total"] < expected_question_count


def test_question_filter_terms_endpoint_is_authenticated_cached_and_etagged(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")
        expected_tag = normalize_tag(source_bank["tags"][0])

    unauthorized = client.get("/instructor/api/questions/filter-terms")
    response = client.get("/instructor/api/questions/filter-terms", headers=HEADERS)
    payload = response.get_json()
    not_modified = client.get(
        "/instructor/api/questions/filter-terms",
        headers={**HEADERS, "If-None-Match": response.headers["ETag"]},
    )

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, max-age=0"
    assert response.headers["ETag"]
    assert payload["schema_version"] == 2
    assert payload["revision"]
    assert source_bank["lesson_id"] in payload["banks"]
    assert source_bank["lesson_id"] in [
        term["value"] for term in payload["fields"]["lesson_id"]
    ]
    assert source_bank["lesson_title"] in [
        term["value"] for term in payload["fields"]["lesson_title"]
    ]
    assert source_bank["topic"] in [
        term["value"] for term in payload["fields"]["topic"]
    ]
    assert expected_tag in [term["value"] for term in payload["fields"]["tag"]]
    assert expected_tag in [
        term["value"]
        for term in payload["banks"][source_bank["lesson_id"]]["fields"]["tag"]
    ]
    assert not_modified.status_code == 304


def test_bank_browser_uses_compact_headers_and_delete_label(app, client):
    raw_json, source_banks = _load_bundle()

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    response = client.get("/instructor/banks", headers=HEADERS)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<th class="table-column-compact">Questions</th>' in html
    assert '<th class="table-column-compact">Hidden</th>' in html
    assert ">Delete this bank<" not in html
    assert ">Delete<" in html
    assert f'aria-label="Delete bank {source_banks[0]["lesson_id"]}"' in html


def test_question_browser_renders_autocomplete_inputs_without_source_autocomplete(
    app,
    client,
):
    raw_json, _source_banks = _load_bundle()

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    response = client.get("/instructor/questions", headers=HEADERS)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-question-filter-form" in html
    assert 'data-filter-terms-url="/instructor/api/questions/filter-terms"' in html
    for field in (
        "lesson_id",
        "lesson_title",
        "topic",
        "tag",
        "hierarchy_section",
        "hierarchy_lecture",
        "difficulty_level",
        "question_type",
    ):
        assert f'data-autocomplete-field="{field}"' in html
    assert 'input name="source"' in html
    assert 'input name="source" value="" data-autocomplete-field' not in html
    assert "fetch(form.dataset.filterTermsUrl" in html


def test_question_detail_exposes_instructor_only_answer_metadata(app, client):
    raw_json, source_banks = _load_bundle()
    first_question = source_banks[0]["questions"][0]

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    list_payload = _get_json(
        client,
        "/instructor/api/questions",
        lesson_id=source_banks[0]["lesson_id"],
        limit=1,
    )
    question_id = list_payload["questions"][0]["id"]

    detail_response = client.get(
        f"/instructor/api/questions/{question_id}",
        headers=HEADERS,
    )
    detail = detail_response.get_json()["question"]
    html_response = client.get(f"/instructor/questions/{question_id}", headers=HEADERS)
    html = html_response.get_data(as_text=True)

    assert detail_response.status_code == 200
    assert detail["question_stem"] == first_question["question_stem"]
    assert detail["explanation"] == first_question["explanation"]
    assert detail["topic"] == first_question["topic"]
    assert detail["difficulty_level"] == first_question["difficulty_level"]
    assert detail["lesson_block"] == first_question["lesson_block"]
    assert detail["specific_source_lesson"] == first_question["specific_source_lesson"]
    assert first_question["tags"][0] in detail["effective_tags"]
    assert any(option["is_correct"] for option in detail["options"])
    assert first_question["correct_answer"] in [
        option["option_text"] for option in detail["options"]
    ]
    assert html_response.status_code == 200
    assert first_question["correct_answer"] in html
    assert "correct" in html


def test_question_browser_is_auth_required_and_read_only(app, client):
    raw_json, source_banks = _load_bundle()
    first_question = source_banks[0]["questions"][0]

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    unauthorized = client.get("/instructor/api/questions")
    assert unauthorized.status_code == 401

    list_payload = _get_json(
        client,
        "/instructor/api/questions",
        lesson_id=source_banks[0]["lesson_id"],
        limit=1,
    )
    question_id = list_payload["questions"][0]["id"]

    edit_attempt = client.post(
        f"/instructor/questions/{question_id}",
        data={"question_stem": "Mutated"},
        headers=HEADERS,
    )
    api_edit_attempt = client.post(
        f"/instructor/api/questions/{question_id}",
        json={"question_stem": "Mutated"},
        headers=HEADERS,
    )
    detail = _get_json(client, f"/instructor/api/questions/{question_id}")["question"]

    assert edit_attempt.status_code == 405
    assert api_edit_attempt.status_code == 405
    assert detail["question_stem"] == first_question["question_stem"]
