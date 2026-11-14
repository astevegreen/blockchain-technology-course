// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

interface IVaultB {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
    function balanceOf(address account) external view returns (uint256);
}

/// @title StepWithdrawer
/// @notice Training code for the lab "The vault that paid twice": the twist's caller. It deposits
///         what it is sent and takes it back 1 ETH at a time, asking for the next 1 ETH from inside
///         each payment until nothing is left to its name. The nesting looks like a drain; the vault
///         loses nothing.
contract StepWithdrawer {
    IVaultB public immutable vault;
    address public immutable owner;

    constructor(address target) {
        vault = IVaultB(target);
        owner = msg.sender;
    }

    function run() external payable {
        require(msg.sender == owner, "not the owner");
        vault.deposit{value: msg.value}();
        vault.withdraw(1 ether);
    }

    receive() external payable {
        if (vault.balanceOf(address(this)) >= 1 ether) {
            vault.withdraw(1 ether);
        }
    }
}
