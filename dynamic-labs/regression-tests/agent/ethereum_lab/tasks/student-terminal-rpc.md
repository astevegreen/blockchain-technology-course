# Task: Student Terminal And RPC

Goal:

- validate the browser terminal path and RPC path used by the student
  SPA

Steps:

1. Start from a working claimed student SPA.
2. Open the Lab Terminal from the page.
3. Run one short real command through the terminal path a student uses.
4. Confirm the command output returns to the browser.
5. Validate that the SPA can still reach RPC-backed content after the
   terminal interaction.
6. Capture console logs and network failures for the terminal and RPC
   interactions.

Preferred safe command:

- `pwd`

Pass criteria:

- browser terminal opens
- at least one real command runs through it
- RPC-backed content still loads
- no unexplained JavaScript or network failures remain

