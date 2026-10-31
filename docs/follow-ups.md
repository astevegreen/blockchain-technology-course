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

## Lessons
- 03-EF fee slide says the priority fee (tip) goes to the block's proposer; a second look said that under
  MEV-Boost it goes to the builder. Settle it with the `source` skill: `lessons/ethereum/03-EF-*.qmd:319`, and the
  worked example at line 340. (31 Oct 2026, second look on `0504bcc`)

## Quizzes
- 03-EF bank has no questions on the DEX, sandwich-attack or look-alike slides. (31 Oct 2026, rebuild `0504bcc`)
- 04-EF bank has no questions on the Coin reading, the 4-byte function code, or Vyper and Rust; q2 leans on a
  slide that is now hidden. (31 Oct 2026, D3 ② rebuild)

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
