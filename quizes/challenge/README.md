# Challenge bank (assessors' follow-ups)

Instructor-only. Students explain their traces informally in week 2 and on day 10; there are no memos and no test
items here. After a student explains, the instructor asks one or two of these questions to see whether the student
can defend each judgment. The bank never goes to students, so it lives here, outside `blockchain-course/` and
`dynamic-labs/`.

From `docs/build-spec.md`, "Additions to existing lessons": routers and batched payouts come first, as the two
known false positives an analyst most often mistakes for a counterparty.

## How an instructor uses it

- Pick the items that fit what the student just explained: a DEX trade (c1, c3, c4), a Bitcoin trace (c2, c5 to
  c7, c12), an attribution (c7 to c11, c13, c14).
- A strong answer makes every point under **Answer points**, in any wording. There is no score.
- A weak answer is a cue to revisit the slide it traces to.

## Files

- `challenge-bank.md`: the 14 items. Each names the visible slides its answer points come from.
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
| c9 | Two platforms agree | 6 | 01-FO, "Attribution confidence: count kinds of evidence" |
| c10 | Error rates and percentages | 6 | 01-FO, "Clustering works for most, fails in known ways" |
| c11 | A sanctions listing | 5, 6 | 05-FO, "The SDN list names some addresses, not all" |
| c12 | Cluster size | 6 | 01-FO, "Platforms run your heuristics at scale" |
| c13 | No error rate | 6 | 01-FO, "Bitcoin Fog: why the court trusted the trace" |
| c14 | Service, not person | 6 | 01-FO, "The chain shows a service; records show who" |

Each item's **Traces to** line lists every slide; the table shows the main one.

## When the lessons change

- A cited slide is renamed or hidden: the verifier names the item. Point it at the new heading, or rewrite it
  from a visible slide.
- Items for later days (mixers on day 7, for example) are added as those lessons are built; keep the bank at 15
  items or fewer.
