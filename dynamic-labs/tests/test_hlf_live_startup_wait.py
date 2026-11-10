"""The live suite's startup wait (regression-tests/automated/hlf/live_support.py) stops at once on a failed startup.

A startup that ends without the network (a bootstrap stopped by its time limit) used to keep every test class
waiting its full 15 minutes, so the Lab Tests job hit 30 minutes before any test said why.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "regression-tests" / "automated" / "hlf"))
sys.modules.pop("live_support", None)

import live_support  # noqa: E402

STOPPED_MESSAGE = "[hlf] ERROR: Fabric setup (lab.sh bootstrap) was stopped after 15 minutes without finishing."


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _status(status: str, task: str | None, detail: str = "") -> dict:
    return {"status": status, "background_task": task, "lifecycle_progress": {"detail": detail}}


class StartupWaitTests(unittest.TestCase):
    def _wait(self, statuses: list[dict], **kwargs) -> tuple[dict | Exception, _Clock]:
        clock = _Clock()
        feed = iter(statuses)
        last = statuses[-1]

        def next_status(*_args, **_kwargs):
            return next(feed, last)

        with patch.object(live_support, "time", clock), \
                patch.object(live_support, "get_hlf_status", side_effect=next_status):
            try:
                return live_support.wait_for_hlf_startup_complete(None, "http://router", **kwargs), clock
            except live_support.RegressionFailure as exc:
                return exc, clock

    def test_a_startup_that_ends_without_the_network_fails_with_its_last_line(self) -> None:
        result, clock = self._wait([
            _status("starting", "start", "[hlf] Building ttyd-enabled Fabric images..."),
            _status("stopped", None, STOPPED_MESSAGE),
        ])
        self.assertIsInstance(result, live_support.RegressionFailure)
        self.assertIn("HLF startup ended without the network running", str(result))
        self.assertIn(STOPPED_MESSAGE, str(result))
        self.assertLess(clock.now - 1000.0, 120, "the wait did not stop soon after the startup ended")

    def test_a_brief_gap_between_tasks_is_not_a_failure(self) -> None:
        result, _clock = self._wait([
            _status("starting", "start"),
            _status("stopped", None),
            _status("starting", "start"),
            _status("running", None),
        ])
        self.assertEqual(result.get("status"), "running")

    def test_a_long_startup_is_still_waited_for(self) -> None:
        statuses = [_status("starting", "start")] * 100 + [_status("running", None)]
        result, _clock = self._wait(statuses)
        self.assertEqual(result.get("status"), "running")


if __name__ == "__main__":
    unittest.main()
