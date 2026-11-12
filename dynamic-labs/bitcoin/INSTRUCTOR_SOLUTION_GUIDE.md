# Bitcoin Lab — Instructor Solution Guide

> Reference answers mapped to the **deployed** lab at
> `https://blockchain.training-as-code.com/labs/bitcoin/`.
>
> Verified on **2026-06-03** by walking the live chain on the `bitcoin-instructor-1` node
> (chain height **275**) and cross-checking in the **btc-rpc-explorer** GUI. The lab text is served
> from `/api/bitcoin/exercises` (source: `lane-service/labs/bitcoin_catalog.yaml`).
>
> **Scope note:** Lab 1 and Lab 2 are deterministic command exercises — the commands below are the
> exact ones the lab hands the student. The Forensics Lab was archived on 11 Nov 2026; its answer key
> and the method for regenerating it are in
> `archive/dynamic-labs/bitcoin-forensics/INSTRUCTOR_SOLUTION_GUIDE-forensics.md`.

---

## 0. Lab at a glance

| | |
|---|---|
| **Tabs** | Primer · Terminal & Zellij · Lab 1 · Regtest · Lab 2 · ClassNet |
| **Tools given to the student** | Web terminal (**ttyd** + **zellij**), **btc-rpc-explorer** ("Explorer" link), **mempool** UI ("Mempool" link), `~/scripts/miner.py`, `~/scripts/agent.py`, a personal static site (`~/share`) |
| **Network** | Custom "ClassNet" Bitcoin Core fork. **Coinbase maturity = 10 blocks** (not 100). **Difficulty retargets every 2 blocks** (not 2016), aiming at 10 seconds a block. Genesis `nBits = 0x207fffff`, 50 BTC initial reward. Uses mainnet-style `bc1q…` bech32 HRP. |
| **Two chains** | Lab 1 runs a **private** regtest node (own datadir/ports, driven by a `btc-lab1` alias). Lab 2 uses the **shared ClassNet** node (`bitcoin-cli` with no `-regtest`). |
| **Explorer URLs** | Tx: `…/labs/bitcoin/btc-explorer/tx/<txid>` · Address: `…/btc-explorer/address/<addr>` · Block: `…/btc-explorer/block-height/<n>` |

The exercise deck has **30 steps** in 4 groups. Each step has a GOAL, YOUR STEPS (with COPY-able
commands), EXPECTED OBSERVATIONS, and WHY THIS MATTERS.

---

## 1. PRIMER — Navigate the workstation

| Step | Solution | Expected |
|---|---|---|
| Orient | `pwd` ; `ls -a` | home dir + dotfiles |
| Move around | `cd ~/scripts` ; `ls` ; `cd ~` | `miner.py`, `agent.py` present |
| Zellij tabs | `Ctrl+G` then `t` then `n` (new tab); `Ctrl+G t Left` (prev) | new tab opens |
| Zellij panes | `Ctrl+G` then `p` then `r` (split L/R); `Alt+Arrow` to move; `exit` to close | split pane |
| Scrollback | `Ctrl+G` then `s` (scroll mode), arrows / PgUp-PgDn, `Ctrl+G` to return | scrollback works |
| Before `nano` | press `Ctrl+G` first to lock zellij so nano shortcuts pass through | — |

---

## 2. LAB 1 · Regtest (private sandbox)

> Drive everything through the `btc-lab1` alias so you never touch the ClassNet node.

### 1.1 Start a private regtest node
```bash
mkdir -p ~/.bitcoin-regtest
bitcoind -regtest -daemon \
  -datadir=$HOME/.bitcoin-regtest \
  -rpcport=18443 -port=18444 \
  -fallbackfee=0.0001 -txindex=1
alias btc-lab1="bitcoin-cli -regtest -datadir=$HOME/.bitcoin-regtest -rpcport=18443"
btc-lab1 getblockchaininfo
```
**Expected:** `"chain": "regtest"`, `"blocks": 0`. The ClassNet node is untouched.

### 1.2 Genesis of a chain — wallets + first blocks
```bash
btc-lab1 createwallet "student"
btc-lab1 createwallet "alice"
STUDENT_ADDR=$(btc-lab1 -rpcwallet=student getnewaddress)
ALICE_ADDR=$(btc-lab1 -rpcwallet=alice getnewaddress)
btc-lab1 generatetoaddress 11 $STUDENT_ADDR
btc-lab1 -rpcwallet=student getbalance
```
**Expected:** **50.0 BTC** (block #1 coinbase, mature after 10 more blocks). Alice = 0.

### 1.3 Anatomy of a block header
```bash
BLK1=$(btc-lab1 getblockhash 1)
btc-lab1 getblock $BLK1            # examine previousblockhash, merkleroot, bits, nonce
```
**Expected:** `previousblockhash` → genesis; `bits` = `207fffff`; a `nonce` the miner found.

### 1.4 Decode the difficulty (bits → target)
```bash
python3 -c 'b=0x207fffff; e=b>>24; c=b&0xffffff; print(hex(c*256**(e-3)))'
```
**Expected:** a very large 256-bit target (lots of room → trivial PoW on regtest).

### 1.5 Send + confirm a transaction
```bash
TXID=$(btc-lab1 -rpcwallet=student sendtoaddress $ALICE_ADDR 10)
btc-lab1 generatetoaddress 1 $STUDENT_ADDR
btc-lab1 -rpcwallet=alice getbalance      # 10
```
### 1.6 Decode the coinbase (money from nothing)
```bash
CB=$(btc-lab1 getblock $(btc-lab1 getblockhash 1) | jq -r '.tx[0]')
btc-lab1 getrawtransaction $CB true        # vin has "coinbase", no prev txid
btc-lab1 getrawtransaction $TXID true      # vin references a real prior output
```
**Expected:** coinbase `vin[0]` has a `coinbase` field and no `txid`; the spend's `vin` references a prior tx (chain of ownership).

### 1.7 Deserialize a tx with python-bitcoinlib
```bash
export RAW_TX_HEX=$(btc-lab1 getrawtransaction $TXID false)
# decoder.py reads $RAW_TX_HEX with bitcoin.core.CTransaction.stream_deserialize
python3 decoder.py
```
**Expected:** prints version, locktime, inputs (prev txid+index), outputs (10 BTC to Alice; change to student, in satoshis).

### 1.8 Refresher — one byte changes everything
```bash
python3 -c 'import hashlib;d=lambda x:hashlib.sha256(hashlib.sha256(x).digest()).digest();
a=b"A"*64;b=b"B"*64;print(d(d(a)+d(b)).hex());print(d(d(b"a"+b"A"*63)+d(b))).hex())'
```
**Expected:** the two roots are completely different (avalanche effect).

### 1.9–1.11 Merkle-root corruption challenge
1. **Corrupt** (`corrupt_block.py <merkleroot>`): de-obfuscates `blk00000.dat` with `xor.dat`, finds the Merkle root bytes (reversed), overwrites with `0xaa…`, re-obfuscates. Back up `.bak` first.
2. **Validate fail:** `btc-lab1 verifychain 4 10` → **false**; `~/.bitcoin-regtest/regtest/debug.log` shows hash mismatch / PoW failure (the 80-byte header changed → block hash no longer meets target).
3. **Fix** (`fix_block.py`): prints the corrupted header's hash (no leading zeros = broken PoW), restores the real Merkle bytes from `.bak`, re-obfuscates → `verifychain 4 10` → **true**.

### 1.12 Cleanup
```bash
btc-lab1 stop
```

---

## 3. LAB 2 · ClassNet (shared chain)

> No `-regtest` / no alias — plain `bitcoin-cli` talks to the shared ClassNet node.

### 2.1 Identity & sharing
```bash
bitcoin-cli createwallet "student_wallet"
MY_ADDR=$(bitcoin-cli -rpcwallet=student_wallet getnewaddress)
echo $MY_ADDR > ~/share/address.txt        # published on your static site
```
### 2.2 Mine coins (until 50 BTC trusted)
```bash
mine-until student_wallet $MY_ADDR
bitcoin-cli -rpcwallet=student_wallet getbalance
```
**Expected:** 50 BTC. `mine-until` (`/usr/local/bin/mine-until`, a short commented bash script) mines one block at a time.
If it prints "would be hard ... waiting", that is expected: back-to-back blocks raise the 2-block retarget 4x a pair, so it
waits about 20 s for the easiest-difficulty block ClassNet allows after a 20 s gap, which resets the next retarget. Without
it, a class mining in a tight loop reaches blocks that take minutes around height 25-30.

### 2.3 Peer discovery & send
Open the **Peers ▾** dropdown → pick a classmate → copy their `address.txt`. Then:
```bash
PEER_ADDR=<peer address>
bitcoin-cli -rpcwallet=student_wallet sendtoaddress $PEER_ADDR 0.01
python3 ~/scripts/miner.py -v --address $MY_ADDR   # mine the confirming block; watch the Merkle line
```
### 2.4 Congestion — the flood agent
```bash
python3 ~/scripts/agent.py --wallet student_wallet --verbose   # Ctrl+C to stop
```
**Expected:** mempool fills; in the **Mempool** UI, fee rates climb. Discussion answer: to jump the queue you must **outbid** the spam (raise your fee rate).

### 2.5 Double-spend challenge
```bash
bitcoin-cli createwallet "cheater"
CHEAT_ADDR=$(bitcoin-cli -rpcwallet=cheater getnewaddress)
mine-until cheater $CHEAT_ADDR
bitcoin-cli -rpcwallet=cheater sendtoaddress $PEER_ADDR 49.999 "" "" true
bitcoin-cli -rpcwallet=cheater sendtoaddress $MY_ADDR  49.999 "" "" true   # ERROR
```
**Expected / answer:** the **second** send fails with **`Insufficient funds`**. Key teaching point: the rejection came from **your own local node's wallet/mempool** (it won't let you build a conflicting spend), *not* from miners — the network never even saw it.

### 2.6 Explore
Use **Explorer** / **Mempool** to look up your own and classmates' TXIDs and addresses (confirmations, fee rate, vin/vout).

### Bonus 2.x
- **RBF (unstick a tx):** `bitcoin-cli -named sendtoaddress address=$PEER_ADDR amount=0.001 fee_rate=1 replaceable=true` → it sticks at the bottom of a congested mempool → `bitcoin-cli bumpfee <txid>` returns a new higher-fee TXID that confirms.
- **Censorship (malicious miner):** edit `~/scripts/miner.py`, in the transaction loop add `if tx_id_hex == "<PARTNER_TXID>": continue` → run the miner → the partner's tx stays unconfirmed in the mempool (miners choose what to include).
- **Difficulty adjustment:** `bitcoin-cli getblockchaininfo | grep difficulty` → mine 5 fast blocks → difficulty **rises** (ClassNet retargets every 2 blocks; fast blocks = harder next round).

---

## 4. Operational notes for instructors

- **Two explorers:** "Explorer" = btc-rpc-explorer (`/labs/bitcoin/btc-explorer/`), best for tx/address
  drill-down; "Mempool" = mempool.space UI (`/labs/bitcoin/mempool/`), best for the fee-market view in
  Lab 2.
- **If the lab UI shows 502 / the terminal won't load**, the per-student lane or the bitcoin instructor
  backend is cycling; the btc-explorer itself stayed healthy during testing. Reload to re-claim a lane.
- **Noise reality check:** because Lab 2 congestion traffic accumulates on the shared chain, students
  will see thousands of unrelated txs.
