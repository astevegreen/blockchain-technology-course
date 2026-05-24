# Shared Instructor Portal Regression Playbook

This playbook validates the cross-lab instructor portal surfaces that
are not owned by one lab-specific browser suite.

Use it when validating the authenticated Labs Progress page, its backing
rollup request, and browser-only failures such as JavaScript or network
errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the live dynamic-labs environment is
   already running and at least one automated lab suite has already run
   against it.
2. Obtain the current instructor credentials from
   `.runtime/instructor-credentials.txt`.
3. Use a fresh unauthenticated browser context for the auth-gate probe.
4. Use a separate authenticated browser context for the portal load.

## Evidence Rules

For every failed step, capture:

- URL
- visible failure
- console errors
- network failures
- screenshot

## Role-Switch Rule

- keep unauthenticated and authenticated portal checks in separate fresh
  browser contexts
- do not reuse student or other lab-role cookies when opening the
  shared instructor portal

## Flow

1. In a fresh unauthenticated context, open `/instructor/labs-progress`
   and confirm it redirects or blocks.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/instructor/labs-progress`.
4. Confirm the page renders without a blank state or auth error shell.
5. Confirm the page successfully loads `/api/portal/progress-rollup`.
6. Confirm the page shows either lab rows or a clean empty-state, not a
   fetch failure.
7. Check console and network failures after the page load and rollup
   request.

## Completion Rule

The shared instructor portal browser regression is only complete when:

- `/instructor/labs-progress` blocks before login
- the page loads behind shared auth
- `/api/portal/progress-rollup` succeeds behind shared auth
- no unexplained JavaScript or network failures remain
