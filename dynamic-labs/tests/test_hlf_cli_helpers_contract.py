from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "hlf" / "scripts" / "hlf_cli_helpers.sh"


class HlfCliHelpersContractTests(unittest.TestCase):
    def _run_bash(self, script: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "-lc", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def test_query_targets_first_live_consortium_peer(self) -> None:
        proc = self._run_bash(
            f"""
source "{HELPERS}"
_hlf_peer_live() {{
  [[ "$1" == "peer0.chesapeakecanoe.example.com:9051" ]]
}}
peer() {{
  printf '%s\\n' "$@"
}}
PEER0_ORG1_CA=/tmp/org1-ca
PEER0_ORG2_CA=/tmp/org2-ca
PEER0_ORG3_CA=/tmp/org3-ca
PEER0_ORG4_CA=/tmp/org4-ca
query shipment-s03-001
"""
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--peerAddresses", proc.stdout)
        self.assertIn("peer0.chesapeakecanoe.example.com:9051", proc.stdout)
        self.assertIn("--tlsRootCertFiles", proc.stdout)
        self.assertIn("/tmp/org2-ca", proc.stdout)
        self.assertIn("ReadAsset", proc.stdout)
        self.assertIn("shipment-s03-001", proc.stdout)

    def test_query_fails_cleanly_when_no_live_consortium_peer_is_reachable(self) -> None:
        proc = self._run_bash(
            f"""
source "{HELPERS}"
_hlf_peer_live() {{
  return 1
}}
peer() {{
  printf 'unexpected'
}}
PEER0_ORG1_CA=/tmp/org1-ca
PEER0_ORG2_CA=/tmp/org2-ca
PEER0_ORG3_CA=/tmp/org3-ca
PEER0_ORG4_CA=/tmp/org4-ca
query shipment-s03-001
"""
        )

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("No live consortium peers are reachable for query", proc.stderr)


if __name__ == "__main__":
    unittest.main()
