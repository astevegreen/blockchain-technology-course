/**
 * RpcClient - Centralized RPC provider and signer management
 * 
 * This module manages the optional write provider for instructor-only
 * actions. Student faucet/top-off requests go through lab-api so browsers do
 * not perform direct RPC reads for balance, nonce, fee, or receipt polling.
 * 
 * Faucet transfers are intentionally server-side. Do not put faucet private
 * keys in the browser bundle.
 */

import { ethers } from 'ethers';

/**
 * Resolve RPC URL to a full URL. Relative paths like /rpc-write must be
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

class RpcClient {
  constructor() {
    this.provider = null;
    this.rpcUrl = null;
    this.bankAddress = null;
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
      this.bankAddress = null;
      this.rpcUrl = null;
      return true;
    }
    
    try {
      this.rpcUrl = sanitized;
      const resolved = resolveRpcUrl(sanitized);
      const network = ethers.Network.from(31337);
      this.provider = new ethers.JsonRpcProvider(resolved, network, { staticNetwork: network });
      return true;
    } catch (e) {
      console.error("Failed to create provider:", e);
      this.provider = null;
      this.bankAddress = null;
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
   * Get the bank address reported by the server-side faucet.
   * @returns {{address: string}|null}
   */
  getBankSigner() {
    return this.bankAddress ? { address: this.bankAddress } : null;
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
    const result = await this.requestFaucetTopOff(toAddress, { amountEth });
    if (result.bankAddress) this.bankAddress = result.bankAddress;
    return result;
  }

  /**
   * Ensure a wallet has at least targetBalanceEth using the server-side faucet.
   * @param {string} toAddress
   * @param {string} targetBalanceEth
   */
  async ensureBankBalance(toAddress, targetBalanceEth) {
    const result = await this.requestFaucetTopOff(toAddress, { targetBalanceEth });
    if (result.bankAddress) this.bankAddress = result.bankAddress;
    return result;
  }

  async requestFaucetTopOff(toAddress, payload) {
    const base = (import.meta.env.BASE_URL || '/');
    const url = base.endsWith('/') ? `${base}lab-api/faucet/topoff` : `${base}/lab-api/faucet/topoff`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ address: toAddress, ...payload }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || result?.ok === false) {
      const err = new Error(result?.error || `Faucet top-off failed (${response.status})`);
      err.code = result?.code || null;
      err.retryable = result?.retryable !== false;
      err.queue = result?.queue || null;
      err.status = response.status;
      throw err;
    }
    if (result.txHash && !result.hash) result.hash = result.txHash;
    return result;
  }
}

// Singleton instance for the entire app
export const rpcClient = new RpcClient();

// Also export the class for testing purposes
export { RpcClient };
