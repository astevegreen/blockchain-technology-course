// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

/// @title VaultA
/// @notice Training code for the lab "The vault that paid twice": the vault the drain empties.
///         It writes an event when it takes a deposit and none when it pays, and it pays before it
///         updates its records, so a caller that is called back can withdraw again.
contract VaultA {
    mapping(address => uint256) public balanceOf;

    event Deposit(address indexed account, uint256 amount);

    function deposit() external payable {
        require(msg.value > 0, "nothing deposited");
        balanceOf[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// Pays the caller everything recorded to its name, then clears the record.
    function withdraw() external {
        uint256 amount = balanceOf[msg.sender];
        require(amount > 0, "nothing to withdraw");
        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "payment failed");
        balanceOf[msg.sender] = 0;
    }
}
