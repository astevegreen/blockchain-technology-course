/**
 * PosClient - Domain class for PoS Simulator contract interactions
 * 
 * This class encapsulates all interactions with the PoSSimulator smart contract,
 * providing a clean API for staking, messaging, and event querying with
 * support for incremental event fetching to improve performance.
 */

import { ethers } from 'ethers';
import PoSABI from '../PoS.json';

export class PosClient {
  /**
   * Create a new PosClient instance
   * @param {ethers.Provider} provider - The ethers provider
   * @param {string} contractAddress - The PoS contract address
   */
  constructor(provider, contractAddress) {
    this.provider = provider;
    this.address = contractAddress;
    this.contract = new ethers.Contract(contractAddress, PoSABI, provider);
    this.lastProcessedBlock = 0;
  }

  /**
   * Check if the contract is valid and accessible
   * @returns {Promise<boolean>}
   */
  async isValid() {
    try {
      await this.contract.totalStaked();
      return true;
    } catch {
      return false;
    }
  }

  // ==================== READ OPERATIONS ====================

  /**
   * Get the total amount staked in the contract
   * @returns {Promise<bigint>}
   */
  async getTotalStaked() {
    return this.contract.totalStaked();
  }

  /**
   * Get a user's stake amount
   * @param {string} address - User address
   * @returns {Promise<bigint>}
   */
  async getStake(address) {
    return this.contract.stakes(address);
  }

  /**
   * Get a user's staking start time
   * @param {string} address - User address
   * @returns {Promise<bigint>}
   */
  async getStakingStartTime(address) {
    return this.contract.stakingStartTime(address);
  }

  /**
   * Calculate pending reward for a user
   * @param {string} address - User address
   * @returns {Promise<bigint>}
   */
  async getReward(address) {
    return this.contract.calculateReward(address);
  }

  /**
   * Get a user's complete staking info
   * @param {string} address - User address
   * @returns {Promise<{amount: string, reward: string, startTime: number}>}
   */
  async getStakeInfo(address) {
    const [stake, reward, startTime] = await Promise.all([
      this.getStake(address),
      this.getReward(address),
      this.getStakingStartTime(address)
    ]);
    
    return {
      amount: ethers.formatEther(stake),
      reward: ethers.formatEther(reward),
      startTime: Number(startTime)
    };
  }

  // ==================== EVENT QUERIES ====================

  /**
   * Fetch chat messages from the contract
   * @param {number} fromBlock - Starting block (0 for all)
   * @param {number} toBlock - Ending block (optional, defaults to latest)
   * @returns {Promise<Array<{sender: string, text: string, timestamp: number, blockNumber: number}>>}
   */
  async getChatMessages(fromBlock = 0, toBlock = null) {
    const to = toBlock ?? 'latest';
    const events = await this.contract.queryFilter("NewMessage", fromBlock, to);
    
    return events.map(e => ({
      sender: e.args[0],
      text: e.args[1],
      timestamp: Number(e.args[2]),
      blockNumber: e.blockNumber
    })).sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * Fetch stake events from the contract
   * @param {number} fromBlock - Starting block (0 for all)
   * @param {number} toBlock - Ending block (optional)
   * @returns {Promise<Array<{validator: string, amount: string, blockNumber: number}>>}
   */
  async getStakeEvents(fromBlock = 0, toBlock = null) {
    const to = toBlock ?? 'latest';
    const events = await this.contract.queryFilter("Staked", fromBlock, to);
    
    return events.map(e => ({
      validator: e.args[0],
      amount: ethers.formatEther(e.args[1]),
      blockNumber: e.blockNumber
    }));
  }

  /**
   * Fetch withdrawal events from the contract
   * @param {number} fromBlock - Starting block (0 for all)
   * @param {number} toBlock - Ending block (optional)
   * @returns {Promise<Array<{validator: string, amount: string, reward: string, blockNumber: number}>>}
   */
  async getWithdrawEvents(fromBlock = 0, toBlock = null) {
    const to = toBlock ?? 'latest';
    const events = await this.contract.queryFilter("Withdrawn", fromBlock, to);
    
    return events.map(e => ({
      validator: e.args[0],
      amount: ethers.formatEther(e.args[1]),
      reward: ethers.formatEther(e.args[2]),
      blockNumber: e.blockNumber
    }));
  }

  /**
   * Get unique participant addresses (anyone who staked or messaged)
   * @param {number} fromBlock - Starting block
   * @returns {Promise<string[]>}
   */
  async getParticipants(fromBlock = 0) {
    const [stakeEvents, msgEvents] = await Promise.all([
      this.contract.queryFilter("Staked", fromBlock),
      this.contract.queryFilter("NewMessage", fromBlock)
    ]);
    
    const addresses = new Set([
      ...stakeEvents.map(e => e.args[0]),
      ...msgEvents.map(e => e.args[0])
    ]);
    
    return [...addresses];
  }

  /**
   * Incremental event fetching - only fetch new events since last call
   * @param {string} eventName - Event name to fetch
   * @returns {Promise<{events: Array, fromBlock: number, toBlock: number}>}
   */
  async fetchNewEvents(eventName) {
    const currentBlock = await this.provider.getBlockNumber();
    const fromBlock = this.lastProcessedBlock === 0 ? 0 : this.lastProcessedBlock + 1;
    
    if (fromBlock > currentBlock) {
      return { events: [], fromBlock, toBlock: currentBlock };
    }
    
    const events = await this.contract.queryFilter(eventName, fromBlock, currentBlock);
    this.lastProcessedBlock = currentBlock;
    
    return { events, fromBlock, toBlock: currentBlock };
  }

  /**
   * Reset the block cursor for incremental fetching
   * @param {number} block - Block to reset to (0 for beginning)
   */
  resetBlockCursor(block = 0) {
    this.lastProcessedBlock = block;
  }

  // ==================== WRITE OPERATIONS ====================
  // These require a signer to be connected

  /**
   * Stake ETH to become a validator
   * @param {ethers.Signer} signer - The signer to use
   * @param {string} amountEth - Amount to stake in ETH (e.g., "1.0")
   * @returns {Promise<ethers.TransactionReceipt>}
   */
  async stake(signer, amountEth) {
    const connected = this.contract.connect(signer);
    const tx = await connected.stake({ value: ethers.parseEther(amountEth) });
    return tx.wait();
  }

  /**
   * Withdraw stake and rewards
   * @param {ethers.Signer} signer - The signer to use
   * @returns {Promise<ethers.TransactionReceipt>}
   */
  async withdraw(signer) {
    const connected = this.contract.connect(signer);
    const tx = await connected.withdraw();
    return tx.wait();
  }

  /**
   * Send a chat message
   * @param {ethers.Signer} signer - The signer to use
   * @param {string} message - The message text
   * @returns {Promise<ethers.TransactionReceipt>}
   */
  async sendMessage(signer, message) {
    const connected = this.contract.connect(signer);
    const tx = await connected.sendMessage(message);
    return tx.wait();
  }

  /**
   * Get the raw contract instance for advanced operations
   * @returns {ethers.Contract}
   */
  getContract() {
    return this.contract;
  }
}

