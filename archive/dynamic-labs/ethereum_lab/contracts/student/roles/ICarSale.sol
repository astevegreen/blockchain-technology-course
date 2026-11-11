// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ICarSale - Interface for Car Sale scenario
 * @dev Use this when building your role contract to interact with the shared CarSale
 */
interface ICarSale {
    function payDeposit() external payable;
    function requestInspection() external;
    function mechanicInspect(bool passed) external;
    function completePurchase() external payable;
    function requestRefund() external;
    function depositAmount() external view returns (uint256);
    function salePrice() external view returns (uint256);
    function currentState() external view returns (uint8);
}
