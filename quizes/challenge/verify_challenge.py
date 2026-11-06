#!/usr/bin/env python3
"""Verify the challenge bank: item count and that every traced slide exists and is visible."""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
LESSONS = REPO / "blockchain-course" / "lessons"
sys.path.insert(0, str(HERE.parent / "pretest"))
from verify_pretest import visible_headings  # noqa: E402

BANK = HERE / "challenge-bank.md"


def main() -> int:
    errors, items, cache = [], 0, {}
    current = None
    for line in BANK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (c\d+) ", line)
        if m:
            current, items = m.group(1), items + 1
            continue
        if not line.startswith("**Traces to:**"):
            continue
        refs = re.findall(r'(\d\d-[A-Z]{2}) "([^"]+)"', line)
        if not refs:
            errors.append(f"{current}: Traces to line names no slide")
        for code, heading in refs:
            if code not in cache:
                files = sorted(LESSONS.glob(f"*/{code}-*.qmd"))
                cache[code] = visible_headings(files[0]) if len(files) == 1 else None
            if cache[code] is None:
                errors.append(f"{current}: no single lesson file for {code}")
            elif heading not in cache[code]:
                errors.append(f'{current}: {code} has no visible slide "{heading}"')
    if not 10 <= items <= 17:
        errors.append(f"{items} items; the build spec asks for 10 to 17")
    for e in errors:
        print(e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
