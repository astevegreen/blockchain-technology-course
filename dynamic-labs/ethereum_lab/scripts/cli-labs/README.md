# CLI Labs

This folder contains two parallel lab systems. Use the one that matches your setup.

## Hardhat Labs (`1-explore-blockchain.js` … `5-validator-simulation.js`)

- **Run with:** `npm run lab1` through `npm run lab5` (from project root)
- **Requires:** Hardhat node running (`npm run chain`), full project setup
- **Uses:** `lib/BlockchainEnv.js`, Hardhat's ethers provider
- **Best for:** Local development, when you have the blockchain running and want to use Hardhat's network helpers

## Standalone Labs (`standalone/`)

- **Run with:** `cd standalone && npm start` (interactive menu) or `node X.js` directly
- **Requires:** RPC endpoint (default `http://localhost:8545`); set `RPC_URL` in `.env` if different
- **Uses:** ethers + dotenv; connects as external client
- **Best for:** Docker, remote students, or running labs without the full Hardhat context

The standalone folder has more labs (1–8) including forensics, contract builder, and token concepts. Lab numbers overlap but the implementations differ.
