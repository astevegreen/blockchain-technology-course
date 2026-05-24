// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title InvestigatorRole - Ransomware scenario: INVESTIGATOR
 * @dev Your task: Trace the ransom flow off-chain (block explorer, Hardhat console).
 *      Submit the attacker's final address to the scenario contract for bounty.
 *      This contract proves you completed the forensics lab.
 * 
 * DEPLOY: npx hardhat run scripts/deploy-role.js --network localhost Investigator
 * USAGE: Use block explorer + Playground to trace. Register this contract when done.
 */
contract InvestigatorRole {
    address public investigator;
    address public submittedAddress; // Address you identified (for record)
    
    event FindingSubmitted(address indexed foundAddress);
    
    constructor() {
        investigator = msg.sender;
    }
    
    /// @notice Record your finding (for your own tracking; bounty is claimed via scenario contract)
    function submitFinding(address _found) external {
        require(msg.sender == investigator, "Only investigator");
        submittedAddress = _found;
        emit FindingSubmitted(_found);
    }
}
