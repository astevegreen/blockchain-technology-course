# Day 6 Bitcoin Trace Lab Regression Playbook

This playbook is the browser-driven companion to the automated `bitcoin-trace` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The lab is running (`./lab-manager.sh start bitcoin-trace`) and the automated suite has passed against it.
   Do not reset just to start the browser stage: the chain is frozen and nothing a student does changes it.
2. The lab is under the course site's router: `http://127.0.0.1/labs/bitcoin-trace/` on this machine.
3. No credentials: the lab has no instructor surface. The ransom is invented and exists only on the training chain.
4. Use a window at least 800 pixels wide. A narrower one shows mempool's mobile page, which the worksheet does
   not describe.

Every ID, address, amount and block number is in `dynamic-labs/bitcoin-trace/quizes/facts.json`
(`tx.<name>.txid`, `addr.<role>`, `tx.<name>.height`); the answers are in
`dynamic-labs/bitcoin-trace/quizes/INSTRUCTOR_ANSWERS.md`. A rebuild changes every value, so read them from
there. The transaction names are v1 and v2 (the victims' payments), t1 to t7 (the trail) and tx (X0's later spend).

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures and a screenshot.

## Explorer Flow

1. Open `/labs/bitcoin-trace/mempool/`. Confirm the dashboard loads under that path (no request to `/api/...`
   without the `/labs/bitcoin-trace/mempool` prefix) and shows blocks up to the facts' `height`.
2. Search the ransom address R1. Confirm the address page lists two transactions (the victim's payment and T1),
   received and sent amounts equal, balance 0. Do the same for R2.
3. Open T1. Confirm two inputs (R1 and R2) and two outputs: X0 (a P2SH `3...` address, round amount) and C1
   (a `bc1q...` address, un-round amount). Press "Details" and confirm the output types read P2SH and P2WPKH.
4. Open T2 and T3. Confirm each pays a Taproot `bc1p...` address a round amount and a `bc1q...` address the
   remainder, and that the change output is in a different position in T3 than in T2.
5. Open T4. Confirm two `bc1q...` outputs, both un-round. Open each output's address page: one is spent (K4) and
   one is not (U4).
6. Open T5. Confirm a round-amount output to D and an un-round output to C5, both `bc1q...`; C5 is unspent.
7. Open T6. Confirm 12 inputs and 1 output, D among the inputs. Open one other input's address page and confirm
   it received once, in an earlier block.
8. Open T7. Confirm 1 input and 14 outputs, all different addresses.
9. Open X0's address page and confirm its later spend (`tx`) has a second input Y.
10. Confirm block times show as local time and that dollar figures or "Accelerate" buttons, if shown, are the
    offline quirks the worksheet's "Reading this explorer" names, not errors.
11. Check console errors and failed network requests. Failed price or websocket reconnects that do not break a
    page are notes; a page that does not load, or an API call outside `/labs/bitcoin-trace/mempool/`, is a failure.

## Worksheet Flow

1. Open `/labs/bitcoin-trace`. Confirm it lands on `/labs/bitcoin-trace/lab/` with the title "Day 6 lab: follow
   the ransom to the first service".
2. Read it top to bottom. Confirm: the confidence table (High, Moderate, Low) renders; the answer-row tables have
   five columns and room to type; the worked example's Low row is finished; no percentage is offered anywhere as a
   confidence.
3. Confirm the worksheet names the two ransom addresses and the victim payment only. It must not name any later
   address, the sweep, the batch or the service (search the page text for T1's ID, X0 and D).
4. Confirm the worksheet's source links jump to entries under "Sources" and the external ones are well formed.
5. Check console errors.

## Links Flow

1. Follow the worksheet's links to the explorer and the saved pages, and back. Confirm every one loads under
   `/labs/bitcoin-trace/`.
2. Open `/labs/bitcoin-trace/fallback/`. Search R1 and confirm the page jumps to R1's section. Search T1's ID and
   confirm its section lists the inputs and outputs. Search an address that is not on the chain and confirm the
   "no transactions" message.
3. Open the course site's lab list and confirm a "Bitcoin Trace Lab" link goes to `/labs/bitcoin-trace/`.
4. Check console errors and failed network requests.
