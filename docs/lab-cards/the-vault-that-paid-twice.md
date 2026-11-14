# Design card: The vault that paid twice

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | The vault that paid twice (review idea 33) |
| Replaces | `ether-smart-contract-micro` (cut down to its reentrancy stepper, turned around) |
| Opens from | `lessons/forensics/10-FO-flash_loans_reentrancy_oracles.qmd`, "Reading a reentrancy: one call nested in itself" |
| Day | Day 8, lesson ② (flash loans, reentrancy and oracles) |
| Kind | prediction lab (five minutes) |

## The ten lines

1. **The wrong belief**: "If a contract paid out, the transaction's logs list every payment." Not on the plan's
   numbered list; review idea 33 names it: "the money moved and no log says so". The old lab taught it by logging
   an `ETHTransfer` event that real ETH transfers do not write.
2. **The prediction** (shell: `commit`): "The vault held 4 ETH of its depositors' money. One
   transaction later it holds nothing. Its Logs tab shows a single entry: a deposit of 1 ETH. Where did the 4 ETH
   go?" Choices: (a) nowhere that can be traced: no log, no record; (b) the logs were deleted after the theft;
   (c) out in payments that the logs do not record, so open the calls; (d) out in another transaction, signed
   with a stolen key. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student starts at the drained vault and works backward. The vault's page shows
   0 ETH and one transaction; its one log is the 1 ETH deposit. The student opens the transaction's calls from the
   outside in: the attacker's contract deposits 1 ETH and calls `withdraw`; inside it the vault sends 1 ETH back;
   inside that payment the attacker's contract calls `withdraw` again, five levels deep. A counter adds each
   payment as it opens: 5 ETH paid out against 1 ETH paid in, a loss of 4. Answers (a) and (b) fail in front of
   them: every payment is there, in the calls, and none has a log. The call's raw fields come last.
4. **The constraint**: a log exists only when the contract's code writes one; a plain ETH payment is the value
   carried by a call, and the vault's code writes nothing when it pays. So the trace, not the Logs tab, is where an
   analyst finds ETH leaving a contract. The vault paid before it updated its records, so each nested call still
   saw 1 ETH to its caller's name.
5. **The name** (shell: `name`): reentrancy. Parts: re- (again) + entry. Plain: a contract is called again before
   its first call has finished, and the second call sees the records the first had not yet updated.
6. **The explorer view** (shell: `explorer`): the same transaction in Otterscan, saved from the chain it was
   recorded on. The Logs tab holds the one deposit; the trace tab shows the call tree, `withdraw` nested inside
   itself, each level with its 1 ETH value; the overview lists the ETH transfers, five of them from the vault.
   These are the four rows of the slide: one transaction, a contract caller, nested withdraw and pay, a loss beyond
   the deposit.
7. **The twist** (shell: `twist`): a second transaction on another vault shows the same nesting, three levels deep,
   from a contract that deposited 3 ETH; the vault paid back 3 ETH and still holds everyone else's funds. "Is this
   a reentrancy theft?" Choices: yes, the nesting proves it; no, it is a callback, and no loss shows; it cannot be
   read without the source code; yes, but smaller. Answer: the second, Low confidence as an attack. Nesting alone is
   not theft: some contracts call back legitimately; the loss beyond the deposit is what makes it one (the slide's
   Ask).
8. **The sentence** (shell: `tell`): "Tell the agent where the vault's 4 ETH went." Example: "Transaction
   0xb17b…ab5a emptied the vault by reentrancy: the attacker's contract deposited 1 ETH and called withdraw five
   times, each call nested inside the vault's last payment, and took out 5 ETH, its own 1 and the depositors' 4
   (Moderate confidence from the trace alone; the payments appear in the call trace, not the logs)."
9. **The game, if any**: none. The plan calls it "a diagnosis, not a contest".
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): an agent forwards a screenshot from a protocol's support channel: "Our vault
shows zero. The explorer shows one small deposit and nothing leaving. Where did the money go?" The transaction is
attached.

How it differs from "Name the money and the flaw" (day 8's afternoon exploit part): this lab is the five-minute
belief-breaker in lesson ②, read backward from the empty vault through one recorded trace, with no source code,
no flash loan and nothing to change; its point is where payments show (the calls, not the logs) and what makes a
nesting a theft (the loss). The afternoon part steps forward through the transaction beside the vault's code,
names the flash loan as the money, moves the flawed line and replays it, then plays "Find the line" on three more
cases. Its vault writes a `Withdrawal` event when it pays, so in the afternoon the logs do list the payments: the
morning lab's constraint is what lets students say why one vault's logs show them and the other's do not.

Left out, for the owner to see: the old lab's invented gas numbers, its "miner" wording and its forward narration
are dropped (static-labs review). The fix (pay last, or a lock) is on the slide "Reentrancy: the contract pays
before it updates" and is the afternoon part's twist, not this one's.

How it is built: the lab is a static page in `src.zip`, a stepper over two recorded transactions. The vaults and
their callers are small in-house contracts run on a fresh Anvil (Foundry 1.8.6) by an instructor-only kit,
`dynamic-labs/explorer/chain/vault-recording/` (listed in `student-exclude.txt`, since its notes say what each
contract does). Its `record.sh` writes the page's `recording.js` from the node's own answers (the call trees, logs,
ETH transfers and balances) and saves Otterscan 2.11.0's pages of both transactions in the page's `saved/`; a rerun
gives the same hashes. Every number on screen comes from the EVM, not from the page. Only the vaults' source is
verified, under neutral names (`VaultA`, `VaultB`), so Otterscan names each vault and shows the callers as bare
addresses, as an attacker's contract usually is; both callers' entry function is `run()`, so no name gives the
answer away. (Recorded 14 Nov 2026; the first build's trace was
written by hand.)

## Load check

- [x] One new term per step: reentrancy is the only term named, from the morning's slides; "log", "internal
  transaction" and "trace" come from day 3's Otterscan lab.
- [x] Nothing drawn for decoration: a call opens only when the student opens it, and the counter moves only on a
  payment.
- [x] Labels sit on the thing they name: the 1 ETH value on each call, the running total on the vault.
- [x] Objects use the shared look: `.tx` and `.hash` for the transaction, `.addr` for the vault and the attacker's
  contract, `.coin` for each 1 ETH payment, `.conf` for the confidence word.

## Sources

The vaults, their depositors and the protocol's message are made up for the lab and say so; both transactions were
recorded on a test chain from the lab's own contracts, so the balances, the hash and the trace are what the EVM
returned (the vault writes no event when it pays).

- Internal ETH transfers are "only unveiled by examining the internal calls"; Otterscan's trace is "a call tree" —
  `@otterscan_otsnamespace_2026`; Otterscan 2.11.0 — `@otterscan_otterscan_2025` (as of 23 Oct 2026)
- Any transfer of ether hands control to the receiving contract, which can call back into `withdraw`; the receive
  function runs on a plain ether transfer — `@solidityteam_securityconsiderations_2026`;
  `@solidityteam_contracts_2026`
- The balance is not updated until the call completes, so later calls withdraw again —
  `@ethereum.org_smartcontractsecurity_2026`
- The DAO's split was called inside split, many times in one transaction — `@l34_ethereum_dao_vulnerability_2016`
- The four trace rows, Moderate from the trace alone, and Low without a loss because some contracts call back
  legitimately — the slide "Reading a reentrancy: one call nested in itself" (`@l34_ethereum_dao_vulnerability_2016`;
  `@ethereum.org_smartcontractsecurity_2026`)
- The old lab's `ETHTransfer` event is not what the EVM writes — static-labs review
  (`docs/analysis/2026-11-static-labs-review.md`, `ether-smart-contract-micro`); `@otterscan_otsnamespace_2026`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale)

## Approval

- Owner: "Find the sandwich,What is it really worth,Beat the freeze,The vault that paid twice" (11 Nov 2026)
- Built in 1f3e59b7 (11 Nov 2026).
