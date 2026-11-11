// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract EntropyLottery {
    uint256 private constant ENTRY_COST = 10 ether;
    uint256 private constant WIN_ODDS = 1000;

    uint256 private _entries;
    bytes32 private _lastEntropy;
    address private _lastWinner;

    event EntryBought(address indexed player, uint256 indexed entryNumber, uint256 paid);
    event PrizePaid(address indexed winner, uint256 amount, bytes32 entropy);
    event EntryLost(address indexed player, uint256 indexed entryNumber, bytes32 entropy);

    constructor() payable {}

    function enter() external payable {
        require(msg.value == ENTRY_COST, "Entry costs exactly 10 ETH");

        _entries += 1;
        emit EntryBought(msg.sender, _entries, msg.value);

        bytes32 previousBlockHash = block.number > 0 ? blockhash(block.number - 1) : bytes32(0);
        bytes32 entropy = keccak256(
            abi.encodePacked(
                previousBlockHash,
                block.timestamp,
                block.prevrandao,
                msg.sender,
                _entries,
                address(this).balance
            )
        );
        _lastEntropy = entropy;

        if (uint256(entropy) % WIN_ODDS == 0) {
            uint256 prize = address(this).balance;
            _lastWinner = msg.sender;
            (bool paid, ) = payable(msg.sender).call{ value: prize }("");
            require(paid, "Prize payment failed");
            emit PrizePaid(msg.sender, prize, entropy);
        } else {
            emit EntryLost(msg.sender, _entries, entropy);
        }
    }

    function entryCost() external pure returns (uint256) {
        return ENTRY_COST;
    }

    function odds() external pure returns (uint256) {
        return WIN_ODDS;
    }

    function entries() external view returns (uint256) {
        return _entries;
    }

    function prizePool() external view returns (uint256) {
        return address(this).balance;
    }

    function lastEntropy() external view returns (bytes32) {
        return _lastEntropy;
    }

    function lastWinner() external view returns (address) {
        return _lastWinner;
    }

    receive() external payable {}
}
