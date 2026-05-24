# Instructor Surfaces Task

## Goal

Validate the Quiz Engine v2 instructor dashboard, workflow guide, core
management surfaces, shared-auth gating, and CSRF behavior behind `/quiz/`.

## Context Ownership

- use a fresh unauthenticated probe context for pre-auth checks
- log in through `/instructor/` in a separate fresh instructor context
- keep instructor and student cookies in separate browser contexts

## Steps

1. In a fresh unauthenticated context, open `/quiz/instructor`,
   `/quiz/instructor/banks`, and `/quiz/instructor/metrics`, and confirm each
   route redirects or blocks before login.
2. Log in through `/instructor/` in a separate fresh instructor context.
3. Open `/quiz/instructor`.
4. Confirm the dashboard shows `Instructor Dashboard`, `Operational Summary`,
   `Quiz Workflow Guide`, and the six workflow steps from import through
   metrics.
5. Open `/quiz/instructor/ingest`, `/quiz/instructor/banks`,
   `/quiz/instructor/questions`, `/quiz/instructor/templates`,
   `/quiz/instructor/quiz-versions`, `/quiz/instructor/grading`,
   `/quiz/instructor/metrics`, and `/quiz/instructor/exports`.
6. Confirm each page shows the shared `Quiz Engine` chrome and instructor
   navigation.
7. On `/quiz/instructor/registration`, submit the visible form normally and
   confirm it succeeds. This validates server-rendered CSRF token injection for
   standard HTML forms.
8. Open `/quiz/instructor/api/metrics` and confirm JSON metrics are returned
   without raw `student_id` text.
9. Check console errors and network failures after each major page change.

## Expected Results

- shared auth blocks instructor routes before login
- shared auth grants access to v2 instructor pages after login
- workflow guide explains import, bank review, template building, generation,
  publishing, grading, and metrics
- all core v2 instructor pages render through `/quiz/instructor`
- CSRF-protected form submission works in the browser
- metrics JSON is reachable behind shared auth and stays PII-free

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
