from __future__ import annotations

import sys
import unittest
from pathlib import Path

from flask import Flask


ROOT = Path(__file__).resolve().parents[3]
LANE_SERVICE_DIR = ROOT / "lane-service"

sys.path.insert(0, str(LANE_SERVICE_DIR))

from lab_blueprint import make_lab_blueprint  # type: ignore  # noqa: E402


VALID_UUID = "11111111-1111-4111-8111-111111111111"


class _FakeConfig:
    lab_name = "consensus"
    state_dir = ROOT / ".runtime" / "test-consensus-startup-race"

    @staticmethod
    def container_name_fn(station: str) -> str:
        return f"consensus-lab-student{station[1:]}"


class _FakeClaimManager:
    def resolve(self, uuid: str):
        if uuid == VALID_UUID:
            return "s01"
        return None


class _FakeLaneManager:
    def __init__(
        self,
        *,
        ready_results: list[tuple[bool, str]] | None = None,
        start_result: tuple[bool, str] = (True, "started"),
    ) -> None:
        self.ready_results = list(ready_results or [(False, "container starting")])
        self.start_result = start_result
        self.start_calls: list[str] = []
        self.wait_calls: list[tuple[str, float]] = []

    def start_lane(self, station: str) -> tuple[bool, str]:
        self.start_calls.append(station)
        return self.start_result

    def wait_until_ready(
        self,
        station: str,
        *,
        timeout_seconds: float = 0.0,
    ) -> tuple[bool, str]:
        self.wait_calls.append((station, timeout_seconds))
        if len(self.ready_results) > 1:
            return self.ready_results.pop(0)
        return self.ready_results[0]


class ConsensusStartupRaceTests(unittest.TestCase):
    def _make_app(self, lane_manager: _FakeLaneManager) -> Flask:
        app = Flask(__name__)
        app.register_blueprint(
            make_lab_blueprint(
                _FakeConfig(),
                lane_manager,
                _FakeClaimManager(),
            )
        )
        return app

    def test_resolve_accepts_stale_cache_when_direct_state_is_running(self) -> None:
        lane_manager = _FakeLaneManager(
            ready_results=[(True, "ready")],
        )
        app = self._make_app(lane_manager)

        with app.test_client() as client:
            response = client.get(
                "/api/consensus/resolve",
                headers={"X-Session-UUID": VALID_UUID},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Lane-Host"), "consensus-lab-student01")
        self.assertEqual(lane_manager.start_calls, [])

    def test_resolve_waits_for_busy_lane_start_before_returning_success(self) -> None:
        lane_manager = _FakeLaneManager(
            ready_results=[(False, "container starting"), (True, "ready")],
            start_result=(False, "lane s01 is busy"),
        )
        app = self._make_app(lane_manager)

        with app.test_client() as client:
            response = client.get(
                "/api/consensus/resolve",
                headers={"X-Session-UUID": VALID_UUID},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Lane-Host"), "consensus-lab-student01")
        self.assertEqual(lane_manager.start_calls, ["s01"])
        self.assertEqual(len(lane_manager.wait_calls), 2)

    def test_wrapper_page_stays_in_startup_until_lane_is_ready(self) -> None:
        lane_manager = _FakeLaneManager(
            ready_results=[(False, "container starting"), (False, "status=created")],
            start_result=(False, "lane s01 is busy"),
        )
        app = self._make_app(lane_manager)

        with app.test_client() as client:
            response = client.get(f"/labs/consensus/c/{VALID_UUID}/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_data(as_text=True), "container starting")


if __name__ == "__main__":
    unittest.main()
