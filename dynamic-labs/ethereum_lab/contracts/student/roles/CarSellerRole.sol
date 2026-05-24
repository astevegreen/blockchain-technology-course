// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title CarSellerRole - Car Sale scenario: SELLER (honest or deceptive)
 * @dev Your task: This contract receives the sale proceeds when the buyer completes.
 *      Admin deploys CarSale with YOUR address as seller. When sale completes, CarSale sends ETH here.
 *      Honest: car is good. Deceptive: car has hidden defects—complete sale before buyer finds out.
 * 
 * DEPLOY: npx hardhat run scripts/deploy-role.js --network localhost CarSeller
 * USAGE: Admin sets this address as seller in CarSale. Withdraw funds after sale completes.
 */
contract CarSellerRole {
    address public seller;
    
    event SaleProceedsReceived(uint256 amount);
    event Withdrawn(uint256 amount);
    
    constructor() {
        seller = msg.sender;
    }
    
    receive() external payable {
        emit SaleProceedsReceived(msg.value);
    }
    
    function withdraw() external {
        require(msg.sender == seller, "Only seller");
        uint256 amount = address(this).balance;
        require(amount > 0, "Nothing to withdraw");
        (bool ok, ) = payable(seller).call{value: amount}("");
        require(ok, "Transfer failed");
        emit Withdrawn(amount);
    }
    
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
