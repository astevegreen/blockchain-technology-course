#!/usr/bin/env python3
"""Print the course's outstanding follow-up work: what the repo can compute, then the hand-kept list.

Usage: python tools/follow_ups.py

Computed: mind-map links that open no slide, and whether the glossary slide index is stale. Both read the rendered
site, so after lesson changes run `python tools/check.py --all --render` first. Hand-kept: docs/follow-ups.md,
where each session adds work outside its task (CLAUDE.md, "Finishing"). A report: it always exits 0.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

LIST = check.REPO / "docs" / "follow-ups.md"


def computed() -> list[tuple[str, list[str]]]:
    strip = lambda lines: [line.removeprefix(check.NOTE) for line in lines]  # noqa: E731
    return [("Mind-map links that open no slide (mind-map pass)", strip(check.mindmap_links())),
            ("Glossary slide index (glossary run)", strip(check.slide_index_check()))]


def listed() -> list[tuple[str, list[str]]]:
    """Each section of docs/follow-ups.md with its items, leaving out its "How to use"."""
    sections, name = [], None
    for line in LIST.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            sections.append((name, []))
        elif name and re.match(r"- ", line):
            sections[-1][1].append(line)
        elif name and sections[-1][1] and re.match(r"\s+\S", line):  # an item wrapped onto the next line
            sections[-1][1][-1] += " " + line.strip()
    return [(name, items) for name, items in sections if name != "How to use"]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # the list holds day markers such as ②
    for title, lines in computed() + listed():
        lines = list(dict.fromkeys(lines))  # the mind map links one slide from several nodes
        print(f"{title}:{'' if lines else ' none'}")
        for line in lines:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
