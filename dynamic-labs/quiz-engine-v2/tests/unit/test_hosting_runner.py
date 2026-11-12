"""The host-side lab hosting runner: what it refuses, what it runs, and its socket protocol."""

import socket
import threading

import pytest

from app import hosting_runner
from app.hosting_runner import Runner, refusal

LABS = ["bitcoin", "tokens"]
SECRET = "s3cret"


class FakeProc:
    def __init__(self, release):
        self.release = release

    def wait(self):
        self.release.wait(5)
        return 0


class FakePopen:
    """Records each command and writes a line to its log; the job ends when `release` is set."""

    def __init__(self):
        self.calls = []
        self.release = threading.Event()

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        kwargs["stdout"].write(f"ran {' '.join(args[2:])}\n".encode())
        return FakeProc(self.release)


@pytest.fixture
def runner(tmp_path):
    popen = FakePopen()
    lab_manager = tmp_path / "lab-manager.sh"
    lab_manager.write_text("#!/bin/bash\n")
    return Runner(lab_manager, tmp_path / "state", SECRET, LABS, popen=popen), popen


@pytest.mark.parametrize(
    "verb,target",
    [("start", "bitcoin"), ("stop", "tokens"), ("start", "all"), ("stop", "all"), ("status", "all")],
)
def test_allowlisted_commands_pass(verb, target):
    assert refusal(verb, target, LABS) is None


@pytest.mark.parametrize(
    "verb,target",
    [
        ("deploy", "all"),
        ("rm", "bitcoin"),
        ("start", "router"),
        ("stop", "quiz-engine-v2"),
        ("start", "bitcoin; rm -rf /"),
        ("start", "--help"),
        ("start", ""),
        ("start", None),
        ("status", "bitcoin"),
    ],
)
def test_anything_else_is_refused(verb, target):
    assert refusal(verb, target, LABS) is not None


def test_wrong_or_missing_secret_is_unauthorized(runner):
    r, popen = runner
    for request in ({"action": "state"}, {"action": "state", "secret": "nope"}, {"action": "state", "secret": 5}):
        assert r.handle(request) == {"ok": False, "error": "unauthorized"}
    assert r.handle({"action": "run", "verb": "start", "target": "bitcoin", "secret": "x"})["ok"] is False
    assert popen.calls == []


def test_secret_is_read_on_each_request(tmp_path):
    current = {"value": "old"}
    r = Runner(tmp_path / "lab-manager.sh", tmp_path / "state", lambda: current["value"], LABS)
    assert r.handle({"action": "state", "secret": "old"})["ok"] is True
    current["value"] = "new"
    assert r.handle({"action": "state", "secret": "old"})["error"] == "unauthorized"
    current["value"] = ""
    assert r.handle({"action": "state", "secret": ""})["error"] == "unauthorized"


def test_empty_secret_refuses_to_start(tmp_path):
    with pytest.raises(ValueError):
        Runner(tmp_path / "lab-manager.sh", tmp_path / "state", "", LABS)


def test_run_starts_lab_manager_without_a_shell_then_reads_status(runner):
    r, popen = runner
    answer = r.handle({"action": "run", "verb": "start", "target": "bitcoin", "secret": SECRET})
    assert answer["ok"] is True
    args, kwargs = popen.calls[0]
    assert args[0] == "bash" and args[1].endswith("lab-manager.sh") and args[2:] == ["start", "bitcoin"]
    assert "shell" not in kwargs and kwargs["start_new_session"] is True

    busy = r.handle({"action": "run", "verb": "stop", "target": "bitcoin", "secret": SECRET})
    assert busy["ok"] is False and busy["error"].startswith("busy")

    state = r.handle({"action": "state", "secret": SECRET})
    assert state["running"]["command"] == "./lab-manager.sh start bitcoin"
    assert "ran start bitcoin" in state["running"]["output"]
    assert "proc" not in state["running"] and "log" not in state["running"]

    popen.release.set()
    for _ in range(100):
        state = r.state()
        if state["running"] is None and state["last_status"]:
            break
        threading.Event().wait(0.02)
    assert [call[0][2:] for call in popen.calls] == [["start", "bitcoin"], ["status", "all"]]
    assert state["last_action"]["exit_code"] == 0
    assert "ran status all" in state["last_status"]["output"]


def test_refused_run_starts_nothing(runner):
    r, popen = runner
    answer = r.handle({"action": "run", "verb": "deploy", "target": "all", "secret": SECRET})
    assert answer["ok"] is False
    assert popen.calls == []


def test_long_output_shows_only_its_tail(runner, tmp_path):
    r, _ = runner
    log = tmp_path / "big.log"
    log.write_bytes(b"x" * 10 + b"\n" + b"y" * (hosting_runner.OUTPUT_TAIL_BYTES + 100) + b"\nlast line\n")
    shown = Runner.view(
        {"verb": "status", "target": "all", "command": "c", "started": "s", "finished": "f", "exit_code": 0, "log": log}
    )
    assert shown["output"].startswith("[earlier output cut]")
    assert shown["output"].endswith("last line\n")


def test_read_secret(tmp_path):
    env = tmp_path / "runtime-secrets.env"
    env.write_text("LANE_SERVICE_SECRET=a\nHOSTING_RUNNER_SECRET=abc123\n")
    assert hosting_runner.read_secret(env) == "abc123"
    assert hosting_runner.read_secret(tmp_path / "missing.env") == ""


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX") or not hasattr(hosting_runner.socketserver,
                    "ThreadingUnixStreamServer"), reason="needs Unix sockets")
def test_socket_round_trip(runner, tmp_path):
    r, _ = runner
    path = tmp_path / "r.sock"
    server = hosting_runner.serve(r, path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert hosting_runner.call(path, {"action": "state", "secret": SECRET})["labs"] == LABS
        assert hosting_runner.call(path, {"action": "state"})["error"] == "unauthorized"
    finally:
        server.shutdown()
        server.server_close()


def test_call_reports_an_absent_runner(tmp_path):
    with pytest.raises(hosting_runner.RunnerUnavailable):
        hosting_runner.call(tmp_path / "nobody-here.sock", {"action": "state"}, timeout=1)
