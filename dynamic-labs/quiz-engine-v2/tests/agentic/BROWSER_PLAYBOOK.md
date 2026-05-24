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
   `QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=test-header` is acceptable.
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

## Last Run

### Latest Focused Run - Roster Density And Metrics Implementation

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  Chromium context `context-46557fb80eed`, page `page-ccaeb7f5ea53`.
- Scope: focused validation for roster table density and replacing metrics
  idea lists with implemented metrics/visualization sections.
- Docker validation: rebuilt the Docker image, ran focused metrics, student
  identity, and UI-page tests with `19 passed`, then ran the full Docker suite
  with `203 passed`.
- Roster result: `/instructor/roster-codes` returned `200`; `Status` and
  `Action` headers used compact non-wrapping column styling, timestamp headers
  and cells used `roster-time-column`, and timestamp cells rendered at 11px with
  constrained width.
- Metrics page result: `/instructor/metrics` returned `200`; the report nav
  linked to `#visualizations`, `#dimensions`, and `#operations`; old
  `Metric Ideas` and `Visualization Ideas` text was absent; the page rendered
  concrete sections for score distribution, completion funnel, item difficulty
  scatter data, template metrics, and equity checks.
- Metrics API result: `/instructor/api/metrics` returned populated
  `difficulty_rollups`, `question_type_rollups`, `visualizations`, and
  `metric_catalog` keys. Visualization keys included status-by-quiz, score
  distribution, quiz-average bars, completion funnel, topic/tag heatmaps, item
  difficulty scatter, distractor charts, written grading status, student
  progress matrix, and attempt timing by quiz. The JSON contained no raw
  `"student_id"` key.
- Console/network errors: no unexpected console or page errors were observed;
  `get_csp_violations` returned no violations.
- Deviations or failures: none.

### Latest Focused Run - Bank And Template Builder UI

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  Chromium context `context-4e2f6a91ec99`, page `page-404280dd8d46`.
- Scope: focused validation for compact Bank table columns/actions and
  template-builder source-bank bulk selection plus topic/tag autocomplete.
- Docker validation: rebuilt the Docker image, ran focused question-bank,
  template, and UI-page tests with `14 passed`, then ran the full Docker suite
  with `203 passed`.
- Banks page result: `/instructor/banks` returned `200`; `Questions` and
  `Hidden` headers used `table-column-compact` with computed
  `white-space: nowrap`, and bank actions rendered as concise `Delete` links
  with bank-specific accessible labels.
- Template builder result: `/instructor/templates/new` returned `200`; the
  page exposed source-bank `Select all`/`Select none` buttons, 42 source-bank
  checkboxes, topic and tag inputs connected to `template-topic-terms` and
  `template-tag-terms` datalists, and live topic/tag options including
  `bitcoin` and `proof-of-work`.
- Source-bank bulk result: `Select all` checked all 42 source banks, filled
  blank quotas with `1`, and updated both visible and hidden question-count
  totals to `42`; `Select none` cleared all source banks and reset the totals
  to `0`.
- Console/network errors: no unexpected console or page errors were observed;
  `get_csp_violations` returned no violations.
- Deviations or failures: none.

### Latest Focused Run - Retire Imports Hidden Rows Fix

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  Chromium context `context-95e8357f8de7`, page `page-8d93a84e0410`.
- Scope: focused validation for the retire-imports dropdown after adding a
  global `[hidden] { display: none !important; }` rule so filtered rows are
  actually removed from layout even when row classes define flex/grid display.
- Docker validation: rebuilt the Docker image, ran focused import-retirement
  and UI-page tests with `8 passed`, then ran the full Docker suite with
  `202 passed`.
- Rendered filtering result: filtering lesson banks to `origins` on
  `/instructor/import-retirements` produced one logical visible row and one
  rendered visible row:
  `bitcoin_01_bf_bitcoin_origins_and_mechanics`. Hidden sample rows reported
  computed `display: none`, zero client rects, and zero height.
- Status result: filter status read `1 of 42 shown; 0 selected.`, matching the
  single rendered row.
- Console/network errors: no unexpected console or page errors were observed;
  `get_csp_violations` returned no violations.
- Deviations or failures: none.

### Latest Focused Run - Retire Imports Filter

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  Chromium context `context-8ddc1cf9bfd7`, page `page-e84c3947b6ec`.
- Scope: focused validation for the retire-imports lesson-bank dropdown
  filter after changing it to grep-like client-side filtering with persistent
  checkbox state.
- Docker validation: rebuilt the Docker image, ran focused import-retirement
  and UI-page tests with `8 passed`, then ran the full Docker suite with
  `202 passed`.
- Health/static result: app container rebuilt and reachable at
  `10.2.0.10:8000`.
- Filter persistence result: `/instructor/import-retirements` returned `200`
  with 42 lesson-bank rows in the live data. Filtering to `origins` showed only
  `bitcoin_01_bf_bitcoin_origins_and_mechanics`; selecting it persisted after
  filtering to `transactions`, where
  `bitcoin_02_bf_transactions_and_mining` could also be selected. Clearing the
  filter restored all 42 rows with both selections still checked.
- Visible-row bulk action result: with `origins` visible, `Select all` selected
  only the visible origin row. With `transactions` visible, `Select all` added
  only the visible transaction row. `Select none` while filtered to
  `transactions` cleared only the transaction row and left the hidden origin
  selection checked.
- Status result: the dropdown status text updated to show visible and selected
  counts, for example `42 of 42 shown; 2 selected.`
- Console/network errors: no unexpected console or page errors were observed;
  `get_csp_violations` returned no violations.
- Deviations or failures: none.

### Latest Focused Run - UX/UI Responsive Cleanup

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  Chromium context `context-d4c97419c688`, page `page-c1dd38f3c4ff`, after a
  prior same-scope metrics/table check in context `context-acebd6b940d0`.
- Scope: focused validation for the comprehensive UX/UI review item: shared
  chrome current-section state, skip-link/main-content behavior, mobile nav,
  touch-sized controls, mobile table scrolling, import-retirement target
  dropdown styling, and student/instructor nav separation. The broader app
  surface remains covered by Docker integration tests and prior browser runs
  below.
- Docker validation: rebuilt the Docker image, ran focused theme/UI tests with
  `8 passed`, then ran the full Docker suite with `202 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dashboard result: `/instructor/` returned `200`, H1 `Instructor
  Dashboard`, exactly one shared `Instructor navigation`, `Dashboard` marked
  with `aria-current="page"`, skip link targeting `#dynamic-labs-main`, and
  `main#dynamic-labs-main` present. No non-checkbox controls were under the
  shared minimum size.
- Mobile import-retirements result: at `390x844`,
  `/instructor/import-retirements` returned `200`, `Retire Imports` was the
  active nav item, the instructor nav scrolled inside the header
  (`overflow-x: auto`), document width stayed at viewport width, target menus
  rendered inside the viewport, and select-all/select-none controls remained
  usable.
- Mobile student result: `/student/` returned `200` with `Student navigation`,
  `Home` marked current, no `href="/instructor..."` links, document width equal
  to viewport width, and visible button/input controls at 44px height.
- Mobile metrics result: before the final skip-link target robustness patch,
  `/instructor/metrics` returned `200`, `Metrics` was marked current, two
  metrics tables scrolled inside their own containers (`overflow-x: auto`)
  while the document width stayed at viewport width, and no non-checkbox
  controls were below the minimum touch target. The final patch only changed
  skip-link target selection for templates that already define a custom main
  ID; Docker regression tests cover both default and custom-main cases.
- Accessibility/focus result: focus order began with `Skip to content`, then
  shared chrome navigation, then page controls in the first focused pass.
  `get_csp_violations` returned no violations after the final browser rerun.
- Console/network errors: no unexpected console or page errors were observed
  in the focused run.
- Deviations or failures: none.

### Latest Focused Run - Navigation Cleanup

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop context `context-b63be2e0f9d5`, page `page-291935a6d394`. The page
  was closed after validation.
- Scope: focused validation for removing duplicate dashboard-local instructor
  navigation and removing instructor links from student chrome. The broader app
  surface remains covered by Docker integration tests and prior browser runs
  below.
- Docker validation: rebuilt the Docker image, ran focused theme/UI tests with
  `5 passed`, then ran the full Docker suite with `190 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dashboard result: dev login as `browser-teacher` succeeded.
  `/instructor/` returned `200`, H1 `Instructor Dashboard`, exactly one shared
  `Instructor navigation` header, expected shared instructor links, and no
  `aria-label="Instructor sections"` dashboard-local duplicate nav.
- Student navigation result: `/student/` and `/student/quizzes` returned `200`
  with shared student navigation and no `href="/instructor...` links.
- Console/network errors: no CSP violations were reported. No unexpected
  network errors were observed in the focused run.
- Deviations or failures: none.

### Latest Focused Run - Structured Template Builder Controls

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-2a765c58df67`, page
  `page-8e3c9dfbe0b1`. The page was closed after validation.
- Scope: focused validation for the newly implemented template-builder UI:
  lesson-bank selection with per-bank counts, selection/result policy
  dropdowns and help disclosures, no-timer `-1` UI handling, and edit-page
  prefill. The broader app surface remains covered by Docker integration tests
  and prior browser runs below.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM state, form POST/fetch responses,
  page outline, viewport overflow, API payloads, and CSP checks were captured
  through MCP.
- Docker validation: rebuilt the Docker image, ran focused template/UI tests
  with `16 passed`, then ran the full Docker suite with `190 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dev login result: same-origin POST to `/instructor/dev/login`
  established the `browser-teacher` instructor session and returned the
  instructor dashboard.
- Template builder page result: `/instructor/templates/new` returned `200`,
  H1 `New Quiz Template`, shared instructor navigation, sections for `Lesson
  Banks`, `Selection Criteria`, and `Policies`, 38 live lesson-bank checkbox
  rows, selection-policy and result-policy `<select>` controls, help
  disclosures for both policy groups, timer help stating `Use -1, 0, or blank
  for no timer.`, and the raw criteria editor under `Advanced criteria JSON`.
- Structured template create result: submitted disposable template
  `Browser Structured Template 1779322060158` selecting
  `bitcoin_01_bf_bitcoin_origins_and_mechanics` with quota `1` and
  `bitcoin_02_bf_transactions_and_mining` with quota `2`, selection policy
  `balanced_difficulty`, result policy `score_and_answers_after_release`,
  attempt limit `2`, and timer `-1`. Save redirected to template detail
  `/instructor/templates/3`.
- Persisted template API result: `/instructor/api/templates/3` returned
  `question_count: 3`, `timer_minutes: null`,
  `selection_policy: balanced_difficulty`,
  `result_policy: score_and_answers_after_release`, and criteria containing
  both lesson IDs plus `quotas.lesson_ids` `{lesson1: 1, lesson2: 2}`.
- Template edit prefill result: `/instructor/templates/3/edit` returned `200`
  with both selected lesson banks checked, quota inputs prefilled as `1` and
  `2`, timer minutes displayed as `-1`, and the saved selection/result policies
  selected.
- Shared theme/chrome result: the template-builder page included shared
  instructor navigation and had no document-level horizontal overflow in the
  desktop viewport.
- PII prompt check: template create/edit pages did not prompt for email, full
  name, student ID, institutional ID, or similar PII.
- Console/network errors: no CSP violations were reported. No unexpected
  network errors were observed in the focused run.
- Deviations or failures: none.

### Latest Focused Run - Roster Whole-Page View And Delete Controls

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-91a647d90481`, page
  `page-f155ba0db606`; headless student contexts
  `context-79e28da59222`, `context-cf9241d67624`, and
  `context-12dcb8a44485` for activation and deleted-login denial checks.
- Scope: focused validation for the newly implemented roster whole-page table,
  per-row `x` delete control, and bulk-delete checkbox page. The broader app
  surface remains covered by Docker integration tests and prior browser runs
  below.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM state, form POST/fetch responses,
  page outlines, viewport overflow, network status, and CSP checks were
  captured through MCP.
- Docker validation: rebuilt the Docker image, ran focused roster/student/UI
  tests with `23 passed`, then ran the full Docker suite with `188 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dev login result: same-origin POST to `/instructor/dev/login`
  established the `browser-teacher` instructor session and returned the
  instructor dashboard.
- Disposable roster data: generated roster identifier `QZ-SF2U-JV5D` and
  imported disposable identifiers `QZ-SVJC-4JKG` and `QZ-L7YG-PECS`.
- Roster generation/export result: `/instructor/roster-codes` returned `200`,
  showed H1 `Roster Codes`, the import form, export/print links, the
  `Bulk delete roster identifiers` link, and a `Whole Roster` table. The table
  included roster identifiers, status/activation/timestamp columns, and `x`
  buttons with accessible labels such as
  `Delete roster identifier QZ-SF2U-JV5D`. Active roster export contained the
  disposable identifiers before deletion and no real-world identity fields.
- Roster first-use activation result: fresh student login with
  `QZ-SF2U-JV5D` succeeded; `/student/session` returned
  `authenticated: true`, source `roster_code`, and status `active`.
- Individual roster delete result: POSTing the row delete form for
  `QZ-SF2U-JV5D` returned `200` after redirect and showed
  `Roster identifier deleted`. The identifier remained visible in `Whole
  Roster` with status `revoked` and no active delete button, while
  `/instructor/roster-codes/export.csv` and `/instructor/roster-codes/print`
  omitted it.
- Revocation denial result: fresh student login attempts with deleted
  identifiers returned the expected `401` denial, and unauthenticated
  `/student/session` also returned `401`.
- Roster bulk delete result: `/instructor/roster-codes/bulk-delete` returned
  `200`, H1 `Bulk Delete Roster Codes`, shared instructor navigation, a
  `Select all active roster identifiers` checkbox, enabled checkboxes for
  `QZ-SVJC-4JKG` and `QZ-L7YG-PECS`, and a disabled checkbox for previously
  deleted `QZ-SF2U-JV5D`. Bulk POST returned `200` after redirect with
  `Deleted 2 roster identifiers`; both imported identifiers were shown as
  `revoked` in the response and omitted from active roster export.
- Shared theme/chrome result: roster and bulk-delete pages included shared
  instructor navigation. The bulk-delete page had no document-level horizontal
  overflow in the desktop viewport.
- PII prompt check: roster and bulk-delete pages did not prompt for email, full
  name, student ID, institutional ID, or similar PII.
- Console/network errors: no CSP violations were reported. The only negative
  network statuses in the focused run were expected `401` responses for
  student login/session checks after identifiers were deleted.
- Deviations or failures: none.

### Latest Focused Run - Hidden Quiz Question Refresh

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-0c8069734369`, page
  `page-057413c928bd`. The context was closed after validation.
- Scope: focused validation for refreshing a hidden generated quiz to latest
  active question revisions after instructor source-question edits, while
  confirming published/attempted quiz versions remain locked.
- Docker validation: rebuilt the Docker image, ran focused refresh tests with
  `3 passed`, then ran the full suite with `199 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Disposable data: imported lesson `browser_refresh_1779328650429`, generated
  hidden quiz version `20` with snapshot stem `Browser refresh original?`, then
  edited source question `477` into active question `478`.
- Hidden refresh result: the hidden quiz detail exposed `Refresh question
  revisions`; after refresh, `/instructor/api/quiz-versions/20` still returned
  version `20` with visibility `hidden`, selected source question ID `478`,
  snapshot stem `Browser refresh edited?`, and option text `Edited correct`.
- Audit result: the latest `quiz_version.questions_refreshed` audit event
  recorded old/new source question IDs and position, and did not include the
  edited stem or option text.
- Lockout result: Docker integration tests confirmed published quiz versions
  and quiz versions with attempts reject refresh. No forced published update
  path was built.
- Console/network errors: the clean validation context had no recent console or
  page errors; CSP violations were empty.
- Deviations or failures: none.

### Previous Focused Run - Metrics Dashboard Selector And Navigation

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-4fedafba63b6`, page
  `page-02df1731a6e2`. The context was closed after validation.
- Scope: focused validation for the instructor metrics dashboard HTML surface.
- Docker validation: rebuilt the Docker image, ran focused metrics tests with
  `1 passed`, then ran the full suite with `196 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dev login result: same-origin POST to `/instructor/dev/login`
  established the instructor session.
- Metrics page result: `/instructor/metrics` returned `200` with H1
  `Instructor Metrics`, an authenticated generated-quiz dropdown for
  `quiz_version_id`, and 20 dropdown choices including `All quiz versions` and
  live quiz versions such as `#19 · Browser edit after quiz 2 · hidden · 1 questions`.
- Navigation result: the report exposed in-page links for Filters, Class
  Summary, Quiz Summary, Student Summary, Topics, Tags, Item Analysis,
  Visualization Ideas, and Metric Ideas.
- Brainstorm result: the page rendered `Visualization Ideas` and `Metric Ideas`
  sections with chart/metric suggestions including status stacked bars, score
  histograms, topic/tag heat maps, item difficulty scatter plots, completion
  funnels, score statistics, per-student trends, per-item metrics, operational
  grading metrics, and longitudinal metrics.
- Filter result: selecting quiz version `19` submitted
  `/instructor/metrics?mode=latest&quiz_version_id=19...`; the dropdown
  preserved the selected quiz version and the quiz summary scoped to
  `Browser edit after quiz 2`.
- PII prompt check: the metrics page body did not include raw `student_id`
  text.
- Console/network errors: no recent console or page errors were reported; CSP
  violations were empty.
- Deviations or failures: none.

### Previous Focused Run - Instructor Question Editing

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-ad84842a0841`, page
  `page-a1c77e17f3b7`. The context was closed after validation.
- Scope: focused validation for the instructor question edit form/API, forward
  question revisions, unchanged historical generated snapshots, future
  generation using the edited row, redacted audit metadata, autocomplete cache
  refresh, and full-export inclusion of `question_edit_batches`.
- Docker validation: rebuilt the Docker image and ran the full suite with
  `196 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Disposable data: imported lesson `browser_edit_1779325373269` with one
  multiple-choice question, generated hidden quiz version `17` before editing,
  then edited source question `475` through the instructor edit form.
- Question detail result: the original question detail page exposed
  `Edit question`; after publishing the edit, the browser redirected to new
  active question `476`, which showed `Browser edited question text?` and the
  edited correct option.
- Revision result: full export showed original question `475` as `superseded`
  with `superseded_at` set, and new question `476` with
  `revises_question_id=475`.
- Active pool result: `/instructor/api/questions?lesson_id=browser_edit_1779325373269`
  returned total `1` with active ID `476`.
- Historical snapshot result: pre-edit quiz version `17` still showed snapshot
  stem `Browser original question text?`.
- Export/audit result: full export included one `question_edit_batches` row.
  The latest `question.edited` audit event did not include the edited stem or
  edited option text.
- Console/network errors: the clean validation context had no recent console or
  page errors; CSP violations were empty.
- Deviations or failures: none.

### Previous Focused Run - Import Retirement By Lesson Or Tag

- Date: 2026-05-21
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-9b322c28f773`, page
  `page-4e56e2a4d4d7`. The context was closed after validation.
- Scope: focused validation for the imported-content retirement UI, including
  lesson/tag target dropdowns, Select all/Select none controls, preview/confirm
  safety, and the `/instructor/banks` `Delete this bank` link into the same
  flow.
- Docker validation: rebuilt the Docker image, ran focused retirement tests
  with `5 passed`, then ran the full Docker suite with `192 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dev login result: same-origin POST to `/instructor/dev/login`
  established the `browser-teacher` instructor session.
- Disposable data: imported lesson `browser_dropdown_retire_1779323426859`
  with two multiple-choice questions and active tags including
  `dropdown-retire`.
- Bank delete entry result: `/instructor/banks` listed the disposable lesson
  with a `Delete this bank` link to
  `/instructor/import-retirements?mode=lesson&targets=browser_dropdown_retire_1779323426859`.
- Prefill result: clicking the bank link opened `Delete Imported Content` with
  the lesson target preselected and the summary showing `1 selected`; no
  content was retired at this point.
- Dropdown result: switching to Tags showed the tag panel with 946 active tag
  choices and included `dropdown-retire`. Select all changed the summary to
  `946 selected`; Select none changed it back to `0 selected`.
- Preview result: switching back to Lesson IDs and submitting preview showed
  mode `lesson`, target `browser_dropdown_retire_1779323426859`, 2 questions,
  1 revision, 1 bank, 0 generated quiz snapshots, 0 attempts, 0 active template
  references, and the affected bank row marked for archive.
- Retirement apply result: submitting the confirm form returned `200` with
  `Retired 2 imported questions`; after apply,
  `/instructor/api/questions?lesson_id=browser_dropdown_retire_1779323426859`
  returned total `0`, and `/instructor/api/banks` no longer listed the lesson.
- Console/network errors: no recent console or page errors were reported; CSP
  violations were empty.
- Deviations or failures: none.

### Previous Focused Run - Import Retirement By Lesson Or Tag

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-6a9be4713270`, page
  `page-c632fb6dba33`. The context was closed after validation.
- Scope: focused validation for the newly implemented imported-content
  retirement workflow. The broader app surface remains covered by Docker
  integration tests and prior browser runs below.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM state, fetch responses, network
  traffic, and CSP checks were captured through MCP.
- Docker validation: rebuilt the Docker image, ran focused retirement,
  ingest, question-browser, generation, export/import, and schema tests with
  `41 passed`, then ran the full Docker suite with `184 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dev login result: same-origin POST to `/instructor/dev/login`
  established the `browser-teacher` instructor session and returned the
  instructor dashboard.
- Disposable data: imported lesson `browser_retire_1779318878075` with two
  multiple-choice questions, then generated hidden quiz version `14` from that
  lesson before retirement.
- Retirement preview result:
  `/instructor/api/import-retirements/preview` for mode `lesson` returned
  `200` with 2 selected questions, 1 revision, 1 bank, 2 generated quiz
  snapshot references, 0 attempts, 0 active template references, and no question
  stem text in the preview payload.
- Retirement apply result: `/instructor/api/import-retirements` returned `201`
  with status `retired`. After apply,
  `/instructor/api/questions?lesson_id=browser_retire_1779318878075` returned
  total `0`, and `/instructor/api/banks` no longer listed the retired lesson.
- Historical snapshot result:
  `/instructor/api/quiz-versions/14` still returned `200` with 2 immutable
  snapshot questions from the generated quiz.
- Full export result: `/instructor/api/exports/full.json` included
  `import_retirement_batches` and `question_retirements`; live counts after the
  disposable retirement were 1 retirement batch and 2 question retirements.
- Re-ingest result: reimporting the same lesson with one replacement question
  returned `200`; default question browsing returned total `1`, `/instructor/api/banks`
  listed the lesson again, and the autocomplete term index included the
  reactivated lesson.
- HTML route result: `/instructor/import-retirements` returned `200`, H1
  `Delete Imported Content`, mode/targets/reason controls, the shared
  `Retire Imports` instructor nav link, and no PII prompts.
- Console/network errors: resource summary for the final HTML page showed one
  stylesheet. No CSP violations were reported.
- Deviations or failures: none.

### Previous Focused Run - Question Filter Autocomplete

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-4093d9bac27e`, page
  `page-cd14162d72a7`. The context was closed after validation.
- Scope: focused validation for the newly implemented instructor
  question-browser autocomplete term index. The broader app surface remains
  covered by Docker integration tests and the prior browser run below.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM state, fetch responses, network
  traffic, and CSP checks were captured through MCP.
- Docker validation: rebuilt the Docker image, ran focused tests for the term
  cache/question browser/UI pages with `9 passed`, then ran the full Docker
  suite with `175 passed`.
- Health/static result: `/healthz` returned `200`; the rebuilt app container
  was reachable at `10.2.0.10:8000`.
- Instructor dev login result: same-origin POST to `/instructor/dev/login`
  established the `browser-teacher` instructor session and returned the
  instructor dashboard.
- Question browser/autocomplete result:
  `/instructor/questions?lesson_id=bitcoin_01_bf_bitcoin_origins_and_mechanics`
  returned `200`, H1 `Question Browser`, and `13 matching questions`. The form
  exposed `data-question-filter-form` and
  `data-filter-terms-url=/instructor/api/questions/filter-terms`.
- Autocomplete field result: native datalist IDs were attached to `lesson_id`,
  `lesson_title`, `topic`, `tag`, `hierarchy_section`, `hierarchy_lecture`,
  `difficulty_level`, and `question_type`; `source` had no autocomplete marker.
  Live option counts were 37 lesson IDs, 37 lesson titles, 7 topics, 943 tags,
  10 sections, 70 lectures, 5 difficulty levels, and 2 question types.
- No per-keystroke network result: typing `bit` into the `topic` field kept the
  `/instructor/api/questions/filter-terms` resource count at `1`; no new term
  index requests were made while typing.
- Filter semantics result: setting the suggested canonical topic value
  `bitcoin` and submitting the form navigated to
  `/instructor/questions?...topic=bitcoin...`, returned
  `55 matching questions`, and listed Bitcoin bank question links.
- Term index API result: `/instructor/api/questions/filter-terms` returned
  `200` with `schema_version: 1`, `generated_at`, `revision`, all expected
  fields, 37 lesson terms, and 943 tag terms. Repeating the request with the
  returned `ETag` in `If-None-Match` returned `304`.
- Security/content result: the term-index payload did not include
  `correct_answer`, `explanation`, `student_id`, `email`, `full name`, or
  `attempt_answers`.
- Console/network errors: resource summary showed one stylesheet and three
  fetches for the page and explicit API checks; no CSP violations were
  reported.
- Deviations or failures: none.

### Previous Browser Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-6edbf4c503cd`, headless narrow student
  context `context-edd17a63b631`, and one discarded narrow student context
  `context-5f825cfba1c4`. All contexts were closed after validation.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM state, form submissions, fetch
  responses, network traffic, and CSP checks were captured through MCP.
- Seed data status: live database from prior phases remained present in the
  Docker volume.
- `open_identifier`: not part of this import validation. A discarded browser
  context accidentally clicked open registration and issued `QZ-9PU3-4LY4`;
  the validation was rerun in a fresh context through the explicit login form.
- `roster_identifier`: no generated roster identifier was created in this run.
- `imported_identifier`: imported identifiers were `QZ-9X7M-8P6D` and
  `QZ-8W6N-7Q5D`; `QZ-8W6N-7Q5D` was used for first-use activation validation.
- Health/static result: app container was rebuilt and reachable at
  `10.2.0.10`; static theme CSS loaded on validated instructor and student
  pages.
- Student enrollment result: not intentionally repeated in this import run.
- Student logout/login result: fresh student login with lower-case
  `qz-8w6n-7q5d` succeeded and normalized to `QZ-8W6N-7Q5D`.
- Instructor dev login result: `/instructor/dev/login` established test
  instructor session `browser-teacher` and redirected to `/instructor/`.
- Instructor dashboard result: `/instructor/` returned `200` with instructor
  dashboard and shared chrome.
- Registration-disabled result: not repeated in this import run.
- Roster generation/export result: `/instructor/roster-codes` rendered the
  import form with paste textarea, UTF-8 file input, and activation selector.
  Posting pasted identifiers `QZ-9X7M-8P6D` and `qz-8w6n-7q5d` to
  `/instructor/roster-codes/import` returned `200`, showed
  `Imported 2 roster codes`, and displayed normalized identifiers
  `QZ-9X7M-8P6D` and `QZ-8W6N-7Q5D`. Export
  `/instructor/roster-codes/export.csv` returned `200` and included both
  imported identifiers with no identity fields.
- Roster first-use activation result: fresh student login using imported
  `qz-8w6n-7q5d` returned confirmation for `QZ-8W6N-7Q5D`; `/student/session`
  returned `authenticated: true`, source `roster_code`, and status `active`.
- Revocation denial result: unchanged from earlier run and covered by Docker
  suite.
- Ingest page result: unchanged from earlier run and covered by Docker suite.
- Bank browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question detail result: unchanged from earlier run and covered by Docker
  suite.
- Re-ingest planner result: unchanged from earlier run and covered by Docker
  suite.
- Template list/API result: unchanged from earlier run and covered by Docker
  suite.
- Template preview result: unchanged from earlier run and covered by Docker
  suite.
- Quiz generation result: unchanged from earlier run and covered by Docker
  suite.
- Quiz regeneration determinism result: unchanged from earlier run and covered
  by Docker suite.
- Generated quiz list/detail result: unchanged from earlier run and covered by
  Docker suite.
- Instructor preview result: unchanged from earlier run and covered by Docker
  suite.
- Admin metadata update result: unchanged from earlier run and covered by
  Docker suite.
- Publication result: unchanged from earlier run and covered by Docker suite.
- Student published quiz list/API result: unchanged from earlier run and covered
  by Docker suite.
- Availability-window result: unchanged from earlier run and covered by Docker
  suite.
- Hide/archive result: unchanged from earlier run and covered by Docker suite.
- Attempt start/resume result: unchanged from earlier run and covered by Docker
  suite.
- Student quiz-list resume/result link result: unchanged from earlier run and
  covered by Docker suite.
- Attempt payload redaction result: unchanged from earlier run and covered by
  Docker suite.
- Auto-save result: unchanged from earlier run and covered by Docker suite.
- Tamper rejection result: duplicate import through
  `/instructor/api/roster-codes/import` with existing `QZ-9X7M-8P6D` returned
  expected `400` without creating a partial batch. Docker integration tests also
  cover invalid formats, duplicate payload values, existing identifiers, and
  unauthenticated API rejection.
- Submission result: unchanged from earlier run and covered by Docker suite.
- Cross-student isolation result: unchanged from earlier run and covered by
  Docker suite.
- Attempt limit result: unchanged from earlier run and covered by Docker suite.
- Extra attempt grant result: unchanged from earlier run and covered by Docker
  suite.
- Attempt voiding result: unchanged from earlier run and covered by Docker
  suite.
- Timed lazy expiration result: unchanged from earlier run and covered by
  Docker suite.
- Expiration worker/tick result: unchanged from earlier run and covered by
  Docker suite.
- Written grading queue result: unchanged from earlier run and covered by
  Docker suite.
- Manual written grading result: unchanged from earlier run and covered by
  Docker suite.
- Result release result: unchanged from earlier run and covered by Docker
  suite.
- Result policy visibility result: unchanged from earlier run and covered by
  Docker suite.
- Expired written grading result: unchanged from earlier run and covered by
  Docker suite.
- Metrics dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Metrics API default/latest result: unchanged from earlier run and covered by
  Docker suite.
- Metrics all-attempt/voided result: unchanged from earlier run and covered by
  Docker suite.
- Metrics status-filter result: unchanged from earlier run and covered by
  Docker suite.
- Metrics item analysis result: unchanged from earlier run and covered by
  Docker suite.
- Metrics topic/tag/source result: unchanged from earlier run and covered by
  Docker suite.
- Metrics student detail result: unchanged from earlier run and covered by
  Docker suite.
- Exports page result: unchanged from earlier run and covered by Docker suite.
- Class report export result: unchanged from earlier run and covered by Docker
  suite.
- Scoped report export result: unchanged from earlier run and covered by Docker
  suite.
- Print-friendly report result: unchanged from earlier run and covered by
  Docker suite.
- Printable roster sheet result: unchanged from earlier run and covered by
  Docker suite.
- Ingest-compatible bank export result: unchanged from earlier run and covered
  by Docker suite.
- Full-engine export result: unchanged from earlier run and covered by Docker
  suite.
- Full-export validation result: unchanged from earlier run and covered by
  Docker suite.
- Backup info result: unchanged from earlier run and covered by Docker suite.
- Shared theme/chrome result: roster import page and student login confirmation
  used shared dynamic-labs theme and navigation.
- Mobile theme result: narrow student login confirmation for imported
  identifier loaded without visible overflow in the checked DOM state.
- Student-hidden content check: no quiz/answer metadata was involved in this
  import validation.
- PII prompt check: roster import page and imported-identifier student login
  did not prompt for email, full name, student ID, or institutional ID.
- Console/network errors: no CSP violations were reported. Network traffic
  included expected `200` page/stylesheet/import/export/session responses and
  the expected `400` duplicate-import API response.
- Deviations or failures: this run intentionally implemented only one backlog
  item, Import Anonymous Identifiers. The first student-context click selected
  open registration instead of return login; the activation check was rerun in
  a fresh context by submitting the `/student/login` form directly.

## Previous Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop student context `context-4b08c2cb75cf` and headless narrow
  unauthenticated security-check context `context-d18ac03a49e6`. Both contexts
  were closed after validation.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM state, computed styles, fetch
  responses, network traffic, and CSP checks were captured through MCP.
- Seed data status: live database from prior phases remained present in the
  Docker volume, including published quiz version `3`.
- `open_identifier`: auto-save toast run issued `QZ-JCTZ-JYBC`.
- `roster_identifier`: not generated in this auto-save toast run.
- Health/static result: app container was rebuilt and reachable at
  `10.2.0.10`; static theme CSS loaded on validated student pages.
- Student enrollment result: open registration issued `QZ-JCTZ-JYBC`; browser
  local storage matched the issued identifier.
- Student logout/login result: not repeated in this auto-save toast run.
- Instructor dev login result: not repeated in this auto-save toast run.
- Instructor dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Registration-disabled result: not repeated in this auto-save toast run.
- Roster generation/export result: not repeated in this auto-save toast run.
- Roster first-use activation result: not repeated in this auto-save toast run.
- Revocation denial result: not repeated in this auto-save toast run.
- Ingest page result: unchanged from earlier run and covered by Docker suite.
- Bank browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question detail result: unchanged from earlier run and covered by Docker
  suite.
- Re-ingest planner result: unchanged from earlier run and covered by Docker
  suite.
- Template list/API result: unchanged from earlier run and covered by Docker
  suite.
- Template preview result: unchanged from earlier run and covered by Docker
  suite.
- Quiz generation result: unchanged from earlier run and covered by Docker
  suite.
- Quiz regeneration determinism result: unchanged from earlier run and covered
  by Docker suite.
- Generated quiz list/detail result: unchanged from earlier run and covered by
  Docker suite.
- Instructor preview result: unchanged from earlier run and covered by Docker
  suite.
- Admin metadata update result: unchanged from earlier run and covered by
  Docker suite.
- Publication result: unchanged from earlier run and covered by Docker suite.
- Student published quiz list/API result: `/student/quizzes` showed published
  quiz version `3`, which was started for the validation attempt.
- Availability-window result: unchanged from earlier run and covered by Docker
  suite.
- Hide/archive result: unchanged from earlier run and covered by Docker suite.
- Attempt start/resume result: starting version `3` created attempt `28` with
  five multiple-choice questions.
- Student quiz-list resume/result link result: unchanged from earlier run and
  covered by Docker suite.
- Attempt payload redaction result: student attempt page and API payload stayed
  redacted; DOM text did not expose correct-answer, source-lesson, or
  explanation metadata.
- Auto-save result: changing the first multiple-choice row on HTML attempt `28`
  triggered a same-origin `PUT /student/api/attempts/28/answers/11` with only
  `question_id: 11` and `selected_option_id: 43` in the JSON payload. The API
  returned `200`, the saved answer included `saved_at:
  2026-05-20T21:18:32+00:00`, and the page displayed a fixed-position
  top-right `Saved ✓` toast. After roughly 1.7 seconds the toast was hidden and
  no longer had the visible class. Reloading `/student/attempts/28` preserved
  the checked option value `43`. A duplicate same-session answer save returned
  `200`. A disposable unauthenticated context attempting the same save returned
  expected `401`.
- Tamper rejection result: unchanged from earlier run and covered by Docker
  suite.
- Submission result: unchanged from earlier run and covered by Docker suite.
- Cross-student isolation result: unchanged from earlier run and covered by
  Docker suite.
- Attempt limit result: unchanged from earlier run and covered by Docker suite.
- Extra attempt grant result: unchanged from earlier run and covered by Docker
  suite.
- Attempt voiding result: unchanged from earlier run and covered by Docker
  suite.
- Timed lazy expiration result: unchanged from earlier run and covered by
  Docker suite.
- Expiration worker/tick result: unchanged from earlier run and covered by
  Docker suite.
- Written grading queue result: unchanged from earlier run and covered by
  Docker suite.
- Manual written grading result: unchanged from earlier run and covered by
  Docker suite.
- Result release result: unchanged from earlier run and covered by Docker
  suite.
- Result policy visibility result: unchanged from earlier run and covered by
  Docker suite.
- Expired written grading result: unchanged from earlier run and covered by
  Docker suite.
- Metrics dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Metrics API default/latest result: unchanged from earlier run and covered by
  Docker suite.
- Metrics all-attempt/voided result: unchanged from earlier run and covered by
  Docker suite.
- Metrics status-filter result: unchanged from earlier run and covered by
  Docker suite.
- Metrics item analysis result: unchanged from earlier run and covered by
  Docker suite.
- Metrics topic/tag/source result: unchanged from earlier run and covered by
  Docker suite.
- Metrics student detail result: unchanged from earlier run and covered by
  Docker suite.
- Exports page result: unchanged from earlier run and covered by Docker suite.
- Class report export result: unchanged from earlier run and covered by Docker
  suite.
- Scoped report export result: unchanged from earlier run and covered by Docker
  suite.
- Print-friendly report result: unchanged from earlier run and covered by
  Docker suite.
- Printable roster sheet result: unchanged from earlier run and covered by
  Docker suite.
- Ingest-compatible bank export result: unchanged from earlier run and covered
  by Docker suite.
- Full-engine export result: unchanged from earlier run and covered by Docker
  suite.
- Full-export validation result: unchanged from earlier run and covered by
  Docker suite.
- Backup info result: unchanged from earlier run and covered by Docker suite.
- Shared theme/chrome result: student attempt page included the shared
  dynamic-labs theme CSS, rendered `data-auto-save-attempt` on the attempt
  form, per-question `data-save-url` attributes, and the `quiz-save-toast`
  status element.
- Mobile theme result: the disposable narrow context loaded `/student/`
  successfully; this run did not repeat a full narrow attempt layout check
  because the changed behavior was validated on the desktop attempt and narrow
  layout remained covered by the previous row-layout run and Docker suite.
- Student-hidden content check: no instructor bank metadata, source lesson,
  explanations, or correct-answer fields were exposed during the student
  attempt validation.
- PII prompt check: no email, full name, student ID, or institutional ID prompts
  appeared on the validated student pages. The auto-save payload did not
  include a student identifier.
- Console/network errors: no CSP violations were reported. Network traffic
  included expected positive `200` page/stylesheet/API requests, expected
  start-form `302` redirect to the attempt, and the expected `401` response for
  the disposable unauthenticated save check.
- Deviations or failures: this run intentionally implemented only one backlog
  item, Student Auto-Save Confirmation Toast.

## Earlier Row-Layout Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop student context `context-0827fbaf74b4` and headless narrow viewport
  student context `context-a952ef7692a3`. Both contexts were closed after
  validation.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM layout, computed styles, network,
  and CSP checks were captured through MCP.
- Seed data status: live database from prior phases remained present in the
  Docker volume, including published quiz version `3`.
- `open_identifier`: desktop row-layout run issued `QZ-DSRL-K44Q`; narrow
  viewport row-layout run issued `QZ-HZPC-HZNS`.
- `roster_identifier`: not generated in this row-layout run.
- Health/static result: app container was rebuilt and reachable at
  `10.2.0.10`; static theme CSS loaded on validated student pages.
- Student enrollment result: open registration issued identifiers in both
  desktop and narrow viewport contexts; browser local storage matched the
  issued identifier in each context.
- Student logout/login result: not repeated in this row-layout run.
- Instructor dev login result: not repeated in this row-layout run.
- Instructor dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Registration-disabled result: not repeated in this row-layout run.
- Roster generation/export result: not repeated in this row-layout run.
- Roster first-use activation result: not repeated in this row-layout run.
- Revocation denial result: not repeated in this row-layout run.
- Ingest page result: unchanged from earlier run and covered by Docker suite.
- Bank browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question detail result: unchanged from earlier run and covered by Docker
  suite.
- Re-ingest planner result: unchanged from earlier run and covered by Docker
  suite.
- Template list/API result: unchanged from earlier run and covered by Docker
  suite.
- Template preview result: unchanged from earlier run and covered by Docker
  suite.
- Quiz generation result: unchanged from earlier run and covered by Docker
  suite.
- Quiz regeneration determinism result: unchanged from earlier run and covered
  by Docker suite.
- Generated quiz list/detail result: unchanged from earlier run and covered by
  Docker suite.
- Instructor preview result: unchanged from earlier run and covered by Docker
  suite.
- Admin metadata update result: unchanged from earlier run and covered by
  Docker suite.
- Publication result: unchanged from earlier run and covered by Docker suite.
- Student published quiz list/API result: `/student/quizzes` showed published
  quiz version `3`, which was started for both validation attempts.
- Availability-window result: unchanged from earlier run and covered by Docker
  suite.
- Hide/archive result: unchanged from earlier run and covered by Docker suite.
- Attempt start/resume result: starting version `3` created desktop attempt
  `26` and narrow viewport attempt `27`; each rendered five multiple-choice
  questions.
- Student quiz-list resume/result link result: unchanged from earlier run and
  covered by Docker suite.
- Attempt payload redaction result: student attempt pages stayed redacted; DOM
  text did not expose correct-answer, source-lesson, or explanation metadata.
- Auto-save result: unchanged from earlier run and covered by Docker suite.
- Tamper rejection result: unchanged from earlier run and covered by Docker
  suite.
- Submission result: unchanged from the previous incomplete-submit run and
  covered by Docker suite.
- Cross-student isolation result: unchanged from earlier run and covered by
  Docker suite.
- Attempt limit result: unchanged from earlier run and covered by Docker suite.
- Extra attempt grant result: unchanged from earlier run and covered by Docker
  suite.
- Attempt voiding result: unchanged from earlier run and covered by Docker
  suite.
- Timed lazy expiration result: unchanged from earlier run and covered by
  Docker suite.
- Expiration worker/tick result: unchanged from earlier run and covered by
  Docker suite.
- Written grading queue result: unchanged from earlier run and covered by
  Docker suite.
- Manual written grading result: unchanged from earlier run and covered by
  Docker suite.
- Result release result: unchanged from earlier run and covered by Docker
  suite.
- Result policy visibility result: unchanged from earlier run and covered by
  Docker suite.
- Expired written grading result: unchanged from earlier run and covered by
  Docker suite.
- Metrics dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Metrics API default/latest result: unchanged from earlier run and covered by
  Docker suite.
- Metrics all-attempt/voided result: unchanged from earlier run and covered by
  Docker suite.
- Metrics status-filter result: unchanged from earlier run and covered by
  Docker suite.
- Metrics item analysis result: unchanged from earlier run and covered by
  Docker suite.
- Metrics topic/tag/source result: unchanged from earlier run and covered by
  Docker suite.
- Metrics student detail result: unchanged from earlier run and covered by
  Docker suite.
- Exports page result: unchanged from earlier run and covered by Docker suite.
- Class report export result: unchanged from earlier run and covered by Docker
  suite.
- Scoped report export result: unchanged from earlier run and covered by Docker
  suite.
- Print-friendly report result: unchanged from earlier run and covered by
  Docker suite.
- Printable roster sheet result: unchanged from earlier run and covered by
  Docker suite.
- Ingest-compatible bank export result: unchanged from earlier run and covered
  by Docker suite.
- Full-engine export result: unchanged from earlier run and covered by Docker
  suite.
- Full-export validation result: unchanged from earlier run and covered by
  Docker suite.
- Backup info result: unchanged from earlier run and covered by Docker suite.
- Shared theme/chrome result: student attempt pages included the shared
  dynamic-labs theme CSS. Every multiple-choice question rendered one
  `.quiz-answer-options` group, and each answer rendered as a
  `.quiz-answer-option-row` with `.quiz-answer-option-input` and
  `.quiz-answer-option-text`.
- Mobile theme result: narrow viewport `390x844` attempt `27` rendered five
  `.quiz-answer-options` groups and twenty `.quiz-answer-option-row` elements;
  all rows computed to `display: flex`, stayed inside the parent width, and
  produced `docOverflow: 0`.
- Student-hidden content check: no instructor bank metadata, source lesson,
  explanations, or correct-answer fields were exposed during the desktop or
  narrow viewport student attempt validation.
- PII prompt check: no email, full name, student ID, or institutional ID prompts
  appeared on the validated student pages.
- Console/network errors: no CSP violations were reported. Network traffic
  included expected positive `200` page/stylesheet requests and expected
  start-form `302` redirects to attempts; no unexpected error responses were
  observed.
- Deviations or failures: this run intentionally implemented only one backlog
  item, Quiz Answer Option Row Layout. A default headed context launch was
  rejected by the browser tool because no X server was available; the narrow
  viewport validation was rerun successfully with `headless: true`.

## Earlier Incomplete-Submit Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop student context `context-8002e82268ae`. The context was closed after
  validation.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM, API response, network, and CSP
  checks were captured through MCP.
- Seed data status: live database from prior phases remained present in the
  Docker volume, including published quiz version `3`.
- `open_identifier`: incomplete-submit run issued `QZ-NHRF-SS2N`.
- `roster_identifier`: not generated in this incomplete-submit run.
- Health/static result: app container was rebuilt and reachable at
  `10.2.0.10`; static theme CSS loaded on validated student pages.
- Student enrollment result: open registration issued `QZ-NHRF-SS2N`; browser
  local storage matched the issued identifier.
- Student logout/login result: not repeated in this incomplete-submit run.
- Instructor dev login result: not repeated in this incomplete-submit run.
- Instructor dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Registration-disabled result: not repeated in this incomplete-submit run.
- Roster generation/export result: not repeated in this incomplete-submit run.
- Roster first-use activation result: not repeated in this incomplete-submit
  run.
- Revocation denial result: not repeated in this incomplete-submit run.
- Ingest page result: unchanged from earlier run and covered by Docker suite.
- Bank browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question detail result: unchanged from earlier run and covered by Docker
  suite.
- Re-ingest planner result: unchanged from earlier run and covered by Docker
  suite.
- Template list/API result: unchanged from earlier run and covered by Docker
  suite.
- Template preview result: unchanged from earlier run and covered by Docker
  suite.
- Quiz generation result: unchanged from earlier run and covered by Docker
  suite.
- Quiz regeneration determinism result: unchanged from earlier run and covered
  by Docker suite.
- Generated quiz list/detail result: unchanged from earlier run and covered by
  Docker suite.
- Instructor preview result: unchanged from earlier run and covered by Docker
  suite.
- Admin metadata update result: unchanged from earlier run and covered by
  Docker suite.
- Publication result: unchanged from earlier run and covered by Docker suite.
- Student published quiz list/API result: `/student/quizzes` showed published
  quiz version `3`, which was started for the validation attempt.
- Availability-window result: unchanged from earlier run and covered by Docker
  suite.
- Hide/archive result: unchanged from earlier run and covered by Docker suite.
- Attempt start/resume result: starting version `3` created attempt `25` with
  five multiple-choice questions.
- Student quiz-list resume/result link result: unchanged from earlier run and
  covered by Docker suite.
- Attempt payload redaction result: student attempt payload stayed redacted.
- Auto-save result: unchanged from earlier run and covered by Docker suite.
- Tamper rejection result: unchanged from earlier run and covered by Docker
  suite.
- Submission result: incomplete API submit with only question `11` answered
  returned expected `422` and `missing_question_ids`; a subsequent HTML submit
  with only the first question selected returned expected `400`, kept
  natural `Quiz in progress` status text, rendered alert text
  `answer all questions before submitting`, highlighted four
  `.quiz-question-incomplete` items, and showed four `Answer required.` rows.
  Fetching `/student/api/attempts/25` after the failed submit showed
  `in_progress` and zero saved answers. A final complete API submit returned
  `200` with status `graded` and five answered questions.
- Cross-student isolation result: unchanged from earlier run and covered by
  Docker suite.
- Attempt limit result: unchanged from earlier run and covered by Docker suite.
- Extra attempt grant result: unchanged from earlier run and covered by Docker
  suite.
- Attempt voiding result: unchanged from earlier run and covered by Docker
  suite.
- Timed lazy expiration result: unchanged from earlier run and covered by
  Docker suite.
- Expiration worker/tick result: unchanged from earlier run and covered by
  Docker suite.
- Written grading queue result: unchanged from earlier run and covered by
  Docker suite.
- Manual written grading result: unchanged from earlier run and covered by
  Docker suite.
- Result release result: unchanged from earlier run and covered by Docker
  suite.
- Result policy visibility result: unchanged from earlier run and covered by
  Docker suite.
- Expired written grading result: unchanged from earlier run and covered by
  Docker suite.
- Metrics dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Metrics API default/latest result: unchanged from earlier run and covered by
  Docker suite.
- Metrics all-attempt/voided result: unchanged from earlier run and covered by
  Docker suite.
- Metrics status-filter result: unchanged from earlier run and covered by
  Docker suite.
- Metrics item analysis result: unchanged from earlier run and covered by
  Docker suite.
- Metrics topic/tag/source result: unchanged from earlier run and covered by
  Docker suite.
- Metrics student detail result: unchanged from earlier run and covered by
  Docker suite.
- Exports page result: unchanged from earlier run and covered by Docker suite.
- Class report export result: unchanged from earlier run and covered by Docker
  suite.
- Scoped report export result: unchanged from earlier run and covered by Docker
  suite.
- Print-friendly report result: unchanged from earlier run and covered by
  Docker suite.
- Printable roster sheet result: unchanged from earlier run and covered by
  Docker suite.
- Ingest-compatible bank export result: unchanged from earlier run and covered
  by Docker suite.
- Full-engine export result: unchanged from earlier run and covered by Docker
  suite.
- Full-export validation result: unchanged from earlier run and covered by
  Docker suite.
- Backup info result: unchanged from earlier run and covered by Docker suite.
- Shared theme/chrome result: incomplete-submit HTML error page included shared
  dynamic-labs theme CSS and preserved student chrome.
- Mobile theme result: unchanged from earlier run and covered by Docker suite.
- Student-hidden content check: no instructor bank metadata or correct-answer
  fields were exposed during the student attempt validation.
- PII prompt check: no email, full name, student ID, or institutional ID prompts
  appeared on the validated student pages.
- Console/network errors: no CSP violations were reported. Network traffic
  included the expected `422` API response and `400` HTML response for
  incomplete submit checks;
  all positive page and stylesheet requests returned `200` or expected
  start-form `302`.
- Deviations or failures: this run intentionally implemented only one backlog
  item, Student Incomplete-Answer Submit Guard.

## Earlier Timer Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop student context `context-ef79efd0f325`. The context was closed after
  validation.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM, timer text, network, and CSP checks
  were captured through MCP.
- Seed data status: live database from prior phases remained present in the
  Docker volume, including timed published quiz versions `8` and `9`.
- `open_identifier`: timer run issued `QZ-2YP8-2LLT`.
- `roster_identifier`: not generated in this timer run.
- Health/static result: app container was rebuilt and reachable at
  `10.2.0.10`; static theme CSS loaded on validated student pages.
- Student enrollment result: open registration issued `QZ-2YP8-2LLT`; browser
  local storage matched the issued identifier.
- Student logout/login result: not repeated in this timer run.
- Instructor dev login result: not repeated in this timer run.
- Instructor dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Registration-disabled result: not repeated in this timer run.
- Roster generation/export result: not repeated in this timer run.
- Roster first-use activation result: not repeated in this timer run.
- Revocation denial result: not repeated in this timer run.
- Ingest page result: unchanged from earlier run and covered by Docker suite.
- Bank browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question detail result: unchanged from earlier run and covered by Docker
  suite.
- Re-ingest planner result: unchanged from earlier run and covered by Docker
  suite.
- Template list/API result: unchanged from earlier run and covered by Docker
  suite.
- Template preview result: unchanged from earlier run and covered by Docker
  suite.
- Quiz generation result: unchanged from earlier run and covered by Docker
  suite.
- Quiz regeneration determinism result: unchanged from earlier run and covered
  by Docker suite.
- Generated quiz list/detail result: unchanged from earlier run and covered by
  Docker suite.
- Instructor preview result: unchanged from earlier run and covered by Docker
  suite.
- Admin metadata update result: unchanged from earlier run and covered by
  Docker suite.
- Publication result: unchanged from earlier run and covered by Docker suite.
- Student published quiz list/API result: `/student/quizzes` showed timed
  published quiz choices with `1 minutes` labels.
- Availability-window result: unchanged from earlier run and covered by Docker
  suite.
- Hide/archive result: unchanged from earlier run and covered by Docker suite.
- Attempt start/resume result: starting timed version `8` created attempt `23`
  with a server `deadline_at`; starting timed version `9` created attempt `24`.
- Student quiz-list resume/result link result: unchanged from earlier run and
  covered by Docker suite.
- Attempt payload redaction result: unchanged from earlier run and covered by
  Docker suite.
- Auto-save result: unchanged from earlier run and covered by Docker suite.
- Tamper rejection result: unchanged from earlier run and covered by Docker
  suite.
- Submission result: unchanged from earlier run and covered by Docker suite.
- Cross-student isolation result: unchanged from earlier run and covered by
  Docker suite.
- Attempt limit result: unchanged from earlier run and covered by Docker suite.
- Extra attempt grant result: unchanged from earlier run and covered by Docker
  suite.
- Attempt voiding result: unchanged from earlier run and covered by Docker
  suite.
- Timed lazy expiration result: attempt `23` rendered a `Time Remaining` live
  clock sourced from `data-deadline-at`; browser text ticked from `0:53` to
  `0:48`. Attempt `24` had its database `deadline_at` shortened through the app
  container; on reload, the active attempt page displayed `Time expired`,
  applied `quiz-timer-expired`, and disabled the HTML submit button with text
  `Time expired`.
- Expiration worker/tick result: unchanged from earlier run and covered by
  Docker suite.
- Written grading queue result: unchanged from earlier run and covered by
  Docker suite.
- Manual written grading result: unchanged from earlier run and covered by
  Docker suite.
- Result release result: unchanged from earlier run and covered by Docker
  suite.
- Result policy visibility result: unchanged from earlier run and covered by
  Docker suite.
- Expired written grading result: unchanged from earlier run and covered by
  Docker suite.
- Metrics dashboard result: unchanged from earlier run and covered by Docker
  suite.
- Metrics API default/latest result: unchanged from earlier run and covered by
  Docker suite.
- Metrics all-attempt/voided result: unchanged from earlier run and covered by
  Docker suite.
- Metrics status-filter result: unchanged from earlier run and covered by
  Docker suite.
- Metrics item analysis result: unchanged from earlier run and covered by
  Docker suite.
- Metrics topic/tag/source result: unchanged from earlier run and covered by
  Docker suite.
- Metrics student detail result: unchanged from earlier run and covered by
  Docker suite.
- Exports page result: unchanged from earlier run and covered by Docker suite.
- Class report export result: unchanged from earlier run and covered by Docker
  suite.
- Scoped report export result: unchanged from earlier run and covered by Docker
  suite.
- Print-friendly report result: unchanged from earlier run and covered by
  Docker suite.
- Printable roster sheet result: unchanged from earlier run and covered by
  Docker suite.
- Ingest-compatible bank export result: unchanged from earlier run and covered
  by Docker suite.
- Full-engine export result: unchanged from earlier run and covered by Docker
  suite.
- Full-export validation result: unchanged from earlier run and covered by
  Docker suite.
- Backup info result: unchanged from earlier run and covered by Docker suite.
- Shared theme/chrome result: timed attempt pages included shared dynamic-labs
  theme CSS and had no document-level overflow.
- Mobile theme result: unchanged from earlier run and covered by Docker suite.
- Student-hidden content check: unchanged from earlier run and covered by
  Docker suite.
- PII prompt check: no email, full name, student ID, or institutional ID prompts
  appeared on the validated student pages.
- Console/network errors: no CSP violations were reported. All validated page
  and stylesheet requests returned `200` or expected start-form `302`.
- Deviations or failures: this run intentionally implemented only one backlog
  item, Quiz Time-Remaining Clock.

## Earlier Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-c41eb2f32687` and headless narrow
  instructor context `context-4b16be220090`. Both contexts were closed after
  validation.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM, fetch, network, and CSP checks were
  captured through MCP.
- Seed data status: live database from prior phases remained present in the
  Docker volume.
- `open_identifier`: not generated in this backlog-navigation run.
- `roster_identifier`: not generated in this backlog-navigation run.
- Health/static result: app container was rebuilt and reachable at
  `10.2.0.10`; static theme CSS loaded on validated pages.
- Student enrollment result: not repeated in this backlog-navigation run.
- Student logout/login result: not repeated in this backlog-navigation run.
- Instructor dev login result: dev login as `browser-teacher` redirected to
  `/instructor/` with H1 `Instructor Dashboard`.
- Instructor dashboard result: `/instructor/` returned `200` with expanded
  instructor navigation: Dashboard, Ingest, Banks, Questions, Templates,
  Generated, Registration, Roster, Grading, Metrics, Exports, and Student View.
- Registration-disabled result: not repeated in this backlog-navigation run.
- Roster generation/export result: not repeated in this backlog-navigation run.
- Roster first-use activation result: not repeated in this backlog-navigation
  run.
- Revocation denial result: not repeated in this backlog-navigation run.
- Ingest page result: `/instructor/ingest` returned `200` with complete
  instructor nav via authenticated browser fetch.
- Bank browser/API result: `/instructor/banks` returned `200` with complete
  instructor nav via authenticated browser fetch.
- Question browser/API result: `/instructor/questions` returned `200` with
  complete instructor nav via authenticated browser fetch.
- Question detail result: unchanged from earlier run and covered by Docker
  suite.
- Re-ingest planner result: unchanged from earlier run and covered by Docker
  suite.
- Template list/API result: `/instructor/templates` returned `200` with
  complete instructor nav via authenticated browser fetch.
- Template preview result: unchanged from earlier run and covered by Docker
  suite.
- Quiz generation result: unchanged from earlier run and covered by Docker
  suite.
- Quiz regeneration determinism result: unchanged from earlier run and covered
  by Docker suite.
- Generated quiz list/detail result: `/instructor/quiz-versions` returned
  `200` with complete instructor nav via authenticated browser fetch.
- Instructor preview result: unchanged from earlier run and covered by Docker
  suite.
- Admin metadata update result: unchanged from earlier run and covered by
  Docker suite.
- Publication result: unchanged from earlier run and covered by Docker suite.
- Student published quiz list/API result: unchanged from earlier run and
  covered by Docker suite.
- Availability-window result: unchanged from earlier run and covered by Docker
  suite.
- Hide/archive result: unchanged from earlier run and covered by Docker suite.
- Attempt start/resume result: unchanged from earlier run and covered by Docker
  suite.
- Student quiz-list resume/result link result: unchanged from earlier run and
  covered by Docker suite.
- Attempt payload redaction result: unchanged from earlier run and covered by
  Docker suite.
- Auto-save result: unchanged from earlier run and covered by Docker suite.
- Tamper rejection result: unchanged from earlier run and covered by Docker
  suite.
- Submission result: unchanged from earlier run and covered by Docker suite.
- Cross-student isolation result: unchanged from earlier run and covered by
  Docker suite.
- Attempt limit result: unchanged from earlier run and covered by Docker suite.
- Extra attempt grant result: unchanged from earlier run and covered by Docker
  suite.
- Attempt voiding result: unchanged from earlier run and covered by Docker
  suite.
- Timed lazy expiration result: unchanged from earlier run and covered by
  Docker suite.
- Expiration worker/tick result: unchanged from earlier run and covered by
  Docker suite.
- Written grading queue result: `/instructor/grading` returned `200` with
  complete instructor nav via authenticated browser fetch.
- Manual written grading result: unchanged from earlier run and covered by
  Docker suite.
- Result release result: unchanged from earlier run and covered by Docker
  suite.
- Result policy visibility result: unchanged from earlier run and covered by
  Docker suite.
- Expired written grading result: unchanged from earlier run and covered by
  Docker suite.
- Metrics dashboard result: `/instructor/metrics` returned `200` with complete
  instructor nav via authenticated browser fetch.
- Metrics API default/latest result: unchanged from earlier run and covered by
  Docker suite.
- Metrics all-attempt/voided result: unchanged from earlier run and covered by
  Docker suite.
- Metrics status-filter result: unchanged from earlier run and covered by
  Docker suite.
- Metrics item analysis result: unchanged from earlier run and covered by
  Docker suite.
- Metrics topic/tag/source result: unchanged from earlier run and covered by
  Docker suite.
- Metrics student detail result: unchanged from earlier run and covered by
  Docker suite.
- Exports page result: `/instructor/exports` returned `200` with complete
  instructor nav via authenticated browser fetch.
- Class report export result: unchanged from earlier run and covered by Docker
  suite.
- Scoped report export result: unchanged from earlier run and covered by Docker
  suite.
- Print-friendly report result: `/instructor/exports/reports/class/print` and
  `/instructor/roster-codes/print` returned `200` with complete instructor nav,
  shared theme CSS, and no raw `"student_id"` text.
- Printable roster sheet result: `/instructor/roster-codes/print` returned
  `200` with complete instructor nav via authenticated browser fetch.
- Ingest-compatible bank export result: unchanged from earlier run and covered
  by Docker suite.
- Full-engine export result: unchanged from earlier run and covered by Docker
  suite.
- Full-export validation result: unchanged from earlier run and covered by
  Docker suite.
- Backup info result: unchanged from earlier run and covered by Docker suite.
- Shared theme/chrome result: representative instructor pages all included
  `/static/dynamic-labs-theme.css`, `.dynamic-labs-shell`, and the complete
  shared instructor navigation contract.
- Mobile theme result: narrow viewport checks for `/instructor/`,
  `/instructor/registration`, and `/instructor/roster-codes` showed no
  document-level overflow and no nav overflow with the expanded nav.
- Student-hidden content check: unchanged from earlier run and covered by
  Docker suite.
- PII prompt check: unchanged from earlier run and covered by Docker suite.
- Console/network errors: no CSP violations were reported. All validated page
  and stylesheet requests returned `200` or expected dev-login `302`.
- Deviations or failures: this run intentionally implemented only one backlog
  item, Consistent Instructor Navigation.

## Earlier Theme Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop student context `context-7606f718d348`, headless desktop instructor
  context `context-fc86cc934f03`, headless narrow student context
  `context-08c037b5a461`, and headless narrow instructor context
  `context-636eb28f14aa`. All contexts were closed after validation.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; DOM, computed-style, network, and CSP
  checks were captured through MCP.
- Seed data status: live database from prior phases remained present in the
  Docker volume, including published quiz version `3` used for student attempt
  theme checks.
- `open_identifier`: desktop theme run issued `QZ-69S8-K64B`; narrow viewport
  run issued `QZ-RXT6-XPE3`.
- `roster_identifier`: not regenerated in this Phase 17 theme-only run; roster
  behavior is unchanged from earlier browser/Docker coverage.
- Health/static result: `/healthz` returned `200`; `/static/health.txt`
  remained covered by Docker tests; `/static/dynamic-labs-theme.css` returned
  `200` and served the extracted dynamic-labs theme variables.
- Student enrollment result: open registration issued identifiers in both
  desktop and narrow contexts; `localStorage.quiz_engine_student_identifier`
  matched the issued desktop identifier.
- Student logout/login result: not repeated in this theme-only run.
- Instructor dev login result: unauthenticated `/instructor` returned the
  expected `401`; dev login as `browser-teacher` redirected to `/instructor/`
  with H1 `Instructor Dashboard`.
- Instructor dashboard result: `/instructor/` returned `200` with shared
  dynamic-labs chrome, dark theme background, and instructor navigation.
- Registration-disabled result: not repeated in this theme-only run.
- Roster generation/export result: not repeated in this theme-only run.
- Roster first-use activation result: not repeated in this theme-only run.
- Revocation denial result: not repeated in this theme-only run.
- Ingest page result: `/instructor/ingest` returned `200` with the shared theme
  stylesheet, dynamic-labs shell, instructor navigation, dark background, and no
  document-level horizontal overflow.
- Bank browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question browser/API result: unchanged from earlier run and covered by Docker
  suite.
- Question detail result: unchanged from earlier run and covered by Docker
  suite.
- Re-ingest planner result: unchanged from earlier run and covered by Docker
  suite.
- Template list/API result: unchanged from earlier run and covered by Docker
  suite.
- Template preview result: unchanged from earlier run and covered by Docker
  suite.
- Quiz generation result: unchanged from earlier run and covered by Docker
  suite.
- Quiz regeneration determinism result: unchanged from earlier run and covered
  by Docker suite.
- Generated quiz list/detail result: unchanged from earlier run and covered by
  Docker suite.
- Instructor preview result: unchanged from earlier run and covered by Docker
  suite.
- Admin metadata update result: unchanged from earlier run and covered by
  Docker suite.
- Publication result: unchanged from earlier run and covered by Docker suite.
- Student published quiz list/API result: `/student/quizzes` returned `200` in
  desktop and narrow contexts with the shared theme stylesheet, student chrome,
  visible published quizzes, and no document-level horizontal overflow.
- Availability-window result: unchanged from earlier run and covered by Docker
  suite.
- Hide/archive result: unchanged from earlier run and covered by Docker suite.
- Attempt start/resume result: desktop attempt `21` and narrow attempt `22`
  started from published version `3` and rendered themed attempt pages.
- Student quiz-list resume/result link result: unchanged from earlier run and
  covered by Docker suite.
- Attempt payload redaction result: unchanged from earlier run and covered by
  Docker suite.
- Auto-save result: unchanged from earlier run and covered by Docker suite.
- Tamper rejection result: unchanged from earlier run and covered by Docker
  suite.
- Submission result: unchanged from earlier run and covered by Docker suite.
- Cross-student isolation result: unchanged from earlier run and covered by
  Docker suite.
- Attempt limit result: unchanged from earlier run and covered by Docker suite.
- Extra attempt grant result: unchanged from earlier run and covered by Docker
  suite.
- Attempt voiding result: unchanged from earlier run and covered by Docker
  suite.
- Timed lazy expiration result: unchanged from earlier run and covered by
  Docker suite.
- Expiration worker/tick result: unchanged from earlier run and covered by
  Docker suite.
- Written grading queue result: unchanged from earlier run and covered by
  Docker suite.
- Manual written grading result: unchanged from earlier run and covered by
  Docker suite.
- Result release result: unchanged from earlier run and covered by Docker
  suite.
- Result policy visibility result: unchanged from earlier run and covered by
  Docker suite.
- Expired written grading result: unchanged from earlier run and covered by
  Docker suite.
- Metrics dashboard result: `/instructor/metrics` returned `200` with shared
  dynamic-labs chrome, dark theme background, two metric tables, and no
  document-level horizontal overflow.
- Metrics API default/latest result: unchanged from earlier run and covered by
  Docker suite.
- Metrics all-attempt/voided result: unchanged from earlier run and covered by
  Docker suite.
- Metrics status-filter result: unchanged from earlier run and covered by
  Docker suite.
- Metrics item analysis result: unchanged from earlier run and covered by
  Docker suite.
- Metrics topic/tag/source result: unchanged from earlier run and covered by
  Docker suite.
- Metrics student detail result: unchanged from earlier run and covered by
  Docker suite.
- Exports page result: `/instructor/exports` returned `200` in desktop and
  narrow contexts with shared instructor chrome, report/migration/roster links,
  and no document-level horizontal overflow.
- Class report export result: unchanged from earlier run and covered by Docker
  suite.
- Scoped report export result: unchanged from earlier run and covered by Docker
  suite.
- Print-friendly report result: `/instructor/exports/reports/class/print`
  returned `200`, included the shared stylesheet and
  `dynamic-labs-print-chrome`, kept the Dynamic Labs brand/header, exposed no
  raw `"student_id"` text, and included print-media CSS for hiding navigation.
- Printable roster sheet result: unchanged from earlier run and covered by
  Docker suite.
- Ingest-compatible bank export result: unchanged from earlier run and covered
  by Docker suite.
- Full-engine export result: unchanged from earlier run and covered by Docker
  suite.
- Full-export validation result: unchanged from earlier run and covered by
  Docker suite.
- Backup info result: unchanged from earlier run and covered by Docker suite.
- Shared theme/chrome result: student home, identifier confirmation, quiz list,
  attempt page, instructor dev login, dashboard, ingest, metrics, exports, and
  class print report all included `/static/dynamic-labs-theme.css`,
  `.dynamic-labs-shell`, Dynamic Labs branding, role labels, and
  role-appropriate navigation. The computed body background used the
  instructor-login dark gradient.
- Mobile theme result: narrow viewport checks for `/student/`,
  `/student/quizzes`, `/student/attempts/22`, `/instructor/`, and
  `/instructor/exports` had `scrollWidth - innerWidth == 0`. Quiz answer
  options rendered as individual full-width rows.
- Student-hidden content check: unchanged from earlier run and covered by
  Docker suite.
- PII prompt check: no email, full name, student ID, or institutional ID prompts
  appeared on the validated student pages.
- Console/network errors: no CSP violations were reported. Network traffic had
  the single expected pre-login `GET /instructor: 401`; all positive page and
  stylesheet requests returned `200` or expected post/redirect `302`.
- Deviations or failures: shared auth and CSRF were intentionally not
  integrated in this theme-only Phase 17 slice.

## Earlier Phase 16 Run

- Date: 2026-05-20
- Base URL: `http://10.2.0.10:8000`
- Browser MCP session/context: browser-puppet MCP, not Kali VM; headless
  desktop instructor context `context-6d5553327c22` after dev login as
  `browser-teacher`, and headless mobile-sized student context
  `context-2cf620c3c9d0`.
- Screenshots captured: not available from the currently exposed
  browser-puppet tool set in this run; page outlines, network traffic, DOM text,
  CSP checks, and same-origin JSON checks were captured through MCP.
- Seed data status: live bundle data present; Phase 16 browser fixture seeded
  bank `phase16_browser_ui_1779302274`, template `2`, and published quiz
  version `13`.
- `open_identifier`: Phase 16 mobile student run issued `QZ-ETNU-FW9Y`.
- `roster_identifier`: not regenerated in this Phase 12 run; roster behavior is
  unchanged from earlier browser/Docker coverage.
- Health/static result: `/healthz` returned `200`; `/static/health.txt`
  returned `quiz-engine-v2 static ok`.
- Student enrollment result: open registration issued `QZ-ETNU-FW9Y`; the
  student was able to continue to `/student/quizzes`.
- Student logout/login result: identifier login remains covered by prior
  browser run and Docker tests; this run kept the clean student session active
  for attempt workflows.
- Instructor dev login result: unauthenticated `/instructor` returned expected
  `401`; dev login redirected to `/instructor` with H1 `Instructor Dashboard`.
- Instructor dashboard result: `/instructor` returned `200` with operational
  summary, needs-attention counts, attempt status counts, struggling students,
  weak topics/tags, confusing questions, and recent generated quizzes. It linked
  ingest, banks, questions, templates, generated quizzes, registration, roster
  codes, grading, metrics, and exports. Phase 16 quiz version `13` appeared in
  recent generated quizzes.
- Registration-disabled result: not repeated in this Phase 13 run.
- Roster generation/export result: not repeated in this Phase 13 run.
- Roster first-use activation result: not repeated in this Phase 13 run.
- Revocation denial result: not repeated in this Phase 13 run.
- Ingest page result: synthetic written bank
  `browser_phase13_written_1779296637453` imported successfully as bank `36`.
- Bank browser/API result: live data from the Bitcoin origins bank was used.
- Question browser/API result: covered by Docker suite in this Phase 13
  iteration.
- Question detail result: covered by Docker suite in this Phase 13 iteration.
- Re-ingest planner result: covered by Docker suite in this Phase 13 iteration.
- Template list/API result: `Browser MCP Template` found.
- Template preview result: covered by Docker suite and prior browser run.
- Quiz generation result: Phase 16 fixture generated and published version `13`
  (`Phase 16 Browser UI Quiz`) with one multiple-choice and one written
  question.
- Quiz regeneration determinism result: covered by Docker suite and prior
  browser run.
- Generated quiz list/detail result: instructor grading queue and APIs found
  the generated written quiz attempts.
- Instructor preview result: unchanged from earlier phase and covered by Docker
  suite.
- Admin metadata update result: Phase 13 written versions were generated with
  open availability windows before publication.
- Publication result: versions `10`, `11`, and `12` published successfully.
- Student published quiz list/API result: authenticated student saw all three
  Phase 13 written quizzes.
- Availability-window result: covered by Docker suite and prior browser run.
- Hide/archive result: covered by Docker suite and prior browser run.
- Attempt start/resume result: starting Phase 16 version `13` created attempt
  `20` for `QZ-ETNU-FW9Y`; the student quiz list then showed
  `Attempt 1 is in progress` and a `Resume quiz` link.
- Student quiz-list resume/result link result: after submitting attempt `20`
  through the student API, `/student/quizzes` showed `Start quiz` plus
  `View results` for `Phase 16 Browser UI Quiz`, with no instructor bank
  metadata.
- Attempt payload redaction result: student attempt payloads stayed redacted
  before grading/release.
- Auto-save result: saved written response on timed attempt `11` returned
  `200`.
- Tamper rejection result: covered by Docker suite and prior isolated browser
  negative context.
- Submission result: attempts `9` and `10` submitted to `needs_grading`.
- Cross-student isolation result: a second student context received expected
  `GET /student/attempts/10/results: 404`.
- Attempt limit result: covered by Phase 12 browser run and Docker suite.
- Extra attempt grant result: covered by Phase 12 browser run and Docker suite.
- Attempt voiding result: covered by Phase 12 browser run and Docker suite.
- Timed lazy expiration result: attempt `11` on version `12` was forced past
  its deadline; student fetch returned `expired`.
- Expiration worker/tick result: covered by Phase 12 browser run and Docker
  suite.
- Written grading queue result: `/instructor/grading` showed the Phase 16
  written response for attempt `20`, associated with anonymous identifier
  `QZ-ETNU-FW9Y`, quiz title, question stem, response text, and point controls.
- Manual written grading result: grading answer `36` changed attempt `9` to
  `graded` with score `0.5 / 1`; answer `37` changed attempt `10` to `graded`
  with score `1 / 1`; original written responses were preserved.
- Result release result: releasing version `10` set `results_released_at` and
  `results_released_by=browser-teacher`, emitted one
  `quiz_results.released` audit event, and did not mutate attempt score/state.
- Result policy visibility result: `score_after_release` kept attempt `9`
  hidden until release, then showed score only. `score_and_answers_after_grading`
  showed score, written response, and explanation for attempt `10` immediately
  after grading.
- Expired written grading result: attempt `11` remained `expired` after grading
  saved written answer `38`; score updated to `0.25 / 1`.
- Metrics dashboard result: instructor dashboard and metrics APIs were checked
  in this Phase 16 run; `/instructor/api/metrics` returned the expected
  top-level metrics keys and no raw `"student_id"` key.
- Metrics API default/latest result: `/instructor/api/metrics` returned
  `class_summary`, `quiz_summary`, `student_summary`, topic/tag/source rollups,
  strongest/weakest rollups, and item analysis. The response used anonymous
  identifiers only.
- Metrics all-attempt/voided result:
  `/instructor/api/metrics?mode=all&include_voided=1` returned `200` with
  `mode: all`, `include_voided: true`, 14 selected attempts, and 1 voided
  attempt in status counts.
- Metrics status-filter result: `statuses=graded` returned 6 selected attempts
  with only graded counted; `statuses=expired` returned 3 selected attempts
  with only expired counted.
- Metrics item analysis result: default metrics returned 28 item-analysis rows.
  Multiple-choice rows included attempts, correct count, percent correct, and
  option selection counts; written rows included saved, graded, ungraded, and
  expired-ungraded counts.
- Metrics topic/tag/source result: default metrics returned 1 topic rollup, 36
  tag rollups, and source rollups grouped into 11 lesson blocks, 11 source
  lessons, and 1 source reading bucket.
- Metrics student detail result:
  `/instructor/api/metrics/students/QZ-FMAC-MLSZ?mode=all&include_voided=1`
  returned 4 attempts for the anonymous identifier; the HTML detail route
  returned `200` and showed attempt-level question snapshots plus source
  metadata.
- Exports page result: `/instructor/exports` returned `200` with H1
  `Instructor Exports` and links for report exports, full-engine JSON export,
  backup info, roster-code printing, and the new class print report.
- Class report export result: `/instructor/api/exports/reports/class.json`
  returned `200` with `schema_version: 1`, `scope: class`, filters, and no raw
  `"student_id"` key. `/instructor/api/exports/reports/class.csv` returned
  `200` with stable headers beginning `record_type,student_identifier,...` and
  contained data rows.
- Scoped report export result:
  `/instructor/api/exports/reports/student.json?student_identifier=QZ-ETNU-FW9Y`
  returned the anonymous identifier with no raw `"student_id"` key.
- Print-friendly report result: `/instructor/exports/reports/class/print`,
  `/instructor/exports/reports/student/print?student_identifier=QZ-ETNU-FW9Y`,
  `/instructor/exports/reports/quiz-version/print?quiz_version_id=13`, and
  `/instructor/exports/reports/template/print?template_id=2` all returned
  `200`, showed report H1s, and did not include raw `"student_id"` text or PII
  prompts.
- Printable roster sheet result: `/instructor/roster-codes/print` returned
  `200`, showed H1 `Printable Roster Codes`, and did not include email, full
  name, student ID, institutional ID, or similar PII prompts.
- Ingest-compatible bank export result:
  `/instructor/api/exports/quiz-banks/1.json` returned `200` for
  `bitcoin_01_bf_bitcoin_origins_and_mechanics` with 13 questions and
  multiple-choice answer fields.
- Full-engine export result: `/instructor/api/exports/full.json` returned
  `200` with `schema_version: 1`, `exported_at`, and tables including
  `students`, `quiz_banks`, `quiz_bank_revisions`, `questions`,
  `question_options`, `question_tags`, `quiz_versions`,
  `quiz_version_questions`, `quiz_version_options`, `attempts`,
  `attempt_answers`, `attempt_grants`, `audit_events`, and `app_settings`.
  Live table counts included 62 students, 36 banks, 12 generated quiz versions,
  17 attempts, 55 attempt answers, 2 attempt grants, and 115 audit events.
- Full-export validation result: posting the full export payload to
  `/instructor/api/imports/full/validate` returned `200` with `valid: true`.
  The destructive import route was not run against the live browser database;
  the fresh-database import path is covered by Docker integration tests.
- Backup info result: `/instructor/api/backup-info` returned `200` with
  database path `/data/quiz-engine.sqlite`, environment variable
  `QUIZ_ENGINE_DB_PATH`, compose volume `quiz_engine_data`, and the retention
  note that attempts, audit events, generated quiz versions, and snapshots are
  not silently deleted.
- Student-hidden content check: student result routes only exposed score/review
  content according to policy and release state.
- PII prompt check: no email, full name, student ID, or institutional ID prompts
  appeared.
- Console/network errors: positive Phase 16 student context had no status
  `>=400` network entries. Instructor context had the single expected
  unauthenticated `GET /instructor: 401` before dev login; no CSP violations
  were reported.
- Deviations or failures: none.

## Latest Run: Wide Layout And Form Widths

- Date: 2026-05-21.
- App URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/unit/test_theme.py tests/integration/test_ui_pages.py`
    passed with 8 tests.
  - `docker compose run --rm test` passed with 203 tests.
- Browser-MCP validation:
  - Rebuilt and restarted the app container with
    `docker compose build app && docker compose up -d app`.
  - Created a headless Chromium desktop context at `1920x1080`.
  - Logged in through `/instructor/dev/login`.
  - Checked `/instructor/templates/new`; the header had
    `dynamic-labs-shell dynamic-labs-instructor`, the main element measured
    `1920px`, and the template-builder form measured `1200px` with computed
    `max-width: 1200px`.
  - Checked `/student/`; the header had
    `dynamic-labs-shell dynamic-labs-student`, the main element measured
    `1920px`, and the student form measured `780px` with computed
    `max-width: 780px`.
- Expected behavior:
  - Instructor views can use the wider desktop canvas up to `1920px`.
  - Instructor forms can expand beyond the student limit up to `1200px`.
  - Student-facing forms remain constrained to `780px`.
- Deviations or failures: none.

## Latest Run: Instructor Workflow Guide

- Date: 2026-05-21.
- App URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/integration/test_ui_pages.py`
    passed with 3 tests.
  - `docker compose run --rm test` passed with 203 tests.
- Browser-MCP validation:
  - Rebuilt and restarted the app container with
    `docker compose build app && docker compose up -d app`.
  - Created a headless Chromium desktop context at `1440x1000`.
  - Logged in through `/instructor/dev/login` and landed on `/instructor/`.
  - Confirmed the dashboard headings include `Operational Summary`, then
    `Quiz Workflow Guide`, then `Needs Attention`.
  - Confirmed `.instructor-workflow-guide` renders 6 workflow steps:
    `Import question banks`, `Review and maintain the bank`,
    `Build a template`, `Generate a quiz version`, `Publish when ready`, and
    `Grade and monitor results`.
  - Confirmed workflow links point to `/instructor/ingest`,
    `/instructor/banks`, `/instructor/questions`, `/instructor/templates/new`,
    `/instructor/templates`, `/instructor/quiz-versions`,
    `/instructor/grading`, and `/instructor/metrics`.
  - Confirmed the workflow step list uses CSS grid at desktop width.
- Deviations or failures: none.

## Latest Run: Product Title Cleanup

- Date: 2026-05-21.
- App URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/unit/test_theme.py tests/integration/test_ui_pages.py`
    passed with 8 tests.
  - `docker compose run --rm test` passed with 203 tests.
- Browser-MCP validation:
  - Rebuilt and restarted the app container with
    `docker compose build app && docker compose up -d app`.
  - Created a headless Chromium desktop context at `1440x900`.
  - Checked `/student/`; document title was `Quiz Engine`, shared chrome logo
    text was `Quiz Engine`, role badge was `Student`, no
    `.dynamic-labs-product` subtitle existed, no `h1` duplicated `Quiz Engine`,
    and the rendered body did not contain `Dynamic Labs`.
  - Logged in through `/instructor/dev/login` and checked `/instructor/`;
    shared chrome logo text was `Quiz Engine`, role badge was `Instructor`, no
  `.dynamic-labs-product` subtitle existed, and the rendered body did not
    contain `Dynamic Labs`.
- Deviations or failures: none.

## Latest Run: Phase 18 Unified Stack Cutover

- Date: 2026-05-21.
- Direct app URL: `http://10.2.0.10:8000`.
- Routed full-stack URL from browser-puppet: `http://router-router-1/quiz`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test` passed with
    211 tests.
  - Parent router/lab-manager/shared-auth contract tests passed with 13 tests
    inside the `quiz-engine-v2:local` Docker image.
  - `regression-tests/automated/quiz-engine/run.sh --skip-start` passed
    against the routed host stack with 4 live tests.
  - `regression-tests/infrastructure/student-home-vm/run.sh smoke` passed.
  - Inside `student-home-vm`,
    `regression-tests/automated/quiz-engine/run.sh --fresh-start` built v2 in
    nested Docker, started the routed shared-auth stack, and passed 4 live
    tests.
  - Inside `student-home-vm`, after `lab-manager.sh start all`,
    `regression-tests/automated/quiz-engine/run.sh --skip-start` passed again
    with 4 live tests.
- Browser-MCP validation:
  - Attached `browser-mcp-browser-puppet-1` to `router-net`.
  - Confirmed `/quiz/` redirects to `/quiz/student/`.
  - Confirmed unauthenticated `/quiz/instructor` redirects to the centralized
    `/instructor/` login.
  - Logged in through `/api/instructor/login` and confirmed
    `/quiz/instructor` loads `Instructor Dashboard` through router shared auth.
  - Confirmed routed instructor links include `/quiz/instructor/...`, theme CSS
    is present, and instructor navigation is visible.
  - Confirmed `/quiz/instructor/registration` contains hidden `_csrf_token`
    fields and the shared CSRF script.
  - Confirmed `/quiz/student/` uses student chrome, has no instructor link, and
    does not prompt for email, full name, student ID, or institutional ID.
  - Confirmed mobile student quiz list has no horizontal overflow.
  - Started a student attempt through the routed UI and confirmed answer
    options render as rows and the autosave toast shows `Saved ✓`.
- Broader stack validation:
  - `lab-manager.sh start all` inside `student-home-vm` started router,
    course-site, instructor-auth-service, lane-service, quiz-engine-v2,
    bitcoin, consensus, cryptography, p2p_trust, exercises, ethereum_lab, and
    hlf.
  - Route smoke inside the VM returned `200` for `/`, `/instructor/`, `/quiz/`,
    `/quiz/student/`, `/labs/bitcoin/`, `/labs/consensus/`,
    `/labs/cryptography/`, `/labs/p2p_trust/`, `/labs/ethereum_lab/`,
    `/labs/hlf/`, `/exercises/bgp/`, and `/exercises/insider/`.
  - Automated regressions passed inside the VM for exercises, cryptography,
    consensus, p2p_trust, bitcoin, ethereum_lab, and quiz-engine.
  - HLF was excluded per operator guidance because ttyd websocket checks can
    fail under QEMU emulation slowdown; HLF API/router/auth checks had passed
    before the ignored ttyd failures.
- Deviations or failures:
  - The browser-puppet container initially was not attached to `router-net`;
    attaching it enabled routed validation.
  - The quiz regression runner now invokes `bash ./lab-manager.sh` so it works
    even when the checkout does not preserve executable bits.

## Latest Run: Persistent Student Identifier Cookie

- Date: 2026-05-21.
- Routed full-stack URL from browser-puppet: `http://router-router-1/quiz`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/unit/test_config.py tests/integration/test_student_identity.py`
    passed with 20 tests.
  - `docker compose run --rm test` passed with 214 tests.
- Deployment validation:
  - Restarted the routed stack with `bash ./lab-manager.sh start quiz-engine-v2`
    so quiz-engine-v2 and the centralized instructor-auth-service use the same
    runtime credentials.
  - A live `POST /quiz/student/enroll` returned `200` and set
    `quiz_engine_student` with `Max-Age=15552000`, `HttpOnly`,
    `Path=/`, and `SameSite=Lax`.
  - The enrollment response no longer writes the identifier to `localStorage`.
  - A live `GET /quiz/student/` with that cookie redirected to
    `/quiz/student/quizzes`.
  - A live `POST /quiz/student/logout` deleted `quiz_engine_student`.
- Browser-MCP validation:
  - Enrolled a student through the routed page and confirmed
    `document.cookie` did not expose the student cookie, proving it is
    HttpOnly.
  - Reloaded `/quiz/student/` in the same browser context and confirmed the
    router followed `302` to `/quiz/student/quizzes`.
  - Logged out and confirmed `/quiz/student/` rendered the login/enroll page
    again instead of bypassing it.
- Deviations or failures: none.

## Latest Run: Student Logout Nav And Active Cap Count

- Date: 2026-05-21.
- Routed full-stack URL from browser-puppet: `http://router-router-1/quiz`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/unit/test_students.py tests/unit/test_theme.py tests/integration/test_student_identity.py tests/integration/test_ui_pages.py`
    passed with 36 tests.
  - `docker compose run --rm test` passed with 221 tests after all edits.
- Deployment validation:
  - Restarted the routed stack from the parent Dynamic Labs directory with
    `bash ./lab-manager.sh start quiz-engine-v2`.
  - A live student login with an existing active identifier set an HttpOnly
    `quiz_engine_student` cookie and rendered `Log out` inside the top student
    navigation.
  - The student quiz list did not render a logout form after `</nav>` and did
    not include instructor links.
  - The live registration page displayed
    `40 of 40 active identifiers are using this cap` while the deployed
    database also contained revoked identifiers, confirming revoked/deleted
    registrations are not counted against the active cap.
- Browser-MCP validation:
  - Logged in as a student through the routed UI and confirmed
    `document.cookie` did not expose `quiz_engine_student`.
  - Reloaded `/quiz/student/` and confirmed the browser followed the
    persistent-cookie redirect to `/quiz/student/quizzes`.
  - Confirmed the student logout form is in `.dynamic-labs-nav`, no logout form
    appears after the nav, and no instructor links render on the student page.
  - Logged in through `/api/instructor/login`, opened
    `/quiz/instructor/registration`, and confirmed the page shows
    `40 of 40 active identifiers are using this cap. Revoked or deleted
    identifiers are excluded.` while retaining hidden CSRF fields.
- Deviations or failures:
  - `http://10.2.0.10/quiz/student/` refused the browser-puppet connection in
    this environment, so the routed container hostname `router-router-1` was
    used for the MCP pass.

## Latest Run: Per-Source Template Criteria And Tag Quotas

- Date: 2026-05-21.
- Direct app URL: `http://10.2.0.10:8000`.
- Docker validation:
  - Rebuilt and restarted the app container with
    `docker compose up -d --build app`.
  - `docker compose run --rm test` passed with 218 tests.
  - After the browser-playbook and autocomplete-script updates,
    `docker compose run --rm test python -m pytest -q tests/integration/test_question_bank_browser.py tests/integration/test_quiz_templates.py tests/integration/test_ui_pages.py tests/unit/test_quiz_templates_unit.py tests/unit/test_quiz_generation_unit.py tests/unit/test_question_filter_terms.py`
    passed with 34 tests.
- Browser-MCP validation:
  - Created a headless Chromium desktop context at `1440x900`.
  - Opened `http://10.2.0.10:8000/healthz`; status was `200` and body was
    `{"status":"ok"}`.
  - Logged in through `/instructor/dev/login` as `browser-teacher`.
  - Imported disposable lesson bank `browser_source_rules_1779378630755` with
    `reading` and `slides` question tags.
  - Called `/instructor/api/questions/filter-terms`; response used
    `schema_version: 2`, included the disposable lesson in `banks`, and that
    bank's tag terms were `browser-bank`, `reading`, and `slides`.
  - Created a template through `/instructor/api/templates` with
    `criteria.schema_version: 2`, one `source_rules` override, and tag quotas
    `reading: 1` and `slides: 1`.
  - Previewed the template through `/instructor/api/templates/preview`; the
    preview returned one source-rule entry with eligible pool size `3`,
    requested count `2`, and no warnings.
  - Generated a hidden quiz through
    `/instructor/api/templates/<template_id>/generate`; the snapshot contained
    `source_allocations`, selected one reading-tagged question and one
    slides-tagged question, and recorded tag quota allocations for both tags.
  - Opened `/instructor/templates/new`, selected the disposable source row,
    switched its filter mode to `Customize`, typed `reading, sl` into the
    per-source tag field, and confirmed the token autocomplete menu suggested
    `slides (1)` from the per-bank term database while leaving the previous
    comma-separated token intact.
- Deviations or failures: none.

## Latest Run: Quiz Version Availability Picker

- Date: 2026-05-21.
- Direct app URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test` rebuilt the quiz-engine image.
  - `docker compose run --rm test python -m pytest -q tests/unit/test_publication.py tests/integration/test_quiz_publication.py`
    passed with 8 tests.
  - `docker compose run --rm test` passed with 225 tests.
- Deployment validation:
  - Restarted the shared-auth stack with
    `bash ./lab-manager.sh start quiz-engine-v2`.
- Browser-MCP validation:
  - Created a headless Chromium desktop context at `1440x1200`.
  - Opened `http://10.2.0.10:8000/healthz`; status was `200`.
  - Set a signed shared-auth `hlf_instructor` cookie for `browser-teacher`.
  - Opened `/instructor/quiz-versions` and then
    `/instructor/quiz-versions/29`; status was `200`.
  - Confirmed the detail page shows `Availability`, `Snapshot Questions`,
    two `Calendar` buttons, two `Clear` buttons, and a live server UTC clock.
  - Confirmed the server UTC clock advanced from
    `2026-05-21 17:17:56 UTC` to `2026-05-21 17:17:57 UTC`.
  - Opened the `Available from` calendar picker and confirmed the calendar
    dialog rendered.
  - Set `Available from` and `Available until` to the same UTC minute and
    clicked `Save admin metadata`; the browser stayed on the detail route,
    showed `Available until must be after available from.`, and marked both
    availability groups invalid.
  - Confirmed the correct snapshot option has the green
    `.snapshot-option-correct` highlight and the green `correct` label.
  - Opened `/instructor/quiz-versions/29/preview`; the preview route also
    renders the green correct-answer highlight and label.
- Deviations or failures:
  - A deliberately invalid browser `PATCH` to
    `/instructor/api/quiz-versions/29` returned the expected HTTP `400`; the
    browser MCP surfaced that expected status as a network issue, so the API
    error body was not captured in that browser call. Docker integration tests
    cover the exact error body.

## Latest Run: Default Random Question And Answer Ordering

- Date: 2026-05-21.
- Direct app URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/unit/test_schema.py tests/integration/test_core_schema.py tests/unit/test_quiz_templates_unit.py tests/unit/test_quiz_generation_unit.py tests/unit/test_attempts.py tests/integration/test_quiz_templates.py`
    passed with 59 tests.
  - `docker compose build test && docker compose run --rm test` passed with
    230 tests.
- Deployment validation:
  - Restarted the shared-auth stack with
    `bash ./lab-manager.sh start quiz-engine-v2` from the parent Dynamic Labs
    directory.
- Browser-MCP validation:
  - Opened `http://10.2.0.10:8000/healthz`; status was `200`.
  - Set a signed shared-auth `hlf_instructor` cookie for `browser-teacher`.
  - Opened `/instructor/templates/new` and confirmed both
    `question_order_mode` and `option_order_mode` default to
    `random_per_attempt`, both dropdowns expose `fixed`, `random_once`, and
    `random_per_attempt`, and the order help disclosure is present.
  - Opened `/instructor/templates/9` and confirmed the template detail shows
    `QUESTION ORDER random_per_attempt` and
    `ANSWER ORDER random_per_attempt`.
  - Confirmed the generation seed input auto-populated, clicked
    `Regenerate seed`, and observed the seed change from
    `2e93b3db3476b5c094e4a64660a3506e` to
    `48458bb5ad16e9973cf8425bc7503b46`.
  - Generated hidden quiz version `30` from template `9` with that seed.
  - Opened `/instructor/quiz-versions/30` and confirmed the detail page shows
    `QUESTION ORDER random_per_attempt`, `ANSWER ORDER random_per_attempt`,
    and the exact generation seed.
  - Inspected the 52 snapshot option lists: 16 questions had the correct
    answer first and 36 had the correct answer in a later position, confirming
    answer correctness is not tied to top answer position after shuffling.
- Deviations or failures: none.

## Latest Run: Student Result Answer Highlighting

- Date: 2026-05-21.
- Direct app URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/integration/test_ui_pages.py tests/integration/test_student_attempts.py tests/unit/test_student_attempt_clock.py`
    passed with 16 tests.
  - `docker compose run --rm test` passed with 231 tests.
- Deployment validation:
  - Restarted the shared-auth stack with
    `bash ./lab-manager.sh start quiz-engine-v2` from the parent Dynamic Labs
    directory.
  - Seeded disposable published quiz version `32`,
    `Browser Result Highlight Quiz 1779388756`, with result policy
    `score_and_answers_after_grading`.
- Browser-MCP validation:
  - Created a headless Chromium desktop context at `1440x1000`.
  - Opened `http://10.2.0.10:8000/healthz`; status was `200`.
  - Enrolled a student, started quiz version `32`, submitted two answers, and
    opened `/student/attempts/36/results`.
  - Confirmed result status displayed natural text `Graded`, with no visible
    raw `Status: graded` or `in_progress` status text.
  - Confirmed the result page had two green
    `.quiz-result-option-correct` answer boxes and one red
    `.quiz-result-option-selected-incorrect` selected-answer box. The computed
    border colors were `rgba(127, 208, 162, 0.85)` for green and
    `rgba(234, 122, 122, 0.9)` for red.
  - Enrolled a second student, started the same quiz, opened
    `/student/attempts/37`, and confirmed the attempt status displayed
    `Quiz in progress` with no visible `Status: in_progress` text.
- Deviations or failures:
  - First `create_context` call omitted `headless: true` and failed because
    the browser-puppet environment has no X server. Retried with headless
    Chromium and completed validation.

## Latest Run: Handle-Style Student Identifiers

- Date: 2026-05-21.
- Direct app URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/unit/test_students.py tests/integration/test_student_identity.py tests/unit/test_config.py tests/unit/test_enums.py tests/unit/test_schema.py tests/integration/test_foundation.py tests/integration/test_ui_pages.py`
    passed with 62 tests.
  - `docker compose run --rm test` passed with 237 tests.
- Deployment validation:
  - Restarted the shared-auth stack with
    `bash ./lab-manager.sh start quiz-engine-v2` from the parent Dynamic Labs
    directory.
- Browser-MCP validation:
  - Created a headless Chromium desktop context at `1440x1000`.
  - Opened `http://10.2.0.10:8000/healthz`; status was `200`.
  - Set a signed shared-auth `hlf_instructor` cookie for `browser-teacher`.
  - Opened `/instructor/registration` and confirmed the default identifier
    style dropdown exposes `code` and `handle`.
  - Submitted registration settings with `registration_mode=open`,
    `open_registration_cap=100`, and `identifier_style=handle`, then
    self-enrolled a student. The issued identifier was
    `validator-fork-ropper9`, confirming handle-style self-registration and
    inclusion of original hacker role terms such as `ropper`.
  - Submitted `/instructor/roster-codes` with count `3`, activation
    `pre_active`, and identifier style `handle`. Generated roster identifiers
    were `maroon-wallet-ropper5`, `peach-patch-node4`, and
    `blue-rollup-auditor7`, confirming roster bulk generation uses the expanded
    blockchain/hacker term union.
- Deviations or failures: none.

## Latest Run: Template Inverse Filters And Sticky Timer

- Date: 2026-05-21.
- Direct app URL: `http://10.2.0.10:8000`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/unit/test_json_validation.py tests/unit/test_quiz_templates_unit.py tests/unit/test_quiz_generation_unit.py tests/integration/test_quiz_templates.py tests/unit/test_student_attempt_clock.py tests/integration/test_student_attempts.py tests/integration/test_foundation.py`
    passed with 63 tests.
  - `docker compose run --rm test` passed with 238 tests.
- Deployment validation:
  - Restarted the shared-auth stack with
    `bash ./lab-manager.sh start quiz-engine-v2` from the parent Dynamic Labs
    directory.
  - Seeded disposable bank `browser_inverse_timer_valid_1779401329`, template
    `14`, and published timed quiz version `34`. Previewing the template with
    `excluded_topics: ["bitcoin"]` and `excluded_tags: ["skip-tag"]` left
    exactly one eligible `primitives` question.
- Browser-MCP validation:
  - Created a headless Chromium desktop context at `1440x1000`.
  - Opened `http://10.2.0.10:8000/healthz`; status was `200`.
  - Set a signed shared-auth `hlf_instructor` cookie for `browser-teacher`.
  - Opened `/instructor/templates/new` and confirmed fallback excluded-topic
    and excluded-tag controls exist, 47 source rows exposed per-source
    excluded-topic and excluded-tag controls, and editing the fallback fields
    live-updated `criteria_json` with `excluded_topics` and `excluded_tags`.
  - Posted `/instructor/api/templates/preview` with the seeded inverse-filter
    criteria and confirmed status `200`, `eligible_pool_size: 1`, no warnings,
    and topic counts only for `primitives`.
  - Opened `/instructor/templates/14/edit` and confirmed the persisted
    excluded filters render in the structured form and criteria JSON.
  - Enrolled student `atomic-merkle-builder8`, started published timed quiz
    version `34`, and opened `/student/attempts/38`.
  - Confirmed the attempt page renders `class="quiz-timer quiz-timer-topbar"`,
    computed `position: sticky`, computed `top: 64px`, a live countdown, no
    instructor link in student navigation, and after scrolling the timer
    remained visible at the top of the viewport.
- Deviations or failures:
  - An initial disposable seed used non-canonical topics, which ingestion
    normalized to `other`; the validation seed was recreated with canonical
    `primitives` and `bitcoin` topics before browser checks.

## Latest Run: Routed Student Cookie Root Path

- Date: 2026-05-21.
- Routed full-stack URL from browser-puppet: `http://router-router-1/quiz`.
- Docker validation:
  - `docker compose build test && docker compose run --rm test python -m pytest -q tests/integration/test_student_identity.py tests/unit/test_config.py tests/integration/test_foundation.py`
    passed with 34 tests.
  - `docker compose run --rm test` passed with 238 tests.
- Deployment validation:
  - Restarted the routed stack with
    `bash ./lab-manager.sh start quiz-engine-v2` from the parent Dynamic Labs
    directory.
  - A live `POST /quiz/student/enroll` returned `200` and set
    `quiz_engine_student` with `Max-Age=15552000`, `HttpOnly`, `Path=/`, and
    `SameSite=Lax`.
  - Replayed only the `quiz_engine_student` cookie, with the Flask `session`
    cookie removed from the cookie jar, against `/quiz/student/`. The routed
    service returned `302 Location: /quiz/student/quizzes`, confirming the
    persistent identifier cookie works without the shorter Flask session.
- Browser-MCP validation:
  - Created a headless Chromium desktop context at `1440x1000`.
  - Opened `/quiz/student/`, enrolled through the routed page, and confirmed
    the issued identifier was `crypto-bitwise-node5`.
  - Confirmed `document.cookie` did not expose `quiz_engine_student`, proving
    it remains `HttpOnly`.
  - Reloaded `/quiz/student/` and confirmed the router redirected to
    `/quiz/student/quizzes`, the page showed `Available Quizzes`, the current
    student identifier, and the top-nav `Log out` control.
- Deviations or failures: none.
