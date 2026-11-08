from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Callable

import requests


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_URL = os.environ.get("QUIZ_ENGINE_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("QUIZ_ENGINE_REGRESSION_TIMEOUT", "120"))
DEFAULT_CREDENTIALS_FILE = Path(
    os.environ.get(
        "QUIZ_ENGINE_REGRESSION_CREDENTIALS_FILE",
        str(ROOT / ".runtime" / "instructor-credentials.txt"),
    )
)
DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE = Path(
    os.environ.get(
        "QUIZ_ENGINE_REGRESSION_INSTRUCTOR_COOKIE_CACHE_FILE",
        str(ROOT / ".runtime" / "quiz-engine-regression-instructor-cookie.json"),
    )
)
INSTRUCTOR_COOKIE_NAME = "hlf_instructor"

_IDENTIFIER_RE = re.compile(r'<p id="student-identifier"><code>([^<]+)</code></p>')


# The session, wait and login helpers live in ../live_common.py, shared by every lab's live_support.py.
# This file keeps the lab's own settings and the thin wrappers that pass them in.
_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

RegressionFailure = live_common.RegressionFailure
new_session = live_common.new_session
clear_cookie = live_common.clear_cookie
_session_has_valid_instructor_cookie = live_common.session_has_valid_instructor_cookie


def parse_instructor_credentials(path: Path = DEFAULT_CREDENTIALS_FILE) -> tuple[str, str]:
    return live_common.parse_instructor_credentials(path, "QUIZ_ENGINE_REGRESSION_CREDENTIALS_FILE")


def wait_for_http(
    session: requests.Session,
    url: str,
    predicate: Callable[[requests.Response], bool],
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    interval_seconds: float = 1.0,
    description: str,
    allow_redirects: bool = True,
) -> requests.Response:
    return live_common.wait_for_http(
        session,
        url,
        predicate,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        description=description,
        allow_redirects=allow_redirects,
    )


def _load_cached_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> bool:
    return live_common.load_cached_instructor_cookie(
        session,
        base_url,
        [cache_path],
        INSTRUCTOR_COOKIE_NAME,
    )


def _persist_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> None:
    live_common.persist_instructor_cookie(session, base_url, cache_path, INSTRUCTOR_COOKIE_NAME)


def login_instructor(session: requests.Session, base_url: str = DEFAULT_BASE_URL) -> None:
    live_common.login_instructor(
        session,
        base_url,
        load_cached=lambda: _load_cached_instructor_cookie(session, base_url),
        credentials=parse_instructor_credentials,
        persist=lambda: _persist_instructor_cookie(session, base_url),
        max_retries=1,
        retry_delay=0.0,
    )


def instructor_csrf_token(session: requests.Session, base_url: str = DEFAULT_BASE_URL) -> str:
    response = session.post(f"{base_url}/quiz/api/instructor/csrf", timeout=10)
    if response.status_code != 200:
        raise RegressionFailure(
            f"csrf mint failed: status={response.status_code} body={response.text[:300]}"
        )
    token = response.json().get("token")
    if not token:
        raise RegressionFailure("csrf response did not include token")
    return token


def instructor_request(
    session: requests.Session,
    method: str,
    path: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    **kwargs,
) -> requests.Response:
    headers = dict(kwargs.pop("headers", {}) or {})
    if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        headers.setdefault("X-CSRFToken", instructor_csrf_token(session, base_url))
    return session.request(
        method,
        f"{base_url}{path}",
        headers=headers,
        timeout=kwargs.pop("timeout", 10),
        **kwargs,
    )


def seed_dummy_data_live(
    session: requests.Session,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    bank = _dummy_bank()
    ingest = instructor_request(
        session,
        "POST",
        "/quiz/instructor/api/ingest",
        base_url=base_url,
        json=bank,
    )
    if ingest.status_code not in (200, 201):
        raise RegressionFailure(f"ingest failed: {ingest.status_code} {ingest.text[:500]}")

    template = instructor_request(
        session,
        "POST",
        "/quiz/instructor/api/templates",
        base_url=base_url,
        json={
            "title": "Regression Template",
            "description": "Seeded by automated regression.",
            "criteria": {
                "lesson_ids": [bank["lesson_id"]],
                "question_types": ["multiple_choice"],
            },
            "question_count": 2,
            "selection_policy": "random",
            "timer_minutes": -1,
            "attempt_limit": 2,
            "result_policy": "score_and_answers_after_grading",
        },
    )
    if template.status_code != 201:
        raise RegressionFailure(f"template create failed: {template.status_code} {template.text[:500]}")
    template_payload = template.json()["template"]

    generated = instructor_request(
        session,
        "POST",
        f"/quiz/instructor/api/templates/{template_payload['id']}/generate",
        base_url=base_url,
        json={
            "random_seed": "quiz-engine-v2-regression",
            "question_order_policy": "fixed",
            "option_order_policy": "fixed",
        },
    )
    if generated.status_code != 201:
        raise RegressionFailure(f"quiz generate failed: {generated.status_code} {generated.text[:500]}")
    version = generated.json()["quiz_version"]

    updated = instructor_request(
        session,
        "PATCH",
        f"/quiz/instructor/api/quiz-versions/{version['id']}",
        base_url=base_url,
        json={
            "title": "Regression Visible Quiz",
            "description": "Visible quiz for full-stack regression.",
            "available_from": "2000-01-01T00:00:00+00:00",
            "available_until": "2999-01-01T00:00:00+00:00",
        },
    )
    if updated.status_code != 200:
        raise RegressionFailure(f"quiz metadata update failed: {updated.status_code} {updated.text[:500]}")
    version = updated.json()["quiz_version"]

    published = instructor_request(
        session,
        "POST",
        f"/quiz/instructor/api/quiz-versions/{version['id']}/publish",
        base_url=base_url,
    )
    if published.status_code != 200:
        raise RegressionFailure(f"quiz publish failed: {published.status_code} {published.text[:500]}")
    version = published.json()["quiz_version"]

    return {
        "lesson_id": bank["lesson_id"],
        "template_id": template_payload["id"],
        "quiz_version_id": version["id"],
        "quiz_title": version["title"],
        "questions": version["questions"],
    }


def enroll_student(session: requests.Session, base_url: str = DEFAULT_BASE_URL) -> str:
    response = session.post(f"{base_url}/quiz/student/enroll", timeout=10)
    if response.status_code != 200:
        raise RegressionFailure(f"student enroll failed: {response.status_code} {response.text[:300]}")
    match = _IDENTIFIER_RE.search(response.text)
    if not match:
        raise RegressionFailure("student enroll page did not expose identifier")
    return match.group(1)


def correct_answers_from_attempt(attempt: dict, seeded_questions: list[dict]) -> list[dict]:
    correct_by_stem = {}
    for question in seeded_questions:
        stem = question.get("question_stem") or question.get("snapshot_question_stem")
        correct = next(
            (option for option in question.get("options", []) if option.get("is_correct")),
            None,
        )
        if stem and correct:
            correct_by_stem[stem] = correct["option_text"]

    answers = []
    for question in attempt["questions"]:
        if question["question_type"] == "multiple_choice":
            correct_text = correct_by_stem[question["question_stem"]]
            selected = next(
                option for option in question["options"] if option["option_text"] == correct_text
            )
            answers.append(
                {
                    "question_id": question["id"],
                    "selected_option_id": selected["id"],
                }
            )
        else:
            answers.append(
                {
                    "question_id": question["id"],
                    "written_response": "Regression written response.",
                }
            )
    return answers


def _dummy_bank() -> dict:
    return {
        "lesson_id": "regression_v2_demo",
        "lesson_title": "Regression v2 Demo",
        "topic": "bitcoin",
        "tags": ["regression", "v2"],
        "questions": [
            {
                "id": "mc1",
                "question_stem": "Regression item 1: pick the first option.",
                "correct_answer": "First option",
                "incorrect_answers": ["Second option", "Third option"],
                "difficulty_level": 1,
                "explanation": "The first option is correct.",
            },
            {
                "id": "mc2",
                "question_stem": "Regression item 2: pick the second option.",
                "correct_answer": "Second option",
                "incorrect_answers": ["First option", "Third option"],
                "difficulty_level": 2,
                "explanation": "The second option is correct.",
            },
            {
                "id": "written1",
                "question_stem": "Regression written item: explain the concept.",
                "question_type": "written",
                "difficulty_level": 3,
                "explanation": "Written answers require instructor grading.",
            },
        ],
    }
