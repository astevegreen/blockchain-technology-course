# Student Explorer, Exercises, And Governance

## Goal

Validate the main browser-only student surfaces beyond the wrapper.

## Context Ownership

- start from one claimed student context
- if you need to reopen the student flow after switching to instructor
  work elsewhere, create a fresh student context instead of reusing
  instructor cookies

## Steps

1. Starting from a claimed student wrapper, open the exercises surface.
2. Confirm the exercise narrative renders and student-specific text is
   present.
3. Open the explorer surface and confirm topology data renders.
4. From the explorer, open one transaction detail page using a visible
   seeded transaction link and confirm structured transaction data
   renders.
5. From the explorer, open one asset detail page using a visible seeded
   asset link and confirm structured asset data renders.
6. Open the chaincode view and confirm the detail/source sections
   render.
7. Open the governance view from the explorer and confirm the policy and
   organization sections render.
8. Open at least one node detail page. Prefer a visible explorer link;
   if no node link is exposed, open `/labs/hlf/peer/org1/` after the
   explorer loads and confirm the node context renders.
9. Inventory the visible lesson command families that the ttyd task
   should execute. Confirm the rendered student lesson flow exposes:
   - `hlf-help`
   - `hlf-files`
   - `hlf-peerenv` when that lesson is visible
   - at least one rendered `query ...` command
   - at least one rendered `invoke create ...` command
   - at least one rendered `invoke transfer ...` command
10. After each page change, capture console and network status.

## Expected Result

- exercises, explorer, transaction, asset, chaincode, governance, and
  node-detail surfaces all render
- the student lesson flow visibly exposes the command families needed
  for ttyd execution coverage
- navigation between them works
- no unexplained browser errors appear
