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

    def test_lesson_change_reports_its_slide_count(self) -> None:
        _, info = self.names(["blockchain-course/lessons/introduction/01-IN-course_welcome.qmd"])
        self.assertTrue(any(line.startswith("01-IN-course_welcome.qmd: ") and " slides " in line for line in info))

    def test_unrelated_change_runs_nothing(self) -> None:
        self.assertEqual(self.names(["README.md"]), ([], []))


PAGES_FENCED = '''
          zip -r blockchain-course/assets/src.zip blockchain-course dynamic-labs \\
            -x "quizes/**" \\
            -x "dynamic-labs/bitcoin-forensics/*_answer_LIVE.json" \\
            -x "dynamic-labs/bitcoin-forensics/malicious_seed_v*.py"
'''
VM_FENCED = '''
      - name: Remove Unused Repo Payload
        run: |
          du -sh dynamic-labs/bitcoin-forensics 2>/dev/null || true
          rm -rf \\
            dynamic-labs/bitcoin-forensics/instructor.zip \\
            dynamic-labs/bitcoin-forensics/*_answer_LIVE.json \\
            || true
      - name: Free Disk Space
        run: rm -rf dynamic-labs/bitcoin-forensics
'''
KEYS = ["dynamic-labs/bitcoin-forensics/v34_answer_LIVE.json", "dynamic-labs/bitcoin-forensics/v36_answer_LIVE.json"]


class AnswerFiles(unittest.TestCase):
    def test_fenced_keys_pass(self) -> None:
        self.assertEqual(check.unfenced_answer_files(KEYS, PAGES_FENCED, VM_FENCED), [])

    def test_key_missing_from_the_zip_fence_is_named(self) -> None:
        pages = PAGES_FENCED.replace('-x "dynamic-labs/bitcoin-forensics/*_answer_LIVE.json" \\\n', "")
        problems = check.unfenced_answer_files(KEYS, pages, VM_FENCED)
        self.assertEqual(len(problems), 2)
        self.assertIn("v34_answer_LIVE.json: ships in src.zip", problems[0])

    def test_key_missing_from_the_vm_cleanup_is_named(self) -> None:
        vm = VM_FENCED.replace("            dynamic-labs/bitcoin-forensics/*_answer_LIVE.json \\\n", "")
        problems = check.unfenced_answer_files(KEYS, PAGES_FENCED, vm)
        self.assertEqual(len(problems), 2)
        self.assertIn("baked into the VM", problems[0])

    def test_a_delete_outside_the_cleanup_step_does_not_count(self) -> None:
        # the Free Disk Space step above deletes the whole folder, but not in the payload cleanup
        vm = VM_FENCED.replace("            dynamic-labs/bitcoin-forensics/*_answer_LIVE.json \\\n", "")
        self.assertEqual(len(check.unfenced_answer_files(KEYS[:1], PAGES_FENCED, vm)), 1)

    def test_deleting_the_folder_covers_what_is_inside_it(self) -> None:
        vm = VM_FENCED.replace("dynamic-labs/bitcoin-forensics/*_answer_LIVE.json", "dynamic-labs/bitcoin-forensics")
        self.assertEqual(check.unfenced_answer_files(KEYS, PAGES_FENCED, vm), [])

    def test_other_files_and_instructor_trees_are_ignored(self) -> None:
        files = ["quizes/answer_sheet.json", "dynamic-labs/bitcoin-forensics/lab.md", "tools/answer_probe.py"]
        self.assertEqual(check.unfenced_answer_files(files, "", ""), [])

    def test_this_repository_fences_every_answer_file(self) -> None:
        self.assertEqual(check.answer_files(), [])

    def test_workflow_or_answer_file_changes_run_the_check(self) -> None:
        for changed in (".github/workflows/pages.yml", "dynamic-labs/x/new_answer_key.json"):
            plan = check.plan_checks([changed], added=[])
            self.assertIn("answer files", [c.name for c in plan.checks])


class AsNotes(unittest.TestCase):
    def test_failures_become_notes(self) -> None:
        lines = check.as_notes(["a.qmd: stale", "note: unrendered"])
        self.assertEqual(lines, ["note: a.qmd: stale", "note: unrendered"])
        self.assertEqual(check.report([("mind-map links", lines)], [], 1.0)[1], 0)


class SlideCount(unittest.TestCase):
    def test_hidden_slides_code_and_comments_do_not_count(self) -> None:
        text = ("---\ntitle: x\n---\n# Part\n## One\n::: {.notes}\n## not a slide\n:::\n"
                ":::: {.content-hidden}\n## Hidden\n::: {.notes}\n:::\n::::\n"
                "```python\n## comment\n```\n<!--\n## commented out\n-->\n## Two\n### Sub\n")
        self.assertEqual(check.slide_count(text), 3)

    def test_slide_level_3_counts_third_level_headings(self) -> None:
        self.assertEqual(check.slide_count("---\nformat:\n  aci-revealjs:\n    slide-level: 3\n---\n## A\n### B\n"), 2)


class BibDates(unittest.TestCase):
    BIB = ("@online{old_page,\n  url = {https://a.example/}\n}\n\n"
           "@online{dated_page,\n  url = {https://b.example/},\n  urldate = {2026-10-22}\n}\n\n"
           "@online{undated_page,\n  title = {X},\n  url = {https://c.example/}\n}\n\n"
           "@book{no_url,\n  title = {Y}\n}\n")

    def test_only_new_entries_with_a_url_need_a_urldate(self) -> None:
        self.assertEqual(check.undated_web_sources(self.BIB, {"old_page"}), [(10, "undated_page")])

    def test_a_bib_change_runs_the_check(self) -> None:
        plan = check.plan_checks(["blockchain-course/lessons/references/Blockchain.bib"], added=[])
        self.assertIn("bib dates", [c.name for c in plan.checks])


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
