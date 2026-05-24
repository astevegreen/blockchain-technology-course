from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class QuizEngineV2PackagingTests(unittest.TestCase):
    def test_vm_image_bundler_packages_quiz_engine_v2(self) -> None:
        script = (REPO_ROOT / "vm-build/prepare-docker-image-bundles.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('"dynamic-labs/quiz-engine-v2"', script)
        self.assertNotIn('"dynamic-labs/quiz-' + 'engine"', script)
        self.assertIn('"$project_dir/compose.yaml"', script)

    def test_vm_workflow_checks_for_v2_bundle_only(self) -> None:
        workflow = (
            REPO_ROOT / ".github/workflows/build-and-package.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("vm-build/docker-image-bundles/quiz-engine-v2.tar", workflow)
        self.assertNotIn(
            "dynamic-labs -maxdepth 1 -type d -name 'quiz-" + "engine'",
            workflow,
        )
        self.assertNotIn(
            "vm-build/docker-image-bundles/quiz-" + "engine.tar",
            workflow,
        )

    def test_quiz_engine_entrypoint_is_resilient_to_lost_host_file_modes(self) -> None:
        dockerfile = (
            REPO_ROOT / "dynamic-labs/quiz-engine-v2/Dockerfile"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/quiz-engine-entrypoint",
            dockerfile,
        )
        self.assertIn(
            'ENTRYPOINT ["/bin/sh", "/usr/local/bin/quiz-engine-entrypoint"]',
            dockerfile,
        )

    def test_shared_auth_sync_no_longer_targets_legacy_quiz_engine(self) -> None:
        script = (REPO_ROOT / "dynamic-labs/scripts/sync-shared.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('"dynamic-labs/quiz-engine-v2:instructor_auth"', script)
        self.assertNotIn('"dynamic-labs/quiz-' + 'engine:instructor_auth"', script)

    def test_student_source_zip_excludes_quiz_solution_inputs(self) -> None:
        workflow = (
            REPO_ROOT / ".github/workflows/build-and-package.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "zip -r blockchain-course/assets/src.zip blockchain-course dynamic-labs",
            workflow,
        )
        self.assertIn("Keep instructor quiz banks/solutions out", workflow)
        self.assertIn('-x "quizes/**"', workflow)
        self.assertIn('-x "quizes/*"', workflow)
        self.assertIn('-x "dynamic-labs/**/quizes/**"', workflow)
        self.assertIn('-x "dynamic-labs/**/quizes/*"', workflow)


if __name__ == "__main__":
    unittest.main()
