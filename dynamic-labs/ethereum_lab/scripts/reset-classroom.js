#!/usr/bin/env node
/**
 * Full Classroom Reset
 *
 * Clears blockchain data so you can deploy a fresh node for a new class.
 *
 * LOCAL: Run this, then close the blockchain node window and run start-lab again.
 * DOCKER: Use "npm run reset:docker" instead (stops containers and removes volumes).
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");

const targets = [
  { path: path.join(ROOT, ".hardhat"), name: "Blockchain data (.hardhat)" },
  { path: path.join(ROOT, "cache", "solidity-files-cache.json"), name: "Solidity cache" },
];

console.log("\n🔄 Full Classroom Reset\n");
console.log("⚠️  STOP the blockchain node first (close the Hardhat window), then run this.\n");

let cleared = 0;
for (const t of targets) {
  try {
    if (fs.existsSync(t.path)) {
      const stat = fs.statSync(t.path);
      if (stat.isDirectory()) {
        fs.rmSync(t.path, { recursive: true });
        console.log(`   ✓ Cleared: ${t.name}`);
      } else {
        fs.unlinkSync(t.path);
        console.log(`   ✓ Cleared: ${t.name}`);
      }
      cleared++;
    } else {
      console.log(`   - Skipped (not found): ${t.name}`);
    }
  } catch (e) {
    console.error(`   ✗ Failed ${t.name}:`, e.message);
  }
}

console.log("");
if (cleared > 0) {
  console.log("✅ Reset complete. Next steps:");
  console.log("   1. Close the blockchain node window (if still open)");
  console.log("   2. Run: .\\start-lab.ps1 -Mode instructor");
  console.log("   Or:   npm run chain  (in one terminal)");
  console.log("         npm run deploy (after node is ready)");
  console.log("");
} else {
  console.log("Nothing to clear (data may already be fresh or node is still running).");
  console.log("");
}
