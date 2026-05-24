// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

/**
 * @title LabNFT
 * @dev Full ERC-721 implementation for the Tokenization Lab.
 * Students learn: balanceOf, ownerOf, approve, transferFrom, tokenURI, mint.
 * Uses ERC721URIStorage for per-token metadata (data URIs or URLs).
 */
contract LabNFT is ERC721, ERC721URIStorage {
    uint256 private _nextTokenId;
    address public minter;

    modifier onlyMinter() {
        require(msg.sender == minter, "LabNFT: only minter");
        _;
    }

    constructor(string memory name_, string memory symbol_) ERC721(name_, symbol_) {
        minter = msg.sender;
        _nextTokenId = 1;
    }

    /**
     * @dev Mints a new token to `to` with the given `tokenURI`.
     * Only the deployer (minter) can call this.
     */
    function mint(address to, string memory tokenURI_) external onlyMinter returns (uint256) {
        require(to != address(0), "LabNFT: mint to zero address");
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);
        return tokenId;
    }

    // The following functions are overrides required by Solidity.
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721URIStorage) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
