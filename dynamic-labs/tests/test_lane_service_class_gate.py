"""Lane-service /claim and /resolve check the class pass (lane-service/instructor_auth.py).

The router's server-level class gate skips locations with their own auth_request,
which is how the lane resolve subrequests are wired, so the lane-service asks the
auth service itself when CLASS_GATE is on.
"""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask


ROOT = Path(__file__).resolve().parents[1]
LANE_SERVICE = ROOT / "lane-service"


class _FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class _FakeLanes:
    def list_lanes(self):
        return [{"id": "s01"}]

    def wait_until_ready(self, station, timeout_seconds=0.0):
        return True, ""

    def start_lane(self, station):
        return True, "started"


class _FakeClaims:
    def claim(self, existing_uuid=None):
        return "11111111-2222-4333-8444-555555555555", "s01", ""

    def resolve(self, uuid):
        return "s01"

    def resolve_short(self, short):
        return "s01"


def _load_lane_modules():
    for name in [m for m in sys.modules if m == "instructor_auth" or m.startswith("instructor_auth.")]:
        sys.modules.pop(name, None)
    sys.modules.pop("lab_blueprint", None)
    if str(LANE_SERVICE) in sys.path:
        sys.path.remove(str(LANE_SERVICE))
    sys.path.insert(0, str(LANE_SERVICE))
    lane_auth = importlib.import_module("instructor_auth")
    blueprint = importlib.import_module("lab_blueprint")
    return lane_auth, blueprint


class LaneServiceClassGateTests(unittest.TestCase):
    UUID = "11111111-2222-4333-8444-555555555555"

    def setUp(self) -> None:
        self._old_env = os.environ.copy()
        self._tmpdir = tempfile.TemporaryDirectory()
        self.lane_auth, blueprint = _load_lane_modules()
        self.lane_auth._class_cache.clear()
        config = SimpleNamespace(
            lab_name="demo",
            state_dir=Path(self._tmpdir.name),
            container_name_fn=lambda station: f"demo-{station}",
        )
        app = Flask(__name__)
        app.register_blueprint(blueprint.make_lab_blueprint(config, _FakeLanes(), _FakeClaims(), enable_peers=True))
        self.client = app.test_client()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)
        self._tmpdir.cleanup()

    def _verify(self, status: int):
        return patch.object(self.lane_auth.requests, "get", return_value=_FakeResponse(status))

    def test_gate_off_leaves_claim_and_resolve_alone(self) -> None:
        os.environ["CLASS_GATE"] = "off"
        with self._verify(403) as remote:
            self.assertEqual(self.client.get("/api/demo/claim").status_code, 200)
            resolve = self.client.get("/api/demo/resolve", headers={"X-Session-UUID": self.UUID})
            self.assertEqual(resolve.status_code, 200)
        remote.assert_not_called()

    def test_no_pass_sends_claim_to_the_code_page_and_refuses_resolve(self) -> None:
        os.environ["CLASS_GATE"] = "on"
        with self._verify(200) as remote:
            claim = self.client.get("/api/demo/claim")
            self.assertEqual(claim.status_code, 302)
            self.assertEqual(claim.headers["Location"], "/class/")
            self.assertNotIn("demo_session=", claim.headers.get("Set-Cookie", ""))
            resolve = self.client.get("/api/demo/resolve", headers={"X-Session-UUID": self.UUID})
            self.assertEqual(resolve.status_code, 403)
            short = self.client.get("/api/demo/resolve-short", headers={"X-Peer-Short": "11111111"})
            self.assertEqual(short.status_code, 403)
        # No cookie at all: nothing to ask the auth service about.
        remote.assert_not_called()

    def test_voided_pass_is_refused(self) -> None:
        os.environ["CLASS_GATE"] = "on"
        self.client.set_cookie("class_pass", "issued-before-the-code-changed")
        with self._verify(403):
            self.assertEqual(self.client.get("/api/demo/claim").status_code, 302)
            resolve = self.client.get("/api/demo/resolve", headers={"X-Session-UUID": self.UUID})
            self.assertEqual(resolve.status_code, 403)

    def test_valid_pass_claims_and_resolves(self) -> None:
        os.environ["CLASS_GATE"] = "on"
        self.client.set_cookie("class_pass", "good-pass")
        with self._verify(200) as remote:
            claim = self.client.get("/api/demo/claim")
            self.assertEqual(claim.status_code, 200)
            self.assertIn("demo_session=", claim.headers.get("Set-Cookie", ""))
            resolve = self.client.get("/api/demo/resolve", headers={"X-Session-UUID": self.UUID})
            self.assertEqual(resolve.status_code, 200)
            self.assertEqual(resolve.headers["X-Lane-Host"], "demo-s01")
        remote.assert_any_call(
            self.lane_auth.CLASS_VERIFY_URL,
            cookies={"class_pass": "good-pass"},
            timeout=self.lane_auth.VERIFY_TIMEOUT,
        )

    def test_instructor_cookie_passes(self) -> None:
        os.environ["CLASS_GATE"] = "on"
        self.client.set_cookie("hlf_instructor", "instructor-session")
        with self._verify(200) as remote:
            self.assertEqual(self.client.get("/api/demo/claim").status_code, 200)
        remote.assert_any_call(
            self.lane_auth.CLASS_VERIFY_URL,
            cookies={"hlf_instructor": "instructor-session"},
            timeout=self.lane_auth.VERIFY_TIMEOUT,
        )

    def test_auth_service_down_fails_closed(self) -> None:
        os.environ["CLASS_GATE"] = "on"
        self.client.set_cookie("class_pass", "good-pass")
        with patch.object(
            self.lane_auth.requests,
            "get",
            side_effect=self.lane_auth.requests.ConnectionError("down"),
        ):
            resolve = self.client.get("/api/demo/resolve", headers={"X-Session-UUID": self.UUID})
        self.assertEqual(resolve.status_code, 403)


if __name__ == "__main__":
    unittest.main()
