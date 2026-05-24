from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUIZ_ENGINE_DIR = ROOT / "quiz-engine-v2"


def _purge_quiz_engine_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app.") or name.startswith("instructor_auth"):
            sys.modules.pop(name, None)


class QuizEngineV2SharedAuthContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._old_env = os.environ.copy()
        cls._tmpdir = tempfile.TemporaryDirectory()
        os.environ["FLASK_ENV"] = "development"
        os.environ["QUIZ_ENGINE_DB_PATH"] = str(Path(cls._tmpdir.name) / "quiz.db")
        os.environ["QUIZ_ENGINE_SECRET_KEY"] = "quiz-session-secret"
        os.environ["QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE"] = "shared"
        os.environ["INSTRUCTOR_AUTH_MODE"] = "shared"
        os.environ["HLF_WEB_SECRET_KEY"] = "quiz-shared-cookie-secret"

        sys.path.insert(0, str(QUIZ_ENGINE_DIR))
        _purge_quiz_engine_modules()

        from app import create_app  # noqa: E402
        from app.db import init_db  # noqa: E402
        from instructor_auth.auth import COOKIE_NAME, _serializer, build_payload  # noqa: E402

        cls.app = create_app()
        with cls.app.app_context():
            init_db()
        cls.cookie_name = COOKIE_NAME
        cls.serializer = _serializer
        cls.build_payload = build_payload

    @classmethod
    def tearDownClass(cls) -> None:
        if sys.path and sys.path[0] == str(QUIZ_ENGINE_DIR):
            sys.path.pop(0)
        _purge_quiz_engine_modules()
        cls._tmpdir.cleanup()
        os.environ.clear()
        os.environ.update(cls._old_env)

    def _set_instructor_cookie(self, client, *, sub: str = "alice") -> None:
        config = self.app.config["INSTRUCTOR_AUTH"]
        token = type(self).serializer(config).dumps(type(self).build_payload(sub=sub))
        client.set_cookie(self.cookie_name, token, domain="localhost")

    def test_instructor_paths_redirect_to_shared_login_when_unauthenticated(self) -> None:
        with self.app.test_client() as client:
            dashboard = client.get("/instructor")
            context = client.get(
                "/instructor/dev/context",
                headers={"Accept": "application/json"},
            )
        self.assertEqual(dashboard.status_code, 302)
        self.assertEqual(dashboard.headers["Location"], "/instructor/")
        self.assertEqual(context.status_code, 401)
        self.assertEqual(context.get_json(), {"error": "instructor_auth_required"})

    def test_student_home_remains_public(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/student/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Quiz Engine", resp.get_data(as_text=True))
        self.assertIn("Get identifier", resp.get_data(as_text=True))

    def test_csrf_mint_requires_shared_cookie(self) -> None:
        with self.app.test_client() as client:
            resp = client.post("/api/instructor/csrf")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {"success": False, "message": "unauthorized"})

    def test_authenticated_shared_cookie_unlocks_instructor_and_csrf(self) -> None:
        with self.app.test_client() as client:
            self._set_instructor_cookie(client)

            csrf = client.post("/api/instructor/csrf")
            dashboard = client.get("/instructor")
            context = client.get("/instructor/dev/context")

        self.assertEqual(csrf.status_code, 200)
        self.assertIn("token", csrf.get_json())
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("Instructor Dashboard", dashboard.get_data(as_text=True))
        self.assertEqual(context.status_code, 200)
        self.assertEqual(
            context.get_json(),
            {"instructor": {"auth_mode": "shared", "subject": "alice"}},
        )

    def test_shared_cookie_form_mutations_require_csrf(self) -> None:
        with self.app.test_client() as client:
            self._set_instructor_cookie(client)
            missing = client.post(
                "/instructor/registration",
                data={"registration_mode": "open", "open_registration_cap": "40"},
            )
            token = client.post("/api/instructor/csrf").get_json()["token"]
            accepted = client.post(
                "/instructor/registration",
                data={"registration_mode": "open", "open_registration_cap": "40"},
                headers={"X-CSRFToken": token},
                follow_redirects=False,
            )

        self.assertEqual(missing.status_code, 403)
        self.assertEqual(accepted.status_code, 302)


if __name__ == "__main__":
    unittest.main()
