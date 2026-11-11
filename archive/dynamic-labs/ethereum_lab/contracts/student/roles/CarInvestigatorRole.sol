// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title CarInvestigatorRole - Car Sale scenario: INVESTIGATOR/DETECTIVE
 * @dev Search the chain: read mechanic reports and original car history (trueCondition).
 *      Buyers pay you (off-chain) to look up and report. You can submit honest or bribed reports.
 *      Instructor sets this contract as investigator in CarSale.
 */
interface ICarSale {
    function submitInvestigatorReport(bool passed) external;
    function getTrueCondition() external view returns (bool);
    function getMechanicReport() external view returns (bool passed, address _mechanic);
}

contract CarInvestigatorRole {
    address public investigator;

    constructor() {
        investigator = msg.sender;
    }

    /// @notice Read the original car history (only this contract can call CarSale.getTrueCondition).
    function getTrueCondition(address carSale) external view returns (bool) {
        require(msg.sender == investigator, "Only investigator");
        return ICarSale(carSale).getTrueCondition();
    }

    /// @notice Submit report for a CarSale. You read trueCondition via getTrueCondition(), then submit.
    ///         You can submit the truth or lie (bribed). Contract cannot verify.
    function submitReport(address carSale, bool passed) external {
        require(msg.sender == investigator, "Only investigator");
        require(carSale != address(0), "Invalid CarSale address");
        ICarSale(carSale).submitInvestigatorReport(passed);
    }
}
