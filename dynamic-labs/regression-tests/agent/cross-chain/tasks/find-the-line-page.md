# Task: Find the line game page

Task ID: `cross-chain-find-the-line-page`

## Purpose

Walk the day 8 team game's page (`blockchain-course/assets/labs/find-the-line/`, card
`docs/lab-cards/find-the-line.md`) as a team would, through the browser. The chain side (the three cases'
transactions, their senders, logs and the neutral Sourcify names) is covered by
`regression-tests/automated/cross-chain/test_cross_chain_live.py`; this task covers the page and its links.

## Context Ownership

- use a fresh student browser context
- class mode: the worksheet reaches the course site through the router; the exploit explorer is `exploit.<host>:8445`

## Routes

- `/labs/cross-chain/lab/`
- `/assets/labs/find-the-line/index.html`

## Steps

1. Open the worksheet and confirm the "Find the line" section links "Open Find the line"; follow it and confirm
   the page title "Find the line" and step 1, the case, with the three complaints.
2. Prediction: confirm four choices; pick "It depends on who called what, and who allowed them: read the
   transactions", pick a confidence word, and confirm the commitment locks.
3. Do step: confirm three case panels (A, B, C), each "Not locked", with block links (A: 20-23, B: 24-27,
   C: 28-30) and address links. Open block 26 from case B and confirm Otterscan shows a transaction from
   `0xf39F…2266` calling `setWithdrawFeeBps`.
4. In case A, confirm "Lock this line" stays disabled until all six fields have text. Fill them and lock: the
   panel shows "Locked" with a time, its fields are read-only, and a "The staking contract's source" link appears.
   No source link shows on an unlocked panel.
5. Click the source link: it opens `StakingRewards.sol` from Sourcify. Back on the page, the record table shows a
   "Source opened" time for case A, and a "Change this line" button appears. Click it and accept: the panel
   unlocks, says "Changed after the source was opened: +1 at most", and the record shows "yes (+1 at most)".
6. Lock case A again, then fill and lock B and C. The step finishes and shows the prediction against choice 3.
7. Name step: the term is access control. Explorer step: the block 23, 26, 27 links and the saved-pages link
   (`/labs/cross-chain/exploit-fallback/`) open.
8. Twist: pick "Yes: fee changes wait out the delay" and confirm it is marked wrong; the answer is the second
   choice.
9. Tell step: write a sentence and confirm the example (blocks 26 and 27) is shown after.
10. Reload the page and confirm it resumes, with the three locked lines and their times kept. "Start the cases
    over" clears them after a confirm.
11. Check console errors and network failures.

## Pass Conditions

- the worksheet link opens the page
- every step renders; a source link appears only on a locked line; the record table keeps lock, source and change
  times
- the do step finishes only when all three lines are locked; the twist accepts choice 2 of 4
- no page or Sourcify file names `ApprovalDrainer`, `TimelockRugVault`, a drainer or a rug
- no unexplained JavaScript or network failures

## Failure Evidence

Capture the URL, a screenshot, visible error text, console errors and failed network requests.

## Required Output

Return pass, partial or fail for each step, and a fix recommendation if non-pass.
