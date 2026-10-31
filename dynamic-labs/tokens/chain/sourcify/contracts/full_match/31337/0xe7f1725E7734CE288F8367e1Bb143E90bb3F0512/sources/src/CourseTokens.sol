// SPDX-License-Identifier: MIT
// The contracts on the day-3 course chain: a dollar token behind a proxy, and a badge (an NFT)
// with a shop that sells it. Kept short so a student can read them on the explorer's Contract
// tab. Training code: it leaves out checks a real token needs.
pragma solidity 0.8.24;

// A dollar token built like the big stablecoins: 6 decimals, an issuer who mints, and a
// blacklist only the issuer can change. It runs behind DollarProxy (below): people send their
// transactions to the proxy, which keeps the balances and borrows this contract's code.
contract CourseDollar {
    string public constant name = "Course Dollar";
    string public constant symbol = "cUSD";
    uint8 public constant decimals = 6; // 1 cUSD is stored as 1000000

    address public owner; // the issuer
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => bool) public isBlackListed;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event AddedBlackList(address indexed user);
    event RemovedBlackList(address indexed user);
    event DestroyedBlackFunds(address indexed user, uint256 balance);

    modifier onlyOwner() {
        require(msg.sender == owner, "only the issuer");
        _;
    }

    // Runs once, through the proxy, when the proxy is created. A proxy cannot use a constructor:
    // a constructor would write this contract's storage, not the proxy's.
    function initialize(address issuer) external {
        require(owner == address(0), "already set up");
        owner = issuer;
    }

    // New money: a Transfer from address zero.
    function mint(address to, uint256 value) external onlyOwner {
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(!isBlackListed[msg.sender], "sender is blacklisted"); // the sender only
        _move(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(!isBlackListed[from], "sender is blacklisted");
        require(allowance[from][msg.sender] >= value, "allowance too low");
        allowance[from][msg.sender] -= value;
        _move(from, to, value);
        return true;
    }

    function addBlackList(address user) external onlyOwner {
        isBlackListed[user] = true;
        emit AddedBlackList(user);
    }

    function removeBlackList(address user) external onlyOwner {
        isBlackListed[user] = false;
        emit RemovedBlackList(user);
    }

    // Wipes a listed address's balance. Like USDT's, it writes no Transfer log.
    function destroyBlackFunds(address user) external onlyOwner {
        require(isBlackListed[user], "not blacklisted");
        uint256 funds = balanceOf[user];
        balanceOf[user] = 0;
        totalSupply -= funds;
        emit DestroyedBlackFunds(user, funds);
    }

    function _move(address from, address to, uint256 value) internal {
        require(balanceOf[from] >= value, "balance too low");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
    }
}

// An ERC-1967 proxy: it holds the token's balances and runs CourseDollar's code on them with
// DELEGATECALL. The code's address sits in a fixed storage slot, so an explorer knows where to
// look, and changing it (an upgrade) changes the token's rules for every holder at once.
contract DollarProxy {
    // keccak256("eip1967.proxy.implementation") - 1 and keccak256("eip1967.proxy.admin") - 1
    bytes32 internal constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 internal constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;

    event Upgraded(address indexed implementation);

    constructor(address implementation, bytes memory setup) {
        assembly {
            sstore(IMPLEMENTATION_SLOT, implementation)
            sstore(ADMIN_SLOT, caller())
        }
        emit Upgraded(implementation);
        (bool ok, ) = implementation.delegatecall(setup); // CourseDollar.initialize, on this storage
        require(ok, "setup failed");
    }

    // Only the admin can swap the code. Not used on the course chain.
    function upgradeTo(address implementation) external {
        address admin;
        assembly { admin := sload(ADMIN_SLOT) }
        require(msg.sender == admin, "only the admin");
        assembly { sstore(IMPLEMENTATION_SLOT, implementation) }
        emit Upgraded(implementation);
    }

    // Every other call: run the implementation's code against this contract's storage.
    fallback() external payable {
        assembly {
            let implementation := sload(IMPLEMENTATION_SLOT)
            calldatacopy(0, 0, calldatasize())
            let ok := delegatecall(gas(), implementation, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch ok
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}

// A minimal NFT (the ERC-721 core, without the "safe" transfers): each badge is one numbered
// token with one owner. Anyone can mint one, to any address, with any metadata.
contract CourseBadge {
    string public constant name = "Course Badge";
    string public constant symbol = "BADGE";
    uint256 public totalSupply; // also the last badge number minted

    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256) public balanceOf;
    mapping(uint256 => address) public getApproved;
    mapping(address => mapping(address => bool)) public isApprovedForAll;
    mapping(uint256 => string) private metadata;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    // A mint is a Transfer from address zero. The metadata here is a data: URI, so it is stored
    // on chain; most real NFTs store a link to metadata kept somewhere else.
    function mint(address to, string calldata uri) external returns (uint256 tokenId) {
        require(to != address(0), "no owner");
        require(bytes(uri).length <= 2048, "metadata too long");
        tokenId = ++totalSupply;
        ownerOf[tokenId] = to;
        balanceOf[to] += 1;
        metadata[tokenId] = uri;
        emit Transfer(address(0), to, tokenId);
    }

    function tokenURI(uint256 tokenId) external view returns (string memory) {
        require(ownerOf[tokenId] != address(0), "no such badge");
        return metadata[tokenId];
    }

    function approve(address to, uint256 tokenId) external {
        address holder = ownerOf[tokenId];
        require(msg.sender == holder || isApprovedForAll[holder][msg.sender], "not allowed");
        getApproved[tokenId] = to;
        emit Approval(holder, to, tokenId);
    }

    function setApprovalForAll(address operator, bool approved) external {
        isApprovedForAll[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    function transferFrom(address from, address to, uint256 tokenId) external {
        require(ownerOf[tokenId] == from, "not the owner");
        require(to != address(0), "no owner");
        require(
            msg.sender == from || getApproved[tokenId] == msg.sender || isApprovedForAll[from][msg.sender],
            "not allowed"
        );
        ownerOf[tokenId] = to;
        balanceOf[from] -= 1;
        balanceOf[to] += 1;
        delete getApproved[tokenId];
        emit Transfer(from, to, tokenId);
    }
}

// Sells badges for ETH. The buyer pays the shop; the shop moves the badge (a Transfer log) and
// pays the seller (an internal transfer: no transaction of its own).
contract BadgeShop {
    CourseBadge public immutable badges;
    mapping(uint256 => uint256) public priceOf;
    mapping(uint256 => address) public sellerOf;

    event Listed(uint256 indexed tokenId, address indexed seller, uint256 price);
    event Sold(uint256 indexed tokenId, address indexed seller, address indexed buyer, uint256 price);

    constructor(CourseBadge badgeContract) {
        badges = badgeContract;
    }

    // The seller must first approve the shop to move the badge.
    function list(uint256 tokenId, uint256 price) external {
        require(badges.ownerOf(tokenId) == msg.sender, "not the owner");
        require(price > 0, "no price");
        priceOf[tokenId] = price;
        sellerOf[tokenId] = msg.sender;
        emit Listed(tokenId, msg.sender, price);
    }

    function buy(uint256 tokenId) external payable {
        uint256 price = priceOf[tokenId];
        address seller = sellerOf[tokenId];
        require(price > 0, "not for sale");
        require(msg.value == price, "wrong price");
        delete priceOf[tokenId];
        delete sellerOf[tokenId];
        badges.transferFrom(seller, msg.sender, tokenId);
        (bool paid, ) = seller.call{value: price}("");
        require(paid, "payment failed");
        emit Sold(tokenId, seller, msg.sender, price);
    }
}
