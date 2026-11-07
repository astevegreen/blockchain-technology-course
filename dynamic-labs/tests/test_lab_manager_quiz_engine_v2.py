from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LabManagerQuizEngineV2Tests(unittest.TestCase):
    def test_lab_manager_starts_quiz_engine_with_shared_instructor_auth(self) -> None:
        script = (ROOT / "lab-manager.sh").read_text(encoding="utf-8")

        self.assertIn(
            "QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=shared INSTRUCTOR_AUTH_MODE=shared compose_up_cmd",
            script,
        )
        # test-header trusts a request header: a deployed quiz engine never uses it.
        self.assertNotIn("test-header", script)


if __name__ == "__main__":
    unittest.main()
