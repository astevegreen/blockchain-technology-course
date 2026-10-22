from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

from flask import Flask, jsonify


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))

from instructor_auth import (  # noqa: E402
    AuthConfig,
    AuthMode,
    build_payload,
    csrf_blueprint,
    install_csrf_protection,
    install_sliding_reissue,
    require_instructor,
)
from instructor_auth.auth import COOKIE_NAME, _serializer  # noqa: E402


def _make_cookie(config: AuthConfig, *, sub: str = "instructor") -> str:
    return _serializer(config).dumps(build_payload(sub=sub))


def _build_app() -> tuple[Flask, AuthConfig]:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-app-secret"
    config = AuthConfig(
        mode=AuthMode.SHARED,
        secret="shared-contract-secret",
    )
    app.config["INSTRUCTOR_AUTH"] = config
    app.register_blueprint(csrf_blueprint(config))
    install_sliding_reissue(app)
    install_csrf_protection(app, config)

    @app.get("/protected")
    @require_instructor(config)
    def protected():
        from flask import g

        return jsonify({"ok": True, "sub": g.instructor.sub})

    @app.post("/mutate")
    @require_instructor(config)
    def mutate():
        return jsonify({"ok": True})

    return app, config


class SharedInstructorAuthContractTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["FLASK_ENV"] = "development"
        self.app, self.config = _build_app()

    def test_protected_get_redirects_to_shared_login_when_unauthenticated(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/protected")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], "/instructor/")

    def test_protected_get_succeeds_with_valid_shared_cookie(self) -> None:
        with self.app.test_client() as client:
            client.set_cookie(COOKIE_NAME, _make_cookie(self.config, sub="alice"), domain="localhost")
            resp = client.get("/protected")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"ok": True, "sub": "alice"})

    def test_csrf_mint_requires_valid_cookie(self) -> None:
        with self.app.test_client() as client:
            resp = client.post("/api/instructor/csrf")
        self.assertEqual(resp.status_code, 401)

    def test_mutating_route_rejects_missing_csrf_even_when_cookie_is_valid(self) -> None:
        with self.app.test_client() as client:
            client.set_cookie(COOKIE_NAME, _make_cookie(self.config), domain="localhost")
            resp = client.post("/mutate")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()["message"], "csrf token required")

    def test_mutating_route_accepts_valid_csrf(self) -> None:
        with self.app.test_client() as client:
            client.set_cookie(COOKIE_NAME, _make_cookie(self.config), domain="localhost")
            mint = client.post("/api/instructor/csrf")
            self.assertEqual(mint.status_code, 200)
            token = mint.get_json()["token"]
            resp = client.post("/mutate", headers={"X-CSRFToken": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"ok": True})


class DevFallbackIsOptInTests(unittest.TestCase):
    """The public dev fallbacks apply only when FLASK_ENV is explicitly a dev value."""

    def _env(self, **overrides: str):
        keys = (
            "FLASK_ENV",
            "INSTRUCTOR_AUTH_MODE",
            "INSTRUCTOR_AUTH_SECRET",
            "INSTRUCTOR_PASSWORD",
            "INSTRUCTOR_AUTH_COOKIE_SECRET",
            "HLF_INSTRUCTOR_COOKIE_SECRET",
            "HLF_WEB_SECRET_KEY",
        )
        env = {k: v for k, v in os.environ.items() if k not in keys}
        env.update(overrides)
        return mock.patch.dict(os.environ, env, clear=True)

    def test_unset_flask_env_refuses_shared_mode_without_a_secret(self) -> None:
        with self._env():
            with self.assertRaisesRegex(RuntimeError, "shared requires"):
                AuthConfig.from_env()

    def test_unset_flask_env_refuses_standalone_mode_without_secret_and_password(self) -> None:
        with self._env(INSTRUCTOR_AUTH_MODE="standalone"):
            with self.assertRaisesRegex(RuntimeError, "INSTRUCTOR_AUTH_SECRET"):
                AuthConfig.from_env()
        with self._env(INSTRUCTOR_AUTH_MODE="standalone", INSTRUCTOR_AUTH_SECRET="s"):
            with self.assertRaisesRegex(RuntimeError, "INSTRUCTOR_PASSWORD"):
                AuthConfig.from_env()

    def test_unset_flask_env_refuses_disabled_mode(self) -> None:
        with self._env(INSTRUCTOR_AUTH_MODE="disabled"):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                AuthConfig.from_env()

    def test_explicit_development_still_uses_the_dev_fallback(self) -> None:
        with self._env(FLASK_ENV="development"):
            self.assertEqual(AuthConfig.from_env().mode, AuthMode.SHARED)

    def test_every_copy_of_the_auth_module_matches_the_shared_one(self) -> None:
        shared = (ROOT / "shared" / "instructor_auth" / "auth.py").read_bytes()
        for rel in (
            "hlf/shared_instructor_auth/auth.py",
            "quiz-engine-v2/instructor_auth/auth.py",
            "exercises/l03-i3-trust-game/instructor_auth/auth.py",
        ):
            with self.subTest(copy=rel):
                self.assertEqual((ROOT / rel).read_bytes(), shared)


if __name__ == "__main__":
    unittest.main()
