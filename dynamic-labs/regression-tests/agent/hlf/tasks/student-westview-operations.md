# Student Westview Vehicle Operations

## Goal

Validate the Westview Used-Car Exchange scenario through the student
ttyd path, covering vehicle creation, service records, role-based access
control rejections, and vehicle transfer.

## Steps

1. From a claimed student wrapper, navigate to the Chapter 6 exercises.
2. Confirm the "Welcome to Westview" orientation exercise is visible and
   explains the scenario (DMV, Insurance, Inspection, AutoFax roles).
3. Open Your Console.
4. Query the Westview inventory:
   ```
   query all
   ```
   Confirm the 10 starter cars are present (car101-car110) with humorous
   names (Toyoda Coroll-Yeah, Hondé Civ-ish, Voltswagon Jettison, etc.).
   If the 10 cars are not present, the instructor may need to seed them
   first — record this as a dependency rather than a failure.
5. Create a vehicle listing from the student's dealership using the
   rendered command from the "Open for Business" exercise:
   ```
   invoke create-vehicle wv-<sid>-001 "WV-F4K3-<sid>-01" 2019 "Toyoda" "Coroll-Yeah" "silver" 45000 14995
   ```
   Confirm success. Query it back and verify `ListedByMSP` matches the
   student's MSP.
6. Add a service record using the rendered command:
   ```
   invoke add-service wv-<sid>-001 oil-change "Full synthetic oil change"
   ```
   Query back and verify `ProviderMSP` matches the student's MSP and
   the service record appears in `ServiceHistory`.
7. Attempt a role-restricted operation (set title status):
   ```
   invoke set-title wv-<sid>-001 clean "Self-certified"
   ```
   Verify rejection with "Role violation" error naming Org1MSP as
   required for DMV operations.
8. Attempt a role-restricted insurance claim:
   ```
   invoke report-claim wv-<sid>-001 theft "Reported stolen"
   ```
   Verify rejection with "Role violation" error naming Org2MSP as
   required for insurance operations.
9. Transfer a vehicle to another owner:
   ```
   invoke transfer-vehicle wv-<sid>-001 "test-buyer"
   ```
   Confirm success. Query back and verify the owner changed.
10. Capture console and network evidence.

## Expected Result

- Westview inventory present (10 cars with humorous names)
- Vehicle creation succeeds with correct `ListedByMSP`
- Service record succeeds with correct `ProviderMSP`
- Title status role-restriction rejected with clear "Role violation" error
- Insurance claim role-restriction rejected with clear "Role violation" error
- Transfer succeeds and ownership updates
