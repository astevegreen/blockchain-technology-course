"""Runs the student launcher's own tests (student-launcher/control/tests) with the tool tests, so the check and CI
run them: the control container's API against a fake Docker, the secrets coverage, and the wrappers' dry runs."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "student-launcher" / "control" / "tests"


def load_tests(loader, tests, pattern):
    for folder in (TESTS, TESTS.parent):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))
    tests.addTests(loader.discover(str(TESTS), pattern="test_*.py", top_level_dir=str(TESTS)))
    return tests


class SameRulesAsTheManifests(unittest.TestCase):
    """The control image carries no tools/, so it keeps its own copies of two manifest rules; these keep them equal."""

    def setUp(self):
        for folder in (REPO / "tools", TESTS.parent):
            if str(folder) not in sys.path:
                sys.path.insert(0, str(folder))

    def test_socket_labs_match_lab_manifest(self):
        import lab_manifest as lm
        from launcher import controller
        self.assertEqual(set(controller.DOCKER_SOCKET_LABS), set(lm.DOCKER_SOCKET_LABS))

    def test_buttons_are_paths_on_lane_service(self):
        from launcher import controller
        schema = json.loads((REPO / "dynamic-labs" / "lab.schema.json").read_text(encoding="utf-8"))
        api = schema["properties"]["local_actions"]["items"]["properties"]["api"]
        self.assertEqual(api["pattern"], "^/")
        self.assertIn("lane-service", api["description"])
        self.assertNotIn("router", api["description"])
        self.assertEqual(controller.Controller.action_url({"api": "/api/x"}),
                         "http://lane-service-lane-service-1:8090/api/x")
