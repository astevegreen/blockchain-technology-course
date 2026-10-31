# Sign and Send Flow Task

## Goal

Confirm a student can build, sign and send a transaction from the signing page, watch it wait
and be mined, and reach it in the explorer; and that the lab's pages link together.

## Steps

1. Follow "Signing Flow" in `../playbook.md`, steps 1 to 6, with seat 39.
2. Follow "Links and Fallback", steps 1 to 3.

## Expected Results

- the signed transaction is mined in a block above 10 within about 15 seconds
- the request log lists every call, including the `null` receipts while it waits
- the worksheet, signing page, saved pages, recorded run and course-site link all load

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
