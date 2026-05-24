# Task: Student Panel Surfaces

Task ID: `btc-student-supplemental-surfaces`

## Purpose

Validate the student-facing browser surfaces linked from the Bitcoin
wrapper.

## Context Ownership

- use a fresh unauthenticated browser context
- claim a fresh lane for this task
- prefer opening surfaces from the wrapper UI instead of typing the
  URLs manually after the wrapper has loaded

## Routes

- `/labs/bitcoin/`
- `/labs/bitcoin/mempool/`
- `/labs/bitcoin/btc-explorer/`
- `/labs/bitcoin/c/<uuid>/static/`
- `/labs/bitcoin/peer/<short>/`

## Steps

1. Open `/labs/bitcoin/` and wait for the wrapper to load.
2. Open `Mempool` from the panel bar and confirm the page renders.
3. Open `Explorer` from the panel bar and confirm the page renders.
4. Open `My Static` from the panel bar and confirm the personal static
   path loads, even if it is empty.
5. Open `Peers` and inspect the dropdown content.
6. If at least one peer entry is listed, open one peer link and confirm
   it loads. If no peers are listed, record `No other peers online.` and
   do not fail the task for that reason alone.
7. After each major surface, check console errors and network failures.

## Pass Conditions

- mempool loads as HTML and is visibly usable
- explorer loads as HTML and is visibly usable
- `My Static` loads through the claimed student route
- peers dropdown renders without browser errors
- any available peer link opens successfully
- no unexplained JavaScript or network failures block these surfaces

## Failure Evidence

Capture all of the following on failure:

- wrapper URL
- surface URL
- screenshot
- visible error text
- console errors
- failed network requests

## Required Output

Return:

- claimed uuid
- whether peers were available
- routes tested
- pass, partial, or fail
- any fix recommendation if non-pass
