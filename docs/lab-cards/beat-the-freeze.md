# Design card: Beat the freeze

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5; tentative in the plan: "Beat the freeze (idea 18, tentative)"). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Beat the freeze (review idea 18, "Can it be frozen?") |
| Replaces | nothing |
| Opens from | `lessons/ethereum/08-EF-layer2s_and_bridges.qmd`, "Answers: bridges moved it faster than freezes" |
| Day | Day 4, lesson ③ (layer 2s and bridges) |
| Kind | prediction lab (five minutes) |

Tentative in the plan: the owner decides from this card whether it is built at all.

Why this slide: its title states the right belief (the money moved faster than the freezes), and lesson ③ has no
prediction lab. Day 3 ③ holds Tether's blacklist slides but already opens Who got paid?, and the plan allows one lab
per lesson. The lab recalls day 3's "Freezable? Which issuer, and how fast?" and prepares this afternoon's last
question, "say who could have frozen the token".

## The ten lines

1. **The wrong belief**: "Once the issuer freezes, the stolen money is caught." Not on the plan's list: the owner
   left it off on 11 Nov 2026, and the card keeps its belief.
2. **The prediction** (shell: `commit`): "1,000,000 USDT is stolen. The victim reports it 30 minutes later, naming
   the address the money went to. Tether freezes that address 2 hours after the report. How much is caught?"
   Choices: (a) all of it: the freeze stops the money; (b) about half: some got away; (c) whatever still sat in
   that address when the freeze landed, which may be nothing; (d) none: freezes do not work on a blockchain. Then
   High, Moderate or Low.
3. **The action** (shell: `do`): the student plays the issuer. The thief's moves play on a fast clock, each
   landing as a block: the stolen USDT goes to address A; within minutes A sends 600,000 to B and 400,000 to C;
   B swaps its share for ETH, and the ETH leaves through a cross-chain swap into BTC, while C waits. Once the
   report arrives the student may press Freeze on any address; each freeze lands a set time later. At the end the
   lab shows each freeze against the address's balance at that block. The freeze in the prediction lands on A,
   already empty: caught 0. Aimed at C, which still holds its share, a freeze catches 400,000; B's share, now ETH
   and then BTC, can never be caught. Answer (c).
4. **The constraint**: a freeze is one line in one token's contract: it marks one address, so that address can no
   longer send that token. It does not follow the money. Funds are freezable only while they sit in that token at
   an address the issuer has listed; once swapped into ETH, which has no issuer, or carried to another chain, the
   list cannot reach them. So the freeze races the thief's next move, and the thief moves first.
5. **The name** (shell: `name`): chain hopping. Parts: chain (one blockchain's ledger) + hopping (moving the funds
   across to another). Plain: moving stolen funds from one chain to another, here by a cross-chain swap, so that
   the trace and any freeze must start again on a new ledger, where a stablecoin issuer may have no reach.
6. **The explorer view** (shell: `explorer`): the same freeze as the analyst meets it, in Otterscan's layout: the
   USDT contract's Logs tab with an `AddedBlackList` event naming address A, dated by its block; then A's token
   transfers, whose last outgoing `Transfer` sits in an earlier block. The analyst compares the two blocks: the
   freeze is real, and it caught nothing. Then the real case on the opening slide: in the Bitget hack, about
   $339,000 of about $387 million was frozen (as of 30 Sep 2026).
7. **The twist** (shell: `twist`): a rerun, and one fact changes: before the freeze lands, the thief swaps C's
   USDT for USDC on the same chain, not for ETH. "Is C's money now out of reach?" Choices: yes, Tether's freeze
   cannot touch USDC; yes, a swapped coin is gone; no, ask Circle, whose contract can list that address too; no,
   Tether's freeze follows the swap. Answer: ask Circle. USDC has its own blacklist, kept by Circle's blacklister
   role, and it blocks a listed address from sending or receiving. Swapping between stablecoins moves the
   question to another issuer; it does not close it.
8. **The sentence** (shell: `tell`): "The agent asks whether any of the stolen money can still be stopped."
   Example: "As of block 21,450,112, address C holds 400,000 USDC, received in block 21,449,870; Circle can block
   it. Tether froze address A in block 21,449,990, after A had sent its whole balance on. The other 600,000
   left as ETH through a cross-chain swap into Bitcoin, which no issuer can freeze (Low confidence for the
   Bitcoin side: the swap's payout matches by amount and time only, and it is not yet traced)."
9. **The game, if any**: none. The plan's game, thief against issuer, is not among the eight the owner locked in,
   and day 4's game is pool trading; the caught amount is shown, not scored.
10. **The archetype**: simulation.

The opening case (shell: `case`): a company's treasury wallet is drained of 1,000,000 USDT overnight. The company
calls the agent 30 minutes later; the agent calls Tether and asks you: "They've frozen the address. Is the money
safe now?"

Left out, for the owner to see:

- `destroyBlackFunds` and the frozen USDT address that can still receive (day 3's "What a USDT freeze leaves on
  chain"): a second trap; the lab keeps to timing.
- Circle's reach on another chain after CCTP: true or not, the twist does not need it, and the lab makes no
  claim about it.
- The two-seat version (one student as thief, one as issuer): it needs the game the owner did not lock in.

How it is built: the theft, the addresses A to C, the blocks, the amounts and the clock's delays are made up for
the lab and say so; the freeze mechanics are the real USDT and USDC contracts' rules, and the Bitget figures are
real. A simulated chain in the page, so it runs offline from `src.zip`.

## Load check

- [x] One new term per step: chain hopping is the only term named. Freeze, blacklist, issuer and `AddedBlackList`
  come from day 3 ③; cross-chain swap and liquidity bridge from this lesson's earlier slides.
- [x] Nothing drawn for decoration: an address lights only while it holds the stolen funds, and a freeze marker
  appears only in the block where it lands.
- [x] Labels sit on the thing they name: each balance on its address, each block number on its block.
- [x] Objects use the shared look: `.addr` for the addresses, `.hash` for the transactions, `.coin.output` for each
  hop's amount, `.conf` for the confidence word.

## Sources

The theft, the victim company, addresses A to C, the blocks, the amounts and the delays are made up for the lab and
say so.

- USDT's blacklist: `addBlackList` sets an address in the public `isBlackListed` list and emits `AddedBlackList`;
  only the owner key can call it; `transfer` and `transferFrom` refuse a listed sender — `@tether_tethertokensource_2017`
- USDC's `transfer` refuses a blacklisted sender or receiver; a separate blacklister role keeps the list; each
  listing emits `Blacklisted` — `@circle_fiattokenv1_2026`; `@circle_blacklistable_2026`
- Funds are freezable only while they sit in an issuer's token; ETH or a token with no issuer cannot be frozen;
  a swap into USDC moves the question to Circle — `@tether_tethertokensource_2017`; `@circle_blacklistable_2026`
  (05-EF, "Freezable? Which issuer, and how fast?")
- Bitget: about $339,000 frozen by Tether and Circle, of about $387 million; most ETH crossed on liquidity
  bridges, and some ETH, BNB and XRP went through THORChain, mostly into BTC — `@bitquery_bitgethack_2026` (as of 30 Sep 2026)
- Chain hopping: cross-chain swaps that exploit "the interoperability of blockchain networks to move assets between
  chains" (AADAPT ADT3005, a defense-evasion technique) — `@mitre_aadapt_2026` (read 1 Nov 2026)
- Otterscan's Logs tab shows a transaction's events — the course's tokens lab,
  `dynamic-labs/tokens/gateway/static/lab/index.html` (a course file, not a citation)
- Confidence words, never a percentage; a match by amount and timing alone is Low — `@odni_icd203_2015` (the
  course scale, build spec "Confidence scale")

## Approval

- Owner: "Find the sandwich,What is it really worth,Beat the freeze,The vault that paid twice" (11 Nov 2026)
- Tentative no longer: ticking it means build it (owner, 11 Nov 2026)
- Built in d7a6cde1 (11 Nov 2026).
