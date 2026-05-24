# Student Entry Task

## Goal

Validate the public Quiz Engine v2 anonymous entry flow: student home,
identifier issuance, identifier-based return, and published quiz list.

## Steps

1. Open `/quiz/`.
2. Confirm the public student home loads with `Quiz Engine`, `Get identifier`,
   and identifier return controls. Confirm it does not show instructor links.
3. Click `Get identifier`.
4. Record the anonymous identifier shown on the confirmation page. It should
   look like `QZ-XXXX-XXXX`.
5. Continue to the quiz list and confirm `Available Quizzes` renders.
6. In a fresh student context, open `/quiz/`, enter the recorded identifier,
   and click `Continue`.
7. Confirm the same quiz list loads and shows any seeded visible regression
   quiz from the automated suite.
8. Check console errors and network failures after the home page, identifier
   confirmation page, and signed-in quiz list.

## Expected Results

- public student home is readable and functional
- identifier issuance succeeds without asking for PII
- identifier login succeeds in a fresh context
- the signed-in quiz list shows published v2 quizzes
- student pages do not expose instructor navigation

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
