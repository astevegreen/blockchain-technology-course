"""The src.zip the Pages workflow builds, rebuilt here with Python's zipfile. Run: python -m unittest discover -s tools/tests

check.py's answer-files check reads dynamic-labs/student-exclude.txt and matches it with fnmatch; pages.yml's zip step
gets the same list as `-x` arguments from tools/student_exclude.py. This test takes those `-x` arguments exactly as
the workflow does, applies them the way Info-ZIP does (a pattern is a wildcard over the whole stored path, `*` crosses
`/`, its own regex translation, not check.matches_any), and builds the archive over the real tracked tree with
`zipfile`, so it needs no `zip` binary and never skips. A pattern the zip step reads differently from the check then
fails here instead of shipping an answer file.

The zipfile build is a model of zip. SourceZipMatchesTheRealZip also runs Info-ZIP's own `zip -r -sf` (which lists
what it would pack and writes nothing) whenever `zip` is on the host, as on the Ubuntu runner, and checks that its list
equals both the check's expectation and the model's. With no `zip` it skips, unless SRC_ZIP_TEST_REQUIRED=1
(pages.yml sets it and runs this test just before it builds the zip), when it fails.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
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


def zip_pattern(pattern: str) -> re.Pattern[str]:
    """An Info-ZIP `-x` pattern as a regex over the whole stored path: `*` (and `**`) crosses `/`, `?` is one
    character, `[...]` a class."""
    out, i = "", 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            while pattern[i:i + 1] == "*":
                i += 1
            out += ".*"
            continue
        if c == "?":
            out += "."
        elif c == "[" and "]" in pattern[i + 2:]:
            j = pattern.index("]", i + 2)
            body = pattern[i + 1:j]
            out += "[" + ("^" + body[1:] if body[:1] == "!" else body) + "]"
            i = j
        else:
            out += re.escape(c)
        i += 1
    return re.compile(out + r"\Z", re.DOTALL)


def would_pack(paths: list[str], args: list[str], out_dir: Path, cwd: Path = check.REPO) -> set[str]:
    """The files in an archive of `paths` (relative to `cwd`) built with the `-x` arguments in `args`."""
    if args[0::2] != ["-x"] * (len(args) // 2):
        raise AssertionError("zip-args must be `-x` and a pattern, repeated")
    excluded = [zip_pattern(p) for p in args[1::2]]
    archive = out_dir / "src.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_STORED) as zf:
        for rel in paths:
            if not any(r.fullmatch(rel) for r in excluded):
                zf.write(cwd / rel, rel)
    with zipfile.ZipFile(archive) as zf:
        return set(zf.namelist())


def tracked_files() -> list[str]:
    return [rel for rel in (check.git(check.REPO, "ls-files") or "").splitlines()
            if rel.startswith(("blockchain-course/", "dynamic-labs/")) and (check.REPO / rel).is_file()]


def zip_lists(paths: list[str], args: list[str], out_dir: Path, cwd: Path = check.REPO) -> set[str]:
    """The files Info-ZIP would put in the archive, run from `cwd` with -sf (show files, write nothing)."""
    cmd = ["zip", "-r", "-sf", (out_dir / "src.zip").as_posix(), *paths, *args]
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    if result.returncode:
        raise AssertionError(f"zip -sf failed ({result.returncode}): {result.stderr.strip()[:500]}")
    return {line.strip() for line in result.stdout.splitlines()
            if line.startswith("  ") and not line.strip().endswith("/")}


class SourceZipMatchesTheCheck(unittest.TestCase):
    def test_zip_packs_exactly_the_tracked_files_the_check_thinks_it_does(self) -> None:
        workflow = (check.REPO / check.PAGES_WORKFLOW).read_text(encoding="utf-8")
        self.assertIn(ZIP_CALL, workflow, "the zip step's command changed shape: update this test")
        patterns = check.read_student_exclusions()
        tracked = tracked_files()
        with tempfile.TemporaryDirectory() as tmp:
            packed = would_pack(tracked, zip_args(), Path(tmp))
        drift = [f"{rel}: zip {'packs' if rel in packed else 'leaves out'} it, the check thinks it "
                 f"{'leaves it out' if check.matches_any(rel, patterns, whole_folders=False) else 'packs it'}"
                 for rel in tracked
                 if (rel in packed) == check.matches_any(rel, patterns, whole_folders=False)]
        self.assertEqual(drift[:20], [], f"{len(drift)} tracked files where zip and the check disagree")


class SourceZipMatchesTheRealZip(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not shutil.which("zip"):
            if os.environ.get("SRC_ZIP_TEST_REQUIRED") == "1":
                raise RuntimeError("Info-ZIP zip is needed to list what src.zip would pack")
            raise unittest.SkipTest("Info-ZIP zip is not on this host")

    def test_zip_lists_what_the_check_expects_and_what_the_model_packs(self) -> None:
        patterns = check.read_student_exclusions()
        tracked = tracked_files()
        with tempfile.TemporaryDirectory() as tmp:
            listed = zip_lists(["blockchain-course", "dynamic-labs"], zip_args(), Path(tmp))
            modelled = would_pack(tracked, zip_args(), Path(tmp))
        drift = [f"{rel}: zip {'packs' if rel in listed else 'leaves out'} it, the check thinks it "
                 f"{'leaves it out' if check.matches_any(rel, patterns, whole_folders=False) else 'packs it'}"
                 for rel in tracked
                 if (rel in listed) == check.matches_any(rel, patterns, whole_folders=False)]
        self.assertEqual(drift[:20], [], f"{len(drift)} tracked files where zip and the check disagree")
        model_drift = [rel for rel in tracked if (rel in listed) != (rel in modelled)]
        self.assertEqual(model_drift[:20], [], f"{len(model_drift)} tracked files where zip and the model disagree")


class ZipArgs(unittest.TestCase):
    def test_every_listed_pattern_becomes_one_x_argument(self) -> None:
        args = zip_args()
        self.assertEqual(args[0::2], ["-x"] * (len(args) // 2))
        self.assertEqual(args[1::2], check.read_student_exclusions())


if __name__ == "__main__":
    unittest.main()
