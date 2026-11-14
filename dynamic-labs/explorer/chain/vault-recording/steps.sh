#!/usr/bin/env bash
# Runs inside the Foundry container (record.sh starts it, with this folder at /rec and the node's URL
# as $1): builds the contracts in src/ and sends the eight blocks the lab reads, each sealed at a set
# time, then writes the addresses and hashes to /rec/out/recording.env.
# Every account is derived from Anvil's public test mnemonic: these keys guard nothing.
set -euo pipefail

R=$1
MN="test test test test test test test test test test test junk"
T0=1789999200            # genesis: 21 Sep 2026 14:00:00 UTC

work=/tmp/build
rm -rf "$work" && mkdir -p "$work/src" /rec/out
cp /rec/src/*.sol "$work/src/"
printf '[profile.default]\nsrc = "src"\nout = "out"\nsolc = "0.8.30"\nbytecode_hash = "ipfs"\n' > "$work/foundry.toml"
(cd "$work" && forge build -q)
cp -r "$work/out" /rec/out/forge-out

key()  { cast wallet private-key "$MN" "$1"; }
addr() { cast wallet address --private-key "$(key "$1")"; }
send() { cast send --async --rpc-url "$R" --gas-limit 1000000 "$@"; }   # queue; prints the hash
mine() { cast rpc --rpc-url "$R" evm_mine "$1" >/dev/null; }            # seal one block at a set time
created() { cast to-check-sum-address "$(cast receipt --rpc-url "$R" "$1" contractAddress)"; }
code() { (cd "$work" && forge inspect "src/$1.sol:$1" bytecode); }

for _ in $(seq 1 30); do cast block-number --rpc-url "$R" >/dev/null 2>&1 && break; sleep 0.5; done

# Block 1: account 0, the protocol, creates the quiet vault.
h=$(send --private-key "$(key 0)" --create "$(code VaultA)"); mine $((T0 + 12))
QUIET=$(created "$h")
# Block 2: four depositors, accounts 1 to 4, put 1 ETH each in it.
for n in 1 2 3 4; do send --private-key "$(key $n)" --value 1ether "$QUIET" "deposit()" >/dev/null; done
mine $((T0 + 24))
# Block 3: account 5 creates its contract, pointed at the quiet vault.
h=$(send --private-key "$(key 5)" --create "$(code VaultDrainer)$(cast abi-encode "f(address)" "$QUIET" | cut -c3-)")
mine $((T0 + 36))
DRAINER=$(created "$h")
# Block 4: the drain. Account 5 calls run() with 1 ETH.
DRAIN_TX=$(send --private-key "$(key 5)" --value 1ether "$DRAINER" "run()"); mine $((T0 + 48))
# Block 5: account 0 creates the careful vault (the twist).
h=$(send --private-key "$(key 0)" --create "$(code VaultB)"); mine $((T0 + 60))
CAREFUL=$(created "$h")
# Block 6: the same four depositors put 1 ETH each in it.
for n in 1 2 3 4; do send --private-key "$(key $n)" --value 1ether "$CAREFUL" "deposit()" >/dev/null; done
mine $((T0 + 72))
# Block 7: account 6 creates its contract, pointed at the careful vault.
h=$(send --private-key "$(key 6)" --create "$(code StepWithdrawer)$(cast abi-encode "f(address)" "$CAREFUL" | cut -c3-)")
mine $((T0 + 84))
STEPPER=$(created "$h")
# Block 8: account 6 calls run() with 3 ETH: deposit 3, then 1 ETH back at a time.
TWIST_TX=$(send --private-key "$(key 6)" --value 3ether "$STEPPER" "run()"); mine $((T0 + 96))

for h in "$DRAIN_TX" "$TWIST_TX"; do
    case "$(cast receipt --rpc-url "$R" "$h" status)" in true|1*) ;; *) false ;; esac || { echo "transaction $h failed" >&2; exit 1; }
done

cat > /rec/out/recording.env <<EOF
QUIET=$QUIET
DRAINER=$DRAINER
CAREFUL=$CAREFUL
STEPPER=$STEPPER
ATTACKER_WALLET=$(addr 5)
STEPPER_WALLET=$(addr 6)
DRAIN_TX=$DRAIN_TX
TWIST_TX=$TWIST_TX
SEL_DEPOSIT=$(cast sig "deposit()")
SEL_WITHDRAW=$(cast sig "withdraw()")
SEL_WITHDRAW_AMOUNT=$(cast sig "withdraw(uint256)")
SEL_RUN=$(cast sig "run()")
SEL_BALANCE_OF=$(cast sig "balanceOf(address)")
TOPIC_DEPOSIT=$(cast keccak "Deposit(address,uint256)")
EOF
echo "recorded: drain $DRAIN_TX, twist $TWIST_TX"
