// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @dev Matches Contract Lab "Write & Compile" default template.
 * Used to validate custom contract deploy flow.
 */
contract MyContract {
    uint256 public value;

    function set(uint256 _value) external {
        value = _value;
    }

    function get() external view returns (uint256) {
        return value;
    }
}
