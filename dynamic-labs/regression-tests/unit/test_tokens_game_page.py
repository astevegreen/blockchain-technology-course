#!/usr/bin/env python3
"""The "Spot the fake" game page against the token lab's chain, without Docker.

The page lives in blockchain-course/, which the live suite's container does not mount, so tools/check.py runs this
from a full checkout. Which token is which comes from the instructor-only quizes/spot-the-fake.env."""
from __future__ import annotations

import unittest
from pathlib import Path

LABS = Path(__file__).resolve().parents[2]
TOKENS = LABS / "tokens"
GAME_ENV = TOKENS / "quizes" / "spot-the-fake.env"
GAME_PAGE = LABS.parent / "blockchain-course" / "assets" / "labs" / "spot-the-fake" / "index.html"


def env(path: Path) -> dict[str, str]:
    return dict(line.strip().split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


@unittest.skipUnless(GAME_ENV.exists() and GAME_PAGE.exists(), "needs a full checkout (instructor files and site)")
class GamePageTest(unittest.TestCase):
    def test_page_lists_the_chains_tokens_and_the_issuer(self) -> None:
        game = env(GAME_ENV)
        page = GAME_PAGE.read_text(encoding="utf-8").lower()
        for key in ["POUND", "FAKE_A", "FAKE_B", "TWIST"]:
            self.assertIn(game[key].lower(), page, key)
        self.assertIn(env(TOKENS / "chain" / "addresses.env")["A0"].lower(), page)

    def test_student_addresses_do_not_say_which_token_is_which(self) -> None:
        # Students receive addresses.env; the game's addresses stay in the instructor file.
        public = (TOKENS / "chain" / "addresses.env").read_text(encoding="utf-8").lower()
        for key, address in env(GAME_ENV).items():
            self.assertNotIn(address.lower(), public, key)


if __name__ == "__main__":
    unittest.main()
