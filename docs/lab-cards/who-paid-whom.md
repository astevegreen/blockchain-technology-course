# Design card: Who paid whom?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Who paid whom? (review idea 28) |
| Replaces | nothing |
| Opens from | `lessons/forensics/06-FO-mixers_and_coinjoin.qmd`, "Before and after the mix still leak" |
| Day | Day 7, lesson ① (mixers and CoinJoin) |
| Kind | prediction lab (five minutes) |

It prepares the afternoon CoinJoin trace, whose product is a limits-of-tracing note: where the trace stops, and
what still shows. This lab works one CoinJoin round in five minutes, on made-up coins. The afternoon lab follows
a whole trail through rounds and a mixer, where the leaks are planted for students to find.

## The ten lines

1. **The wrong belief**: "A mixer or Monero makes funds untraceable, full stop." Belief 12 on the plan's list,
   marked common by the owner. Here it is the CoinJoin half.
2. **The prediction** (shell: `commit`): "The ransom's coin, 0.1003 BTC, is one of five inputs to this
   transaction. It pays five outputs of 0.1 BTC each. Which output is the ransom's now?" Choices: (a) output 0,
   listed first like the ransom's input; (b) whichever output is spent first afterwards; (c) any of the five,
   because nothing in the transaction pairs an input with an output; (d) none of them: the mix ended the trail, and
   there is nothing more to say. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student draws a line from the ransom's input to the output they believe is
   its, then gives the evidence for the line. The lab offers what the transaction holds: the amounts (all 0.1), the
   address types (all one kind) and the outputs' positions (the lab lists them in a fresh order each run). None of
   these picks an output, so the line turns grey. A participants slider then runs from 2 to 50. Beside it, "the
   ransom's coin could be any of n" and "ways to pair the whole round" both update; with 5 participants the second
   reads 120. Last, a "still shows" panel fills in: the five inputs (who took part), the block and time, and the five
   outputs (the ransom's money is in one of them). Answer (c). Choice (d) is belief 12: the trail narrows to five
   leads, and it does not vanish.
4. **The constraint**: the outputs must all be one size, or the arithmetic pairs them back up. An input of 0.1372
   less a fee can only have become the output that matches it. That is why CoinJoins pay repeated equal amounts, and
   it is also why they are easy to spot. Without the slider, five looks like a small number to guess from. Without
   the "still shows" panel, the stop reads as the end of the case.
5. **The name** (shell: `name`): anonymity set. Parts: anonymity (not knowing which) + set (the equal outputs a
   coin could have become). Plain: how many outputs the coin could now be. The larger the set, the weaker any guess,
   and the set is also the list of leads.
6. **The explorer view** (shell: `explorer`): the round on mempool's transaction page, as the afternoon lab meets
   it. Five inputs show with their addresses and amounts, and five outputs of 0.1 BTC show in the transaction's
   order. The analyst quotes the txid, the block, the time, the inputs and the output amount. The page has no field
   that pairs an input with an output.
7. **The twist** (shell: `twist`): the same round, but two users brought odd-sized coins, and the ransom's is one
   of them: inputs of 0.1372 and 0.2500 BTC among the five. The round pays each of the two its leftover as change, so
   it pays five 0.1 outputs plus 0.0370 and 0.1498. "Which outputs can you now pair with an input?" Choices: none,
   it is still a CoinJoin; all seven; the two change outputs only; the change outputs and the ransom's 0.1. Answer:
   the two change outputs only. Each matches one input by subtraction (0.1372 − 0.1 − its share of the fee =
   0.0370), so the ransom's change is traceable again (Moderate: the amounts add up only one way here). The five 0.1
   outputs are still any of five. Unequal amounts give links back, and a 2014 analysis of one CoinJoin service did
   this at scale.
8. **The sentence** (shell: `tell`): "The agent asks: 'So the money's gone?'" Example: "The ransom cluster's
   0.1003 BTC went into CoinJoin transaction 7c1e…40ab in block 812,400 (Moderate confidence, carried from the
   cluster). The trace stops there: the coin became one of five 0.1 BTC outputs, and nothing in the transaction says
   which. The five outputs are the leads. A later spend that joins two of them, or that pays an address already in
   the ransom cluster, would pick the trace up again."
9. **The game, if any**: none. Day 7's game is hide and trace, in the second half of the day.
10. **The archetype**: simulation.

The opening case (shell: `case`): the ransom the agent has been following went into a transaction with four other
people's coins. "The tool says the trail ends here. Is that it? Do we close this lead?"

Left out, for the owner to see:

- Address reuse, post-mix co-spending and timing ("Before and after the mix still leak") are named in the
  sentence but not shown. The afternoon lab plants them for students to find, so showing them here would give the
  afternoon away.
- Custodial mixers ("A mixer pools coins and pays out others") are not in this lab. A mixer cuts the link instead
  of hiding it, and the afternoon trail runs through one.
- The plan's afternoon idea, in which the class joins one CoinJoin and each student tries to unmix a neighbour, is
  the many-player version of this lab's action. If it is built, this lab is the five-minute warm-up for it.
- Confidence for the twist's change link: Moderate (owner, 11 Nov 2026) (one strong line, the arithmetic). The slide's
  table rates matching amounts across pools Low, but that is a weaker case: amounts paired across separate
  transactions, not inside one.
- PayJoin and dust are separate slides of the same lesson, and they are left to the lesson.

How it is built: the ransom, the five users, every address, amount, txid and block are made up for the lab, and
the lab says so. The lab draws the round and computes the slider's counts itself (n, and n! ways to pair the
round), so it runs offline from `src.zip`. The explorer step shows a saved mempool page of the same made-up round.

## Load check

- [x] One new term per step: anonymity set is the only term named. It is defined on "A CoinJoin is many owners in
  one transaction", and the lab names it after the student has failed to pick an output. "CoinJoin", "pre-mix" and
  "post-mix" come from the slides before.
- [x] Nothing drawn for decoration: the line greys out only when its evidence fails, and the counts move only with
  the slider.
- [x] Labels sit on the thing they name: each amount on its coin, the fee share beside the change output it
  explains.
- [x] Objects use the shared look: `.tx` for the round, `.coin.input`, `.coin.output` and `.coin.change` for the
  coins, `.coin.fee` for the fee, `.addr`, `.hash` for the txid, `.conf` for the confidence word.

## Sources

The ransom, the five users, their addresses, the round (7c1e…40ab, block 812,400) and its twist version are made
up for the lab, and the lab says so.

- A CoinJoin is one transaction that several users build, each signing their own inputs —
  `@gmaxwell_coinjoinbitcoinprivacy_2013`
- The anonymity set: the equal outputs a coin could have become; treating a CoinJoin's inputs as one wallet makes
  clustering "erroneously merge unrelated address groups" — `@svenda_coinjoinecosystem_2026` (the slide "A CoinJoin
  is many owners in one transaction")
- CoinJoin designs pay repeated amounts (Wasabi 1.x about 0.1 BTC; Whirlpool 5 by 5 in fixed pools; WabiSabi
  "arbitrary output denominations"); they are detected with "> 99%" accuracy — `@svenda_coinjoinecosystem_2026`,
  sec. 2.1; `@stutz_adoptionprivacycoinjoin_2022` (as of 31 Oct 2026)
- "The traceability of addresses during the pre-mixing and post-mixing narrows down the anonymity set" —
  `@stutz_adoptionprivacycoinjoin_2022`; address reuse "directly reveals ownership by the same entity" —
  `@svenda_coinjoinecosystem_2026`, p. 564
- A 2014 tool, CoinJoin Sudoku, analysed thousands of transactions from SharedCoin, a CoinJoin service, and "could
  identify relationships between specific payments and payees" — `@coindesk_sharedcoinusersidentified_2014` (read 10 Nov 2026)
- A stop is a fact and takes no confidence word; a lead after it carries its own — the slides "From raw transactions
  to the note's first rows" and "A limits-of-tracing note: where it stops"; `@odni_icd203_2015` (the course scale,
  build spec "Confidence scale")
- The explorer: mempool, version 3.3.2, AGPL-3.0 — `@mempool_mempool_2026` (as of 31 Oct 2026)

## Approval

- Owner: "Approve, Moderate (Recommended)" (11 Nov 2026): the twist's change link carries Moderate
