/**
 * BeaconChainLabView - Interactive Beacon Chain Lab
 * Demonstrates committee formation, justification threshold, attestation, finality, and slashing
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ethers } from 'ethers';
import BeaconChainLabABI from '../contracts/BeaconChainLab.json';
import { ChainSearch } from '../components/ChainSearch';

const SESSION_STATE_LABELS = { 0: 'LOBBY', 1: 'ACTIVE', 2: 'FINISHED' };

export function BeaconChainLabView({ provider, wallet, rpcUrl }) {
  // Use wallet's provider when available so reads hit the same network as writes (join, attest, etc.)
  const readProvider = wallet?.signer?.provider ?? provider;

  const [config, setConfig] = useState(null);
  const [contract, setContract] = useState(null);
  const [sessionState, setSessionState] = useState(0);
  const [committee, setCommittee] = useState([]);
  const [committeeSize, setCommitteeSize] = useState(8);
  const [totalStaked, setTotalStaked] = useState('0');
  const [quorumThreshold, setQuorumThreshold] = useState('0');
  const [blocks, setBlocks] = useState([]);
  const [currentEpoch, setCurrentEpoch] = useState(1);
  const [currentSlot, setCurrentSlot] = useState(1);
  const [lastFinalizedIndex, setLastFinalizedIndex] = useState(null);
  const [instructor, setInstructor] = useState(null);
  const [activityLog, setActivityLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [txPending, setTxPending] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [stakeAmount, setStakeAmount] = useState('32');
  const [slashTarget, setSlashTarget] = useState('');
  const [slashReason, setSlashReason] = useState('');
  const [attestBlockIndex, setAttestBlockIndex] = useState(0);
  const [selectedBlockIndex, setSelectedBlockIndex] = useState(null);
  const [selectedValidator, setSelectedValidator] = useState(null); // address
  const [blockDetailData, setBlockDetailData] = useState(null); // { attestations, slashEvents }
  const [blockSlashCounts, setBlockSlashCounts] = useState(new Map()); // blockIndex -> count
  const [blockIndexToEthBlock, setBlockIndexToEthBlock] = useState(new Map()); // blockIndex -> { blockNumber, blockHash }
  const [blocksPerEpoch, setBlocksPerEpoch] = useState(4);
  const [poolSize, setPoolSize] = useState(64);
  const [validatorsPerCommittee, setValidatorsPerCommittee] = useState(8);
  const [validatorsPerCommitteeInput, setValidatorsPerCommitteeInput] = useState('8');
  const [requireHumanAttestation, setRequireHumanAttestation] = useState(false);
  const [committeesPerEpoch, setCommitteesPerEpoch] = useState(8);
  const [committeeForSlot, setCommitteeForSlot] = useState(null); // { epoch, slotIndex, members }
  const [pendingSlashes, setPendingSlashes] = useState([]); // addresses with pending slash
  const [pendingSlashEvidence, setPendingSlashEvidence] = useState(new Map()); // addr -> { reason, blockIndex, slot, expectedHash, attestedHash, firstBlock, secondBlock }
  const [validatorDetailData, setValidatorDetailData] = useState(null); // { attestedBlocks, proposedCount, slashEvents }
  const [botWrongHashChance, setBotWrongHashChance] = useState(5);
  const [botDoubleVoteChance, setBotDoubleVoteChance] = useState(10);
  const [inactivityPenaltyEnabled, setInactivityPenaltyEnabled] = useState(false);

  const [searchParams, setSearchParams] = useSearchParams();

  // Validator stats cache
  const [validatorStats, setValidatorStats] = useState(new Map());
  const [hasAttestedMap, setHasAttestedMap] = useState(new Map());
  const [lastProposer, setLastProposer] = useState(null);
  const [contractSupportsReset, setContractSupportsReset] = useState(true); // assume yes until we know otherwise
  const [useOldBlockFormat, setUseOldBlockFormat] = useState(false);
  const [oldFormatWarning, setOldFormatWarning] = useState(null);
  const [epochCommittees, setEpochCommittees] = useState(null); // { epoch, committees: address[][] }
  const [taskCompleted, setTaskCompleted] = useState(new Set());
  const [userExited, setUserExited] = useState(false); // Fetched directly so Rejoin shows even if not in committee stats
  const [userInPool, setUserInPool] = useState(false);  // contract.inPool - definitive "can attest" check (exited users have inPool=false)
  const taskStorageKey = config?.contractAddress ? `beacon-lab-tasks-${config.contractAddress.toLowerCase()}` : null;

  useEffect(() => {
    if (!taskStorageKey) return;
    try {
      const s = localStorage.getItem(taskStorageKey);
      const stored = s ? new Set(JSON.parse(s)) : new Set();
      setTaskCompleted((prev) => new Set([...prev, ...stored]));
    } catch (_) {}
  }, [taskStorageKey]);

  const markTaskComplete = useCallback((taskId) => {
    setTaskCompleted((prev) => {
      const next = new Set(prev);
      next.add(taskId);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!taskStorageKey || taskCompleted.size === 0) return;
    try {
      localStorage.setItem(taskStorageKey, JSON.stringify([...taskCompleted]));
    } catch (_) {}
  }, [taskStorageKey, taskCompleted]);

  const isInstructor = wallet?.address && instructor && wallet.address.toLowerCase() === instructor.toLowerCase();
  const isCommitteeMember = committee.some((c) => c.toLowerCase() === wallet?.address?.toLowerCase());
  const getStats = (a) => validatorStats.get(a) ?? validatorStats.get((a || '').toLowerCase());
  const getAttested = (a, idx) => hasAttestedMap.get(`${a}-${idx}`) ?? hasAttestedMap.get(`${(a || '').toLowerCase()}-${idx}`);
  const myAttested = blocks.length > 0 ? getAttested(wallet?.address, blocks.length - 1) : false;
  const latestBlockIndex = blocks.length > 0 ? blocks.length - 1 : null;

  // Canonical chain: blocks reachable from head by following parent pointers (excludes orphaned fork blocks)
  const canonicalBlockIndices = useMemo(() => {
    const set = new Set();
    if (blocks.length === 0) return set;
    let idx = blocks.length - 1;
    while (idx != null && idx >= 0) {
      set.add(idx);
      const b = blocks[idx];
      if (!b?.parentHash || String(b.parentHash) === String(ethers.ZeroHash)) break;
      const parentIdx = blocks.findIndex((x) => x.blockHash && String(x.blockHash) === String(b.parentHash));
      if (parentIdx < 0) break;
      idx = parentIdx;
    }
    return set;
  }, [blocks]);

  // Blocks the user can attest to (only slots where they're in the committee)
  const attestableBlocks = useMemo(() => {
    if (!wallet?.address || !epochCommittees || blocks.length === 0) return [];
    const userCommitteeIndex = epochCommittees.committees.findIndex((members) =>
      members.some((m) => m?.toLowerCase() === wallet.address?.toLowerCase())
    );
    if (userCommitteeIndex < 0) return [];
    return blocks.filter((b) => {
      const blockEpoch = Math.floor(b.index / blocksPerEpoch) + 1;
      if (blockEpoch !== epochCommittees.epoch) return false;
      const committeeIndex = (b.slot - 1) % committeesPerEpoch;
      return committeeIndex === userCommitteeIndex;
    }).slice(-2); // last 2 blocks user can attest to
  }, [blocks, epochCommittees, wallet?.address, blocksPerEpoch, committeesPerEpoch]);

  // Pending slashes filtered to only those in blocks not yet finalized (or currently being justified)
  const filteredPendingSlashes = useMemo(() => {
    return pendingSlashes.filter((addr) => {
      const ev = pendingSlashEvidence.get(addr);
      if (!ev) return true; // keep if no evidence (shouldn't happen)
      const finalizedCutoff = lastFinalizedIndex != null ? lastFinalizedIndex : -1;
      if (ev.reason === 1) {
        return ev.blockIndex > finalizedCutoff;
      }
      if (ev.reason === 2) {
        return ev.firstBlock > finalizedCutoff || ev.secondBlock > finalizedCutoff;
      }
      return true;
    });
  }, [pendingSlashes, pendingSlashEvidence, lastFinalizedIndex]);

  // Proposer selection stats: stake share vs actual proposal frequency (for educational comparison)
  const proposerStats = useMemo(() => {
    const total = parseFloat(totalStaked) || 0;
    const totalBlocks = blocks.length;
    return committee
      .filter((addr) => !getStats(addr)?.exited)
      .map((addr) => {
        const stats = getStats(addr);
        const stake = parseFloat(stats?.stake || '0');
        const blocksProposed = blocks.filter((b) => b.proposer?.toLowerCase() === addr.toLowerCase()).length;
        const stakePercent = total > 0 ? (stake / total) * 100 : 0;
        const actualPercent = totalBlocks > 0 ? (blocksProposed / totalBlocks) * 100 : 0;
        return { address: addr, stake, blocksProposed, stakePercent, actualPercent };
      })
      .sort((a, b) => b.blocksProposed - a.blocksProposed);
  }, [committee, blocks, totalStaked, validatorStats]);

  // Student tasks: auto-complete when conditions met
  const STUDENT_TASKS = [
    { id: 'join', title: 'Join the validator pool', hint: 'Stake 32+ ETH in the lobby', auto: () => userInPool },
    { id: 'attest', title: 'Attest to a block', hint: 'When in committee, use the Attest button', auto: () => blocks.some((_, i) => getAttested(wallet?.address, i)) },
    { id: 'view-block', title: 'View a block\'s details', hint: 'Click any block in the Latest Blocks table', auto: () => selectedBlockIndex !== null },
    { id: 'see-justified', title: 'Observe a block become justified', hint: 'Watch the attestation progress bar reach 2/3', auto: () => blocks.some((b) => b.justified) },
    { id: 'see-finalized', title: 'Observe a block become finalized', hint: 'Block N finalizes when block N+2 is justified', auto: () => blocks.some((b) => b.finalized) },
    { id: 'find-committee', title: 'Find your committee for the current slot', hint: 'Expand "Committees for Epoch" or check "Your committee for current slot"', auto: () => committeeForSlot != null },
    { id: 'view-slash', title: 'View slash evidence on the chain', hint: 'Click a block or validator with a slash, or check Pending Slashes', auto: () => (selectedBlockIndex != null && blockDetailData?.slashEvents?.length > 0) || (selectedValidator != null && validatorDetailData?.slashEvents?.length > 0) || filteredPendingSlashes.length > 0 },
    { id: 'exit', title: 'Exit the validator pool', hint: 'Click "Exit validator pool" to withdraw stake', auto: () => userExited },
  ];

  useEffect(() => {
    if (!wallet?.address) return;
    STUDENT_TASKS.forEach((t) => {
      if (t.auto?.() && !taskCompleted.has(t.id)) markTaskComplete(t.id);
    });
  }, [userInPool, userExited, blocks, selectedBlockIndex, selectedValidator, committeeForSlot, blockDetailData, validatorDetailData, filteredPendingSlashes, wallet?.address, validatorStats, hasAttestedMap, taskCompleted, markTaskComplete]);

  const tasksDone = STUDENT_TASKS.filter((t) => taskCompleted.has(t.id)).length;

  const fetchConfig = useCallback(async () => {
    try {
      // Prefer /api/config.json for beaconLabContractAddress (Docker runtime deploy)
      let apiConfig = null;
      try {
        const apiRes = await fetch(import.meta.env.BASE_URL + 'api/config.json', { cache: 'no-store' });
        if (apiRes.ok) apiConfig = await apiRes.json();
      } catch (_) {}

      const res = await fetch(import.meta.env.BASE_URL + 'beacon-lab-config.json');
      if (!res.ok) return null;
      const beaconConfig = await res.json();

      // Use beaconLabContractAddress from API when available (runtime-deployed in Docker)
      const contractAddress = apiConfig?.beaconLabContractAddress || beaconConfig.contractAddress;
      const data = { ...beaconConfig, contractAddress };
      setConfig(data);
      return data;
    } catch {
      return null;
    }
  }, []);

  const fetchData = useCallback(async () => {
    if (!contract || !readProvider) return;
    try {
      // Check that a contract exists at this address (0x = no contract / wrong network)
      const addr = await contract.getAddress();
      const code = await readProvider.getCode(addr);
      if (!code || code === '0x' || code === '0x0') {
        setError(`No BeaconChainLab contract at ${addr}. Connect to the correct network (e.g. local Hardhat node) and ensure the contract is deployed. Run: npm run deploy:beacon-lab`);
        setLoading(false);
        return;
      }
      const baseCalls = [
        contract.getSessionState(),
        contract.getCommittee(),
        contract.getCommitteeSize(),
        contract.totalStaked(),
        contract.getQuorumThreshold(),
        contract.getBlocksLength(),
        contract.currentEpoch(),
        contract.currentSlot(),
        contract.lastFinalizedIndex(),
        contract.instructor(),
        contract.blocksPerEpoch ? contract.blocksPerEpoch() : Promise.resolve(4),
      ];
      // Optional calls for upgraded contract (old deployments lack these; catch to avoid revert)
      const safeCall = async (fn, fallback) => {
        try {
          return await (typeof fn === 'function' ? fn() : fn);
        } catch {
          return fallback;
        }
      };
      const [pSize, vpc, reqHuman, cpe, wrongCh, dvCh, inactPen] = await Promise.all([
        safeCall(() => contract.getPoolSize(), 64),
        safeCall(() => contract.validatorsPerCommittee(), 8),
        safeCall(() => contract.requireHumanAttestation(), false),
        safeCall(() => contract.committeesPerEpoch(), 8),
        safeCall(() => contract.botWrongHashChance(), 5),
        safeCall(() => contract.botDoubleVoteChance(), 10),
        safeCall(() => contract.inactivityPenaltyEnabled(), false),
      ]);
      const all = await Promise.all(baseCalls);
      const [state, committeeList, size, total, quorum, blocksLen, epoch, slot, lastFinal, inst, bpe] = all;

      setSessionState(Number(state));
      setCommittee(committeeList || []);
      setCommitteeSize(Number(size));
      setTotalStaked(ethers.formatEther(total));
      setQuorumThreshold(ethers.formatEther(quorum));
      setCurrentEpoch(Number(epoch));
      setCurrentSlot(Number(slot));
      setLastFinalizedIndex(Number(blocksLen) > 0 ? Number(lastFinal) : null);
      setInstructor(inst);
      setBlocksPerEpoch(Number(bpe) || 4);
      setPoolSize(Number(pSize) || 64);
      const vpcNum = Number(vpc) || 8;
      setValidatorsPerCommittee(vpcNum);
      setValidatorsPerCommitteeInput(String(vpcNum));
      setRequireHumanAttestation(!!reqHuman);
      setCommitteesPerEpoch(Number(cpe) || 8);
      setBotWrongHashChance(Number(wrongCh) ?? 5);
      setBotDoubleVoteChance(Number(dvCh) ?? 10);
      setInactivityPenaltyEnabled(!!inactPen);

      const blockInfos = [];
      let useOldBlockFormat = false;
      for (let i = 0; i < Number(blocksLen); i++) {
        try {
          const info = await contract.getBlockInfo(i);
          const hasHumanCount = info.length >= 9;
          blockInfos.push({
            index: i,
            proposer: info[0],
            blockHash: info[1],
            parentHash: info[2],
            slot: Number(info[3]),
            attestationCount: Number(info[4]),
            attestationStake: ethers.formatEther(info[5]),
            humanAttestationCount: hasHumanCount ? Number(info[6]) : 0,
            justified: hasHumanCount ? info[7] : info[6],
            finalized: hasHumanCount ? info[8] : info[7],
          });
        } catch (e) {
          if (e.code !== 'BAD_DATA' && e.info?.code !== 'BAD_DATA') throw e;
          let raw = e.data ?? e.value;
          if (!raw || raw.length < 130) {
            const match = String(e.message || e).match(/value="(0x[a-fA-F0-9]+)"/);
            if (match) raw = match[1];
          }
          if (!raw || raw.length < 130) {
            raw = await readProvider.call({
              to: await contract.getAddress(),
              data: contract.interface.encodeFunctionData('getBlockInfo', [i]),
            });
          }
          if (raw && raw.length >= 130) {
            useOldBlockFormat = true;
            const decoded = ethers.AbiCoder.defaultAbiCoder().decode(
              ['address', 'uint256', 'uint256', 'bool', 'bool'],
              raw
            );
            blockInfos.push({
              index: i,
              proposer: decoded[0],
              blockHash: null,
              parentHash: null,
              slot: i + 1,
              attestationCount: Number(decoded[1]),
              attestationStake: ethers.formatEther(decoded[2]),
              justified: decoded[3],
              finalized: decoded[4],
            });
          } else {
            throw e;
          }
        }
      }
      setUseOldBlockFormat(useOldBlockFormat);
      setOldFormatWarning(useOldBlockFormat ? 'Contract uses old format. Redeploy for slashing features: npm run deploy:beacon-lab' : null);
      setError(null);
      setBlocks(blockInfos);

      // Map each Beacon block to the real Ethereum chain block that contains its propose tx
      const ethBlockMap = new Map();
      try {
        const blockProposedEvents = await contract.queryFilter(contract.filters.BlockProposed());
        const blockNumbers = new Set();
        for (const ev of blockProposedEvents) {
          const blockIndex = Number(ev.args[0]);
          const ethBlockNumber = ev.blockNumber;
          blockNumbers.add(ethBlockNumber);
          ethBlockMap.set(blockIndex, { blockNumber: ethBlockNumber });
        }
        for (const bn of blockNumbers) {
          try {
            const ethBlock = await readProvider.getBlock(bn);
            if (ethBlock?.hash) {
              for (const [idx, data] of ethBlockMap) {
                if (data.blockNumber === bn) ethBlockMap.set(idx, { ...data, blockHash: ethBlock.hash });
              }
            }
          } catch (_) {}
        }
        setBlockIndexToEthBlock(ethBlockMap);
      } catch (_) {
        setBlockIndexToEthBlock(new Map());
      }

      if (blockInfos.length > 0) {
        setLastProposer(blockInfos[blockInfos.length - 1].proposer);
      }

      const stats = new Map();
      const attested = new Map();
      for (const addr of committeeList || []) {
        const [stake, isBot, isSlashed] = await contract.getValidatorStats(addr);
        let exited = false;
        try { exited = await contract.exited(addr); } catch (_) {}
        const entry = { stake: ethers.formatEther(stake), isBot, slashed: isSlashed, exited };
        stats.set(addr, entry);
        stats.set(addr.toLowerCase(), entry); // support both formats for lookup
        if (Number(blocksLen) > 0) {
          const lastIdx = Number(blocksLen) - 1;
          const hasAtt = await contract.hasAttested(addr, lastIdx);
          attested.set(`${addr}-${lastIdx}`, hasAtt);
          attested.set(`${addr.toLowerCase()}-${lastIdx}`, hasAtt);
        }
      }
      if (wallet?.address && Number(blocksLen) > 0) {
        for (let j = 0; j < Number(blocksLen); j++) {
          const hasAtt = await contract.hasAttested(wallet.address, j);
          attested.set(`${wallet.address}-${j}`, hasAtt);
          attested.set(`${wallet.address.toLowerCase()}-${j}`, hasAtt);
        }
      }
      setValidatorStats(stats);
      setHasAttestedMap(attested);

      // Fetch current user's inPool and exited status - use contract + stats fallback (stats come from committee iteration)
      if (wallet?.address && contract) {
        try {
          const [inPoolVal, exitedVal] = await Promise.all([
            contract.inPool(wallet.address),
            contract.exited(wallet.address),
          ]);
          // Fallback: stats from committee iteration may have exited before direct call (e.g. RPC caching)
          const statsEntry = stats.get(wallet.address) ?? stats.get(wallet.address?.toLowerCase?.());
          const exitedFromStats = !!statsEntry?.exited;
          const stakeZero = statsEntry && parseFloat(statsEntry.stake || '0') === 0;
          const isExited = !!exitedVal || exitedFromStats || (stakeZero && !!statsEntry);
          const isInPool = !!inPoolVal && !isExited;
          setUserExited(isExited);
          setUserInPool(isInPool);
        } catch (_) {
          const statsEntry = stats.get(wallet.address) ?? stats.get(wallet.address?.toLowerCase?.());
          setUserExited(!!statsEntry?.exited);
          setUserInPool(false);
        }
      } else {
        setUserInPool(false);
        setUserExited(false);
      }

      // Check if contract has resetSession (sessionId was added in same update)
      try {
        await contract.sessionId();
        setContractSupportsReset(true);
      } catch {
        setContractSupportsReset(false);
      }
    } catch (e) {
      const isBadData = e?.code === 'BAD_DATA' || e?.info?.code === 'BAD_DATA';
      const isEmptyResult = /value="0x"/i.test(String(e?.message || e?.value || ''));
      if (isBadData && isEmptyResult) {
        setError(`No BeaconChainLab contract at this address. Connect to the correct network (e.g. local Hardhat node) and deploy: npm run deploy:beacon-lab`);
      } else {
        setError(e.message || 'Failed to fetch');
      }
    } finally {
      setLoading(false);
    }
  }, [contract, readProvider, wallet?.address]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const cfg = await fetchConfig();
      if (cancelled || !cfg?.contractAddress || !readProvider) return;
      const c = new ethers.Contract(cfg.contractAddress, BeaconChainLabABI, readProvider);
      setContract(c);
    })();
    return () => { cancelled = true; };
  }, [readProvider, fetchConfig]);

  useEffect(() => {
    if (!contract) return;
    fetchData();
    const iv = setInterval(fetchData, 2000);
    return () => clearInterval(iv);
  }, [contract, fetchData]);

  useEffect(() => {
    if (attestableBlocks.length > 0) {
      const validIndices = new Set(attestableBlocks.map((b) => b.index));
      if (!validIndices.has(attestBlockIndex)) {
        setAttestBlockIndex(attestableBlocks[attestableBlocks.length - 1].index);
      }
    }
  }, [attestableBlocks, attestBlockIndex]);

  // URL state: ?block=5 or ?validator=0x... for bookmarkable drill-down (block takes priority)
  useEffect(() => {
    const blockParam = searchParams.get('block');
    const validatorParam = searchParams.get('validator');
    if (blockParam !== null && blocks.length > 0) {
      const idx = parseInt(blockParam, 10);
      if (!isNaN(idx) && idx >= 0 && idx < blocks.length) {
        setSelectedBlockIndex(idx);
        setSelectedValidator(null);
        return;
      }
    }
    if (validatorParam && committee.some((c) => c.toLowerCase() === validatorParam.toLowerCase())) {
      setSelectedValidator(validatorParam);
      setSelectedBlockIndex(null);
    }
  }, [searchParams, blocks.length, committee]);
  const updateUrlForDrillDown = useCallback((block, validator) => {
    const next = new URLSearchParams(searchParams);
    next.set('view', 'beacon-lab'); // Preserve view so URL change doesn't navigate away
    if (block != null) next.set('block', String(block));
    else next.delete('block');
    if (validator) next.set('validator', validator);
    else next.delete('validator');
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams]);

  // Fetch block detail when a block is selected (drill-down)
  useEffect(() => {
    if (!contract || selectedBlockIndex === null || selectedBlockIndex >= blocks.length) {
      setBlockDetailData(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const blockIndex = selectedBlockIndex;
        const attestations = [];
        for (const addr of committee) {
          const hasAtt = await contract.hasAttested(addr, blockIndex);
          if (hasAtt) {
            const [stake] = await contract.getValidatorStats(addr);
            attestations.push({ address: addr, stake: ethers.formatEther(stake) });
          }
        }
        const wrongSlashFilter = contract.filters.WrongAttestationSlashed(null, blockIndex);
        const wrongSlashEvents = await contract.queryFilter(wrongSlashFilter);
        const doubleSlashFilter = contract.filters.DoubleVoteSlashed();
        const doubleSlashEvents = await contract.queryFilter(doubleSlashFilter);
        const slashEvents = [
          ...wrongSlashEvents.map((e) => ({
            type: 'wrong_attestation',
            validator: e.args[0],
            blockIndex: Number(e.args[1]),
            expectedHash: e.args[2],
            attestedHash: e.args[3],
          })),
          ...doubleSlashEvents
            .filter((e) => Number(e.args[2]) === blockIndex || Number(e.args[3]) === blockIndex)
            .map((e) => ({
              type: 'double_vote',
              validator: e.args[0],
              slot: Number(e.args[1]),
              firstBlock: Number(e.args[2]),
              secondBlock: Number(e.args[3]),
            })),
        ];
        let transactions = [];
        const ethBlockData = blockIndexToEthBlock.get(blockIndex);
        if (ethBlockData?.blockNumber != null && readProvider) {
          try {
            const ethBlock = await readProvider.getBlock(ethBlockData.blockNumber, true);
            const txs = ethBlock?.prefetchedTransactions ?? ethBlock?.transactions ?? [];
            transactions = txs.map((tx) => ({
              hash: typeof tx === 'string' ? tx : tx.hash,
              from: typeof tx === 'object' ? tx.from : null,
              to: typeof tx === 'object' ? tx.to : null,
              value: typeof tx === 'object' ? tx.value : null,
            }));
          } catch (_) {}
        }
        if (!cancelled) {
          setBlockDetailData({ attestations, slashEvents, transactions });
        }
      } catch (e) {
        if (!cancelled) setBlockDetailData(null);
      }
    })();
    return () => { cancelled = true; };
  }, [contract, selectedBlockIndex, committee, blocks.length, blockIndexToEthBlock, readProvider]);

  // Fetch validator detail when selected
  useEffect(() => {
    if (!contract || !selectedValidator || committee.length === 0 || blocks.length === 0) {
      setValidatorDetailData(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const addr = selectedValidator;
        const attestedBlocks = [];
        for (let i = 0; i < blocks.length; i++) {
          const hasAtt = await contract.hasAttested(addr, i);
          if (hasAtt) attestedBlocks.push({ blockIndex: i, slot: blocks[i].slot });
        }
        const proposedCount = blocks.filter((b) => b.proposer?.toLowerCase() === addr.toLowerCase()).length;
        const wrongEvents = await contract.queryFilter(contract.filters.WrongAttestationSlashed(addr));
        const doubleEvents = await contract.queryFilter(contract.filters.DoubleVoteSlashed(addr));
        const manualEvents = await contract.queryFilter(contract.filters.Slashed(addr));
        const manualOnly = manualEvents.filter((e) => {
          const r = String(e.args[2] || '');
          return r !== 'Wrong block hash' && r !== 'Double vote';
        });
        const slashEvents = [
          ...wrongEvents.map((e) => ({ type: 'wrong_attestation', blockIndex: Number(e.args[1]), expectedHash: e.args[2], attestedHash: e.args[3] })),
          ...doubleEvents.map((e) => ({ type: 'double_vote', slot: Number(e.args[1]), firstBlock: Number(e.args[2]), secondBlock: Number(e.args[3]) })),
          ...manualOnly.map((e) => ({ type: 'manual', reason: e.args[2] })),
        ];
        if (!cancelled) {
          setValidatorDetailData({ attestedBlocks, proposedCount, slashEvents });
        }
      } catch {
        if (!cancelled) setValidatorDetailData(null);
      }
    })();
    return () => { cancelled = true; };
  }, [contract, selectedValidator, committee, blocks]);

  // Fetch pending slashes and their evidence
  useEffect(() => {
    if (!contract || !contract.hasPendingSlash || committee.length === 0) return;
    let cancelled = false;
    (async () => {
      try {
        const pending = [];
        const evidenceMap = new Map();
        for (const addr of committee) {
          const has = await contract.hasPendingSlash(addr);
          if (has) {
            pending.push(addr);
            try {
              const ev = await contract.pendingSlash(addr);
              if (Number(ev.reason) !== 0) {
                evidenceMap.set(addr, {
                  reason: Number(ev.reason),
                  blockIndex: Number(ev.blockIndex),
                  slot: Number(ev.slot),
                  expectedHash: ev.expectedHash,
                  attestedHash: ev.attestedHash,
                  firstBlock: Number(ev.firstBlock),
                  secondBlock: Number(ev.secondBlock),
                });
              }
            } catch (_) {}
          }
        }
        if (!cancelled) {
          setPendingSlashes(pending);
          setPendingSlashEvidence(evidenceMap);
        }
      } catch {
        if (!cancelled) setPendingSlashes([]);
      }
    })();
    return () => { cancelled = true; };
  }, [contract, committee]);

  // Fetch committee for current slot (for "Your committee" display)
  useEffect(() => {
    if (!contract || !contract.getCommitteeForSlot || blocks.length === 0) return;
    const latest = blocks[blocks.length - 1];
    if (!latest) return;
    const epoch = Math.floor(latest.index / blocksPerEpoch) + 1;
    const slotIndex = (latest.slot - 1) % committeesPerEpoch;
    let cancelled = false;
    (async () => {
      try {
        const members = await contract.getCommitteeForSlot(epoch, slotIndex);
        if (!cancelled) setCommitteeForSlot({ epoch, slotIndex, members: members.filter(Boolean) });
      } catch {
        if (!cancelled) setCommitteeForSlot(null);
      }
    })();
    return () => { cancelled = true; };
  }, [contract, blocks, blocksPerEpoch, committeesPerEpoch]);

  // Fetch all committees for current epoch (for committee assignment table)
  useEffect(() => {
    if (!contract || !contract.getCommitteeForSlot || blocks.length === 0 || sessionState !== 1) return;
    const latest = blocks[blocks.length - 1];
    if (!latest) return;
    const epoch = Math.floor(latest.index / blocksPerEpoch) + 1;
    let cancelled = false;
    (async () => {
      try {
        const committees = [];
        for (let i = 0; i < committeesPerEpoch; i++) {
          const members = await contract.getCommitteeForSlot(epoch, i);
          committees.push((members || []).filter(Boolean));
        }
        if (!cancelled) setEpochCommittees({ epoch, committees });
      } catch {
        if (!cancelled) setEpochCommittees(null);
      }
    })();
    return () => { cancelled = true; };
  }, [contract, blocks, committeesPerEpoch, sessionState]);

  // Fetch slash counts per block for badges
  useEffect(() => {
    if (!contract || blocks.length === 0) return;
    let cancelled = false;
    (async () => {
      try {
        const counts = new Map();
        const wrongEvents = await contract.queryFilter(contract.filters.WrongAttestationSlashed());
        for (const e of wrongEvents) {
          const idx = Number(e.args[1]);
          counts.set(idx, (counts.get(idx) || 0) + 1);
        }
        const doubleEvents = await contract.queryFilter(contract.filters.DoubleVoteSlashed());
        for (const e of doubleEvents) {
          const fb = Number(e.args[2]);
          const sb = Number(e.args[3]);
          counts.set(fb, (counts.get(fb) || 0) + 1);
          counts.set(sb, (counts.get(sb) || 0) + 1);
        }
        if (!cancelled) setBlockSlashCounts(counts);
      } catch {
        if (!cancelled) setBlockSlashCounts(new Map());
      }
    })();
    return () => { cancelled = true; };
  }, [contract, blocks.length]);

  // Auto-propose blocks (Ethereum simulation: ~12s block time, stake-weighted proposer selection)
  const proposingRef = useRef(false);
  useEffect(() => {
    if (!isInstructor || sessionState !== 1 || !config?.contractAddress || !wallet?.signer) return;
    const BLOCK_TIME_MS = 12000; // Ethereum mainnet ~12 seconds
    const propose = async () => {
      if (proposingRef.current) return;
      proposingRef.current = true;
      try {
        const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
        await c.proposeBlock();
      } catch (e) {
        console.warn('[BeaconLab] Auto-propose:', e.message);
      } finally {
        proposingRef.current = false;
      }
    };
    const t0 = setTimeout(propose, 3000); // First block after 3s
    const iv = setInterval(propose, BLOCK_TIME_MS);
    return () => {
      clearTimeout(t0);
      clearInterval(iv);
    };
  }, [isInstructor, sessionState, config?.contractAddress, wallet?.signer]);

  useEffect(() => {
    if (!contract || !readProvider) return;
    const addLog = (msg) => setActivityLog((prev) => [...prev.slice(-99), { ts: Date.now(), msg }]);

    const onBlockProposed = (idx, proposer, epoch) =>
      addLog(`Block #${Number(idx)} proposed by ${proposer.slice(0, 10)}... (epoch ${Number(epoch)})`);
    const onAttested = (validator, blockIndex) =>
      addLog(`${validator.slice(0, 10)}... attested to block #${Number(blockIndex)}`);
    const onJustified = (blockIndex) => addLog(`Block #${Number(blockIndex)} justified (justification threshold reached)`);
    const onFinalized = (blockIndex) => addLog(`Block #${Number(blockIndex)} finalized`);
    const onSlashed = (validator, amount, reason) =>
      addLog(`Slashed ${validator.slice(0, 10)}... (${ethers.formatEther(amount)} ETH): ${reason}`);
    const onWrongAttestationSlashed = (validator, blockIndex, expectedHash, attestedHash) =>
      addLog(`Wrong attestation slash: ${validator.slice(0, 10)}... expected ${String(expectedHash).slice(0, 18)}..., attested ${String(attestedHash).slice(0, 18)}...`);
    const onDoubleVoteSlashed = (validator, slot, firstBlock, secondBlock) =>
      addLog(`Double vote slash: ${validator.slice(0, 10)}... at slot ${Number(slot)} attested to block #${Number(firstBlock)} and #${Number(secondBlock)}`);
    const onJoined = (validator, stake) =>
      addLog(`${validator.slice(0, 10)}... joined with ${ethers.formatEther(stake)} ETH`);
    const onSessionStarted = (humanCount, botCount) =>
      addLog(`Session started: ${Number(humanCount)} humans, ${Number(botCount)} bots`);
    const onSessionEnded = () => addLog('Session ended');
    const onSlashEvidenceSubmitted = (validator, reason) =>
      addLog(`Slash evidence submitted for ${validator.slice(0, 10)}... (reason: ${Number(reason)})`);
    const onSlashReported = (reporter, validator, reward) =>
      addLog(`${reporter.slice(0, 10)}... reported slash, earned ${ethers.formatEther(reward)} ETH`);
    const onCommitteesAssigned = (epoch) => addLog(`Committees assigned for epoch ${Number(epoch)}`);
    const onEpochAdvanced = (epoch) => {
      addLog(`Epoch advanced to ${Number(epoch)}`);
      fetchData().catch((e) => console.warn('[BeaconLab] EpochAdvanced fetchData:', e));
    };
    const onValidatorExited = (validator, amount) =>
      addLog(`${validator.slice(0, 10)}... exited, refunded ${ethers.formatEther(amount)} ETH`);
    const onInactivityPenalty = (validator, blockIndex, amount) =>
      addLog(`${validator.slice(0, 10)}... inactivity penalty (block #${Number(blockIndex)}): -${ethers.formatEther(amount)} ETH`);

    contract.on('BlockProposed', onBlockProposed);
    contract.on('Attested', onAttested);
    contract.on('BlockJustified', onJustified);
    contract.on('BlockFinalized', onFinalized);
    contract.on('Slashed', onSlashed);
    contract.on('WrongAttestationSlashed', onWrongAttestationSlashed);
    contract.on('DoubleVoteSlashed', onDoubleVoteSlashed);
    contract.on('Joined', onJoined);
    contract.on('SessionStarted', onSessionStarted);
    contract.on('SessionEnded', onSessionEnded);
    try {
      contract.on('SlashEvidenceSubmitted', onSlashEvidenceSubmitted);
      contract.on('SlashReported', onSlashReported);
      contract.on('CommitteesAssigned', onCommitteesAssigned);
      contract.on('EpochAdvanced', onEpochAdvanced);
      contract.on('ValidatorExited', onValidatorExited);
      contract.on('InactivityPenalty', onInactivityPenalty);
    } catch (_) {}

    return () => {
      contract.off('BlockProposed', onBlockProposed);
      contract.off('Attested', onAttested);
      contract.off('BlockJustified', onJustified);
      contract.off('BlockFinalized', onFinalized);
      contract.off('Slashed', onSlashed);
      contract.off('WrongAttestationSlashed', onWrongAttestationSlashed);
      contract.off('DoubleVoteSlashed', onDoubleVoteSlashed);
      contract.off('Joined', onJoined);
      contract.off('SessionStarted', onSessionStarted);
      contract.off('SessionEnded', onSessionEnded);
      try {
        contract.off('SlashEvidenceSubmitted', onSlashEvidenceSubmitted);
        contract.off('SlashReported', onSlashReported);
        contract.off('CommitteesAssigned', onCommitteesAssigned);
        contract.off('EpochAdvanced', onEpochAdvanced);
        contract.off('ValidatorExited', onValidatorExited);
        contract.off('InactivityPenalty', onInactivityPenalty);
      } catch (_) {}
    };
  }, [contract, readProvider, fetchData]);

  const handleProcessSlash = async (validator) => {
    if (!config?.contractAddress || !wallet?.signer) return;
    setTxPending(true);
    setStatusMsg('Reporting slash...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.processSlash(validator);
      await tx.wait();
      setStatusMsg('Slash reported! You earned a whistleblower reward.');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleJoin = async () => {
    if (!config?.contractAddress || !wallet?.signer) {
      setStatusMsg('Connect wallet first');
      return;
    }
    const amt = parseFloat(stakeAmount);
    if (isNaN(amt) || amt < 32) {
      setStatusMsg('Minimum stake is 32 ETH');
      return;
    }
    setTxPending(true);
    setStatusMsg('Joining...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.join({ value: ethers.parseEther(stakeAmount) });
      await tx.wait();
      setStatusMsg('Joined successfully!');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleRejoin = async () => {
    if (!config?.contractAddress || !wallet?.signer) {
      setStatusMsg('Connect wallet first');
      return;
    }
    const amt = parseFloat(stakeAmount);
    if (isNaN(amt) || amt < 32) {
      setStatusMsg('Minimum stake is 32 ETH');
      return;
    }
    setTxPending(true);
    setStatusMsg('Rejoining...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.rejoin({ value: ethers.parseEther(stakeAmount) });
      await tx.wait();
      setStatusMsg('Rejoined successfully!');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const RESERVE_FOR_LATE_JOINERS = 10;
  // Hardhat node uses blockGasLimit: 300M - no bot cap needed
  const GAS_LIMIT = 300_000_000n;

  const handleFillBotsAndStart = async () => {
    if (!config?.contractAddress || !wallet?.signer || !config.botAddresses?.length) {
      setStatusMsg('Config missing or no bot addresses');
      return;
    }
    // Pre-flight checks to surface clear errors (avoids "missing revert data" from gas estimation)
    if (!isInstructor) {
      setStatusMsg(`Only the instructor (${(instructor || '0x...').slice(0, 10)}...) can fill bots and start. Connect with the deployer wallet (Hardhat account 0 in Docker). Use Import in the sidebar.`);
      return;
    }
    if (sessionState !== 0) {
      setStatusMsg(`Session must be in LOBBY. Current state: ${SESSION_STATE_LABELS[sessionState] || sessionState}. Reset the session first if needed.`);
      return;
    }
    if (committee.length === 0) {
      setStatusMsg('Join the pool first (stake 32 ETH above), then Fill Bots and Start. As instructor, you can join with your own wallet.');
      return;
    }
    setTxPending(true);
    setStatusMsg('Filling bots and starting...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const emptySlots = poolSize - committee.length;
      const botsToAdd = emptySlots <= 0 ? 0 : Math.max(1, Math.min(emptySlots - Math.min(RESERVE_FOR_LATE_JOINERS, emptySlots - 1), config.botAddresses.length));
      const botAddrs = botsToAdd > 0 ? config.botAddresses.slice(0, botsToAdd) : config.botAddresses.slice(0, 1);
      let addrs = botAddrs.length ? botAddrs : config.botAddresses.slice(0, 1);
      const gasOpts = { gasLimit: GAS_LIMIT };
      let tx;
      try {
        tx = await c.fillBotsAndStart(addrs, !!requireHumanAttestation, gasOpts);
      } catch (e) {
        if (/not enough bot|Not enough bot/i.test(String(e?.message || e?.reason || e))) {
          addrs = config.botAddresses.slice(0, emptySlots);
          tx = await c.fillBotsAndStart(addrs, !!requireHumanAttestation, gasOpts);
        } else throw e;
      }
      await tx.wait();
      setStatusMsg('Session started!');
      fetchData();
    } catch (e) {
      const msg = e?.reason || e?.message || String(e);
      if (/missing revert data|data=null|reason=null/i.test(msg)) {
        setStatusMsg('Transaction reverted (no reason from node). Ensure you are the instructor, session is in LOBBY, and at least one student has joined.');
      } else if (/ran out of gas|out of gas/i.test(msg)) {
        setStatusMsg('Transaction ran out of gas. Pool may be too large; try with fewer validators or reset the session.');
      } else {
        setStatusMsg('Error: ' + msg);
      }
    } finally {
      setTxPending(false);
    }
  };

  const handleJoinAndStart = async () => {
    if (!isInstructor || sessionState !== 0 || committee.length > 0) return;
    if (!config?.contractAddress || !wallet?.signer || !config.botAddresses?.length) {
      setStatusMsg('Config missing or no bot addresses');
      return;
    }
    const amt = parseFloat(stakeAmount);
    if (isNaN(amt) || amt < 32) {
      setStatusMsg('Minimum stake is 32 ETH');
      return;
    }
    setTxPending(true);
    setStatusMsg('Joining as instructor...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const joinTx = await c.join({ value: ethers.parseEther(stakeAmount) });
      await joinTx.wait();
      setStatusMsg('Joined. Filling bots and starting...');
      const committeeList = await c.getCommittee();
      const currentLen = (committeeList || []).length;
      const emptySlots = poolSize - currentLen;
      const botsToAdd = emptySlots <= 0 ? 0 : Math.max(1, Math.min(emptySlots - Math.min(RESERVE_FOR_LATE_JOINERS, emptySlots - 1), config.botAddresses.length));
      const botAddrs = botsToAdd > 0 ? config.botAddresses.slice(0, botsToAdd) : config.botAddresses.slice(0, 1);
      let addrs = botAddrs.length ? botAddrs : config.botAddresses.slice(0, 1);
      const gasOpts = { gasLimit: GAS_LIMIT };
      let tx;
      try {
        tx = await c.fillBotsAndStart(addrs, !!requireHumanAttestation, gasOpts);
      } catch (e) {
        if (/not enough bot|Not enough bot/i.test(String(e?.message || e?.reason || e))) {
          addrs = config.botAddresses.slice(0, emptySlots);
          tx = await c.fillBotsAndStart(addrs, !!requireHumanAttestation, gasOpts);
        } else throw e;
      }
      await tx.wait();
      setStatusMsg('Session started!');
      fetchData();
    } catch (e) {
      const msg = e?.reason || e?.message || String(e);
      if (/missing revert data|data=null|reason=null/i.test(msg)) {
        setStatusMsg('Transaction reverted. Ensure RPC is connected and you are the instructor.');
      } else {
        setStatusMsg('Error: ' + msg);
      }
    } finally {
      setTxPending(false);
    }
  };

  const handleProposeBlockFork = async () => {
    if (!config?.contractAddress || !wallet?.signer) return;
    setTxPending(true);
    setStatusMsg('Proposing fork block...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.proposeBlockFork();
      await tx.wait();
      setStatusMsg('Fork block proposed!');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleProposeBlock = async () => {
    if (!config?.contractAddress || !wallet?.signer) return;
    setTxPending(true);
    setStatusMsg('Proposing block...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.proposeBlock();
      await tx.wait();
      setStatusMsg('Block proposed!');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleAttest = async (useWrongHash = false) => {
    if (!config?.contractAddress || !wallet?.signer || blocks.length === 0) return;
    const blockIndex = attestBlockIndex;
    const block = blocks[blockIndex];
    if (!block) return;
    const claimedHash = useWrongHash ? ethers.keccak256(ethers.toUtf8Bytes('wrong')) : block.blockHash;
    setTxPending(true);
    setStatusMsg(useWrongHash ? 'Attesting with wrong hash (demo)...' : 'Attesting...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.attest(blockIndex, claimedHash);
      await tx.wait();
      if (useWrongHash) {
        setStatusMsg('Attestation rejected (wrong hash). Violation reported - report slash to earn reward.');
      } else {
        setStatusMsg('Attested!');
      }
      fetchData();
    } catch (e) {
      const msg = e.reason || e.message || '';
      setStatusMsg(msg.includes('slashed') ? 'Slashed (5% penalty). Click the block to see details.' : msg.includes('Not in committee') ? 'You are not in the committee for this slot.' : 'Error: ' + msg);
    } finally {
      setTxPending(false);
    }
  };

  const handleExit = async () => {
    if (!config?.contractAddress || !wallet?.signer) return;
    setTxPending(true);
    setStatusMsg('Exiting validator pool...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.exit();
      await tx.wait();
      setStatusMsg('Exited! Stake refunded.');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleSetInactivityPenalty = async () => {
    if (!config?.contractAddress || !wallet?.signer) return;
    setTxPending(true);
    setStatusMsg('Updating inactivity penalty...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.setInactivityPenaltyEnabled(inactivityPenaltyEnabled);
      await tx.wait();
      setStatusMsg('Inactivity penalty ' + (inactivityPenaltyEnabled ? 'enabled' : 'disabled'));
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleSetBotMisbehavior = async () => {
    if (!config?.contractAddress || !wallet?.signer) return;
    setTxPending(true);
    setStatusMsg('Setting bot misbehavior...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.setBotMisbehaviorChance(botWrongHashChance, botDoubleVoteChance);
      await tx.wait();
      setStatusMsg('Bot misbehavior chance updated');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleSlash = async () => {
    if (!config?.contractAddress || !wallet?.signer || !slashTarget || !slashReason.trim()) {
      setStatusMsg('Select validator and enter reason');
      return;
    }
    setTxPending(true);
    setStatusMsg('Slashing...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.slash(slashTarget, slashReason.trim());
      await tx.wait();
      setStatusMsg('Slashed!');
      setSlashTarget('');
      setSlashReason('');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleEndSession = async () => {
    if (!config?.contractAddress || !wallet?.signer) return;
    setTxPending(true);
    setStatusMsg('Ending session...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.endSession();
      await tx.wait();
      setStatusMsg('Session ended');
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  const handleReset = async () => {
    if (!config?.contractAddress) {
      setStatusMsg('No contract address. Run: npm run deploy:beacon-lab');
      return;
    }
    if (!wallet?.signer) {
      setStatusMsg('Connect your wallet (instructor) to reset');
      return;
    }
    if (!confirm('Reset the lab? This will refund all stakers and clear the committee. Students can join again.')) return;
    setError(null);
    setTxPending(true);
    setStatusMsg('Resetting... (confirm in wallet)');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.resetSession();
      setStatusMsg('Waiting for confirmation...');
      await tx.wait();
      setError(null);
      setStatusMsg('Lab reset to lobby');
      fetchData();
    } catch (e) {
      const msg = (typeof e?.reason === 'string' ? e.reason : null) || (typeof e?.message === 'string' ? e.message : null) || 'Reset failed';
      setStatusMsg('Error: ' + msg);
      const isRevert = /revert|invalid|selector|not found|Refund failed/i.test(msg);
      setError(isRevert ? msg + ' — If using an old deployment, run: npm run deploy:beacon-lab' : msg);
      console.error('[BeaconLab] Reset failed:', e);
    } finally {
      setTxPending(false);
    }
  };

  const handleSetValidatorsPerCommittee = async () => {
    if (!config?.contractAddress || !wallet?.signer) {
      setStatusMsg('Connect wallet first');
      return;
    }
    const v = parseInt(validatorsPerCommitteeInput, 10);
    if (isNaN(v) || v < 1 || v > 256) {
      setStatusMsg('Validators per committee must be 1–256');
      return;
    }
    if (committee.length > committeesPerEpoch * v) {
      setStatusMsg(`Cannot set: ${committee.length} validators already joined, need pool size >= ${committee.length}`);
      return;
    }
    setTxPending(true);
    setStatusMsg('Setting validators per committee...');
    try {
      const c = new ethers.Contract(config.contractAddress, BeaconChainLabABI, wallet.signer);
      const tx = await c.setValidatorsPerCommittee(v);
      await tx.wait();
      setStatusMsg(`Set to ${v} validators. Pool size now ${committeesPerEpoch * v}.`);
      fetchData();
    } catch (e) {
      setStatusMsg('Error: ' + (e.reason || e.message));
    } finally {
      setTxPending(false);
    }
  };

  if (!config) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
        <p>Beacon Chain Lab not deployed. Run: <code>npm run deploy:beacon-lab</code></p>
        <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
          Ensure the chain is running and deploy script writes to frontend/public/beacon-lab-config.json
        </p>
      </div>
    );
  }

  if (loading && !contract) {
    return <div style={{ padding: '2rem', color: '#94a3b8' }}>Loading...</div>;
  }

  const latestBlock = blocks.length > 0 ? blocks[blocks.length - 1] : null;
  const attestationProgress = latestBlock && parseFloat(totalStaked) > 0
    ? (parseFloat(latestBlock.attestationStake) / parseFloat(quorumThreshold)) * 100
    : 0;

  const participationPct = parseFloat(totalStaked) > 0 && latestBlock
    ? (parseFloat(latestBlock.attestationStake) / parseFloat(totalStaked)) * 100
    : 0;
  const finalizedEpoch = lastFinalizedIndex != null && blocks[lastFinalizedIndex] && blocksPerEpoch > 0
    ? Math.floor(lastFinalizedIndex / blocksPerEpoch) + 1
    : 0;
  const finalizedSlot = lastFinalizedIndex != null && blocks[lastFinalizedIndex]
    ? blocks[lastFinalizedIndex].slot
    : 0;

  const findBlockByHash = (hash) => {
    if (!hash || hash === ethers.ZeroHash) return null;
    const idx = blocks.findIndex((b) => b.blockHash && String(b.blockHash).toLowerCase() === String(hash).toLowerCase());
    return idx >= 0 ? idx : null;
  };

  // Chain visualization for slash evidence (wrong hash = forged attestation, double vote = equivocation fork)
  const SlashEvidenceChain = ({ ev, validator, onSelectBlock }) => {
    if (!ev || ev.reason === 0) return null;
    const isWrongHash = ev.reason === 1;
    const isDoubleVote = ev.reason === 2;
    const realBlock = blocks[isWrongHash ? ev.blockIndex : ev.firstBlock];
    const forkBlock = isDoubleVote ? blocks[ev.secondBlock] : null;
    const parentIdx = realBlock?.parentHash && realBlock.parentHash !== ethers.ZeroHash
      ? blocks.findIndex((b) => b.blockHash && String(b.blockHash) === String(realBlock.parentHash))
      : -1;

    if (isWrongHash) {
      return (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(0,0,0,0.3)', borderRadius: '0.5rem', border: '1px solid #475569' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', fontWeight: 600 }}>Violation on chain — Forged attestation</div>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
            <div
              style={{
                flex: '1 1 200px',
                padding: '0.75rem',
                background: 'rgba(34,197,94,0.15)',
                borderRadius: '0.5rem',
                border: '1px solid rgba(34,197,94,0.5)',
              }}
            >
              <div style={{ fontSize: '0.7rem', color: '#86efac', marginBottom: '0.35rem' }}>✓ Canonical block on chain</div>
              <div style={{ fontSize: '0.8rem', color: '#e2e8f0' }}>Block #{ev.blockIndex} · Slot {ev.slot}</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.25rem', wordBreak: 'break-all' }}>
                Root: {String(ev.expectedHash).slice(0, 20)}...
              </div>
              {realBlock?.proposer && (
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.2rem' }}>Proposer: {String(realBlock.proposer).slice(0, 12)}...</div>
              )}
              {onSelectBlock && (
                <button type="button" onClick={() => onSelectBlock(ev.blockIndex)} style={{ marginTop: '0.5rem', padding: '0.2rem 0.4rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#86efac', fontSize: '0.7rem', cursor: 'pointer' }}>
                  View block
                </button>
              )}
            </div>
            <div style={{ alignSelf: 'center', color: '#64748b', fontSize: '1.2rem' }}>→</div>
            <div
              style={{
                flex: '1 1 200px',
                padding: '0.75rem',
                background: 'rgba(239,68,68,0.15)',
                borderRadius: '0.5rem',
                border: '1px solid rgba(239,68,68,0.5)',
              }}
            >
              <div style={{ fontSize: '0.7rem', color: '#fca5a5', marginBottom: '0.35rem' }}>✗ Invalid blob validator attested to</div>
              <div style={{ fontSize: '0.8rem', color: '#e2e8f0' }}>Forged / wrong root hash</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.25rem', wordBreak: 'break-all' }}>
                Claimed: {String(ev.attestedHash).slice(0, 20)}...
              </div>
              <div style={{ fontSize: '0.7rem', color: '#fca5a5', marginTop: '0.35rem' }}>Equivocation — validator signed a block root that does not exist on chain</div>
            </div>
          </div>
        </div>
      );
    }

    if (isDoubleVote && forkBlock) {
      return (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(0,0,0,0.3)', borderRadius: '0.5rem', border: '1px solid #475569' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', fontWeight: 600 }}>Violation on chain — Double spend / equivocation</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
            {parentIdx >= 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: '#64748b' }}>Parent</span>
                <button type="button" onClick={() => onSelectBlock?.(parentIdx)} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: 0, textDecoration: 'underline', fontSize: 'inherit' }}>
                  Block #{parentIdx}
                </button>
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div
                style={{
                  padding: '0.6rem 0.9rem',
                  background: 'rgba(34,197,94,0.15)',
                  borderRadius: '0.5rem',
                  border: '1px solid rgba(34,197,94,0.5)',
                  flex: '1 1 140px',
                }}
              >
                <div style={{ fontSize: '0.7rem', color: '#86efac' }}>Canonical · Slot {ev.slot}</div>
                <button type="button" onClick={() => onSelectBlock?.(ev.firstBlock)} style={{ background: 'none', border: 'none', color: '#86efac', cursor: 'pointer', padding: 0, fontWeight: 600, fontSize: 'inherit' }}>
                  Block #{ev.firstBlock}
                </button>
              </div>
              <div style={{ color: '#f59e0b', fontWeight: 'bold' }}>↔</div>
              <div
                style={{
                  padding: '0.6rem 0.9rem',
                  background: 'rgba(239,68,68,0.15)',
                  borderRadius: '0.5rem',
                  border: '1px solid rgba(239,68,68,0.5)',
                  flex: '1 1 140px',
                }}
              >
                <div style={{ fontSize: '0.7rem', color: '#fca5a5' }}>Fork · Same slot</div>
                <button type="button" onClick={() => onSelectBlock?.(ev.secondBlock)} style={{ background: 'none', border: 'none', color: '#fca5a5', cursor: 'pointer', padding: 0, fontWeight: 600, fontSize: 'inherit' }}>
                  Block #{ev.secondBlock}
                </button>
              </div>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#fca5a5' }}>
              Validator attested to both blocks at slot {ev.slot} — equivocation (double vote)
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard?.writeText(text).then(() => setStatusMsg('Copied!'));
  };

  const selectBlock = (idx) => {
    setSelectedBlockIndex(idx === selectedBlockIndex ? null : idx);
    setSelectedValidator(null);
    updateUrlForDrillDown(idx === selectedBlockIndex ? null : idx, null);
  };
  const selectValidator = (addr) => {
    setSelectedValidator(addr === selectedValidator ? null : addr);
    setSelectedBlockIndex(null);
    updateUrlForDrillDown(null, addr === selectedValidator ? null : addr);
  };

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* BeaconScan-style header */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
        marginBottom: '1.5rem',
        padding: '1rem',
        background: 'var(--card)',
        borderRadius: '0.75rem',
        border: '1px solid #475569',
      }}>
        <span style={{
          padding: '0.35rem 0.75rem',
          background: sessionState === 0 ? '#f59e0b' : sessionState === 1 ? '#22c55e' : '#64748b',
          borderRadius: '0.5rem',
          fontWeight: 'bold',
          fontSize: '0.9rem',
        }}>
          {SESSION_STATE_LABELS[sessionState]}
        </span>
        <span style={{ color: '#94a3b8' }}>Current Epoch {currentEpoch}</span>
        <span style={{ color: '#94a3b8' }}>Finalized Epoch {finalizedEpoch}</span>
        <span style={{ color: '#94a3b8' }}>Current Slot {currentSlot}</span>
        <span style={{ color: '#94a3b8' }}>Finalized Slot {finalizedSlot}</span>
        <span style={{ color: '#94a3b8' }}>Participation {participationPct.toFixed(1)}%</span>
        <span style={{ color: '#94a3b8' }}>Pool {committee.length}/{poolSize}</span>
        {statusMsg && <span style={{ color: '#86efac', fontSize: '0.9rem' }}>{statusMsg}</span>}
      </div>

      {/* Prominent Rejoin section when user has exited - always visible at top */}
      {wallet?.address && userExited && (sessionState === 0 || sessionState === 1) && committee.length < poolSize && (
        <div style={{
          padding: '1rem 1.25rem',
          marginBottom: '1rem',
          background: 'linear-gradient(135deg, rgba(59,130,246,0.25) 0%, rgba(99,102,241,0.2) 100%)',
          borderRadius: '0.75rem',
          border: '2px solid rgba(59,130,246,0.5)',
          color: '#e2e8f0',
        }}>
          <div style={{ fontWeight: 'bold', fontSize: '1rem', marginBottom: '0.5rem', color: '#93c5fd' }}>
            You exited the validator pool
          </div>
          <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
            Rejoin to participate again. Stake at least 32 ETH.
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
            <input
              type="number"
              min="32"
              step="1"
              value={stakeAmount}
              onChange={(e) => setStakeAmount(e.target.value)}
              style={{
                padding: '0.5rem',
                width: '100px',
                background: '#334155',
                border: '1px solid #475569',
                borderRadius: '0.5rem',
                color: '#e2e8f0',
                fontSize: '0.95rem',
              }}
            />
            <span style={{ color: '#94a3b8' }}>ETH</span>
            <button
              onClick={handleRejoin}
              disabled={txPending || committee.length >= poolSize}
              style={{
                padding: '0.5rem 1.25rem',
                background: 'var(--primary)',
                border: 'none',
                borderRadius: '0.5rem',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '0.95rem',
                cursor: txPending ? 'not-allowed' : 'pointer',
              }}
            >
              Rejoin Pool
            </button>
            <span style={{ fontSize: '0.9rem', color: '#64748b' }}>Pool {committee.length}/{poolSize}</span>
          </div>
        </div>
      )}

      {sessionState === 1 && currentSlot === 1 && (
        <div style={{ padding: '1rem', background: 'rgba(59,130,246,0.15)', borderRadius: '0.5rem', marginBottom: '1rem', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.4)' }}>
          <strong>Committees reshuffled for Epoch {currentEpoch}</strong>
          <span style={{ marginLeft: '0.5rem', fontSize: '0.9rem' }}>
            — New committees assigned at epoch start (like Ethereum every ~6.4 min). Each validator is in exactly one committee this epoch.
          </span>
        </div>
      )}

      {!contractSupportsReset && isInstructor && (
        <div style={{ padding: '1rem', background: 'rgba(245,158,11,0.2)', borderRadius: '0.5rem', marginBottom: '1rem', color: '#fcd34d', border: '1px solid rgba(245,158,11,0.5)' }}>
          <strong>Reset requires a fresh deployment.</strong> Run <code>npm run deploy:beacon-lab</code> (with the chain running), then refresh this page.
        </div>
      )}

      {oldFormatWarning && (
        <div style={{ padding: '1rem', background: 'rgba(245,158,11,0.2)', borderRadius: '0.5rem', marginBottom: '1rem', color: '#fcd34d', border: '1px solid rgba(245,158,11,0.5)' }}>
          {oldFormatWarning}
        </div>
      )}
      {error && (
        <div style={{
          padding: '1.25rem',
          background: 'rgba(239,68,68,0.15)',
          borderRadius: '0.75rem',
          marginBottom: '1rem',
          border: '1px solid rgba(239,68,68,0.4)',
        }}>
          <div style={{ color: '#fca5a5', marginBottom: '1rem' }}>{error}</div>
          <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '1rem' }}>
            <strong style={{ color: '#e2e8f0' }}>Fix:</strong>
            <ol style={{ margin: '0.5rem 0 0 1rem', paddingLeft: '0.5rem', lineHeight: 1.7 }}>
              <li>Start the blockchain: <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4 }}>npm run chain</code> (keep the window open)</li>
              <li>Deploy the Beacon Lab: <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4 }}>npm run deploy:beacon-lab</code></li>
              <li>Ensure your RPC is <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4 }}>http://localhost:8545</code> (Connection Setup in Live view)</li>
              <li>Click Retry below after deploying</li>
            </ol>
            <p style={{ margin: '0.75rem 0 0', color: '#64748b', fontSize: '0.85rem' }}>
              Or run <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4 }}>.\start-lab.ps1 -Mode instructor</code> for full setup.
            </p>
          </div>
          <button
            onClick={() => { setError(null); setLoading(true); fetchData(); }}
            style={{
              padding: '0.5rem 1rem',
              background: 'rgba(34, 197, 94, 0.3)',
              border: '1px solid rgba(34, 197, 94, 0.6)',
              borderRadius: '0.5rem',
              color: '#86efac',
              cursor: 'pointer',
              fontSize: '0.9rem',
            }}
          >
            Retry
          </button>
        </div>
      )}

      <ChainSearch provider={readProvider} rpcUrl={rpcUrl} />

      <div className="beacon-lab-grid">
        <div>
          {/* Attest to Block - always visible with buttons (disabled when not applicable) */}
          <div style={{
            marginBottom: '1.5rem',
            padding: '1rem',
            background: 'var(--card)',
            borderRadius: '0.75rem',
            border: '2px solid var(--primary)',
          }}>
            <h3 style={{ marginBottom: '0.75rem', color: 'var(--primary)' }}>Attest to Block</h3>
            {!wallet?.address ? (
              <div style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Connect your wallet to attest.</div>
            ) : useOldBlockFormat ? (
              <div style={{ fontSize: '0.9rem', color: '#f59e0b' }}>Redeploy the contract for attestation: <code>npm run deploy:beacon-lab</code></div>
            ) : (
              <>
                {(sessionState === 1 && userInPool && !getStats(wallet?.address)?.slashed) && (
                  <div style={{ marginBottom: '0.5rem' }}>
                    <div style={{ fontWeight: 'bold', color: '#94a3b8', fontSize: '0.85rem' }}>
                      Attestation progress: {attestationProgress.toFixed(0)}% (threshold: {quorumThreshold} ETH)
                    </div>
                    <div style={{ height: '8px', background: '#334155', borderRadius: '4px', marginTop: '0.25rem', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${Math.min(100, attestationProgress)}%`, background: 'var(--primary)' }} />
                    </div>
                    {requireHumanAttestation && latestBlock && (
                      <div style={{ fontSize: '0.8rem', color: latestBlock.humanAttestationCount >= 1 ? '#22c55e' : '#f59e0b', marginTop: '0.25rem' }}>
                        Human attestations: {latestBlock.humanAttestationCount || 0}/1 required
                      </div>
                    )}
                  </div>
                )}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Block: </label>
                  <select
                    value={attestableBlocks.length > 0 ? attestBlockIndex : 0}
                    onChange={(e) => setAttestBlockIndex(Number(e.target.value))}
                    disabled={attestableBlocks.length === 0}
                    style={{
                      padding: '0.35rem 0.5rem',
                      background: '#334155',
                      border: '1px solid #475569',
                      borderRadius: '0.35rem',
                      color: '#e2e8f0',
                      fontSize: '0.85rem',
                      minWidth: '140px',
                      cursor: attestableBlocks.length === 0 ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {attestableBlocks.length > 0 ? (
                      attestableBlocks.map((b) => {
                        const attested = getAttested(wallet?.address, b.index);
                        return (
                          <option key={b.index} value={b.index} disabled={attested}>
                            #{b.index} slot {b.slot} {attested ? '(attested)' : ''}
                          </option>
                        );
                      })
                    ) : blocks.length > 0 ? (
                      <option value={0}>No blocks in your committee — wait for next slot</option>
                    ) : (
                      <option value={0}>No blocks yet — wait ~12s</option>
                    )}
                  </select>
                  <button
                    onClick={() => handleAttest(false)}
                    disabled={!wallet?.address || txPending || sessionState !== 1 || !userInPool || !!getStats(wallet?.address)?.slashed || attestableBlocks.length === 0 || !!getAttested(wallet?.address, attestBlockIndex)}
                    style={{
                      padding: '0.5rem 1.25rem',
                      background: 'var(--primary)',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: 'white',
                      fontWeight: 'bold',
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      opacity: (!wallet?.address || sessionState !== 1 || !userInPool || !!getStats(wallet?.address)?.slashed || attestableBlocks.length === 0 || !!getAttested(wallet?.address, attestBlockIndex)) ? 0.6 : 1,
                    }}
                  >
                    {getAttested(wallet?.address, attestBlockIndex) ? 'Attested' : 'Attest'}
                  </button>
                  {!userInPool && !userExited && (sessionState === 0 || sessionState === 1) && committee.length < poolSize && (
                    <>
                      <input
                        type="number"
                        min="32"
                        step="1"
                        value={stakeAmount}
                        onChange={(e) => setStakeAmount(e.target.value)}
                        style={{
                          padding: '0.35rem 0.5rem',
                          width: '70px',
                          background: '#334155',
                          border: '1px solid #475569',
                          borderRadius: '0.35rem',
                          color: '#e2e8f0',
                          fontSize: '0.9rem',
                        }}
                      />
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>ETH</span>
                      <button
                        onClick={handleJoin}
                        disabled={txPending || committee.length >= poolSize}
                        style={{
                          padding: '0.5rem 1rem',
                          background: '#22c55e',
                          border: 'none',
                          borderRadius: '0.5rem',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.9rem',
                          cursor: txPending ? 'not-allowed' : 'pointer',
                        }}
                      >
                        Join
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => handleAttest(true)}
                    disabled={!wallet?.address || txPending || sessionState !== 1 || !userInPool || !!getStats(wallet?.address)?.slashed || attestableBlocks.length === 0 || !!getAttested(wallet?.address, attestBlockIndex)}
                    title="Attest with wrong hash to demonstrate slashing"
                    style={{
                      padding: '0.5rem 0.75rem',
                      background: '#f59e0b',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: 'white',
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      opacity: (!wallet?.address || sessionState !== 1 || !userInPool || !!getStats(wallet?.address)?.slashed || attestableBlocks.length === 0 || !!getAttested(wallet?.address, attestBlockIndex)) ? 0.6 : 1,
                    }}
                  >
                    Demo slash
                  </button>
                  {userExited && (sessionState === 0 || sessionState === 1) && committee.length < poolSize && (
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <input
                        type="number"
                        min="32"
                        step="1"
                        value={stakeAmount}
                        onChange={(e) => setStakeAmount(e.target.value)}
                        style={{
                          padding: '0.35rem 0.5rem',
                          width: '70px',
                          background: '#334155',
                          border: '1px solid #475569',
                          borderRadius: '0.35rem',
                          color: '#e2e8f0',
                          fontSize: '0.9rem',
                        }}
                      />
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>ETH</span>
                      <button
                        onClick={handleRejoin}
                        disabled={txPending || committee.length >= poolSize}
                        style={{
                          padding: '0.5rem 1rem',
                          background: 'var(--primary)',
                          border: 'none',
                          borderRadius: '0.5rem',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.9rem',
                          cursor: txPending ? 'not-allowed' : 'pointer',
                        }}
                      >
                        Rejoin
                      </button>
                    </div>
                  )}
                  {userInPool && sessionState === 1 && !getStats(wallet?.address)?.slashed && (
                    <button
                      onClick={handleExit}
                      disabled={txPending}
                      title="Voluntarily exit and withdraw your stake"
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#64748b',
                        border: 'none',
                        borderRadius: '0.5rem',
                        color: 'white',
                        fontSize: '0.9rem',
                        cursor: txPending ? 'not-allowed' : 'pointer',
                        opacity: txPending ? 0.6 : 1,
                      }}
                    >
                      Exit validator pool
                    </button>
                  )}
                </div>
                {sessionState !== 1 && (
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                    Join the pool below. Instructor clicks <strong>Fill Bots and Start</strong> to begin.
                  </div>
                )}
                {sessionState === 1 && !userInPool && !userExited && (
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                    Join the validator pool below (stake 32+ ETH) to attest. You can join anytime.
                  </div>
                )}
                {sessionState === 1 && userExited && (
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                    You exited. Use Rejoin above to stake again and participate.
                  </div>
                )}
                {sessionState === 1 && blocks.length === 0 && (
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                    Blocks are proposed automatically every ~12s when the instructor has this page open.
                  </div>
                )}
                {(blocks.length > 0 || attestableBlocks.length > 0) && (
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.35rem' }}>
                    Only blocks in your committee are shown (up to the last 2). Committee for slot S = (S−1) % {committeesPerEpoch}.
                  </div>
                )}
                <details style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
                  <summary style={{ cursor: 'pointer', color: 'var(--primary)', fontWeight: 600 }}>What is attestation? (5 Ws + how)</summary>
                  <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'rgba(59,130,246,0.08)', borderRadius: '0.5rem', color: '#94a3b8', lineHeight: 1.5 }}>
                    <div style={{ marginBottom: '0.4rem' }}><strong style={{ color: '#e2e8f0' }}>Who</strong> — Validators in the committee for that block&apos;s slot (you, if you&apos;re in that committee).</div>
                    <div style={{ marginBottom: '0.4rem' }}><strong style={{ color: '#e2e8f0' }}>What</strong> — Attestation = you vote that you saw block X with hash H. You&apos;re saying &quot;I agree this block is canonical.&quot;</div>
                    <div style={{ marginBottom: '0.4rem' }}><strong style={{ color: '#e2e8f0' }}>When</strong> — After a block is proposed, before the next epoch. You attest to recent blocks (last 2 here).</div>
                    <div style={{ marginBottom: '0.4rem' }}><strong style={{ color: '#e2e8f0' }}>Where</strong> — On-chain. Your vote is recorded in the contract and counts toward the attestation progress bar.</div>
                    <div style={{ marginBottom: '0.4rem' }}><strong style={{ color: '#e2e8f0' }}>Why</strong> — Reach the 2/3 justification threshold so blocks become justified, then finalized. Finality = consensus that the chain won&apos;t revert.</div>
                    <div><strong style={{ color: '#e2e8f0' }}>How</strong> — Pick a block, click Attest. The contract sends your vote with the block&apos;s canonical hash. Demo slash does the same but with a wrong hash.</div>
                  </div>
                </details>
                <details style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
                  <summary style={{ cursor: 'pointer', color: '#f59e0b', fontWeight: 600 }}>What does Demo slash do?</summary>
                  <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'rgba(245,158,11,0.08)', borderRadius: '0.5rem', color: '#94a3b8', lineHeight: 1.5 }}>
                    Demo slash attests with a <strong>wrong hash</strong> — as if you&apos;re lying about a block. The contract detects this and slashes you (~5% penalty). Use it to see how slash evidence appears on-chain (wrong attestation). You can click the block afterward to view the slash details.
                  </div>
                </details>
              </>
            )}
          </div>

          <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Validator Pool</h3>
          <details style={{ marginBottom: '1rem', fontSize: '0.85rem', color: '#94a3b8' }}>
            <summary style={{ cursor: 'pointer', color: 'var(--primary)' }}>How committees form</summary>
            <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'rgba(59,130,246,0.1)', borderRadius: '0.5rem' }}>
              <p style={{ marginBottom: '0.5rem' }}>
                Validators join the pool. At epoch start, validators are assigned to {committeesPerEpoch} committees (round-robin).
                Committee for slot S = (S-1) % {committeesPerEpoch}. Only validators in that committee can attest to blocks at that slot.
                <strong> Each validator belongs to exactly one committee per epoch.</strong> This prevents collusion by rotating assignments.
              </p>
              <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
                On Ethereum mainnet, committees reshuffle every epoch (~6.4 min). Sync Committees are different—they last 256 epochs (~27 hours).
              </p>
            </div>
          </details>
          {epochCommittees && sessionState === 1 && (
            <details style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
              <summary style={{ cursor: 'pointer', color: 'var(--primary)' }}>Committees for Epoch {epochCommittees.epoch}</summary>
              <div style={{ marginTop: '0.5rem', overflowX: 'auto', border: '1px solid #334155', borderRadius: '0.5rem' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                  <thead>
                    <tr style={{ background: '#334155', color: '#94a3b8' }}>
                      <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Committee</th>
                      <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Slot</th>
                      <th style={{ padding: '0.4rem 0.6rem', textAlign: 'right' }}>Size</th>
                      <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Validators</th>
                    </tr>
                  </thead>
                  <tbody>
                    {epochCommittees.committees.map((members, i) => {
                      const isUserCommittee = members.some((m) => m?.toLowerCase() === wallet?.address?.toLowerCase());
                      return (
                      <tr
                        key={i}
                        style={{
                          borderBottom: '1px solid #334155',
                          background: isUserCommittee ? 'rgba(59,130,246,0.15)' : undefined,
                          borderLeft: isUserCommittee ? '3px solid var(--primary)' : undefined,
                        }}
                      >
                        <td style={{ padding: '0.4rem 0.6rem', color: '#e2e8f0' }}>{i}{isUserCommittee ? ' (you)' : ''}</td>
                        <td style={{ padding: '0.4rem 0.6rem', color: '#94a3b8' }}>
                          {(epochCommittees.epoch - 1) * blocksPerEpoch + i + 1}
                        </td>
                        <td style={{ padding: '0.4rem 0.6rem', textAlign: 'right', color: '#e2e8f0' }}>{members.length}</td>
                        <td style={{ padding: '0.4rem 0.6rem', color: '#94a3b8', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {members.map((m, midx) => (
                            <span
                              key={m ? `${m}-${midx}` : `empty-${i}-${midx}`}
                              style={{
                                display: 'inline-block',
                                marginRight: '0.25rem',
                                padding: '0.1rem 0.2rem',
                                background: m?.toLowerCase() === wallet?.address?.toLowerCase() ? 'rgba(59,130,246,0.3)' : 'transparent',
                                borderRadius: '0.2rem',
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                              }}
                            >
                              {m ? `${m.slice(0, 8)}...` : ''}
                            </span>
                          ))}
                        </td>
                      </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </details>
          )}
          {committeeForSlot && (
            <div style={{ marginBottom: '1rem', padding: '0.5rem', background: 'rgba(34,197,94,0.1)', borderRadius: '0.5rem', fontSize: '0.85rem' }}>
              Your committee for current slot: {committeeForSlot.members.some((m) => m?.toLowerCase() === wallet?.address?.toLowerCase()) ? 'Yes' : 'No'}
            </div>
          )}

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
            gap: '0.75rem',
          }}>
            {committee.map((addr) => {
              const stats = getStats(addr);
              const isProposer = lastProposer && addr.toLowerCase() === lastProposer.toLowerCase();
              const attested = latestBlockIndex !== null && getAttested(addr, latestBlockIndex);
              const isSelected = selectedValidator && addr.toLowerCase() === selectedValidator.toLowerCase();
              return (
                <div
                  key={addr}
                  role="button"
                  tabIndex={0}
                  onClick={() => selectValidator(isSelected ? null : addr)}
                  onKeyDown={(e) => e.key === 'Enter' && selectValidator(isSelected ? null : addr)}
                  style={{
                    padding: '0.75rem',
                    background: isSelected ? 'rgba(59,130,246,0.2)' : 'var(--card)',
                    borderRadius: '0.5rem',
                    border: `2px solid ${isSelected ? '#3b82f6' : isProposer ? 'var(--primary)' : '#334155'}`,
                    position: 'relative',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#94a3b8' }}>
                    {addr.slice(0, 12)}...
                  </div>
                  <div style={{ marginTop: '0.5rem', fontWeight: 'bold', color: '#e2e8f0' }}>
                    {stats?.stake || '0'} ETH
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                    {stats?.isBot ? '🤖 Bot' : '👤 Human'}
                    {stats?.slashed && ' · ⚠️ Slashed'}
                    {stats?.exited && ' · 🚪 Exited'}
                    {attested && !stats?.exited && ' · ✓ Attested'}
                  </div>
                </div>
              );
            })}
          </div>

          <h3 style={{ marginTop: '1.5rem', marginBottom: '1rem', color: 'var(--primary)' }}>Proposer Selection Stats</h3>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
            Proposer selection is stake-weighted. Higher stake = higher chance to be chosen. Compare expected % (stake share) vs actual % (blocks proposed) to see the correlation.
          </div>
          {blocks.length === 0 ? (
            <div style={{ padding: '1rem', background: 'var(--card)', borderRadius: '0.5rem', border: '1px solid #475569', color: '#94a3b8', fontSize: '0.9rem' }}>
              Propose blocks to see proposer selection stats. Stake-weighted selection determines who proposes each block.
            </div>
          ) : (
            <div style={{ overflowX: 'auto', borderRadius: '0.5rem', border: '1px solid #475569' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: '#334155', color: '#94a3b8' }}>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Validator</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Stake (ETH)</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Expected %</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Blocks proposed</th>
                    <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Actual %</th>
                  </tr>
                </thead>
                <tbody>
                  {proposerStats.map((p) => {
                    const isCurrentUser = wallet?.address && p.address.toLowerCase() === wallet.address.toLowerCase();
                    const isSelected = selectedValidator && p.address.toLowerCase() === selectedValidator.toLowerCase();
                    return (
                      <tr
                        key={p.address}
                        onClick={() => selectValidator(isSelected ? null : p.address)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => e.key === 'Enter' && selectValidator(isSelected ? null : p.address)}
                        style={{
                          cursor: 'pointer',
                          background: isCurrentUser ? 'rgba(59,130,246,0.15)' : isSelected ? 'rgba(59,130,246,0.2)' : 'var(--card)',
                          borderBottom: '1px solid #334155',
                        }}
                      >
                        <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace', fontSize: '0.8rem', color: '#e2e8f0' }}>{p.address.slice(0, 12)}...</td>
                        <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#e2e8f0' }}>{p.stake}</td>
                        <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>{p.stakePercent.toFixed(2)}%</td>
                        <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#e2e8f0' }}>{p.blocksProposed}</td>
                        <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>{p.actualPercent.toFixed(2)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          <h3 style={{ marginTop: '1.5rem', marginBottom: '1rem', color: 'var(--primary)' }}>Latest Blocks</h3>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.5rem' }}>Click a row to view details (attestations, slashings). <strong>Chain Block</strong> = real Hardhat block that contains this propose tx.</div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <span><strong style={{ color: '#94a3b8' }}>Proposed</strong> — awaiting attestations</span>
            <span><strong style={{ color: '#3b82f6' }}>Justified</strong> — 2/3 stake attested</span>
            <span><strong style={{ color: '#22c55e' }}>Finalized</strong> — checkpoint finalized</span>
          </div>
          {blocks.length > 0 && !blocks.some((b) => b.justified || b.finalized) && sessionState === 1 && (
            <div style={{ fontSize: '0.8rem', padding: '0.5rem 0.75rem', background: 'rgba(245,158,11,0.12)', borderRadius: '0.5rem', marginBottom: '0.75rem', color: '#fcd34d', border: '1px solid rgba(245,158,11,0.3)' }}>
              <strong>All blocks &quot;proposed&quot;?</strong> Justification needs 2/3 of total stake to attest. With {committeesPerEpoch} committee{committeesPerEpoch !== 1 ? 's' : ''}, each block gets ~{committeesPerEpoch > 1 ? Math.round(100 / committeesPerEpoch) : 100}% of stake — {committeesPerEpoch > 1 ? 'justification threshold may be unreachable. Redeploy with COMMITTEES_PER_EPOCH=1 for small classes.' : 'attest to reach the justification threshold.'}
            </div>
          )}
          <div style={{ overflowX: 'auto', borderRadius: '0.5rem', border: '1px solid #475569' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ background: '#334155', color: '#94a3b8' }}>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Epoch</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Slot</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Pos</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Att</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Slash</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Proposer</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Beacon Hash</th>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left' }}>Chain Block</th>
                </tr>
              </thead>
              <tbody>
                {blocks.map((b) => {
                  const bEpoch = Math.floor(b.index / blocksPerEpoch);
                  const isFork = blocks.some((o) => o.index !== b.index && o.slot === b.slot && Math.floor(o.index / blocksPerEpoch) === bEpoch);
                  const isOrphaned = isFork && !canonicalBlockIndices.has(b.index);
                  const isSelected = selectedBlockIndex === b.index;
                  const epoch = Math.floor(b.index / blocksPerEpoch) + 1;
                  const posInEpoch = ((b.slot - 1) % blocksPerEpoch) + 1;
                  const status = b.finalized ? 'finalized' : isOrphaned ? 'orphaned' : b.justified ? 'justified' : isFork ? 'fork' : 'proposed';
                  const slashCount = blockSlashCounts.get(b.index) || 0;
                  return (
                    <tr
                      key={b.index}
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); selectBlock(isSelected ? null : b.index); }}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => { e.preventDefault(); if (e.key === 'Enter') selectBlock(isSelected ? null : b.index); }}
                      style={{
                        cursor: 'pointer',
                        background: isSelected ? 'rgba(59,130,246,0.2)' : b.finalized ? 'rgba(34,197,94,0.1)' : isOrphaned ? 'rgba(148,163,184,0.15)' : isFork ? 'rgba(245,158,11,0.1)' : 'var(--card)',
                        borderBottom: '1px solid #334155',
                      }}
                    >
                      <td style={{ padding: '0.5rem 0.75rem', color: '#e2e8f0' }}>{epoch}</td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#e2e8f0' }}>{b.slot}</td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#94a3b8' }}>{posInEpoch} of {blocksPerEpoch}</td>
                      <td style={{ padding: '0.5rem 0.75rem' }}>
                        <span style={{
                          color: status === 'finalized' ? '#22c55e' : status === 'orphaned' ? '#94a3b8' : status === 'justified' ? '#3b82f6' : status === 'fork' ? '#f59e0b' : '#94a3b8',
                          fontWeight: status !== 'proposed' ? 600 : 400,
                        }}>
                          {status.charAt(0).toUpperCase() + status.slice(1)}
                        </span>
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#e2e8f0' }}>{b.attestationCount}</td>
                      <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>
                        {slashCount > 0 ? (
                          <span style={{ padding: '0.1rem 0.4rem', background: 'rgba(239,68,68,0.3)', color: '#fca5a5', borderRadius: '0.25rem' }}>
                            {slashCount}
                          </span>
                        ) : '0'}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#94a3b8', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {b.proposer ? `${b.proposer.slice(0, 10)}...` : '—'}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#94a3b8', fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all' }}>
                        {b.blockHash ? `${String(b.blockHash).slice(0, 18)}...` : '—'}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#86efac', fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all' }} title={blockIndexToEthBlock.get(b.index)?.blockHash}>
                        {blockIndexToEthBlock.get(b.index) ? (
                          <>#{blockIndexToEthBlock.get(b.index).blockNumber} {blockIndexToEthBlock.get(b.index).blockHash ? `${String(blockIndexToEthBlock.get(b.index).blockHash).slice(0, 18)}...` : ''}</>
                        ) : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {selectedBlockIndex !== null && blocks[selectedBlockIndex] && (
            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: 'var(--card)',
              borderRadius: '0.75rem',
              border: '1px solid #475569',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h4 style={{ color: 'var(--primary)' }}>Slot {blocks[selectedBlockIndex].slot} — Block #{selectedBlockIndex}</h4>
                <button
                  onClick={() => selectBlock(null)}
                  style={{ padding: '0.25rem 0.5rem', background: '#334155', border: 'none', borderRadius: '0.5rem', color: '#94a3b8', cursor: 'pointer' }}
                >
                  Close
                </button>
              </div>
              {(() => {
                const b = blocks[selectedBlockIndex];
                const bEpoch = Math.floor(b.index / blocksPerEpoch);
                const isFork = blocks.some((o) => o.index !== b.index && o.slot === b.slot && Math.floor(o.index / blocksPerEpoch) === bEpoch);
                const isOrphaned = isFork && !canonicalBlockIndices.has(b.index);
                const epoch = Math.floor(b.index / blocksPerEpoch) + 1;
                const parentIdx = b.parentHash ? findBlockByHash(b.parentHash) : null;
                const attesterSlashCount = blockDetailData?.slashEvents?.length ?? blockSlashCounts.get(selectedBlockIndex) ?? 0;
                const statusLabel = b.finalized ? 'Finalized' : isOrphaned ? 'Orphaned' : b.justified ? 'Justified' : isFork ? 'Fork (proposed)' : 'Proposed';
                const statusColor = b.finalized ? '#22c55e' : isOrphaned ? '#94a3b8' : b.justified ? '#3b82f6' : '#94a3b8';
                return (
                  <div style={{ fontSize: '0.9rem' }}>
                    <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.25rem' }}>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Epoch</span>
                        <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{epoch}</div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Status</span>
                        <div style={{ color: statusColor, fontWeight: 600 }}>
                          {statusLabel}{isOrphaned && ' — not on canonical chain'}
                        </div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Proposer</span>
                        <div>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); selectValidator(b.proposer); }}
                            style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontFamily: 'monospace', fontSize: '0.9rem', padding: 0, textDecoration: 'underline' }}
                          >
                            {b.proposer}
                          </button>
                        </div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Block Root Hash</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <code style={{ fontSize: '0.8rem', wordBreak: 'break-all', color: '#e2e8f0' }}>{b.blockHash || '—'}</code>
                          {b.blockHash && (
                            <button
                              type="button"
                              onClick={() => copyToClipboard(b.blockHash)}
                              style={{ padding: '0.2rem 0.4rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', cursor: 'pointer', fontSize: '0.75rem' }}
                            >
                              Copy
                            </button>
                          )}
                        </div>
                      </div>
                      {blockIndexToEthBlock.get(b.index) && (
                        <div>
                          <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Chain Block (Hardhat)</span>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <code style={{ fontSize: '0.8rem', wordBreak: 'break-all', color: '#86efac' }}>
                              #{blockIndexToEthBlock.get(b.index).blockNumber} · {blockIndexToEthBlock.get(b.index).blockHash || '—'}
                            </code>
                            {blockIndexToEthBlock.get(b.index).blockHash && (
                              <button
                                type="button"
                                onClick={() => copyToClipboard(blockIndexToEthBlock.get(b.index).blockHash)}
                                style={{ padding: '0.2rem 0.4rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', cursor: 'pointer', fontSize: '0.75rem' }}
                              >
                                Copy
                              </button>
                            )}
                          </div>
                        </div>
                      )}
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Parent Root Hash</span>
                        <div>
                          {b.parentHash ? (
                            parentIdx != null ? (
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); selectBlock(parentIdx); }}
                                style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontFamily: 'monospace', fontSize: '0.8rem', padding: 0, textDecoration: 'underline', wordBreak: 'break-all', textAlign: 'left' }}
                              >
                                {b.parentHash}
                              </button>
                            ) : (
                              <code style={{ fontSize: '0.8rem', wordBreak: 'break-all', color: '#94a3b8' }}>{b.parentHash}</code>
                            )
                          ) : (
                            <span style={{ color: '#64748b' }}>—</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Slashing P/A</span>
                        <div style={{ color: '#e2e8f0' }}>0 proposer slashed / {attesterSlashCount} attester slashed</div>
                      </div>
                    </div>
                    <h5 style={{ color: '#94a3b8', marginBottom: '0.5rem' }}>Attestations ({b.attestationCount})</h5>
                    {blockDetailData?.attestations?.length > 0 ? (
                      <div style={{ overflowX: 'auto', marginBottom: '1rem', border: '1px solid #334155', borderRadius: '0.5rem' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                          <thead>
                            <tr style={{ background: '#334155', color: '#94a3b8' }}>
                              <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Validator</th>
                              <th style={{ padding: '0.4rem 0.6rem', textAlign: 'right' }}>Stake</th>
                            </tr>
                          </thead>
                          <tbody>
                            {blockDetailData.attestations.map((a) => (
                              <tr key={a.address} style={{ borderBottom: '1px solid #334155' }}>
                                <td style={{ padding: '0.4rem 0.6rem' }}>
                                  <button
                                    type="button"
                                    onClick={(e) => { e.stopPropagation(); selectValidator(a.address); }}
                                    style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontFamily: 'monospace', fontSize: '0.85rem', padding: 0, textDecoration: 'underline' }}
                                  >
                                    {a.address}
                                  </button>
                                </td>
                                <td style={{ padding: '0.4rem 0.6rem', textAlign: 'right', color: '#e2e8f0' }}>{a.stake} ETH</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div style={{ color: '#64748b', marginBottom: '1rem' }}>No attestations yet</div>
                    )}
                    <h5 style={{ color: '#94a3b8', marginBottom: '0.5rem' }}>Transactions in Chain Block</h5>
                    {blockDetailData?.transactions?.length > 0 ? (
                      <div style={{ overflowX: 'auto', marginBottom: '1rem', border: '1px solid #334155', borderRadius: '0.5rem' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                          <thead>
                            <tr style={{ background: '#334155', color: '#94a3b8' }}>
                              <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Hash</th>
                              <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>From</th>
                              <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>To</th>
                              <th style={{ padding: '0.4rem 0.6rem', textAlign: 'right' }}>Value</th>
                            </tr>
                          </thead>
                          <tbody>
                            {blockDetailData.transactions.map((tx) => (
                              <tr key={tx.hash} style={{ borderBottom: '1px solid #334155' }}>
                                <td style={{ padding: '0.4rem 0.6rem', fontFamily: 'monospace', fontSize: '0.8rem', wordBreak: 'break-all' }}>{tx.hash}</td>
                                <td style={{ padding: '0.4rem 0.6rem', fontFamily: 'monospace', fontSize: '0.8rem', wordBreak: 'break-all' }}>{tx.from ?? '—'}</td>
                                <td style={{ padding: '0.4rem 0.6rem', fontFamily: 'monospace', fontSize: '0.8rem', wordBreak: 'break-all' }}>{tx.to ?? '—'}</td>
                                <td style={{ padding: '0.4rem 0.6rem', textAlign: 'right', color: '#e2e8f0' }}>{tx.value != null ? ethers.formatEther(tx.value) : '—'} ETH</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div style={{ color: '#64748b', marginBottom: '1rem' }}>No transactions in this chain block</div>
                    )}
                    <h5 style={{ color: '#94a3b8', marginBottom: '0.5rem' }}>Slashings</h5>
                    {blockDetailData?.slashEvents?.length > 0 ? (
                      <div style={{ display: 'grid', gap: '0.75rem' }}>
                        {blockDetailData.slashEvents.map((s, i) => {
                          const ev = s.type === 'wrong_attestation'
                            ? { reason: 1, blockIndex: s.blockIndex, slot: blocks[s.blockIndex]?.slot ?? 0, expectedHash: s.expectedHash, attestedHash: s.attestedHash, firstBlock: 0, secondBlock: 0 }
                            : s.type === 'double_vote'
                              ? { reason: 2, blockIndex: 0, slot: s.slot, expectedHash: ethers.ZeroHash, attestedHash: ethers.ZeroHash, firstBlock: s.firstBlock, secondBlock: s.secondBlock }
                              : null;
                          return (
                            <div key={i} style={{ padding: '0.75rem', background: 'rgba(239,68,68,0.15)', borderRadius: '0.5rem', border: '1px solid rgba(239,68,68,0.4)' }}>
                              <div style={{ fontWeight: 'bold', color: '#fca5a5' }}>
                                {s.type === 'wrong_attestation' ? 'Wrong attestation' : 'Double vote'}:{' '}
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); selectValidator(s.validator); }}
                                  style={{ background: 'none', border: 'none', color: '#fca5a5', cursor: 'pointer', fontFamily: 'monospace', fontSize: 'inherit', padding: 0, textDecoration: 'underline' }}
                                >
                                  {String(s.validator).slice(0, 14)}...
                                </button>
                              </div>
                              {ev && <SlashEvidenceChain ev={ev} validator={s.validator} onSelectBlock={(idx) => { selectBlock(idx); }} />}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div style={{ color: '#64748b' }}>No slashings for this block</div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          {selectedValidator && committee.some((c) => c.toLowerCase() === selectedValidator.toLowerCase()) && (
            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: 'var(--card)',
              borderRadius: '0.75rem',
              border: '1px solid #475569',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h4 style={{ color: 'var(--primary)' }}>Validator Details</h4>
                <button
                  type="button"
                  onClick={() => selectValidator(null)}
                  style={{ padding: '0.25rem 0.5rem', background: '#334155', border: 'none', borderRadius: '0.5rem', color: '#94a3b8', cursor: 'pointer' }}
                >
                  Close
                </button>
              </div>
              {(() => {
                const stats = getStats(selectedValidator);
                return (
                  <div style={{ fontSize: '0.9rem' }}>
                    <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.25rem' }}>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Address</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <code style={{ fontSize: '0.85rem', wordBreak: 'break-all', color: '#e2e8f0' }}>{selectedValidator}</code>
                          <button
                            type="button"
                            onClick={() => copyToClipboard(selectedValidator)}
                            style={{ padding: '0.2rem 0.4rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', cursor: 'pointer', fontSize: '0.75rem' }}
                          >
                            Copy
                          </button>
                        </div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Stake</span>
                        <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{stats?.stake || '0'} ETH</div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Status</span>
                        <div style={{ color: '#e2e8f0' }}>
                          {stats?.isBot ? 'Bot' : 'Human'}
                          {stats?.slashed && ' · Slashed'}
                        </div>
                      </div>
                      {validatorDetailData && (
                        <div>
                          <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Proposed blocks</span>
                          <div style={{ color: '#e2e8f0' }}>{validatorDetailData.proposedCount}</div>
                        </div>
                      )}
                    </div>
                    <h5 style={{ color: '#94a3b8', marginBottom: '0.5rem' }}>Attestations</h5>
                    {validatorDetailData?.attestedBlocks?.length > 0 ? (
                      <div style={{ display: 'grid', gap: '0.25rem', marginBottom: '1rem' }}>
                        {validatorDetailData.attestedBlocks.map((ab) => (
                          <div key={ab.blockIndex} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <button
                              type="button"
                              onClick={(e) => { e.stopPropagation(); selectBlock(ab.blockIndex); }}
                              style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '0.85rem', padding: 0, textDecoration: 'underline' }}
                            >
                              Block #{ab.blockIndex}
                            </button>
                            <span style={{ color: '#64748b', fontSize: '0.8rem' }}>slot {ab.slot}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ color: '#64748b', marginBottom: '1rem' }}>No attestations yet</div>
                    )}
                    <h5 style={{ color: '#94a3b8', marginBottom: '0.5rem' }}>Slash events</h5>
                    {validatorDetailData?.slashEvents?.length > 0 ? (
                      <div style={{ display: 'grid', gap: '0.75rem' }}>
                        {validatorDetailData.slashEvents.map((s, i) => {
                          const ev = s.type === 'wrong_attestation'
                            ? { reason: 1, blockIndex: s.blockIndex, slot: blocks[s.blockIndex]?.slot ?? 0, expectedHash: s.expectedHash, attestedHash: s.attestedHash, firstBlock: 0, secondBlock: 0 }
                            : s.type === 'double_vote'
                              ? { reason: 2, blockIndex: 0, slot: s.slot, expectedHash: ethers.ZeroHash, attestedHash: ethers.ZeroHash, firstBlock: s.firstBlock, secondBlock: s.secondBlock }
                              : null;
                          return (
                            <div key={i} style={{ padding: '0.75rem', background: 'rgba(239,68,68,0.15)', borderRadius: '0.5rem', border: '1px solid rgba(239,68,68,0.4)' }}>
                              <div style={{ fontWeight: 'bold', color: '#fca5a5' }}>
                                {s.type === 'wrong_attestation' ? 'Wrong attestation' : s.type === 'double_vote' ? 'Double vote' : 'Manual'}
                                {s.type === 'wrong_attestation' && ` (block #${s.blockIndex})`}
                              </div>
                              {s.type === 'manual' && s.reason && (
                                <div style={{ fontSize: '0.85rem', marginTop: '0.35rem', color: '#fca5a5' }}>Reason: {s.reason}</div>
                              )}
                              {ev && <SlashEvidenceChain ev={ev} validator={selectedValidator} onSelectBlock={(idx) => selectBlock(idx)} />}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div style={{ color: '#64748b' }}>No slash events</div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          {sessionState === 1 && (userExited || getStats(wallet?.address)?.slashed) && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--card)', borderRadius: '0.75rem', border: '1px solid #475569' }}>
              <h4 style={{ marginBottom: '0.5rem', color: '#94a3b8' }}>Validator status</h4>
              {userExited ? (
                <>
                  <p style={{ fontSize: '0.9rem', color: '#94a3b8' }}>You have exited the pool. Your stake was refunded.</p>
                  {committee.length < poolSize && (sessionState === 0 || sessionState === 1) && (
                    <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <input
                        type="number"
                        min="32"
                        step="1"
                        value={stakeAmount}
                        onChange={(e) => setStakeAmount(e.target.value)}
                        style={{
                          padding: '0.5rem',
                          width: '100px',
                          background: '#334155',
                          border: '1px solid #475569',
                          borderRadius: '0.5rem',
                          color: '#e2e8f0',
                        }}
                      />
                      <span style={{ color: '#94a3b8' }}>ETH</span>
                      <button
                        onClick={handleRejoin}
                        disabled={txPending || committee.length >= poolSize}
                        style={{
                          padding: '0.5rem 1rem',
                          background: 'var(--primary)',
                          border: 'none',
                          borderRadius: '0.5rem',
                          color: 'white',
                          fontWeight: 'bold',
                          cursor: txPending ? 'not-allowed' : 'pointer',
                        }}
                      >
                        Rejoin
                      </button>
                      <span style={{ fontSize: '0.85rem', color: '#64748b' }}>Pool {committee.length}/{poolSize}</span>
                    </div>
                  )}
                </>
              ) : getStats(wallet?.address)?.slashed ? (
                <p style={{ fontSize: '0.9rem', color: '#fca5a5' }}>You have been slashed. You cannot attest or exit.</p>
              ) : null}
            </div>
          )}

          {isInstructor && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--card)', borderRadius: '0.75rem', border: '1px solid #475569' }}>
              <h4 style={{ marginBottom: '0.75rem', color: '#e2e8f0' }}>Instructor Controls</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
                {sessionState === 0 && (
                  <>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid #334155', marginBottom: '0.5rem' }}>
                      <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Validators per committee:</span>
                      <input
                        type="number"
                        min="1"
                        max="256"
                        value={validatorsPerCommitteeInput}
                        onChange={(e) => setValidatorsPerCommitteeInput(e.target.value)}
                        style={{
                          padding: '0.35rem 0.5rem',
                          width: '60px',
                          background: '#334155',
                          border: '1px solid #475569',
                          borderRadius: '0.35rem',
                          color: '#e2e8f0',
                          fontSize: '0.9rem',
                        }}
                      />
                      <button
                        type="button"
                        onClick={handleSetValidatorsPerCommittee}
                        disabled={txPending || parseInt(validatorsPerCommitteeInput, 10) === validatorsPerCommittee}
                        style={{
                          padding: '0.35rem 0.75rem',
                          background: '#475569',
                          border: 'none',
                          borderRadius: '0.35rem',
                          color: '#e2e8f0',
                          fontSize: '0.85rem',
                          cursor: txPending ? 'not-allowed' : 'pointer',
                        }}
                      >
                        Set
                      </button>
                      <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                        Pool size: {committeesPerEpoch * (parseInt(validatorsPerCommitteeInput, 10) || validatorsPerCommittee)} ({committeesPerEpoch} × validators). Smaller = less gas.
                      </span>
                    </div>
                    {committee.length === 0 && (
                      <div style={{ padding: '0.75rem', background: 'rgba(251, 191, 36, 0.15)', borderRadius: '0.5rem', border: '1px solid rgba(251, 191, 36, 0.4)', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#fde047' }}>
                        ⚠️ <strong>Join the pool first:</strong> At least one validator must join before starting. Use <strong>Join &amp; Start</strong> below (one click) or Join above, then Fill Bots and Start.
                      </div>
                    )}
                    {committee.length === 0 && (
                      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                        <button
                          onClick={handleJoinAndStart}
                          disabled={txPending}
                          title="Join as instructor (stake 32 ETH) and immediately fill bots and start"
                          style={{
                            padding: '0.5rem 1rem',
                            background: '#f59e0b',
                            border: 'none',
                            borderRadius: '0.5rem',
                            color: 'white',
                            fontWeight: 'bold',
                            cursor: txPending ? 'not-allowed' : 'pointer',
                          }}
                        >
                          Join &amp; Start
                        </button>
                      </div>
                    )}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', fontSize: '0.9rem' }}>
                      <input
                        type="checkbox"
                        checked={requireHumanAttestation}
                        onChange={(e) => setRequireHumanAttestation(e.target.checked)}
                      />
                      Require human attestation per block
                    </label>
                    <button
                      onClick={handleFillBotsAndStart}
                      disabled={txPending || committee.length === 0}
                      title={committee.length === 0 ? "Join the pool first (stake 32 ETH above), then click here" : "Fills empty slots with bots, reserves 10 for students who join later"}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#22c55e',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: 'white',
                      fontWeight: 'bold',
                      cursor: txPending ? 'not-allowed' : 'pointer',
                    }}
                  >
                    Fill Bots and Start
                  </button>
                  </>
                )}
                {sessionState === 1 && (
                  <>
                    <span style={{ color: '#86efac', fontSize: '0.9rem' }}>
                      Blocks auto-propose every ~12s (Ethereum simulation)
                    </span>
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }} title="New validators join committees at next epoch start">
                      Students can join/rejoin anytime.
                    </span>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', fontSize: '0.9rem' }}>
                      <input
                        type="checkbox"
                        checked={inactivityPenaltyEnabled}
                        onChange={(e) => setInactivityPenaltyEnabled(e.target.checked)}
                      />
                      Inactivity penalty
                    </label>
                    <button
                      type="button"
                      onClick={handleSetInactivityPenalty}
                      disabled={txPending}
                      title="0.001 ETH penalty for missed attestations"
                      style={{ padding: '0.25rem 0.5rem', background: '#475569', border: 'none', borderRadius: '0.35rem', color: '#e2e8f0', fontSize: '0.8rem', cursor: txPending ? 'not-allowed' : 'pointer' }}
                    >
                      Apply
                    </button>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.85rem', color: '#94a3b8' }}>
                      Bot misbehavior:
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        Wrong hash
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={botWrongHashChance}
                          onChange={(e) => setBotWrongHashChance(Number(e.target.value) || 0)}
                          style={{ width: '40px', padding: '0.2rem', background: '#334155', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0' }}
                        />
                        %
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        Double vote (on fork)
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={botDoubleVoteChance}
                          onChange={(e) => setBotDoubleVoteChance(Number(e.target.value) || 0)}
                          style={{ width: '40px', padding: '0.2rem', background: '#334155', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0' }}
                        />
                        %
                      </label>
                      <button
                        type="button"
                        onClick={handleSetBotMisbehavior}
                        disabled={txPending}
                        title="Bots occasionally try wrong hash or double vote to demonstrate slashing"
                        style={{ padding: '0.25rem 0.5rem', background: '#475569', border: 'none', borderRadius: '0.35rem', color: '#e2e8f0', fontSize: '0.8rem', cursor: txPending ? 'not-allowed' : 'pointer' }}
                      >
                        Apply
                      </button>
                    </span>
                    <button
                      onClick={handleProposeBlockFork}
                      disabled={txPending || blocks.length === 0}
                      title="Create a fork block at same slot for double-vote demo"
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#f59e0b',
                        border: 'none',
                        borderRadius: '0.5rem',
                        color: 'white',
                        fontWeight: 'bold',
                        cursor: txPending || blocks.length === 0 ? 'not-allowed' : 'pointer',
                      }}
                    >
                      Propose fork block
                    </button>
                  </>
                )}
                {sessionState === 1 && (
                  <>
                    <select
                      value={slashTarget}
                      onChange={(e) => setSlashTarget(e.target.value)}
                      style={{
                        padding: '0.5rem',
                        background: '#334155',
                        border: '1px solid #475569',
                        borderRadius: '0.5rem',
                        color: '#e2e8f0',
                      }}
                    >
                      <option value="">Select validator</option>
                      {committee.map((addr) => (
                        <option key={addr} value={addr} disabled={getStats(addr)?.slashed}>
                          {addr.slice(0, 12)}... {getStats(addr)?.slashed ? '(slashed)' : ''}
                        </option>
                      ))}
                    </select>
                    <input
                      type="text"
                      placeholder="Slash reason"
                      value={slashReason}
                      onChange={(e) => setSlashReason(e.target.value)}
                      style={{
                        padding: '0.5rem',
                        background: '#334155',
                        border: '1px solid #475569',
                        borderRadius: '0.5rem',
                        color: '#e2e8f0',
                        width: '150px',
                      }}
                    />
                    <button
                      onClick={handleSlash}
                      disabled={txPending || !slashTarget || !slashReason.trim()}
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#ef4444',
                        border: 'none',
                        borderRadius: '0.5rem',
                        color: 'white',
                        fontWeight: 'bold',
                        cursor: txPending ? 'not-allowed' : 'pointer',
                      }}
                    >
                      Slash
                    </button>
                  </>
                )}
                {sessionState === 1 && (
                  <button
                    onClick={handleEndSession}
                    disabled={txPending}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#64748b',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: 'white',
                      cursor: txPending ? 'not-allowed' : 'pointer',
                    }}
                  >
                    End Session
                  </button>
                )}
                {(sessionState === 1 || sessionState === 2) && (
                  <button
                    onClick={handleReset}
                    disabled={txPending || !contractSupportsReset}
                    title={!contractSupportsReset ? 'Redeploy contract first: npm run deploy:beacon-lab' : ''}
                    style={{
                      padding: '0.5rem 1rem',
                      background: contractSupportsReset ? '#f59e0b' : '#64748b',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: 'white',
                      fontWeight: 'bold',
                      cursor: txPending || !contractSupportsReset ? 'not-allowed' : 'pointer',
                    }}
                  >
                    Reset Lab
                  </button>
                )}
              </div>
            </div>
          )}

          {userExited && (sessionState === 0 || sessionState === 1) && committee.length < poolSize && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(99,102,241,0.1) 100%)', borderRadius: '0.75rem', border: '1px solid rgba(59,130,246,0.4)' }}>
              <h4 style={{ marginBottom: '0.75rem', color: '#93c5fd' }}>Rejoin Validator Pool</h4>
              <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '0.75rem' }}>You exited. Stake 32+ ETH to rejoin and participate again.</p>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <input
                  type="number"
                  min="32"
                  step="1"
                  value={stakeAmount}
                  onChange={(e) => setStakeAmount(e.target.value)}
                  style={{
                    padding: '0.5rem',
                    width: '100px',
                    background: '#334155',
                    border: '1px solid #475569',
                    borderRadius: '0.5rem',
                    color: '#e2e8f0',
                  }}
                />
                <span style={{ color: '#94a3b8' }}>ETH</span>
                <button
                  onClick={handleRejoin}
                  disabled={txPending || committee.length >= poolSize}
                  style={{
                    padding: '0.5rem 1rem',
                    background: 'var(--primary)',
                    border: 'none',
                    borderRadius: '0.5rem',
                    color: 'white',
                    fontWeight: 'bold',
                    cursor: txPending ? 'not-allowed' : 'pointer',
                  }}
                >
                  Rejoin
                </button>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                Pool {committee.length}/{poolSize}. Committees form at epoch start.
              </p>
            </div>
          )}
          {!userInPool && !userExited && (sessionState === 0 || sessionState === 1) && committee.length < poolSize && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--card)', borderRadius: '0.75rem', border: '1px solid #475569' }}>
              <h4 style={{ marginBottom: '0.75rem', color: '#e2e8f0' }}>Join Validator Pool</h4>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <input
                  type="number"
                  min="32"
                  step="1"
                  value={stakeAmount}
                  onChange={(e) => setStakeAmount(e.target.value)}
                  style={{
                    padding: '0.5rem',
                    width: '100px',
                    background: '#334155',
                    border: '1px solid #475569',
                    borderRadius: '0.5rem',
                    color: '#e2e8f0',
                  }}
                />
                <span style={{ color: '#94a3b8' }}>ETH</span>
                <button
                  onClick={handleJoin}
                  disabled={txPending || committee.length >= poolSize}
                  style={{
                    padding: '0.5rem 1rem',
                    background: 'var(--primary)',
                    border: 'none',
                    borderRadius: '0.5rem',
                    color: 'white',
                    fontWeight: 'bold',
                    cursor: txPending ? 'not-allowed' : 'pointer',
                  }}
                >
                  Join
                </button>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                Min 32 ETH. Pool {committee.length}/{poolSize}. You can join anytime — committees form at epoch start.
              </p>
            </div>
          )}
        </div>

        <div>
          {wallet?.address && (
            <>
              <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Lab Activity ({tasksDone}/{STUDENT_TASKS.length})</h3>
              <div style={{
                padding: '1rem',
                background: 'var(--card)',
                borderRadius: '0.75rem',
                border: '1px solid #475569',
                marginBottom: '1rem',
              }}>
                {STUDENT_TASKS.map((t) => {
                  const done = taskCompleted.has(t.id);
                  return (
                    <div
                      key={t.id}
                      style={{
                        marginBottom: '0.75rem',
                        padding: '0.5rem 0',
                        borderBottom: t.id === STUDENT_TASKS[STUDENT_TASKS.length - 1].id ? 'none' : '1px solid #334155',
                        opacity: done ? 0.7 : 1,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                        <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{done ? '✓' : '○'}</span>
                        <div>
                          <div style={{ fontWeight: done ? 400 : 600, color: done ? '#64748b' : '#e2e8f0', fontSize: '0.9rem' }}>
                            {t.title}
                          </div>
                          {!done && <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>{t.hint}</div>}
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem' }}>
                  Tasks check off automatically when you do or observe them — no clicking needed. Progress is saved in your browser.
                </div>
                {taskCompleted.size > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setTaskCompleted(new Set());
                      try { taskStorageKey && localStorage.removeItem(taskStorageKey); } catch (_) {}
                    }}
                    style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', fontSize: '0.75rem', cursor: 'pointer' }}
                  >
                    Reset progress
                  </button>
                )}
              </div>
            </>
          )}
          {wallet?.address && !isInstructor && (
            <div style={{
              marginBottom: '1rem',
              padding: '1rem',
              background: 'var(--card)',
              borderRadius: '0.75rem',
              border: '1px solid #475569',
            }}>
              <h3 style={{ marginBottom: '0.75rem', color: 'var(--primary)' }}>Student Actions</h3>
              {sessionState === 1 && userInPool && !getStats(wallet?.address)?.slashed && !useOldBlockFormat ? (
                <>
                  <div style={{ marginBottom: '0.5rem' }}>
                    <div style={{ fontWeight: 'bold', color: '#94a3b8', fontSize: '0.85rem' }}>Attest</div>
                    <div style={{ height: '6px', background: '#334155', borderRadius: '3px', marginTop: '0.2rem', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${Math.min(100, attestationProgress)}%`, background: 'var(--primary)' }} />
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>{attestationProgress.toFixed(0)}% (threshold: {quorumThreshold} ETH)</div>
                    {requireHumanAttestation && latestBlock && (
                      <div style={{ fontSize: '0.75rem', color: latestBlock.humanAttestationCount >= 1 ? '#22c55e' : '#f59e0b', marginTop: '0.2rem' }}>
                        Human: {latestBlock.humanAttestationCount || 0}/1
                      </div>
                    )}
                  </div>
                  {blocks.length > 0 && (
                    <div style={{ marginBottom: '0.5rem' }}>
                      {attestableBlocks.length > 0 ? (
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <select
                            value={attestBlockIndex}
                            onChange={(e) => setAttestBlockIndex(Number(e.target.value))}
                            style={{ padding: '0.3rem 0.5rem', background: '#334155', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0', fontSize: '0.8rem' }}
                          >
                            {attestableBlocks.map((b) => {
                              const attested = getAttested(wallet?.address, b.index);
                              return (
                                <option key={b.index} value={b.index} disabled={attested}>
                                  #{b.index} slot {b.slot} {attested ? '(attested)' : ''}
                                </option>
                              );
                            })}
                          </select>
                          <button
                            onClick={() => handleAttest(false)}
                            disabled={txPending || getAttested(wallet?.address, attestBlockIndex)}
                            style={{
                              padding: '0.35rem 1rem',
                              background: 'var(--primary)',
                              border: 'none',
                              borderRadius: '0.35rem',
                              color: 'white',
                              fontWeight: 'bold',
                              fontSize: '0.85rem',
                              cursor: txPending || getAttested(wallet?.address, attestBlockIndex) ? 'not-allowed' : 'pointer',
                            }}
                          >
                            {getAttested(wallet?.address, attestBlockIndex) ? 'Attested' : 'Attest'}
                          </button>
                          <button
                            onClick={() => handleAttest(true)}
                            disabled={txPending || getAttested(wallet?.address, attestBlockIndex)}
                            title="Attest with wrong hash to demonstrate slashing"
                            style={{
                              padding: '0.35rem 0.6rem',
                              background: '#f59e0b',
                              border: 'none',
                              borderRadius: '0.35rem',
                              color: 'white',
                              fontSize: '0.8rem',
                              cursor: txPending || getAttested(wallet?.address, attestBlockIndex) ? 'not-allowed' : 'pointer',
                            }}
                          >
                            Demo slash
                          </button>
                        </div>
                      ) : (
                        <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                          No blocks in your committee — wait for next slot.
                        </div>
                      )}
                    </div>
                  )}
                  <div style={{ marginTop: '0.5rem' }}>
                    <button
                      type="button"
                      onClick={handleExit}
                      disabled={txPending}
                      title="Voluntarily exit and withdraw your stake"
                      style={{
                        padding: '0.3rem 0.6rem',
                        background: '#64748b',
                        border: 'none',
                        borderRadius: '0.35rem',
                        color: '#e2e8f0',
                        fontSize: '0.8rem',
                        cursor: txPending ? 'not-allowed' : 'pointer',
                      }}
                    >
                      Exit validator pool
                    </button>
                  </div>
                </>
              ) : sessionState === 1 && (userExited || getStats(wallet?.address)?.slashed) ? (
                <div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                    {userExited ? 'You have exited. Stake was refunded.' : 'You have been slashed.'}
                  </div>
                  {userExited && committee.length < poolSize && (
                    <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <input
                        type="number"
                        min="32"
                        step="1"
                        value={stakeAmount}
                        onChange={(e) => setStakeAmount(e.target.value)}
                        style={{
                          padding: '0.4rem',
                          width: '80px',
                          background: '#334155',
                          border: '1px solid #475569',
                          borderRadius: '0.35rem',
                          color: '#e2e8f0',
                          fontSize: '0.9rem',
                        }}
                      />
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>ETH</span>
                      <button
                        onClick={handleRejoin}
                        disabled={txPending || committee.length >= poolSize}
                        style={{
                          padding: '0.4rem 0.75rem',
                          background: 'var(--primary)',
                          border: 'none',
                          borderRadius: '0.35rem',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.85rem',
                          cursor: txPending ? 'not-allowed' : 'pointer',
                        }}
                      >
                        Rejoin
                      </button>
                    </div>
                  )}
                </div>
              ) : sessionState === 1 && !userInPool && !userExited ? (
                <div>
                  {committee.length < poolSize ? (
                    <>
                      <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
                        Join the validator pool to attest. Stake 32+ ETH.
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <input
                          type="number"
                          min="32"
                          step="1"
                          value={stakeAmount}
                          onChange={(e) => setStakeAmount(e.target.value)}
                          style={{
                            padding: '0.4rem',
                            width: '70px',
                            background: '#334155',
                            border: '1px solid #475569',
                            borderRadius: '0.35rem',
                            color: '#e2e8f0',
                            fontSize: '0.9rem',
                          }}
                        />
                        <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>ETH</span>
                        <button
                          onClick={handleJoin}
                          disabled={txPending || committee.length >= poolSize}
                          style={{
                            padding: '0.4rem 0.75rem',
                            background: 'var(--primary)',
                            border: 'none',
                            borderRadius: '0.35rem',
                            color: 'white',
                            fontWeight: 'bold',
                            fontSize: '0.85rem',
                            cursor: txPending ? 'not-allowed' : 'pointer',
                          }}
                        >
                          Join
                        </button>
                        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Pool {committee.length}/{poolSize}</span>
                      </div>
                    </>
                  ) : (
                    <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                      Pool full ({committee.length}/{poolSize}). Wait for instructor to reset.
                    </div>
                  )}
                </div>
              ) : sessionState === 2 ? (
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  Session ended. Instructor can reset to start a new session.
                </div>
              ) : sessionState === 0 ? (
                <div>
                  {userInPool ? (
                    <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                      You&apos;re in the pool. Session will start when instructor fills bots.
                    </div>
                  ) : committee.length < poolSize ? (
                    <>
                      <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
                        Join the validator pool now. Stake 32+ ETH.
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <input
                          type="number"
                          min="32"
                          step="1"
                          value={stakeAmount}
                          onChange={(e) => setStakeAmount(e.target.value)}
                          style={{
                            padding: '0.4rem',
                            width: '70px',
                            background: '#334155',
                            border: '1px solid #475569',
                            borderRadius: '0.35rem',
                            color: '#e2e8f0',
                            fontSize: '0.9rem',
                          }}
                        />
                        <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>ETH</span>
                        <button
                          onClick={handleJoin}
                          disabled={txPending || committee.length >= poolSize}
                          style={{
                            padding: '0.4rem 0.75rem',
                            background: 'var(--primary)',
                            border: 'none',
                            borderRadius: '0.35rem',
                            color: 'white',
                            fontWeight: 'bold',
                            fontSize: '0.85rem',
                            cursor: txPending ? 'not-allowed' : 'pointer',
                          }}
                        >
                          Join
                        </button>
                        <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Pool {committee.length}/{poolSize}</span>
                      </div>
                    </>
                  ) : (
                    <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                      Pool full ({committee.length}/{poolSize}). Session will start when instructor fills bots.
                    </div>
                  )}
                </div>
              ) : null}
              <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#64748b', borderTop: '1px solid #334155', paddingTop: '0.75rem' }}>
                <div style={{ marginBottom: '0.35rem' }}><strong style={{ color: '#94a3b8' }}>Observe justified:</strong> Watch the progress bar above reach 100%.</div>
                <div style={{ marginBottom: '0.35rem' }}><strong style={{ color: '#94a3b8' }}>Observe finalized:</strong> Latest Blocks table — Status changes to &quot;finalized&quot; when block N+2 is justified.</div>
                <div><strong style={{ color: '#94a3b8' }}>View slash evidence:</strong> Click a block with Slash &gt; 0, or check Pending Slashes below.</div>
              </div>
            </div>
          )}

          <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Stats</h3>
          <div style={{
            padding: '1rem',
            background: 'var(--card)',
            borderRadius: '0.75rem',
            border: '1px solid #475569',
            marginBottom: '1rem',
          }}>
            <div style={{ marginBottom: '0.5rem' }}>Total staked: {totalStaked} ETH</div>
            <div style={{ marginBottom: '0.5rem' }}>Justification threshold: {quorumThreshold} ETH</div>
            <div style={{ marginBottom: '0.5rem' }}>Blocks: {blocks.length}</div>
            <div style={{ marginBottom: '0.5rem' }}>Finalized: {lastFinalizedIndex !== null ? Number(lastFinalizedIndex) + 1 : 0}</div>
            <div style={{ marginBottom: '0.5rem', fontWeight: 600, color: 'var(--primary)' }}>Epoch: {currentEpoch} · Slot: {currentSlot}</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Epoch advances every {blocksPerEpoch} blocks</div>
          </div>

          {(filteredPendingSlashes.length > 0 || (wallet?.address && !isInstructor && sessionState === 1)) && (
            <>
              <h3 style={{ marginBottom: '1rem', color: '#f59e0b' }}>Pending Slashes</h3>
              <div style={{
                padding: '1rem',
                background: filteredPendingSlashes.length > 0 ? 'rgba(245,158,11,0.1)' : 'var(--card)',
                borderRadius: '0.75rem',
                border: `1px solid ${filteredPendingSlashes.length > 0 ? 'rgba(245,158,11,0.4)' : '#475569'}`,
                marginBottom: '1rem',
              }}>
                {filteredPendingSlashes.length > 0 ? (
                  <>
                    {filteredPendingSlashes.map((addr, idx) => {
                      const ev = pendingSlashEvidence.get(addr);
                      return (
                        <div key={addr} style={{ marginBottom: idx < filteredPendingSlashes.length - 1 ? '1rem' : 0, paddingBottom: idx < filteredPendingSlashes.length - 1 ? '1rem' : 0, borderBottom: idx < filteredPendingSlashes.length - 1 ? '1px solid rgba(245,158,11,0.3)' : 'none' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: ev ? '0.5rem' : 0 }}>
                            <button
                              type="button"
                              onClick={() => selectValidator(addr)}
                              style={{ background: 'none', border: 'none', color: '#fcd34d', fontFamily: 'monospace', fontSize: '0.85rem', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
                            >
                              {addr.slice(0, 14)}...
                            </button>
                            <button
                              type="button"
                              onClick={() => handleProcessSlash(addr)}
                              disabled={txPending}
                              style={{
                                padding: '0.25rem 0.5rem',
                                background: '#f59e0b',
                                border: 'none',
                                borderRadius: '0.35rem',
                                color: 'white',
                                fontSize: '0.8rem',
                                cursor: txPending ? 'not-allowed' : 'pointer',
                              }}
                            >
                              Report slash (earn reward)
                            </button>
                          </div>
                          {ev && <SlashEvidenceChain ev={ev} validator={addr} onSelectBlock={selectBlock} />}
                        </div>
                      );
                    })}
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                      Bots or any validator can report to process the slash and earn a whistleblower reward.
                    </div>
                  </>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                    When violations occur (wrong hash, double vote), they appear here. Click a block with Slash &gt; 0 in the Latest Blocks table to view evidence.
                  </div>
                )}
              </div>
            </>
          )}
          {committee.filter((a) => getStats(a)?.slashed).length > 0 && (
            <>
              <h3 style={{ marginBottom: '1rem', color: '#ef4444' }}>Slashed Validators</h3>
              <div style={{
                padding: '1rem',
                background: 'rgba(239,68,68,0.1)',
                borderRadius: '0.75rem',
                border: '1px solid rgba(239,68,68,0.4)',
                marginBottom: '1rem',
              }}>
                {committee.filter((a) => getStats(a)?.slashed).map((addr) => (
                  <button
                    key={addr}
                    type="button"
                    onClick={() => selectValidator(addr)}
                    style={{ display: 'block', marginBottom: '0.5rem', color: '#fca5a5', fontFamily: 'monospace', fontSize: '0.85rem', background: 'none', border: 'none', cursor: 'pointer', padding: 0, textDecoration: 'underline', textAlign: 'left' }}
                  >
                    {addr}
                  </button>
                ))}
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                  Click a block below to see slash details (wrong hash, double vote)
                </div>
              </div>
            </>
          )}

          <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Activity Log</h3>
          <div style={{
            padding: '1rem',
            background: 'var(--card)',
            borderRadius: '0.75rem',
            border: '1px solid #475569',
            maxHeight: '300px',
            overflowY: 'auto',
            fontSize: '0.85rem',
          }}>
            {activityLog.length === 0 ? (
              <div style={{ color: '#64748b' }}>No activity yet</div>
            ) : (
              activityLog.slice().reverse().map((a, i) => {
                const isSlash = /slash|Slashed/i.test(a.msg);
                return (
                  <div
                    key={i}
                    style={{
                      marginBottom: '0.5rem',
                      color: isSlash ? '#fca5a5' : '#94a3b8',
                      background: isSlash ? 'rgba(239,68,68,0.1)' : 'transparent',
                      padding: isSlash ? '0.35rem 0.5rem' : 0,
                      borderRadius: isSlash ? '0.35rem' : 0,
                      fontWeight: isSlash ? 600 : 400,
                    }}
                  >
                    {new Date(a.ts).toLocaleTimeString()} {a.msg}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
