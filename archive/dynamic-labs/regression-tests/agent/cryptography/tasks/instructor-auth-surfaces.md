# Task: Instructor Admin And Guide

Goal:

- validate shared-auth protection on the Cryptography instructor
  surfaces
- confirm the admin console, rendered guide, progress data, and raw
  instructor source all render after auth

## Context Ownership

- use a fresh unauthenticated probe context for pre-auth checks
- log in through `/instructor/` in a separate fresh instructor context
- do not reuse student cookies in either context

Steps:

1. In a fresh unauthenticated context, verify `/labs/cryptography/admin`
   redirects or blocks without instructor auth.
2. In the same unauthenticated context, verify
   `/labs/cryptography/instructor/` and
   `/labs/cryptography/instructor/lab02_crypto_overview.qmd` also
   redirect or block.
3. Log in through `/instructor/` in a separate fresh instructor
   context.
4. Open `/labs/cryptography/admin`.
5. Confirm the session summary area, progress view, and rendered
   solution guide appear.
6. Confirm the admin page successfully loads
   `/api/cryptography/instructor-guide` and its progress data without
   browser errors.
7. Open `/labs/cryptography/instructor/lab02_crypto_overview.qmd`.
8. Confirm the raw Quarto source file loads only after auth.
9. Capture console logs and network failures for both surfaces.

Pass criteria:

- auth gates work before login
- admin console loads after login
- rendered guide and progress data load after login
- raw Quarto source loads after login
- no unexplained JavaScript or network failures remain
