// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./ICarSale.sol";

/**
 * @title MechanicRole - Car Sale scenario: MECHANIC (honest or bribed)
 * @dev Your task: Call mechanicInspect(true) or mechanicInspect(false) on the CarSale
 *      Honest: report actual condition. Bribed: always pass (true).
 * 
 * DEPLOY: npx hardhat run scripts/deploy-role.js --network localhost Mechanic <CARSALE_ADDRESS>
 * USAGE: mechanicInspect(true) or mechanicInspect(false)
 */
contract MechanicRole {
    address public mechanic;
    ICarSale public carSale;
    
    event InspectionSubmitted(bool passed);
    
    constructor(address _carSale) {
        mechanic = msg.sender;
        carSale = ICarSale(_carSale);
    }
    
    /// @notice Submit inspection result. Honest: report truth. Bribed: always pass.
    function mechanicInspect(bool passed) external {
        require(msg.sender == mechanic, "Only mechanic");
        carSale.mechanicInspect(passed);
        emit InspectionSubmitted(passed);
    }
}
