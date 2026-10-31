#!/usr/bin/env bash
# Builds the spike's small chain inside the lab mempool image's own bitcoind (see ../mempool.md, "How to repeat it").
# Alice holds a legacy (P2PKH) coin and a native SegWit (P2WPKH) coin and pays Bob from both without RBF (tx1).
# Bob then pays Alice back twice with RBF on: tx2 is mined, tx3 is left unconfirmed.
# Run as root: the RPC cookie belongs to root. Run once on a fresh container; it is not idempotent.
set -euo pipefail
cli() { bitcoin-cli -datadir=/home/user/.bitcoin "$@"; }
# The course chain has real (low) proof of work and maxtries counts across the whole call, so a call can mine
# fewer blocks than asked: on 31 Oct 2026 the run reached height 23, not 106. Coins mature after 10 blocks here.
mine() { cli -rpcwallet=miner generatetoaddress "$1" "$maddr" 100000000 >/dev/null; }
txid() { python3 -c 'import sys,json; print(json.load(sys.stdin)["txid"])'; }
cli -rpcwait getblockcount >/dev/null
for w in miner alice bob; do cli createwallet "$w" >/dev/null 2>&1 || cli loadwallet "$w" >/dev/null 2>&1 || true; done
M="cli -rpcwallet=miner"; A="cli -rpcwallet=alice"; B="cli -rpcwallet=bob"
maddr=$($M getnewaddress "" bech32)
mine 101
a_legacy=$($A getnewaddress "" legacy)
a_segwit=$($A getnewaddress "" bech32)
$M sendtoaddress "$a_legacy" 0.10 >/dev/null
$M sendtoaddress "$a_segwit" 0.05 >/dev/null
mine 1
bob=$($B getnewaddress "" bech32)
# tx1: both of Alice's coins, sequence 0xffffffff (no RBF), change back to the legacy address, 0.00005 BTC fee.
inputs=$($A listunspent | python3 -c 'import sys,json; print(json.dumps([{"txid":u["txid"],"vout":u["vout"],"sequence":4294967295} for u in json.load(sys.stdin)]))')
raw=$($A createrawtransaction "$inputs" "[{\"$bob\":0.12},{\"$a_legacy\":0.02995}]" 0 false)
signed=$($A signrawtransactionwithwallet "$raw" | python3 -c 'import sys,json; print(json.load(sys.stdin)["hex"])')
tx1=$(cli sendrawtransaction "$signed")
mine 1
# tx2: Bob pays Alice with RBF (BIP 125) on, then it is mined.
tx2=$($B -named send outputs="{\"$a_segwit\":0.01}" fee_rate=5 replaceable=true | txid)
mine 3
# tx3: the same again, left unconfirmed.
tx3=$($B -named send outputs="{\"$a_segwit\":0.005}" fee_rate=3 replaceable=true | txid)
echo "alice_legacy=$a_legacy alice_segwit=$a_segwit bob=$bob"
echo "tx1=$tx1"
echo "tx2=$tx2"
echo "tx3_unconfirmed=$tx3"
echo "height=$(cli getblockcount)"
