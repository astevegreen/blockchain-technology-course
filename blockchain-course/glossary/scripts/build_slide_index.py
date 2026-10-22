#!/usr/bin/env python3
"""Build a lesson slide index with Reveal anchors.

Run `--check` to compare a fresh build with the committed index without writing it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "lessons"
SITE = ROOT / "_site"
OUT = ROOT / "glossary" / "slide-index.yml"

SECTION_ORDER = {
    "introduction": 1,
    "primitives": 2,
    "distributed_primitives": 3,
    "consensus_primitives": 4,
    "permissioned_ledger": 5,
    "bitcoin": 6,
    "ethereum": 7,
    "forensics": 8,
    "conclusion": 9,
}

SKIP_HEADINGS = {
    "agenda",
    "objectives",
    "references",
    "reference",
    "discussion",
    "key sources",
}


def read_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 4 :]
    return yaml.safe_load(raw) or {}, body


def clean_heading(raw: str) -> str:
    raw = re.sub(r"\s+\{[^}]*\}\s*$", "", raw)
    raw = re.sub(r"`([^`]*)`", r"\1", raw)
    raw = re.sub(r"\*\*([^*]*)\*\*", r"\1", raw)
    raw = re.sub(r"\*([^*]*)\*", r"\1", raw)
    raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\s+", " ", raw).strip()


CODE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
DIV_FENCE = re.compile(r"^\s*(:{3,})\s*(.*?)\s*$")
SLIDE_HEADING = re.compile(r"^##\s+(.+?)\s*$")
EXPLICIT_ID = re.compile(r"\{[^}]*#([\w.:-]+)[^}]*\}\s*$")


def visible_headings(body: str) -> list[tuple[int, str]]:
    """Return (body line index, raw heading) for each `## ` line that renders as a slide.

    Skips headings inside code fences, HTML comments and `.content-hidden` divs.
    """
    found: list[tuple[int, str]] = []
    fence: str | None = None
    in_comment = False
    divs: list[bool] = []  # one entry per open div: True when it hides its content
    for idx, line in enumerate(body.split("\n")):
        if fence:
            stripped = line.strip()
            if stripped.startswith(fence) and set(stripped) == {fence[0]}:
                fence = None
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        code = CODE_FENCE.match(line)
        if code:
            fence = code.group(1)
            continue
        if "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            in_comment = True
            continue
        div = DIV_FENCE.match(line)
        if div:
            if div.group(2):
                divs.append(".content-hidden" in div.group(2) and "when-" not in div.group(2))
            elif divs:
                divs.pop()
            continue
        heading = SLIDE_HEADING.match(line)
        if heading and not any(divs):
            found.append((idx, heading.group(1)))
    return found


def parse_qmd_slides(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    text = path.read_text(encoding="utf-8")
    front, body = read_front_matter(text)
    body_offset = text[: text.find(body)].count("\n")
    slides: list[dict[str, Any]] = []
    for idx, raw in visible_headings(body):
        heading = clean_heading(raw)
        if not heading:
            continue
        explicit = EXPLICIT_ID.search(raw)
        slides.append(
            {
                "number": len(slides) + 1,
                "heading": heading,
                "source_line": body_offset + idx + 1,
                "substantive": heading.lower() not in SKIP_HEADINGS,
                "_explicit_id": explicit.group(1) if explicit else None,
            }
        )
    return front, slides


def match_key(heading: str) -> str:
    """Compare source and rendered headings on letters and digits only (Pandoc smartens quotes and dashes).

    A trailing `{...}` attribute block is dropped even when no space precedes it (`Title{.smaller}`).
    """
    heading = re.sub(r"\{[^}]*\}\s*$", "", heading)
    return re.sub(r"[\W_]+", "", heading.lower())


def html_slides(qmd_path: Path) -> list[tuple[str, str]] | None:
    """Return (id, heading text) per rendered level-2 slide, or None when the lesson has no HTML in _site."""
    html_path = SITE / qmd_path.relative_to(ROOT).with_suffix(".html")
    if not html_path.exists():
        return None
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    slides = []
    for section in soup.select("section.slide.level2[id]"):
        h2 = section.find("h2")
        slides.append((section.get("id", ""), h2.get_text(" ", strip=True) if h2 else ""))
    return slides


def assign_anchors(slides: list[dict[str, Any]], rendered: list[tuple[str, str]]) -> list[str]:
    """Pair each source slide with its rendered section by explicit id, then by heading text in order.

    Returns the headings that had no rendered match and fell back to a generated slug.
    """
    ids = {section_id for section_id, _ in rendered}
    used: set[int] = set()
    seen: dict[str, int] = {}
    fallbacks: list[str] = []
    cursor = 0
    for slide in slides:
        explicit = slide.pop("_explicit_id")
        anchor = None
        if explicit in ids:
            anchor = explicit
            used.update(i for i, (section_id, _) in enumerate(rendered) if section_id == explicit)
        else:
            key = match_key(slide["heading"])
            candidates = [i for i, (_, text) in enumerate(rendered) if i not in used and match_key(text) == key]
            after = [i for i in candidates if i >= cursor]
            pick = (after or candidates or [None])[0]
            if pick is not None:
                used.add(pick)
                cursor = pick + 1
                anchor = rendered[pick][0]
        if anchor is None:
            anchor = fallback_anchor(slide["heading"], seen)
            fallbacks.append(slide["heading"])
        slide["anchor"] = anchor
    return fallbacks


def fallback_anchor(heading: str, seen: dict[str, int]) -> str:
    slug = heading.lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    if not slug:
        slug = "slide"
    count = seen.get(slug, 0)
    seen[slug] = count + 1
    return slug if count == 0 else f"{slug}-{count}"


def build() -> tuple[dict[str, Any], list[str]]:
    """Build the index in memory; return it with one warning line per unrendered lesson or unmatched slide."""
    lessons: list[dict[str, Any]] = []
    warnings: list[str] = []
    qmds = sorted(
        LESSONS.rglob("*.qmd"),
        key=lambda path: (
            SECTION_ORDER.get(path.relative_to(LESSONS).parts[0], 999),
            path.name,
        ),
    )
    for qmd in qmds:
        if "references" in qmd.parts:
            continue
        front, slides = parse_qmd_slides(qmd)
        if not slides:
            continue
        source_rel = qmd.relative_to(ROOT).as_posix()
        rendered = html_slides(qmd)
        if rendered is None:
            warnings.append(f"{source_rel}: not rendered in _site; anchors guessed from headings")
            rendered = []
        for heading in assign_anchors(slides, rendered):
            if rendered:
                warnings.append(f"{source_rel}: no rendered slide matches '{heading}'; anchor guessed")
        html_rel = qmd.relative_to(ROOT).with_suffix(".html")
        for slide in slides:
            slide["href"] = f"../{html_rel.as_posix()}#/{slide['anchor']}"
        lessons.append(
            {
                "lesson_id": str(front.get("lesson", qmd.stem[:5])),
                "lesson_title": str(front.get("title", qmd.stem)),
                "source_path": source_rel,
                "html_path": html_rel.as_posix(),
                "slides": slides,
            }
        )

    data = {
        "generated_by": "glossary/scripts/build_slide_index.py",
        "lesson_count": len(lessons),
        "lessons": lessons,
    }
    return data, warnings


def stale_lessons(fresh: dict[str, Any], committed: dict[str, Any]) -> list[str]:
    """Name each lesson whose entry differs between a fresh build and the committed index."""
    old = {lesson.get("source_path"): lesson for lesson in committed.get("lessons", []) or []}
    new = {lesson.get("source_path"): lesson for lesson in fresh.get("lessons", [])}
    stale = []
    for path in sorted(set(old) | set(new)):
        if path not in new:
            stale.append(f"{path}: in the index but no longer a lesson")
        elif path not in old:
            stale.append(f"{path}: missing from the index")
        elif old[path] != new[path]:
            old_slides = [(s.get("heading"), s.get("anchor")) for s in old[path].get("slides", [])]
            new_slides = [(s["heading"], s["anchor"]) for s in new[path]["slides"]]
            added = [f"'{h}' -> #/{a}" for h, a in new_slides if (h, a) not in old_slides]
            removed = [f"'{h}' -> #/{a}" for h, a in old_slides if (h, a) not in new_slides]
            if added:
                detail = f" (now {added[0]})"
            elif removed:
                detail = f" (no longer {removed[0]})"
            else:
                detail = " (slide numbers or lines moved)"
            stale.append(f"{path}: slide entries differ{detail}")
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare with glossary/slide-index.yml; exit 1 when stale")
    args = parser.parse_args()

    data, warnings = build()
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if args.check:
        committed = yaml.safe_load(OUT.read_text(encoding="utf-8")) or {} if OUT.exists() else {}
        stale = stale_lessons(data, committed)
        if not stale:
            return 0
        print(f"{OUT.relative_to(ROOT).as_posix()} is stale in {len(stale)} lesson(s):")
        for line in stale[:5]:
            print(f"  {line}")
        print("Fix: render the changed lessons, then rerun the glossary pipeline (glossary/README.md).")
        return 1

    OUT.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(data['lessons'])} lessons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
