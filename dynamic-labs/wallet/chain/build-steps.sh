#!/usr/bin/env bash
# Runs inside a throwaway container of the lab's mempool image (build-chain.sh starts it) and mines the
# day-2 wallet chain on the course chain's own bitcoind. Writes to /chain/out/:
#   blocks.hex   every block after genesis, oldest first, as raw hex (load-chain.sh replays them)
#   facts.json   the addresses, keys and transactions the worksheet names (the tests check against it)
#   tx-*.json    decoded transactions for the saved pages (capture_pages.py)
#
# The story: Dana's wallet comes from a seed phrase (BIP 84, native SegWit). Payments arrive at her first
# three receiving addresses and one far down the list (index 23, past the gap limit of 20); she pays a shop
# from two of them, with change to her first change address. Dana, Eli and Fran share a 2-of-3 P2WSH
# treasury (BIP 48 keys A, B and C); it is funded, then Dana (A) and Fran (C) sign a payment to a vendor,
# with change back to the treasury. The miner wallet is the course's faucet.
set -euo pipefail
cli() { bitcoin-cli -datadir=/home/user/.bitcoin "$@"; }
jget() { python3 -c "import sys,json; d=json.load(sys.stdin); print(d$1)"; }
keys() { python3 /chain/seedkeys.py "$1" "$2"; }
f() { echo "$1" | jget "[\"$2\"]"; }

PHRASE_A="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
PHRASE_B="legal winner thank year wave sausage worth useful legal winner thank yellow"
PHRASE_C="letter advice cage absurd amount doctor acoustic avoid letter advice cage above"

mkdir -p /home/user/.bitcoin /chain/out
cat > /home/user/.bitcoin/bitcoin.conf <<'CONF'
server=1
txindex=1
maxtipage=9999999999
CONF
bitcoind -datadir=/home/user/.bitcoin -daemon >/dev/null
cli -rpcwait getblockcount >/dev/null

# The course chain has real (low) proof of work, and generatetoaddress's maxtries counts across the whole
# call, so mine one block per call and repeat until it lands.
mine() {
    local i h
    for ((i = 0; i < $1; i++)); do
        h=$(cli getblockcount)
        until [ "$(cli getblockcount)" -gt "$h" ]; do
            cli generatetoaddress 1 "$MINER" 10000000 >/dev/null
        done
    done
}

cli -named createwallet wallet_name=miner >/dev/null
MINER=$(cli -rpcwallet=miner getnewaddress faucet bech32)
SHOP=$(cli -rpcwallet=miner getnewaddress shop bech32)
VENDOR=$(cli -rpcwallet=miner getnewaddress vendor bech32)
mine 12   # coinbase coins mature after 10 blocks on the course chain

checksum() { cli getdescriptorinfo "$1" | jget '["checksum"]'; }
derive() { cli deriveaddresses "$1#$(checksum "$1")" "[$2,$2]" | jget '[0]'; }
import_pair() {   # $1 wallet, $2 receiving descriptor, $3 change descriptor
    cli -rpcwallet="$1" importdescriptors "[
      {\"desc\":\"$2#$(checksum "$2")\",\"active\":true,\"internal\":false,\"timestamp\":\"now\",\"range\":[0,30]},
      {\"desc\":\"$3#$(checksum "$3")\",\"active\":true,\"internal\":true,\"timestamp\":\"now\",\"range\":[0,30]}]" \
      | python3 -c "import sys,json; r=json.load(sys.stdin); assert all(x['success'] for x in r), r"
}

# Dana's single-signature wallet: BIP 84, account 0, receiving chain /0/*, change chain /1/*.
K84=$(keys "$PHRASE_A" "m/84'/0'/0'")
recv="wpkh($(f "$K84" xprv)/0/*)"; chg="wpkh($(f "$K84" xprv)/1/*)"
cli -named createwallet wallet_name=dana blank=true >/dev/null
import_pair dana "$recv" "$chg"
R0=$(derive "$recv" 0); R1=$(derive "$recv" 1); R2=$(derive "$recv" 2); R3=$(derive "$recv" 3)
R23=$(derive "$recv" 23); C0=$(derive "$chg" 0); C1=$(derive "$chg" 1)

pay() { cli -rpcwallet=miner -named send outputs="{\"$1\":$2}" fee_rate=4 | jget '["txid"]'; }
vout_of() { cli getrawtransaction "$1" true | python3 -c "
import sys,json; t=json.load(sys.stdin)
print([o['n'] for o in t['vout'] if o['scriptPubKey'].get('address')=='$2'][0])"; }

FUND0=$(pay "$R0" 0.05); mine 1
FUND1=$(pay "$R1" 0.02); mine 1
FUND2=$(pay "$R2" 0.015); FUND23=$(pay "$R23" 0.01); mine 1

# Dana pays the shop 0.06 BTC from receiving addresses 0 and 1; 0.00998 BTC change to change address 0.
inputs="[{\"txid\":\"$FUND0\",\"vout\":$(vout_of "$FUND0" "$R0")},{\"txid\":\"$FUND1\",\"vout\":$(vout_of "$FUND1" "$R1")}]"
raw=$(cli createrawtransaction "$inputs" "[{\"$SHOP\":0.06},{\"$C0\":0.00998}]")
signed=$(cli -rpcwallet=dana signrawtransactionwithwallet "$raw" | jget '["hex"]')
SPEND=$(cli sendrawtransaction "$signed"); mine 1

# The treasury: wsh(sortedmulti(2, A, B, C)), each key at BIP 48 m/48'/0'/0'/2' (P2WSH), chains /0/* and /1/*.
KA=$(keys "$PHRASE_A" "m/48'/0'/0'/2'"); KB=$(keys "$PHRASE_B" "m/48'/0'/0'/2'"); KC=$(keys "$PHRASE_C" "m/48'/0'/0'/2'")
origin() { echo "[$(f "$1" fingerprint)/48h/0h/0h/2h]"; }
PA="$(origin "$KA")$(f "$KA" xpub)"; PB="$(origin "$KB")$(f "$KB" xpub)"; PC="$(origin "$KC")$(f "$KC" xpub)"
SA="$(origin "$KA")$(f "$KA" xprv)"; SC="$(origin "$KC")$(f "$KC" xprv)"
multi() { echo "wsh(sortedmulti(2,$1/$4/*,$2/$4/*,$3/$4/*))"; }
cli -named createwallet wallet_name=treasury_a blank=true >/dev/null
import_pair treasury_a "$(multi "$SA" "$PB" "$PC" 0)" "$(multi "$SA" "$PB" "$PC" 1)"
cli -named createwallet wallet_name=treasury_c blank=true >/dev/null
import_pair treasury_c "$(multi "$PA" "$PB" "$SC" 0)" "$(multi "$PA" "$PB" "$SC" 1)"
T0=$(derive "$(multi "$PA" "$PB" "$PC" 0)" 0); TC0=$(derive "$(multi "$PA" "$PB" "$PC" 1)" 0)
[ "$T0" = "$(cli -rpcwallet=treasury_a getnewaddress '' bech32)" ]
[ "$T0" = "$(cli -rpcwallet=treasury_c getnewaddress '' bech32)" ]

TFUND=$(pay "$T0" 0.3); mine 1

# Dana (key A) builds the payment; Dana and Fran (key C) sign separately; the two halves are combined.
psbt=$(cli -rpcwallet=treasury_a -named walletcreatefundedpsbt outputs="[{\"$VENDOR\":0.12}]" \
       options="{\"changeAddress\":\"$TC0\",\"fee_rate\":5}" | jget '["psbt"]')
half_a=$(cli -rpcwallet=treasury_a walletprocesspsbt "$psbt" | jget '["psbt"]')
half_c=$(cli -rpcwallet=treasury_c walletprocesspsbt "$psbt" | jget '["psbt"]')
both=$(cli combinepsbt "[\"$half_a\",\"$half_c\"]")
final=$(cli finalizepsbt "$both" | jget '["hex"]')
TSPEND=$(cli sendrawtransaction "$final"); mine 1
mine 2   # two more blocks, so the treasury's spend has three confirmations

HEIGHT=$(cli getblockcount)
: > /chain/out/blocks.hex
for ((h = 1; h <= HEIGHT; h++)); do cli getblock "$(cli getblockhash "$h")" 0 >> /chain/out/blocks.hex; done
for t in FUND0 FUND1 FUND2 FUND23 SPEND TFUND TSPEND; do
    cli getrawtransaction "${!t}" 2 > "/chain/out/tx-$(echo "$t" | tr 'A-Z' 'a-z').json"
done

DESC="$(multi "$PA" "$PB" "$PC" 0)"
export HEIGHT R0 R1 R2 R3 R23 C0 C1 SHOP VENDOR MINER T0 TC0 FUND0 FUND1 FUND2 FUND23 SPEND TFUND TSPEND
export XPUB84="$(f "$K84" xpub)" DESC="$DESC#$(checksum "$DESC")"
export FP_A="$(f "$KA" fingerprint)" FP_B="$(f "$KB" fingerprint)" FP_C="$(f "$KC" fingerprint)"
export XPUB_A="$(f "$KA" xpub)" XPUB_B="$(f "$KB" xpub)" XPUB_C="$(f "$KC" xpub)"
python3 - <<'PY'
import json, os
e = os.environ
facts = {
    "height": int(e["HEIGHT"]),
    "dana": {"path": "m/84'/0'/0'", "xpub": e["XPUB84"],
             "receiving": {i: e["R" + i] for i in ("0", "1", "2", "3", "23")},
             "change": {i: e["C" + i] for i in ("0", "1")}},
    "treasury": {"path": "m/48'/0'/0'/2'", "descriptor": e["DESC"],
                 "keys": {k: {"fingerprint": e["FP_" + k], "xpub": e["XPUB_" + k]} for k in "ABC"},
                 "receiving0": e["T0"], "change0": e["TC0"]},
    "others": {"shop": e["SHOP"], "vendor": e["VENDOR"], "faucet": e["MINER"]},
    "tx": {k.lower(): e[k] for k in ("FUND0", "FUND1", "FUND2", "FUND23", "SPEND", "TFUND", "TSPEND")},
}
with open("/chain/out/facts.json", "w") as out:
    json.dump(facts, out, indent=2)
PY
cli stop >/dev/null
echo "built height $HEIGHT"
