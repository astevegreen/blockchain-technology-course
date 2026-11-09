"""The vendored instructor_auth copies match dynamic-labs/shared/instructor_auth/.

Each lab's Docker build context carries its own copy (scripts/sync-shared.sh writes
them and marks each with a VENDORED file). A fix made only in shared/ would never
reach the labs, so this fails when any copy differs from shared/, file by file.

To change the login code: edit shared/instructor_auth/, then run
dynamic-labs/scripts/sync-shared.sh from the repo root.
"""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared" / "instructor_auth"
COPIES = (
    "quiz-engine-v2/instructor_auth",
    "exercises/l03-i3-trust-game/instructor_auth",
    "hlf/shared_instructor_auth",
)
# Files a copy may differ in on purpose, by name, each with why. VENDORED marks a
# copy (sync-shared.sh writes it) and is absent from shared/.
ONLY_IN_COPIES = {"VENDORED"}
SKIP_DIRS = {"__pycache__"}


def _files(folder: Path) -> dict[str, bytes]:
    """Every file under `folder` by relative path, with line endings normalised (a Windows checkout may hold CRLF)."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes().replace(b"\r\n", b"\n")
        for path in sorted(folder.rglob("*"))
        if path.is_file() and not SKIP_DIRS.intersection(path.relative_to(folder).parts)
    }


class VendoredInstructorAuthTests(unittest.TestCase):
    def test_every_copy_matches_shared(self) -> None:
        shared = _files(SHARED)
        self.assertIn("audit.py", shared)
        for copy in COPIES:
            with self.subTest(copy=copy):
                vendored = {name: data for name, data in _files(ROOT / copy).items() if name not in ONLY_IN_COPIES}
                self.assertEqual(sorted(vendored), sorted(shared), f"{copy}: files differ from shared/")
                stale = [name for name in shared if vendored[name] != shared[name]]
                self.assertEqual(stale, [], f"{copy} differs from shared/instructor_auth: run "
                                            "dynamic-labs/scripts/sync-shared.sh")

    def test_every_marked_copy_is_listed(self) -> None:
        # A new copy (a VENDORED file naming shared/instructor_auth) must be checked here too.
        marked = {
            path.parent.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("VENDORED")
            if "node_modules" not in path.parts
            and "shared/instructor_auth" in path.read_text(encoding="utf-8")
        }
        self.assertEqual(marked, set(COPIES))


if __name__ == "__main__":
    unittest.main()
