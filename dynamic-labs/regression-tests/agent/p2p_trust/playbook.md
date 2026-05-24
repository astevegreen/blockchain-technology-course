# P2P Trust Regression Playbook

This playbook is the browser-driven companion to the automated
`p2p_trust` regression suite.

Use it when validating the live wrapper, the visible lab guide, the
real ttyd web path, and browser-only failures such as JavaScript or
network errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the live `p2p_trust` environment is
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
- if the overall run explicitly chose fresh-start mode, that reset
  should have happened once before the automated stage
- only reset again if the run has failed badly enough that the
  environment is no longer trustworthy, or if the suite is being
  started over from scratch

Optional fresh-start reference:

- if a fresh-start run is needed, use
  `../../automated/p2p_trust/README.md`

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

1. Open `/labs/p2p_trust/`.
2. Confirm the route claims a lane and lands on
   `/labs/p2p_trust/c/<uuid>/`.
3. Confirm the wrapper page loads and the `help-btn` is present.
4. Confirm the visible guide exposes the `Lab A · Reputation` and
   `Lab B · Routing` tabs or equivalents.
5. Confirm the wrapper renders stable command blocks such as:
   - `python3 scripts/ngo_sim.py score`
   - `python3 scripts/gossip_demo.py --mode broadcast`
   - `python3 scripts/dht_demo.py`
   - `python3 scripts/pastry.py`
6. Check console errors and network failures for the landing route and
   wrapper route.

TTYD rule:

- run the visible page-derived `p2p_trust` commands through ttyd
- send the input through the browser path, not through `exec`
- use the rendered commands verbatim from the visible page text
- minimum required coverage:
  - `python3 scripts/ngo_sim.py score`
  - `python3 scripts/gossip_demo.py --mode lookup`
  - `python3 scripts/gossip_demo.py --mode broadcast`
  - `python3 scripts/dht_demo.py`
  - `python3 scripts/pastry.py`
- if the student guide exposes additional fully concrete command blocks
  during navigation, run those too and record them
- if a page command is not fully concrete because it still contains an
  unresolved placeholder such as `<BADACTOR_ID>`, record that specific
  blocker instead of substituting `pwd`

## Instructor Flow

1. In a fresh unauthenticated context, open `/labs/p2p_trust/admin` and
   `/labs/p2p_trust/instructor/` and confirm both redirect or block.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/labs/p2p_trust/admin` and confirm it loads only after auth.
4. Open `/labs/p2p_trust/instructor/` and confirm the instructor ttyd
   route loads only after auth.
5. Check both surfaces for JavaScript and network errors.

## Completion Rule

The `p2p_trust` browser regression is only complete when:

- student claim and wrapper flow work
- the wrapper help affordance is present
- the visible guide/tabs render correctly
- ttyd works through the real web route
- the required Reputation and Routing page commands run through ttyd
- instructor admin and instructor ttyd both load behind shared auth
- no unexplained JavaScript or network failures remain
