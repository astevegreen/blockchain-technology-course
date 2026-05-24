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
8. Return to the host context, enable fill-with-agents, and start the
   game.
9. Confirm the host receives a role and the round advances into the
   live game state.
10. Check console and network failures after each major phase.

## Expected Results

- the student host flow works visibly
- the QR image route works
- the instructor route blocks before login
- the instructor dashboard sees the new room
- the host can start a live round after enabling fill-with-agents

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
