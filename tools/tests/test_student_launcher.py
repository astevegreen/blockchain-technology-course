"""Runs the student launcher's own tests (student-launcher/control/tests) with the tool tests, so the check and CI
run them: the control container's API against a fake Docker, the secrets coverage, and the wrappers' dry runs."""
from __future__ import annotations

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parents[2] / "student-launcher" / "control" / "tests"


def load_tests(loader, tests, pattern):
    for folder in (TESTS, TESTS.parent):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))
    tests.addTests(loader.discover(str(TESTS), pattern="test_*.py", top_level_dir=str(TESTS)))
    return tests
