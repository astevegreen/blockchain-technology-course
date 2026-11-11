# Follow-ups

Known work that a session found outside its task. The list carries it forward, so session summaries stop repeating
it. `python tools/follow_ups.py` prints this list after what it computes itself (stale mind-map links, the glossary
slide index), which is never listed here.

## How to use
- Grep this file before adding: an item already here gets nothing more.
- One item per bullet: what is wrong or missing, and where (`file:line` or the Notion page), then the date found
  and how, in brackets.
- Finish an item: delete its bullet in the same commit.
- A decision only the owner can make goes to the owner as a question, not here.
- Work that waits for a day that has not come (the real cloud host, a real class, a Mac) goes to
  `docs/before-first-class.md`, not this list.

## Lessons
- Day 9 ③'s "Who holds which record" slide (`docs/build-spec.md`, Additions) needs the reviewing expert's meaning
  of "what to do with all of that info", asked in the same request as the bridge guide, before it is built
  [10 Nov 2026, expert feedback review]

## Labs
- The shared look's role colours and shapes (`blockchain-course/assets/labs/shared/look.css`) are used only by labs
  built on the shell; slide diagrams of inputs, outputs, change and keys, and the dynamic labs' web pages, still
  draw them their own way, so one object can look two ways in one day [10 Nov 2026, plan step 3]
- Day 8's lab has no worked example of following funds across a bridge yet (`docs/build-spec.md`, Additions,
  "Following funds across a bridge"); it waits on the guide the reviewing expert offered, which the owner is to
  request [10 Nov 2026, expert feedback review]

## Tooling and rules
- The alignment map's keyword match is wrong in places: it shows no lab for concept 42 though day 1's explorer
  part 2(b) and terminal Q2 practise it, credits day 3 `tokens` Q3 and Q5 to concept 12, and credits day 4 and
  day 6 Q12 to concept 5 (`tools/alignment_terms.yml`). [10 Nov 2026, lab and concept catalog]

## Notion and documents
- `docs/quality-rubric.md:86-87` says 04-CP, 01-CM and 01-EF have no "Ask:" prompts; 04-CP now has 12 and 01-CM
  has 7, and the lessons with none are 01-EF, 04-EF and 05-EF. `docs/analysis/2026-11-static-labs-review.md:28`
  repeats it. [10 Nov 2026, grep count]
- The Notion home page's Decision log has no entries for the 10 Nov lab-plan decisions (the prediction-lab trial,
  the eight games and their scoring, the Docker labs' fates, belief 8, the mining lottery); they are only in
  `docs/build-spec.md` and `docs/analysis/2026-11-lab-plan.md` [10 Nov 2026, Notion fetch]
