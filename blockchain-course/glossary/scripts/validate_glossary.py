#!/usr/bin/env python3
"""Validate glossary data and source links."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = ROOT / "glossary"
TERMS = GLOSSARY / "terms.yml"
SLIDE_INDEX = GLOSSARY / "slide-index.yml"


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    errors: list[str] = []
    if not TERMS.exists():
        errors.append("Missing glossary/terms.yml")
    if not SLIDE_INDEX.exists():
        errors.append("Missing glossary/slide-index.yml")
    if errors:
        print("\n".join(errors))
        return 1

    slide_data = load(SLIDE_INDEX)
    valid_hrefs = {
        slide.get("href")
        for lesson in slide_data.get("lessons", [])
        for slide in lesson.get("slides", [])
    }
    terms = load(TERMS).get("terms", []) or []
    seen: set[str] = set()

    for idx, term in enumerate(terms, start=1):
        display = str(term.get("display", "")).strip()
        definition = str(term.get("definition", "")).strip()
        source = term.get("source", {}) or {}
        href = source.get("href")
        if not display:
            errors.append(f"Term {idx} has no display value")
        if display.lower() in seen:
            errors.append(f"Duplicate display term: {display}")
        seen.add(display.lower())
        if not definition:
            errors.append(f"{display}: missing definition")
        if href not in valid_hrefs:
            errors.append(f"{display}: source href is not in slide-index.yml: {href}")
        if not source.get("lesson_id") or not source.get("slide_heading"):
            errors.append(f"{display}: incomplete source metadata")

    if errors:
        print("Glossary validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Glossary validation passed: {len(terms)} terms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
