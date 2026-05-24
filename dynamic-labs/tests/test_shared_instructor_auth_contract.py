from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
