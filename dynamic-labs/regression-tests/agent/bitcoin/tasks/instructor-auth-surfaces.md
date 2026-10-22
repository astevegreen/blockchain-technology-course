# Task: Instructor Auth, Admin, and TTYD

Task ID: `btc-instructor-auth-surfaces`

## Purpose

Validate instructor gating and the instructor-only Bitcoin surfaces.

## Context Ownership

- use a fresh browser context dedicated to instructor auth
- keep this context separate from all student tasks
- obtain credentials from `.runtime/instructor-credentials.txt`

## Routes

- `/instructor/`
- `/labs/bitcoin/admin`
- `/labs/bitcoin/instructor/`

## Steps

1. In a fresh unauthenticated context, open `/labs/bitcoin/admin` and
   confirm it redirects to `/instructor/`.
2. In the same fresh unauthenticated context, open
   `/labs/bitcoin/instructor/` and confirm it redirects to
   `/instructor/`.
3. Log in through `/instructor/` with the shared instructor credentials.
4. Re-open `/labs/bitcoin/admin` and confirm the instructor console
   loads.
5. Open `/labs/bitcoin/instructor/` and confirm the instructor ttyd
   route loads.
6. In a separate student context, open a student ttyd shell and run
   `curl -sS --max-time 5 http://bitcoin-instructor-1:7681/`. It must fail
   (connection refused or timeout): the instructor ttyd binds only to its
   mgmt-net address (`ttyd-bind-mgmt.sh`), never to p2p-net.
7. Check console errors and network failures after each major phase.

## Pass Conditions

- unauthenticated instructor surfaces redirect correctly
- login succeeds with shared instructor credentials
- admin loads after auth
- instructor ttyd loads after auth
- the instructor ttyd is unreachable from a student shell
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
