# Day 7 CoinJoin Trace Lab Regression Playbook

This playbook is the browser-driven companion to the automated `coinjoin-trace` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The lab is running (`./lab-manager.sh start coinjoin-trace`) and the automated suite has passed against it.
   Do not reset just to start the browser stage: the chain is frozen and nothing a student does changes it.
2. The lab is under the course site's router: `http://127.0.0.1/labs/coinjoin-trace/` on this machine.
3. No credentials: the lab has no instructor surface. The ransom, the mixer and its label are invented and exist
   only on the training chain.
4. Use a window at least 800 pixels wide. A narrower one shows mempool's mobile page, which the worksheet does
   not describe.

Every ID, address, amount and block number is in `dynamic-labs/coinjoin-trace/quizes/facts.json`
(`tx.<name>.txid`, `addr.<role>`, `tx.<name>.height`); the answers are in
`dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md`, whose "The story the build wrote" table names each
transaction. A rebuild changes every value, so read them from there. The transaction names are v1 (the victim's
payment), t1 (the pre-mix split), j0 to j3 (the CoinJoin rounds; j0 is the worked example), m1 and m2 (the leaks),
late (J3's late mover), dep, sweep and payout (the mixer).

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures and a screenshot.

## Explorer Flow

1. Open `/labs/coinjoin-trace/mempool/`. Confirm the dashboard loads under that path (no request to `/api/...`
   without the `/labs/coinjoin-trace/mempool` prefix) and shows blocks up to the facts' `height`.
2. Search the ransom address R1. Confirm the address page lists four transactions: the victim's payment, T1, the
   second payment in (M2) and the spend to the mixer's deposit (DEP); balance 0. Open M2 and confirm a second,
   zero-value OP_RETURN output whose text reads "HACKY HACK HACK".
3. Open T1. Confirm one input (R1) and five outputs: four of the same amount (0.5001 BTC) and one that differs (C1).
4. Open J0 (the worked example) and J1. Confirm each shows five inputs of the same amount and five outputs of
   0.5 BTC. Open two of J1's inputs and confirm they come from T1.
5. Open M1. Confirm three inputs (an output of J1, an output of J2 and C1) and two outputs of different amounts.
   Open the change output's address page and confirm it is unspent.
6. Open J1's five output addresses. Confirm one is spent in M1, one is spent alone to a new address in a
   transaction (K1) whose OP_RETURN output reads "DEAD END", and three are unspent. J2's output spent alone (K2)
   carries the same "DEAD END" note.
7. Open J3. Confirm eight inputs and eight outputs of 0.5 BTC. Open its outputs' address pages and confirm five are
   spent one block after J3, one ten blocks after J3, and two are unspent.
8. Open DEP and then the sweep. Confirm the sweep has six inputs, the deposit third, and one output to the pool
   address the worksheet labels a mixer.
9. Open the payout. Confirm one input (the pool) and eight outputs, two of them within about 2% of the deposit.
10. Confirm block times show as local time and that dollar figures or "Accelerate" buttons, if shown, are the
    offline quirks the worksheet's "Reading this explorer" names, not errors.
11. Open the explorer's dashboard (`/labs/coinjoin-trace/mempool/`). Confirm it shows the chain's blocks, not grey
    skeletons with an "Offline" badge, and that its websocket connects at `/labs/coinjoin-trace/mempool/api/v1/ws`.
12. Check console errors and failed network requests. Failed price requests that do not break a page are notes;
    a page that does not load, a websocket that does not connect, or an API call outside
    `/labs/coinjoin-trace/mempool/`, is a failure.

## Worksheet Flow

1. Open `/labs/coinjoin-trace`. Confirm it lands on `/labs/coinjoin-trace/lab/` with the title "Day 7 lab: where
   the trace stops".
2. Read it top to bottom. Confirm: the note on planted leaks is near the top; the confidence table (High, Moderate,
   Low) renders; the note table has the lesson's five columns (Step, What you see, The trace, Still shows,
   Confidence); the worked example's J0 row is finished as a stop with "—"; the problem's questions run 1 to 13 in
   three parts with their hints; the challenge steps are marked optional; no percentage is offered as a confidence.
3. Confirm the worksheet names only the ransom address, the mixer's labelled pool address and the worked example.
   It must not name T1, any round past J0, the leaks, the late mover or the withdrawals (search the page text for
   T1's ID, J3's ID and the address L). "Reading this explorer" says some transactions carry a text note in an
   OP_RETURN output, and does not say which.
4. Confirm the worksheet's source links jump to entries under "Sources".
5. Check console errors.

## Links Flow

1. Follow the worksheet's links to the explorer and the saved pages, and back. Confirm every one loads under
   `/labs/coinjoin-trace/`.
2. Open `/labs/coinjoin-trace/fallback/`. Search R1 and confirm the page jumps to R1's section. Search J3's ID and
   confirm its section lists the eight inputs and outputs. Search M2's ID and confirm its OP_RETURN output shows
   "HACKY HACK HACK". Search an address that is not on the chain and confirm
   the "no transactions" message.
3. Open the course site's lab list and confirm a "CoinJoin Trace Lab" link goes to `/labs/coinjoin-trace/`.
4. Check console errors and failed network requests.
