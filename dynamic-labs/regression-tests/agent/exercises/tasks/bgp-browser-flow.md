# BGP Browser Flow Task

## Goal

Validate the visible BGP exercise flow for both the student and the
instructor.

## Context Ownership

- use one fresh student context for the student room flow
- use a separate fresh instructor context for instructor checks
- do not reuse student cookies in the instructor context, or instructor
  cookies in the student context

## Steps

1. Open `/exercises/bgp/` in a student context.
2. Confirm the student page renders and the connection state settles.
3. In a separate fresh instructor context, open
   `/exercises/bgp/instructor` and confirm it redirects or blocks before
   login.
4. Log in through `/instructor/` in that instructor context and open
   `/exercises/bgp/instructor`.
5. Use the instructor UI to enable self-service mode.
6. Return to the student context and create a single-player room.
7. Confirm the student view advances into the simulation state.
8. Check console and network failures after student page load,
   instructor auth probe, instructor page load, self-service enable, and
   room creation.

## Expected Results

- the student shell loads
- the instructor route blocks before login
- the instructor dashboard loads behind shared auth
- self-service can be enabled from the instructor UI
- the student can create a room and enter the simulation

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
