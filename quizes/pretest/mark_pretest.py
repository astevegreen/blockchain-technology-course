#!/usr/bin/env python3
"""Mark the students' pretest replies and say, day by day, who is offered the lab's problem.

  python quizes/pretest/mark_pretest.py <folder or files>... [--out results.md] [--no-ask]

Students take the pretest on the course site (blockchain-course/assets/labs/pretest/) and email their answers:
a block between "----- BEGIN PRETEST ANSWERS -----" and "----- END PRETEST ANSWERS -----". Save each reply into
one folder as a .txt or .eml file (in Outlook: File > Save As, "Text Only"), or paste every reply into one text
file. This script reads every block in them.

Multiple-choice items mark themselves. For a written item the script shows the student's answer beside the
answer key and asks whether it states every point (README.md, "How an instructor uses it"); each decision is kept in
pretest-marks.json in the first folder given, so a second run asks nothing already decided. --no-ask leaves
written items unmarked ("?") instead.

The lab entry rule (README.md): a student who got every gate item for a day right is offered that day's problem;
everyone else, and anyone with no pretest, starts at the worked example. Week 1 lists its gates in
metadata.lab_gates; in week 2 every item of a day gates it.
"""

from __future__ import annotations

import argparse
import email
import email.policy
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_page  # noqa: E402

BEGIN = "----- BEGIN PRETEST ANSWERS -----"
END = "----- END PRETEST ANSWERS -----"
ITEM_LINE = re.compile(r"^(q\d+):\s?(.*)$")
FIELD_LINE = re.compile(r"^(form|name|answered):\s?(.*)$")
QUOTE = re.compile(r"^>(?: ?>)* ?")
MARKS_FILE = "pretest-marks.json"


@dataclass
class Reply:
    name: str
    form: str
    source: str
    answers: dict[str, str] = field(default_factory=dict)


def unquote(line: str) -> str:
    """A line as the student's page wrote it, with any reply quoting ("> ") taken off."""
    return QUOTE.sub("", line.rstrip("\r"))


def parse(text: str, source: str = "") -> list[Reply]:
    """Every answers block in `text`. Tolerates quoting and a mail program wrapping long lines."""
    replies, current, item = [], None, None
    for raw in text.splitlines():
        line = unquote(raw)
        if line.strip() == BEGIN:
            current, item = Reply(name="", form="", source=source), None
            continue
        if current is None:
            continue
        if line.strip() == END:
            current.answers = {k: v.strip() for k, v in current.answers.items()}
            current.name = current.name if current.name and not current.name.startswith("(no name") else f"(no name: {source})"
            replies.append(current)
            current = None
            continue
        head = ITEM_LINE.match(line)
        if head:
            item = head.group(1)
            current.answers[item] = "" if head.group(2).strip() == "-" else head.group(2).strip()
            continue
        meta = FIELD_LINE.match(line)
        if meta and item is None:
            if meta.group(1) in ("form", "name"):
                setattr(current, meta.group(1), meta.group(2).strip())
            continue
        if item is not None:  # a written answer's next line, or a long line the mail program wrapped
            body = line[4:] if line.startswith("    ") else line
            joined = current.answers[item]
            current.answers[item] = f"{joined}\n{body}" if joined else body
    return replies


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".eml":
        msg = email.message_from_bytes(path.read_bytes(), policy=email.policy.default)
        parts = [p for p in msg.walk() if p.get_content_type() in ("text/plain", "text/html")]
        texts = []
        for part in sorted(parts, key=lambda p: p.get_content_type() != "text/plain"):
            content = part.get_content()
            if part.get_content_type() == "text/html":
                content = re.sub(r"<br\s*/?>|</p>|</div>", "\n", content, flags=re.I)
                content = re.sub(r"<[^>]+>", "", content).replace("&nbsp;", " ").replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            texts.append(content)
            if BEGIN in content:
                break
        return "\n".join(texts)
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        if BEGIN in text or enc == "cp1252":
            return text
    return ""


def gather(paths: list[Path]) -> tuple[list[Reply], list[str]]:
    files, notes = [], []
    for p in paths:
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.is_file() and f.suffix.lower() in (".txt", ".eml", ".md"))
            skipped = sorted(f.name for f in p.iterdir() if f.suffix.lower() == ".msg")
            if skipped:
                notes.append(f"skipped {len(skipped)} .msg file(s): in Outlook use File > Save As, \"Text Only\"")
        elif p.is_file():
            files.append(p)
        else:
            notes.append(f"{p}: not found")
    replies = []
    for f in files:
        found = parse(read_text(f), f.name)
        if not found and f.suffix.lower() != ".md":
            notes.append(f"{f.name}: no answers block (is the reply's text all there?)")
        replies += found
    by_name: dict[str, Reply] = {}
    for r in replies:
        key = r.name.casefold()
        if key in by_name:
            notes.append(f"{r.name}: two replies ({by_name[key].source}, {r.source}); using {r.source}")
        by_name[key] = r
    return list(by_name.values()), notes


@dataclass
class Bank:
    items: dict[str, dict]             # id -> bank item
    week: dict[str, int]               # id -> week
    gates: dict[int, list[str]]        # day -> gate item ids
    days: dict[int, list[str]]         # day -> every item id
    form: str


def load_bank() -> Bank:
    banks = build_page.load_banks()
    items, week, gates, days = {}, {}, {}, {}
    for w, bank in banks.items():
        meta = bank["metadata"]
        for q in bank["questions"]:
            items[q["id"]], week[q["id"]] = q, w
        for day, ids in meta["days"].items():
            days[int(day)] = list(ids)
            gates[int(day)] = list(meta.get("lab_gates", {}).get(day, ids))
    return Bank(items, week, gates, days, build_page.form_id(build_page.page_items(banks)))


def answer_digest(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()[:12]


def mark_mc(q: dict, answer: str) -> bool | None:
    """True, False, or None when the answer matches no option in today's bank (the bank changed since)."""
    if not answer:
        return False
    option = re.findall(r"[0-9a-f]{6}", answer.lower())
    if not option:
        return None
    texts = [q["correct_answer"], *q["incorrect_answers"]]
    ids = {build_page.option_id(q["id"], t): t == q["correct_answer"] for t in texts}
    return ids.get(option[-1])


def ask_written(reply: Reply, q: dict, answer: str) -> bool | None:
    print("\n" + "=" * 72)
    print(f"{reply.name}: {q['id']} (day {q['day']}, {q['concept']['name']})")
    print("-" * 72)
    print(answer)
    print("-" * 72)
    print("Right only if it states every point:")
    for point in q["answer_key"]:
        print(f"  - {point}")
    while True:
        try:
            got = input("Every point stated? [y]es / [n]o / [s]kip: ").strip().lower()
        except EOFError:
            return None
        if got in ("y", "yes"):
            return True
        if got in ("n", "no"):
            return False
        if got in ("s", "skip", ""):
            return None


def mark(replies: list[Reply], bank: Bank, decisions: dict[str, bool], ask: bool,
         notes: list[str]) -> dict[str, dict[str, bool | None]]:
    """name -> item id -> True / False / None (unmarked). Items a reply does not hold are left out."""
    results = {}
    for r in replies:
        if r.form and r.form != bank.form:
            notes.append(f"{r.name}: answered an older form ({r.form}; today's is {bank.form}): "
                         "items whose options changed since show as unmarked")
        marks = {}
        for qid, answer in r.answers.items():
            q = bank.items.get(qid)
            if q is None:
                notes.append(f"{r.name}: {qid} is not in today's banks; ignored")
                continue
            if q["question_type"] == "multiple_choice":
                marks[qid] = mark_mc(q, answer)
                continue
            if not answer.strip():
                marks[qid] = False
                continue
            key = f"{r.name.casefold()}|{qid}|{answer_digest(answer)}"
            if key not in decisions and ask:
                got = ask_written(r, q, answer)
                if got is not None:
                    decisions[key] = got
            marks[qid] = decisions.get(key)
        results[r.name] = marks
    return results


def entry(marks: dict[str, bool | None], gate: list[str]) -> str:
    """Problem, worked example, "?" (a gate item unmarked) or "-" (the reply holds no item of that day)."""
    held = [marks[g] for g in gate if g in marks]
    if not held:
        return "-"
    if len(held) < len(gate) or any(m is False for m in held):
        return "worked example"
    if any(m is None for m in held):
        return "?"
    return "problem"


def table(results: dict[str, dict[str, bool | None]], bank: Bank) -> str:
    days = sorted(d for d in bank.days if any(any(q in m for q in bank.days[d]) for m in results.values()))
    lines = ["# Pretest: where each student starts each day's lab", "",
             "**problem**: got every gate item right, so offered the day's problem. **worked example**: everyone "
             "else (any student may still choose it). **?**: a gate item is not marked yet (a written item still to judge, or an option changed since the student answered). **-**: did "
             "not answer that day's items. Readiness: the day's other items, right out of asked, for your eye only.",
             "", "| Student | " + " | ".join(f"Day {d}" for d in days) + " |",
             "| --- | " + " | ".join("---" for _ in days) + " |"]
    for name in sorted(results, key=str.casefold):
        m = results[name]
        cells = []
        for d in days:
            cell = entry(m, bank.gates[d])
            ready = [q for q in bank.days[d] if q not in bank.gates[d] and q in m]
            if ready:
                cell += f" (readiness {sum(m[q] is True for q in ready)}/{len(ready)})"
            cells.append(cell)
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    unmarked = sorted(f"{n} {q}" for n, m in results.items() for q, v in m.items() if v is None)
    if unmarked:
        lines += ["", "Not marked yet: " + ", ".join(unmarked) + ". Run again to mark them."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path, help="folders of saved replies, or reply files")
    parser.add_argument("--out", type=Path, help="also write the table to this Markdown file")
    parser.add_argument("--no-ask", action="store_true", help="leave written items unmarked instead of asking")
    args = parser.parse_args(argv)

    replies, notes = gather(args.paths)
    if not replies:
        for n in notes:
            print(f"note: {n}")
        print("No pretest answers found.")
        return 1
    home = next((p for p in args.paths if p.is_dir()), args.paths[0].parent)
    marks_path = home / MARKS_FILE
    decisions = json.loads(marks_path.read_text(encoding="utf-8")) if marks_path.is_file() else {}
    results = mark(replies, load_bank(), decisions, not args.no_ask, notes)
    if decisions:
        marks_path.write_text(json.dumps(decisions, indent=1, sort_keys=True), encoding="utf-8")
    report = table(results, load_bank())
    print("\n" + report)
    for n in notes:
        print(f"note: {n}")
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
