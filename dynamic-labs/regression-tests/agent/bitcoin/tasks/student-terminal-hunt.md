# Task: Student terminal scavenger hunt

Task ID: `btc-student-terminal-hunt`

## Purpose

Walk day 1's terminal scavenger hunt (`docs/lab-cards/terminal-scavenger-hunt.md`) as a student: the Hunt button,
the five facts checked against the class chain, the re-run after the instructor mines, the twist and the score bar.
The automated suite checks the checker's answers; this task checks the page.

## Context Ownership

- use a fresh student browser context with one claimed lane
- mining needs a shell on the Docker host (the instructor's run sheet,
  `quizes/microlabs/terminal_scavenger_hunt_INSTRUCTOR_ANSWERS.md`)

## Routes

- `/labs/bitcoin/c/<uuid>/`
- `/api/bitcoin/hunt/?c=<uuid>`
- `/labs/bitcoin/btc-explorer/block-height/5`

## Steps

1. Claim a lane, open the wrapper, and confirm the panel bar has a **Hunt** button whose link carries `?c=<uuid>`.
   Open it: the page shows "Terminal scavenger hunt", no warning about the panel bar, and a score bar reading
   `Score 0/8` with a running clock.
2. Commit: pick (b), High, type a reason, lock it. The score bar shows `Prediction 1/1`.
3. In the lane's terminal run each command the page shows and paste the command and line. Each fact turns green and
   locks; `Facts 5/5`. Also try one wrong pair (e.g. `getblockhash 50`, or a date for fact 3) and confirm a red
   reason that does not show the right value.
4. After fact 5 the page asks for the instructor to mine. Before mining, paste the same confirmations line again:
   refused. Mine one block on `bitcoin-instructor-1`, rerun `getblock`, paste: accepted, and the step shows what changed and lets Next go on.
5. Open the explorer link from the explorer step; block 5's hash matches fact 2.
6. Mine two more blocks, then answer the twist "Neither" with a reason: `Twist 2/2`, `Score 8/8`.
7. Tell step: the hint asks for the sentence with no confidence word. Finish; the clock stops and says finished.
8. Reload: everything above is kept. Restart and confirm: the facts, the score and the clock reset.

## Solo run (the course launcher)

On a machine running the student launcher (`LANE_MODE=student-local`) there is no instructor, and the page mines:

9. After fact 5 the page shows a **Mine one block** button instead of "Tell your instructor". Paste the same
   confirmations line first: refused. Press the button: it says "Mined", and the re-run `getblock` pasted now is
   accepted. `getblockcount` on `bitcoin-instructor-1` grew by one.
10. Once the re-run is accepted, `getblockcount` on `bitcoin-instructor-1` grows by two more without anyone mining;
    the explorer at block 5 shows two more confirmations than the re-run. Reload: the button stays done and nothing
    more is mined.
11. In the classroom (step 4) the page shows no button, and `POST /api/bitcoin/hunt/mine` answers 403 (the
    automated suite checks this).

## Pass

Every step behaves as above, with no console errors and no failed requests other than the deliberate wrong pair's
`ok: false` answer (HTTP 200).
