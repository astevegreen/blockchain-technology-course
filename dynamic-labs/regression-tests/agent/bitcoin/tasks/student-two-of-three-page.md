# Task: Two of three game page

Task ID: `btc-student-two-of-three-page`

## Purpose

Walk the day 2 pair game's page (`blockchain-course/assets/labs/two-of-three/`, card
`docs/lab-cards/two-of-three.md`) as a student would, through the browser. The chain side (funding, both
`finalizepsbt` answers, the witness, the paid indexes, the watch-only try) is covered by
`regression-tests/automated/bitcoin/test_two_of_three_live.py`; this task covers only the page.

## Context Ownership

- use a fresh student browser context
- class mode only: the panel button reaches the course site through the router

## Routes

- `/labs/bitcoin/c/<uuid>/`
- `/assets/labs/two-of-three/index.html`

## Steps

1. Claim a Bitcoin station and confirm the wrapper's panel bar shows a "Two of three" button.
2. Click it and confirm the game page opens in a new tab with the title "Two of three" and step 1, the case.
3. Next to the prediction: confirm four choices, pick "It is refused: the lock wants a second signature.", pick a
   confidence word, and confirm the commitment locks.
4. In the do step, confirm seven command blocks (one for both partners, three for partner 1, three for partner 2).
   Set the two selects to `true` and `false`: a note must appear and the step must not finish. Set them to
   `false` and `true`: the step finishes and shows the prediction against "refused" (choice 3 on the page).
5. Name step: the term is PSBT. Explorer step: the mempool link opens `/labs/bitcoin/mempool/`.
6. Twist: pick "Spend their coins." and confirm it is marked wrong; pick "List their addresses and see their coins,
   but spend none." and confirm it is accepted and the round 2 commands (deriveaddresses, then the `watch` wallet
   try) are shown.
7. Tell step: write a sentence and confirm the example is shown after.
8. Reload the page and confirm it resumes at the same step; press P and confirm projector mode.
9. Check console errors and network failures.

## Pass Conditions

- the panel button opens the page
- every step renders; the do step finishes only on false, then true; the twist accepts choice 2 of 4
- no page holds an address, index or key
- no unexplained JavaScript or network failures

## Failure Evidence

Capture the URL, a screenshot, visible error text, console errors and failed network requests.

## Required Output

Return pass, partial or fail for each step, and a fix recommendation if non-pass.
