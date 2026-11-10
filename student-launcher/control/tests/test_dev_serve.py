"""The canned /api answers dev_serve.py serves for screenshots stay the shape the real controller answers with."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dev_serve  # noqa: E402
from launcher.server import dispatch  # noqa: E402
from fake_docker import Bench  # noqa: E402

STATES = {"not-downloaded", "downloaded", "starting", "running", "stopped", "error", "unavailable"}


class Fixtures(unittest.TestCase):
    def setUp(self):
        bench = Bench()
        try:
            self.lab_keys = set(bench.controller.labs()[0])
            self.system_keys = set(bench.controller.system())
        finally:
            bench.close()

    def test_rows_match_the_controller(self):
        for name in dev_serve.scenarios():
            data = dev_serve.load(name).data
            self.assertEqual(set(data["system"]), self.system_keys, name)
            for row in data.get("labs", []):
                self.assertEqual(set(row), self.lab_keys, f"{name}: {row['id']}")
                self.assertIn(row["state"], STATES)

    def test_all_states_shows_every_state_progress_error_and_update(self):
        canned = dev_serve.load("all-states")
        self.assertEqual({row["state"] for row in canned.data["labs"]}, STATES)
        self.assertEqual(dispatch(canned, "GET", "/api/update"), (200, {"available": True}))
        first = dispatch(canned, "GET", "/api/labs/bitcoin/progress")[1]
        for _ in range(5):
            last = dispatch(canned, "GET", "/api/labs/bitcoin/progress")[1]
        self.assertEqual(first["pulled_mb"], 0)
        self.assertEqual((last["phase"], last["pulled_mb"]), ("pulling", 730))
        status, body = dispatch(canned, "POST", "/api/labs/tokens/start")
        self.assertEqual(status, 409)
        self.assertIn("memory", body["message"])
        self.assertEqual(dispatch(canned, "POST", "/api/labs/ethereum_lab/start")[0], 202)
        busy = next(row for row in canned.data["labs"] if row["action"])
        self.assertEqual(set(busy["action"]), {"id", "label", "phase", "message", "elapsed_s"})
        self.assertEqual(dispatch(canned, "POST", f"/api/labs/{busy['id']}/actions/seed")[0], 202)

    def test_docker_down(self):
        canned = dev_serve.load("docker-down")
        status, body = dispatch(canned, "GET", "/api/labs")
        self.assertEqual(status, 503)
        self.assertIn("Docker isn't running", body["message"])
        self.assertFalse(dispatch(canned, "GET", "/api/system")[1]["docker"]["running"])

    def test_docker_old_refuses_the_fabric_lab(self):
        canned = dev_serve.load("docker-old")
        status, body = dispatch(canned, "POST", "/api/labs/hlf/start")
        self.assertEqual(status, 409)
        self.assertIn("Docker Desktop 4.29 or newer", body["message"])


if __name__ == "__main__":
    unittest.main()
