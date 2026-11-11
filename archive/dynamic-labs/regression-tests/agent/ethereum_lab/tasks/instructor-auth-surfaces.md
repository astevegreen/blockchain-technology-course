# Task: Instructor Admin And Mode

Goal:

- validate shared-auth protection on the Ethereum instructor surfaces
- confirm the admin console and instructor mode both render after auth

## Context Ownership

- use a fresh unauthenticated probe context for pre-auth checks
- log in through `/instructor/` in a separate fresh instructor context
- do not reuse student cookies in either context

Steps:

1. In a fresh unauthenticated context, verify `/labs/ethereum/admin`
   redirects or blocks without instructor auth.
2. In the same unauthenticated context, verify
   `/labs/ethereum_lab/instructor/` and
   `/labs/ethereum_lab/?mode=instructor` also redirect or block.
3. Log in through `/instructor/` in a separate fresh instructor
   context.
4. Open `/labs/ethereum/admin`.
5. Confirm the instructor console renders.
6. Open `/labs/ethereum_lab/instructor/`.
7. Confirm the alias lands on instructor mode and loads after auth.
8. Confirm the instructor page can reach its config and
   `/labs/ethereum_lab/lab-api/fund-requests`.
9. Capture console logs and network failures for both surfaces.

Pass criteria:

- auth gates work before login
- admin console loads after login
- instructor mode loads after login
- instructor-only lab-api is reachable
- no unexplained JavaScript or network failures remain
