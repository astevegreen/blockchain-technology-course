// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VictimRole - Ransomware scenario: VICTIM
 * @dev Your task: Pay ransom through the RansomPayment contract. Your payment creates an on-chain trail.
 * 
 * DEPLOY: npx hardhat run scripts/deploy-role.js --network localhost Victim
 * USAGE: 1. Fund this contract  2. Call payRansomOnBehalf(ransomContractAddress) with ETH
 */
interface IRansomPayment {
    function payRansom() external payable;
}

contract VictimRole {
    address public victim;
    
    event RansomPaid(address indexed ransomContract, uint256 amount);
    
    constructor() {
        victim = msg.sender;
    }
    
    receive() external payable {}
    
    /// @notice Pay ransom through the scenario's RansomPayment contract
    function payRansomOnBehalf(address ransomContract) external payable {
        require(msg.sender == victim, "Only victim");
        require(ransomContract != address(0), "Invalid contract");
        require(msg.value > 0, "Send ETH");
        IRansomPayment(ransomContract).payRansom{value: msg.value}();
        emit RansomPaid(ransomContract, msg.value);
    }
    
    function withdraw() external {
        require(msg.sender == victim, "Only victim");
        (bool ok, ) = payable(victim).call{value: address(this).balance}("");
        require(ok, "Transfer failed");
    }
}
