#!/usr/bin/env python3
"""The "Pool trading" course page opens the game on the exchange lab's host and gives away no answer, without Docker.

The page lives in blockchain-course/, which the live suite's container does not mount, so tools/check.py runs this
from a full checkout; the live test (automated/dex/test_pool_trading_live.py) plays a round on the chain."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

LABS = Path(__file__).resolve().parents[2]
PAGE = LABS.parent / "blockchain-course" / "assets" / "labs" / "pool-trading" / "index.html"
GAME = LABS / "dex" / "gateway" / "static" / "sign" / "pool-trading.html"
LESSON = LABS.parent / "blockchain-course" / "lessons" / "ethereum" / "07-EF-liquidity_and_exits.qmd"
# What only the instructor's script and key know: which seats get the twist, the bot's floor, the script itself.
LEAKS = ("TWIST_SEATS", "MIN_PROFIT", "FRONT_CAP", "pool_trading.py", "POOL_TRADING_ANSWERS", "quizes/")


@unittest.skipUnless(PAGE.exists(), "needs a full checkout (the course site)")
class PoolTradingPageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.page = PAGE.read_text(encoding="utf-8")

    def test_page_opens_the_game_on_the_lab_host(self) -> None:
        self.assertTrue(GAME.exists())
        self.assertIn('"/sign/pool-trading.html"', self.page)
        self.assertIn('"//dex."', self.page)
        self.assertIn('":8443"', self.page)

    def test_slide_link_resolves(self) -> None:
        found = re.search(r'href: "\.\./\.\./\.\./lessons/ethereum/07-EF-liquidity_and_exits\.html#/([a-z0-9-]+)"',
                          self.page)
        self.assertIsNotNone(found)
        self.assertIn("## A bigger trade gets a worse price", LESSON.read_text(encoding="utf-8"))
        self.assertEqual(found.group(1), "a-bigger-trade-gets-a-worse-price")
        self.assertIn("/assets/labs/pool-trading/index.html", LESSON.read_text(encoding="utf-8"))

    def test_twist_answer_is_no_sandwich(self) -> None:
        self.assertIn("answer: 2,", self.page)
        self.assertIn('"No: no one bought before you and sold after you."', self.page)

    def test_pages_name_no_answer(self) -> None:
        game = GAME.read_text(encoding="utf-8") + (GAME.with_suffix(".js")).read_text(encoding="utf-8")
        for leak in LEAKS:
            self.assertNotIn(leak, self.page, leak)
            self.assertNotIn(leak, game, leak)


if __name__ == "__main__":
    unittest.main()
