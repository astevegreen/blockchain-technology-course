# Instructor Reset And Restart

## Goal

Validate that the instructor console can reset the HLF network and then
start it again cleanly from the browser.

## Steps

1. Log in through `/instructor/`.
2. Open `/labs/hlf/hlf_instructor.html`.
3. Click `Reset Network`.
4. Confirm the lifecycle overlay opens and progresses without browser
   errors.
5. Wait until the reset completes and `/api/hlf/status` reports the
   network is stopped, idle, or otherwise no longer running.
6. Click `Start Network`.
7. Confirm the lifecycle overlay opens again and completes without
   browser errors.
8. Wait until `/api/hlf/status` reports the network is running.
9. Open one instructor console path such as `/labs/hlf/peer/org1/console/`
   and confirm the ttyd page still loads after the restart.
10. Capture console errors and network failures for the reset and start
    operations.

## Expected Result

- reset can be triggered from the instructor console
- start can be triggered again from the instructor console
- lifecycle overlay reflects both operations correctly
- network status returns to running after the restart
- at least one instructor ttyd console still loads after the restart
- no unexplained browser or network failures remain
