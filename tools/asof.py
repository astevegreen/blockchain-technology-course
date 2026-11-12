#!/usr/bin/env python3
"""The "as of" dates in the lessons: list them, or check them.

A fact that changes carries the date it was true. In a lesson the date is written as a tag with no words and
no parentheses, `[11 Nov 2026]{.asof}`, and the build shows it as "(11 Nov 2026)"
(blockchain-course/filters/asof.lua). Release and event dates, such as "0.12.0 (Feb 2016)", are not tagged.

Usage:
  python tools/asof.py [<file.qmd>...]             list every tagged date with its lesson and slide, oldest first
  python tools/asof.py --check <file.qmd>... | --all [--tags-only]
                                                   print nothing and exit 0 when clean; otherwise print
                                                   `path:line: message` lines and exit 1

The check refuses:
  - a leftover "as of" phrase (the quoted term "as of", used to name the convention, is allowed);
  - a `{.asof}` tag that does not hold a valid date: `D Mon YYYY`, `Mon YYYY` or `YYYY`, not in the future;
  - a tag inside parentheses, which would show two pairs.
`--tags-only` skips the first.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COURSE = REPO / "blockchain-course"
LESSONS = COURSE / "lessons"
MAX_LINES = 20

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
FORMS = "`D Mon YYYY`, `Mon YYYY` or `YYYY`, with the month as " + ", ".join(MONTHS[:3]) + " …"
DATE = re.compile(r"^(?:(?:(\d{1,2}) )?([A-Z][a-z]{2}) )?(\d{4})$")
TAG = re.compile(r"\[([^\]\[]*)\]\{\.asof\}")
TAG_MARK = re.compile(r"\{[^}]*\.asof\b[^}]*\}")
PHRASE = re.compile(r"\bas of\b", re.IGNORECASE)
QUOTED_TERM = re.compile(r"[\"“]as of[\"”]", re.IGNORECASE)  # the convention's name, not a dated fact
CODE_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
HEADING_ATTRS = re.compile(r"\s*\{[^}]*\}\s*$")
INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
LINK_TARGET = re.compile(r"\]\([^)]*\)|<https?://[^>]*>|https?://\S+")
RAW_BLOCK = re.compile(r"<(style|script)\b", re.IGNORECASE)
SLIDE_LEVEL = re.compile(r"^\s*slide-level:\s*(\d)\s*$", re.MULTILINE)


@dataclass
class Tagged:
    path: str  # repo-relative
    line: int
    slide: str
    text: str  # the date as written
    when: datetime.date | None  # the first day the date covers; None when it is not a valid date


def parse_date(text: str, today: datetime.date | None = None) -> tuple[datetime.date | None, str]:
    """The first day `text` covers, or None and why it is refused."""
    match = DATE.match(text)
    if not match:
        return None, f"is not a date: write {FORMS}"
    day, month, year = match.groups()
    if month and month not in MONTHS:
        return None, f"has no month `{month}`: write {FORMS}"
    try:
        when = datetime.date(int(year), MONTHS.index(month) + 1 if month else 1, int(day or 1))
    except ValueError:
        return None, "is not a day on the calendar"
    if day and day.startswith("0"):
        return None, f"has a leading zero: write `{int(day)} {month} {year}`"
    # One day of slack: the check also runs in CI, on a UTC clock.
    if when > (today or datetime.date.today()) + datetime.timedelta(days=1):
        return None, "is in the future"
    if when.year < 1990:
        return None, "is before 1990: an event date, not an \"as of\" date, is left untagged"
    return when, ""


def mask(line: str) -> str:
    """`line` with inline code and link targets blanked, every other character where it was."""
    blank = lambda m: " " * len(m.group(0))  # noqa: E731
    return LINK_TARGET.sub(blank, INLINE_CODE.sub(blank, line))


def prose_lines(text: str) -> list[tuple[int, str, str]]:
    """(line number, slide heading, line) for each line outside code fences, HTML comments and raw blocks."""
    lines = text.splitlines()
    start, slide_level = 0, 2
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() in ("---", "...")), 0)
        level = SLIDE_LEVEL.search("\n".join(lines[1:end]))
        slide_level = int(level.group(1)) if level else 2
        start = end + 1 if end else 0
    out = [(num, "(front matter)", lines[num - 1]) for num in range(1, start + 1)]
    fence: str | None = None
    in_comment = False
    raw_tag: str | None = None
    slide = "(before the first slide)"
    for idx in range(start, len(lines)):
        line = lines[idx]
        if fence:
            stripped = line.strip()
            if stripped and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                fence = None
            continue
        if in_comment:
            in_comment = "-->" not in line
            continue
        if raw_tag:
            if f"</{raw_tag}" in line:
                raw_tag = None
            continue
        code = CODE_FENCE.match(line)
        if code:
            fence = code.group(1)
            continue
        raw = RAW_BLOCK.search(line)
        if raw and f"</{raw.group(1)}" not in line[raw.end():]:
            raw_tag = raw.group(1)
            continue
        if "<!--" in line:
            in_comment = "-->" not in line.split("<!--", 1)[1]
            continue
        heading = HEADING.match(line)
        if heading and len(heading.group(1)) <= slide_level:
            slide = HEADING_ATTRS.sub("", heading.group(2)) or "(untitled slide)"
        out.append((idx + 1, slide, line))
    return out


def scan(rel: str, text: str, phrases: bool = True,
         today: datetime.date | None = None) -> tuple[list[Tagged], list[str]]:
    """Every tagged date in a lesson, and every line the check refuses."""
    tagged: list[Tagged] = []
    problems: list[str] = []
    for num, slide, line in prose_lines(text):
        clean = mask(line)
        if phrases and PHRASE.search(QUOTED_TERM.sub(lambda m: " " * len(m.group(0)), clean)):
            problems.append(f"{rel}:{num}: \"as of\" phrase: tag the date, `[11 Nov 2026]{{.asof}}`, with no "
                            "words and no parentheses, or reword it when it holds no date")
        tags = list(TAG.finditer(clean))
        if len(TAG_MARK.findall(clean)) != len(tags):
            problems.append(f"{rel}:{num}: a `.asof` tag must be written `[date]{{.asof}}`: square brackets "
                            "round the date alone, and no other attribute")
        for tag in tags:
            when, why = parse_date(tag.group(1), today)
            tagged.append(Tagged(rel, num, slide, tag.group(1), when))
            if when is None:
                problems.append(f"{rel}:{num}: `{tag.group(0)}` {why}")
            depth = 0
            for char in clean[:tag.start()]:
                depth = depth + 1 if char == "(" else max(0, depth - 1) if char == ")" else depth
            if depth:
                problems.append(f"{rel}:{num}: `{tag.group(0)}` is inside parentheses, so it would show two "
                                "pairs: move the tag out, or drop the parentheses round it")
    return tagged, problems


def lesson_files() -> list[Path]:
    return sorted(p for p in LESSONS.rglob("*.qmd") if "references" not in p.parts)


def relative(path: Path) -> str:
    return path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.as_posix()


def listing(tagged: list[Tagged]) -> list[str]:
    """One line per tagged date, oldest first, then a count."""
    known = sorted((t for t in tagged if t.when), key=lambda t: (t.when, t.path, t.line))
    rows = known + [t for t in tagged if not t.when]
    width = max((len(f"{t.path}:{t.line}") for t in rows), default=0)
    out = [f"{t.text:>11}  {f'{t.path}:{t.line}':<{width}}  {t.slide}" for t in rows]
    lessons = len({t.path for t in rows})
    span = f"; oldest {known[0].text}, newest {known[-1].text}" if known else ""
    out.append(f"{len(rows)} tagged date(s) in {lessons} lesson(s){span}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List or check the lessons' tagged \"as of\" dates.")
    parser.add_argument("files", nargs="*", type=Path, help="lesson .qmd files (default: every lesson)")
    parser.add_argument("--check", action="store_true", help="check instead of listing")
    parser.add_argument("--all", action="store_true", help="with --check: every lesson")
    parser.add_argument("--tags-only", action="store_true", help="with --check: skip the leftover-phrase rule")
    args = parser.parse_args(argv)
    if args.check and not args.files and not args.all:
        parser.error("--check needs .qmd files or --all")
    files = [f.resolve() for f in args.files] if args.files else lesson_files()

    tagged: list[Tagged] = []
    problems: list[str] = []
    for path in files:
        if not path.exists():
            problems.append(f"{path}:1: file not found")
            continue
        found, refused = scan(relative(path), path.read_text(encoding="utf-8"), phrases=not args.tags_only)
        tagged += found
        problems += refused

    if not args.check:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print("\n".join(listing(tagged)))
        return 0
    if len(problems) > MAX_LINES:
        problems = problems[: MAX_LINES - 1] + [f"... ({len(problems) - MAX_LINES + 1} more)"]
    if problems:
        print("\n".join(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
