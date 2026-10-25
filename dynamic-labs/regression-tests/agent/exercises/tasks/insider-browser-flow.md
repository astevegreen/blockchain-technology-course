# Insider Browser Flow Task

## Goal

Validate the visible Insider exercise flow for the host and the
instructor dashboard.

## Context Ownership

- use one fresh student context for the host flow
- use a separate fresh instructor context for instructor checks
- do not reuse student cookies in the instructor context, or instructor
  cookies in the student context

## Steps

1. Open `/exercises/insider/` in a student context.
2. Create a private room as the host.
3. Confirm the room code or room state is visible.
4. Open `/exercises/insider/room/<room-id>/qr.png` and confirm the QR
   image responds.
5. In a separate fresh instructor context, open
   `/exercises/insider/instructor` and confirm it redirects or blocks
   before login.
6. Log in through `/instructor/` in that instructor context and open
   `/exercises/insider/instructor`.
7. Confirm the room appears on the instructor dashboard.
8. Return to the host context and start the round. Agents fill the room
   to 5 players on their own (there is no fill-with-agents toggle since
   the June 2026 pilot).
9. Confirm the host receives a role, the roster shows 4 agents, and the
   round advances into the live game state.
10. Check console and network failures after each major phase.
11. Compare the student pages with `dynamic-labs/exercises/l03-i3-trust-game/HANDOUT.md`: every
    button the handout names in bold (**Join open game**, **Join private game**, **Invite more
    players**, **Start round**, **Lock in clue**, **Guess now**, **Return to main menu**) appears
    with that label, and the room badge shows a maximum of 6 players. **Join private game** shows
    only while private rooms are allowed, and **Guess now** only to the Insider: check those two in
    the page source (`templates/index.html`) when the run does not reach them.

## Expected Results

- the student host flow works visibly
- the QR image route works
- the instructor route blocks before login
- the instructor dashboard sees the new room
- the host can start a live round alone, with agents filling the room
- the student handout's button names and room size match the pages

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
