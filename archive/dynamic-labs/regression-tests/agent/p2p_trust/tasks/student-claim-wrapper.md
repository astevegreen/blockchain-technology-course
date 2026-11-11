# Task: Student Claim and Wrapper Shell

Task ID: `p2p-student-claim-wrapper`

## Purpose

Validate that a fresh student browser context can claim a `p2p_trust`
lane and land on the expected wrapper page without browser-side errors.

## Context Ownership

- use a fresh unauthenticated browser context
- do not reuse cookies from any other task
- do not use instructor credentials in this context

## Routes

- `/labs/p2p_trust/`
- `/labs/p2p_trust/c/<uuid>/`

## Steps

1. Open `/labs/p2p_trust/`.
2. Confirm the route claims a lane and lands on
   `/labs/p2p_trust/c/<uuid>/`.
3. Record the claimed `uuid`.
4. Confirm the wrapper shows the station badge, the `help-btn`, and
   the ttyd frame area.
5. Confirm the wrapper is not stuck on an error splash or loading
   state.
6. Check console errors and network failures for the landing route and
   wrapper route.

## Pass Conditions

- final URL matches `/labs/p2p_trust/c/<uuid>/`
- a station identifier is visible
- wrapper UI is present
- `help-btn` exists on the wrapper page
- no unexplained JavaScript or network failures block the flow

## Failure Evidence

Capture all of the following on failure:

- final URL
- screenshot
- visible error text
- console errors
- failed network requests

## Required Output

Return:

- claimed uuid
- station if visible
- pass, partial, or fail
- any fix recommendation if non-pass

