# Code review — `workstation/agent.py` (+ `miner.py`) for the v34 forensics run

**Question:** are the deployed student-station agents sufficient to (a) **mine** the forensics seeder's
transactions (the seeder runs in `external` mode and waits for the agents), and (b) **fill blocks to
~4,000 transactions** for a realistic "busy chain" vibe?

**Verdict: No on both counts as written.** `agent.py` is a light P2P-chatter + occasional-block
simulator (its original LAB2 purpose: gently demonstrate a fee market). It is ~2 orders of magnitude
short on volume and unreliable as a miner. Details below.

---

## What `agent.py` actually does
- `loop_transactions` (the engine): `sleep random(30–90)s`, then **one** `sendmany` with **2 outputs**
  (a peer + a self-churn), amounts 0.01–0.5 BTC. → **~1 tx / minute / agent.**
- It mines a block (`generatetoaddress [1, addr]`) only when one of these fires:
  1. mempool **size > 4000** ("janitor" clean — a *ceiling*, line 334),
  2. wallet balance **== 0** (refill, line 354),
  3. a send **fails** — unconfirmed-ancestor chain limit or insufficient funds (lines 395–405).
- Plus P2P address exchange, peer discovery, IBD wait, rotating logs, signal handling — all fine.

`miner.py` is a separate *educational* manual PoW miner: `getblocktemplate` → build block → brute-force
the nonce (`while True: nonce+=1`) → `submitblock`. Real PoW, one block per run, slow, includes mempool
txs. It's a teaching tool, not a continuous/pacing miner.

---

## Problem 1 (CRITICAL) — throughput is ~100–170× too low to fill 4,000-tx blocks
At ~1 tx/min/agent, to fill a block to 4,000 txs on, say, a ~60s cadence you need **4,000 tx/min total**:

| Student agents | tx/min produced | tx per ~60s block | vs 4,000 target |
|---|---|---|---|
| 25 (current rate) | ~25 | **~25** | ~0.6% |
| 25 (needed) | 4,000 | 4,000 | each agent would need **~160 tx/min (~2.7 tx/s)** |

The mempool realistically sits in the **tens** of txs, never near 4,000.

## Problem 2 (CRITICAL) — the design *can't* accumulate to 4,000 anyway
The agent's `sendmany` churns **to itself**, building an unconfirmed UTXO chain. Bitcoin Core's default
ancestor limit is **25** unconfirmed txs — so after ~25 self-churns an agent's send fails and it **mines
to unstick** (line 396). That drains the (tiny) mempool long before it could approach 4,000. The
`>4000` "janitor" trigger is effectively **dead code** — the mempool never gets there. To grow a mempool
to 4,000 you must broadcast txs that **don't chain** (spend *confirmed* coins to distinct recipients),
which requires UTXO management the agent doesn't do.

## Problem 3 (CRITICAL) — mining lacks `maxtries`; can stall on the ClassNet fork
All four mine calls are `generatetoaddress [1, addr]` with **no `maxtries`** (default 1,000,000). The
lab's own LAB2 text says *"on classnet the miner needs a higher maxtries budget than regtest"* and uses
`generatetoaddress ... 50000000`. The ClassNet fork **retargets difficulty every 4 blocks**, so once
difficulty rises, the bare call can **fail to find a block** and silently return `[]` — and the agent
never checks the result. If agents can't mine, the seeder's transactions **never confirm**.

## Problem 4 (CRITICAL) — mining is event-triggered, not time-cadenced → the seeder can stall
Blocks only appear on a ceiling/chain-limit/empty-balance event. In a calm moment — every agent funded
(`balance > 0`), mempool `< 4000`, nobody at the 25-ancestor limit — **no agent mines at all** and the
chain freezes. The seeder (external mode) polls for confirmation and, with `confirm_timeout` (1h), can
**time out and fail**. A laundering DAG of ~35 dependent txs needs a *steady* block cadence to drain.

## Problem 5–7 (MODERATE)
- **"4000" is a ceiling, not a fill target** — even if reached, the next block clears it and the size
  oscillates; you don't get sustained ~4,000-tx blocks.
- **No UTXO fan-out** to sustain a high send rate (the root of Problem 2).
- **Thundering herd** — when the mempool *does* cross 4,000, every agent mines near-simultaneously → a
  burst of blocks then idle; erratic intervals.

## What's fine
RPC-via-subprocess with 30s timeout, IBD gate, connection semaphore, graceful shutdown, log rotation,
and the self-heal-by-mining-on-chain-limit are all reasonable. The bones are OK; the **load + mining
model** is the problem.

---

## Recommendation
Split the two jobs the seeder needs — **fill** and **mine** — which `agent.py` currently conflates and
does weakly:

1. **A real load generator** (new mode of agent.py, or a dedicated flooder on a few stations): on start,
   **fan a confirmed coin into N fresh UTXOs**, then spend them to **distinct fresh addresses in a tight
   loop** (no self-chaining → no 25-ancestor wall), targeting a sustained tx/s. Re-fan when low. This is
   what actually grows the mempool toward 4,000.
2. **A pacing miner** (separate role, on a stable station — e.g. the instructor station): mine **every
   ~T seconds**, with a **high `maxtries`**, including whatever is in the mempool, and **check the
   result / retry**. Time-cadenced blocks (a) give the forensics seeder a reliable confirmation drumbeat
   and (b) produce ~4,000-tx blocks *if* the flooders are fast enough between blocks.
3. **Tune to the target:** pick the block interval `T` and total flood rate so `rate × T ≈ 4,000`
   (e.g. ~67 tx/s across the room at `T=60s`). Make the miner's pull bounded by the block weight limit.
4. **Fix `maxtries`** on every mine call regardless.

As-is, the agents will produce a near-empty, intermittently-mined chain — fine for the original LAB2
fee-market demo, **insufficient** for a believable forensics backdrop or for driving the seeder.

> Note on the seeder: even with great flooders, the **pacing miner is the load-bearing piece** for the
> forensics build — it's what guarantees `external`-mode `confirm()` advances. If you'd rather not run a
> separate miner, the alternative is to let the *seeder* mine its own confirmation blocks (drop the
> "no-mining" rule for the seeder only) — but a pacing miner keeps the realism and the no-self-mining
> property you wanted.
