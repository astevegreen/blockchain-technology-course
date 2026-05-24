// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

/**
 * @title LabNFTSale
 * @dev Simple single-listing NFT-for-ETH sale. Seller lists, buyer pays, atomic swap.
 * For Tokenization Lab: teaches escrow, approve, and payable patterns.
 */
contract LabNFTSale {
    IERC721 public nft;
    uint256 public tokenId;
    uint256 public price;
    address public seller;

    function list(IERC721 _nft, uint256 _tokenId, uint256 _price) external {
        require(_nft.ownerOf(_tokenId) == msg.sender, "Not owner");
        require(_price > 0, "Price must be > 0");
        nft = _nft;
        tokenId = _tokenId;
        price = _price;
        seller = msg.sender;
        _nft.transferFrom(msg.sender, address(this), _tokenId);
    }

    function buy() external payable {
        require(msg.value == price, "Wrong amount");
        require(seller != address(0), "Not listed");
        address _seller = seller;
        seller = address(0);
        nft.transferFrom(address(this), msg.sender, tokenId);
        payable(_seller).transfer(msg.value);
    }
}
