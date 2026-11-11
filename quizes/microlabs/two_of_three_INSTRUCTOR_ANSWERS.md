# Two of three: instructor key

Instructor only (students never receive `quizes/`). Lab: `blockchain-course/assets/labs/two-of-three/index.html`,
opened from the Bitcoin lab's panel bar ("Two of three") or the day 2 slide "A PSBT carries a half-signed spend";
design card `docs/lab-cards/two-of-three.md`. Pairs, one terminal each, about 35 minutes in two rounds.

## Before the game

With every student's Bitcoin lab station running, run on the lab host (where `docker` reaches the lab's containers):

```bash
python3 dynamic-labs/bitcoin/two-of-three/fund.py
```

By default it pairs the running stations in order (1 with 2, 3 with 4, ...); `--pairs 1:4,2:3` chooses the pairs.
An odd student out is paired with your own node: `--pairs 5:instructor`, or the default does it. It takes a minute
or two (it may wait for easy blocks), then prints the answer sheet and writes it beside the script as
`answers-<time>.md` (git-ignored). That sheet holds this class's addresses and blocks; this page holds what does not
change between classes.

What the script leaves in each student's node:

- wallet `two-of-three`: the pair's 2-of-3 lock, `wsh(sortedmulti(2, own key, partner's key, away key))`, holding
  0.5 BTC at its first address; it can sign with the student's own key only. The away key is on your node, in
  wallet `two-of-three-away`, and is never used.
- wallet `game-account`: the student's own account, paid 0.1 BTC at three receiving indexes.
- `~/two-of-three/partner-host` (the partner's container name) and `~/two-of-three/classmate.xpub` (the account key
  of the classmate this student watches in round 2: the station two along in the list, or the partner when only
  two play).

If you are a student's partner, your node holds wallet `two-of-three-with-<station>` (and its key wallet
`two-of-three-key-for-<station>`): the student is partner 1 and puts the half-signed spend in their share folder;
fetch it with `curl -s http://bitcoin-lab-student<station>:8000/half-signed.psbt` and run partner 2's commands with
`-rpcwallet=two-of-three-with-<station>`.

## The paid indexes (round 2)

The indexes depend only on the station number; the third is always beyond index 4.

| Station | Paid indexes |
| --- | --- |
| 1, 5, 9, ... (n mod 4 = 1) | 1, 3, 6 |
| 2, 6, 10, ... (n mod 4 = 2) | 0, 2, 7 |
| 3, 7, 11, ... (n mod 4 = 3) | 1, 3, 8 |
| 4, 8, 12, ... (n mod 4 = 0) | 0, 2, 5 |

All three are paid in one block: its height is on the printed sheet ("All funding confirmed in block N"), with each
student's classmate and the classmate's three addresses.

## Round 1

- **Prediction**: (c), refused: the lock wants a second signature. The reason to accept: two of three keys must
  sign, and one signature is not two. (a) and (b) treat the coin as being in the wallet (the wrong belief); (d)
  misreads "two of three".
- **finalizepsbt** after partner 1 signs: `"complete": false`, and no `"hex"`, so there is nothing to send.
  Partner 2 asks the same of the fetched file before signing and gets the same answer. After partner 2 signs the same spend: `"complete": true`, with a `"hex"` that `sendrawtransaction` accepts.
- **Witness** (explorer or `getrawtransaction <txid> 2`): four items: an empty first item (the extra item
  `OP_CHECKMULTISIG` consumes, which must be empty: `@lau_bip147dummy_2016`), two signatures, and the script
  `OP_2 <key> <key> <key> OP_3 OP_CHECKMULTISIG` (in hex it starts `52` and ends `53ae`). Three keys named, two
  signatures given, and nothing that names a person.

## Round 2

- **Twist**: "list their addresses and see their coins, but spend none". An xpub derives every receiving address
  of the account (`@wuille_bip32hierarchicaldeterministic_2012`) and holds no private key, so none can be spent.
- **The finds**: the classmate's three paid indexes (table above) and the funding block. The index is the address's
  position in the `deriveaddresses` list, counting from 0. A student who lists only indexes 0 to 4 misses the third:
  the page lists 0 to 9.
- **"Can you spend them?"**: no, because the xpub has no private key. The page's try puts the xpub in a wallet
  `watch` with no private keys: `getbalance` shows the classmate's 0.3, and `walletprocesspsbt` on a spend from it
  answers `complete` false. Seeing is not spending.

## Scoring (card line 9)

| Round | What | Points |
| --- | --- | --- |
| 1 | The prediction, with its reason | 1 |
| 1 | Both finalizepsbt answers: false after one signature, true after two | 2 |
| 1 | The witness read: three keys, two signatures, and that it shows no person | 2 |
| 2 | Each of the classmate's paid addresses with its index and block | 1 each, 3 in all |
| 2 | "Can you spend them?" answered no, with the reason | 1 |

Ten points in all; time only breaks ties.

## The sentence

An accepted answer says the coin left a 2-of-3 multisig address signed by two of its three keys, that the chain
does not show who held them (one person holding two keys looks the same), and that naming a signer from the chain
alone is Low.

## If something goes wrong

- Balance 0 in `two-of-three`: the node has not seen the funding block yet; wait a few seconds. If it stays 0, run
  `fund.py` again for that pair (`--pairs 3:4`): it reuses the wallets and pays the same address again.
- `curl` of the partner's file prints nothing: partner 1 has not saved it yet, or a typo in the file name.
- `createwallet` says wallet `watch` already exists (a second try): skip that line, or use `loadwallet watch`.
- `generatetoaddress` prints `[]`: the next block is briefly hard; wait 20 s and run it again. You can also mine
  from your own terminal; any block confirms the spend.
