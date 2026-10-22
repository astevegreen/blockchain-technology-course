#!/usr/bin/env python3
"""Lint lesson .qmd files without rendering them.

Usage: python tools/qmd_lint.py <file.qmd>... | --all  [--notes]

Prints nothing and exits 0 when clean. Otherwise prints at most 20 `path:line: message`
lines, most serious first, and exits 1. `--notes` also prints the non-blocking notes
(slides without a speaker-notes block, notes blocks missing one of the four parts).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COURSE = REPO / "blockchain-course"
LESSONS = COURSE / "lessons"
DEFAULT_BIB = LESSONS / "references" / "Blockchain.bib"

sys.path.insert(0, str(COURSE / "glossary" / "scripts"))
from build_slide_index import SKIP_HEADINGS, clean_heading  # noqa: E402

import yaml  # noqa: E402

MAX_LINES = 20
CODE_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*(.*)$")
DIV_FENCE = re.compile(r"^\s{0,3}(:{3,})\s*(.*?)\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
NOTES_DIV = re.compile(r"^\{?\s*\.?notes\b")
NOTE_PARTS = ("**Overall Slide Concept**", "**Key Points**", "**Walkthrough**", "**Sources**")
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
# Pandoc citation: `@key` not preceded by a word character; internal punctuation must be followed by a word character.
CITATION = re.compile(r"(?<![\w@\\])-?@(?:\{([^}\s]+)\}|(\w+(?:[:.#$%&+?<>~/-]\w+)*))")
CROSSREF = re.compile(r"^(fig|tbl|sec|eq|lst|thm|lem|cor|prp|cnj|def|exm|exr|sol|rem)-")
INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
LINK_TARGET = re.compile(r"\]\([^)]*\)|<https?://[^>]*>|https?://\S+")
BIB_KEY = re.compile(r"^@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
RAW_BLOCK = re.compile(r"<(style|script)\b", re.IGNORECASE)


@dataclass
class Findings:
    errors: list[tuple[int, str]] = field(default_factory=list)  # (priority, message)
    notes: list[str] = field(default_factory=list)

    def error(self, priority: int, path: str, line: int, message: str) -> None:
        self.errors.append((priority, f"{path}:{line}: {message}"))


def bib_keys(path: Path, cache: dict[Path, set[str]]) -> set[str]:
    if path not in cache:
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        cache[path] = set(BIB_KEY.findall(text))
    return cache[path]


def split_front_matter(lines: list[str]) -> tuple[str | None, int]:
    """Return the raw YAML front matter and the index of the first body line."""
    if not lines or lines[0].strip() != "---":
        return None, 0
    for idx in range(1, len(lines)):
        if lines[idx].strip() in ("---", "..."):
            return "\n".join(lines[1:idx]), idx + 1
    return None, 0


def check_front_matter(raw: str | None, rel: str, found: Findings) -> dict:
    if raw is None:
        found.error(3, rel, 1, "no YAML front matter (needs title, lesson and format: aci-revealjs)")
        return {}
    try:
        front = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        found.error(3, rel, (mark.line + 2) if mark else 1, f"front matter is not valid YAML: {exc}".splitlines()[0])
        return {}
    for key in ("title", "lesson"):
        if not front.get(key):
            found.error(3, rel, 1, f"front matter has no `{key}`")
    if "aci-revealjs" not in str(front.get("format", "")):
        found.error(3, rel, 1, "front matter `format` must use aci-revealjs")
    return front


def lint_file(path: Path, found: Findings, bib_cache: dict[Path, set[str]]) -> None:
    rel = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.as_posix()
    if not SAFE_NAME.match(path.name):
        found.error(5, rel, 1, "file name may use only letters, digits, '-', '_' and '.'")
    lines = path.read_text(encoding="utf-8").splitlines()
    raw_front, start = split_front_matter(lines)
    front = check_front_matter(raw_front, rel, found)

    slide_level = 2
    fmt = front.get("format")
    if isinstance(fmt, dict) and isinstance(fmt.get("aci-revealjs"), dict):
        slide_level = int(fmt["aci-revealjs"].get("slide-level", 2) or 2)

    bibs = front.get("bibliography") or []
    bibs = [bibs] if isinstance(bibs, str) else list(bibs)
    keys = set(bib_keys(DEFAULT_BIB, bib_cache))
    for bib in bibs:
        keys |= bib_keys((path.parent / str(bib)).resolve(), bib_cache)

    fence: tuple[str, int] | None = None  # (fence chars, line opened)
    comment_start: int | None = None
    raw_tag: str | None = None  # inside a raw <style> or <script> block
    divs: list[tuple[int, str]] = []  # (line opened, attributes)
    slides: list[dict] = []  # visible slide headings and whether a notes block follows

    def hidden() -> bool:
        return any(".content-hidden" in attrs and "when-" not in attrs for _, attrs in divs)

    for idx in range(start, len(lines)):
        line = lines[idx]
        num = idx + 1
        if fence:
            stripped = line.strip()
            if stripped and set(stripped) == {fence[0][0]} and len(stripped) >= len(fence[0]):
                fence = None
            continue
        if comment_start is not None:
            if re.match(r"^\s{0,3}`{3,}\s*\{", line):
                found.error(1, rel, num, "executable cell inside an HTML comment still runs; "
                            "hide the slide with `:::: {.content-hidden}` instead")
            elif HEADING.match(line) and len(HEADING.match(line).group(1)) <= slide_level:
                found.error(1, rel, num, "slide heading inside an HTML comment; "
                            "hide the slide with `:::: {.content-hidden}` instead")
            if "-->" in line:
                comment_start = None
            continue
        if raw_tag:
            if f"</{raw_tag}" in line:
                raw_tag = None
            continue
        code = CODE_FENCE.match(line)
        if code:
            fence = (code.group(1), num)
            continue
        raw = RAW_BLOCK.search(line)
        if raw and f"</{raw.group(1)}" not in line[raw.end():]:
            raw_tag = raw.group(1)
            continue
        if "<!--" in line:
            if "-->" not in line.split("<!--", 1)[1]:
                comment_start = num
            continue
        div = DIV_FENCE.match(line)
        if div:
            attrs = div.group(2).strip(":").strip()
            if attrs:
                if NOTES_DIV.match(attrs) and slides and not hidden():
                    slides[-1]["notes"] = num
                divs.append((num, attrs))
            elif divs:
                divs.pop()
            else:
                found.error(0, rel, num, "closing ':::' has no matching opening div")
            continue
        heading = HEADING.match(line)
        if heading and len(heading.group(1)) <= slide_level:
            if hidden():
                continue
            if divs:
                found.error(2, rel, num, f"slide heading inside the div opened at line {divs[-1][0]} "
                            f"({divs[-1][1]}); close the div before the heading")
                divs.clear()  # report the unclosed div once, not again at every later slide
                continue
            if len(heading.group(1)) == slide_level or (len(heading.group(1)) == 2 and slide_level == 3):
                slides.append({"line": num, "heading": clean_heading(heading.group(2)), "notes": None})
            continue
        if not hidden():
            text = LINK_TARGET.sub(" ", INLINE_CODE.sub(" ", line))
            for match in CITATION.finditer(text):
                key = match.group(1) or match.group(2)
                if not CROSSREF.match(key) and key not in keys:
                    found.error(4, rel, num, f"citation @{key} is not in {DEFAULT_BIB.name}"
                                + (" or the lesson's other bibliographies" if len(bibs) > 1 else ""))

    if fence:
        found.error(0, rel, fence[1], f"code fence {fence[0]} is never closed")
    if comment_start is not None:
        found.error(0, rel, comment_start, "HTML comment is never closed")
    for opened, attrs in divs:
        found.error(0, rel, opened, f"div {attrs} is never closed")

    for slide in slides:
        if slide["heading"].lower() in SKIP_HEADINGS or not slide["heading"]:
            continue
        if slide["notes"] is None:
            found.notes.append(f"{rel}:{slide['line']}: slide '{slide['heading']}' has no speaker-notes block")
            continue
        block = notes_text(lines, slide["notes"])
        missing = [part.strip("*") for part in NOTE_PARTS if part not in block]
        if missing:
            found.notes.append(f"{rel}:{slide['notes']}: notes for '{slide['heading']}' lack {', '.join(missing)}")


def notes_text(lines: list[str], opened: int) -> str:
    """Text of the notes div opened at 1-based line `opened`, up to its closing fence."""
    depth = 0
    out = []
    for line in lines[opened - 1:]:
        div = DIV_FENCE.match(line)
        if div:
            depth += 1 if div.group(2).strip(":").strip() else -1
            if depth == 0:
                break
            continue
        out.append(line)
    return "\n".join(out)


def lesson_files() -> list[Path]:
    return sorted(p for p in LESSONS.rglob("*.qmd") if "references" not in p.parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint lesson .qmd files without rendering them.")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--all", action="store_true", help="lint every lesson")
    parser.add_argument("--notes", action="store_true", help="also print non-blocking notes")
    args = parser.parse_args(argv)
    files = lesson_files() if args.all else [f.resolve() for f in args.files]
    if not files:
        parser.error("give .qmd files or --all")

    found = Findings()
    bib_cache: dict[Path, set[str]] = {}
    for path in files:
        if not path.exists():
            found.error(0, str(path), 1, "file not found")
            continue
        lint_file(path, found, bib_cache)

    out = [message for _, message in sorted(found.errors, key=lambda e: e[0])]
    if len(out) > MAX_LINES:
        out = out[: MAX_LINES - 1] + [f"... ({len(out) - MAX_LINES + 1} more)"]
    if args.notes and found.notes:
        out += [f"note: {n}" for n in found.notes] + [f"{len(found.notes)} note(s) (non-blocking)"]
    if out:
        print("\n".join(out))
    return 1 if found.errors else 0


if __name__ == "__main__":
    sys.exit(main())
