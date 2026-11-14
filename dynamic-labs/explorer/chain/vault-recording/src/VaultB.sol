// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

/// @title VaultB
/// @notice Training code for the lab "The vault that paid twice": the twist's vault. Like the
///         quiet vault it writes an event only on a deposit, but it updates its records before it
///         pays, so a caller that is called back can take out only what is recorded to its name.
contract VaultB {
    mapping(address => uint256) public balanceOf;

    event Deposit(address indexed account, uint256 amount);

    function deposit() external payable {
        require(msg.value > 0, "nothing deposited");
        balanceOf[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// Takes the amount off the caller's record, then pays it.
    function withdraw(uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "more than recorded");
        balanceOf[msg.sender] -= amount;
        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "payment failed");
    }
}
