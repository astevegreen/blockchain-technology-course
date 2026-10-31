#!/usr/bin/env bash
# Runs inside the Foundry container (build-chain.sh starts it): builds the day-1 course chain
# block by block, with each block's time set on purpose, and saves it to /chain/out/.
# Every account here is derived from Anvil's public test mnemonic: these keys guard nothing.
set -euo pipefail

R=http://127.0.0.1:8546
MN="test test test test test test test test test test test junk"
T0=1789394400            # genesis: 14 Sep 2026 14:00:00 UTC
SEATS=40                 # accounts 10..49 are the class's seats on the signing page

work=/tmp/build
rm -rf "$work" && mkdir -p "$work/src" /chain/out
cp /chain/src/CourseChain.sol "$work/src/"
printf '[profile.default]\nsrc = "src"\nout = "out"\nsolc = "0.8.24"\nbytecode_hash = "ipfs"\n' > "$work/foundry.toml"
(cd "$work" && forge build -q)

key()  { cast wallet private-key "$MN" "$1"; }
addr() { cast wallet address --private-key "$(key "$1")"; }
K0=$(key 0); K1=$(key 1); K2=$(key 2); K3=$(key 3); K4=$(key 4)
A0=$(addr 0); A1=$(addr 1); A2=$(addr 2); A3=$(addr 3); A4=$(addr 4); A5=$(addr 5)

# Every account starts with 100 ETH in the genesis block (no transaction pays them).
anvil --port 8546 --accounts $((10 + SEATS)) --balance 100 --timestamp $T0 --no-mining \
      --state "$work/chain.json" --state-interval 1 --preserve-historical-states >"$work/anvil.log" 2>&1 &
pid=$!
for _ in $(seq 1 30); do cast block-number --rpc-url $R >/dev/null 2>&1 && break; sleep 0.5; done

send() { cast send --async --rpc-url $R "$@"; }            # queue in the mempool; prints the hash
mine() { cast rpc --rpc-url $R evm_mine "$1" >/dev/null; } # seal one block at the given time
token_code=$(cd "$work" && forge inspect src/CourseChain.sol:CourseToken bytecode)
split_code=$(cd "$work" && forge inspect src/CourseChain.sol:Splitter bytecode)

# Block 1: account 0 creates the token contract.
h1=$(send --private-key "$K0" --gas-limit 1500000 --create "$token_code"); mine $((T0 + 12))
TOKEN=$(cast to-check-sum-address "$(cast receipt --rpc-url $R "$h1" contractAddress)")
# Block 2: account 0 creates the splitter contract.
h2=$(send --private-key "$K0" --gas-limit 500000 --create "$split_code"); mine $((T0 + 24))
SPLITTER=$(cast to-check-sum-address "$(cast receipt --rpc-url $R "$h2" contractAddress)")
# Block 3: the worked example, an ordinary ETH transfer from account 1 to account 2.
send --private-key "$K1" --gas-limit 21000 "$A2" --value 1.5ether >/dev/null; mine $((T0 + 36))
# Block 4: account 0 sends 5,000 CRT to account 3 (a call to the token, with a Transfer log).
send --private-key "$K0" --gas-limit 100000 "$TOKEN" "transfer(address,uint256)" "$A3" 5000e18 >/dev/null
mine $((T0 + 48))
# Block 5: account 1 sends 2 ETH to the splitter, which pays accounts 2 and 4 1 ETH each.
send --private-key "$K1" --gas-limit 100000 "$SPLITTER" "split(address,address)" "$A2" "$A4" --value 2ether >/dev/null
mine $((T0 + 60))
# Block 6: account 4 tries to send 10 CRT it does not have; the transaction fails but is mined.
send --private-key "$K4" --gas-limit 100000 "$TOKEN" "transfer(address,uint256)" "$A1" 10e18 >/dev/null
mine $((T0 + 72))
# Block 7: two transactions in one block, from two senders.
send --private-key "$K2" --gas-limit 21000 "$A3" --value 0.4ether >/dev/null
send --private-key "$K3" --gas-limit 100000 "$TOKEN" "transfer(address,uint256)" "$A1" 250e18 >/dev/null
mine $((T0 + 84))
# Block 8: account 3 sends 0.1 ETH to account 4.
send --private-key "$K3" --gas-limit 21000 "$A4" --value 0.1ether >/dev/null; mine $((T0 + 96))
# Blocks 9 and 10: empty, so block 3's transaction has confirmations inside the saved history.
mine $((T0 + 108)); mine $((T0 + 120))

sleep 3                              # let the interval save catch the last block
kill -INT $pid; wait $pid || true
cp "$work/chain.json" /chain/out/course-chain.json
cp -r "$work/out" /chain/out/forge-out
cat >/chain/out/addresses.env <<EOF
A0=$A0
A1=$A1
A2=$A2
A3=$A3
A4=$A4
A5=$A5
TOKEN=$TOKEN
SPLITTER=$SPLITTER
EOF
echo "chain built: token $TOKEN, splitter $SPLITTER"
