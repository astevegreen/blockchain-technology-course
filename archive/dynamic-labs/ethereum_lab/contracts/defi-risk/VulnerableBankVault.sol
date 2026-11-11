// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableBankVault {
    mapping(address => uint256) private balances;

    event Deposit(address indexed account, uint256 amount);
    event Withdrawal(address indexed account, uint256 amount);
    event UntrackedSeedFunding(address indexed sender, uint256 amount);

    function deposit() external payable {
        require(msg.value > 0, "Deposit required");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // Intentionally vulnerable: control is transferred before accounting updates.
        (bool sent, ) = payable(msg.sender).call{ value: amount }("");
        require(sent, "ETH transfer failed");

        unchecked {
            balances[msg.sender] -= amount;
        }
        emit Withdrawal(msg.sender, amount);
    }

    function totalAssets() external view returns (uint256) {
        return address(this).balance;
    }

    function balanceOf(address account) external view returns (uint256) {
        return balances[account];
    }

    receive() external payable {
        emit UntrackedSeedFunding(msg.sender, msg.value);
    }
}
