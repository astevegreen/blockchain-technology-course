# Days 6-7 Hide and Trace Regression Playbook

This playbook is the browser-driven companion to the automated `hide-and-trace` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The automated suite has passed on this machine. It plays a whole game, so its chain is spent: for the game flow,
   start a fresh one (`docker compose -p hide-and-trace down -v`, then `./lab-manager.sh start hide-and-trace`) and
   wait until the instructor page shows "Ready for teams" (a few minutes).
2. The lab is under the course site's router: `http://127.0.0.1/labs/hide-and-trace/` on this machine.
3. Obtain the current instructor credentials from `.runtime/instructor-credentials.txt`. Team codes are drawn at
   run time and shown only on the instructor page: never copy one into a report.
4. Use windows at least 800 pixels wide: one for the instructor, one for each of two teams.

The rules the pages must follow are on the design card (`docs/lab-cards/hide-and-trace.md`) and in
`dynamic-labs/hide-and-trace/quizes/SCORING_NOTES.md`.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures and a screenshot.

## Game Flow

1. Open `/labs/hide-and-trace`. Confirm it lands on `/labs/hide-and-trace/game/`, which asks for a team code.
   Enter a made-up code and confirm the page refuses it.
2. Open `/labs/hide-and-trace/game/instructor/` without signing in and confirm the router sends you to the
   instructor sign-in. Sign in and confirm the page shows the phase "ready" and "Ready for teams".
3. Set the clock to 0 (blocks by hand) and make 2 teams. Confirm the table lists Team 1 and Team 2 with a code
   each, Team 1 tracing Team 2 and Team 2 tracing Team 1, and moves used 0 of 8.
4. In each team window enter that team's code. Confirm the page shows one coin of 2.1 BTC, the exchange deposit
   address, the eight-move budget, block count and the move menu (split, CoinJoin, peel, mixer, wait). Confirm no
   other team's coins or code appear.
5. Confirm a move is refused before the hide starts. On the instructor page start the hide.
6. Team 1: split into 0.5001 BTC, 0.8 BTC and the rest. Team 2: split into 0.5001 BTC and the rest. On the
   instructor page mine 1 block. Confirm each team page now lists the new coins and moves used 1 of 8.
7. Both teams send their 0.5001 BTC coin to the CoinJoin. Confirm the page says which block the round runs in. Mine
   blocks until it does. Open the round in the explorer from the team page and confirm many equal 0.5 BTC outputs,
   and as many inputs.
8. Team 2 sends a coin through the mixer to its own start address. Confirm the payee menu offers the start address as
   a "reuse" choice and the move is accepted. Mine past its delay and confirm, in the explorer, that the start
   address now shows two receives.
9. Mine to block 30. Confirm both team pages move to the trace, each names its target and the target's start coin,
   no move log of any team is shown, and the move menu is gone.
10. Team 1: make a High call on an output of Team 2's with two reasons of different kinds, a High on timing alone,
    and the stop call. Confirm the page shows each call with its word and reasons and lets one be deleted before
    the reveal. Team 2: make an Undetermined call.
11. On the instructor page open the reveal (confirm the dialog). Confirm every page now shows the scores, each
    team's move log beside the calls its tracer made on it, the class table of High calls grouped by evidence, and
    the line counting Highs on amount or timing alone and how many were wrong. Confirm the timing-alone High is
    shown scored as a Low and calls can no longer be made or deleted.
12. Use "Save this game" and confirm a JSON file downloads. Check console errors and failed network requests on all
    three windows. Failed websocket reconnects in the explorer that do not break a page are notes; a page that does
    not load, or an API call outside `/labs/hide-and-trace/`, is a failure.

## Shell Flow

1. Open `/assets/labs/hide-and-trace/index.html` from the course site. Confirm it opens on the case (2.1 BTC, 30
   blocks, made-up names) and asks the commit question before showing any step after it.
2. Answer the commit question and confirm the "do" step shows links to the game page and the explorer, under
   `/labs/hide-and-trace/`, and the five checkboxes for where the trail was picked up.
3. Tick one checkbox and confirm "That is our trail" appears and leads to the naming step (calibration) with its
   sources, then the explorer step, the twist question and the tell step's worked example.
4. Confirm the slide link opens "Before and after the mix still leak" in the mixers lesson, and the slide's link
   opens this page.
5. Confirm no team code, move log, score or real mixer or coordinator name appears on the page.
