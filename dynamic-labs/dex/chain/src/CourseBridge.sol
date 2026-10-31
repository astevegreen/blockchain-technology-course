// SPDX-License-Identifier: MIT
// The bridge between the day-4 course chain (L1) and its second chain (L2). It locks cUSD in a
// contract on L1 and creates the same amount of a bridged token on L2: lock and mint. In a real
// rollup the protocol carries the deposit message across; here one account, the relayer, reads
// the L1 log and sends the L2 transaction. Training code: no withdrawals back to L1.
pragma solidity 0.8.24;

interface IToken {
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

// On L1: holds every deposited cUSD. Each deposit gets a number and a log the relayer reads.
contract CourseBridgeL1 {
    address public immutable token; // the one token this bridge takes (cUSD)
    address public immutable owner;
    bool public paused;
    uint256 public nextDepositId;

    event DepositInitiated(
        uint256 indexed depositId, address indexed l1Token, address indexed from, address to, uint256 amount
    );
    event Paused(bool paused);

    constructor(address token_) {
        token = token_;
        owner = msg.sender;
    }

    // Lock amount of the sender's cUSD here; `to` receives the same amount on L2.
    function depositERC20To(address l1Token, address to, uint256 amount) external returns (uint256 depositId) {
        require(!paused, "bridge paused");
        require(l1Token == token, "token not supported");
        require(amount > 0, "nothing to send");
        IToken(token).transferFrom(msg.sender, address(this), amount);
        depositId = nextDepositId++;
        emit DepositInitiated(depositId, l1Token, msg.sender, to, amount);
    }

    // The owner can stop new deposits. Not used on the course chain.
    function setPaused(bool paused_) external {
        require(msg.sender == owner, "only the owner");
        paused = paused_;
        emit Paused(paused_);
    }
}

// On L2: the bridged dollar. Only the L2 bridge, which creates it, can mint it.
contract BridgedDollar {
    string public constant name = "Bridged Course Dollar";
    string public constant symbol = "bcUSD";
    uint8 public constant decimals = 6;

    address public immutable bridge;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor() {
        bridge = msg.sender;
    }

    function mint(address to, uint256 value) external {
        require(msg.sender == bridge, "only the bridge");
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "balance too low");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}

// On L2: mints bcUSD for each L1 deposit the relayer reports, once per deposit number.
contract CourseBridgeL2 {
    BridgedDollar public immutable token;
    address public immutable owner;
    address public immutable relayer;
    bool public paused;
    mapping(uint256 => bool) public processed;

    event DepositFinalized(uint256 indexed depositId, address indexed from, address indexed to, uint256 amount);
    event Paused(bool paused);

    constructor(address relayer_) {
        owner = msg.sender;
        relayer = relayer_;
        token = new BridgedDollar();
    }

    // The relayer copies an L1 DepositInitiated log here. The contract cannot see L1: it trusts
    // the relayer's word for the numbers.
    function finalizeDeposit(uint256 depositId, address from, address to, uint256 amount) external {
        require(msg.sender == relayer, "only the relayer");
        require(!paused, "bridge paused");
        require(!processed[depositId], "already done");
        processed[depositId] = true;
        token.mint(to, amount);
        emit DepositFinalized(depositId, from, to, amount);
    }

    // The owner can stop new mints. Not used on the course chain.
    function setPaused(bool paused_) external {
        require(msg.sender == owner, "only the owner");
        paused = paused_;
        emit Paused(paused_);
    }
}
