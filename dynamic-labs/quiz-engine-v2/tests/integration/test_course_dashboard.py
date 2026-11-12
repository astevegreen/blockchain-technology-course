import json
import os
from pathlib import Path

import pytest

HEADERS = {"X-Test-Instructor": "teacher"}


def _quizes_dir():
    """The full quizes folder: the dashboard also reads posttest/ and run-sheet/, which
    tools/check.py's sample folder (quiz_json/ only) leaves out."""
    candidates = []
    configured = os.environ.get("QUIZ_ENGINE_SAMPLE_QUIZ_DIR")
    if configured:
        candidates.append(Path(configured))
    here = Path(__file__).resolve()
    if len(here.parents) > 4:
        candidates.append(here.parents[4] / "quizes")
    for candidate in candidates:
        if (candidate / "posttest").is_dir() and (candidate / "run-sheet").is_dir():
            return candidate
    pytest.skip("the full quizes folder is not available")


@pytest.fixture
def dash_client(app_factory):
    app = app_factory(QUIZES_DIR=str(_quizes_dir()))
    return app.test_client()


def test_dashboard_needs_an_instructor(dash_client):
    assert dash_client.get("/instructor/dashboard").status_code in (302, 401, 403)


def test_dashboard_lists_links_and_bank_buttons(dash_client):
    page = dash_client.get("/instructor/dashboard", headers=HEADERS)
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "Run sheet" in body
    assert "Class code" in body
    assert "quiz_json/daily_d2_review_of_day1-quiz-bank.json" in body
    assert "quiz_json/weekone_check-quiz-bank.json" in body
    assert "posttest/posttest_day10-quiz-bank.json" in body
    # The pretest is taken on the public site, never loaded from here.
    assert "pretest_week1" not in body
    # The daily bank sits in its own group, not again among the lesson banks.
    assert body.count('value="quiz_json/daily_d2_review_of_day1-quiz-bank.json"') == 1


def test_missing_hosting_and_pretest_pages_say_not_built(dash_client):
    body = dash_client.get("/instructor/dashboard", headers=HEADERS).get_data(as_text=True)
    for label in ("Lab hosting", "Pretest results"):
        assert label in body


def test_load_one_bank(dash_client):
    response = dash_client.post(
        "/instructor/dashboard/load",
        data={"bank": "quiz_json/weekone_check-quiz-bank.json"},
        headers=HEADERS,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200, body
    assert "1 bank(s) loaded" in body


def test_load_a_group(dash_client):
    response = dash_client.post(
        "/instructor/dashboard/load", data={"group": "checks"}, headers=HEADERS
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200, body
    assert "weekone_check" in body and "weektwo_check" in body


def test_loading_twice_is_safe(dash_client):
    data = {"bank": "posttest/posttest_day10-quiz-bank.json"}
    first = dash_client.post("/instructor/dashboard/load", data=data, headers=HEADERS)
    second = dash_client.post("/instructor/dashboard/load", data=data, headers=HEADERS)
    assert first.status_code == 200, first.get_data(as_text=True)
    assert second.status_code == 200, second.get_data(as_text=True)


@pytest.mark.parametrize(
    "bank",
    ["../README.md", "pretest/pretest_week1-quiz-bank.json", "/etc/passwd", ""],
)
def test_refuses_banks_the_page_does_not_offer(dash_client, bank):
    response = dash_client.post(
        "/instructor/dashboard/load", data={"bank": bank}, headers=HEADERS
    )
    assert response.status_code == 400
    assert "not a bank this page offers" in response.get_data(as_text=True)


def test_missing_quizes_folder_is_explained(app_factory, tmp_path):
    client = app_factory(QUIZES_DIR=str(tmp_path / "absent")).test_client()
    body = client.get("/instructor/dashboard", headers=HEADERS).get_data(as_text=True)
    assert "not mounted" in body
    assert client.post(
        "/instructor/dashboard/load", data={"group": "daily"}, headers=HEADERS
    ).status_code == 400


def test_run_sheet_is_served(dash_client):
    response = dash_client.get("/instructor/dashboard/run-sheet", headers=HEADERS)
    assert response.status_code == 200
    assert "Day 1" in response.get_data(as_text=True)
