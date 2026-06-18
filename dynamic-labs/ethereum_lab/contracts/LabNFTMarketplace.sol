// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title LabNFTMarketplace
 * @dev Approval-based, multi-listing NFT marketplace for the Tokenization Lab.
 *
 * The NFT stays in the seller's wallet — they approve this marketplace (approve(marketplace, tokenId)
 * or setApprovalForAll) and `buy()` pulls the token from the seller to the buyer while forwarding ETH
 * to the seller. Many sellers can have many listings at once; sellers can cancel, change price, and
 * relist after re-acquiring a token. Replaces the single-slot LabNFTSale.
 *
 * Teaches: approve/allowance, listings as offers (not escrow), and atomic settlement.
 */
contract LabNFTMarketplace is ReentrancyGuard {
    struct Listing {
        uint256 id;
        address seller;
        address nft;
        uint256 tokenId;
        uint256 price;
        bool active;
    }

    uint256 public nextListingId = 1;
    uint256 public activeCount;
    mapping(uint256 => Listing) public listings;

    event Listed(uint256 indexed id, address indexed seller, address indexed nft, uint256 tokenId, uint256 price);
    event Sale(uint256 indexed id, address indexed buyer, address indexed seller, address nft, uint256 tokenId, uint256 price);
    event Cancelled(uint256 indexed id, address indexed seller, address nft, uint256 tokenId);
    event PriceUpdated(uint256 indexed id, uint256 newPrice);

    function _approvedForMarketplace(address nft, address owner, uint256 tokenId) internal view returns (bool) {
        return IERC721(nft).getApproved(tokenId) == address(this)
            || IERC721(nft).isApprovedForAll(owner, address(this));
    }

    /// @notice List an NFT you own for `price` wei. Approve this marketplace for the token first
    /// (approve(marketplace, tokenId) or setApprovalForAll). The NFT stays in your wallet until sold.
    function list(address nft, uint256 tokenId, uint256 price) external returns (uint256 id) {
        require(price > 0, "Marketplace: price must be > 0");
        require(IERC721(nft).ownerOf(tokenId) == msg.sender, "Marketplace: not owner");
        require(_approvedForMarketplace(nft, msg.sender, tokenId), "Marketplace: approve marketplace first");
        id = nextListingId++;
        listings[id] = Listing({ id: id, seller: msg.sender, nft: nft, tokenId: tokenId, price: price, active: true });
        activeCount++;
        emit Listed(id, msg.sender, nft, tokenId, price);
    }

    /// @notice Change the asking price of one of your active listings.
    function updatePrice(uint256 id, uint256 newPrice) external {
        Listing storage l = listings[id];
        require(l.active, "Marketplace: not active");
        require(l.seller == msg.sender, "Marketplace: not seller");
        require(newPrice > 0, "Marketplace: price must be > 0");
        l.price = newPrice;
        emit PriceUpdated(id, newPrice);
    }

    /// @notice Remove your listing from sale (the NFT was never escrowed, so nothing to return).
    function cancelListing(uint256 id) external {
        Listing storage l = listings[id];
        require(l.active, "Marketplace: not active");
        require(l.seller == msg.sender, "Marketplace: not seller");
        l.active = false;
        activeCount--;
        emit Cancelled(id, l.seller, l.nft, l.tokenId);
    }

    /// @notice Buy a listed NFT: pays the seller and pulls the token from the seller to you.
    function buy(uint256 id) external payable nonReentrant {
        Listing storage l = listings[id];
        require(l.active, "Marketplace: not active");
        require(msg.value == l.price, "Marketplace: wrong ETH amount");
        // Stale-listing guard: the seller may have moved/sold the token outside the marketplace, or
        // revoked approval. Re-check both so we never take ETH for a token we can't deliver.
        require(IERC721(l.nft).ownerOf(l.tokenId) == l.seller, "Marketplace: seller no longer owns token");
        require(_approvedForMarketplace(l.nft, l.seller, l.tokenId), "Marketplace: approval revoked");

        // Checks-effects-interactions: close the listing BEFORE any external call.
        address seller = l.seller;
        address nft = l.nft;
        uint256 tokenId = l.tokenId;
        uint256 price = l.price;
        l.active = false;
        activeCount--;

        IERC721(nft).transferFrom(seller, msg.sender, tokenId);
        (bool ok, ) = payable(seller).call{value: price}("");
        require(ok, "Marketplace: ETH transfer to seller failed");
        emit Sale(id, msg.sender, seller, nft, tokenId, price);
    }

    /// @notice Paginated active listings. On-chain fallback for the UI, which normally reads the
    /// instructor's /marketplace/state cache. Pass cursor=0 to start; nextCursor=0 means done.
    function getActiveListings(uint256 cursor, uint256 limit) external view returns (Listing[] memory page, uint256 nextCursor) {
        if (limit == 0) limit = 50;
        Listing[] memory tmp = new Listing[](limit);
        uint256 n = 0;
        uint256 i = cursor == 0 ? 1 : cursor;
        for (; i < nextListingId && n < limit; i++) {
            if (listings[i].active) { tmp[n] = listings[i]; n++; }
        }
        page = new Listing[](n);
        for (uint256 j = 0; j < n; j++) page[j] = tmp[j];
        nextCursor = (i >= nextListingId) ? 0 : i;
    }
}
