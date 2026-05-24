// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleNFT
 * @dev Minimal Non-Fungible Token for teaching FT vs NFT concepts.
 * Demonstrates: ownerOf, mint, transfer. Each token has a unique ID.
 * Not a full ERC-721 - educational purposes only.
 */
contract SimpleNFT {
    string public name;
    string public symbol;
    uint256 public nextTokenId;

    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Mint(address indexed to, uint256 indexed tokenId);

    address public minter;

    modifier onlyMinter() {
        require(msg.sender == minter, "Only minter can call");
        _;
    }

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
        minter = msg.sender;
        nextTokenId = 1;
    }

    /// @notice Mint a new token (deployer only)
    function mint(address to) external onlyMinter returns (uint256) {
        require(to != address(0), "Invalid address");
        uint256 tokenId = nextTokenId++;
        ownerOf[tokenId] = to;
        balanceOf[to]++;
        emit Mint(to, tokenId);
        emit Transfer(address(0), to, tokenId);
        return tokenId;
    }

    /// @notice Mint multiple tokens in one transaction (avoids nonce issues)
    function mintBatch(address to, uint256 count) external onlyMinter returns (uint256[] memory) {
        require(to != address(0), "Invalid address");
        require(count > 0 && count <= 10, "Count 1-10");
        uint256[] memory ids = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            uint256 tokenId = nextTokenId++;
            ownerOf[tokenId] = to;
            balanceOf[to]++;
            ids[i] = tokenId;
            emit Mint(to, tokenId);
            emit Transfer(address(0), to, tokenId);
        }
        return ids;
    }

    /// @notice Transfer a token to another address
    function transfer(address to, uint256 tokenId) external {
        require(ownerOf[tokenId] == msg.sender, "Not your token");
        require(to != address(0), "Invalid recipient");

        ownerOf[tokenId] = to;
        balanceOf[msg.sender]--;
        balanceOf[to]++;

        emit Transfer(msg.sender, to, tokenId);
    }
}
