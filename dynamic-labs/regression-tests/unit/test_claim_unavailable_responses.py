#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
LANE_SERVICE_DIR = ROOT / "lane-service"
HLF_WEB_SERVICE_DIR = ROOT / "hlf" / "web_service"

sys.path.insert(0, str(LANE_SERVICE_DIR))
sys.path.insert(0, str(HLF_WEB_SERVICE_DIR))

from lab_blueprint import make_lab_blueprint  # type: ignore  # noqa: E402
import claim_routes  # type: ignore  # noqa: E402


class _DummyClaimManager:
    def claim(self, existing_uuid=None):
        return None, None, "no free stations"

    def summary(self):
        return {
            "total_stations": 3,
            "claimed": 3,
            "free": 0,
            "paused": False,
            "policy": "sticky",
            "pool_size": 1,
            "pool_hot_free": 0,
            "idle_timeout_seconds": 1200,
        }


class _DummyConfig:
    lab_name = "consensus"
    state_dir = ROOT / ".runtime" / "test-claim-responses"


class ClaimUnavailableResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.claim_manager = _DummyClaimManager()

    def test_lane_service_claim_json_response_is_clear(self) -> None:
        app = Flask(__name__)
        app.register_blueprint(
            make_lab_blueprint(
                _DummyConfig(),
                object(),
                self.claim_manager,
            )
        )
        with app.test_client() as client:
            response = client.get("/api/consensus/claim", headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 503)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "no_available_workstations")
        self.assertIn("No available workstations", payload["message"])
        self.assertEqual(payload["summary"]["free"], 0)

    def test_lane_service_claim_html_response_is_clear(self) -> None:
        app = Flask(__name__)
        app.register_blueprint(
            make_lab_blueprint(
                _DummyConfig(),
                object(),
                self.claim_manager,
            )
        )
        with app.test_client() as client:
            response = client.get("/api/consensus/claim", headers={"Accept": "text/html"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("text/html", response.headers.get("Content-Type", ""))
        self.assertIn(b"No available workstations", response.data)
        self.assertIn(b"Claimed: 3 / 3 workstations", response.data)

    def test_hlf_claim_json_response_is_clear(self) -> None:
        app = Flask(__name__)
        app.register_blueprint(claim_routes.claim_bp)
        with patch.object(claim_routes, "get_claim_manager", return_value=self.claim_manager):
            with app.test_client() as client:
                response = client.get("/api/hlf/claim", headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 503)
        payload = response.get_json()
        self.assertEqual(payload["reason"], "no_available_workstations")
        self.assertIn("No available workstations", payload["message"])
        self.assertEqual(payload["summary"]["free"], 0)

    def test_hlf_claim_html_response_is_clear(self) -> None:
        app = Flask(__name__)
        app.register_blueprint(claim_routes.claim_bp)
        with patch.object(claim_routes, "get_claim_manager", return_value=self.claim_manager):
            with app.test_client() as client:
                response = client.get("/api/hlf/claim", headers={"Accept": "text/html"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("text/html", response.headers.get("Content-Type", ""))
        self.assertIn(b"No available workstations", response.data)
        self.assertIn(b"Claimed: 3 / 3 workstations", response.data)


if __name__ == "__main__":
    unittest.main()
