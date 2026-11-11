# Explorer Flow Task

## Goal

Confirm the mempool explorer shows every field the worksheet's questions send students to.

## Steps

Follow "Explorer Flow" in `../playbook.md`, steps 1 to 11, in a window at least 800 pixels wide.

## Expected Results

- the dashboard, search, transaction and address pages load under `/labs/bitcoin-trace/mempool/`
- T1 shows two inputs and a P2SH round output beside a P2WPKH un-round one
- T4's two outputs look alike and only one is spent; T6 shows 12 inputs and 1 output; T7 shows 1 input and 14 outputs
- T6's second 0.05 BTC deposit, E, walks back through q3, q2 and q1 (one input each) to a 2.45 BTC coin, and q3's
  input holds more than 1 BTC

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
