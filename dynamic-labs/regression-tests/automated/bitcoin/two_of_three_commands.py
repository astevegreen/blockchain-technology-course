"""The "Two of three" game page's commands as the shell receives them (blockchain-course/assets/labs/two-of-three/).

The live suite's container mounts only dynamic-labs/, so the live test runs these lines, and
regression-tests/unit/test_two_of_three_page.py (run by tools/check.py on a full checkout) checks that the page
still gives exactly these lines."""

# Round 1: one list of lines per command block on the page, in order.
ROUND_1 = [
    [
        'cat ~/two-of-three/partner-host',
        'bitcoin-cli -rpcwallet=two-of-three getbalance',
    ],
    [
        'TO=$(bitcoin-cli -rpcwallet=two-of-three getnewaddress)',
        'PSBT=$(bitcoin-cli -rpcwallet=two-of-three walletcreatefundedpsbt \'[]\' "[{\\"$TO\\":0.4}]" | jq -r .psbt)',
        'SIGNED=$(bitcoin-cli -rpcwallet=two-of-three walletprocesspsbt "$PSBT" | jq -r .psbt)',
    ],
    [
        'bitcoin-cli finalizepsbt "$SIGNED"',
    ],
    [
        'echo "$SIGNED" > ~/share/half-signed.psbt',
    ],
    [
        'HALF=$(curl -s http://$(cat ~/two-of-three/partner-host):8000/half-signed.psbt)',
        'bitcoin-cli finalizepsbt "$HALF"',
    ],
    [
        'FULL=$(bitcoin-cli -rpcwallet=two-of-three walletprocesspsbt "$HALF" | jq -r .psbt)',
        'bitcoin-cli finalizepsbt "$FULL"',
    ],
    [
        'TXID=$(bitcoin-cli sendrawtransaction "$(bitcoin-cli finalizepsbt "$FULL" | jq -r .hex)")',
        'echo $TXID',
        'bitcoin-cli generatetoaddress 1 "$(bitcoin-cli -rpcwallet=two-of-three getnewaddress)"',
    ],
]


# Round 2's spend attempt, line for line as the twist's "why" gives it (the test checks the page still has each).
WATCH_TRY = "\n".join([
    "bitcoin-cli -named createwallet wallet_name=watch disable_private_keys=true blank=true >/dev/null",
    'bitcoin-cli -rpcwallet=watch importdescriptors "[{\\"desc\\":\\"$DESC\\",\\"timestamp\\":0,\\"range\\":9}]" >/dev/null',
    "bitcoin-cli -rpcwallet=watch getbalance",
    "TO=$(bitcoin-cli -rpcwallet=game-account getnewaddress)",
    "BACK=$(bitcoin-cli -rpcwallet=game-account getnewaddress)",
    "TRY=$(bitcoin-cli -rpcwallet=watch walletcreatefundedpsbt '[]' \"[{\\\"$TO\\\":0.05}]\" 0 "
    "\"{\\\"changeAddress\\\":\\\"$BACK\\\"}\" | jq -r .psbt)",
    'bitcoin-cli -rpcwallet=watch walletprocesspsbt "$TRY" | jq .complete',
])
