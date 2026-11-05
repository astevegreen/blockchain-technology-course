#!/usr/bin/env python3
"""Follow every "day N", "lesson ③" and "(NN-XX)" pointer in a taught lesson to the lesson it names.

Usage: python tools/pointer_check.py [--notes] [--list] [--by-lesson] [<file.qmd>...]

Reads which lesson is taught in which day and slot from the instructor run sheet
(quizes/run-sheet/RUN_SHEET.md), then reads the visible slides and speaker notes of each taught
lesson (not HTML comments, code blocks or `.content-hidden` slides) and reports a pointer when:
  - it names a lesson code that no lesson file has, or a lesson no day teaches;
  - the day or slot written beside a lesson code ("day 6 (02-FO)", "07-FO (day 7 ②)") is not where
    the run sheet puts that lesson;
  - "day N ②" or "lesson ③" points at a day or slot with no lesson (day 10, day 11, slot ④);
  - it names a slide of the lesson ("02-BF's slide "Mining a Candidate Block"") that is hidden or
    that the lesson does not have;
  - a time word beside it says the idea came earlier ("seen", "yesterday", "this morning") but the
    lesson comes later, or says it comes later ("tomorrow", "comes back to") but it was already taught.
With --notes it also prints, as `note:` lines, pointers whose topic it could not find: a backticked
term beside a lesson code, or a "day N's <term>", that no visible slide of that lesson or day shows.
Topic notes are leads for a person to read, never failures.

With no files it reads every lesson on the run sheet. Prints `path:line: message` lines and exits 1
when any pointer is wrong; prints nothing and exits 0 when all are right. --list also prints every
pointer it resolved; --by-lesson groups the findings under each lesson's day and slot.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LESSONS = REPO / "blockchain-course" / "lessons"
RUN_SHEET = REPO / "quizes" / "run-sheet" / "RUN_SHEET.md"
LAST_DAY = 10  # day 10 has no lessons (run sheet: "No new lessons")

SLOTS = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5}
SLOT_MARK = {0: "welcome", 1: "①", 2: "②", 3: "③"}
ANY_SLOT = -1  # a bare "day N": the day is known, the slot is not
CODE_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
DIV_FENCE = re.compile(r"^\s{0,3}(:{3,})\s*(.*?)\s*$")
SLIDE_HEADING = re.compile(r"^##\s+(.*?)\s*$")
DAY_HEADING = re.compile(r"^## Day (\d+)\b")
SHEET_ROW = re.compile(r"^\|\s*([①②③]|0845)\s*\|.*?`(blockchain-course/lessons/[^`]+\.qmd)`")
LESSON_FILE = re.compile(r"^(\d{2}-[A-Z]{2})-")
# A lesson code is never part of a file name or anchor (`04-CP-asymmetric…`, `02-IN.html`).
CODE = re.compile(r"(?<![\w/#-])(\d{2}-[A-Z]{2})(?![\w-]|\.(?:qmd|html)|:\d)")
DAY = re.compile(r"(?<![\w-])(?:[Dd]ay|D)\s?(\d{1,2})(?![\d\w-])(?:\s*(?:'s\s+)?(?:lesson\s+)?([①②③④⑤]))?")
SLOT_ONLY = re.compile(r"(?<!\w)[Ll]esson\s+([①②③④⑤])")
DAY_RANGE = re.compile(r"\b[Dd]ays\s+\d")
# "day 6 (02-FO)", "02-FO (day 6)", "02-FO, day 6": only brackets, commas and spaces between the two.
BESIDE = re.compile(r"^[\s(),]{0,3}$")
QUOTED = re.compile(r"[\"“]([^\"”\n]{4,90})[\"”]")
TOPIC_TICK = re.compile(r"`([^`\s]{2,40})`")
# "day 1's triangle", "the day 6 bridge case": a day used as an adjective names a topic, the next word.
DAY_TOPIC = re.compile(r"(?:\bthe\s+[Dd]ay\s?(\d{1,2})|(?<![\w-])[Dd]ay\s?(\d{1,2})'s)\s+([A-Za-z][\w-]{2,})")
CUE_WINDOW = 30  # a time word counts only this close to the pointer
DURATION = re.compile(r"\b\d+\s+(?:seconds?|minutes?|hours?|days?|blocks?|weeks?)\s+later\b", re.IGNORECASE)
BACK_CUES = re.compile(
    r"\b(earlier|yesterday|this morning|seen|saw|met|showed|learned|learnt|recall|remember|as on|as in)\b",
    re.IGNORECASE)
FORWARD_CUES = re.compile(
    r"\b(later|tomorrow|comes? back|returns?|picks? up|ahead|upcoming|saved for|forward to)\b", re.IGNORECASE)
TOPIC_STOP = {"lesson", "lessons", "slide", "slides", "lab", "labs", "case", "cases", "quiz", "worked",
              "example", "first", "second", "third", "last", "morning", "afternoon", "review", "this", "that",
              "same", "own", "other", "graded", "point", "points", "check", "start", "end", "with", "from",
              "question", "questions", "skills", "methods", "method", "work", "idea", "ideas", "habit", "rule"}
FRONT_TITLE = re.compile(r"^title:\s*[\"']?(.*?)[\"']?\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Slot:
    day: int
    slot: int  # 0 = welcome, 1-3 = ①-③, ANY_SLOT = somewhere that day

    def label(self) -> str:
        if self.slot == ANY_SLOT:
            return f"day {self.day}"
        return f"day {self.day} {SLOT_MARK.get(self.slot, str(self.slot))}"

    def order(self, other: Slot) -> int:
        """-1 when self is before other, 1 when after, 0 when the same or unknown."""
        if ANY_SLOT in (self.slot, other.slot):
            mine, theirs = (self.day,), (other.day,)
        else:
            mine, theirs = (self.day, self.slot), (other.day, other.slot)
        return (mine > theirs) - (mine < theirs)


@dataclass
class Lesson:
    code: str
    path: Path
    slot: Slot | None
    lines: list[tuple[int, str]] = field(default_factory=list)  # (1-based line, visible text)
    visible: set[str] = field(default_factory=set)  # slide titles, normalised
    hidden: set[str] = field(default_factory=set)
    subject: str = ""  # the lesson's own title, from its front matter

    @property
    def rel(self) -> str:
        return self.path.relative_to(REPO).as_posix()


@dataclass
class Pointer:
    said: str
    start: int
    end: int
    where: Slot
    lesson: Lesson | None = None


@dataclass
class Finding:
    lesson: Lesson
    line: int
    message: str
    note: bool = False

    def text(self) -> str:
        return f"{'note: ' if self.note else ''}{self.lesson.rel}:{self.line}: {self.message}"


@dataclass
class Course:
    lessons: dict[str, Lesson]
    taught: dict[str, Slot]

    def in_slot(self, where: Slot) -> str | None:
        return next((code for code, slot in self.taught.items() if slot == where), None)

    def on_day(self, day: int) -> list[Lesson]:
        return [les for les in self.lessons.values() if les.slot and les.slot.day == day]


def read_run_sheet(path: Path = RUN_SHEET) -> dict[str, Slot]:
    """Map each taught lesson's code to its day and slot."""
    taught: dict[str, Slot] = {}
    day = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = DAY_HEADING.match(line)
        if heading:
            day = int(heading.group(1))
            continue
        row = SHEET_ROW.match(line)
        code = row and LESSON_FILE.match(Path(row.group(2)).name)
        if code and day is not None:
            taught[code.group(1)] = Slot(day, SLOTS.get(row.group(1), 0))
    return taught


def strip_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Drop HTML comments from one line, including several on a line and one that spans lines."""
    kept = ""
    while line:
        if in_comment:
            end = line.find("-->")
            if end < 0:
                return kept, True
            in_comment, line = False, line[end + 3:]
        else:
            begin = line.find("<!--")
            if begin < 0:
                return kept + line, False
            kept, in_comment, line = kept + line[:begin], True, line[begin + 4:]
    return kept, in_comment


def body_start(lines: list[str]) -> int:
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() in ("---", "..."):
                return idx + 1
    return 0


def read_lines(text: str) -> tuple[list[tuple[int, str]], list[tuple[str, bool]]]:
    """Visible lines (slide text and notes) and every slide title with whether it shows.

    Front matter, HTML comments, code blocks and `.content-hidden` divs do not show.
    """
    lines = text.split("\n")
    out: list[tuple[int, str]] = []
    titles: list[tuple[str, bool]] = []
    fence: str | None = None
    in_comment = False
    divs: list[bool] = []
    for idx in range(body_start(lines), len(lines)):
        line = lines[idx]
        if fence:
            if line.strip().startswith(fence) and set(line.strip()) == {fence[0]}:
                fence = None
            continue
        code = CODE_FENCE.match(line)
        if code and not in_comment:
            fence = code.group(1)
            continue
        was_comment = in_comment or "<!--" in line
        kept, in_comment = strip_comments(line, in_comment)
        div = DIV_FENCE.match(kept)
        if div:
            if div.group(2):
                divs.append(".content-hidden" in div.group(2) and "when-" not in div.group(2))
            elif divs:
                divs.pop()
            continue
        shows = not any(divs)
        heading = SLIDE_HEADING.match(line if was_comment else kept)
        if heading:
            titles.append((heading.group(1), shows and bool(SLIDE_HEADING.match(kept))))
        if shows and kept.strip():
            out.append((idx + 1, kept))
    return out, titles


def norm_title(raw: str) -> str:
    title = re.sub(r"\{[^}]*\}\s*$", "", raw)
    title = re.sub(r"<[^>]+>", "", title)
    title = re.sub(r"[*_`\"“”‘’']", "", title)
    return re.sub(r"\s+", " ", title).strip().lower()


def load_course(root: Path = LESSONS, sheet: Path = RUN_SHEET) -> Course:
    taught = read_run_sheet(sheet)
    lessons: dict[str, Lesson] = {}
    for qmd in sorted(root.glob("*/*.qmd")):
        code = LESSON_FILE.match(qmd.name)
        if not code or code.group(1) in lessons:
            continue
        lesson = Lesson(code.group(1), qmd, taught.get(code.group(1)))
        text = qmd.read_text(encoding="utf-8", errors="replace")
        lesson.lines, titles = read_lines(text)
        lesson.visible = {norm_title(t) for t, shows in titles if shows}
        front = FRONT_TITLE.search(text[:2000])
        lesson.subject = norm_title(front.group(1)) if front else ""
        lesson.hidden = {norm_title(t) for t, shows in titles if not shows} - lesson.visible
        lessons[lesson.code] = lesson
    return Course(lessons, taught)


def clauses(text: str) -> list[str]:
    """Split a line at sentence ends, semicolons, dashes and table cells, so time words stay with their pointer."""
    return [part for part in re.split(r"(?<=[.;!?])\s+(?=[A-Z(*`\"])|;\s+|\s+—\s+|\s\|\s", text) if part.strip()]


def stem(word: str) -> str:
    word = word.lower().strip("`'\"()")
    for suffix in ("ing", "es", "s", "ed"):
        if len(word) > 5 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def mentions(lessons: list[Lesson], term: str, titles: bool = False) -> bool:
    """Whether a visible line (or, with titles, a visible slide title) of these lessons shows the term by its stem."""
    words = re.split(r"[\s-]+", term.strip("`").rstrip("()").lower())
    pattern = re.compile(r"[\s-]+".join(re.escape(stem(w)) + r"\w*" for w in words if w))
    if titles:
        return any(pattern.search(title) for les in lessons for title in les.visible | {les.subject})
    return any(pattern.search(text.lower()) for les in lessons for _, text in les.lines)


class ClauseCheck:
    """The pointers in one clause of one line, and what is wrong with them."""

    def __init__(self, lesson: Lesson, line: int, clause: str, course: Course):
        self.lesson, self.line, self.clause, self.course = lesson, line, clause, course
        self.found: list[Finding] = []
        self.pointers: list[Pointer] = []
        skip_days = DAY_RANGE.search(clause) and not CODE.search(clause)
        self.days = [] if skip_days else list(DAY.finditer(clause))
        self.codes = [m for m in CODE.finditer(clause) if m.group(1) != lesson.code]

    def say(self, message: str, note: bool = False) -> None:
        finding = Finding(self.lesson, self.line, message, note)
        if finding not in self.found:
            self.found.append(finding)

    def run(self) -> list[Finding]:
        used = self.code_pointers()
        self.day_pointers(used)
        self.slot_pointers()
        self.slide_titles()
        self.time_words()
        self.topics()
        return self.found

    def beside(self, code: re.Match) -> int | None:
        for idx, day in enumerate(self.days):
            between = self.clause[day.end():code.start()] if day.end() <= code.start() \
                else self.clause[code.end():day.start()]
            if BESIDE.match(between):
                return idx
        return None

    def code_pointers(self) -> set[int]:
        used: set[int] = set()
        for match in self.codes:
            code = match.group(1)
            idx = self.beside(match)
            day = self.days[idx] if idx is not None else None
            if idx is not None:
                used.add(idx)
            said = f"{day.group(0).strip()} ({code})" if day else code
            target = self.course.lessons.get(code)
            if target is None:
                self.say(f"{said}: no lesson has the code {code}")
            elif target.slot is None:
                self.say(f"{said}: {code} is not taught on any day of the run sheet")
            elif day and (int(day.group(1)) != target.slot.day
                          or SLOTS.get(day.group(2) or "", target.slot.slot) != target.slot.slot):
                self.say(f"{said}: the run sheet teaches {code} on {target.slot.label()}")
            else:
                start, end = (min(match.start(), day.start()), max(match.end(), day.end())) if day \
                    else match.span()
                self.pointers.append(Pointer(said, start, end, target.slot, target))
        return used

    def day_pointers(self, used: set[int]) -> None:
        for idx, match in enumerate(self.days):
            if idx in used:
                continue
            day, said = int(match.group(1)), match.group(0).strip()
            slot = SLOTS.get(match.group(2) or "")
            if not 1 <= day <= LAST_DAY:
                self.say(f"{said}: the course has days 1 to {LAST_DAY}")
            elif slot and not self.course.in_slot(Slot(day, slot)):
                self.say(f"{said}: the run sheet has no lesson in that slot")
            else:
                where = Slot(day, slot or ANY_SLOT)
                target = self.course.lessons.get(self.course.in_slot(where) or "")
                self.pointers.append(Pointer(said, match.start(), match.end(), where, target))

    def slot_pointers(self) -> None:
        here = self.lesson.slot
        for match in SLOT_ONLY.finditer(self.clause):
            if not here or any(d.start() <= match.start() <= d.end() for d in self.days):
                continue
            where = Slot(here.day, SLOTS[match.group(1)])
            code = self.course.in_slot(where)
            if not code:
                self.say(f"{match.group(0)}: day {here.day} has no lesson in that slot")
            else:
                self.pointers.append(Pointer(match.group(0), match.start(), match.end(), where,
                                             self.course.lessons[code]))

    def slide_titles(self) -> None:
        """A quoted slide title beside a lesson pointer must be a visible slide of that lesson."""
        named = [p for p in self.pointers if p.lesson and p.lesson is not self.lesson]
        if not named:
            return
        for quote in QUOTED.finditer(self.clause):
            title = norm_title(quote.group(1))
            target = min(named, key=lambda p: abs(p.start - quote.start())).lesson
            if title in target.visible:
                continue
            if title in target.hidden:
                self.say(f"\"{quote.group(1)}\" is a hidden slide in {target.code}")
            elif re.search(r"\bslides?\b", self.clause[max(0, quote.start() - 20):quote.start()]):
                self.say(f"{target.code} has no slide titled \"{quote.group(1)}\"")

    def time_words(self) -> None:
        here = self.lesson.slot
        if not here:
            return
        text = DURATION.sub(lambda m: " " * len(m.group(0)), self.clause)
        for pointer in self.pointers:
            near = text[max(0, pointer.start - CUE_WINDOW):pointer.end + CUE_WINDOW]
            back, forward = bool(BACK_CUES.search(near)), bool(FORWARD_CUES.search(near))
            order = pointer.where.order(here)
            if back and not forward and order > 0:
                self.say(f"{pointer.said}: written as already taught, but {pointer.where.label()} comes after "
                         f"this lesson ({here.label()})")
            elif forward and not back and order < 0:
                self.say(f"{pointer.said}: written as still to come, but {pointer.where.label()} was before "
                         f"this lesson ({here.label()})")

    def topics(self) -> None:
        for match in DAY_TOPIC.finditer(self.clause):
            day, term = int(match.group(1) or match.group(2)), match.group(3)
            if term.lower() in TOPIC_STOP or not 1 <= day < LAST_DAY:
                continue
            on_day = self.course.on_day(day)
            if on_day and not mentions(on_day, term, titles=True):
                self.say(f"\"{match.group(0)}\": no visible slide title on day {day} has \"{term}\"", note=True)
        for pointer in self.pointers:
            target = pointer.lesson
            if not target or target is self.lesson or not CODE.search(pointer.said):
                continue
            for tick in TOPIC_TICK.finditer(self.clause):
                term = tick.group(1)
                if tick.start() > pointer.end + CUE_WINDOW or tick.end() < pointer.start - CUE_WINDOW:
                    continue
                if not CODE.fullmatch(term) and "/" not in term and not mentions([target], term):
                    self.say(f"`{term}` beside {target.code}: no visible slide of {target.code} mentions it",
                             note=True)


def check_lesson(lesson: Lesson, course: Course, listing: list[str] | None = None) -> list[Finding]:
    found: list[Finding] = []
    for line, text in lesson.lines:
        clean = re.sub(r"\]\([^)]*\)|https?://\S+", "]", text)  # link targets are not pointers
        for clause in clauses(clean):
            check = ClauseCheck(lesson, line, clause, course)
            found += check.run()
            if listing is not None:
                listing += [f"{lesson.rel}:{line}: {p.said} -> {p.where.label()}"
                            f"{f' ({p.lesson.code})' if p.lesson else ''}" for p in check.pointers]
    return found


def report(scan: list[Lesson], shown: list[Finding], by_lesson: bool) -> list[str]:
    if not by_lesson:
        return [f.text() for f in shown]
    out: list[str] = []
    for lesson in scan:
        mine = [f for f in shown if f.lesson is lesson]
        if mine:
            where = lesson.slot.label() if lesson.slot else "not on the run sheet"
            out.append(f"{lesson.code} ({where}): {lesson.rel}")
            out += [f"  {'note: ' if f.note else ''}line {f.line}: {f.message}" for f in mine]
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--notes", action="store_true", help="also print topic leads as note: lines")
    parser.add_argument("--list", action="store_true", help="also print every pointer resolved")
    parser.add_argument("--by-lesson", action="store_true", help="group findings under each lesson")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    course = load_course()
    if args.files:
        wanted = {p.resolve() for p in args.files}
        scan = [les for les in course.lessons.values() if les.path.resolve() in wanted]
    else:
        scan = sorted((les for les in course.lessons.values() if les.slot),
                      key=lambda les: (les.slot.day, les.slot.slot))
    listing: list[str] | None = [] if args.list else None
    findings = [f for les in scan for f in check_lesson(les, course, listing)]
    lines = (listing or []) + report(scan, [f for f in findings if args.notes or not f.note], args.by_lesson)
    if lines:
        print("\n".join(lines))
    return 1 if any(not f.note for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
