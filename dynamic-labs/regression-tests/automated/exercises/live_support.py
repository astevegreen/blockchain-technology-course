from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path
from typing import Callable

import requests

try:
    import socketio
except ImportError:  # pragma: no cover
    socketio = None


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_URL = os.environ.get("EXERCISES_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("EXERCISES_REGRESSION_TIMEOUT", "120"))
DEFAULT_SOCKET_TIMEOUT_SECONDS = int(os.environ.get("EXERCISES_REGRESSION_SOCKET_TIMEOUT", "20"))
DEFAULT_CREDENTIALS_FILE = Path(
    os.environ.get(
        "EXERCISES_REGRESSION_CREDENTIALS_FILE",
        str(ROOT / ".runtime" / "instructor-credentials.txt"),
    )
)
DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE = Path(
    os.environ.get(
        "EXERCISES_REGRESSION_INSTRUCTOR_COOKIE_CACHE_FILE",
        str(ROOT / ".runtime" / "exercises-regression-instructor-cookie.json"),
    )
)
INSTRUCTOR_COOKIE_NAME = "hlf_instructor"



# The session, wait and login helpers live in ../live_common.py, shared by every lab's live_support.py.
# This file keeps the lab's own settings and the thin wrappers that pass them in.
_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

RegressionFailure = live_common.RegressionFailure
STUDENT_LAUNCHER = live_common.STUDENT_LAUNCHER
new_session = live_common.new_session
clear_cookie = live_common.clear_cookie
_session_has_valid_instructor_cookie = live_common.session_has_valid_instructor_cookie


def parse_instructor_credentials(path: Path = DEFAULT_CREDENTIALS_FILE) -> tuple[str, str]:
    return live_common.parse_instructor_credentials(path, "EXERCISES_REGRESSION_CREDENTIALS_FILE")


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


class SocketHarness:
    def __init__(
        self,
        connect_url: str,
        *,
        cookie_header: str = "",
        socketio_path: str = "socket.io",
        event_names: list[str] | tuple[str, ...] = (),
    ) -> None:
        if socketio is None:
            raise RegressionFailure(
                "python-socketio client dependencies are not installed. "
                "Use the runner container or install regression-tests/automated/exercises/requirements.txt."
            )
        self._condition = threading.Condition()
        self._events: dict[str, list[object]] = {}
        self.client = socketio.Client(
            reconnection=False,
            logger=False,
            engineio_logger=False,
            request_timeout=10,
        )
        for event_name in event_names:
            self.client.on(event_name, self._record(event_name))
        headers = {"Cookie": cookie_header} if cookie_header else None
        self.client.connect(
            connect_url,
            socketio_path=socketio_path,
            headers=headers,
            wait_timeout=10,
        )

    def _record(self, event_name: str):
        def handler(payload=None):
            with self._condition:
                self._events.setdefault(event_name, []).append(payload)
                self._condition.notify_all()

        return handler

    def emit(self, event_name: str, payload=None) -> None:
        if payload is None:
            self.client.emit(event_name)
            return
        self.client.emit(event_name, payload)

    def wait_for(
        self,
        event_name: str,
        predicate: Callable[[object], bool] | None = None,
        *,
        timeout_seconds: int = DEFAULT_SOCKET_TIMEOUT_SECONDS,
    ):
        deadline = time.time() + timeout_seconds
        with self._condition:
            while time.time() < deadline:
                for payload in self._events.get(event_name, []):
                    if predicate is None or predicate(payload):
                        return payload
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._condition.wait(min(0.5, remaining))
        seen = self._events.get(event_name, [])
        raise RegressionFailure(
            f"timed out waiting for socket event {event_name}: observed {len(seen)} payload(s)"
        )

    def events(self, event_name: str) -> list[object]:
        with self._condition:
            return list(self._events.get(event_name, []))

    def disconnect(self) -> None:
        if self.client.connected:
            self.client.disconnect()


def cookie_header(session: requests.Session) -> str:
    cookies = session.cookies.get_dict()
    return "; ".join(f"{name}={value}" for name, value in cookies.items())

