# Day 3 Token Lab Regression Playbook

This playbook is the browser-driven companion to the automated `tokens` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The token stack is running (`./lab-manager.sh start tokens`) and the automated suite has
   passed against it. Do not reset just to start the browser stage.
2. The lab has its own host: `http://tokens.localhost/` on this machine. The course site's
   `/labs/tokens/` redirects there.
3. No credentials: the lab has no instructor surface. The mint page's seat keys come from a
   public test phrase and exist only on the training chain.
4. Use seat 39 for the mint task (the automated suite uses seat 40). Every run mints a new
   badge, so badge numbers rise from run to run until the lab restarts: that is expected.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures
and a screenshot.

## Token Flow

1. Open `/` on the lab host. Confirm the header reads "Course chain (training)" and the footer
   names `/rpc` on the same host.
2. Search `3`. Confirm block 3's page shows Timestamp `Sep-16-2026 02:00:36 PM +UTC` and one
   transaction.
3. Open `/tx/0x8a26810f5f5f0c4701c72507945289bafca405635ed7bec1c93cea737d9b39a5`. Confirm
   "From / Nonce" shows `0xf39F…2266` with nonce 2, "Interacted With (To)" reads "Course Dollar
   (cUSD)" and links to `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512`, Value 0 ETH, Transaction
   Fee 0.000059038401873552 ETH, and the Input Data starts `0x40c10f19`.
4. On the same transaction, open the Logs tab: one `Transfer` from the zero address to
   `0x7099…79C8`, 10,000 cUSD. Open the Trace tab: a `call` to Course Dollar (cUSD), then a
   `delegatecall` to Course Dollar (cUSD) that links to
   `0x5FbDB2315678afecb367f032d93F642f64180aa3`.
5. Open the cUSD address. Confirm the name, a Contract tab showing DollarProxy as an exact match
   with `decimals = 6` in the source (served from the lab's own `/sourcify`), and a list of the
   eight transactions of blocks 2 to 9.
6. Open block 2's transaction (`0xe9b059481ea3f18c16bdc80be365d7b45b3022a70b4bddd0e452111fd2135074`).
   Confirm its Logs tab shows `Upgraded` naming `0x5FbDB…0aa3`.
7. Open block 4's transaction. Confirm "Tokens Transferred (1)" shows Account 1 to Account 2,
   2,500 Course Dollar (cUSD).
8. Open block 6's transaction. Confirm its Logs tab shows `AddedBlackList` naming
   `0x90F7…b906`. Open block 7's transaction. Confirm the Status line reads "Fail with revert
   message" and names "sender is blacklisted".
9. Open block 8's transaction. Confirm it succeeded and its Logs tab shows a `Transfer` from
   `0x7099…79C8` to `0x90F7…b906`, 100 cUSD. Open block 9's transaction. Confirm its Logs tab
   shows `DestroyedBlackFunds` for `0x90F7…b906` and no `Transfer` log.
10. Open block 11's transaction. Confirm "Interacted With (To)" reads "CourseBadge", there is no
    "Tokens Transferred" line, and the Logs tab's `Transfer` has four topics (badge number 1).
11. Open block 15's transaction (`0x65fee341d80f01ffc871b04522bbf516e3fe7c6d3a4e2eca82202d701f1e2767`).
    Confirm "Interacted With (To)" reads "BadgeShop" with two TRANSFER lines (Account 2 to
    BadgeShop 0.5 ETH, then BadgeShop to Account 4 0.5 ETH), Transaction Action "buy", and the
    Logs tab shows a badge `Transfer` and a shop `Sold`.
12. Open Account 3 (`0x90F79bf6EB2c4f870365E785982E1f101E93b906`). Confirm it lists only the
    block 7 transaction (hint 7 tells students to go to the cUSD page instead). More rows mean
    someone sent from Account 3 on the live chain: note it, not a failure.
13. Check console errors and failed network requests. Three kinds of 404 are expected: from
    `/sourcify` for an address that is not a contract, from `/topic0/<hash>` for an event
    Otterscan's built-in list does not name (the shop's `Sold`), and from
    `/assets/31337/<address>/logo.png` for a token with no logo. Anything else is a failure.

## Mint Flow

1. Open `/sign/`. Enter seat 39 and load the account. Confirm an address and a balance appear,
   and the request log shows `eth_getBalance`.
2. Keep the default name and description and build the mint. Confirm the badge image appears,
   To is the badge contract, and the function selector is `0xd0def521`.
3. Sign and send. Within about 15 seconds confirm the status reads "Mined in block N" with N
   above 17, a badge number, a Transfer log from the zero address to the seat's address, and
   "Same as what you sent?" answered yes, with the image read back from the contract.
4. Confirm the log shows `eth_getTransactionCount`, `eth_getBlockByNumber`,
   `eth_sendRawTransaction`, `eth_getTransactionReceipt` answering `null` until it returns a
   receipt with status `0x1`, then an `eth_call` for `tokenURI`.
5. Follow the transaction link. Confirm the explorer shows From the seat's address,
   "Interacted With (To)" CourseBadge, Transaction Action "mint" and Logs (1).
6. Under "Ask the contracts", ask `ownerOf` for the new badge (the seat's address) and
   `balanceOf` for Account 3 (0, "the token has 6 decimals"). Check console errors and failed
   network requests.

## Links and Fallback

1. Open `/lab/`. Confirm the worksheet renders and its links to the explorer, the mint page and
   the saved pages all load.
2. Open `/fallback/`. Confirm the blocks 0-17 navigation works and "Contract reads at block 17"
   lists the implementation slot, supply 8,900 cUSD and `ownerOf(1)` Account 2. Follow its
   "recorded mint" link: `mint-run.html` shows the badge, the five steps and the request log,
   with links back to the worksheet and the saved pages.
3. On the course site host, open `/labs/tokens/`. Confirm it lands on the worksheet.

## Spot the Fake

The day's last game (blocks 18-30). Its key is `dynamic-labs/tokens/quizes/SPOT_THE_FAKE_ANSWERS.md`; the
addresses are in `dynamic-labs/tokens/quizes/spot-the-fake.env`.

1. On the course site host, open `/assets/labs/spot-the-fake/index.html`. Walk the case and the
   prediction (pick the creator and the code, Moderate). On the do step, confirm three tokens are
   listed with their addresses and their "Open in the explorer" links point at the lab host.
2. Follow Token 2's link. Confirm Otterscan shows a Contract creator line naming Account 0
   (`0xf39F…2266`) with a creation transaction in block 19, and a Contract tab with DollarProxy
   as an exact match and its implementation, CoursePound. Token 1 shows Account 7
   (`0x14dC…9955`), block 21, and PlainToken; Token 3 shows Account 7, block 24, DollarProxy.
3. On `/sign/`, "Ask the contracts", ask `name()`, `symbol()` and `decimals()` of each token:
   all answer Course Pound, cGBP and 6. Ask `owner()` of Token 1: the contract refuses.
4. Back on the game, call Token 2 real because of its creator, Tokens 1 and 3 fake because of
   their creator, with a line each, and finish: the shell shows the prediction held. Pick "its
   name or symbol" for one token instead and confirm the page marks it 0 points.
5. Name and explorer steps render; on the twist, open the fourth token: `owner()` on the sign
   page answers Account 0, its creator is Account 7. Answer "no" and confirm the answer and why
   appear. On the tell step, write a sentence with a confidence word and confirm the example
   shows. Check console errors and failed network requests.

## Not Covered Here

- the classroom (`tokens.lab`) and cloud (`tokens.<domain>`) hosts and their certificates
- a whole class minting at once (40 seats against one 12-second block)
- Otterscan's look on a phone-width screen

## Completion Rule

Complete when every step above passes, or each failure carries its evidence and a fix
recommendation.
