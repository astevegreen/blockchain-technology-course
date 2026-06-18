const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const signers = await hre.ethers.getSigners();
  const deployer = signers[0];

  // Defaults are tuned for a working classroom sim: committeesPerEpoch MUST be 1 so
  // the whole pool attests each slot and blocks can reach the 2/3 justification
  // quorum (justification is per-block vs total stake). Short epochs keep finality
  // observable in ~20-30s. Override via env only if you know what you're doing.
  const committeesPerEpoch = parseInt(process.env.COMMITTEES_PER_EPOCH || "1", 10);
  const validatorsPerCommittee = parseInt(process.env.VALIDATORS_PER_COMMITTEE || "32", 10);
  const blocksPerEpoch = parseInt(process.env.BLOCKS_PER_EPOCH || "4", 10);
  const poolSize = committeesPerEpoch * validatorsPerCommittee;

  console.log(`\nDeploying Beacon Chain Lab with instructor: ${deployer.address}`);
  console.log(`   Committees per epoch: ${committeesPerEpoch}, Validators per committee: ${validatorsPerCommittee}`);
  console.log(`   Blocks per epoch: ${blocksPerEpoch}, Pool size: ${poolSize}`);

  const BeaconChainLab = await hre.ethers.getContractFactory("BeaconChainLab");
  const lab = await BeaconChainLab.deploy(committeesPerEpoch, validatorsPerCommittee, blocksPerEpoch);
  await lab.waitForDeployment();

  const fundingAmount = hre.ethers.parseEther("100.0");
  await deployer.sendTransaction({
    to: lab.target,
    value: fundingAmount,
  });

  console.log(`\nBeacon Chain Lab deployed to: ${lab.target}`);
  console.log(`Reward pool funded with: 100 ETH`);

  // Bot addresses: use Hardhat accounts 10+ and derive more if needed
  const MNEMONIC = "test test test test test test test test test test test junk";
  let botAddresses = signers.slice(10, 20).map((s) => s.address).filter(Boolean);

  if (botAddresses.length < poolSize) {
    const { HDNodeWallet } = await import("ethers");
    for (let i = 20; botAddresses.length < poolSize; i++) {
      const w = HDNodeWallet.fromPhrase(MNEMONIC, undefined, `m/44'/60'/0'/0/${i}`);
      botAddresses.push(w.address);
    }
  }
  botAddresses = botAddresses.slice(0, poolSize);

  const config = {
    contractAddress: lab.target,
    committeesPerEpoch,
    validatorsPerCommittee,
    blocksPerEpoch,
    poolSize,
    instructor: deployer.address,
    botAddresses,
    deployedAt: new Date().toISOString(),
  };

  const configPath = path.join(__dirname, "..", "frontend", "public", "beacon-lab-config.json");
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log(`\nConfig written to frontend/public/beacon-lab-config.json`);

  // Copy ABI to frontend
  const artifactPath = path.join(
    __dirname,
    "..",
    "artifacts",
    "contracts",
    "BeaconChainLab.sol",
    "BeaconChainLab.json"
  );
  const destDir = path.join(__dirname, "..", "frontend", "src", "contracts");
  const destPath = path.join(destDir, "BeaconChainLab.json");

  if (fs.existsSync(artifactPath)) {
    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }
    fs.writeFileSync(destPath, JSON.stringify(artifact.abi));
    console.log(`ABI copied to frontend/src/contracts/BeaconChainLab.json`);
  } else {
    console.log(`Artifact not found at ${artifactPath} - run 'npx hardhat compile' first`);
  }

  console.log(`\nShare this contract address with students: ${lab.target}`);
  console.log(`   Lab: /?view=beacon-lab`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
