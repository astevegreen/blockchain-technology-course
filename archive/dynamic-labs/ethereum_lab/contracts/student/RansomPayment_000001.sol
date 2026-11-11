// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title RansomPayment - Ransomware Forensics Lab
 * @dev Victims pay ETH through contract; creates on-chain trail for investigators to trace.
 *      Instructor deploys, sets attacker address. Investigators trace Victim → Contract → Attacker → Tumblers → Final.
 */
contract RansomPayment {
    address public admin;
    address public attacker; // Receives ransom; investigators trace from here

    event RansomPaid(address indexed victim, uint256 amount);
    event AttackerSet(address indexed attacker);
    event BountyClaimed(address indexed investigator, address foundAddress, uint256 amount);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }

    constructor(address _attacker) {
        admin = msg.sender;
        attacker = _attacker != address(0) ? _attacker : msg.sender;
        emit AttackerSet(attacker);
    }

    function setAttacker(address _attacker) external onlyAdmin {
        require(_attacker != address(0), "Invalid address");
        attacker = _attacker;
        emit AttackerSet(_attacker);
    }

    /// @notice Victim pays ransom; ETH forwarded to attacker address
    function payRansom() external payable {
        require(msg.value > 0, "Send ETH");
        require(attacker != address(0), "Attacker not set");
        emit RansomPaid(msg.sender, msg.value);
        (bool ok, ) = payable(attacker).call{value: msg.value}("");
        require(ok, "Transfer failed");
    }

    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
