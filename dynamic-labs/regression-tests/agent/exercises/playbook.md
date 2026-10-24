# Dynamic L03 Exercises Regression Playbook

This playbook is the browser-driven companion to the automated
`exercises` regression suite.

Use it when validating the visible student and instructor experience for
the BGP and Insider exercises, along with JavaScript or network errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the live exercises environment is
   already running and has already passed the automated suite.
2. Obtain the current instructor credentials from
   `.runtime/instructor-credentials.txt`.
3. Use a fresh browser context for each student task.
4. Use a separate authenticated browser context for each instructor
   task.

Reset policy:

- do not perform a second independent reset just to start the browser
  stage
- the browser stage should reuse the same live environment that the
  automated stage already validated
- if the overall run explicitly chose fresh-start mode, that reset
  should have happened once before the automated stage
- only reset again if the run has failed badly enough that the
  environment is no longer trustworthy, or if the suite is being
  started over from scratch

Optional fresh-start reference:

- if a fresh-start run is needed, use
  `../../automated/exercises/README.md`

## Evidence Rules

For every failed step, capture:

- URL
- visible failure
- console errors
- network failures
- screenshot

## Role-Switch Rule

- keep student and instructor work in separate fresh browser contexts
- if you need to re-enter either role later in the flow, create a new
  context/session for that role instead of reusing the other role's
  cookies

## BGP Flow

Since the June 2026 pilot the BGP game is student-only: no instructor
dashboard, and each student plays a room of bots.

1. Open `/exercises/bgp/`.
2. Confirm the student shell loads without a blank page.
3. Create a room with 4 nodes and 0 malicious nodes.
4. Broadcast, vote for the order received, and reveal the debrief.
5. Confirm the debrief shows the correct consensus and the student's node
   surviving.
6. Check console and network failures after each major state change.

## Insider Flow

1. Open `/exercises/insider/`.
2. Create a private room as the host.
3. Confirm the room code or room state is visible.
4. In a separate fresh instructor context, confirm
   `/exercises/insider/instructor` redirects or blocks before login.
5. Log in through `/instructor/` in that instructor context and open
   `/exercises/insider/instructor`.
6. Confirm the room appears on the instructor dashboard.
7. From the host UI, start the round; agents fill the room to 5 players.
8. Confirm the role assignment and first live round state appear.
9. Check console and network failures after each major state change.

## Completion Rule

The dynamic L03 exercises browser regression is only complete when:

- both student home pages load
- the Insider instructor dashboard loads behind shared auth
- the Insider instructor dashboard blocks before login
- the BGP student path works visibly from room creation to debrief
- the Insider private-room host path works visibly
- no unexplained JavaScript or network failures remain
