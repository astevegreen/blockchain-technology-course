#!/usr/bin/env node
const eMod = require('ethers');
const ethers = eMod.ethers || eMod;

const DEFAULT_FAUCET_PRIVATE_KEY = '0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6';
const DEFAULT_FAUCET_BALANCE_ETH = '1000000000000'; // 1 trillion ETH on the classroom test chain.

const privateKey = process.env.FAUCET_PRIVATE_KEY || DEFAULT_FAUCET_PRIVATE_KEY;
const rpcUrl = (
  process.env.FAUCET_RPC_URL
  || process.env.INSTRUCTOR_RPC_URL
  || process.env.RPC_URL
  || `http://127.0.0.1:${process.env.RPC_PORT || '8545'}`
).trim();
const balanceEth = String(process.env.CLASS_FAUCET_BALANCE_ETH || DEFAULT_FAUCET_BALANCE_ETH).trim();

async function main() {
  const targetWei = ethers.parseEther(balanceEth);
  if (targetWei <= 0n) throw new Error('CLASS_FAUCET_BALANCE_ETH must be greater than zero');

  const wallet = new ethers.Wallet(privateKey);
  const network = ethers.Network.from(31337);
  const provider = new ethers.JsonRpcProvider(rpcUrl, network, { staticNetwork: network });
  const hexWei = `0x${targetWei.toString(16)}`;

  await provider.send('hardhat_setBalance', [wallet.address, hexWei]);
  const actualWei = await provider.getBalance(wallet.address);
  if (actualWei < targetWei) {
    throw new Error(`Faucet balance verification failed: expected ${balanceEth} ETH, got ${ethers.formatEther(actualWei)} ETH`);
  }

  console.log(`[faucet] class bank ${wallet.address} funded to ${ethers.formatEther(actualWei)} ETH`);
}

main().catch((err) => {
  console.error(`[faucet] failed to set class bank balance: ${err?.message || err}`);
  process.exit(1);
});
