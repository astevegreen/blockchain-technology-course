# Challenge bank (assessors' follow-ups)

Instructor-only. Students explain their traces informally in week 2 and on day 10; there are no memos and no test
items here. After a student explains, the instructor asks one or two of these questions to see whether the student
can defend each judgment. The bank never goes to students, so it lives here, outside `blockchain-course/` and
`dynamic-labs/`.

From `docs/build-spec.md`, "Additions to existing lessons": routers and batched payouts come first, as the two
known false positives an analyst most often mistakes for a counterparty.

## How an instructor uses it

- Pick the items that fit what the student just explained: a DEX trade (c1, c3, c4), a Bitcoin trace (c2, c5 to
  c7), a mixer trace (c15), a contract read (c16), a typology call (c17), a stablecoin
  freeze (c18), a Tron deposit and its sweep (c19), an attribution (c7, c8, c10, c11, c13, c14).
- A strong answer makes every point under **Answer points**, in any wording. There is no score.
- A weak answer is a cue to revisit the slide it traces to.

## Files

- `challenge-bank.md`: the 17 items. Each names the visible slides its answer points come from.
- `verify_challenge.py`: checks that every traced slide exists and is visible (not inside a `content-hidden`
  block). Run `python quizes/challenge/verify_challenge.py` from the repo root after editing the bank or the slides
  it cites.

## Blueprint

| Item | Topic | Day | Lesson and slide |
| --- | --- | --- | --- |
| c1 | Router in the path | 4 | 03-EF, "Routers and aggregators are only in the path" |
| c2 | Batched payout | 6 | 02-FO, "Batched payouts look busy but aren't a peel" |
| c3 | Bundler, paymaster, relayer | 4 | 03-EF, "Paymasters and relayers pay gas, not the bill" |
| c4 | MEV bot beside a trade | 4 | 03-EF, "An MEV bot trades beside you, not with you" |
| c5 | Co-spending and CoinJoin | 6 | 02-FO, "Co-spending links inputs, unless it's a CoinJoin" |
| c6 | Clues versus kinds of evidence | 6 | 02-FO, "Same-transaction clues never reach High alone" |
| c7 | Huge cluster, no label | 6 | 01-FO, "Step 4 ended Low: now name the service" |
| c8 | A platform tag | 6 | 01-FO, "A label is only as good as its source" |
| c10 | Error rates and percentages | 6 | 01-FO, "Clustering works for most, fails in known ways" |
| c11 | A sanctions listing | 5, 6 | 05-FO, "The SDN list names some addresses, not all" |
| c13 | No error rate | 6 | 01-FO, "Bitcoin Fog: why the court trusted the trace" |
| c14 | Service, not person | 6 | 01-FO, "The chain shows a service; records show who" |
| c15 | Timing and a mixer | 7 | 06-FO, "User habits link deposit to withdrawal" |
| c16 | A code read | 8 | 11-FO, "How sure: what a code read rests on" |
| c17 | A typology call | 9 | 12-FO, "Chain-hopping: the trail changes ledgers" |
| c18 | A stablecoin freeze | 3, 5, 9 | 14-FO, "A freeze is a source: read it narrowly" |
| c19 | A Tron sweep | 5, 9 | 04-FO, "Name the deposit, not the sweep" |

Each item's **Traces to** line lists every slide; the table shows the main one.

## When the lessons change

- A cited slide is renamed or hidden: the verifier names the item. Point it at the new heading, or rewrite it
  from a visible slide.
- Items for days 7 to 9 are added as those lessons are built; keep the bank at 17 items or fewer (the owner raised
  the cap from 15 for c18 and c19), replacing the weakest item (c9 and c12 were retired for c15 to c17).
