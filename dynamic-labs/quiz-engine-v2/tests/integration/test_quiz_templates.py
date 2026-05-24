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
        "title": "Bitcoin Origins Template",
        "description": "Real bundle template",
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
        "default_available_offset_minutes": 0,
        "default_available_duration_minutes": 120,
    }
    payload.update(overrides)
    return payload


def test_template_crud_preview_and_archive_with_real_bundle(app, client):
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
    preview_response = client.post(
        "/instructor/api/templates/preview",
        json={"template_id": template["id"]},
        headers=HEADERS,
    )
    update_response = client.put(
        f"/instructor/api/templates/{template['id']}",
        json={"title": "Updated Bitcoin Template", "question_count": 4},
        headers=HEADERS,
    )
    duplicate_response = client.post(
        f"/instructor/api/templates/{template['id']}/duplicate",
        headers=HEADERS,
    )
    archive_response = client.post(
        f"/instructor/api/templates/{template['id']}/archive",
        headers=HEADERS,
    )
    visible_list = client.get("/instructor/api/templates", headers=HEADERS).get_json()
    full_list = client.get(
        "/instructor/api/templates",
        query_string={"include_archived": "1"},
        headers=HEADERS,
    ).get_json()

    assert create_response.status_code == 201
    assert template["title"] == "Bitcoin Origins Template"
    assert template["criteria"]["lesson_ids"] == [source_bank["lesson_id"]]
    assert template["criteria"]["tags"] == ["bitcoin-origins-and-mechanics"]
    assert template["selection_policy"] == "balanced_difficulty"
    assert template["attempt_limit"] == 2
    assert template["timer_minutes"] == 30

    preview = preview_response.get_json()["preview"]
    assert preview_response.status_code == 200
    assert preview["eligible_pool_size"] == len(
        source_bank["hierarchy"]["sections"][0]["lectures"][0]["question_ids"]
    )
    assert preview["question_count"] == 5
    assert preview["warnings"] == []

    updated = update_response.get_json()["template"]
    duplicated = duplicate_response.get_json()["template"]
    archived = archive_response.get_json()["template"]
    assert update_response.status_code == 200
    assert updated["title"] == "Updated Bitcoin Template"
    assert updated["question_count"] == 4
    assert duplicate_response.status_code == 201
    assert duplicated["title"] == "Updated Bitcoin Template Copy"
    assert archive_response.status_code == 200
    assert archived["archived"] is True
    assert [item["id"] for item in visible_list["templates"]] == [duplicated["id"]]
    assert {item["id"] for item in full_list["templates"]} == {
        template["id"],
        duplicated["id"],
    }


def test_template_builder_form_uses_policy_dropdowns_and_lesson_bank_quotas(
    app,
    client,
):
    raw_json, source_banks = _load_bundle()
    first_bank = source_banks[0]
    second_bank = source_banks[1]

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    new_page = client.get("/instructor/templates/new", headers=HEADERS)
    new_html = new_page.get_data(as_text=True)
    created = client.post(
        "/instructor/templates",
        data={
            "title": "Structured Builder Template",
            "description": "Created through the HTML builder.",
            "lesson_ids": [first_bank["lesson_id"], second_bank["lesson_id"]],
            f"lesson_quota:{first_bank['lesson_id']}": "2",
            f"lesson_quota:{second_bank['lesson_id']}": "1",
            f"source_filter_mode:{first_bank['lesson_id']}": "override",
            f"source_selection_policy:{first_bank['lesson_id']}": "",
            f"source_criteria_json:{first_bank['lesson_id']}": json.dumps(
                {
                    "schema_version": 1,
                    "lesson_ids": [],
                    "topics": [first_bank["topic"]],
                    "tags": ["will-be-overridden"],
                    "excluded_topics": ["will-be-overridden-topic"],
                    "excluded_tags": ["will-be-overridden-tag"],
                    "tag_match_mode": "all",
                    "hierarchy_sections": [
                        first_bank["hierarchy"]["sections"][0]["id"]
                    ],
                    "hierarchy_lectures": [],
                    "difficulty_min": 2,
                    "difficulty_max": 4,
                    "question_types": ["multiple_choice"],
                    "quotas": {"topics": {first_bank["topic"]: 1}},
                    "require_topic_coverage": True,
                }
            ),
            f"source_tags:{first_bank['lesson_id']}": source_banks[0]["tags"][0],
            f"source_tag_quotas:{first_bank['lesson_id']}": (
                f"{source_banks[0]['tags'][0]}:1"
            ),
            f"source_tag_match_mode:{first_bank['lesson_id']}": "any",
            f"source_excluded_topics:{first_bank['lesson_id']}": "deprecated-topic",
            f"source_excluded_tags:{first_bank['lesson_id']}": "draft-source",
            f"source_filter_mode:{second_bank['lesson_id']}": "inherit",
            "topics": "",
            "tags": "",
            "excluded_topics": "legacy-fallback",
            "excluded_tags": "draft-fallback",
            "tag_match_mode": "any",
            "difficulty_min": "1",
            "difficulty_max": "5",
            "question_types": ["multiple_choice"],
            "selection_policy": "balanced_difficulty",
            "timer_minutes": "-1",
            "attempt_limit": "2",
            "result_policy": "score_and_answers_after_release",
        },
        headers=HEADERS,
        follow_redirects=True,
    )

    with app.app_context():
        row = get_db().execute(
            """
            SELECT id, criteria_json, question_count, selection_policy,
                   timer_minutes, attempt_limit, result_policy,
                   question_order_mode, option_order_mode
            FROM quiz_templates
            WHERE title = 'Structured Builder Template'
            """
        ).fetchone()
        criteria = json.loads(row["criteria_json"])

    edit_page = client.get(
        f"/instructor/templates/{row['id']}/edit",
        headers=HEADERS,
    )
    edit_html = edit_page.get_data(as_text=True)
    detail_html = client.get(
        f"/instructor/templates/{row['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)

    assert new_page.status_code == 200
    assert '<select name="selection_policy">' in new_html
    assert '<select name="result_policy">' in new_html
    assert 'data-template-bank-select-all' in new_html
    assert 'data-template-bank-select-none' in new_html
    assert 'data-template-builder-form' in new_html
    assert 'data-preview-url="/instructor/api/templates/preview"' in new_html
    assert 'data-template-validation-summary' in new_html
    assert 'data-template-bank-checkbox' in new_html
    assert 'data-template-bank-quota' in new_html
    assert 'data-template-source-filter-mode' in new_html
    assert 'data-template-source-override-panel' in new_html
    assert 'data-tag-chip-widget' in new_html
    assert 'data-tag-chip-add' in new_html
    assert 'data-source-criteria-json' in new_html
    assert 'data-source-tags-hidden' in new_html
    assert 'data-source-tag-quotas-hidden' in new_html
    assert f'name="source_excluded_topics:{first_bank["lesson_id"]}"' in new_html
    assert f'name="source_excluded_tags:{first_bank["lesson_id"]}"' in new_html
    assert 'data-token-autocomplete-field="tag"' in new_html
    assert f'data-token-autocomplete-bank="{first_bank["lesson_id"]}"' in new_html
    assert 'data-criteria-json' in new_html
    assert 'data-criteria-json-apply' in new_html
    assert 'data-criteria-json-reset' in new_html
    assert 'list="template-topic-terms"' in new_html
    assert 'list="template-tag-terms"' in new_html
    assert '<datalist id="template-topic-terms">' in new_html
    assert '<datalist id="template-tag-terms">' in new_html
    assert 'name="excluded_topics"' in new_html
    assert 'name="excluded_tags"' in new_html
    assert source_banks[0]["topic"] in new_html
    assert "proof-of-work" in new_html
    assert "Selection policy help" in new_html
    assert "Result policy help" in new_html
    assert "Order help" in new_html
    assert 'name="question_order_mode"' in new_html
    assert 'name="option_order_mode"' in new_html
    assert 'value="random_per_attempt" selected' in new_html
    assert "Use -1, 0, or blank for no timer." in new_html
    assert first_bank["lesson_id"] in new_html
    assert second_bank["lesson_id"] in new_html

    assert created.status_code == 200
    assert row["question_count"] == 3
    assert row["selection_policy"] == "balanced_difficulty"
    assert row["timer_minutes"] is None
    assert row["attempt_limit"] == 2
    assert row["result_policy"] == "score_and_answers_after_release"
    assert row["question_order_mode"] == "random_per_attempt"
    assert row["option_order_mode"] == "random_per_attempt"
    assert criteria["schema_version"] == 2
    assert criteria["lesson_ids"] == [
        first_bank["lesson_id"],
        second_bank["lesson_id"],
    ]
    assert criteria["excluded_topics"] == ["legacy-fallback"]
    assert criteria["excluded_tags"] == ["draft-fallback"]
    assert criteria["quotas"] == {}
    assert criteria["source_rules"][0]["lesson_id"] == first_bank["lesson_id"]
    assert criteria["source_rules"][0]["filter_mode"] == "override"
    assert criteria["source_rules"][0]["question_count"] == 2
    assert criteria["source_rules"][0]["criteria"]["topics"] == [first_bank["topic"]]
    assert criteria["source_rules"][0]["criteria"]["excluded_topics"] == [
        "deprecated-topic"
    ]
    assert criteria["source_rules"][0]["criteria"]["excluded_tags"] == [
        "draft-source"
    ]
    assert criteria["source_rules"][0]["criteria"]["hierarchy_sections"] == [
        first_bank["hierarchy"]["sections"][0]["id"]
    ]
    assert criteria["source_rules"][0]["criteria"]["difficulty_min"] == 2
    assert criteria["source_rules"][0]["criteria"]["difficulty_max"] == 4
    assert criteria["source_rules"][0]["criteria"]["require_topic_coverage"] is True
    assert criteria["source_rules"][0]["criteria"]["tag_match_mode"] == "any"
    assert criteria["source_rules"][0]["criteria"]["quotas"]["tags"] == {
        source_banks[0]["tags"][0]: 1,
    }
    assert criteria["source_rules"][0]["criteria"]["quotas"]["topics"] == {
        first_bank["topic"]: 1,
    }
    assert criteria["source_rules"][1]["lesson_id"] == second_bank["lesson_id"]
    assert criteria["source_rules"][1]["filter_mode"] == "inherit"
    assert criteria["source_rules"][1]["question_count"] == 1

    assert edit_page.status_code == 200
    assert f'value="{first_bank["lesson_id"]}" checked' in edit_html
    assert f'name="lesson_quota:{first_bank["lesson_id"]}" inputmode="numeric" value="2"' in edit_html
    assert f'name="source_filter_mode:{first_bank["lesson_id"]}"' in edit_html
    assert f'name="source_tag_quotas:{first_bank["lesson_id"]}"' in edit_html
    assert 'value="deprecated-topic"' in edit_html
    assert 'value="draft-source"' in edit_html
    assert 'value="balanced_difficulty" selected' in edit_html
    assert 'value="score_and_answers_after_release" selected' in edit_html
    assert 'name="question_order_mode"' in edit_html
    assert 'name="option_order_mode"' in edit_html
    assert 'name="timer_minutes" inputmode="numeric" value="-1"' in edit_html
    assert 'data-random-seed-input' in detail_html
    assert 'data-random-seed-regenerate' in detail_html
    assert "Generate hidden quiz" in detail_html


def test_template_preview_returns_warnings(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    response = client.post(
        "/instructor/api/templates/preview",
        json={
            "criteria": {
                "lesson_ids": [source_bank["lesson_id"]],
                "topics": [source_bank["topic"], "ethereum"],
                "tags": ["missing-tag"],
                "tag_match_mode": "any",
                "difficulty_min": 1,
                "difficulty_max": 5,
                "question_types": ["multiple_choice"],
                "quotas": {"tags": {"missing-tag": 2}},
                "require_topic_coverage": True,
            },
            "question_count": 20,
        },
        headers=HEADERS,
    )
    warnings = response.get_json()["preview"]["warnings"]
    codes = {warning["code"] for warning in warnings}

    assert response.status_code == 200
    assert "insufficient_pool" in codes
    assert "unsatisfied_quota" in codes
    assert "unsatisfied_topic_coverage" in codes


def test_template_pages_are_instructor_only_and_not_student_visible(app, client):
    raw_json, source_banks = _load_bundle()

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    unauthorized = client.get("/instructor/api/templates")
    assert unauthorized.status_code == 401

    create_response = client.post(
        "/instructor/api/templates",
        json=_template_payload(source_banks[0]),
        headers=HEADERS,
    )
    template = create_response.get_json()["template"]
    student_home = client.get("/student/").get_data(as_text=True)
    student_quizzes = client.get("/student/quizzes", follow_redirects=True).get_data(
        as_text=True
    )
    html_list = client.get("/instructor/templates", headers=HEADERS).get_data(
        as_text=True
    )

    assert create_response.status_code == 201
    assert template["title"] in html_list
    assert template["title"] not in student_home
    assert template["title"] not in student_quizzes


def test_editing_template_does_not_mutate_existing_generated_version(app, client):
    raw_json, source_banks = _load_bundle()
    source_bank = source_banks[0]
    snapshot_json = (
        '{"schema_version": 1, "criteria": {"lesson_ids": ["original"]}, '
        '"eligible_pool_size": 1, "quota_allocations": {}, '
        '"coverage_allocations": {}, "random_seed": "seed", '
        '"bank_revision_ids": [], "selected_question_ids": []}'
    )

    with app.app_context():
        ingest_json(raw_json, filename=_bundle_path().name, actor_sub="teacher")

    create_response = client.post(
        "/instructor/api/templates",
        json=_template_payload(source_bank),
        headers=HEADERS,
    )
    template = create_response.get_json()["template"]
    with app.app_context():
        db = get_db()
        with db:
            quiz_version_id = db.execute(
                """
                INSERT INTO quiz_versions (
                    template_id,
                    title,
                    generation_snapshot_json,
                    created_at
                )
                VALUES (?, 'Generated From Template', ?, CURRENT_TIMESTAMP)
                """,
                (template["id"], snapshot_json),
            ).lastrowid

    update_response = client.put(
        f"/instructor/api/templates/{template['id']}",
        json={"criteria": {"lesson_ids": ["changed"]}, "question_count": 3},
        headers=HEADERS,
    )

    with app.app_context():
        snapshot_after = get_db().execute(
            "SELECT generation_snapshot_json FROM quiz_versions WHERE id = ?",
            (quiz_version_id,),
        ).fetchone()[0]

    assert update_response.status_code == 200
    assert json.loads(snapshot_after) == json.loads(snapshot_json)
