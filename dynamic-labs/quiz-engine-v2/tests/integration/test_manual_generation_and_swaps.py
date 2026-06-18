import json

from app.db import get_db
from app.generation import generate_quiz_version_from_template_manual
from app.ingest import ingest_json
from app.publication import set_quiz_version_visibility
from app.question_editing import edit_question
from app.quiz_templates import create_template


HEADERS = {"X-Test-Instructor": "teacher"}


def _question(source_qid, stem, *, topic="bitcoin", tags=None, difficulty=1):
    return {
        "id": source_qid,
        "question_stem": stem,
        "correct_answer": f"{stem} correct",
        "incorrect_answers": [f"{stem} wrong"],
        "explanation": f"{stem} explanation",
        "difficulty_level": difficulty,
        "topic": topic,
        "tags": tags or [],
    }


def _bank(lesson_id, title, questions, *, topic="bitcoin", tags=None):
    return {
        "lesson_id": lesson_id,
        "lesson_title": title,
        "topic": topic,
        "tags": tags or [],
        "questions": questions,
    }


def _ingest_bundle():
    ingest_json(
        json.dumps(
            [
                _bank(
                    "manual_a",
                    "Manual A",
                    [
                        _question("a1", "A one", tags=["slot"]),
                        _question("a2", "A two", tags=["slot"]),
                        _question("a3", "A three", tags=["other"]),
                    ],
                    tags=["bank-a"],
                ),
                _bank(
                    "manual_b",
                    "Manual B",
                    [
                        _question("b1", "B one", topic="ethereum", tags=["override"]),
                        _question("b2", "B two", topic="ethereum", tags=["override"]),
                    ],
                    topic="ethereum",
                    tags=["bank-b"],
                ),
            ]
        ),
        actor_sub="teacher",
    )


def _template_payload(**overrides):
    payload = {
        "title": "Manual Template",
        "criteria": {
            "lesson_ids": ["manual_a"],
            "question_types": ["multiple_choice"],
            "difficulty_min": 1,
            "difficulty_max": 5,
        },
        "question_count": 2,
        "selection_policy": "random",
        "question_order_mode": "fixed",
        "option_order_mode": "fixed",
        "attempt_limit": 1,
        "result_policy": "score_after_grading",
    }
    payload.update(overrides)
    return payload


def _question_ids_by_source_qid():
    rows = get_db().execute("SELECT id, source_qid FROM questions").fetchall()
    return {row["source_qid"]: row["id"] for row in rows}


def test_manual_template_generation_uses_selected_questions(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(_template_payload(), actor_sub="teacher")
        ids = _question_ids_by_source_qid()

    detail_html = client.get(
        f"/instructor/templates/{template['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)
    form_html = client.get(
        f"/instructor/templates/{template['id']}/manual-generate",
        headers=HEADERS,
    ).get_data(as_text=True)
    candidate_response = client.get(
        f"/instructor/api/templates/{template['id']}/manual-candidates",
        headers=HEADERS,
    )
    invalid_response = client.post(
        f"/instructor/api/templates/{template['id']}/generate-manual",
        json={"selected_question_ids": [ids["a1"]], "random_seed": "manual"},
        headers=HEADERS,
    )
    response = client.post(
        f"/instructor/api/templates/{template['id']}/generate-manual",
        json={
            "selected_question_ids": [ids["a2"], ids["a1"]],
            "random_seed": "manual",
        },
        headers=HEADERS,
    )
    version = response.get_json()["quiz_version"]

    assert "Choose questions manually" in detail_html
    assert "Select exactly 2 questions" in form_html
    assert candidate_response.status_code == 200
    assert len(candidate_response.get_json()["candidates"]["groups"][0]["questions"]) == 3
    assert invalid_response.status_code == 400
    assert "exactly 2 questions" in invalid_response.get_json()["error"]
    assert response.status_code == 201
    assert version["visibility"] == "hidden"
    assert version["generation_snapshot"]["selection_mode"] == "manual"
    assert version["generation_snapshot"]["selected_question_ids"] == [
        ids["a2"],
        ids["a1"],
    ]


def test_generated_quiz_question_edit_link_opens_latest_revision_and_disables_when_published(
    app,
    client,
):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=1),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"]],
            overrides={"random_seed": "edit-link"},
            actor_sub="teacher",
        )
        edit = edit_question(
            ids["a1"],
            {
                "expected_question_id": ids["a1"],
                "question_stem": "A one edited",
                "explanation": "Edited explanation",
                "difficulty_level": 2,
                "topic": "bitcoin",
                "question_tags": ["edited"],
                "options": [
                    {"option_text": "Edited correct", "is_correct": True},
                    {"option_text": "Edited wrong", "is_correct": False},
                ],
            },
            actor_sub="teacher",
        )
        version_question_id = version["questions"][0]["id"]

    edit_link = client.get(
        f"/instructor/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/edit-source",
        headers=HEADERS,
    )

    with app.app_context():
        set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")

    published_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)

    assert edit_link.status_code == 302
    assert edit_link.headers["Location"].endswith(
        f"/instructor/questions/{edit['new_question_id']}/edit"
    )
    assert "Generated quiz questions can only be edited while the quiz is hidden" in (
        published_html
    )
    assert "<button type=\"button\" disabled>Edit source</button>" in published_html


def test_swap_question_respects_template_slot_and_allows_override(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=1),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"]],
            overrides={"random_seed": "swap"},
            actor_sub="teacher",
        )
        version_question_id = version["questions"][0]["id"]

    candidates = client.get(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/swap-candidates",
        headers=HEADERS,
    ).get_json()["candidates"]["candidates"]
    blocked = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/swap",
        json={"replacement_question_id": ids["b1"]},
        headers=HEADERS,
    )
    overridden = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/swap",
        json={"replacement_question_id": ids["b1"], "override": True},
        headers=HEADERS,
    )
    swapped = overridden.get_json()["result"]["quiz_version"]

    assert [candidate["id"] for candidate in candidates] == [ids["a2"], ids["a3"]]
    assert blocked.status_code == 400
    assert "enable override" in blocked.get_json()["error"]
    assert overridden.status_code == 200
    assert swapped["generation_snapshot"]["selected_question_ids"] == [ids["b1"]]
    assert swapped["generation_snapshot"]["question_swaps"][0]["override"]
    assert swapped["questions"][0]["source_question_id"] == ids["b1"]
    assert swapped["questions"][0]["snapshot_question_stem"] == "B one"


def test_auto_swap_and_no_replacement_failure(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(
                question_count=1,
                criteria={
                    "lesson_ids": ["manual_a"],
                    "tags": ["other"],
                    "question_types": ["multiple_choice"],
                },
            ),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a3"]],
            overrides={"random_seed": "no-swap"},
            actor_sub="teacher",
        )
        version_question_id = version["questions"][0]["id"]

    failed = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/swap-auto",
        headers=HEADERS,
    )
    overridden = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/swap-auto",
        json={"override": True},
        headers=HEADERS,
    )

    assert failed.status_code == 400
    assert "no replacement question exists" in failed.get_json()["error"]
    assert overridden.status_code == 200
    assert overridden.get_json()["result"]["replacement"]["new_source_question_id"] in {
        ids["a1"],
        ids["a2"],
        ids["b1"],
        ids["b2"],
    }


def test_swap_rejects_duplicate_question(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(_template_payload(), actor_sub="teacher")
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"], ids["a2"]],
            overrides={"random_seed": "duplicate-swap"},
            actor_sub="teacher",
        )
        version_question_id = version["questions"][0]["id"]

    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/swap",
        json={"replacement_question_id": ids["a2"], "override": True},
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert "already in this quiz" in response.get_json()["error"]


def test_hidden_quiz_can_add_and_remove_questions(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(_template_payload(), actor_sub="teacher")
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"], ids["a2"]],
            overrides={"random_seed": "length-change"},
            actor_sub="teacher",
        )

    detail_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)
    add_form_html = client.get(
        f"/instructor/quiz-versions/{version['id']}/questions/add",
        headers=HEADERS,
    ).get_data(as_text=True)
    candidates = client.get(
        f"/instructor/api/quiz-versions/{version['id']}/questions/add-candidates",
        headers=HEADERS,
    ).get_json()["candidates"]["candidates"]
    added_auto = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/add-auto",
        headers=HEADERS,
    )
    added_auto_result = added_auto.get_json()["result"]
    blocked = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/add",
        json={"source_question_id": ids["b1"]},
        headers=HEADERS,
    )
    overridden = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/add",
        json={"source_question_id": ids["b1"], "override": True},
        headers=HEADERS,
    )
    overridden_version = overridden.get_json()["result"]["quiz_version"]
    question_to_remove = next(
        question
        for question in overridden_version["questions"]
        if question["source_question_id"] == ids["a2"]
    )
    removed = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{question_to_remove['id']}/remove",
        headers=HEADERS,
    )
    removed_result = removed.get_json()["result"]

    assert "Quiz Questions" in detail_html
    assert "Choose question to add" in detail_html
    assert "Remove from quiz" in detail_html
    assert 'data-confirm="Remove this question from the quiz?"' in detail_html
    assert 'name="question_count"' not in detail_html
    assert "Add Question" in add_form_html
    assert [candidate["id"] for candidate in candidates] == [ids["a3"]]
    assert added_auto.status_code == 200
    assert added_auto_result["addition"]["source_question_id"] == ids["a3"]
    assert added_auto_result["quiz_version"]["question_count"] == 3
    assert blocked.status_code == 400
    assert "enable override" in blocked.get_json()["error"]
    assert overridden.status_code == 200
    assert overridden_version["question_count"] == 4
    assert overridden_version["generation_snapshot"]["selected_question_ids"] == [
        ids["a1"],
        ids["a2"],
        ids["a3"],
        ids["b1"],
    ]
    assert overridden_version["generation_snapshot"]["question_additions"][-1][
        "override"
    ]
    assert removed.status_code == 200
    assert removed_result["removal"]["source_question_id"] == ids["a2"]
    assert removed_result["quiz_version"]["question_count"] == 3
    assert removed_result["quiz_version"]["generation_snapshot"][
        "selected_question_ids"
    ] == [ids["a1"], ids["a3"], ids["b1"]]
    assert [
        question["position"]
        for question in removed_result["quiz_version"]["questions"]
    ] == [1, 2, 3]
    assert removed_result["quiz_version"]["generation_snapshot"]["question_removals"][
        -1
    ]["source_question_id"] == ids["a2"]


def test_auto_add_reports_when_no_more_questions_exist(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=3),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"], ids["a2"], ids["a3"]],
            overrides={"random_seed": "length-no-more"},
            actor_sub="teacher",
        )

    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/add-auto",
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert "no question exists" in response.get_json()["error"]


def test_remove_rejects_last_question(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=1),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"]],
            overrides={"random_seed": "last-remove"},
            actor_sub="teacher",
        )
        version_question_id = version["questions"][0]["id"]

    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/remove",
        headers=HEADERS,
    )
    detail_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)

    assert response.status_code == 400
    assert "at least one question" in response.get_json()["error"]
    assert '<button type="submit" disabled>Remove from quiz</button>' in detail_html


def test_hidden_quiz_timer_minutes_can_update_and_clear(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=1, timer_minutes=None),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"]],
            overrides={"random_seed": "timer-change"},
            actor_sub="teacher",
        )

    detail_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)
    updated = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/timer",
        json={"timer_minutes": 45},
        headers=HEADERS,
    )
    cleared = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/timer",
        json={"timer_minutes": ""},
        headers=HEADERS,
    )
    invalid = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/timer",
        json={"timer_minutes": "abc"},
        headers=HEADERS,
    )

    assert 'name="timer_minutes"' in detail_html
    assert updated.status_code == 200
    assert updated.get_json()["result"]["old_timer_minutes"] is None
    assert updated.get_json()["result"]["new_timer_minutes"] == 45
    assert updated.get_json()["result"]["quiz_version"]["timer_minutes"] == 45
    assert cleared.status_code == 200
    assert cleared.get_json()["result"]["old_timer_minutes"] == 45
    assert cleared.get_json()["result"]["new_timer_minutes"] is None
    assert cleared.get_json()["result"]["quiz_version"]["timer_minutes"] is None
    assert invalid.status_code == 400
    assert "timer_minutes must be an integer" in invalid.get_json()["error"]


def test_published_quiz_swap_is_rejected(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=1),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"]],
            overrides={"random_seed": "published-swap"},
            actor_sub="teacher",
        )
        set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")
        version_question_id = version["questions"][0]["id"]

    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/swap",
        json={"replacement_question_id": ids["a2"]},
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert "only be edited while the quiz is hidden" in response.get_json()["error"]


def test_published_quiz_add_and_remove_are_rejected(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=1),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"]],
            overrides={"random_seed": "published-length"},
            actor_sub="teacher",
        )
        set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")

        version_question_id = version["questions"][0]["id"]

    add_response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/add-auto",
        headers=HEADERS,
    )
    remove_response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/questions/"
        f"{version_question_id}/remove",
        headers=HEADERS,
    )
    detail_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)

    assert add_response.status_code == 400
    assert "only be edited while the quiz is hidden" in add_response.get_json()["error"]
    assert remove_response.status_code == 400
    assert "only be edited while the quiz is hidden" in remove_response.get_json()[
        "error"
    ]
    assert "<button type=\"button\" disabled>Choose question to add</button>" in (
        detail_html
    )
    assert "<button type=\"button\" disabled>Remove from quiz</button>" in detail_html


def test_published_quiz_timer_update_is_rejected(app, client):
    with app.app_context():
        _ingest_bundle()
        template = create_template(
            _template_payload(question_count=1, timer_minutes=20),
            actor_sub="teacher",
        )
        ids = _question_ids_by_source_qid()
        version = generate_quiz_version_from_template_manual(
            template["id"],
            [ids["a1"]],
            overrides={"random_seed": "published-timer"},
            actor_sub="teacher",
        )
        set_quiz_version_visibility(version["id"], "published", actor_sub="teacher")

    response = client.post(
        f"/instructor/api/quiz-versions/{version['id']}/timer",
        json={"timer_minutes": 30},
        headers=HEADERS,
    )
    detail_html = client.get(
        f"/instructor/quiz-versions/{version['id']}",
        headers=HEADERS,
    ).get_data(as_text=True)

    assert response.status_code == 400
    assert "timer can only be edited while the quiz is hidden" in response.get_json()[
        "error"
    ]
    assert '<button type="submit" disabled>Update timer</button>' in detail_html
