# Task: Instructor Labs Progress Page And Rollup

Task ID: `portal-instructor-progress-surfaces`

## Purpose

Validate the shared instructor Labs Progress page and the rollup request
it depends on.

## Context Ownership

- use a fresh unauthenticated probe context for the auth-gate check
- log in through `/instructor/` in a separate fresh instructor context
- do not reuse student or other lab-role cookies in either context

## Routes

- `/instructor/`
- `/instructor/labs-progress`
- `/api/portal/progress-rollup`

## Steps

1. In a fresh unauthenticated context, open `/instructor/labs-progress`
   and confirm it redirects or blocks before login.
2. Log in through `/instructor/` in a separate fresh instructor
   context.
3. Open `/instructor/labs-progress`.
4. Confirm the page renders without a blank shell or auth error.
5. Confirm the page successfully loads `/api/portal/progress-rollup`.
6. Confirm the page shows either lab rows or a clean empty-state, not a
   fetch failure banner.
7. Check console errors and network failures after the page load and the
   rollup request.

## Pass Conditions

- unauthenticated access redirects or blocks cleanly
- the labs-progress page loads behind shared auth
- the rollup request succeeds behind shared auth
- no unexplained JavaScript or network failures remain

## Failure Evidence

Capture all of the following on failure:

- failing URL
- screenshot
- visible error text
- console errors
- failed network requests

## Required Output

Return:

- whether unauthenticated access blocked correctly
- whether the page rendered lab rows or an empty-state
- pass, partial, or fail
- any fix recommendation if non-pass
