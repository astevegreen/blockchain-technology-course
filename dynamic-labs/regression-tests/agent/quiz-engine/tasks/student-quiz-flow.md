# Student Quiz Flow Task

## Goal

Validate one visible Quiz Engine v2 browser quiz flow end to end, including
auto-save feedback, incomplete-submit validation, submit, and results access.

## Steps

1. Open `/quiz/` in a fresh student context.
2. Get a new anonymous identifier or sign in with an identifier created during
   the student-entry task.
3. Open the quiz list and start the seeded `Regression Visible Quiz`.
4. Confirm the attempt page shows the quiz title, answer rows, and `Submit
   quiz`.
5. Select or type one answer and confirm the short-lived `Saved` toast appears.
6. Attempt to submit with at least one question unanswered.
7. Confirm the page stays on the attempt and highlights incomplete questions.
8. Complete every visible question and submit.
9. Open the result page when redirected, or use the visible result link from
   the quiz list if the attempt needs written grading.
10. Check console errors and network failures after quiz load, auto-save,
    incomplete submit, final submit, and result view.

## Expected Results

- the quiz loads visibly and accepts answers
- auto-save shows a saved toast and survives page reload
- incomplete submit is blocked and incomplete items are highlighted
- final submit succeeds
- result or pending-result view is reachable according to the quiz result policy

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
