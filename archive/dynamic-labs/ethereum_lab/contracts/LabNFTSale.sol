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

    event Listed(address indexed seller, address indexed nft, uint256 indexed tokenId, uint256 price);
    event Purchased(address indexed buyer, address indexed seller, address indexed nft, uint256 tokenId, uint256 price);
    event Cancelled(address indexed seller, address indexed nft, uint256 indexed tokenId);

    function isListed() external view returns (bool) {
        return seller != address(0);
    }

    function list(IERC721 _nft, uint256 _tokenId, uint256 _price) external {
        require(seller == address(0), "Already listed");
        require(_nft.ownerOf(_tokenId) == msg.sender, "Not owner");
        require(_price > 0, "Price must be > 0");
        nft = _nft;
        tokenId = _tokenId;
        price = _price;
        seller = msg.sender;
        _nft.transferFrom(msg.sender, address(this), _tokenId);
        emit Listed(msg.sender, address(_nft), _tokenId, _price);
    }

    function cancel() external {
        require(seller == msg.sender, "Not seller");
        IERC721 _nft = nft;
        uint256 _tokenId = tokenId;
        address _seller = seller;
        seller = address(0);
        price = 0;
        tokenId = 0;
        nft = IERC721(address(0));
        _nft.transferFrom(address(this), _seller, _tokenId);
        emit Cancelled(_seller, address(_nft), _tokenId);
    }

    function buy() external payable {
        require(msg.value == price, "Wrong amount");
        require(seller != address(0), "Not listed");
        IERC721 _nft = nft;
        uint256 _tokenId = tokenId;
        uint256 _price = price;
        address _seller = seller;
        seller = address(0);
        price = 0;
        tokenId = 0;
        nft = IERC721(address(0));
        _nft.transferFrom(address(this), msg.sender, _tokenId);
        payable(_seller).transfer(msg.value);
        emit Purchased(msg.sender, _seller, address(_nft), _tokenId, _price);
    }
}
