"""Tests for tools/asof.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import contextlib
import datetime
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import asof  # noqa: E402

TODAY = datetime.date(2026, 11, 12)
FRONT = """---
title: "Probe"
lesson: 99-ZZ
format:
  aci-revealjs:
    slide-level: 2
---
"""


def problems(body: str, phrases: bool = True) -> list[str]:
    return asof.scan("probe.qmd", FRONT + body, phrases=phrases, today=TODAY)[1]


class Dates(unittest.TestCase):
    def test_the_three_forms_are_dates(self) -> None:
        self.assertEqual(asof.parse_date("11 Nov 2026", TODAY), (datetime.date(2026, 11, 11), ""))
        self.assertEqual(asof.parse_date("Jan 2026", TODAY), (datetime.date(2026, 1, 1), ""))
        self.assertEqual(asof.parse_date("2019", TODAY), (datetime.date(2019, 1, 1), ""))

    def test_anything_else_is_refused(self) -> None:
        for text in ("", "soon", "November 2026", "11 November 2026", "Nov 11, 2026", "2026-11-11", "11 nov 2026",
                     "11 Nov 26", "as of 11 Nov 2026", "(11 Nov 2026)", "31 Feb 2026", "0 Nov 2026",
                     "07 Nov 2026", "11 Abc 2026", "v1.2", "block 840,000", "1985", "11 Nov 2026 "):
            self.assertIsNone(asof.parse_date(text, TODAY)[0], text)

    def test_a_future_date_is_refused_with_a_day_of_slack_for_ci(self) -> None:
        self.assertIsNotNone(asof.parse_date("13 Nov 2026", TODAY)[0])
        self.assertIsNone(asof.parse_date("14 Nov 2026", TODAY)[0])
        self.assertIsNone(asof.parse_date("Dec 2026", TODAY)[0])
        self.assertIsNone(asof.parse_date("2027", TODAY)[0])


class Rules(unittest.TestCase):
    def test_a_tagged_date_passes(self) -> None:
        self.assertEqual(problems("## Fees\n\nThe subsidy is 3.125 BTC [@key] [24 Oct 2026]{.asof}.\n"), [])

    def test_a_leftover_phrase_is_refused(self) -> None:
        for body in ("## A\n\nThe subsidy is 3.125 BTC (as of 24 Oct 2026).\n",
                     "## A\n\n::: {.notes}\n- As of 24 Oct 2026 the subsidy is 3.125 BTC.\n:::\n",
                     "## A\n\nTrue as of [24 Oct 2026]{.asof}.\n",
                     "## A true only as of the read\n"):
            found = problems(body)
            self.assertEqual(len(found), 1, body)
            self.assertIn('"as of" phrase', found[0])

    def test_the_line_and_file_are_named(self) -> None:
        self.assertTrue(problems("## A\n\nFine.\n\nOpen as of Jan 2026.\n")[0].startswith("probe.qmd:12: "))

    def test_the_quoted_term_code_and_comments_are_left_alone(self) -> None:
        body = ('## Dates\n\nA date in parentheses means "as of"; so does “as of”.\n\n'
                "Run `balance --as of latest`.\n\n```bash\n# as of block 5\n```\n\n"
                "<!-- as of the last edit -->\n\n<!--\nas of then\n-->\n\nWas of no use; has often.\n")
        self.assertEqual(problems(body), [])

    def test_tags_only_skips_the_phrase_but_not_the_tags(self) -> None:
        body = "## A\n\nOpen as of Jan 2026. Closed [soon]{.asof}.\n"
        self.assertEqual(len(problems(body)), 2)
        found = problems(body, phrases=False)
        self.assertEqual(len(found), 1)
        self.assertIn("is not a date", found[0])

    def test_a_tag_that_is_not_a_date_is_refused(self) -> None:
        for tag, why in (("[November 2026]{.asof}", "is not a date"), ("[31 Feb 2026]{.asof}", "calendar"),
                         ("[11 Abc 2026]{.asof}", "no month"), ("[2 Jan 2031]{.asof}", "future"),
                         ("[]{.asof}", "is not a date"), ("[07 Nov 2026]{.asof}", "leading zero"),
                         ("[**11 Nov 2026**]{.asof}", "is not a date")):
            found = problems(f"## A\n\nA fact {tag}.\n")
            self.assertEqual(len(found), 1, tag)
            self.assertIn(why, found[0])

    def test_a_tag_written_another_way_is_refused(self) -> None:
        for line in ("A fact (11 Nov 2026){.asof}.", "A fact [11 Nov 2026]{.asof .small}.",
                     "A fact [11 Nov 2026]{#d .asof}.", "A fact 11 Nov 2026{.asof}."):
            found = problems(f"## A\n\n{line}\n")
            self.assertTrue(found and "must be written" in found[0], line)

    def test_a_tag_inside_parentheses_is_refused(self) -> None:
        for line in ("A fact ([11 Nov 2026]{.asof}).", "mempool (open source, AGPL-3.0, [31 Oct 2026]{.asof})"):
            found = problems(f"## A\n\n{line}\n")
            self.assertEqual(len(found), 1, line)
            self.assertIn("inside parentheses", found[0])

    def test_a_tag_after_closed_parentheses_or_a_link_passes(self) -> None:
        for line in ("mempool (open source, AGPL-3.0) [31 Oct 2026]{.asof}",
                     "Core 30.0 (Oct 2025) relays them [24 Oct 2026]{.asof}.",
                     "See [the page](https://example.org/a_(b) [11 Nov 2026]{.asof}.",
                     "a) first, b) second [11 Nov 2026]{.asof}",
                     "Run `f(x` then read it [11 Nov 2026]{.asof}."):
            self.assertEqual(problems(f"## A\n\n{line}\n"), [], line)


class Listing(unittest.TestCase):
    BODY = ("# Part\n\n## Fees {.smaller}\n\nA [24 Oct 2026]{.asof} and B [2019]{.asof}.\n\n"
            "## Halving\n\nC [May 2019]{.asof}.\n\n```\n[1 Jan 2020]{.asof}\n```\n")

    def test_every_tag_is_listed_oldest_first_with_its_slide(self) -> None:
        tagged, _ = asof.scan("lessons/a/01-ZZ-probe.qmd", FRONT + self.BODY, today=TODAY)
        lines = asof.listing(tagged)
        self.assertEqual([line.split()[-1] for line in lines[:3]], ["Fees", "Halving", "Fees"])
        self.assertTrue(lines[0].lstrip().startswith("2019  lessons/a/01-ZZ-probe.qmd:12"))
        self.assertTrue(lines[1].lstrip().startswith("May 2019  lessons/a/01-ZZ-probe.qmd:16"))
        self.assertEqual(lines[3], "3 tagged date(s) in 1 lesson(s); oldest 2019, newest 24 Oct 2026")

    def test_the_slide_follows_the_lessons_slide_level(self) -> None:
        deep = FRONT.replace("slide-level: 2", "slide-level: 3") + "## Part\n\n### Deep slide\n\nA [2019]{.asof}.\n"
        self.assertEqual(asof.scan("p.qmd", deep, today=TODAY)[0][0].slide, "Deep slide")
        shallow = FRONT + "## Slide\n\n### Sub-heading\n\nA [2019]{.asof}.\n"
        self.assertEqual(asof.scan("p.qmd", shallow, today=TODAY)[0][0].slide, "Slide")

    def test_an_empty_list_says_so(self) -> None:
        self.assertEqual(asof.listing([]), ["0 tagged date(s) in 0 lesson(s)"])


class CommandLine(unittest.TestCase):
    def run_main(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = asof.main(list(args))
        return code, out.getvalue()

    def test_check_is_silent_when_clean_and_fails_with_the_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = Path(tmp) / "good.qmd", Path(tmp) / "bad.qmd"
            good.write_text(FRONT + "## A\n\nA fact [24 Oct 2026]{.asof}.\n", encoding="utf-8")
            bad.write_text(FRONT + "## A\n\nA fact (as of 24 Oct 2026).\n", encoding="utf-8")
            self.assertEqual(self.run_main("--check", str(good)), (0, ""))
            code, out = self.run_main("--check", str(good), str(bad))
            self.assertEqual(code, 1)
            self.assertIn("bad.qmd:10: \"as of\" phrase", out)
            self.assertEqual(self.run_main("--check", "--tags-only", str(bad)), (0, ""))

    def test_check_needs_files_or_all(self) -> None:
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            asof.main(["--check"])

    def test_every_lesson_s_tags_are_valid(self) -> None:
        # The rule --all runs today; the phrase rule joins it when every lesson is converted.
        self.assertEqual(self.run_main("--check", "--all", "--tags-only"), (0, ""))


if __name__ == "__main__":
    unittest.main()
