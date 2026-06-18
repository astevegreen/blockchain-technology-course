# Tokenization Lab — Fungible Token (ERC-20) Arcade Plan

## Purpose

This is the fungible-token half of the Tokenization Lab, a sibling to the NFT bank
(`tokenization-nft-bank-plan.md`). Where the NFT flow teaches ERC-721 ("I own *this specific*
thing"), this flow teaches ERC-20 ("I have *a balance* of an interchangeable thing") and, just as
importantly, gives the token a **reason to be spent**: students buy an arcade token with ETH, then
burn it to play shallow in-browser arcade games. That closes a real economic loop — buy → spend →
balance drops → buy again — instead of stopping at "look, you can transfer it."

The two standards taught side by side:

- **ERC-721 (NFT lab):** unique, indivisible. `ownerOf(tokenId)`.
- **ERC-20 (arcade lab):** fungible, divisible, interchangeable. `balanceOf(addr)`, `transfer`,
  `approve` / `transferFrom`, `allowance`, `totalSupply`.

The reference design for the buy flow is the well-known **Token Vendor** pattern (Speedrun Ethereum
challenge #2), adapted for the classroom: `buyToken()` sells exactly **1 ARC** at an
instructor-configurable ETH price. The default price should be **50 ETH per 1 ARC**.

## Architecture At A Glance

```
  Student lane SPA
      │
      │  write txs via assigned wallet + write-filtered RPC proxy
      ▼
  /labs/ethereum_lab/rpc-write ─────────► instructor Hardhat node
      │                                      │
      │ buyToken() {value: priceWei}         │ TokenVendor mints 1 ARC
      │ approve(vault, n)                    │ ArcadeToken records allowance
      │ playGame(gameId)                     │ ArcadeVault burns ARC + emits SessionStarted
      │                                      ▼
      │                           on-chain ERC-20 state + events
      │
      │  cache-first reads
      ├──────────────────────────────────► /labs/ethereum_lab/arcade-state
      │                                      instructor lab-api cache polls once for everyone
      │
      │  POST {txHash} after playGame()
      └──────────────────────────────────► /api/ethereum/arcade/session
                                             lane-service verifies the receipt/log,
                                             consumes player:nonce once, signs session

  Client-side game (canvas) runs with the session token. Gameplay is OFF-chain.
```

**The architecture rule** (the student already intuited this): on-chain for ownership, payment, and
authorization; off-chain for the actual gameplay. Ball physics never become transactions.

| Concern                         | Where        | Why |
|---------------------------------|--------------|-----|
| Buy tokens, hold a balance      | on-chain     | trustless ownership, real ERC-20 state |
| Pay to start a session          | on-chain     | the enforceable "you must pay" boundary |
| Issue a 10-min play session     | lane-service | shared, class-wide authority; a contract **cannot** sign a JWT |
| Balance/allowance/class reads   | instructor cache | one RPC reader, not one polling loop per browser |
| Run the game, move the paddle   | client (off) | fast, free, needs no consensus |

`/labs/ethereum_lab/rpc` is intentionally unavailable to classroom browsers. Browser writes go
through `/labs/ethereum_lab/rpc-write`, whose proxy rejects read methods such as `eth_call`,
`eth_getBalance`, and `eth_getCode`. The only browser-side RPC reads tolerated there are write
lifecycle helpers needed by ethers around a submitted transaction, such as chain ID, fee data,
nonce, block number, and transaction receipt polling.

## Live Lab Design Constraints

This lab must be wired into the existing live Ethereum lab, not built as an isolated local demo.

- **One shared chain.** The Hardhat node runs only inside `ethereum-trainer-instructor`.
- **Per-student lanes are thin.** Student containers serve the SPA and local lab-api helpers, but they
  must not become the source of shared class state.
- **Shared authority lives in `lane-service`.** Consumed arcade session nonces and any resettable
  classroom arcade state belong under `/api/ethereum/arcade/*`, backed by files in
  `lane-service/runtime/ethereum/`.
- **Instructor deploys and configures contracts.** `scripts/deploy-tokenization-contracts.js` should
  deploy the ERC-20 arcade contracts alongside the NFT contracts during instructor startup. The
  instructor/deployer wallet owns price updates.
- **Browsers write, caches read.** Student browsers may submit transactions through their assigned
  wallet, but routine reads should come from shared cache endpoints (`arcade-state`, `chain-state`,
  marketplace state) instead of polling the RPC port.
- **Direct `/rpc` remains blocked.** Any plan step that needs a browser read must use a cache route
  or a backend cache-refresh/API route, not a browser `eth_call`.
- **Router routes preserve query strings.** Ethereum router locations that use variable
  `proxy_pass` targets must append `$is_args$args`; otherwise explicit cache-refresh flags are
  silently dropped.
- **No host testing.** Local validation runs in containers. Live validation runs on the remote VM using
  `lab-manager.sh` there, then browser MCP against the public endpoint.

## Scalability and Consistency Invariants

These are non-negotiable implementation constraints for the live classroom environment:

- **One shared RPC reader per read model.** The instructor `lab-api` owns polling/indexing for
  arcade state. Student browsers poll compact JSON only.
- **No shared authority in student lanes.** Student containers can render the SPA and hold
  per-session state, but consumed arcade nonces, resets, and class-wide state live in `lane-service`.
- **Session identity is UUID-backed.** Arcade session issuance should associate activity with the
  active `ethereum_session` UUID and the assigned wallet from the backend session store. Browser
  localStorage must not be the source of truth.
- **On-demand cache refresh beats direct reads.** If the UI needs a fresh transaction/block/session
  detail, it should request a backend cache fill with rate limiting, then reread the cache.
- **Deployment config is the single source of addresses.** Instructor startup writes arcade
  addresses/constants into `tokenization-config.json` and `/api/config.json`; lane-service propagates
  those values into student lanes.
- **The vendor treasury is explicit.** Student purchase ETH should not sit indefinitely in the
  vendor. The vendor forwards or sweeps ETH to a configured treasury address, defaulting to the
  instructor/deployer/default Hardhat wallet unless `ARCADE_TREASURY_ADDRESS` overrides it.
- **Chain reset/prune awareness.** Any indexer must detect head rollback and clear/rebuild its
  in-memory state. Contract deployment must still complete before the Beacon conductor snapshots.

## Why "the smart contract signs the auth token" can't work literally

A smart contract has **no private key**. It can *verify* a signature on-chain (`ecrecover`) but
cannot *produce* one, so it cannot mint a JWT or sign any off-chain message. The intent — "prove on
chain that the student paid, then grant a session" — is achieved by splitting the two meanings of
"token":

1. The **fungible ERC-20** the contract mints (ARC). The contract does this.
2. The **JWT session token** the backend signs. The backend (which *does* hold a key) does this,
   gated by an on-chain `SessionStarted` event.

So the contract is the source of truth for payment; the backend is the issuer of the session token.

## Token Economics

Tunable constants; on a free lab chain the absolute ETH numbers don't matter, the **ratio** is what
teaches fungibility.

- `ArcadeToken` decimals: **18** (standard/realistic; the UI formats with `ethers.formatUnits`).
  A simpler alternative is `decimals = 0` so `balanceOf` reads as a whole number of plays, at the
  cost of hiding the wei-style scaling lesson. Recommendation: keep 18 for realism, format in the UI.
- Vendor price: **default `50 ETH = 1 ARC`**, stored as `arcadeTokenPriceWei` in deployment config
  and as mutable contract state on `TokenVendor`.
- Purchase unit: students buy **exactly 1 ARC per transaction**. This keeps the classroom action
  legible: one purchase gives one playable token.
- Instructor price control: the instructor/deployer can update the price from the instructor UI.
  The UI should display the current cached price and the last price-update transaction.
- Play cost: `PLAY_COST = 1 ARC` per game start.
- Net: 50 ETH → 1 ARC → 1 play by default. Students can buy again to replay, and can still transfer
  spare ARC to classmates if they choose.
- Treasury: purchase ETH is forwarded to, or sweepable into, the configured instructor/default
  treasury wallet so arcade purchases recycle value back into the classroom wallet.

## Smart Contracts

Use OpenZeppelin as the base for all three. Solidity ^0.8.x (built-in overflow checks). Do not reuse
the existing `SimpleFT.sol` for this lab: it is useful as an educational minimal token, but it is not
a real ERC-20 and does not teach `approve`, `allowance`, `transferFrom`, or standard ERC-20 events
correctly.

### 1. `ArcadeToken` — ERC20Burnable

- `ERC20` + `ERC20Burnable` (so the vault can `burnFrom`). Name "Arcade Token", symbol "ARC".
- Minting authority: grant the `TokenVendor` a minter role (`Ownable`/`AccessControl`).
  - **Primary:** mint-on-purchase (uncapped) — simplest for unlimited classroom scale, no
    "vendor out of stock" failure mode.
  - **Alt (more realistic):** fixed supply pre-minted to the vendor, which sells from inventory;
    owner can top up. Teaches fixed supply but can run dry mid-class.
- Standard events students will inspect: `Transfer`, `Approval`.

### 2. `TokenVendor` — the instructor-priced buy desk

```solidity
uint256 public constant TOKENS_PER_PURCHASE = 1e18;  // 1 ARC with 18 decimals
uint256 public tokenPriceWei = 50 ether;             // instructor-configurable
address payable public treasury;                     // default instructor/deployer wallet

event TokenPurchased(address indexed buyer, uint256 ethIn, uint256 tokensOut, uint256 priceWei);
event TokenPriceUpdated(uint256 oldPriceWei, uint256 newPriceWei, address indexed updatedBy);
event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);

function buyToken() external payable nonReentrant {  // mints exactly 1 ARC to msg.sender
    require(msg.value == tokenPriceWei, "wrong ETH amount");
    token.mint(msg.sender, TOKENS_PER_PURCHASE);
    (bool ok, ) = treasury.call{value: msg.value}("");
    require(ok, "treasury transfer failed");
    emit TokenPurchased(msg.sender, msg.value, TOKENS_PER_PURCHASE, tokenPriceWei);
}

function setTokenPriceWei(uint256 newPriceWei) external onlyOwner {
    require(newPriceWei > 0, "price required");
    emit TokenPriceUpdated(tokenPriceWei, newPriceWei, msg.sender);
    tokenPriceWei = newPriceWei;
}

function setTreasury(address payable nextTreasury) external onlyOwner { ... }
function sweep() external onlyOwner { ... }          // safety valve for any stuck ETH
```

Skip `sellTokens()` for the MVP. It adds reserve/accounting complexity and is not needed for the
core classroom loop. The `approve` / `transferFrom` lesson already happens in `ArcadeVault` when a
student spends ARC to play. Guard ETH-sending paths with `ReentrancyGuard`; the treasury should
default to the instructor/deployer wallet but be configurable at deploy time.

### 3. `ArcadeVault` — the spend / "pay to play" sink

```solidity
uint256 public constant PLAY_COST = 1e18;            // 1 ARC (18 decimals)
mapping(address => uint256) public sessionNonce;     // per-player, monotonic, anti-replay
event SessionStarted(address indexed player, uint8 indexed gameId, uint256 nonce, uint256 timestamp);

function playGame(uint8 gameId) external {
    token.burnFrom(msg.sender, PLAY_COST);           // requires approve(vault, >=PLAY_COST) first
    uint256 nonce = ++sessionNonce[msg.sender];
    emit SessionStarted(msg.sender, gameId, nonce, block.timestamp);
}
```

Using **burn** (not transfer-to-vault) makes the sink legible: `totalSupply` visibly drops as
students play. `burnFrom` requires the student to `approve` the vault first — an extra tx, but that
mirrors the NFT lab's "approve the sale contract" step and is itself a core ERC-20 lesson
(`approve` / `allowance` / spender-pulls-tokens). A one-time large/`max` approval avoids approving
per play.

## Backend — live session authority and shared cache

The backend is split deliberately:

- **`lane-service` is authoritative for arcade sessions.** It owns nonce consumption and resettable
  class state because it is shared across all student lanes.
- **The instructor `server/lab-api.js` owns cache fan-in.** It polls the shared Hardhat node once,
  builds a compact read model, and serves it to every browser through the router.
- **Student-lane `server/lab-api.js` must not store arcade authority.** Per-lane memory disappears
  when lanes recycle and would let different students consume the same burn nonce independently.

### `lane-service` session issuance

Add these routes in `../lane-service/labs/ethereum.py`:

```
GET /api/ethereum/arcade/state
  -> { consumedSessions, recentSessions }        // no RPC; persisted class state only

POST /api/ethereum/arcade/session
  body: { txHash }            // the playGame() transaction
  steps:
    1. Fetch the tx receipt from the instructor RPC; require status == success.
    2. Find a SessionStarted log emitted by the known ArcadeVault address; decode
       (player, gameId, nonce, timestamp).
    3. Reject if already consumed: key = `${player}:${nonce}` in persisted lane-service state.
       Reject if the block timestamp is too old.
    4. Persist consumption. Sign and return an HS256 session token:
         { sid: ethereum_session_uuid, sub: player, game: gameId, nonce, iat, exp: iat + 600 }
       signed with ARCADE_JWT_SECRET (env, or runtime-generated fallback). 10-minute lifetime.
  → { token: "<jwt>", game, exp }

POST /api/ethereum/arcade/reset
  instructor-only; clears consumed arcade session state, not the chain
```

Notes:

- **Verification is from the chain, not the client.** The client sends only a `txHash`; the backend
  re-derives player/gameId/nonce from the on-chain log so a forged body can't mint a session.
- **One burn = one session.** The nonce is single-use (consumed at issuance). To play again, burn
  again. Short `exp` (10 min) is just the join window.
- **Use persisted state.** Store consumed nonces in
  `lane-service/runtime/ethereum/tokenization-arcade-state.json` with atomic writes, mirroring the
  NFT state pattern.
- **Use stdlib signing if possible.** Python can issue HS256 with `hmac`, `hashlib`, and base64url
  encoding; do not add a JWT dependency unless there is a clear need.

### Instructor cache fan-in

Add an instructor-only poller in `server/lab-api.js`, guarded like the existing beacon/chain/
marketplace pollers (`MODE !== 'student'`):

```
GET /lab-api/arcade/state
  -> {
       ok,
       token,
       vendor,
       vault,
       tokenPriceWei,
       treasury,
       totalSupply,
       balances,        // address(lower) -> token balance string
       allowances,      // owner(lower) -> vault allowance string
       recentBuys,
       recentPriceUpdates,
       recentApprovals,
       recentSessions,
       at,
       ageMs,
       cache: { pollMs, stale, staleAfterMs, refreshing }
     }

POST /lab-api/arcade/state
  body: { refresh: true, address?: "0x...", txHash?: "0x..." }
  -> rate-limited cache refresh/fill for explicit "verify on chain" actions.
     The server may read RPC; browsers still receive only JSON cache state.
```

The poller should:

- read deployed addresses from `frontend/public/labs/ethereum_lab/tokenization-config.json`;
- rate-limit explicit refreshes by area (for example `address:<addr>` or `tx:<hash>`) so one student
  cannot turn "verify" into a node hammer;
- read `tokenPriceWei()` and `treasury()` each poll so instructor price changes appear without
  browser RPC reads;
- index `TokenPurchased`, `TokenPriceUpdated`, ERC-20 `Transfer`, ERC-20 `Approval`, and
  `SessionStarted` logs incrementally;
- reconstruct balances from `Transfer` events, including mints from `address(0)` and burns to
  `address(0)`;
- reconstruct vault allowances from the most recent `Approval(owner, vault, amount)`;
- reset its in-memory index if the chain head moves backwards after a prune/revert;
- never run in student lanes.

Add a router alias in `../router/routes/ethereum.conf`:

```
location = /labs/ethereum_lab/arcade-state {
    set $target_host "ethereum-trainer-instructor";
    proxy_pass http://$target_host:8080/lab-api/arcade/state$is_args$args;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Origin "";
}
```

Optional score endpoint (only if the achievement capstone is built):

```
POST /api/ethereum/arcade/score   body: { token, score, runProof }
  - verify JWT (valid, unexpired, game matches); the nonce in the JWT is the one-time key
  - best-effort sanity checks (see "Anti-cheat"); if it qualifies, authorize an achievement NFT mint
```

## Frontend — `ArcadeLabView.jsx`

A new view mirroring the NFT view's manifest-backed, explorer-centered style. No reservation model —
unlike the NFT lab (one student per theme), the arcade is shared: every student can buy ARC and play.

The UI should be **cache-first for reads** and **wallet-first for writes**:

- Writes use `ethers.Contract(..., wallet.signer)` and the `/rpc-write` provider from runtime
  config. Do not point the browser at `/rpc`.
- Reads use `/labs/ethereum_lab/arcade-state` by default.
- Direct `balanceOf`, `allowance`, `totalSupply`, `queryFilter`, `getCode`, and broad explorer reads
  are not browser operations. Explicit "verify on chain" controls should call a backend cache refresh
  route and then reread the cache.
- Transaction receipt polling after a submitted buy/approve/play transaction is acceptable through
  `/rpc-write`, because `eth_getTransactionReceipt` is part of the write lifecycle.
- The view must not trigger Live dashboard sync, `BlockchainSync`, or broad explorer polling on load.

Panels:

1. **Buy** — "Buy 1 ARC for `<cached price>`" → `vendor.buyToken({ value: tokenPriceWei })`.
   Show cached `balanceOf(me)`, `totalSupply`, current price, and treasury.
2. **Approve** — `token.approve(vaultAddr, amount)` (offer a one-time max approval). Show cached
   `allowance(me, vault)`.
3. **Play** — three game cards. "Play (1 ARC)" →
   `vault.playGame(gameId)` → await receipt → read `SessionStarted` nonce →
   `POST /api/ethereum/arcade/session {txHash}` → receive JWT → launch the game component with it.
4. **Explorer** — the teaching surface (see workflow below).

UX requirements:

- Every disabled action must state the exact blocker: no wallet, contracts missing, insufficient ARC,
  allowance missing, transaction pending, session issuance failed, or cache stale.
- If the cached price is missing or stale, disable Buy and show "class price cache updating" rather
  than guessing a value.
- After a buy, approve, or play transaction, optimistically show the receipt hash and then let the
  cache catch up.
- If the cache is stale, show a visible "class cache updating" status. Offer a manual cache refresh
  button if needed, backed by a server-side rate limit, instead of silently reading RPC in a loop.
- Game launch is secondary. Progress should advance once the on-chain burn/session event is verified,
  even if the canvas game later fails.

Instructor UI requirements:

- Add an Arcade pricing control in `InstructorView` or the tokenization instructor panel.
- Show current cached `tokenPriceWei`, treasury address, and recent price updates.
- Allow the instructor to submit `setTokenPriceWei(newPriceWei)` through the instructor wallet.
- Default display should be `50 ETH per 1 ARC`; the control should make it clear that changing the
  price affects future purchases only.
- Optional: expose `setTreasury()` only as an advanced instructor control. Most classes should leave
  treasury at the deployer/default wallet.

## The Games (client-side canvas, original names + Ethereum theme)

Three shallow, single-level HTML5-canvas games (`requestAnimationFrame`, vector shapes, no art
assets, keyboard controls), each a self-contained React component. **Original names** both to avoid
IP issues (consistent with the NFT plan's "no copyrighted characters" rule) and to reinforce the
lab's theme. Mechanics mirror the classics the requester named:

| Game | Classic it mirrors | One-level concept |
|------|--------------------|-------------------|
| **Block Breaker** | Breakout / Arkanoid | paddle bounces a ball to break a wall of transaction "blocks"; clear them all → "block confirmed" |
| **Mempool Invaders** | Space Invaders | waves of descending pending transactions; shoot to "confirm" them before they reach the chain; clear the wave |
| **Gas Climber** | Donkey Kong | climb girders/ladders dodging rolling "gas" barrels to reach the top |

Each exposes a simple lifecycle: `start(jwt)` → win/lose → optional `submitScore()`.

## Anti-cheat — what is and isn't defensible (read this)

A **pure client-side game cannot be made cheat-proof.** A determined student can open devtools and
call the win function or replay the loop. We should be honest about which boundary we actually
enforce:

- **Enforced (hard boundary): "you must pay to get a session."** There is no valid session JWT
  without an on-chain `burnFrom`, verified by the backend from the chain log. You cannot mint a
  session for free. Mitigations: single-use nonce, 10-minute expiry, JWT bound to `player + game +
  nonce`.
- **Best-effort (soft boundary): gameplay/score integrity.** For a shallow one-level game whose only
  reward is fun, low stakes — accept it. If scores gate a reward (the achievement capstone),
  add server-side sanity checks: minimum play duration, plausible/monotonic event stream, score
  caps, and never trust a raw client score. Optionally stream lightweight telemetry the server
  spot-checks. None of this is cryptographically secure, and that's an acceptable, *documented*
  trade-off for a teaching lab.
- **Bonus teaching moment.** This *is* the lesson: web3 trust boundaries. What you can enforce
  trustlessly (payment) versus what you can't (off-chain computation) is exactly the distinction the
  lab should make explicit.

Recommendation: ship the JWT-gated version (it teaches the real pattern and enforces the paywall),
document the residual client-side risk, and don't over-invest in anti-cheat for one-level games.

## Optional Capstone — links the two labs

Beating a game emits a score; the backend verifies it (best-effort) and authorizes the student to
**mint an achievement NFT** from the ERC-721 contract. **ERC-20 spent → ERC-721 earned**, tying the
fungible and non-fungible halves of the Tokenization Lab into one arc. Implement either as a
backend-held minter role or a signed voucher the student redeems on-chain. Keep it optional and out
of the MVP.

## Explorer-Centered Workflow

Mirror the NFT plan: make the explorer central to every action.

1. Buy 1 ARC for the current instructor-set ETH price; inspect the `buyToken` receipt, the
   `TokenPurchased` event, and the `Transfer(0x0 → you)` mint event.
2. Inspect cached `balanceOf(you)` and `totalSupply()` from `/arcade-state`; if needed, request a
   backend cache refresh rather than calling browser RPC.
3. `approve` the ArcadeVault; inspect the `Approval` event and `allowance(you, vault)`.
4. `playGame(gameId)`; inspect the receipt, the `Transfer(you → 0x0)` burn event, the
   `SessionStarted` event, the dropped cached `totalSupply`, and your reduced cached `balanceOf`.
5. Backend issues the session JWT from that on-chain event; play the game off-chain.
6. (Optional) Submit score → mint achievement NFT; inspect that mint in the NFT contract.

## Implementation Phases

### Phase 1 — Contracts and unit tests

Files:

- `contracts/ArcadeToken.sol`
- `contracts/TokenVendor.sol`
- `contracts/ArcadeVault.sol`
- `test/ArcadeTokenLab.test.js`

Acceptance criteria:

- buying 1 ARC through `TokenVendor.buyToken()` requires exactly the current `tokenPriceWei`;
- a successful purchase mints exactly `1e18` ARC to the buyer and forwards/sweeps ETH to the
  treasury/default wallet;
- `setTokenPriceWei()` is `onlyOwner`, rejects zero price, and emits `TokenPriceUpdated`;
- `balanceOf`, `totalSupply`, and `Transfer(address(0), buyer, amount)` reflect the buy;
- `token.approve(vault, amount)` emits `Approval` and updates `allowance`;
- `vault.playGame(gameId)` requires allowance and balance;
- `playGame` burns exactly `PLAY_COST`, decrements `totalSupply`, increments per-player nonce, and
  emits `SessionStarted(player, gameId, nonce, timestamp)`;
- insufficient balance/allowance paths revert with clear messages.

### Phase 2 — Instructor deployment and config

Files:

- `scripts/deploy-tokenization-contracts.js`
- `docker-entrypoint.sh`
- `scripts/copy-token-artifacts.js`
- `frontend/src/contracts/*.json`
- `frontend/public/labs/ethereum_lab/tokenization-config.json`

Deployment wiring:

- deploy arcade contracts during instructor startup, immediately after the NFT tokenization contracts;
- grant `TokenVendor` mint authority on `ArcadeToken`;
- verify bytecode with `provider.getCode` for all deployed contracts;
- copy `ArcadeToken`, `TokenVendor`, and `ArcadeVault` artifacts into `frontend/src/contracts/`;
- write these fields to `frontend/public/labs/ethereum_lab/tokenization-config.json` and `frontend/dist/...`:
  - `arcadeTokenAddress`
  - `arcadeVendorAddress`
  - `arcadeVaultAddress`
  - `arcadeTokenPriceWei`
  - `arcadeTreasuryAddress`
  - `arcadePlayCost`
- default `arcadeTokenPriceWei` to `50 ether`, configurable by environment variable
  (`ARCADE_TOKEN_PRICE_ETH` or equivalent) before deployment;
- default `arcadeTreasuryAddress` to the instructor/deployer/default wallet unless
  `ARCADE_TREASURY_ADDRESS` is set;
- include the same fields in instructor `/api/config.json`;
- add student-mode env/config propagation so lane-created `/api/config.json` exposes the same fields;
- keep NFT config fields intact (`nftAddress`, `saleAddress`, `marketplaceAddress`, `updatedAt`) so
  the existing NFT lab and marketplace continue to work.

### Phase 3 — Shared backend state in lane-service

Files:

- `../lane-service/labs/ethereum.py`
- `../lane-service/labs/ethereum_catalog.py`

Work:

- extend runtime config fetch/cache to include arcade addresses and constants;
- inject arcade config into student lane environment and generated `/api/config.json`;
- expose `GET /api/ethereum/arcade/state`;
- expose `POST /api/ethereum/arcade/session`;
- expose instructor-only `POST /api/ethereum/arcade/reset`;
- persist consumed sessions under `STATE_DIR / "tokenization-arcade-state.json"`;
- verify `POST /api/ethereum/arcade/session` from the submitted transaction receipt only; never trust
  client-supplied `player`, `gameId`, or `nonce`;
- bind issued session tokens to `{ ethereum_session UUID, player, gameId, nonce }`;
- add progress IDs:
  - `eth-ft-load`
  - `eth-ft-buy`
  - `eth-ft-approve`
  - `eth-ft-play`
  - `eth-ft-burn-verify`

### Phase 4 — Instructor cache and router path

Files:

- `server/lab-api.js`
- `../router/routes/ethereum.conf`

Work:

- add an instructor-only arcade poller in `server/lab-api.js`;
- expose `GET /lab-api/arcade/state`;
- route `/labs/ethereum_lab/arcade-state` to the instructor cache and preserve query strings with
  `$is_args$args`;
- ensure the poller never runs in `MODE=student`;
- keep cache payloads compact enough for frequent browser polling.
- index incrementally from the last processed block and reset the index if chain height moves
  backward;
- include `ageMs`, `pollMs`, `stale`, and `refreshing` metadata so the UI can communicate cache lag
  without falling back to direct RPC reads.

### Phase 5 — Frontend Arcade lab

Files:

- `frontend/src/views/ArcadeLabView.jsx`
- `frontend/src/views/InstructorView.jsx`
- `frontend/src/App.jsx`
- `frontend/src/constants/labs.js`
- `frontend/src/contracts/ArcadeToken.json`
- `frontend/src/contracts/TokenVendor.json`
- `frontend/src/contracts/ArcadeVault.json`

Work:

- add `arcade-lab` as a deep-linkable view;
- add `arcade-lab` to `SHAREABLE_QUERY_VIEWS`, `LAB_ENABLED`, URL parsing, wallet auto-load view
  lists, `CACHE_BACKED_NODE_STATUS_VIEWS`, and the progress route map;
- add a sidebar/nav entry near Tokenization Lab and NFT Marketplace;
- load config from `/api/config.json` and static `tokenization-config.json`;
- use `/labs/ethereum_lab/arcade-state` for balances, allowances, total supply, and recent actions;
- use direct contract writes only for buy, approve, and play through `/rpc-write`;
- keep balance/allowance/supply reads out of browser RPC calls; explicit verification should request a
  cache refresh and then reread `/arcade-state`;
- add instructor-only price controls that call `setTokenPriceWei()` and then let `/arcade-state`
  reflect the updated price;
- add one working canvas game first, then add the other two shells/skins;
- gate progress on successful on-chain actions and session issuance, not on high-score integrity.

### Phase 6 — Container and live validation

Local validation:

- run only in the existing Docker/fullstack lab container setup;
- do not build or test on the host;
- verify contract tests inside a container;
- verify the SPA through the container-bound lab endpoint.

Remote deployment:

- rsync changed `ethereum_lab` files to
  `/home/ubuntu/courseware-builder-pipeline/dynamic-labs/ethereum_lab`;
- rsync `lane-service` and `router` changes to sibling directories;
- on `ubuntu@blockchain.training-as-code.com`, rebuild `ethereum-trainer`;
- rebuild `lane-service`;
- restart through remote `lab-manager.sh`;
- restart/reload router only through `lab-manager.sh` when route files change;
- restart only the ethereum lab/lane-service targets needed for the change;
- clear only ethereum student lane containers when new student config and bundles are required.

Browser MCP validation against the public endpoint:

1. Open `https://blockchain.training-as-code.com/labs/ethereum_lab/?view=arcade-lab`.
2. Confirm claim flow preserves `?view=arcade-lab`.
3. Confirm assigned wallet imports before any random wallet is created.
4. Confirm the Buy panel shows the default/current price, initially `50 ETH per 1 ARC`.
5. Buy 1 ARC from the UI and watch cached balance/totalSupply update.
6. Confirm the purchase ETH is forwarded/sweepable to the configured treasury/default wallet.
7. As instructor, change the ARC price and confirm the student Buy panel updates from `/arcade-state`.
8. Approve the vault from the UI and watch cached allowance update.
9. Start a game from the UI and verify ARC burns, nonce increments, progress advances, and a session
   token is issued.
10. Inspect the same buy, approval, burn, and `SessionStarted` events in the explorer/cache UI.

## Implementation Notes

- Keep `arcadeTokenPriceWei`, `arcadeTreasuryAddress`, `PLAY_COST`, and JWT lifetime centralized in
  deployment config and UI labels.
- If purchases should replenish the top-off faucet bank specifically, set `ARCADE_TREASURY_ADDRESS`
  to that bank address. Otherwise the default is the instructor/deployer wallet.
- The MVP should include buy, approve, burn/session, and one playable canvas game. The other two games
  can be thin variants once the payment/session loop is solid.
- Avoid adding heavyweight backend dependencies. `lane-service` can verify JSON-RPC receipts with
  Python stdlib HTTP/JSON and can sign HS256 with stdlib crypto primitives.
- If the Beacon conductor can prune/revert the chain, tokenization mode must freeze pruning before
  FT/NFT exercises begin, or the deployed token contracts and cache indexes can become stale.

## Adjacent NFT Lab Design Fixes

These are not required for the FT arcade MVP, but they should be considered while touching the
Tokenization lab surface:

- Split NFT flow into clearer sub-tabs: `Mint`, `Your NFTs`, `Marketplace`, and `Explorer`.
- After a theme claim, collapse unavailable themes and present the claimed theme as a locked receipt.
- Keep ownership/marketplace reads cache-first by default; put direct `ownerOf`, `tokenURI`, and
  `queryFilter` calls behind explicit "Verify on chain" controls.
- Add an instructor/status banner when Tokenization mode freezes the Beacon lab and chain pruning.
- Make failed mints actionable by showing the exact blocker: wallet, claim state, minted-batch state,
  contract cap, stale config, receipt failure, or cache lag.
