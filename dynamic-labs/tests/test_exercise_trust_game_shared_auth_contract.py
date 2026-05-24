from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRUST_GAME_DIR = ROOT / "exercises" / "l03-i3-trust-game"


def _purge_trust_game_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name == "word_bank" or name.startswith("instructor_auth"):
            sys.modules.pop(name, None)


class TrustGameSharedAuthContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if importlib.util.find_spec("flask_socketio") is None:
            raise unittest.SkipTest("flask_socketio is not installed in the host test environment")
        cls._old_env = os.environ.copy()
        os.environ["FLASK_ENV"] = "development"
        os.environ["SECRET_KEY"] = "trust-session-secret"
        os.environ["INSTRUCTOR_AUTH_MODE"] = "shared"
        os.environ["HLF_WEB_SECRET_KEY"] = "trust-shared-cookie-secret"

        sys.path.insert(0, str(TRUST_GAME_DIR))
        _purge_trust_game_modules()

        import app as trust_module  # noqa: E402
        from instructor_auth.auth import COOKIE_NAME, _serializer, build_payload  # noqa: E402

        cls.module = trust_module
        cls.app = trust_module.app
        cls.socketio = trust_module.socketio
        cls.cookie_name = COOKIE_NAME
        cls.serializer = _serializer
        cls.build_payload = build_payload

    @classmethod
    def tearDownClass(cls) -> None:
        if sys.path and sys.path[0] == str(TRUST_GAME_DIR):
            sys.path.pop(0)
        _purge_trust_game_modules()
        os.environ.clear()
        os.environ.update(cls._old_env)

    def _set_instructor_cookie(self, client, *, sub: str = "alice") -> None:
        config = self.app.config["INSTRUCTOR_AUTH"]
        token = type(self).serializer(config).dumps(type(self).build_payload(sub=sub))
        client.set_cookie(self.cookie_name, token, domain="localhost")

    def test_instructor_page_redirects_when_unauthenticated(self) -> None:
        with self.app.test_client() as client:
            resp = client.get("/instructor")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], "/instructor/")

    def test_authenticated_instructor_page_sets_socket_session(self) -> None:
        with self.app.test_client() as client:
            self._set_instructor_cookie(client)
            resp = client.get("/instructor")
            with client.session_transaction() as session:
                is_instructor = session.get("is_instructor")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(is_instructor)

    def test_socketio_instructor_join_uses_authenticated_flask_session(self) -> None:
        with self.app.test_client() as client:
            self._set_instructor_cookie(client)
            page = client.get("/instructor")
            self.assertEqual(page.status_code, 200)

            socket_client = self.socketio.test_client(self.app, flask_test_client=client)
            self.assertTrue(socket_client.is_connected())
            socket_client.emit("instructor_join")
            received = socket_client.get_received()
            socket_client.disconnect()

        names = [event["name"] for event in received]
        self.assertIn("instructor_update", names)


if __name__ == "__main__":
    unittest.main()
