// SPDX-License-Identifier: MIT
// The exchange on the day-4 course chain: a dollar token, wrapped ether, one pool that trades
// them and a router people call to trade. The pool and router follow Uniswap v2's design and use
// its function names, so their selectors match the real ones. Kept short so a student can read
// them on the explorer's Contract tab. Training code: it leaves out checks a real exchange needs.
pragma solidity 0.8.24;

interface IToken {
    function balanceOf(address who) external view returns (uint256);
    function transfer(address to, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

// A dollar token: 6 decimals, an issuer who mints, and a blacklist only the issuer can change.
contract CourseDollar {
    string public constant name = "Course Dollar";
    string public constant symbol = "cUSD";
    uint8 public constant decimals = 6; // 1 cUSD is stored as 1000000

    address public immutable owner; // the issuer
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => bool) public isBlackListed;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event AddedBlackList(address indexed user);

    constructor() {
        owner = msg.sender;
    }

    // New money: a Transfer from address zero.
    function mint(address to, uint256 value) external {
        require(msg.sender == owner, "only the issuer");
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value);
    }

    // A frozen address cannot send. Not used on the course chain.
    function addBlackList(address user) external {
        require(msg.sender == owner, "only the issuer");
        isBlackListed[user] = true;
        emit AddedBlackList(user);
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(!isBlackListed[msg.sender], "sender is blacklisted");
        _move(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(!isBlackListed[from], "sender is blacklisted");
        require(allowance[from][msg.sender] >= value, "allowance too low");
        allowance[from][msg.sender] -= value;
        _move(from, to, value);
        return true;
    }

    function _move(address from, address to, uint256 value) internal {
        require(balanceOf[from] >= value, "balance too low");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
    }
}

// Wrapped ether: send ETH in, get the same amount of WETH, a token a contract can move like any
// other. The contract holds the ETH, so its supply is its ETH balance. A deposit writes a Deposit
// log, not a Transfer log.
contract WETH {
    string public constant name = "Wrapped Ether";
    string public constant symbol = "WETH";
    uint8 public constant decimals = 18;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Deposit(address indexed to, uint256 value);
    event Withdrawal(address indexed from, uint256 value);

    function totalSupply() external view returns (uint256) {
        return address(this).balance;
    }

    function deposit() public payable {
        balanceOf[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    function withdraw(uint256 value) external {
        require(balanceOf[msg.sender] >= value, "balance too low");
        balanceOf[msg.sender] -= value;
        emit Withdrawal(msg.sender, value);
        payable(msg.sender).transfer(value);
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transfer(address to, uint256 value) external returns (bool) {
        _move(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(allowance[from][msg.sender] >= value, "allowance too low");
        allowance[from][msg.sender] -= value;
        _move(from, to, value);
        return true;
    }

    function _move(address from, address to, uint256 value) internal {
        require(balanceOf[from] >= value, "balance too low");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
    }
}

// The pool: it holds two tokens and trades one for the other at a price set by how much of each
// it holds. A trade must leave reserve0 x reserve1 no smaller than before, after a 0.3% fee on
// what came in. Whoever adds tokens gets pool shares (CLP), a claim on the pool and its fees.
contract CoursePair {
    string public constant name = "Course LP";
    string public constant symbol = "CLP";
    uint8 public constant decimals = 18;

    address public immutable token0; // the token with the lower address
    address public immutable token1;
    uint112 private reserve0;
    uint112 private reserve1;
    uint32 private blockTimestampLast;

    uint256 public totalSupply; // pool shares
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Mint(address indexed sender, uint256 amount0, uint256 amount1);
    event Swap(
        address indexed sender, uint256 amount0In, uint256 amount1In,
        uint256 amount0Out, uint256 amount1Out, address indexed to
    );
    event Sync(uint112 reserve0, uint112 reserve1);

    constructor(address tokenA, address tokenB) {
        (token0, token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
    }

    function getReserves() public view returns (uint112, uint112, uint32) {
        return (reserve0, reserve1, blockTimestampLast);
    }

    // Shares for tokens already sent to the pool. The first deposit sets the price.
    function mint(address to) external returns (uint256 shares) {
        uint256 balance0 = IToken(token0).balanceOf(address(this));
        uint256 balance1 = IToken(token1).balanceOf(address(this));
        uint256 amount0 = balance0 - reserve0;
        uint256 amount1 = balance1 - reserve1;
        if (totalSupply == 0) {
            shares = _sqrt(amount0 * amount1);
        } else {
            uint256 s0 = amount0 * totalSupply / reserve0;
            uint256 s1 = amount1 * totalSupply / reserve1;
            shares = s0 < s1 ? s0 : s1;
        }
        require(shares > 0, "no shares");
        totalSupply += shares;
        balanceOf[to] += shares;
        emit Transfer(address(0), to, shares);
        _update(balance0, balance1);
        emit Mint(msg.sender, amount0, amount1);
    }

    // Pays out first, then checks that what came in covers it (the input was sent beforehand).
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata) external {
        require(amount0Out > 0 || amount1Out > 0, "nothing out");
        require(amount0Out < reserve0 && amount1Out < reserve1, "not enough in the pool");
        if (amount0Out > 0) IToken(token0).transfer(to, amount0Out);
        if (amount1Out > 0) IToken(token1).transfer(to, amount1Out);
        uint256 balance0 = IToken(token0).balanceOf(address(this));
        uint256 balance1 = IToken(token1).balanceOf(address(this));
        uint256 amount0In = balance0 > reserve0 - amount0Out ? balance0 - (reserve0 - amount0Out) : 0;
        uint256 amount1In = balance1 > reserve1 - amount1Out ? balance1 - (reserve1 - amount1Out) : 0;
        require(amount0In > 0 || amount1In > 0, "nothing in");
        // The fee: only 99.7% of what came in counts toward keeping the product.
        uint256 adjusted0 = balance0 * 1000 - amount0In * 3;
        uint256 adjusted1 = balance1 * 1000 - amount1In * 3;
        require(adjusted0 * adjusted1 >= uint256(reserve0) * reserve1 * 1000 ** 2, "K");
        _update(balance0, balance1);
        emit Swap(msg.sender, amount0In, amount1In, amount0Out, amount1Out, to);
    }

    function _update(uint256 balance0, uint256 balance1) private {
        reserve0 = uint112(balance0);
        reserve1 = uint112(balance1);
        blockTimestampLast = uint32(block.timestamp);
        emit Sync(reserve0, reserve1);
    }

    function _sqrt(uint256 y) private pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }
}

// What people call to trade. It works out the price from the pool's reserves, moves the input
// into the pool and asks the pool to pay out. It never holds tokens after a call ends.
contract CourseRouter {
    CoursePair public immutable pair;
    WETH public immutable weth;

    constructor(CoursePair pair_, WETH weth_) {
        pair = pair_;
        weth = weth_;
    }

    modifier ensure(uint256 deadline) {
        require(deadline >= block.timestamp, "expired");
        _;
    }

    // Tokens in, pool shares out. Training code: it takes the amounts as given and does not
    // check them against the pool's price.
    function addLiquidity(
        address tokenA, address tokenB, uint256 amountADesired, uint256 amountBDesired,
        uint256, uint256, address to, uint256 deadline
    ) external ensure(deadline) returns (uint256, uint256, uint256 shares) {
        _check(tokenA, tokenB);
        IToken(tokenA).transferFrom(msg.sender, address(pair), amountADesired);
        IToken(tokenB).transferFrom(msg.sender, address(pair), amountBDesired);
        shares = pair.mint(to);
        return (amountADesired, amountBDesired, shares);
    }

    // Uniswap v2's price formula: what the pool pays for amountIn, after the 0.3% fee.
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut) public pure returns (uint256) {
        uint256 inWithFee = amountIn * 997;
        return inWithFee * reserveOut / (reserveIn * 1000 + inWithFee);
    }

    function getAmountsOut(uint256 amountIn, address[] calldata path) public view returns (uint256[] memory amounts) {
        _check(path[0], path[1]);
        (uint112 r0, uint112 r1, ) = pair.getReserves();
        (uint256 rIn, uint256 rOut) = path[0] == pair.token0() ? (r0, r1) : (r1, r0);
        amounts = new uint256[](2);
        amounts[0] = amountIn;
        amounts[1] = getAmountOut(amountIn, rIn, rOut);
    }

    // Sell an exact amount of one token. amountOutMin protects the trader if the price moves.
    function swapExactTokensForTokens(
        uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline
    ) external ensure(deadline) returns (uint256[] memory amounts) {
        amounts = getAmountsOut(amountIn, path);
        require(amounts[1] >= amountOutMin, "too little received");
        IToken(path[0]).transferFrom(msg.sender, address(pair), amountIn);
        _swap(path[0], amounts[1], to);
    }

    // Sell ETH: the router wraps it into WETH, sends the WETH to the pool, then swaps.
    function swapExactETHForTokens(
        uint256 amountOutMin, address[] calldata path, address to, uint256 deadline
    ) external payable ensure(deadline) returns (uint256[] memory amounts) {
        require(path[0] == address(weth), "path must start with WETH");
        amounts = getAmountsOut(msg.value, path);
        require(amounts[1] >= amountOutMin, "too little received");
        weth.deposit{value: msg.value}();
        weth.transfer(address(pair), msg.value);
        _swap(path[0], amounts[1], to);
    }

    function _swap(address tokenIn, uint256 amountOut, address to) private {
        (uint256 out0, uint256 out1) = tokenIn == pair.token0() ? (uint256(0), amountOut) : (amountOut, uint256(0));
        pair.swap(out0, out1, to, "");
    }

    function _check(address a, address b) private view {
        require(
            (a == pair.token0() && b == pair.token1()) || (a == pair.token1() && b == pair.token0()),
            "this router trades one pair"
        );
    }
}
