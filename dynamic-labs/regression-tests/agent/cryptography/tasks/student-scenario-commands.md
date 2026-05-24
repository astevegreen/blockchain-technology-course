# Task: Student Scenario Commands And Navigation

Goal:

- validate that the visible module/scenario navigation works
- run short real commands through the on-page terminal widgets
- identify any drift between visible command instructions and actual
  working command names

Steps:

1. Start from `/labs/cryptography/app/`.
2. Visit Module 1 and select at least one Hashing scenario.
3. Run one short command in the Hashing terminal widget using the same
   input control a student uses.
4. Visit Module 2 and select at least one Merkle scenario.
5. Run one short command in the Merkle terminal widget.
6. Visit Module 3 and select at least one Symmetric/Asymmetric scenario.
7. Run one short command in that terminal widget.
8. While visiting each module, compare the visible instructions and
   command examples against what the terminal actually accepts.
9. Record any drift as a concrete finding with a recommended fix to the
   specific page or instruction source.
10. Capture console logs and network failures after each module change.

Preferred safe commands:

- a visible `help` command if the page documents it
- a short page-derived command like `list_tx` or `status`

Pass criteria:

- all three modules load
- at least one real command runs in each visited module
- any command drift is explicitly recorded
- no unexplained JavaScript or network failures remain

