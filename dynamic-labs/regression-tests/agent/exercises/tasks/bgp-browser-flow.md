# BGP Browser Flow Task

## Goal

Validate the visible BGP exercise flow for a student. Since the June 2026
pilot the BGP game is self-service: each student plays a room of bots, and
there is no instructor dashboard.

## Context Ownership

- use one fresh student context for the whole room flow

## Steps

1. Open `/exercises/bgp/` in a student context.
2. Confirm the student page renders and the connection state settles.
3. In Mission Control, create a room with 4 nodes and 0 malicious nodes.
4. Confirm the Network View shows the student's node and 3 bot peers, and
   the student is asked to broadcast.
5. Broadcast, then confirm the student receives 3 messages carrying the
   same order and is asked for a final vote.
6. Vote for that order, then reveal the debrief.
7. Confirm the Self-Service Debrief Explorer shows the network, the
   correct consensus, and the student's node as surviving.
8. Check console and network failures after page load, room creation,
   broadcast, vote, and debrief.

## Expected Results

- the student shell loads
- a room of bots opens without an instructor
- the room advances from broadcast to vote to debrief
- the debrief matches the order every node sent

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
