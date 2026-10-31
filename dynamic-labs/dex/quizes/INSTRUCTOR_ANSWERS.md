# Day 4 DEX and bridge lab: instructor answers

Numbers read from the built chain (`chain/build-chain.sh`, genesis 17 Sep 2026 14:00:00 UTC on
L1). The worksheet is `gateway/static/lab/index.html`; the build steps, block by block, are in
`build-steps.sh` beside this file. Amounts: cUSD and bcUSD have 6 decimals, WETH 18.

## Part 1: the problem

### The swap (L1 block 11)

1. **Who, what, where the money is.** Transaction
   `0x16d011bb2c6ff0d1f76b955ff80c8bc512f3d6aa58867c84437708bf91ed447a`, 17 Sep 2026 14:02:12 UTC,
   sent by Account 4 (`0x15d3…6A65`, nonce 2) to the router (`0xCf7E…0Fc9`). The pool (pair,
   `0x9fE4…a6e0`) holds the money: the Transfer logs move WETH into it and cUSD out of it. Account
   4's approval of the router is block 10. Fact.
2. **Amounts.** 2 WETH in (WETH Transfer, Account 4 to the pool, `0x1bc16d674ec80000`) and
   4,219.4806 cUSD out (cUSD Transfer, pool to Account 4, `0xfb802a18` = 4,219,480,600). The Swap
   log repeats both (`amount1In` 2 WETH, `amount0Out` 4,219.4806 cUSD). Fact.
3. **Reserves.** Before: block 9's Sync, 105,000 cUSD and 47.625851312092203649 WETH. After: block
   11's Sync, 100,780.5194 cUSD and 49.625851312092203649 WETH. Reserve 0 is cUSD (lower address).
4. **Price.** Before 105,000 / 47.6259 ≈ 2,204.69 cUSD per WETH; after 100,780.5194 / 49.6259 ≈
   2,030.81. The trader got 4,219.4806 / 2 ≈ 2,109.74 (4.3% below the price before). The swap moved
   the price down about 7.9% (selling WETH made WETH cheaper).
5. **Statement and confidence.** For example: "On 17 Sep 2026 at 14:02:12 UTC, Account 4 sold 2 WETH
   for 4,219.48 cUSD through the course exchange's router, moving the pool's price from about 2,205
   to about 2,031 cUSD per WETH." Account 4 is the trader: **High**. In block 11, Account 4 signed
   the swap, the WETH left Account 4 and the cUSD went to Account 4 (Transfer, and the Swap log's
   `to`, which repeat the same payout). Those are one look at one transaction, so they count as one
   line. The independent line is block 10: a separate transaction in which Account 4 approved the
   router to take its WETH. A student who counts four lines from block 11 alone has missed the
   worksheet's definition of independent; without block 10 the answer is Moderate. The router is the Swap
   log's `sender` only because it called the pool; it holds nothing after the call. Whether Account
   4 traded for itself is a judgment the chain cannot settle.

### The bridge (L1 to L2)

6. **The deposit.** L1 block 14, 17 Sep 2026 14:02:48 UTC, transaction
   `0x3f61c0abb2304f421e8331c39103ba6d792a08082821a602d20442a1f4cf4a2c` (its second; the first,
   `0x23ab…f201`, is Account 5's `approve` of the bridge). Account 5 (`0x9965…A4dc`) called
   `depositERC20To` on the L1 bridge: 3,000 cUSD to Account 8 (`0x2361…1E8f`) on L2. The
   DepositInitiated log carries deposit number 1, the token, Account 5 and Account 8. Fact.
7. **The other side.** L2 block 101, 14:03:22 UTC, transaction
   `0x95bea788730c0bbb4be240c3e3f276ba134bc0cbbda4b40d014fff8433f674e1`: Account 7, the relayer,
   called `finalizeDeposit` on the L2 bridge. It minted 3,000 bcUSD to Account 8 (bcUSD Transfer from
   the zero address) and wrote DepositFinalized with deposit number 1, Account 5 and Account 8. 34 s
   after the L1 deposit (the relayer waits for two more L1 blocks). Links: the deposit number, the
   amount, both addresses, and the timing. Confidence that they are the two halves of one transfer:
   **High** (the number and the addresses are written by the contracts on each side, the amount and
   time agree). Deposit 0 (block 13, Account 1, 1,200 cUSD to itself; L2 block 95) is the other
   one on the chain: a student who matched by amount or time alone should check its number.
8. **Holdings.** Account 5's 3,000 cUSD is held by the L1 bridge (locked, with Account 1's 1,200:
   4,200 cUSD). Account 8 holds 3,000 bcUSD on L2 (`balanceOf` on the swap page; the explorer lists
   no transactions for Account 8 because it neither sent a transaction nor was sent one; it appears
   only in token logs). bcUSD was created by the L2 bridge in the
   bridge's own creation transaction, `0xfe13834ea07f82f327f935d4b5123c0171dbaa147b689413d71bd6b8e87128f5`
   (L2 block 15, sent by Account 6). Fact.
9. **Kind of bridge.** Lock and mint. L1: the cUSD moved into the bridge contract and stayed there
   (no burn: total supply unchanged). L2: bcUSD came from the zero address, minted by the bridge,
   which is the only address bcUSD lets mint. The code says the same: `depositERC20To` pulls tokens
   into the L1 bridge, `finalizeDeposit` mints on L2. **High**.
10. **Who could stop or freeze it.** The bridge owner (Account 6) on either side can `setPaused`:
    paused L1 refuses deposits, paused L2 refuses finalizing. The relayer (Account 7) is the only
    address `finalizeDeposit` accepts, so it can stop money arriving by not sending. The cUSD issuer
    (Account 0) can `addBlackList` the L1 bridge, which freezes the locked cUSD. **Moderate**: read
    from the code and the `owner`/`relayer` answers, not seen happen on these chains. A strong answer
    adds that the relayer, being one key, could also mint bcUSD with no deposit behind it (Part 2c).

## Part 2: the recorded run (seat 39, 31 Oct 2026)

Students on live chains get their own numbers; check the shape, not the values. The recorded run
(`gateway/static/fallback/swap-run.html`) has:

a. Swap `0xda3cf5e327694529b14e8b0c94a4158a87f35ee6ee0aa8a4737286e4f004316f`, L1 block 24: 0.1 ETH
   in, 202.065487 cUSD out, exactly the quote. Pool price 2,030.81 before, 2,022.66 after. A student
   who got less than the quote had someone else's swap land first (the class shares one pool); the
   99% minimum keeps the difference small or makes the swap fail.
b. Deposit number 2, L1 block 26 (`0x6579…b1c5`, after the `approve` in block 25). Completed by L2
   transaction `0xe41e4feb1cf799f958885234fb614e8f6ba5a836fdc28ef9a46ce37b9b0aa62c`, L2 block 167,
   22 s after L1 block 26 by the two blocks' timestamps; the recorded run's page says it waited 28 s
   (its own clock, from receiving the deposit's receipt until a 2-second check saw the finalize).
   Either is right. Sent by
   Account 7, the relayer. Live runs take about 20 to 40 s.
c. bcUSD would appear on L2 with nothing locked on L1: L2's total supply would exceed what the L1
   bridge holds, and the DepositFinalized number would match no DepositInitiated on L1 (or match one
   with a different amount or address). Finding it means reconciling the two sides: each L2
   finalize against its L1 deposit, and the totals.

## Challenge

d. On the saved pages (L1 block 18, L2 block 105): the L1 bridge holds 4,200 cUSD and bcUSD's total
   supply is 4,200. They should match for a lock-and-mint bridge with no withdrawals. A larger L2
   supply means unbacked bcUSD: a mint with no deposit (a bad or compromised relayer, or a bug).
   Live, after Part 2, both have grown by the class's deposits; between a deposit and its finalize
   L1 is briefly ahead.
e. Account 2 holds all 2,236,067,977,499,789 of the pool's shares (`totalSupply` equals Account 2's
   `balanceOf`; this course pool keeps no locked minimum). At block 18 they are worth the whole
   reserves: 100,780.5194 cUSD and 49.625851312092203649 WETH. Account 2 put in 100,000 cUSD and 50
   WETH: the trades left it with more cUSD, less WETH, plus fees.
