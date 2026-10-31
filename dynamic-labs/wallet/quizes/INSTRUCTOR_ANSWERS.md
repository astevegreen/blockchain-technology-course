# Day 2 wallet lab: instructor answers

Instructor only: `pages.yml` and `vm-build.yml` leave every lab's `quizes/` folder out of what
students receive. The worksheet is `gateway/static/lab/index.html`; the numbers below come from
the frozen chain (`quizes/facts.json`, built by `quizes/build-steps.sh`) and match the saved pages
(`gateway/static/fallback/`). The automated suite checks the wallet page's addresses and the live
explorer against `facts.json`.

The chain is frozen: blocks 1-20 never change and nothing on it accepts new transactions, so live
and saved answers always agree. Block 13 was made at 31 Oct 2026, 18:04:09 UTC; blocks 14-18 at
18:04:10 UTC. mempool shows them in the viewer's local time.

## Names

| Name | Address | Where it comes from |
|---|---|---|
| Dana receiving 0 (R0) | `bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu` | `m/84'/0'/0'/0/0`, abandon phrase (BIP 84 test vector) |
| Dana receiving 1 (R1) | `bc1qnjg0jd8228aq7egyzacy8cys3knf9xvrerkf9g` | `m/84'/0'/0'/0/1` |
| Dana receiving 2 (R2) | `bc1qp59yckz4ae5c4efgw2s5wfyvrz0ala7rgvuz8z` | `m/84'/0'/0'/0/2` |
| Dana receiving 3 (R3) | `bc1qgl5vlg0zdl7yvprgxj9fevsc6q6x5dmcyk3cn3` | `m/84'/0'/0'/0/3`, never used |
| Dana receiving 23 (R23) | `bc1qut5hjrs2l8lxk5rrmt9a0s0z9237h44szk0fyr` | `m/84'/0'/0'/0/23`, past the gap limit |
| Dana change 0 (C0) | `bc1q8c6fshw2dlwun7ekn9qwf37cu2rn755upcp6el` | `m/84'/0'/0'/1/0` (BIP 84 test vector) |
| Treasury receiving 0 (T0) | `bc1qm43n7nnev58aj3nrznz2xscgv98t7gxycq5pmp20a5vzfp5t0q2s7r6twa` | 2-of-3, chain 0, index 0 |
| Treasury change 0 (TC0) | `bc1qy0qa9lx04k0lk9lrv4542ndehul9spkcafdtcpdv38qx6ft5km2ssnce5d` | 2-of-3, chain 1, index 0 |
| Shop | `bc1qtvrqtcq8edgtd2xdcesdyvxtpg7g47ygz60r70` | course faucet wallet |
| Vendor | `bc1q5denfzx3pz24tgxggtqr9dj4j4racrpj0wfxna` | course faucet wallet |
| Faucet | `bc1qkmyuwjwpxcqp82hfcqmphfvzyf7q4acajmthfw` | mines every block |

Treasury keys, all at `m/48'/0'/0'/2'`:

| Key | Holder | Phrase | Master fingerprint | Public key at `/0/0` |
|---|---|---|---|---|
| A | Dana | abandon ... about | `73c5da0a` | `03dc1953c2756c7c58d4f48ca1bbba767f414fd236bf4d662b67721ac626c514e0` |
| B | Eli | legal winner ... yellow | `b8688df1` | `028e818df63d6f2dce9308d7455fd4c85cbb39d703608b8fbed647d75e262322d8` |
| C | Fran | letter advice ... above | `28645006` | `03229cb34fe3eb1af43b6dd2a2e1b31681039b71d9303ded36b3128ef359e379bd` |

## Transactions

| Block | Name | ID | Inputs | Outputs | Fee |
|---|---|---|---|---|---|
| 13 | fund0 | `f1716cc102e3a41b93b23527a1a23b8ebfd527fcf238c8e1451d5ab2a4193371` | faucet 50 | `bc1qlxhay94m…kj09` 49.94999436; R0 0.05 | 564 sats, 141 vB |
| 14 | fund1 | `81d9c77d4bccc7e28e8d4d281d2b39082a71fd7c960103d867d5d7f6b9f0117d` | fund0 output 0 | `bc1q9fl39cpx…nq7` 49.92998872; R1 0.02 | 564 sats, 141 vB |
| 15 | fund2 | `e60f0f3d145271695741d50ffa06aa223b5d5197b9c5a2694516a452ebfb91e2` | fund1 output 0 | `bc1qzaktvjam…j3x` 49.91498308; R2 0.015 | 564 sats, 141 vB |
| 15 | fund23 | `a06c0d1f04452c4863f05f9bce3695de923e91cae31af2016a09fd600d62edde` | faucet 50 | R23 0.01; `bc1qvy9xpfnk…7zr` 49.98999436 | 564 sats, 141 vB |
| 16 | spend | `6727f64849f26d210a7569edf9377a177d94638e4580fe707c362b52eae83e9e` | R0 0.05, R1 0.02 | shop 0.06; C0 0.00998 | 2,000 sats, 208 vB |
| 17 | tfund | `bbbd35a93b3d3c9ada97c8300f9706a52551bae0c5175e411fb94614478d9a45` | fund2 output 0 | `bc1pugfmxqks…qyww` (P2TR) 49.61497648; T0 0.3 | 660 sats, 165 vB |
| 18 | tspend | `c61b85d0c7091124584d18331753e06ee90f1498df99e41a80ac53a4fc8cf829` | T0 0.3 | TC0 0.17999055; vendor 0.12 | 945 sats, 189 vB |

Every input signals replaceability (nSequence `0xfffffffd`). The faucet's change goes to a fresh
address each time. On the saved pages, which leave out block rewards, the faucet's own address
shows only its two 50 BTC spends; the live explorer also lists the 20 block rewards it received.

## Worked example

Receiving 0 is R0. fund0 (block 13) spends a 50 BTC faucet output: 0.05 BTC to R0 at output 1,
49.94999436 BTC to a new address at output 0 (likely the faucet's change), fee 564 sats for 141 vB
(4 sat/vB). The witness is a 71-byte signature and a 33-byte public key. R0 is spent in block 16.
"R0 received 0.05 BTC in block 13 and spent it in block 16" is a recorded fact and takes no
confidence word; that R0 is Dana's comes from her phrase, not from the chain.

## Questions

1. **`m/84'/0'/0'/0/0`.** `m` the master key; `84'` purpose (BIP 84, native SegWit P2WPKH);
   `0'` coin type (Bitcoin); `0'` account (her first); `0` the receiving chain (`1` is change);
   `0` the address index. `'` marks a hardened level.
2. **Indices 0, 1 and 2 are used; 3 is not.** R0 received 0.05 in block 13, R1 0.02 in block 14,
   R2 0.015 in block 15. R0 and R1 were spent in block 16; R2 is unspent. R3 has no transactions
   (the explorer shows an empty address; the saved pages say no transactions touch it).
3. **Shop 0.06 is the payment, C0 0.00998 is change.** From the explorer alone: both outputs are
   new addresses and both are P2WPKH like the inputs, so those clues do not separate them; only
   the round amount does. On the amount alone: **Low**. Accept Moderate only if the student
   names a second, different clue (there is none on this transaction). With the wallet page:
   C0 is Dana's change address 0, so the call is certain given the phrase; the point is that the
   certainty comes from off-chain evidence (the phrase), not the chain.
4. **Co-spending in block 16** ties R0 and R1: one transaction spends both. C0 is tied only if the
   change call in Q3 is right. Confidence **Moderate** for R0 and R1 (one strong line; CoinJoin is
   the known false positive). C0 with them: **Low** (it rests on the round-amount call). Day 6
   builds clustering on this.
5. **Every address on her account branch**: all receiving and change addresses below
   `m/84'/0'/0'`, past and future. **No spending**: an xpub holds no private key. **No treasury
   key**: key A is at `m/48'/0'/0'/2'`, a different hardened branch from the master; a hardened
   child cannot be derived from a public key, so the account xpub reaches nothing outside its own
   branch.
6. **P2WSH** (`V0_P2WSH`). Witness script `OP_PUSHNUM_2`, three 33-byte keys, `OP_PUSHNUM_3`,
   `OP_CHECKMULTISIG`: 2 of 3. The witness has four items: empty, 71 bytes, 71 bytes, 105 bytes
   (the script). The empty first item is the dummy `OP_CHECKMULTISIG` consumes; BIP 147 requires
   it to be empty.
7. **B, C, A.** First key `028e81…22d8` is B (Eli), second `03229c…79bd` is C (Fran), third
   `03dc19…14e0` is A (Dana). BIP 67 sorts keys by their bytes, so `02…` comes before `03…`, and
   `0322…` before `03dc…`. The order says nothing about who is who or who matters most.
8. **A and C signed** (Dana and Fran; the build script has them sign). The explorer cannot say:
   it shows two signatures but not which key each matches. Signatures must be in key order, so
   the possible pairs are B+C, B+A or C+A. A student who says "I can't tell from the explorer"
   is right. Teaching note: the 06-BF speaker notes describe "A's signature, C's signature"
   generically; on this chain the sorted order makes signature 1 C's and signature 2 A's.
9. **Vendor 0.12 is the payment; TC0 0.17999055 is change.** Clues: TC0 is P2WSH like the input
   (the vendor's is P2WPKH), and 0.12 is round while 0.17999055 is not. Two different clues agree,
   but both are heuristics a careful wallet can defeat: **Moderate**; accept Low with a reason.
   The wallet page (chain 1, index 0) gives TC0 as the treasury's change address.
10. **Only a hash.** TC0's page shows a P2WSH output: a 32-byte script hash. The 2-of-3 rule, the
    keys and the threshold appear only when it is spent. That it belongs to the same treasury is
    known only from the wallet page.
11. **Model sentence** (06-BF): "This transaction spends a P2WSH 2-of-3 multi-sig output; two of
    its three keys signed (read from the witness). Who holds the keys is not shown on chain."
    Accept any sentence that gives the type, the 2-of-3 and two signatures, and says the holders
    (and which two signed) are not shown.
12. **On chain: no link.** No transaction moves coins between Dana's addresses and the treasury,
    and none spends from both. Both were paid by the faucet (its change chain runs fund0 → fund1 →
    fund2 → tfund), but a common payer is not a common owner. **Off chain:** Dana's master
    fingerprint (`73c5da0a`, section 1) equals key A's: one seed holds both. Fingerprints appear in
    descriptors and wallet files, never in a transaction.

## Challenge

a. R23 received 0.01 BTC in block 15 (fund23). A standard restore misses it: indices 3-22 are 20
   unused addresses in a row, the gap limit, so the wallet stops before 23. An analyst with a
   recovered phrase should raise the gap limit or check addresses further down the list.
b. The passphrase `TREZOR` gives master fingerprint `b4e3f5ed` and receiving 0
   `bc1qv5rmq0kt9yz3pm36wvzct7p3x6mtgehjul0feu`, which has no transactions. The wallet is valid,
   not wrong: every passphrase opens a valid wallet, and only the right one opens the funded one.
c. No. The witness holds two signatures and nothing about who made them or where. One person with
   two of the three phrases would produce the same transaction.
