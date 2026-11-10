# Day 4 Exchange and Bridge Lab Regression Playbook

This playbook is the browser-driven companion to the automated `dex` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The dex stack is running (`./lab-manager.sh start dex`) and the automated suite has passed
   against it. Do not reset just to start the browser stage.
2. The lab has two hosts: `http://dex.localhost/` (L1) and `http://dex-l2.localhost/` (L2) on this
   machine. The course site's `/labs/dex/` redirects to the L1 host's worksheet.
3. No credentials: the lab has no instructor surface. The swap page's seat keys come from Anvil's
   public test phrase and exist only on the training chains.
4. Use seat 39 for the swap task (the automated suite uses seat 40). Every run adds a swap and a
   deposit, so the pool's price and the deposit numbers move from run to run until the lab
   restarts: that is expected.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures
and a screenshot.

## Read Flow

1. Open `/` on the L1 host. Confirm it names "Course L1 (training)". Open `/` on the L2 host.
   Confirm it names "Course L2 (training)".
2. On L1, search `9`. Confirm block 9's page shows 17 Sep 2026 14:01:48 UTC and one transaction.
3. Open `/tx/0x637c6489f69b169e81feba5895fc9c2f2f0752d2e44d98fe1470ad7838d46fd9`. Confirm From
   `0x90F7…b906` with nonce 1, "Interacted With (To)" the router
   (`0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9`), Value 0 ETH, Transaction Fee
   0.00003864323857377 ETH, and Input Data starting `0x38ed1739` (`swapExactTokensForTokens`).
4. On the same transaction, open the Logs tab: a cUSD `Transfer` of 5,000 cUSD from Account 3 to
   the pair, a WETH `Transfer` of 2.374148687907796351 WETH from the pair to Account 3, then the
   pair's `Sync` and `Swap`.
5. Open block 11's transaction
   (`0x16d011bb2c6ff0d1f76b955ff80c8bc512f3d6aa58867c84437708bf91ed447a`). Confirm From
   `0x15d3…6A65` and the Logs tab: 2 WETH in, 4,219.4806 cUSD out, `Sync` and `Swap`.
6. Open the pair (`0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0`). Confirm a Contract tab with
   verified source, served from the lab's own `/sourcify`.
7. Open `/tx/0x3f61c0abb2304f421e8331c39103ba6d792a08082821a602d20442a1f4cf4a2c` (block 14's
   second transaction). Confirm From `0x9965…A4dc`, "Interacted With (To)" the bridge
   (`0x7ef8…174B`), Input Data decoded as `depositERC20To`, and the Logs tab: a cUSD `Transfer` of
   3,000 cUSD from Account 5 to the bridge and a `DepositInitiated` with deposit number 1.
8. On the L2 host, open `/tx/0x95bea788730c0bbb4be240c3e3f276ba134bc0cbbda4b40d014fff8433f674e1`
   (block 101, 14:03:22 UTC). Confirm From `0x14dC…9955` (the relayer), Input Data decoded as
   `finalizeDeposit`, and the Logs tab: a bcUSD `Transfer` of 3,000 bcUSD from the zero address to
   `0x2361…1E8f` and `DepositFinalized` with deposit number 1.
9. On L2, open bcUSD (`0x61Ab51bE7C866a54B0B442c149d7715367743EfD`). Confirm its creator is the
   bridge, in transaction `0xfe13834ea07f82f327f935d4b5123c0171dbaa147b689413d71bd6b8e87128f5`,
   and a Contract tab with verified source.
10. On L2, open Account 8 (`0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f`). Confirm it lists no
    transactions (the worksheet's question 8 sends students to the swap page's `balanceOf`
    instead).
11. Check console errors and failed network requests on both hosts. Four kinds of 404 are
    expected: from `/sourcify` for an address that is not a contract, from `/signatures/<selector>`
    and `/topic0/<hash>` for a function or event Otterscan's built-in lists do not name (the
    bridge's `finalizeDeposit` and `DepositFinalized`), and from `/assets/<chain>/<address>/logo.png`
    for a token with no logo. Anything else is a failure.

## Swap Flow

1. Open `/sign/` on the L1 host. Enter seat 39 and load the account. Confirm an address, an L1
   ETH balance, an L1 cUSD balance and an L2 bcUSD balance appear, and the request log shows
   calls to both `/rpc` and `/rpc-l2`.
2. Quote 0.1 ETH. Confirm a cUSD amount, the price you get and the pool's price.
3. Build the swap. Confirm To is the router and the selector is `0x7ff36ab5`
   (`swapExactETHForTokens`). Sign and send. Within about 30 seconds confirm a block number, the
   cUSD received and the pool's price before and now (lower now).
4. Approve and deposit. Confirm two L1 transactions and a deposit number, then within about a
   minute the L2 transaction, sent by the relayer
   `0x14dC79964da2C08b23698B3D3cc7Ca32193d9955`, and the seconds waited.
5. Follow the L2 transaction link. Confirm the L2 explorer opens it and shows `DepositFinalized`
   with the same deposit number.
6. Under "Ask the contracts", ask L2 bcUSD `balanceOf` for the seat's address (the amount
   bridged, plus any earlier runs) and the L2 bridge's `relayer` (Account 7). Ask with a bad
   address and confirm the row reads "No answer". Check console errors and failed network
   requests.

## Links and Fallback

1. Open `/lab/`. Confirm the worksheet renders and its links to both explorers, the swap page
   and the saved pages all load.
2. Open `/fallback/`. Confirm the L1 and L2 pages navigate, and the contract reads show 4,200 cUSD
   in the L1 bridge and a bcUSD supply of 4,200. Follow its link to the recorded run:
   `swap-run.html` shows the seat 39 run and its request log, with links back to the worksheet
   and the saved pages.
3. On the course site host, open `/labs/dex/`. Confirm it lands on the worksheet.

## Not Covered Here

- the classroom (`dex.lab`, `dex-l2.lab`) and cloud hosts and their certificates
- a whole class swapping at once (40 seats against one pool and one 12-second block)
- Otterscan's look on a phone-width screen

## Completion Rule

Complete when every step above passes, or each failure carries its evidence and a fix
recommendation.
