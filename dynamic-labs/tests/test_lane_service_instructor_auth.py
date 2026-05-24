from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lane-service"))
sys.modules.pop("instructor_auth", None)

import instructor_auth as lane_instructor_auth  # noqa: E402


class _FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class LaneServiceInstructorAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        lane_instructor_auth._cache.clear()
        self.app = Flask(__name__)

    def test_default_verify_url_points_to_central_auth_service(self) -> None:
        self.assertEqual(
            lane_instructor_auth.VERIFY_URL,
            "http://instructor-auth-service:8080/api/instructor/verify",
        )

    def test_verify_cookie_calls_remote_verify_endpoint(self) -> None:
        with patch.object(
            lane_instructor_auth.requests,
            "get",
            return_value=_FakeResponse(200),
        ) as mock_get:
            ok = lane_instructor_auth._verify_cookie("cookie-123")

        self.assertTrue(ok)
        mock_get.assert_called_once_with(
            lane_instructor_auth.VERIFY_URL,
            cookies={"hlf_instructor": "cookie-123"},
            timeout=lane_instructor_auth.VERIFY_TIMEOUT,
        )

    def test_verify_cookie_uses_cache_for_repeat_lookups(self) -> None:
        with patch.object(
            lane_instructor_auth.requests,
            "get",
            return_value=_FakeResponse(200),
        ) as mock_get:
            self.assertTrue(lane_instructor_auth._verify_cookie("cookie-abc"))
            self.assertTrue(lane_instructor_auth._verify_cookie("cookie-abc"))

        mock_get.assert_called_once()

    def test_require_instructor_rejects_missing_cookie(self) -> None:
        @lane_instructor_auth.require_instructor
        def protected():
            return {"ok": True}

        with self.app.test_request_context("/protected"):
            resp, status = protected()

        self.assertEqual(status, 401)
        self.assertEqual(resp.get_json(), {"error": "unauthorized"})

    def test_require_instructor_accepts_valid_cookie(self) -> None:
        @lane_instructor_auth.require_instructor
        def protected():
            return {"ok": True}, 200

        with patch.object(lane_instructor_auth, "_verify_cookie", return_value=True):
            with self.app.test_request_context(
                "/protected",
                headers={"Cookie": "hlf_instructor=valid-cookie"},
            ):
                resp, status = protected()

        self.assertEqual(status, 200)
        self.assertEqual(resp, {"ok": True})


if __name__ == "__main__":
    unittest.main()
