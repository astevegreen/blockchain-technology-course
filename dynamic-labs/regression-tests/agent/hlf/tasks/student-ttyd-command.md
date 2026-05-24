# Student TTYD Lesson-Command Coverage

## Goal

Validate the real HLF ttyd browser route using rendered student lesson
commands.

## Steps

1. Starting from a claimed student wrapper, open the student lesson
   content and copy the rendered commands you will execute.
2. Confirm the visible lesson flow exposes the required command
   families:
   - `hlf-help`
   - `hlf-files`
   - `hlf-peerenv` when visible
   - one rendered `query ...` command
   - one rendered `invoke create ...` command
   - one rendered `invoke transfer ...` command
3. Open `Your Console`.
4. Confirm the ttyd terminal loads inside the browser.
5. Run `hlf-help` through the browser path.
6. Run `hlf-files` through the browser path.
7. Run `hlf-peerenv` when that command is visibly presented in the
   lesson flow.
8. Run one rendered `query ...` command copied verbatim from the page.
9. Run one rendered `invoke create ...` command copied verbatim from the
   page.
10. Run one rendered `invoke transfer ...` command copied verbatim from
    the page.
11. If a required command family is missing from the rendered lesson
    flow, record that as a student-lesson regression instead of using a
    fallback smoke command.
12. Navigate to the "Try to Forge a Diploma" exercise in the lesson
    flow and run the three forgery scenarios through the terminal:
    - **consortium forgery**: run the rendered `invoke create` that
      claims "Cascadia State" as issuer — verify the chaincode rejects
      with "Issuer forgery rejected" naming both MSPs
    - **peer-to-peer forgery**: run the rendered `invoke create` that
      claims another student school (e.g. "North Ridge University") —
      verify the same rejection pattern (if the claimed student IS
      Student01, substitute a different student school name)
    - **freeform issuer**: run the rendered `invoke create` with a
      made-up school name (e.g. "Wonderland Academy") — verify it
      succeeds, then `query` it back and confirm the `IssuerMSP`
      field shows the student's real MSP, not the freeform name
13. Capture console and network evidence after the terminal interaction.

## Expected Result

- the browser ttyd path connects
- the required student lesson command families execute successfully
- the output matches the claimed student context
- consortium forgery is rejected by the chaincode
- peer-to-peer forgery is rejected by the chaincode
- freeform issuer succeeds but IssuerMSP records the real signer MSP
