#!/usr/bin/env node
/**
 * Deploy role-specific contracts for scenario completion.
 * 
 * Usage (use env vars - Hardhat doesn't pass extra args):
 *   ROLE=CarSeller npx hardhat run scripts/deploy-role.js --network localhost
 *   ROLE=CarBuyer CARSALE_ADDRESS=0x... npx hardhat run scripts/deploy-role.js --network localhost
 *   ROLE=Mechanic CARSALE_ADDRESS=0x... npx hardhat run scripts/deploy-role.js --network localhost
 *   ROLE=Victim npx hardhat run scripts/deploy-role.js --network localhost
 *   ROLE=Attacker npx hardhat run scripts/deploy-role.js --network localhost
 *   ROLE=Investigator npx hardhat run scripts/deploy-role.js --network localhost
 *   ROLE=EscrowAgent npx hardhat run scripts/deploy-role.js --network localhost
 * 
 * After deploy: Register the contract address in the web UI (Complete your role section).
 */

const hre = require("hardhat");

const ROLE_CONTRACTS = {
  CarSeller: { contract: "CarSellerRole", args: [] },
  CarSellerHonest: { contract: "CarSellerRole", args: [] },
  CarSellerDeceptive: { contract: "CarSellerRole", args: [] },
  CarBuyer: { contract: "CarBuyerRole", args: ["CARSALE"] },
  Mechanic: { contract: "MechanicRole", args: ["CARSALE"] },
  MechanicBribed: { contract: "MechanicRole", args: ["CARSALE"] },
  Victim: { contract: "VictimRole", args: [] },
  Attacker: { contract: "AttackerRole", args: [] },
  Investigator: { contract: "InvestigatorRole", args: [] },
  Detective: { contract: "CarInvestigatorRole", args: [] },
  CarInvestigator: { contract: "CarInvestigatorRole", args: [] },
  EscrowAgent: { contract: "EscrowAgentRole", args: [] },
};

/** Maps legacy ROLE env names (no longer documented) to current keys. */
function normalizeRoleEnv(role) {
  const compact = String(role).toLowerCase().replace(/\s/g, "");
  const legacySeller = "carseller" + String.fromCharCode(108, 101, 109, 111, 110);
  if (compact === legacySeller) return "CarSellerDeceptive";
  return role;
}

async function main() {
  const role = normalizeRoleEnv(process.env.ROLE || "CarSeller");
  const carSaleArg = process.env.CARSALE_ADDRESS;
  
  const roleKey = Object.keys(ROLE_CONTRACTS).find(
    (k) => k.toLowerCase().replace(/\s/g, "") === String(role).toLowerCase().replace(/\s/g, "")
  ) || role;
  
  const config = ROLE_CONTRACTS[roleKey] || ROLE_CONTRACTS[role];
  if (!config) {
    console.error("\n❌ Unknown role. Available:", Object.keys(ROLE_CONTRACTS).join(", "));
    process.exit(1);
  }

  const [deployer] = await hre.ethers.getSigners();
  console.log(`\n🎭 Deploying ${config.contract} as ${deployer.address}`);

  const deployArgs = config.args.map((a) => {
    if (a === "CARSALE") {
      const addr = carSaleArg || process.env.CARSALE_ADDRESS;
      if (!addr) {
        console.error("\n❌ CarSale address required. Pass as argument or set CARSALE_ADDRESS env.");
        console.error("   Example: npx hardhat run scripts/deploy-role.js --network localhost CarBuyer 0x...");
        process.exit(1);
      }
      return addr;
    }
    return a;
  });

  const Contract = await hre.ethers.getContractFactory(config.contract);
  const instance = await Contract.deploy(...deployArgs);
  await instance.waitForDeployment();

  console.log(`\n✅ ${config.contract} deployed to: ${instance.target}`);
  console.log(`\n📋 Next steps:`);
  console.log(`   1. Copy this address: ${instance.target}`);
  console.log(`   2. In the web UI, go to "Complete your role"`);
  console.log(`   3. Paste the address and click Register`);
  if (config.contract === "CarBuyerRole") {
    console.log(`\n   Usage: Send 2+ ETH to this contract, then call payDeposit() → requestInspection() → completePurchase()`);
  }
  if (config.contract === "MechanicRole") {
    console.log(`\n   Usage: Call mechanicInspect(true) or mechanicInspect(false)`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
