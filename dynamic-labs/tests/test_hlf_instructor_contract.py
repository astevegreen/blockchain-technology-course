from __future__ import annotations

import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hlf" / "web_service"))
docker_mod = types.ModuleType("docker")
docker_errors = types.ModuleType("docker.errors")


class _DummyDockerError(Exception):
    pass


docker_errors.APIError = _DummyDockerError
docker_errors.NotFound = _DummyDockerError
docker_mod.errors = docker_errors
docker_mod.from_env = lambda: None
sys.modules.setdefault("docker", docker_mod)
sys.modules.setdefault("docker.errors", docker_errors)

for name in (
    "shared_auth",
    "instructor_routes",
    "hlf_router",
    "claim_routes",
    "shared_instructor_auth",
    "shared_instructor_auth.auth",
    "shared_instructor_auth.csrf",
):
    sys.modules.pop(name, None)

import claim_routes  # noqa: E402
import hlf_router  # noqa: E402
import instructor_routes  # noqa: E402
import progress_routes  # noqa: E402
import shared_auth  # noqa: E402
from shared_instructor_auth.auth import _serializer, build_payload  # noqa: E402
from shared_instructor_auth.csrf import mint_csrf_token  # noqa: E402


class _FakeService:
    def start_network(self):
        return True, "started"

    def get_instructor_snapshot(self, lines: int):
        return {"ok": True, "lines": lines}


class _FakeClaimManager:
    def summary(self):
        return {"claimed": 1}

    def list_claims(self):
        return [{"uuid": "11111111-1111-1111-1111-111111111111", "station": "s01"}]

    def touch(self, uuid: str):
        return uuid == "11111111-1111-1111-1111-111111111111"

    def resolve(self, uuid: str):
        if uuid == "11111111-1111-1111-1111-111111111111":
            return "s01"
        return None


def _build_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "hlf-contract-secret"
    shared_auth.init_shared_auth(app)
    app.register_blueprint(instructor_routes.instructor_assets_bp)
    app.register_blueprint(hlf_router.hlf_bp)
    app.register_blueprint(claim_routes.claim_bp)
    app.register_blueprint(progress_routes.progress_bp)
    return app


class HlfInstructorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = os.environ.copy()
        os.environ["FLASK_ENV"] = "development"
        os.environ["HLF_WEB_SECRET_KEY"] = "hlf-contract-secret"
        self.app = _build_app()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)

    def _set_instructor_cookie(self, client, *, sub: str = "alice") -> str:
        config = self.app.config["INSTRUCTOR_AUTH"]
        payload = build_payload(sub=sub)
        token = _serializer(config).dumps(payload)
        client.set_cookie("hlf_instructor", token, domain="localhost")
        return payload["jti"]

    def test_hlf_instructor_asset_redirects_to_shared_login_when_unauthenticated(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/hlf_instructor.html", headers={"Accept": "text/html"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], "/instructor/")

    def test_hlf_instructor_asset_is_served_with_valid_shared_cookie(self) -> None:
        with self.app.test_client() as client:
            self._set_instructor_cookie(client)
            resp = client.get("/hlf_instructor.html")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("Instructor", body)
        self.assertIn('href="/labs/hlf/peer/org5/"', body)

    def test_mutating_hlf_api_requires_cookie(self) -> None:
        with patch.object(hlf_router, "_service", _FakeService()):
            with self.app.test_client() as client:
                resp = client.post("/api/hlf/start")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {"success": False, "message": "unauthorized"})

    def test_mutating_hlf_api_requires_csrf_when_authenticated(self) -> None:
        with patch.object(hlf_router, "_service", _FakeService()):
            with self.app.test_client() as client:
                self._set_instructor_cookie(client)
                resp = client.post("/api/hlf/start")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json(), {"success": False, "message": "csrf token required"})

    def test_mutating_hlf_api_accepts_valid_shared_cookie_and_csrf(self) -> None:
        with patch.object(hlf_router, "_service", _FakeService()):
            with self.app.test_client() as client:
                jti = self._set_instructor_cookie(client)
                token = mint_csrf_token(self.app.config["INSTRUCTOR_AUTH"], jti)
                resp = client.post("/api/hlf/start", headers={"X-CSRFToken": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"success": True, "message": "started"})

    def test_hlf_claims_list_uses_shared_cookie_verification(self) -> None:
        with patch.object(claim_routes, "get_claim_manager", return_value=_FakeClaimManager()):
            with self.app.test_client() as client:
                self._set_instructor_cookie(client)
                resp = client.get("/api/hlf/claims")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.get_json(),
            {
                "summary": {"claimed": 1},
                "claims": [{"uuid": "11111111-1111-1111-1111-111111111111", "station": "s01"}],
            },
        )

    def test_student_session_posts_are_not_blocked_by_instructor_csrf(self) -> None:
        fake_mgr = _FakeClaimManager()
        with patch.object(claim_routes, "get_claim_manager", return_value=fake_mgr):
            with patch.object(progress_routes, "get_claim_manager", return_value=fake_mgr):
                with patch.object(progress_routes, "get_tracker") as get_tracker:
                    get_tracker.return_value.record.return_value = True
                    with self.app.test_client() as client:
                        client.set_cookie(
                            "hlf_session",
                            "11111111-1111-1111-1111-111111111111",
                            domain="localhost",
                        )
                        self._set_instructor_cookie(client)

                        heartbeat = client.post("/api/hlf/claims/heartbeat", json={})
                        progress = client.post(
                            "/api/hlf/progress/touch",
                            json={"route_id": "exercise:orientation"},
                        )

        self.assertEqual(heartbeat.status_code, 200)
        self.assertEqual(heartbeat.get_json(), {"ok": True})
        self.assertEqual(progress.status_code, 200)
        self.assertEqual(progress.get_json(), {"ok": True, "recorded": True})

    def test_active_claims_accepts_student_session_cookie_without_instructor_auth(self) -> None:
        fake_mgr = _FakeClaimManager()
        with patch.object(claim_routes, "get_claim_manager", return_value=fake_mgr):
            with self.app.test_client() as client:
                client.set_cookie(
                    "hlf_session",
                    "11111111-1111-1111-1111-111111111111",
                    domain="localhost",
                )
                resp = client.get("/api/hlf/claims/active")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.get_json(),
            {
                "ok": True,
                "claimed_stations": ["s01"],
                "claimed_msps": ["Student01MSP"],
            },
        )


if __name__ == "__main__":
    unittest.main()
