// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title EscrowAgentRole - Car Sale scenario: ESCROW AGENT
 * @dev Your task: Hold funds until conditions are met. The CarSale contract IS the escrow.
 *      Deploy this to prove you understand the escrow pattern.
 * 
 * DEPLOY: npx hardhat run scripts/deploy-role.js --network localhost EscrowAgent
 */
contract EscrowAgentRole {
    address public agent;
    
    constructor() {
        agent = msg.sender;
    }
    
    receive() external payable {}
    
    function releaseTo(address payable to, uint256 amount) external {
        require(msg.sender == agent, "Only agent");
        require(address(this).balance >= amount, "Insufficient balance");
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "Transfer failed");
    }
    
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
