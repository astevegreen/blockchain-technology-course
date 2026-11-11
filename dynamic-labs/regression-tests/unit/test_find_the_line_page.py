#!/usr/bin/env python3
"""The "Find the line" game page against the exploit chain's addresses, without Docker.

The page lives in blockchain-course/, which the live suite's container does not mount, so tools/check.py runs this
from a full checkout. The card (docs/lab-cards/find-the-line.md) has two rules a file can break: the page holds no
key, and nothing a student receives names the two contracts' answers (their old names, ApprovalDrainer and
TimelockRugVault, or a drain, a drainer or a rug)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

LABS = Path(__file__).resolve().parents[2]
EXPLOIT = LABS / "cross-chain" / "exploit"
ADDRESSES = EXPLOIT / "chain" / "addresses.env"
GAME_PAGE = LABS.parent / "blockchain-course" / "assets" / "labs" / "find-the-line" / "index.html"
GIVEAWAYS = re.compile(r"ApprovalDrainer|TimelockRugVault|\bDRAINER\b|\bRUG_VAULT\b|drainer|\bdrain\b|\brug\b", re.I)


def env(path: Path) -> dict[str, str]:
    return dict(line.strip().split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


@unittest.skipUnless(GAME_PAGE.exists(), "needs a full checkout (the course site)")
class FindTheLinePageTest(unittest.TestCase):
    def test_page_names_the_chains_addresses(self) -> None:
        page = GAME_PAGE.read_text(encoding="utf-8").lower()
        chain = env(ADDRESSES)
        for key in ["A0", "A8", "A9", "TOKEN", "STAKING", "TIMELOCK_VAULT", "BORROWER", "LENDER"]:
            self.assertIn(chain[key].lower(), page, key)

    def test_page_opens_each_source_by_its_neutral_name(self) -> None:
        page = GAME_PAGE.read_text(encoding="utf-8")
        for name in ["StakingRewards.sol", "TimelockVault.sol", "PlainBorrower.sol", "CourseFlashLender.sol"]:
            self.assertIn(name, page)
            self.assertTrue((EXPLOIT / "contracts" / name).exists(), name)

    def test_page_holds_no_key(self) -> None:
        page = GAME_PAGE.read_text(encoding="utf-8")
        # The page stores the team's lines; it never scores them or names the answer lines.
        self.assertNotIn("0x095ea7b3", page)  # approve's selector
        self.assertNotIn("0x92092809", page)  # setWithdrawFeeBps's selector
        self.assertIsNone(re.search(r"0x[0-9a-fA-F]{64}", page), "a transaction hash points at a line")

    def test_student_files_carry_no_giveaway_names(self) -> None:
        # The page's own text says "rug pull" once, in the tell example, which is shown only after the game.
        page = GAME_PAGE.read_text(encoding="utf-8").replace("It fits a rug pull", "")
        files = {"page": page, "addresses.env": ADDRESSES.read_text(encoding="utf-8")}
        for sol in (EXPLOIT / "contracts").glob("*.sol"):
            files[sol.name] = sol.read_text(encoding="utf-8")
        fallback = EXPLOIT / "gateway" / "static" / "fallback" / "index.html"
        if fallback.exists():
            files["fallback"] = fallback.read_text(encoding="utf-8")
        # Sourcify serves each contract's metadata and source to Otterscan's contract tab.
        for pattern in ("metadata.json", "*.sol"):
            for sourcify in (EXPLOIT / "chain" / "sourcify").rglob(pattern):
                files[str(sourcify.relative_to(EXPLOIT))] = sourcify.read_text(encoding="utf-8")
        for name, text in files.items():
            self.assertIsNone(GIVEAWAYS.search(text), f"{name}: {GIVEAWAYS.search(text)}")


if __name__ == "__main__":
    unittest.main()
