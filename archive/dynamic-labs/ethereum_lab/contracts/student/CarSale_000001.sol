// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title CarSale - Defective-Vehicle-Capable Escrow with Marketplace Features
 * @dev Teaches information asymmetry: contract enforces process, not truth.
 *      - Mechanic can attest honestly or lie (bribed).
 *      - Investigator can read trueCondition but submit a report that may be bribed to lie.
 *      - Buyers see: car features (incentivize purchase), mechanic report. Optionally pay investigator for a report (investigator may lie).
 *      - Only ways to detect hidden defects: mechanic report, guess, or pay investigator (who could be bribed).
 *
 * Flow: Listed → DepositPaid → InspectionRequested → InspectionPassed/Failed → Completed/Refunded
 */
contract CarSale {
    address public admin;
    address public seller;
    address public buyer;
    address public mechanic;
    address public investigator;

    uint256 public salePrice;
    uint256 public depositAmount;

    /// @dev Car features visible to all - incentivize buyers to want the car
    uint16 public carYear;
    uint32 public carMileage;
    string public carMake;
    string public carModel;

    /// @dev Original car condition set by admin. true = good, false = defective. Only investigator can read.
    bool public trueCondition;
    /// @dev What the mechanic attested. Visible to buyers.
    bool public mechanicAttestation;
    /// @dev Investigator's report to buyer. Investigator can lie (bribed). Visible after submission.
    bool public investigatorReport;
    bool public investigatorReportSubmitted;

    enum State {
        Listed,
        DepositPaid,
        InspectionRequested,
        InspectionPassed,
        InspectionFailed,
        Completed,
        Refunded
    }
    State public currentState;

    event CarListed(uint256 price);
    event DepositReceived(address buyer, uint256 amount);
    event InspectionRequested(address buyer);
    event InspectionResult(bool passed, address mechanic);
    event SaleCompleted(address seller, address buyer, uint256 amount);
    event SaleRefunded(address buyer, uint256 amount);
    event ParticipantChanged(string role, address participant);
    event InvestigatorReportSubmitted(bool passed, address investigator);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    modifier onlyBuyer() {
        require(msg.sender == buyer, "Only buyer");
        _;
    }
    modifier onlyMechanic() {
        require(msg.sender == mechanic, "Only mechanic");
        _;
    }
    modifier onlyInvestigator() {
        require(msg.sender == investigator, "Only investigator");
        _;
    }
    modifier inState(State _state) {
        require(currentState == _state, "Invalid state");
        _;
    }

    constructor(address _seller, address _buyer, address _mechanic) {
        admin = msg.sender;
        seller = _seller != address(0) ? _seller : msg.sender;
        buyer = _buyer;
        mechanic = _mechanic;
        salePrice = 2 ether;
        depositAmount = salePrice / 2; // 50% deposit
        currentState = State.Listed;
        emit CarListed(salePrice);
        emit ParticipantChanged("seller", seller);
        if (buyer != address(0)) emit ParticipantChanged("buyer", buyer);
        if (mechanic != address(0)) emit ParticipantChanged("mechanic", mechanic);
    }

    function setSeller(address _seller) external onlyAdmin inState(State.Listed) {
        require(_seller != address(0), "Invalid address");
        seller = _seller;
        emit ParticipantChanged("seller", _seller);
    }

    function setBuyer(address _buyer) external onlyAdmin inState(State.Listed) {
        buyer = _buyer;
        emit ParticipantChanged("buyer", _buyer);
    }

    function setMechanic(address _mechanic) external onlyAdmin inState(State.Listed) {
        mechanic = _mechanic;
        emit ParticipantChanged("mechanic", _mechanic);
    }

    function setInvestigator(address _investigator) external onlyAdmin inState(State.Listed) {
        investigator = _investigator;
        emit ParticipantChanged("investigator", _investigator);
    }

    /// @notice Admin sets the true car condition when listing. true = good, false = defective. Only investigator can read.
    function setTrueCondition(bool _passed) external onlyAdmin inState(State.Listed) {
        trueCondition = _passed;
    }

    /// @notice Admin sets car features (visible to all). Incentivizes buyers.
    function setCarFeatures(uint16 _year, uint32 _mileage, string calldata _make, string calldata _model) external onlyAdmin inState(State.Listed) {
        carYear = _year;
        carMileage = _mileage;
        carMake = _make;
        carModel = _model;
    }

    function getParticipants() external view returns (address _admin, address _seller, address _buyer, address _mechanic) {
        return (admin, seller, buyer, mechanic);
    }

    /// @notice Buyers and sellers can only see the mechanic report. Public read.
    function getMechanicReport() external view returns (bool passed, address _mechanic) {
        return (mechanicAttestation, mechanic);
    }

    /// @notice Only investigator can read the original car history. Compare to getMechanicReport() to detect fraud.
    function getTrueCondition() external view onlyInvestigator returns (bool) {
        return trueCondition;
    }

    /// @notice Investigator submits report for buyer. Can be honest or bribed to lie—contract cannot verify.
    function submitInvestigatorReport(bool _passed) external onlyInvestigator {
        require(!investigatorReportSubmitted, "Already reported");
        require(
            currentState == State.InspectionPassed || currentState == State.InspectionFailed,
            "Mechanic must inspect first"
        );
        investigatorReport = _passed;
        investigatorReportSubmitted = true;
        emit InvestigatorReportSubmitted(_passed, msg.sender);
    }

    /// @notice Get investigator report. Buyer can see after investigator submits (investigator may have lied).
    function getInvestigatorReport() external view returns (bool passed, bool submitted) {
        return (investigatorReport, investigatorReportSubmitted);
    }

    /// @notice Get car features for marketplace display. Visible to all.
    function getCarFeatures() external view returns (uint16 year, uint32 mileage, string memory make, string memory model) {
        return (carYear, carMileage, carMake, carModel);
    }

    /// @notice Buyer pays deposit to secure the car
    function payDeposit() external payable inState(State.Listed) {
        require(msg.value >= depositAmount, "Deposit too low");
        if (buyer != address(0)) {
            require(msg.sender == buyer, "Not designated buyer");
        } else {
            buyer = msg.sender;
            emit ParticipantChanged("buyer", msg.sender);
        }
        currentState = State.DepositPaid;
        emit DepositReceived(msg.sender, msg.value);
    }

    /// @notice Buyer requests inspection (must have mechanic assigned)
    function requestInspection() external onlyBuyer inState(State.DepositPaid) {
        require(mechanic != address(0), "No mechanic assigned");
        currentState = State.InspectionRequested;
        emit InspectionRequested(msg.sender);
    }

    /// @notice Mechanic attests to condition. If passed, buyer can complete. If failed, buyer can refund.
    /// @param passed Whether the mechanic attests the car is in good condition (honest or bribed - contract cannot know)
    function mechanicInspect(bool passed) external onlyMechanic inState(State.InspectionRequested) {
        mechanicAttestation = passed;
        if (passed) {
            currentState = State.InspectionPassed;
        } else {
            currentState = State.InspectionFailed;
        }
        emit InspectionResult(passed, msg.sender);
    }

    /// @notice Buyer completes purchase after inspection passed (sends remaining balance)
    function completePurchase() external payable onlyBuyer inState(State.InspectionPassed) {
        uint256 remaining = salePrice - depositAmount;
        require(msg.value >= remaining, "Send remaining balance");
        require(address(this).balance >= salePrice, "Full payment not received");
        currentState = State.Completed;
        (bool ok, ) = payable(seller).call{value: address(this).balance}("");
        require(ok, "Transfer failed");
        emit SaleCompleted(seller, buyer, salePrice);
    }

    /// @notice Buyer gets refund after inspection failed
    function requestRefund() external onlyBuyer inState(State.InspectionFailed) {
        uint256 amount = address(this).balance;
        require(amount > 0, "Nothing to refund");
        currentState = State.Refunded;
        (bool ok, ) = payable(buyer).call{value: amount}("");
        require(ok, "Refund failed");
        emit SaleRefunded(buyer, amount);
    }

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
