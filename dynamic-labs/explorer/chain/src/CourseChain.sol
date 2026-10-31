// SPDX-License-Identifier: MIT
// The two contracts on the day-1 course chain. Kept short so a student can read them on the
// explorer's Contract tab.
pragma solidity 0.8.24;

// A minimal token: balances, a transfer that refuses an overdraft, and the Transfer event
// explorers read to list token movements.
contract CourseToken {
    string public constant name = "Course Token";
    string public constant symbol = "CRT";
    uint8 public constant decimals = 18;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor() {
        totalSupply = 1_000_000e18;
        balanceOf[msg.sender] = totalSupply;
        emit Transfer(address(0), msg.sender, totalSupply);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "balance too low");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}

// Splits the ETH sent to it between two addresses. Its payouts are internal transfers: the
// contract moves the ETH, so they have no transaction of their own.
contract Splitter {
    function split(address payable a, address payable b) external payable {
        a.transfer(msg.value / 2);
        b.transfer(msg.value - msg.value / 2);
    }
}
