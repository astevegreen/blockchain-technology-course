// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";

/**
 * @title ArcadeToken
 * @dev Standard ERC-20 for the fungible-token arcade lab.
 *
 * The vendor is the only minter. Students buy ARC from TokenVendor, approve
 * ArcadeVault, then ArcadeVault burns ARC when a game session starts.
 */
contract ArcadeToken is ERC20, ERC20Burnable, Ownable {
    address public minter;

    event MinterUpdated(address indexed oldMinter, address indexed newMinter);

    constructor() ERC20("Arcade Token", "ARC") {}

    modifier onlyMinter() {
        require(msg.sender == minter, "ArcadeToken: caller is not minter");
        _;
    }

    function setMinter(address newMinter) external onlyOwner {
        require(newMinter != address(0), "ArcadeToken: minter required");
        emit MinterUpdated(minter, newMinter);
        minter = newMinter;
    }

    function mint(address to, uint256 amount) external onlyMinter {
        _mint(to, amount);
    }
}
