"""Tests for tools/pointer_check.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pointer_check as pc  # noqa: E402

SHEET = """# Run sheet

## Day 1: One

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Welcome | `blockchain-course/lessons/a/01-IN-welcome.qmd` |
| ① | First | `blockchain-course/lessons/a/02-IN-first.qmd` |
| ② | Second | `blockchain-course/lessons/a/04-CP-second.qmd` |
| ③ | Third | `blockchain-course/lessons/a/01-CM-third.qmd` |

## Day 2: Two

| Slot | Teach | File |
| --- | --- | --- |
| ① | Bitcoin | `blockchain-course/lessons/b/02-BF-bitcoin.qmd` |
"""

FRONT = '---\ntitle: "{title}"\n---\n\n'


def lesson(title: str, body: str) -> str:
    return FRONT.format(title=title) + body


class PointerCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.root = root / "lessons"
        (self.root / "a").mkdir(parents=True)
        (self.root / "b").mkdir()
        self.sheet = root / "RUN_SHEET.md"
        self.sheet.write_text(SHEET, encoding="utf-8")
        self.write("a/01-IN-welcome.qmd", lesson("Welcome", "## Hello\n\nHi.\n"))
        self.write("a/04-CP-second.qmd", lesson("Keys", "## Keys and the triangle\n\nKeys.\n"))
        self.write("a/01-CM-third.qmd", lesson("Consensus", "## Finality\n\nFinal.\n"))
        self.write("a/09-ZZ-untaught.qmd", lesson("Spare", "## Spare\n\nNot on the sheet.\n"))
        self.write("b/02-BF-bitcoin.qmd", lesson("Bitcoin", (
            "## Mining a Candidate Block\n\nMining.\n\n"
            "::: {.content-hidden}\n## Old Mempool Slide\n\nOld.\n:::\n")))
        self.addCleanup(self.tmp.cleanup)
        self.old_repo = pc.REPO
        pc.REPO = root
        self.addCleanup(setattr, pc, "REPO", self.old_repo)

    def write(self, rel: str, text: str) -> None:
        (self.root / rel).write_text(text, encoding="utf-8")

    def findings(self, body: str, notes: bool = False) -> list[str]:
        self.write("a/02-IN-first.qmd", lesson("First", body))
        course = pc.load_course(self.root, self.sheet)
        found = pc.check_lesson(course.lessons["02-IN"], course)
        return [f.message for f in found if notes or not f.note]

    def test_run_sheet_maps_lessons_to_days_and_slots(self) -> None:
        taught = pc.read_run_sheet(self.sheet)
        self.assertEqual(taught["01-IN"], pc.Slot(1, 0))
        self.assertEqual(taught["01-CM"], pc.Slot(1, 3))
        self.assertEqual(taught["02-BF"], pc.Slot(2, 1))

    def test_right_pointers_pass(self) -> None:
        body = ("## A\n\n- Day 2 ① (02-BF) teaches mining, in the slide \"Mining a Candidate Block\".\n"
                "- Lesson ③ shows finality; 01-IN showed the plan this morning.\n")
        self.assertEqual(self.findings(body), [])

    def test_unknown_and_untaught_lessons(self) -> None:
        found = self.findings("## A\n\n- See 77-QQ and 09-ZZ.\n")
        self.assertEqual(len(found), 2)
        self.assertIn("no lesson has the code 77-QQ", found[0])
        self.assertIn("09-ZZ is not taught", found[1])

    def test_day_beside_code_must_match(self) -> None:
        found = self.findings("## A\n\n- Day 3 (02-BF) teaches mining.\n")
        self.assertEqual(len(found), 1)
        self.assertIn("teaches 02-BF on day 2 ①", found[0])

    def test_day_not_beside_code_is_its_own_pointer(self) -> None:
        self.assertEqual(self.findings("## A\n\n- The cash-out is day 2 (exchanges) and 04-CP.\n"), [])

    def test_empty_slots_and_days(self) -> None:
        found = self.findings("## A\n\n- Day 2 ③ covers it, so does day 11, so does lesson ④.\n")
        self.assertEqual(len(found), 3)

    def test_hidden_slide_named(self) -> None:
        found = self.findings("## A\n\n- See 02-BF's slide \"Old Mempool Slide\" and the slide \"No Such Slide\".\n")
        self.assertEqual(found, ["\"Old Mempool Slide\" is a hidden slide in 02-BF",
                                 "02-BF has no slide titled \"No Such Slide\""])

    def test_time_words_against_order(self) -> None:
        found = self.findings("## A\n\n- As you saw in 02-BF, mining is costly.\n- 04-CP comes back to keys tomorrow.\n")
        self.assertEqual(len(found), 1)
        self.assertIn("written as already taught", found[0])

    def test_forward_word_to_past_lesson(self) -> None:
        self.write("b/02-BF-bitcoin.qmd", lesson("Bitcoin", "## Mine\n\n- Day 1 ③ (01-CM) returns to finality later.\n"))
        course = pc.load_course(self.root, self.sheet)
        found = [f.message for f in pc.check_lesson(course.lessons["02-BF"], course)]
        self.assertEqual(len(found), 1)
        self.assertIn("written as still to come", found[0])

    def test_durations_are_not_time_words(self) -> None:
        self.write("b/02-BF-bitcoin.qmd", lesson("Bitcoin", "## Mine\n\n- Final about 15 minutes later (day 1).\n"))
        course = pc.load_course(self.root, self.sheet)
        self.assertEqual(pc.check_lesson(course.lessons["02-BF"], course), [])

    def test_hidden_comments_and_code_are_skipped(self) -> None:
        body = ("## A\n\n<!-- Moved to 77-QQ on day 12 -->\n\n```text\nday 12 (77-QQ)\n```\n\n"
                "::: {.content-hidden}\n## B\n\n- 77-QQ\n:::\n\n- Inline <!-- 77-QQ --> text.\n")
        self.assertEqual(self.findings(body), [])

    def test_notes_are_read(self) -> None:
        found = self.findings("## A\n\nText.\n\n::: {.notes}\n- See 77-QQ.\n:::\n")
        self.assertEqual(len(found), 1)

    def test_file_names_and_ranges_are_not_pointers(self) -> None:
        body = ("## A\n\n- Open `02-BF-bitcoin.qmd` or [it](../b/02-BF-bitcoin.html#/x).\n"
                "- Days 6 to 9 run the traces.\n")
        self.assertEqual(self.findings(body), [])

    def test_topic_leads_are_notes(self) -> None:
        body = ("## A\n\n- Day 1's triangle again, and the day 2 mining case.\n"
                "- Scale by `decimals()` (04-CP) and `Keys` (04-CP).\n- And day 1's spaceship.\n")
        self.assertEqual(self.findings(body), [])
        notes = self.findings(body, notes=True)
        self.assertEqual(len(notes), 2)
        self.assertIn("`decimals()` beside 04-CP", notes[0])
        self.assertIn("\"spaceship\"", notes[1])


if __name__ == "__main__":
    unittest.main()
