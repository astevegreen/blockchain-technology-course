# Instructor Scenario Controls

## Goal

Validate the scenario control panel: seed data, trigger/recover fault
scenarios, and confirm their effects are visible in the student-facing UI.

## Steps

1. Log in through `/instructor/`.
2. Open `/labs/hlf/hlf_instructor.html`.
3. Seed sample transactions via the Scenario Controls panel (or via
   `POST /labs/hlf/api/hlf/seed` with `{"preset":"sample"}`). Confirm
   the response shows 3 successful operations (2 creates + 1 transfer).
4. For at least one peer-based scenario (e.g. `peer_org1`):
   a. Trigger the scenario (click Activate in the UI or `POST /labs/hlf/api/hlf/fault`
      with `{"target":"peer_org1","action":"stop"}`).
   b. Confirm the scenario status shows "active" / peer stopped.
   c. Open the student explorer and confirm the affected peer is missing
      or shows degraded state.
   d. Recover the scenario (click Validate/Deactivate in the UI or POST with
      `{"target":"peer_org1","action":"start"}`).
   e. Confirm the peer recovers and shows in the student explorer.
5. For the `endorsement_policy` scenario:
   a. Ensure seed data exists (step 3).
   b. Activate the scenario. Confirm it reports policy violation detected.
   c. Deactivate and confirm recovery.
6. Check console errors and network failures after each scenario toggle.

## Expected Result

- seed transactions complete without errors (including the transfer)
- peer stop/start scenarios toggle correctly and are visible in student UI
- endorsement policy scenario activates only when seed data is present
- scenario recovery restores normal state
- no unexplained browser errors appear
