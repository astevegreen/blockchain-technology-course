# Design card: What time was it sent?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 4: the lab proposed for belief 8). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | What time was it sent? (new: proposed for belief 8, which had no lab) |
| Replaces | nothing |
| Opens from | `lessons/bitcoin/02-BF-transactions_and_mining.qmd`, "A transaction has no timestamp of its own" |
| Day | Day 2, lesson ① (reading a Bitcoin transaction) |
| Kind | prediction lab (five minutes) |

## The ten lines

1. **The wrong belief**: "A transaction's time is when it was sent." Belief 8 on the plan's list; the owner did
   not mark it common, and chose to have a lab proposed for it ("Propose one in step 4").
2. **The prediction** (shell: `commit`): "Ana pressed Send at 09:02 by her phone's clock. The explorer shows 09:09
   beside her payment. What is 09:09?" Choices: when Ana pressed Send; when the first node saw the payment; the
   time the miner wrote in the block that included it; when the explorer read the payment. Then High, Moderate or
   Low.
3. **The action** (shell: `do`): a wall clock, Ana's phone, a pool of waiting payments and a row of blocks. The
   student presses Send at 09:02 with a low fee and watches the payment wait in the pool while blocks with
   better-paying transactions go by. A miner whose clock runs a few minutes slow finally includes it and stamps
   the block 09:09, though the block before it says 09:11; the chain accepts it. The student opens the payment's
   own fields: inputs, outputs, locktime 0. No field says 09:02, or any time at all. (Why a low fee waits is the
   next slide, "Fees are priced per virtual byte"; here the wait is only shown, and the instructor points ahead.)
4. **The constraint**: thousands of strangers' computers share no clock, and none can be trusted to keep the
   time for the rest. So a transaction carries no time of its own; the miner writes one time per block, and the
   rules accept it within loose limits, not in strict order. What every node does agree on is the order of the
   blocks, because each one names the block before it.
5. **The name** (shell: `name`): block time. Parts: block + time, the time written in the block. Plain: the time
   the miner put in the header of the block that included a transaction; it is the miner's claim, not the moment
   anyone sent anything.
6. **The explorer view** (shell: `explorer`): Alice's payment from the slides on a Bitcoin explorer: the time
   printed beside it, the block it sits in (277,316) and the locktime field (0). The printed time is block
   277,316's time, 1388185914, which is 27 Dec 2013, 23:11:54 UTC. A report says "block time" and gives the
   block.
7. **The twist** (shell: `twist`): two blocks. Block 800,001 is stamped 10:05; block 800,002 is stamped 10:03. A
   payment in each. "Which payment did the chain record first?" Choices: the one in 800,002, it has the earlier
   time; the one in 800,001, it has the lower height; both at once; there is no way to tell. Answer: the one in
   800,001. Each block names the block before it, so height sets the order of recording; the times only show
   that one miner's clock disagreed with another's, which the rules allow. Which was *sent* first, the chain
   cannot say: as the action showed, a payment can wait in the pool while later ones are mined.
8. **The sentence** (shell: `tell`): "The agent asks when Ana sent the payment." Example: "The payment was
   confirmed in block 812,331, whose miner stamped it 09:09 UTC; the chain does not record when it was sent. It
   was sent some time before that block was mined, and the stamp is the miner's claim, so it may have been sent
   before 09:05 (Low confidence on when it was sent: timing alone)."
9. **The game, if any**: none. The prediction and the twist are the hook.
10. **The archetype**: simulation.

The opening case (shell: `case`): an agent has a timeline. The suspect's alibi covers 09:00 to 09:05, and the
explorer shows a payment from the suspect's wallet at 09:09. "So the payment was sent after the alibi ends,
right?"

## Load check

- [x] One new term per step: block time is the only new term; "locktime" is read off the explorer as a field
  name from the slide, and "height" was named on day 1.
- [x] Nothing drawn for decoration: the clocks, the pool and the stamps are what the student predicts.
- [x] Labels sit on the thing they name: each time on the clock or block that holds it.
- [x] Objects use the shared look: `.hash` for the txid and block hashes, `.coin` objects for the payment's
  inputs and outputs, `.conf` for the confidence word; gold only on Send and the fee control.

## Sources

Ana, her clock times and blocks 812,331, 800,001 and 800,002 are made up for the lab and say so; Alice's payment is the
real example.

- The consensus rules "do not mandate strict ordering of block timestamps", so a block can show an earlier time
  than the one before it — `@kerin_bip113mediantimepast_2015`
- Locktime: the earliest point a transaction may be mined; a height below 500 million, a Unix time otherwise —
  `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- Miners choose transactions mostly by fee per byte; a minimum-fee transaction "should be prepared to wait a
  long time" — `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- Each block header names the previous block's hash, which fixes the order — `@bitcoin.orgdevelopers_blockchaindeveloper_2024`
- Alice's payment: locktime 0; block 277,316, time 1388185914 (27 Dec 2013, 23:11:54 UTC) —
  `@antonopoulos_masteringbitcoinprogramming_2017`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Approve all four" (10 Nov 2026)
- Built in 902d1a64 (11 Nov 2026).
