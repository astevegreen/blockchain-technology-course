---
name: lab
description: Build or rework a lab in dynamic-labs: its student steps, data, instructor answers and test playbook. Use for any lab work.
paths:
  - "dynamic-labs/**"
---
# Lab work

What a lab must be is in `docs/build-spec.md` ("A lab"); the lab rules are in `.claude/rules/labs.md`; this is the order.
What a lab asks students to find (its scenario) is the owner's call: when the tracker row leaves it open, ask one
question with a recommendation before building.

1. **Find it.** Read the item's Build Tracker row, then ask the `scout` agent where the lab, its compose target and
   its playbook live (`dynamic-labs/README.md`, "Managed targets").
2. **Write the product first**: the worksheet, memo, trace or diagram the student hands in, with the confidence it
   must state. Every step that follows earns a line of that product.
3. **Write the worked example**, then the problem it prepares for. One version with two entry points: the worked
   example, or straight to the problem for a student whose pretest shows the basics. Optional challenge steps go
   last.
4. **Hand over every query ready-made**: the student runs it and reads the output. The data is captured
   (snapshot, frozen extract, course chain) so every run gives the same answer.
5. **Fence the instructor answers**: each answer, solution or instructor seed gets an `-x` entry in
   `.github/workflows/pages.yml` and a removal in `.github/workflows/vm-build.yml`, in the same change.
6. **Write or extend the playbook** in `dynamic-labs/regression-tests/agent/<lab>/`
   (`dynamic-labs/regression-tests/how-to-write-a-lab-regression-test.md`): it walks the worked example and the
   problem as a student would, through the browser, and checks the product's expected answers.
7. **Check**: `python tools/check.py`, then, where Docker runs (the desktop), the lab's automated tests as
   CLAUDE.md says (`regression-tests/automated/<lab>/run.sh` in WSL) and paste the result. Where Docker doesn't
   run, or the lab has no automated tests, say the lab is unverified here.
8. **Hand to the desktop only what the tests don't cover**: if the playbook has steps the automated tests don't
   (the browser walk, the product's answers), set the item's Build Tracker status to Desktop test and list those
   steps. Only the owner marks Done.

Done when the check passes, the `reviewer` agent returns PASS, and the summary pastes the lab tests' result or says
why they couldn't run, and names the playbook steps left for the desktop.
