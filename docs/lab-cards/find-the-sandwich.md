# Design card: Find the sandwich

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Find the sandwich (review idea 20) |
| Replaces | `ether_mev` |
| Opens from | `lessons/ethereum/03-EF-ethereum_network.qmd`, "A sandwich: three transactions, one victim" |
| Day | Day 4, lesson ① (the Ethereum network) |
| Kind | prediction lab (five minutes) |

The slides before it teach a swap against a pool ("A DEX swaps against a pool, not a person"), reading a swap's
logs ("Reading a swap: two Transfers and a Swap"), MEV as profit from choosing the order, and the sandwich itself:
same block, same pool, consecutive positions, the outer two by one bot, with `amountOutMin` capping the damage.
The slides after it say who sets the order and that "position next to a trade is not evidence of a link to it".
The old `ether_mev` put the student in the proposer's seat with every transaction labelled; this lab hands the
analyst an ordered block with no labels.

## The ten lines

1. **The wrong belief**: "Trades side by side in a block are linked: the address that traded just before and just
   after the subject was trading with them, or working with them." Not on the plan's list; it is the belief
   review idea 20 breaks, and the one the lesson's "What to say" answers.
2. **The prediction** (shell: `commit`): "In block A the subject's swap of 10,000 USDC for token X sits at
   position 4. Address 0xB07…e2 bought X at position 3 and sold X at position 5, in the same pool. Is 0xB07…e2
   working with the subject?" Choices: (a) yes, a partner trading in concert; (b) it is the counterparty that sold
   the subject the X; (c) no, a third party that took value from the subject's trade; (d) position alone says
   nothing. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student steps through block A's swaps in pool X/USDC in position order, each
   with its sender, what went in and out, and the pool's price after it: 0.2000, then 0.2063 after 0xB07…e2 buys
   15,455 X with 3,149 USDC, 0.2271 after the subject, 0.2198 after 0xB07…e2 sells the same 15,455 X for 3,443
   USDC. The student marks the three positions and names the evidence: one address on both sides, the sale undoes
   the purchase, and the subject received 46,058 X, its minimum, against the 47,483 X its quote promised. Answer
   (c): about 294 USDC moved from the subject's trade to the bot; the subject traded with the pool, so (b) fails.
   Then block B, the look-alike: 0xA7…41 buys X before the subject and 0xC3…9d sells X after. The student marks it
   "no sandwich": two addresses, a sale of X held long before, and a subject who got 46,571 X, above its minimum.
   Last, the fields: each `Swap` log's `amount0In`, `amount1Out` and `to`, and the subject's `amountOutMin`.
4. **The constraint**: a block's order is set by its builder, not by the traders. A searcher who sees the subject's
   swap waiting in the public mempool can pay for the places either side of it, so neighbours share a moment, not
   a purpose. The pattern shows a sandwich (one address on both sides, the purchase undone, the victim held to its
   minimum); position alone shows nothing, and the old lab's ready-made labels hid that.
5. **The name** (shell: `name`): slippage tolerance. Parts: slippage (the change in price while a swap waits to
   run) + tolerance (how much of it the trader accepts). Plain: the worst price the trader agreed to, written into
   the swap as its minimum output; below it the swap fails. A sandwich bot pushes the price to just inside it, so
   the tolerance sets how much the bot can take.
6. **The explorer view** (shell: `explorer`): Otterscan's block page lists the transactions in position order with
   From and To. The analyst opens positions 3, 4 and 5: the same From at 3 and 5, each `Swap` log from the same
   pool, and the token `Transfer` logs showing the X bought at 3 leaving at 5. The subject's decoded input
   (`swapExactTokensForTokens`) shows its `amountOutMin`, and its X `Transfer` matches it.
7. **The twist** (shell: `twist`): one slider, the subject's slippage tolerance. At 3% the bot takes about 294
   USDC; at 1%, about 98; at 0.5%, about 49. The made-up bot pays about 60 USDC in fees and to the builder for
   each sandwich. "At 0.5%, would block A hold a sandwich?" Answer: no. A searcher pays up to what the trade
   earns it and no more, and here the cost would exceed the take. A tight tolerance has its own cost: the swap
   fails if the price moves for any reason.
8. **The sentence** (shell: `tell`): "The agent asks whether 0xB07…e2 is the subject's partner." Example: "In
   block A the subject's swap at position 4 was sandwiched by 0xB07…e2, an MEV bot that bought 15,455 X just
   before it and sold the same 15,455 X just after, taking about 294 USDC from the trade (Moderate confidence:
   one address on both sides, and the sale undoes the purchase, all read from these three transactions; the bot's
   other blocks would be a second line). The bot was a third
   party, not the subject's counterparty or partner."
9. **The game, if any**: none. Day 4's game, pool trading in the afternoon, makes the students the traders,
   setting their own tolerance against a bot. This lab makes them the analyst reading a finished block: no
   trading, no score, and its pool, bot and numbers are not the game's.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): an agent tracing a subject's funds sees the subject swap 10,000 USDC for a token.
The address that traded just before the subject also traded just after. The agent asks: "That has to be a
partner. Should we add it to the case?"

Left out, for the owner to see:

- A lone back-run (an arbitrage bot trading right after a big swap, with nothing before it) is a second
  look-alike; one is enough for five minutes, and the slide "An MEV bot trades beside you, not with you" covers it.
- Searchers, builders, relays and private order flow (the next slide) are named but not modelled; the student
  never builds a block.
- Bots that split the two legs across two addresses would defeat the "one address" test; the card keeps one bot.
- The twist teaches the defence (a tighter tolerance) that the afternoon game rewards; it is kept, for the owner
  to confirm, because the game still scores the trading, not the knowing.

How it is built: both blocks, the pool, the bot, the other traders, the subject, their addresses, the 60 USDC cost
and every amount are made up for the lab and say so; the amounts are worked from the constant product with the
0.3% fee. The lab computes the slider's values itself, so it runs offline from `src.zip`.

## Load check

- [x] One new term per step: slippage tolerance is the only term named. Sandwich, front-run, back-run, MEV,
  searcher and `amountOutMin` come from the slides before it; price impact is not used.
- [x] Nothing drawn for decoration: the price line moves only as each swap runs, and the bot's take moves only
  with the slider.
- [x] Labels sit on the thing they name: the price after each swap on that swap, the minimum beside the subject's
  received amount.
- [x] Objects use the shared look: `.addr` for the bot, the traders and the subject, `.hash` for each
  transaction, `.coin.input` and `.coin.output` for each swap's in and out, `.coin.fee` for the bot's cost, `.conf`
  for the confidence word.

## Sources

Blocks A and B, pool X/USDC, 0xB07…e2, 0xA7…41, 0xC3…9d, the subject, the 60 USDC cost and every amount are made
up for the lab and say so.

- A sandwich: the same block, the same pool, consecutive positions, the outer two by the same bot — the opening
  slide, on `@ethereumorg_mev_2026`; a searcher
  watches the mempool for large DEX trades; sandwiched users "face increased slippage" — `@ethereumorg_mev_2026`
  (read 31 Oct 2026; the slide's source)
- The router refuses a swap whose output falls below `amountOutMin`; `swapExactTokensForTokens` carries it —
  `@uniswaplabs_uniswapv2router02_2020`
- Slippage is the price change "while a submitted transaction is pending"; a slippage tolerance is the change
  the user accepts, and outside it "the transaction will fail" — `@uniswaplabs_understandingswaps_2026` (read 10
  Nov 2026)
- A searcher pays fees up to its MEV and no more, "because if the gas fee was higher, the searcher would lose
  money" — `@ethereumorg_mev_2026`
- A pool trades by x·y = k with a 0.3% fee, which sets every amount here — `@adams_uniswapv2core_2020`;
  `@uniswap_v2pair_2020` (the `Swap` log's fields)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Find the sandwich,What is it really worth,Beat the freeze,The vault that paid twice" (11 Nov 2026)
- The twist is kept, although the afternoon game rewards the same defence (owner, 11 Nov 2026)
