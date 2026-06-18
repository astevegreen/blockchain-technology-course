# Ethereum Lab Running Fix Estimates

Working notes for correctness and live-lab issues found during a stabilization pass. These are estimates, not yet applied patches.

## High: Pivotal Finality Never Advances

- Evidence: `contracts/BeaconChainLab.sol:662` justifies the previous held-back block, but the new latest block remains below quorum; `contracts/BeaconChainLab.sol:872` returns unless the latest block is justified.
- Live symptom: after restart the chain reached 21 blocks with 19 justified and 0 finalized.
- Likely fix: after pivotal fallback, ensure the current block can reach justification when idle, or make `_checkFinality()` evaluate justified epoch checkpoints rather than requiring the newest block to be justified.
- Estimate: medium contract patch plus focused tests for idle pivotal finality.

## High: `lastFinalizedIndex` Can Move Backwards

- Evidence: `_checkFinality()` sets `lastFinalizedIndex` to the checkpoint at `contracts/BeaconChainLab.sol:887`, then the ancestor loop overwrites it with older ancestor indexes at `contracts/BeaconChainLab.sol:898`.
- Impact: the frontend uses `lastFinalizedIndex` for finalized counts and cutoffs, so UI can report the wrong finalized head even after finality starts working.
- Likely fix: track the maximum finalized canonical index and do not overwrite it with lower ancestors.
- Estimate: small contract patch plus a regression test.

## High: Human Double-Vote Tracking Crosses Epochs

- Evidence: `attestedSlotToBlock` is keyed by validator and slot at `contracts/BeaconChainLab.sol:67`, but slots repeat every epoch. `attest()` checks it at `contracts/BeaconChainLab.sol:814`, and `_applyAttestation()` writes it at `contracts/BeaconChainLab.sol:839`.
- Impact: a valid attestation in epoch 2 slot 1 can be flagged as a double vote because the same validator attested epoch 1 slot 1.
- Likely fix: key by epoch and slot, or by a canonical epoch-slot value.
- Estimate: small contract patch plus cross-epoch attestation test.

## High: Join After Exit Can Wedge A Validator

- Evidence: `join()` checks `inPool[msg.sender]` at `contracts/BeaconChainLab.sol:176`, but it does not reject or clear `exited[msg.sender]`. `exit()` leaves the address in `validatorPool` at `contracts/BeaconChainLab.sol:386`; `rejoin()` assumes that existing entry can be reactivated at `contracts/BeaconChainLab.sol:405`. On live chain, `0x9586A4833970847aef259aD5BFB7aa8901DDf746` joined at block 48, exited at block 75, then successfully called `join()` again at block 85, producing `inPool=true`, `exited=true`, `stake=32 ETH`, and two entries in `validatorPool`.
- Impact: the validator is wedged. `join()` now reverts "Already joined", `rejoin()` reverts "Already in pool", and `exit()` reverts "Already exited". The reported transaction `0x2924362b17e3d744c1df6c3026becec471a65e6f33cdf0eb1ce35ef312fa8dfe` was another `join()` call and reverted for this reason.
- Likely fix: prevent `join()` after a prior exit with `require(!exited[msg.sender], "Use rejoin")`, make `rejoin()` the only path that clears `exited`, and add a one-time cleanup/redeploy path for any already wedged live state. Also add frontend preflight reads so the UI never sends `join()` when `exited=true`.
- Estimate: medium contract/frontend patch plus lifecycle tests for join, exit, rejoin, duplicate prevention, and wedged state recovery.

## Medium: Exit Path Lacks Explicit Gas Limit And Immediate State Update

- Evidence: `handleExit()` sends `c.exit()` without an explicit gas limit at `frontend/src/views/BeaconChainLabView.jsx:1204`, while join/rejoin/attest use explicit gas limits. After success it only calls `fetchData()` and does not immediately set `userInPool=false` / `userExited=true`.
- Impact: under shared Hardhat/RPC load, gas estimation or delayed polling can make exit feel failed or leave stale UI actions visible.
- Likely fix: send `exit({ gasLimit: ... })`, set local state immediately after `tx.wait()`, and refresh data.
- Estimate: small frontend patch.

## High: Contract Reset Reverts Because Bot Stake Is Virtual

- Evidence: `resetSession()` refunds every `validatorPool` member from `stakes[member]` at `contracts/BeaconChainLab.sol:432`, including bots whose stake was never deposited as ETH. A live `eth_call` to `resetSession()` reverted with "Refund failed": contract balance was about `129.44175 ETH` while `totalStaked` was about `1429.8195 ETH`.
- Impact: instructor reset can fail exactly when it is needed to recover from broken classroom state. Browser/container session reset cannot repair on-chain state.
- Likely fix: refund only non-bot validators with real deposits, clear bot stake as bookkeeping, and avoid refunding duplicate pool entries twice. Consider replacing classroom reset with the conductor snapshot/revert path when available.
- Estimate: medium contract patch plus reset tests with bots, humans, exits, slashes, and duplicate pool entries.

## Medium: Exited Validators Stay In `validatorPool`

- Evidence: `exit()` sets `inPool=false` and `exited=true` at `contracts/BeaconChainLab.sol:394`, but does not remove the address from `validatorPool`.
- Impact: committee and pool displays can include inactive/exited validators unless every read path filters them. Rejoin is designed to reuse the existing pool entry, so this may be intentional, but it needs consistent UI and committee handling.
- Likely fix: either keep entries but aggressively filter inactive validators in all UI/committee views, or implement explicit slot reuse/removal semantics.
- Estimate: medium contract/frontend patch because it touches pool lifecycle assumptions.

## Medium: Fork Blocks Can Corrupt Epoch/Finality Assumptions

- Evidence: `proposeBlockFork()` copies `latest.slot` and `latest.parentHash` at `contracts/BeaconChainLab.sol:734`, but stamps the fork with `currentEpoch` at `contracts/BeaconChainLab.sol:748`. `_checkFinality()` computes checkpoints from block array indexes at `contracts/BeaconChainLab.sol:879`.
- Impact: appended fork blocks can mismatch canonical epoch data and shift checkpoint math.
- Likely fix: explicitly model canonical indexes versus fork indexes, or keep demo forks out of checkpoint calculations.
- Estimate: medium contract patch plus fork regression tests.

## Medium: `BlockProposed` Emits Wrong Epoch At Boundaries

- Evidence: `_createBlock()` advances `currentEpoch` at `contracts/BeaconChainLab.sol:679` before emitting `BlockProposed(blockIndex, proposer, currentEpoch)` at `contracts/BeaconChainLab.sol:690`.
- Impact: block struct epoch is correct, but event-driven UI/logs can show the last block of an epoch as belonging to the next epoch.
- Likely fix: emit `blocks[blockIndex].epoch`.
- Estimate: tiny contract patch plus event assertion.

## Medium: Claim Flow Waits On Readiness, Not Image Build

- Evidence: claim creates a session and starts the lane asynchronously at `../lane-service/generic_claims.py:215`. Resolve then calls `_ensure_lane_ready()` at `../lane-service/lab_blueprint.py:282`; if readiness is not reached within the busy wait, it returns `503 container starting` at `../lane-service/lab_blueprint.py:284`.
- Ethereum-specific detail: `../lane-service/labs/ethereum.py:227` does not configure a custom readiness probe, so readiness is effectively lane-manager status plus Docker running checks, not an HTTP health check.
- Live symptom: Docker events for later claims showed container create/start against the existing `ethereum-trainer:latest` image, not a rebuild. Older claimed lanes are still on pre-fix image IDs, while newer lanes are on the rebuilt image.
- Likely fix: add timing logs around `start_lane()` and readiness checks, ensure all old lanes are recycled after image changes, and consider pre-warming more lanes.
- Estimate: small service/UI patch; performance fix depends on measured container startup time.

## Medium: Browser Session Reset Leaves Old Wallets In Account Dropdown

- Evidence: `frontend/src/App.jsx:6731` only removed legacy `eth_lab_wallet_pk`, while `frontend/src/web3.js` now stores the dropdown list in `eth_lab_wallets` and the active selection in `eth_lab_active_wallet_id`.
- Impact: after "Reset your session", old generated/imported private keys still appear under "Your Account". In student lanes, the assigned station wallet may still reappear after reload because `/api/config.json` intentionally auto-imports it.
- Fix: patched reset to also clear `eth_lab_wallet_nickname`, `eth_lab_wallets`, and `eth_lab_active_wallet_id`.
- Estimate: tiny frontend patch; deploy with the next frontend hot patch.

## Test Gap

- There are no direct `BeaconChainLab` scenario tests in `test/`. Add targeted tests for pivotal finality, `lastFinalizedIndex`, cross-epoch attestation, fork checkpoint behavior, and exit/rejoin UI preflight assumptions.
