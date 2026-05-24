from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HlfCloudRuntimeAssetsTests(unittest.TestCase):
    def test_cloud_deploy_allows_hlf_asset_download_and_prebuilds_hlf(self) -> None:
        script = (ROOT / "deploy-cloud.sh").read_text(encoding="utf-8")

        self.assertIn("LAB_MANAGER_CLOUD_MODE=1 HLF_ALLOW_RUNTIME_DOWNLOADS=1", script)
        self.assertIn("build-images bitcoin consensus p2p_trust ethereum_lab hlf", script)

    def test_cloud_deploy_help_documents_forwarded_capacity_options(self) -> None:
        script = (ROOT / "deploy-cloud.sh").read_text(encoding="utf-8")

        self.assertIn("Usage:", script)
        self.assertIn("--max-student-capacity N", script)
        self.assertIn("--bitcoin-student-capacity N", script)
        self.assertIn("--consensus-student-capacity N", script)
        self.assertIn("--p2p-trust-student-capacity N", script)
        self.assertIn("--ethereum-student-capacity N", script)
        self.assertIn("--hlf-student-capacity N", script)
        self.assertIn("Capacity options are forwarded to:", script)

    def test_readme_documents_cloud_capacity_and_quiz_engine_v2_target(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Cloud deploy accepts the same claim-lane capacity controls", readme)
        self.assertIn("--hlf-student-capacity N", readme)
        self.assertIn("`quiz-engine-v2` | Quiz engine", readme)
        self.assertIn("cryptography, exercises, quiz-engine-v2", readme)

    def test_lab_manager_enables_hlf_downloads_only_for_cloud_mode(self) -> None:
        script = (ROOT / "lab-manager.sh").read_text(encoding="utf-8")

        self.assertIn("cloud_runtime_mode() {", script)
        self.assertIn('${RUNTIME_DIR}/cloud-domain.txt', script)
        self.assertIn('export HLF_ALLOW_RUNTIME_DOWNLOADS="${HLF_ALLOW_RUNTIME_DOWNLOADS:-1}"', script)
        self.assertIn('if [[ "$(basename "${dir}")" == "hlf" ]]; then', script)

    def test_hlf_lab_keeps_offline_default_but_supports_explicit_runtime_downloads(self) -> None:
        script = (ROOT / "hlf" / "lab.sh").read_text(encoding="utf-8")

        self.assertIn("HLF_ALLOW_RUNTIME_DOWNLOADS", script)
        self.assertIn('local install_script="${HERE}/runtime/install-fabric.sh"', script)
        self.assertIn('FABRIC_SAMPLES_REF="${FABRIC_SAMPLES_REF}"', script)
        self.assertIn("Runtime bootstrap no longer clones or downloads from the internet", script)


if __name__ == "__main__":
    unittest.main()
