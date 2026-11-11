// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title CarMarketplace - Lists CarSale contracts for buyers to browse
 * @dev Instructor adds CarSale addresses. Buyers see listings with car features, mechanic reports, investigator reports.
 */
contract CarMarketplace {
    address public admin;
    address[] public listings;

    event ListingAdded(address indexed carSale);
    event ListingRemoved(address indexed carSale);

    constructor() {
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }

    function addListing(address _carSale) external onlyAdmin {
        require(_carSale != address(0), "Invalid address");
        listings.push(_carSale);
        emit ListingAdded(_carSale);
    }

    function addListings(address[] calldata _carSales) external onlyAdmin {
        for (uint256 i = 0; i < _carSales.length; i++) {
            if (_carSales[i] != address(0)) {
                listings.push(_carSales[i]);
                emit ListingAdded(_carSales[i]);
            }
        }
    }

    function removeListing(uint256 index) external onlyAdmin {
        require(index < listings.length, "Invalid index");
        address removed = listings[index];
        listings[index] = listings[listings.length - 1];
        listings.pop();
        emit ListingRemoved(removed);
    }

    function getListings() external view returns (address[] memory) {
        return listings;
    }

    function getListingCount() external view returns (uint256) {
        return listings.length;
    }
}
