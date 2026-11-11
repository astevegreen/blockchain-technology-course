#!/usr/bin/env python3
"""The "Find the exchange" game page against the Tron lab's queries and answer key, without Docker.

The page lives in blockchain-course/, which the live suite's container does not mount, so tools/check.py runs this
from a full checkout. The key (which seat is the deposit address) is in the instructor-only quizes/facts_find.json;
the live suite (automated/tron/test_tron_live.py) checks that file against the served snapshot."""
from __future__ import annotations

import fnmatch
import json
import re
import unittest
from pathlib import Path

LABS = Path(__file__).resolve().parents[2]
TRON = LABS / "tron"
FACTS = TRON / "quizes" / "facts_find.json"
PAGE = LABS.parent / "blockchain-course" / "assets" / "labs" / "find-the-exchange" / "index.html"


def game_seats() -> dict[str, str]:
    """The game view in queries/find.sql: seat letter -> address."""
    sql = (TRON / "queries" / "find.sql").read_text(encoding="utf-8")
    view = sql.split("CREATE OR REPLACE VIEW game AS", 1)[1].split(";", 1)[0]
    return dict(re.findall(r"\('([A-D])', '(T[1-9A-HJ-NP-Za-km-z]{33})'\)", view))


@unittest.skipUnless(FACTS.exists() and PAGE.exists(), "needs a full checkout (instructor files and site)")
class FindTheExchangePageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.page = PAGE.read_text(encoding="utf-8")
        self.facts = json.loads(FACTS.read_text(encoding="utf-8"))

    def test_page_lists_the_queries_four_addresses_in_the_same_seats(self) -> None:
        page = dict(re.findall(r'\{ id: "([A-D])", addr: "(T\w{33})" \}', self.page))
        self.assertEqual(page, game_seats())
        self.assertEqual(sorted(page.values()), list(page.values()), "alphabetical, so the order says nothing")

    def test_page_opens_the_find_lab_and_its_saved_results(self) -> None:
        self.assertIn('"/labs/tron/query/?lab=find"', self.page)
        self.assertIn('"/labs/tron/fallback/find/"', self.page)
        self.assertTrue((TRON / "query-page" / "labs" / "find.json").exists())

    def test_hot_wallet_is_the_labelled_one(self) -> None:
        labels = (TRON / "snapshot" / "find" / "labels.csv").read_text(encoding="utf-8")
        hot = self.facts["deposit"]["swept_to"]
        self.assertIn(f'var HOT = "{hot}"', self.page)
        self.assertIn(hot, labels)

    def test_tell_example_is_the_cards_worked_example_sentence(self) -> None:
        # The card's sentence uses the worked example's deposit (TXLh…, 400 USDT), so the game's answer stays off the page.
        tell = self.page.split("example:", 1)[1].split(chr(10), 1)[0]
        for value in ("400 USDT", "TXLh…", "TV6Mu…", "Moderate confidence", "The other three reached no labelled exchange"):
            self.assertIn(value, tell)
        self.assertTrue((TRON / "snapshot" / "transfers.csv").read_text(encoding="utf-8").count("TXLhMxzterktHm9z27XamgXz2EL9EfoBnR"))

    def test_answer_key_is_fenced_from_students(self) -> None:
        rules = [line.strip() for line in (LABS / "student-exclude.txt").read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.startswith("#")]
        for path in ("dynamic-labs/tron/quizes/facts_find.json", "dynamic-labs/tron/quizes/FIND_THE_EXCHANGE_ANSWERS.md"):
            self.assertTrue(any(fnmatch.fnmatch(path, rule) for rule in rules), path)

    def test_student_files_do_not_say_which_seat_is_the_deposit(self) -> None:
        # The lab files name the four neutrally; only the key says which one swept to the hot wallet.
        student = [TRON / "queries" / "find.sql", TRON / "query-page" / "labs" / "find.json",
                   TRON / "snapshot" / "find" / "labels.csv"]
        address = self.facts["deposit"]["address"]
        for path in student:
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                if address in line:
                    self.assertNotRegex(line.lower(), r"deposit|binance|answer|customer", path.name)

    def test_page_never_shows_the_deposits_figures(self) -> None:
        # The board lists all four addresses in full; no hint, step or example may carry the deposit's figures.
        d = self.facts["deposit"]
        for value in (d["paid"] + " USDT", d["swept"], d["address"][:4] + "…" + d["address"][-4:], d["sweep_time"][:10]):
            self.assertNotIn(value, self.page)

    def test_outcome_is_always_the_deposit_address(self) -> None:
        # The prediction has one answer, (b); a team that names the hot wallet must not read "Your prediction held".
        self.assertRegex(self.page, r"var choice = 1;")
        self.assertNotRegex(self.page, r"choice = hot \?")


if __name__ == "__main__":
    unittest.main()
