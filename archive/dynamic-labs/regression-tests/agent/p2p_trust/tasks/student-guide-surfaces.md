# Task: Student Guide and Tabs

Task ID: `p2p-student-guide-surfaces`

## Purpose

Validate that the student wrapper renders the `p2p_trust` guide content
and the visible Reputation and Routing tab structure.

## Context Ownership

- use a fresh unauthenticated browser context
- claim a fresh lane for this task
- prefer the visible wrapper controls over typing URLs manually once
  the wrapper has loaded

## Routes

- `/labs/p2p_trust/`
- `/labs/p2p_trust/c/<uuid>/`

## Steps

1. Open `/labs/p2p_trust/` and wait for the wrapper to load.
2. Confirm the wrapper shows the `help-btn`.
3. Confirm the visible guide exposes the `Lab A · Reputation` and
   `Lab B · Routing` tabs or equivalent lab selectors.
4. Switch between the visible lab tabs to prove the guide updates
   cleanly.
5. Confirm the page text includes the stable command blocks for:
   - `python3 scripts/ngo_sim.py score`
   - `python3 scripts/gossip_demo.py --mode lookup`
   - `python3 scripts/gossip_demo.py --mode broadcast`
   - `python3 scripts/dht_demo.py`
   - `python3 scripts/pastry.py`
6. Check console errors and network failures after each major phase.

## Pass Conditions

- wrapper and guide render correctly
- the visible lab tabs or selectors are present
- the page shows the expected stable command text
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
- visible stable command blocks if available
- pass, partial, or fail
- any fix recommendation if non-pass
