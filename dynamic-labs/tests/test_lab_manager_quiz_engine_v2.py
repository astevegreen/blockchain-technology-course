from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LabManagerQuizEngineV2Tests(unittest.TestCase):
    def test_quiz_engine_target_points_to_v2(self) -> None:
        script = (ROOT / "lab-manager.sh").read_text(encoding="utf-8")

        self.assertIn(
            'quiz|quiz-engine-v2) echo "${BASE_DIR}/quiz-engine-v2" ;;',
            script,
        )
        self.assertNotIn("quiz|quiz-" + "engine|quiz-engine-v2)", script)
        listed_targets = script.split("list_targets() {", 1)[1].split("EOF", 2)[1]
        self.assertIn("quiz-engine-v2", listed_targets)
        self.assertNotIn("\nquiz-engine\n", listed_targets)
        self.assertIn(
            "QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=shared INSTRUCTOR_AUTH_MODE=shared compose_up_cmd",
            script,
        )


if __name__ == "__main__":
    unittest.main()
