# Cryptography Regression Playbook

This playbook is the browser-driven companion to the automated
Cryptography regression suite.

Use it when validating the live Streamlit experience, the visible
scenario commands, and browser-only failures such as JavaScript or
network errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the live Cryptography environment is
   already running and has already passed the automated suite.
2. Obtain the current instructor credentials from
   `.runtime/instructor-credentials.txt`.
3. Use a fresh browser context for the student path.
4. Use a separate authenticated browser context for instructor surfaces.

Reset policy:

- do not perform a second independent reset just to start the browser
  stage
- the browser stage should reuse the same live environment that the
  automated stage already validated
- if the overall run explicitly chose fresh-start mode, that reset should
  have happened once before the automated stage
- only reset again if the run has failed badly enough that the
  environment is no longer trustworthy, or if the suite is being started
  over from scratch

Optional fresh-start reference:

- if a fresh-start run is needed, use
  `../../automated/cryptography/README.md`

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

1. Open `/labs/cryptography/`.
2. Confirm the landing page redirects into `/labs/cryptography/app/`.
3. Confirm the Streamlit shell loads without a blank page.
4. Visit all three modules and at least one scenario in each module.
5. In each visited scenario, compare the visible command instructions
   against the actual terminal widget behavior.
6. Run at least one short command in each module's terminal widget using
   the actual on-page input, not a synthetic API call.
7. Record any mismatch between the visible command text and the working
   command names as a documentation or lab-logic bug.
8. Check console errors and network failures after each major navigation
   change.

Suggested student commands:

- Hashing: a safe short command like `help` or a visible page-derived
  hash command
- Merkle: `list_tx` or another short command shown in the scenario
- Symmetric/Asymmetric: `status` or a short scenario-specific command

## Instructor Flow

1. In a fresh unauthenticated context, confirm
   `/labs/cryptography/admin`, `/labs/cryptography/instructor/`, and the
   raw instructor file path all redirect or block.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/labs/cryptography/admin` and confirm the session cards,
   progress summary, and rendered solution guide appear.
4. Confirm the admin page successfully loads its
   `/api/cryptography/instructor-guide` and progress data.
5. Open `/labs/cryptography/instructor/lab02_crypto_overview.qmd` and
   confirm the raw instructor source file is reachable behind auth.
6. Check both surfaces for JavaScript and network errors.

## Completion Rule

The Cryptography browser regression is only complete when:

- the student landing redirect works
- the Streamlit app loads
- all three modules have been visited
- at least one real terminal command has been run in each module
- any command-text drift has been recorded with a specific fix
- instructor auth gates block before login
- instructor admin, rendered guide, progress data, and raw Quarto
  source all load behind shared auth
- no unexplained JavaScript or network failures remain
