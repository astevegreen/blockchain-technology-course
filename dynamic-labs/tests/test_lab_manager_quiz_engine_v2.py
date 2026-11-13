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

    def test_hosting_page_reaches_lab_manager_through_the_runner_not_docker(self) -> None:
        script = (ROOT / "lab-manager.sh").read_text(encoding="utf-8")
        compose = (ROOT / "quiz-engine-v2" / "compose.yaml").read_text(encoding="utf-8")
        credentials = (ROOT / "runtime-credentials.sh").read_text(encoding="utf-8")

        self.assertRegex(script, r"\n\s+start_hosting_runner\n")
        self.assertIn("quiz-engine-v2/app/hosting_runner.py", script)
        # The quiz engine faces students' network: it gets the runner's socket folder, never Docker's socket.
        self.assertNotIn("docker.sock", compose)
        self.assertIn(":/run/hosting-runner", compose)
        # The runner binds its socket in the folder the engine mounts (a Linux path: WSL cannot bind on /mnt/c),
        # and the script refuses a shared-/tmp folder it does not own.
        self.assertIn('--socket-dir "${socket_dir}"', script)
        self.assertIn('QUIZ_ENGINE_HOSTING_RUNNER_DIR="${HOSTING_RUNNER_SOCKET_DIR:-}"', script)
        self.assertIn('-L "${socket_dir}" || ! -O "${socket_dir}"', script)
        # deploy generates the secret, and an older env file gains it on the next deploy.
        self.assertIn("HOSTING_RUNNER_SECRET=${HOSTING_RUNNER_SECRET}", credentials)
        self.assertEqual(credentials.count('HOSTING_RUNNER_SECRET="$(runtime_random_hex 32)"'), 2)


if __name__ == "__main__":
    unittest.main()
