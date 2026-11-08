"""The session, wait and login helpers the labs' live_support.py files share.

Each lab's live_support.py imports this module (as run-lab.sh is shared by the runners) and keeps what is its own:
its settings (base URL, timeouts, cookie cache file), its claim and terminal helpers, and thin wrappers that hand
those settings to the functions here. Nothing in this module reads a lab's settings, so a wait, timeout or retry
count is whatever the lab's wrapper passes in.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse, urlunparse

import requests

USERNAME_RE = re.compile(r"^Username:\s*(.+)$", re.MULTILINE)
PASSWORD_RE = re.compile(r"^Password:\s*(.+)$", re.MULTILINE)
ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
OSC_RE = re.compile(r"\x1B\].*?(?:\x07|\x1B\\)")


class RegressionFailure(RuntimeError):
    pass


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


def to_websocket_url(http_url: str) -> str:
    parsed = urlparse(http_url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse(parsed._replace(scheme=ws_scheme))


def decode_terminal_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def strip_terminal_artifacts(text: str) -> str:
    text = OSC_RE.sub("", text)
    text = ANSI_RE.sub("", text)
    text = text.replace("\r", "")
    return text


def parse_instructor_credentials(path: Path, env_var: str) -> tuple[str, str]:
    """Read the instructor's Username/Password lines; env_var names the lab's setting for the file in the error."""
    if not path.exists():
        raise RegressionFailure(
            f"instructor credentials file not found: {path}. "
            f"Run deploy first or point {env_var} at a valid file."
        )
    content = path.read_text(encoding="utf-8")
    username = USERNAME_RE.search(content)
    password = PASSWORD_RE.search(content)
    if not username or not password:
        raise RegressionFailure(f"could not parse instructor credentials from {path}")
    return username.group(1).strip(), password.group(1).strip()


def wait_for_http(
    session: requests.Session,
    url: str,
    predicate: Callable[[requests.Response], bool],
    *,
    timeout_seconds: int,
    interval_seconds: float,
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
            f"timed out waiting for {description}: "
            f"last status={last_response.status_code} url={last_response.url}"
        )
    raise RegressionFailure(f"timed out waiting for {description}: last error={last_error}")


def session_has_valid_instructor_cookie(session: requests.Session, base_url: str) -> bool:
    try:
        response = session.get(f"{base_url}/api/instructor/whoami", timeout=10)
    except requests.RequestException:
        return False
    if response.status_code != 200:
        return False
    payload = response.json()
    return bool(payload.get("authenticated"))


def candidate_cookie_cache_paths(cache_path: Path, root: Path) -> list[Path]:
    """The lab's own cache file first, then every lab's cache file under <root>/.runtime."""
    candidates = [cache_path]
    runtime_dir = root / ".runtime"
    try:
        for path in sorted(runtime_dir.glob("*-regression-instructor-cookie.json")):
            if path not in candidates:
                candidates.append(path)
    except OSError:
        pass
    return candidates


def load_cached_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_paths: list[Path],
    cookie_name: str,
    *,
    match_base_url: bool = True,
    max_age_seconds: float | None = None,
    after_valid: Callable[[], None] | None = None,
) -> bool:
    """Try each cached cookie in turn; True once one passes the whoami probe."""
    for candidate in cache_paths:
        if not candidate.exists():
            continue
        try:
            # Instructor cookies expire 1 h after login, with no renewal; an older cached one passes the probe
            # and then expires mid-suite. Only labs that pass max_age_seconds skip stale files.
            if max_age_seconds is not None and time.time() - candidate.stat().st_mtime > max_age_seconds:
                continue
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if match_base_url and payload.get("base_url") != base_url:
            continue
        cookie_value = (payload.get("cookie_value") or "").strip()
        if not cookie_value:
            continue
        session.cookies.set(cookie_name, cookie_value, path="/")
        if session_has_valid_instructor_cookie(session, base_url):
            if after_valid is not None:
                after_valid()
            return True
        clear_cookie(session, cookie_name)
    return False


def persist_instructor_cookie(
    session: requests.Session,
    base_url: str,
    cache_path: Path,
    cookie_name: str,
) -> None:
    cookie_value = session.cookies.get(cookie_name)
    if not cookie_value:
        return
    payload = {
        "base_url": base_url,
        "cookie_name": cookie_name,
        "cookie_value": cookie_value,
    }
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        return


def login_instructor(
    session: requests.Session,
    base_url: str,
    *,
    load_cached: Callable[[], bool],
    credentials: Callable[[], tuple[str, str]],
    persist: Callable[[], None],
    max_retries: int,
    retry_delay: float,
    after_login: Callable[[], None] | None = None,
) -> None:
    """Reuse a cached instructor cookie, else log in, retrying a 429 after retry_delay * attempt seconds.

    max_retries=1 means no retry. after_login runs after a 200 and before the cookie is probed.
    """
    if load_cached():
        return

    username, password = credentials()
    for attempt in range(1, max_retries + 1):
        response = session.post(
            f"{base_url}/api/instructor/login",
            json={"user": username, "key": password},
            timeout=10,
        )
        if response.status_code == 200:
            if after_login is not None:
                after_login()
            if not session_has_valid_instructor_cookie(session, base_url):
                raise RegressionFailure("instructor login did not yield a usable instructor session")
            persist()
            return
        if response.status_code == 429 and attempt < max_retries:
            time.sleep(retry_delay * attempt)
            continue
        raise RegressionFailure(
            f"instructor login failed: status={response.status_code} body={response.text[:300]}"
        )
