"""The host-side runner behind the quiz engine's lab hosting page (/instructor/hosting).

It runs on the lab host, never in a container: `./lab-manager.sh start quiz-engine-v2` starts it in the background.
It holds no Docker socket of its own; it runs `lab-manager.sh` exactly as an instructor at the host's shell would,
and only three ways: `start <lab|all>`, `stop <lab|all>` and `status all`, for the labs `lab-manager.sh list` names.
It listens on a Unix socket file in `.runtime/hosting-runner/`, which `compose.yaml` mounts into the quiz engine, so
nothing on any network can reach it, and every request carries HOSTING_RUNNER_SECRET, which `lab-manager.sh deploy`
generates into `.runtime/runtime-secrets.env`. Why this and not the Docker socket: README.md, "Lab hosting".

Standard library only, so the host's own python3 runs it: `python3 app/hosting_runner.py --help`. The quiz engine
imports the same file for the client half (`call`), so both ends share one protocol: one JSON object per line.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import socket
import socketserver
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

SECRET_NAME = "HOSTING_RUNNER_SECRET"
SOCKET_NAME = "runner.sock"
# The verbs the page may ask for. status only for every lab at once: it is one read of all of them.
VERBS = ("start", "stop", "status")
# Started by every `start` (router, course site, login) or with any lane lab (lane-service), so the page shows their
# status but gives them no buttons. The quiz engine is left off too: stopping it would take this page down mid-run.
NO_BUTTONS = ("router", "course-site", "instructor-auth-service", "lane-service", "quiz-engine-v2")
TARGET_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
MAX_REQUEST_BYTES = 4096
OUTPUT_TAIL_BYTES = 64 * 1024
KEEP_LOGS = 20


class RunnerUnavailable(Exception):
    """The quiz engine could not reach the runner or got no usable answer."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def refusal(verb, target, labs) -> str | None:
    """Why the runner will not run `lab-manager.sh <verb> <target>`, or None when it may."""
    if verb not in VERBS:
        return f"unknown action {verb!r}"
    if not isinstance(target, str) or not TARGET_PATTERN.match(target):
        return "unknown lab"
    if verb == "status":
        return None if target == "all" else "status is read for all labs at once"
    if target == "all" or target in labs:
        return None
    return f"{target} has no {verb} button on this page"


def read_secret(env_file: Path) -> str:
    """HOSTING_RUNNER_SECRET from the runtime env file (KEY=VALUE lines), or ''."""
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in lines:
        key, sep, value = line.partition("=")
        if sep and key.strip() == SECRET_NAME:
            return value.strip().strip("'\"")
    return ""


def list_labs(lab_manager: Path) -> list[str]:
    """The labs `lab-manager.sh list` names, less the ones the page gives no buttons."""
    proc = subprocess.run(
        ["bash", str(lab_manager), "list"],
        cwd=str(lab_manager.parent),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    names = [line.strip() for line in proc.stdout.splitlines()]
    return [n for n in names if TARGET_PATTERN.match(n) and n not in NO_BUTTONS]


class Runner:
    """Runs one lab-manager.sh command at a time and remembers the latest action and the latest status read."""

    def __init__(self, lab_manager: Path, state_dir: Path, secret, labs: list[str], popen=subprocess.Popen):
        """secret: the string, or a function that reads it (main re-reads the env file, so a rotation applies)."""
        if not callable(secret) and not secret:
            raise ValueError(f"{SECRET_NAME} is empty: run ./lab-manager.sh deploy, which generates it")
        self.lab_manager = Path(lab_manager)
        self.jobs_dir = Path(state_dir) / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.secret = secret
        self.labs = list(labs)
        self.popen = popen
        self.lock = threading.Lock()
        self.running: dict | None = None
        self.last_action: dict | None = None
        self.last_status: dict | None = None
        self.counter = 0

    # --- requests ---------------------------------------------------------------------------------

    def handle(self, request) -> dict:
        if not isinstance(request, dict):
            return {"ok": False, "error": "bad request"}
        offered = request.get("secret")
        expected = self.secret() if callable(self.secret) else self.secret
        if not (expected and isinstance(offered, str) and hmac.compare_digest(offered.encode(), expected.encode())):
            return {"ok": False, "error": "unauthorized"}
        action = request.get("action")
        if action == "state":
            return self.state()
        if action == "run":
            return self.run(request.get("verb"), request.get("target"))
        return {"ok": False, "error": "unknown request"}

    def state(self) -> dict:
        with self.lock:
            return {
                "ok": True,
                "labs": list(self.labs),
                "no_buttons": list(NO_BUTTONS),
                "running": self.view(self.running),
                "last_action": self.view(self.last_action),
                "last_status": self.view(self.last_status),
            }

    def run(self, verb, target) -> dict:
        reason = refusal(verb, target, self.labs)
        if reason:
            return {"ok": False, "error": reason}
        with self.lock:
            if self.running is not None:
                return {"ok": False, "error": f"busy: {self.running['command']} is still running"}
            try:
                job = self.start_job(verb, target)
            except OSError as exc:
                return {"ok": False, "error": f"could not run lab-manager.sh: {exc}"}
        # A start or stop is followed by a fresh status read, so the page shows what it changed.
        follow = verb != "status"
        threading.Thread(target=self.finish, args=(job, follow), daemon=True).start()
        return {"ok": True, "job": self.view(job)}

    # --- jobs -------------------------------------------------------------------------------------

    def start_job(self, verb: str, target: str) -> dict:
        """Start `lab-manager.sh <verb> <target>`; its output goes to a log file, not a pipe, so it outlives us."""
        self.counter += 1
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        log = self.jobs_dir / f"{stamp}-{self.counter:03d}-{verb}-{target}.log"
        with open(log, "wb") as out:
            proc = self.popen(
                ["bash", str(self.lab_manager), verb, target],
                cwd=str(self.lab_manager.parent),
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        job = {
            "verb": verb,
            "target": target,
            "command": f"./lab-manager.sh {verb} {target}",
            "started": utc_now(),
            "finished": None,
            "exit_code": None,
            "log": log,
            "proc": proc,
        }
        self.running = job
        self.prune_logs()
        return job

    def finish(self, job: dict, follow: bool) -> None:
        code = job["proc"].wait()
        with self.lock:
            job["exit_code"] = code
            job["finished"] = utc_now()
            if job["verb"] == "status":
                self.last_status = job
            else:
                self.last_action = job
            self.running = None
            next_job = None
            if follow:
                try:
                    next_job = self.start_job("status", "all")
                except OSError:
                    next_job = None
        if next_job is not None:
            self.finish(next_job, False)

    def prune_logs(self) -> None:
        logs = sorted(self.jobs_dir.glob("*.log"))
        for old in logs[:-KEEP_LOGS]:
            try:
                old.unlink()
            except OSError:
                pass

    @staticmethod
    def view(job: dict | None) -> dict | None:
        if job is None:
            return None
        try:
            with open(job["log"], "rb") as fh:
                fh.seek(0, os.SEEK_END)
                size = fh.tell()
                fh.seek(max(0, size - OUTPUT_TAIL_BYTES))
                output = fh.read().decode("utf-8", "replace")
            if size > OUTPUT_TAIL_BYTES:
                output = "[earlier output cut]\n" + output.split("\n", 1)[-1]
        except OSError:
            output = ""
        shown = {key: job[key] for key in ("verb", "target", "command", "started", "finished", "exit_code")}
        shown["output"] = output
        return shown


# --- the socket -----------------------------------------------------------------------------------


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline(MAX_REQUEST_BYTES + 1)
        if len(line) > MAX_REQUEST_BYTES:
            answer = {"ok": False, "error": "request too large"}
        else:
            try:
                answer = self.server.runner.handle(json.loads(line.decode("utf-8")))
            except (ValueError, UnicodeDecodeError):
                answer = {"ok": False, "error": "bad request"}
        self.wfile.write(json.dumps(answer).encode("utf-8") + b"\n")


def serve(runner: Runner, socket_path: Path):
    """Listen on socket_path until killed. Mode 0666: the quiz engine runs as another uid; the secret is the lock."""
    if not hasattr(socketserver, "ThreadingUnixStreamServer"):
        raise SystemExit("this runner needs Unix sockets (Linux or macOS)")
    socket_path = Path(socket_path)
    if socket_path.exists() or socket_path.is_symlink():
        socket_path.unlink()
    server = socketserver.ThreadingUnixStreamServer(str(socket_path), _Handler)
    server.daemon_threads = True
    server.runner = runner
    os.chmod(socket_path, 0o666)
    return server


def call(socket_path, payload: dict, timeout: float = 10.0) -> dict:
    """The quiz engine's half: send one request, read one answer. Raises RunnerUnavailable."""
    if not hasattr(socket, "AF_UNIX"):
        raise RunnerUnavailable("this system has no Unix sockets")
    data = json.dumps(payload).encode("utf-8") + b"\n"
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(str(socket_path))
            sock.sendall(data)
            chunks = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                if chunk.endswith(b"\n"):
                    break
    except OSError as exc:
        raise RunnerUnavailable(f"cannot reach the hosting runner at {socket_path}: {exc}") from exc
    try:
        answer = json.loads(b"".join(chunks).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise RunnerUnavailable("the hosting runner gave an answer that is not JSON") from exc
    if not isinstance(answer, dict):
        raise RunnerUnavailable("the hosting runner gave an answer that is not a JSON object")
    return answer


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lab-manager", required=True, type=Path, help="path to dynamic-labs/lab-manager.sh")
    parser.add_argument("--dir", required=True, type=Path, help="state folder (.runtime/hosting-runner)")
    parser.add_argument("--env-file", required=True, type=Path, help=".runtime/runtime-secrets.env")
    args = parser.parse_args(argv)

    secret = read_secret(args.env_file)
    if not secret:
        print(f"{SECRET_NAME} is not in {args.env_file}: run ./lab-manager.sh deploy", file=sys.stderr)
        return 1
    lab_manager = args.lab_manager.resolve()
    runner = Runner(lab_manager, args.dir, lambda: read_secret(args.env_file), list_labs(lab_manager))
    server = serve(runner, args.dir / SOCKET_NAME)
    print(f"{utc_now()} hosting runner listening on {args.dir / SOCKET_NAME} for {', '.join(runner.labs)}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
