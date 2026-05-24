# Task: Student TTYD Page-Command Coverage

Task ID: `btc-student-ttyd-guide-command`

## Purpose

Validate that ttyd accepts real student input through the browser path
and that page-derived commands from both Lab 1 and Lab 2 actually run.

## Context Ownership

- use a fresh unauthenticated browser context
- claim a fresh lane for this task
- do not use `docker exec` as the execution path for the command under
  test

## Routes

- `/labs/bitcoin/`
- `/labs/bitcoin/c/<uuid>/`
- `/labs/bitcoin/c/<uuid>/ttyd/`

## Steps

1. Open `/labs/bitcoin/` and wait for the wrapper to load.
2. Let the ttyd frame finish loading through the live wrapper route.
3. Navigate to the visible Lab 1 lesson content and inspect the rendered
   page text for runnable commands.
4. Copy the visible Lab 1 alias command if shown and run it through
   ttyd. Then copy one visible Lab 1 Bitcoin command and run it through
   ttyd. Prefer the rendered alias plus
   `btc-lab1 getblockchaininfo` when those exact commands are visible.
5. Navigate to the visible Lab 2 lesson content and inspect the
   rendered page text for runnable commands.
6. Copy one visible Lab 2 command verbatim and run it through ttyd.
   Prefer a safe read command such as
   `bitcoin-cli -rpcwallet=student_wallet getbalance` or
   `bitcoin-cli getblockchaininfo | grep difficulty` when that exact
   text is visible.
7. If either lab does not expose a runnable student command, record that
   as a page-command regression instead of using a fallback smoke
   command.
8. Confirm that ttyd echoes each command and returns output.
9. Check console errors and network failures before and after the ttyd
   interaction.

## Pass Conditions

- ttyd loads through the real wrapper path
- the agent sends input through ttyd as a student would
- Lab 1 and Lab 2 page-derived commands actually execute and return
  output
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
- exact Lab 1 command or commands run
- exact Lab 2 command run
- whether each command was copied verbatim from visible page text
- pass, partial, or fail
- any fix recommendation if non-pass
