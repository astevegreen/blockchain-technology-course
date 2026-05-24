# Task: Student TTYD Page-Command Coverage

Task ID: `p2p-student-ttyd-smoke`

## Purpose

Validate that ttyd accepts real student input through the browser path
and runs the visible `p2p_trust` page commands.

## Context Ownership

- use a fresh unauthenticated browser context
- claim a fresh lane for this task
- do not use `docker exec` as the execution path for the command under
  test

## Routes

- `/labs/p2p_trust/`
- `/labs/p2p_trust/c/<uuid>/`
- `/labs/p2p_trust/c/<uuid>/ttyd/`

## Steps

1. Open `/labs/p2p_trust/` and wait for the wrapper to load.
2. Let the ttyd frame finish loading through the live wrapper route.
3. Inspect the visible guide and inventory the concrete rendered
   commands.
4. Run the minimum required concrete page commands through ttyd:
   - `python3 scripts/ngo_sim.py score`
   - `python3 scripts/gossip_demo.py --mode lookup`
   - `python3 scripts/gossip_demo.py --mode broadcast`
   - `python3 scripts/dht_demo.py`
   - `python3 scripts/pastry.py`
5. If the guide exposes additional fully concrete command blocks during
   navigation, run those too and record them.
6. If a visible page command is not fully concrete because it still
   contains an unresolved placeholder such as `<BADACTOR_ID>`, record
   that blocker instead of substituting `pwd`.
7. Confirm that ttyd echoes each command and returns output.
8. Check console errors and network failures before and after the ttyd
   interaction.

## Pass Conditions

- ttyd loads through the real wrapper path
- the agent sends input through ttyd as a student would
- the required concrete page commands execute and return output
- console and network state do not show unexplained blocking failures

## Failure Evidence

Capture all of the following on failure:

- wrapper URL
- ttyd URL
- screenshot
- commands entered
- visible terminal output or failure mode
- console errors
- failed network requests

## Required Output

Return:

- claimed uuid
- exact commands run
- any placeholder or missing command blocks that prevented coverage
- pass, partial, or fail
- any fix recommendation if non-pass
