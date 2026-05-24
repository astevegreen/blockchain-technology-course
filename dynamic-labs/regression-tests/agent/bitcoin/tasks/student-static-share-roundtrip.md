# Task: Student Static Share Round Trip

Task ID: `btc-student-static-share-roundtrip`

## Purpose

Validate that a student can create a file through the live ttyd route,
fetch it through `My Static`, and expose the same file through the
cookie-free peer short-id route.

## Context Ownership

- use a fresh primary student context for claim, ttyd, and `My Static`
- use a second fresh student context for the peer short-id fetch
- do not reuse cookies between the two contexts
- do not use `docker exec` as the execution path for the file write

## Routes

- `/labs/bitcoin/`
- `/labs/bitcoin/c/<uuid>/`
- `/labs/bitcoin/c/<uuid>/ttyd/`
- `/labs/bitcoin/c/<uuid>/static/<filename>`
- `/labs/bitcoin/peer/<short>/<filename>`

## Steps

1. In the primary student context, open `/labs/bitcoin/` and wait for
   the wrapper to load.
2. Record the claimed `uuid`.
3. Derive the peer short id as the first 8 hex characters of the
   claimed uuid.
4. Let the ttyd frame finish loading through the live wrapper route.
5. Through ttyd, create a unique file in `~/share`, for example:
   `printf '%s' 'mcp-static-<token>' > ~/share/<filename> && cat ~/share/<filename>`.
6. Confirm ttyd echoes the command and returns the expected file
   contents.
7. Open `My Static` from the wrapper (or the direct static path) and
   confirm `/labs/bitcoin/c/<uuid>/static/<filename>` returns the same
   contents.
8. In the second fresh student context, open
   `/labs/bitcoin/peer/<short>/<filename>` and confirm it returns the
   same contents without relying on the original student's cookies.
9. Check console errors and network failures after the ttyd write, the
   `My Static` fetch, and the peer-route fetch.

## Pass Conditions

- ttyd accepts the file-write command through the real browser route
- the file appears through `My Static`
- the same file appears through the peer short-id route in a fresh
  context
- console and network state do not show unexplained blocking failures

## Failure Evidence

Capture all of the following on failure:

- claimed uuid
- derived short id
- wrapper URL
- static or peer URL under test
- screenshot
- command entered
- visible terminal output or failure mode
- console errors
- failed network requests

## Required Output

Return:

- claimed uuid
- derived short id
- filename used
- exact command run
- pass, partial, or fail
- any fix recommendation if non-pass
