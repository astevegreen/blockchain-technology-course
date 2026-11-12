"""Tests for the site's Lua filters, blockchain-course/filters/. Run: python -m unittest discover -s tools/tests

Each test runs Pandoc (the one Quarto ships) on a few slides of Markdown and reads the RevealJS HTML it writes.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

FILTERS = Path(__file__).resolve().parents[2] / "blockchain-course" / "filters"
QUARTO = shutil.which("quarto")
CITATION = 'class="citation"'


def render(markdown: str, to: str = "revealjs", slide_level: int = 2) -> str:
    done = subprocess.run(
        [QUARTO, "pandoc", "--from", "markdown", "--to", to, f"--slide-level={slide_level}", "--wrap=none",
         "--lua-filter", str(FILTERS / "cite-notes.lua"), "--lua-filter", str(FILTERS / "asof.lua")],
        input=markdown, capture_output=True, text=True, encoding="utf-8", timeout=120, check=False)
    if done.returncode:
        raise AssertionError(done.stderr)
    return done.stdout


def slides(html: str) -> dict[str, tuple[str, str]]:
    """Each slide's id, mapped to (what the class sees, the speaker notes)."""
    out = {}
    for section in re.findall(r'<section id="([^"]+)" class="slide[^>]*>(.*?)</section>', html, re.S):
        ident, body = section
        notes = "".join(re.findall(r'<aside class="notes">(.*?)</aside>', body, re.S))
        out[ident] = (re.sub(r'<aside class="notes">.*?</aside>', "", body, flags=re.S), notes)
    return out


@unittest.skipUnless(QUARTO, "quarto is not on PATH")
class CitationsMoveToTheNotes(unittest.TestCase):
    def test_a_citation_leaves_the_slide_and_joins_its_notes(self) -> None:
        deck = slides(render(
            "## Fees\n\nMiners order by fee rate [@fees; @blocks]. Blocks are scarce [@blocks, sec. 2].\n\n"
            "::: {.notes}\n**Sources**\n\n- @fees\n:::\n\n"
            "## Halving\n\nNo sources here.\n\n::: {.notes}\nPlain notes.\n:::\n"))
        seen, notes = deck["fees"]
        self.assertNotIn(CITATION, seen)
        self.assertIn("<p>Miners order by fee rate. Blocks are scarce.</p>", seen)
        self.assertEqual(notes.count(CITATION), 3)  # the one already there, and the two moved
        self.assertIn("<strong>Cited on the slide</strong>", notes)
        self.assertIn('<li>Miners order by fee rate <span class="citation" data-cites="fees blocks">', notes)
        self.assertIn('<li>Blocks are scarce <span class="citation" data-cites="blocks">', notes)
        self.assertIn("[@blocks, sec. 2]", notes)  # the locator moves with its citation
        seen, notes = deck["halving"]
        self.assertNotIn("Cited on the slide", notes)
        self.assertIn("Plain notes.", notes)

    def test_each_slide_keeps_its_own_citations(self) -> None:
        deck = slides(render(
            "## One\n\nFirst claim [@a].\n\n::: {.notes}\nNotes one.\n:::\n\n"
            "## Two\n\nSecond claim [@b].\n\n::: {.notes}\nNotes two.\n:::\n"))
        self.assertIn('data-cites="a"', deck["one"][1])
        self.assertNotIn('data-cites="b"', deck["one"][1])
        self.assertIn('data-cites="b"', deck["two"][1])
        self.assertNotIn('data-cites="a"', deck["two"][1])

    def test_a_slide_without_notes_gets_a_notes_block(self) -> None:
        seen, notes = slides(render("## Bare\n\nA claim [@a].\n"))["bare"]
        self.assertIn("<p>A claim.</p>", seen)
        self.assertIn('data-cites="a"', notes)

    def test_the_label_is_the_last_words_before_the_citation(self) -> None:
        _, notes = slides(render(
            "## Long\n\nOne two three four five six seven eight nine ten [@a].\n\n- [@b] opens this bullet here.\n"))["long"]
        self.assertIn("<li>…three four five six seven eight nine ten <span", notes)
        self.assertIn("<li>opens this bullet here. <span", notes)

    def test_two_citations_for_one_claim_share_its_label(self) -> None:
        seen, notes = slides(render("## Twice\n\nOne claim [@a] [@b]; then another [@c].\n"))["twice"]
        self.assertIn("<p>One claim; then another.</p>", seen)
        self.assertIn('<li>One claim <span class="citation" data-cites="a">', notes)
        self.assertIn('<li>One claim <span class="citation" data-cites="b">', notes)
        self.assertIn('<li>then another <span class="citation" data-cites="c">', notes)

    def test_citations_in_lists_columns_and_emphasis_move_too(self) -> None:
        seen, notes = slides(render(
            "## Mixed\n\n:::: {.columns}\n::: {.column}\n- A bullet [@a].\n- **Bold claim [@b]** stays bold.\n:::\n"
            "::: {.column}\n> A quote [@c].\n:::\n::::\n\n::: {.notes}\nNotes.\n:::\n"))["mixed"]
        self.assertNotIn(CITATION, seen)
        self.assertIn("<strong>Bold claim</strong> stays bold.", seen)
        self.assertEqual(notes.count(CITATION), 3)

    def test_a_source_only_column_is_dropped_from_a_table(self) -> None:
        seen, notes = slides(render(
            "## Table\n\n| Tool | Use | Source |\n|---|---|---|\n| Alpha | Reads blocks | [@a] |\n"
            "| Beta | Reads fees [@c] | [@b] |\n\n::: {.notes}\nNotes.\n:::\n"))["table"]
        self.assertNotIn(CITATION, seen)
        self.assertNotIn("Source", seen)
        self.assertEqual(len(re.findall(r"<th[ >]", seen)), 2)
        self.assertIn("Reads fees</td>", seen)
        self.assertIn('<li>Alpha <span class="citation" data-cites="a">', notes)
        self.assertIn('<li>Beta <span class="citation" data-cites="b">', notes)
        self.assertIn('<li>Reads fees <span class="citation" data-cites="c">', notes)

    def test_a_column_with_other_text_stays(self) -> None:
        seen, _ = slides(render(
            "## Table\n\n| Tool | Source |\n|---|---|\n| Alpha | [@a] |\n| Beta | none found |\n"))["table"]
        self.assertEqual(len(re.findall(r"<th[ >]", seen)), 2)
        self.assertIn("none found", seen)

    def test_a_paragraph_that_was_only_a_citation_goes(self) -> None:
        seen, notes = slides(render("## Only\n\nA claim.\n\n[@a]\n"))["only"]
        self.assertNotIn("<p></p>", seen)
        self.assertIn('data-cites="a"', notes)

    def test_slides_inside_a_hidden_block_and_at_level_three(self) -> None:
        deck = slides(render(
            "## Shown\n\nA claim [@a].\n\n:::: {.content-hidden}\n\n## Wrapped\n\nB claim [@b].\n\n"
            "::: {.notes}\nWrapped notes.\n:::\n\n::::\n"))
        self.assertIn('data-cites="a"', deck["shown"][1])
        self.assertNotIn('data-cites="b"', deck["shown"][1])
        deep = render("# Part\n\n## Section\n\n### Deep\n\nA claim [@a].\n\n### Next\n\nB claim [@b].\n", slide_level=3)
        deep_slides = slides(deep)
        self.assertIn('data-cites="a"', deep_slides["deep"][1])
        self.assertIn('data-cites="b"', deep_slides["next"][1])

    def test_other_formats_keep_their_citations_in_place(self) -> None:
        html = render("## Page\n\nA claim [@a].\n", to="html")
        self.assertIn('A claim <span class="citation" data-cites="a">', html)
        self.assertNotIn("Cited on the slide", html)


@unittest.skipUnless(QUARTO, "quarto is not on PATH")
class AsOfDatesShowInParentheses(unittest.TestCase):
    def test_a_tagged_date_gets_parentheses_on_slides_and_pages(self) -> None:
        for to in ("revealjs", "html"):
            html = render("## Fees\n\nThe subsidy is 3.125 BTC [@a] [24 Oct 2026]{.asof}.\n", to=to)
            self.assertIn('<span class="asof">(24 Oct 2026)</span>', html, to)

    def test_the_date_follows_the_fact_once_the_citation_moves(self) -> None:
        seen, _ = slides(render("## Fees\n\nThe subsidy is 3.125 BTC [@a] [24 Oct 2026]{.asof}.\n"))["fees"]
        self.assertIn('<p>The subsidy is 3.125 BTC <span class="asof">(24 Oct 2026)</span>.</p>', seen)

    def test_other_spans_are_left_alone(self) -> None:
        self.assertIn('<span class="smaller">Feb 2016</span>', render("## A\n\n[Feb 2016]{.smaller}\n"))


if __name__ == "__main__":
    unittest.main()
