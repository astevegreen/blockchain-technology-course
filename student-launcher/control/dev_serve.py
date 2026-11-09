"""Serve the real control page against canned /api answers, for screenshots and page work without Docker.

    python student-launcher/control/dev_serve.py [--scenario all-states|docker-down] [--port 8470]

Then open http://127.0.0.1:8470/. The answers come from tests/fixtures/api/<scenario>.json; buttons answer but
change nothing, so every screenshot shows the same page.
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from launcher.controller import Refused  # noqa: E402
from launcher.server import make_handler  # noqa: E402

FIXTURES = HERE / "tests" / "fixtures" / "api"


class CannedController:
    """Answers what server.dispatch asks a Controller, from one fixture file."""

    def __init__(self, data: dict):
        self.data = data
        self.release = SimpleNamespace(version=data["health"]["version"])
        self.polls: dict[str, int] = {}

    def answer(self, key: str, default):
        canned = self.data.get("responses", {}).get(key)
        if not canned:
            return default
        if canned["status"] >= 400:
            raise Refused(canned["status"], canned["body"]["message"])
        return canned["body"]

    def labs(self):
        return self.answer("GET labs", None) or self.data.get("labs", [])

    def system(self):
        return self.answer("GET system", self.data["system"])

    def update(self):
        return self.answer("GET update", self.data["update"])

    def progress(self, lab_id):
        frames = self.data.get("progress", {}).get(lab_id)
        if not frames:
            raise Refused(404, "This lab hasn't been started.")
        n = self.polls[lab_id] = self.polls.get(lab_id, -1) + 1
        return frames[min(n, len(frames) - 1)]  # holds on the last frame, so the bar stays on screen

    def start(self, lab_id):
        return self.answer(f"POST labs/{lab_id}/start", {"ok": True})

    def stop(self, lab_id):
        return self.answer(f"POST labs/{lab_id}/stop", {"ok": True})

    def reset(self, lab_id):
        return self.answer(f"POST labs/{lab_id}/reset", {"ok": True})

    def action(self, lab_id, action_id):
        return self.answer(f"POST labs/{lab_id}/actions/{action_id}", {"ok": True})

    def shutdown(self):
        return {"ok": True}


def scenarios() -> list[str]:
    return sorted(p.stem for p in FIXTURES.glob("*.json"))


def load(scenario: str) -> CannedController:
    return CannedController(json.loads((FIXTURES / f"{scenario}.json").read_text(encoding="utf-8")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", default="all-states", choices=scenarios())
    parser.add_argument("--port", type=int, default=8470)
    args = parser.parse_args()
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(load(args.scenario)))
    print(f"Control page ({args.scenario}): http://127.0.0.1:{args.port}/  (Ctrl+C stops it)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
