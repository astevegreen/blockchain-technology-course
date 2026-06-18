# Ethereum Lab Local Fixes Backlog

Local-only working list. Do not deploy or test remotely until explicitly cleared.

## Completed Locally, Awaiting Remote Validation

- ARC dashboard send should only allow whole-token transfers.
- Arcade session recovery should show active sessions before another ARC burn.
- Arcade session recovery should list multiple game sessions, disable expired sessions, and make active sessions resumable.
- Top-off mining game should wait 1 second after Start Game, then start robots and player simultaneously.
- Arcade activity tables should stack full-width and wrap tx links.
- DeFi Risk Garden contracts should deploy during normal ethereum lane startup before the beacon conductor snapshot.
- DeFi Risk Garden contracts should appear in "All smart contracts on chain" with names and ABIs.
- TimelockRugVault instructor controls should read state from cache/API and mutate only through instructor-only lab-api routes.

## Remote Validation Needed After Green Light

- Dashboard Send Transaction:
  - Buy ARC, confirm dashboard Assets shows ARC.
  - Attempt `1.5` ARC send and verify UI blocks it before `/rpc-write`.
  - Send `1` ARC to another wallet and verify cache/transaction history updates.
- Arcade sessions:
  - Buy ARC, approve vault, start one game, reload page, confirm active session appears before burn buttons.
  - Recover/continue active session and verify the game launches without burning another ARC.
  - Start multiple paid sessions, confirm all active sessions are visible by game.
  - Wait past the 10-minute TTL or use an expired saved session and verify the UI disables reuse.
  - Confirm expired-session recovery returns a clear error instead of appearing to do nothing.
- Top-off mining game:
  - Open top-off modal and confirm Start Game gives a 1-second ready delay.
  - Confirm Mine is disabled during the ready delay.
  - Confirm robots and player begin mining simultaneously after the delay.
  - Confirm no "head start" copy remains.
- Arcade activity lists:
  - Verify high scores, recent submissions, recent purchases, and recent burns each occupy full-width stacked rows.
  - Confirm tx links wrap inside the row instead of overflowing.
- DeFi Risk Garden:
  - Rebuild/restart only the ethereum lane with lab-manager after green light.
  - Confirm startup logs show DeFi Risk Garden deployment before Beacon conductor startup.
  - Confirm `defi-risk-config.json` is written and all seven configured addresses have bytecode.
  - Confirm "All smart contracts on chain" lists EntropyLottery, ThousandEthDoubler, VulnerableBankVault, HoneypotToken, ApprovalDrainer, FakeAirdropClaimer, and TimelockRugVault with ABIs available.
  - Confirm ThousandEthDoubler advertises a 1000 ETH reward for a qualifying 1 ETH deposit event and does not pay out.
  - Confirm VulnerableBankVault has untracked seed ETH and still credits only explicit `deposit()` callers.
  - Confirm EntropyLottery has a 10 ETH entry cost, 1-in-1000 odds, and a 1000 ETH initial pool.
  - Confirm TimelockRugVault instructor panel displays owner, treasury, pause state, fee bps, unlock delay, and total assets.
  - Confirm instructor can update pause, withdrawal fee, unlock delay, and treasury from the panel.
  - Confirm fee values above 9000 bps are rejected before transaction submission.
