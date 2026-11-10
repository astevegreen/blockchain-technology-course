"""A failed network task reads as "error", and its last lifecycle lines stay readable after it ends.

Before, the status API turned a failed start into "stopped" (the instructor's overlay then said "Completed
successfully."), and the in-memory log was emptied the moment the task ended, so the overlay could miss the line
that said why.
"""
from __future__ import annotations

import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch


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
sys.modules.pop("hlf_service", None)

import hlf_service  # noqa: E402

NAMES = {
    "peer_org1": "peer0.cascadiastate.example.com",
    "peer_org2": "peer0.chesapeakecanoe.example.com",
    "peer_org3": "peer0.southhudson.example.com",
    "peer_org4": "peer0.mapleleaf.example.com",
    "peer_org5": "peer0.meridian.example.com",
    "orderer": "orderer.example.com",
}


class _Container:
    def __init__(self, status: str) -> None:
        self.status = status
        self.id = "0123456789abcdef"


class LifecycleStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.service = hlf_service.HLFLabService(lab_path=tmp.name)
        self.service._container_names = dict(NAMES)
        self.containers: dict = {}
        for name, value in (
            ("_list_containers_by_name", lambda: self.containers),
            ("_live_student_lanes", lambda: []),
        ):
            p = patch.object(self.service, name, side_effect=value)
            p.start()
            self.addCleanup(p.stop)

    def _run_task(self, target) -> None:
        self.service._run_background_task("start", target)
        deadline = time.monotonic() + 10
        while self.service.background_task is not None and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertIsNone(self.service.background_task)

    def _failed_start(self) -> None:
        svc = self.service

        def target() -> None:
            svc._record_lifecycle_line("[hlf] ERROR: Fabric setup (lab.sh bootstrap) was stopped after 15 minutes.")
            with svc._state_lock:
                svc.status = hlf_service.LabStatus.ERROR

        self._run_task(target)

    def test_a_failed_start_reads_as_error_not_stopped(self) -> None:
        self._failed_start()
        for _ in range(2):  # the status poll must not overwrite it either
            self.assertEqual(self.service.get_network_status()["status"], hlf_service.LabStatus.ERROR)
        self.assertEqual(self.service.get_lifecycle_log(0)["status"], hlf_service.LabStatus.ERROR)

    def test_a_running_network_clears_the_error(self) -> None:
        self._failed_start()
        self.containers = {name: _Container("running") for name in NAMES.values()}
        self.assertEqual(self.service.get_network_status()["status"], hlf_service.LabStatus.RUNNING)

    def test_a_network_stopped_without_an_error_still_reads_stopped(self) -> None:
        self.assertEqual(self.service.get_network_status()["status"], hlf_service.LabStatus.STOPPED)

    def test_the_last_lines_stay_readable_after_the_task_ends(self) -> None:
        self._failed_start()
        lines = self.service.get_lifecycle_log(0)["lines"]
        self.assertTrue(any("was stopped after 15 minutes" in line for line in lines), lines)

    def test_the_next_task_starts_with_an_empty_log(self) -> None:
        self._failed_start()
        seen_at_start = []
        started = threading.Event()

        def target() -> None:
            seen_at_start.extend(self.service.get_lifecycle_log(0)["lines"])
            started.set()

        self._run_task(target)
        self.assertTrue(started.is_set())
        self.assertEqual(seen_at_start, [])

    def test_a_new_task_shows_as_running_while_it_runs(self) -> None:
        self._failed_start()
        release = threading.Event()
        self.service._run_background_task("start", release.wait)
        try:
            self.assertEqual(self.service.get_network_status()["status"], hlf_service.LabStatus.STARTING)
        finally:
            release.set()


if __name__ == "__main__":
    unittest.main()
