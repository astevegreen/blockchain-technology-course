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
