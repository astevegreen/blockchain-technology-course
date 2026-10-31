#!/usr/bin/env bash
# Runs inside the Foundry container (chain/build-chain.sh starts it, with the lab at /lab):
# builds the day-3 course chain block by block, with each block's time set on purpose, and saves
# it to /lab/chain/out/. It lives in quizes/ because its comments are the worksheet's answers.
# Every account here is derived from Anvil's public test mnemonic: these keys guard nothing.
set -euo pipefail

R=http://127.0.0.1:8546
MN="test test test test test test test test test test test junk"
T0=1789567200            # genesis: 16 Sep 2026 14:00:00 UTC (day 3)
SEATS=40                 # accounts 10..49 are the class's seats on the mint page

work=/tmp/build
rm -rf "$work" && mkdir -p "$work/src" /lab/chain/out
cp /lab/chain/src/CourseTokens.sol "$work/src/"
printf '[profile.default]\nsrc = "src"\nout = "out"\nsolc = "0.8.24"\nbytecode_hash = "ipfs"\n' > "$work/foundry.toml"
(cd "$work" && forge build -q)

key()  { cast wallet private-key "$MN" "$1"; }
addr() { cast wallet address --private-key "$(key "$1")"; }
K0=$(key 0); K1=$(key 1); K2=$(key 2); K3=$(key 3); K4=$(key 4); K5=$(key 5)
A0=$(addr 0); A1=$(addr 1); A2=$(addr 2); A3=$(addr 3); A4=$(addr 4); A5=$(addr 5)

# Every account starts with 100 ETH in the genesis block (no transaction pays them).
anvil --port 8546 --accounts $((10 + SEATS)) --balance 100 --timestamp $T0 --no-mining \
      --state "$work/chain.json" --state-interval 1 --preserve-historical-states >"$work/anvil.log" 2>&1 &
pid=$!
for _ in $(seq 1 30); do cast block-number --rpc-url $R >/dev/null 2>&1 && break; sleep 0.5; done

send() { cast send --async --rpc-url $R "$@"; }            # queue in the mempool; prints the hash
mine() { cast rpc --rpc-url $R evm_mine "$1" >/dev/null; } # seal one block at the given time
created() { cast to-check-sum-address "$(cast receipt --rpc-url $R "$1" contractAddress)"; }
code() { (cd "$work" && forge inspect "src/CourseTokens.sol:$1" bytecode); }

# Block 1: account 0, the issuer, creates the dollar's code (the implementation).
h=$(send --private-key "$K0" --gas-limit 3000000 --create "$(code CourseDollar)"); mine $((T0 + 12))
DOLLAR_CODE=$(created "$h")
# Block 2: account 0 creates the proxy, which records the implementation (Upgraded log) and
# runs initialize(account 0) on its own storage: account 0 becomes the issuer.
args=$(cast abi-encode "constructor(address,bytes)" "$DOLLAR_CODE" "$(cast calldata "initialize(address)" "$A0")")
h=$(send --private-key "$K0" --gas-limit 1000000 --create "$(code DollarProxy)${args#0x}"); mine $((T0 + 24))
DOLLAR=$(created "$h")
# Block 3: the worked example. The issuer mints 10,000 cUSD to account 1: a Transfer from 0x0.
send --private-key "$K0" --gas-limit 200000 "$DOLLAR" "mint(address,uint256)" "$A1" 10000000000 >/dev/null
mine $((T0 + 36))
# Block 4: account 1 sends 2,500 cUSD to account 2.
send --private-key "$K1" --gas-limit 200000 "$DOLLAR" "transfer(address,uint256)" "$A2" 2500000000 >/dev/null
mine $((T0 + 48))
# Block 5: account 2 sends 1,000 cUSD to account 3.
send --private-key "$K2" --gas-limit 200000 "$DOLLAR" "transfer(address,uint256)" "$A3" 1000000000 >/dev/null
mine $((T0 + 60))
# Block 6: the issuer blacklists account 3 (AddedBlackList log).
send --private-key "$K0" --gas-limit 200000 "$DOLLAR" "addBlackList(address)" "$A3" >/dev/null
mine $((T0 + 72))
# Block 7: account 3 tries to send 500 cUSD to account 4; it fails ("sender is blacklisted").
send --private-key "$K3" --gas-limit 200000 "$DOLLAR" "transfer(address,uint256)" "$A4" 500000000 >/dev/null
mine $((T0 + 84))
# Block 8: account 1 sends 100 cUSD to account 3; it succeeds (only the sender is checked).
send --private-key "$K1" --gas-limit 200000 "$DOLLAR" "transfer(address,uint256)" "$A3" 100000000 >/dev/null
mine $((T0 + 96))
# Block 9: the issuer destroys account 3's 1,100 cUSD: a DestroyedBlackFunds log, no Transfer log.
send --private-key "$K0" --gas-limit 200000 "$DOLLAR" "destroyBlackFunds(address)" "$A3" >/dev/null
mine $((T0 + 108))
# Block 10: account 5 creates the badge contract (the NFT).
h=$(send --private-key "$K5" --gas-limit 3000000 --create "$(code CourseBadge)"); mine $((T0 + 120))
BADGE=$(created "$h")
# Block 11: account 4 mints badge 1 to itself, with its metadata in the transaction's input.
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><rect width="200" height="200" rx="24" fill="#1d3557"/><circle cx="100" cy="90" r="48" fill="#f1c40f"/><text x="100" y="104" font-family="sans-serif" font-size="40" font-weight="bold" text-anchor="middle" fill="#1d3557">D3</text><text x="100" y="172" font-family="sans-serif" font-size="18" text-anchor="middle" fill="#ffffff">Course Badge</text></svg>'
uri="data:application/json,{\"name\":\"Course Badge #1\",\"description\":\"Minted by account 4 on the day-3 course chain.\",\"image\":\"data:image/svg+xml;base64,$(printf '%s' "$svg" | base64 | tr -d '\n')\"}"
send --private-key "$K4" --gas-limit 1500000 "$BADGE" "mint(address,string)" "$A4" "$uri" >/dev/null
mine $((T0 + 132))
# Block 12: account 5 creates the badge shop.
shop_args=$(cast abi-encode "constructor(address)" "$BADGE")
h=$(send --private-key "$K5" --gas-limit 2000000 --create "$(code BadgeShop)${shop_args#0x}"); mine $((T0 + 144))
SHOP=$(created "$h")
# Block 13: account 4 lets the shop move badge 1 (Approval log).
send --private-key "$K4" --gas-limit 200000 "$BADGE" "approve(address,uint256)" "$SHOP" 1 >/dev/null
mine $((T0 + 156))
# Block 14: account 4 lists badge 1 for 0.5 ETH (Listed log).
send --private-key "$K4" --gas-limit 200000 "$SHOP" "list(uint256,uint256)" 1 0.5ether >/dev/null
mine $((T0 + 168))
# Block 15: account 2 buys badge 1 for 0.5 ETH. The shop moves the badge from account 4 to
# account 2 (Transfer log) and pays account 4 0.5 ETH (an internal transfer).
send --private-key "$K2" --gas-limit 300000 "$SHOP" "buy(uint256)" 1 --value 0.5ether >/dev/null
mine $((T0 + 180))
# Blocks 16 and 17: empty, so the last transactions have confirmations inside the saved history.
mine $((T0 + 192)); mine $((T0 + 204))

sleep 3                              # let the interval save catch the last block
kill -INT $pid; wait $pid || true
cp "$work/chain.json" /lab/chain/out/course-chain.json
cp -r "$work/out" /lab/chain/out/forge-out
cat >/lab/chain/out/addresses.env <<EOF
A0=$A0
A1=$A1
A2=$A2
A3=$A3
A4=$A4
A5=$A5
DOLLAR_CODE=$DOLLAR_CODE
DOLLAR=$DOLLAR
BADGE=$BADGE
SHOP=$SHOP
EOF
echo "chain built: dollar $DOLLAR (code $DOLLAR_CODE), badge $BADGE, shop $SHOP"
