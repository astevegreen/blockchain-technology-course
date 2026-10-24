// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

contract Token {
    mapping(address => uint256) public balanceOf;
    event Transfer(address indexed from, address indexed to, uint256 value);
    constructor() { balanceOf[msg.sender] = 1_000_000e18; emit Transfer(address(0), msg.sender, 1_000_000e18); }
    function transfer(address to, uint256 v) external returns (bool) {
        require(balanceOf[msg.sender] >= v, "balance too low");
        balanceOf[msg.sender] -= v; balanceOf[to] += v; emit Transfer(msg.sender, to, v); return true;
    }
}

contract Forwarder {
    function fwd(address payable to) external payable { to.transfer(msg.value); }
    function split(address payable a, address payable b) external payable { a.transfer(msg.value / 2); b.transfer(msg.value - msg.value / 2); }
}
