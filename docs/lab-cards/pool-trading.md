# Design card: Pool trading

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 8: build the games the owner locked in). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Pool trading (the lab plan's "Every lab" row for day 4's exchange and bridge lab, new; it also covers review idea 20, find the sandwich) |
| Replaces | nothing: it follows the swap-and-bridge worksheet, on the same L1 chain |
| Opens from | `lessons/ethereum/07-EF-liquidity_and_exits.qmd`, "A bigger trade gets a worse price" |
| Day | Day 4, afternoon, last: after the bridge questions |
| Kind | game (alone, one seat each, three rounds, about 40 minutes) |

The whole class trades against the lab's one pool (cUSD and WETH) in three rounds, each student swapping 1 ETH
for cUSD per round, as the swap page already does. Before each trade the student predicts what they will get and
sets the least they will accept. An in-house bot watches trades waiting for the next block and sandwiches any
whose limit leaves it room. After each block, students find their own trade and say whether they were
sandwiched. Each seat's ending balance is shown as the consequence.

## The ten lines

1. **The wrong belief**: "The price the page quotes is the price I get." Belief 11 on the plan's list (a
   token's quoted value is what it sells for).
2. **The prediction** (shell: `commit`): "You swap 1 ETH for cUSD. The page quotes what the pool would pay you
   now, your own trade's effect included. You accept any amount (no minimum). What do you get?" Choices: (a) the
   quote; (b) more than the quote: the pool rewards a large trade; (c) possibly much less: anyone who sees your
   trade before the block can move the price against you first; (d) nothing: the trade fails. Then High,
   Moderate or Low.
3. **The action** (shell: `do`): each round the student works out their output from the pool's reserves (the
   lesson's formula, on the page), picks a limit (none, 5% or 0.5% below the quote) and sends the swap in their
   turn. When the block arrives they read what they got. Those with no limit find well under the quote: the bot
   bought cUSD just before them and sold it just after. Those with a 0.5% limit get close to the quote, because
   the bot leaves them alone.
4. **The constraint**: the lab's swap page fixes the limit at 99% of the quote, and the chain's worked examples
   trade with no limit and no bot, so students read about sandwiches on a slide but never pay for one. A careless
   limit has to cost them something in front of them, or the router's minimum stays a field name.
5. **The name** (shell: `name`): slippage tolerance. Parts: the quote, the least you will accept (in the swap it
   is `amountOutMin`), and the router's check that refuses the trade if the output would be lower. Plain: how much
   worse than the quote you will let the price get before the trade is refused.
6. **The explorer view** (shell: `explorer`): Otterscan, the block with the student's trade: transactions in
   order, and each swap's `Swap` and `Sync` events on the pool. A sandwich is three in a row on the same pool:
   one address buys cUSD, the victim buys cUSD at a worse price, the same address sells its cUSD back; the bot's
   profit is the ETH it got back less the ETH it paid.
7. **The twist** (shell: `twist`): round 3 has no bot, but in a few chosen blocks the instructor's account swaps
   20 ETH for cUSD just ahead of a student's trade, the same way the student trades. "Your trade got much less
   than the quote, or was refused. Were you sandwiched?" Choices: yes: you got less; yes: a big trade came first;
   no: no one bought before you and sold after you; cannot tell. Answer: no. A sandwich needs the same account
   on both sides of your trade; one large trade ahead is price impact from another trader, not someone profiting
   from where you sit in the order. A 0.5% limit is refused here, `too little received`, and the student keeps
   their ETH.
8. **The sentence** (shell: `tell`): "Tell the agent what happened to the victim's trade in block 214." Example:
   "The victim's swap of 1 ETH received 1,850 cUSD, against a quote of 1,950. In the same block, account
   0xB07… bought cUSD from the same pool just before the victim and sold it back just after, ending about
   0.04 ETH up. The order of the three trades is read straight from the block. We assess with Moderate confidence
   that the account set out to profit from the victim's trade rather than trading twice by chance: its gain fits a
   sandwich, but every part of the case comes from the same three transactions."
9. **The game, if any**: pool trading (owner, 10 Nov 2026). Per round: the predicted output with its working,
   +1; the limit chosen with its reason, +1; "sandwiched or not" with the three transactions (or why there are
   none), +2. A sandwich called where there was none, -2. Time only breaks ties. The ending balance is shown on
   the page for each seat but does not score: a careless trader loses money, and the points go to seeing why.
10. **The archetype**: simulation.

The opening case (shell: `case`): a trader complains to the exchange: "I sold at the price on the screen and got
far less. The exchange cheated me." The exchange is a pool, and the trade is on the chain.

Left out, for the owner to see:

- The plan's row said "ranked by what each ends with". The owner's approved scoring says a correct answer with
  its reason scores and time only breaks ties, so this card scores the calls and shows the balances. Ranking by
  balance would reward a student who never trades.
- Trades are staggered: the game page gives each seat a turn, one student trade per block, so a round of 40
  seats takes about 8 minutes of 12-second blocks. Otherwise every student's trade would be another's "big trade
  ahead", and rounds 1 and 2 would blur into the twist.
- The bot sandwiches only trades whose limit leaves it a profit after both pool fees, as a real bot does; a
  student who sets 0.5% is never sandwiched, which is the lesson.
- Who sets the order on Ethereum (searchers, builders, relays) stays on day 4's slides: here the bot simply pays
  more to go first and less to go after.

How it is built: one in-house bot script for the L1 chain (anvil, open source), using an instructor account
that holds ETH; it reads the trades waiting for the next block (anvil's 12-second blocks give it time) and
sends a buy that pays a higher tip and a sell that pays a lower one. A game page beside the swap page adds the
turn order, the limit choice, the prediction box and the round's scores, and sends the same ETH-for-cUSD swap
the swap page sends, with the student's own limit. The pool, the router and Otterscan are the lab's own. The
answer key (each round's sandwiches, read from the chain after the round) goes in `dynamic-labs/dex/quizes/`,
which students never receive.

## Load check

- [x] One new term per step: slippage tolerance is the only term named; pool, reserves, price impact and
  sandwich come from the morning's lessons.
- [x] Nothing drawn for decoration: the page is the quote, the limit and the result.
- [x] Labels sit on the thing they name: each trade's result sits on its own row.
- [x] Objects use the shared look: `.addr` for the bot and seats, `.hash` for transactions, `.conf` for the
  confidence word.

## Sources

The trader, the block number and the amounts in the sentence are made up for the game and say so.

- A pool's price is the ratio of its reserves; the product of the reserves cannot decrease; traders pay 0.30% —
  `@adams_uniswapv2core_2020`; a bigger trade gets a worse price, output `997·a·y / (1000·x + 997·a)` —
  `lessons/ethereum/07-EF-liquidity_and_exits.qmd`; `@uniswap_howuniswapworks_2026`
- `amountOutMin` protects a swap; the router refuses one that would get less —
  `@uniswaplabs_uniswapv2router02_2020`; the course router's `too little received` —
  `dynamic-labs/dex/chain/src/CourseDex.sol` (read 10 Nov 2026)
- A sandwich: buy before the victim's trade, sell after it, profit from the price the victim moves —
  `@ethereumorg_mev_2026`; `lessons/ethereum/03-EF-ethereum_network.qmd`, "A sandwich: three transactions, one
  victim"
- Bots pay higher fees to be placed first — `@daian_flashboys20_2019`
- The lab's L1 chain: one cUSD/WETH pool, accounts 10 to 49 as the class's seats, 12-second blocks; the swap page
  swaps ETH for cUSD — `dynamic-labs/dex/README.md`; `dynamic-labs/dex/gateway/static/sign/swap.js` (read 10 Nov
  2026)
- Confidence words, never a percentage; independent evidence is a different kind, not a second reading of the
  same transactions — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: waiting
