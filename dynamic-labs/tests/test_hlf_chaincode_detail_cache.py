from __future__ import annotations

import sys
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


class HlfChaincodeDetailCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = hlf_service.HLFLabService()

    def test_get_chaincode_detail_returns_placeholder_while_refresh_starts(self) -> None:
        with patch.object(
            self.service,
            "get_network_status",
            return_value={"status": hlf_service.LabStatus.RUNNING},
        ), patch.object(self.service, "_refresh_chaincode_detail_async") as refresh:
            payload = self.service.get_chaincode_detail()

        self.assertEqual(payload["network"]["status"], hlf_service.LabStatus.RUNNING)
        self.assertTrue(payload["chaincode"]["meta"]["refreshing"])
        self.assertIn("Preparing chaincode lifecycle details", payload["chaincode"]["message"])
        refresh.assert_called_once()

    def test_get_chaincode_detail_returns_stale_cache_while_refreshing(self) -> None:
        self.service._chaincode_detail_cache = {
            "name": "basic",
            "channel": "diplomas",
            "committed": {"org1": {"ok": True, "output": "cached"}},
            "approved": {},
            "installed": {},
        }
        self.service._chaincode_detail_ts = time.time() - 121

        with patch.object(
            self.service,
            "get_network_status",
            return_value={"status": hlf_service.LabStatus.RUNNING},
        ), patch.object(self.service, "_refresh_chaincode_detail_async") as refresh:
            payload = self.service.get_chaincode_detail()

        self.assertTrue(payload["chaincode"]["meta"]["cached"])
        self.assertTrue(payload["chaincode"]["meta"]["refreshing"])
        self.assertEqual(payload["chaincode"]["committed"]["org1"]["output"], "cached")
        self.assertIn("Refreshing chaincode lifecycle details", payload["chaincode"]["message"])
        refresh.assert_called_once()

    def test_get_chaincode_detail_returns_fresh_cache_without_refresh(self) -> None:
        self.service._chaincode_detail_cache = {
            "name": "basic",
            "channel": "diplomas",
            "committed": {"org1": {"ok": True, "output": "fresh"}},
            "approved": {},
            "installed": {},
        }
        self.service._chaincode_detail_ts = time.time() - 5

        with patch.object(
            self.service,
            "get_network_status",
            return_value={"status": hlf_service.LabStatus.RUNNING},
        ), patch.object(self.service, "_refresh_chaincode_detail_async") as refresh:
            payload = self.service.get_chaincode_detail()

        self.assertTrue(payload["chaincode"]["meta"]["cached"])
        self.assertFalse(payload["chaincode"]["meta"]["refreshing"])
        self.assertEqual(payload["chaincode"]["committed"]["org1"]["output"], "fresh")
        self.assertNotIn("message", payload["chaincode"])
        refresh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
