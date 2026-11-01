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

## Quizzes
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)

- The daily banks `daily_d6_review_of_day5`, `daily_d7_review_of_day6` and `daily_d8_review_of_day7` hold only their
  lab's questions (4, 5 and 5); they still need questions on the previous day's lessons, about five each (build-spec
  "Daily quizzes"). The week-one check replaces the day 5 morning quiz. (1 Nov 2026, lab quiz questions)

- No quiz question tests who signs a sweep on the Tron lab's worked example (the sweeping address signs it and pays
  nothing itself; `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS.md` question 1). (1 Nov 2026, lab quiz questions)

## Labs
- `dynamic-labs/tokens/chain/src/CourseTokens.sol:153-154` says "most real NFTs store a link"; the source found
  (`das_understandingsecurityissues_2022`) supports "many". Students read it on the Contract tab. Reword at the next
  chain rebuild: a comment change alters the bytecode, so the deploy hashes and possibly every fee after them
  change. (31 Oct 2026, D3 token lab review)
- The exchange and bridge lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every
  seat's 0.1 ETH swap into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little
  received"); re-quoting and sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3
  minutes) and the price fell from about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one
  L1 block in about 25 s each, and every seat found its L2 transaction. The swap page now explains a revert and asks
  for a new quote. The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage
  lesson"); the instructor answers warn to expect it. Still open: a real class. (31 Oct 2026, D4 exchange and
  bridge lab build)

- The Bitcoin trace lab's students receive `regression-tests/automated/bitcoin-trace/` in `src.zip` and on the VM; its
  shape tests spell out the trail's design (12-input sweep, 14-output batch). Same decision as the explorer and wallet
  tests above. (31 Oct 2026, D6 Bitcoin trace lab build)
- The CoinJoin trace lab's students receive `regression-tests/automated/coinjoin-trace/` in `src.zip` and on the VM;
  its shape tests name the planted leaks and the mixer's two near-match outputs. Same decision as the Bitcoin trace
  tests above. (31 Oct 2026, D7 lab build)
- Students still receive the explorer lab's chain build scripts, the other labs' browser playbooks and the
  automated tests (`dynamic-labs/explorer/chain/`, `dynamic-labs/regression-tests/`) in `src.zip` and on the VM;
  the wallet tests hold the lab's fees and amounts. The wallet playbook, `wallet/quizes/facts.json` and
  `wallet/quizes/build-steps.sh` (it names the signers) are fenced. Decide whether the rest count as instructor
  seeds (rule 1) and fence them in `pages.yml` and `vm-build.yml`. (31 Oct 2026, D2 wallet lab review)
- About 1,700 files outside `dynamic-labs/` are CRLF on the desktop checkout (`git ls-files --eol`); `dynamic-labs/`
  was fixed 31 Oct. Renormalize the rest. (31 Oct 2026, D5 Fabric demo build)

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
