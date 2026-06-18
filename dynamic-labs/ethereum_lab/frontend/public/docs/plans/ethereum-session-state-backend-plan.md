# Ethereum Lab Backend Session State Plan

## Goal

Move student-owned Ethereum lab state out of browser storage and into the lane-service backend, keyed by the claimed lane UUID. A claimed session owns all app state for that student. When the claim is released or discarded, that UUID state is deleted.

## Current Problems

- Browser `localStorage`/`sessionStorage` stores wallet private keys, active wallet selection, progress, nicknames, task completion, runtime overrides, and contract source registry.
- Student lane `lab-api.js` stores process-local state keyed by IP for `hasCreatedWallet`, fund requests, and some NFT state.
- Tokenization NFT theme state is global/address-keyed. Station wallets can be reused, so a discarded claim can block the next claimant if ownership is not tied to UUID.
- Claim release currently wipes progress logs only under wipe policy. There is no Ethereum-specific state cleanup hook.

## Target Model

The lane-service claim UUID is the authoritative student identity:

```text
/app/runtime/ethereum/
  claims/<uuid>.json
  progress/<uuid>.jsonl
  sessions/<uuid>/
    meta.json
    wallets.json
    ui.json
    live.json
    beacon.json
    contract-builder.json
    tokenization.json
    contract-sources.json
    tx-history.json
  tokenization-nft-state.json
```

State classes:

- Session-owned: wallets/private keys, active wallet, nickname, UI progress, task completion, tx history, contract source registry, tokenization claim/mint record.
- Class-owned: deployed contract config, shared beacon/chain/marketplace caches, global NFT theme inventory.
- Ephemeral client-only: loading spinners, hover previews, modal open state, transient status text.

On-chain transactions cannot be deleted without resetting the shared chain. Session discard deletes server metadata and wallet ownership, not historical chain state. New claims receive fresh UUID state, so old tokens/transactions do not affect the new user.

## Backend Design

### Session Store

Add an Ethereum session store in lane-service:

- Resolve UUID from `ethereum_session` cookie or `X-Session-UUID`.
- Store one folder per UUID under `STATE_DIR/sessions`.
- Use atomic JSON writes with `*.tmp` + `replace`.
- Validate namespace names.
- Provide merge/replace helpers.
- Initialize state on claim.
- Wipe state on claim release/discard.

Local/fullstack mode does not run lane-service, so the in-container lab API must
also expose `/api/ethereum/session/*` and store equivalent UUID-scoped JSON
server-side. That fallback is only for container validation and standalone
instructor mode; the live platform remains lane-service authoritative.

### Wallets

The session store owns wallet persistence:

- Initial wallet comes from the station wallet pool and is stored in `wallets.json`.
- Additional generated/imported wallets are POSTed to the session store.
- Browser may hold keys in React memory, but must not persist them in browser storage.
- Public runtime config should no longer be the source of assigned private key after frontend migration.

### NFT Theme Tracker

Keep a central class tracker in lane-service:

- `tokenization-nft-state.json` remains global class state.
- Theme claims are atomic under a single lock and file write.
- A theme is owned by one active UUID.
- A UUID can claim one theme and mint one five-token batch.
- Wallet address is metadata, not the authoritative owner.
- If all themes are claimed, UUIDs without a theme may mint color fallback.
- On UUID discard, release any unminted theme claim and remove session-owned mint metadata as policy requires.

## API Surface

Student/session endpoints:

- `GET /api/ethereum/session/state`
- `PATCH /api/ethereum/session/state/<namespace>`
- `POST /api/ethereum/session/wallets`
- `PATCH /api/ethereum/session/wallets/active`
- `POST /api/ethereum/session/reset`

Tokenization endpoints:

- `GET /api/ethereum/nft/state`
- `POST /api/ethereum/nft/claim`
- `POST /api/ethereum/nft/minted-batch`
- `POST /api/ethereum/nft/reset` instructor only

Instructor endpoints:

- `GET /api/ethereum/sessions`
- `GET /api/ethereum/sessions/<uuid>`

## Frontend Migration

1. Add a small session-state client module for `/api/ethereum/session/*`.
2. Replace wallet persistence in `web3.js` with backend calls and in-memory state.
3. Replace top-level `App.jsx` local storage state with backend session namespaces:
   - `ui`
   - `live`
   - `tx-history`
4. Replace Beacon and Contract Builder task local storage with backend namespaces:
   - `beacon`
   - `contract-builder`
5. Replace contract source registry local storage with backend namespace:
   - `contract-sources`
6. Mount the local lab API at `/api/ethereum/*` and add a server-backed session
   fallback so fullstack container testing uses the same browser contract.
7. Keep transient UI-only state in React.

## Rollout Order

1. Implement backend session store and claim cleanup hook.
2. Migrate tokenization NFT tracker to UUID ownership and atomic updates.
3. Migrate wallet persistence.
4. Migrate active lab UI/task/source state.
5. Remove browser storage fallbacks in managed classroom mode.
6. Add local/fullstack `/api/ethereum/session/*` fallback for container testing.
7. Add static check for student-runtime `localStorage`/`sessionStorage`.

## Acceptance Criteria

- Reloading an active session restores state from backend.
- Releasing/discarding a claim removes `STATE_DIR/sessions/<uuid>`.
- Same browser claiming again receives no old wallet, nickname, task progress, tx history, NFT claim, or contract source state.
- NFT theme ownership is atomic and keyed by active UUID.
- Additional generated/imported keys are persisted only in the session store.
- Student frontend no longer depends on browser storage for managed lab state.
- Local fullstack validation can exercise session state without browser storage
  or a host-side lane-service process.
