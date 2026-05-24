# Task: Student Guide and Tabs

Task ID: `cons-student-guide-surfaces`

## Purpose

Validate that the student wrapper renders the Consensus guide content
and the visible PoW/PoS tab structure.

## Context Ownership

- use a fresh unauthenticated browser context
- claim a fresh lane for this task
- prefer the visible wrapper controls over typing URLs manually once the
  wrapper has loaded

## Routes

- `/labs/consensus/`
- `/labs/consensus/c/<uuid>/`

## Steps

1. Open `/labs/consensus/` and wait for the wrapper to load.
2. Confirm the wrapper shows the `help-btn`.
3. Confirm the visible guide exposes the `Lab A · Proof of Work` and
   `Lab B · Proof of Stake` tabs or equivalent lab selectors.
4. Switch between the visible lab tabs to prove the guide updates cleanly.
5. Confirm the page text includes the unique visible command blocks for:
   - `python3 scripts/pow_local.py --reset --miners 4 --strategy honest`
   - `python3 scripts/pow_local.py --reset --miners 4 --strategy selfish-cpu`
   - `python3 scripts/pow_local.py --reset --miners 4 --strategy selfish-student`
   - `python3 scripts/pow_local.py --reset --miners 4 --throttle 0.3 --strategy honest`
   - `python3 scripts/pos_sim.py --rounds 15`
   - `python3 scripts/pos_strategy.py`
6. Check console errors and network failures after each major phase.

## Pass Conditions

- wrapper and guide render correctly
- the visible lab tabs or selectors are present
- the page shows the expected unique command text for the visible PoW
  and PoS labs
- no unexplained JavaScript or network failures block the guide

## Failure Evidence

Capture all of the following on failure:

- wrapper URL
- screenshot
- visible error text
- console errors
- failed network requests

## Required Output

Return:

- claimed uuid
- visible tab labels if available
- visible unique command blocks if available
- pass, partial, or fail
- any fix recommendation if non-pass
