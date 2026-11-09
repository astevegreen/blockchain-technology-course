"""The class gate in the instructor auth service (instructor_auth_service/class_gate.py).

Covers each path a student or instructor can take: no pass, a valid pass, a pass voided
by a code change, an instructor cookie, the portal's code change, the return-to page,
the wrong-code limit (which a forged X-Forwarded-For can't dodge) and the pass cookie's
domain for the lab subdomains.
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ClassGateServiceTests(unittest.TestCase):
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
        os.environ["CLASS_GATE"] = "on"
        os.environ["CLASS_CODE"] = "K7MP4QXR"
        os.environ["CLASS_GATE_STATE_DIR"] = str(runtime_dir / "class-gate")
        os.environ.pop("CLASS_PASS_COOKIE_DOMAIN", None)

        sys.modules.pop("instructor_auth", None)
        sys.modules.pop("instructor_auth.auth", None)

        from instructor_auth_service import class_gate, sessions
        from instructor_auth_service.app import create_app

        importlib.reload(sessions)._seen_cache.clear()
        self.class_gate = importlib.reload(class_gate)
        self.state_dir = runtime_dir / "class-gate"
        self.app = create_app()

    def tearDown(self) -> None:
        audit = logging.getLogger("instructor_audit")
        for handler in list(audit.handlers):
            audit.removeHandler(handler)
            handler.close()
        os.environ.clear()
        os.environ.update(self._old_env)
        self._tmpdir.cleanup()

    # helpers ---------------------------------------------------------------

    def _enter(self, client, code: str, ip: str = "203.0.113.10"):
        return client.post(
            "/api/class/enter",
            json={"code": code},
            environ_base={"REMOTE_ADDR": ip},
        )

    def _login_instructor(self, client) -> None:
        resp = client.post("/api/instructor/login", json={"user": "alice", "key": "correct-horse"})
        self.assertEqual(resp.status_code, 200)

    def _csrf(self, client) -> str:
        resp = client.post("/api/instructor/csrf")
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()["token"]

    # paths -----------------------------------------------------------------

    def test_no_pass_is_refused(self) -> None:
        with self.app.test_client() as client:
            self.assertEqual(client.get("/api/class/verify").status_code, 403)
            client.set_cookie("class_pass", "forged-value")
            self.assertEqual(client.get("/api/class/verify").status_code, 403)

    def test_wrong_code_gives_no_pass(self) -> None:
        with self.app.test_client() as client:
            resp = self._enter(client, "WRONGCODE")
            self.assertEqual(resp.status_code, 401)
            self.assertNotIn("class_pass=", resp.headers.get("Set-Cookie", ""))
            self.assertEqual(client.get("/api/class/verify").status_code, 403)

    def test_right_code_gives_a_pass_that_verifies(self) -> None:
        with self.app.test_client() as client:
            # Lower case and a dash are accepted: the code is read off a screen.
            resp = self._enter(client, "k7mp-4qxr")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json(), {"success": True, "redirect_to": "/"})
            cookie = resp.headers.get("Set-Cookie", "")
            self.assertIn("class_pass=", cookie)
            self.assertIn("HttpOnly", cookie)
            self.assertEqual(client.get("/api/class/verify").status_code, 200)
            self.assertTrue(client.get("/api/class/status").get_json()["has_pass"])

    def test_changing_the_code_voids_old_passes(self) -> None:
        student, instructor = self.app.test_client(), self.app.test_client()
        self.assertEqual(self._enter(student, "K7MP4QXR").status_code, 200)
        self.assertEqual(student.get("/api/class/verify").status_code, 200)

        self._login_instructor(instructor)
        token = self._csrf(instructor)
        change = instructor.post(
            "/api/instructor/class-code",
            json={"code": "NEWCODE9"},
            headers={"X-CSRFToken": token},
        )
        self.assertEqual(change.status_code, 200)
        self.assertEqual(change.get_json()["code"], "NEWCODE9")

        self.assertEqual(student.get("/api/class/verify").status_code, 403)
        self.assertEqual(self._enter(student, "K7MP4QXR").status_code, 401)
        self.assertEqual(self._enter(student, "NEWCODE9").status_code, 200)
        self.assertEqual(student.get("/api/class/verify").status_code, 200)

        # Stored where both gunicorn workers read it.
        state = json.loads((self.state_dir / "class-code.json").read_text(encoding="utf-8"))
        self.assertEqual(state["code"], "NEWCODE9")

    def test_a_redeploy_with_a_new_code_wins_over_an_older_portal_change(self) -> None:
        self.class_gate.set_code("PORTAL22")
        self.assertEqual(self.class_gate.current_code(), ("PORTAL22", "portal"))
        os.environ["CLASS_CODE"] = "ROTATED7"
        self.assertEqual(self.class_gate.current_code(), ("ROTATED7", "deploy"))

    def test_instructor_cookie_passes_the_gate(self) -> None:
        with self.app.test_client() as client:
            self._login_instructor(client)
            self.assertEqual(client.get("/api/class/verify").status_code, 200)

    def test_class_code_api_needs_an_instructor_and_a_csrf_token(self) -> None:
        with self.app.test_client() as client:
            self.assertEqual(client.get("/api/instructor/class-code").status_code, 401)
            self.assertEqual(
                client.post("/api/instructor/class-code", json={"generate": True}).status_code, 401
            )
            self._login_instructor(client)
            shown = client.get("/api/instructor/class-code").get_json()
            self.assertEqual(shown, {"code": "K7MP4QXR", "source": "deploy", "gate_on": True})
            self.assertEqual(
                client.post("/api/instructor/class-code", json={"generate": True}).status_code, 403
            )
            token = self._csrf(client)
            short = client.post(
                "/api/instructor/class-code", json={"code": "abc"}, headers={"X-CSRFToken": token}
            )
            self.assertEqual(short.status_code, 400)
            made = client.post(
                "/api/instructor/class-code", json={"generate": True}, headers={"X-CSRFToken": token}
            )
            self.assertEqual(made.status_code, 200)
            new_code = made.get_json()["code"]
            self.assertEqual(len(new_code), 8)
            self.assertNotEqual(new_code, "K7MP4QXR")
            self.assertEqual(client.get("/api/instructor/class-code").get_json()["code"], new_code)

    def test_instructor_can_enter_the_code_without_a_csrf_token(self) -> None:
        with self.app.test_client() as client:
            self._login_instructor(client)
            self.assertEqual(self._enter(client, "K7MP4QXR").status_code, 200)

    def test_return_to_brings_the_student_back(self) -> None:
        with self.app.test_client() as client:
            capture = client.get(
                "/api/class/return-to",
                headers={"X-Original-URI": "/labs/bitcoin/?day=2", "X-Original-Method": "GET"},
            )
            self.assertEqual(capture.status_code, 302)
            self.assertEqual(capture.headers["Location"], "/class/")
            self.assertIn("class_return_to=", capture.headers.get("Set-Cookie", ""))
            resp = self._enter(client, "K7MP4QXR")
            self.assertEqual(resp.get_json()["redirect_to"], "/labs/bitcoin/?day=2")

    def test_return_to_refuses_offsite_api_and_non_get_targets(self) -> None:
        gate = self.class_gate
        for target in ("https://evil.example/", "//evil.example/", "/api/bitcoin/admin", "/class/", "/\\evil"):
            with self.subTest(target=target):
                self.assertIsNone(gate.safe_return_to(target))
        self.assertIsNone(gate.safe_return_to("/labs/bitcoin/", method="POST"))
        self.assertEqual(gate.safe_return_to("/api/ethereum/claim"), "/api/ethereum/claim")

    def test_class_page_is_served(self) -> None:
        with self.app.test_client() as client:
            self.assertEqual(client.get("/class").status_code, 301)
            page = client.get("/class/")
            self.assertEqual(page.status_code, 200)
            self.assertIn("/api/class/enter", page.get_data(as_text=True))
            page.close()

    def test_wrong_codes_are_limited_per_client_and_a_forged_header_does_not_reset_it(self) -> None:
        with self.app.test_client() as client:
            for attempt in range(20):
                resp = client.post(
                    "/api/class/enter",
                    json={"code": "WRONGCODE"},
                    environ_base={"REMOTE_ADDR": "198.51.100.7"},
                    headers={"X-Forwarded-For": f"10.9.{attempt}.1, 198.51.100.7"},
                )
                self.assertEqual(resp.status_code, 401)
            blocked = client.post(
                "/api/class/enter",
                json={"code": "K7MP4QXR"},
                environ_base={"REMOTE_ADDR": "198.51.100.7"},
                headers={"X-Forwarded-For": "10.99.99.99, 198.51.100.7"},
            )
            self.assertEqual(blocked.status_code, 429)
            self.assertIn("Retry-After", blocked.headers)
            # Another client is unaffected.
            self.assertEqual(self._enter(client, "K7MP4QXR", ip="198.51.100.8").status_code, 200)

    def test_pass_cookie_domain_covers_the_lab_subdomains(self) -> None:
        domain = self.class_gate.cookie_domain
        self.assertEqual(domain("lab.example.org"), "lab.example.org")
        self.assertEqual(domain("explorer.lab.example.org"), "lab.example.org")
        self.assertEqual(domain("dex-l2.lab.example.org"), "lab.example.org")
        self.assertEqual(domain("dex.lab.example.org"), "lab.example.org")
        self.assertIsNone(domain("203.0.113.5"))
        self.assertIsNone(domain("localhost"))
        self.assertIsNone(domain("[2001:db8::1]"))
        os.environ["CLASS_PASS_COOKIE_DOMAIN"] = ".course.example.net"
        self.assertEqual(domain("lab.example.org"), "course.example.net")

    def test_pass_cookie_is_set_on_the_parent_domain(self) -> None:
        with self.app.test_client() as client:
            resp = client.post(
                "/api/class/enter",
                json={"code": "K7MP4QXR"},
                base_url="https://explorer.lab.example.org",
            )
            self.assertEqual(resp.status_code, 200)
            cookie = resp.headers.get("Set-Cookie", "")
            self.assertIn("Domain=lab.example.org", cookie)
            self.assertIn("Secure", cookie)


class LoginRateLimitClientIpTests(unittest.TestCase):
    """The instructor login limit counts the address the router saw, not a client header."""

    def test_forged_forwarded_for_does_not_reset_the_login_limit(self) -> None:
        from flask import Flask, jsonify
        from werkzeug.middleware.proxy_fix import ProxyFix

        sys.path.insert(0, str(ROOT / "shared"))
        sys.modules.pop("instructor_auth", None)
        sys.modules.pop("instructor_auth.ratelimit", None)
        from instructor_auth.ratelimit import install_login_rate_limit

        app = Flask(__name__)
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)  # type: ignore[assignment]

        @app.post("/api/instructor/login")
        def login():
            return jsonify({"success": False}), 401

        install_login_rate_limit(app, login_endpoints=["login"])
        statuses = []
        with app.test_client() as client:
            for attempt in range(6):
                # The router appends the real client address last ($proxy_add_x_forwarded_for).
                resp = client.post(
                    "/api/instructor/login",
                    headers={"X-Forwarded-For": f"10.0.0.{attempt}, 198.51.100.20"},
                )
                statuses.append(resp.status_code)
        self.assertEqual(statuses[:5], [401] * 5)
        self.assertEqual(statuses[5], 429)


if __name__ == "__main__":
    unittest.main()
