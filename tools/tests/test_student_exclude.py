"""dynamic-labs/student-exclude.txt reaches every student build context, and no excluded file lands in one.

The zip side is test_src_zip.py; this file covers the student images (tools/student_exclude.py stage, called by
student-release.yml for every build context in the images file) and the VM (remove --vm, called by vm-build.yml).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import check  # noqa: E402
import student_exclude  # noqa: E402

IMAGES = REPO / "dynamic-labs" / "student-release-images.json"
STUB = REPO / "tools" / "tests" / "fixtures" / "student-release-images.stub.json"
RELEASE = REPO / ".github" / "workflows" / "student-release.yml"


def build_contexts() -> list[str]:
    data = json.loads((IMAGES if IMAGES.is_file() else STUB).read_text(encoding="utf-8"))
    contexts = {row["context"] for row in data["images"] if row["source"] == "build"}
    contexts |= {"dynamic-labs/bitcoin/workstation", "dynamic-labs/bitcoin/mempool"}
    if (REPO / "student-launcher" / "control").is_dir():
        contexts.add("student-launcher/control")
    return sorted(contexts)


class EveryBuildContextIsFenced(unittest.TestCase):
    def test_no_excluded_file_is_staged(self):
        pats = student_exclude.patterns()
        for context in build_contexts():
            with self.subTest(context=context):
                self.assertTrue((REPO / context).is_dir(), f"{context} is in the images file but not in the repo")
                staged = student_exclude.stage_list(REPO, REPO / context, pats)
                self.assertTrue(staged, f"{context}: nothing staged")
                leaked = [rel for rel in staged if student_exclude.excluded(rel, pats)]
                self.assertEqual(leaked, [], f"{context} would ship instructor files")

    def test_an_excluded_folder_inside_a_context_is_dropped(self):
        # dynamic-labs/ as a context (tokens and dex build from it) holds regression-tests/ and the forensics answers.
        pats = student_exclude.patterns()
        staged = set(student_exclude.stage_list(REPO, REPO / "dynamic-labs", pats))
        self.assertFalse([p for p in staged if p.startswith("dynamic-labs/regression-tests/")])
        self.assertFalse([p for p in staged if "/quizes/" in p])
        # The Bitcoin exercise catalog holds no solutions, so the lab service it feeds keeps it.
        self.assertIn("dynamic-labs/lane-service/labs/bitcoin_catalog.yaml", staged)

    def test_the_release_workflow_stages_every_context(self):
        text = RELEASE.read_text(encoding="utf-8")
        self.assertIn('python3 tools/student_exclude.py stage "$CONTEXT"', text)
        self.assertIn('python3 tools/student_exclude.py stage "$2"', text)  # the Bitcoin bases
        self.assertIn("python3 tools/student_exclude.py stage student-launcher/control", text)
        # Builds read the staged copy only: every `docker buildx build` ends on a staged folder.
        for line in [ln for ln in text.splitlines() if "--metadata-file" in ln or "--push \"$out\"" in ln]:
            self.assertRegex(line.strip(), r'"\$(STAGED|out)"$')


class StageAndRemove(unittest.TestCase):
    def make_tree(self, root: Path) -> None:
        files = {
            "dynamic-labs/student-exclude.txt": "# test\ndynamic-labs/lab/answers/**\ndynamic-labs/lab/key.md\n"
                                                "dynamic-labs/lab/solution.md\n",
            "dynamic-labs/lab/Dockerfile": "FROM scratch\n",
            "dynamic-labs/lab/app.py": "print(1)\n",
            "dynamic-labs/lab/key.md": "secret\n",
            "dynamic-labs/lab/answers/one.json": "{}\n",
            "dynamic-labs/lab/answers/deep/two.json": "{}\n",
        }
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def test_stage_copies_only_student_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            self.make_tree(root)
            out = Path(tmp) / "out"
            code = student_exclude.main(["--root", str(root), "stage", "dynamic-labs/lab", str(out)])
            self.assertEqual(code, 0)
            got = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
            self.assertEqual(got, ["Dockerfile", "app.py"])

    def test_stage_refuses_a_folder_with_files_in_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            self.make_tree(root)
            out = Path(tmp) / "out"
            out.mkdir()
            (out / "stale").write_text("x")
            with self.assertRaises(SystemExit):
                student_exclude.main(["--root", str(root), "stage", "dynamic-labs/lab", str(out)])

    def test_stage_refuses_a_context_outside_the_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            self.make_tree(root)
            with self.assertRaises(SystemExit):
                student_exclude.main(["--root", str(root), "stage", "..", "--list"])

    def test_remove_vm_deletes_listed_files_and_empty_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)
            removed = student_exclude.remove_vm(root, student_exclude.patterns(root))
            self.assertEqual(sorted(removed), ["dynamic-labs/lab/answers/deep/two.json",
                                               "dynamic-labs/lab/answers/one.json", "dynamic-labs/lab/key.md"])
            self.assertFalse((root / "dynamic-labs/lab/answers").exists())
            self.assertTrue((root / "dynamic-labs/lab/app.py").is_file())

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_symlinks_stay_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            self.make_tree(root)
            os.symlink("app.py", root / "dynamic-labs/lab/link.py")
            out = Path(tmp) / "out"
            student_exclude.main(["--root", str(root), "stage", "dynamic-labs/lab", str(out)])
            self.assertTrue((out / "link.py").is_symlink())
            self.assertEqual(os.readlink(out / "link.py"), "app.py")


if __name__ == "__main__":
    unittest.main()
