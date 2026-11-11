#!/usr/bin/env python3
"""The "Two of three" game page gives exactly the commands the live suite runs, without Docker.

The page lives in blockchain-course/, which the live suite's container does not mount, so tools/check.py runs this
from a full checkout; the live test (automated/bitcoin/test_two_of_three_live.py) runs the same lines on two stations."""
from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

LABS = Path(__file__).resolve().parents[2]
COMMANDS = LABS / "regression-tests" / "automated" / "bitcoin" / "two_of_three_commands.py"
PAGE = LABS.parent / "blockchain-course" / "assets" / "labs" / "two-of-three" / "index.html"


def page_blocks(text: str) -> list[list[str]]:
    """Each round 1 command block on the page, as the shell receives it (JS string escapes undone)."""
    blocks = []
    # Each block opens `cmd("who", [` and closes with `]` on a line of its own; commands hold brackets too.
    for match in re.finditer(r'cmd\("[^"]*", \[\n(.*?)\n\s*\]', text, re.S):
        lines = re.findall(r'^\s*"((?:[^"\\]|\\.)*)"', match.group(1), re.M)
        blocks.append([json.loads(f'"{line}"') for line in lines])
    return blocks


@unittest.skipUnless(PAGE.exists(), "needs a full checkout (the course site)")
class TwoOfThreePageTest(unittest.TestCase):
    def setUp(self) -> None:
        spec = importlib.util.spec_from_file_location("two_of_three_commands", COMMANDS)
        self.commands = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.commands)
        self.page = PAGE.read_text(encoding="utf-8")

    def test_round_1_blocks_match(self) -> None:
        self.assertEqual(page_blocks(self.page), self.commands.ROUND_1)

    def test_round_2_spend_try_is_on_the_page(self) -> None:
        for line in self.commands.WATCH_TRY.split("\n"):
            self.assertIn(json.dumps(line.replace(" >/dev/null", ""))[1:-1], self.page)

    def test_page_names_no_answer(self) -> None:
        # The paid indexes and addresses are on the instructor's sheet only.
        for leak in ("paid_indexes", "bcrt1", "bc1q", "tpub", "xpub6"):
            self.assertNotIn(leak, self.page)


if __name__ == "__main__":
    unittest.main()
