# Design card: Which one is real?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Which one is real? (review idea 30) |
| Replaces | nothing |
| Opens from | `lessons/forensics/07-FO-privacy_coins.qmd`, "Old Monero leaked: zero decoys, newest is real" |
| Day | Day 7, lesson ② (privacy coins) |
| Kind | prediction lab (five minutes) |

It opens after the three slides it needs: the ring of 16 ("A ring hides the spender among 15 decoys"), what an
explorer shows ("What a Monero explorer shows, and what it hides") and the 2018 study. The prediction is aimed at
the student who has just heard "newest is real" and wants to use it on today's Monero. The twist then shows where
the study's results do apply. "Who paid whom?" (day 7 ①) does the same for a CoinJoin; this card is the Monero
half of belief 12.

## The ten lines

1. **The wrong belief**: "A mixer or Monero makes funds untraceable, full stop." Belief 12 on the plan's list,
   marked common by the owner. Here it is the Monero half.
2. **The prediction** (shell: `commit`): "The ransom went to a swap service, which paid out in Monero. This 2024
   Monero transaction is the suspect spending it. Its one input has a ring of 16, listed with each member's age.
   Which member is the ransom's coin?" Choices: (a) the newest, because the study found the newest was real; (b)
   the one that appears in the fewest other rings; (c) undetermined: it is one of 16, and nothing on the chain picks
   one; (d) nothing about this transaction can be said at all. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student clicks the member they predicted and gives the on-chain reason for
   it. The lab tests each reason: age (the study measured early Monero only), how often a member appears elsewhere
   (every member is a real output that other rings can also use), position in the list (the lab shuffles it each
   run). None holds, so the pick turns grey. Then the lab opens its made-up truth: the real member was the ninth
   newest, not the newest. Last, a "still shows" panel fills in what can be quoted: the txid, the block and time, the
   fee, one input and two outputs, the 16 ring members and the key image. Answer (c). Choice (d) is belief 12: the
   spender is hidden, and the transaction is still a dated, quotable record.
4. **The constraint**: decoys are real outputs drawn from the chain, so a member's history cannot mark it as a
   decoy. The key image changes only if the same output is spent twice, so it shows that an output was spent, never
   which member. Without the made-up truth, a lucky guess on (a) feels like proof. Without the "still shows" panel,
   "undetermined" reads as "nothing to report".
5. **The name** (shell: `name`): mixin. Parts: mix (blend in) + in (added to the ring). Plain: a decoy, under the
   name the 2018 study and many tools use. A ring of 16 has 15 mixins. An input with zero mixins has a ring of one:
   it names the output it spent, like Bitcoin.
6. **The explorer view** (shell: `explorer`): a Monero transaction page that the lab draws, with the fields from
   "What a Monero explorer shows, and what it hides". Shown: the txid, the block, the time, the fee, the input and
   output counts, each input's ring of 16 and its key image. Each output is a one-time key with its amount hidden,
   and no field says who paid whom. The analyst quotes the first group and writes "not shown" for the rest.
7. **The twist** (shell: `twist`): the date changes. The same suspect's 2016 transaction has an input with a ring
   of three: one fresh member and two old ones. The lab shows that each old member was spent elsewhere by an input
   with zero mixins, which named it outright. "Which member is real now?" Choices: still undetermined, one of
   three; the newest; the fresh member, because the other two were already spent; none, a ring hides the spender.
   Answer: the fresh member (Moderate: a published heuristic, with known misses). An output is spent only once, so a
   member already spent elsewhere cannot be this ring's real one. Early Monero leaked this way at scale, before the
   minimum of four mixins (September 2017) and the ring of 16 (August 2022). The trace's reach depends on when the
   transaction was made.
8. **The sentence** (shell: `tell`): "The agent asks: 'So we lost him at the swap?'" Example: "The ransom
   cluster's 2.0 BTC reached a swap service's deposit address in block 812,400 (Moderate confidence, carried from the
   cluster). The swap paid out in Monero, and the trace stops there: the suspect's spend in transaction 5b2e…91cd
   uses a ring of 16, and nothing on the chain says which member is his. That transaction's time, fee and shape
   are on record. A later Monero-to-Bitcoin swap paid out 1.97 BTC six hours on; it
   matches by amount and timing only (Low)."
9. **The game, if any**: none. Day 7's game is hide and trace, in the second half of the day.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): the agent has the swap service's receipt showing the ransom left as Monero. "The
vendor's tool says Monero is a dead end. Is there anything you can tell me about this transaction?"

Left out, for the owner to see:

- Guess-newest (the 2018 study's "about 80%") is the trap in the prediction, not a twist of its own. The
  chain-reaction twist is the one the study applies to, and the lab says the study measured early Monero only.
- The edges ("The edges still show: ramps, swaps, delistings") appear only as the sentence's Low lead. The lesson
  covers them two slides later, and the afternoon lab's note uses them.
- Zcash and view keys are separate slides of the same lesson, and they are left to the lesson.
- The explorer is drawn by the lab, not a named tool. Naming a real Monero explorer would need its source and
  licence checked first (CLAUDE.md's open-source rule), and the card does not need one.
- Monero's ring is 16 as of 31 Oct 2026. The Monero project's roadmap lists "Full-Chain Membership Proofs" under
  "Coming Soon", with no date (read 10 Nov 2026). If that upgrade activates before the course runs, the 2024
  example stays true of 2024, but "today's Monero" would change. Recheck on the build day.

How it is built: the suspect, the swap, the ransom, both Monero transactions, their rings, ages, key images and the
made-up truth are made up for the lab, and the lab says so. The lab draws the transactions in the shared look and
shuffles the ring order each run, so it runs offline from `src.zip`.

## Load check

- [x] One new term per step: mixin is the only term named. "Ring", "decoy" and "key image" come from "A ring hides
  the spender among 15 decoys", and the lab names "mixin" just before the twist turns on it.
- [x] Nothing drawn for decoration: a pick greys out only when its reason fails, and the truth opens only after the
  student has committed.
- [x] Labels sit on the thing they name: each age on its ring member, the "spent elsewhere" mark on the member it
  rules out.
- [x] Objects use the shared look: `.tx` for each transaction, `.coin.input` for the ring members, `.coin.output`
  for the one-time keys, `.coin.spent` for members spent elsewhere, `.coin.fee` for the fee, `.key` for the key
  image, `.sig` for the ring signature, `.hash` for the txids, `.conf` for the confidence word.

## Sources

The suspect, the swap, the ransom, transaction 5b2e…91cd and its 2016 counterpart, their rings, ages and key images,
and the made-up truth are made up for the lab, and the lab says so.

- A ring signature proves that one member of the ring signed, not which; decoys are earlier outputs from the chain;
  Monero's privacy is on by default — `@koe_zeromonerosecond_2020`
- Rings of 16 (15 decoys) since the August 2022 upgrade, block 2,688,888 (11 before) —
  `@monero_networkupgradejuly_2022` (as of 31 Oct 2026)
- Each spent output gives one key image, and a second spend shows the same image and is refused —
  `@monerocommunityundermit_moneroprivatekey_2025`
- Each output is a one-time key, and a Monero address is never found on chain — `@monero_stealthaddress_2025`;
  `@koe_zeromonerosecond_2020` (the slide "What a Monero explorer shows, and what it hides")
- 64.04% of inputs in the study's data had no decoys and named the output they spent; spent outputs could then be
  struck off other rings, tracing about 62% of inputs with decoys; guessing the newest member was right about 80% of
  the time; a minimum of 4 decoys from September 2017; RingCT hid amounts, not the spender; "mixin" is the study's
  word for a decoy — `@moser_empiricalanalysistraceability_2018`, secs. 1–2
- Which ring member was spent today is undetermined and takes no word; an old input traced by a published heuristic
  is Moderate; a swap payout matched by amount and timing is Low — the slide "How sure: words for a trail that goes
  dark"; `@odni_icd203_2015` (the course scale, build spec "Confidence scale")
- The roadmap lists "Full-Chain Membership Proofs" under "Coming Soon", with no date — `@monero_roadmap_2026`
  (as of 10 Nov 2026)

## Approval

- Owner: "Approve (Recommended)" (11 Nov 2026)
