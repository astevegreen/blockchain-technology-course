"""The slides' glossary lookup (blockchain-course/_extensions/aci/_extensions/glossary-lookup/).

Its search and the terms.json it reads are tested in glossary_lookup.test.mjs, which this file runs under node
when node is present. Run: python -m unittest discover -s tools/tests
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class GlossaryLookup(unittest.TestCase):
    def test_node_suite(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not on PATH")
        out = subprocess.run([node, "--test", "tools/tests/glossary_lookup.test.mjs"], cwd=REPO, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(out.returncode, 0, out.stdout[-2000:] + out.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
