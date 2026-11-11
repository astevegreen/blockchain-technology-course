# Design card: Find the line

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 6: day 8's game). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Find the line (day 8's game; the lab plan's "Every lab" row for the exploit part) |
| Replaces | nothing |
| Opens from | `lessons/forensics/10-FO-flash_loans_reentrancy_oracles.qmd`, "Three patterns in a trace look different"; it recalls "Where the three sit on OWASP's Top 10" |
| Day | Day 8, afternoon lab, the end of the exploit part: after the vault replay, before the Bybit contract read |
| Kind | game (teams of three or four, one page per team, about 20 minutes: the second half of the exploit part's 40) |

The exploit part ("Name the money and the flaw", approved) teaches reentrancy on one vault. This game keeps the
three cases that card fixed in its line 9 and adds what the vault could not show: money can leave a contract with no
bug at all. In each case the team reads the transactions first, names the money and the line that let it leave,
and locks the answer; only then does the source open, to confirm. It is practice: day 8's graded point stays the
cross-chain trace's note.

## The ten lines

1. **The wrong belief**: "Money left the contract, so its code had a bug. Find the bug." It is a cousin of belief
   15 on the plan's list ("a hack means the cryptography was broken", marked common); the exploit part keeps 15
   itself. Here no case's money left by a flaw in the code: one by the victim's own approval, one by the owner's
   power used as written, one not at all.
2. **The prediction** (shell: `commit`): asked once, before the first case opens: "Three more contracts lost money,
   or seemed to. In how many did the contract's code have a bug?" Choices: (a) three: money left, so the code
   failed; (b) two: the flash loan was repaid; (c) it depends on who called what, and who allowed them: read the
   transactions; (d) none can be told until the source is read. Then High, Moderate or Low. (Answer: (c); in fact
   none of the three.)
3. **The action** (shell: `do`): for each case the team opens its transactions in Otterscan and fills one line per
   case: the money (where it came from and where it went), the line (the transaction or the code line that let it
   leave, or "none") and who was allowed to do it, each with its reason; then it locks the line. The approval
   drain has two transactions, both sent by the victim: `approve` for the "staking" contract, then "claim
   rewards", whose internal `transferFrom` moves the tokens to the contract's treasury. The fee rug has the
   owner's `setWithdrawFeeBps(9000)`, then a depositor's 10 ETH withdrawal that pays 1 ETH out and 9 ETH to the
   treasury. The flash loan goes out and comes back with its fee, and nothing else moves. A team that picked (a)
   hunts for a bug and finds a victim's signature, an owner's call that the contract accepts from one address only,
   and a loan repaid.
4. **The constraint**: a contract does what its code allows, for whoever its code allows, and it has no key of its
   own. So money leaving shows only that someone was allowed to call something: the analyst asks who, and who
   allowed them. Three answers fit three kinds of finding: the code let anyone in (a flaw, as with the vault); the
   code let one key in (the owner's power, as with Tether's `onlyOwner` blacklist on day 3); or the holder gave
   permission (an approval, 09-FO). OWASP's list covers the first kind only, weaknesses "found in smart
   contracts"; the other two are found in who held the power, not in a line of code.
5. **The name** (shell: `name`): access control. Parts: access (the right to call a function) + control (the rule
   that grants it). Plain: who a contract lets do each thing. `onlyOwner` lets one address in; an approval lets a
   spender move a holder's tokens; a function with no check lets anyone in. The term recalls 04-EF, where the
   storage contract has none ("anyone can call `set`"); here it gets its three kinds. (The glossary's entry
   defines the permissioned-ledger sense from 04-DS and lists "Access control (smart contracts)" as an alias; the
   build gives that alias its own definition. OWASP's SC01 is "Access Control Vulnerabilities", which the 10-FO
   slide says is "not taught here".)
6. **The explorer view** (shell: `explorer`): the Otterscan transaction page, read in this order: the sender, the
   contract and the function called (decoded from the verified source), then the internal transfers in the
   trace, then the Logs tab. In the drain, the contract's own event is `RewardsClaimed`: it is the contract's word
   for what happened, and the token's `Transfer` from the victim to the treasury, beside it, is what moved. In the
   rug, the owner's call writes `WithdrawFeeSet(9000)`, and the withdrawal's `Withdrawal` event records the 9 ETH
   fee. The team page links the source from Sourcify only after the line is locked.
7. **The twist** (shell: `twist`): the fee-rug project's page says its vault is time-locked. "Does the timelock
   protect depositors from the fee change?" Choices: yes: fee changes wait out the delay; no: the delay holds the
   depositors' withdrawals, and the owner's settings take effect at once; yes: the code caps the fee; can't tell
   without the owner's key. Answer: the second. The delay is checked only in `withdraw`; `setWithdrawFeeBps`
   takes effect in the block it is called, and `setUnlockDelay` has no cap at all, so the same owner can also keep
   depositors in. The cap is 90%, the fee the owner set. Read the access control, not the contract's name or its
   page.
8. **The sentence** (shell: `tell`): "Tell the agent how the vault's depositor lost 9 ETH." Example: "In block
   212 the vault's owner raised its withdrawal fee to 90%, the most its code allows; in block 213 a depositor
   withdrew 10 ETH, received 1 ETH, and 9 ETH went to the owner's treasury. No code failed: the contract lets its
   owner set the fee at any time, and only the owner (High confidence: the two transactions and the verified
   source agree). It fits a rug pull: the owner's power used against the depositors."
9. **The game, if any**: find the line. Per case: the money with its reason, +1; the line with its reason, +2 (a
   right "none" for the flash loan scores the +2). A flaw named in the clean flash loan: -1. Each line is locked
   before its source opens; a team may unlock a line after the source is open, and the changed line scores +1 at
   most, since the trace alone did not give it. Time only breaks ties. The points come from naming the money and the line apart, and from
   reading the line in the record before the code, so the score is the concept.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): an agent forwards three complaints from one week: "A staking site took all my
tokens. I only clicked claim." "I withdrew 10 ETH from a vault and got 1 back." "Someone borrowed 2,000 ETH from
our pool in one transaction. Were we attacked?"

Left out, for the owner to see:

- No case has a line of code to blame, and that is the point: after the vault, a team expects a bug in each. The
  approved card's "none is a right answer" covers the loan; for the drain and the rug the line is a transaction
  (the victim's `approve`, the owner's `setWithdrawFeeBps`) and the reason names who was allowed. A team that
  names the drain contract's `_drain` function scores the line too, if its reason says the victim's approval is
  what let it run. Two changes to how the approved card's line 9 reads, within its "a correct answer with its
  reason scores": the scored line for the drain and the rug is a transaction and who was allowed, and naming a
  flaw in the clean loan costs 1 point.
- The lock is a rule of the game, not a wall: Otterscan's contract page shows the verified source too, so a team
  could read it early. The team page records when each line was locked and when its source link was opened.
- Two contracts' names give their answers away (`ApprovalDrainer`, `TimelockRugVault`), and Sourcify shows the
  name. The build deploys them under neutral names (say, a staking contract and `TimelockVault`), a technical
  decision; the rug keeps "Timelock" for the twist.
- The other owner settings (`setPaused`, `setTreasury`, `sweepFees`) are not a case: one owner case is enough, and
  the twist uses `setUnlockDelay`.
- The rug and the drain are not mapped to OWASP's list in the game: the 10-FO slide keeps the list to the three
  patterns, and the drain sits off the list by that slide's own rule.

How it is built: the three cases are deployed and sent by the exploit part's build script on the same frozen course
chain (anvil, Otterscan 2.11.0 with Sourcify), with the in-house flash lender that part already adds. The team page
sits beside the exploit part's, on the shared shell and look; it records each locked line and its time, and opens
each source link only after the line is locked. It holds no key: the scoring key and the accepted reasons go in
`dynamic-labs/cross-chain/quizes/`, which `student-exclude.txt` already keeps from students.

## Load check

- [x] One new term per step: access control is the only term named, recalled from 04-EF and given its three kinds;
  "approval" (09-FO), `onlyOwner` (05-EF), "rug pull" (07-EF) and "flash loan" (10-FO) come from earlier lessons.
- [x] Nothing drawn for decoration: the page is the three cases' lines and their lock.
- [x] Labels sit on the thing they name: amounts on each transfer, the sender on each transaction.
- [x] Objects use the shared look: `.tx` and `.hash` for each transaction, `.addr` for the victim, owner,
  treasury and contracts, `.coin` for each transfer, `.conf` for the confidence word; the locked line needs one new
  object in `look.css`, added when the game is built.

## Sources

The complaints, the 2,000 ETH loan, the block numbers and the project's page are made up for the game and say so;
the 10 ETH withdrawal and its 9 ETH fee are the approved card's; the contracts' behaviour is their own code
(`dynamic-labs/ethereum_lab/contracts/defi-risk/`).

- Access control is "who is allowed to do this thing"; ownership is its most common and basic form, and
  `onlyOwner` lets only the owner call a function — `@openzeppelin_accesscontrol_2026` (as of 10 Nov 2026)
- Tether's blacklist functions are `onlyOwner` — `@tether_tethertokensource_2017`
- A contract account has no private key and is controlled by its code — `@ethereum.org_accountsdeveloperdocs_2025`
- `approve` lets a spender withdraw from the holder's account; `transferFrom` moves tokens the holder approved —
  `@vogelsteller_eip20tokenstandard_2015`
- Rug pulls: scam tokens built to take investors' money — `@xia_tradeortrick_2021`
- A flash loan is borrowed and repaid with a fee in one transaction — `@aave_flashloans_2026` (as of 31 Oct 2026)
- OWASP's 2026 list: SC01 Access Control Vulnerabilities; it covers weaknesses "found in smart contracts" —
  `@owasp_smartcontracttop10_2026` (as of 10 Nov 2026)
- Otterscan 2.11.0 — `@otterscan_otterscan_2025` (as of 23 Oct 2026); its trace and internal transfers —
  `@otterscan_otsnamespace_2026`; verified source from Sourcify — `@sourcify_exactmatch_2026`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Approve as drafted (Recommended)" (11 Nov 2026)
