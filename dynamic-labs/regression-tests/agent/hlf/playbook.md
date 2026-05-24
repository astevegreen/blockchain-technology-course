# HLF Regression Playbook

This playbook is the browser-driven companion to the automated HLF
regression suite.

Use it when validating the visible student and instructor experience,
the real ttyd web path, and browser-only failures such as JavaScript or
network errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the live HLF environment is already
   running and has already passed the automated suite.
2. Obtain the current instructor credentials from
   `.runtime/instructor-credentials.txt`.
3. Use a fresh browser context for the student path.
4. Use a separate authenticated browser context for instructor surfaces.

Reset policy:

- do not perform a second independent reset just to start the browser
  stage
- the browser stage should reuse the same live environment that the
  automated stage already validated
- if the overall run explicitly chose fresh-start mode, that reset
  should have happened once before the automated stage
- only reset again if the run has failed badly enough that the
  environment is no longer trustworthy, or if the suite is being
  started over from scratch

Optional fresh-start reference:

- if a fresh-start run is needed, use
  `../../automated/hlf/reset-and-startup.md`

## Evidence Rules

For every failed step, capture:

- URL
- visible failure
- console errors
- network failures
- screenshot

## Role-Switch Rule

- when moving from student flow to instructor flow, or back again,
  close the current browser context and create a fresh session for the
  new role
- never reuse student cookies for instructor pages, or instructor
  cookies for student pages

## Student Flow

1. Open `/labs/hlf/`.
2. Confirm the route redirects to `/labs/hlf/claim`.
3. Claim a student station and confirm the wrapper lands on
   `/labs/hlf/c/<uuid>/`.
4. Confirm the wrapper renders the student role, the current school, and
   links for exercises, explorer, governance, and `Your Console`.
5. Open the exercises and explorer surfaces and verify they render
   without browser errors.
6. From the explorer, open one transaction detail page, one asset detail
   page, the chaincode view, the governance view, and at least one node
   detail page.
7. Check console errors and network failures after each major page
   change.

TTYD rule:

- run the visible page-derived HLF lesson commands through ttyd
- send the input through the browser path, not through `exec`
- copy rendered commands verbatim from the visible lesson text rather
  than inventing your own
- minimum required command-family coverage from the student lessons:
  - helper: `hlf-help`
  - environment/files: `hlf-files` and `hlf-peerenv` when those lessons
    are visible
  - read: one rendered `query ...` command
  - write/create: one rendered `invoke create ...` command (should use
    8-arg syntax with explicit school name as the 8th arg)
  - transfer/update: one rendered `invoke transfer ...` command
- if the page no longer exposes a required command family, record that
  as a student-lesson regression instead of falling back to a smoke
  command

Forgery verification (from the "Try to Forge a Diploma" exercise):

- after completing the basic command coverage above, run the forgery
  exercise commands through the same ttyd session
- test all three forgery scenarios:
  1. consortium forgery: `invoke create` with a consortium school name
     (e.g. "Cascadia State") as the 8th arg — must be rejected with
     "Issuer forgery rejected" error
  2. peer-to-peer forgery: `invoke create` with another student peer's
     school name (e.g. "North Ridge University") as the 8th arg — must
     also be rejected with the same error pattern
  3. freeform issuer: `invoke create` with a made-up school name (e.g.
     "Wonderland Academy") — must succeed, then `query` it back and
     verify the `IssuerMSP` field shows the student's real MSP (not
     the freeform name)
- if the student happens to BE Student01 (North Ridge University),
  substitute a different student school name for the peer-to-peer test
- record PASS only if all three scenarios behave as expected

## Instructor Flow

1. In a fresh unauthenticated context, open
   `/labs/hlf/hlf_instructor.html`, `/labs/hlf/peer/org1/console/`, and
   `/labs/hlf/api/hlf/instructor-snapshot` and confirm they redirect or
   block.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/labs/hlf/instructor/`.
4. Open every consortium console route plus the orderer console and
   confirm they load behind auth.
5. Trigger `Reset Network`, confirm it completes, then trigger
   `Start Network` and confirm the network returns to running.
6. Open at least one instructor-only fault or snapshot surface that the
   HLF UI exposes.
7. Check all instructor surfaces for JavaScript and network errors.

## Westview Scenario

1. After the instructor flow completes, confirm the "Ch 6 — Westview
   Used-Car Exchange" heading is visible in the Scenario Controls panel.
2. Click "Seed Westview Inventory" (in Ledger Seeding or Scenario
   Controls) and verify 10 cars appear in the explorer (car101-car110).
3. Execute each consortium role button from the Westview scenario
   controls:
   - DMV: Set Salvage Title → verify car108 TitleStatus = "salvage"
   - Insurance: Report Claim → verify car104 has collision claim
   - Inspection: Fail Vehicle → verify car105 InspectionStatus = "failed"
   - AutoFax: Flag Discrepancy → verify car108 has odometer-discrepancy
     flag
4. In a student context, create a vehicle, add a service record, and
   attempt a role-restricted operation (expecting rejection with "Role
   violation" error).
5. Verify the forgery check blocks cross-shop service records.
6. Transfer a vehicle and confirm ownership change.

## Completion Rule

The HLF browser regression is only complete when:

- student claim and wrapper flow work
- exercises, explorer, transaction, asset, chaincode, governance, and
  node-detail surfaces render
- ttyd works through the real web route
- page-derived command families from the student lessons run through
  ttyd
- forgery verification passes (consortium, peer-to-peer, freeform)
- instructor auth gates block before login
- instructor surfaces and all consortium consoles load behind shared
  auth
- instructor reset/start works from the browser
- Westview inventory seeds correctly
- consortium role buttons execute from correct org contexts
- student vehicle operations (create, service, transfer) work
- role-based and forgery restrictions are enforced
- no unexplained JavaScript or network failures remain
