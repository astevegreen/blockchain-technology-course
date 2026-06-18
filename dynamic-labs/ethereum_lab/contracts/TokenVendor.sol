// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

interface IArcadeTokenMint {
    function mint(address to, uint256 amount) external;
}

/**
 * @title TokenVendor
 * @dev Instructor-priced desk that sells exactly one ARC per purchase.
 */
contract TokenVendor is Ownable, ReentrancyGuard {
    uint256 public constant TOKENS_PER_PURCHASE = 1 ether;

    IArcadeTokenMint public immutable token;
    uint256 public tokenPriceWei;
    address payable public treasury;

    event TokenPurchased(address indexed buyer, uint256 ethIn, uint256 tokensOut, uint256 priceWei);
    event TokenPriceUpdated(uint256 oldPriceWei, uint256 newPriceWei, address indexed updatedBy);
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);
    event Swept(address indexed treasury, uint256 amount);

    constructor(IArcadeTokenMint token_, uint256 tokenPriceWei_, address payable treasury_) {
        require(address(token_) != address(0), "TokenVendor: token required");
        require(tokenPriceWei_ > 0, "TokenVendor: price required");
        require(treasury_ != address(0), "TokenVendor: treasury required");
        token = token_;
        tokenPriceWei = tokenPriceWei_;
        treasury = treasury_;
    }

    function buyToken() external payable nonReentrant {
        require(msg.value == tokenPriceWei, "TokenVendor: wrong ETH amount");
        token.mint(msg.sender, TOKENS_PER_PURCHASE);
        (bool ok, ) = treasury.call{value: msg.value}("");
        require(ok, "TokenVendor: treasury transfer failed");
        emit TokenPurchased(msg.sender, msg.value, TOKENS_PER_PURCHASE, tokenPriceWei);
    }

    function setTokenPriceWei(uint256 newPriceWei) external onlyOwner {
        require(newPriceWei > 0, "TokenVendor: price required");
        emit TokenPriceUpdated(tokenPriceWei, newPriceWei, msg.sender);
        tokenPriceWei = newPriceWei;
    }

    function setTreasury(address payable nextTreasury) external onlyOwner {
        require(nextTreasury != address(0), "TokenVendor: treasury required");
        emit TreasuryUpdated(treasury, nextTreasury);
        treasury = nextTreasury;
    }

    function sweep() external onlyOwner nonReentrant {
        uint256 amount = address(this).balance;
        require(amount > 0, "TokenVendor: nothing to sweep");
        (bool ok, ) = treasury.call{value: amount}("");
        require(ok, "TokenVendor: treasury transfer failed");
        emit Swept(treasury, amount);
    }
}
