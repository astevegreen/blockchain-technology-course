# Ethereum Regression Playbook

This playbook is the browser-driven companion to the automated
Ethereum regression suite.

Use it when validating the live claim flow, the visible SPA views, the
embedded Lab Terminal behavior, and browser-only failures such as
JavaScript or network errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the live Ethereum environment is
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
  `../../automated/ethereum_lab/README.md`

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

1. Open `/labs/ethereum_lab/`.
2. Confirm the route claims a lane and eventually lands on the student
   SPA instead of looping on the staging page forever.
3. Confirm the SPA loads and the student runtime config is valid.
4. Visit the main views needed for classroom use: Live Network,
   Diagnostics, Beacon Lab, Contract Builder Lab, and Tokenization Lab.
5. Open the Lab Terminal and run at least one short real command through
   the same terminal path the student uses.
6. Confirm RPC-backed views load without obvious failures.
7. Check console errors and network failures after each major view
   change.

Terminal rule:

- run at least one real command through the browser terminal path
- send the input through the browser path, not through `exec`
- prefer a short safe command such as `pwd`

## Instructor Flow

1. In a fresh unauthenticated context, confirm `/labs/ethereum/admin`,
   `/labs/ethereum_lab/instructor/`, and `?mode=instructor` all redirect
   or block.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/labs/ethereum/admin` and confirm it loads only after auth.
4. Open `/labs/ethereum_lab/instructor/` and confirm it reaches
   instructor mode behind auth.
5. Confirm the instructor page can reach its config and instructor-only
   lab-api surfaces.
6. Check both surfaces for JavaScript and network errors.

## Completion Rule

The Ethereum browser regression is only complete when:

- claim flow works
- the student SPA loads
- the key classroom views load
- the Lab Terminal works through the real browser route
- at least one real command is run through the terminal
- instructor auth gates block before login
- instructor admin and instructor mode both load behind shared auth
- no unexplained JavaScript or network failures remain
