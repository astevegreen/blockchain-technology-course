/**
 * BlockchainSync - Robust real-time blockchain synchronization
 * 
 * Provides reliable polling-based updates for classroom environments
 * where WebSocket connections may not be available.
 * 
 * Features:
 * - Fast polling (1 second default)
 * - Automatic retry on connection issues
 * - Change detection to avoid unnecessary re-renders
 * - Centralized data fetching for all components
 */

import { ethers } from 'ethers';
import PoSABI from '../PoS.json';

class BlockchainSync {
  constructor() {
    this.provider = null;
    this.contractAddress = null;
    this.contract = null;
    this.listeners = new Set();
    this.pollInterval = null;
    this.lastBlockNumber = 0;
    this.lastDataHash = '';
    this.isPolling = false;
    this.pollIntervalMs = 1000; // 1 second for responsive updates
    this.retryCount = 0;
    this.maxRetries = 5;
  }

  /**
   * Initialize the sync service with provider and contract
   */
  init(provider, contractAddress) {
    const addressChanged = contractAddress !== this.contractAddress;
    const providerChanged = provider !== this.provider;
    
    if (!addressChanged && !providerChanged) return;
    
    this.provider = provider;
    this.contractAddress = contractAddress;
    
    if (provider && contractAddress && contractAddress.length === 42) {
      this.contract = new ethers.Contract(contractAddress, PoSABI, provider);
      console.log('[BlockchainSync] Initialized with contract:', contractAddress);
    } else {
      this.contract = null;
    }
    
    // Reset state when config changes
    this.lastBlockNumber = 0;
    this.lastDataHash = '';
    this.retryCount = 0;
  }

  /**
   * Subscribe to blockchain updates
   * @param {Function} callback - Called with new data
   * @returns {Function} - Unsubscribe function
   */
  subscribe(callback) {
    this.listeners.add(callback);
    
    // Start polling if this is the first subscriber
    if (this.listeners.size === 1) {
      this.startPolling();
    }
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
      if (this.listeners.size === 0) {
        this.stopPolling();
      }
    };
  }

  /**
   * Start the polling loop
   */
  startPolling() {
    if (this.isPolling) return;
    
    this.isPolling = true;
    console.log('[BlockchainSync] Starting polling at', this.pollIntervalMs, 'ms intervals');
    
    // Immediate first fetch
    this.fetchAndNotify();
    
    // Set up interval
    this.pollInterval = setInterval(() => {
      this.fetchAndNotify();
    }, this.pollIntervalMs);
  }

  /**
   * Stop the polling loop
   */
  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
    this.isPolling = false;
    console.log('[BlockchainSync] Stopped polling');
  }

  /**
   * Force an immediate refresh (useful after transactions)
   */
  forceRefresh() {
    this.lastDataHash = ''; // Clear hash to force notification
    return this.fetchAndNotify();
  }

  /**
   * Fetch all blockchain data and notify listeners if changed
   */
  async fetchAndNotify() {
    if (!this.provider || !this.contract) {
      return;
    }

    try {
      // Verify contract exists before fetching data
      const code = await this.provider.getCode(this.contractAddress);
      if (code === '0x' || code === '0x0') {
        // Contract not deployed yet - silently skip
        return;
      }
      
      // Get current block number first
      const blockNumber = await this.provider.getBlockNumber();
      
      // Skip if no new blocks (optimization)
      // But still fetch every 5th poll to catch any missed updates
      const shouldFetch = blockNumber > this.lastBlockNumber || 
                          (Date.now() % 5000 < this.pollIntervalMs);
      
      if (!shouldFetch && this.lastDataHash) {
        return;
      }
      
      this.lastBlockNumber = blockNumber;
      
      // Fetch all data in parallel
      const data = await this.fetchAllData(blockNumber);
      
      // Check if data changed
      const dataHash = JSON.stringify(data);
      if (dataHash === this.lastDataHash) {
        return;
      }
      
      this.lastDataHash = dataHash;
      this.retryCount = 0; // Reset retry count on success
      
      // Notify all listeners
      this.listeners.forEach(callback => {
        try {
          callback(data);
        } catch (e) {
          console.error('[BlockchainSync] Listener error:', e);
        }
      });
      
    } catch (error) {
      // Ignore BAD_DATA errors (contract not deployed) - not a real error
      if (error.message?.includes('BAD_DATA') || error.message?.includes('could not decode')) {
        return;
      }
      
      this.retryCount++;
      console.warn('[BlockchainSync] Fetch error (attempt', this.retryCount, '):', error.message);
      
      // Notify listeners of connection issue after max retries
      if (this.retryCount >= this.maxRetries) {
        this.listeners.forEach(callback => {
          try {
            callback({ error: 'Connection lost. Retrying...', connected: false });
          } catch (e) {}
        });
      }
    }
  }

  /**
   * Fetch all data from the blockchain
   */
  async fetchAllData(blockNumber) {
    const contract = this.contract;
    const provider = this.provider;
    
    // Fetch network stats
    const [
      totalStaked,
      validatorCount,
      currentEpoch,
      timeUntilNextEpoch,
      currentAPY,
      contractBalance,
      lastProposedBlockNumber
    ] = await Promise.all([
      contract.totalStaked(),
      contract.getValidatorCount(),
      contract.currentEpoch(),
      contract.getTimeUntilNextEpoch(),
      contract.getCurrentAPY(),
      provider.getBalance(this.contractAddress),
      contract.lastProposedBlockNumber()
    ]);

    // Fetch recent events (last 100 blocks or from block 0)
    const fromBlock = Math.max(0, blockNumber - 100);
    const [stakeEvents, withdrawEvents, messageEvents, slashEvents, blockEvents] = await Promise.all([
      contract.queryFilter(contract.filters.Staked(), fromBlock),
      contract.queryFilter(contract.filters.Withdrawn(), fromBlock),
      contract.queryFilter(contract.filters.NewMessage(), fromBlock),
      contract.queryFilter(contract.filters.Slashed(), fromBlock),
      contract.queryFilter(contract.filters.BlockProposed(), fromBlock)
    ]);

    // Process chat messages (all time)
    const allMessages = await contract.queryFilter(contract.filters.NewMessage(), 0);
    const messages = allMessages.map(e => {
      const args = e.args || [];
      return {
        sender: args[0] ?? args.sender,
        text: args[1] ?? args.message ?? '',
        timestamp: Number(args[2] ?? args.timestamp ?? 0)
      };
    }).sort((a, b) => a.timestamp - b.timestamp);

    // Build participant roster from events (stakers + chat participants)
    const allStakeEvents = await contract.queryFilter(contract.filters.Staked(), 0);
    const stakerAddresses = allStakeEvents.map(e => e.args.validator);
    // Note: allMessages is raw events, so use e.args[0] not m.sender
    const chatAddresses = allMessages.map(e => e.args[0]);
    // Filter out any undefined values and create unique set
    const validatorAddresses = [...new Set([...stakerAddresses, ...chatAddresses].filter(Boolean))];

    // Build recent activity feed
    const recentActivity = [
      ...stakeEvents.map(e => ({
        type: 'stake',
        address: e.args.validator,
        amount: ethers.formatEther(e.args.amount),
        block: e.blockNumber
      })),
      ...withdrawEvents.map(e => ({
        type: 'withdraw',
        address: e.args.validator,
        amount: ethers.formatEther(e.args.amount),
        reward: ethers.formatEther(e.args.reward),
        block: e.blockNumber
      })),
      ...slashEvents.map(e => ({
        type: 'slash',
        address: e.args.validator,
        amount: ethers.formatEther(e.args.amount),
        reason: e.args.reason,
        block: e.blockNumber
      })),
      ...blockEvents.map(e => ({
        type: 'block',
        address: e.args.proposer,
        blockNumber: Number(e.args.blockNumber),
        reward: ethers.formatEther(e.args.reward),
        block: e.blockNumber
      }))
    ].sort((a, b) => b.block - a.block).slice(0, 20);

    return {
      connected: true,
      blockNumber,
      network: {
        totalStaked: ethers.formatEther(totalStaked),
        validatorCount: Number(validatorCount),
        currentEpoch: Number(currentEpoch),
        timeUntilNextEpoch: Number(timeUntilNextEpoch),
        currentAPY: Number(currentAPY) / 100,
        contractBalance: ethers.formatEther(contractBalance),
        lastProposedBlockNumber: Number(lastProposedBlockNumber)
      },
      messages,
      validators: validatorAddresses,
      recentActivity,
      timestamp: Date.now()
    };
  }

  /**
   * Get validator stats for a specific address
   */
  async getValidatorStats(address) {
    if (!this.contract || !this.provider) return null;
    
    try {
      // Verify contract exists
      const code = await this.provider.getCode(this.contractAddress);
      if (code === '0x' || code === '0x0') {
        return null; // Contract not deployed
      }
      
      const [stats, hasAttested, minDuration, unbondingReq] = await Promise.all([
        this.contract.getValidatorStats(address),
        this.contract.hasAttestedThisEpoch(address),
        this.contract.getMinStakeDurationRemaining(address),
        this.contract.withdrawalRequestTime(address)
      ]);
      
      return {
        amount: ethers.formatEther(stats.stakeAmount),
        reward: ethers.formatEther(stats.rewardAmount),
        slashCount: Number(stats.slashes),
        blocksProposed: Number(stats.blocks),
        missedAttestations: Number(stats.attestations),
        unbondingTime: Number(stats.unbondingTime),
        minStakeDuration: Number(minDuration),
        hasAttestedThisEpoch: hasAttested,
        withdrawalRequested: Number(unbondingReq) > 0
      };
    } catch (e) {
      // Only log if it's not a contract-not-found error
      if (!e.message?.includes('BAD_DATA') && !e.message?.includes('could not decode')) {
        console.error('[BlockchainSync] getValidatorStats error:', e);
      }
      return null;
    }
  }

  /**
   * Set polling interval (in milliseconds)
   */
  setPollingInterval(ms) {
    this.pollIntervalMs = Math.max(500, ms); // Minimum 500ms
    
    if (this.isPolling) {
      this.stopPolling();
      this.startPolling();
    }
  }
}

// Singleton instance
export const blockchainSync = new BlockchainSync();

