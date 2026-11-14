# The vault lab's recording

Instructor-only (`dynamic-labs/student-exclude.txt`): the notes below say what each contract does, which is the
lab's answer.

The lab page shows two real transactions: the drain of a vault that pays before it updates its records, and the
twist, a contract that takes back its own deposit 1 ETH at a time through a careful vault. Both were run on a fresh
Anvil from the contracts here; the page (`blockchain-course/assets/labs/the-vault-that-paid-twice/`) reads what the node returned, so no number on it is typed by hand.

To record again (needs Docker; the Otterscan pictures also need Chrome or Edge), from the repo root:

```bash
bash dynamic-labs/explorer/chain/vault-recording/record.sh
```

A rerun gives the same addresses, hashes and pictures: every account comes from Anvil's public test phrase
("test test … junk"), so the keys guard nothing, and every block's time is set.

| File | What it is |
| --- | --- |
| `src/VaultA.sol` | the drained vault: pays the whole balance, then zeroes it; logs only deposits |
| `src/VaultDrainer.sol` | the attacker's contract: deposits 1 ETH, withdraws, and withdraws again from `receive()` |
| `src/VaultB.sol` | the twist's vault: updates its records, then pays |
| `src/StepWithdrawer.sol` | the twist's caller: deposits 3 ETH, then takes 1 ETH back per call from `receive()` |
| `steps.sh` | runs in the Foundry container: builds the contracts and sends the eight blocks |
| `record.py` | reads both transactions back from the node (call trees, logs, ETH transfers, balances) |
| `record.sh` | starts Anvil and Otterscan, runs the two scripts, saves the pictures, removes the containers |
| `recording.js` (in the lab's folder) | what `record.py` wrote; the page loads it |
| `saved/*.png` (in the lab's folder) | Otterscan 2.11.0's overview, logs and trace pages of the drain, and the twist's trace |

Only the two vaults are verified in Otterscan, under neutral names (`VaultA`, `VaultB`); the callers stay bare
addresses, as an attacker's contract usually is, and both callers' entry function is `run()`, so no name in the
pictures gives the answer away.
