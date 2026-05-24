# Instructor Westview Scenario Controls

## Goal

Validate instructor Westview scenario buttons and role-based consortium
operations from the instructor console.

## Steps

1. Log in as instructor, open the HLF instructor console.
2. Confirm the "Ch 6 — Westview Used-Car Exchange" heading is visible
   in the Scenario Controls panel, with buttons for:
   - Westview: Seed Inventory
   - Westview DMV: Set Salvage Title
   - Westview Insurance: Report Claim
   - Westview Inspection: Fail Vehicle
   - Westview AutoFax: Flag Discrepancy
3. In the Ledger Seeding section, confirm a "Seed Westview Inventory"
   button is present alongside the existing sample seed button.
4. Click "Seed Westview Inventory" (either the seeding button or the
   scenario control) and confirm it completes successfully.
5. Open a student-context explorer and confirm the 10 cars appear
   (car101-car110) with correct vehicle fields.
6. Return to the instructor console. Click "Westview DMV: Set Salvage
   Title" (Run button) — confirm success toast/status.
7. Click "Westview Insurance: Report Claim" — confirm success.
8. Click "Westview Inspection: Fail Vehicle" — confirm success.
9. Click "Westview AutoFax: Flag Discrepancy" — confirm success.
10. Query car108 from the explorer or an instructor console and verify
    it has:
    - TitleStatus = "salvage"
    - A Flags entry for "odometer-discrepancy"
11. Query car104 and verify it has an InsuranceClaims entry for
    "collision".
12. Query car105 and verify InspectionStatus = "failed".
13. Check for JavaScript and network errors throughout.

## Expected Result

- All 5 Westview scenario buttons visible under the Westview heading
- Westview seed button also appears in Ledger Seeding section
- Seed creates the 10 cars with humorous names
- Each role-specific operation succeeds from its designated org
- Vehicle records reflect all consortium actions
- No JavaScript or network errors
