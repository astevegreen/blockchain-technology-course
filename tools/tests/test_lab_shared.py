"""The labs' shared look and shell (blockchain-course/assets/labs/shared/) and the design-card template.

Run: python -m unittest discover -s tools/tests. The lab plan (docs/analysis/2026-11-lab-plan.md, Stage 2) asks
for one look and one shell that work offline with no Pyodide, and a card with ten lines; these tests hold those.
The shell's own logic is tested in lab_shell.test.mjs, which this file runs under node when node is present.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHARED = REPO / "blockchain-course" / "assets" / "labs" / "shared"
TEMPLATE = REPO / "docs" / "lab-cards" / "template.md"

# Every role the plan names gets a token (colour) in look.css: inputs, outputs, change, keys, signatures.
TOKENS = ["--input", "--output", "--change", "--fee", "--private-key", "--public-key", "--signature", "--hash"]
CLASSES = [".coin.input", ".coin.output", ".coin.change", ".coin.fee", ".key.private", ".key.public", ".addr",
           ".sig", ".hash", ".tx", ".conf[data-level=\"high\"]", ".conf[data-level=\"moderate\"]",
           ".conf[data-level=\"low\"]", ":root[data-display=\"projector\"]"]
CARD_LINES = ["The wrong belief", "The prediction", "The action", "The constraint", "The name", "The explorer view",
              "The twist", "The sentence", "The game, if any", "The archetype"]


def shared_files() -> list[Path]:
    return sorted(p for p in SHARED.iterdir() if p.suffix in {".css", ".js", ".html"})


class SharedLabFiles(unittest.TestCase):
    def test_offline(self):
        # Labs run from the src.zip as plain files, and in class without a network.
        for path in shared_files():
            text = path.read_text(encoding="utf-8")
            with self.subTest(path.name):
                self.assertIsNone(re.search(r"(?:src|href)\s*=\s*[\"']?(?:https?:)?//", text), "loads from the network")
                self.assertIsNone(re.search(r"@import\s+url\(\s*[\"']?(?:https?:)?//", text), "imports from the network")
                self.assertNotIn("type=\"module\"", text, "an ES module does not load from a plain file")

    def test_no_pyodide(self):
        # A load, not a mention: the shell's header says "no Pyodide".
        for path in shared_files():
            with self.subTest(path.name):
                hit = re.search(r"loadPyodide|pyodide(?:\.asm)?\.m?js", path.read_text(encoding="utf-8"), re.I)
                self.assertIsNone(hit, f"loads Pyodide: {hit and hit.group(0)}")

    def test_look_has_every_role(self):
        css = (SHARED / "look.css").read_text(encoding="utf-8")
        for token in TOKENS:
            with self.subTest(token):
                self.assertRegex(css, re.escape(token) + r"\s*:")
        for cls in CLASSES:
            with self.subTest(cls):
                self.assertIn(cls, css)

    def test_look_sheet_shows_every_object(self):
        sheet = (SHARED / "index.html").read_text(encoding="utf-8")
        for cls in ["coin input", "coin output", "coin change", "coin fee", "key private", "key public", "addr", "sig",
                    "hash", "tx"]:
            with self.subTest(cls):
                self.assertIn(f'class="{cls}', sheet)

    def test_shell_logic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not on PATH")
        out = subprocess.run([node, "--test", "tools/tests/lab_shell.test.mjs"], cwd=REPO, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(out.returncode, 0, out.stdout[-2000:] + out.stderr[-2000:])


class DesignCardTemplate(unittest.TestCase):
    def test_ten_lines_in_order(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        found = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, flags=re.M)
        self.assertEqual([int(n) for n, _ in found], list(range(1, 11)))
        self.assertEqual([name for _, name in found], CARD_LINES)

    def test_sources_and_approval(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("## Sources", text)
        self.assertIn("as of", text)
        self.assertIn("## Approval", text)


if __name__ == "__main__":
    unittest.main()
