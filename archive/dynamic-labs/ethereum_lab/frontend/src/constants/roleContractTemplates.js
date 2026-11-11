/**
 * Role-specific contract boilerplates and deploy scripts.
 * Students use these to build and deploy their role contract, then register in the web UI.
 */

export const ROLE_CONTRACT_TEMPLATES = {
  'Escrow Agent': {
    name: 'EscrowAgentRole',
    filePath: 'contracts/student/roles/EscrowAgentRole.sol',
    deployCmd: 'ROLE=EscrowAgent npx hardhat run scripts/deploy-role.js --network localhost',
    description: 'Hold funds until conditions are met. Release to designated address.',
    template: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract EscrowAgentRole {
    address public agent;
    
    constructor() { agent = msg.sender; }
    
    receive() external payable {}
    
    function releaseTo(address payable to, uint256 amount) external {
        require(msg.sender == agent);
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "Transfer failed");
    }
}`,
    deployHint: 'ROLE=EscrowAgent npx hardhat run scripts/deploy-role.js --network localhost',
    buildSteps: ['Deploy EscrowAgentRole', 'Register in web UI']
  },
  'Victim': {
    name: 'VictimRole',
    filePath: 'contracts/student/roles/VictimRole.sol',
    deployCmd: 'ROLE=Victim npx hardhat run scripts/deploy-role.js --network localhost',
    description: 'Pay ransom through RansomPayment contract. Your payment creates an on-chain trail.',
    template: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IRansomPayment {
    function payRansom() external payable;
}

contract VictimRole {
    address public victim;
    
    constructor() { victim = msg.sender; }
    
    receive() external payable {}
    
    function payRansomOnBehalf(address ransomContract) external payable {
        require(msg.sender == victim);
        IRansomPayment(ransomContract).payRansom{value: msg.value}();
    }
}`,
    deployHint: 'ROLE=Victim npx hardhat run scripts/deploy-role.js --network localhost',
    buildSteps: ['Deploy VictimRole', 'Get RansomPayment address from instructor', 'Call payRansomOnBehalf(ransomAddr) with ETH']
  },
  'Attacker': {
    name: 'AttackerRole',
    filePath: 'contracts/student/roles/AttackerRole.sol',
    deployCmd: 'ROLE=Attacker npx hardhat run scripts/deploy-role.js --network localhost',
    description: 'Receive ransom payments. Instructor sets your address in RansomPayment.',
    template: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract AttackerRole {
    address public attacker;
    
    constructor() { attacker = msg.sender; }
    
    receive() external payable {}
    
    function withdraw() external {
        require(msg.sender == attacker);
        (bool ok, ) = payable(attacker).call{value: address(this).balance}("");
        require(ok, "Transfer failed");
    }
}`,
    deployHint: 'ROLE=Attacker npx hardhat run scripts/deploy-role.js --network localhost',
    buildSteps: ['Deploy AttackerRole', 'Share address with instructor', 'Instructor sets you in RansomPayment.setAttacker()', 'Receive payments from victims']
  },
  'Investigator': {
    name: 'InvestigatorRole',
    filePath: 'contracts/student/roles/InvestigatorRole.sol',
    deployCmd: 'ROLE=Investigator npx hardhat run scripts/deploy-role.js --network localhost',
    description: 'Trace the ransom flow. Submit findings to scenario contract for bounty.',
    template: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract InvestigatorRole {
    address public investigator;
    address public submittedAddress;
    
    constructor() { investigator = msg.sender; }
    
    function submitFinding(address _found) external {
        require(msg.sender == investigator);
        submittedAddress = _found;
    }
}`,
    deployHint: 'ROLE=Investigator npx hardhat run scripts/deploy-role.js --network localhost',
    buildSteps: ['Deploy InvestigatorRole', 'Use block explorer + Playground to trace', 'Submit correct address for bounty', 'Register this contract when done']
  },
  'Admin': { name: 'Admin', filePath: 'contracts/student/', deployCmd: 'Contract Builder → House Sale', template: '// Deploy via Contract Builder', deployHint: 'Contract Builder (CLI option 9)', buildSteps: ['Use Contract Builder'] },
  'Seller': { name: 'Seller', filePath: 'contracts/student/', deployCmd: 'Contract Builder → House Sale', template: '// Deploy via Contract Builder', deployHint: 'Contract Builder', buildSteps: ['Contract Builder → House Sale'] },
  'Buyer': { name: 'Buyer', filePath: 'contracts/student/', deployCmd: 'Contract Builder', template: '// Deploy via Contract Builder', deployHint: 'Contract Builder', buildSteps: ['Contract Builder'] },
  'Organizer': { name: 'Organizer', filePath: 'contracts/student/', deployCmd: 'Contract Builder → Event Tickets', template: '// Contract Builder → Event Tickets', deployHint: 'Contract Builder', buildSteps: ['Contract Builder → Event Tickets'] },
  'Creator': { name: 'Creator', filePath: 'contracts/student/', deployCmd: 'Contract Builder → Crowdfunding', template: '// Contract Builder → Crowdfunding', deployHint: 'Contract Builder', buildSteps: ['Contract Builder → Crowdfunding'] },
  'Contributor': { name: 'Contributor', filePath: 'contracts/student/', deployCmd: 'Interact with Creator contract', template: '// Interact with Creator\'s contract', deployHint: 'Register address you use', buildSteps: ['Contribute via Creator\'s contract'] },
  'Voter': { name: 'Voter', filePath: 'contracts/student/', deployCmd: 'Interact with voting contract', template: '// Interact with voting contract', deployHint: 'Register any contract', buildSteps: ['Vote via voting contract'] }
};
