"""The Fabric bootstrap's time limit (hlf_service.bootstrap_runtime) and the lifecycle log that reports it.

Lab Tests run 42760037609 (10 Nov 2026) sat in the bootstrap until the job's 30-minute limit, and the lifecycle
log reached the job output only when startup ended. These tests run a stand-in for `lab.sh bootstrap`.
"""
from __future__ import annotations

import re
import sys
import tempfile
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

LAB_TESTS_WORKFLOW = ROOT.parent / ".github" / "workflows" / "lab-tests.yml"


def _python(script: str) -> list[str]:
    return [sys.executable, "-u", "-c", script]


SLOW_BOOTSTRAP = _python("print('[hlf] Building ttyd-enabled Fabric images...'); import time; time.sleep(60)")


class BootstrapLimitTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.lab = Path(tmp.name)
        self.service = hlf_service.HLFLabService(lab_path=str(self.lab))
        self.lifecycle_file = self.lab / "runtime" / "lifecycle.log"

    def _bootstrap_with(self, command: list[str], timeout_seconds: int = 60):
        with patch.object(self.service, "_bootstrap_command", return_value=command):
            return self.service.bootstrap_runtime(timeout_seconds=timeout_seconds)

    def _log(self) -> list[str]:
        return self.service.get_lifecycle_log(0)["lines"]

    def test_a_bootstrap_that_runs_past_the_limit_is_stopped_with_a_plain_message(self) -> None:
        started = time.monotonic()
        ok, message = self._bootstrap_with(SLOW_BOOTSTRAP, timeout_seconds=1)
        self.assertLess(time.monotonic() - started, 30, "the limit did not stop the bootstrap")
        self.assertFalse(ok)
        self.assertIn("Fabric setup (lab.sh bootstrap) was stopped after 1 second without finishing", message)
        self.assertIn("Check the internet connection and Docker, then start the network again.", message)
        self.assertNotIn("bootstrap", self.service.processes)
        log = self._log()
        self.assertTrue(any("Building ttyd-enabled Fabric images" in line for line in log), log)
        self.assertTrue(log[-1].endswith(message), log)
        self.assertEqual(self.service.lifecycle_progress["detail"], message)

    def test_the_stopped_bootstrap_leaves_no_process_running(self) -> None:
        procs = []
        real_popen = hlf_service.subprocess.Popen

        def keep(*args, **kwargs):
            proc = real_popen(*args, **kwargs)
            procs.append(proc)
            return proc

        with patch.object(hlf_service.subprocess, "Popen", side_effect=keep):
            self._bootstrap_with(SLOW_BOOTSTRAP, timeout_seconds=1)
        self.assertEqual(len(procs), 1)
        self.assertIsNotNone(procs[0].poll(), "the bootstrap process was left running")

    def test_the_message_names_the_last_lines_of_the_bootstrap_log(self) -> None:
        (self.lab / "runtime" / "bootstrap.log").write_text(
            "#5 [2/9] RUN apt-get update\n\n#5 Get:1 http://deb.debian.org/debian trixie InRelease\n",
            encoding="utf-8",
        )
        self._bootstrap_with(SLOW_BOOTSTRAP, timeout_seconds=1)
        log = "\n".join(self._log())
        self.assertIn("The last lines of runtime/bootstrap.log:", log)
        self.assertIn("RUN apt-get update", log)
        self.assertIn("Get:1 http://deb.debian.org/debian trixie InRelease", log)

    def test_the_lines_reach_lifecycle_log_on_disk_as_they_happen(self) -> None:
        # The hlf-launcher job follows runtime/lifecycle.log; the stop must be there before the start task ends.
        _ok, message = self._bootstrap_with(SLOW_BOOTSTRAP, timeout_seconds=1)
        on_disk = self.lifecycle_file.read_text(encoding="utf-8")
        self.assertIn("Building ttyd-enabled Fabric images", on_disk)
        self.assertIn(message, on_disk)
        self.assertIsNone(self.service.background_task)

    def test_a_failed_bootstrap_reports_its_exit_code(self) -> None:
        ok, message = self._bootstrap_with(_python("print('[hlf] ERROR: boom'); raise SystemExit(3)"))
        self.assertFalse(ok)
        self.assertIn("failed with exit code 3", message)
        log = self._log()
        self.assertTrue(any(line.endswith("[hlf] ERROR: boom") for line in log), log)
        self.assertTrue(log[-1].endswith(message), log)

    def test_a_bootstrap_that_finishes_in_time_succeeds_and_logs_its_output(self) -> None:
        # Its output used to be read only when a stream callback was passed, and start_network passes none.
        ok, message = self._bootstrap_with(_python("print('[hlf] Bootstrap complete.')"))
        self.assertTrue(ok, message)
        self.assertTrue(any(line.endswith("[hlf] Bootstrap complete.") for line in self._log()))

    def test_the_default_limit_leaves_room_in_the_lab_tests_job(self) -> None:
        self.assertEqual(hlf_service.BOOTSTRAP_TIMEOUT_SECONDS, 15 * 60)
        if not LAB_TESTS_WORKFLOW.is_file():
            self.skipTest("no .github folder in this copy")
        text = LAB_TESTS_WORKFLOW.read_text(encoding="utf-8")
        job = re.search(r"\n  test:\n(.*?)(?=\n  \S|\Z)", text, re.S)
        self.assertIsNotNone(job, "lab-tests.yml has no test job")
        minutes = re.search(r"timeout-minutes:\s*(\d+)", job.group(1))
        self.assertIsNotNone(minutes, "the test job has no timeout-minutes")
        # The image builds and the stack start come before the bootstrap, and the message must land inside the job.
        self.assertLessEqual(hlf_service.BOOTSTRAP_TIMEOUT_SECONDS / 60, int(minutes.group(1)) - 10)

    def test_start_network_ends_in_error_with_the_message_when_the_bootstrap_stalls(self) -> None:
        svc = self.service
        with patch.object(svc, "get_network_status", return_value={"status": hlf_service.LabStatus.STOPPED}), \
                patch.object(svc, "_test_network_exists", return_value=False), \
                patch.object(svc, "_bootstrap_command", return_value=SLOW_BOOTSTRAP), \
                patch.object(hlf_service, "BOOTSTRAP_TIMEOUT_SECONDS", 1):
            ok, _ = svc.start_network()
            self.assertTrue(ok)
            deadline = time.monotonic() + 30
            while svc.background_task is not None and time.monotonic() < deadline:
                time.sleep(0.1)
        self.assertIsNone(svc.background_task, "the start task did not end")
        self.assertEqual(svc.status, hlf_service.LabStatus.ERROR)
        detail = svc.lifecycle_progress["detail"]
        self.assertIn("Fabric setup (lab.sh bootstrap) was stopped after 1 second", detail)
        self.assertIn(detail, self.lifecycle_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
