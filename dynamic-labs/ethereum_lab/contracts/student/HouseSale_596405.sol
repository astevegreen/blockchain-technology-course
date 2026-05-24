// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title HouseSale
 * @dev Escrow contract for property sale: 123 Main St, Anytown USA
 * 
 * How it works:
 * 1. Seller deploys with property details
 * 2. Buyer deposits earnest money (10% of 10 ETH)
 * 3. Inspection period of 7 days
 * 4. If approved, buyer sends remaining balance
 * 5. Seller confirms transfer, funds released
 */
contract HouseSale {
    // ===== STATE VARIABLES =====
    address public seller;
    address public buyer;
    string public propertyAddress;
    uint256 public salePrice;
    uint256 public depositAmount;
    uint256 public inspectionDeadline;
    
    // Contract state
    enum State { Listed, DepositPaid, InspectionPassed, Completed, Cancelled }
    State public currentState;
    
    // ===== EVENTS =====
    event PropertyListed(string propertyAddress, uint256 price);
    event DepositReceived(address buyer, uint256 amount);
    event InspectionApproved(address buyer);
    event SaleCompleted(address seller, address buyer, uint256 amount);
    event SaleCancelled(string reason);
    
    // ===== MODIFIERS =====
    modifier onlySeller() {
        require(msg.sender == seller, "Only seller can call this");
        _;
    }
    
    modifier onlyBuyer() {
        require(msg.sender == buyer, "Only buyer can call this");
        _;
    }
    
    modifier inState(State _state) {
        require(currentState == _state, "Invalid state for this action");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor() {
        seller = msg.sender;
        propertyAddress = "123 Main St, Anytown USA";
        salePrice = 10 ether;
        depositAmount = (salePrice * 10) / 100;
        currentState = State.Listed;
        
        emit PropertyListed(propertyAddress, salePrice);
    }
    
    // ===== BUYER FUNCTIONS =====
    
    /// @notice Buyer pays deposit to secure the property
    function payDeposit() external payable inState(State.Listed) {
        require(msg.value >= depositAmount, "Deposit too low");
        require(buyer == address(0), "Buyer already set");
        
        buyer = msg.sender;
        inspectionDeadline = block.timestamp + (7 * 1 days);
        currentState = State.DepositPaid;
        
        emit DepositReceived(msg.sender, msg.value);
    }
    
    /// @notice Buyer approves after inspection
    function approveInspection() external onlyBuyer inState(State.DepositPaid) {
        require(block.timestamp <= inspectionDeadline, "Inspection period expired");
        currentState = State.InspectionPassed;
        emit InspectionApproved(msg.sender);
    }
    
    /// @notice Buyer pays remaining balance
    function payBalance() external payable onlyBuyer inState(State.InspectionPassed) {
        uint256 remaining = salePrice - depositAmount;
        require(msg.value >= remaining, "Insufficient payment");
        
        // Any overpayment stays in contract (or could refund)
    }
    
    // ===== SELLER FUNCTIONS =====
    
    /// @notice Seller confirms title transfer and receives funds
    function confirmTransfer() external onlySeller inState(State.InspectionPassed) {
        require(address(this).balance >= salePrice, "Full payment not received");
        
        currentState = State.Completed;
        
        // Transfer funds to seller
        (bool success, ) = payable(seller).call{value: address(this).balance}("");
        require(success, "Transfer failed");
        
        emit SaleCompleted(seller, buyer, salePrice);
    }
    
    /// @notice Seller can cancel if buyer misses inspection deadline
    function cancelSale(string calldata reason) external onlySeller {
        require(
            currentState == State.Listed || 
            (currentState == State.DepositPaid && block.timestamp > inspectionDeadline),
            "Cannot cancel at this stage"
        );
        
        currentState = State.Cancelled;
        
        // Refund buyer if deposit was paid
        if (buyer != address(0) && address(this).balance > 0) {
            (bool success, ) = payable(buyer).call{value: address(this).balance}("");
            require(success, "Refund failed");
        }
        
        emit SaleCancelled(reason);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
    
    function getRemainingPayment() external view returns (uint256) {
        if (currentState == State.InspectionPassed) {
            return salePrice - address(this).balance;
        }
        return salePrice - depositAmount;
    }
    
    function getTimeUntilInspectionDeadline() external view returns (int256) {
        if (inspectionDeadline == 0) return -1;
        return int256(inspectionDeadline) - int256(block.timestamp);
    }
}
