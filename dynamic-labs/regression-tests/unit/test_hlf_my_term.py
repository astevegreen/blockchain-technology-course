#!/usr/bin/env python3
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
HLF_WEB_SERVICE_DIR = ROOT / "hlf" / "web_service"

sys.path.insert(0, str(HLF_WEB_SERVICE_DIR))

docker_stub = types.ModuleType("docker")
docker_errors_stub = types.ModuleType("docker.errors")
docker_errors_stub.APIError = Exception
docker_errors_stub.NotFound = Exception
docker_stub.errors = docker_errors_stub
sys.modules.setdefault("docker", docker_stub)
sys.modules.setdefault("docker.errors", docker_errors_stub)

import hlf_router  # type: ignore  # noqa: E402


class _DummyLaneManager:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def start_lane(self, lane_id: str):
        self.calls.append(lane_id)
        return True, "started"


class HlfMyTermTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)
        self.app.register_blueprint(hlf_router.hlf_bp)

    def test_my_term_starts_claimed_lane(self) -> None:
        lane_manager = _DummyLaneManager()
        with patch.object(
            hlf_router,
            "get_student_context",
            return_value={"is_student": True, "student_id": "s04"},
        ), patch.object(hlf_router, "get_lane_manager", return_value=lane_manager):
            with self.app.test_client() as client:
                response = client.get("/api/hlf/my-term")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["url"], "/labs/hlf/s/s04/term/")
        self.assertEqual(payload["lane_start"], {"success": True, "message": "started"})
        self.assertEqual(lane_manager.calls, ["s04"])

    def test_my_term_requires_student_context(self) -> None:
        lane_manager = _DummyLaneManager()
        with patch.object(
            hlf_router,
            "get_student_context",
            return_value={"is_student": False, "student_id": None},
        ), patch.object(hlf_router, "get_lane_manager", return_value=lane_manager):
            with self.app.test_client() as client:
                response = client.get("/api/hlf/my-term")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(lane_manager.calls, [])


if __name__ == "__main__":
    unittest.main()
