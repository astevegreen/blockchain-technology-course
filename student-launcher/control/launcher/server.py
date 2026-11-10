"""The control page and its JSON API (docs/student-launcher-design.md section 5), on the standard library only."""
from __future__ import annotations

import json
import mimetypes
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__, messages
from .controller import Controller, Refused

STATIC = Path(__file__).resolve().parent.parent / "static"

ROUTES = [
    ("GET", re.compile(r"^/api/health$"), "health"),
    ("GET", re.compile(r"^/api/system$"), "system"),
    ("GET", re.compile(r"^/api/labs$"), "labs"),
    ("POST", re.compile(r"^/api/labs/(?P<lab>[a-z0-9][a-z0-9_-]*)/start$"), "start"),
    ("GET", re.compile(r"^/api/labs/(?P<lab>[a-z0-9][a-z0-9_-]*)/progress$"), "progress"),
    ("POST", re.compile(r"^/api/labs/(?P<lab>[a-z0-9][a-z0-9_-]*)/stop$"), "stop"),
    ("POST", re.compile(r"^/api/labs/(?P<lab>[a-z0-9][a-z0-9_-]*)/reset$"), "reset"),
    ("POST", re.compile(r"^/api/labs/(?P<lab>[a-z0-9][a-z0-9_-]*)/actions/(?P<action>[a-z0-9-]+)$"), "action"),
    ("GET", re.compile(r"^/api/update$"), "update"),
    ("POST", re.compile(r"^/api/shutdown$"), "shutdown"),
]


def dispatch(controller: Controller, method: str, path: str) -> tuple[int, dict]:
    """(status, JSON body) for an API request. Kept apart from the handler so tests call it directly."""
    path = path.split("?", 1)[0]
    allowed = False
    for verb, pattern, name in ROUTES:
        match = pattern.match(path)
        if not match:
            continue
        allowed = True
        if verb != method:
            continue
        args = match.groupdict()
        try:
            if name == "health":
                return 200, {"ok": True, "version": controller.release.version}
            if name == "system":
                return 200, controller.system()
            if name == "labs":
                return 200, {"labs": controller.labs()}
            if name == "start":
                return 202, controller.start(args["lab"])
            if name == "progress":
                return 200, controller.progress(args["lab"])
            if name == "stop":
                return 200, controller.stop(args["lab"])
            if name == "reset":
                return 200, controller.reset(args["lab"])
            if name == "action":
                return 202, controller.action(args["lab"], args["action"])
            if name == "update":
                return 200, controller.update()
            if name == "shutdown":
                return 200, controller.shutdown()
        except Refused as err:
            return err.status, {"error": True, "message": err.message}
        except Exception:  # noqa: BLE001 - never a stack trace on the student's page
            return 500, {"error": True, "message": messages.GENERIC.format(doing="talking to Docker")}
    if allowed:
        return 405, {"error": True, "message": "That button doesn't work that way."}
    return 404, {"error": True, "message": "There is nothing at this address."}


def make_handler(controller: Controller, on_shutdown=None):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"course-launcher/{__version__}"

        def log_message(self, fmt, *args):  # quiet: the wrapper shows no server log
            return

        def send_json(self, status: int, body: dict) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def same_origin(self) -> bool:
            """A web page elsewhere must not drive Docker through the student's browser (CSRF)."""
            origin = self.headers.get("Origin")
            if not origin:
                return True
            return bool(re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", origin))

        def do_GET(self):  # noqa: N802
            if self.path.startswith("/api/"):
                self.send_json(*dispatch(controller, "GET", self.path))
                return
            self.serve_static()

        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(min(length, 65536))
            if not self.same_origin():
                self.send_json(403, {"error": True, "message": "Use the control page to press buttons."})
                return
            status, body = dispatch(controller, "POST", self.path)
            self.send_json(status, body)
            if self.path.split("?", 1)[0] == "/api/shutdown" and status == 200 and on_shutdown:
                threading.Thread(target=on_shutdown, daemon=True).start()

        def serve_static(self) -> None:
            name = self.path.split("?", 1)[0].lstrip("/") or "index.html"
            target = (STATIC / name).resolve()
            if STATIC.resolve() not in target.parents or not target.is_file():
                target = STATIC / "index.html"
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(controller: Controller, host: str = "0.0.0.0", port: int = 8470) -> None:  # noqa: S104 - in a container
    httpd = ThreadingHTTPServer((host, port), make_handler(controller, on_shutdown=lambda: httpd.shutdown()))
    httpd.serve_forever()


def main() -> None:
    from .docker_cli import Docker
    from .release import Release

    release = Release.load(Path(os.environ.get("RELEASE_DIR", "/release")))
    controller = Controller(release, Docker(), Path(os.environ.get("STATE_DIR", "/state")),
                            self_image=os.environ.get("LAUNCHER_IMAGE", ""))
    try:
        controller.reconcile()
    except Exception:  # noqa: BLE001 - the page still opens; the next Start reconciles again
        pass
    serve(controller, port=int(os.environ.get("PORT", "8470")))


if __name__ == "__main__":
    main()
