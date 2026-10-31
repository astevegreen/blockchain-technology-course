# Day 1 Explorer Lab Regression Playbook

This playbook is the browser-driven companion to the automated `explorer` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The explorer stack is running (`./lab-manager.sh start explorer`) and the automated suite has
   passed against it. Do not reset just to start the browser stage.
2. The explorer has its own host: `http://explorer.localhost/` on this machine. The course
   site's `/labs/explorer/` redirects there.
3. No credentials: the lab has no instructor surface. The signing page's seat keys come from a
   public test phrase and exist only on the training chain.
4. Use seat 39 for the signing task (the automated suite uses seat 40). If an earlier run used
   seat 39, its nonce has moved on: that is expected.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures
and a screenshot.

## Explorer Flow

1. Open `/` on the explorer host. Confirm the header reads "Course chain (training)" and the
   footer names `/rpc` on the same host.
2. Search `3`. Confirm block 3's page shows Timestamp `Sep-14-2026 02:00:36 PM +UTC`, one
   transaction, a Base Fee and a Parent Hash.
3. Open `/tx/0xaeff71f0c8f69a5dc00df35f2f754423568847cb550ad40121d6d13324aaa779`. Confirm
   "From / Nonce" shows Account 1 with nonce 0, "Interacted With (To)" Account 2, Value 1.5 ETH,
   Transaction Fee 0.000016180715292 ETH, and "Block / Position" with a confirmation count.
4. Open the token address `0x5FbDB2315678afecb367f032d93F642f64180aa3`. Confirm the name
   "Course Token (CRT)", a "Contract creator" field, and the Contract tab showing Solidity
   source (served from the lab's own `/sourcify`).
5. Open block 4's transaction. Confirm "Tokens Transferred" shows 5,000 CRT to Account 3 and the
   Logs tab shows a decoded `Transfer` event.
6. Open block 5's transaction. Confirm three TRANSFER lines: 2 ETH to the Splitter, then 1 ETH
   each to Account 2 and Account 4.
7. Open block 6's transaction. Confirm the Status line reads "Fail with revert message" and
   names "balance too low".
8. Open `/block/7/txs`. Confirm two transactions, listed newest first (position 1 above
   position 0); open each and confirm "Block / Position" 7/0 for Account 2's 0.4 ETH and 7/1 for
   Account 3's token transfer.
9. Open Account 3 (`0x90F79bf6EB2c4f870365E785982E1f101E93b906`). Confirm "Transactions sent: 2"
   and three rows (blocks 8, 7, 7). A higher count means someone sent from Account 3 on the live
   chain: note it, not a failure.
10. Open Account 2 (`0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC`). Confirm its block-5 row shows
    2 ETH (the challenge tells students to open the transaction for the 1 ETH that reached it).
11. Open Account 5 (`0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc`). Confirm the explorer gives it
    no name: the "class drop box" label is only on the saved pages.
12. Check console errors and failed network requests. A 404 from `/sourcify` for an address
    that is not a contract is expected; anything else is a failure.

## Signing Flow

1. Open `/sign/`. Enter seat 39 and load the account. Confirm an address, a balance and a next
   nonce appear, and the request log shows `eth_getBalance` and `eth_getTransactionCount`.
2. Build the default transaction (0.01 ETH to Account 5). Confirm type 2, chain ID 31337, the
   nonce, gas limit 21000, and a From row saying it is not in the transaction.
3. Sign. Confirm r, s, yParity, the signed bytes, a transaction hash, and "Matches your
   address?" answered yes.
4. Send. Within about 15 seconds confirm the status reads "Mined in block N after about M s in
   the mempool" with N above 10, and the log shows `eth_sendRawTransaction`, then
   `eth_getTransactionReceipt` answering `null` until it returns a receipt with status `0x1`.
5. Follow "Open it in the explorer". Confirm the transaction page loads for that hash with From
   the seat's address.
6. Check console errors and failed network requests.

## Openers Flow

Follow `tasks/openers-flow.md`. It needs the exercises and bitcoin labs running as well as the explorer.

## Links and Fallback

1. Open `/lab/`. Confirm the worksheet renders and its links to the explorer, the signing page
   and the saved pages all load.
2. Open `/fallback/`. Confirm the blocks 0-10 navigation works and block 7 lists position 0
   before position 1. Follow its "recorded run" link: `sign-run.html` shows the four steps and
   the request log, with links back to the worksheet and the saved pages.
3. On the course site host, open `/labs/explorer/`. Confirm it lands on the worksheet.

## Not Covered Here

- the classroom (`explorer.lab`) and cloud (`explorer.<domain>`) hosts and their certificates
- a whole class sending at once (40 seats against one 12-second block)
- Otterscan's look on a phone-width screen
- the CI Lab Tests: the explorer is not in them yet (`docs/follow-ups.md`)

## Completion Rule

Complete when every step above passes, or each failure carries its evidence and a fix
recommendation.
