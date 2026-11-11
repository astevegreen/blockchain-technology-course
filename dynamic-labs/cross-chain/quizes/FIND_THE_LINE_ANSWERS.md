# Find the line: instructor answers

Instructor only (this folder is in `dynamic-labs/student-exclude.txt`). Design card:
`docs/lab-cards/find-the-line.md` (approved 11 Nov 2026). Team page:
`blockchain-course/assets/labs/find-the-line/index.html`, played in teams of three or four, about 20 minutes, after
the vault replay ("Name the money and the flaw"). The chain is the exploit part's frozen chain; blocks 19-32 are
built by `exploit-build-steps.sh`, part 3. Addresses: `exploit/chain/addresses.env`.

## The prediction

"In how many did the contract's code have a bug?" Answer: (c), "it depends on who called what, and who allowed
them: read the transactions". In fact none of the three: one by the victim's own approval, one by the owner's power
used as written, one not at all.

## Scoring

Per case:

| Part | Points |
| --- | --- |
| The money, with its reason | +1 |
| The line, with its reason (a right "none" for the loan scores this) | +2 |
| A flaw named in the clean loan (case C) | -1 |
| A line changed after its source was opened | the line scores +1 at most |

Time only breaks ties. The team page's record table shows when each line was locked, when its source link was first
opened, and whether the line was changed afterwards. The lock is a rule of the game, not a wall: Otterscan's
contract page shows the verified source too.

A reason must point at something in the record: a transaction's sender, the function called, an internal transfer
or a log. "The code is malicious" with no transaction is no reason.

## Case A: the staking site (blocks 19-23)

| | |
| --- | --- |
| What happened | Block 19: A0 deploys CourseToken (CTK). Block 20: A0 sends 10,000 CTK to the complainant (A8). Block 21: A9 deploys `StakingRewards` (its treasury is A9). Block 22: the complainant sends `approve(StakingRewards, 1,000 CTK)` on the token. Block 23: the complainant sends `claimRewards(token, 1,000 CTK)`; inside it, the contract calls `transferFrom(complainant, treasury, 1,000 CTK)` on the token. |
| The money (+1) | 1,000 CTK, from the complainant (A8) to the treasury (A9). Not "all" the tokens: the complainant still holds 9,000; only the approved amount could move. |
| The line (+2) | The complainant's own `approve` in block 22. Also accept `_drain`'s `transferFrom` line (or `claimRewards`) if the reason says the complainant's approval is what let it run. |
| Who was allowed | The staking contract, as spender, by the complainant's approval. Both transactions were sent by the complainant. |
| Reason | Block 22's sender is A8 and its function is `approve`; block 23's sender is also A8. The token's `Transfer` log in block 23 moves exactly the amount approved in block 22 to A9. The contract's own `RewardsClaimed` event is its word for what happened; the `Transfer` is what moved. |
| Not a flaw | The token and the staking contract both did what their code says. ERC-20's `approve` lets a spender move the holder's tokens (`@vogelsteller_eip20tokenstandard_2015`). |

## Case B: the vault (blocks 24-27)

| | |
| --- | --- |
| What happened | Block 24: A0 deploys `TimelockVault` (one-day unlock delay, 1% fee, treasury A0). Block 25: the depositor (A8) deposits 10 ETH. Block 26: the owner (A0) sends `setWithdrawFeeBps(9000)`, twelve seconds before the deposit unlocks; its log is `WithdrawFeeSet(9000)`. Block 27: the depositor withdraws 10 ETH; 9 ETH goes to the treasury (A0), 1 ETH to the depositor; its log is `Withdrawal(account, 10 ETH, fee 9 ETH)`. |
| The money (+1) | The depositor's 10 ETH: 9 ETH to the owner's treasury (A0), 1 ETH back to the depositor. |
| The line (+2) | The owner's `setWithdrawFeeBps(9000)` in block 26. |
| Who was allowed | The owner only (`onlyOwner`, the code's access control: one account may call it, `@openzeppelin_accesscontrol_2026`); the code caps the fee at 90%, the fee set. |
| Reason | Block 26's sender is A0, the vault's deployer and owner; block 27's internal transfers split 9 and 1. |
| Not a flaw | The contract lets its owner set the fee at any time, as written. It fits a rug pull: the owner's power used against the depositors (`@xia_tradeortrick_2021`). |

The twist's answer is the second choice: the delay is checked only in `withdraw`; `setWithdrawFeeBps` takes effect
in the block it is called, and `setUnlockDelay` has no cap, so the owner can also keep depositors in.

The page's "Tell an agent" example uses blocks 26 and 27 (the card drafted it with placeholder blocks 212 and 213).

## Case C: the pool (blocks 28-30)

| | |
| --- | --- |
| What happened | Block 28: A0 deploys `PlainBorrower`. Block 29: A0 sends it 2 ETH for the fee. Block 30: `borrow(2,000 ETH)` calls the lender's `flashLoan`; the lender sends 2,000 ETH, the borrower's `onFlashLoan` repays 2,001.8 ETH, all in one transaction. |
| The money (+1) | 2,000 ETH out of the pool and back, with a 1.8 ETH fee to the pool. No one lost money. |
| The line (+2) | **None.** |
| A flaw named (-1) | Any flaw named here costs a point. |
| Reason | The trace shows the 2,000 ETH out and 2,001.8 ETH back in one transaction; the lender's balance rises by the fee. A flash loan is borrowed and repaid with a fee in one transaction (`@aave_flashloans_2026`, as of 31 Oct 2026). |

## The constraint, to close

A contract does what its code allows, for whoever its code allows, and it has no key of its own
(`@ethereum.org_accountsdeveloperdocs_2025`). Money leaving shows only that someone was allowed to call something:
ask who, and who allowed them. The code let anyone in (a flaw, as with the vault); the code let one key in (the
owner's power); or the holder gave permission (an approval).
