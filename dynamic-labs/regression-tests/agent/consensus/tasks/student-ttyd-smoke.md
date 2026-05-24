# Task: Student TTYD Page-Command Coverage

Task ID: `cons-student-ttyd-smoke`

## Purpose

Validate that ttyd accepts real student input through the browser path
and runs the visible Consensus page commands.

## Context Ownership

- use a fresh unauthenticated browser context
- claim a fresh lane for this task
- do not use `docker exec` as the execution path for the command under
  test

## Routes

- `/labs/consensus/`
- `/labs/consensus/c/<uuid>/`
- `/labs/consensus/c/<uuid>/ttyd/`

## Steps

1. Open `/labs/consensus/` and wait for the wrapper to load.
2. Let the ttyd frame finish loading through the live wrapper route.
3. Inspect the visible guide and inventory each unique rendered command
   block.
4. Run each unique visible command through ttyd exactly once:
   - `python3 scripts/pow_local.py --reset --miners 4 --strategy honest`
   - `python3 scripts/pow_local.py --reset --miners 4 --strategy selfish-cpu`
   - `python3 scripts/pow_local.py --reset --miners 4 --strategy selfish-student`
   - `python3 scripts/pow_local.py --reset --miners 4 --throttle 0.3 --strategy honest`
   - `python3 scripts/pos_sim.py --rounds 15`
   - `python3 scripts/pos_strategy.py`
5. If one of those commands is no longer present in the rendered lesson
   text, record that as a page-command regression instead of using a
   fallback smoke command.
6. Confirm that ttyd echoes each command and returns output.
7. Check console errors and network failures before and after the ttyd
   interaction.

## Pass Conditions

- ttyd loads through the real wrapper path
- the agent sends input through ttyd as a student would
- each required visible page command executes and returns output
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
- any visible command blocks that were missing from the rendered page
- pass, partial, or fail
- any fix recommendation if non-pass
