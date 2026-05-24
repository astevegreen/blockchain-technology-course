/**
 * RpcClient - Centralized RPC provider and signer management
 * 
 * This module manages a single provider instance for the entire app,
 * eliminating redundant provider instantiation and centralizing the
 * "bank" account used for classroom faucet operations.
 * 
 * ⚠️ CLASSROOM USE ONLY ⚠️
 * The bank private key is a well-known test account.
 * NEVER use this pattern with real funds or on mainnet.
 */

import { ethers } from 'ethers';

/**
 * Resolve RPC URL to a full URL. Relative paths like /rpc-proxy must be
 * converted to same-origin URLs for ethers.JsonRpcProvider (which requires
 * http/https protocol).
 */
export function resolveRpcUrl(url) {
  const sanitized = (url || '').trim();
  if (!sanitized) return sanitized;
  if (sanitized.startsWith('/')) {
    const base = import.meta.env.BASE_URL || '/';
    const cleanPath = sanitized.substring(1); // remove leading slash from sanitized
    return (typeof window !== 'undefined' ? window.location.origin : '') + base + cleanPath;
  }
  return sanitized;
}

// Account 0 = deployer = bank/faucet (Hardhat's first test account).
// Same address deploys the PoS contract and sends test ETH to students.
const BANK_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";

class RpcClient {
  constructor() {
    this.provider = null;
    this.rpcUrl = null;
    this.bankSigner = null;
  }

  /**
   * Set the RPC URL and create a new provider
   * @param {string} url - The RPC endpoint URL
   * @returns {boolean} - True if provider was updated, false if unchanged
   */
  setRpcUrl(url) {
    const sanitized = (url || '').trim();
    
    // Don't recreate if URL hasn't changed
    if (sanitized === this.rpcUrl) return false;
    
    // Clear provider if URL is empty
    if (!sanitized) {
      this.provider = null;
      this.bankSigner = null;
      this.rpcUrl = null;
      return true;
    }
    
    try {
      this.rpcUrl = sanitized;
      const resolved = resolveRpcUrl(sanitized);
      this.provider = new ethers.JsonRpcProvider(resolved);
      this.bankSigner = new ethers.Wallet(BANK_PRIVATE_KEY, this.provider);
      return true;
    } catch (e) {
      console.error("Failed to create provider:", e);
      this.provider = null;
      this.bankSigner = null;
      this.rpcUrl = null;
      return false;
    }
  }

  /**
   * Get the current provider instance
   * @returns {ethers.JsonRpcProvider|null}
   */
  getProvider() {
    return this.provider;
  }

  /**
   * Get the current RPC URL
   * @returns {string|null}
   */
  getRpcUrl() {
    return this.rpcUrl;
  }

  /**
   * Get the bank signer for faucet operations
   * ⚠️ CLASSROOM USE ONLY - This is a test account
   * @returns {ethers.Wallet|null}
   */
  getBankSigner() {
    return this.bankSigner;
  }

  /**
   * Create a guest signer from a private key
   * @param {string} privateKey - The private key
   * @returns {ethers.Wallet}
   */
  createGuestSigner(privateKey) {
    if (!this.provider) {
      throw new Error("Provider not initialized. Call setRpcUrl first.");
    }
    return new ethers.Wallet(privateKey, this.provider);
  }

  /**
   * Check if the provider is connected to the network
   * @returns {Promise<{connected: boolean, blockNumber?: number, chainId?: string}>}
   */
  async checkConnection() {
    if (!this.provider) {
      return { connected: false };
    }
    
    try {
      const [blockNumber, network] = await Promise.all([
        this.provider.getBlockNumber(),
        this.provider.getNetwork()
      ]);
      return {
        connected: true,
        blockNumber,
        chainId: network.chainId.toString()
      };
    } catch (e) {
      return { connected: false, error: e.message };
    }
  }

  /**
   * Send ETH from the bank account (faucet)
   * ⚠️ CLASSROOM USE ONLY
   * @param {string} toAddress - Recipient address
   * @param {string} amountEth - Amount in ETH (e.g., "5.0")
   * @returns {Promise<ethers.TransactionReceipt>}
   */
  async sendFromBank(toAddress, amountEth) {
    if (!this.bankSigner) {
      throw new Error("Bank signer not initialized. Call setRpcUrl first.");
    }
    
    const tx = await this.bankSigner.sendTransaction({
      to: toAddress,
      value: ethers.parseEther(amountEth)
    });
    
    return tx.wait();
  }
}

// Singleton instance for the entire app
export const rpcClient = new RpcClient();

// Also export the class for testing purposes
export { RpcClient };

