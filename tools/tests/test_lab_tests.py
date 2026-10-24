"""Tests for tools/lab_tests.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab_tests  # noqa: E402

TESTS = "dynamic-labs/regression-tests"


class LabsFor(unittest.TestCase):
    def setUp(self) -> None:
        patch = mock.patch.object(lab_tests, "IN_CI", ["exercises", "quiz-engine"])
        patch.start()
        self.addCleanup(patch.stop)

    def test_a_lab_folder_runs_its_own_tests(self) -> None:
        self.assertEqual(lab_tests.labs_for(["dynamic-labs/exercises/l03-i3-bgp-game/app/app.py"]), ["exercises"])
        self.assertEqual(lab_tests.labs_for(["dynamic-labs/quiz-engine-v2/app.py"]), ["quiz-engine"])
        self.assertEqual(lab_tests.labs_for([f"{TESTS}/automated/quiz-engine/run.sh"]), ["quiz-engine"])

    def test_a_lab_not_yet_in_ci_runs_nothing(self) -> None:
        self.assertEqual(lab_tests.labs_for(["dynamic-labs/hlf/app.py", f"{TESTS}/automated/hlf/run.sh"]), [])

    def test_shared_parts_and_the_workflow_run_every_ci_lab(self) -> None:
        for f in ["dynamic-labs/lab-manager.sh", "dynamic-labs/router/nginx.conf", "dynamic-labs/lane-service/app.py",
                  f"{TESTS}/infrastructure/reset_live_claims.py", ".github/workflows/lab-tests.yml", "tools/lab_tests.py"]:
            self.assertEqual(lab_tests.labs_for([f]), ["exercises", "quiz-engine"], f)

    def test_docs_playbooks_and_files_outside_the_labs_run_nothing(self) -> None:
        for f in ["dynamic-labs/README.md", "dynamic-labs/docs/plan.md", "dynamic-labs/bitcoin-forensics/lab.md",
                  f"{TESTS}/agent/exercises/playbook.md", f"{TESTS}/unit/test_hlf_my_term.py",
                  f"{TESTS}/automated/README.md", "blockchain-course/index.qmd", "CLAUDE.md"]:
            self.assertEqual(lab_tests.labs_for([f]), [], f)

    def test_every_ci_lab_and_renamed_lab_has_a_run_sh(self) -> None:
        tested = lab_tests.tested_labs()
        for lab in [*lab_tests.IN_CI, *lab_tests.TEST_NAME.values()]:
            self.assertIn(lab, tested)
        for folder in lab_tests.TEST_NAME:
            self.assertTrue((lab_tests.REPO / "dynamic-labs" / folder).is_dir(), folder)


class Runners(unittest.TestCase):
    def test_every_run_sh_calls_lab_manager_through_bash(self) -> None:
        # lab-manager.sh isn't executable in git: `./lab-manager.sh` works on Windows and WSL, then fails on GitHub.
        for lab in lab_tests.tested_labs():
            run_sh = lab_tests.REPO / lab_tests.AUTOMATED / lab / "run.sh"
            for n, line in enumerate(run_sh.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0].strip()
                if code.startswith("./lab-manager.sh"):
                    self.fail(f"{run_sh.relative_to(lab_tests.REPO)}:{n} runs ./lab-manager.sh; use bash ./lab-manager.sh")


class Main(unittest.TestCase):
    def test_named_labs_must_have_a_run_sh(self) -> None:
        with mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(lab_tests.main(["--labs", "hlf exercises"]), 0)
            self.assertEqual(lab_tests.main(["--labs", "exercise"]), 1)

    def test_a_missing_base_commit_runs_every_ci_lab(self) -> None:
        with mock.patch.object(lab_tests, "changed", return_value=None), mock.patch("builtins.print") as out:
            lab_tests.main(["--base", "0" * 40])
        out.assert_called_once_with(lab_tests.json.dumps(lab_tests.IN_CI))


if __name__ == "__main__":
    unittest.main()
