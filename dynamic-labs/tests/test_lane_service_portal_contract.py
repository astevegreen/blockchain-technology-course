from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lane-service"))
sys.modules.pop("instructor_auth", None)
sys.modules.pop("portal", None)

import instructor_auth as lane_instructor_auth  # noqa: E402
import portal  # noqa: E402


class _FakeTracker:
    def __init__(self, lab: str, sessions: int, active_10m: int, exercises_total: int) -> None:
        self._lab = lab
        self._sessions = sessions
        self._active_10m = active_10m
        self._exercises_total = exercises_total

    def rollup(self) -> dict:
        return {
            "lab": self._lab,
            "sessions": self._sessions,
            "active_10m": self._active_10m,
            "exercises_total": self._exercises_total,
        }


class LaneServicePortalContractTests(unittest.TestCase):
    def setUp(self) -> None:
        lane_instructor_auth._cache.clear()
        self.app = Flask(__name__)
        self.app.register_blueprint(portal.portal_bp)

    def test_progress_rollup_requires_instructor_cookie(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/api/portal/progress-rollup")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {"error": "unauthorized"})

    def test_progress_rollup_returns_sorted_labs_for_authenticated_instructor(self) -> None:
        trackers = {
            "zeta": _FakeTracker("zeta", 2, 1, 5),
            "alpha": _FakeTracker("alpha", 4, 2, 7),
        }
        with patch.object(portal, "all_trackers", return_value=trackers):
            with patch.object(lane_instructor_auth, "_verify_cookie", return_value=True):
                with self.app.test_client() as client:
                    client.set_cookie("hlf_instructor", "valid-cookie", domain="localhost")
                    resp = client.get("/api/portal/progress-rollup")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.get_json(),
            {
                "labs": [
                    {
                        "lab": "alpha",
                        "sessions": 4,
                        "active_10m": 2,
                        "exercises_total": 7,
                    },
                    {
                        "lab": "zeta",
                        "sessions": 2,
                        "active_10m": 1,
                        "exercises_total": 5,
                    },
                ]
            },
        )

    def test_progress_summary_page_requires_instructor_cookie(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/instructor/labs-progress")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {"error": "unauthorized"})

    def test_progress_summary_page_returns_html_for_authenticated_instructor(self) -> None:
        with patch.object(lane_instructor_auth, "_verify_cookie", return_value=True):
            with self.app.test_client() as client:
                client.set_cookie("hlf_instructor", "valid-cookie", domain="localhost")
                resp = client.get("/instructor/labs-progress")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "text/html; charset=utf-8")
        self.assertIn("Labs Progress", resp.get_data(as_text=True))

    def test_progress_summary_page_uses_hlf_instructor_console_url(self) -> None:
        with patch.object(lane_instructor_auth, "_verify_cookie", return_value=True):
            with self.app.test_client() as client:
                client.set_cookie("hlf_instructor", "valid-cookie", domain="localhost")
                resp = client.get("/instructor/labs-progress")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("function adminHref(lab)", body)
        self.assertIn('if (lab === "hlf") return "/labs/hlf/hlf_instructor.html";', body)
        self.assertIn("adminHref(l.lab)", body)
        self.assertNotIn("l.lab === 'hlf' ? 'instructor/' : 'admin'", body)


if __name__ == "__main__":
    unittest.main()
