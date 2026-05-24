/**
 * BlockchainEnv - Shared utility class for CLI scripts
 * 
 * Provides common functionality for interacting with the blockchain
 * from CLI scripts, reducing code duplication across lab scripts.
 * 
 * Usage:
 *   const { BlockchainEnv } = require("../../lib/BlockchainEnv");
 *   const env = new BlockchainEnv();
 */

const { ethers } = require("hardhat");

class BlockchainEnv {
  constructor() {
    this.provider = ethers.provider;
    this._signers = null;
  }

  /**
   * Get all available signers (pre-funded accounts)
   * @returns {Promise<Array<Signer>>}
   */
  async getSigners() {
    if (!this._signers) {
      this._signers = await ethers.getSigners();
    }
    return this._signers;
  }

  /**
   * Get a specific signer by index
   * @param {number} index - Account index (0-19)
   * @returns {Promise<Signer>}
   */
  async getSigner(index = 0) {
    const signers = await this.getSigners();
    if (index < 0 || index >= signers.length) {
      throw new Error(`Invalid signer index: ${index}. Available: 0-${signers.length - 1}`);
    }
    return signers[index];
  }

  /**
   * Get block information
   * @param {number|string} blockNumber - Block number or 'latest'
   * @returns {Promise<Object>}
   */
  async getBlockInfo(blockNumber = 'latest') {
    const block = await this.provider.getBlock(blockNumber);
    if (!block) {
      throw new Error(`Block ${blockNumber} not found`);
    }
    return {
      number: block.number,
      hash: block.hash,
      parentHash: block.parentHash,
      timestamp: new Date(block.timestamp * 1000),
      txCount: block.transactions.length,
      gasUsed: block.gasUsed.toString(),
      gasLimit: block.gasLimit.toString(),
      miner: block.miner
    };
  }

  /**
   * Get current block number
   * @returns {Promise<number>}
   */
  async getBlockNumber() {
    return this.provider.getBlockNumber();
  }

  /**
   * Get account balance in ETH
   * @param {string} address - Account address
   * @returns {Promise<string>}
   */
  async getBalance(address) {
    const bal = await this.provider.getBalance(address);
    return ethers.formatEther(bal);
  }

  /**
   * Get account balance as BigInt
   * @param {string} address - Account address
   * @returns {Promise<bigint>}
   */
  async getBalanceRaw(address) {
    return this.provider.getBalance(address);
  }

  /**
   * Get network information
   * @returns {Promise<Object>}
   */
  async getNetwork() {
    return this.provider.getNetwork();
  }

  /**
   * Get transaction count (nonce) for an address
   * @param {string} address - Account address
   * @returns {Promise<number>}
   */
  async getTransactionCount(address) {
    return this.provider.getTransactionCount(address);
  }

  /**
   * Get gas fee data
   * @returns {Promise<Object>}
   */
  async getFeeData() {
    return this.provider.getFeeData();
  }

  /**
   * Estimate gas for a transaction
   * @param {Object} tx - Transaction object
   * @returns {Promise<bigint>}
   */
  async estimateGas(tx) {
    return this.provider.estimateGas(tx);
  }

  /**
   * Check if an address is a contract
   * @param {string} address - Address to check
   * @returns {Promise<boolean>}
   */
  async isContract(address) {
    const code = await this.provider.getCode(address);
    return code !== "0x";
  }

  /**
   * Get a transaction by hash
   * @param {string} hash - Transaction hash
   * @returns {Promise<Object>}
   */
  async getTransaction(hash) {
    return this.provider.getTransaction(hash);
  }

  /**
   * Get a transaction receipt
   * @param {string} hash - Transaction hash
   * @returns {Promise<Object>}
   */
  async getTransactionReceipt(hash) {
    return this.provider.getTransactionReceipt(hash);
  }

  /**
   * Send ETH from one account to another
   * @param {Signer} signer - The sender
   * @param {string} to - Recipient address
   * @param {string} amountEth - Amount in ETH
   * @returns {Promise<Object>} - Transaction receipt
   */
  async sendEth(signer, to, amountEth) {
    const tx = await signer.sendTransaction({
      to,
      value: ethers.parseEther(amountEth)
    });
    return tx.wait();
  }

  /**
   * Format ETH from Wei
   * @param {bigint|string} wei - Amount in Wei
   * @returns {string}
   */
  formatEther(wei) {
    return ethers.formatEther(wei);
  }

  /**
   * Parse ETH to Wei
   * @param {string} eth - Amount in ETH
   * @returns {bigint}
   */
  parseEther(eth) {
    return ethers.parseEther(eth);
  }

  /**
   * Format gas units (Gwei)
   * @param {bigint|string} wei - Amount in Wei
   * @returns {string}
   */
  formatGwei(wei) {
    return ethers.formatUnits(wei, "gwei");
  }

  /**
   * Get a contract factory
   * @param {string} contractName - Name of the contract
   * @returns {Promise<ContractFactory>}
   */
  async getContractFactory(contractName) {
    return ethers.getContractFactory(contractName);
  }

  /**
   * Get an existing contract
   * @param {string} contractName - Name of the contract
   * @param {string} address - Contract address
   * @returns {Promise<Contract>}
   */
  async getContractAt(contractName, address) {
    return ethers.getContractAt(contractName, address);
  }

  /**
   * Print a separator line
   * @param {string} char - Character to use
   * @param {number} length - Line length
   */
  printSeparator(char = '=', length = 50) {
    console.log(char.repeat(length));
  }

  /**
   * Print a header
   * @param {string} title - Header title
   */
  printHeader(title) {
    console.log(`\n${title}\n`);
    this.printSeparator();
  }

  /**
   * Print account balances for first N accounts
   * @param {number} count - Number of accounts to show
   */
  async printAccountBalances(count = 5) {
    const signers = await this.getSigners();
    console.log("\n--- Account Balances ---");
    for (let i = 0; i < Math.min(count, signers.length); i++) {
      const bal = await this.getBalance(signers[i].address);
      console.log(`Account ${i}: ${signers[i].address}`);
      console.log(`  Balance: ${bal} ETH`);
    }
  }
}

module.exports = { BlockchainEnv };

