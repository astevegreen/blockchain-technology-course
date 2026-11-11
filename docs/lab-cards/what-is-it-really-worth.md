# Design card: What is it really worth?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | What is it really worth? (review idea 21) |
| Replaces | nothing |
| Opens from | `lessons/ethereum/07-EF-liquidity_and_exits.qmd`, "Quoted value is not what can be sold" |
| Day | Day 4, lesson ② (liquidity and exits) |
| Kind | prediction lab (five minutes) |

The slides before it teach the constant product, price impact ("A bigger trade gets a worse price"), the `Swap`
and `Sync` logs, and a thin market ("A thin market moves on a small sale"). The lab uses them and names one term.
It prepares the lesson's "Can it exit here? Six checks", where depth against the holding is one check, and the
afternoon lab's reading of a pool's reserves ("This afternoon you swap and read the pool").

## The ten lines

1. **The wrong belief**: "A token's quoted value is what it can be sold for." Belief 11 on the plan's list,
   marked common by the owner.
2. **The prediction** (shell: `commit`): "The subject's wallet shows 5,000,000 TKN, 'value $10,000,000' at 2.00
   USDC each. The only market for TKN is one pool holding 50,000 TKN and 100,000 USDC. If the subject sold it all
   there today, roughly what would they get?" Choices: (a) about $10,000,000; (b) about $9,970,000, the quote less
   the 0.3% fee; (c) about $5,000,000; (d) under $100,000. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student sells the holding into the pool in ten lots of 500,000 TKN (each
   quoted at $1,000,000) and says, before each press, what the lot will bring. The first brings $90,884, and the
   pool's price falls from 2.00 to 0.017 USDC; the second $4,334; the tenth $109. The total is about $99,000, and
   the pool's USDC bar runs down towards zero without reaching it: a sale can never take out more than the pool
   holds. Answer (d). Then one slider, the pool's depth at the same 2.00 price: the whole holding sold at once
   brings 1% of its quote from a 100,000 USDC pool, 9% from 1 million, 50% from 10 million (a pool as deep as
   the holding) and 91% from 100 million. Last, the reserves under the bar: `reserve0` and `reserve1` from the
   pool's `getReserves`, as its `Sync` log records them.
4. **The constraint**: a pool is not a queue of buyers waiting at the quoted price. It pays each sale out of its
   other reserve at the price the constant product sets, and every unit sold lowers the price for the next. A
   quoted value prices every unit at the last trade's price, as though no sale moved it; how far a sale falls
   short depends only on how big the holding is against the pool.
5. **The name** (shell: `name`): depth. Plain: what a pool holds on the side the seller is paid from, here
   100,000 USDC. It is the most any sale there can bring, and the measure of a holding: sold into a pool as deep
   as its quoted value, a holding brings about half the quote.
6. **The explorer view** (shell: `explorer`): the same pool in Otterscan, as the afternoon lab meets it: the pool
   contract's latest `Sync` log, with `reserve0` and `reserve1` in raw units (the student turns them into 50,000
   TKN and 100,000 USDC with each token's decimals), and the subject's TKN balance in units. The $10,000,000 is
   on no block: a wallet or a price site multiplied the units by the last price. The analyst reports the units,
   the pool and its depth.
7. **The twist** (shell: `twist`): the subject's lawyer says the subject sold 1,000 TKN in this pool last week
   for $1,955, "so the price is real and the holding is worth ten million." "Does that sale show it?" Choices:
   yes, a real sale at about 2 USDC; yes, less the fee; no, a small sale tests the price, not the depth; cannot
   tell without more sales. Answer: no. 1,000 TKN is 2% of the pool's TKN and came within 3% of its quote; the
   same pool still pays about $99,000 for the whole 5,000,000.
8. **The sentence** (shell: `tell`): "The agent asks what the subject's TKN is worth." Example: "The subject holds
   5,000,000 TKN, quoted at $10,000,000 (2.00 USDC each) in pool 0x9f01…7c, which holds 100,000 USDC. Selling the
   holding there would bring about $99,000 and never more than 100,000 USDC (High confidence: worked from the
   reserves in the pool's latest `Sync` log). We found no other market for TKN; a listing elsewhere would raise
   the figure."
9. **The game, if any**: none. Day 4's game, pool trading in the afternoon, has the class trading one shared pool
   while a bot sandwiches the careless; it scores each call and its reason, and shows each seat's balance without
   ranking by it (owner, on the pool-trading card: "Approve, score the calls (Recommended)", 11 Nov 2026). This
   lab has one seller, no other traders and no score, and it asks what a holding is worth, not how to trade well.
   Its pool and token are not the game's.
10. **The archetype**: simulation.

The opening case (shell: `case`): an agent has a screenshot of a subject's wallet: "Portfolio: $10,000,000", all
of it in a token called TKN. The agent plans to write that the subject holds ten million dollars of proceeds and
asks: "That's what they have, right?"

Left out, for the owner to see:

- Rug pulls (the next slide, "Thin pools let creators pull the rug") and tokens that cannot be sold ("Some tokens
  have no exit") are other reasons a quote fails; they are separate beliefs, not this lab's.
- Other venues (an exchange's order book, an OTC desk) and concentrated-liquidity pools are not modelled; the
  sentence says only that no other market was found.
- The same engine later shows oracle manipulation (review idea 34); nothing of it appears here.
- The numbers differ from the opening slide's (1,000,000 TKN against a 10 ETH pool) so the slide does not give
  away the prediction; the twist could instead be a second, deeper pool, but a past small sale is the claim
  analysts meet.

How it is built: the token, the pool, the subject, the lawyer and the addresses are made up for the lab and say
so. The lab works every sale from the constant product with the 0.3% fee itself, so it runs offline from
`src.zip`.

## Load check

- [x] One new term per step: depth is the only term named. Price impact, the constant product, the `Sync` log,
  thin market and quoted value come from the slides before it; the lab uses them and does not rename them.
- [x] Nothing drawn for decoration: the USDC bar moves only when a lot is sold or the slider moves, and the
  running total sits beside the fixed quote.
- [x] Labels sit on the thing they name: the price on the pool, the amount on each lot, the quote on the wallet.
- [x] Objects use the shared look: `.addr` for the pool and the subject, `.coin.input` for the TKN sold,
  `.coin.output` for the USDC received, `.coin.fee` for the 0.3% fee, `.conf` for the confidence word.

## Sources

The subject, the lawyer, TKN, pool 0x9f01…7c, its reserves and every sale are made up for the lab and say so; the
amounts are worked from the constant product below.

- A Uniswap v2 pool trades against its reserves by x·y = k, with a 0.3% fee on the amount in; the marginal price
  is the ratio of the reserves — `@adams_uniswapv2core_2020` (the slide's source)
- "Larger trades relative to pool depth move the price more (known as price impact)" —
  `@uniswap_howuniswapworks_2026` (read for the slide "A bigger trade gets a worse price")
- The pool's `Sync(reserve0, reserve1)` event and `getReserves()`; the swap check that takes the 0.3% fee —
  `@uniswap_v2pair_2020`
- Report the units held, then the value "quoted at" a named pool with that pool's depth; a quoted value is not
  what the subject could have realized — the opening slide, on `@adams_uniswapv2core_2020`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Find the sandwich,What is it really worth,Beat the freeze,The vault that paid twice" (11 Nov 2026)
- Built: 11 Nov 2026, `blockchain-course/assets/labs/what-is-it-really-worth/index.html`; opened from the slide named above.
