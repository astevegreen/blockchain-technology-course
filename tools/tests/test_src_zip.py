"""The src.zip the Pages workflow builds, listed by zip itself. Run: python -m unittest discover -s tools/tests

check.py's answer-files check reads dynamic-labs/student-exclude.txt and matches it with fnmatch; pages.yml's zip step
gets the same list as `-x` arguments from tools/student_exclude.py. This test runs that zip in dry-run mode (`zip -sf`, which lists what it would pack and writes nothing) over
the real tree, so a pattern zip reads differently from fnmatch fails here instead of shipping an answer file.
It needs Info-ZIP `zip`, as the Ubuntu runner has; on a host without it it skips, unless
SRC_ZIP_TEST_REQUIRED=1 (pages.yml sets it, and runs this test just before it builds the zip).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402

ARCHIVE = "blockchain-course/assets/src.zip"


ZIP_CALL = 'zip -r blockchain-course/assets/src.zip blockchain-course dynamic-labs "${EXCLUDES[@]}"'


def zip_args() -> list[str]:
    """The `-x` arguments pages.yml passes, from the same script it runs."""
    out = subprocess.run([sys.executable, str(check.REPO / "tools" / "student_exclude.py"), "zip-args"],
                         capture_output=True, text=True, check=True).stdout
    return out.splitlines()


def would_pack(paths: list[str], args: list[str], out_dir: Path, cwd: Path = check.REPO) -> set[str]:
    """The files zip would put in the archive, run from `cwd` with -sf (show files, write nothing)."""
    cmd = ["zip", "-r", "-sf", (out_dir / "src.zip").as_posix(), *paths, *args]
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    if result.returncode:
        raise AssertionError(f"zip -sf failed ({result.returncode}): {result.stderr.strip()[:500]}")
    return {line.strip() for line in result.stdout.splitlines()
            if line.startswith("  ") and not line.strip().endswith("/")}


class SourceZipMatchesTheCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not shutil.which("zip"):
            if os.environ.get("SRC_ZIP_TEST_REQUIRED") == "1":
                raise RuntimeError("Info-ZIP zip is needed to list what src.zip would pack")
            raise unittest.SkipTest("Info-ZIP zip is not on this host")

    def test_zip_packs_exactly_the_tracked_files_the_check_thinks_it_does(self) -> None:
        workflow = (check.REPO / check.PAGES_WORKFLOW).read_text(encoding="utf-8")
        self.assertIn(ZIP_CALL, workflow, "the zip step's command changed shape: update this test")
        patterns = check.read_student_exclusions()
        tracked = [rel for rel in (check.git(check.REPO, "ls-files") or "").splitlines()
                   if rel.startswith(("blockchain-course/", "dynamic-labs/")) and (check.REPO / rel).is_file()]
        with tempfile.TemporaryDirectory() as tmp:
            packed = would_pack(["blockchain-course", "dynamic-labs"], zip_args(), Path(tmp))
        drift = [f"{rel}: zip {'packs' if rel in packed else 'leaves out'} it, the check thinks it "
                 f"{'leaves it out' if check.matches_any(rel, patterns, whole_folders=False) else 'packs it'}"
                 for rel in tracked
                 if (rel in packed) == check.matches_any(rel, patterns, whole_folders=False)]
        self.assertEqual(drift[:20], [], f"{len(drift)} tracked files where zip and the check disagree")


class ZipArgs(unittest.TestCase):
    def test_every_listed_pattern_becomes_one_x_argument(self) -> None:
        args = zip_args()
        self.assertEqual(args[0::2], ["-x"] * (len(args) // 2))
        self.assertEqual(args[1::2], check.read_student_exclusions())


if __name__ == "__main__":
    unittest.main()
