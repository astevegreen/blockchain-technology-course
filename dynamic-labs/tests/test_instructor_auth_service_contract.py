from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import importlib
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstructorAuthServiceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = os.environ.copy()
        self._tmpdir = tempfile.TemporaryDirectory()
        runtime_dir = Path(self._tmpdir.name)

        os.environ["FLASK_ENV"] = "development"
        os.environ["SECRET_KEY"] = "service-session-secret"
        os.environ["HLF_WEB_SECRET_KEY"] = "service-cookie-secret"
        os.environ["HLF_INSTRUCTOR_USER"] = "alice"
        os.environ["HLF_INSTRUCTOR_KEY"] = "correct-horse"
        os.environ["INSTRUCTOR_AUTH_SESSION_DIR"] = str(runtime_dir / "sessions")
        os.environ["INSTRUCTOR_AUDIT_LOG_PATH"] = str(runtime_dir / "audit.log")

        sys.modules.pop("instructor_auth", None)
        sys.modules.pop("instructor_auth.auth", None)

        from instructor_auth_service import sessions
        from instructor_auth_service.app import create_app

        self.sessions = importlib.reload(sessions)
        self.sessions._seen_cache.clear()
        self.active_path = self.sessions._ACTIVE
        self.app = create_app()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)
        self._tmpdir.cleanup()

    def test_instructor_root_redirects_to_trailing_slash(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/instructor")
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.headers["Location"], "/instructor/")

    def test_sessions_page_redirects_when_unauthenticated(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/instructor/sessions")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], "/instructor/")

    def test_instructor_portal_links_to_ethereum_trainer_query_mode(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/instructor/")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('/labs/ethereum_lab/?mode=instructor', body)

    def test_instructor_live_progress_uses_hlf_instructor_console_url(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/instructor/")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("function adminHref(lab)", body)
        self.assertIn("if (lab === 'hlf') return '/labs/hlf/hlf_instructor.html';", body)
        self.assertIn("adminHref(l.lab)", body)
        self.assertNotIn('href="/labs/\' + l.lab + \'/admin"', body)

    def test_login_verify_whoami_and_logout_contract(self) -> None:
        with self.app.test_client() as client:
            login = client.post(
                "/api/instructor/login",
                json={"user": "alice", "key": "correct-horse"},
            )
            self.assertEqual(login.status_code, 200)
            self.assertEqual(login.get_json(), {"success": True})
            self.assertIn("hlf_instructor=", login.headers.get("Set-Cookie", ""))

            verify = client.get("/api/instructor/verify")
            self.assertEqual(verify.status_code, 200)

            whoami = client.get("/api/instructor/whoami")
            self.assertEqual(
                whoami.get_json(),
                {
                    "authenticated": True,
                    "auth_bypassed": False,
                    "auth_enabled": True,
                    "sub": "alice",
                    "using_default_credentials": False,
                },
            )

            sessions = client.get("/api/instructor/sessions")
            self.assertEqual(sessions.status_code, 200)
            self.assertEqual(len(sessions.get_json()["sessions"]), 1)

            logout = client.post("/api/instructor/logout")
            self.assertEqual(logout.status_code, 200)
            self.assertEqual(logout.get_json(), {"success": True})

            verify_after = client.get("/api/instructor/verify")
            self.assertEqual(verify_after.status_code, 401)

    def test_return_to_cookie_redirects_after_successful_login(self) -> None:
        with self.app.test_client() as client:
            capture = client.get(
                "/api/instructor/return-to",
                headers={
                    "X-Original-URI": "/quiz/instructor/templates?tag=consensus",
                    "X-Original-Method": "GET",
                },
            )
            self.assertEqual(capture.status_code, 302)
            self.assertEqual(capture.headers["Location"], "/instructor/")
            self.assertIn("hlf_instructor_return_to=", capture.headers.get("Set-Cookie", ""))
            self.assertIn("HttpOnly", capture.headers.get("Set-Cookie", ""))

            login = client.post(
                "/api/instructor/login",
                json={"user": "alice", "key": "correct-horse"},
            )
            self.assertEqual(login.status_code, 200)
            self.assertEqual(
                login.get_json(),
                {
                    "success": True,
                    "redirect_to": "/quiz/instructor/templates?tag=consensus",
                },
            )
            self.assertTrue(
                any(
                    "hlf_instructor_return_to=;" in header
                    for header in login.headers.getlist("Set-Cookie")
                )
            )

    def test_return_to_cookie_rejects_external_api_and_non_get_targets(self) -> None:
        unsafe_targets = [
            "https://evil.example/quiz/instructor",
            "//evil.example/quiz/instructor",
            "/api/instructor/whoami",
            "/api/bitcoin/admin",
            "/instructor/",
        ]
        for index, target in enumerate(unsafe_targets, start=1):
            with self.subTest(target=target):
                with self.app.test_client() as client:
                    capture = client.get(
                        "/api/instructor/return-to",
                        headers={
                            "X-Original-URI": target,
                            "X-Original-Method": "GET",
                        },
                    )
                    self.assertEqual(capture.status_code, 302)

                    login = client.post(
                        "/api/instructor/login",
                        json={"user": "alice", "key": "correct-horse"},
                        headers={"X-Forwarded-For": f"192.0.2.{index}"},
                    )
                    self.assertEqual(login.status_code, 200)
                    self.assertEqual(login.get_json(), {"success": True})

        with self.app.test_client() as client:
            capture = client.get(
                "/api/instructor/return-to",
                headers={
                    "X-Original-URI": "/quiz/instructor/templates",
                    "X-Original-Method": "POST",
                },
            )
            self.assertEqual(capture.status_code, 302)
            login = client.post(
                "/api/instructor/login",
                json={"user": "alice", "key": "correct-horse"},
                headers={"X-Forwarded-For": "192.0.2.250"},
            )
            self.assertEqual(login.get_json(), {"success": True})

    def test_invalid_credentials_are_rejected(self) -> None:
        with self.app.test_client() as client:
            resp = client.post("/api/instructor/login", json={"user": "alice", "key": "wrong"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {"success": False, "message": "invalid credentials"})

    def test_csrf_and_revoke_flow(self) -> None:
        with self.app.test_client() as client:
            unauthenticated = client.post("/api/instructor/csrf")
            self.assertEqual(unauthenticated.status_code, 401)
            self.assertEqual(unauthenticated.get_json(), {"success": False, "message": "unauthorized"})

            login = client.post(
                "/api/instructor/login",
                json={"user": "alice", "key": "correct-horse"},
            )
            self.assertEqual(login.status_code, 200)

            missing_csrf = client.post(
                "/api/instructor/sessions/revoke",
                json={"jti": "target-session"},
            )
            self.assertEqual(missing_csrf.status_code, 403)
            self.assertEqual(
                missing_csrf.get_json(),
                {"success": False, "message": "csrf token required"},
            )

            mint = client.post("/api/instructor/csrf")
            self.assertEqual(mint.status_code, 200)
            token = mint.get_json()["token"]

            revoke = client.post(
                "/api/instructor/sessions/revoke",
                json={"jti": "target-session"},
                headers={"X-CSRFToken": token},
            )
            self.assertEqual(revoke.status_code, 200)
            self.assertEqual(revoke.get_json(), {"success": True})

    def test_verify_throttles_session_last_seen_writes(self) -> None:
        with self.app.test_client() as client:
            login = client.post(
                "/api/instructor/login",
                json={"user": "alice", "key": "correct-horse"},
            )
            self.assertEqual(login.status_code, 200)

            initial = json.loads(self.active_path.read_text(encoding="utf-8"))
            self.assertEqual(len(initial), 1)
            jti, entry = next(iter(initial.items()))
            issued_last_seen = int(entry["last_seen"])

            with mock.patch.object(self.sessions.time, "time", return_value=issued_last_seen + 5):
                verify = client.get("/api/instructor/verify")
            self.assertEqual(verify.status_code, 200)
            unchanged = json.loads(self.active_path.read_text(encoding="utf-8"))
            self.assertEqual(int(unchanged[jti]["last_seen"]), issued_last_seen)

            with mock.patch.object(self.sessions.time, "time", return_value=issued_last_seen + 35):
                verify = client.get("/api/instructor/verify")
            self.assertEqual(verify.status_code, 200)
            updated = json.loads(self.active_path.read_text(encoding="utf-8"))
            self.assertEqual(int(updated[jti]["last_seen"]), issued_last_seen + 35)


if __name__ == "__main__":
    unittest.main()
