"""Tests for tools/alignment_map.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import alignment_map as am  # noqa: E402


class Terms(unittest.TestCase):
    def test_capital_term_matches_capitals_only(self):
        pats = am.compile_terms(["PoS", "AML"])
        self.assertEqual(am.hits(pats, "AML rules"), 1)
        self.assertEqual(am.hits(pats, "aml rules"), 0)
        # PoS has a lower-case letter, so it ignores case like any other term.
        self.assertEqual(am.hits(pats, "pos and PoS"), 2)

    def test_whole_words_only(self):
        pats = am.compile_terms(["hops?"])
        self.assertEqual(am.hits(pats, "two hops, one hop"), 2)
        self.assertEqual(am.hits(pats, "shops"), 0)

    def test_term_split_across_lines_in_yaml(self):
        pats = am.compile_terms(["pending\n     transactions?"])
        self.assertEqual(am.hits(pats, "pending transactions"), 1)


class Slides(unittest.TestCase):
    def read(self, text: str) -> list[am.Slide]:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.qmd"
            p.write_text(text, encoding="utf-8")
            return am.read_slides(p)

    def test_notes_hidden_slides_and_code(self):
        slides = self.read(
            "# Section\n\n"
            "## Visible {.smaller}\n\nbody word\n\n::: {.notes}\nnotes word\n:::\n\n"
            "::: {.content-hidden}\n## Hidden\n\nhidden body\n:::\n\n"
            "## Code\n\n```python\n## not a slide\n```\n"
        )
        self.assertEqual([s.title for s in slides], ["Visible", "Code"])
        self.assertIn("body word", slides[0].body)
        self.assertNotIn("notes word", slides[0].body)
        self.assertIn("## not a slide", slides[1].body)

    def test_nested_fences_inside_hidden(self):
        slides = self.read(
            "::: {.content-hidden}\n## Hidden\n\n:::: {.columns}\ninner\n::::\n\n## Still hidden\n:::\n\n## Shown\n"
        )
        self.assertEqual([s.title for s in slides], ["Shown"])


class RunSheet(unittest.TestCase):
    def test_lessons_lab_wrapped_across_lines_and_graded_question(self):
        text = (
            "## Day 7: Mixers\n\n"
            "| ① | 0900 | `blockchain-course/lessons/forensics/06-FO-mixers_and_coinjoin.qmd` |\n"
            "| 0845 | W | `blockchain-course/lessons/introduction/01-IN-welcome.qmd` |\n\n"
            "Start the lab. Students open\n`/labs/coinjoin-trace/` in the browser.\n\n"
            "**Graded point 2:** the limits-of-tracing note (question 12). Rubric follows.\n\n"
            "## Day 8: Next\n"
        )
        days = am.read_run_sheet(text)
        d = days[7]
        self.assertEqual([s for s, _ in d.lessons], ["①", "W"])
        self.assertEqual(d.labs, ["dynamic-labs/coinjoin-trace/gateway/static/lab/index.html"])
        self.assertEqual(d.graded, [12])
        self.assertEqual(d.graded_note, "the limits-of-tracing note (question 12)")
        self.assertEqual(days[8].labs, [])


class Labs(unittest.TestCase):
    def test_numbered_questions_then_unnumbered_parts(self):
        page = (
            "<h2>Questions</h2><ol><li>One</li><li>Two</li></ol>"
            '<h2>Part 2</h2><ol start="3"><li>Three</li></ol>'
            "<h2>Graded note</h2><ol><li>Where it stops</li></ol>"
            "<h2>Sources</h2><ol><li>A source</li></ol>"
        )
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.html"
            p.write_text(page, encoding="utf-8")
            items = am.read_lab(str(p))
        self.assertEqual([i.label for i in items], ["Q1", "Q2", "Q3", "Graded note, item 1"])
        self.assertEqual([i.number for i in items], [1, 2, 3, None])


if __name__ == "__main__":
    unittest.main()
