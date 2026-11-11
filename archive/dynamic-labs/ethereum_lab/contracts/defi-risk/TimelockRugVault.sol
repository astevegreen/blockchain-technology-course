// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract TimelockRugVault {
    address public owner;
    address public treasury;
    bool public paused;
    uint256 public withdrawFeeBps;
    uint256 public unlockDelaySeconds;
    uint256 public totalUserDeposits;

    mapping(address => uint256) private balances;
    mapping(address => uint256) private depositTimestamps;

    event Deposit(address indexed account, uint256 amount, uint256 unlockTime);
    event Withdrawal(address indexed account, uint256 amount, uint256 fee);
    event PausedSet(bool paused);
    event WithdrawFeeSet(uint256 feeBps);
    event UnlockDelaySet(uint256 delaySeconds);
    event TreasurySet(address indexed treasury);
    event FeesSwept(address indexed to, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor(uint256 initialUnlockDelaySeconds, uint256 initialWithdrawFeeBps, address initialTreasury) payable {
        require(initialWithdrawFeeBps <= 9000, "Fee too high");
        owner = msg.sender;
        treasury = initialTreasury == address(0) ? msg.sender : initialTreasury;
        unlockDelaySeconds = initialUnlockDelaySeconds;
        withdrawFeeBps = initialWithdrawFeeBps;
    }

    function deposit() external payable {
        require(msg.value > 0, "Deposit required");
        balances[msg.sender] += msg.value;
        totalUserDeposits += msg.value;
        depositTimestamps[msg.sender] = block.timestamp;
        emit Deposit(msg.sender, msg.value, unlockTime(msg.sender));
    }

    function withdraw(uint256 amount) external {
        require(!paused, "Withdrawals paused");
        require(block.timestamp >= unlockTime(msg.sender), "Still locked");
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        totalUserDeposits -= amount;

        uint256 fee = (amount * withdrawFeeBps) / 10_000;
        uint256 payout = amount - fee;

        if (fee > 0) {
            (bool feeSent, ) = payable(treasury).call{ value: fee }("");
            require(feeSent, "Fee transfer failed");
        }

        (bool paid, ) = payable(msg.sender).call{ value: payout }("");
        require(paid, "Withdrawal failed");
        emit Withdrawal(msg.sender, amount, fee);
    }

    function setPaused(bool value) external onlyOwner {
        paused = value;
        emit PausedSet(value);
    }

    function setWithdrawFeeBps(uint256 value) external onlyOwner {
        require(value <= 9000, "Fee too high");
        withdrawFeeBps = value;
        emit WithdrawFeeSet(value);
    }

    function setUnlockDelay(uint256 value) external onlyOwner {
        unlockDelaySeconds = value;
        emit UnlockDelaySet(value);
    }

    function setTreasury(address value) external onlyOwner {
        require(value != address(0), "Zero treasury");
        treasury = value;
        emit TreasurySet(value);
    }

    function sweepFees() external onlyOwner {
        uint256 recordedDeposits = totalUserDeposits;
        require(address(this).balance > recordedDeposits, "No excess fees");
        uint256 excess = address(this).balance - recordedDeposits;
        (bool sent, ) = payable(treasury).call{ value: excess }("");
        require(sent, "Sweep failed");
        emit FeesSwept(treasury, excess);
    }

    function balanceOf(address account) external view returns (uint256) {
        return balances[account];
    }

    function unlockTime(address account) public view returns (uint256) {
        if (depositTimestamps[account] == 0) {
            return 0;
        }
        return depositTimestamps[account] + unlockDelaySeconds;
    }

    function totalAssets() external view returns (uint256) {
        return address(this).balance;
    }

    receive() external payable {}
}
