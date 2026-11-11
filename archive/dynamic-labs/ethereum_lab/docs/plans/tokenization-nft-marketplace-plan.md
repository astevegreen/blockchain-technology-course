# Tokenization Lab — NFT Marketplace Plan

## Why

The current `LabNFTSale` is a **single global escrow slot**: `require(seller == address(0), "Already listed")`
means only one token can be listed in the entire contract at a time, and `buy()` buys *that* token
(no selection). Two students can't list at once, there's nothing to browse, and the NFT is escrowed
away while listed. We want a real **marketplace**: many concurrent listings, browse, buy a specific
one, and relist after you own it.

## Confirmed design decisions (2026-06-03)

1. **Custody: approval-based** (OpenSea-style). The NFT stays in the seller's wallet; they approve the
   marketplace; `buy()` does `transferFrom(seller → buyer)`. Teaches approve/allowance, supports
   multiple listings and instant relist. Stale listings (seller moved the NFT) are handled by a
   current-owner re-check in `buy`.
2. **Replace `LabNFTSale`** with `LabNFTMarketplace`. One sale mechanism; the guided
   list → classmate buys → relist steps all use the marketplace.
3. **Ownership via event indexing**: the instructor `lab-api` tracks ERC-721 `Transfer` events to know
   the current owner of each token (no contract change to `LabNFT`, no extra gas) and serves it in the
   cache for "Your Assets" + relist.
4. **Dedicated Marketplace view/tab** (top-level, like a lab tab), plus owned-NFTs surfaced in the
   main-page "Your Assets" panel.

## Contract: `LabNFTMarketplace.sol`

Approval-based, multi-listing, generic over any ERC-721 (the lab only uses `LabNFT`).

```solidity
struct Listing { uint256 id; address seller; address nft; uint256 tokenId; uint256 price; bool active; }
uint256 public nextListingId = 1;
mapping(uint256 => Listing) public listings;

event Listed(uint256 indexed id, address indexed seller, address indexed nft, uint256 tokenId, uint256 price);
event Sale(uint256 indexed id, address indexed buyer, address indexed seller, address nft, uint256 tokenId, uint256 price);
event Cancelled(uint256 indexed id, address indexed seller, address nft, uint256 tokenId);
event PriceUpdated(uint256 indexed id, uint256 newPrice);

function list(address nft, uint256 tokenId, uint256 price) external returns (uint256 id);
//   require ownerOf(tokenId)==msg.sender; require price>0;
//   require getApproved(tokenId)==this || isApprovedForAll(seller,this)  (so buy can pull it)
function updatePrice(uint256 id, uint256 newPrice) external; // seller only, active only
function cancelListing(uint256 id) external;                 // seller only -> active=false
function buy(uint256 id) external payable nonReentrant;
//   require active; require msg.value==price;
//   require ownerOf(tokenId)==seller (stale check); active=false BEFORE transfers (CEI);
//   nft.transferFrom(seller, msg.sender, tokenId); (bool ok,)=seller.call{value:msg.value}("");
//   emit Sale(...)
function getActiveListings(uint256 cursor, uint256 limit) external view returns (Listing[] memory);
```

- **Security:** `ReentrancyGuard`; checks-effects-interactions (flip `active=false` before transfers);
  push ETH with `.call` + success check; stale-owner re-check so a moved NFT reverts cleanly.
- The NFT **never leaves the seller's wallet** until a sale; relist = call `list()` again with a fresh id.
- `getActiveListings` is a paginated on-chain fallback; the UI normally reads the cache (below).

## Deploy + config

- `scripts/deploy-tokenization-contracts.js`: deploy `LabNFT` + `LabNFTMarketplace` (drop `LabNFTSale`).
  Write `marketplaceAddress` into `tokenization-config.json` (and `docker-entrypoint.sh` runtime config
  keys: `tokenizationMarketplaceAddress`). Keep `saleAddress` temporarily for back-compat or remove.
- Reminder (root cause we already fixed): tokenization contracts must deploy **before** the beacon
  conductor starts, so the prune snapshot includes them. See `tokenization-nft-marketplace`'s sibling
  fix in the entrypoint. New contracts inherit that ordering automatically.

## lab-api caches

Two new server-side indexes on the instructor (same RPC-fan-in pattern as `/beacon/state`,
`/chain/state`), revert-safe (re-sync the log cursor after a prune `evm_revert`):

1. **`/marketplace/state`** — incremental `getLogs` of marketplace events → array of **active listings**
   `{ id, seller, nft, tokenId, price, image, name }` (image/name resolved from the manifest by
   tokenURI/token mapping). Drops listings on `Sale`/`Cancelled`. Router: `/labs/ethereum_lab/marketplace-state`.
2. **Ownership index** — incremental `getLogs` of `LabNFT` `Transfer(from,to,tokenId)` →
   `tokenOwner[tokenId] = to` and `owned[address] = Set<tokenId>`. Exposed either in `/chain/state` or a
   small `/nft/owned?address=` endpoint. Powers "Your Assets" and the relist list. Mint = Transfer from
   `0x0`; the cache already needs to handle `0x0` for mints.

## Frontend

- **New `MarketplaceView`** (top-level tab, wired into `App.jsx`: `LAB_ENABLED`, view routing, nav button):
  - **Browse**: grid of live listings from `/marketplace-state` (image, name, price, seller nickname);
    **Buy** (hidden/disabled for your own listings) → `marketplace.buy(id, { value: price })`.
  - **List**: pick an owned NFT → price → `nft.approve(marketplace, tokenId)` (or a one-time
    `setApprovalForAll`) → `marketplace.list(nft, tokenId, price)`.
  - **My listings**: cancel / update price.
- **Your Assets** (main-page panel, `App.jsx`): owned NFTs (from the ownership index) with thumbnail,
  **View in explorer** (deep-link), and **List for sale** (jumps to the marketplace list flow / relist).
- **Explorer deep-linking**: add an `initialQuery` prop to `ChainExplorer` so a token id / tx hash /
  address opens the embedded explorer focused on it. Token table rows, receipts, and asset rows become
  clickable; `tokenURI` opens the metadata JSON.
- **ABI**: add `frontend/src/contracts/LabNFTMarketplace.json`; register in `abiRegistry.js`.

## Explorer-centered workflow (teaching arc)

1. Mint a batch (existing).
2. **Your Assets** shows the NFTs you own → **List for sale** at a price (approve + list).
3. The **Marketplace** shows your listing alongside classmates'.
4. A classmate **buys** it; ownership transfers, ETH moves, listing closes — inspect the `Sale` event +
   new `ownerOf` in the explorer.
5. The buyer now sees it in **their** Your Assets and can **relist** at a new price.

## Build order

1. `LabNFTMarketplace.sol` + hardhat tests (list/buy/cancel/updatePrice, stale-owner revert, reentrancy).
2. Deploy script + config + entrypoint config keys.
3. lab-api: `/marketplace/state` + ownership index + router routes.
4. `MarketplaceView` + nav wiring + ABI registration.
5. Your Assets owned-NFTs + `ChainExplorer` `initialQuery` deep-links.
6. Deploy (local-first) + end-to-end test (list → buy from a 2nd wallet → relist).
