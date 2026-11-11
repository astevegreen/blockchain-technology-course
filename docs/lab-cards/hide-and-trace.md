# Design card: Hide and trace

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 6: days 6-7's game). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Hide and trace (days 6-7's game, new; the lab plan's "Every lab" row of that name) |
| Replaces | nothing |
| Opens from | `lessons/forensics/06-FO-mixers_and_coinjoin.qmd`, "Before and after the mix still leak"; it recalls "A limits-of-tracing note: where it stops" |
| Day | Day 7, second half of the afternoon: after the CoinJoin trace's graded note (approved guardrail) |
| Kind | game (teams of three or four, one page per team, about 75 minutes: briefing 10, hide 20, trace 25, reveal 20) |

Every team is a hiding team and then a tracing team. All teams hide at once on one live chain, each moving its own
stolen coin with a fixed menu of moves and a fixed budget; then each team traces another team's coin and makes
calls with confidence words, scored by calibration. The guardrails are the owner's (lab plan, "Locked in"; build
spec, "Lab games") and are not reopened here; this card fills in the menu, the budget, the calls and the points.
Day 6's Bitcoin trace and day 7's CoinJoin trace teach the heuristics on frozen chains; this game is the first time
the students' own moves make the trail. It is practice: day 7's graded point stays the limits-of-tracing note.

## The ten lines

1. **The wrong belief**: "With enough hops, splits and a mix, nobody can follow the money." Belief 12 on the plan's
   list ("a mixer or Monero makes funds untraceable, full stop", marked common), from the hider's side; the
   prediction labs Who paid whom? and Which one is real? break it from the tracer's.
2. **The prediction** (shell: `commit`): asked of each team before it hides: "Your team holds 2.1 BTC stolen from
   an exchange. You have eight moves, including a CoinJoin and a mixer, and 30 blocks to get it to an exchange
   deposit. Can another team follow it there?" Choices: (a) no: after the mixer nobody can; (b) no: enough hops
   loses anyone; (c) it depends on what leaks: a merge, a reused address, a withdrawal the size of the deposit
   less the fee, a cash-out timed to the mix; (d) yes: every move is on chain, so all of it. Then High, Moderate or
   Low. (Answer: (c).)
3. **The action** (shell: `do`): hide, then trace. Hiding, the team picks its moves on its page and the game server
   sends them: it has no command line to learn. Tracing, it is given another team's stolen coin and follows it in
   the explorer, making calls: "this output carries the target's money", each with a confidence word and a reason
   (the heuristic and its transaction), and one call on where the trace stops and why. At the reveal each hiding
   team sees the calls made on its own trail beside its move log: the merge it made to save a move, the address
   it used twice, the mixer withdrawal that matched its deposit less the fee, and the deadline's forced deposit.
   A team that picked (a) or (b) watches its trail picked up after the mix, and a team that picked (d) watches
   the tracers stop at a CoinJoin and stay there.
4. **The constraint**: without the menu, the game measures who can script a wallet; without the budget, who can
   keep moving longest; without calibration scoring, calling everything High wins, and speed favours the
   experienced. The menu holds the moves the lessons teach, and each can leak the way 06-FO says: a pre-mix split
   ties the CoinJoin entry to the coin, a reuse or post-mix co-spend is one strong line, and timing alone is Low.
   The budget makes the hiders trade: every hop that hides costs a move that a merge would save.
5. **The name** (shell: `name`): calibration. Parts: from calibrate, to check a measure against a known standard.
   Plain: your confidence words match how often you turn out right, so your Highs are right more often than your
   Moderates, and your Moderates more often than your Lows. The reveal is the known standard.
6. **The explorer view** (shell: `explorer`): mempool on the game's live chain: the transaction page, where a
   CoinJoin shows as equal outputs and a merge as several inputs; the address page, where a reused address shows
   two receives; the block page, for when a coin moved. At the reveal the hiding team's move log sits beside the
   same pages, so each call can be checked against what was done.
7. **The twist** (shell: `twist`): after the reveal, the class table: every High call, its reason and whether it
   was right, sorted by the kind of evidence it rested on. One row is read aloud: a High that a CoinJoin output
   spent to the exchange one block after the round was the target's ("first out, straight to the exchange"). It
   was wrong: two hiding teams had a coin in that round, and the output was the other team's. "What did the call
   lack?" Choices: nothing: it was bad luck; a second, independent line: timing is one kind of evidence, Low on
   its own; more blocks of watching; the other team's move log. Answer: the second. What changes is who shares
   the round: the tracers could see only the chain, and on it the other team's move looked like their target's.
   The table then shows how many Highs rested on amount or timing alone, and how many of those were wrong.
8. **The sentence** (shell: `tell`): "Tell the agent where the 2.1 BTC went, and where the trace stops."
   Example: "In block 3 the 2.1 BTC was split into three coins. The pool-sized coin, 0.5001 BTC, joined a CoinJoin
   in block 9, where its trace stops. The 0.8 BTC coin paid out a round 0.3 BTC in block 12; on amount alone its
   0.5 BTC change looked like the thieves' own (Low). At the deadline, in block 30, that change and the split's
   third coin were deposited to exchange deposit E3 in one transaction (Moderate: the co-spend is one strong line
   that the change is still the thieves'). Where the 0.3 BTC went is undetermined."
9. **The game, if any**: hide and trace. Only the tracing scores (owner, 11 Nov 2026). Each call that names an
   output as the target's money, right or wrong: Low +1 or -1; Moderate +2 or -3; High +3 or -9. "Undetermined"
   scores 0. A word above what its reason allows on the course scale is scored as the word the reason allows (a
   High on timing alone scores as a Low). The call on where the trace stops, with its reason: +2 if it names the
   move that ended it. A call with no reason is struck. Time only breaks ties. "Right" means the output belongs to
   the hiding team, from the game server's log. High pays most and costs most, and only two independent lines
   earn it; a guess past a CoinJoin loses points on average, so "undetermined" is the right call there. The
   score is the concept.
10. **The archetype**: simulation.

The opening case (shell: `case`): "Your team has just stolen 2.1 BTC from an exchange's hot wallet. In 30 blocks
it must reach an exchange that will pay you out, and the other teams will be watching the chain."

The menu, the budget and the chain (the card's design, inside the approved guardrails):

- **The menu**, one move each: peel (a round payment, change to a fresh address); split (one coin into two to five);
  merge (two or more of your coins in one transaction, including coins split a few hops before: Forensics 3's
  three-hop re-gather, which the day 6 card left for this menu); wait (let blocks pass); CoinJoin (one 0.5001 BTC
  coin into the next round of the 0.5 BTC pool, day 7's pool, for the coordinator's fee); mixer (a deposit to the
  custodial mixer, with a chosen delay and withdrawal address, for its fee); cash out (a deposit to the exchange,
  where the trail ends). Each output goes to a fresh address unless the team picks one it has used: reuse is a
  choice, and a leak.
- **The budget**: eight moves and 30 blocks. Whatever has not reached the exchange by the last block is deposited
  there in one transaction, so a team that runs out of time co-spends its own coins.
- **The chain**: a live copy of the course chain in the course's `bitcoin-mempool` image, with an in-house game
  server that mines a block every 30 seconds, sends the teams' moves, and runs a crowd: payments, exchange
  withdrawals, crowd entries in every CoinJoin round, and crowd mixer withdrawals of similar sizes and times, so
  that every leak has a look-alike. All teams hide on the same chain, so each team's coins also hide among the
  others'.

Left out, for the owner to see:

- The points behind the words. With these payoffs, against "undetermined" at 0, a Low call pays on average only
  if the team is wrong less than one time in two; Moderate, less than two times in five; High, less than one time
  in four. A word is worth choosing over the word below it only if the team is wrong less than one time in three
  (Moderate over Low) or one time in seven (High over Moderate). Students see the points and the course scale's
  rules for each word, never these fractions, so the scale stays a scale of evidence and the game checks it.
- The points alone reward a word by how often it turns out right, not by the evidence under it: a team often
  right on one strong line would still earn by saying High. So a word above what its reason allows is scored as
  the allowed word, which keeps the points tied to the course scale (owner, 11 Nov 2026: "Keep both").
- The hiders do not score. A hiding score would reward laundering skill, which the course does not teach; the
  hiders' payoff is the reveal, where they see their own leaks. (Owner, 11 Nov 2026: "Hiders don't score".)
- Monero, Tornado Cash and bridges are not on the menu: day 7's chain is Bitcoin, and day 8 has the bridge.
- The lab plan's row says "then swap". Here every team hides and every team traces, so the swap is built in, and
  the round runs once: a second round would not fit day 7's second half.
- The mixer and the CoinJoin coordinator are the game server's, in-house; no real mixer or coordinator is used or
  named on the page.

How it is built (last of the games, per the guardrail): `dynamic-labs/hide-and-trace/`, a lab in the stack like
`coinjoin-trace`, with the `bitcoin-mempool` image left running rather than frozen, and the game server (an in-house
service: the move page, the coordinator, the mixer, the exchange, the crowd and the scoring). The tracing page
records each call with its time. The move logs and the scoring reveal stay on the server until the instructor opens
the reveal; the instructor's scoring notes go in `dynamic-labs/hide-and-trace/quizes/`, which
`student-exclude.txt` already covers (`dynamic-labs/**/quizes/**`). The game server's code reaches students, which is
safe only because the answers are the move logs made at run time: the build hard-codes no key. A saved chain from a
test run is the fallback the build spec asks of a live part.

## Load check

- [x] One new term per step: calibration is the only term named; "peel", "co-spend", "CoinJoin", "mixer",
  "address reuse" and the confidence words come from days 6 and 7.
- [x] Nothing drawn for decoration: the move page shows the coins and the budget; the reveal shows the calls beside
  the moves.
- [x] Labels sit on the thing they name: amounts on each coin, the confidence word on each call.
- [x] Objects use the shared look: `.coin` for each coin, `.addr` for each address, `.tx` and `.hash` for each move,
  `.conf` for the confidence word; the move menu and the class table need new objects in `look.css`, added when
  the game is built.

## Sources

The theft, the 2.1 BTC, the teams' moves, the crowd, the block numbers and the example's amounts are made up for
the game and say so; the 0.5 BTC pool and 0.5001 BTC pre-mix coins are day 7's chain
(`dynamic-labs/coinjoin-trace/quizes/build-steps.py`).

- Calibration is "the degree of correspondence between a forecaster's subjective probabilities and the observed
  relative frequency of event occurrences"; analysts' forecasts were checked against outcomes and found well
  calibrated, erring mainly towards underconfidence — `@mandel_accuracyforecastsstrategic_2014`
- Pre-mix and post-mix traceability narrows the anonymity set — `@stutz_adoptionprivacycoinjoin_2022`; address reuse
  "directly reveals ownership"; a pre-mix split spends from the traced cluster; timing in the mix —
  `@svenda_coinjoinecosystem_2026`
- Co-spent inputs share an owner, and CoinJoin is the known false positive — `@meiklejohn_fistfulbitcoinscharacterizing_2013`;
  `@gmaxwell_coinjoinbitcoinprivacy_2013`
- A mixer accepts coins and retransmits them to prevent tracing — `@financialcrimesenforcementnetworkfincen_applicationcertainbusinessmodels_2019`
  (as of May 2019); user habits, not the mixer's math, link deposits to withdrawals; matching amounts and timing
  are among them — `@wang_zkpmixers_2023`
- The explorer: mempool, version 3.3.2, AGPL-3.0 — `@mempool_mempool_2026` (as of 31 Oct 2026)
- Confidence words, never a percentage; timing alone Low, a reuse or post-mix co-spend Moderate —
  `@odni_icd203_2015` (the course scale); `lessons/forensics/06-FO-mixers_and_coinjoin.qmd`

## Approval

- Owner: "Approve as drafted (Recommended)" (11 Nov 2026)
- Hiders: "Hiders don't score (Recommended)"; the payoffs and the confidence cap: "Keep both (Recommended)" (owner,
  11 Nov 2026)
- Built in 62d38b76 (11 Nov 2026).
