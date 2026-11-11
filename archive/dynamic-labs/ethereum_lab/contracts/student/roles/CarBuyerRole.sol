// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./ICarSale.sol";

/**
 * @title CarBuyerRole - Car Sale scenario: BUYER
 * @dev Your task: Fund this contract, then call payDeposit → requestInspection → completePurchase (or requestRefund)
 * 
 * DEPLOY: npx hardhat run scripts/deploy-role.js --network localhost CarBuyer <CARSALE_ADDRESS>
 * USAGE: 1. Send 2+ ETH to this contract  2. payDeposit()  3. requestInspection()  4. completePurchase()
 */
contract CarBuyerRole {
    address public buyer;
    ICarSale public carSale;
    
    event DepositPaid(uint256 amount);
    event InspectionRequested();
    event PurchaseCompleted(uint256 amount);
    event RefundReceived(uint256 amount);
    
    constructor(address _carSale) {
        buyer = msg.sender;
        carSale = ICarSale(_carSale);
    }
    
    receive() external payable {}
    
    /// @notice Pay deposit to secure the car (state: Listed)
    function payDeposit() external {
        require(msg.sender == buyer, "Only buyer");
        uint256 amount = carSale.depositAmount();
        require(address(this).balance >= amount, "Fund contract first - send ETH to this address");
        carSale.payDeposit{value: amount}();
        emit DepositPaid(amount);
    }
    
    /// @notice Request inspection (state: DepositPaid)
    function requestInspection() external {
        require(msg.sender == buyer, "Only buyer");
        carSale.requestInspection();
        emit InspectionRequested();
    }
    
    /// @notice Complete purchase after mechanic passes (state: InspectionPassed)
    function completePurchase() external {
        require(msg.sender == buyer, "Only buyer");
        uint256 remaining = carSale.salePrice() - carSale.depositAmount();
        require(address(this).balance >= remaining, "Need more ETH - send remaining balance");
        carSale.completePurchase{value: remaining}();
        emit PurchaseCompleted(carSale.salePrice());
    }
    
    /// @notice Get refund if mechanic fails (state: InspectionFailed)
    function requestRefund() external {
        require(msg.sender == buyer, "Only buyer");
        carSale.requestRefund();
        emit RefundReceived(address(this).balance);
    }
    
    function withdraw() external {
        require(msg.sender == buyer, "Only buyer");
        (bool ok, ) = payable(buyer).call{value: address(this).balance}("");
        require(ok, "Transfer failed");
    }
    
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
