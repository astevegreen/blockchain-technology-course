"""Tests for tools/check.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
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
        self.assertEqual(names, ["lesson lint", "as-of dates", "render 02-IN-blockchain_at_a_glance.qmd",
                                 "glossary slide index", "mind-map links", "lesson pointers",
                                 "pretest", "post-test", "challenge bank"])

    def test_a_changed_lesson_and_all_get_every_date_rule(self) -> None:
        lesson = "blockchain-course/lessons/introduction/02-IN-blockchain_at_a_glance.qmd"
        with unittest.mock.patch.object(check, "run", return_value=(1, f"{lesson}:9: \"as of\" phrase")) as run:
            self.assertEqual(check.asof_dates([lesson]), [f"{lesson}:9: \"as of\" phrase"])
        self.assertEqual(run.call_args.args[0][2:], ["--check", lesson])
        with unittest.mock.patch.object(check, "run", return_value=(0, "")) as run:
            self.assertEqual(check.asof_dates(None), [])
        self.assertEqual(run.call_args.args[0][2:], ["--check", "--all"])
        self.assertIn("as-of dates", [c.name for c in check.plan_checks(None, added=[]).checks])

    def test_a_filter_change_is_site_wide_and_runs_the_filter_tests(self) -> None:
        names, info = self.names(["blockchain-course/filters/asof.lua"])
        self.assertIn("tool tests", names)
        self.assertTrue(any("--all --render" in line for line in info))

    def test_run_sheet_change_checks_lesson_pointers(self) -> None:
        names, _ = self.names(["quizes/run-sheet/RUN_SHEET.md"])
        self.assertIn("lesson pointers", names)

    def test_a_wrong_pointer_fails_and_topic_notes_do_not(self) -> None:
        out = "note: 03-FO.qmd:9: `xpub` not shown in 02-BF\nlessons/a/01-FO.qmd:12: day 6 (02-FO): run sheet says day 3\n"
        with unittest.mock.patch.object(check, "run", return_value=(1, out)):
            self.assertEqual(check.lesson_pointers(), ["lessons/a/01-FO.qmd:12: day 6 (02-FO): run sheet says day 3"])
        with unittest.mock.patch.object(check, "run", return_value=(0, "")):
            self.assertEqual(check.lesson_pointers(), [])

    def test_quiz_bank_change(self) -> None:
        bank = "quizes/quiz_json/bitcoin_01-BF-bitcoin_origins_and_mechanics-quiz-bank.json"
        names, _ = self.names([bank])
        self.assertEqual(names, ["lesson pointers", "quiz banks", "quiz bundle", "distractor alignment", "quiz engine tests"])

    def test_pretest_change_runs_the_verifiers_that_read_it(self) -> None:
        names, _ = self.names(["quizes/pretest/pretest_week2-quiz-bank.json"])
        self.assertEqual(names, ["lesson pointers", "pretest", "post-test"])

    def test_files_that_name_slides_check_lesson_pointers(self) -> None:
        for path in ("docs/lab-cards/is-it-final-yet.md", "blockchain-course/assets/labs/merkle-trees/index.html",
                     "dynamic-labs/tokens/quizes/INSTRUCTOR_ANSWERS.md", "dynamic-labs/wallet/gateway/static/lab/index.html"):
            names, _ = self.names([path])
            self.assertIn("lesson pointers", names, path)

    def test_challenge_bank_change(self) -> None:
        names, _ = self.names(["quizes/challenge/challenge-bank.md"])
        self.assertEqual(names, ["challenge bank"])

    def test_every_quiz_verifier_is_run(self) -> None:
        scripts = {s.relative_to(check.REPO).as_posix() for s in (check.REPO / "quizes").glob("**/verify*.py")}
        self.assertEqual(scripts - {"quizes/verify_single_quiz.py"}, {s for _, s, _ in check.QUIZ_VERIFIERS})
        names = [c.name for c in check.plan_checks(None, added=[]).checks]
        for name, _, _ in check.QUIZ_VERIFIERS:
            self.assertIn(name, names)

    def test_a_failing_verifier_names_its_failures(self) -> None:
        out = "=== Single Quiz ===\n- Margin violations: 0\nFAIL: pretest_week2-quiz-bank.json: day 6: bad\nPretest: 1 failure(s).\n"
        with unittest.mock.patch.object(check, "run", return_value=(1, out)):
            lines = check.run_verifier("quizes/pretest/verify_pretest.py")
        self.assertEqual(lines, ["quizes/pretest/verify_pretest.py failed",
                                 "  FAIL: pretest_week2-quiz-bank.json: day 6: bad"])

    def test_site_wide_and_lab_changes_inform(self) -> None:
        _, info = self.names(["blockchain-course/_quarto.yml", "dynamic-labs/README.md"])
        self.assertTrue(any("--all --render" in line for line in info))
        self.assertTrue(any("regression-tests/automated/<lab>/run.sh" in line for line in info))

    def test_lesson_change_reports_its_slide_count(self) -> None:
        _, info = self.names(["blockchain-course/lessons/introduction/01-IN-course_welcome.qmd"])
        self.assertTrue(any(line.startswith("01-IN-course_welcome.qmd: ") and " slides " in line for line in info))

    def test_unrelated_change_runs_nothing(self) -> None:
        self.assertEqual(self.names(["README.md"]), ([], []))


class LabTests(unittest.TestCase):
    def names(self, files: list[str] | None) -> list[str]:
        return [c.name for c in check.plan_checks(files, added=[]).checks]

    def test_a_lab_change_runs_the_lab_unit_tests(self) -> None:
        for changed in ("dynamic-labs/lane-service/app.py", "dynamic-labs/lab-manager.sh",
                        "dynamic-labs/tests/test_capacity_defaults.py",
                        "dynamic-labs/regression-tests/unit/test_hlf_my_term.py", ".github/workflows/pages.yml"):
            self.assertIn("lab unit tests", self.names([changed]), changed)

    def test_a_quiz_engine_or_bank_change_runs_the_quiz_engine_tests(self) -> None:
        for changed in ("dynamic-labs/quiz-engine-v2/app/grading.py", "quizes/build_quiz_bank_bundle.py",
                        "quizes/quiz_json/bitcoin_01-BF-bitcoin_origins_and_mechanics-quiz-bank.json"):
            self.assertIn("quiz engine tests", self.names([changed]), changed)
        self.assertNotIn("quiz engine tests", self.names(["dynamic-labs/hlf/lab.sh"]))

    def test_shared_auth_or_dev_requirements_run_both_suites(self) -> None:
        # The quiz engine imports dynamic-labs/shared/instructor_auth; both suites install requirements-dev.txt.
        for changed in ("dynamic-labs/shared/instructor_auth/auth.py", "requirements-dev.txt"):
            self.assertIn("quiz engine tests", self.names([changed]), changed)
            self.assertIn("lab unit tests", self.names([changed]), changed)

    def test_everything_runs_both(self) -> None:
        names = self.names(None)
        self.assertIn("lab unit tests", names)
        self.assertIn("quiz engine tests", names)

    def test_each_contract_test_file_runs_in_its_own_process(self) -> None:
        # The files import different modules that share a name (instructor_auth, app), so one process can't hold them.
        calls = []
        with unittest.mock.patch.object(check, "run", side_effect=lambda cmd, **kw: calls.append(cmd) or (0, "OK")):
            self.assertEqual(check.lab_unit_tests(), [])
        files = sorted(p.name for p in (check.REPO / "dynamic-labs" / "tests").glob("test_*.py"))
        self.assertGreater(len(files), 10)
        run_files = [Path(c[-1]).name for c in calls if c[-1].endswith(".py")]
        self.assertEqual(run_files, files)
        self.assertTrue(any("discover" in c and "regression-tests/unit" in c for c in calls))

    def test_a_failing_lab_test_is_named_with_its_failure(self) -> None:
        out = "ERROR: test_x (test_capacity_defaults.T.test_x)\nTraceback...\nAssertionError: 3 != 4\nFAILED (failures=1)\n"
        with unittest.mock.patch.object(check, "run", return_value=(1, out)):
            lines = check.lab_unit_tests()
        self.assertIn("dynamic-labs/tests/test_capacity_defaults.py failed (python -m unittest)", lines)
        self.assertIn("  AssertionError: 3 != 4", lines)

    def test_a_missing_package_names_the_install(self) -> None:
        out = "ModuleNotFoundError: No module named 'flask'\n"
        with unittest.mock.patch.object(check, "run", return_value=(1, out)):
            lines = check.lab_unit_tests()
        self.assertIn("fix: python -m pip install -r requirements-dev.txt", lines)

    def test_quiz_engine_tests_run_against_a_freshly_built_bundle(self) -> None:
        seen = {}

        def fake_run(cmd, cwd=check.REPO, timeout=1800, env=None):
            if "build_quiz_bank_bundle.py" in " ".join(cmd):
                out = Path(cmd[cmd.index("--output") + 1])
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text("{}", encoding="utf-8")
                return 0, ""
            sample = Path(env["QUIZ_ENGINE_SAMPLE_QUIZ_DIR"])
            seen["bundle"] = (sample / "dist" / "blockchain-course-quiz-bank-bundle.json").is_file()
            seen["banks"] = any((sample / "quiz_json").glob("*-quiz-bank.json"))
            seen["cmd"], seen["cwd"] = cmd, cwd
            return 1, "FAILED tests/unit/test_grading.py::test_x - AssertionError\n1 failed, 3 passed"

        with unittest.mock.patch.object(check, "run", side_effect=fake_run):
            lines = check.quiz_engine_tests()
        self.assertTrue(seen["bundle"] and seen["banks"])
        self.assertEqual(seen["cmd"][1:3], ["-m", "pytest"])
        self.assertEqual(seen["cwd"], check.REPO / "dynamic-labs" / "quiz-engine-v2")
        self.assertIn("  FAILED tests/unit/test_grading.py::test_x - AssertionError", lines)


PAGES_FENCED = '''# student-exclude.txt
quizes/**
dynamic-labs/bitcoin-forensics/*_answer_LIVE.json
dynamic-labs/bitcoin-forensics/malicious_seed_v*.py
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
        pages = PAGES_FENCED.replace("dynamic-labs/bitcoin-forensics/*_answer_LIVE.json\n", "")
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

    def test_a_lab_quizes_folder_must_leave_the_vm(self) -> None:
        pages = PAGES_FENCED + "dynamic-labs/**/quizes/**\n"
        files = ["dynamic-labs/exercises/l03/quizes/keys.json"]
        self.assertEqual(len(check.unfenced_answer_files(files, pages, VM_FENCED)), 1)
        find = "          find dynamic-labs -type d -name quizes -prune -exec rm -rf {} + || true\n"
        vm = VM_FENCED.replace("      - name: Free Disk Space", find + "      - name: Free Disk Space")
        self.assertEqual(check.unfenced_answer_files(files, pages, vm), [])

    def test_every_listed_lab_file_must_leave_the_vm(self) -> None:
        # No lab file is exempt: the Bitcoin catalog, once a runtime exception, now fails like any other.
        pages = PAGES_FENCED + "dynamic-labs/lane-service/labs/bitcoin_catalog.yaml\ndynamic-labs/p2p_trust/notes.md\n"
        files = ["dynamic-labs/lane-service/labs/bitcoin_catalog.yaml", "dynamic-labs/p2p_trust/notes.md"]
        problems = check.unfenced_answer_files(files, pages, VM_FENCED)
        self.assertEqual(len(problems), 2)
        self.assertIn("bitcoin_catalog.yaml: baked into the VM", problems[0])
        self.assertIn("p2p_trust/notes.md: baked into the VM", problems[1])

    def test_other_files_and_instructor_trees_are_ignored(self) -> None:
        files = ["quizes/answer_sheet.json", "dynamic-labs/bitcoin-forensics/lab.md", "tools/answer_probe.py"]
        self.assertEqual(check.unfenced_answer_files(files, "", ""), [])

    def test_solution_seed_and_instructor_files_must_be_fenced_too(self) -> None:
        files = ["dynamic-labs/lab/solution_walkthrough.md", "dynamic-labs/lab/class_seed.py",
                 "dynamic-labs/lab/INSTRUCTOR_NOTES.md", "blockchain-course/assets/instructor-key.pdf"]
        problems = check.unfenced_answer_files(files, PAGES_FENCED, VM_FENCED)
        for rel in files:
            self.assertTrue(any(p.startswith(f"{rel}: ships in src.zip") for p in problems), rel)

    def test_instructor_code_is_the_running_lab_and_may_ship(self) -> None:
        files = ["dynamic-labs/hlf/web_service/instructor_routes.py", "dynamic-labs/hlf/web_ui/hlf_instructor.js",
                 "dynamic-labs/exercises/l03-i3-trust-game/templates/instructor.html",
                 "dynamic-labs/hlf/web_ui/instructor_login.html", "dynamic-labs/shared/instructor_auth/README.md"]
        self.assertEqual(check.unfenced_answer_files(files, PAGES_FENCED, VM_FENCED), [])

    def test_a_folder_named_for_instructors_seeds_or_answers_fences_what_is_inside(self) -> None:
        files = ["dynamic-labs/x/instructor/key.json", "dynamic-labs/x/seeds/class.json",
                 "dynamic-labs/x/answers/day1.md", "dynamic-labs/x/solutions/lab.py",
                 "dynamic-labs/x/instructor/grader.py", "dynamic-labs/x/instructor/panel.js",
                 "dynamic-labs/bitcoin-forensics/seeder/scenario_v37.py"]
        problems = check.unfenced_answer_files(files, PAGES_FENCED, VM_FENCED)
        for rel in files:
            self.assertTrue(any(p.startswith(f"{rel}: ships in src.zip") for p in problems), rel)

    def test_only_the_listed_instructor_pages_ship_not_any_page_so_named(self) -> None:
        files = ["dynamic-labs/p2p_trust/instructor_notes.html", "dynamic-labs/hlf/web_ui/instructor_guide.html",
                 "dynamic-labs/x/instructor/index.html"]
        problems = check.unfenced_answer_files(files, PAGES_FENCED, VM_FENCED)
        for rel in files:
            self.assertTrue(any(p.startswith(f"{rel}: ships in src.zip") for p in problems), rel)

    def test_answers_solutions_or_seeds_in_code_are_never_waved_through(self) -> None:
        files = ["dynamic-labs/hlf/web_service/instructor_answers.py", "dynamic-labs/lab/instructor_solution.js",
                 "dynamic-labs/lab/instructor_seed.py"]
        self.assertEqual(len(check.unfenced_answer_files(files, PAGES_FENCED, VM_FENCED)), 6)

    def test_every_student_facing_entry_has_a_reason_and_still_matches_a_file(self) -> None:
        tracked = (check.git(check.REPO, "ls-files") or "").splitlines()
        for pattern, reason in check.STUDENT_FACING.items():
            self.assertTrue(reason.strip(), pattern)
            self.assertTrue(any(check.matches_any(f.lower(), [pattern.lower()], False) for f in tracked), pattern)

    def test_this_repository_fences_every_answer_file(self) -> None:
        self.assertEqual(check.answer_files(), [])

    def test_an_untracked_answer_file_is_caught_before_it_is_added(self) -> None:
        # The check stamps untracked files too, so a commit after `git add` would never look at it again.
        real_git = check.git
        def git(root, *args):
            if args == ("ls-files", "--others", "--exclude-standard"):
                return "dynamic-labs/x/new_answer_key.json"
            return real_git(root, *args)
        with unittest.mock.patch.object(check, "git", git):
            problems = check.answer_files()
        self.assertTrue(any(p.startswith("dynamic-labs/x/new_answer_key.json: ships in src.zip") for p in problems),
                        problems)

    def test_workflow_or_answer_file_changes_run_the_check(self) -> None:
        for changed in (".github/workflows/pages.yml", "dynamic-labs/x/new_answer_key.json",
                        "dynamic-labs/x/Solution.md", "dynamic-labs/x/instructor_guide.md", "dynamic-labs/x/seed.sh",
                        "dynamic-labs/x/instructor/key.json"):
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

    def test_slides_mode_counts_a_commit_without_checking(self) -> None:
        rel = "blockchain-course/lessons/bitcoin/01-BF-bitcoin_origins_and_mechanics.qmd"
        want = check.slide_count(subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=check.REPO, check=True,
                                                capture_output=True, text=True, encoding="utf-8").stdout)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check.print_slides([rel], "HEAD"), 0)
            self.assertEqual(check.print_slides([str(check.REPO / rel)], None), 0)
            self.assertEqual(check.print_slides(["lessons/none.qmd"], "HEAD"), 1)
        self.assertEqual(out.getvalue().splitlines(), [f"Slides: {rel} {want}"] * 2
                         + ["Slides: lessons/none.qmd not found at HEAD"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            check.main(["--at", "HEAD"])


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
        self.assertIn("bib keys", [c.name for c in plan.checks])

    def test_a_repeated_key_is_named_whatever_its_case(self) -> None:
        bib = "@book{Nakamoto_2008,\n  title = {A}\n}\n\n@misc{other,\n  title = {B}\n}\n\n@book{nakamoto_2008,\n  title = {A}\n}\n"
        self.assertEqual(check.duplicate_bib_keys(bib), [(9, "nakamoto_2008", 1)])
        self.assertEqual(check.duplicate_bib_keys(self.BIB), [])


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


    def test_lab_page_scripts(self) -> None:
        with tempfile.TemporaryDirectory(dir=check.REPO) as tmp:
            page = Path(tmp) / "index.html"
            rel = page.relative_to(check.REPO).as_posix()
            page.write_text("<html>\n<script src=\"x.js\"></script>\n<script>\nvar a = 1;\n</script>\n</html>\n")
            self.assertEqual(check.lab_page_scripts([rel]), [])
            page.write_text("<html>\n<script>\nvar a = 1;\nvar b = f(1));\n</script>\n</html>\n")
            failures = check.lab_page_scripts([rel])
            self.assertEqual(len(failures), 1)
            self.assertTrue(failures[0].startswith(f"{rel}:4: SyntaxError"), failures[0])

    @unittest.skipUnless(check.find_browser(), "no Chrome or Edge")
    def test_lab_page_loads(self) -> None:
        with tempfile.TemporaryDirectory(dir=check.REPO) as tmp:
            page = Path(tmp) / "index.html"
            rel = page.relative_to(check.REPO).as_posix()
            (Path(tmp) / "here.js").write_text("window.here = 1;\n")
            page.write_text('<html>\n<script src="here.js"></script>\n<script>\nvar a = here;\n</script>\n</html>\n')
            self.assertEqual(check.lab_page_loads([rel]), [])
            # Both scripts parse, so the syntax check passes them; only loading the page finds what is wrong.
            page.write_text('<html>\n<script src="gone.js"></script>\n<script>\nvar a = 1;\nnotDefined();\n</script>\n</html>\n')
            self.assertEqual(check.lab_page_scripts([rel]), [])
            failures = check.lab_page_loads([rel])
            self.assertEqual(len(failures), 2, failures)
            self.assertTrue(failures[0].startswith(f"{rel}: index.html:5: Uncaught ReferenceError"), failures[0])
            self.assertTrue(failures[1].endswith("gone.js, which is not there"), failures[1])
            # A message with quotes in it, and a broken lab shown as a box rather than thrown; <noscript> is not shown.
            page.write_text('<html>\n<noscript><p class="lab-error">Needs JavaScript.</p></noscript>\n<script>\n'
                            'throw new Error(\'bad "q7" value\');\n</script>\n</html>\n')
            failures = check.lab_page_loads([rel])
            self.assertEqual(len(failures), 1, failures)
            self.assertIn('Uncaught Error: bad "q7" value', failures[0])
            page.write_text('<html>\n<body><script>\ndocument.body.insertAdjacentHTML("beforeend",'
                            ' \'<pre class="lab-error">This lab\\\'s config has problems</pre>\');\n</script></body>\n</html>\n')
            failures = check.lab_page_loads([rel])
            self.assertEqual(failures, [f"{rel}: the page shows a lab error: This lab's config has problems"])

    def test_pages_to_load(self) -> None:
        pages = ["blockchain-course/assets/labs/make-change/index.html",
                 "blockchain-course/assets/labs/two-of-three/index.html"]
        self.assertEqual(check.pages_to_load(["blockchain-course/assets/labs/make-change/data.js"], pages), pages[:1])
        self.assertEqual(check.pages_to_load(["blockchain-course/assets/labs/shared/look.css"], pages), pages)
        self.assertEqual(check.pages_to_load(["docs/follow-ups.md"], pages), [])

    def test_lab_page_pattern(self) -> None:
        self.assertTrue(check.LAB_PAGE.search("blockchain-course/assets/labs/is-it-final-yet/index.html"))
        self.assertFalse(check.LAB_PAGE.search("blockchain-course/assets/labs/shared/shell.js"))

if __name__ == "__main__":
    unittest.main()
