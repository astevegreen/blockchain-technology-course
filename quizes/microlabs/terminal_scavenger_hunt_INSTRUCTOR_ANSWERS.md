# Terminal scavenger hunt: instructor key and run sheet

Instructor only (students never receive `quizes/`). Day 1 afternoon, after the Insider game and the terminal
orientation, before the explorer worksheet. Design card `docs/lab-cards/terminal-scavenger-hunt.md`. Page: the
**Hunt** button on the Bitcoin lab's panel bar (served by lane-service at `/api/bitcoin/hunt/`, from
`dynamic-labs/lane-service/labs/bitcoin_hunt/`). Alone, one terminal each, about 15 minutes.

## What the page checks

The class chain is mined fresh at each lab start (the instructor node mines 11 blocks), so there is no fixed
answer. For each fact the student pastes the command they ran and the output line that proves it; lane-service's
checker (`dynamic-labs/lane-service/labs/bitcoin_hunt.py`) reads the same fact from the instructor's node, or from
the student's own node for the confirmations (one block either way), and says right or wrong with a reason. It
never shows the expected value. A correct fact locks; a wrong one can be tried again.

## The five facts (the scoring key)

Every command is `bitcoin-cli -datadir=/home/user/.bitcoin …`; the page shows each in full.

| # | Fact | Command that finds it | Line that proves it |
| --- | --- | --- | --- |
| 1 | How many blocks the node has | `getblockcount` | the one number it prints (the student's node or the instructor's: they match once synced) |
| 2 | Block 5's hash | `getblockhash 5` | the 64-character hash |
| 3 | Block 5's time | `getblock <block 5's hash>` | `"time": …`, seconds since 1970, set by the miner's clock |
| 4 | Transactions in block 5 | `getblock <block 5's hash>` | `"nTx": 1` (the miner's reward) |
| 5 | Block 5's confirmations | `getblock <block 5's hash>` | `"confirmations": …`, the student's node's count |

`getblock $(bitcoin-cli … getblockhash 5)` also counts. What the checker refuses, with the reason it gives:

- a command that is not `bitcoin-cli`, or asks for something else (`getblockchaininfo`, `getbestblockhash`,
  `getblockhash 50`, `getblock` on another block);
- a date in place of the `"time"` line (copied from the explorer, which shows the time as a date: the card's "0");
- the `"mediantime"` line in place of `"time"` (worked out from the last 11 blocks, not block 5's own).

## Run sheet

Mine on the instructor node (nothing on the class chain mines by itself). From the instructor host:

```bash
ADDR=$(docker exec -u 1000 bitcoin-instructor-1 bitcoin-cli -datadir=/home/user/.bitcoin -rpcwallet=instructor_seed getnewaddress)
```

```bash
docker exec -u 1000 bitcoin-instructor-1 bitcoin-cli -datadir=/home/user/.bitcoin generatetoaddress 1 "$ADDR"
```

1. Students start the hunt (Hunt on the panel bar) and work facts 1 to 5.
2. When most have fact 5, **mine one block** (the second command, with `1`). Students run `getblock` on block 5
   again and paste the new `"confirmations"` line: the checker accepts it only once it has grown. Hash, time and
   transaction are the same.
3. Students open the class explorer at block 5, then reach the twist. **Mine two more blocks** (`generatetoaddress
   2 "$ADDR"`) so the explorer shows two more confirmations than their re-run (three more than fact 5).

(`instructor_seed` is the wallet
`bitcoin-instructor-seed.sh` creates; `bitcoin-instructor-1` is the instructor container's name.)

## The prediction

Correct: **(b)** the hash, the time and the transactions; the confirmations are worked out from the node's newest
block. A student who picked (a) watches a "stored" fact change after you mine one block.

## The twist

Correct: **neither** (third choice). Each count is from the newest block seen when it was asked; the explorer has
seen blocks the student's answer has not. Block 5 itself, its hash and its time, is the same on both.

## Scoring (owner's design, 10 Nov 2026)

| Item | Points |
| --- | --- |
| Each of the five facts, with its command and the line that proves it | +1 each (5) |
| A fact with no command, or copied from the explorer | 0 |
| The prediction answered (b), with its reason | +1 |
| The twist answered "neither", with its reason | +2 |
| **Most** | **8** |

The page keeps the score at the bottom and the time since the student opened the hunt; time only breaks ties,
within the 15-minute limit (the clock turns red past 15:00). The page scores a reason only with the correct
answer; read the reasons aloud when you go over the twist. The re-run after you mine is not scored: it is the
lesson.

## The sentence

A fact read straight off the chain takes no confidence word. Example: "My node shows block 5 as hash 0000…a3f1,
mined at 14:02 UTC by the miner's clock, holding one transaction, the reward; its confirmation count is my
node's, not part of the block."
