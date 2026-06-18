#!/usr/bin/env node
// Derive the configured student account pool, fund any with low balance from
// accounts[0], and write the
// pool to /app/frontend/dist/api/student-pool.json so lane-service
// can fetch it over HTTP on first claim.
//
// By default the pool mnemonic is generated fresh on each instructor chain boot
// so station wallets do not carry on-chain history across classroom resets. Set
// POOL_MNEMONIC only when reproducible addresses are explicitly needed.
//
// The hardhat node funds accounts 0-19 by default. We re-fund any
// pool address whose balance is below TARGET_FUND_ETH so that
// reused classroom restarts or higher-capacity classrooms are always topped up.

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { ethers } = require("hardhat");
const { HDNodeWallet, Mnemonic } = require("ethers");

const POOL_SIZE = parseInt(
  process.env.POOL_SIZE ||
    process.env.ETHEREUM_STUDENT_CAPACITY ||
    process.env.MAX_STUDENT_CAPACITY ||
    "20",
  10
);
// Derive student accounts from a HIGH base index so they never collide with the
// reserved accounts: #0 = instructor/deployer/conductor, #9 = bank/faucet, and
// #10..#41 = initial beacon bots. Without this, a capacity of >9 would hand
// students the bank/bot/instructor accounts (the wallet auto-imports the assigned
// key — App.jsx). Students get funded regardless of index, so the base is free.
const POOL_BASE = parseInt(process.env.STUDENT_POOL_BASE || "100", 10);
// Funder is hardhat accounts[0] (10k ETH at boot, but the existing deploy
// step burns a sizable chunk on contracts + reward pool funding). Keep
// the per-station target modest so the configured lanes fit comfortably in what's
// left over.
const TARGET_FUND_ETH = process.env.TARGET_FUND_ETH || "10";
const MIN_BALANCE_ETH = process.env.MIN_BALANCE_ETH || "1";
const CONFIGURED_MNEMONIC = (process.env.POOL_MNEMONIC || "").trim();
const MNEMONIC =
  CONFIGURED_MNEMONIC || Mnemonic.fromEntropy(crypto.randomBytes(16)).phrase;
const MNEMONIC_SOURCE = CONFIGURED_MNEMONIC ? "env" : "generated";
const POOL_ID = process.env.POOL_ID || crypto.randomUUID();
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
    const w = HDNodeWallet.fromMnemonic(m, `m/44'/60'/0'/0/${POOL_BASE + i}`);
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
        mnemonicSource: MNEMONIC_SOURCE,
        poolId: POOL_ID,
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
