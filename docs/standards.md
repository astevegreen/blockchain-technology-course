# Course standards

The index of the course's standing operating procedures: which document governs what, in what order to check
work against them, and who may change them. Start here before writing or reviewing a lesson, lab or quiz item.
Every standard below was adopted by the owner, and changing one is the owner's decision (CLAUDE.md rule 4).
`CLAUDE.md` holds the hard rules and the workflow; this page holds what "good" means.

## The standards

| Standard | Governs | Use it when |
| --- | --- | --- |
| `docs/build-spec.md` | What the course builds: the direction, the day map, what a lesson and a lab are, the confidence scale, sources and dates, what is out of scope | Deciding whether something belongs, and how big it is |
| `docs/quality-rubric.md` | What "better" means: 15 criteria in three groups (aligned, teaches well, evidence) | Scoring a lesson or lab, or choosing what to fix next |
| `docs/lesson-standard.md` | How a lesson's slides work together: 13 checks from objective to close (rubric criterion 15) | Building, reworking or reviewing a lesson as a whole |
| `docs/writing-standard.md` | The wording inside each slide, note, lab page and quiz item: 13 checks (rubric criteria 5 and 13) | Writing or reviewing any text students or instructors read |
| `.claude/skills/source/SKILL.md` | Finding and judging a source; what to do when none states a claim | Adding a fact, or a fact a review disputes |

**Form rules.** The mechanics of each kind of file sit in `.claude/rules/`, loaded automatically for the paths
they cover: `lessons.md` (front matter, the four-part notes block, citations, hiding, anchors), `labs.md`,
`quizzes.md`, `glossary.md`, `site.md`, `ci.md`.

**Quiz and lab procedures.** Quiz banks follow the guides in `quizes/` in pipeline order (`.claude/rules/quizzes.md`
lists them) and `quizes/QUIZ_ENGINE_JSON_SPEC.md`. Labs follow `.claude/skills/lab/SKILL.md` and
`dynamic-labs/README.md`.

**Background, not standards.** `docs/analysis/` holds the reviews behind each standard (for example
`2026-11-writing-standard-review.md`, `2026-11-lesson-standard-review.md`), and
`docs/technical-educator-pedagogical-blueprint.md` is an earlier synthesis. Read them for the reasons; check work
against the standards.

## Checking a lesson, in order

Each step assumes the one before it passed, so no effort goes on a slide that will move or go.

1. **Does it belong?** `docs/build-spec.md`: the lesson's place on the day map, its 50-minute slot, the direction
   (the analyst's job ends at the assessment), what is out of scope.
2. **Does it work as a lesson?** `docs/lesson-standard.md`, checks 1 to 13, starting with the titles-only read.
3. **Does each slide read clearly?** `docs/writing-standard.md`, checks 1 to 13, in its review order.
4. **Is every fact sourced and dated?** A `Blockchain.bib` key for each fact, an as-of tag on each fact that
   changes (CLAUDE.md, Course direction; `docs/build-spec.md`, "Sources and dates"), the `source` skill for any gap.
5. **Is the form right?** `.claude/rules/lessons.md`: notes in four parts, headings outside divs, moved anchors
   listed.
6. **Machine check, then review.** `python tools/check.py`, then the `reviewer` agent, which applies steps 1 to 5
   and reports blockers and minor concerns.

A lab or a quiz item runs the same order, with the lab skill or the quiz guides in place of step 2.

## What holds the work

A `blocker` holds a change until it is fixed; a `minor` concern ships with a note. The standards' blockers:

- **Lesson standard:** an idea used before it is taught (check 5); a task asked of students that the lesson never
  showed done (check 8).
- **Writing standard:** a term used before it is taught (check 1); a step a newcomer cannot supply (check 5).
- **Build spec and sources:** a wrong or unsourced fact; a lesson that does not fit its slot; a cut with no
  searches listed.
- **CLAUDE.md hard rules:** any broken hard rule, among them instructor-only material reaching students, a
  generated file edited by hand, and a quiz answer that no longer traces to the lesson.
- **Review:** a link the change breaks; a new source whose quoted passage is not in the source. The full list is
  in `.claude/agents/reviewer.md`.

Everything else a standard flags is `minor`. A count (words per slide, slides per lesson) can point a review at
something to read first; it never passes or fails anything (rubric, owner 4 Nov 2026).

## Who decides

- **Adding** teaching material that is sourced and meets the standards is the writer's call (owner, 12 Nov 2026).
- **Cutting, splitting or replacing** material, what a lesson teaches, quiz difficulty, lab scenarios and how lab
  answers are checked are the owner's: ask one question with a recommendation.
- **Changing a standard** is the owner's. Propose it with a review in `docs/analysis/`, as the writing and lesson
  standards were.
