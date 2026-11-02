# Day 8 lab: a cross-chain trace — instructor answers

**Instructors only.** `pages.yml` and `vm-build.yml` leave every lab's `quizes/` folder out of what
students receive. The worksheet is `static/lab/index.html`. Every number below is what `queries/d8.sql`
gives on the frozen snapshot (`snapshot/`, sealed in `snapshot/meta.json`), the same text the query page
and the saved results (`static/fallback/`) show; `facts.json` holds the anchor values the automated suite
checks. Times are UTC. Sources are the worksheet's numbered list.

## What the lab grades

Question 17 is the day's graded point (build spec: "Day 8's cross-chain trace includes its contract read
(what a function does, who may call it and what it changed) and a diagram naming each contract, the assets
in and out and the far-side address").

**Meets** when the note has all three:

1. **The contract read.** Does: the function at `0x96221423…` looks like an ERC-20 `transfer` but writes
   its first argument into storage slot 0, which in the Safe wallet is the master copy, so the wallet's code
   was swapped for `0xbdd077f6…`. Who may call: the wallet ran it through its own `execTransaction`
   (selector `0x6a761202`), which runs only what the wallet's required signers sign; so the signers were
   made to sign it. Changed: the wallet's logic contract, after which the sweeps ran (about 1.5 minutes
   later).
2. **The Kelp diagram**, naming each contract by address and role as the queries show it, the asset in and
   out at each step, and the far-side address on Arbitrum. At least: the release (`0x85d456b2…`, 116,500
   rsETH out) → `0x8b1b6c9a…` → the split → `0x1f4c1c2e…` → the lending pool (rsETH in, WETH/ETH out) →
   ETH to the collecting address `0x5d3919f1…` on Ethereum; and the bridge sends (rsETH out on Ethereum)
   to the same addresses on Arbitrum (rsETH in), ETH to `0x5d3919f1…` on Arbitrum → `0x…0da0`.
3. **An assessment** with a confidence word per judgment, no percentages, and at least one thing the chain
   does not show (the rsETH-to-ETH step on Arbitrum; who holds the keys; what Aave or the Council decided
   off-chain).

**Not yet** when any of the three is missing, the diagram leaves out the far-side address, a judgment has
no confidence or carries a percentage, or the note names a contract by a label the snapshot leaves blank
as if it were a fact. Questions 1 to 16 are feedback, not graded. A different confidence with a reason the
scale supports is right. One retry in class time.

**Scale used.** High: two independent kinds of evidence agree. Moderate: one strong line, or weaker lines
that agree, with a known false positive possible. Low: timing, amount, behavior or one unverified label
alone. A name from a selector or a token symbol is one unverified label.

## The contract read (questions 1 to 4, everyone)

1. Transaction `0x46deef0f…`, 21 Feb 2025 14:13:35. Path `0_0` delegatecalls `0x96221423…` with selector
   `0xa9059cbb`. 4byte lists six signatures for it (read 1 Nov 2026): `transfer(address,uint256)` and five
   others such as `workMyDirefulOwner(uint256,uint256)`. The name is a claim.
2. Before: path `0` runs `0x34cfac64…` (selector `0x6a761202`, `execTransaction`). After: every call runs
   `0xbdd077f6…`. The first sweep is at 14:15:11, about 1.5 minutes later; the last at 14:16:11.
3. `0x1163b2b0` = `sweepETH(address)`, used in `0xb61413c4…` (the ETH sweep, 401,346.768858404671846374
   ETH). `0x582515c7` = `sweepERC20(address,address)`, used for the token sweeps (USDT 90, cmETH 15,000,
   stETH 90,375.547907685258392043, mETH 8,000). The names fit what moved: **moderate** (4byte only, but
   consistent with the moves). Accept low with that reason.
4. Does: overwrote the wallet's logic contract, **high** (NCC's code read [6] and the on-chain switch from
   `0x34cfac64…` to `0xbdd077f6…` are two kinds). Who may call: the wallet's own signers, through
   `execTransaction`, **moderate** or **high** (NCC says so; path `0` shows it). Changed: slot 0, so the
   wallet now runs `0xbdd077f6…`, **high**. A student who calls the function "a transfer" from the
   selector alone has missed the point.

## The worked example (questions 5 to 10, not graded)

5. Five sweeps to `0x47666fab…` (query 2). Query 3: at 15:48:23–35, four × 10,000 ETH to `0x51e9d833…`
   (on the FBI list [1]), `0x83ef5e80…`, `0xcd1a4a45…` and `0x1eb27f13…`.
6. The hub `0x31c4b3da…` (query 4), 24–25 Feb: 929.2099 ETH from `0x51e9…` (11 payments), 713.8080 from
   `0xcd1a…` (8), 304.5248 from `0x1eb2…` (2), 98.9901 from `0x83ef…` (1); 107.5198 and 101.431 from two
   senders the snapshot does not trace; 17 tiny payments. Pooling: **moderate**.
7. Address poisoning [12]: 16 look-alikes match the first and last four hex characters of an address the
   hub paid (10, 20 or 103.105 ETH), 5 to 207 blocks later; the hub never paid any of them. Strangers, not
   the thief: **moderate** to **high** (the pattern and the published behavior). Not in the cluster.
8. Query 6: 25 Feb 21:56:47, three × 9.98 ETH into vault `0x863df8de…` from `0xbfd21476…`, `0x1e15cd18…`
   and `0xf19e24cf…` (each paid by the hub). Each memo: `=:BTC.BTC:bc1qjm4u…:0/10/0`.
9. Query 7: 22:39:21, 43 minutes later; 0.27748623, 0.27393619 and 0.27305932 BTC to `bc1qjm4u…`;
   `as_the_memo_asked` true for all three.
10. Query 8, as of Bitcoin block 972,854: 249 transactions, 61.78505337 BTC in and out, nothing held,
    24 Feb 17:06:10 to 26 Feb 02:56:35. Report: the crossing to Bitcoin through THORChain, **high**.

## The problem (questions 11 to 16)

11. Query 9: just before, Ethereum had accepted 307 messages from Unichain's rsETH contract; at 17:35:35
    on 18 Apr 2026 a delivery claiming message 308 was accepted. Unichain had sent 307 then, and still
    307 an hour later. A message accepted that was never sent: the delivery was forged, **high** (both
    chains' own counters; each nonce on a channel stands for one message sent, worksheet source [14],
    `layerzero_v2glossary_2026`). The heads later reach 320 on both
    chains (normal traffic after).
12. Query 10: 116,500 rsETH from `0x85d456b2…` (blank label: "the contract that released it") to
    `0x8b1b6c9a…` in `0x1ae232da…`. 17:37:23–17:41:59 it is split: 53,000 to `0x1f4c1c2e…`; 30,000 to
    `0xeba786c9…`; 10,000 `0xcbb24a6b…`; 8,000 `0x1b748b68…`; 6,000 `0xbb6a6006…`; 5,000 `0x8d11aeac…`;
    4,500 `0xe9e2f48b…`.
13. Query 11: `0x1f4c…` supplies 1 + 5,000 + 20,000 + 27,999 = 53,000 rsETH to the `aEthrsETH` contract
    `0x2d621092…` and gets `aEthrsETH`; borrows 0.98 + 4,923.96 + 19,745.04 + 27,770.59 ETH (WETH through
    `0xd01607c3…`, debt token `variableDebtEthWETH`); at 17:44:47 sends 52,440.676111351964954319 ETH to
    the collecting address `0x5d3919f1…`. Aave V3: **moderate** (Blockaid [3] plus the token names; the
    pool addresses carry no sourced label here). Blockaid says 116,500 went into Aave; the snapshot shows
    only `0x1f4c…`'s 53,000. A student who spots that gap has read well.
14. Query 12: six sends Ethereum → Arbitrum, each to the sender's own address on Arbitrum
    (`receiver = sender`), arriving in 512–518 s: 8,000 (`0x1b74…`), 4,500 (`0xe9e2…`), 12,573.795185
    (`0xeba7…`), 770 (`0xbb6a…`), 9,299 (`0xcbb2…`), 4,600 (`0x8d11…`); 39,742.795185 rsETH in all. The one
    sent back, 3,575.571057 rsETH from `0x8d11…` at 18:30:31, was cleared with nothing released on 22 Apr.
15. Query 13: on Arbitrum, 10 payments in, 30,765.667501709008927568 ETH, 17:58:20–19:34:26 on 18 Apr.
    How rsETH became that ETH on Arbitrum is not in the snapshot: say so. Query 14: 21 Apr 03:26:47, the
    Security Council's transaction on Ethereum; 03:35:08, Arbitrum tx `0x56180442…` (type 101, a
    cross-chain retryable), `from` the collecting address, moves 30,765.667401709008927568 ETH to
    `0x…0da0`. The Council says it made a cross-chain transaction impersonating the address [5], and its
    frozen figure is exactly query 13's "in" (the transaction itself moves 0.0001 ETH less: accept either
    figure if the student says which row it is from). Did the owner sign it? No, **high** (the Council's statement,
    the Ethereum-side transaction minutes before, and type 101).
16. Query 14: 15 Jun 2026 10:18:25, 30,765.617401709008927568 ETH from `0x…0da0` to `0x3b87db6d…`. Query
    15: as of Arbitrum block 517,703,385 it holds 30,765.627396224479240951 ETH. The snapshot gives
    `0x3b87…` no label and the course has no source naming it: say what it holds and when it got it, and
    that the Council said release was for Arbitrum governance [5]. A student who names who controls it
    should say where that came from.

## Challenge key (optional, ungraded)

a. **75,700 ETH** out on Ethereum (2 payments, 21 Apr 07:39–07:40) against 52,440.676 in: 23,259.32 more.
   The snapshot holds only the case's transactions; the rest came in by transactions it does not include.
b. **3,575.571057 rsETH** sent back from Arbitrum by `0x8d11…` (guid `0x8bef09cd…`), cleared with nothing
   released on 22 Apr 2026 by the delegate `0xcbcdd778…`.
c. **`0xe81c9749a665e2f65d7dd7efcb96d50c86e94ac6`**: its 0.000000001 ETH matches no payee (`imitates` is
   blank).

The flags are **23259.32**, **3575.571057** and **`0xe81c9749a665e2f65d7dd7efcb96d50c86e94ac6`** (also in
`quizes/facts.json` under `flags`). Each part's box on the worksheet holds only `sha256("course-flag:" + flag)`
and says whether a typed answer matches: amounts are rounded half up to the flag's places (2 for a, 6 for b),
commas and units are ignored, and an address may be in any letter case.
