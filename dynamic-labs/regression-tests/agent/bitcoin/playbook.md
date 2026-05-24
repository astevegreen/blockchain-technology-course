# Bitcoin Regression Playbook

This playbook is the browser-driven companion to the automated Bitcoin
regression suite.

Use it when validating the real student flow, the real ttyd web path,
and browser-only failures such as JavaScript or network errors.

If this stage is being split across multiple agents, dispatch from
`suite.yaml` instead of handing one agent this whole document.

## Prerequisites

1. The default assumption is that the overall Bitcoin regression run is
   using the existing live environment without wiping it first.
2. Obtain the current instructor credentials from
   `.runtime/instructor-credentials.txt`.
3. Use a fresh browser context for the student path.
4. Use a separate authenticated browser context for instructor surfaces.

Reset policy:

- do not perform a second independent reset just to start the agent
  stage
- the agent stage is expected to run after the automated stage against
  the same live environment
- if the overall run explicitly chose fresh-start mode, that reset should
  have happened once before the automated stage
- only reset again if the run has failed badly enough that the
  environment is no longer trustworthy, or if the suite is being started
  over from scratch

Optional fresh-start reference:

- if a fresh-start run is needed, use
  `../../automated/bitcoin/reset-and-startup.md`

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

1. Open `/labs/bitcoin/`.
2. Confirm the route claims a lane and redirects to
   `/labs/bitcoin/c/<uuid>/`.
3. Confirm the wrapper page loads and the ttyd frame is present.
4. Confirm the panel links for mempool, explorer, and static sharing are
   visible.
5. Open the mempool, explorer, and `My Static` surfaces and check for
   JavaScript or network errors.
6. Interact with ttyd through the live web route.
7. Use ttyd to create a small file in `~/share`, confirm it loads
   through `My Static`, and confirm the same file is reachable through a
   peer short-id URL from a second fresh student context.

TTYD rule:

- run page-derived commands through ttyd for both Lab 1 and Lab 2
- send the input through the browser path, not through `exec`
- use rendered commands copied from the visible lesson text, not
  invented substitutes
- minimum required coverage:
  - one Lab 1 command, preferably `btc-lab1 getblockchaininfo` after
    defining the visible `btc-lab1` alias
  - one Lab 2 command from the visible ClassNet instructions, preferably
    a safe read command such as `bitcoin-cli -rpcwallet=student_wallet getbalance`
    or `bitcoin-cli getblockchaininfo | grep difficulty`
- if the current page no longer exposes a runnable command for one of
  those labs, record that as a documentation regression instead of
  falling back to `pwd`

## Instructor Flow

1. In a fresh unauthenticated context, open `/labs/bitcoin/admin` and
   `/labs/bitcoin/instructor/` and confirm both redirect or block.
2. Log in through `/instructor/` in a fresh instructor context.
3. Open `/labs/bitcoin/admin` and confirm it loads only after auth.
4. Open `/labs/bitcoin/instructor/` and confirm the instructor ttyd
   route loads only after auth.
5. Check both surfaces for JavaScript and network errors.

## Completion Rule

The Bitcoin browser regression is only complete when:

- student claim and wrapper flow work
- ttyd works through the real web route
- page-derived command coverage is proven for both Lab 1 and Lab 2
- mempool, explorer, and static-share surfaces all load
- a file written through ttyd is reachable through both `My Static` and
  the peer short-id route
- instructor admin and instructor ttyd both load behind shared auth
- no unexplained JavaScript or network failures remain
