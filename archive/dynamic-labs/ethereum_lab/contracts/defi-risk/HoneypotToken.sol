// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract HoneypotToken {
    string public name = "Honey Garden Token";
    string public symbol = "HNY";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    address public immutable owner;
    uint256 public constant TOKENS_PER_ETH = 1_000;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event TrapSprung(address indexed account, uint256 amount, string reason);

    constructor() {
        owner = msg.sender;
    }

    function buy() external payable returns (bool) {
        return _buy(msg.sender, msg.value);
    }

    function _buy(address buyer, uint256 amountPaid) internal returns (bool) {
        require(amountPaid > 0, "ETH required");
        uint256 tokens = amountPaid * TOKENS_PER_ETH;
        totalSupply += tokens;
        balanceOf[buyer] += tokens;
        emit Transfer(address(0), buyer, tokens);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        return _transfer(msg.sender, to, amount);
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= amount, "Allowance too low");
        allowance[from][msg.sender] = allowed - amount;
        emit Approval(from, msg.sender, allowance[from][msg.sender]);
        return _transfer(from, to, amount);
    }

    function _transfer(address from, address to, uint256 amount) internal returns (bool) {
        require(to != address(0), "Zero address");
        require(balanceOf[from] >= amount, "Balance too low");

        if (from != owner) {
            emit TrapSprung(from, amount, "Non-owner transfers are blocked by design");
            revert("HONEYPOT: only owner can move tokens");
        }

        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        emit Transfer(from, to, amount);
        return true;
    }

    receive() external payable {
        _buy(msg.sender, msg.value);
    }
}
