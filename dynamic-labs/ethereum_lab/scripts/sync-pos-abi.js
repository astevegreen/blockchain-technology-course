#!/usr/bin/env node
/**
 * Copy only PoSSimulator ABI (array) to frontend/src/PoS.json.
 * ethers v6 Contract requires an ABI array — not the full Hardhat artifact object.
 */
const fs = require("fs");
const path = require("path");

const artifactPath = path.join(
  __dirname,
  "..",
  "artifacts",
  "contracts",
  "PoS.sol",
  "PoSSimulator.json"
);
const destPath = path.join(__dirname, "..", "frontend", "src", "PoS.json");

if (!fs.existsSync(artifactPath)) {
  console.warn("sync-pos-abi: PoSSimulator artifact missing; run: npx hardhat compile");
  process.exit(0);
}

const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
if (!artifact.abi) {
  console.error("sync-pos-abi: artifact has no abi");
  process.exit(1);
}

fs.writeFileSync(destPath, JSON.stringify(artifact.abi));
console.log("sync-pos-abi: wrote frontend/src/PoS.json (" + artifact.abi.length + " entries)");
