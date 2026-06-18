#!/usr/bin/env python3
"""Find quiz questions whose stem references the lesson/slides directly."""

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PATTERNS = [
    r"\bin this lesson\b",
    r"\bin the lesson\b",
    r"\bthis lesson\b",
    r"\bthe lesson\b",
    r"\bin this slide\b",
    r"\bin the slide\b",
    r"\bin these slides\b",
    r"\bin the slides\b",
    r"\bthis slide\b",
    r"\bthe slide\b",
    r"\bthe slides\b",
    r"\baccording to the (?:lesson|slide|slides|material|reading)\b",
    r"\bas (?:discussed|presented|shown|covered|mentioned|stated|noted) (?:in )?(?:the )?(?:lesson|slide|slides|reading|material)\b",
    r"\bas (?:discussed|presented|shown|covered|mentioned|stated|noted) in class\b",
    r"\bin the (?:reading|material|module|unit|course)\b",
    r"\bcovered in (?:the )?(?:lesson|slides|reading|class|module)\b",
]
COMBINED = re.compile("|".join(PATTERNS), re.IGNORECASE)


def scan_file(path):
    with open(path) as f:
        data = json.load(f)
    hits = []
    for q in data.get("questions", []):
        stem = q.get("question_stem", "") or ""
        m = COMBINED.search(stem)
        if m:
            hits.append((q.get("id", "?"), m.group(0), stem))
    return hits


def main():
    files = sorted(glob.glob(os.path.join(HERE, "*.json")))
    total_q = 0
    total_hits = 0
    files_with_hits = 0
    print(f"Scanning {len(files)} quiz banks for lesson/slide references in question stems...\n")
    for path in files:
        try:
            data = json.load(open(path))
        except Exception as e:
            print(f"!! {os.path.basename(path)}: {e}", file=sys.stderr)
            continue
        n = len(data.get("questions", []))
        total_q += n
        hits = scan_file(path)
        if not hits:
            continue
        files_with_hits += 1
        total_hits += len(hits)
        print(f"=== {os.path.basename(path)}  ({len(hits)}/{n} questions) ===")
        for qid, phrase, stem in hits:
            print(f"  [{qid}] matched: {phrase!r}")
            print(f"      {stem}")
        print()
    print("-" * 60)
    print(f"Files scanned     : {len(files)}")
    print(f"Files with hits   : {files_with_hits}")
    print(f"Total questions   : {total_q}")
    print(f"Flagged questions : {total_hits}")


if __name__ == "__main__":
    main()
