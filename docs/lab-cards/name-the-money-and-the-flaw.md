# Design card: Name the money and the flaw

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 6). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Name the money and the flaw (new: the plan's day 8 exploit part) |
| Replaces | nothing (the Ethereum Lab's unused DeFi-risk contracts become its material; the rest of that lab is archived at step 7) |
| Opens from | `lessons/forensics/10-FO-flash_loans_reentrancy_oracles.qmd`, "Three patterns in a trace look different" |
| Day | Day 8, afternoon lab (cross-chain trace), its first part |
| Kind | afternoon lab part (about 40 minutes), ending in the game "Find the line" |

## The ten lines

1. **The wrong belief**: "The vault was emptied, so someone must have stolen its key or broken its cryptography."
   Belief 15 on the plan's list ("a hack means the cryptography was broken"), marked common by the owner, in its
   contract form; "The wallet that emptied itself" (idea 5) keeps its key form.
2. **The prediction** (shell: `commit`): "The vault held 500 ETH. One transaction, from an address that had never
   used it, left it empty. How?" Choices: (a) the attacker stole the vault's private key; (b) the attacker forged
   a signature; (c) the attacker called the vault's own withdraw in a way its code allows; (d) the vault's owner
   moved the money. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student opens the one transaction on the course chain and steps through its
   calls in order, beside the vault's 41 lines. Two counters run on the vault: the ETH it holds and the balance it
   has recorded for the attacker. The attacker borrows 100 ETH, deposits it, asks to withdraw 100; the vault sends
   100, and before the vault records it, the attacker's contract asks again. The recorded balance still reads 100,
   so the check passes six times, until the vault holds nothing; the loan is repaid last. The student then picks
   the line to blame and moves it; the page replays the same transaction against the changed vault (results
   recorded at build time). Answer (a) fails in front of them: the vault has no key, and every step is a call its
   code accepted.
4. **The constraint**: sending ETH to a contract runs that contract's code, and anyone may call `withdraw`. A vault
   that pays first and records after hands control to the caller while its books are still wrong; recording first
   (checks, effects, then interactions) or a lock closes that window.
5. **The name** (shell: `name`): reentrancy. Parts: re- (again) + entry. Plain: a contract is called again before
   its first call has finished, and the second call sees the state the first had not yet updated.
6. **The explorer view** (shell: `explorer`): the transaction in Otterscan. The trace tab shows the call tree:
   `withdraw` nested inside the attacker's contract six times, each with its 100 ETH transfer, which shows only in
   the trace and its internal calls; the Logs tab has the vault's own six `Withdrawal` events, written on the way
   back out, innermost first. The vault's source opens from Sourcify beside the trace; the lender's 100 ETH goes out
   first and comes back, with its fee, last. The flash loan is the money; the line is the flaw.
7. **The twist** (shell: `twist`): the vault with the line moved, so it records the withdrawal before it pays. The
   same transaction is sent again. "What happens to the loan and the vault?" Choices: the attacker gets 100 ETH
   and stops; the loan stays unpaid; the whole transaction fails and nothing moves; the vault pays once and the
   lender loses its fee. Answer (the attacker's contract does not catch the failure, and the recorded replay is
   built that way): the second withdraw fails its check, so the whole transaction fails: the loan, the
   deposit and every payment are undone. The attempt is still on chain, with its sender, the attacker's contract and
   a failure status, and the sender paid the fee. A failed attempt is evidence too.
8. **The sentence** (shell: `tell`): "Tell the agent how the vault was emptied." Example: "Transaction 0x7c4e…19a2
   emptied the vault of 500 ETH by reentrancy: the vault pays before it records the withdrawal, and the attacker's
   contract called withdraw again from inside each payment. A 100 ETH flash loan, repaid in the same transaction,
   was the money; no key was taken (High confidence: the trace and the verified source agree)."
9. **The game, if any**: Find the line. Each team gets three more cases on the course chain, read from their
   transactions and traces first: an approval drain (`ApprovalDrainer`: the victim's earlier `approve`, then a
   "claim rewards" call whose `transferFrom` sends the tokens to the drainer's treasury); a fee rug
   (`TimelockRugVault`: the owner's `setWithdrawFeeBps(9000)`, then a depositor's withdrawal of 10 ETH that pays
   1 ETH out and 9 ETH to the treasury in the same call); and a flash loan from the course's lender, borrowed and
   repaid with no flaw at all. For each, the team names the money and the flaw with its reason ("none" is a right
   answer); the source opens only to confirm the line. A correct answer with its reason scores; time only breaks
   ties. The score is the concept: money and flaw named apart.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): an agent forwards a protocol's message: "Our vault held 500 ETH last night. This
morning it holds nothing, and we never signed anything. Were we hacked?" One transaction is attached.

Left out, for the owner to see: the vault has a second line that lets this attack run. Its subtraction sits in an
`unchecked` block, so the attacker's recorded balance wraps round instead of failing; with Solidity's default check
the same replay fails too. The page replays that change as well. Scoring (owner, 10 Nov 2026: "Either line, full
credit"): a student who moves either line gets full credit, because both fixes stop the replay and the page shows
it; the debrief then names reentrancy as the lesson's term. The oracle (price move) pattern stays with day 4's pool game and day 8 ②: the set has no oracle
contract. `EntropyLottery` is not a game case: no source found states how a calling contract beats it (see
Sources). The build spec keeps one exploit contract read at the start of day 8's lab (owner, 30 Oct), today
Bybit's, which is graded; this part, decided on 10 Nov, puts the vault's read before it, ungraded. Outcome 5 has
students recognize the other attack types from their transactions, so the game's cases are read from
transactions, with their source as confirmation only. Both points are settled (owner, 10 Nov 2026: "Keep both as
drafted"). Three contracts of the
set (`HoneypotToken`, `ThousandEthDoubler`, `FakeAirdropClaimer`) are scams, not exploits; they move with the set
but no step uses them.

Where the contracts live (a technical decision): at step 7 the seven DeFi-risk contracts move from
`dynamic-labs/ethereum_lab/contracts/defi-risk/` to `dynamic-labs/cross-chain/exploit/contracts/`, with two
in-house contracts the set lacks (the flash lender and the attacker's contract). A build script deploys them to a
frozen course chain, as the tokens lab does (anvil loads `chain/course-chain.json`; Otterscan 2.11.0 with Sourcify),
and saves each replay and each Otterscan page for the fallback the build spec asks of a live part. The answer key
goes in `dynamic-labs/cross-chain/quizes/`, which `student-exclude.txt` already keeps from students. The part is
not graded: day 8's graded contract read stays Bybit's.

## Load check

- [x] One new term per step: reentrancy is the only term named; "flash loan" was named in the morning lesson and
  is a label on the lender's two transfers.
- [x] Nothing drawn for decoration: the two counters are what the student predicts, and the call tree is the trace.
- [x] Labels sit on the thing they name: amounts on each transfer, the two counters on the vault.
- [x] Objects use the shared look: `.tx` and `.hash` for the transaction, `.addr` for the vault, attacker and
  lender, `.coin` for each 100 ETH payment, `.verdict` for the replay's result, `.conf` for the confidence word. A
  code line the student can pick is new to `look.css` and is added there when the lab is built.

## Sources

The vault's 500 ETH, the 100 ETH loan, the fee, the transaction hash and the protocol's message are made up for
the lab and say so; the contracts' behaviour is their own code.

- A contract account has no private key and is controlled by its code; it acts only in response to a transaction —
  `@ethereum.org_accountsdeveloperdocs_2025`
- An ETH transfer hands control to the receiving contract, which can call back into `withdraw`; the receive
  function runs on a call with empty calldata, as the vault's payment is —
  `@solidityteam_securityconsiderations_2026`;
  `@solidityteam_contracts_2026`
- Because the balance is not updated until the call completes, later calls succeed and withdraw again; the fix is
  checks-effects-interactions or a mutex — `@ethereum.org_smartcontractsecurity_2026`
- Since Solidity 0.8.0 a subtraction that underflows reverts, and inside `unchecked` it wraps; a revert undoes all
  changes in the call and its sub-calls — `@solidityteam_controlstructures_2026`
- A flash loan is borrowed without collateral and repaid with a fee in the same transaction, or the transaction
  reverts — `@aave_flashloans_2026` (as of 31 Oct 2026); flash loans fund attacks — `@qin_attackingdefiecosystem_2021`
- The receipt's status records whether a transaction failed (0) or succeeded (1) —
  `@johnson_eip658embeddingtransaction_2017`; the fee is paid whether a transaction succeeds or fails —
  `@ethereum.org_gasfeesdeveloper_2025`
- Otterscan's trace is a call tree, and internal ETH transfers show only in the internal calls —
  `@otterscan_otsnamespace_2026`; Otterscan 2.11.0 — `@otterscan_otterscan_2025` (as of 23 Oct 2026); verified
  source from Sourcify — `@sourcify_exactmatch_2026`
- `transferFrom` moves tokens the owner approved the caller to spend — `@vogelsteller_eip20tokenstandard_2015`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale). "The flash loan is the money, the
  line is the flaw" is the course's method from the slide "Three patterns in a trace look different", not a
  sourced fact.
- Searched, not used: the lottery's weak randomness. The Solidity docs warn against `block.timestamp` and
  `blockhash` as randomness but name only block producers; SWC-120 says the same and is "no longer actively
  maintained". Neither states that a calling contract can compute the draw, so the lottery stays out of the game.

## Approval

- Owner: "Bitcoin trace decoys", "Echo hunt", "Name the money and the flaw" (10 Nov 2026)
- Scoring of the unchecked line: "Either line, full credit"; the vault read before Bybit's and the game's cases read
  from transactions: "Keep both as drafted" (owner, 10 Nov 2026)
- Built in 4f6a89e8 (11 Nov 2026).
