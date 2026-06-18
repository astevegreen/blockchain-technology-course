#!/usr/bin/env python3
"""Build a lesson slide index with Reveal anchors."""

from __future__ import annotations

import re
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


def parse_qmd_slides(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    text = path.read_text(encoding="utf-8")
    front, body = read_front_matter(text)
    slides: list[dict[str, Any]] = []
    for match in re.finditer(r"^(##)\s+(.+?)\s*$", body, flags=re.MULTILINE):
        heading = clean_heading(match.group(2))
        if not heading:
            continue
        source_line = body[: match.start()].count("\n") + text[: text.find(body)].count("\n") + 1
        slides.append(
            {
                "number": len(slides) + 1,
                "heading": heading,
                "source_line": source_line,
                "substantive": heading.lower() not in SKIP_HEADINGS,
            }
        )
    return front, slides


def html_slide_ids(qmd_path: Path) -> list[str]:
    html_path = SITE / qmd_path.relative_to(ROOT).with_suffix(".html")
    if not html_path.exists():
        return []
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    sections = soup.select("section.slide.level2[id]")
    return [section.get("id", "") for section in sections]


def fallback_anchor(heading: str, seen: dict[str, int]) -> str:
    slug = heading.lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    if not slug:
        slug = "slide"
    count = seen.get(slug, 0)
    seen[slug] = count + 1
    return slug if count == 0 else f"{slug}-{count}"


def main() -> None:
    lessons: list[dict[str, Any]] = []
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
        ids = html_slide_ids(qmd)
        seen: dict[str, int] = {}
        html_rel = qmd.relative_to(ROOT).with_suffix(".html")
        for idx, slide in enumerate(slides):
            anchor = ids[idx] if idx < len(ids) and ids[idx] else fallback_anchor(slide["heading"], seen)
            slide["anchor"] = anchor
            slide["href"] = f"../{html_rel.as_posix()}#/{anchor}"
        lessons.append(
            {
                "lesson_id": str(front.get("lesson", qmd.stem[:5])),
                "lesson_title": str(front.get("title", qmd.stem)),
                "source_path": qmd.relative_to(ROOT).as_posix(),
                "html_path": html_rel.as_posix(),
                "slides": slides,
            }
        )

    data = {
        "generated_by": "glossary/scripts/build_slide_index.py",
        "lesson_count": len(lessons),
        "lessons": lessons,
    }
    OUT.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(lessons)} lessons")


if __name__ == "__main__":
    main()
