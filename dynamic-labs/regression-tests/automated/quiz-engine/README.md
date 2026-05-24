# Quiz Engine v2 Automated Regression

This directory holds the code-driven regression suite for the Quiz
Engine v2 surface routed under `/quiz/`.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- public home, anonymous identifier issue, student quiz list, and auth gates
- shared-auth gating for instructor routes
- deterministic live seeding through the v2 instructor APIs
- seeded student identifier enrollment, quiz start, submit, and results coverage
- instructor dashboard, banks, questions, templates, generated quizzes, grading,
  metrics, exports, and CSRF checks against the seeded v2 quiz

Implemented files:

- `test_quiz_engine_live.py` - live router, auth, seed, student, and
  instructor checks
- `live_support.py` - request, login, cookie-cache, CSRF, and v2 API seeding
  helpers
- `run.sh` - default runner
- `runner.Dockerfile` - router-net attached test runner image

Current split:

- browser-less automated checks cover the stable seeded request flows,
  shared-auth gates, CSRF gates, and instructor metrics
- richer browser validation such as auto-save toasts, incomplete-submit
  highlighting, dashboard rendering, and console/network failures belongs in
  the agent suite

Default run:

```bash
./regression-tests/automated/quiz-engine/run.sh
```

Single-test iteration:

```bash
./regression-tests/automated/quiz-engine/run.sh --skip-start --match test_student_enroll_start_submit_and_results
```

Optional fresh-start run:

```bash
./regression-tests/automated/quiz-engine/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/quiz-engine/run.sh --direct-host
```
