"""The src.zip the Pages workflow builds, listed by zip itself. Run: python -m unittest discover -s tools/tests

check.py's answer-files check reads the `-x` patterns of pages.yml's zip step and matches them with fnmatch. This test
runs that step's own zip command in dry-run mode (`zip -sf`, which lists what it would pack and writes nothing) over
the real tree, so a pattern zip reads differently from fnmatch fails here instead of shipping an answer file.
It needs Info-ZIP `zip` and `bash`, as the Ubuntu runner has; on a host without them it skips, unless
SRC_ZIP_TEST_REQUIRED=1 (pages.yml sets it, and runs this test just before it builds the zip).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402

ARCHIVE = "blockchain-course/assets/src.zip"


def zip_command(workflow: str) -> str:
    """The `zip -r ...` command of the "Create source zip" step, backslash continuations joined."""
    step = re.search(r"- name: Create source zip\n(.*?)(?=\n\s*- name:|\Z)", workflow, re.S)
    lines, taking = [], False
    for line in (step.group(1) if step else "").splitlines():
        taking = taking or line.strip().startswith("zip ")
        if taking:
            lines.append(line.strip().rstrip("\\").strip())
            if not line.rstrip().endswith("\\"):
                break
    return " ".join(lines)


def would_pack(command: str, out_dir: Path) -> set[str]:
    """The files zip would put in the archive, run from the repo root with -sf (show files, write nothing)."""
    dry = command.replace(f"zip -r {ARCHIVE}", f"zip -r -sf {(out_dir / 'src.zip').as_posix()}", 1)
    result = subprocess.run(["bash", "-c", dry], cwd=check.REPO, capture_output=True, text=True, timeout=600)
    if result.returncode:
        raise AssertionError(f"zip -sf failed ({result.returncode}): {result.stderr.strip()[:500]}")
    return {line.strip() for line in result.stdout.splitlines()
            if line.startswith("  ") and not line.strip().endswith("/")}


class SourceZipMatchesTheCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (shutil.which("zip") and shutil.which("bash")):
            if os.environ.get("SRC_ZIP_TEST_REQUIRED") == "1":
                raise RuntimeError("Info-ZIP zip and bash are needed to list what src.zip would pack")
            raise unittest.SkipTest("Info-ZIP zip and bash are not on this host")

    def test_zip_packs_exactly_the_tracked_files_the_check_thinks_it_does(self) -> None:
        workflow = (check.REPO / check.PAGES_WORKFLOW).read_text(encoding="utf-8")
        command = zip_command(workflow)
        self.assertIn(f"zip -r {ARCHIVE}", command, "the zip step's command changed shape: update this test")
        patterns = check.zip_exclusions(workflow)
        tracked = [rel for rel in (check.git(check.REPO, "ls-files") or "").splitlines()
                   if rel.startswith(("blockchain-course/", "dynamic-labs/")) and (check.REPO / rel).is_file()]
        with tempfile.TemporaryDirectory() as tmp:
            packed = would_pack(command, Path(tmp))
        drift = [f"{rel}: zip {'packs' if rel in packed else 'leaves out'} it, the check thinks it "
                 f"{'leaves it out' if check.matches_any(rel, patterns, whole_folders=False) else 'packs it'}"
                 for rel in tracked
                 if (rel in packed) == check.matches_any(rel, patterns, whole_folders=False)]
        self.assertEqual(drift[:20], [], f"{len(drift)} tracked files where zip and the check disagree")


class ZipCommand(unittest.TestCase):
    def test_zip_command_is_read_from_the_create_source_zip_step(self) -> None:
        workflow = ('      - name: Create source zip\n        run: |\n          # note\n'
                    f'          zip -r {ARCHIVE} a b \\\n            -x "q/**" \\\n            -x "r/*"\n'
                    '      - name: Render\n        run: zip -r other.zip c\n')
        self.assertEqual(zip_command(workflow), f'zip -r {ARCHIVE} a b -x "q/**" -x "r/*"')


if __name__ == "__main__":
    unittest.main()
