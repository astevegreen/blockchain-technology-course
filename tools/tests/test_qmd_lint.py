"""Tests for tools/qmd_lint.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import qmd_lint  # noqa: E402

FRONT = """---
title: "Probe"
lesson: 99-ZZ
format:
  aci-revealjs:
    slide-level: 2
---
"""

NOTES = """
::: {.notes}
**Overall Slide Concept**
Why this slide matters.

**Key Points**
- One

**Walkthrough**
None

**Sources**
- @nakamoto_bitcoinpeertopeerelectronic_2008
:::
"""

CLEAN = FRONT + f"""
## First Slide

- A point citing [@nakamoto_bitcoinpeertopeerelectronic_2008].
- Mail admin@example.com and `@decorator` are not citations.

:::: {{.columns}}
::: {{.column width="50%"}}
Left
:::
::::
{NOTES}
## References
"""


class LintCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def lint(self, text: str, name: str = "probe.qmd", notes: bool = False) -> tuple[int, str]:
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = qmd_lint.main([str(path), *(["--notes"] if notes else [])])
        return code, out.getvalue()

    def test_clean_lesson_is_silent(self) -> None:
        self.assertEqual(self.lint(CLEAN), (0, ""))

    def test_dot_cell_inside_html_comment(self) -> None:
        text = FRONT + "\n## Kept\n" + NOTES + "\n<!--\n\n## Retired\n\n```{dot}\ndigraph { a -> b }\n```\n\n-->\n"
        code, out = self.lint(text)
        self.assertEqual(code, 1)
        self.assertIn("executable cell inside an HTML comment", out)
        self.assertIn("slide heading inside an HTML comment", out)
        self.assertIn(":::: {.content-hidden}", out)

    def test_content_hidden_div_is_accepted(self) -> None:
        text = FRONT + "\n## Kept\n" + NOTES + "\n:::: {.content-hidden}\n\n## Retired\n\n```{dot}\ndigraph { a }\n```\n\n::::\n"
        self.assertEqual(self.lint(text), (0, ""))

    def test_unclosed_div(self) -> None:
        code, out = self.lint(FRONT + "\n## Slide\n\n::: {.callout-note}\nText\n" + NOTES)
        self.assertEqual(code, 1)
        self.assertIn("probe.qmd:11: div {.callout-note} is never closed", out)

    def test_stray_closing_fence(self) -> None:
        code, out = self.lint(FRONT + "\n## Slide\n" + NOTES + "\n:::\n")
        self.assertEqual(code, 1)
        self.assertIn("closing ':::' has no matching opening div", out)

    def test_fences_inside_code_blocks_are_ignored(self) -> None:
        text = FRONT + "\n## Slide\n\n```markdown\n::: {.notes}\n## Not a slide\n```\n" + NOTES
        self.assertEqual(self.lint(text), (0, ""))

    def test_heading_inside_div(self) -> None:
        code, out = self.lint(FRONT + "\n## Slide\n" + NOTES + "\n::: {.callout-note}\n## Trapped\n:::\n")
        self.assertEqual(code, 1)
        self.assertIn("slide heading inside the div opened at line", out)

    def test_front_matter_needs_title_lesson_and_format(self) -> None:
        code, out = self.lint("---\ntitle: x\nformat: html\n---\n\n## Slide\n" + NOTES)
        self.assertEqual(code, 1)
        self.assertIn("front matter has no `lesson`", out)
        self.assertIn("must use aci-revealjs", out)

    def test_unknown_citation(self) -> None:
        code, out = self.lint(FRONT + "\n## Slide\n\nClaim [@no_such_key_2099].\n" + NOTES)
        self.assertEqual(code, 1)
        self.assertIn("citation @no_such_key_2099 is not in Blockchain.bib", out)

    def test_file_name(self) -> None:
        code, out = self.lint(CLEAN, name="bad name.qmd")
        self.assertEqual(code, 1)
        self.assertIn("file name may use only", out)

    def test_missing_notes_is_a_note_not_an_error(self) -> None:
        text = FRONT + "\n## Slide Without Notes\n\nText.\n\n## Agenda\n\nSkipped heading.\n"
        self.assertEqual(self.lint(text), (0, ""))
        code, out = self.lint(text, notes=True)
        self.assertEqual(code, 0)
        self.assertIn("'Slide Without Notes' has no speaker-notes block", out)
        self.assertNotIn("Agenda", out)

    def test_output_is_capped(self) -> None:
        text = FRONT + "\n## Slide\n" + NOTES + "".join(f"\nClaim [@missing_{i}].\n" for i in range(30))
        code, out = self.lint(text)
        lines = out.strip().splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), qmd_lint.MAX_LINES)
        self.assertTrue(lines[-1].startswith("... (11 more)"))


if __name__ == "__main__":
    unittest.main()
