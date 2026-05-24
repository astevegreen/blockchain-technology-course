# Consensus Regression Playbook

This playbook is the browser-driven companion to the automated
Consensus regression suite.

Use it when validating the live wrapper, the visible lab guide, the
real ttyd web path, and browser-only failures such as JavaScript or
network errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the live Consensus environment is
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
  `../../automated/consensus/README.md`

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

1. Open `/labs/consensus/`.
2. Confirm the route claims a lane and lands on `/labs/consensus/c/<uuid>/`.
3. Confirm the wrapper page loads and the `help-btn` is present.
4. Confirm the wrapper exposes the consensus guide/tabs and the visible
   PoW and PoS command blocks.
5. Switch between the visible lab tabs if needed to prove the wrapper
   updates cleanly.
6. Check console errors and network failures for the landing route and
   wrapper route.

TTYD rule:

- run all unique visible page-derived Consensus commands through ttyd
- send the input through the browser path, not through `exec`
- use the rendered commands verbatim from the visible page text
- minimum required unique command coverage:
  - `python3 scripts/pow_local.py --reset --miners 4 --strategy honest`
  - `python3 scripts/pow_local.py --reset --miners 4 --strategy selfish-cpu`
  - `python3 scripts/pow_local.py --reset --miners 4 --strategy selfish-student`
  - `python3 scripts/pow_local.py --reset --miners 4 --throttle 0.3 --strategy honest`
  - `python3 scripts/pos_sim.py --rounds 15`
  - `python3 scripts/pos_strategy.py`
- if the page no longer exposes one of those command blocks, record that
  as a page-command regression instead of falling back to `pwd`

## Instructor Flow

1. In a fresh unauthenticated context, open `/labs/consensus/admin` and
   `/labs/consensus/instructor/` and confirm both redirect or block.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/labs/consensus/admin` and confirm it loads only after auth.
4. Open `/labs/consensus/instructor/` and confirm the instructor ttyd
   route loads only after auth.
5. Check both surfaces for JavaScript and network errors.

## Completion Rule

The Consensus browser regression is only complete when:

- student claim and wrapper flow work
- the wrapper help affordance is present
- the visible guide/tabs render correctly
- ttyd works through the real web route
- the full visible PoW and PoS page-command set runs through ttyd
- instructor admin and instructor ttyd both load behind shared auth
- no unexplained JavaScript or network failures remain
