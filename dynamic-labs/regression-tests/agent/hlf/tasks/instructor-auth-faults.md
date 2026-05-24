# Instructor Auth, Consoles, And Fault Surfaces

## Goal

Validate the HLF instructor-only surfaces behind shared auth, including
all consortium node consoles and the orderer console.

## Context Ownership

- use a fresh unauthenticated probe context for pre-auth checks
- log in through `/instructor/` in a separate fresh instructor context
- do not reuse student cookies in either context

## Steps

1. In a fresh unauthenticated context, confirm
   `/labs/hlf/hlf_instructor.html`, `/labs/hlf/peer/org1/console/`,
   `/labs/hlf/peer/org5/console/`, `/labs/hlf/orderer/console/`, and
   `/labs/hlf/api/hlf/instructor-snapshot` all redirect or block before
   login.
2. Log in through `/instructor/` in a separate fresh instructor
   context.
3. Open `/labs/hlf/hlf_instructor.html` and confirm it loads only after auth.
4. Verify the instructor panel contains links for all 6 consortium nodes:
   Org1 (Cascadia State), Org2 (Chesapeake Canoe), Org3 (South Hudson),
   Org4 (Maple Leaf), Org5 (Meridian, read-only), and Orderer.
5. Open `/labs/hlf/peer/org1/console/` — confirm it loads behind auth and
   the ttyd iframe points to `/labs/hlf/instructor/term/org1/` (absolute,
   not through a student claim prefix).
6. Open `/labs/hlf/peer/org2/console/` — confirm it loads behind auth and
   the ttyd iframe points to `/labs/hlf/instructor/term/org2/`.
7. Open `/labs/hlf/peer/org3/console/` — confirm it loads behind auth and
   the ttyd iframe points to `/labs/hlf/instructor/term/org3/`.
8. Open `/labs/hlf/peer/org4/console/` — confirm it loads behind auth and
   the ttyd iframe points to `/labs/hlf/instructor/term/org4/`.
9. Open `/labs/hlf/peer/org5/console/` — confirm console loads with the
   read-only Meridian context.
10. Open `/labs/hlf/orderer/console/` — confirm orderer console loads and
    the ttyd iframe points to `/labs/hlf/instructor/term/orderer/`.
11. Open an instructor-only data surface such as the instructor snapshot
   or visible fault controls in the instructor UI.
12. Check console errors and network failures after each major step.

## Expected Result

- instructor auth works for login and session persistence
- instructor panel shows links for all 6 consortium nodes
- all consortium node consoles load behind auth with correct ttyd paths
- unauthenticated requests redirect to instructor login or block cleanly
- no unexplained browser errors appear
