const { ethers } = require("ethers");

async function main() {
  console.log("Attempting to connect to local Hardhat node...");
  
  // Connect to the local Hardhat node
  const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");

  try {
    // Get the network information
    const network = await provider.getNetwork();
    console.log(`Connected to network: ${network.name} (chainId: ${network.chainId})`);

    // Get the block number
    const blockNumber = await provider.getBlockNumber();
    console.log(`Current block number: ${blockNumber}`);

    // Get accounts (Hardhat default accounts)
    const accounts = await provider.listAccounts();
    console.log(`Found ${accounts.length} accounts.`);
    if (accounts.length > 0) {
      const balance = await provider.getBalance(accounts[0].address);
      console.log(`Balance of first account (${accounts[0].address}): ${ethers.formatEther(balance)} ETH`);
    }

    console.log("Connection verification successful!");
  } catch (error) {
    console.error("Failed to connect to Hardhat node:", error.message);
    console.error("Make sure 'npx hardhat node' is running in a separate terminal.");
    process.exit(1);
  }
}

main();

