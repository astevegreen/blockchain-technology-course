import json

import pytest

from app.db import get_db
from app.ingest import ingest_json

HEADERS = {"X-Test-Instructor": "teacher"}
LESSON = "posttest_marking_test"


def _mc(qid):
    return {
        "id": qid,
        "question_type": "multiple_choice",
        "question_stem": f"Multiple-choice item {qid}?",
        "correct_answer": "Right",
        "incorrect_answers": ["Wrong one", "Wrong two", "Wrong three"],
        "explanation": "Because.",
        "difficulty_level": 2,
    }


def _written(qid, key):
    return {
        "id": qid,
        "question_type": "written",
        "question_stem": f"Written item {qid}.",
        "answer_key": key,
        "explanation": "Because.",
        "difficulty_level": 3,
    }


# Ten items: seven multiple choice and three written, so the pass mark is 7 of 10.
BANK = {
    "lesson_id": LESSON,
    "lesson_title": "Post-test marking test",
    "topic": "other",
    "questions": [_mc(f"m{i}") for i in range(1, 8)]
    + [_written("w1", ["Point A", "Point B"]), _written("w2", ["Point C"]), _written("w3", ["Point D"])],
}


@pytest.fixture
def marking(app_factory, tmp_path):
    quizes = tmp_path / "quizes"
    (quizes / "posttest").mkdir(parents=True)
    (quizes / "posttest" / "test-quiz-bank.json").write_text(json.dumps(BANK), encoding="utf-8")
    app = app_factory(QUIZES_DIR=str(quizes))
    with app.app_context():
        ingest_json(json.dumps(BANK), actor_sub="teacher")
    return app


def _publish(client):
    template = client.post(
        "/instructor/api/templates",
        json={
            "title": "Post-test",
            "description": "Marking test",
            "criteria": {"lesson_ids": [LESSON], "question_types": ["multiple_choice", "written"]},
            "question_count": 10,
            "selection_policy": "random",
            "timer_minutes": None,
            "attempt_limit": 1,
            "result_policy": "score_after_release",
        },
        headers=HEADERS,
    ).get_json()["template"]
    version = client.post(
        f"/instructor/api/templates/{template['id']}/generate", json={"random_seed": "marking"}, headers=HEADERS
    ).get_json()["quiz_version"]
    client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={"title": "Post-test", "available_from": "2000-01-01T00:00:00+00:00",
              "available_until": "2999-01-01T00:00:00+00:00"},
        headers=HEADERS,
    )
    return client.post(f"/instructor/api/quiz-versions/{version['id']}/publish", headers=HEADERS).get_json()[
        "quiz_version"
    ]


def _take(app, client, version, mc_right):
    """Enroll a new student and submit: `mc_right` multiple-choice items right, every written item answered."""
    client.post("/student/enroll")
    attempt = client.post(f"/student/api/quizzes/{version['id']}/start").get_json()["attempt"]
    with app.app_context():
        correct = {
            row["quiz_version_question_id"]: row["id"]
            for row in get_db().execute("SELECT id, quiz_version_question_id FROM quiz_version_options WHERE is_correct = 1")
        }
    answers, right = [], 0
    for question in sorted(attempt["questions"], key=lambda q: q["id"]):
        if question["options"]:
            wrong = next(o["id"] for o in question["options"] if o["id"] != correct[question["id"]])
            pick = correct[question["id"]] if right < mc_right else wrong
            right += pick == correct[question["id"]]
            answers.append({"question_id": question["id"], "selected_option_id": pick})
        else:
            answers.append({"question_id": question["id"], "written_response": "My answer."})
    response = client.post(f"/student/api/attempts/{attempt['id']}/submit", json={"answers": answers})
    assert response.status_code == 200, response.get_data(as_text=True)
    return attempt


def _overview(app):
    from app.blueprints.marking import posttest_overview

    with app.app_context():
        return posttest_overview()


def test_marking_needs_an_instructor(marking):
    assert marking.test_client().get("/instructor/marking").status_code in (302, 401, 403)


def test_dashboard_links_to_marking(marking):
    page = marking.test_client().get("/instructor/dashboard", headers=HEADERS).get_data(as_text=True)
    assert 'href="/instructor/marking/"' in page


def test_multiple_choice_decides_who_needs_marking(marking):
    version = _publish(marking.test_client())
    _take(marking, marking.test_client(), version, mc_right=7)  # 7 of 10: passed without marking
    _take(marking, marking.test_client(), version, mc_right=3)  # 3 + 3 < 7: cannot pass
    _take(marking, marking.test_client(), version, mc_right=5)  # needs 2 of the 3 written
    results = sorted((e["mc_score"], e["result"], e["needs_marking"]) for e in _overview(marking))
    assert results == [(3.0, "not passed", False), (5.0, "still marking", True), (7.0, "passed", False)]
    page = marking.test_client().get("/instructor/marking", headers=HEADERS).get_data(as_text=True)
    assert page.count("Save mark") == 3  # only the open student's three answers
    assert "Point A" in page and "Point B" in page


def test_written_item_is_right_only_with_every_key_point(marking):
    version = _publish(marking.test_client())
    _take(marking, marking.test_client(), version, mc_right=5)
    client = marking.test_client()
    items = {i["item_id"]: i for i in _overview(marking)[0]["to_mark"]}
    # w1 has two key points: one ticked is not right.
    client.post(f"/instructor/marking/posttest/{items['w1']['answer_id']}", data={"key_point": ["0"]}, headers=HEADERS)
    client.post(f"/instructor/marking/posttest/{items['w2']['answer_id']}", data={"key_point": ["0"]}, headers=HEADERS)
    entry = _overview(marking)[0]
    assert entry["written_score"] == 1.0 and entry["result"] == "still marking"
    client.post(f"/instructor/marking/posttest/{items['w3']['answer_id']}", data={"key_point": ["0"]}, headers=HEADERS)
    assert _overview(marking)[0]["result"] == "passed"


def test_marking_an_unknown_answer_is_refused(marking):
    response = marking.test_client().post("/instructor/marking/posttest/9999", data={}, headers=HEADERS)
    assert response.status_code == 400


def _student_id(app):
    with app.app_context():
        return get_db().execute("SELECT id FROM students ORDER BY id DESC").fetchone()["id"]


def _mark(client, student_id, point, try_number, result, note=""):
    return client.post(
        "/instructor/marking/lab-point",
        data={"student_id": student_id, "point": point, "try_number": try_number, "result": result, "note": note},
        headers=HEADERS,
    )


def test_lab_points_retry_and_certificate(marking):
    from app.blueprints.marking import certificate_rows

    version = _publish(marking.test_client())
    _take(marking, marking.test_client(), version, mc_right=7)
    sid = _student_id(marking)
    client = marking.test_client()
    assert _mark(client, sid, 1, 1, "not_yet").status_code == 400  # Not yet needs what was missing
    assert _mark(client, sid, 2, 2, "meets").status_code == 400  # no retry before a first try
    assert _mark(client, sid, 1, 1, "not_yet", "No false positive for the co-spend.").status_code == 302
    assert _mark(client, sid, 1, 2, "meets").status_code == 302
    for point in (2, 3):
        assert _mark(client, sid, point, 1, "meets").status_code == 302
    with marking.app_context():
        row = next(r for r in certificate_rows() if r["id"] == sid)
    assert row["posttest"] == "passed" and row["certificate"] == "not yet"
    assert row["points"][0]["text"] == "Not yet, then Meets on the retry"
    assert _mark(client, sid, 4, 1, "meets").status_code == 302
    with marking.app_context():
        row = next(r for r in certificate_rows() if r["id"] == sid)
    assert row["certificate"] == "yes"
    page = client.get("/instructor/marking", headers=HEADERS).get_data(as_text=True)
    assert "No false positive for the co-spend." in page


def test_first_try_cannot_become_meets_after_a_retry(marking):
    marking.test_client().post("/student/enroll")
    sid = _student_id(marking)
    client = marking.test_client()
    _mark(client, sid, 1, 1, "not_yet", "Missing the stop.")
    _mark(client, sid, 1, 2, "not_yet", "Still missing the stop.")
    assert _mark(client, sid, 1, 1, "meets").status_code == 400
    assert _mark(client, sid, 5, 1, "meets").status_code == 400


def test_lab_point_marks_are_in_the_full_export(marking):
    from app.migrate import FULL_EXPORT_TABLES

    assert "lab_point_marks" in FULL_EXPORT_TABLES
