"""The double-click wrappers in --dry-run mode, against a fake `docker` first on a PATH that holds no real one.

Dry run opens no browser and starts no Docker Desktop; it prints "would: ..." instead, so the tests read what each
wrapper would have done and which docker commands it sent.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]  # student-launcher/
IMAGE = "ghcr.io/astevegreen/course-labs:launcher-stable"

FAKE_SH = """#!/bin/sh
echo "$*" >> "$FAKE_LOG"
case "$1" in
  info) [ "$FAKE_DOCKER" = down ] && exit 1 ;;
  pull) [ "$FAKE_PULL" = fail ] && exit 1 ;;
  image) [ "$FAKE_LOCAL" = yes ] || exit 1 ;;
esac
exit 0
"""

FAKE_CMD = """@echo off
echo %*>> "%FAKE_LOG%"
if "%1"=="info" if "%FAKE_DOCKER%"=="down" exit /b 1
if "%1"=="pull" if "%FAKE_PULL%"=="fail" exit /b 1
if "%1"=="image" if not "%FAKE_LOCAL%"=="yes" exit /b 1
exit /b 0
"""


def git_bash() -> str | None:
    if os.name == "nt":
        for root in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramW6432", "")):
            candidate = Path(root) / "Git" / "bin" / "bash.exe"
            if root and candidate.is_file():
                return str(candidate)
        return None  # System32's bash.exe is WSL: never use it here
    return shutil.which("bash")


class Wrapper(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        self.log = Path(self.tmp.name) / "docker.log"

    def tearDown(self):
        self.tmp.cleanup()

    def calls(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.is_file() else []


@unittest.skipUnless(git_bash(), "needs bash (Git Bash on Windows)")
class Posix(Wrapper):
    def run_script(self, name, with_docker=True, **env):
        bash = git_bash()
        if with_docker:
            fake = self.bin / "docker"
            fake.write_text(FAKE_SH, encoding="utf-8", newline="\n")
            fake.chmod(0o755)
        tools = Path(bash).parent.parent / "usr" / "bin" if os.name == "nt" else Path("/usr/bin")
        path = os.pathsep.join([str(self.bin), str(tools), "/bin"])
        full = {"PATH": path, "FAKE_LOG": str(self.log), "HOME": self.tmp.name, **env}
        if os.name == "nt":
            full["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
        done = subprocess.run([bash, str(HERE / name), "--dry-run"], env=full, capture_output=True, text=True,
                              timeout=120, check=False)
        return done.returncode, done.stdout

    def test_command_and_sh_are_the_same(self):
        for stem in ("Start-Course-Labs", "Stop-Course-Labs"):
            self.assertEqual((HERE / f"{stem}.command").read_bytes(), (HERE / f"{stem}.sh").read_bytes())

    def test_start_runs_the_control_container(self):
        code, out = self.run_script("Start-Course-Labs.sh")
        self.assertEqual(code, 0, out)
        calls = self.calls()
        self.assertIn(f"pull {IMAGE}", calls)
        self.assertIn("rm -f course-launcher", calls)
        run = next(c for c in calls if c.startswith("run "))
        for part in ("-v /var/run/docker.sock:/var/run/docker.sock", "-v course-launcher-state:/state",
                     "-p 127.0.0.1:8470:8470", f"-e LAUNCHER_IMAGE={IMAGE}", "--name course-launcher"):
            self.assertIn(part, run)
        self.assertTrue(any(c.startswith("exec course-launcher wget") and "/api/health" in c for c in calls))
        self.assertIn("would: ", out)
        self.assertIn("http://127.0.0.1:8470/", out)

    def test_no_docker_opens_the_guide(self):
        code, out = self.run_script("Start-Course-Labs.sh", with_docker=False)
        self.assertEqual(code, 1)
        self.assertIn("run-labs.html#install-docker", out)
        self.assertIn("isn't installed", out)

    def test_docker_down_tries_to_start_it(self):
        code, out = self.run_script("Start-Course-Labs.sh", FAKE_DOCKER="down")
        self.assertEqual(code, 1)
        self.assertIn("Starting Docker Desktop", out)
        self.assertIn("Docker didn't start", out)
        self.assertFalse([c for c in self.calls() if c.startswith("run ")])

    def test_offline_uses_the_image_already_here(self):
        code, _ = self.run_script("Start-Course-Labs.sh", FAKE_PULL="fail", FAKE_LOCAL="yes")
        self.assertEqual(code, 0)
        code, out = self.run_script("Start-Course-Labs.sh", FAKE_PULL="fail")
        self.assertEqual(code, 1)
        self.assertIn("internet connection", out)

    def test_stop(self):
        code, out = self.run_script("Stop-Course-Labs.sh")
        self.assertEqual(code, 0, out)
        calls = self.calls()
        self.assertTrue(any("/api/shutdown" in c for c in calls))
        self.assertEqual(calls[-1], "rm -f course-launcher")


@unittest.skipUnless(os.name == "nt", "cmd.exe is Windows only")
class Windows(Wrapper):
    def run_script(self, name, with_docker=True, **env):
        if with_docker:
            (self.bin / "docker.cmd").write_text(FAKE_CMD.replace("\n", "\r\n"), encoding="ascii", newline="")
        system32 = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32"
        full = {"PATH": os.pathsep.join([str(self.bin), str(system32)]), "PATHEXT": ".COM;.EXE;.BAT;.CMD",
                "FAKE_LOG": str(self.log), "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
                "ProgramFiles": self.tmp.name, "LOCALAPPDATA": self.tmp.name, **env}
        done = subprocess.run(["cmd", "/d", "/c", str(HERE / name), "--dry-run"], env=full, capture_output=True,
                              text=True, timeout=120, check=False, stdin=subprocess.DEVNULL)
        return done.returncode, done.stdout

    def test_start_runs_the_control_container(self):
        code, out = self.run_script("Start-Course-Labs.cmd")
        self.assertEqual(code, 0, out)
        calls = self.calls()
        self.assertIn(f"pull \"{IMAGE}\"", calls)
        run = next(c for c in calls if c.startswith("run "))
        for part in ("-v /var/run/docker.sock:/var/run/docker.sock", "-v course-launcher-state:/state",
                     "-p 127.0.0.1:8470:8470", "--name course-launcher"):
            self.assertIn(part, run)
        self.assertTrue(any("/api/health" in c for c in calls))
        self.assertIn("would: open", out)

    def test_no_docker_opens_the_guide(self):
        code, out = self.run_script("Start-Course-Labs.cmd", with_docker=False)
        self.assertEqual(code, 1)
        self.assertIn("run-labs.html#install-docker", out)

    def test_docker_down_tries_to_start_it(self):
        code, out = self.run_script("Start-Course-Labs.cmd", FAKE_DOCKER="down")
        self.assertEqual(code, 1, out)
        self.assertIn("would: start", out)
        self.assertIn("Docker Desktop.exe", out)
        self.assertIn("Docker didn't start", out)

    def test_offline_uses_the_image_already_here(self):
        self.assertEqual(self.run_script("Start-Course-Labs.cmd", FAKE_PULL="fail", FAKE_LOCAL="yes")[0], 0)
        code, out = self.run_script("Start-Course-Labs.cmd", FAKE_PULL="fail")
        self.assertEqual(code, 1)
        self.assertIn("internet connection", out)

    def test_stop(self):
        code, out = self.run_script("Stop-Course-Labs.cmd")
        self.assertEqual(code, 0, out)
        calls = self.calls()
        self.assertTrue(any("/api/shutdown" in c for c in calls))
        self.assertEqual(calls[-1], "rm -f course-launcher")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
