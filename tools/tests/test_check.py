"""Tests for tools/check.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   cwd=root, check=True, capture_output=True)


class ChangedFiles(unittest.TestCase):
    def test_reports_unpushed_staged_unstaged_and_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init", "-q", "-b", "main")
            for name in ("kept.txt", "edited.txt"):
                (root / name).write_text("v1\n")
            git(root, "add", ".")
            git(root, "commit", "-q", "-m", "base")
            git(root, "checkout", "-q", "-b", "work")
            (root / "committed.txt").write_text("new\n")
            git(root, "add", "committed.txt")
            git(root, "commit", "-q", "-m", "unpushed")
            (root / "staged.txt").write_text("s\n")
            git(root, "add", "staged.txt")
            (root / "edited.txt").write_text("v2\n")
            (root / "untracked.txt").write_text("u\n")

            self.assertEqual(check.changed_files(root),
                             ["committed.txt", "edited.txt", "staged.txt", "untracked.txt"])
            self.assertEqual(check.added_files(root), ["committed.txt", "staged.txt", "untracked.txt"])

    def test_clean_tree_has_no_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init", "-q", "-b", "main")
            (root / "a.txt").write_text("a\n")
            git(root, "add", ".")
            git(root, "commit", "-q", "-m", "base")
            self.assertEqual(check.changed_files(root), [])

    def test_line_ending_warnings_are_not_file_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "core.autocrlf", "true")
            (root / "edited.txt").write_bytes(b"v1\n")
            git(root, "add", ".")
            git(root, "commit", "-q", "-m", "base")
            (root / "edited.txt").write_bytes(b"v2\n")  # LF in a CRLF checkout: git warns on stderr
            self.assertEqual(check.changed_files(root), ["edited.txt"])

    def test_outside_a_repo_means_everything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(check.changed_files(Path(tmp)))


class Stamps(unittest.TestCase):
    def test_tree_key_follows_untracked_edits_and_leaves_the_index_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init", "-q", "-b", "main")
            (root / "a.txt").write_text("a\n")
            git(root, "add", ".")
            git(root, "commit", "-q", "-m", "base")
            (root / "new.txt").write_text("v1\n")
            first = check.tree_key(root)
            self.assertEqual(check.tree_key(root), first)
            (root / "new.txt").write_text("v2\n")
            self.assertNotEqual(check.tree_key(root), first)
            status = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True).stdout
            self.assertEqual(status, "?? new.txt\n")

    def test_git_hook_variables_are_not_passed_on(self) -> None:
        env = {**check.os.environ, "GIT_INDEX_FILE": "elsewhere/index", "GIT_DIR": "elsewhere"}
        probe = "import check; print(sorted(check.GIT_HOOK_VARS & check.ENV.keys()))"
        out = subprocess.run([sys.executable, "-c", probe], cwd=Path(check.__file__).parent, env=env,
                             capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.strip(), "[]")


class Report(unittest.TestCase):
    def test_success_is_one_line(self) -> None:
        text, code = check.report([("a", []), ("b", [])], [], 1.234)
        self.assertEqual((text, code), ("check: passed (2 checks, 1.2s)", 0))

    def test_notes_do_not_fail(self) -> None:
        text, code = check.report([("a", ["note: unrendered"])], ["labs unverified"], 0.5)
        self.assertEqual(code, 0)
        self.assertEqual(text.splitlines()[-1], "check: passed (1 checks, 0.5s)")
        self.assertIn("note: labs unverified", text)

    def test_failures_are_grouped_and_capped_at_40_lines(self) -> None:
        many = [f"file.py:{i}: broken" for i in range(100)]
        text, code = check.report([("ok", []), ("python syntax", many)], [], 2.0)
        lines = text.splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "[python syntax]")
        self.assertEqual(lines[-1], "check: FAILED")
        self.assertEqual(len(lines), check.MAX_LINES + 1)
        self.assertTrue(lines[-2].startswith("... ("))


class Planning(unittest.TestCase):
    def names(self, files: list[str]) -> tuple[list[str], list[str]]:
        plan = check.plan_checks(files, added=[])
        return [c.name for c in plan.checks], plan.info

    def test_lesson_change(self) -> None:
        lesson = "blockchain-course/lessons/introduction/02-IN-blockchain_at_a_glance.qmd"
        names, _ = self.names([lesson])
        self.assertEqual(names, ["lesson lint", "render 02-IN-blockchain_at_a_glance.qmd",
                                 "glossary slide index", "mind-map links"])

    def test_quiz_bank_change(self) -> None:
        bank = "quizes/quiz_json/bitcoin_01-BF-bitcoin_origins_and_mechanics-quiz-bank.json"
        names, _ = self.names([bank])
        self.assertEqual(names, ["quiz banks", "quiz bundle"])

    def test_site_wide_and_lab_changes_inform(self) -> None:
        _, info = self.names(["blockchain-course/_quarto.yml", "dynamic-labs/README.md"])
        self.assertTrue(any("--all --render" in line for line in info))
        self.assertTrue(any("Docker is unavailable" in line for line in info))

    def test_unrelated_change_runs_nothing(self) -> None:
        self.assertEqual(self.names(["README.md"]), ([], []))


class Helpers(unittest.TestCase):
    def test_quarto_warning_blocks(self) -> None:
        out = "Rendering\nWARNING (x.qmd:3): problem with a fenced div\n  near line 3\n\nOutput created\n"
        self.assertEqual(check.quarto_warnings(out, "lesson.qmd"),
                         ["lesson.qmd: WARNING (x.qmd:3): problem with a fenced div near line 3"])

    def test_file_names(self) -> None:
        self.assertEqual(check.file_names(["ok/a-b_c.1.md", "pkg/@scope/x.json"]), [])
        self.assertEqual(len(check.file_names(["bad dir/x.md", "a|b.md"])), 2)

    def test_python_syntax(self) -> None:
        with tempfile.TemporaryDirectory(dir=check.REPO) as tmp:
            bad = Path(tmp) / "broken_probe.py"
            bad.write_text("def f(:\n    pass\n")
            rel = bad.relative_to(check.REPO).as_posix()
            self.assertEqual(check.compile_python([rel]), [f"{rel}:1: invalid syntax"])


if __name__ == "__main__":
    unittest.main()
