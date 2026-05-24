const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log(`\n🎓 Deploying PoS Simulator with instructor: ${deployer.address}`);
  
  const pos = await hre.ethers.deployContract("PoSSimulator");
  await pos.waitForDeployment();
  
  // Fund the reward pool with 200 ETH from the deployer
  // This provides enough for rewards, slashing burns, and extended demos
  const fundingAmount = hre.ethers.parseEther("200.0");
  await deployer.sendTransaction({
    to: pos.target,
    value: fundingAmount
  });

  console.log(`\n✅ PoS Simulator deployed to: ${pos.target}`);
  console.log(`💰 Reward pool funded with: 200 ETH`);
  console.log(`\n📋 Contract Features:`);
  console.log(`   - Minimum stake: 1 ETH`);
  console.log(`   - Unbonding period: 60 seconds`);
  console.log(`   - Min stake duration: 30 seconds`);
  console.log(`   - Epoch duration: 30 seconds`);
  console.log(`   - Slash penalty: 5%`);
  console.log(`   - Attestation penalty: 0.1%`);
  console.log(`   - Block reward: 0.01 ETH`);
  console.log(`\n🎛️ Instructor Commands (from instructor dashboard):`);
  console.log(`   - Slash validators for misbehavior`);
  console.log(`   - Simulate block proposals`);
  console.log(`   - Check missed attestations`);
  console.log(`\n📣 Share this contract address with students: ${pos.target}`);
  
  // Verify the contract is callable (catches wrong contract at address)
  const epoch = await pos.currentEpoch();
  if (epoch === undefined || epoch === null) {
    throw new Error('PoS verification failed: currentEpoch() returned invalid value');
  }
  console.log(`\n🔍 Verified: currentEpoch() = ${epoch}`);

  // Write contract address to file for easy access
  const fs = require('fs');
  const path = require('path');
  fs.writeFileSync('CONTRACT_ADDRESS.txt', pos.target + '\n');
  
  // Also write to frontend public dir so the app can auto-detect it
  const publicConfig = path.join(__dirname, '..', 'frontend', 'public', 'contract-config.json');
  fs.writeFileSync(publicConfig, JSON.stringify({ contractAddress: pos.target, deployedAt: new Date().toISOString() }));
  console.log(`\n📝 Contract address saved to CONTRACT_ADDRESS.txt and frontend/public/contract-config.json`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
