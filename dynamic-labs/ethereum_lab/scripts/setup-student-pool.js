#!/usr/bin/env node
// Derive the configured deterministic student account pool from the canonical hardhat
// mnemonic, fund any with low balance from accounts[0], and write the
// pool to /app/frontend/dist/api/student-pool.json so lane-service
// can fetch it over HTTP on first claim.
//
// The hardhat node funds accounts 0-19 by default. We re-fund any
// pool address whose balance is below TARGET_FUND_ETH so that
// reused classroom restarts or higher-capacity classrooms are always topped up.

const fs = require("fs");
const path = require("path");
const { ethers } = require("hardhat");
const { HDNodeWallet, Mnemonic } = require("ethers");

const POOL_SIZE = parseInt(
  process.env.POOL_SIZE ||
    process.env.ETHEREUM_STUDENT_CAPACITY ||
    process.env.MAX_STUDENT_CAPACITY ||
    "20",
  10
);
// Funder is hardhat accounts[0] (10k ETH at boot, but the existing deploy
// step burns a sizable chunk on contracts + reward pool funding). Keep
// the per-station target modest so the configured lanes fit comfortably in what's
// left over.
const TARGET_FUND_ETH = process.env.TARGET_FUND_ETH || "10";
const MIN_BALANCE_ETH = process.env.MIN_BALANCE_ETH || "1";
const MNEMONIC =
  process.env.POOL_MNEMONIC ||
  "test test test test test test test test test test test junk";
const OUT_PATH =
  process.env.STUDENT_POOL_PATH ||
  "/app/frontend/dist/api/student-pool.json";

async function main() {
  const m = Mnemonic.fromPhrase(MNEMONIC);
  const provider = ethers.provider;
  const [funder] = await ethers.getSigners();

  const min = ethers.parseEther(MIN_BALANCE_ETH);
  const target = ethers.parseEther(TARGET_FUND_ETH);

  const pool = [];
  for (let i = 0; i < POOL_SIZE; i++) {
    const w = HDNodeWallet.fromMnemonic(m, `m/44'/60'/0'/0/${i}`);
    const station = `s${String(i + 1).padStart(2, "0")}`;
    const balance = await provider.getBalance(w.address);
    let funded = false;
    if (balance < min) {
      const topUp = target - balance;
      const tx = await funder.sendTransaction({
        to: w.address,
        value: topUp,
      });
      await tx.wait();
      funded = true;
    }
    pool.push({
      station,
      index: i,
      address: w.address,
      privateKey: w.privateKey,
      fundedThisRun: funded,
    });
    console.log(
      `  ${station}  ${w.address}  ${funded ? "funded" : "ok"}`
    );
  }

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(
    OUT_PATH,
    JSON.stringify(
      {
        mnemonic: MNEMONIC,
        targetEth: TARGET_FUND_ETH,
        generatedAt: new Date().toISOString(),
        pool,
      },
      null,
      2
    )
  );
  console.log(`\n  wrote ${pool.length} accounts → ${OUT_PATH}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
