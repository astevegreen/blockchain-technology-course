# Instructor Fabric Demo (day 5)

## Goal

Walk the 30-minute day-5 demo as the instructor projects it
(`dynamic-labs/hlf/docs/INSTRUCTOR_GUIDE.md`, "Day 5 demo"), through the
browser, and confirm each beat shows what the guide says it shows. The
automated suite (`HLFFabricDemoTests`) drives the same commands through the
API; this task checks the screens the class actually sees.

## Steps

1. Log in through `/instructor/` and open `/labs/hlf/hlf_instructor.html`.
   Wait until the network shows as up, then press **Seed Sample
   Transactions**.
2. From the node links, open the **Org1 · Cascadia State**, **Org2 ·
   Chesapeake Canoe** and **Org5 · Meridian** consoles
   (`/labs/hlf/peer/org1/console/`, `/org2/`, `/org5/`) in separate tabs,
   and **Open Explorer**. Pick a fresh tag `T` (for example the current
   minute, `1431`).
3. Beat 1. In the Org2 console run
   `invoke create diploma-T-forgery credential 4 "George Washington" 2024 "History" "Bachelor of Arts" "Cascadia State"`.
   Confirm the output says `Issuer forgery rejected` and names both
   `Org2MSP` and `Org1MSP`. In the Org1 console run the same command with
   id `diploma-T-honest`; confirm four `committed with status (VALID)`
   lines. In the Org2 console run `query diploma-T-honest`; confirm
   `"IssuerMSP": "Org1MSP"`.
4. Beat 2. In Scenario Controls press **Activate** on **Endorsement policy
   demo**; confirm the message reports two peers stopped. In the Org1
   console run the create with id `diploma-T-two`; confirm it ends with
   `ENDORSEMENT_POLICY_FAILURE: insufficient live peers (2/4, need 3)`.
   Press **Restore** straight away (within ten seconds); confirm the card
   leaves the fault state, and that within two minutes a create with id
   `diploma-T-after` from Org1 commits.
5. Beat 3. In the Org5 console run `query all`; confirm
   `diploma-T-honest` is listed. Hover the **Org5 · Meridian** node link;
   confirm the tooltip says Meridian may propose under its own name but
   never endorses. Run the Meridian create from the console's hint list
   (with id `diploma-T-meridian`); confirm it commits and the payload shows
   `"IssuerMSP":"Org5MSP"`.
6. In the Explorer open **Governance**. Confirm the organizations list
   Org1MSP to Org5MSP, the policies are listed "via `Admins`", and the
   config history lists `CONFIG` blocks.
7. Check console errors and network failures after each beat.

## Expected Result

- the forged diploma is refused with both MSPs named; the honest one commits
  and reads back with `IssuerMSP` `Org1MSP` from another school's console
- with two peers down a write is refused, and **Restore** pressed at once
  brings writes back
- Meridian reads the whole ledger, its hints and tooltip do not claim it
  cannot write, and its own diploma is stamped `Org5MSP`
- Governance shows the member list, `Admins` mod policies and the config
  history
- no unexplained browser errors appear
