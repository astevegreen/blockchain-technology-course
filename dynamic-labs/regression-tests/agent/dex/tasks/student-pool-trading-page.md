# Task: Pool trading pages

Task ID: `dex-student-pool-trading-page`

## Purpose

Walk the day 4 game's two pages as a student would, through the browser: the course page
(`blockchain-course/assets/labs/pool-trading/`, card `docs/lab-cards/pool-trading.md`) and the game page on the
exchange lab's L1 host (`/sign/pool-trading.html`). The chain side (the instructor's round script, the bot's
sandwiches, the 0.5% limit left alone, the twist's refused trade and the answer key) is covered by
`regression-tests/automated/dex/test_pool_trading_live.py`; this task covers only the pages.

## Context Ownership

- use a fresh student browser context
- class mode only: the course page reaches the lab host through the router

## Routes

- `/assets/labs/pool-trading/index.html`
- `/sign/pool-trading.html` on the dex host

## Steps

1. Open the course page and confirm the title "Pool trading", step 1 (the case) and the slide link
   "A bigger trade gets a worse price".
2. Prediction: confirm four choices, pick "Possibly much less: anyone who sees your trade before the block can move
   the price against you first.", pick a confidence word, and confirm the commitment locks.
3. In the do step, confirm "Open the game page" opens `/sign/pool-trading.html` on the dex host in a new tab.
4. On the game page: load seat 30 and confirm its address and balances show. The round line says either that it
   is waiting for the instructor or that the last round (the live suite's) is over; with no round open for the
   seat, confirm "Read the pool now", the limits and "Send my trade in my turn" stay disabled. Confirm the score
   table and "Show the class's balances" render, in seat order with no ranking. Do not open a round or send a
   trade: the live suite plays the round.
5. Back on the course page, set round 1 and round 2 to "none", "close to the quote", "no": a note and the button
   "My blocks really show this" must appear and the step must not finish. Set both to "none", "well under the
   quote", "yes": the step finishes.
6. Name step: the term is slippage tolerance. Twist: pick "Yes: a big trade came first." and confirm it is marked
   wrong; pick "No: no one bought before you and sold after you." and confirm it is accepted.
7. Tell step: write a sentence and confirm the example is shown after.
8. Reload the course page and confirm it resumes at the same step; press P and confirm projector mode.
9. Check console errors and network failures on both pages.

## Pass Conditions

- the course page opens the game page on the dex host
- every step renders; the do step finishes on a fitting reading; the twist accepts choice 3 of 4 (index 2)
- neither page names the twist's seats, the bot's profit floor or the instructor's script
- no unexplained JavaScript or network failures

## Failure Evidence

Capture the URL, a screenshot, visible error text, console errors and failed network requests.

## Required Output

Return pass, partial or fail for each step, and a fix recommendation if non-pass.
