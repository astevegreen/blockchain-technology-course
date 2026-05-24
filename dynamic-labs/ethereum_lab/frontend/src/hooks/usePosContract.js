/**
 * usePosContract - React hook for PoS contract interactions
 * 
 * Provides state management for chat messages, validators, and staking
 * with incremental event fetching for optimal performance.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ethers } from 'ethers';
import { PosClient } from '../lib/PosClient';
import { EventIndexer } from '../lib/EventIndexer';

/**
 * Hook for managing PoS contract state
 * @param {ethers.Provider} provider - The ethers provider
 * @param {string} posAddress - The PoS contract address
 * @returns {Object} - Contract state and methods
 */
export function usePosContract(provider, posAddress) {
  // State
  const [messages, setMessages] = useState([]);
  const [validators, setValidators] = useState([]);
  const [myStake, setMyStake] = useState({ amount: '0', reward: '0', startTime: 0 });
  const [totalStaked, setTotalStaked] = useState('0');
  const [isSyncing, setIsSyncing] = useState(false);
  const [isValid, setIsValid] = useState(false);

  // Refs for client and indexer (don't trigger re-renders)
  const clientRef = useRef(null);
  const indexerRef = useRef(new EventIndexer({ maxEventsPerType: 1000 }));

  // Initialize client when provider or address changes
  useEffect(() => {
    if (!provider || !posAddress || posAddress.length !== 42) {
      clientRef.current = null;
      setIsValid(false);
      return;
    }

    const client = new PosClient(provider, posAddress);
    clientRef.current = client;
    indexerRef.current.clear(); // Reset cache for new address

    // Validate contract
    client.isValid().then(valid => {
      setIsValid(valid);
    });
  }, [provider, posAddress]);

  // Sync data - fetches messages and validators with incremental updates
  const syncData = useCallback(async (walletAddress = null) => {
    const client = clientRef.current;
    if (!client || !provider) return;

    setIsSyncing(true);

    try {
      const indexer = indexerRef.current;
      const currentBlock = await provider.getBlockNumber();
      const lastMsgBlock = indexer.getLastBlock('NewMessage');
      const lastStakeBlock = indexer.getLastBlock('Staked');

      // === CHAT MESSAGES ===
      if (lastMsgBlock === 0) {
        // Initial load - fetch all
        const allMsgs = await client.getChatMessages(0, currentBlock);
        indexer.setEvents('NewMessage', allMsgs, currentBlock);
        setMessages(allMsgs);
      } else if (currentBlock > lastMsgBlock) {
        // Incremental - only new blocks
        const newMsgs = await client.getChatMessages(lastMsgBlock + 1, currentBlock);
        if (newMsgs.length > 0) {
          const allMsgs = indexer.appendEvents('NewMessage', newMsgs, currentBlock);
          setMessages([...allMsgs].sort((a, b) => a.timestamp - b.timestamp));
        } else {
          // Update last block even if no new events
          indexer.appendEvents('NewMessage', [], currentBlock);
        }
      }

      // === VALIDATORS (Staked events) ===
      if (lastStakeBlock === 0) {
        // Initial load
        const stakeEvents = await client.getStakeEvents(0, currentBlock);
        indexer.setEvents('Staked', stakeEvents, currentBlock);
        
        // Also get message senders for full participant list
        const participants = await client.getParticipants(0);
        setValidators(participants);
      } else if (currentBlock > lastStakeBlock) {
        // Incremental
        const newStakes = await client.getStakeEvents(lastStakeBlock + 1, currentBlock);
        if (newStakes.length > 0) {
          indexer.appendEvents('Staked', newStakes, currentBlock);
          // Refresh full participant list
          const participants = await client.getParticipants(0);
          setValidators(participants);
        } else {
          indexer.appendEvents('Staked', [], currentBlock);
        }
      }

      // === TOTAL STAKED ===
      const total = await client.getTotalStaked();
      setTotalStaked(ethers.formatEther(total));

      // === USER STAKE INFO ===
      if (walletAddress) {
        const stakeInfo = await client.getStakeInfo(walletAddress);
        setMyStake(stakeInfo);
      }

    } catch (e) {
      console.error("Sync error:", e);
    } finally {
      setIsSyncing(false);
    }
  }, [provider]);

  // Stake ETH
  const stake = useCallback(async (signer, amountEth) => {
    const client = clientRef.current;
    if (!client) throw new Error("Contract not initialized");

    const receipt = await client.stake(signer, amountEth);
    
    // Force resync after staking
    indexerRef.current.clearEventType('Staked');
    
    return receipt;
  }, []);

  // Withdraw stake
  const withdraw = useCallback(async (signer) => {
    const client = clientRef.current;
    if (!client) throw new Error("Contract not initialized");

    const receipt = await client.withdraw(signer);
    
    // Force resync after withdrawal
    indexerRef.current.clearEventType('Staked');
    
    return receipt;
  }, []);

  // Send chat message
  const sendMessage = useCallback(async (signer, message) => {
    const client = clientRef.current;
    if (!client) throw new Error("Contract not initialized");

    const receipt = await client.sendMessage(signer, message);
    
    // Immediately add the message to state for instant feedback
    const newMsg = {
      sender: await signer.getAddress(),
      text: message,
      timestamp: Math.floor(Date.now() / 1000),
      blockNumber: receipt.blockNumber
    };
    
    setMessages(prev => [...prev, newMsg].sort((a, b) => a.timestamp - b.timestamp));
    
    return receipt;
  }, []);

  // Send sponsored message (using bank for gas)
  const sendSponsoredMessage = useCallback(async (bankSigner, userAddress, message) => {
    const client = clientRef.current;
    if (!client) throw new Error("Contract not initialized");

    // Format message to show original sender
    const shortAddr = `${userAddress.slice(0, 6)}...${userAddress.slice(-4)}`;
    const formattedMessage = `[${shortAddr}] ${message}`;

    const receipt = await client.sendMessage(bankSigner, formattedMessage);
    
    return receipt;
  }, []);

  // Get the client for advanced operations
  const getClient = useCallback(() => {
    return clientRef.current;
  }, []);

  // Get cache stats for debugging
  const getCacheStats = useCallback(() => {
    return indexerRef.current.getStats();
  }, []);

  // Clear cache and force full resync
  const clearCache = useCallback(() => {
    indexerRef.current.clear();
    setMessages([]);
    setValidators([]);
  }, []);

  return {
    // State
    messages,
    validators,
    myStake,
    totalStaked,
    isSyncing,
    isValid,
    
    // Methods
    syncData,
    stake,
    withdraw,
    sendMessage,
    sendSponsoredMessage,
    getClient,
    getCacheStats,
    clearCache
  };
}

