#!/usr/bin/env node
/**
 * CLI Lab 5: Smart Contract Builder
 * 
 * Guided contract development with templates:
 * - House/Property Sale (escrow)
 * - Vehicle Title Transfer
 * - Event Tickets
 * - Voting System
 * - Crowdfunding
 * 
 * Run: node 5-contract-builder.js
 */

import { ethers } from 'ethers';
import * as readline from 'readline';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import 'dotenv/config';

// Get directory paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '../../..');

// Configuration
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';
const STUDENT_CONTRACTS_DIR = path.join(PROJECT_ROOT, 'contracts', 'student');

// Test accounts (Hardhat default)
const TEST_ACCOUNTS = [
  { name: 'Account 0', address: '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', key: '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80' },
  { name: 'Account 1', address: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8', key: '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d' },
  { name: 'Account 2', address: '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC', key: '0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a' },
];

// Colors
const c = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
};

const color = (col, text) => `${c[col]}${text}${c.reset}`;
const line = (char = '─', len = 60) => char.repeat(len);

// Readline setup - only create when running standalone
let rl = null;
let ask = null;
let pause = null;
let usingExternalRl = false;

function initReadline(externalRl = null) {
  if (externalRl) {
    // Using external readline from interactive.js - don't create our own
    rl = externalRl;
    usingExternalRl = true;
  } else if (!rl) {
    // Standalone mode - create our own readline
    rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    usingExternalRl = false;
  }
  // Set up ask/pause to use the current rl
  ask = (q) => new Promise(resolve => rl.question(q, resolve));
  pause = () => ask('\nPress Enter to continue...');
}

// Global state
let provider, wallet;
let selectedAccount = TEST_ACCOUNTS[0];

// ============================================================================
// CONTRACT TEMPLATES
// ============================================================================

const TEMPLATES = {
  simpleFT: {
    name: 'Simple Fungible Token (Token Concepts)',
    description: 'Minimal FT for learning: mint, transfer, balanceOf, totalSupply. Teaches interchangeable tokens.',
    icon: '🪙',
    fields: [
      { name: 'tokenName', prompt: 'Token name', type: 'string', default: 'LearningToken' },
      { name: 'symbol', prompt: 'Token symbol', type: 'string', default: 'LTK' },
    ],
    generateContract: (params) => `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleFT
 * @dev Minimal Fungible Token for teaching FT vs NFT concepts.
 * Demonstrates: balanceOf, totalSupply, mint, transfer.
 */
contract SimpleFT {
    string public name;
    string public symbol;
    uint256 public totalSupply;
    
    address public minter;
    mapping(address => uint256) public balanceOf;
    
    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Mint(address indexed to, uint256 amount);
    
    modifier onlyMinter() {
        require(msg.sender == minter, "Only minter can call");
        _;
    }
    
    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
        minter = msg.sender;
    }
    
    function mint(address to, uint256 amount) external onlyMinter {
        require(to != address(0), "Invalid address");
        balanceOf[to] += amount;
        totalSupply += amount;
        emit Mint(to, amount);
        emit Transfer(address(0), to, amount);
    }
    
    function transfer(address to, uint256 amount) external {
        require(to != address(0), "Invalid address");
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
    }
}
`,
    constructorArgs: (params) => [params.tokenName, params.symbol],
  },

  simpleNFT: {
    name: 'Simple NFT (Token Concepts)',
    description: 'Minimal NFT for learning: mint, transfer, ownerOf. Each token has a unique ID. Teaches non-fungible tokens.',
    icon: '🎟️',
    fields: [
      { name: 'tokenName', prompt: 'Token name', type: 'string', default: 'EventTicket' },
      { name: 'symbol', prompt: 'Token symbol', type: 'string', default: 'TKT' },
    ],
    generateContract: (params) => `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleNFT
 * @dev Minimal Non-Fungible Token for teaching FT vs NFT concepts.
 * Demonstrates: ownerOf, mint, transfer. Each token has a unique ID.
 */
contract SimpleNFT {
    string public name;
    string public symbol;
    uint256 public nextTokenId;

    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Mint(address indexed to, uint256 indexed tokenId);

    address public minter;

    modifier onlyMinter() {
        require(msg.sender == minter, "Only minter can call");
        _;
    }

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
        minter = msg.sender;
        nextTokenId = 1;
    }

    function mint(address to) external onlyMinter returns (uint256) {
        require(to != address(0), "Invalid address");
        uint256 tokenId = nextTokenId++;
        ownerOf[tokenId] = to;
        balanceOf[to]++;
        emit Mint(to, tokenId);
        emit Transfer(address(0), to, tokenId);
        return tokenId;
    }

    function mintBatch(address to, uint256 count) external onlyMinter returns (uint256[] memory) {
        require(to != address(0), "Invalid address");
        require(count > 0 && count <= 10, "Count 1-10");
        uint256[] memory ids = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            uint256 tokenId = nextTokenId++;
            ownerOf[tokenId] = to;
            balanceOf[to]++;
            ids[i] = tokenId;
            emit Mint(to, tokenId);
            emit Transfer(address(0), to, tokenId);
        }
        return ids;
    }

    function transfer(address to, uint256 tokenId) external {
        require(ownerOf[tokenId] == msg.sender, "Not your token");
        require(to != address(0), "Invalid recipient");

        ownerOf[tokenId] = to;
        balanceOf[msg.sender]--;
        balanceOf[to]++;

        emit Transfer(msg.sender, to, tokenId);
    }
}
`,
    constructorArgs: (params) => [params.tokenName, params.symbol],
  },

  houseSale: {
    name: 'House/Property Sale',
    description: 'Escrow contract for real estate transactions with buyer/seller roles, inspection period, and secure fund transfer.',
    icon: '🏠',
    fields: [
      { name: 'propertyAddress', prompt: 'Property address (string)', type: 'string', default: '123 Main St, Anytown USA' },
      { name: 'salePrice', prompt: 'Sale price in ETH', type: 'eth', default: '10' },
      { name: 'depositPercent', prompt: 'Deposit percentage (e.g., 10 for 10%)', type: 'uint', default: '10' },
      { name: 'inspectionDays', prompt: 'Inspection period in days', type: 'uint', default: '7' },
      { name: 'sellerAddress', prompt: 'Seller address (leave blank for deployer)', type: 'address', default: '' },
      { name: 'buyerAddress', prompt: 'Buyer address (leave blank to set later)', type: 'address', default: '' },
    ],
    generateContract: (params) => `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title HouseSale
 * @dev Escrow contract for property sale: ${params.propertyAddress}
 * 
 * How it works:
 * 1. Admin deploys and assigns seller/buyer roles
 * 2. Buyer deposits earnest money (${params.depositPercent}% of ${params.salePrice} ETH)
 * 3. Inspection period of ${params.inspectionDays} days
 * 4. If approved, buyer sends remaining balance
 * 5. Seller confirms transfer, funds released
 */
contract HouseSale {
    // ===== STATE VARIABLES =====
    address public admin;
    address public seller;
    address public buyer;
    string public propertyAddress;
    uint256 public salePrice;
    uint256 public depositAmount;
    uint256 public inspectionDeadline;
    
    // Contract state
    enum State { Listed, DepositPaid, InspectionPassed, Completed, Cancelled }
    State public currentState;
    
    // ===== EVENTS =====
    event PropertyListed(string propertyAddress, uint256 price);
    event DepositReceived(address buyer, uint256 amount);
    event InspectionApproved(address buyer);
    event SaleCompleted(address seller, address buyer, uint256 amount);
    event SaleCancelled(string reason);
    event ParticipantChanged(string role, address participant);
    
    // ===== MODIFIERS =====
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this");
        _;
    }
    
    modifier onlySeller() {
        require(msg.sender == seller, "Only seller can call this");
        _;
    }
    
    modifier onlyBuyer() {
        require(msg.sender == buyer, "Only buyer can call this");
        _;
    }
    
    modifier inState(State _state) {
        require(currentState == _state, "Invalid state for this action");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor(address _seller, address _buyer) {
        admin = msg.sender;
        seller = _seller != address(0) ? _seller : msg.sender;
        buyer = _buyer;  // Can be address(0) initially
        propertyAddress = "${params.propertyAddress}";
        salePrice = ${params.salePrice} ether;
        depositAmount = (salePrice * ${params.depositPercent}) / 100;
        currentState = State.Listed;
        
        emit PropertyListed(propertyAddress, salePrice);
        emit ParticipantChanged("seller", seller);
        if (buyer != address(0)) {
            emit ParticipantChanged("buyer", buyer);
        }
    }
    
    // ===== ADMIN FUNCTIONS =====
    
    /// @notice Admin can change seller before deposit is paid
    function setSeller(address _seller) external onlyAdmin {
        require(currentState == State.Listed, "Cannot change seller now");
        require(_seller != address(0), "Invalid address");
        seller = _seller;
        emit ParticipantChanged("seller", _seller);
    }
    
    /// @notice Admin can set/change buyer before deposit is paid
    function setBuyer(address _buyer) external onlyAdmin {
        require(currentState == State.Listed, "Cannot change buyer now");
        buyer = _buyer;
        emit ParticipantChanged("buyer", _buyer);
    }
    
    /// @notice Get all participants
    function getParticipants() external view returns (address _admin, address _seller, address _buyer) {
        return (admin, seller, buyer);
    }
    
    // ===== BUYER FUNCTIONS =====
    
    /// @notice Buyer pays deposit to secure the property
    function payDeposit() external payable inState(State.Listed) {
        require(msg.value >= depositAmount, "Deposit too low");
        // If buyer was pre-set, only that buyer can deposit
        if (buyer != address(0)) {
            require(msg.sender == buyer, "You are not the designated buyer");
        } else {
            buyer = msg.sender;
            emit ParticipantChanged("buyer", msg.sender);
        }
        
        inspectionDeadline = block.timestamp + (${params.inspectionDays} * 1 days);
        currentState = State.DepositPaid;
        
        emit DepositReceived(msg.sender, msg.value);
    }
    
    /// @notice Buyer approves after inspection
    function approveInspection() external onlyBuyer inState(State.DepositPaid) {
        require(block.timestamp <= inspectionDeadline, "Inspection period expired");
        currentState = State.InspectionPassed;
        emit InspectionApproved(msg.sender);
    }
    
    /// @notice Buyer pays remaining balance
    function payBalance() external payable onlyBuyer inState(State.InspectionPassed) {
        uint256 remaining = salePrice - depositAmount;
        require(msg.value >= remaining, "Insufficient payment");
    }
    
    // ===== SELLER FUNCTIONS =====
    
    /// @notice Seller confirms title transfer and receives funds
    function confirmTransfer() external onlySeller inState(State.InspectionPassed) {
        require(address(this).balance >= salePrice, "Full payment not received");
        
        currentState = State.Completed;
        
        (bool success, ) = payable(seller).call{value: address(this).balance}("");
        require(success, "Transfer failed");
        
        emit SaleCompleted(seller, buyer, salePrice);
    }
    
    /// @notice Seller can cancel if buyer misses inspection deadline
    function cancelSale(string calldata reason) external onlySeller {
        require(
            currentState == State.Listed || 
            (currentState == State.DepositPaid && block.timestamp > inspectionDeadline),
            "Cannot cancel at this stage"
        );
        
        currentState = State.Cancelled;
        
        if (buyer != address(0) && address(this).balance > 0) {
            (bool success, ) = payable(buyer).call{value: address(this).balance}("");
            require(success, "Refund failed");
        }
        
        emit SaleCancelled(reason);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
    
    function getRemainingPayment() external view returns (uint256) {
        if (currentState == State.InspectionPassed) {
            return salePrice - address(this).balance;
        }
        return salePrice - depositAmount;
    }
    
    function getTimeUntilInspectionDeadline() external view returns (int256) {
        if (inspectionDeadline == 0) return -1;
        return int256(inspectionDeadline) - int256(block.timestamp);
    }
}
`,
    constructorArgs: (params) => [
      params.sellerAddress || '0x0000000000000000000000000000000000000000',
      params.buyerAddress || '0x0000000000000000000000000000000000000000'
    ],
  },

  carSale: {
    name: 'Car Sale (Defective Vehicle Scenario)',
    description: 'Escrow with mechanic inspection. Teaches information asymmetry: contract enforces process, not truth. Mechanic can attest honestly or lie.',
    icon: '🚗',
    fields: [
      { name: 'sellerAddress', prompt: 'Seller address (leave blank for deployer)', type: 'address', default: '' },
      { name: 'buyerAddress', prompt: 'Buyer address (leave blank to set later)', type: 'address', default: '' },
      { name: 'mechanicAddress', prompt: 'Mechanic/Inspector address (leave blank to set later)', type: 'address', default: '' },
    ],
    generateContract: () => {
      const carSaleSource = fs.readFileSync(path.join(PROJECT_ROOT, 'contracts', 'student', 'CarSale_000001.sol'), 'utf8');
      return carSaleSource;
    },
    constructorArgs: (params) => [
      params.sellerAddress || '0x0000000000000000000000000000000000000000',
      params.buyerAddress || '0x0000000000000000000000000000000000000000',
      params.mechanicAddress || '0x0000000000000000000000000000000000000000'
    ],
  },

  ransomPayment: {
    name: 'Ransomware Payment (Forensics Lab)',
    description: 'Victims pay ETH through contract; creates on-chain trail. Investigators trace to attacker address.',
    icon: '🔐',
    fields: [
      { name: 'attackerAddress', prompt: 'Attacker address (receives ransom)', type: 'address', default: '' },
    ],
    generateContract: () => {
      return fs.readFileSync(path.join(PROJECT_ROOT, 'contracts', 'student', 'RansomPayment_000001.sol'), 'utf8');
    },
    constructorArgs: (params) => [
      params.attackerAddress || '0x0000000000000000000000000000000000000000'
    ],
  },

  vehicleTitle: {
    name: 'Vehicle Title Transfer',
    description: 'Registry for vehicle ownership with transfer history and VIN tracking.',
    icon: '🚗',
    fields: [
      { name: 'vin', prompt: 'Vehicle Identification Number (VIN)', type: 'string', default: '1HGCM82633A004352' },
      { name: 'make', prompt: 'Vehicle make', type: 'string', default: 'Honda' },
      { name: 'model', prompt: 'Vehicle model', type: 'string', default: 'Accord' },
      { name: 'year', prompt: 'Vehicle year', type: 'uint', default: '2023' },
      { name: 'ownerAddress', prompt: 'Initial owner address (leave blank for deployer)', type: 'address', default: '' },
    ],
    generateContract: (params) => `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VehicleTitle
 * @dev Vehicle ownership registry for VIN: ${params.vin}
 * 
 * Features:
 * - Immutable vehicle details
 * - Ownership transfer with history
 * - Title status tracking (clean, salvage, etc.)
 * - Admin can set initial owner
 */
contract VehicleTitle {
    // ===== STATE VARIABLES =====
    address public admin;
    string public vin;
    string public make;
    string public model;
    uint256 public year;
    address public currentOwner;
    uint256 public transferCount;
    
    enum TitleStatus { Clean, Salvage, Rebuilt, Flood, Defective }
    TitleStatus public titleStatus;
    
    // Ownership history
    struct OwnerRecord {
        address owner;
        uint256 timestamp;
        uint256 mileage;
    }
    OwnerRecord[] public ownerHistory;
    
    // ===== EVENTS =====
    event VehicleRegistered(string vin, address owner);
    event OwnershipTransferred(address indexed from, address indexed to, uint256 mileage);
    event TitleStatusChanged(TitleStatus oldStatus, TitleStatus newStatus, string reason);
    event ParticipantChanged(string role, address participant);
    
    // ===== MODIFIERS =====
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this");
        _;
    }
    
    modifier onlyOwner() {
        require(msg.sender == currentOwner, "Only current owner can call this");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor(address _initialOwner) {
        admin = msg.sender;
        vin = "${params.vin}";
        make = "${params.make}";
        model = "${params.model}";
        year = ${params.year};
        currentOwner = _initialOwner != address(0) ? _initialOwner : msg.sender;
        titleStatus = TitleStatus.Clean;
        
        // Record first owner
        ownerHistory.push(OwnerRecord({
            owner: currentOwner,
            timestamp: block.timestamp,
            mileage: 0
        }));
        
        emit VehicleRegistered(vin, currentOwner);
        emit ParticipantChanged("owner", currentOwner);
    }
    
    // ===== ADMIN FUNCTIONS =====
    
    /// @notice Admin can force transfer (e.g., for corrections)
    function adminSetOwner(address _newOwner, uint256 mileage) external onlyAdmin {
        require(_newOwner != address(0), "Invalid address");
        address previousOwner = currentOwner;
        currentOwner = _newOwner;
        transferCount++;
        
        ownerHistory.push(OwnerRecord({
            owner: _newOwner,
            timestamp: block.timestamp,
            mileage: mileage
        }));
        
        emit OwnershipTransferred(previousOwner, _newOwner, mileage);
        emit ParticipantChanged("owner", _newOwner);
    }
    
    /// @notice Get all participants
    function getParticipants() external view returns (address _admin, address _owner) {
        return (admin, currentOwner);
    }
    
    // ===== TRANSFER FUNCTIONS =====
    
    /// @notice Transfer ownership to new owner
    /// @param newOwner Address of the new owner
    /// @param currentMileage Current odometer reading
    function transferOwnership(address newOwner, uint256 currentMileage) external onlyOwner {
        require(newOwner != address(0), "Invalid new owner address");
        require(newOwner != currentOwner, "Already the owner");
        
        // Verify mileage is not rolled back
        if (ownerHistory.length > 0) {
            uint256 lastMileage = ownerHistory[ownerHistory.length - 1].mileage;
            require(currentMileage >= lastMileage, "Mileage cannot decrease");
        }
        
        address previousOwner = currentOwner;
        currentOwner = newOwner;
        transferCount++;
        
        ownerHistory.push(OwnerRecord({
            owner: newOwner,
            timestamp: block.timestamp,
            mileage: currentMileage
        }));
        
        emit OwnershipTransferred(previousOwner, newOwner, currentMileage);
        emit ParticipantChanged("owner", newOwner);
    }
    
    /// @notice Report title status change (e.g., accident damage)
    /// @param newStatus The new title status
    /// @param reason Reason for the change
    function updateTitleStatus(TitleStatus newStatus, string calldata reason) external onlyOwner {
        TitleStatus oldStatus = titleStatus;
        titleStatus = newStatus;
        emit TitleStatusChanged(oldStatus, newStatus, reason);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    function getOwnerHistoryCount() external view returns (uint256) {
        return ownerHistory.length;
    }
    
    function getOwnerAt(uint256 index) external view returns (address owner, uint256 timestamp, uint256 mileage) {
        require(index < ownerHistory.length, "Index out of bounds");
        OwnerRecord memory record = ownerHistory[index];
        return (record.owner, record.timestamp, record.mileage);
    }
    
    function getVehicleInfo() external view returns (
        string memory _vin,
        string memory _make,
        string memory _model,
        uint256 _year,
        address _owner,
        TitleStatus _status
    ) {
        return (vin, make, model, year, currentOwner, titleStatus);
    }
    
    function getTitleStatusString() external view returns (string memory) {
        if (titleStatus == TitleStatus.Clean) return "Clean";
        if (titleStatus == TitleStatus.Salvage) return "Salvage";
        if (titleStatus == TitleStatus.Rebuilt) return "Rebuilt";
        if (titleStatus == TitleStatus.Flood) return "Flood Damage";
        if (titleStatus == TitleStatus.Defective) return "Defective";
        return "Unknown";
    }
}
`,
    constructorArgs: (params) => [
      params.ownerAddress || '0x0000000000000000000000000000000000000000'
    ],
  },

  eventTickets: {
    name: 'Event Tickets (Token Concepts - NFT)',
    description: 'NFT example: unique ticket IDs, ownerOf, transferTicket. Teaches non-fungible tokens.',
    icon: '🎟️',
    fields: [
      { name: 'eventName', prompt: 'Event name', type: 'string', default: 'Blockchain Conference 2026' },
      { name: 'maxSupply', prompt: 'Maximum ticket supply', type: 'uint', default: '100' },
      { name: 'ticketPrice', prompt: 'Ticket price in ETH', type: 'eth', default: '0.1' },
      { name: 'eventDate', prompt: 'Event date (YYYY-MM-DD)', type: 'string', default: '2026-06-15' },
      { name: 'organizerAddress', prompt: 'Organizer address (leave blank for deployer)', type: 'address', default: '' },
    ],
    generateContract: (params) => `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title EventTickets
 * @dev Ticket system for: ${params.eventName}
 * 
 * Features:
 * - Limited supply of ${params.maxSupply} tickets
 * - Price: ${params.ticketPrice} ETH per ticket
 * - Transfer capability
 * - Check-in verification for event entry
 * - Admin can designate organizer
 */
contract EventTickets {
    // ===== STATE VARIABLES =====
    address public admin;
    string public eventName;
    string public eventDate;
    uint256 public ticketPrice;
    uint256 public maxSupply;
    uint256 public ticketsSold;
    address public organizer;
    bool public eventCancelled;
    
    // Ticket ownership
    mapping(uint256 => address) public ticketOwner;
    mapping(address => uint256[]) public ownedTickets;
    mapping(uint256 => bool) public checkedIn;
    
    // ===== EVENTS =====
    event TicketPurchased(address indexed buyer, uint256 ticketId, uint256 price);
    event TicketTransferred(uint256 indexed ticketId, address indexed from, address indexed to);
    event TicketCheckedIn(uint256 indexed ticketId, address indexed holder);
    event EventCancelled(string reason);
    event RefundIssued(address indexed holder, uint256 amount);
    event ParticipantChanged(string role, address participant);
    
    // ===== MODIFIERS =====
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this");
        _;
    }
    
    modifier onlyOrganizer() {
        require(msg.sender == organizer, "Only organizer can call this");
        _;
    }
    
    modifier eventActive() {
        require(!eventCancelled, "Event has been cancelled");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor(address _organizer) {
        admin = msg.sender;
        eventName = "${params.eventName}";
        eventDate = "${params.eventDate}";
        ticketPrice = ${params.ticketPrice} ether;
        maxSupply = ${params.maxSupply};
        organizer = _organizer != address(0) ? _organizer : msg.sender;
        
        emit ParticipantChanged("organizer", organizer);
    }
    
    // ===== ADMIN FUNCTIONS =====
    
    /// @notice Admin can change organizer
    function setOrganizer(address _organizer) external onlyAdmin {
        require(_organizer != address(0), "Invalid address");
        organizer = _organizer;
        emit ParticipantChanged("organizer", _organizer);
    }
    
    /// @notice Get all participants
    function getParticipants() external view returns (address _admin, address _organizer) {
        return (admin, organizer);
    }
    
    // ===== PURCHASE FUNCTIONS =====
    
    /// @notice Purchase a ticket
    function buyTicket() external payable eventActive returns (uint256) {
        require(ticketsSold < maxSupply, "Sold out");
        require(msg.value >= ticketPrice, "Insufficient payment");
        
        ticketsSold++;
        uint256 ticketId = ticketsSold;
        
        ticketOwner[ticketId] = msg.sender;
        ownedTickets[msg.sender].push(ticketId);
        
        // Refund excess payment
        if (msg.value > ticketPrice) {
            (bool success, ) = payable(msg.sender).call{value: msg.value - ticketPrice}("");
            require(success, "Refund failed");
        }
        
        emit TicketPurchased(msg.sender, ticketId, ticketPrice);
        return ticketId;
    }
    
    /// @notice Buy multiple tickets at once
    function buyTickets(uint256 quantity) external payable eventActive returns (uint256[] memory) {
        require(ticketsSold + quantity <= maxSupply, "Not enough tickets available");
        require(msg.value >= ticketPrice * quantity, "Insufficient payment");
        
        uint256[] memory newTickets = new uint256[](quantity);
        
        for (uint256 i = 0; i < quantity; i++) {
            ticketsSold++;
            uint256 ticketId = ticketsSold;
            ticketOwner[ticketId] = msg.sender;
            ownedTickets[msg.sender].push(ticketId);
            newTickets[i] = ticketId;
            emit TicketPurchased(msg.sender, ticketId, ticketPrice);
        }
        
        // Refund excess
        uint256 totalCost = ticketPrice * quantity;
        if (msg.value > totalCost) {
            (bool success, ) = payable(msg.sender).call{value: msg.value - totalCost}("");
            require(success, "Refund failed");
        }
        
        return newTickets;
    }
    
    // ===== TRANSFER FUNCTIONS =====
    
    /// @notice Transfer ticket to another address
    function transferTicket(uint256 ticketId, address to) external eventActive {
        require(ticketOwner[ticketId] == msg.sender, "Not your ticket");
        require(!checkedIn[ticketId], "Ticket already used");
        require(to != address(0), "Invalid recipient");
        
        ticketOwner[ticketId] = to;
        ownedTickets[to].push(ticketId);
        
        // Remove from sender's list
        _removeTicketFromOwner(msg.sender, ticketId);
        
        emit TicketTransferred(ticketId, msg.sender, to);
    }
    
    // ===== CHECK-IN FUNCTIONS =====
    
    /// @notice Check in at the event (organizer only)
    function checkIn(uint256 ticketId) external onlyOrganizer eventActive {
        require(ticketOwner[ticketId] != address(0), "Ticket does not exist");
        require(!checkedIn[ticketId], "Already checked in");
        
        checkedIn[ticketId] = true;
        emit TicketCheckedIn(ticketId, ticketOwner[ticketId]);
    }
    
    /// @notice Verify a ticket is valid for entry
    function verifyTicket(uint256 ticketId) external view returns (
        bool valid,
        address holder,
        bool alreadyCheckedIn
    ) {
        if (ticketOwner[ticketId] == address(0)) {
            return (false, address(0), false);
        }
        return (true, ticketOwner[ticketId], checkedIn[ticketId]);
    }
    
    // ===== ORGANIZER FUNCTIONS =====
    
    /// @notice Cancel event and enable refunds
    function cancelEvent(string calldata reason) external onlyOrganizer {
        eventCancelled = true;
        emit EventCancelled(reason);
    }
    
    /// @notice Withdraw ticket sales (only if not cancelled)
    function withdrawFunds() external onlyOrganizer {
        require(!eventCancelled, "Cannot withdraw - event cancelled");
        (bool success, ) = payable(organizer).call{value: address(this).balance}("");
        require(success, "Withdrawal failed");
    }
    
    /// @notice Claim refund if event cancelled
    function claimRefund() external {
        require(eventCancelled, "Event not cancelled");
        
        uint256[] memory tickets = ownedTickets[msg.sender];
        require(tickets.length > 0, "No tickets to refund");
        
        uint256 refundAmount = tickets.length * ticketPrice;
        
        // Clear ownership
        for (uint256 i = 0; i < tickets.length; i++) {
            delete ticketOwner[tickets[i]];
        }
        delete ownedTickets[msg.sender];
        
        (bool success, ) = payable(msg.sender).call{value: refundAmount}("");
        require(success, "Refund failed");
        
        emit RefundIssued(msg.sender, refundAmount);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    function getMyTickets() external view returns (uint256[] memory) {
        return ownedTickets[msg.sender];
    }
    
    function getTicketsRemaining() external view returns (uint256) {
        return maxSupply - ticketsSold;
    }
    
    function getEventInfo() external view returns (
        string memory _name,
        string memory _date,
        uint256 _price,
        uint256 _sold,
        uint256 _remaining,
        bool _cancelled
    ) {
        return (eventName, eventDate, ticketPrice, ticketsSold, maxSupply - ticketsSold, eventCancelled);
    }
    
    // ===== INTERNAL FUNCTIONS =====
    
    function _removeTicketFromOwner(address owner, uint256 ticketId) internal {
        uint256[] storage tickets = ownedTickets[owner];
        for (uint256 i = 0; i < tickets.length; i++) {
            if (tickets[i] == ticketId) {
                tickets[i] = tickets[tickets.length - 1];
                tickets.pop();
                break;
            }
        }
    }
}
`,
    constructorArgs: (params) => [
      params.organizerAddress || '0x0000000000000000000000000000000000000000'
    ],
  },

  voting: {
    name: 'Voting System',
    description: 'Simple voting with proposal creation, weighted votes, deadline, and result tallying.',
    icon: '🗳️',
    fields: [
      { name: 'votingTitle', prompt: 'Voting title/topic', type: 'string', default: 'Board Election 2026' },
      { name: 'options', prompt: 'Voting options (comma-separated)', type: 'array', default: 'Alice,Bob,Charlie' },
      { name: 'durationDays', prompt: 'Voting duration in days', type: 'uint', default: '7' },
      { name: 'adminAddress', prompt: 'Administrator address (leave blank for deployer)', type: 'address', default: '' },
    ],
    generateContract: (params) => {
      const options = params.options.split(',').map(o => o.trim());
      const optionsInit = options.map((o, i) => `        options.push(Option("${o}", 0));`).join('\n');
      
      return `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VotingSystem
 * @dev Voting contract for: ${params.votingTitle}
 * 
 * Options: ${options.join(', ')}
 * Duration: ${params.durationDays} days
 */
contract VotingSystem {
    // ===== STATE VARIABLES =====
    string public votingTitle;
    uint256 public votingDeadline;
    address public administrator;
    bool public votingClosed;
    
    struct Option {
        string name;
        uint256 voteCount;
    }
    Option[] public options;
    
    mapping(address => bool) public hasVoted;
    mapping(address => uint256) public voterChoice;
    address[] public voters;
    
    // ===== EVENTS =====
    event VoteCast(address indexed voter, uint256 indexed optionIndex, string optionName);
    event VotingClosed(string winner, uint256 voteCount);
    event VotingExtended(uint256 newDeadline);
    event ParticipantChanged(string role, address participant);
    
    // ===== MODIFIERS =====
    modifier onlyAdmin() {
        require(msg.sender == administrator, "Only administrator can call this");
        _;
    }
    
    modifier votingOpen() {
        require(!votingClosed, "Voting is closed");
        require(block.timestamp <= votingDeadline, "Voting period has ended");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor(address _administrator) {
        votingTitle = "${params.votingTitle}";
        votingDeadline = block.timestamp + (${params.durationDays} * 1 days);
        administrator = _administrator != address(0) ? _administrator : msg.sender;
        
        // Initialize options
${optionsInit}
        
        emit ParticipantChanged("administrator", administrator);
    }
    
    // ===== ADMIN FUNCTIONS =====
    
    /// @notice Transfer admin role to another address
    function setAdministrator(address _newAdmin) external onlyAdmin {
        require(_newAdmin != address(0), "Invalid address");
        administrator = _newAdmin;
        emit ParticipantChanged("administrator", _newAdmin);
    }
    
    /// @notice Get participant info
    function getParticipants() external view returns (address _administrator) {
        return administrator;
    }
    
    // ===== VOTING FUNCTIONS =====
    
    /// @notice Cast a vote for an option
    /// @param optionIndex The index of the option to vote for
    function vote(uint256 optionIndex) external votingOpen {
        require(!hasVoted[msg.sender], "Already voted");
        require(optionIndex < options.length, "Invalid option");
        
        hasVoted[msg.sender] = true;
        voterChoice[msg.sender] = optionIndex;
        voters.push(msg.sender);
        options[optionIndex].voteCount++;
        
        emit VoteCast(msg.sender, optionIndex, options[optionIndex].name);
    }
    
    /// @notice Close voting early (admin only)
    function closeVoting() external onlyAdmin {
        require(!votingClosed, "Already closed");
        votingClosed = true;
        
        (string memory winner, uint256 count) = getWinner();
        emit VotingClosed(winner, count);
    }
    
    /// @notice Extend voting deadline (admin only)
    function extendVoting(uint256 additionalDays) external onlyAdmin {
        require(!votingClosed, "Voting is closed");
        votingDeadline += additionalDays * 1 days;
        emit VotingExtended(votingDeadline);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    function getOptionCount() external view returns (uint256) {
        return options.length;
    }
    
    function getOption(uint256 index) external view returns (string memory name, uint256 voteCount) {
        require(index < options.length, "Invalid index");
        return (options[index].name, options[index].voteCount);
    }
    
    function getAllResults() external view returns (string[] memory names, uint256[] memory votes) {
        names = new string[](options.length);
        votes = new uint256[](options.length);
        
        for (uint256 i = 0; i < options.length; i++) {
            names[i] = options[i].name;
            votes[i] = options[i].voteCount;
        }
        
        return (names, votes);
    }
    
    function getWinner() public view returns (string memory winnerName, uint256 winnerVotes) {
        require(options.length > 0, "No options");
        
        uint256 highestVotes = 0;
        uint256 winnerIndex = 0;
        
        for (uint256 i = 0; i < options.length; i++) {
            if (options[i].voteCount > highestVotes) {
                highestVotes = options[i].voteCount;
                winnerIndex = i;
            }
        }
        
        return (options[winnerIndex].name, highestVotes);
    }
    
    function getTotalVotes() external view returns (uint256) {
        return voters.length;
    }
    
    function getTimeRemaining() external view returns (int256) {
        if (votingClosed) return 0;
        return int256(votingDeadline) - int256(block.timestamp);
    }
    
    function getVotingStatus() external view returns (
        string memory _title,
        uint256 _deadline,
        uint256 _totalVotes,
        bool _closed,
        int256 _timeRemaining
    ) {
        int256 remaining = votingClosed ? int256(0) : int256(votingDeadline) - int256(block.timestamp);
        return (votingTitle, votingDeadline, voters.length, votingClosed, remaining);
    }
}
`;
    },
    constructorArgs: (params) => [
      params.adminAddress || '0x0000000000000000000000000000000000000000'
    ],
  },

  crowdfunding: {
    name: 'Crowdfunding Campaign',
    description: 'Fundraising with goal amount, deadline, contributions, and refund if goal not met.',
    icon: '💰',
    fields: [
      { name: 'campaignName', prompt: 'Campaign name', type: 'string', default: 'Community Garden Project' },
      { name: 'goalAmount', prompt: 'Funding goal in ETH', type: 'eth', default: '50' },
      { name: 'durationDays', prompt: 'Campaign duration in days', type: 'uint', default: '30' },
      { name: 'minimumContribution', prompt: 'Minimum contribution in ETH', type: 'eth', default: '0.01' },
      { name: 'creatorAddress', prompt: 'Creator/beneficiary address (leave blank for deployer)', type: 'address', default: '' },
    ],
    generateContract: (params) => `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Crowdfunding
 * @dev Crowdfunding campaign: ${params.campaignName}
 * 
 * Goal: ${params.goalAmount} ETH
 * Duration: ${params.durationDays} days
 * Min contribution: ${params.minimumContribution} ETH
 * 
 * If goal is reached: creator can withdraw
 * If goal not reached: contributors can claim refunds
 */
contract Crowdfunding {
    // ===== STATE VARIABLES =====
    address public admin;
    string public campaignName;
    address public creator;
    uint256 public goalAmount;
    uint256 public deadline;
    uint256 public minimumContribution;
    uint256 public totalRaised;
    bool public goalReached;
    bool public fundsWithdrawn;
    
    mapping(address => uint256) public contributions;
    address[] public contributors;
    
    // ===== EVENTS =====
    event ContributionReceived(address indexed contributor, uint256 amount, uint256 totalRaised);
    event GoalReached(uint256 totalAmount);
    event FundsWithdrawn(address indexed creator, uint256 amount);
    event RefundClaimed(address indexed contributor, uint256 amount);
    event CampaignExtended(uint256 newDeadline);
    event ParticipantChanged(string role, address participant);
    
    // ===== MODIFIERS =====
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this");
        _;
    }
    
    modifier onlyCreator() {
        require(msg.sender == creator, "Only creator can call this");
        _;
    }
    
    modifier campaignActive() {
        require(block.timestamp <= deadline, "Campaign has ended");
        require(!fundsWithdrawn, "Funds already withdrawn");
        _;
    }
    
    modifier campaignEnded() {
        require(block.timestamp > deadline || goalReached, "Campaign still active");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor(address _creator) {
        admin = msg.sender;
        campaignName = "${params.campaignName}";
        creator = _creator != address(0) ? _creator : msg.sender;
        goalAmount = ${params.goalAmount} ether;
        deadline = block.timestamp + (${params.durationDays} * 1 days);
        minimumContribution = ${params.minimumContribution} ether;
        
        emit ParticipantChanged("creator", creator);
    }
    
    // ===== ADMIN FUNCTIONS =====
    
    /// @notice Admin can change creator/beneficiary before funds withdrawn
    function setCreator(address _creator) external onlyAdmin {
        require(!fundsWithdrawn, "Funds already withdrawn");
        require(_creator != address(0), "Invalid address");
        creator = _creator;
        emit ParticipantChanged("creator", _creator);
    }
    
    /// @notice Get participant info
    function getParticipants() external view returns (address _admin, address _creator) {
        return (admin, creator);
    }
    
    // ===== CONTRIBUTION FUNCTIONS =====
    
    /// @notice Contribute to the campaign
    function contribute() external payable campaignActive {
        require(msg.value >= minimumContribution, "Below minimum contribution");
        
        if (contributions[msg.sender] == 0) {
            contributors.push(msg.sender);
        }
        
        contributions[msg.sender] += msg.value;
        totalRaised += msg.value;
        
        emit ContributionReceived(msg.sender, msg.value, totalRaised);
        
        // Check if goal reached
        if (totalRaised >= goalAmount && !goalReached) {
            goalReached = true;
            emit GoalReached(totalRaised);
        }
    }
    
    /// @notice Receive function to accept direct ETH transfers
    receive() external payable {
        require(msg.value >= minimumContribution, "Below minimum");
        require(block.timestamp <= deadline, "Campaign ended");
        
        if (contributions[msg.sender] == 0) {
            contributors.push(msg.sender);
        }
        contributions[msg.sender] += msg.value;
        totalRaised += msg.value;
        
        emit ContributionReceived(msg.sender, msg.value, totalRaised);
        
        if (totalRaised >= goalAmount && !goalReached) {
            goalReached = true;
            emit GoalReached(totalRaised);
        }
    }
    
    // ===== CREATOR FUNCTIONS =====
    
    /// @notice Withdraw funds if goal reached
    function withdrawFunds() external onlyCreator {
        require(goalReached, "Goal not reached");
        require(!fundsWithdrawn, "Already withdrawn");
        
        fundsWithdrawn = true;
        uint256 amount = address(this).balance;
        
        (bool success, ) = payable(creator).call{value: amount}("");
        require(success, "Withdrawal failed");
        
        emit FundsWithdrawn(creator, amount);
    }
    
    /// @notice Extend campaign deadline (only if goal not yet reached)
    function extendDeadline(uint256 additionalDays) external onlyCreator {
        require(!goalReached, "Goal already reached");
        require(block.timestamp <= deadline, "Campaign already ended");
        
        deadline += additionalDays * 1 days;
        emit CampaignExtended(deadline);
    }
    
    // ===== CONTRIBUTOR FUNCTIONS =====
    
    /// @notice Claim refund if goal not reached after deadline
    function claimRefund() external campaignEnded {
        require(!goalReached, "Goal was reached - no refunds");
        require(contributions[msg.sender] > 0, "No contribution to refund");
        
        uint256 amount = contributions[msg.sender];
        contributions[msg.sender] = 0;
        
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Refund failed");
        
        emit RefundClaimed(msg.sender, amount);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    function getContributorCount() external view returns (uint256) {
        return contributors.length;
    }
    
    function getMyContribution() external view returns (uint256) {
        return contributions[msg.sender];
    }
    
    function getRemainingToGoal() external view returns (uint256) {
        if (totalRaised >= goalAmount) return 0;
        return goalAmount - totalRaised;
    }
    
    function getTimeRemaining() external view returns (int256) {
        return int256(deadline) - int256(block.timestamp);
    }
    
    function getProgress() external view returns (uint256) {
        if (goalAmount == 0) return 100;
        return (totalRaised * 100) / goalAmount;
    }
    
    function getCampaignStatus() external view returns (
        string memory _name,
        uint256 _goal,
        uint256 _raised,
        uint256 _deadline,
        uint256 _contributors,
        bool _goalReached,
        bool _withdrawn
    ) {
        return (
            campaignName,
            goalAmount,
            totalRaised,
            deadline,
            contributors.length,
            goalReached,
            fundsWithdrawn
        );
    }
}
`,
    constructorArgs: (params) => [
      params.creatorAddress || '0x0000000000000000000000000000000000000000'
    ],
  },

  // ===== CLASSROOM VOTING DEMO =====
  classroomVote: {
    name: 'Classroom Voting Demo',
    description: 'Simple open voting for classroom demonstrations. Instructor controls, any address can vote once.',
    icon: '🎓',
    fields: [
      { name: 'question', prompt: 'Voting question', type: 'string', default: 'What should our lunch break policy be?' },
      { name: 'optionA', prompt: 'Option A', type: 'string', default: 'Keep lunch at 1 hour 30 minutes' },
      { name: 'optionB', prompt: 'Option B', type: 'string', default: 'Change to 1 hour lunch, leave 30 minutes early' },
    ],
    generateContract: (params) => `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ClassroomVote
 * @dev Simple classroom voting demonstration
 * 
 * Question: ${params.question}
 * Option A: ${params.optionA}
 * Option B: ${params.optionB}
 * 
 * Features:
 * - Open voting (any address can vote once)
 * - Instructor controls (open/close voting)
 * - Live results display
 */
contract ClassroomVote {
    // ===== STATE VARIABLES =====
    address public instructor;
    string public question;
    string public optionA;
    string public optionB;
    
    uint256 public votesForA;
    uint256 public votesForB;
    bool public votingOpen;
    
    mapping(address => bool) public hasVoted;
    mapping(address => string) public voterChoice;
    address[] public voters;
    
    // ===== EVENTS =====
    event VotingOpened(string question);
    event VoteCast(address indexed voter, string choice);
    event VotingClosed(string winner, uint256 winnerVotes, uint256 totalVotes);
    
    // ===== MODIFIERS =====
    modifier onlyInstructor() {
        require(msg.sender == instructor, "Only instructor can call this");
        _;
    }
    
    modifier whenVotingOpen() {
        require(votingOpen, "Voting is not open");
        _;
    }
    
    // ===== CONSTRUCTOR =====
    constructor() {
        instructor = msg.sender;
        question = "${params.question}";
        optionA = "${params.optionA}";
        optionB = "${params.optionB}";
        votingOpen = false;
    }
    
    // ===== INSTRUCTOR FUNCTIONS =====
    
    /// @notice Open voting for students
    function openVoting() external onlyInstructor {
        require(!votingOpen, "Voting already open");
        votingOpen = true;
        emit VotingOpened(question);
    }
    
    /// @notice Close voting and announce winner
    function closeVoting() external onlyInstructor {
        require(votingOpen, "Voting not open");
        votingOpen = false;
        
        string memory winner;
        uint256 winnerVotes;
        
        if (votesForA > votesForB) {
            winner = optionA;
            winnerVotes = votesForA;
        } else if (votesForB > votesForA) {
            winner = optionB;
            winnerVotes = votesForB;
        } else {
            winner = "TIE";
            winnerVotes = votesForA;
        }
        
        emit VotingClosed(winner, winnerVotes, voters.length);
    }
    
    /// @notice Reset voting for a new round
    function resetVoting() external onlyInstructor {
        require(!votingOpen, "Close voting first");
        
        // Clear all votes
        for (uint256 i = 0; i < voters.length; i++) {
            delete hasVoted[voters[i]];
            delete voterChoice[voters[i]];
        }
        delete voters;
        votesForA = 0;
        votesForB = 0;
    }
    
    // ===== STUDENT VOTING =====
    
    /// @notice Vote for Option A
    function voteA() external whenVotingOpen {
        require(!hasVoted[msg.sender], "Already voted");
        
        hasVoted[msg.sender] = true;
        voterChoice[msg.sender] = "A";
        voters.push(msg.sender);
        votesForA++;
        
        emit VoteCast(msg.sender, optionA);
    }
    
    /// @notice Vote for Option B
    function voteB() external whenVotingOpen {
        require(!hasVoted[msg.sender], "Already voted");
        
        hasVoted[msg.sender] = true;
        voterChoice[msg.sender] = "B";
        voters.push(msg.sender);
        votesForB++;
        
        emit VoteCast(msg.sender, optionB);
    }
    
    // ===== VIEW FUNCTIONS =====
    
    /// @notice Get current results (can be called anytime)
    function getResults() external view returns (
        string memory _question,
        string memory _optionA,
        uint256 _votesA,
        string memory _optionB,
        uint256 _votesB,
        uint256 _totalVoters,
        bool _isOpen
    ) {
        return (question, optionA, votesForA, optionB, votesForB, voters.length, votingOpen);
    }
    
    /// @notice Get the current winner (or leading option)
    function getWinner() external view returns (string memory winner, uint256 votes, string memory status) {
        if (votesForA > votesForB) {
            return (optionA, votesForA, votesForA == votesForB ? "TIE" : "LEADING");
        } else if (votesForB > votesForA) {
            return (optionB, votesForB, "LEADING");
        } else {
            return ("TIE", votesForA, "TIE");
        }
    }
    
    /// @notice Get formatted results for display
    function getFormattedResults() external view returns (string memory) {
        // Returns a simple summary string
        return string(abi.encodePacked(
            "Question: ", question,
            " | Option A: ", _uint2str(votesForA), " votes",
            " | Option B: ", _uint2str(votesForB), " votes",
            " | Total: ", _uint2str(voters.length), " voters"
        ));
    }
    
    /// @notice Check if an address has voted
    function checkVoter(address voter) external view returns (bool voted, string memory choice) {
        return (hasVoted[voter], voterChoice[voter]);
    }
    
    /// @notice Get total number of voters
    function getTotalVoters() external view returns (uint256) {
        return voters.length;
    }
    
    // Helper to convert uint to string
    function _uint2str(uint256 _i) internal pure returns (string memory) {
        if (_i == 0) return "0";
        uint256 j = _i;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint256 k = length;
        while (_i != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(_i - _i / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }
}
`,
    constructorArgs: () => [],
  },
};

// ============================================================================
// BUILDER WIZARD
// ============================================================================

async function selectTemplate() {
  console.log(color('cyan', '\n📋 SELECT A CONTRACT TEMPLATE\n'));
  console.log(line());
  
  const templateKeys = Object.keys(TEMPLATES);
  templateKeys.forEach((key, index) => {
    const t = TEMPLATES[key];
    console.log(`  ${index + 1}. ${t.icon} ${color('bright', t.name)}`);
    console.log(`     ${color('dim', t.description)}\n`);
  });
  
  const choice = await ask(`Select template (1-${templateKeys.length}): `);
  const index = parseInt(choice) - 1;
  
  if (index < 0 || index >= templateKeys.length) {
    console.log(color('red', 'Invalid choice'));
    return null;
  }
  
  return templateKeys[index];
}

async function customizeTemplate(templateKey) {
  const template = TEMPLATES[templateKey];
  console.log(color('cyan', `\n⚙️ CUSTOMIZE: ${template.name}\n`));
  console.log(line());
  console.log('Enter your values or press Enter for defaults.\n');
  
  const params = {};
  
  for (const field of template.fields) {
    const defaultText = color('dim', ` [default: ${field.default}]`);
    const value = await ask(`${field.prompt}${defaultText}: `);
    params[field.name] = value.trim() || field.default;
  }
  
  return params;
}

function generateContractName(templateKey, params) {
  // Generate a unique contract name based on template and a parameter
  const baseName = templateKey.charAt(0).toUpperCase() + templateKey.slice(1);
  const timestamp = Date.now().toString().slice(-6);
  return `${baseName}_${timestamp}`;
}

async function reviewContract(contractCode, contractName) {
  console.log(color('cyan', '\n📄 CONTRACT PREVIEW\n'));
  console.log(line('═'));
  console.log(color('bright', `Contract Name: ${contractName}.sol\n`));
  
  // Show the contract with line numbers
  const lines = contractCode.split('\n');
  const preview = lines.slice(0, 50).map((line, i) => 
    `${color('dim', String(i + 1).padStart(3))} │ ${line}`
  ).join('\n');
  
  console.log(preview);
  
  if (lines.length > 50) {
    console.log(color('dim', `\n... ${lines.length - 50} more lines ...\n`));
  }
  
  console.log(line('═'));
  
  const confirm = await ask('\nProceed with this contract? (y/n): ');
  return confirm.toLowerCase() === 'y';
}

// ============================================================================
// COMPILE & DEPLOY
// ============================================================================

function ensureStudentDir() {
  if (!fs.existsSync(STUDENT_CONTRACTS_DIR)) {
    fs.mkdirSync(STUDENT_CONTRACTS_DIR, { recursive: true });
    console.log(color('green', `✓ Created student contracts directory`));
  }
}

async function writeContract(contractName, contractCode) {
  ensureStudentDir();
  const filePath = path.join(STUDENT_CONTRACTS_DIR, `${contractName}.sol`);
  console.log(color('dim', `  → fs.writeFileSync(contracts/student/${contractName}.sol)`));
  fs.writeFileSync(filePath, contractCode);
  console.log(color('green', `✓ Contract written to: contracts/student/${contractName}.sol`));
  return filePath;
}

async function compileContract(contractName) {
  console.log(color('yellow', '\n⏳ Compiling contract...\n'));
  
  try {
    // Run hardhat compile
    console.log(color('dim', '  → npx hardhat compile'));
    execSync('npx hardhat compile', {
      cwd: PROJECT_ROOT,
      stdio: 'pipe',
      encoding: 'utf-8',
    });
    
    // Read the compiled artifact
    const artifactPath = path.join(
      PROJECT_ROOT,
      'artifacts',
      'contracts',
      'student',
      `${contractName}.sol`,
      `${contractName}.json`
    );
    
    // Wait a moment for file system
    await new Promise(r => setTimeout(r, 500));
    
    if (!fs.existsSync(artifactPath)) {
      // Try to find any contract in the file
      const studentArtifactDir = path.join(PROJECT_ROOT, 'artifacts', 'contracts', 'student', `${contractName}.sol`);
      if (fs.existsSync(studentArtifactDir)) {
        const files = fs.readdirSync(studentArtifactDir).filter(f => f.endsWith('.json') && !f.includes('dbg'));
        if (files.length > 0) {
          const actualArtifact = path.join(studentArtifactDir, files[0]);
          const artifact = JSON.parse(fs.readFileSync(actualArtifact, 'utf-8'));
          console.log(color('green', '✓ Compilation successful!'));
          return { success: true, abi: artifact.abi, bytecode: artifact.bytecode, contractName: artifact.contractName };
        }
      }
      throw new Error('Artifact not found after compilation');
    }
    
    const artifact = JSON.parse(fs.readFileSync(artifactPath, 'utf-8'));
    console.log(color('green', '✓ Compilation successful!'));
    return { success: true, abi: artifact.abi, bytecode: artifact.bytecode, contractName: artifact.contractName };
    
  } catch (error) {
    const stderr = error.stderr?.toString() || error.message;
    console.log(color('red', '✗ Compilation failed!\n'));
    
    // Parse and display errors nicely
    const errorLines = stderr.split('\n').filter(line => 
      line.includes('Error') || line.includes('error') || line.includes('-->') || line.includes('|')
    );
    
    if (errorLines.length > 0) {
      console.log(color('yellow', 'Compiler errors:\n'));
      errorLines.slice(0, 20).forEach(line => console.log(`  ${line}`));
    } else {
      console.log(stderr.slice(0, 500));
    }
    
    return { success: false, error: stderr };
  }
}

async function deployContract(abi, bytecode, constructorArgs = []) {
  console.log(color('yellow', '\n⏳ Deploying contract...\n'));
  
  try {
    const factory = new ethers.ContractFactory(abi, bytecode, wallet);
    console.log(color('dim', '  → factory.deploy(...constructorArgs)'));
    const contract = await factory.deploy(...constructorArgs);
    
    console.log(color('dim', `  Transaction hash: ${contract.deploymentTransaction().hash}`));
    console.log(color('dim', '  → contract.waitForDeployment()'));
    await contract.waitForDeployment();
    console.log(color('dim', '  → contract.getAddress()'));
    const address = await contract.getAddress();
    
    console.log(color('green', `\n✓ Contract deployed successfully!`));
    console.log(color('bright', `  Address: ${address}`));
    
    return { success: true, address, contract };
    
  } catch (error) {
    console.log(color('red', `✗ Deployment failed: ${error.message}`));
    return { success: false, error: error.message };
  }
}

// ============================================================================
// INTERACTION HELPER
// ============================================================================

async function interactWithContract(contract, abi) {
  console.log(color('cyan', '\n🔧 CONTRACT INTERACTION\n'));
  console.log(line());
  
  // Parse ABI to get functions
  const iface = new ethers.Interface(abi);
  const functions = [];
  const viewFunctions = [];
  
  iface.forEachFunction((func) => {
    if (func.stateMutability === 'view' || func.stateMutability === 'pure') {
      viewFunctions.push(func);
    } else {
      functions.push(func);
    }
  });
  
  while (true) {
    console.log(color('cyan', '\n📖 View Functions (read-only):'));
    viewFunctions.forEach((f, i) => {
      const inputs = f.inputs.map(inp => `${inp.type} ${inp.name}`).join(', ');
      console.log(`  ${i + 1}. ${f.name}(${inputs})`);
    });
    
    console.log(color('cyan', '\n📝 Write Functions (modify state):'));
    functions.forEach((f, i) => {
      const inputs = f.inputs.map(inp => `${inp.type} ${inp.name}`).join(', ');
      const payable = f.payable ? ' [payable]' : '';
      console.log(`  ${viewFunctions.length + i + 1}. ${f.name}(${inputs})${color('yellow', payable)}`);
    });
    
    console.log(color('dim', '\n  0. Exit interaction'));
    
    const choice = await ask('\nSelect function: ');
    
    if (choice === '0') break;
    
    const index = parseInt(choice) - 1;
    let selectedFunc;
    let isView = false;
    
    if (index < viewFunctions.length) {
      selectedFunc = viewFunctions[index];
      isView = true;
    } else if (index < viewFunctions.length + functions.length) {
      selectedFunc = functions[index - viewFunctions.length];
    } else {
      console.log(color('red', 'Invalid choice'));
      continue;
    }
    
    // Get arguments
    const args = [];
    for (const input of selectedFunc.inputs) {
      const value = await ask(`  Enter ${input.name} (${input.type}): `);
      
      // Convert value based on type
      if (input.type.includes('uint') || input.type.includes('int')) {
        args.push(BigInt(value));
      } else if (input.type === 'bool') {
        args.push(value.toLowerCase() === 'true');
      } else {
        args.push(value);
      }
    }
    
    // Get value for payable functions
    let txValue = 0n;
    if (selectedFunc.payable) {
      const ethValue = await ask('  Send ETH value (in ETH, e.g., 0.1): ');
      if (ethValue) {
        txValue = ethers.parseEther(ethValue);
      }
    }
    
    try {
      if (isView) {
        const result = await contract[selectedFunc.name](...args);
        console.log(color('green', `\n✓ Result: ${formatResult(result)}`));
      } else {
        console.log(color('yellow', '\n⏳ Sending transaction...'));
        const tx = await contract[selectedFunc.name](...args, { value: txValue });
        console.log(color('dim', `  Transaction hash: ${tx.hash}`));
        const receipt = await tx.wait();
        console.log(color('green', `✓ Transaction confirmed in block ${receipt.blockNumber}`));
        
        if (receipt.logs.length > 0) {
          console.log(color('cyan', '\n  Events emitted:'));
          receipt.logs.forEach((log, i) => {
            try {
              const parsed = iface.parseLog(log);
              if (parsed) {
                console.log(`    ${parsed.name}: ${JSON.stringify(parsed.args.toObject())}`);
              }
            } catch (e) {
              // Skip unparseable logs
            }
          });
        }
      }
    } catch (error) {
      console.log(color('red', `\n✗ Error: ${error.reason || error.message}`));
    }
    
    await pause();
  }
}

function formatResult(result) {
  if (typeof result === 'bigint') {
    // Check if it looks like ETH (> 1e15)
    if (result > 1000000000000000n) {
      return `${ethers.formatEther(result)} ETH (${result})`;
    }
    return result.toString();
  }
  if (Array.isArray(result)) {
    return result.map(formatResult).join(', ');
  }
  if (typeof result === 'object' && result !== null) {
    return JSON.stringify(result, (_, v) => typeof v === 'bigint' ? v.toString() : v);
  }
  return String(result);
}

// ============================================================================
// MAIN BUILDER FLOW
// ============================================================================

async function builderWizard(externalRl = null) {
  // Initialize readline with external interface if provided
  initReadline(externalRl);
  
  // Initialize provider/wallet if not already done
  if (!provider || !wallet) {
    try {
      provider = new ethers.JsonRpcProvider(RPC_URL);
      console.log(color('dim', '  → provider.getBlockNumber()'));
      await provider.getBlockNumber();
      wallet = new ethers.Wallet(selectedAccount.key, provider);
    } catch (error) {
      console.log(color('red', `✗ Connection failed: ${error.message}`));
      return;
    }
  }
  
  console.log(color('cyan', '\n🏗️ SMART CONTRACT BUILDER LAB\n'));
  console.log('═'.repeat(60));
  console.log('Build your own smart contract from guided templates!');
  console.log('═'.repeat(60));
  
  // Step 1: Select template
  const templateKey = await selectTemplate();
  if (!templateKey) return;
  
  const template = TEMPLATES[templateKey];
  console.log(color('green', `\n✓ Selected: ${template.icon} ${template.name}`));
  
  // Step 2: Customize
  const params = await customizeTemplate(templateKey);
  
  // Step 3: Generate contract
  console.log(color('yellow', '\n⏳ Generating contract...'));
  const contractCode = template.generateContract(params);
  const contractName = generateContractName(templateKey, params);
  
  // Step 4: Review
  const proceed = await reviewContract(contractCode, contractName);
  if (!proceed) {
    console.log(color('yellow', '\nContract creation cancelled.'));
    return;
  }
  
  // Step 5: Write file
  await writeContract(contractName, contractCode);
  
  // Step 6: Compile
  const compileResult = await compileContract(contractName);
  if (!compileResult.success) {
    const retry = await ask('\nWould you like to edit and retry? (y/n): ');
    if (retry.toLowerCase() === 'y') {
      console.log(color('yellow', `\nEdit the file at: contracts/student/${contractName}.sol`));
      console.log('Then run the compile command again.');
    }
    return;
  }
  
  // Step 7: Deploy
  const doDeploy = await ask('\nDeploy contract to blockchain? (y/n): ');
  if (doDeploy.toLowerCase() !== 'y') {
    console.log(color('green', '\n✓ Contract saved and compiled. You can deploy later.'));
    return;
  }
  
  const constructorArgs = template.constructorArgs(params);
  const deployResult = await deployContract(compileResult.abi, compileResult.bytecode, constructorArgs);
  
  if (!deployResult.success) {
    return;
  }
  
  // Save deployment info
  const deploymentInfo = {
    contractName,
    address: deployResult.address,
    deployer: selectedAccount.address,
    timestamp: new Date().toISOString(),
    template: templateKey,
  };
  
  const deploymentsFile = path.join(STUDENT_CONTRACTS_DIR, 'deployments.json');
  let deployments = [];
  if (fs.existsSync(deploymentsFile)) {
    deployments = JSON.parse(fs.readFileSync(deploymentsFile, 'utf-8'));
  }
  deployments.push(deploymentInfo);
  fs.writeFileSync(deploymentsFile, JSON.stringify(deployments, null, 2));
  
  console.log(color('dim', `\n  Deployment saved to: contracts/student/deployments.json`));
  
  // Step 8: Interact
  const doInteract = await ask('\nInteract with your deployed contract? (y/n): ');
  if (doInteract.toLowerCase() === 'y') {
    await interactWithContract(deployResult.contract, compileResult.abi);
  }
  
  console.log(color('green', '\n✓ Contract Builder Lab complete!'));
  console.log(color('dim', `Your contract is live at: ${deployResult.address}`));
}

// ============================================================================
// VIEW DEPLOYMENTS
// ============================================================================

async function viewDeployments() {
  console.log(color('cyan', '\n📋 YOUR DEPLOYED CONTRACTS\n'));
  console.log(line());
  
  const deploymentsFile = path.join(STUDENT_CONTRACTS_DIR, 'deployments.json');
  
  if (!fs.existsSync(deploymentsFile)) {
    console.log(color('yellow', 'No deployments found yet. Build and deploy a contract first!'));
    return;
  }
  
  const allDeployments = JSON.parse(fs.readFileSync(deploymentsFile, 'utf-8'));
  
  if (allDeployments.length === 0) {
    console.log(color('yellow', 'No deployments found.'));
    return;
  }
  
  // Filter to only contracts that exist on chain (excludes stale entries after chain reset)
  console.log(color('dim', '  Checking which contracts exist on chain...'));
  console.log(color('dim', '  → provider.getCode(address) for each deployment'));
  const existenceChecks = await Promise.all(
    allDeployments.map(async (d) => {
      const code = await provider.getCode(d.address);
      return { deployment: d, exists: !!code && code !== '0x' };
    })
  );
  const deployments = existenceChecks.filter((c) => c.exists).map((c) => c.deployment);
  const staleCount = allDeployments.length - deployments.length;
  
  if (staleCount > 0) {
    console.log(color('dim', `  (${staleCount} deployment(s) no longer on chain—hidden)\n`));
  }
  
  if (deployments.length === 0) {
    console.log(color('yellow', '\nNo accessible contracts found.'));
    console.log(color('dim', '\n  All recorded deployments are no longer on this chain (e.g. node was restarted).'));
    console.log(color('cyan', '  Build and deploy a new contract (option 1) to get started.'));
    return;
  }
  
  deployments.forEach((d, i) => {
    const template = TEMPLATES[d.template];
    console.log(`\n  ${i + 1}. ${template?.icon || '📜'} ${color('bright', d.contractName)}`);
    console.log(`     Address: ${d.address}`);
    console.log(`     Template: ${d.template}`);
    console.log(`     Deployed: ${d.timestamp}`);
  });
  
  const choice = await ask('\nSelect contract to interact (0 to go back): ');
  const index = parseInt(choice) - 1;
  
  if (index < 0 || index >= deployments.length) return;
  
  const deployment = deployments[index];
  
  // Load the ABI
  const artifactPath = path.join(
    PROJECT_ROOT,
    'artifacts',
    'contracts',
    'student',
    `${deployment.contractName}.sol`
  );
  
  if (!fs.existsSync(artifactPath)) {
    console.log(color('red', 'Contract artifacts not found. May need to recompile.'));
    return;
  }
  
  const files = fs.readdirSync(artifactPath).filter(f => f.endsWith('.json') && !f.includes('dbg'));
  if (files.length === 0) {
    console.log(color('red', 'No ABI found.'));
    return;
  }
  
  const artifact = JSON.parse(fs.readFileSync(path.join(artifactPath, files[0]), 'utf-8'));
  
  // Verify contract exists at address (catches chain reset or wrong network)
  console.log(color('dim', '  → provider.getCode(deployment.address)'));
  const code = await provider.getCode(deployment.address);
  if (!code || code === '0x') {
    console.log(color('red', '\n✗ No contract found at this address.'));
    console.log(color('yellow', '\n  This usually means:'));
    console.log('    • The blockchain node was restarted (local chain state was reset)');
    console.log('    • You\'re connected to a different RPC than where it was deployed');
    console.log(color('cyan', '\n  Fix: Build and deploy the contract again (option 1), or connect to the'));
    console.log('  same RPC where it was originally deployed.');
    return;
  }
  
  const contract = new ethers.Contract(deployment.address, artifact.abi, wallet);
  
  await interactWithContract(contract, artifact.abi);
}

// ============================================================================
// MAIN MENU
// ============================================================================

async function mainMenu() {
  while (true) {
    console.log(color('cyan', '\n═══ CONTRACT BUILDER LAB ═══\n'));
    console.log('  1. 🏗️  Build New Contract (Guided)');
    console.log('  2. 📋 View My Deployments');
    console.log('  3. 📖 Learn About Templates');
    console.log('  0. Exit');
    
    const choice = await ask('\nSelect option: ');
    
    switch (choice) {
      case '1':
        await builderWizard();
        await pause();
        break;
      case '2':
        await viewDeployments();
        await pause();
        break;
      case '3':
        await showTemplateInfo();
        await pause();
        break;
      case '0':
        console.log(color('cyan', '\n✓ Thanks for using Contract Builder Lab!\n'));
        rl.close();
        process.exit(0);
      default:
        console.log(color('red', 'Invalid choice'));
    }
  }
}

async function showTemplateInfo() {
  console.log(color('cyan', '\n📖 TEMPLATE INFORMATION\n'));
  console.log(line('═'));
  
  for (const [key, template] of Object.entries(TEMPLATES)) {
    console.log(`\n${template.icon} ${color('bright', template.name)}`);
    console.log(color('dim', line('-', 50)));
    console.log(template.description);
    console.log(color('cyan', '\nCustomizable fields:'));
    template.fields.forEach(f => {
      console.log(`  • ${f.name}: ${f.prompt}`);
    });
  }
  
  console.log('\n' + line('═'));
}

// ============================================================================
// STARTUP
// ============================================================================

async function init() {
  // Initialize readline for standalone execution
  initReadline();
  
  console.log(color('cyan', '\n🏗️ SMART CONTRACT BUILDER LAB\n'));
  console.log('Build, compile, and deploy your own smart contracts!');
  console.log(line());
  
  console.log(`\n📡 Connecting to: ${RPC_URL}`);
  
  try {
    provider = new ethers.JsonRpcProvider(RPC_URL);
    console.log(color('dim', '  → provider.getBlockNumber()'));
    await provider.getBlockNumber();
    wallet = new ethers.Wallet(selectedAccount.key, provider);
    
    console.log(color('green', '✓ Connected to blockchain'));
    console.log(color('dim', `  Account: ${selectedAccount.address}`));
    
    console.log(color('dim', '  → provider.getBalance(account)'));
    const balance = await provider.getBalance(selectedAccount.address);
    console.log(color('dim', `  Balance: ${ethers.formatEther(balance)} ETH`));
    
  } catch (error) {
    console.log(color('red', `✗ Connection failed: ${error.message}`));
    console.log('\nMake sure the blockchain node is running.');
    console.log('  Set RPC_URL if using a different endpoint.');
    process.exit(1);
  }
  
  await mainMenu();
}

// Export for use in interactive.js
export { builderWizard, viewDeployments, showTemplateInfo };

// Run if executed directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  init().catch(console.error);
}
