// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleFT
 * @dev Minimal Fungible Token for teaching FT vs NFT concepts.
 * Demonstrates: balanceOf, totalSupply, mint, transfer.
 * Not a full ERC-20 - educational purposes only.
 */
contract SimpleFT {
    string public name;
    string public symbol;
    uint256 public totalSupply;
    
    address public minter;
    mapping(address => uint256) public balanceOf;
    
    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Mint(address indexed to, uint256 amount);
    
    modifier onlyMinter() {
        require(msg.sender == minter, "Only minter can call");
        _;
    }
    
    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
        minter = msg.sender;
    }
    
    /// @notice Mint new tokens (deployer only)
    function mint(address to, uint256 amount) external onlyMinter {
        require(to != address(0), "Invalid address");
        balanceOf[to] += amount;
        totalSupply += amount;
        emit Mint(to, amount);
        emit Transfer(address(0), to, amount);
    }
    
    /// @notice Transfer tokens to another address
    function transfer(address to, uint256 amount) external {
        require(to != address(0), "Invalid address");
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
    }
}
