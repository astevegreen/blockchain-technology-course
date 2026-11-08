# Browser MCP Integration Playbook

Direct app base URL: `http://10.2.0.10:8000`

Routed full-stack base URL: `http://router-router-1/quiz` from a
browser-puppet container attached to `router-net`, or
`http://127.0.0.1/quiz` from the host.

This playbook covers the implemented application surface through Phase 18:
foundation routes, student anonymous identity, instructor dev auth for direct
test-header runs, shared dynamic-labs instructor auth and CSRF for routed runs,
registration/roster management with whole-roster viewing and roster-code
deletion, quiz-bank ingest, imported-content retirement
by lesson or tag, question-bank browsing,
instructor question-filter autocomplete term indexing with global and per-bank
term databases, explicit re-ingest planning, quiz templates with per-source
bank criteria, chip-based source tag selection, per-tag quotas, live advanced
criteria JSON synchronization, eligible-pool preview,
deterministic quiz generation, immutable generated quiz snapshots, instructor
preview, publication controls, availability windows, and student published-quiz
listing, student attempt start/resume, answer auto-save, tamper rejection, and
final submission, attempt limits, instructor extra-attempt grants,
administrative attempt voiding, timed attempts, lazy expiration, and expiration
worker finalization, written-response grading, result release, and
student-facing result visibility policies including instructor-triggered
per-question review reveal, instructor metrics dashboard
rollups, latest/all attempt filters, status filters, item analysis, topic/tag
and source rollups, anonymous student detail metrics, report CSV/JSON exports,
printable roster-code sheets, ingest-compatible bank export, full-engine JSON
export, full-export validation, SQLite backup-path reporting, the instructor
dashboard/root route, explicit student resume/result actions on the quiz list,
print-friendly HTML report views, and shared dynamic-labs theme chrome on
student, instructor, and printable HTML pages, including current-section
navigation state, skip-link/main-content behavior, responsive touch targets,
mobile table scrolling, import-retirement target dropdown behavior, and
long-lived signed student identifier cookies that bypass the login form until
the student logs out.

After each implementation phase, update this file for any newly implemented
browser-visible route or workflow, then rerun the playbook against the running
Docker container before closing the phase.

Use a real browser through the browser-puppet MCP attached to the Docker
network. Capture a screenshot at each meaningful transition and record any
console, page, or network errors in the run log.

### Latest Focused Run - Template Tags, Criteria JSON, And Review Reveal

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop context `context-a587f58ddee5`, page `page-7a599ceecc33`.
- Scope: focused validation for chip-based per-source tag selection, per-tag
  quota inputs, live advanced criteria JSON sync/apply/reset behavior, collapsed
  per-bank source override panels when using fallback criteria, and the
  per-quiz `release-review` route. Broader behavior remains covered by Docker
  integration/unit tests and prior browser runs below.
- Docker validation: rebuilt the Docker image, ran focused checks for the
  template builder and review reveal behavior with `2 passed`, then ran the
  full Docker suite with `222 passed`.
- Health/static result: rebuilt app container was reachable at
  `10.2.0.10:8000`; `/healthz` returned `200`.
- Template builder collapse result: `/instructor/templates/new` returned `200`
  with 44 source rows. The first row started with filter mode `inherit`, its
  `[data-template-source-override-panel]` was hidden, and nested override
  controls were disabled. Switching the filter to `override` revealed the panel
  and enabled visible controls.
- Chip/quota result: selecting the first bank, setting its count to `2`, adding
  `reading` and `slides` chips, and setting only `reading` quota to `1`
  produced hidden tags `reading, slides`, hidden quotas `reading:1`, and live
  criteria JSON with `source_rules[0].criteria.tags=["reading","slides"]` and
  `quotas.tags.reading=1`; the blank `slides` quota remained random.
- Criteria JSON result: enabling JSON edit mode made the textarea editable and
  showed `Save JSON` plus `Reset from form`. Invalid JSON shape reported
  `source_rules must be a list`. A valid schema v2 JSON payload applied back to
  the structured controls, updated fallback tags, source policy, selected bank,
  quota, chip state, and preserved advanced hidden source criteria including
  topic, hierarchy section, difficulty range, and topic/tag quotas. Reset
  regenerated equivalent JSON from the form, and leaving JSON edit mode returned
  the textarea to read-only with JSON actions hidden.
- Review reveal result: fetched an existing generated quiz detail page and
  verified the `Reveal per-question results` control was present. POSTing
  `/instructor/api/quiz-versions/26/release-review` returned `200` and set
  `review_released_at=2026-05-21T16:40:30+00:00`, which persisted in the
  follow-up quiz-version API response.
- Screenshot captured:
  `/data/artifacts/context-a587f58ddee5/screenshots/annotated-3c86c4232ebe.png`.
- Console/page/CSP result: no console errors, page errors, or CSP violations
  were reported.
- Deviations or failures: none.

## Preconditions

1. The app container is running through Docker Compose.
2. For direct app checks, the app service is attached to the
   `quiz_engine_v2_browser` Docker network at `10.2.0.10`, the browser MCP
   container is attached to the same Docker network, and
   `QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=test-header` with `TESTING=1` is acceptable
   (the app refuses test-header without it).
3. For routed full-stack checks, `lab-manager.sh start quiz-engine-v2` or
   `lab-manager.sh start all` has started router, course-site,
   instructor-auth-service, lane-service, and quiz-engine-v2; the browser MCP
   container is attached to `router-net`; and the app is using
   `QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=shared` plus the same runtime secret as
   the centralized instructor auth service.
4. Routed instructor checks log in through `/instructor/` or
   `/api/instructor/login`, not `/instructor/dev/login`.
5. Mutating instructor checks under routed shared auth must verify both sides
   of CSRF: missing tokens reject and a token from `/quiz/api/instructor/csrf`
   allows the mutation.
6. For the question-bank and template checks, the app should contain live quiz
   data. If the database is empty, import
   `../../quizes/dist/blockchain-course-quiz-bank-bundle.json` through
   `/instructor/ingest` or seed it through the app container, then create one
   template named `Browser MCP Template`.

## Browser Run

Use fresh, separate browser contexts/sessions if the MCP supports them: one
instructor context and one student context. Student login intentionally clears
the Flask browser session before storing the student identifier, so sharing one
browser context can remove the dev instructor session and invalidate later
instructor checks. The steps below use CSS selectors where stable selectors
exist; otherwise select by visible text. It is acceptable to use same-origin
`fetch()` from the browser MCP for JSON API POST checks when direct form
automation would make the run brittle.

1. Open `http://10.2.0.10:8000/healthz`.
   Expected: JSON text contains `status` and `ok`.

2. Open `http://10.2.0.10:8000/static/health.txt`.
   Expected: text contains `quiz-engine-v2 static ok`.

3. Open `http://10.2.0.10:8000/`.
   Expected: redirect lands on `/student/`, page title or H1 is `Quiz Engine`,
   and the page shows the anonymous identifier return form.

4. Inspect visible text on `/student/`.
   Expected: the form asks only for an anonymous identifier. It must not prompt
   for email, full name, student ID, institutional ID, or similar PII.

5. Open `http://10.2.0.10:8000/instructor`.
   Expected: before instructor login this returns `401` JSON/error text with
   `instructor_auth_required`. Continue with `/instructor/dev/login`.

6. Open `http://10.2.0.10:8000/instructor/dev/context` before dev login in a
   fresh browser context if possible, or after clearing cookies.
   Expected: `401` JSON/error text with `instructor_auth_required`.

7. In the instructor context, open
   `http://10.2.0.10:8000/instructor/dev/login`, enter
   `browser-teacher`, and submit.
   Expected: redirected to `/instructor`, page H1 is `Instructor Dashboard`,
   navigation links are present for ingest, banks, questions, templates,
   generated quizzes, registration, roster codes, grading, metrics, and
   exports, the dashboard link has `aria-current="page"`, the skip link targets
   `#dynamic-labs-main`, and dashboard sections include `Needs Attention`,
   `Attempt Status`, `Struggling Students`, `Weak Topics And Tags`, and
   `Confusing Questions`.

8. In the instructor context, open `/instructor/registration`, set mode to
   `Open`, cap to `40`, and save.
   Expected: page shows `Registration updated`.

9. In the student context, open `/student/`, click `Get identifier`.
   Expected: confirmation page H1 is `Your Identifier`, identifier text matches
   `QZ-XXXX-XXXX`, and there is a `Continue` link.
   Record this identifier as `open_identifier`.

10. Check browser local storage for key `quiz_engine_student_identifier`.
   Expected: value equals `open_identifier`.

11. Click `Continue`.
   Expected: `/student/quizzes` shows `Available Quizzes`, `Signed in as
   open_identifier`, and `No published quizzes are available`.

12. Open `http://10.2.0.10:8000/student/session`.
   Expected: JSON contains `authenticated: true`, the same identifier, status
   `active`, and source `open_registration`.

13. Return to `/student/quizzes` and click `Sign out`.
   Expected: redirected to `/student/` with `Signed out`.

14. On `/student/`, enter `open_identifier` in the identifier field and click
   `Continue`.
   Expected: confirmation page shows the same identifier.

15. Return to instructor context. On `/instructor/registration`, set mode to
    `Disabled`, cap to `12`, and save. Also toggle the default identifier
    style between `code` and `handle`.
    Expected: page shows `Registration updated`. When `handle` is selected,
    later self-enrolled students receive lower-case hyphenated handles using a
    union of blockchain and hacker-style terms, such as
    `validator-fork-ropper9`; when `code` is selected, students receive
    compact `QZ-XXXX-XXXX` IDs.

16. Open `/student/` in a fresh student browser context if available.
    Expected: page shows `Registration is closed`; attempting `/student/enroll`
    through the form should not issue a new identifier.

17. Return to instructor context and open `/instructor/roster-codes`.
    Generate one code with activation `Activate on first use`, then generate a
    second small batch with identifier style `handle`.
    Expected: page shows `Generated 1 roster codes` and one `QZ-XXXX-XXXX`
    identifier for code mode. In handle mode, generated roster identifiers are
    lower-case hyphenated handles using the blockchain/hacker term union. The
    page also shows a `Whole Roster` table with identifier, status, activation,
    created/used timestamps, deleted timestamp, and an `x` delete control for
    active roster items.
    Record it as `roster_identifier`.

18. On `/instructor/roster-codes`, import anonymous identifiers by pasting a
    comma/newline-separated list such as
    `QZ-7K4M-2P9D, QZ-8K4M-3P9D`, with activation `Activate on first use`.
    Expected: page shows `Imported 2 roster codes`, displays both normalized
    identifiers, does not ask for name/email/student ID, and a repeated import
    through `/instructor/api/roster-codes/import` reports already existing
    identifiers without creating a partial batch.
    Record one imported identifier as `imported_identifier`. Then open
    `/instructor/roster-codes/export.csv`.
    Expected: plain text contains `roster_identifier` and no real-world identity
    fields. The imported identifiers are also present.

19. In a fresh student context, open `/student/`, enter `roster_identifier`, and
    submit.
    Expected: confirmation page shows `roster_identifier`; `/student/session`
    returns source `roster_code` and status `active`. Repeat with
    `imported_identifier` and expect the same roster-code activation behavior.

20. In instructor context, open `/instructor/roster-codes`, press the `x`
    delete control next to `roster_identifier`, and submit the form.
    Expected: redirected back to roster page with `Roster identifier deleted`;
    the identifier remains visible in the `Whole Roster` table with status
    `revoked`, has no active delete control, and is omitted from
    `/instructor/roster-codes/export.csv` and `/instructor/roster-codes/print`.

21. In a fresh student context, attempt login with `roster_identifier`.
    Expected: HTTP 401 or page text `Identifier was not recognized`; no
    authenticated session is established.

22. In instructor context, open `/instructor/roster-codes/bulk-delete`.
    Expected: page H1 is `Bulk Delete Roster Codes`, the active imported
    identifiers are selectable with checkboxes, previously revoked identifiers
    are visible but disabled, and the page has shared instructor navigation.
    Select the imported identifiers and submit.
    Expected: redirected back to roster page with `Deleted N roster
    identifiers`; selected identifiers are shown as `revoked`, student login
    with those identifiers is denied, and active roster exports/print sheets no
    longer include them.

23. In instructor context, open `/instructor/ingest`.
    Expected: page H1 is `Ingest Quiz Banks`; it includes file, JSON, revision
    mapping, and import controls.

24. Open `/instructor/api/banks`.
    Expected: authenticated JSON contains a non-empty `banks` array when live
    quiz data has been seeded. One bank should have lesson ID
    `bitcoin_01_bf_bitcoin_origins_and_mechanics`.

25. Open `/instructor/banks`.
    Expected: page H1 is `Question Banks`, and the same Bitcoin lesson is
    visible as a link to the question browser. The `Questions` and `Hidden`
    table headers should not wrap, and each bank action should use concise
    `Delete` text with an accessible label that identifies the bank.

26. Open `/instructor/api/questions?lesson_id=bitcoin_01_bf_bitcoin_origins_and_mechanics&limit=5`.
    Expected: JSON `total` is greater than zero and `questions` contains
    multiple-choice items with effective tags.

27. Open `/instructor/questions?lesson_id=bitcoin_01_bf_bitcoin_origins_and_mechanics`.
    Expected: page H1 is `Question Browser`, shows matching question count, and
    includes stems from the Bitcoin Origins bank. The filter form should have
    `data-question-filter-form`, should fetch
    `/instructor/api/questions/filter-terms` once, and should attach
    suggestions to `lesson_id`, `lesson_title`, `topic`, `tag`,
    `hierarchy_section`, `hierarchy_lecture`, `difficulty_level`, and
    `question_type`. The `source` field should remain free-text. Typing in an
    autocomplete-enabled field should not trigger additional term-index network
    requests, and selecting a suggested canonical value should preserve the
    existing server-side filter semantics. In the tag field, type one accepted
    tag, a comma, and a prefix for a second tag; expected: suggestions match
    the current token after the comma rather than replacing the whole field.

    Also open `/instructor/api/questions/filter-terms`.
    Expected: authenticated JSON includes `schema_version`, `generated_at`,
    `revision`, and a `fields` map for the known-value question-browser
    filters plus a `banks` map keyed by lesson ID. Global records and per-bank
    records should contain `value`, `label`, and `count`; a per-bank tag list
    should include only tags available in that lesson bank. The payload should
    not include answers, explanations, student identifiers, attempts, or PII.
    Repeat the request with the returned `ETag` in `If-None-Match`.
    Expected: `304 Not Modified`.

28. From the question API result, open `/instructor/api/questions/<question_id>`.
    Expected: JSON includes stem, answer choices, at least one option with
    `is_correct: 1`, explanation, topic, difficulty, lesson block, tags, and
    source provenance.

29. Open `/instructor/questions/<question_id>`.
    Expected: page H1 contains the lesson/source question ID, the correct answer
    is visibly marked `correct`, explanation/metadata are visible, and active
    editable questions expose an `Edit question` link.

    For a disposable lesson, generate a hidden quiz before editing, open the
    question's edit form, change the stem, explanation, difficulty, topic,
    question-specific tags, and multiple-choice option text/correctness, then
    publish a new question version. Expected: the old question row is
    superseded, the new question detail renders at a different question ID,
    default question browsing and future quiz generation use the edited row,
    the pre-edit generated quiz snapshot remains unchanged, the edit audit
    event includes IDs/counts but not stems/options/answers, and full export
    includes `question_edit_batches`.

    Then open the pre-edit hidden generated quiz detail and use
    `Refresh question revisions`. Expected: the hidden quiz updates its
    snapshot to the latest active question revision, keeps the same generated
    quiz version ID, records a redacted `quiz_version.questions_refreshed`
    audit event, and still refuses refresh for published quizzes or any quiz
    version with existing attempts. Do not test or build a forced published
    quiz update path.

30. Open `/instructor/api/ingest/plan` with a same-lesson bank payload if the
    MCP runner supports POST/fetch from the page.
    Expected: response contains candidate matches with `match_reasons` such as
    `source_qid` or `question_stem_exact`. If the runner cannot POST JSON from
    the browser, mark this as tool-limited and rely on the Docker integration
    test for the planner.

    Also validate imported-content retirement on a disposable lesson or tag.
    Import or identify test-only quiz-bank content, open
    `/instructor/import-retirements`, verify the target control is a
    multi-select dropdown, switch between Lesson IDs and Tags, confirm the tag
    dropdown lists active tags, and use Select all/Select none. Type partial
    lesson/tag text into the dropdown filter and confirm it hides non-matching
    rows, preserves already checked hidden rows, restores all rows when the
    filter is cleared, and lets select-all/select-none operate only on visible
    filtered rows. Preview by exact lesson ID or effective tag and confirm the
    retirement. Expected:
    preview shows affected question, revision, bank, generated snapshot,
    attempt, and template-reference counts; the apply response records a
    retirement batch; selected content disappears from default bank/question
    browsing, generation, and autocomplete; old generated quiz details still
    render from immutable snapshots; full export includes
    `import_retirement_batches` and `question_retirements`; and re-ingesting
    the same retired lesson creates a new active pool.

    Also open `/instructor/banks`, click `Delete this bank` for a disposable
    or test-only bank, and confirm it routes to
    `/instructor/import-retirements?mode=lesson&targets=<lesson_id>` with that
    bank preselected. Expected: no content is retired until the preview and
    confirmation form is submitted.

31. Run the responsive UX smoke pass at desktop width and mobile width
    (`390x844` is sufficient for the mobile pass) on these routes:
    `/student/`, `/student/quizzes`, one in-progress student attempt,
    `/instructor/`, `/instructor/questions`, `/instructor/templates/new`,
    `/instructor/import-retirements`, `/instructor/roster-codes`, and
    `/instructor/metrics`.
    Expected: shared nav is reachable and horizontally scrollable on mobile,
    active top-level nav uses `aria-current="page"`, the skip link can receive
    focus, each page has `main#dynamic-labs-main`, primary buttons and inputs
    have touch-sized hit areas, tables do not force the whole viewport wider
    than the document, import-retirement dropdown options wrap without clipped
    counts, student pages do not expose instructor links, and no console, CSP,
    page, or unexpected network errors are observed.

32. Open `/instructor/templates`.
    Expected: page H1 is `Quiz Templates`; live seeded data should show
    `Browser MCP Template`.

33. Open `/instructor/templates/new`.
    Expected: page H1 is `New Quiz Template`; the form has lesson-bank rows
    with checkboxes and per-bank question-count inputs, a computed total
    question count, source-bank `Select all`/`Select none` controls,
    fallback topic/tag autocomplete, source-bank filter-mode controls,
    fallback excluded-topic and excluded-tag fields, per-source tag fields,
    per-source tag quota fields, per-source excluded-topic and excluded-tag
    fields, selection-policy and result-policy dropdowns, hover/help
    disclosure blocks for both policy groups, question-order and answer-order
    dropdowns defaulting to
    `random_per_attempt`, order-mode help explaining `fixed`, `random_once`,
    and `random_per_attempt`, and timer help stating that `-1`, `0`, or blank
    means no timer.
    The raw `criteria_json` textarea should be inside an advanced disclosure
    and should not be the primary workflow.

34. Create a disposable template from the HTML builder by selecting one or two
    lesson banks, assigning positive per-bank question counts, selecting a
    selection policy and result policy from the dropdowns, setting timer
    minutes to `-1`, and leaving most source banks on `Use fallback`.
    Customize one source bank with a tag filter and tag quotas, for example
    `reading:1, slides:1` if those tags exist in the chosen bank. In the
    source tag field, type one tag, a comma, and a second tag prefix; expected:
    the autocomplete suggestions come from that specific bank's term database
    and insert only the current comma-delimited token.
    Add one fallback excluded tag or topic, and add one source-specific
    excluded tag or topic on the customized source.
    Expected: save redirects to the template detail page; the saved template
    has `question_count` equal to the sum of selected lesson-bank counts,
    stores `timer_minutes` as no timer/null, and stores criteria
    `schema_version: 2` with `source_rules`. The saved template should retain
    `question_order_mode: random_per_attempt` and
    `option_order_mode: random_per_attempt` unless the tester deliberately
    changed those dropdowns. Inherited sources should have `filter_mode:
    inherit`; customized sources should have `filter_mode: override`,
    source-specific tags, per-tag quotas, and source-specific excluded filters.

35. Open `/instructor/templates/<template_id>/edit` for that template.
    Expected: the selected lesson banks remain checked, per-bank counts are
    prefilled, customized source filters and tag quotas are retained, timer
    minutes displays `-1`, excluded-topic and excluded-tag filters are
    retained, and the selected selection/result/order policies remain
    selected.

36. Open `/instructor/api/templates`.
    Expected: authenticated JSON contains non-archived templates and includes
    `Browser MCP Template`.

37. Open `/instructor/api/templates/preview` with either `template_id` for
    `Browser MCP Template` or an equivalent criteria payload if the MCP runner
    supports POST/fetch from the page.
    Expected: preview JSON has `eligible_pool_size > 0`, `question_count`, count
    rollups, and no warnings for the seeded template. For a schema-version-2
    disposable template, preview JSON should also include per-source preview
    entries under `source_rules`, each with a source lesson ID, requested count,
    eligible pool size, and any source-specific warnings.
    For a payload that sets `excluded_topics` or `excluded_tags`, the eligible
    pool should drop questions matching those topics or effective tags without
    mutating the selected lesson banks.

38. Generate a hidden quiz version from `Browser MCP Template` using
    `/instructor/api/templates/<template_id>/generate` and a fixed seed such as
    `browser-phase-8-seed`; from the template detail page, the seed field
    should already be populated with a random value and the `Regenerate seed`
    button should replace it before submission.
    Expected: response status `201`, visibility `hidden`, `template_id` is the
    template ID, `generation_snapshot.random_seed` matches the supplied seed,
    `generation_snapshot.selected_question_ids` has `question_count` entries,
    `generation_snapshot.question_order_mode` and
    `generation_snapshot.option_order_mode` match the template or submitted
    overrides, and generated quizzes use `random_per_attempt` by default for
    both question order and answer order. Snapshot options should not assume
    the correct answer is first; correctness must be carried by the snapshot
    option identity/flag after shuffling.
    `question_order_policy` and `option_order_policy` should remain compatible
    with the student attempt payload, with `random_per_attempt` producing
    per-attempt question and answer shuffles and `random_once` producing one
    generated order shared by all student attempts.
    Snapshot questions include stems, options, correct flags, explanations,
    tags, topics, difficulty, lesson block, and source metadata. For
    schema-version-2 templates, `generation_snapshot.source_allocations`
    should show each source lesson, requested count, selected question IDs, and
    tag quota allocations; selected questions must satisfy the customized
    source tag quotas.

39. Generate again from the same template using the same fixed seed.
    Expected: a different quiz-version ID is created, while
    `generation_snapshot.selected_question_ids`, generated question order, and
    generated snapshot option order match the first generated version when the
    same seed and the same template order modes are used.

40. Open `/instructor/quiz-versions`.
    Expected: page H1 is `Generated Quizzes`; it includes the generated quiz
    title, visibility `hidden`, and the generated question count.

41. Open `/instructor/quiz-versions/<version_id>` and
    `/instructor/api/quiz-versions/<version_id>`.
    Expected: instructor detail shows `Snapshot Questions`, correct answers,
    generation seed, eligible-pool size, question order, answer order, and
    immutable snapshot metadata. The quiz editor shows a UTC server clock,
    calendar buttons for `Available from` and `Available until`, separate UTC
    hour/minute selectors, and the correct snapshot answer is highlighted with
    a green outline plus a green `correct` label.

42. Open `/instructor/quiz-versions/<version_id>/preview` and
    `/instructor/api/quiz-versions/<version_id>/preview`.
    Expected: instructor preview works while the quiz is still hidden, shows
    correct answers and explanations, and does not create a student attempt.

43. Update administrative metadata for the generated quiz through
    `/instructor/api/quiz-versions/<version_id>` or the detail form.
    Expected: title, description, `available_from`, `available_until`, and
    instructor notes update in place. The detail form must block an
    `Available until` value that is equal to or earlier than `Available from`;
    the API must also return `400` with a clear `available_until must be after
    available_from` error for that invalid window. Content and grading-critical
    settings such as attempts, timer, result policy, question order, option
    order, generation snapshot, questions, and options remain immutable.

44. Open `/student/` and `/student/quizzes` before publication.
    Expected: student-facing pages do not show template titles, hidden imported
    banks, hidden generated quiz titles, correct answers, explanations, or
    source provenance.

45. Publish the generated quiz with
    `/instructor/api/quiz-versions/<version_id>/publish` or the detail form.
    Expected: response/detail visibility is `published`, `published_at` is set,
    and the quiz remains otherwise immutable.

46. In an authenticated student context, open `/student/quizzes` and
    `/student/api/quizzes`.
    Expected: the published in-window quiz title, description, timer, and
    question count are visible. Student payloads must not include snapshot
    questions, correct-answer flags, explanations, source provenance,
    instructor notes, hidden generated versions, archived generated versions,
    or out-of-window generated versions.

47. Hide the generated quiz with
    `/instructor/api/quiz-versions/<version_id>/hide`.
    Expected: visibility becomes `hidden`; the quiz disappears from
    `/student/quizzes`.

48. Publish again, then set a future `available_from` or past
    `available_until`.
    Expected: visibility may be `published`, but the quiz is not student-visible
    because it is outside the availability window.

49. Archive the generated quiz with
    `/instructor/api/quiz-versions/<version_id>/archive`.
    Expected: visibility becomes `archived`, `archived_at` is set, attempts are
    not deleted, and the quiz stays hidden from students.

50. Start the published quiz from `/student/quizzes` or
    `/student/api/quizzes/<version_id>/start`.
    Expected: response creates an `in_progress` attempt, records question and
    option order, and returns a student-safe payload with question text and
    option text but no correct flags, correct option IDs, explanations, source
    provenance, or grading metadata.

51. Start the same quiz again while the attempt is still `in_progress`.
    Expected: response resumes the same attempt ID. Reopen `/student/quizzes`
    and confirm the visible action is `Resume quiz`, not only `Start quiz`.

52. Open `/student/attempts/<attempt_id>` and
    `/student/api/attempts/<attempt_id>`.
    Expected: the same redacted attempt payload is visible and no instructor
    metadata leaks. Every multiple-choice option on the HTML attempt page is
    rendered as its own `.quiz-answer-option-row` inside a
    `.quiz-answer-options` group, with readable spacing and a visible selected
    row state after an option is chosen.

53. Auto-save a multiple-choice answer with
    `/student/api/attempts/<attempt_id>/answers/<question_id>`.
    Expected: response status `200`; saved answer is reflected on the attempt;
    duplicate save for the same question updates the same answer row. Also
    change an option on the HTML attempt page and confirm the top-right
    `Saved` check-mark toast appears briefly, then reload the attempt and verify
    the selected option remains checked.

54. Attempt to save an option from a different question to the first question.
    Expected: request is rejected with `400` and a clear validation error. Run
    this in the main student context only if the browser issue tooling can treat
    the expected 400 as non-fatal; otherwise isolate it in a disposable context.

55. Try to submit the attempt through
    `/student/api/attempts/<attempt_id>/submit` with at least one required
    question unanswered, then try the same through the HTML form when practical.
    Expected: the API request is rejected with `422`, the API includes
    `missing_question_ids`, the attempt remains `in_progress`, no final score is
    recorded, and the HTML submit is rejected with `400` while the attempt page
    shows the natural status text
    `Quiz in progress`, a concise error, and incomplete questions highlighted
    in red. The page should not visibly render raw status strings such as
    `Status: in_progress`.

56. Submit the fully answered attempt through
    `/student/api/attempts/<attempt_id>/submit`.
    Expected: multiple-choice-only quiz reaches `graded`; duplicate submit
    returns the same final state without changing saved answers or creating a
    new attempt. Reopen `/student/quizzes` and confirm a `View results` link is
    shown for the final attempt while no instructor bank metadata appears.
    Open `/student/attempts/<attempt_id>/results`; expected: the result status
    uses natural text such as `Graded`, selected/correct answers have a green
    `.quiz-result-option-correct` outline, selected incorrect answers have a
    red `.quiz-result-option-selected-incorrect` outline, and the page does not
    visibly render raw status strings such as `Status: graded`.

57. In a second authenticated student context, try to fetch the first
    student's attempt.
    Expected: `404`/not found; no attempt payload is exposed.

58. Try to start the same one-attempt quiz again after the first student has
    submitted it.
    Expected: request is rejected with `400` and `attempt limit reached`.

59. In instructor context, grant the first student one extra attempt with
    `/instructor/api/quiz-versions/<version_id>/attempt-grants`, passing the
    student identifier, `extra_attempts: 1`, and a short reason.
    Expected: response status `201`, grant payload records the quiz version,
    student ID, `extra_attempts`, and effective allowance.

60. Start the same quiz again in the first student context.
    Expected: a new attempt is created with `attempt_number: 2`, while the
    prior submitted attempt remains final.

61. Void the first submitted attempt from instructor context with
    `/instructor/api/attempts/<attempt_id>/void`.
    Expected: response status `200`, attempt status is `voided`, `voided_at` is
    set, and the instructor quiz detail page lists the attempt controls without
    deleting the attempt.

62. Generate or reuse a timed published quiz with `timer_minutes: 1`, start it
    as a student, open `/student/attempts/<attempt_id>`, and save one answer.
    For deterministic validation, force that attempt's `deadline_at` into the
    past through the app container database before the next browser request.
    Expected: the attempt page shows a sticky top-bar `Time Remaining` live
    countdown sourced from the server-rendered `deadline_at`; the countdown
    remains visible while scrolling, updates in the browser, and disables the
    HTML submit button when it reaches zero. The next
    `/student/api/attempts/<attempt_id>` request lazily finalizes the attempt
    as `expired`; saved multiple-choice answers are auto-graded, unanswered
    questions count as zero, and another start is rejected with
    `attempt limit reached` until an instructor grant is made.

63. Grant an extra attempt for the expired timed quiz and start it again.
    Expected: a new attempt is created after expiration with the next
    `attempt_number`.

64. Start another timed attempt, force its `deadline_at` into the past through
    the app container database, run the expiration tick in the app container
    (`python -m flask --app app:create_app shell` or an equivalent app-context
    command that calls `finalize_expired_attempts()`), then fetch the attempt in
    the student browser context.
    Expected: worker/tick finalization marks it `expired` before the lazy
    browser fetch, and repeated fetches/ticks do not create duplicate
    expiration audit events.

65. In instructor context, ingest a small synthetic bank containing a written
    question, generate and publish a written quiz with
    `result_policy: score_after_release`, then start and submit it in the
    student context.
    Expected: submitted attempt status is `needs_grading`; student
    `/student/api/attempts/<attempt_id>/results` shows submitted status but
    `score_visible: false`.

66. Open `/instructor/grading` and `/instructor/api/grading/written`.
    Expected: the written response appears in the instructor queue, associated
    with only the anonymous student identifier, attempt number, quiz title,
    question stem, response text, and point controls.

67. Grade the queued written answer with
    `/instructor/api/attempt-answers/<answer_id>/grade`.
    Expected: points are recorded, original `written_response` is preserved,
    attempt status changes from `needs_grading` to `graded`, and score fields
    update. Student result remains hidden until release because the policy is
    `score_after_release`.

68. Release results with
    `/instructor/api/quiz-versions/<version_id>/release-results`.
    Expected: quiz version receives `results_released_at` and
    `results_released_by`; an audit event is recorded; student result now shows
    score only and still does not expose explanations or review answers.

69. Generate and publish another written quiz with
    `result_policy: score_and_answers_after_grading`, submit it, grade it, and
    open `/student/attempts/<attempt_id>/results`.
    Expected: after grading, score and review details are visible without an
    explicit release. The result view includes the student's written response
    and explanation, and it remains session-bound to that student.

70. Start a timed written quiz, save a written answer, force `deadline_at` into
    the past through the app container, let it expire, then grade the saved
    written answer from the instructor queue.
    Expected: grading fills points and score while the attempt status remains
    `expired`.

71. Open `/instructor/metrics` in the instructor context.
    Expected: page H1 is `Instructor Metrics`; the filter form exposes
    latest/all mode, status checkboxes, optional quiz-version filtering through
    a generated-quiz dropdown, and an explicit `Include voided` control. The
    report includes in-page navigation links for filters, class summary, quiz
    summary, student summary, topics, tags, item analysis, visualization ideas,
    and metric ideas. The class summary distinguishes missing, in-progress,
    expired, voided, submitted, needs-grading, and graded attempt states, with
    voided excluded by default. The page includes brainstorm sections for useful
    future visualizations and additional metrics.

72. Open `/instructor/api/metrics`.
    Expected: JSON contains `filters`, `class_summary`, `quiz_summary`,
    `student_summary`, `topic_rollups`, `tag_rollups`, `source_rollups`, and
    `item_analysis`. `filters.rollup_attempts` states that the default uses
    the latest non-voided attempt per student per quiz version, and
    `filters.voided_policy` states that voided attempts are excluded by
    default. Student records use anonymous identifiers only; no raw
    `"student_id"` field appears in the JSON payload.

73. Open `/instructor/api/metrics?mode=all&include_voided=1`.
    Expected: JSON says `mode: all`, `include_voided: true`, and all-attempt
    analysis includes any previously voided attempts in the relevant status
    counts without deleting or mutating audit history.

74. Open `/instructor/api/metrics?statuses=graded` and, if a timed expired
    attempt exists, `/instructor/api/metrics?statuses=expired`.
    Expected: status filtering changes selected-attempt counts and leaves the
    response explicit about which statuses are included. Expired latest
    attempts count finalized unanswered questions as zero unless expired
    attempts are filtered out.

75. Inspect `item_analysis` in `/instructor/api/metrics`.
    Expected: multiple-choice items show attempts per question, correct count,
    percent correct, and option/distractor selection counts. Written items
    separately show saved, graded, ungraded, and expired-ungraded counts.

76. Inspect `topic_rollups`, `tag_rollups`, and `source_rollups` in
    `/instructor/api/metrics`.
    Expected: topic and tag rollups identify score percentages across
    normalized answer records. Source rollups are grouped by `lesson_block`,
    `specific_source_lesson`, and `specific_source_reading`.

77. Open `/instructor/api/metrics/students/<student_identifier>?mode=all&include_voided=1`
    for a student with more than one attempt if available, then open the HTML
    route `/instructor/metrics/students/<student_identifier>?mode=all&include_voided=1`.
    Expected: the detail view shows all matching attempts for the anonymous
    identifier, including expired and voided attempts when included, and keeps
    archived quiz-version snapshots and historical source-question metadata
    visible.

78. Open `/instructor/exports`.
    Expected: page H1 is `Instructor Exports`; links are present for class JSON
    report, class CSV report, class print report, full-engine JSON export,
    SQLite backup path, and printable roster-code sheet.

79. Open `/instructor/api/exports/reports/class.json` and
    `/instructor/api/exports/reports/class.csv`.
    Expected: JSON has `schema_version`, `exported_at`, `scope: class`,
    `filters`, and report data. CSV has stable headers beginning with
    `record_type` and includes class, quiz, student, topic/tag/source, and item
    rows where live data exists.

80. Open student, quiz-version, and template scoped report routes with live IDs:
    `/instructor/api/exports/reports/student.json?student_identifier=<identifier>`,
    `/instructor/api/exports/reports/quiz-version.csv?quiz_version_id=<version_id>`,
    and `/instructor/api/exports/reports/template.json?template_id=<template_id>`.
    Expected: student reports use anonymous identifiers only and no raw
    `"student_id"` key; quiz-version CSV includes item-analysis rows; template
    JSON lists generated quiz versions and their aggregate metrics.

81. Open print-friendly report views:
    `/instructor/exports/reports/class/print`,
    `/instructor/exports/reports/student/print?student_identifier=<identifier>`,
    `/instructor/exports/reports/quiz-version/print?quiz_version_id=<version_id>`,
    and `/instructor/exports/reports/template/print?template_id=<template_id>`.
    Expected: each route returns HTML with a report H1, operational tables, and
    anonymous identifiers only. No raw `"student_id"` text or PII prompts
    appear.

82. Open `/instructor/roster-codes/print`.
    Expected: printable HTML sheet lists active roster identifiers only and
    omits identifiers deleted/revoked through roster management. It must not
    include real names, email addresses, institutional IDs, or student PII.

83. Open `/instructor/api/exports/quiz-banks/<bank_id>.json` for a live bank.
    Expected: JSON is ingest-compatible, including lesson metadata, hierarchy,
    tags, questions, correct answer/incorrect answers for multiple-choice
    items, and written question fields where present.

84. Open `/instructor/api/exports/full.json`.
    Expected: JSON has top-level `schema_version`, `exported_at`, and `tables`.
    Tables include students, cohorts, roster-code batches, banks, revisions,
    revision relationships, questions, options, tags, import retirement
    batches, question retirements, templates, generated quiz snapshots, result
    release state, attempts, answers, grants, audit events, and settings.

85. POST the full export payload back to
    `/instructor/api/imports/full/validate` using same-origin `fetch()`.
    Expected: response is `200` with `valid: true`. This validation route must
    not mutate the live database. The destructive import route
    `/instructor/api/imports/full` is covered by Docker integration tests
    against a fresh database, not run against the live browser database.

86. Open `/instructor/api/backup-info`.
    Expected: JSON reports the configured SQLite database path, the
    `QUIZ_ENGINE_DB_PATH` environment variable, the default `quiz_engine_data`
    Docker volume, and a retention note that attempts, audit events, generated
    quiz versions, and snapshots are not silently deleted.

87. Check shared dynamic-labs theme and chrome on representative pages:
    `/student/`, `/student/quizzes`, `/instructor`, `/instructor/ingest`,
    `/instructor/metrics`, `/instructor/exports`, and
    `/instructor/exports/reports/class/print`.
    Expected: every HTML page includes `/static/dynamic-labs-theme.css`, a
    `.dynamic-labs-shell` header, the `Dynamic Labs` brand, dark shared-theme
    colors matching the existing instructor-login visual language, and
    role-appropriate navigation. Instructor pages should expose the same links
    for dashboard, ingest, banks, questions, templates, generated quizzes,
    registration, roster, grading, metrics, exports, and student view, with no
    duplicate dashboard-local instructor navigation. Student
    pages should expose home and quizzes, but no instructor links. Printable report
    pages should keep the brand/header and hide only navigation in print media.

88. Repeat the theme/chrome check in a narrow mobile viewport for
    `/student/`, `/student/quizzes`, `/student/attempts/<attempt_id>`,
    `/instructor`, and `/instructor/exports`.
    Expected: the shared header and navigation wrap or scroll cleanly, forms
    remain readable, quiz answer rows are individually tappable, and no page has
    incoherent text/control overlap or document-level horizontal overflow.

89. Read browser console/error/network buffers.
    Expected: no uncaught JavaScript errors, no failed same-origin app requests,
    and no unexpected redirects other than the redirects described above.

## Run Log Template

- Base URL:
- Browser MCP session/context:
- Screenshots captured:
- Seed data status:
- `open_identifier`:
- `roster_identifier`:
- Health/static result:
- Student enrollment result:
- Student logout/login result:
- Instructor dev login result:
- Instructor dashboard result:
- Registration-disabled result:
- Roster generation/export result:
- Roster first-use activation result:
- Revocation denial result:
- Roster bulk delete result:
- Ingest page result:
- Bank browser/API result:
- Question browser/API result:
- Question detail result:
- Re-ingest planner result:
- Template list/API result:
- Template preview result:
- Quiz generation result:
- Quiz regeneration determinism result:
- Generated quiz list/detail result:
- Instructor preview result:
- Admin metadata update result:
- Publication result:
- Student published quiz list/API result:
- Availability-window result:
- Hide/archive result:
- Attempt start/resume result:
- Student quiz-list resume/result link result:
- Attempt payload redaction result:
- Auto-save result:
- Tamper rejection result:
- Submission result:
- Cross-student isolation result:
- Attempt limit result:
- Extra attempt grant result:
- Attempt voiding result:
- Timed lazy expiration result:
- Expiration worker/tick result:
- Written grading queue result:
- Manual written grading result:
- Result release result:
- Result policy visibility result:
- Expired written grading result:
- Metrics dashboard result:
- Metrics API default/latest result:
- Metrics all-attempt/voided result:
- Metrics status-filter result:
- Metrics item analysis result:
- Metrics topic/tag/source result:
- Metrics student detail result:
- Exports page result:
- Class report export result:
- Scoped report export result:
- Print-friendly report result:
- Printable roster sheet result:
- Ingest-compatible bank export result:
- Full-engine export result:
- Full-export validation result:
- Backup info result:
- Shared theme/chrome result:
- Mobile theme result:
- Student-hidden content check:
- PII prompt check:
- Console/network errors:
- Deviations or failures:

Fill in the template in the pull request or issue the run is for; this playbook keeps no run history.
