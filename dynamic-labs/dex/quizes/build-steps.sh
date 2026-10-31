#!/usr/bin/env bash
# Runs inside the Foundry container (chain/build-chain.sh starts it, with the lab at /lab):
# builds the day-4 course chains block by block, with each block's time set on purpose, and saves
# them to /lab/chain/out/. L1 is the exchange's chain; L2 is the chain the bridge mints on.
# It lives in quizes/ because its comments are the worksheet's answers.
# Every account here is derived from Anvil's public test mnemonic: these keys guard nothing.
set -euo pipefail

R=http://127.0.0.1:8546   # L1, chain id 31337, a block every 12 s
R2=http://127.0.0.1:8547  # L2, chain id 31338, a block every 2 s
MN="test test test test test test test test test test test junk"
T0=1789653600            # genesis: 17 Sep 2026 14:00:00 UTC (day 4), on both chains
SEATS=40                 # accounts 10..49 are the class's seats on the swap page

work=/tmp/build
rm -rf "$work" && mkdir -p "$work/src" /lab/chain/out
cp /lab/chain/src/CourseDex.sol /lab/chain/src/CourseBridge.sol "$work/src/"
printf '[profile.default]\nsrc = "src"\nout = "out"\nsolc = "0.8.24"\nbytecode_hash = "ipfs"\n' > "$work/foundry.toml"
(cd "$work" && forge build -q)

key()  { cast wallet private-key "$MN" "$1"; }
addr() { cast wallet address --private-key "$(key "$1")"; }
for i in 0 1 2 3 4 5 6 7 8; do
    eval "K$i=$(key $i); A$i=$(addr $i)"
done

start_anvil() { # port, chain id, state file
    anvil --port "$1" --chain-id "$2" --accounts $((10 + SEATS)) --balance 100 --timestamp $T0 --no-mining \
          --state "$3" --state-interval 1 --preserve-historical-states >"$3.log" 2>&1 &
}
start_anvil 8546 31337 "$work/l1.json"; pid1=$!
start_anvil 8547 31338 "$work/l2.json"; pid2=$!
for rpc in $R $R2; do
    for _ in $(seq 1 30); do cast block-number --rpc-url $rpc >/dev/null 2>&1 && break; sleep 0.5; done
done

send()  { cast send --async --rpc-url $R "$@"; }              # L1: queue in the mempool; prints the hash
# (two transactions from one sender in one block name their nonces: cast would reuse the first)
send2() { cast send --async --rpc-url $R2 "$@"; }             # L2
mine()  { cast rpc --rpc-url $R evm_mine "$1" >/dev/null; }   # seal one L1 block at the given time
mine2() { cast rpc --rpc-url $R2 evm_mine "$1" >/dev/null; }
created()  { cast to-check-sum-address "$(cast receipt --rpc-url $R "$1" contractAddress)"; }
created2() { cast to-check-sum-address "$(cast receipt --rpc-url $R2 "$1" contractAddress)"; }
code() { (cd "$work" && forge inspect "$1" bytecode); }
l1() { mine $((T0 + 12 * $1)); }                  # L1 block n is sealed at T0 + 12n
l2_to() { # seal empty L2 blocks, one every 2 s, up to and including block $1
    local n; n=$(cast block-number --rpc-url $R2)
    while [ "$n" -lt "$1" ]; do n=$((n + 1)); mine2 $((T0 + 2 * n)); done
}
FAR=$((T0 + 86400))                               # a swap deadline a day after genesis

# --- L1: the exchange ---
# Block 1: account 0 creates the dollar token (cUSD).
h=$(send --private-key "$K0" --gas-limit 2000000 --create "$(code src/CourseDex.sol:CourseDollar)"); l1 1
DOLLAR=$(created "$h")
# Block 2: account 0 creates wrapped ether (WETH).
h=$(send --private-key "$K0" --gas-limit 2000000 --create "$(code src/CourseDex.sol:WETH)"); l1 2
WETH=$(created "$h")
# Block 3: account 0 creates the pool (pair) for cUSD and WETH.
args=$(cast abi-encode "constructor(address,address)" "$DOLLAR" "$WETH")
h=$(send --private-key "$K0" --gas-limit 3000000 --create "$(code src/CourseDex.sol:CoursePair)${args#0x}"); l1 3
PAIR=$(created "$h")
# Block 4: account 0 creates the router, the contract traders call.
args=$(cast abi-encode "constructor(address,address)" "$PAIR" "$WETH")
h=$(send --private-key "$K0" --gas-limit 3000000 --create "$(code src/CourseDex.sol:CourseRouter)${args#0x}"); l1 4
ROUTER=$(created "$h")
# Block 5: the issuer mints cUSD to accounts 2 (100,000), 3 (5,000), 1 (1,200) and 5 (3,000);
# account 2 wraps 50 ETH and account 4 wraps 5 ETH (Deposit logs, no Transfer).
send --private-key "$K0" --nonce 4 --gas-limit 200000 "$DOLLAR" "mint(address,uint256)" "$A2" 100000000000 >/dev/null
send --private-key "$K0" --nonce 5 --gas-limit 200000 "$DOLLAR" "mint(address,uint256)" "$A3" 5000000000 >/dev/null
send --private-key "$K0" --nonce 6 --gas-limit 200000 "$DOLLAR" "mint(address,uint256)" "$A1" 1200000000 >/dev/null
send --private-key "$K0" --nonce 7 --gas-limit 200000 "$DOLLAR" "mint(address,uint256)" "$A5" 3000000000 >/dev/null
send --private-key "$K2" --gas-limit 100000 "$WETH" "deposit()" --value 50ether >/dev/null
send --private-key "$K4" --gas-limit 100000 "$WETH" "deposit()" --value 5ether >/dev/null
l1 5
# Block 6: account 2 lets the router move its cUSD and WETH.
send --private-key "$K2" --nonce 1 --gas-limit 100000 "$DOLLAR" "approve(address,uint256)" "$ROUTER" 100000000000 >/dev/null
send --private-key "$K2" --nonce 2 --gas-limit 100000 "$WETH" "approve(address,uint256)" "$ROUTER" 50ether >/dev/null
l1 6
# Block 7: account 2 fills the pool with 100,000 cUSD and 50 WETH: 2,000 cUSD per WETH.
send --private-key "$K2" --gas-limit 400000 "$ROUTER" \
    "addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)" \
    "$DOLLAR" "$WETH" 100000000000 50ether 0 0 "$A2" $FAR >/dev/null
l1 7
# Block 8: account 3 lets the router move its cUSD.
send --private-key "$K3" --gas-limit 100000 "$DOLLAR" "approve(address,uint256)" "$ROUTER" 5000000000 >/dev/null
l1 8
# Block 9: the worked example. Account 3 sells 5,000 cUSD for WETH.
send --private-key "$K3" --gas-limit 300000 "$ROUTER" \
    "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)" \
    5000000000 0 "[$DOLLAR,$WETH]" "$A3" $FAR >/dev/null
l1 9
# Block 10: account 4 lets the router move its WETH.
send --private-key "$K4" --gas-limit 100000 "$WETH" "approve(address,uint256)" "$ROUTER" 2ether >/dev/null
l1 10
# Block 11: the problem. Account 4 sells 2 WETH for cUSD.
send --private-key "$K4" --gas-limit 300000 "$ROUTER" \
    "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)" \
    2ether 0 "[$WETH,$DOLLAR]" "$A4" $FAR >/dev/null
l1 11

# --- L2: the bridge's second half, created early so it is ready for the deposits ---
# L2 block 15 (T0 + 30 s): account 6 creates the L2 bridge, naming account 7 as its relayer; the
# bridge creates the bridged token (bcUSD) in the same transaction. Account 6's first contract on
# each chain, so the L1 bridge below gets the same address on L1.
l2_to 14
args=$(cast abi-encode "constructor(address)" "$A7")
h=$(send2 --private-key "$K6" --gas-limit 3000000 --create "$(code src/CourseBridge.sol:CourseBridgeL2)${args#0x}")
mine2 $((T0 + 30))
BRIDGE_L2=$(created2 "$h")
BCUSD=$(cast to-check-sum-address "$(cast call --rpc-url $R2 "$BRIDGE_L2" "token()(address)")")

# --- L1: the bridge ---
# Block 12: account 6 creates the L1 bridge for cUSD.
args=$(cast abi-encode "constructor(address)" "$DOLLAR")
h=$(send --private-key "$K6" --gas-limit 2000000 --create "$(code src/CourseBridge.sol:CourseBridgeL1)${args#0x}"); l1 12
BRIDGE_L1=$(created "$h")
# Block 13: account 1 approves the bridge and deposits 1,200 cUSD to itself on L2 (deposit 0).
send --private-key "$K1" --nonce 0 --gas-limit 100000 "$DOLLAR" "approve(address,uint256)" "$BRIDGE_L1" 1200000000 >/dev/null
send --private-key "$K1" --nonce 1 --gas-limit 200000 "$BRIDGE_L1" "depositERC20To(address,address,uint256)" \
    "$DOLLAR" "$A1" 1200000000 >/dev/null
l1 13
# Block 14: account 5 approves the bridge and deposits 3,000 cUSD to account 8 on L2 (deposit 1).
send --private-key "$K5" --nonce 0 --gas-limit 100000 "$DOLLAR" "approve(address,uint256)" "$BRIDGE_L1" 3000000000 >/dev/null
send --private-key "$K5" --nonce 1 --gas-limit 200000 "$BRIDGE_L1" "depositERC20To(address,address,uint256)" \
    "$DOLLAR" "$A8" 3000000000 >/dev/null
l1 14
# Blocks 15 to 18: empty, so the deposits have confirmations and L1's history outlasts L2's.
l1 15; l1 16; l1 17; l1 18

# --- L2: the relayer copies each deposit, a few L1 blocks after it ---
# L2 block 95 (T0 + 190 s, 34 s after L1 block 13): the relayer finalizes deposit 0.
l2_to 94
send2 --private-key "$K7" --gas-limit 200000 "$BRIDGE_L2" "finalizeDeposit(uint256,address,address,uint256)" \
    0 "$A1" "$A1" 1200000000 >/dev/null
mine2 $((T0 + 190))
# L2 block 101 (T0 + 202 s, 34 s after L1 block 14): the relayer finalizes deposit 1.
l2_to 100
send2 --private-key "$K7" --gas-limit 200000 "$BRIDGE_L2" "finalizeDeposit(uint256,address,address,uint256)" \
    1 "$A5" "$A8" 3000000000 >/dev/null
mine2 $((T0 + 202))
# L2 blocks 102 to 105: empty.
l2_to 105

sleep 3                              # let the interval saves catch the last blocks
kill -INT $pid1 $pid2; wait $pid1 || true; wait $pid2 || true
cp "$work/l1.json" /lab/chain/out/course-chain.json
cp "$work/l2.json" /lab/chain/out/course-chain-l2.json
cp -r "$work/out" /lab/chain/out/forge-out
cat >/lab/chain/out/addresses.env <<EOF
A0=$A0
A1=$A1
A2=$A2
A3=$A3
A4=$A4
A5=$A5
A6=$A6
A7=$A7
A8=$A8
DOLLAR=$DOLLAR
WETH=$WETH
PAIR=$PAIR
ROUTER=$ROUTER
BRIDGE_L1=$BRIDGE_L1
BRIDGE_L2=$BRIDGE_L2
BCUSD=$BCUSD
EOF
echo "chains built: pair $PAIR, router $ROUTER, bridges $BRIDGE_L1 / $BRIDGE_L2, bcUSD $BCUSD"
