// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract FakeAirdropClaimer {
    uint256 public constant CLAIM_FEE = 0.05 ether;
    uint256 public claims;

    event FakeAirdropClaimed(address indexed claimant, uint256 feePaid, uint256 advertisedTokens);

    function claim() external payable {
        require(msg.value >= CLAIM_FEE, "Pay the claim fee");
        claims += 1;
        emit FakeAirdropClaimed(msg.sender, msg.value, 10_000 ether);
    }

    receive() external payable {}
}
