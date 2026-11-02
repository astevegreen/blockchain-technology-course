#!/usr/bin/env python3
"""Verify the pretest banks (weeks 1 and 2): blueprint, answer keys, visible sources, option lengths."""

import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from verify_single_quiz import check_single_quiz  # noqa: E402

# docs/build-spec.md, "Pretest blueprint": day -> {Role Concepts Order: skill}.
BLUEPRINT_WEEK1 = {
    1: {1: "familiarity", 2: "familiarity", 3: "familiarity", 4: "familiarity",
        5: "familiarity", 41: "working", 42: "familiarity"},
    2: {},
    3: {18: "working", 46: "working"},
    4: {6: "familiarity", 10: "working", 12: "working"},
    5: {31: "familiarity", 38: "familiarity", 39: "familiarity", 48: "familiarity", 49: "familiarity"},
}
BLUEPRINT_WEEK2 = {
    6: {7: "working", 8: "working", 20: "working", 21: "familiarity", 25: "familiarity",
        27: "familiarity", 28: "working", 40: "familiarity", 45: "working"},
    7: {9: "working", 11: "familiarity", 23: "familiarity"},
    8: {13: "familiarity", 14: "familiarity", 15: "familiarity", 16: "familiarity", 17: "familiarity",
        19: "familiarity", 22: "familiarity", 24: "familiarity", 47: "familiarity"},
    9: {26: "familiarity", 29: "familiarity", 30: "familiarity", 37: "working"},
}
BANKS = [
    (HERE / "pretest_week1-quiz-bank.json", BLUEPRINT_WEEK1),
    (HERE / "pretest_week2-quiz-bank.json", BLUEPRINT_WEEK2),
]
TYPE_FOR_SKILL = {"familiarity": "multiple_choice", "working": "written"}


def visible_headings(path: Path) -> set[str]:
    """Slide headings outside every content-hidden fence (fences nest, so track a stack)."""
    stack, code, out = [], False, set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            code = not code
            continue
        if code:
            continue
        m = re.match(r"^(:{3,})\s*(.*?)\s*$", line)
        if m:
            if m.group(2):
                stack.append("content-hidden" in m.group(2))
            elif stack:
                stack.pop()
            continue
        if line.startswith("## ") and not any(stack):
            out.add(re.sub(r"\s*\{.*\}\s*$", "", line[3:]).strip())
    return out


def check_bank(bank_path: Path, blueprint: dict, cache: dict[Path, set[str]]) -> list[str]:
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    questions = bank["questions"]
    errors = []

    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        errors.append("duplicate question ids")
    listed = [qid for s in bank["hierarchy"]["sections"] for lec in s["lectures"] for qid in lec["question_ids"]]
    if sorted(listed) != sorted(ids):
        errors.append("hierarchy does not list every question exactly once")

    for day, concepts in blueprint.items():
        got = {q["concept"]["order"]: q for q in questions if q["day"] == day}
        if set(got) != set(concepts):
            errors.append(f"day {day}: concepts {sorted(got)} != blueprint {sorted(concepts)}")
        if sorted(bank["metadata"]["days"][str(day)]) != sorted(q["id"] for q in got.values()):
            errors.append(f"day {day}: metadata.days does not match the items")
        for order, skill in concepts.items():
            q = got.get(order)
            if not q:
                continue
            if q["concept"]["skill"] != skill or q["question_type"] != TYPE_FOR_SKILL[skill]:
                errors.append(f"{q['id']}: concept {order} is {skill}, so it must be {TYPE_FOR_SKILL[skill]}")
    if len(questions) != sum(len(c) for c in blueprint.values()):
        errors.append(f"{len(questions)} items; the blueprint has {sum(len(c) for c in blueprint.values())}")

    for q in questions:
        if q["question_type"] == "written" and not q.get("answer_key"):
            errors.append(f"{q['id']}: written item has no answer_key")
        if not q.get("post_test"):
            errors.append(f"{q['id']}: no post_test note")
        primary = q["specific_source"]
        if {"lesson": primary["lesson"], "slide": primary["reading"]} not in q["sources"]:
            errors.append(f"{q['id']}: specific_source is not one of its sources")
        for src in q["sources"]:
            path = REPO / src["lesson"]
            if not path.exists():
                errors.append(f"{q['id']}: no lesson {src['lesson']}")
                continue
            if path not in cache:
                cache[path] = visible_headings(path)
            if src["slide"] not in cache[path]:
                errors.append(f"{q['id']}: no visible slide '{src['slide']}' in {path.name}")

    # Option lengths: the course rule for multiple choice, run on the multiple-choice items only.
    mc = {**bank, "questions": [q for q in questions if q["question_type"] == "multiple_choice"]}
    with tempfile.TemporaryDirectory() as tmp:
        mc_file = Path(tmp) / f"{bank_path.stem}_mc.json"
        mc_file.write_text(json.dumps(mc), encoding="utf-8")
        if check_single_quiz(mc_file) != 0:
            errors.append("multiple-choice option lengths fail verify_single_quiz")
    return [f"{bank_path.name}: {e}" for e in errors]


def main() -> int:
    errors, cache, seen = [], {}, set()
    for bank_path, blueprint in BANKS:
        errors += check_bank(bank_path, blueprint, cache)
        ids = {q["id"] for q in json.loads(bank_path.read_text(encoding="utf-8"))["questions"]}
        if seen & ids:
            errors.append(f"{bank_path.name}: ids {sorted(seen & ids)} are used in another pretest bank")
        seen |= ids

    for e in errors:
        print(f"FAIL: {e}")
    print("Pretest OK." if not errors else f"Pretest: {len(errors)} failure(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
