/**
 * InstructorView - Enhanced Instructor Dashboard
 * 
 * Features:
 * - Real-time student monitoring with staking stats
 * - Slashing controls for misbehavior
 * - Block proposal simulation with weighted validator selection
 * - Attestation checking and penalties
 * - Network stats (APY, validators, epochs)
 */

import { useState, useEffect, useRef } from 'react';
import { ethers } from 'ethers';
import { rpcClient } from '../lib/RpcClient';
import { MempoolTable } from '../components/MempoolTable';
import PoSABI from '../PoS.json';

// Scenario/role assignment belongs to the cut CRUD/forensics labs. Disabled so
// the instructor can't broadcast roles students can't use.
const SCENARIO_ROLES_ENABLED = false;
const LEGACY_INSTRUCTOR_RPC_POLL_ENABLED = false;
const ARCADE_GAME_NAMES = { 1: 'Block Breaker', 2: 'Mempool Invaders', 3: 'Gas Climber' };

const cacheBase = () => ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
const safeArcadeFormatEth = (wei) => {
  try {
    return `${Number(ethers.formatEther(BigInt(wei || 0))).toLocaleString(undefined, { maximumFractionDigits: 4 })} ETH`;
  } catch (_) {
    return '0 ETH';
  }
};
const shortAddress = (address) => (address ? `${String(address).slice(0, 8)}...${String(address).slice(-6)}` : '-');
const safeScore = (score) => Number(score || 0).toLocaleString();
const safeElapsed = (ms) => {
  const n = Number(ms || 0);
  if (!Number.isFinite(n) || n <= 0) return '-';
  return n < 1000 ? `${Math.round(n)}ms` : `${(n / 1000).toFixed(1)}s`;
};
const arcadeErrorMessage = (error) => error?.shortMessage || error?.reason || error?.message || String(error);

async function fetchInstructorArcadeState() {
  const base = cacheBase();
  for (const url of [`${base}/arcade-state`, `${base}/lab-api/arcade/state`]) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) continue;
      const data = await r.json();
      if (data && (data.ok || data.reason)) return data;
    } catch (_) {
      // Try the alternate route.
    }
  }
  return null;
}

async function fetchInstructorDefiRiskState() {
  const base = cacheBase();
  for (const url of [`${base}/lab-api/defi-risk/state`, `${base}/defi-risk/state`]) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) continue;
      const data = await r.json();
      if (data && (data.ok || data.reason || data.error)) return data;
    } catch (_) {
      // Try the alternate route.
    }
  }
  return null;
}

export function InstructorView({ provider, posAddress, rpcUrl, wallet, onOpenTerminal }) {
  // Initialize rpcClient with the RPC URL
  useEffect(() => {
    if (rpcUrl) {
      rpcClient.setRpcUrl(rpcUrl);
      console.log('[InstructorView] RpcClient initialized with:', rpcUrl);
    }
  }, [rpcUrl]);
  
  // Student data
  const [students, setStudents] = useState([]);
  
  // Contract stats
  const [contractBalance, setContractBalance] = useState('0');
  const [totalStaked, setTotalStaked] = useState('0');
  const [validatorCount, setValidatorCount] = useState(0);
  const [currentAPY, setCurrentAPY] = useState(0);
  const [currentEpoch, setCurrentEpoch] = useState(1);
  const [currentSlot, setCurrentSlot] = useState(1);
  const [participationRate, setParticipationRate] = useState(0);
  const [timeUntilNextEpoch, setTimeUntilNextEpoch] = useState(0);
  
  // Activity feed
  const [recentActivity, setRecentActivity] = useState([]);
  const [blockProposals, setBlockProposals] = useState([]);
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [slashReason, setSlashReason] = useState('');
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [actionLog, setActionLog] = useState([]);
  const [isActionInProgress, setIsActionInProgress] = useState(false);
  const [activeScenario, setActiveScenario] = useState('House Sale');
  const [fundAddress, setFundAddress] = useState('');
  const [autoBeaconActivity, setAutoBeaconActivity] = useState(true);
  const [miningState, setMiningState] = useState(null);
  const [fundAmount, setFundAmount] = useState('5');
  const [artifactInput, setArtifactInput] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterHasContract, setFilterHasContract] = useState('');
  const [fundRequests, setFundRequests] = useState([]);
  const [beaconCacheHealth, setBeaconCacheHealth] = useState(null);
  const [arcadeState, setArcadeState] = useState(null);
  const [arcadePriceInput, setArcadePriceInput] = useState('');
  const [arcadePriceDirty, setArcadePriceDirty] = useState(false);
  const [defiRiskState, setDefiRiskState] = useState(null);
  const [timelockFeeInput, setTimelockFeeInput] = useState('');
  const [timelockDelayInput, setTimelockDelayInput] = useState('');
  const [timelockTreasuryInput, setTimelockTreasuryInput] = useState('');
  const [timelockFormDirty, setTimelockFormDirty] = useState(false);

  // Poll student fund requests from Lab API
  useEffect(() => {
    const poll = async () => {
      try {
        const r = await fetch(import.meta.env.BASE_URL + 'lab-api/fund-requests');
        if (r.ok) {          const data = await r.json();
          setFundRequests(data.requests || []);
        }
      } catch {}
    };
    poll();
    const id = setInterval(poll, 3000);
    return () => clearInterval(id);
  }, []);

  // Beacon cache health: HTTP-only, no direct RPC from the instructor browser.
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
      for (const url of [base + '/beacon-state', base + '/lab-api/beacon/state']) {
        try {
          const r = await fetch(url, { cache: 'no-store' });
          if (!r.ok) continue;
          const snapshot = await r.json();
          if (!cancelled) setBeaconCacheHealth({ snapshot, fetchedAt: Date.now(), error: null });
          return;
        } catch (_) {}
      }
      if (!cancelled) {
        setBeaconCacheHealth((prev) => ({ ...(prev || {}), fetchedAt: Date.now(), error: 'Beacon cache endpoint unavailable' }));
      }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    const snapshot = beaconCacheHealth?.snapshot;
    if (!snapshot?.ok) return;

    setTotalStaked(snapshot.totalStaked || '0');
    setContractBalance(snapshot.totalStaked || '0');
    setValidatorCount(Number(snapshot.committeeSize || snapshot.committee?.length || 0));
    setCurrentAPY(0);
    setCurrentEpoch(Number(snapshot.currentEpoch || 0));
    setCurrentSlot(Number(snapshot.currentSlot || 0));
    setTimeUntilNextEpoch(0);

    const committee = snapshot.committee || [];
    const attestedMap = snapshot.committeeAttestedLast || {};
    const attested = committee.filter((address) => attestedMap[String(address).toLowerCase()]).length;
    setParticipationRate(committee.length ? Math.round((attested / committee.length) * 100) : 0);

    const validatorStats = snapshot.validatorStats || {};
    const slashCounts = snapshot.validatorSlashEvents || {};
    const validatorAttestations = snapshot.validatorAttestations || {};
    const rows = Object.values(validatorStats)
      .filter((entry) => entry && !entry.isBot)
      .map((entry) => {
        const key = String(entry.address || '').toLowerCase();
        return {
          address: entry.address,
          balance: '0',
          stake: entry.stake || '0',
          reward: '0',
          slashCount: (slashCounts[key] || []).length || (entry.slashed ? 1 : 0),
          blocksProposed: 0,
          missedAttestations: 0,
          unbondingTime: entry.exited ? 1 : 0,
          hasAttestedThisEpoch: !!attestedMap[key],
          role: '',
          roleContract: null,
          stakes: parseFloat(entry.stake || '0') > 0 ? 1 : 0,
          messages: 0,
          withdrawals: entry.exited ? 1 : 0,
          slashes: (slashCounts[key] || []).length || (entry.slashed ? 1 : 0),
          blocks: (validatorAttestations[key] || []).length,
        };
      });
    setStudents(rows);

    const recent = (snapshot.recentActivity || []).slice(-20).reverse().map((item) => {
      const msg = String(item.msg || '');
      const address = msg.match(/0x[0-9a-fA-F]{40}/)?.[0] || '0x0000000000000000000000000000000000000000';
      const type = /slash/i.test(msg) ? 'slash' : /proposed|block/i.test(msg) ? 'block' : /joined|stake/i.test(msg) ? 'stake' : 'message';
      return {
        type,
        address,
        amount: '0',
        reward: '0',
        reason: msg,
        message: msg,
        blockNumber: Number(item.blockNumber || 0),
        block: Number(item.blockNumber || 0),
      };
    });
    setRecentActivity(recent);
    setBlockProposals((snapshot.blocks || []).slice(-10).reverse());
  }, [beaconCacheHealth]);

  // Role options per scenario (plan: Part Z)
  const SCENARIO_ROLES = {
    'House Sale': ['', 'Admin', 'Seller', 'Buyer'],
    'Ransomware': ['', 'Victim', 'Attacker', 'Investigator'],
    'Event Tickets': ['', 'Organizer', 'Buyer'],
    'Voting': ['', 'Admin', 'Voter'],
    'Crowdfunding': ['', 'Creator', 'Contributor']
  };
  
  // Track last processed block for incremental updates
  const lastBlockRef = useRef(0);
  const activityCacheRef = useRef({
    stakeEvents: [],
    withdrawEvents: [],
    messageEvents: [],
    slashEvents: [],
    blockEvents: [],
    addressMap: new Map()
  });

  // Main data fetching effect
  useEffect(() => {
    if (!LEGACY_INSTRUCTOR_RPC_POLL_ENABLED) return;
    if (!provider || !posAddress || posAddress.length !== 42) {
      console.log("InstructorView: Waiting for valid contract address...");
      return;
    }

    const fetchData = async () => {
      try {
        // Verify contract exists before fetching data
        const code = await provider.getCode(posAddress);
        if (code === '0x' || code === '0x0') {
          // Contract not deployed at this address
          console.warn(`[InstructorView] No contract at ${posAddress}. Check CONTRACT_ADDRESS.txt or redeploy.`);
          return;
        }
        // Verify it's actually a PoS contract by checking for instructor()
        const posContract = new ethers.Contract(posAddress, PoSABI, provider);
        try {
          await posContract.instructor();
        } catch (abiErr) {
          console.error(`[InstructorView] Contract at ${posAddress} doesn't have instructor() — wrong contract or ABI mismatch.`);
          return;
        }
        
        const currentBlock = await provider.getBlockNumber();
        const isInitialLoad = lastBlockRef.current === 0;
        const fromBlock = isInitialLoad ? 0 : lastBlockRef.current + 1;
        
        // Skip if no new blocks
        if (!isInitialLoad && currentBlock <= lastBlockRef.current) {
          return;
        }

        setIsLoading(true);
        
        const cache = activityCacheRef.current;
        
        // Get contract stats
        const [total, balance, valCount, apy, epoch, epochTime, currentSlot] = await Promise.all([
          posContract.totalStaked(),
          provider.getBalance(posAddress),
          posContract.getValidatorCount(),
          posContract.getCurrentAPY(),
          posContract.currentEpoch(),
          posContract.getTimeUntilNextEpoch(),
          posContract.currentSlot()
        ]);
        
        setTotalStaked(ethers.formatEther(total));
        setContractBalance(ethers.formatEther(balance));
        setValidatorCount(Number(valCount));
        setCurrentAPY(Number(apy) / 100); // Convert from 500 to 5.00
        setCurrentEpoch(Number(epoch));
        setTimeUntilNextEpoch(Number(epochTime));
        setCurrentSlot(Number(currentSlot));
        
        // Fetch all event types
        const [newStakes, newWithdraws, newMsgs, newSlashes, newBlocks] = await Promise.all([
          posContract.queryFilter(posContract.filters.Staked(), fromBlock, currentBlock),
          posContract.queryFilter(posContract.filters.Withdrawn(), fromBlock, currentBlock),
          posContract.queryFilter(posContract.filters.NewMessage(), fromBlock, currentBlock),
          posContract.queryFilter(posContract.filters.Slashed(), fromBlock, currentBlock),
          posContract.queryFilter(posContract.filters.BlockProposed(), fromBlock, currentBlock)
        ]);
        
        // Merge new events into cache
        cache.stakeEvents.push(...newStakes);
        cache.withdrawEvents.push(...newWithdraws);
        cache.messageEvents.push(...newMsgs);
        cache.slashEvents.push(...newSlashes);
        cache.blockEvents.push(...newBlocks);
        
        // Limit cache size
        const maxCache = 500;
        if (cache.stakeEvents.length > maxCache) cache.stakeEvents = cache.stakeEvents.slice(-maxCache);
        if (cache.withdrawEvents.length > maxCache) cache.withdrawEvents = cache.withdrawEvents.slice(-maxCache);
        if (cache.messageEvents.length > maxCache) cache.messageEvents = cache.messageEvents.slice(-maxCache);
        if (cache.slashEvents.length > maxCache) cache.slashEvents = cache.slashEvents.slice(-maxCache);
        if (cache.blockEvents.length > maxCache) cache.blockEvents = cache.blockEvents.slice(-maxCache);
        
        // Update address activity map
        newStakes.forEach(e => {
          if (!cache.addressMap.has(e.args.validator)) {
            cache.addressMap.set(e.args.validator, { stakes: 0, messages: 0, withdrawals: 0, slashes: 0, blocks: 0 });
          }
          cache.addressMap.get(e.args.validator).stakes++;
        });
        
        newWithdraws.forEach(e => {
          if (!cache.addressMap.has(e.args.validator)) {
            cache.addressMap.set(e.args.validator, { stakes: 0, messages: 0, withdrawals: 0, slashes: 0, blocks: 0 });
          }
          cache.addressMap.get(e.args.validator).withdrawals++;
        });
        
        newMsgs.forEach(e => {
          if (!cache.addressMap.has(e.args.sender)) {
            cache.addressMap.set(e.args.sender, { stakes: 0, messages: 0, withdrawals: 0, slashes: 0, blocks: 0 });
          }
          cache.addressMap.get(e.args.sender).messages++;
        });
        
        newSlashes.forEach(e => {
          if (!cache.addressMap.has(e.args.validator)) {
            cache.addressMap.set(e.args.validator, { stakes: 0, messages: 0, withdrawals: 0, slashes: 0, blocks: 0 });
          }
          cache.addressMap.get(e.args.validator).slashes++;
        });
        
        newBlocks.forEach(e => {
          if (!cache.addressMap.has(e.args.proposer)) {
            cache.addressMap.set(e.args.proposer, { stakes: 0, messages: 0, withdrawals: 0, slashes: 0, blocks: 0 });
          }
          cache.addressMap.get(e.args.proposer).blocks++;
        });

        // Build role map from [SCENARIO:...] and [ROLES:...] chat messages (frontend-only roles)
        const roleMap = new Map();
        const sortedAddrs = [...cache.addressMap.keys()].map(a => a.toLowerCase()).sort();
        for (const e of cache.messageEvents) {
          const text = e.args?.message || e.args?.[1];
          if (!text || typeof text !== 'string') continue;
          const scenarioMatch = text.match(/^\[SCENARIO:([^:]+):([^\]]+)\]$/);
          if (scenarioMatch) {
            const roles = scenarioMatch[2].split(',').map(r => r.trim()).filter(Boolean);
            sortedAddrs.forEach((addr, idx) => {
              roleMap.set(addr, roles[idx % roles.length]);
            });
          }
          const rolesMatch = text.match(/\[ROLES:([^\]]+)\]/);
          if (rolesMatch) {
            rolesMatch[1].split(';').forEach(p => {
              if (p.length < 44) return;
              const addr = p.slice(0, 42).toLowerCase();
              if (p[42] !== ':') return;
              const role = p.slice(43).trim();
              if (addr && role) roleMap.set(addr, role);
            });
          }
        }
        
        // Build student data with enhanced stats (role from parsed chat, not contract)
        const studentData = await Promise.all(
          Array.from(cache.addressMap.keys()).map(async (address) => {
            const activity = cache.addressMap.get(address) || { stakes: 0, messages: 0, withdrawals: 0, slashes: 0, blocks: 0 };
            const role = roleMap.get(address.toLowerCase()) || '';
            try {
              const [bal, stats, hasAttested, roleContract] = await Promise.all([
                provider.getBalance(address),
                posContract.getValidatorStats(address),
                posContract.hasAttestedThisEpoch(address),
                posContract.roleContractAddress(address)
              ]);
              return {
                address,
                balance: ethers.formatEther(bal),
                stake: ethers.formatEther(stats.stakeAmount),
                reward: ethers.formatEther(stats.rewardAmount),
                slashCount: Number(stats.slashes),
                blocksProposed: Number(stats.blocks),
                missedAttestations: Number(stats.attestations),
                unbondingTime: Number(stats.unbondingTime),
                hasAttestedThisEpoch: hasAttested,
                role,
                roleContract: roleContract && roleContract !== ethers.ZeroAddress ? roleContract : null,
                ...activity
              };
            } catch (e) {
              console.warn(`Stats fetch failed for ${address}:`, e.message);
              return {
                address,
                balance: '0',
                stake: '0',
                reward: '0',
                slashCount: 0,
                blocksProposed: 0,
                missedAttestations: 0,
                unbondingTime: 0,
                hasAttestedThisEpoch: false,
                role,
                roleContract: null,
                ...activity
              };
            }
          })
        );
        
        // Filter out nulls and sort by activity
        const validStudents = studentData.filter(s => s !== null);
        validStudents.sort((a, b) => {
          const aTotal = a.stakes + a.messages + a.withdrawals + a.blocks;
          const bTotal = b.stakes + b.messages + b.withdrawals + b.blocks;
          return bTotal - aTotal;
        });
        
        setStudents(validStudents);
        
        // Participation rate: validators who attested this epoch / total validators
        const validators = validStudents.filter(s => parseFloat(s.stake) > 0);
        const attested = validators.filter(s => s.hasAttestedThisEpoch);
        setParticipationRate(validators.length > 0 ? Math.round((attested.length / validators.length) * 100) : 0);
        
        // Build recent activity feed
        const allEvents = [
          ...cache.stakeEvents.map(e => ({ 
            type: 'stake', 
            address: e.args.validator, 
            amount: ethers.formatEther(e.args.amount), 
            block: e.blockNumber 
          })),
          ...cache.withdrawEvents.map(e => ({ 
            type: 'withdraw', 
            address: e.args.validator, 
            amount: ethers.formatEther(e.args.amount), 
            reward: ethers.formatEther(e.args.reward), 
            block: e.blockNumber 
          })),
          ...cache.messageEvents.map(e => ({ 
            type: 'message', 
            address: e.args.sender, 
            message: e.args.message, 
            block: e.blockNumber 
          })),
          ...cache.slashEvents.map(e => ({
            type: 'slash',
            address: e.args.validator,
            amount: ethers.formatEther(e.args.amount),
            reason: e.args.reason,
            block: e.blockNumber
          })),
          ...cache.blockEvents.map(e => ({
            type: 'block',
            address: e.args.proposer,
            blockNumber: Number(e.args.blockNumber),
            reward: ethers.formatEther(e.args.reward),
            block: e.blockNumber 
          }))
        ];
        
        allEvents.sort((a, b) => b.block - a.block);
        setRecentActivity(allEvents.slice(0, 15));
        
        // Set block proposals separately
        setBlockProposals(cache.blockEvents.slice(-10).reverse());
        
        lastBlockRef.current = currentBlock;
        
      } catch (error) {
        // Only log if it's not a contract-not-found error
        if (!error.message?.includes('BAD_DATA') && !error.message?.includes('could not decode')) {
          console.error("Error fetching instructor data:", error);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    // Fast 1-second polling for responsive instructor dashboard
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [provider, posAddress]);

  // Format address for display
  const formatAddress = (addr) => `${addr.slice(0, 6)}...${addr.slice(-4)}`;

  const filteredStudents = students;

  // Export progress to CSV
  const exportProgressCSV = () => {
    const headers = ['Address', 'Staked', 'Blocks', 'Slashes', 'Attested'];
    const rows = filteredStudents.map((s) => [
      s.address,
      s.stake,
      s.blocksProposed || 0,
      s.slashCount || 0,
      s.hasAttestedThisEpoch ? 'Yes' : 'No',
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `progress-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showStatus('✅ CSV exported');
  };

  // Get activity icon
  const getActivityIcon = (type) => {
    switch (type) {
      case 'stake': return '💰';
      case 'withdraw': return '🏦';
      case 'message': return '💬';
      case 'slash': return '⚡';
      case 'block': return '🎲';
      default: return '📝';
    }
  };

  // Show temporary status message
  const showStatus = (msg, duration = 3000) => {
    setStatusMessage(msg);
    setTimeout(() => setStatusMessage(''), duration);
  };

  // Add to action log with timestamp
  const logAction = (action, status, details = '') => {
    const timestamp = new Date().toLocaleTimeString();
    const entry = { timestamp, action, status, details };
    console.log(`[Instructor ${timestamp}] ${action}: ${status}${details ? ' - ' + details : ''}`);
    setActionLog(prev => [entry, ...prev.slice(0, 19)]); // Keep last 20 entries
  };

  const formatCacheMs = (ms) => {
    if (ms == null || Number.isNaN(Number(ms))) return 'n/a';
    return `${(Number(ms) / 1000).toFixed(1)}s`;
  };

  const depositToWallet = async (address, amountEth, requestId = null) => {
    if (!address || !ethers.isAddress(address)) {
      showStatus('❌ Enter valid address');
      return;
    }
    const amt = parseFloat(amountEth);
    if (Number.isNaN(amt) || amt <= 0) {
      showStatus('❌ Enter valid amount');
      return;
    }
    setIsActionInProgress(true);
    showStatus(`💰 Depositing ${amt} ETH...`);
    try {
      const r = await fetch(import.meta.env.BASE_URL + 'lab-api/faucet/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address, amountEth: String(amt) }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || j.ok === false) throw new Error(j.error || `HTTP ${r.status}`);
      if (requestId) {
        await fetch(import.meta.env.BASE_URL + `lab-api/fund-request/${requestId}`, { method: 'DELETE' });
        setFundRequests(prev => prev.filter(req => req.id !== requestId));
      }
      showStatus(`✅ Deposited ${amt} ETH to ${formatAddress(address)}`, 5000);
      logAction('Deposit', '✅ SUCCESS', `${amt} ETH → ${formatAddress(address)}${j.txHash ? ` (${j.txHash.slice(0, 10)}...)` : ''}`);
      if (!requestId) setFundAddress('');
    } catch (e) {
      showStatus('❌ Deposit failed: ' + (e.message || e), 6000);
      logAction('Deposit', '❌ FAILED', e.message || String(e));
    } finally {
      setIsActionInProgress(false);
    }
  };

  // ==================== INSTRUCTOR ACTIONS ====================

  // Slash a validator
  const handleSlash = async (address) => {
    if (!slashReason.trim()) {
      showStatus('⚠️ Please enter a reason for slashing');
      logAction('Slash', '⚠️ BLOCKED', 'No reason provided');
      return;
    }
    
    if (!confirm(`Slash ${formatAddress(address)} for "${slashReason}"?\nThis will deduct 5% of their stake.`)) {
      logAction('Slash', '❌ CANCELLED', `User cancelled for ${formatAddress(address)}`);
      return;
    }
    
    setIsActionInProgress(true);
    logAction('Slash', '⏳ STARTED', `Target: ${formatAddress(address)}, Reason: ${slashReason}`);
    
    try {
      showStatus('⚡ Slashing validator...');
      const bankSigner = rpcClient.getBankSigner();
      if (!bankSigner) {
        showStatus('❌ Bank signer not initialized. Check RPC connection.');
        logAction('Slash', '❌ FAILED', 'Bank signer not initialized');
        return;
      }
      const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
      console.log('[Instructor] Sending slash transaction...');
      const tx = await contract.slash(address, slashReason);
      console.log('[Instructor] Slash TX sent:', tx.hash);
      logAction('Slash', '📤 TX SENT', `Hash: ${tx.hash.slice(0, 18)}...`);
      
      const receipt = await tx.wait();
      console.log('[Instructor] Slash TX confirmed in block:', receipt.blockNumber);
      
      showStatus(`✅ Slashed ${formatAddress(address)}!`);
      logAction('Slash', '✅ SUCCESS', `${formatAddress(address)} slashed, block #${receipt.blockNumber}`);
      setSlashReason('');
      setSelectedStudent(null);
    } catch (e) {
      console.error('Slash error:', e);
      showStatus('❌ Slash failed: ' + (e.reason || e.message));
      logAction('Slash', '❌ FAILED', e.reason || e.message);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // Reflect whether the conductor is generating synthetic Beacon activity.
  useEffect(() => {
    let cancelled = false;
    fetch(import.meta.env.BASE_URL + 'lab-api/beacon/auto-activity', { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => { if (!cancelled && j) setAutoBeaconActivity(j.enabled !== false); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await fetch(import.meta.env.BASE_URL + 'lab-api/mining/state', { cache: 'no-store' });
        if (!r.ok) return;
        const j = await r.json();
        if (!cancelled) setMiningState(j);
      } catch (_) {}
    };
    load();
    const id = setInterval(load, 2000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const data = await fetchInstructorArcadeState();
      if (cancelled) return;
      setArcadeState(data);
      if (!arcadePriceDirty && data?.tokenPriceWei) {
        try {
          setArcadePriceInput(ethers.formatEther(BigInt(data.tokenPriceWei)));
        } catch (_) {
          setArcadePriceInput('');
        }
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, [arcadePriceDirty]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const data = await fetchInstructorDefiRiskState();
      if (cancelled) return;
      setDefiRiskState(data);
      const timelock = data?.timelock;
      if (!timelockFormDirty && timelock?.address) {
        setTimelockFeeInput(timelock.withdrawFeeBps || '0');
        setTimelockDelayInput(timelock.unlockDelaySeconds || '0');
        setTimelockTreasuryInput(timelock.treasury || '');
      }
    };
    load();
    const id = setInterval(load, 10000);
    return () => { cancelled = true; clearInterval(id); };
  }, [timelockFormDirty]);

  const handleToggleAutoBeaconActivity = async () => {
    const next = !autoBeaconActivity;
    setIsActionInProgress(true);
    showStatus(next ? '▶ Enabling auto Beacon activity…' : '⏸ Pausing auto Beacon activity…');
    try {
      const r = await fetch(import.meta.env.BASE_URL + 'lab-api/beacon/auto-activity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: next }),
      });
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.error || `HTTP ${r.status}`);
      }
      const j = await r.json().catch(() => ({}));
      setAutoBeaconActivity(j.enabled !== false);
      showStatus(next ? '✅ Auto Beacon activity ON.' : '✅ Auto Beacon activity OFF — Beacon remains available for student transactions.', 6000);
    } catch (e) {
      showStatus('❌ Auto activity toggle failed: ' + (e.message || e), 6000);
    } finally {
      setIsActionInProgress(false);
    }
  };

  const handleSetAutomine = async (automine) => {
    setIsActionInProgress(true);
    showStatus(automine ? '⚡ Enabling automine…' : '⏱ Enabling delayed mining…');
    try {
      const r = await fetch(import.meta.env.BASE_URL + 'lab-api/mining/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ automine }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || j.ok === false) throw new Error(j.error || `HTTP ${r.status}`);
      setMiningState(j);
      showStatus(automine ? '✅ Automine enabled.' : `✅ Delayed mining enabled (${j.delayMs ?? 500}ms).`, 5000);
    } catch (e) {
      showStatus('❌ Mining mode update failed: ' + (e.message || e), 6000);
    } finally {
      setIsActionInProgress(false);
    }
  };

  const handleSetArcadePrice = async () => {
    const raw = String(arcadePriceInput || '').trim();
    if (!raw || Number(raw) <= 0) {
      showStatus('❌ Enter a positive ARC price.', 5000);
      return;
    }
    setIsActionInProgress(true);
    showStatus(`Updating ARC price to ${raw} ETH...`);
    try {
      const r = await fetch(import.meta.env.BASE_URL + 'lab-api/arcade/price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priceEth: raw }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || j.ok === false) throw new Error(j.error || `HTTP ${r.status}`);
      setArcadeState(j.state || await fetchInstructorArcadeState());
      setArcadePriceDirty(false);
      showStatus(`✅ ARC price updated to ${raw} ETH.`, 5000);
      logAction('Arcade Price', '✅ SUCCESS', `${raw} ETH${j.txHash ? ` (${j.txHash.slice(0, 10)}...)` : ''}`);
    } catch (e) {
      showStatus('❌ ARC price update failed: ' + arcadeErrorMessage(e), 6000);
      logAction('Arcade Price', '❌ FAILED', arcadeErrorMessage(e));
    } finally {
      setIsActionInProgress(false);
    }
  };

  const postTimelockUpdate = async (payload, label) => {
    setIsActionInProgress(true);
    showStatus(`Updating TimelockRugVault ${label}...`);
    try {
      const r = await fetch(import.meta.env.BASE_URL + 'lab-api/defi-risk/timelock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || j.ok === false) throw new Error(j.error || `HTTP ${r.status}`);
      const nextState = j.state || await fetchInstructorDefiRiskState();
      setDefiRiskState(nextState);
      const timelock = nextState?.timelock;
      if (timelock?.address) {
        setTimelockFeeInput(timelock.withdrawFeeBps || '0');
        setTimelockDelayInput(timelock.unlockDelaySeconds || '0');
        setTimelockTreasuryInput(timelock.treasury || '');
      }
      setTimelockFormDirty(false);
      const hash = Array.isArray(j.txHashes) && j.txHashes.length > 0 ? ` (${j.txHashes[0].slice(0, 10)}...)` : '';
      showStatus(`✅ TimelockRugVault ${label} updated.`, 5000);
      logAction('DeFi Timelock', '✅ SUCCESS', `${label}${hash}`);
    } catch (e) {
      showStatus('❌ Timelock update failed: ' + arcadeErrorMessage(e), 6000);
      logAction('DeFi Timelock', '❌ FAILED', `${label}: ${arcadeErrorMessage(e)}`);
    } finally {
      setIsActionInProgress(false);
    }
  };

  const handleSaveTimelockSettings = async () => {
    const fee = String(timelockFeeInput || '').trim();
    const delay = String(timelockDelayInput || '').trim();
    const treasury = String(timelockTreasuryInput || '').trim();
    if (!/^\d+$/.test(fee) || Number(fee) > 9000) {
      showStatus('❌ Withdrawal fee must be an integer from 0 to 9000 bps.', 5000);
      return;
    }
    if (!/^\d+$/.test(delay)) {
      showStatus('❌ Unlock delay must be a non-negative integer number of seconds.', 5000);
      return;
    }
    if (!ethers.isAddress(treasury)) {
      showStatus('❌ Treasury must be a valid Ethereum address.', 5000);
      return;
    }
    await postTimelockUpdate({
      withdrawFeeBps: fee,
      unlockDelaySeconds: delay,
      treasury,
    }, 'settings');
  };

  // Reset the beacon chain. Signals the conductor (account #0, which owns the
  // chain) to evm_revert to its clean snapshot — clears blocks, reseats bots,
  // and reclaims node memory without changing any contract addresses.
  const handleResetChain = async () => {
    const typed = window.prompt('Reset the Beacon chain? This reverts Beacon/class activity to the conductor snapshot. Type RESET BEACON CHAIN to confirm.');
    if (typed !== 'RESET BEACON CHAIN') {
      showStatus('Reset cancelled.');
      return;
    }
    setIsActionInProgress(true);
    showStatus('🔄 Requesting chain reset...');
    try {
      const r = await fetch(import.meta.env.BASE_URL + 'lab-api/beacon/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: 'RESET BEACON CHAIN' }),
      });
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.error || `HTTP ${r.status}`);
      }
      showStatus('✅ Reset requested — chain will prune within a few seconds.', 6000);
    } catch (e) {
      showStatus('❌ Reset failed: ' + (e.message || e), 6000);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // Propose block (staker-first, instructor fallback)
  const handleSimulateBlock = async () => {
    setIsActionInProgress(true);
    logAction('Block Proposal', '⏳ STARTED', 'Selecting proposer...');
    
    try {
      showStatus('📦 Proposing block...');
      const bankSigner = rpcClient.getBankSigner();
      if (!bankSigner) {
        showStatus('❌ Bank signer not initialized');
        logAction('Block Proposal', '❌ FAILED', 'Bank signer not initialized');
        return;
      }
      const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
      
      console.log('[Instructor] Sending block proposal transaction...');
      const tx = await contract.proposeBlock();
      console.log('[Instructor] Block proposal TX sent:', tx.hash);
      logAction('Block Proposal', '📤 TX SENT', `Hash: ${tx.hash.slice(0, 18)}...`);
      
      const receipt = await tx.wait();
      console.log('[Instructor] Block proposal TX confirmed in block:', receipt.blockNumber);
      
      // Parse the event to get the selected validator
      const event = receipt.logs.find(log => {
        try {
          const parsed = contract.interface.parseLog(log);
          return parsed.name === 'BlockProposed';
        } catch { return false; }
      });
      
      if (event) {
        const parsed = contract.interface.parseLog(event);
        const proposer = parsed.args.proposer;
        const reward = ethers.formatEther(parsed.args.reward);
        showStatus(`✅ Block proposed by ${formatAddress(proposer)}!`, 5000);
        logAction('Block Proposal', '✅ SUCCESS', `Proposer: ${formatAddress(proposer)}, Reward: ${reward} ETH`);
      } else {
        showStatus('✅ Block proposed!');
        logAction('Block Proposal', '✅ SUCCESS', 'Block confirmed');
      }
    } catch (e) {
      console.error('Block simulation error:', e);
      showStatus('❌ Simulation failed: ' + (e.reason || e.message));
      logAction('Block Proposal', '❌ FAILED', e.reason || e.message);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // Check missed attestations
  const handleCheckAttestations = async () => {
    setIsActionInProgress(true);
    logAction('Attestation Check', '⏳ STARTED', 'Scanning validators...');
    
    try {
      showStatus('🔍 Checking missed attestations...');
      const bankSigner = rpcClient.getBankSigner();
      if (!bankSigner) {
        showStatus('❌ Bank signer not initialized');
        logAction('Attestation Check', '❌ FAILED', 'Bank signer not initialized');
        return;
      }
      const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
      
      console.log('[Instructor] Sending attestation check transaction...');
      const tx = await contract.checkMissedAttestations();
      console.log('[Instructor] Attestation check TX sent:', tx.hash);
      logAction('Attestation Check', '📤 TX SENT', `Hash: ${tx.hash.slice(0, 18)}...`);
      
      const receipt = await tx.wait();
      console.log('[Instructor] Attestation check TX confirmed in block:', receipt.blockNumber);
      
      // Count penalty events
      const penaltyEvents = receipt.logs.filter(log => {
        try {
          const parsed = contract.interface.parseLog(log);
          return parsed.name === 'AttestationMissed';
        } catch { return false; }
      });
      
      showStatus('✅ Attestation check complete!');
      logAction('Attestation Check', '✅ SUCCESS', `${penaltyEvents.length} validators penalized`);
      console.log('[Instructor] Attestation check complete,', penaltyEvents.length, 'validators penalized');
    } catch (e) {
      console.error('Attestation check error:', e);
      showStatus('❌ Check failed: ' + (e.reason || e.message));
      logAction('Attestation Check', '❌ FAILED', e.reason || e.message);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // Advance epoch manually
  const handleAdvanceEpoch = async () => {
    setIsActionInProgress(true);
    logAction('Advance Epoch', '⏳ STARTED', `Current epoch: ${currentEpoch}`);
    
    try {
      showStatus('⏰ Advancing epoch...');
      const bankSigner = rpcClient.getBankSigner();
      if (!bankSigner) {
        showStatus('❌ Bank signer not initialized');
        logAction('Advance Epoch', '❌ FAILED', 'Bank signer not initialized');
        return;
      }
      const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
      
      console.log('[Instructor] Sending advance epoch transaction...');
      const tx = await contract.advanceEpoch();
      console.log('[Instructor] Advance epoch TX sent:', tx.hash);
      logAction('Advance Epoch', '📤 TX SENT', `Hash: ${tx.hash.slice(0, 18)}...`);
      
      const receipt = await tx.wait();
      console.log('[Instructor] Advance epoch TX confirmed in block:', receipt.blockNumber);
      
      showStatus('✅ Epoch advanced!');
      logAction('Advance Epoch', '✅ SUCCESS', `Now epoch ${currentEpoch + 1}`);
    } catch (e) {
      console.error('Epoch advance error:', e);
      showStatus('❌ Advance failed: ' + (e.reason || e.message));
      logAction('Advance Epoch', '❌ FAILED', e.reason || e.message);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // Send ETH to all students
  const resetStudentBalances = async () => {
    if (students.length === 0) {
      showStatus('⚠️ No students to fund');
      logAction('Fund Students', '⚠️ BLOCKED', 'No students found');
      return;
    }
    
    if (!confirm(`Send 5 ETH to all ${students.length} students?`)) {
      logAction('Fund Students', '❌ CANCELLED', 'User cancelled');
      return;
    }
    
    setIsActionInProgress(true);
    logAction('Fund Students', '⏳ STARTED', `Funding ${students.length} students...`);
    
    try {
      showStatus('💰 Sending ETH to students...');
      const bankSigner = rpcClient.getBankSigner();
      if (!bankSigner) {
        showStatus('❌ Bank signer not initialized');
        logAction('Fund Students', '❌ FAILED', 'Bank signer not initialized');
        return;
      }
      
      let funded = 0;
      for (const student of students) {
        console.log(`[Instructor] Sending 5 ETH to ${formatAddress(student.address)}...`);
        const tx = await bankSigner.sendTransaction({
          to: student.address,
          value: ethers.parseEther("5.0")
        });
        await tx.wait();
        funded++;
        showStatus(`💰 Funded ${funded}/${students.length} students...`);
      }
      
      showStatus(`✅ Sent 5 ETH to ${students.length} students!`);
      logAction('Fund Students', '✅ SUCCESS', `${funded} students received 5 ETH each`);
      console.log('[Instructor] Successfully funded', funded, 'students');
    } catch (e) {
      console.error("Reset error:", e);
      showStatus('❌ Failed: ' + e.message);
      logAction('Fund Students', '❌ FAILED', e.message);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // Send ETH to a single address (used by quick rewards)
  // Key roles per scenario — assigned first for even distribution (1 each of necessary roles)
  const SCENARIO_KEY_ROLES = {
    'House Sale': ['Admin', 'Seller', 'Buyer'],
    'Ransomware': ['Victim', 'Attacker', 'Investigator'],
    'Event Tickets': ['Organizer', 'Buyer'],
    'Voting': ['Admin', 'Voter'],
    'Crowdfunding': ['Creator', 'Contributor']
  };

  // Start scenario: broadcast via chat (frontend-only roles, no contract permissions needed)
  // Role pool: key roles first for even distribution, then extras. No shuffle — deterministic.
  const handleStartScenario = async () => {
    console.log('[Instructor] handleStartScenario called. activeScenario:', activeScenario);
    const roles = SCENARIO_ROLES[activeScenario]?.filter(r => r !== '') || [];
    if (roles.length === 0) {
      showStatus('⚠️ No roles for this scenario.');
      console.log('[Instructor] ABORT: no roles for', activeScenario);
      return;
    }
    const keyRoles = SCENARIO_KEY_ROLES[activeScenario] || [];
    const remaining = roles.filter(r => !keyRoles.includes(r));
    const rolePool = [...keyRoles, ...remaining];
    setIsActionInProgress(true);
    try {
      const bankSigner = rpcClient.getBankSigner();
      if (!bankSigner) {
        showStatus('❌ RPC not initialized. Set RPC URL in Account settings.');
        console.log('[Instructor] ABORT: bankSigner is null');
        return;
      }
      console.log('[Instructor] bankSigner:', await bankSigner.getAddress(), 'posAddress:', posAddress);
      const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
      const code = await rpcClient.getProvider().getCode(posAddress);
      if (!code || code === '0x' || code === '0x0') {
        showStatus('❌ No contract at this address.');
        console.log('[Instructor] ABORT: no contract code at', posAddress);
        return;
      }
      const msg = `[SCENARIO:${activeScenario}:${rolePool.join(',')}]`;
      console.log('[Instructor] Sending SCENARIO message:', msg);
      const tx = await contract.sendMessage(msg);
      console.log('[Instructor] TX sent:', tx.hash);
      const receipt = await tx.wait();
      console.log('[Instructor] TX confirmed block:', receipt.blockNumber, 'status:', receipt.status);
      showStatus(`✅ Scenario "${activeScenario}" started! Students will receive roles from chat.`);
      logAction('Start Scenario', '✅ SUCCESS', activeScenario);
    } catch (e) {
      console.error('[Instructor] Start scenario FAILED:', e);
      showStatus('❌ ' + (e.reason || e.message || String(e)));
      logAction('Start Scenario', '❌ FAILED', e.reason || e.message);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // Assign roles via chat: [ROLES:addr1:Role1;addr2:Role2;...] — students parse and set locally
  const handleAssignRandomRoles = async () => {
    console.log('[Instructor] handleAssignRandomRoles called. students:', students.length, 'activeScenario:', activeScenario);
    if (students.length === 0) {
      showStatus('⚠️ No participants yet. Students must join (stake or chat) first.');
      console.log('[Instructor] ABORT: no students');
      return;
    }
    const roles = SCENARIO_ROLES[activeScenario]?.filter(r => r !== '') || [];
    if (roles.length === 0) {
      showStatus('⚠️ No roles for this scenario. Select a scenario first.');
      console.log('[Instructor] ABORT: no roles for scenario', activeScenario, 'available:', Object.keys(SCENARIO_ROLES));
      return;
    }
    console.log('[Instructor] Roles for scenario:', roles);
    setIsActionInProgress(true);
    try {
      const bankSigner = rpcClient.getBankSigner();
      if (!bankSigner) {
        showStatus('❌ Bank signer not initialized. Check RPC connection.');
        console.log('[Instructor] ABORT: bankSigner is null');
        return;
      }
      console.log('[Instructor] bankSigner address:', await bankSigner.getAddress());
      const who = students.filter(s => s.address && ethers.isAddress(s.address)).map(s => s.address);
      console.log('[Instructor] Valid student addresses:', who);
      if (who.length === 0) {
        showStatus('⚠️ No valid addresses to assign.');
        return;
      }
      const keyRoles = SCENARIO_KEY_ROLES[activeScenario] || [];
      const remaining = roles.filter(r => !keyRoles.includes(r));
      const basePool = [...keyRoles, ...remaining];
      const shuffled = [...who];
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
      }
      const rolesToAssign = shuffled.map((_, i) => basePool[i % basePool.length]);
      const pairs = shuffled.map((addr, i) => `${addr}:${rolesToAssign[i]}`).join(';');
      const msg = `[ROLES:${pairs}]`;
      console.log('[Instructor] Sending ROLES message:', msg.slice(0, 200));
      console.log('[Instructor] Contract address:', posAddress);
      const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
      showStatus(`🎭 Assigning roles to ${who.length} participant(s)...`);
      const tx = await contract.sendMessage(msg);
      console.log('[Instructor] TX sent:', tx.hash);
      const receipt = await tx.wait();
      console.log('[Instructor] TX confirmed in block:', receipt.blockNumber, 'status:', receipt.status);
      showStatus(`✅ Roles assigned to ${who.length} participant(s)! TX: ${tx.hash.slice(0,10)}...`);
      logAction('Assign Roles', '✅ SUCCESS', `${who.length} assigned`);
    } catch (e) {
      console.error('[Instructor] Assign FAILED:', e);
      showStatus('❌ Assign failed: ' + (e.reason || e.message));
      logAction('Assign Roles', '❌ FAILED', e.reason || e.message);
    } finally {
      setIsActionInProgress(false);
    }
  };

  // ==================== RENDER ====================
  const beaconSnapshot = beaconCacheHealth?.snapshot || null;
  const beaconHealth = beaconSnapshot?.cache || {};
  const beaconCacheAge = beaconSnapshot?.ageMs;
  const beaconCacheStale = !!beaconHealth.stale;
  const beaconStatus = beaconCacheHealth?.error
    ? 'unreachable'
    : beaconSnapshot?.ok
      ? (beaconCacheStale ? 'stale' : 'online')
      : 'starting';
  const beaconPool = beaconSnapshot?.pool || {};
  const poolValidators = Array.isArray(beaconPool.validators) ? beaconPool.validators : [];
  const recentHumans = poolValidators.filter((v) => v.kind === 'human').slice(-8).reverse();
  const miningAutomine = miningState?.automine !== false;
  const arcadeOk = arcadeState?.ok === true;
  const arcadeAge = arcadeState?.ageMs == null ? 'not ready' : `${Math.round(Number(arcadeState.ageMs) / 1000)}s`;
  const arcadeCurrentPrice = arcadeState?.tokenPriceWei ? safeArcadeFormatEth(arcadeState.tokenPriceWei) : 'not configured';
  const arcadeHighScores = Object.values(arcadeState?.highScores || {})
    .filter((row) => row?.score)
    .sort((a, b) => Number(a.gameId || 0) - Number(b.gameId || 0));
  const defiRiskOk = defiRiskState?.ok === true;
  const defiRiskAge = defiRiskState?.ageMs == null ? 'not ready' : `${Math.round(Number(defiRiskState.ageMs) / 1000)}s`;
  const timelock = defiRiskState?.timelock || null;
  const defiContractCount = Object.entries(defiRiskState?.config || {})
    .filter(([key, value]) => key.endsWith('Address') && ethers.isAddress(String(value || '')))
    .length;

  return (
    <div className="instructor-dashboard">
      <h2>🎓 Instructor Dashboard</h2>
      
      {/* Status Messages */}
      {(isLoading || statusMessage) && (
        <div style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          background: statusMessage.includes('❌') ? '#ef4444' : '#3b82f6',
          color: 'white',
          padding: '0.75rem 1.25rem',
          borderRadius: '0.5rem',
          fontSize: '0.9rem',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
        }}>
          {statusMessage || 'Syncing...'}
        </div>
      )}
      
      {/* Instructor Controls */}
      <div style={{
        marginBottom: '20px', 
        padding: '20px', 
        background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)', 
        borderRadius: '12px',
        border: '2px solid #f59e0b'
      }}>
        <h3 style={{marginBottom: '15px', color: '#1e293b'}}>🎛️ Instructor Controls</h3>
        
        {/* Action Buttons */}
        <div style={{display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '15px'}}>
          {onOpenTerminal && (
            <button 
              onClick={onOpenTerminal}
              style={{
                padding: '12px 20px', 
                background: 'linear-gradient(135deg, #334155 0%, #1e293b 100%)', 
                color: 'white', 
                border: '1px solid #475569', 
                borderRadius: '8px', 
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '0.9rem'
              }}
            >
              🖥️ Lab Terminal
            </button>
          )}
          <button
            onClick={handleResetChain}
            disabled={isActionInProgress}
            style={{
              padding: '12px 20px',
              background: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: isActionInProgress ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
          >
            🔄 Reset Beacon Chain
          </button>
          <button
            onClick={handleToggleAutoBeaconActivity}
            disabled={isActionInProgress}
            title="Controls synthetic bot/demo Beacon traffic. Student transactions still work when paused."
            style={{
              padding: '12px 20px',
              background: autoBeaconActivity
                ? 'linear-gradient(135deg, #10b981 0%, #34d399 100%)'
                : 'linear-gradient(135deg, #64748b 0%, #94a3b8 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: isActionInProgress ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
          >
            {autoBeaconActivity ? '▶ Auto Beacon Activity: ON' : '⏸ Auto Beacon Activity: OFF'}
          </button>
          <button
            onClick={() => handleSetAutomine(!(miningState?.automine !== false))}
            disabled={isActionInProgress || !miningState}
            style={{
              padding: '12px 20px',
              background: miningState?.automine !== false
                ? 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)'
                : 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: (isActionInProgress || !miningState) ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
          >
            {miningState?.automine !== false ? '⚡ Automine: ON' : `⏱ Delayed Mining: ${miningState?.delayMs ?? 500}ms`}
          </button>
        </div>

        {/* Beacon cache health - confirms browsers are reading the shared cache instead of RPC */}
        <div style={{
          marginTop: '12px',
          padding: '12px 15px',
          background: beaconStatus === 'online' ? 'rgba(16, 185, 129, 0.16)' : beaconStatus === 'stale' ? 'rgba(245, 158, 11, 0.18)' : 'rgba(239, 68, 68, 0.16)',
          borderRadius: '8px',
          border: `1px solid ${beaconStatus === 'online' ? '#10b981' : beaconStatus === 'stale' ? '#f59e0b' : '#ef4444'}`
        }}>
          <div style={{display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap', alignItems: 'center'}}>
            <div>
              <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#1e293b'}}>
                Beacon cache: {beaconStatus}
              </div>
              <div style={{fontSize: '0.78rem', color: '#475569', marginTop: '3px'}}>
                Age {formatCacheMs(beaconCacheAge)} · poll every {formatCacheMs(beaconHealth.pollMs)} · last poll {formatCacheMs(beaconHealth.lastPollDurationMs)}
              </div>
            </div>
            <div style={{fontSize: '0.78rem', color: '#475569', textAlign: 'right'}}>
              Blocks {beaconSnapshot?.blocks?.length ?? 0} · errors {beaconHealth.errorCount ?? 0}
              {beaconHealth.lastError && (
                <div style={{color: '#991b1b', maxWidth: '420px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                  {beaconHealth.lastError}
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={{
          marginTop: '12px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '12px'
        }}>
          <div style={{
            padding: '12px 15px',
            background: 'rgba(14, 165, 233, 0.14)',
            borderRadius: '8px',
            border: '1px solid #0ea5e9'
          }}>
            <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#1e293b'}}>
              ⛏ Mining / mempool
            </div>
            <div style={{fontSize: '0.8rem', color: '#475569', marginTop: '6px', display: 'grid', gap: '3px'}}>
              <div>Mode: <strong>{miningState ? (miningAutomine ? 'automine' : `delayed ${miningState.delayMs ?? 500}ms`) : 'loading'}</strong></div>
              <div>Pending txs: <strong>{miningState?.pendingTransactionCount ?? 'n/a'}</strong></div>
              <div>Write queue: <strong>{miningState?.queue?.queuedMessages ?? 0}</strong> queued · <strong>{miningState?.queue?.activeMessages ?? 0}</strong> active</div>
              <div>Last mined: <strong>{miningState?.lastMinedBlock ?? 'n/a'}</strong> ({miningState?.lastMinedTxCount ?? 0} tx)</div>
              {miningState?.nextMineEtaMs != null && (
                <div>Next mine in: <strong>{Math.ceil(miningState.nextMineEtaMs)}ms</strong></div>
              )}
              {miningState?.lastPollError && (
                <div style={{color: '#991b1b'}}>Miner: {miningState.lastPollError}</div>
              )}
            </div>
          </div>

          <div style={{
            padding: '12px 15px',
            background: 'rgba(16, 185, 129, 0.14)',
            borderRadius: '8px',
            border: '1px solid #10b981'
          }}>
            <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#1e293b'}}>
              🧭 Beacon validator pool
            </div>
            <div style={{fontSize: '0.8rem', color: '#475569', marginTop: '6px', display: 'grid', gap: '3px'}}>
              <div>Pool: <strong>{beaconPool.size ?? 0}</strong> / {beaconPool.capacity ?? 0}</div>
              <div>Humans: <strong>{beaconPool.humans ?? 0}</strong> · Bots: <strong>{beaconPool.bots ?? 0}</strong></div>
              <div>Active: <strong>{beaconPool.active ?? 0}</strong> · Slashed: <strong>{beaconPool.slashed ?? 0}</strong> · Pending slash: <strong>{beaconPool.pendingSlashes ?? 0}</strong></div>
              {recentHumans.length > 0 ? (
                <div style={{display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '5px'}}>
                  {recentHumans.map((v) => (
                    <span key={v.address} style={{fontFamily: 'monospace', background: 'rgba(255,255,255,0.55)', padding: '2px 6px', borderRadius: '4px'}}>
                      {formatAddress(v.address)} · {Number(v.stake || 0).toFixed(1)} ETH
                    </span>
                  ))}
                </div>
              ) : (
                <div>No human validators seated yet.</div>
              )}
            </div>
          </div>

          <div style={{
            padding: '12px 15px',
            background: 'rgba(20, 83, 45, 0.14)',
            borderRadius: '8px',
            border: arcadeOk ? '1px solid #22c55e' : '1px solid #ef4444'
          }}>
            <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#1e293b'}}>
              🕹 FT Arcade token sale
            </div>
            <div style={{fontSize: '0.8rem', color: '#475569', marginTop: '6px', display: 'grid', gap: '5px'}}>
              <div>Cache: <strong>{arcadeOk ? 'online' : (arcadeState?.reason || 'loading')}</strong> · age <strong>{arcadeAge}</strong></div>
              <div>Price: <strong>{arcadeCurrentPrice}</strong> per ARC</div>
              <div>Total supply: <strong>{safeArcadeFormatEth(arcadeState?.totalSupply).replace(' ETH', ' ARC')}</strong></div>
              <div>Treasury: <strong style={{fontFamily: 'monospace'}}>{shortAddress(arcadeState?.treasury)}</strong></div>
              <div>Recent buys: <strong>{arcadeState?.recentBuys?.length || 0}</strong> · recent burns: <strong>{arcadeState?.recentSessions?.length || 0}</strong> · recent scores: <strong>{arcadeState?.recentScores?.length || 0}</strong></div>
              <div style={{marginTop: '3px'}}>
                <strong>High scores:</strong>
                {arcadeHighScores.length === 0 ? (
                  <span> none yet</span>
                ) : (
                  <div style={{display: 'grid', gap: '4px', marginTop: '4px'}}>
                    {arcadeHighScores.map((row) => (
                      <div key={`${row.gameId}-${row.player}-${row.nonce}`} style={{display: 'grid', gridTemplateColumns: '1fr auto', gap: '8px', padding: '5px 7px', background: 'rgba(255,255,255,0.5)', borderRadius: '6px'}}>
                        <span>{ARCADE_GAME_NAMES[row.gameId] || `Game ${row.gameId}`} · {shortAddress(row.player)}</span>
                        <strong>{safeScore(row.score)} / {safeElapsed(row.elapsedMs)}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div style={{display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap', marginTop: '4px'}}>
                <input
                  type="number"
                  min="0.0001"
                  step="0.1"
                  value={arcadePriceInput}
                  onChange={(event) => {
                    setArcadePriceInput(event.target.value);
                    setArcadePriceDirty(true);
                  }}
                  placeholder="50"
                  style={{
                    width: '90px',
                    padding: '7px 9px',
                    borderRadius: '6px',
                    border: '1px solid #334155',
                    fontSize: '0.85rem'
                  }}
                />
                <span>ETH per ARC</span>
                <button
                  onClick={handleSetArcadePrice}
                  disabled={isActionInProgress || !arcadePriceInput}
                  style={{
                    padding: '7px 12px',
                    background: (isActionInProgress || !arcadePriceInput) ? '#94a3b8' : '#16a34a',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: (isActionInProgress || !arcadePriceInput) ? 'not-allowed' : 'pointer',
                    fontWeight: 'bold',
                    fontSize: '0.8rem'
                  }}
                >
                  Update price
                </button>
	              </div>
	            </div>
	          </div>

	          <div style={{
	            padding: '12px 15px',
	            background: 'rgba(127, 29, 29, 0.12)',
	            borderRadius: '8px',
	            border: defiRiskOk ? '1px solid #dc2626' : '1px solid #ef4444'
	          }}>
	            <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#1e293b'}}>
	              🧪 DeFi Risk Garden
	            </div>
	            <div style={{fontSize: '0.8rem', color: '#475569', marginTop: '6px', display: 'grid', gap: '5px'}}>
	              <div>Cache: <strong>{defiRiskOk ? 'online' : (defiRiskState?.reason || defiRiskState?.error || 'loading')}</strong> · age <strong>{defiRiskAge}</strong></div>
	              <div>Known contracts: <strong>{defiContractCount}</strong> / 7</div>
	              {timelock?.address ? (
	                <>
	                  <div>TimelockRugVault: <strong style={{fontFamily: 'monospace'}}>{shortAddress(timelock.address)}</strong></div>
	                  <div>Owner: <strong style={{fontFamily: 'monospace'}}>{shortAddress(timelock.owner)}</strong></div>
	                  <div>Total assets: <strong>{safeArcadeFormatEth(timelock.totalAssets)}</strong></div>
	                  <div>Status: <strong>{timelock.paused ? 'paused' : 'withdrawals enabled'}</strong></div>
	                  <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px'}}>
	                    <button
	                      onClick={() => postTimelockUpdate({ paused: !timelock.paused }, timelock.paused ? 'unpause' : 'pause')}
	                      disabled={isActionInProgress}
	                      style={{
	                        padding: '7px 12px',
	                        background: isActionInProgress ? '#94a3b8' : (timelock.paused ? '#16a34a' : '#dc2626'),
	                        color: 'white',
	                        border: 'none',
	                        borderRadius: '6px',
	                        cursor: isActionInProgress ? 'not-allowed' : 'pointer',
	                        fontWeight: 'bold',
	                        fontSize: '0.8rem'
	                      }}
	                    >
	                      {timelock.paused ? 'Unpause withdrawals' : 'Pause withdrawals'}
	                    </button>
	                  </div>
	                  <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '8px', marginTop: '5px'}}>
	                    <label style={{display: 'grid', gap: '3px'}}>
	                      <span>Fee bps</span>
	                      <input
	                        type="number"
	                        min="0"
	                        max="9000"
	                        step="1"
	                        value={timelockFeeInput}
	                        onChange={(event) => {
	                          setTimelockFeeInput(event.target.value);
	                          setTimelockFormDirty(true);
	                        }}
	                        style={{padding: '7px 9px', borderRadius: '6px', border: '1px solid #334155'}}
	                      />
	                    </label>
	                    <label style={{display: 'grid', gap: '3px'}}>
	                      <span>Unlock delay seconds</span>
	                      <input
	                        type="number"
	                        min="0"
	                        step="1"
	                        value={timelockDelayInput}
	                        onChange={(event) => {
	                          setTimelockDelayInput(event.target.value);
	                          setTimelockFormDirty(true);
	                        }}
	                        style={{padding: '7px 9px', borderRadius: '6px', border: '1px solid #334155'}}
	                      />
	                    </label>
	                  </div>
	                  <label style={{display: 'grid', gap: '3px', marginTop: '5px'}}>
	                    <span>Treasury</span>
	                    <input
	                      value={timelockTreasuryInput}
	                      onChange={(event) => {
	                        setTimelockTreasuryInput(event.target.value);
	                        setTimelockFormDirty(true);
	                      }}
	                      placeholder="0x..."
	                      style={{
	                        padding: '7px 9px',
	                        borderRadius: '6px',
	                        border: '1px solid #334155',
	                        fontFamily: 'monospace',
	                        fontSize: '0.78rem'
	                      }}
	                    />
	                  </label>
	                  <button
	                    onClick={handleSaveTimelockSettings}
	                    disabled={isActionInProgress || !timelockFormDirty}
	                    style={{
	                      width: 'fit-content',
	                      padding: '7px 12px',
	                      background: (isActionInProgress || !timelockFormDirty) ? '#94a3b8' : '#7f1d1d',
	                      color: 'white',
	                      border: 'none',
	                      borderRadius: '6px',
	                      cursor: (isActionInProgress || !timelockFormDirty) ? 'not-allowed' : 'pointer',
	                      fontWeight: 'bold',
	                      fontSize: '0.8rem'
	                    }}
	                  >
	                    Save timelock settings
	                  </button>
	                </>
	              ) : (
	                <div>{defiRiskState?.reason || 'TimelockRugVault is not configured yet.'}</div>
	              )}
	            </div>
	          </div>
	        </div>

        <MempoolTable
          title="Pending transaction pool"
          subtitle="Instructor view of the cached mempool mirror. Browser reads never touch the RPC port."
          tone="light"
          maxPendingRows={16}
          maxRecentRows={10}
        />
        
        {/* Student fund requests - students click "Request funds" to notify instructor */}
        {fundRequests.length > 0 && (
          <div style={{
            marginTop: '12px',
            padding: '12px 15px',
            background: 'rgba(59, 130, 246, 0.2)',
            borderRadius: '8px',
            border: '1px solid #3b82f6'
          }}>
            <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '8px'}}>
              📤 Fund requests ({fundRequests.length})
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '160px', overflowY: 'auto'}}>
              {fundRequests.slice(0, 10).map((req) => (
                <div key={req.id} style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '6px 10px',
                  background: 'rgba(255,255,255,0.5)',
                  borderRadius: '6px',
                  fontSize: '0.8rem'
                }}>
                  <span style={{fontFamily: 'monospace'}}>{req.address.slice(0, 10)}...{req.address.slice(-8)}</span>
                  {req.nickname && <span style={{color: '#64748b'}}>({req.nickname})</span>}
                  <div style={{display: 'flex', gap: '6px', alignItems: 'center'}}>
                    <button
                      onClick={async () => {
                        setFundAddress(req.address);
                        await depositToWallet(req.address, fundAmount || '5', req.id);
                      }}
                      disabled={isActionInProgress}
                      style={{
                        padding: '4px 10px',
                        background: '#10b981',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: isActionInProgress ? 'not-allowed' : 'pointer',
                        fontSize: '0.75rem'
                      }}
                    >
                      Fund {fundAmount || 5} ETH
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          await fetch(import.meta.env.BASE_URL + `lab-api/fund-request/${req.id}`, { method: 'DELETE' });
                          setFundRequests(prev => prev.filter(r => r.id !== req.id));
                          showStatus('Request denied');
                        } catch (e) {
                          showStatus('❌ ' + (e.message || e.reason));
                        }
                      }}
                      disabled={isActionInProgress}
                      style={{
                        padding: '4px 10px',
                        background: '#64748b',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: isActionInProgress ? 'not-allowed' : 'pointer',
                        fontSize: '0.75rem'
                      }}
                    >
                      Deny
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fund by address - for students who haven't joined yet (no gas to interact) */}
        <div style={{
          marginTop: '12px',
          padding: '12px 15px',
          background: 'rgba(16, 185, 129, 0.15)',
          borderRadius: '8px',
          border: '1px solid #10b981'
        }}>
          <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#1e293b', marginBottom: '8px'}}>
            💸 Fund by address (students with 0 ETH can't join — fund them first)
          </div>
          <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center'}}>
            <input
              placeholder="0x... (paste student address)"
              value={fundAddress}
              onChange={e => setFundAddress(e.target.value)}
              style={{
                flex: 1,
                minWidth: '200px',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #334155',
                fontFamily: 'monospace',
                fontSize: '0.85rem'
              }}
            />
            <input
              type="number"
              step="0.1"
              min="0.1"
              placeholder="ETH"
              value={fundAmount}
              onChange={e => setFundAmount(e.target.value)}
              style={{
                width: '70px',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #334155'
              }}
            />
            <button
              onClick={() => depositToWallet(fundAddress, fundAmount)}
              disabled={isActionInProgress || !fundAddress}
              style={{
                padding: '8px 16px',
                background: (isActionInProgress || !fundAddress) ? '#94a3b8' : '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: (isActionInProgress || !fundAddress) ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                fontSize: '0.85rem'
              }}
            >
              Fund
            </button>
          </div>
        </div>
        
        <p style={{fontSize: '12px', color: '#475569'}}>
          <strong>Note:</strong> Slashing and attestation penalties affect validator stakes. Block proposals demonstrate weighted random selection.
          In real Ethereum, validators attest in committees of ~128. Unbonding: 60s (real: ~27h). Min stake: 1 ETH (real: 32 ETH).
        </p>
        
        {/* Action Log Panel */}
        <div style={{
          marginTop: '15px',
          background: '#1e293b',
          borderRadius: '8px',
          border: '1px solid #334155',
          maxHeight: '200px',
          overflowY: 'auto'
        }}>
          <div style={{
            padding: '8px 12px',
            background: '#334155',
            borderBottom: '1px solid #475569',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span style={{fontWeight: 'bold', fontSize: '0.85rem', color: '#e2e8f0'}}>
              📋 Action Log {isActionInProgress && <span style={{color: '#fbbf24', marginLeft: '8px'}}>⏳ Processing...</span>}
            </span>
            <button 
              onClick={() => setActionLog([])}
              style={{
                padding: '4px 8px',
                background: '#475569',
                border: 'none',
                borderRadius: '4px',
                color: '#94a3b8',
                fontSize: '0.7rem',
                cursor: 'pointer'
              }}
            >
              Clear
            </button>
          </div>
          <div style={{padding: '8px'}}>
            {actionLog.length === 0 ? (
              <div style={{color: '#64748b', fontSize: '0.8rem', textAlign: 'center', padding: '10px'}}>
                No actions yet. Click a button above to see the log.
              </div>
            ) : (
              actionLog.map((entry, idx) => (
                <div 
                  key={idx} 
                  style={{
                    padding: '6px 8px',
                    borderBottom: idx < actionLog.length - 1 ? '1px solid #334155' : 'none',
                    fontSize: '0.8rem',
                    display: 'flex',
                    gap: '10px',
                    alignItems: 'flex-start'
                  }}
                >
                  <span style={{color: '#64748b', minWidth: '70px', fontFamily: 'monospace'}}>
                    {entry.timestamp}
                  </span>
                  <span style={{
                    color: entry.status.includes('SUCCESS') ? '#34d399' : 
                           entry.status.includes('FAILED') ? '#ef4444' : 
                           entry.status.includes('STARTED') ? '#fbbf24' :
                           entry.status.includes('TX SENT') ? '#22d3ee' : '#94a3b8',
                    fontWeight: 'bold',
                    minWidth: '80px'
                  }}>
                    {entry.status}
                  </span>
                  <span style={{color: '#e2e8f0', flex: 1}}>
                    <strong>{entry.action}</strong>
                    {entry.details && <span style={{color: '#94a3b8', marginLeft: '8px'}}>{entry.details}</span>}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      
      {/* Network Stats */}
      <div className="instructor-stats" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '15px',
        marginBottom: '20px'
      }}>
        <div className="stat-card" style={{background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', padding: '15px', borderRadius: '10px', textAlign: 'center'}}>
          <div style={{fontSize: '0.8rem', color: '#94a3b8', marginBottom: '5px'}}>Active Validators</div>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#22d3ee'}}>{validatorCount}</div>
        </div>
        <div className="stat-card" style={{background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', padding: '15px', borderRadius: '10px', textAlign: 'center'}}>
          <div style={{fontSize: '0.8rem', color: '#94a3b8', marginBottom: '5px'}}>Total Staked</div>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#a78bfa'}}>{parseFloat(totalStaked).toFixed(2)} ETH</div>
        </div>
        <div className="stat-card" style={{background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', padding: '15px', borderRadius: '10px', textAlign: 'center'}}>
          <div style={{fontSize: '0.8rem', color: '#94a3b8', marginBottom: '5px'}}>Contract Balance</div>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#34d399'}}>{parseFloat(contractBalance).toFixed(2)} ETH</div>
        </div>
        <div className="stat-card" style={{background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', padding: '15px', borderRadius: '10px', textAlign: 'center'}}>
          <div style={{fontSize: '0.8rem', color: '#94a3b8', marginBottom: '5px'}}>Current APY</div>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#fbbf24'}}>{currentAPY.toFixed(2)}%</div>
        </div>
        <div className="stat-card" style={{background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', padding: '15px', borderRadius: '10px', textAlign: 'center'}}>
          <div style={{fontSize: '0.8rem', color: '#94a3b8', marginBottom: '5px'}}>Epoch / Slot</div>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#f472b6'}}>{currentEpoch} / {currentSlot}</div>
          <div style={{fontSize: '0.65rem', color: '#64748b'}}>of 8 slots</div>
        </div>
        <div className="stat-card" style={{background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', padding: '15px', borderRadius: '10px', textAlign: 'center'}}>
          <div style={{fontSize: '0.8rem', color: '#94a3b8', marginBottom: '5px'}}>Participation</div>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: participationRate >= 66 ? '#34d399' : participationRate >= 33 ? '#fbbf24' : '#ef4444'}}>{participationRate}%</div>
          <div style={{fontSize: '0.65rem', color: '#64748b'}}>attested</div>
        </div>
        <div className="stat-card" style={{background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', padding: '15px', borderRadius: '10px', textAlign: 'center'}}>
          <div style={{fontSize: '0.8rem', color: '#94a3b8', marginBottom: '5px'}}>Next Epoch</div>
          <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#38bdf8'}}>{timeUntilNextEpoch}s</div>
        </div>
      </div>
      
      {/* Student Table */}
      <div style={{marginBottom: '20px', overflowX: 'auto'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '15px'}}>
          <h3 style={{margin: 0}}>📊 Validator Activity</h3>
          <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap'}}>
            <button
              onClick={exportProgressCSV}
              style={{padding: '6px 12px', background: '#10b981', border: 'none', borderRadius: '6px', color: 'white', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 'bold'}}
            >
              Export CSV
            </button>
          </div>
        </div>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          background: '#1e293b',
          borderRadius: '10px',
          overflow: 'hidden'
        }}>
          <thead>
            <tr style={{background: '#334155'}}>
              <th style={{padding: '12px', textAlign: 'left', color: '#94a3b8', fontSize: '0.8rem'}}>#</th>
              <th style={{padding: '12px', textAlign: 'left', color: '#94a3b8', fontSize: '0.8rem'}}>Address</th>
              <th style={{padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '0.8rem'}}>Staked</th>
              <th style={{padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem'}}>Blocks</th>
              <th style={{padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem'}}>Slashes</th>
              <th style={{padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem'}}>Missed</th>
            </tr>
          </thead>
          <tbody>
            {filteredStudents.map((student, idx) => (
              <tr 
                key={student.address} 
                style={{
                  borderBottom: '1px solid #334155'
                }}
              >
                <td style={{padding: '12px', color: '#e2e8f0'}}>{idx + 1}</td>
                <td style={{padding: '12px'}}>
                  <span 
                    style={{color: '#22d3ee', fontFamily: 'monospace', cursor: 'pointer'}}
                    onClick={() => navigator.clipboard.writeText(student.address)}
                    title={student.address}
                  >
                    {formatAddress(student.address)}
                  </span>
                  {student.unbondingTime > 0 && student.unbondingTime < 9999999999 && (
                    <span style={{marginLeft: '8px', fontSize: '0.75rem', color: '#fbbf24'}}>
                      ⏳ {student.unbondingTime}s
                    </span>
                  )}
                </td>
                <td style={{
                  padding: '12px', 
                  textAlign: 'right', 
                  color: parseFloat(student.stake) > 0 ? '#a78bfa' : '#64748b',
                  fontWeight: parseFloat(student.stake) > 0 ? 'bold' : 'normal'
                }}>
                  {parseFloat(student.stake).toFixed(3)}
                </td>
                <td style={{padding: '12px', textAlign: 'center', color: '#8b5cf6', fontWeight: 'bold'}}>
                  {student.blocksProposed}
                </td>
                <td style={{
                  padding: '12px', 
                  textAlign: 'center', 
                  color: student.slashCount > 0 ? '#ef4444' : '#64748b',
                  fontWeight: student.slashCount > 0 ? 'bold' : 'normal'
                }}>
                  {student.slashCount}
                </td>
                <td style={{
                  padding: '12px', 
                  textAlign: 'center', 
                  color: student.missedAttestations > 0 ? '#f59e0b' : '#64748b'
                }}>
                  {student.missedAttestations}
                </td>
              </tr>
            ))}
            {filteredStudents.length === 0 && (
              <tr>
                <td colSpan="6" style={{padding: '30px', textAlign: 'center', color: '#64748b'}}>
                  {students.length === 0 ? 'Waiting for students to stake...' : 'No students match filter'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {/* Recent Activity Feed */}
      <div style={{marginBottom: '20px'}}>
        <h3 style={{marginBottom: '15px'}}>🔄 Recent Activity</h3>
        <div style={{
          background: '#1e293b',
          borderRadius: '10px',
          padding: '15px',
          maxHeight: '400px',
          overflowY: 'auto'
        }}>
          {recentActivity.map((event, idx) => (
            <div 
              key={idx} 
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px',
                borderBottom: idx < recentActivity.length - 1 ? '1px solid #334155' : 'none',
                background: event.type === 'slash' ? 'rgba(239, 68, 68, 0.1)' : 
                           event.type === 'block' ? 'rgba(139, 92, 246, 0.1)' : 'transparent'
              }}
            >
              <span style={{fontSize: '1.25rem'}}>{getActivityIcon(event.type)}</span>
              <span style={{color: '#22d3ee', fontFamily: 'monospace', minWidth: '100px'}}>
                {formatAddress(event.address)}
              </span>
              <span style={{flex: 1, color: '#e2e8f0', fontSize: '0.9rem'}}>
                {event.type === 'stake' && `Staked ${parseFloat(event.amount).toFixed(2)} ETH`}
                {event.type === 'withdraw' && `Withdrew ${parseFloat(event.amount).toFixed(2)} ETH (+${parseFloat(event.reward).toFixed(4)} reward)`}
                {event.type === 'message' && `"${event.message?.slice(0, 40)}${event.message?.length > 40 ? '...' : ''}"`}
                {event.type === 'slash' && <span style={{color: '#ef4444'}}>Slashed {parseFloat(event.amount).toFixed(4)} ETH - "{event.reason}"</span>}
                {event.type === 'block' && <span style={{color: '#a78bfa'}}>Proposed block #{event.blockNumber}</span>}
              </span>
              <span style={{color: '#64748b', fontSize: '0.8rem'}}>
                Block #{event.block}
              </span>
            </div>
          ))}
          {recentActivity.length === 0 && (
            <div style={{padding: '20px', textAlign: 'center', color: '#64748b'}}>
              No activity yet...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default InstructorView;
