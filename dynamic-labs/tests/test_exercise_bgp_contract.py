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
        if name.startswith("app"):
            sys.modules.pop(name, None)


class BgpStudentOnlyContractTests(unittest.TestCase):
    """Since the June 2026 pilot the BGP game has no instructor dashboard and no instructor auth."""

    @classmethod
    def setUpClass(cls) -> None:
        if importlib.util.find_spec("flask_socketio") is None:
            raise unittest.SkipTest("flask_socketio is not installed in the host test environment")
        cls._old_env = os.environ.copy()
        cls._old_path = list(sys.path)
        os.environ["FLASK_ENV"] = "development"
        os.environ["SECRET_KEY"] = "bgp-session-secret"
        sys.path.insert(0, str(BGP_DIR))
        _purge_bgp_modules()
        bgp_module = importlib.import_module("app.app")
        cls.app = bgp_module.create_app()
        cls.socketio = bgp_module.socketio

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path[:] = cls._old_path
        _purge_bgp_modules()
        os.environ.clear()
        os.environ.update(cls._old_env)

    def test_serves_only_the_student_page_health_and_static_files(self) -> None:
        routes = {rule.rule for rule in self.app.url_map.iter_rules()}
        self.assertEqual(routes, {"/", "/healthz", "/static/<path:filename>"})
        with self.app.test_client() as client:
            self.assertEqual(client.get("/instructor").status_code, 404)

    def test_a_student_socket_registers_into_the_lobby(self) -> None:
        socket_client = self.socketio.test_client(self.app)
        self.assertTrue(socket_client.is_connected())
        socket_client.emit("register", {"uuid": "contract-student"})
        received = socket_client.get_received()
        socket_client.disconnect()
        restore = [event for event in received if event["name"] == "restore_state"]
        self.assertEqual(len(restore), 1)
        self.assertEqual(restore[0]["args"][0]["view"], "lobby")


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
