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
    uint256 public constant MAX_MINTS_PER_RECIPIENT = 5;

    uint256 private _nextTokenId;
    mapping(address => uint256) private _mintedByRecipient;
    mapping(bytes32 => bool) private _usedTokenUriHashes;
    address public minter;

    constructor(string memory name_, string memory symbol_) ERC721(name_, symbol_) {
        minter = msg.sender;
        _nextTokenId = 1;
    }

    /**
     * @dev Mints a new token to `to` with the given `tokenURI`.
     * Public on purpose for the classroom lab, but guarded so bypassing the UI
     * cannot mint more than one five-token batch to a wallet or reuse the same
     * metadata/image URI.
     */
    function mint(address to, string memory tokenURI_) external returns (uint256) {
        require(to != address(0), "LabNFT: mint to zero address");
        require(bytes(tokenURI_).length != 0, "LabNFT: token URI required");
        require(_mintedByRecipient[to] < MAX_MINTS_PER_RECIPIENT, "LabNFT: recipient mint limit reached");

        bytes32 uriHash = keccak256(bytes(tokenURI_));
        require(!_usedTokenUriHashes[uriHash], "LabNFT: token URI already minted");

        uint256 tokenId = _nextTokenId++;
        _usedTokenUriHashes[uriHash] = true;
        _mintedByRecipient[to] += 1;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);
        return tokenId;
    }

    function mintBatch(address to, string[] calldata tokenURIs) external returns (uint256[] memory) {
        require(to != address(0), "LabNFT: mint to zero address");
        require(tokenURIs.length > 0, "LabNFT: empty batch");
        require(
            _mintedByRecipient[to] + tokenURIs.length <= MAX_MINTS_PER_RECIPIENT,
            "LabNFT: recipient mint limit reached"
        );

        uint256[] memory tokenIds = new uint256[](tokenURIs.length);
        for (uint256 i = 0; i < tokenURIs.length; i++) {
            require(bytes(tokenURIs[i]).length != 0, "LabNFT: token URI required");
            bytes32 uriHash = keccak256(bytes(tokenURIs[i]));
            require(!_usedTokenUriHashes[uriHash], "LabNFT: token URI already minted");
            _usedTokenUriHashes[uriHash] = true;

            uint256 tokenId = _nextTokenId++;
            _mintedByRecipient[to] += 1;
            _safeMint(to, tokenId);
            _setTokenURI(tokenId, tokenURIs[i]);
            tokenIds[i] = tokenId;
        }
        return tokenIds;
    }

    function mintedCount(address owner) external view returns (uint256) {
        return _mintedByRecipient[owner];
    }

    function tokenURIExists(string memory tokenURI_) external view returns (bool) {
        return _usedTokenUriHashes[keccak256(bytes(tokenURI_))];
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
