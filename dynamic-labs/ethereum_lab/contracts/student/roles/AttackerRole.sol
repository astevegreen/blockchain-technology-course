// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AttackerRole - Ransomware scenario: ATTACKER
 * @dev Your task: Receive ransom payments. Instructor sets YOUR address in RansomPayment.
 *      Investigators will trace: Victim → RansomPayment → You → tumblers → final address.
 * 
 * DEPLOY: npx hardhat run scripts/deploy-role.js --network localhost Attacker
 * USAGE: Instructor calls RansomPayment.setAttacker(YOUR_ADDRESS). Victims pay; you receive.
 */
contract AttackerRole {
    address public attacker;
    
    event RansomReceived(uint256 amount);
    
    constructor() {
        attacker = msg.sender;
    }
    
    receive() external payable {
        emit RansomReceived(msg.value);
    }
    
    function withdraw() external {
        require(msg.sender == attacker, "Only attacker");
        (bool ok, ) = payable(attacker).call{value: address(this).balance}("");
        require(ok, "Transfer failed");
    }
}
