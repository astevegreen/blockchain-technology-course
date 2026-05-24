from __future__ import annotations

import sys
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


class HlfGovernanceDetailContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = hlf_service.HLFLabService()

    def test_save_scenario_state_invalidates_governance_detail_cache(self) -> None:
        self.service._governance_detail_cache = {"active_scenario": {"id": "identity-authority"}}
        self.service._governance_detail_ts = 123.0

        self.service._save_scenario_state({"identity-authority": {"phase": "active"}})

        self.assertIsNone(self.service._governance_detail_cache)
        self.assertEqual(self.service._governance_detail_ts, 0.0)

    def test_governance_detail_surfaces_cached_active_identity_scenario(self) -> None:
        self.service._scenario_status_cache = {
            "identity-authority": {
                "phase": "active",
                "checks": [{"label": "cached check", "ok": True, "detail": "cached detail"}],
            }
        }

        with patch.object(
            self.service,
            "get_network_status",
            return_value={"status": hlf_service.LabStatus.RUNNING, "containers": {}},
        ), patch.object(
            self.service,
            "_inspect_channel_governance",
            return_value={"channel_id": "diplomas", "application_policies": [], "orderer_policies": [], "organizations": []},
        ), patch.object(
            self.service,
            "_inspect_recent_blocks",
            return_value={"recent_blocks": []},
        ):
            payload = self.service.get_governance_detail()

        self.assertEqual(payload["active_scenario"]["id"], "identity-authority")
        self.assertEqual(payload["active_scenario"]["title"], "Governance: Who Can Change the Rules?")
        self.assertEqual(payload["active_scenario"]["checks"][0]["label"], "cached check")

    def test_governance_detail_falls_back_to_persisted_active_identity_scenario(self) -> None:
        governance_snapshot = {
            "application_policies": [{"name": "Admins", "mod_policy": "Admins"}],
            "orderer_policies": [{"name": "BlockValidation", "mod_policy": "Admins"}],
            "organizations": [{"msp_id": "Org1MSP"}, {"msp_id": "Org2MSP"}],
        }

        with patch.object(
            self.service,
            "get_network_status",
            return_value={"status": hlf_service.LabStatus.RUNNING, "containers": {}},
        ), patch.object(
            self.service,
            "_inspect_channel_governance",
            return_value={"channel_id": "diplomas", "application_policies": [], "orderer_policies": [], "organizations": []},
        ), patch.object(
            self.service,
            "_inspect_recent_blocks",
            return_value={"recent_blocks": []},
        ), patch.object(
            self.service,
            "_load_scenario_state",
            return_value={"identity-authority": {"phase": "active", "governance_snapshot": governance_snapshot}},
        ):
            payload = self.service.get_governance_detail()

        self.assertEqual(payload["active_scenario"]["id"], "identity-authority")
        self.assertEqual(payload["active_scenario"]["phase"], "active")
        self.assertEqual(len(payload["active_scenario"]["checks"]), 3)
        self.assertTrue(payload["active_scenario"]["checks"][0]["ok"])


if __name__ == "__main__":
    unittest.main()
