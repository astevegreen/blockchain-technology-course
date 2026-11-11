# Task: Instructor Auth and Terminal

Task ID: `p2p-instructor-auth-surfaces`

## Purpose

Validate instructor gating and the instructor-only `p2p_trust`
surfaces.

## Context Ownership

- use a fresh browser context dedicated to instructor auth
- keep this context separate from all student tasks
- obtain credentials from `.runtime/instructor-credentials.txt`

## Routes

- `/instructor/`
- `/labs/p2p_trust/admin`
- `/labs/p2p_trust/instructor/`

## Steps

1. In a fresh unauthenticated context, open `/labs/p2p_trust/admin`
   and confirm it redirects to `/instructor/`.
2. In the same fresh unauthenticated context, open
   `/labs/p2p_trust/instructor/` and confirm it redirects to
   `/instructor/`.
3. Log in through `/instructor/` with the shared instructor
   credentials.
4. Re-open `/labs/p2p_trust/admin` and confirm the instructor console
   loads.
5. Open `/labs/p2p_trust/instructor/` and confirm the instructor ttyd
   route loads.
6. Check console errors and network failures after each major phase.

## Pass Conditions

- unauthenticated instructor surfaces redirect correctly
- login succeeds with shared instructor credentials
- admin loads after auth
- instructor ttyd loads after auth
- no unexplained JavaScript or network failures block the instructor
  flow

## Failure Evidence

Capture all of the following on failure:

- URL
- screenshot
- visible error text
- console errors
- failed network requests

## Required Output

Return:

- whether unauthenticated redirects worked
- whether instructor login succeeded
- pass, partial, or fail
- any fix recommendation if non-pass
