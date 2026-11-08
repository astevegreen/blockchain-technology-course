from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Callable

import requests


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_URL = os.environ.get("CRYPTOGRAPHY_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("CRYPTOGRAPHY_REGRESSION_TIMEOUT", "120"))
DEFAULT_CREDENTIALS_FILE = Path(
    os.environ.get(
        "CRYPTOGRAPHY_REGRESSION_CREDENTIALS_FILE",
        str(ROOT / ".runtime" / "instructor-credentials.txt"),
    )
)
DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE = Path(
    os.environ.get(
        "CRYPTOGRAPHY_REGRESSION_INSTRUCTOR_COOKIE_CACHE_FILE",
        str(ROOT / ".runtime" / "cryptography-regression-instructor-cookie.json"),
    )
)
DEFAULT_EXEC_CONTAINER = os.environ.get(
    "CRYPTOGRAPHY_REGRESSION_EXEC_CONTAINER",
    "crypto-lab-student-1",
)
INSTRUCTOR_COOKIE_NAME = "hlf_instructor"



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
    return live_common.parse_instructor_credentials(path, "CRYPTOGRAPHY_REGRESSION_CREDENTIALS_FILE")


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


def set_cryptography_session_cookie(session: requests.Session, session_id: str) -> None:
    session.cookies.set("crypto_lab_session", session_id, path="/")


def docker_exec(container: str, command: str, *, timeout_seconds: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "docker",
            "exec",
            container,
            "timeout",
            "--signal=TERM",
            "--kill-after=5",
            f"{timeout_seconds}s",
            "bash",
            "-lc",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 10,
    )


def docker_exec_checked(container: str, command: str, *, timeout_seconds: int = 60) -> str:
    result = docker_exec(container, command, timeout_seconds=timeout_seconds)
    if result.returncode != 0:
        raise RegressionFailure(
            "docker exec failed for "
            f"{container}: command={command!r} stdout={result.stdout[-400:]} stderr={result.stderr[-400:]}"
        )
    return result.stdout


def get_progress_summary(
    instructor_session: requests.Session,
    session_id: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    response = instructor_session.get(f"{base_url}/api/cryptography/progress", timeout=10)
    if response.status_code != 200:
        raise RegressionFailure(
            f"progress summary failed: status={response.status_code} body={response.text[:300]}"
        )
    progress = response.json().get("progress", {})
    if session_id not in progress:
        raise RegressionFailure(f"progress summary missing session {session_id}")
    return progress[session_id]


def get_progress_detail(
    instructor_session: requests.Session,
    session_id: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    response = instructor_session.get(
        f"{base_url}/api/cryptography/progress/{session_id}",
        timeout=10,
    )
    if response.status_code != 200:
        raise RegressionFailure(
            f"progress detail failed: status={response.status_code} body={response.text[:300]}"
        )
    payload = response.json()
    if not payload.get("success", True) and "detail" not in payload:
        raise RegressionFailure(f"progress detail missing payload for session {session_id}")
    return payload.get("detail", payload)

