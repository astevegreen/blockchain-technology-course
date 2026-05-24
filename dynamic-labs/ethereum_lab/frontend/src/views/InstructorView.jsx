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
import PoSABI from '../PoS.json';
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
  const [fundAmount, setFundAmount] = useState('5');
  const [artifactInput, setArtifactInput] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterHasContract, setFilterHasContract] = useState('');
  const [fundRequests, setFundRequests] = useState([]);

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

  // Filter students by role and contract status
  const filteredStudents = students.filter((s) => {
    if (filterRole && (s.role || '') !== filterRole) return false;
    if (filterHasContract === 'yes' && !s.roleContract) return false;
    if (filterHasContract === 'no' && s.roleContract) return false;
    return true;
  });

  // Export progress to CSV
  const exportProgressCSV = () => {
    const headers = ['Address', 'Role', 'Balance', 'Staked', 'Rewards', 'Role Contract', 'Blocks', 'Slashes', 'Attested'];
    const rows = filteredStudents.map((s) => [
      s.address,
      s.role || '',
      s.balance,
      s.stake,
      s.reward,
      s.roleContract || '',
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
            onClick={handleSimulateBlock}
            style={{
              padding: '12px 20px', 
              background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '8px', 
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
          >
            📦 Propose Block
          </button>
          <button 
            onClick={handleCheckAttestations}
            style={{
              padding: '12px 20px', 
              background: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '8px', 
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
          >
            🔍 Check Attestations
          </button>
          <button 
            onClick={handleAdvanceEpoch}
            disabled={timeUntilNextEpoch > 0}
            style={{
              padding: '12px 20px', 
              background: timeUntilNextEpoch > 0 ? '#94a3b8' : 'linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '8px', 
              cursor: timeUntilNextEpoch > 0 ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
          >
            ⏰ Advance Epoch {timeUntilNextEpoch > 0 ? `(${timeUntilNextEpoch}s)` : ''}
          </button>
          <button 
            onClick={resetStudentBalances}
            style={{
              padding: '12px 20px', 
              background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '8px', 
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}
          >
            💰 Fund All Students
          </button>
        </div>
        
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
                        try {
                          setIsActionInProgress(true);
                          const bankSigner = rpcClient.getBankSigner();
                          if (!bankSigner) return;
                          const amt = parseFloat(fundAmount) || 5;
                          const tx = await bankSigner.sendTransaction({
                            to: req.address,
                            value: ethers.parseEther(String(amt))
                          });
                          await tx.wait();
                          showStatus(`✅ Sent ${amt} ETH to ${req.nickname || req.address.slice(0, 10)}...`);
                          await fetch(import.meta.env.BASE_URL + `lab-api/fund-request/${req.id}`, { method: 'DELETE' });
                          setFundRequests(prev => prev.filter(r => r.id !== req.id));
                        } catch (e) {
                          showStatus('❌ ' + (e.message || e.reason));
                        } finally {
                          setIsActionInProgress(false);
                        }
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
              onClick={async () => {
                if (!fundAddress || !ethers.isAddress(fundAddress)) {
                  showStatus('❌ Enter valid address');
                  return;
                }
                const amt = parseFloat(fundAmount);
                if (isNaN(amt) || amt <= 0) {
                  showStatus('❌ Enter valid amount');
                  return;
                }
                try {
                  setIsActionInProgress(true);
                  const bankSigner = rpcClient.getBankSigner();
                  if (!bankSigner) {
                    showStatus('❌ Bank signer not initialized');
                    return;
                  }
                  const tx = await bankSigner.sendTransaction({
                    to: fundAddress,
                    value: ethers.parseEther(String(amt))
                  });
                  await tx.wait();
                  showStatus(`✅ Sent ${amt} ETH to ${formatAddress(fundAddress)}`);
                  setFundAddress('');
                  logAction('Fund by Address', '✅ SUCCESS', `${amt} ETH → ${formatAddress(fundAddress)}`);
                } catch (e) {
                  showStatus('❌ ' + (e.message || e.reason));
                } finally {
                  setIsActionInProgress(false);
                }
              }}
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
      
      {/* Scenario & Role Assignment */}
      <div style={{marginBottom: '15px', padding: '12px 15px', background: 'rgba(30, 41, 59, 0.8)', borderRadius: '8px', border: '1px solid #475569'}}>
        <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px'}}>
          🎭 Scenario & Auto-Assign
        </div>
        <div style={{display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap'}}>
          <label style={{color: '#94a3b8', fontSize: '0.9rem'}}>
            Scenario:
            <select
              value={activeScenario}
              onChange={e => setActiveScenario(e.target.value)}
              style={{
                marginLeft: '8px',
                padding: '8px 12px',
                background: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '6px',
                color: '#e2e8f0',
                fontSize: '0.9rem'
              }}
            >
              {Object.keys(SCENARIO_ROLES).map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
          <button
            onClick={handleStartScenario}
            disabled={isActionInProgress}
            style={{
              padding: '8px 16px',
              background: isActionInProgress ? '#475569' : 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isActionInProgress ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '0.85rem'
            }}
          >
            ▶ Start Scenario
          </button>
          <button
            onClick={handleAssignRandomRoles}
            disabled={isActionInProgress || students.length === 0}
            style={{
              padding: '8px 16px',
              background: (isActionInProgress || students.length === 0) ? '#475569' : 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: (isActionInProgress || students.length === 0) ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '0.85rem'
            }}
          >
            🎲 Assign Unassigned
          </button>
        </div>
        <div style={{fontSize: '0.8rem', color: '#64748b', marginTop: '8px'}}>
          <strong>Start Scenario</strong> broadcasts roles; new joiners get roles automatically by sorted address (key roles first for even distribution). <strong>Assign Unassigned</strong> assigns roles to current participants who joined before you started. Students join by connecting wallet (auto) or sending a chat message.
        </div>
      </div>
      
      {/* Post scenario artifact (clues for students to investigate) */}
      <div style={{
        marginBottom: '15px',
        padding: '12px 15px',
        background: 'rgba(30, 41, 59, 0.8)',
        borderRadius: '8px',
        border: '1px solid #475569'
      }}>
        <div style={{fontSize: '0.85rem', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px'}}>
          📂 Post artifact (clue for scenario)
        </div>
        <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
          <input
            placeholder="e.g. Ledger excerpt: payment 0.5 ETH to 0x… at block 42."
            value={artifactInput}
            onChange={e => setArtifactInput(e.target.value)}
            style={{
              flex: 1,
              minWidth: '250px',
              padding: '8px 12px',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '6px',
              color: '#e2e8f0',
              fontSize: '0.9rem'
            }}
          />
          <button
            onClick={async () => {
              if (!artifactInput.trim()) return;
              const msg = `[ARTIFACT:${artifactInput.trim()}]`;
              try {
                setIsActionInProgress(true);
                const bankSigner = rpcClient.getBankSigner();
                if (!bankSigner) { showStatus('❌ Bank signer not initialized'); return; }
                const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
                const tx = await contract.sendMessage(msg);
                await tx.wait();
                showStatus('✅ Artifact posted. Students see it in Evidence section.');
                setArtifactInput('');
              } catch (e) {
                showStatus('❌ ' + (e.reason || e.message));
              } finally {
                setIsActionInProgress(false);
              }
            }}
            disabled={isActionInProgress || !artifactInput.trim()}
            style={{
              padding: '8px 16px',
              background: (isActionInProgress || !artifactInput.trim()) ? '#475569' : '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: (isActionInProgress || !artifactInput.trim()) ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '0.85rem'
            }}
          >
            Post
          </button>
        </div>
        <div style={{fontSize: '0.75rem', color: '#64748b', marginTop: '6px'}}>
          Students see artifacts in Evidence section. Make clues tricky—inconsistencies help buyers/investigators.
        </div>
      </div>
      
      {/* Student Table */}
      <div style={{marginBottom: '20px', overflowX: 'auto'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '15px'}}>
          <h3 style={{margin: 0}}>📊 Validator Activity</h3>
          <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap'}}>
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              style={{padding: '6px 10px', background: '#1e293b', border: '1px solid #475569', borderRadius: '6px', color: '#e2e8f0', fontSize: '0.85rem'}}
            >
              <option value="">All roles</option>
              {Object.values(SCENARIO_ROLES).flat().filter(Boolean).filter((v, i, a) => a.indexOf(v) === i).map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            <select
              value={filterHasContract}
              onChange={(e) => setFilterHasContract(e.target.value)}
              style={{padding: '6px 10px', background: '#1e293b', border: '1px solid #475569', borderRadius: '6px', color: '#e2e8f0', fontSize: '0.85rem'}}
            >
              <option value="">All</option>
              <option value="yes">Has contract</option>
              <option value="no">No contract</option>
            </select>
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
              <th style={{padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '0.8rem'}}>Balance</th>
              <th style={{padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '0.8rem'}}>Staked</th>
              <th style={{padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '0.8rem'}}>Rewards</th>
              <th style={{padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem'}}>Blocks</th>
              <th style={{padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem'}}>Slashes</th>
              <th style={{padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem'}}>Missed</th>
              <th style={{padding: '12px', textAlign: 'left', color: '#94a3b8', fontSize: '0.8rem'}}>Role</th>
              <th style={{padding: '12px', textAlign: 'left', color: '#94a3b8', fontSize: '0.8rem'}}>Contract</th>
              <th style={{padding: '12px', textAlign: 'left', color: '#94a3b8', fontSize: '0.8rem'}}>Progress</th>
              <th style={{padding: '12px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem'}}>Actions</th>
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
                <td style={{padding: '12px', textAlign: 'right', color: '#e2e8f0'}}>
                  {parseFloat(student.balance).toFixed(3)}
                </td>
                <td style={{
                  padding: '12px', 
                  textAlign: 'right', 
                  color: parseFloat(student.stake) > 0 ? '#a78bfa' : '#64748b',
                  fontWeight: parseFloat(student.stake) > 0 ? 'bold' : 'normal'
                }}>
                  {parseFloat(student.stake).toFixed(3)}
                </td>
                <td style={{padding: '12px', textAlign: 'right', color: '#34d399'}}>
                  +{parseFloat(student.reward).toFixed(6)}
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
                <td style={{padding: '12px'}}>
                  <select
                    value={student.role || ''}
                    onChange={async (e) => {
                      const role = e.target.value;
                      if (!role) return;
                      try {
                        setIsActionInProgress(true);
                        const bankSigner = rpcClient.getBankSigner();
                        if (!bankSigner) return;
                        const contract = new ethers.Contract(posAddress, PoSABI, bankSigner);
                        const tx = await contract.setRole(student.address, role);
                        await tx.wait();
                        setStatusMessage(`✅ Role "${role}" assigned`);
                        setTimeout(() => setStatusMessage(''), 3000);
                      } catch (err) {
                        setStatusMessage('❌ ' + (err.reason || err.message));
                      } finally {
                        setIsActionInProgress(false);
                      }
                    }}
                    style={{
                      padding: '4px 8px',
                      background: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '4px',
                      color: '#e2e8f0',
                      fontSize: '0.8rem',
                      minWidth: '140px'
                    }}
                  >
                    {SCENARIO_ROLES[activeScenario].map(r => (
                      <option key={r || 'none'} value={r}>{r || '(none)'}</option>
                    ))}
                  </select>
                </td>
                <td style={{padding: '12px', fontSize: '0.8rem'}}>
                  {student.roleContract ? (
                    <span 
                      style={{color: '#34d399', fontFamily: 'monospace', cursor: 'pointer'}}
                      onClick={() => navigator.clipboard.writeText(student.roleContract)}
                      title={student.roleContract}
                    >
                      ✓ {student.roleContract.slice(0, 10)}...
                    </span>
                  ) : (
                    <span style={{color: '#64748b'}}>—</span>
                  )}
                </td>
                <td style={{padding: '12px', fontSize: '0.8rem'}}>
                  {student.roleContract ? (
                    <span style={{color: '#34d399'}}>✓ Deployed</span>
                  ) : (
                    <span style={{color: '#64748b'}}>—</span>
                  )}
                </td>
                <td style={{padding: '12px', textAlign: 'center'}}>
                  {parseFloat(student.stake) > 0 && (
                    <button
                      onClick={() => setSelectedStudent(selectedStudent === student.address ? null : student.address)}
                      style={{
                        padding: '6px 12px',
                        background: selectedStudent === student.address ? '#ef4444' : '#475569',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.8rem'
                      }}
                    >
                      ⚡ Slash
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {filteredStudents.length === 0 && (
              <tr>
                <td colSpan="12" style={{padding: '30px', textAlign: 'center', color: '#64748b'}}>
                  {students.length === 0 ? 'Waiting for students to stake...' : 'No students match filter'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
        
        {/* Slash Input Panel */}
        {selectedStudent && (
          <div style={{
            marginTop: '15px',
            padding: '15px',
            background: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
            borderRadius: '10px',
            border: '2px solid #ef4444'
          }}>
            <div style={{marginBottom: '10px', color: '#fecaca'}}>
              ⚡ Slashing {formatAddress(selectedStudent)} - Enter reason:
            </div>
            <div style={{display: 'flex', gap: '10px'}}>
              <input
                type="text"
                value={slashReason}
                onChange={(e) => setSlashReason(e.target.value)}
                placeholder="e.g., Double signing, being offline, misbehavior..."
                style={{
                  flex: 1,
                  padding: '10px',
                  background: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '6px',
                  color: '#e2e8f0',
                  fontSize: '0.9rem'
                }}
              />
              <button
                onClick={() => handleSlash(selectedStudent)}
                style={{
                  padding: '10px 20px',
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Confirm Slash
              </button>
              <button
                onClick={() => { setSelectedStudent(null); setSlashReason(''); }}
                style={{
                  padding: '10px 20px',
                  background: '#475569',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
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
