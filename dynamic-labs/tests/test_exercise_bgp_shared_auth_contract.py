from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BGP_DIR = ROOT / "exercises" / "l03-i3-bgp-game"


def _purge_bgp_modules() -> None:
    for name in list(sys.modules):
        if name.startswith("app") or name.startswith("instructor_auth"):
            sys.modules.pop(name, None)


class BgpExerciseSharedAuthContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if importlib.util.find_spec("flask_socketio") is None:
            raise unittest.SkipTest("flask_socketio is not installed in the host test environment")
        cls._old_env = os.environ.copy()
        os.environ["FLASK_ENV"] = "development"
        os.environ["SECRET_KEY"] = "bgp-session-secret"
        os.environ["INSTRUCTOR_AUTH_MODE"] = "shared"
        os.environ["HLF_WEB_SECRET_KEY"] = "bgp-shared-cookie-secret"

        sys.path.insert(0, str(BGP_DIR))
        _purge_bgp_modules()

        bgp_module = importlib.import_module("app.app")
        game_state_module = importlib.import_module("app.state.game_state")
        from instructor_auth.auth import COOKIE_NAME, _serializer, build_payload  # noqa: E402

        cls.module = bgp_module
        cls.app = bgp_module.create_app()
        cls.socketio = bgp_module.socketio
        cls.game_state = game_state_module.game_state
        cls.cookie_name = COOKIE_NAME
        cls.serializer = _serializer
        cls.build_payload = build_payload

    @classmethod
    def tearDownClass(cls) -> None:
        if sys.path and sys.path[0] == str(BGP_DIR):
            sys.path.pop(0)
        _purge_bgp_modules()
        os.environ.clear()
        os.environ.update(cls._old_env)

    def setUp(self) -> None:
        self.game_state.queue.clear()
        self.game_state.rooms.clear()
        self.game_state.players.clear()
        self.game_state.uuid_to_sid.clear()
        self.game_state.sid_to_uuid.clear()
        self.game_state.instructor_sids.clear()
        self.game_state.next_student_number = 1
        self.game_state.next_room_number = 1

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
            socket_client.emit("join_instructor")
            received = socket_client.get_received()
            socket_client.disconnect()

        names = [event["name"] for event in received]
        self.assertIn("dashboard_state", names)


class BgpSessionSecretTests(unittest.TestCase):
    def setUp(self) -> None:
        if importlib.util.find_spec("flask_socketio") is None:
            self.skipTest("flask_socketio is not installed in the host test environment")
        self._old_env = os.environ.copy()
        self._old_path = list(sys.path)
        sys.path.insert(0, str(BGP_DIR))
        _purge_bgp_modules()

    def tearDown(self) -> None:
        sys.path[:] = self._old_path
        _purge_bgp_modules()
        os.environ.clear()
        os.environ.update(self._old_env)

    def test_create_app_refuses_to_start_without_session_secret(self) -> None:
        os.environ["FLASK_ENV"] = "development"
        bgp_module = importlib.import_module("app.app")
        with mock.patch.object(bgp_module.Config, "SECRET_KEY", None):
            with self.assertRaisesRegex(RuntimeError, "SECRET_KEY is not set"):
                bgp_module.create_app()


if __name__ == "__main__":
    unittest.main()
