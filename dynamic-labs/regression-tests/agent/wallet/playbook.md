# Day 2 Wallet Lab Regression Playbook

This playbook is the browser-driven companion to the automated `wallet` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The wallet stack is running (`./lab-manager.sh start wallet`) and the automated suite has
   passed against it. Do not reset just to start the browser stage: the chain is frozen at height
   20 and nothing a student does changes it.
2. The lab is under the course site's router: `http://127.0.0.1/labs/wallet/` on this machine.
3. No credentials: the lab has no instructor surface. The phrases come from published test
   vectors and exist only on the training chain.
4. Use a window at least 800 pixels wide. A narrower one shows mempool's mobile page, which the
   worksheet does not describe.

The names below (R0, C0, T0, TC0 and so on) and every value come from
`dynamic-labs/wallet/quizes/INSTRUCTOR_ANSWERS.md` and `dynamic-labs/wallet/quizes/facts.json`.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures
and a screenshot.

## Explorer Flow

1. Open `/labs/wallet/mempool/`. Confirm the dashboard loads under that path (no request to
   `/api/...` without the `/labs/wallet/mempool` prefix) and shows blocks up to height 20.
2. Search R0, `bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu`. Confirm the address page lists two
   transactions, received 0.05 BTC and a balance of 0.
3. Open the older one, `f1716cc102e3a41b93b23527a1a23b8ebfd527fcf238c8e1451d5ab2a4193371`
   (fund0, block 13). Confirm the worked example's table: input
   `bc1qkmyuwjwpxcqp82hfcqmphfvzyf7q4acajmthfw` 50 BTC; output 0
   `bc1qlxhay94m94y9jx0meq64e75ld6ahj6tn88kj09` 49.94999436 BTC; output 1 R0 0.05 BTC; fee 564 sat;
   141 vB.
4. Press "Details". Confirm the input shows nSequence `0xfffffffd`, a witness of two items (a
   71-byte signature and a 33-byte key) and the type P2WPKH.
5. Open the spend, `6727f64849f26d210a7569edf9377a177d94638e4580fe707c362b52eae83e9e` (block 16).
   Confirm two inputs (R0 0.05, R1 0.02), outputs shop `bc1qtvrqtcq8edgtd2xdcesdyvxtpg7g47ygz60r70`
   0.06 and C0 `bc1q8c6fshw2dlwun7ekn9qwf37cu2rn755upcp6el` 0.00998, fee 2,000 sat. Confirm the
   explorer labels neither output as change.
6. Open the treasury spend,
   `c61b85d0c7091124584d18331753e06ee90f1498df99e41a80ac53a4fc8cf829` (block 18), and press
   "Details". Confirm the input is P2WSH (T0, 0.3 BTC); the witness has four items, the first
   empty; the explorer decodes the last as "P2WSH witness script" reading `OP_PUSHNUM_2`, three
   33-byte keys starting `028e818d`, `03229cb3`, `03dc1953` in that order, `OP_PUSHNUM_3`,
   `OP_CHECKMULTISIG`. Outputs: TC0 0.17999055 (P2WSH) and vendor
   `bc1q5denfzx3pz24tgxggtqr9dj4j4racrpj0wfxna` 0.12 (P2WPKH); fee 945 sat.
7. Search R3, `bc1qgl5vlg0zdl7yvprgxj9fevsc6q6x5dmcyk3cn3`. Confirm an address page with no
   transactions (not an error page).
8. Search R23, `bc1qut5hjrs2l8lxk5rrmt9a0s0z9237h44szk0fyr`. Confirm 0.01 BTC received in block 15.
9. Search TC0, `bc1qy0qa9lx04k0lk9lrv4542ndehul9spkcafdtcpdv38qx6ft5km2ssnce5d`. Confirm one
   unspent output of 0.17999055 BTC and no script shown (only spending reveals it).
10. Confirm block times show as local time and that dollar figures or "Accelerate" buttons, if
    shown, are the offline quirks the worksheet's "Reading this explorer" names, not errors.
11. Check console errors and failed network requests. Failed price or websocket reconnects that
    do not break a page are notes; a page that does not load, or an API call outside
    `/labs/wallet/mempool/`, is a failure.

## Wallet Page Flow

1. Open `/labs/wallet/wallet/`. Confirm both sections render and the page makes no network
   request after loading (the derivation runs in the browser).
2. Paste `abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about`
   into section 1, leave the passphrase empty, press "Derive the wallet". Confirm fingerprint
   `73c5da0a`, account path `m/84'/0'/0'`, an xpub starting `xpub` and a zpub starting `zpub`;
   receiving index 0 to 3 are R0, `bc1qnjg0jd8228aq7egyzacy8cys3knf9xvrerkf9g`,
   `bc1qp59yckz4ae5c4efgw2s5wfyvrz0ala7rgvuz8z` and R3, with paths `m/84'/0'/0'/0/0` to `/0/3`;
   20 receiving rows; change index 0 is C0 at `m/84'/0'/0'/1/0`.
3. Press "Show 20 more". Confirm 40 rows and index 23 is R23.
4. Type `TREZOR` as the passphrase and derive again. Confirm fingerprint `b4e3f5ed` and receiving
   0 `bc1qv5rmq0kt9yz3pm36wvzct7p3x6mtgehjul0feu`.
5. Change one word of the phrase (for example the last word to `abandon`) and derive. Confirm the
   red message "That is not a valid seed phrase: a word is misspelled, missing or out of order."
   and that the address tables hide.
6. In section 2, paste key A (the abandon phrase), key B
   `legal winner thank year wave sausage worth useful legal winner thank yellow` and key C
   `letter advice cage absurd amount doctor acoustic avoid letter advice cage above`; leave index 0
   and press "Combine the keys". Confirm fingerprints `73c5da0a`, `b8688df1`, `28645006`; the
   receiving public keys `03dc1953…14e0` (A), `028e818d…22d8` (B), `03229cb3…79bd` (C); receiving
   address T0 `bc1qm43n7nnev58aj3nrznz2xscgv98t7gxycq5pmp20a5vzfp5t0q2s7r6twa`; a witness script
   with the keys sorted B, C, A, matching explorer step 6; a descriptor starting
   `wsh(sortedmulti(2,[73c5da0a/48h/0h/0h/2h]xpub` and ending `#` plus eight characters.
7. Confirm the change address (chain 1) at index 0 is TC0.
8. Clear key C and press "Combine the keys". Confirm the message ends "Check all three phrases."
9. Check console errors.

## Links Flow

1. Open `/labs/wallet`. Confirm it lands on `/labs/wallet/lab/` with the title "Day 2 lab: a
   wallet on the course chain".
2. Follow the worksheet's links to the explorer, the wallet page and the saved pages, and back
   through each page's crumbs. Confirm every one loads under `/labs/wallet/`.
3. Confirm the worksheet's source links (`[1]` to `[19]`) jump to entries under "Sources".
4. Open `/labs/wallet/fallback/`. Search R0 and confirm the page jumps to R0's section (received
   0.05 in block 13, sent in block 16). Search the block 18 transaction ID and confirm its section,
   with the witness script. Search R3 and confirm "No transactions on this chain touch that
   address."
5. Open the course site's lab list and confirm a "Wallet Lab" link goes to `/labs/wallet/`.
6. Check console errors and failed network requests.
