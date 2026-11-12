#!/usr/bin/env python3
"""Write docs/alignment-map.md: for each Role Concept, where it is taught, practised, recalled and tested.

    python tools/alignment_map.py            write the map
    python tools/alignment_map.py --stdout   print it instead

Inputs, all read fresh each run:
- the concepts and their test items: quizes/posttest/ and quizes/pretest/ (each item names its concept);
- what is taught on which day: the day tables in quizes/run-sheet/RUN_SHEET.md, read slide by slide, hidden slides
  and speaker notes left out;
- what a lab asks: the numbered questions on each day's lab page, and the graded point the run sheet names;
- what the daily quizzes recall: quizes/quiz_json/daily_*.json and the week-one check;
- which words signal a concept: tools/alignment_terms.yml (tune it there).
Word matching finds where a concept is likely covered, not proof that it is taught well: read the slides it lists.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
TERMS = REPO / "tools" / "alignment_terms.yml"
RUN_SHEET = REPO / "quizes" / "run-sheet" / "RUN_SHEET.md"
POSTTEST = REPO / "quizes" / "posttest" / "posttest_day10-quiz-bank.json"
PRETEST = REPO / "quizes" / "pretest"
QUIZ_JSON = REPO / "quizes" / "quiz_json"
OUT = REPO / "docs" / "alignment-map.md"
SLOTS = "①②③"


# ---------------------------------------------------------------- matching

def compile_terms(terms: list[str]) -> list[re.Pattern]:
    """Whole-word patterns; a term in capitals and digits only matches in capitals only."""
    out = []
    for t in terms:
        t = " ".join(str(t).split())
        flags = 0 if re.fullmatch(r"[A-Z0-9&]{2,}s?", t) else re.IGNORECASE
        out.append(re.compile(rf"(?<!\w)(?:{t})(?!\w)", flags))
    return out


def hits(patterns: list[re.Pattern], text: str) -> int:
    return sum(len(p.findall(text)) for p in patterns)


# ---------------------------------------------------------------- slides

@dataclass
class Slide:
    lesson: str  # path from the repo root
    title: str
    body: str


def read_slides(path: Path) -> list[Slide]:
    """Visible slides: `## ` headings outside code, outside .content-hidden fences, without their speaker notes."""
    rel = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.as_posix()
    slides: list[Slide] = []
    stack: list[str] = []  # the attributes of each open ::: fence
    code = False
    cur: Slide | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            code = not code
            if cur and not hidden(stack) and not notes(stack):
                cur.body += line + "\n"
            continue
        m = None if code else re.match(r"^(:{3,})\s*(.*?)\s*$", line)
        if m:
            if m.group(2):
                stack.append(m.group(2))
            elif stack:
                stack.pop()
            continue
        if not code and line.startswith("## "):
            cur = None
            if not hidden(stack):
                cur = Slide(rel, re.sub(r"\s*\{.*\}\s*$", "", line[3:]).strip(), "")
                slides.append(cur)
            continue
        if not code and line.startswith("# "):
            cur = None
            continue
        if cur and not hidden(stack) and not notes(stack):
            cur.body += line + "\n"
    return slides


def hidden(stack: list[str]) -> bool:
    return any("content-hidden" in a for a in stack)


def notes(stack: list[str]) -> bool:
    return any(".notes" in a for a in stack)


# ---------------------------------------------------------------- the run sheet

@dataclass
class Day:
    number: int
    lessons: list[tuple[str, str]] = field(default_factory=list)  # (slot, path)
    labs: list[str] = field(default_factory=list)  # lab pages, from the repo root
    graded: list[int] = field(default_factory=list)  # graded question numbers
    graded_note: str = ""


def lab_page(url: str) -> str | None:
    """`/labs/tron/lab/d9/` -> dynamic-labs/tron/static/lab/d9/index.html, wherever the lab keeps its page."""
    parts = [p for p in url.strip("/").split("/") if p][1:]
    if not parts:
        return None
    lab, sub = parts[0], [p for p in parts[1:] if p != "lab"]
    for base in ("gateway/static/lab", "static/lab"):
        cand = REPO / "dynamic-labs" / lab / base / Path(*sub) / "index.html" if sub else \
            REPO / "dynamic-labs" / lab / base / "index.html"
        if cand.exists():
            return cand.relative_to(REPO).as_posix()
    return None


def read_run_sheet(text: str) -> dict[int, Day]:
    days: dict[int, Day] = {}
    for m in re.finditer(r"^## Day (\d+):.*?(?=^## |\Z)", text, re.S | re.M):
        day = Day(int(m.group(1)))
        block = m.group(0)
        for line in block.splitlines():
            row = re.match(r"^\|\s*([①②③]|0845)\s*\|.*`(blockchain-course/lessons/[^`]+\.qmd)`", line)
            if row:
                day.lessons.append(("W" if row.group(1) == "0845" else row.group(1), row.group(2)))
        for url in re.findall(r"[Ss]tudents (?:then )?open\s+`(/labs/[^`]+)`", block)[:1]:
            page = lab_page(url)
            if page:
                day.labs.append(page)
        day.labs += re.findall(r"`(blockchain-course/assets/labs/[^`]+\.html)`", block)
        g = re.search(r"\*\*Graded point \d+:\*\*(.*)", block)
        if g:
            day.graded = [int(n) for n in re.findall(r"question (\d+)", g.group(1))]
            day.graded_note = g.group(1).split(".")[0].strip()
        days[day.number] = day
    return days


# ---------------------------------------------------------------- lab questions

@dataclass
class LabItem:
    page: str
    label: str
    number: int | None
    text: str
    section: str = ""


def strip_tags(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def read_lab(page: str) -> list[LabItem]:
    """Each numbered step on a lab page, labelled by its section; the Sources section is left out."""
    src = (REPO / page).read_text(encoding="utf-8")
    items: list[LabItem] = []
    section = ""
    seen_numbered = False
    pattern = re.compile(r"<h2[^>]*>(.*?)</h2>|<ol([^>]*)>(.*?)</ol>", re.S | re.I)
    for m in pattern.finditer(src):
        if m.group(1) is not None:
            section = strip_tags(m.group(1))
            continue
        if section.lower().startswith("sources"):
            continue
        start = re.search(r'start="(\d+)"', m.group(2) or "")
        n = int(start.group(1)) if start else 1
        # A list with its own start number, or the page's first question list, is numbered questions; a later list
        # with no start number (the parts of a graded note) is labelled by its section instead.
        numbered = bool(re.search(r"question|problem|part|challenge|graded|answer", section, re.I)) and (
            bool(start) or not seen_numbered)
        seen_numbered = seen_numbered or numbered
        for li in re.findall(r"<li[^>]*>(.*?)</li>", m.group(3), re.S | re.I):
            label = f"Q{n}" if numbered else f"{section}, item {n}"
            items.append(LabItem(page, label, n if numbered else None, strip_tags(li), section))
            n += 1
    return items + read_terminal_questions(page)


def read_terminal_questions(page: str) -> list[LabItem]:
    """The questions on the terminal.html beside a lab's index.html (the day 1 terminal orientation), as "Terminal Q<n>".
    That page lays its questions out as bold-numbered paragraphs, not a list, so read_lab's list reader misses them."""
    path = (REPO / page).with_name("terminal.html")
    if not path.exists():
        return []
    src = path.read_text(encoding="utf-8")
    start = re.search(r"<h2[^>]*>\s*The questions", src, re.I)
    if not start:
        return []
    block = src[start.end():].split("<h2", 1)[0]
    return [LabItem(page, f"Terminal Q{n}", int(n), strip_tags(text), "The questions you answer")
            for n, text in re.findall(r"<p><b>(\d+)\.</b>(.*?)</p>", block, re.S)]


# ---------------------------------------------------------------- quizzes

@dataclass
class QuizItem:
    bank: str
    id: str
    day: int  # the morning it is asked
    text: str


def daily_banks() -> list[tuple[str, int]]:
    out = []
    for f in sorted(QUIZ_JSON.glob("daily_d*-quiz-bank.json")):
        m = re.match(r"daily_d(\d+)_", f.name)
        if m:
            out.append((f.name, int(m.group(1))))
    if (QUIZ_JSON / "weekone_check-quiz-bank.json").exists():
        out.append(("weekone_check-quiz-bank.json", 5))
    if (QUIZ_JSON / "weektwo_check-quiz-bank.json").exists():
        out.append(("weektwo_check-quiz-bank.json", 10))
    return out


def read_quizzes() -> list[QuizItem]:
    items = []
    for name, day in daily_banks():
        for q in json.loads((QUIZ_JSON / name).read_text(encoding="utf-8")).get("questions", []):
            text = " ".join([q.get("question_stem", ""), str(q.get("correct_answer", "")),
                             " ".join(t.replace("-", " ") for t in q.get("tags", []))])
            items.append(QuizItem(name, q["id"], day, text))
    return items


def read_tests() -> tuple[dict[int, dict], dict[int, list[str]]]:
    """Post-test items by concept (with their source slides), and pretest item ids by concept."""
    post = {}
    for q in json.loads(POSTTEST.read_text(encoding="utf-8"))["questions"]:
        c = q["concept"]
        post[c["order"]] = {"id": q["id"], "day": q["day"], "name": c["name"], "skill": c["skill"],
                            "type": q["question_type"], "sources": q.get("sources", [])}
    pre: dict[int, list[str]] = {}
    for f in sorted(PRETEST.glob("*.json")):
        for q in json.loads(f.read_text(encoding="utf-8")).get("questions", []):
            if isinstance(q.get("concept"), dict):
                pre.setdefault(q["concept"]["order"], []).append(q["id"])
    return post, pre


# ---------------------------------------------------------------- the map

@dataclass
class Row:
    order: int
    name: str
    skill: str
    day: int
    post: dict
    pre: list[str]
    slides: list[tuple[int, str, Slide]] = field(default_factory=list)  # (day, slot, slide)
    labs: list[tuple[int, LabItem, bool]] = field(default_factory=list)  # (day, item, graded)
    quizzes: list[QuizItem] = field(default_factory=list)
    anchors: list[tuple[str, int | None]] = field(default_factory=list)  # (source slide, its day or None)
    flags: list[str] = field(default_factory=list)


def short(path: str) -> str:
    """lessons/forensics/06-FO-mixers_and_coinjoin.qmd -> 06-FO."""
    m = re.search(r"/(\d\d-[A-Z]{2})-", path)
    return m.group(1) if m else Path(path).stem


def build(terms: dict, days: dict[int, Day]) -> tuple[list[Row], dict]:
    post, pre = read_tests()
    lesson_day = {}
    slides_by_day: list[tuple[int, str, Slide]] = []
    for d in sorted(days):
        for slot, path in days[d].lessons:
            lesson_day.setdefault(path, d)
            for s in read_slides(REPO / path):
                slides_by_day.append((d, slot, s))
    labs_by_day: list[tuple[int, LabItem, bool]] = []
    for d in sorted(days):
        for page in days[d].labs:
            main = page == (days[d].labs[0] if days[d].labs else None)
            for it in read_lab(page):
                # Graded: the question the run sheet names, anything under a "graded" heading, or, when the run
                # sheet names no question (day 6: the whole trace), every numbered question.
                graded = main and bool(days[d].graded_note) and (
                    it.number in days[d].graded or "graded" in it.section.lower()
                    or (not days[d].graded and it.number is not None))
                labs_by_day.append((d, it, graded))
    quizzes = read_quizzes()

    rows = []
    for order, info in sorted(post.items(), key=lambda kv: (kv[1]["day"], kv[0])):
        pats = compile_terms(terms.get(order, []))
        r = Row(order, info["name"], info["skill"], info["day"], info, pre.get(order, []))
        for d, slot, s in slides_by_day:
            if hits(pats, s.title) or hits(pats, s.body) >= 2:
                r.slides.append((d, slot, s))
        r.labs = [(d, it, g) for d, it, g in labs_by_day if hits(pats, it.text)]
        # A graded question that sums up a lab (day 7's limits-of-tracing note) rarely repeats the lab's subject
        # words, so it also practises each concept named in at least half of that lab's numbered questions.
        for d in days:
            numbered = [it for dd, it, _ in labs_by_day if dd == d and it.number is not None]
            if numbered and 2 * sum(1 for it in numbered if hits(pats, it.text)) >= len(numbered):
                have = {id(it) for _, it, _ in r.labs}
                r.labs += [(dd, it, g) for dd, it, g in labs_by_day if dd == d and g and id(it) not in have]
        r.labs.sort(key=lambda t: t[0])
        r.quizzes = [q for q in quizzes if hits(pats, q.text)]
        for src in info["sources"]:
            r.anchors.append((f"{short(src['lesson'])}: {src['slide']}", lesson_day.get(src["lesson"])))
        flag(r)
        rows.append(r)

    # Material no concept claims.
    claimed = {id(s) for r in rows for _, _, s in r.slides}
    lab_claimed = {id(it) for r in rows for _, it, _ in r.labs}
    quiz_claimed = {id(q) for r in rows for q in r.quizzes}
    lessons = []
    for d in sorted(days):
        for slot, path in days[d].lessons:
            ss = [s for dd, sl, s in slides_by_day if s.lesson == path and dd == d]
            lessons.append({"day": d, "slot": slot, "path": path, "slides": len(ss),
                            "claimed": sum(id(s) in claimed for s in ss),
                            "unclaimed": [s.title for s in ss if id(s) not in claimed]})
    scheduled = {p for d in days.values() for _, p in d.lessons}
    unscheduled = sorted(p.relative_to(REPO).as_posix() for p in (REPO / "blockchain-course" / "lessons").glob("*/*.qmd")
                         if p.relative_to(REPO).as_posix() not in scheduled)
    extra = {
        "lessons": lessons,
        "unscheduled": unscheduled,
        "lab_unclaimed": [(d, it) for d, it, _ in labs_by_day if id(it) not in lab_claimed and it.number is not None],
        "lab_total": sum(1 for _, it, _ in labs_by_day if it.number is not None),
        "quiz_unclaimed": [q for q in quizzes if id(q) not in quiz_claimed],
        "quiz_total": len(quizzes),
        "graded": {d: (days[d].graded, days[d].graded_note) for d in days if days[d].graded_note},
    }
    return rows, extra


def flag(r: Row) -> None:
    first = min((d for d, _, _ in r.slides), default=None)
    if first is None:
        r.flags.append("no slide found")
    elif first > r.day:
        r.flags.append(f"first slide on day {first}, after its test day {r.day}")
    if not any(d == r.day for d, _, _ in r.slides) and first is not None:
        r.flags.append(f"no slide on its own day {r.day}")
    late = [a for a, d in r.anchors if d is None or d > r.day]
    if late:
        r.flags.append(f"post-test answer rests on slides taught after day {r.day}, or not scheduled: " + "; ".join(late))
    if r.skill == "working":
        if not r.labs:
            r.flags.append("working skill, no lab question found")
        elif r.day >= 6 and not any(g for _, _, g in r.labs):
            r.flags.append("working skill, not in a graded lab question")
    if r.labs and first is not None and min(d for d, _, _ in r.labs) < first:
        r.flags.append(f"lab practice on day {min(d for d, _, _ in r.labs)}, before the first slide")
    if r.day <= 8 and not any(q.day > r.day for q in r.quizzes):
        r.flags.append("no daily-quiz recall after it is taught")
    if not r.pre:
        r.flags.append("no pretest item")


# ---------------------------------------------------------------- writing

def days_summary(pairs: list[int]) -> str:
    counts: dict[int, int] = {}
    for d in pairs:
        counts[d] = counts.get(d, 0) + 1
    return ", ".join(f"D{d}: {n}" for d, n in sorted(counts.items())) or "none"


def cell(s: str) -> str:
    return s.replace("|", "\\|")


def render(rows: list[Row], extra: dict) -> str:
    out = [
        "# Alignment map",
        "",
        "Generated by `python tools/alignment_map.py`; do not edit by hand (CLAUDE.md rule 2). Rerun it after a",
        "change to a lesson, lab page, quiz bank, the pretest or post-test, the run sheet or `tools/alignment_terms.yml`.",
        "",
        "For each Role Concept: the slides that teach it, the lab questions that practise it, the daily-quiz items that",
        "recall it, and the pretest and post-test items that test it. Only the lessons and labs the run sheet schedules",
        "count, and only visible slides. Coverage is found by matching each concept's words",
        "(`tools/alignment_terms.yml`), so it says where a concept is likely covered, not how well: a flag is a place",
        "to look, and a concept with many slides can still be taught badly.",
        "",
        "## Flags",
        "",
    ]
    flagged = [r for r in rows if r.flags]
    if not flagged:
        out.append("None.")
    for r in flagged:
        out.append(f"- **{r.order}. {r.name}** (day {r.day}, {r.skill}): " + "; ".join(r.flags) + ".")
    out += ["", "## By concept", "",
            "Slides, lab questions and quiz items are counted by day (D6: 4 is four on day 6). A graded lab question",
            "is marked with *g*.", "",
            "| # | Concept | Skill | Day | Slides | Lab questions | Daily-quiz recall | Pretest | Post-test |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        labs = days_summary([d for d, _, _ in r.labs])
        if any(g for _, _, g in r.labs):
            labs += " (*g*)"
        out.append(f"| {r.order} | {cell(r.name)} | {r.skill} | {r.day} | {days_summary([d for d, _, _ in r.slides])} | "
                   f"{labs} | {days_summary([q.day for q in r.quizzes])} | {', '.join(r.pre) or 'none'} | "
                   f"{r.post['id']} |")

    out += ["", "## By lesson", "",
            "How many of each scheduled lesson's visible slides match at least one concept. A slide no concept claims",
            "may be context, a story or an opener, or material to cut or tie to a concept: the list under the table",
            "names them.", "",
            "| Day | Slot | Lesson | Slides | Matched | Unmatched |", "| --- | --- | --- | --- | --- | --- |"]
    for les in extra["lessons"]:
        out.append(f"| {les['day']} | {les['slot']} | {short(les['path'])} `{Path(les['path']).stem}` | {les['slides']} | "
                   f"{les['claimed']} | {les['slides'] - les['claimed']} |")
    out.append("")
    for les in extra["lessons"]:
        if les["unclaimed"]:
            out.append(f"- **D{les['day']} {les['slot']} {short(les['path'])}**: " +
                       "; ".join(cell(t) for t in les["unclaimed"]))
    out += ["", "Lessons in `blockchain-course/lessons/` that the run sheet does not schedule (students receive them,",
            "but no slot teaches them):", ""]
    out += [f"- `{p}`" for p in extra["unscheduled"]] or ["- none"]

    out += ["", "## Labs and quizzes no concept claims", "",
            f"{len(extra['lab_unclaimed'])} of {extra['lab_total']} numbered lab questions and "
            f"{len(extra['quiz_unclaimed'])} of {extra['quiz_total']} daily-quiz items match no concept.", ""]
    for d, it in extra["lab_unclaimed"]:
        out.append(f"- D{d} `{it.page.split('/')[1]}` {it.label}: {cell(it.text[:110])}")
    if extra["quiz_unclaimed"]:
        out += ["", "Quiz items:", ""]
        out.append("- " + "; ".join(f"`{q.bank.split('-quiz')[0]}` {q.id}" for q in extra["quiz_unclaimed"]))

    out += ["", "## Detail", ""]
    for r in rows:
        out += [f"### {r.order}. {r.name}", "",
                f"Day {r.day}, {r.skill}. Post-test {r.post['id']} ({r.post['type'].replace('_', ' ')}); "
                f"pretest {', '.join(r.pre) or 'none'}.", ""]
        if r.anchors:
            out.append("- Post-test answer rests on: " + "; ".join(
                f"{a} (day {d})" if d else f"{a} (not scheduled)" for a, d in r.anchors))
        if r.slides:
            out.append("- Slides: " + "; ".join(f"D{d}{sl} {short(s.lesson)} {cell(s.title)}" for d, sl, s in r.slides))
        else:
            out.append("- Slides: none found")
        if r.labs:
            out.append("- Lab: " + "; ".join(f"D{d} {it.label}{' (graded)' if g else ''}" for d, it, g in r.labs))
        else:
            out.append("- Lab: none found")
        out.append("- Daily quiz: " + (", ".join(f"D{q.day} {q.id}" for q in r.quizzes) or "none found"))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stdout", action="store_true", help="print the map instead of writing it")
    args = ap.parse_args()
    terms = {int(k): v for k, v in yaml.safe_load(TERMS.read_text(encoding="utf-8")).items()}
    days = read_run_sheet(RUN_SHEET.read_text(encoding="utf-8"))
    rows, extra = build(terms, days)
    missing = [r.order for r in rows if r.order not in terms]
    if missing:
        print(f"tools/alignment_terms.yml has no terms for concepts {missing}", file=sys.stderr)
        return 1
    text = render(rows, extra)
    if args.stdout:
        sys.stdout.write(text)
    else:
        OUT.write_text(text, encoding="utf-8", newline="\n")
        print(f"Wrote {OUT.relative_to(REPO).as_posix()}: {len(rows)} concepts, "
              f"{sum(bool(r.flags) for r in rows)} flagged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
