# Quiz Engine v2 Regression Playbook

This playbook is the browser-driven companion to the automated
`quiz-engine` regression suite. It validates Quiz Engine v2 through the unified
dynamic-labs `/quiz/` route.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The live dynamic-labs stack is already running.
2. The automated quiz-engine suite has already seeded `Regression Visible Quiz`.
3. Instructor credentials are available in `.runtime/instructor-credentials.txt`.
4. Use a fresh browser context for student flows.
5. Use a separate authenticated browser context for instructor surfaces.

Reset policy:

- do not perform a second independent reset just to start the browser stage
- reuse the same live environment that the automated stage already validated
- only reset again if the environment is no longer trustworthy, or if the suite
  is being started over from scratch

Optional fresh-start reference:

- if a fresh-start run is needed, use
  `../../automated/quiz-engine/README.md`

## Evidence Rules

For every failed step, capture:

- URL
- visible failure
- console errors
- network failures
- screenshot

## Role-Switch Rule

- when moving from student flow to instructor flow, or back again, close the
  current browser context and create a fresh session for the new role
- never reuse student cookies for instructor pages, or instructor cookies for
  student pages

## Student Flow

1. Open `/quiz/`.
2. Confirm the public student home loads with `Quiz Engine`, `Get identifier`,
   and identifier return controls. Confirm no instructor links are shown.
3. Get a new anonymous identifier and record it.
4. Continue to `/quiz/student/quizzes` and confirm the seeded
   `Regression Visible Quiz` appears.
5. In a fresh context, return to `/quiz/`, enter the recorded identifier, and
   confirm the same quiz list loads.
6. Start `Regression Visible Quiz`.
7. Answer one question and confirm the `Saved` toast appears.
8. Try to submit with at least one unanswered item and confirm incomplete items
   are highlighted.
9. Complete all items and submit.
10. Confirm the result or pending-result page is reachable according to the
    quiz result policy.
11. Check console and network failures after each major page change.

## Instructor Flow

1. In a fresh unauthenticated context, confirm `/quiz/instructor`,
   `/quiz/instructor/banks`, and `/quiz/instructor/metrics` redirect or block.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/quiz/instructor`.
4. Confirm the dashboard shows the `Quiz Workflow Guide` with import, bank
   review, template, generation, publishing, grading, and metrics guidance.
5. Open `/quiz/instructor/ingest`, `/quiz/instructor/banks`,
   `/quiz/instructor/questions`, `/quiz/instructor/templates`,
   `/quiz/instructor/quiz-versions`, `/quiz/instructor/grading`,
   `/quiz/instructor/metrics`, and `/quiz/instructor/exports`.
6. Confirm each page uses the `Quiz Engine` chrome and instructor navigation.
7. Submit the registration settings form normally and confirm CSRF-protected
   HTML form submission succeeds.
8. Open `/quiz/instructor/api/metrics` and confirm metrics JSON is returned
   without raw `student_id` text.
9. Check console and network failures after each major page change.

## Completion Rule

The Quiz Engine v2 browser regression is only complete when:

- public anonymous identifier issue and identifier sign-in work visibly
- at least one quiz can be taken end to end in the browser
- auto-save and incomplete-submit validation have been observed
- result or pending-result view is reachable
- instructor auth gates block before login
- instructor dashboard, workflow guide, management pages, metrics, and exports
  work behind shared auth
- CSRF-protected instructor form submission works in the browser
- no unexplained JavaScript or network failures remain
