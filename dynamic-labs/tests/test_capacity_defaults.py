from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CapacityDefaultsTests(unittest.TestCase):
    def test_lab_manager_defaults_to_20_and_accepts_40(self) -> None:
        script = (ROOT / "lab-manager.sh").read_text(encoding="utf-8")

        self.assertIn(
            'MAX_STUDENT_CAPACITY_LIMIT="${LAB_MANAGER_MAX_STUDENT_CAPACITY_LIMIT:-40}"',
            script,
        )
        self.assertIn(
            'DEFAULT_INSTRUCTOR_MAX_STUDENT_CAPACITY="${LAB_MANAGER_DEFAULT_INSTRUCTOR_MAX_STUDENT_CAPACITY:-20}"',
            script,
        )
        self.assertIn(
            'DEFAULT_STUDENT_MAX_STUDENT_CAPACITY="${LAB_MANAGER_DEFAULT_STUDENT_MAX_STUDENT_CAPACITY:-5}"',
            script,
        )
        self.assertIn(
            "Base lane capacity for claim-based labs (default instructor: 20, max: 40)",
            script,
        )
        self.assertIn(
            'Capacity must be ${MAX_STUDENT_CAPACITY_LIMIT} or less',
            script,
        )

    def test_lane_service_defaults_to_20(self) -> None:
        compose = (ROOT / "lane-service/docker-compose.yml").read_text(
            encoding="utf-8"
        )
        generic = (ROOT / "lane-service/generic_lanes.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("MAX_STUDENT_CAPACITY=${MAX_STUDENT_CAPACITY:-20}", compose)
        self.assertIn("student_count: int = 20", generic)
        self.assertIn('os.getenv("MAX_STUDENT_CAPACITY") or "20"', generic)

        for rel in (
            "lane-service/labs/bitcoin.py",
            "lane-service/labs/consensus.py",
            "lane-service/labs/p2p_trust.py",
            "lane-service/labs/ethereum.py",
        ):
            lab = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("default=20", lab, rel)
            self.assertNotIn("default=30", lab, rel)

    def test_ethereum_student_pool_uses_configured_capacity(self) -> None:
        compose = (ROOT / "ethereum_lab/docker-compose.yml").read_text(
            encoding="utf-8"
        )
        entrypoint = (ROOT / "ethereum_lab/docker-entrypoint.sh").read_text(
            encoding="utf-8"
        )
        pool_script = (
            ROOT / "ethereum_lab/scripts/setup-student-pool.js"
        ).read_text(encoding="utf-8")

        self.assertIn("MAX_STUDENT_CAPACITY=${MAX_STUDENT_CAPACITY:-20}", compose)
        self.assertIn("ETHEREUM_STUDENT_CAPACITY=${ETHEREUM_STUDENT_CAPACITY:-}", compose)
        self.assertIn(
            'export POOL_SIZE="${POOL_SIZE:-${ETHEREUM_STUDENT_CAPACITY:-${MAX_STUDENT_CAPACITY:-20}}}"',
            entrypoint,
        )
        self.assertIn("process.env.ETHEREUM_STUDENT_CAPACITY", pool_script)
        self.assertIn("process.env.MAX_STUDENT_CAPACITY", pool_script)
        self.assertIn('"20"', pool_script)

    def test_hlf_defaults_to_20_and_committed_assets_include_40(self) -> None:
        hlf_lab = (ROOT / "hlf/lab.sh").read_text(encoding="utf-8")
        hlf_compose = (ROOT / "hlf/docker-compose.yml").read_text(
            encoding="utf-8"
        )
        lanes = (ROOT / "hlf/web_service/lanes.py").read_text(encoding="utf-8")
        student_context = (ROOT / "hlf/web_service/student_context.py").read_text(
            encoding="utf-8"
        )
        schools = json.loads(
            (ROOT / "hlf/managed_runtime/schools.json").read_text(
                encoding="utf-8"
            )
        )
        committed_compose = (
            ROOT / "hlf/managed_runtime/compose-students.yaml"
        ).read_text(encoding="utf-8")
        committed_configtx = (
            ROOT / "hlf/managed_runtime/configtx-4org-students.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn('${MAX_STUDENT_CAPACITY:-20}', hlf_lab)
        self.assertIn("MAX_STUDENT_CAPACITY: ${MAX_STUDENT_CAPACITY:-20}", hlf_compose)
        self.assertIn('os.environ.get("MAX_STUDENT_CAPACITY", "20")', lanes)
        self.assertIn('or "20"', student_context)
        self.assertIn("s40", schools)
        self.assertIn("Student40MSP", schools["s40"]["msp_id"])
        self.assertIn("peer0.student40.example.com", committed_compose)
        self.assertIn("Student overlay compose: 40 profile-gated", committed_compose)
        self.assertIn("Student01..40", committed_configtx)
        self.assertTrue((ROOT / "hlf/managed_runtime/crypto-config-student40.yaml").exists())

    def test_hlf_generator_can_render_40_lanes(self) -> None:
        script = ROOT / "hlf/managed_runtime/generate_student_overlay.py"
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HLF_STUDENT_COUNT"] = "40"
            env["HLF_HOST_HLF_DIR"] = str(ROOT / "hlf")
            subprocess.run(
                [sys.executable, str(script), "--out", tmp],
                check=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            out = Path(tmp)
            self.assertTrue((out / "crypto-config-student40.yaml").exists())
            self.assertIn(
                "peer0.student40.example.com",
                (out / "compose-students.yaml").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Student40MSP",
                (out / "configtx-4org-students.yaml").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
