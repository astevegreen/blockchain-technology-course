#!/usr/bin/env bash
# Rebuilds course-chain-sample.json: two contracts, an ETH transfer, a token
# transfer, an internal split and a failed transfer, on a fresh Anvil.
# Needs Foundry (anvil, forge, cast) on PATH. Run from this folder.
set -euo pipefail
R=http://127.0.0.1:8546
PK=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80   # Anvil's public test key 0
A1=0x70997970C51812dc3A010C7d01b50e0d17dc79C8
A2=0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
A3=0x90F79bf6EB2c4f870365E785982E1f101E93b906

work=$(mktemp -d)
mkdir -p "$work/src" && cp Spike.sol "$work/src/"
printf '[profile.default]\nsrc = "src"\nout = "out"\n' > "$work/foundry.toml"

anvil --port 8546 --state "$work/chain.json" --state-interval 2 --preserve-historical-states >/dev/null &
pid=$!
trap 'kill $pid 2>/dev/null || true' EXIT
sleep 2

(cd "$work" && forge build -q)
tok=$(cd "$work" && forge create src/Spike.sol:Token --rpc-url $R --private-key $PK --broadcast | awk '/Deployed to/ {print $3}')
fwd=$(cd "$work" && forge create src/Spike.sol:Forwarder --rpc-url $R --private-key $PK --broadcast | awk '/Deployed to/ {print $3}')
cast send -q --rpc-url $R --private-key $PK $A1 --value 1ether
cast send -q --rpc-url $R --private-key $PK "$tok" "transfer(address,uint256)" $A2 500e18
cast send -q --rpc-url $R --private-key $PK "$fwd" "split(address,address)" $A2 $A3 --value 2ether
cast send -q --rpc-url $R --private-key $PK "$tok" "transfer(address,uint256)" $A3 1e30 --gas-limit 100000 || true  # fails on purpose

sleep 3   # let the interval dump catch the last block
cp "$work/chain.json" course-chain-sample.json
echo "token $tok, forwarder $fwd, saved course-chain-sample.json"
