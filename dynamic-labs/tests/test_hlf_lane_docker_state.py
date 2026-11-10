"""The lane manager acts on Docker's state now, not the poller's last view of it.

Lab Tests run 42832515054 (10 Nov 2026): lab.sh's startup enrols each student peer and stops it, and the Docker state
cache polls every few seconds. start_lane trusted a cache that still said the claimed station's peer was running,
waited 180s for a stopped peer to open its port and gave up; in the other job the lane it had just started read
"stopped" until the next poll. These tests run the cache and the lane manager against a stand-in for Docker.
"""
from __future__ import annotations

import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
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
sys.modules.pop("lanes", None)

import hlf_service  # noqa: E402
import lanes  # noqa: E402

PEER = "peer0.student01.example.com"


class _FakeDocker:
    """Docker's container list, which the test changes as lab.sh or compose would."""

    def __init__(self) -> None:
        self.running: set[str] = set()

    def containers(self, _path: str) -> list[dict]:
        return [
            {"Names": [f"/{name}"], "Id": f"{i:012d}", "State": "running" if name in self.running else "exited"}
            for i, name in enumerate(sorted({PEER} | self.running))
        ]


def _cache() -> hlf_service.DockerStateCache:
    """A cache with no poller thread: the test decides when it polls."""
    cache = object.__new__(hlf_service.DockerStateCache)
    cache._lock = threading.Lock()
    cache._containers = {}
    cache._running_names = set()
    cache._logs = {}
    cache._updated_at = 0
    cache._containers_read_at = 0
    return cache


class DockerStateCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.docker = _FakeDocker()
        p = patch.object(hlf_service, "_docker_api_get", side_effect=self.docker.containers)
        p.start()
        self.addCleanup(p.stop)
        self.cache = _cache()

    def test_refresh_containers_reads_docker_now(self) -> None:
        self.docker.running = {PEER}
        self.assertTrue(self.cache.refresh_containers())
        self.assertIn(PEER, self.cache.running_names())
        self.docker.running = set()
        self.assertTrue(self.cache.refresh_containers())
        self.assertNotIn(PEER, self.cache.running_names())

    def test_a_poll_read_before_a_refresh_does_not_overwrite_it(self) -> None:
        # The poller reads the list, then spends seconds on logs; a refresh meanwhile holds the newer list.
        self.docker.running = set()
        old_list = hlf_service.DockerStateCache._read_containers()
        self.docker.running = {PEER}
        self.assertTrue(self.cache.refresh_containers())
        self.assertFalse(self.cache._store_containers(old_list, read_at=0.5))
        self.assertIn(PEER, self.cache.running_names())

    def test_refresh_containers_reports_docker_not_answering(self) -> None:
        with patch.object(hlf_service, "_docker_api_get", side_effect=OSError("no socket")):
            self.assertFalse(self.cache.refresh_containers())


class StartLaneTests(unittest.TestCase):
    """start_lane against a cache whose poller has not run since lab.sh stopped the peer."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        compose = Path(tmp.name) / "compose-students.yaml"
        compose.write_text("services: {}\n", encoding="utf-8")
        self.docker = _FakeDocker()
        self.cache = _cache()
        patches = [
            patch.object(hlf_service, "_docker_api_get", side_effect=self.docker.containers),
            patch.object(hlf_service.DockerStateCache, "get", return_value=self.cache),
            patch.object(lanes, "lane_ids", lambda: ["s01"]),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.mgr = lanes.LaneManager(compose_file=compose, state_path=Path(tmp.name) / "lanes.json")
        self.compose_calls: list[list[str]] = []

        def run(cmd, timeout=None):
            self.compose_calls.append(list(cmd))
            if "up" in cmd:
                self.docker.running.add(PEER)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        for name, value in {
            "_run": run,
            "_ensure_lane_disk_seeded": lambda lane_id: (True, ""),
            "_apply_peer_limits": lambda peer: (True, ""),
            "_ensure_channel_joined": self._joined,
            "_shell_helpers_ready": lambda peer: True,
        }.items():
            p = patch.object(self.mgr, name, side_effect=value)
            p.start()
            self.addCleanup(p.stop)

    def _joined(self, lane_id: str) -> tuple[bool, str]:
        # The real join waits for the peer's port; a stopped peer never opens it.
        if PEER not in self.docker.running:
            return False, f"{PEER} did not open 7051 within 180s"
        return True, "already-joined"

    def test_a_peer_stopped_since_the_last_poll_is_started(self) -> None:
        self.docker.running = {PEER}
        self.cache.refresh_containers()  # the poller saw the peer that enrolment started
        self.docker.running = set()      # then lab.sh stopped it, and the poller has not run since
        ok, msg = self.mgr.start_lane("s01")
        self.assertTrue(ok, msg)
        self.assertEqual(msg, "started")
        self.assertTrue(any("up" in cmd for cmd in self.compose_calls), self.compose_calls)

    def test_a_started_lane_reads_running_at_once(self) -> None:
        self.cache.refresh_containers()
        ok, msg = self.mgr.start_lane("s01")
        self.assertTrue(ok, msg)
        lane = {row["id"]: row for row in self.mgr.list_lanes()}["s01"]
        self.assertEqual((lane["status"], lane["live"]), ("running", True), lane)

    def test_a_stopped_lane_reads_stopped_at_once(self) -> None:
        self.docker.running = {PEER}
        self.cache.refresh_containers()

        def stop(cmd, timeout=None):
            self.docker.running.discard(PEER)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch.object(self.mgr, "_run", side_effect=stop):
            ok, msg = self.mgr.stop_lane("s01")
        self.assertTrue(ok, msg)
        lane = {row["id"]: row for row in self.mgr.list_lanes()}["s01"]
        self.assertEqual((lane["status"], lane["live"]), ("stopped", False), lane)


if __name__ == "__main__":
    unittest.main()
