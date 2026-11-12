"""/instructor/hosting: the page reads the runner's state and every button posts one allowlisted command."""

import pytest

from app import hosting_runner
from app.blueprints import hosting

HEADERS = {"X-Test-Instructor": "teacher"}

STATUS_OUTPUT = """=== router ===
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
router-1  nginx     "nginx"   router    1h        Up 1h
=== bitcoin ===
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
btc-1     btc       "x"       node      1h        Up 1h
btc-2     btc       "x"       miner     1h        Up 1h
=== tokens ===
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
"""


def _state(**overrides):
    state = {
        "ok": True,
        "labs": ["bitcoin", "tokens"],
        "no_buttons": ["router", "quiz-engine-v2"],
        "running": None,
        "last_action": None,
        "last_status": {
            "verb": "status", "target": "all", "command": "./lab-manager.sh status all",
            "started": "2026-11-12 10:00:00 UTC", "finished": "2026-11-12 10:00:05 UTC", "exit_code": 0,
            "output": STATUS_OUTPUT,
        },
    }
    state.update(overrides)
    return state


@pytest.fixture
def runner_calls(monkeypatch):
    calls = []

    def fake(payload):
        calls.append(payload)
        if payload["action"] == "state":
            return _state()
        return {"ok": True}

    monkeypatch.setattr(hosting, "call_runner", fake)
    return calls


def test_page_lists_labs_with_status_and_buttons(client, runner_calls):
    response = client.get("/instructor/hosting", headers=HEADERS)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Starting from cold is not on this page" in html
    assert "./lab-manager.sh deploy --mode instructor --max-student-capacity 20" in html
    assert "./lab-manager.sh start quiz-engine-v2" in html
    assert "running (2 containers)" in html
    assert "tokens</td>\n          <td>not running" in html
    assert "router: running (1 container)" in html
    assert "quiz-engine-v2: not checked" in html  # absent from that status read
    assert 'name="target" value="bitcoin"' in html
    assert 'name="target" value="router"' not in html
    assert "Stop all" in html and "Start all" in html
    assert runner_calls == [{"action": "state"}]


def test_button_posts_the_command(client, runner_calls):
    response = client.post(
        "/instructor/hosting/run", data={"verb": "start", "target": "bitcoin"}, headers=HEADERS
    )
    assert response.status_code == 302
    assert "/instructor/hosting" in response.headers["Location"]
    assert runner_calls == [{"action": "run", "verb": "start", "target": "bitcoin"}]


@pytest.mark.parametrize(
    "data",
    [
        {"verb": "deploy", "target": "all"},
        {"verb": "start", "target": "bitcoin && reboot"},
        {"verb": "status", "target": "bitcoin"},
        {"verb": "stop", "target": "all"},  # Stop all without the confirm box
    ],
)
def test_bad_or_unconfirmed_commands_never_reach_the_runner(client, runner_calls, data):
    response = client.post("/instructor/hosting/run", data=data, headers=HEADERS)
    assert response.status_code == 302
    assert runner_calls == []


def test_stop_all_with_confirm_is_sent(client, runner_calls):
    client.post(
        "/instructor/hosting/run", data={"verb": "stop", "target": "all", "confirm": "yes"}, headers=HEADERS
    )
    assert runner_calls == [{"action": "run", "verb": "stop", "target": "all"}]


def test_runner_refusal_is_shown(client, monkeypatch):
    monkeypatch.setattr(hosting, "call_runner", lambda payload: {"ok": False, "error": "busy: x is still running"})
    response = client.post(
        "/instructor/hosting/run", data={"verb": "start", "target": "bitcoin"}, headers=HEADERS,
        follow_redirects=False,
    )
    assert "busy" in response.headers["Location"]


def test_runner_unavailable_shows_the_shell_commands(client, monkeypatch):
    def unavailable(payload):
        raise hosting_runner.RunnerUnavailable("cannot reach the hosting runner")

    monkeypatch.setattr(hosting, "call_runner", unavailable)
    html = client.get("/instructor/hosting", headers=HEADERS).get_data(as_text=True)
    assert "The hosting runner is not answering" in html
    assert "cannot reach the hosting runner" in html
    assert "./lab-manager.sh start &lt;lab&gt;" in html
    assert "<button" not in html


def test_running_job_refreshes_the_page(client, monkeypatch):
    running = {"command": "./lab-manager.sh start tokens", "started": "now", "output": "\x1b[32mStarting tokens\x1b[0m"}
    monkeypatch.setattr(hosting, "call_runner", lambda payload: _state(running=running))
    html = client.get("/instructor/hosting", headers=HEADERS).get_data(as_text=True)
    assert 'http-equiv="refresh"' in html
    assert "Starting tokens" in html and "\x1b" not in html
    assert "disabled" in html


def test_call_runner_without_a_secret_is_unavailable(app, monkeypatch):
    monkeypatch.delenv("QUIZ_ENGINE_HOSTING_RUNNER_SECRET", raising=False)
    with app.app_context():
        with pytest.raises(hosting_runner.RunnerUnavailable):
            hosting.call_runner({"action": "state"})


def test_call_runner_sends_the_secret(app, monkeypatch):
    sent = {}

    def fake_call(path, payload):
        sent.update(path=path, payload=payload)
        return {"ok": True}

    monkeypatch.setattr(hosting_runner, "call", fake_call)
    monkeypatch.setenv("QUIZ_ENGINE_HOSTING_RUNNER_SECRET", "abc")
    with app.app_context():
        hosting.call_runner({"action": "state"})
    assert sent == {"path": hosting.DEFAULT_SOCKET, "payload": {"action": "state", "secret": "abc"}}


def test_hosting_buttons_need_csrf_with_cookie_login(app_factory, monkeypatch, runner_calls):
    monkeypatch.setenv("INSTRUCTOR_AUTH_MODE", "standalone")
    monkeypatch.setenv("INSTRUCTOR_AUTH_SECRET", "standalone-secret")
    monkeypatch.setenv("INSTRUCTOR_PASSWORD", "admin")
    monkeypatch.setenv("FLASK_ENV", "development")
    client = app_factory(INSTRUCTOR_AUTH_MODE="standalone").test_client()
    client.post("/instructor/login", data={"username": "teacher", "password": "admin"})

    html = client.get("/instructor/hosting").get_data(as_text=True)
    assert 'name="_csrf_token"' in html

    refused = client.post("/instructor/hosting/run", data={"verb": "start", "target": "bitcoin"})
    assert refused.status_code == 403
    assert runner_calls == [{"action": "state"}]

    token = client.post("/api/instructor/csrf").get_json()["token"]
    accepted = client.post(
        "/instructor/hosting/run", data={"verb": "start", "target": "bitcoin"}, headers={"X-CSRFToken": token}
    )
    assert accepted.status_code == 302
    assert runner_calls[-1] == {"action": "run", "verb": "start", "target": "bitcoin"}
