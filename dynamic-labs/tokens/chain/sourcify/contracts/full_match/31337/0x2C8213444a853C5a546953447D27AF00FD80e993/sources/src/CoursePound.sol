// SPDX-License-Identifier: MIT
// A pound token built like Course Dollar (CourseTokens.sol): 6 decimals, an issuer who mints, and a
// blacklist only the issuer can change. It runs behind a DollarProxy, which keeps the balances and
// borrows this contract's code. Training code: it leaves out checks a real token needs.
pragma solidity 0.8.24;

contract CoursePound {
    string public constant name = "Course Pound";
    string public constant symbol = "cGBP";
    uint8 public constant decimals = 6; // 1 cGBP is stored as 1000000

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

    // Runs once, through the proxy, when the proxy is created. Whoever creates the proxy picks
    // all three values: the issuer, and who receives the first money, if any.
    function initialize(address issuer, address firstHolder, uint256 firstSupply) external {
        require(owner == address(0), "already set up");
        owner = issuer;
        if (firstSupply > 0) {
            totalSupply = firstSupply;
            balanceOf[firstHolder] = firstSupply;
            emit Transfer(address(0), firstHolder, firstSupply);
        }
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
