# Mint Flow Task

## Goal

Confirm a student can mint a badge from the mint page, see it read back from the contract, reach
it in the explorer and ask the contracts the worksheet's questions; and that the lab's pages link
together.

## Steps

1. Follow "Mint Flow" in `../playbook.md`, steps 1 to 6, with seat 39.
2. Follow "Links and Fallback", steps 1 to 3.

## Expected Results

- the mint is mined in a block above 17 within about 15 seconds, and "Same as what you sent?"
  reads yes
- the request log lists every call, including the `null` receipts while it waits
- the worksheet, mint page, saved pages, recorded run and course-site link all load

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
