# Pool trading: instructor key

Instructor only (students never receive `quizes/`). Lab: `blockchain-course/assets/labs/pool-trading/index.html`,
opened from the day 4 slide "A bigger trade gets a worse price" (`lessons/ethereum/07-EF-liquidity_and_exits.qmd`);
students trade on the game page `/sign/pool-trading.html` on the exchange lab's L1 host. Design card
`docs/lab-cards/pool-trading.md`. Alone, one seat each, three rounds, about 40 minutes, last thing on day 4.

## Running a round

With the exchange lab running, from the repo root on the lab host (where `docker` reaches its containers):

```bash
docker exec -i dex-relayer-1 python - round 1 < dynamic-labs/dex/quizes/pool_trading.py
```

The script sends a marker transaction from the instructor's account (Anvil's dev account 9), which every game page
is waiting for, then plays that account until the round ends. Seat N trades in block marker + 1 + (N - first), so a
40-seat round takes about 8 minutes of 12-second blocks. A seat that misses its block gets no trade that round
(the key lists it at the end); `round 1 --make-up` gives every seat a second block one round of seats later, at
the cost of doubling the round to about 16 minutes. `--first F --seats K` runs a smaller class (seats F to
F + K - 1). Wait for "Round 1 over" before opening round 2.

- **Rounds 1 and 2**: the bot. For each seat trade waiting for the next block, it works out the largest buy ahead
  of the trade (up to 5 ETH) that the trade's limit still lets through, and sandwiches only if that leaves it at
  least 0.01 ETH after both pool fees: a buy paying a higher tip than the trade (so it runs first) and a sell of
  everything it bought paying a lower one (so it runs after).
- **Round 3**: the twist (`round 3`). No bot. Ahead of seats 3, 11, 19, 27 and 35 (`--twist` picks others), the
  instructor's account buys cUSD with 20 ETH, the same swap a student sends, at a higher fee, and sells nothing
  after.

The pool is never reset between rounds or classes: each sandwich and each twist leaves more ETH in it, so quotes
fall from round to round. The game reads the chain as it is; the formula and the calls do not change.

## The answer key

After each round:

```bash
docker exec -i dex-relayer-1 python - key 1 < dynamic-labs/dex/quizes/pool_trading.py
```

prints one row per seat trade: its block, the quote (what 1 ETH bought from the pool as the block found it), the
limit, what it received or why it was refused, whether it was sandwiched with the two transactions' hashes and the
bot's profit, and any trade ahead with no sell after (the twist). Seats with no trade are listed at the end.

## What students should find

- **Prediction** (the shell's question): (c), possibly much less. (a) is the wrong belief; (b) inverts price
  impact; (d) holds only with a limit the price passes.
- **Their own prediction** each round: `997·1·y / (1000·x + 997·1)` cUSD, with x and y the pool's WETH and cUSD
  read just before their turn. The page scores it within 1% of that formula on the reserves it showed them.
- **No limit, rounds 1 and 2**: sandwiched. The bot buys up to 5 ETH just ahead; the student gets well under the
  quote (about 17% less on the starting pool, about 7% once it holds 130 ETH). Before and after are the same account, buy then sell.
- **5% limit**: sandwiched, but the bot can push the price only until the trade would get 5% under the quote:
  the student gets just above their limit.
- **0.5% limit**: left alone (the most the bot could make is under its 0.01 ETH floor); the student gets the
  quote, to the last few units.
- **Round 3, a twist seat**: a 20 ETH buy just ahead, nothing after from that account. Not a sandwich (the twist's
  answer, "No: no one bought before you and sold after you"). With 0.5% the router refuses the trade, `too little
  received`, and the student keeps the ETH; 5% is refused too (the 20 ETH ahead costs a quarter or more); with no
  limit it gets far less.
- **Round 3, other seats**: no trade ahead; they get the quote whatever their limit.

## Scoring (the game page does it)

Per round: prediction with its working +1; limit with a reason +1; the right call +2 (with the two hashes for a
sandwich, or a reason for none); a sandwich called where there was none −2. A "no" without a reason, or a "yes"
with the wrong hashes, scores 0. Time only breaks ties. The page also shows the class's balances, in seat order and
never ranked: a careless trader loses money, and the points go to seeing why.

A student's score lives in their browser, on the game page. Read it there; the answer key is what the chain shows.

## Sources

- Output formula and fee: `@adams_uniswapv2core_2020`; `@uniswap_howuniswapworks_2026`.
- `amountOutMin` and the router's refusal: `@uniswaplabs_uniswapv2router02_2020`; the course router's
  `too little received` in `dynamic-labs/dex/chain/src/CourseDex.sol`.
- Sandwiches and fee priority: `@ethereumorg_mev_2026`; `@daian_flashboys20_2019`.
