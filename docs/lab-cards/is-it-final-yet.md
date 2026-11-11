# Design card: Is it final yet?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 4). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Is it final yet? (review idea 9) |
| Replaces | `pos-micro` (archived: it taught that going offline is slashed) |
| Opens from | `lessons/ethereum/01-EF-ethereum_intro.qmd`, "Pending, then included, then final" |
| Day | Day 3, lesson ① (accounts, the EVM and transactions) |
| Kind | prediction lab (five minutes) |

Why day 3 and not day 1: the natural slide, "Each chain puts a different number on 'final'", is in day 1's
lesson ③, which already opens the confirmation race, and a lesson opens one prediction lab at most. Day 3's slide
says inclusion is not finality and points back to day 1, and by then students have met an Ethereum block.

## The ten lines

1. **The wrong belief**: "Once it appears in an explorer, it has happened and cannot be undone." Belief 7 on the
   plan's list, in its cross-chain form (the confirmation race takes its depth form); the owner did not mark it
   common.
2. **The prediction** (shell: `commit`): "The same payment was made on Bitcoin, Ethereum and Tron eight minutes
   ago. The agent asks whether the money has moved for good. On which chains can you say it is final?" Choices:
   all three; Ethereum and Tron; Tron only; none. Then High, Moderate or Low.
3. **The action** (shell: `do`): three lanes, one per chain, and a clock the student drags from 0 to 70 minutes.
   Each lane shows the payment's state as time passes, in that chain's own words: Tron's block is "solidified"
   within about a minute; Ethereum's block is included at once but its checkpoint finalized only at about
   15 minutes (12.8 at best); Bitcoin's count climbs a block at a time and never says "final", with six
   confirmations at about an hour. At eight minutes only Tron's lane says final.
4. **The constraint**: an open chain cannot count votes from strangers, so Bitcoin makes reversal costlier with
   every block and never declares an end, and Ethereum waits for a vote of two-thirds of its stake. Tron's 27
   producers are known and few, so it can count them quickly. Each design answers "who may vote?" differently, so
   each puts a different clock on "final".
5. **The name** (shell: `name`): finality. Parts: final + -ity, the state of being final. Plain: the point after
   which a chain's own rules say a block will not be reversed. Bitcoin has no such point, only depth.
6. **The explorer view** (shell: `explorer`): the status each explorer prints. A Bitcoin explorer: a
   confirmations count. An Ethereum explorer: the block's status, included or finalized. A Tron explorer: whether
   the block is solidified. A report gives that status, the block and the time it was read.
7. **The twist** (shell: `twist`): back to Ethereum. More than a third of the stake stops voting. The clock
   reaches 20 minutes; new blocks keep arriving on top of the payment's block, but its status stays "included".
   "Is it final now?" Choices: yes, it has many blocks on top; yes, 15 minutes have passed; no: finality has
   stopped while blocks keep coming; no: the payment failed. Answer: no, finality has stopped. Blocks keep coming
   but stop being finalized until the protocol drains the non-voters' stake (the inactivity leak). The payment is
   recorded, not final: say so and check again.
8. **The sentence** (shell: `tell`): "Tell the agent where the payment stands at eight minutes." Example: "As of
   09:38, the Tron transfer is in a solidified block and can be stated as fact; the Ethereum transfer is in block
   N but not yet finalized, and I will check again before we rely on it; the Bitcoin payment has one
   confirmation, so a reversal is unlikely but still possible (Moderate confidence that it stands)."
9. **The game, if any**: none. The plan marks the case for a game weak: it stays a judgment call.
10. **The archetype**: simulation.

Left out, for the owner to see: the review's idea also had students sort four pieces of evidence into "offline"
and "slashed". It adds a second belief and a second term, so it stays with the slide "Slashing — Making
Misbehavior Expensive" (`lessons/consensus_primitives/03-CM-pos.qmd`), which day 1's lesson ③ does not absorb. The twist's answer states only that the non-voters lose stake slowly.

The opening case (shell: `case`): a victim paid a scammer three times, minutes apart, on three different chains.
An agent calls eight minutes after the last payment: "Has the money gone? Can it still come back?"

## Load check

- [x] One new term per step: finality is the only new term; "solidified" and "finalized" appear as each
  explorer's own status words, and "inactivity leak" only in the twist's answer, as on the slide.
- [x] Nothing drawn for decoration: each lane's state is what the student predicts.
- [x] Labels sit on the thing they name: each status on its own block.
- [x] Objects use the shared look: `.hash` for blocks and transactions, `.coin` for the payment in each lane,
  `.conf` for the confidence word; gold only on the clock.

## Sources

The victim, times and blocks are made up for the lab and say so.

- Bitcoin never declares finality; six confirmations, about an hour, is the usual wait —
  `@bitcoinorg_payment_2026` (as of 23 Oct 2026); `@nakamoto_bitcoinpeertopeerelectronic_2008`
- Ethereum: slots of 12 seconds, epochs of 32 slots (6.4 minutes) — `@ethereumorg_glossary_2026` (as of 23 Oct 2026)
- Ethereum finality by votes from two-thirds of staked ETH, about 15 minutes; 12.8 minutes at best is the
  slides' arithmetic from the epoch — `@ethereumorg_pos_2026`; `@ethereumorg_ssf_2026` (as of 23 Oct 2026)
- Inclusion is not finality — `@ethereumorg_transactions_2025`; `@ethereumorg_ssf_2026` (as of 31 Oct 2026)
- If more than a third of the stake stops voting, blocks keep coming without finality until the inactivity leak
  drains the non-voters' stake — `@ethereumorg_pos_2026` (as of 23 Oct 2026)
- Tron: a block is solidified once 19 of the 27 Super Representatives have produced blocks at or above it; about
  a minute, no fixed upper bound — `@tron_consensus_2026` (as of 23 Oct 2026)
- Open chains price influence in work or stake because they cannot count identities —
  `@bano_consensusageblockchains_2017`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale").
  Stating a finalized transfer as fact, and giving the time a status was read, is the course's method from the
  slide "Finality says the record holds, not who did it", not a sourced fact.

## Approval

- Owner: "Approve all four" and "Keep day 3" (10 Nov 2026)
- Built 11 Nov 2026: `blockchain-course/assets/labs/is-it-final-yet/`; opens from the "Pending, then included, then final" slide in 01-EF.
