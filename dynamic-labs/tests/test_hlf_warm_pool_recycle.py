from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hlf" / "web_service"))
sys.modules.pop("claims", None)

import claims  # noqa: E402


class _FakeLaneManager:
    def __init__(self, statuses):
        self.statuses = dict(statuses)
        self.reset_calls = []
        self.start_calls = []

    def list_lanes(self):
        return [
            {"id": lane_id, "status": status}
            for lane_id, status in sorted(self.statuses.items())
        ]

    def get_failed_lanes(self):
        return set()

    def reset_lane(self, lane_id):
        self.reset_calls.append(lane_id)
        self.statuses[lane_id] = "stopped"
        return True, "reset"

    def start_lane(self, lane_id):
        self.start_calls.append(lane_id)
        self.statuses[lane_id] = "running"
        return True, "started"


class HlfWarmPoolRecycleTests(unittest.TestCase):
    def _manager(self, fake_lanes):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        runtime = Path(tmp.name)
        lane_ids = lambda: ["s01", "s02", "s03", "s04", "s05"]
        patches = [
            patch.object(claims, "CLAIMS_DIR", runtime / "claims"),
            patch.object(claims, "SETTINGS_PATH", runtime / "claim-settings.json"),
            patch.object(claims, "lane_ids", lane_ids),
            patch.object(claims, "get_lane_manager", return_value=fake_lanes),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return claims.ClaimManager()

    def test_reset_unclaimed_hot_spares_excludes_claimed_lanes_and_refills(self):
        fake_lanes = _FakeLaneManager({
            "s01": "running",
            "s02": "running",
            "s03": "error",
            "s04": "stopped",
            "s05": "stopped",
        })
        mgr = self._manager(fake_lanes)
        mgr._pool_size = 2
        mgr._claims["11111111-1111-1111-1111-111111111111"] = {
            "station": "s01",
            "claimed_at": 1.0,
            "last_active": 1.0,
        }
        mgr._by_station["s01"] = "11111111-1111-1111-1111-111111111111"

        result = mgr.reset_unclaimed_hot_spares(
            reason="test",
            refill=True,
            force_runtime_ready=True,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(fake_lanes.reset_calls, ["s02", "s03"])
        self.assertEqual(fake_lanes.start_calls, ["s02", "s03"])
        self.assertEqual(fake_lanes.statuses["s01"], "running")

    def test_start_claimed_lanes_starts_only_the_claimed_stations(self):
        # Network startup leaves every student peer stopped; a station claimed while it ran needs its peer started.
        fake_lanes = _FakeLaneManager({
            "s01": "error",
            "s02": "stopped",
            "s03": "stopped",
            "s04": "running",
            "s05": "stopped",
        })
        mgr = self._manager(fake_lanes)
        for uuid, station in (
            ("11111111-1111-1111-1111-111111111111", "s01"),
            ("22222222-2222-2222-2222-222222222222", "s04"),
        ):
            mgr._claims[uuid] = {"station": station, "claimed_at": 1.0, "last_active": 1.0}
            mgr._by_station[station] = uuid

        results = mgr.start_claimed_lanes()

        self.assertEqual(fake_lanes.start_calls, ["s01", "s04"])
        self.assertEqual([r["lane"] for r in results], ["s01", "s04"])
        self.assertTrue(all(r["success"] for r in results))
        self.assertEqual(fake_lanes.statuses["s02"], "stopped")

    def test_start_claimed_lanes_reports_a_lane_that_fails(self):
        fake_lanes = _FakeLaneManager({"s01": "stopped"})
        fake_lanes.start_lane = lambda lane_id: (False, "compose up failed")
        mgr = self._manager(fake_lanes)
        mgr._claims["11111111-1111-1111-1111-111111111111"] = {
            "station": "s01", "claimed_at": 1.0, "last_active": 1.0,
        }
        mgr._by_station["s01"] = "11111111-1111-1111-1111-111111111111"

        self.assertEqual(
            mgr.start_claimed_lanes(),
            [{"lane": "s01", "success": False, "message": "compose up failed"}],
        )

    def test_start_claimed_lanes_waits_for_a_busy_lane(self):
        # The page's own early start can still hold the lane when the network comes up.
        fake_lanes = _FakeLaneManager({"s01": "starting"})
        answers = [(False, "lane s01 is busy"), (False, "lane s01 is busy"), (True, "already running")]
        fake_lanes.start_lane = lambda lane_id: answers.pop(0)
        mgr = self._manager(fake_lanes)
        self._claim_the_only_station(mgr)

        with patch.object(claims.time, "sleep") as sleep:
            results = mgr.start_claimed_lanes()

        self.assertEqual(results, [{"lane": "s01", "success": True, "message": "already running"}])
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(answers, [])

    def test_start_claimed_lanes_leaves_a_station_released_meanwhile(self) -> None:
        # A release stops the lane (that is what held it busy); the peer must not be started again after it.
        fake_lanes = _FakeLaneManager({"s01": "running"})
        mgr = self._manager(fake_lanes)
        self._claim_the_only_station(mgr)
        calls = []

        def busy_then_released(lane_id):
            calls.append(lane_id)
            mgr._by_station.pop(lane_id)
            return False, f"lane {lane_id} is busy"

        fake_lanes.start_lane = busy_then_released
        with patch.object(claims.time, "sleep"):
            self.assertEqual(mgr.start_claimed_lanes(), [])
        self.assertEqual(calls, ["s01"])

    def _claim_the_only_station(self, mgr):
        owner = "11111111-1111-1111-1111-111111111111"
        mgr._claims[owner] = {"station": "s01", "claimed_at": 1.0, "last_active": 1.0}
        mgr._by_station["s01"] = owner
        return owner

    def test_single_user_claim_hands_back_the_station_without_a_cookie(self):
        # The launcher runs one station for one student: a second browser must not see "no workstations".
        fake_lanes = _FakeLaneManager({"s01": "running"})
        mgr = self._manager(fake_lanes)
        with patch.object(claims, "lane_ids", lambda: ["s01"]), patch.object(claims, "SINGLE_USER", True), \
                patch.object(mgr, "_kick_start_lane") as kick:
            owner = self._claim_the_only_station(mgr)
            self.assertEqual(mgr.claim(existing_uuid=None), (owner, "s01", "resumed"))
            kick.assert_called_once_with("s01")
        self.assertGreater(mgr._claims[owner]["last_active"], 1.0)

    def test_classroom_claim_still_refuses_when_every_station_is_taken(self):
        fake_lanes = _FakeLaneManager({"s01": "running"})
        mgr = self._manager(fake_lanes)
        with patch.object(claims, "lane_ids", lambda: ["s01"]), patch.object(claims, "SINGLE_USER", False), \
                patch.object(mgr, "_kick_start_lane") as kick:
            self._claim_the_only_station(mgr)
            self.assertEqual(mgr.claim(existing_uuid=None), (None, None, "no free stations"))
            kick.assert_not_called()

    def test_pick_free_station_ignores_hot_spares_during_recycle(self):
        fake_lanes = _FakeLaneManager({
            "s01": "running",
            "s02": "stopped",
            "s03": "running",
            "s04": "running",
            "s05": "running",
        })
        mgr = self._manager(fake_lanes)
        mgr._warm_pool_recycling = True

        self.assertEqual(mgr._pick_free_station(), "s02")

        fake_lanes.statuses["s02"] = "running"
        self.assertIsNone(mgr._pick_free_station())


if __name__ == "__main__":
    unittest.main()
