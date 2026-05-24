from __future__ import annotations

import json
import os
import re
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

_USERNAME_RE = re.compile(r"^Username:\s*(.+)$", re.MULTILINE)
_PASSWORD_RE = re.compile(r"^Password:\s*(.+)$", re.MULTILINE)


class RegressionFailure(RuntimeError):
    pass


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

    def disconnect(self) -> None:
        if self.client.connected:
            self.client.disconnect()


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def clear_cookie(session: requests.Session, cookie_name: str) -> None:
    for cookie in list(session.cookies):
        if cookie.name == cookie_name:
            session.cookies.clear(domain=cookie.domain, path=cookie.path, name=cookie.name)


def cookie_header(session: requests.Session) -> str:
    cookies = session.cookies.get_dict()
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def parse_instructor_credentials(path: Path = DEFAULT_CREDENTIALS_FILE) -> tuple[str, str]:
    if not path.exists():
        raise RegressionFailure(
            f"instructor credentials file not found: {path}. "
            "Run deploy first or point EXERCISES_REGRESSION_CREDENTIALS_FILE at a valid file."
        )
    content = path.read_text(encoding="utf-8")
    username = _USERNAME_RE.search(content)
    password = _PASSWORD_RE.search(content)
    if not username or not password:
        raise RegressionFailure(f"could not parse instructor credentials from {path}")
    return username.group(1).strip(), password.group(1).strip()


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
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    last_response: requests.Response | None = None
    while time.time() < deadline:
        try:
            response = session.get(url, timeout=10, allow_redirects=allow_redirects)
            last_response = response
            if predicate(response):
                return response
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(interval_seconds)
    if last_response is not None:
        raise RegressionFailure(
            f"timed out waiting for {description}: last status={last_response.status_code} url={last_response.url}"
        )
    raise RegressionFailure(f"timed out waiting for {description}: last error={last_error}")


def _session_has_valid_instructor_cookie(
    session: requests.Session,
    base_url: str,
) -> bool:
    try:
        response = session.get(f"{base_url}/api/instructor/whoami", timeout=10)
    except requests.RequestException:
        return False
    if response.status_code != 200:
        return False
    payload = response.json()
    return bool(payload.get("authenticated"))


def _load_cached_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> bool:
    if not cache_path.exists():
        return False
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if payload.get("base_url") != base_url:
        return False
    cookie_value = (payload.get("cookie_value") or "").strip()
    if not cookie_value:
        return False
    session.cookies.set(INSTRUCTOR_COOKIE_NAME, cookie_value, path="/")
    if _session_has_valid_instructor_cookie(session, base_url):
        return True
    clear_cookie(session, INSTRUCTOR_COOKIE_NAME)
    return False


def _persist_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path = DEFAULT_INSTRUCTOR_COOKIE_CACHE_FILE,
) -> None:
    cookie_value = session.cookies.get(INSTRUCTOR_COOKIE_NAME)
    if not cookie_value:
        return
    payload = {
        "base_url": base_url,
        "cookie_name": INSTRUCTOR_COOKIE_NAME,
        "cookie_value": cookie_value,
    }
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        return


def login_instructor(session: requests.Session, base_url: str = DEFAULT_BASE_URL) -> None:
    if _load_cached_instructor_cookie(session, base_url):
        return

    username, password = parse_instructor_credentials()
    response = session.post(
        f"{base_url}/api/instructor/login",
        json={"user": username, "key": password},
        timeout=10,
    )
    if response.status_code != 200:
        raise RegressionFailure(
            f"instructor login failed: status={response.status_code} body={response.text[:300]}"
        )
    if not _session_has_valid_instructor_cookie(session, base_url):
        raise RegressionFailure("instructor login did not yield a usable instructor session")
    _persist_instructor_cookie(session, base_url)
