#!/usr/bin/env node
/**
 * Copy SimpleFT and SimpleNFT artifacts to frontend for browser deploy.
 * Run after: npx hardhat compile
 */
const fs = require('fs');
const path = require('path');

const destDir = path.join(__dirname, '..', 'frontend', 'src', 'contracts');
if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true });
}

const tokens = [
  { name: 'SimpleFT', artifact: 'SimpleFT.sol/SimpleFT.json' },
  { name: 'SimpleNFT', artifact: 'SimpleNFT.sol/SimpleNFT.json' },
  { name: 'LabNFT', artifact: 'LabNFT.sol/LabNFT.json' },
  { name: 'LabNFTSale', artifact: 'LabNFTSale.sol/LabNFTSale.json' },
  { name: 'SimpleStorage', artifact: 'SimpleStorage.sol/SimpleStorage.json' },
  { name: 'CarSale', artifact: 'student/CarSale_000001.sol/CarSale.json' },
  { name: 'ClassVote', artifact: 'ClassVote.sol/ClassVote.json' }
];

for (const { name, artifact } of tokens) {
  const artifactPath = path.join(__dirname, '..', 'artifacts', 'contracts', artifact);
  const destPath = path.join(destDir, `${name}.json`);
  if (!fs.existsSync(artifactPath)) {
    console.warn(`${name} artifact not found. Run: npx hardhat compile`);
    continue;
  }
  fs.copyFileSync(artifactPath, destPath);
  console.log(`Copied ${name}.json to frontend/src/contracts/`);
}
