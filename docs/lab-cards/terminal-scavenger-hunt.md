# Design card: Terminal scavenger hunt

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 8: build the games the owner locked in). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Terminal scavenger hunt (the lab plan's "Every lab" row for day 1's terminal orientation, new) |
| Replaces | nothing: it follows the terminal orientation's four questions, in the same terminal |
| Opens from | `lessons/introduction/02-IN-blockchain_at_a_glance.qmd`, "An explorer is a node's record, plus extras" |
| Day | Day 1, afternoon: after the Insider game and the terminal orientation, before the explorer worksheet |
| Kind | game (alone, one terminal each, about 15 minutes) |

Each student gets one hunt sheet with five facts to find on the class's Bitcoin chain, using only `bitcoin-cli`
in their own terminal. A fact scores only with the command that found it and the output line that proves it. It
turns the orientation's one node query into five, so the explorer worksheet that follows starts from what a node
holds.

## The ten lines

1. **The wrong belief**: "The explorer is the blockchain: what its page says is what the chain says." It is not
   on the plan's list of fifteen; its nearest is belief 14 (a tool's label is proof), since an explorer's tags and
   figures are the explorer's own.
2. **The prediction** (shell: `commit`): "An explorer shows block 5 with its hash, its time, its transactions and
   how many confirmations it has. Which of these does your own node store as part of block 5?" Choices: (a) all
   four; (b) the hash, the time and the transactions; the confirmations are worked out from the node's newest
   block; (c) only the hash; (d) none: the node only relays, the explorer keeps the record. Then High, Moderate or
   Low.
3. **The action** (shell: `do`): the student finds the five facts with `bitcoin-cli`: (1) how many blocks the
   node has (`getblockcount`); (2) block 5's hash (`getblockhash 5`); (3) block 5's time (`getblock <hash>`, the
   `time` line, in seconds since 1970); (4) how many transactions block 5 holds (`nTx`: one, the miner's reward);
   (5) how many confirmations block 5 has. Then the instructor mines one block (`generatetoaddress 1` on the
   instructor node, since nothing on the class chain mines by itself) and the student runs `getblock` again: the
   hash, time and transactions are the same, and the confirmation count has grown by one. A student who picked
   (a) watches a "stored" fact change in front of them. (The page shows each command in full, with the
   `-datadir` the orientation uses.)
4. **The constraint**: day 1's slide tells students to "rely on the first; check the rest" (what the node holds
   against what an explorer works out or adds), but nothing yet makes them ask a node themselves. Analysts quote
   explorer pages in their work; without a direct query they cannot tell the record from the extras.
5. **The name** (shell: `name`): node query. Plain: asking a node directly, with its own tool, for what it holds,
   rather than reading a page someone built on top of it.
6. **The explorer view** (shell: `explorer`): the class's btc-rpc-explorer, block 5's page: the same hash and
   transaction, the time shown as a date in the viewer's time zone, and a confirmation count. The explorer reads
   a node too, so every chain fact on the page matches the student's query; what differs is the form (a date, not
   seconds) and what it works out.
7. **The twist** (shell: `twist`): after the student records fact 5, the instructor mines two more blocks, and
   the explorer now shows block 5 with two more confirmations than the student's answer. "Which is wrong?"
   Choices: the explorer; the student's node; neither: each count is from the newest block seen when it was
   asked, and the explorer has seen blocks the answer has not; the chain has split. Answer: neither, very
   likely. Confirmations are a view from one node's tip at one moment, so two readings can disagree while block
   5 itself, its hash and its time, is the same on both.
8. **The sentence** (shell: `tell`): "Tell a colleague what block 5 is, from your node, in one sentence."
   Example: "My node shows block 5 as hash 0000…a3f1, mined at 14:02 UTC by the miner's clock, holding one
   transaction, the reward; its confirmation count is my node's, not part of the block." (A fact read straight
   off the chain takes no confidence word.)
9. **The game, if any**: terminal scavenger hunt (owner, 10 Nov 2026). Each of the five facts with its command
   and the output line that proves it: +1; a fact with no command, or copied from the explorer: 0. The answer to
   the prediction, with its reason: +1. The twist answered with its reason: +2. Time only breaks ties, within a
   15-minute limit. The command is the reason, so a point only comes from asking the node, and the score is the
   concept.
10. **The archetype**: step-by-step procedure.

The opening case (shell: `case`): a colleague sends a screenshot of an explorer page and writes: "The explorer says
block 5 was mined at 2:02 pm and has 7 confirmations. Can you check that on our own node before I put it in the
file?"

Left out, for the owner to see:

- The class chain is mined fresh at each lab start (the instructor node mines 11 blocks), so the hashes and times
  differ every run. The hunt sheet names facts, not answers, and each answer is checked against the student's
  own screen, as the orientation's question 2 already is. The hunt checker reads the instructor's node for the
  same fact; the instructor mines the action's one block and the twist's two from a short run sheet.
- Fact 3 uses block 5's time, not a payment's: the chain has no payments on day 1 (newly mined coins cannot be
  spent for 100 blocks), so a fee fact is left out.

How it is built: one page on the Bitcoin lab's panel bar, beside the student's terminal: the hunt
sheet, a box per fact for the command and the output line, and an in-house checker that compares each line with
the instructor node's answer for that fact (or with the student's own node, one block either way, for the
confirmations). Bitcoin Core, ttyd and zellij are already in the lab and all open source. The scoring key (which
command finds each fact) goes in `quizes/`, which students never receive.

## Load check

- [x] One new term per step: node query is the only term named; block, hash and confirmation come from the
  morning's lessons.
- [x] Nothing drawn for decoration: the page is the sheet and the student's own output.
- [x] Labels sit on the thing they name: each box names its fact.
- [x] Objects use the shared look: `.hash` for the block hash; the hunt sheet uses the shell's existing step
  boxes.

## Sources

- An explorer shows what a node holds, plus figures it works out and labels it adds; Bitcoin Core's `bitcoin-cli`
  returns the record itself — `lessons/introduction/02-IN-blockchain_at_a_glance.qmd`;
  `@antonopoulos_masteringbitcoinprogramming_2017`; `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- A block's time is set by its miner; confirmations count the blocks on top of it, as seen by one node —
  `@bitcoin.orgdevelopers_blockchaindeveloper_2024`; `@antonopoulos_masteringbitcoinprogramming_2017`
- Newly mined coins cannot be spent until 100 more blocks are mined —
  `@antonopoulos_masteringbitcoinprogramming_2017`
- The class chain: the instructor node mines 11 blocks at a fresh start; the chain identifies as `main` —
  `dynamic-labs/bitcoin/bitcoin-instructor-seed.sh`; `dynamic-labs/bitcoin/README.md` (read 10 Nov 2026)
- Bitcoin Core is open source (MIT) — `@bitcoincore_repository_2026` (as of 10 Nov 2026)

## Approval

- Owner: selected "Terminal scavenger hunt,Two-of-three,Spot the fake,Find the exchange" (11 Nov 2026)
