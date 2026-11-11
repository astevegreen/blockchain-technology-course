# Spot the Fake Task

## Goal

Confirm the day 3 game's four Course Pounds read as the key says, in Otterscan and on the mint page,
and that the game page walks all seven steps.

## Steps

Follow "Spot the Fake" in `../playbook.md`, steps 1 to 5.

## Expected Results

- all four tokens answer Course Pound, cGBP, 6 decimals
- the real token's creator is Account 0; the other three's is Account 7
- Otterscan shows the creator line and verified source for each
- the twist token's `owner()` answers Account 0
- the game page links to the lab host and records calls without showing which token is real

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
