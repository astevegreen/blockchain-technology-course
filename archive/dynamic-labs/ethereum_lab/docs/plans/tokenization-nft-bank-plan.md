# Tokenization Lab NFT Bank Plan

## Purpose

The Tokenization Lab NFT bank is static course content for the rebuilt ERC-721 workflow. Students choose a theme, mint one or more NFTs from that theme, inspect the resulting transactions and metadata in the lab explorer, then trade or sell those NFTs with classmates on the shared class chain.

The bank should make tokenization concrete:

- An NFT represents ownership of a specific digital asset.
- The image is static course content served by the lab.
- The token metadata points to that image through a stable URL.
- ERC-721 ownership, approval, transfer, sale, and purchase state are enforced on-chain.
- Explorer views should prove minting, ownership, metadata URI, events, approvals, listings, sales, and post-sale ownership.

## Static Asset Strategy

Pre-generate all images before class. Do not generate images live during the lab.

- 40 themes.
- 5 images per theme.
- 200 total images.
- 512x512 PNG target size.
- Images are original Ethereum, mempool, and blockchain-adjacent educational art.
- No pop-culture references, real brands, copyrighted characters, or external dependencies.

Recommended static paths:

- Images: `/labs/ethereum_lab/nft-assets/<theme-slug>/<variant-slug>.png`
- Metadata: `/labs/ethereum_lab/nft-metadata/<theme-slug>/<variant-slug>.json`
- Manifest: `/labs/ethereum_lab/nft-bank/manifest.json`

Workspace locations:

- `frontend/public/labs/ethereum_lab/nft-assets/`
- `frontend/public/labs/ethereum_lab/nft-metadata/`
- `frontend/public/labs/ethereum_lab/nft-bank/manifest.json`

## Claiming And Ownership Model

The lab should separate reservation from ERC-721 ownership.

- Theme reservation: one student checks out a theme, preventing other students from claiming that same theme.
- Token ownership: ERC-721 state determines who owns each minted token at any moment.
- Trading: students can list and buy NFTs from one another through `LabNFTSale`.

Recommended class behavior:

- A student claims one theme.
- The UI locks that theme for everyone else.
- The student may mint one or more of the 5 variants from that theme.
- The student may transfer or list minted NFTs for classmates.
- The explorer shows claimed, minted, owner, metadata URI, approval, listed, sold, and sale-state transitions.

The reservation layer may be implemented later as a simple API-backed class-state store or as an on-chain claim registry. ERC-721 ownership and trading must remain on-chain.

## Theme List

1. Mempool Storms
2. Gas Relics
3. Validator Badges
4. Block Fossils
5. Calldata Glyphs
6. Nonce Keys
7. Fork Artifacts
8. Receipt Scrolls
9. Event Echoes
10. Topic Hash Totems
11. Rollup Cities
12. Bridge Portals
13. Merkle Trees
14. State Roots
15. Storage Slots
16. Smart Contract Blueprints
17. Minting Forges
18. Transfer Trails
19. Approval Seals
20. Escrow Chambers
21. Payable Gates
22. Revert Posters
23. Gas Limit Engines
24. Pending Transaction Lanterns
25. Miner's Archive
26. Beacon Chain Signals
27. Epoch Clocks
28. Block Builder Workshops
29. Execution Layer Maps
30. Address Masks
31. Wallet Sigils
32. Signature Runes
33. Token Vaults
34. Metadata Capsules
35. URI Beacons
36. Explorer Windows
37. Contract Creatures
38. Liquidity Bazaars
39. Atomic Swap Machines
40. Genesis Mint Cards

## Generation Direction

Each theme should have 5 visually distinct variants. The bank should feel cohesive as one collection while still making each claimed theme easy to recognize.

Global style:

- Square 512x512 educational NFT artwork.
- High-detail stylized concept art.
- Clean centered composition.
- Strong silhouette and readable subject.
- No text, lettering, logos, watermarks, signatures, or UI screenshots.
- Original Ethereum-adjacent visual language without using protected brand marks.

Variant naming:

- `variant-01.png`
- `variant-02.png`
- `variant-03.png`
- `variant-04.png`
- `variant-05.png`

Metadata fields:

- `name`
- `description`
- `image`
- `attributes`

The `image` value should use the static lab image path. The `tokenURI` used during minting should point to the matching metadata path.

## Explorer-Centered Workflow

The rebuilt UI should make the explorer central for every major action:

1. Claim a theme.
2. Mint a selected variant.
3. Inspect the mint receipt and `Transfer(address(0), owner, tokenId)` event.
4. Inspect `ownerOf`, `balanceOf`, and `tokenURI`.
5. View metadata JSON and image URL.
6. Transfer to a classmate.
7. Inspect the transfer receipt and new owner.
8. Approve the sale contract.
9. List the NFT for native ETH.
10. Buy the NFT from another account.
11. Verify sale state, payment, ownership, and emitted events.

## Implementation Notes

The static NFT bank should be generated first, then wired into `TokenizationLabView.jsx` through a manifest-backed selector. The manifest should expose enough state for the UI to display theme availability and variant choices, while dynamic claim, mint, listing, and ownership state should come from the class backend and chain reads.
