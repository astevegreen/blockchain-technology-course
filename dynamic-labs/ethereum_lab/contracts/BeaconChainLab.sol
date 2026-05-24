// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.19;

/**
 * @title BeaconChainLab - Interactive Educational Beacon Chain Simulator
 * @notice Demonstrates committee formation, quorum, attestation, finality, and slashing
 * @dev Multiple committees per epoch, validator pool, report-based slashing with whistleblower
 */
contract BeaconChainLab {
    // ==================== ENUMS ====================

    enum SessionState { LOBBY, ACTIVE, FINISHED }
    enum SlashReason { NONE, WRONG_HASH, DOUBLE_VOTE }

    // ==================== STRUCTS ====================

    struct BlockInfo {
        address proposer;
        bytes32 blockHash;
        bytes32 parentHash;
        uint256 slot;
        uint256 attestationCount;
        uint256 attestationStake;
        uint256 humanAttestationCount;
        bool justified;
        bool finalized;
    }

    struct SlashEvidence {
        SlashReason reason;
        uint256 blockIndex;
        uint256 slot;
        bytes32 expectedHash;
        bytes32 attestedHash;
        uint256 firstBlock;
        uint256 secondBlock;
    }

    // ==================== STATE VARIABLES ====================

    address public instructor;
    SessionState public sessionState;
    uint256 public blocksPerEpoch;
    uint256 public committeesPerEpoch;
    uint256 public validatorsPerCommittee;
    uint256 public poolSize; // max validators in pool = committeesPerEpoch * validatorsPerCommittee

    // Validator pool (replaces single committee)
    address[] public validatorPool;
    mapping(address => uint256) public stakes;
    mapping(address => bool) public isBot;
    mapping(address => bool) public inPool;
    mapping(address => bool) public exited;
    mapping(address => bool) public slashed;
    uint256 public totalStaked;

    // Committee assignment: epoch => committeeIndex => validatorIndex => address
    mapping(uint256 => mapping(uint256 => mapping(uint256 => address))) public committeeMember;
    mapping(uint256 => uint256) public lastAssignedEpoch;

    // Blocks
    BlockInfo[] public blocks;
    uint256 public sessionId;
    mapping(uint256 => mapping(uint256 => mapping(address => bool))) public hasAttestedBlock;
    mapping(address => mapping(uint256 => uint256)) public attestedSlotToBlock;

    uint256 public currentEpoch;
    uint256 public currentSlot;
    uint256 public lastFinalizedIndex;

    // Practice attestation
    bool public requireHumanAttestation;

    // Inactivity penalty (small penalty for missed attestations)
    bool public inactivityPenaltyEnabled;

    // Bot misbehavior (educational: bots occasionally try slashable offenses)
    uint256 public botWrongHashChance = 5;   // 5% chance per block a bot tries wrong hash
    uint256 public botDoubleVoteChance = 10; // 10% chance when fork proposed a bot double-votes

    // Report-based slashing
    mapping(address => SlashEvidence) public pendingSlash;

    uint256 public constant MIN_STAKE = 32 ether;
    uint256 public constant SLASH_PENALTY_PERCENT = 5;
    uint256 public constant WHISTLEBLOWER_REWARD_PERCENT = 10;
    uint256 public constant BLOCK_REWARD = 0.01 ether;
    uint256 public constant INACTIVITY_PENALTY = 0.001 ether;
    uint256 public constant QUORUM_NUMERATOR = 2;
    uint256 public constant QUORUM_DENOMINATOR = 3;

    // ==================== EVENTS ====================

    event Joined(address indexed validator, uint256 stake);
    event SessionStarted(uint256 humanCount, uint256 botCount);
    event SessionEnded();
    event BlockProposed(uint256 indexed blockIndex, address indexed proposer, uint256 epoch);
    event Attested(address indexed validator, uint256 indexed blockIndex);
    event BlockJustified(uint256 indexed blockIndex);
    event BlockFinalized(uint256 indexed blockIndex);
    event Slashed(address indexed validator, uint256 amount, string reason);
    event WrongAttestationSlashed(address indexed validator, uint256 blockIndex, bytes32 expectedHash, bytes32 attestedHash);
    event DoubleVoteSlashed(address indexed validator, uint256 slot, uint256 firstBlock, uint256 secondBlock);
    event SlashEvidenceSubmitted(address indexed validator, SlashReason reason, uint256 blockIndex);
    event SlashReported(address indexed reporter, address indexed validator, uint256 reward);
    event EpochAdvanced(uint256 newEpoch);
    event SessionReset(uint256 newSessionId);
    event CommitteesAssigned(uint256 epoch);
    event ValidatorExited(address indexed validator, uint256 amount);
    event InactivityPenalty(address indexed validator, uint256 blockIndex, uint256 amount);
    event PoolConfigUpdated(uint256 validatorsPerCommittee, uint256 poolSize);

    // ==================== MODIFIERS ====================

    modifier onlyInstructor() {
        require(msg.sender == instructor, "Only instructor");
        _;
    }

    modifier onlyInPool() {
        require(inPool[msg.sender], "Not in validator pool");
        _;
    }

    modifier notSlashedMod() {
        require(!slashed[msg.sender], "Slashed");
        _;
    }

    // ==================== CONSTRUCTOR ====================

    constructor(uint256 _committeesPerEpoch, uint256 _validatorsPerCommittee, uint256 _blocksPerEpoch) {
        instructor = msg.sender;
        sessionState = SessionState.LOBBY;
        committeesPerEpoch = _committeesPerEpoch == 0 ? 8 : _committeesPerEpoch;
        validatorsPerCommittee = _validatorsPerCommittee == 0 ? 256 : _validatorsPerCommittee;
        blocksPerEpoch = _blocksPerEpoch == 0 ? 32 : _blocksPerEpoch;
        poolSize = committeesPerEpoch * validatorsPerCommittee; // 2048 with defaults; no practical limit for classroom
        currentEpoch = 1;
        currentSlot = 1;
    }

    // ==================== LOBBY / SESSION ====================

    /**
     * @notice Join the validator pool (students can join in LOBBY or during ACTIVE session)
     */
    function join() external payable {
        require(sessionState == SessionState.LOBBY || sessionState == SessionState.ACTIVE, "Session not open for joining");
        require(msg.value >= MIN_STAKE, "Min stake 32 ETH");
        require(!inPool[msg.sender], "Already joined");
        require(validatorPool.length < poolSize, "Pool full");

        stakes[msg.sender] = msg.value;
        totalStaked += msg.value;
        validatorPool.push(msg.sender);
        inPool[msg.sender] = true;
        isBot[msg.sender] = false;

        emit Joined(msg.sender, msg.value);
    }

    /**
     * @notice Instructor fills pool with bots and starts the session
     */
    function fillBotsAndStart(address[] calldata botAddresses, bool _requireHumanAttestation) external onlyInstructor {
        require(sessionState == SessionState.LOBBY, "Not in lobby");
        require(validatorPool.length > 0, "No humans joined");

        uint256 emptySlots = poolSize - validatorPool.length;
        require(botAddresses.length >= 1, "Need at least one bot address");
        // Fill available slots with bots; leave remainder for late joiners
        uint256 toFill = emptySlots < botAddresses.length ? emptySlots : botAddresses.length;

        requireHumanAttestation = _requireHumanAttestation;

        uint256 botsAdded = 0;
        for (uint256 i = 0; i < toFill; i++) {
            address bot = botAddresses[i];
            if (bot == address(0) || inPool[bot]) continue;

            uint256 r = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, bot, i))) % 33;
            uint256 botStake = MIN_STAKE + r * 1 ether;
            stakes[bot] = botStake;
            totalStaked += botStake;
            validatorPool.push(bot);
            inPool[bot] = true;
            isBot[bot] = true;
            botsAdded++;
        }

        sessionState = SessionState.ACTIVE;
        _assignCommitteesForEpoch(currentEpoch);
        emit SessionStarted(validatorPool.length - botsAdded, botsAdded);
    }

    function endSession() external onlyInstructor {
        require(sessionState == SessionState.ACTIVE, "Not active");
        sessionState = SessionState.FINISHED;
        emit SessionEnded();
    }

    /**
     * @notice Set bot misbehavior chance (0 = disabled). Wrong hash: per-block %. Double vote: per-fork %.
     */
    function setBotMisbehaviorChance(uint256 _wrongHashChance, uint256 _doubleVoteChance) external onlyInstructor {
        botWrongHashChance = _wrongHashChance > 100 ? 0 : _wrongHashChance;
        botDoubleVoteChance = _doubleVoteChance > 100 ? 0 : _doubleVoteChance;
    }

    function setInactivityPenaltyEnabled(bool _enabled) external onlyInstructor {
        inactivityPenaltyEnabled = _enabled;
    }

    /**
     * @notice Instructor sets validators per committee in LOBBY. Reduces pool size and gas for fillBotsAndStart.
     */
    function setValidatorsPerCommittee(uint256 _validatorsPerCommittee) external onlyInstructor {
        require(sessionState == SessionState.LOBBY, "Only in lobby");
        require(_validatorsPerCommittee >= 1 && _validatorsPerCommittee <= 256, "Validators per committee 1-256");
        require(validatorPool.length <= committeesPerEpoch * _validatorsPerCommittee, "Pool would be smaller than current validators");
        validatorsPerCommittee = _validatorsPerCommittee;
        poolSize = committeesPerEpoch * validatorsPerCommittee;
        emit PoolConfigUpdated(validatorsPerCommittee, poolSize);
    }

    /**
     * @notice Voluntary exit: withdraw stake and leave the validator pool.
     */
    function exit() external onlyInPool {
        require(!slashed[msg.sender], "Slashed");
        require(!exited[msg.sender], "Already exited");
        uint256 amt = stakes[msg.sender];
        require(amt > 0, "No stake");

        stakes[msg.sender] = 0;
        totalStaked -= amt;
        exited[msg.sender] = true;
        inPool[msg.sender] = false;

        (bool ok,) = msg.sender.call{value: amt}("");
        require(ok, "Refund failed");
        emit ValidatorExited(msg.sender, amt);
    }

    /**
     * @notice Rejoin the validator pool after exiting. Stake ETH to become active again.
     */
    function rejoin() external payable {
        require(sessionState == SessionState.LOBBY || sessionState == SessionState.ACTIVE, "Session not open");
        require(msg.value >= MIN_STAKE, "Min stake 32 ETH");
        require(exited[msg.sender], "Must have exited first");
        require(!inPool[msg.sender], "Already in pool");

        stakes[msg.sender] = msg.value;
        totalStaked += msg.value;
        inPool[msg.sender] = true;
        exited[msg.sender] = false;
        isBot[msg.sender] = false;

        if (sessionState == SessionState.ACTIVE) {
            _assignCommitteesForEpoch(currentEpoch);
        }
        emit Joined(msg.sender, msg.value);
    }

    function resetSession() external onlyInstructor {
        require(sessionState != SessionState.LOBBY, "Already in lobby");

        uint256 len = validatorPool.length;
        for (uint256 i = 0; i < len; i++) {
            address member = validatorPool[i];
            uint256 amt = stakes[member];
            if (amt > 0) {
                stakes[member] = 0;
                (bool ok,) = member.call{value: amt}("");
                require(ok, "Refund failed");
            }
            inPool[member] = false;
            exited[member] = false;
            isBot[member] = false;
            slashed[member] = false;
            delete pendingSlash[member];
            for (uint256 j = 0; j < blocks.length; j++) {
                attestedSlotToBlock[member][blocks[j].slot] = 0;
            }
        }

        while (validatorPool.length > 0) validatorPool.pop();
        while (blocks.length > 0) blocks.pop();

        totalStaked = 0;
        currentEpoch = 1;
        currentSlot = 1;
        lastFinalizedIndex = 0;
        sessionId++;
        sessionState = SessionState.LOBBY;

        emit SessionReset(sessionId);
    }

    // ==================== COMMITTEE ASSIGNMENT ====================

    function _assignCommitteesForEpoch(uint256 epoch) internal {
        if (lastAssignedEpoch[epoch] != 0) return;
        lastAssignedEpoch[epoch] = block.timestamp;
        uint256 n = validatorPool.length;
        if (n == 0) return;
        uint256 idx = 0;
        for (uint256 i = 0; i < n && idx < committeesPerEpoch * validatorsPerCommittee; i++) {
            address v = validatorPool[i];
            if (exited[v] || slashed[v] || stakes[v] == 0) continue;
            uint256 c = idx % committeesPerEpoch;
            uint256 k = idx / committeesPerEpoch;
            if (k < validatorsPerCommittee) committeeMember[epoch][c][k] = v;
            idx++;
        }
        emit CommitteesAssigned(epoch);
    }

    function _isInCommitteeForSlot(address validator, uint256 slot) internal view returns (bool) {
        uint256 epoch = (slot + blocksPerEpoch - 1) / blocksPerEpoch;
        if (lastAssignedEpoch[epoch] == 0) return false;
        uint256 committeeIndex = (slot - 1) % committeesPerEpoch;
        for (uint256 k = 0; k < validatorsPerCommittee; k++) {
            if (committeeMember[epoch][committeeIndex][k] == validator) return true;
        }
        return false;
    }

    // ==================== BLOCK PROPOSAL ====================

    function proposeBlock() external onlyInstructor returns (address) {
        require(sessionState == SessionState.ACTIVE, "Session not active");
        require(validatorPool.length > 0 && totalStaked > 0, "No validators");

        // Assign committees for new epoch if needed
        if (currentSlot == 1) {
            _assignCommitteesForEpoch(currentEpoch);
        }

        address[] memory eligible = new address[](validatorPool.length);
        uint256 eligibleCount = 0;
        uint256 eligibleStake = 0;
        for (uint256 i = 0; i < validatorPool.length; i++) {
            address v = validatorPool[i];
            if (!exited[v] && !slashed[v] && stakes[v] > 0) {
                eligible[eligibleCount] = v;
                eligibleCount++;
                eligibleStake += stakes[v];
            }
        }

        address proposer;
        if (eligibleCount == 0 || eligibleStake == 0) {
            proposer = instructor;
        } else {
            uint256 random = uint256(keccak256(abi.encodePacked(
                block.timestamp, block.prevrandao, totalStaked, blocks.length
            ))) % eligibleStake;
            uint256 cumulative = 0;
            proposer = eligible[0];
            for (uint256 i = 0; i < eligibleCount; i++) {
                cumulative += stakes[eligible[i]];
                if (random < cumulative) {
                    proposer = eligible[i];
                    break;
                }
            }
        }

        if (proposer != instructor && inPool[proposer]) {
            stakes[proposer] += BLOCK_REWARD;
            totalStaked += BLOCK_REWARD;
        }

        bytes32 parentHash = blocks.length == 0 ? bytes32(0) : blocks[blocks.length - 1].blockHash;
        uint256 slot = currentSlot;

        blocks.push(BlockInfo({
            proposer: proposer,
            blockHash: bytes32(0),
            parentHash: parentHash,
            slot: slot,
            attestationCount: 0,
            attestationStake: 0,
            humanAttestationCount: 0,
            justified: false,
            finalized: false
        }));
        uint256 blockIndex = blocks.length - 1;
        blocks[blockIndex].blockHash = keccak256(abi.encodePacked(
            blockIndex, proposer, parentHash, slot, currentEpoch, sessionId
        ));

        // Bots in committee for this slot auto-attest (occasionally one tries wrong hash for demo)
        uint256 committeeIndex = (slot - 1) % committeesPerEpoch;
        for (uint256 k = 0; k < validatorsPerCommittee; k++) {
            address v = committeeMember[currentEpoch][committeeIndex][k];
            if (v != address(0) && isBot[v] && !slashed[v] && stakes[v] > 0 && !hasAttestedBlock[sessionId][blockIndex][v]) {
                uint256 roll = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, blockIndex, k, v))) % 100;
                if (botWrongHashChance > 0 && roll < botWrongHashChance && pendingSlash[v].reason == SlashReason.NONE) {
                    bytes32 wrongHash = keccak256(abi.encodePacked(uint256(999), v, blockIndex));
                    pendingSlash[v] = SlashEvidence({
                        reason: SlashReason.WRONG_HASH,
                        blockIndex: blockIndex,
                        slot: slot,
                        expectedHash: blocks[blockIndex].blockHash,
                        attestedHash: wrongHash,
                        firstBlock: 0,
                        secondBlock: 0
                    });
                    emit SlashEvidenceSubmitted(v, SlashReason.WRONG_HASH, blockIndex);
                } else {
                    _applyAttestation(v, blockIndex, slot);
                }
            }
        }

        // Inactivity penalty: human committee members who didn't attest
        if (inactivityPenaltyEnabled) {
            for (uint256 k = 0; k < validatorsPerCommittee; k++) {
                address v = committeeMember[currentEpoch][committeeIndex][k];
                if (v != address(0) && !isBot[v] && !slashed[v] && !exited[v] && stakes[v] >= INACTIVITY_PENALTY) {
                    if (!hasAttestedBlock[sessionId][blockIndex][v]) {
                        stakes[v] -= INACTIVITY_PENALTY;
                        totalStaked -= INACTIVITY_PENALTY;
                        emit InactivityPenalty(v, blockIndex, INACTIVITY_PENALTY);
                    }
                }
            }
        }

        if (currentSlot >= blocksPerEpoch) {
            currentSlot = 1;
            currentEpoch++;
            emit EpochAdvanced(currentEpoch);
        } else {
            currentSlot++;
        }

        _checkJustification(blockIndex);
        _checkFinality();

        emit BlockProposed(blockIndex, proposer, currentEpoch);
        return proposer;
    }

    function proposeBlockFork() external onlyInstructor returns (address) {
        require(sessionState == SessionState.ACTIVE, "Not active");
        require(blocks.length > 0, "No block to fork");
        require(validatorPool.length > 0 && totalStaked > 0, "No validators");

        address[] memory eligible = new address[](validatorPool.length);
        uint256 eligibleCount = 0;
        uint256 eligibleStake = 0;
        for (uint256 i = 0; i < validatorPool.length; i++) {
            address v = validatorPool[i];
            if (!exited[v] && !slashed[v] && stakes[v] > 0) {
                eligible[eligibleCount] = v;
                eligibleCount++;
                eligibleStake += stakes[v];
            }
        }

        address proposer;
        if (eligibleCount == 0 || eligibleStake == 0) {
            proposer = instructor;
        } else {
            uint256 random = uint256(keccak256(abi.encodePacked(
                block.timestamp, block.prevrandao, totalStaked, blocks.length
            ))) % eligibleStake;
            uint256 cumulative = 0;
            proposer = eligible[0];
            for (uint256 i = 0; i < eligibleCount; i++) {
                cumulative += stakes[eligible[i]];
                if (random < cumulative) {
                    proposer = eligible[i];
                    break;
                }
            }
        }

        if (proposer != instructor && inPool[proposer]) {
            stakes[proposer] += BLOCK_REWARD;
            totalStaked += BLOCK_REWARD;
        }

        BlockInfo storage latest = blocks[blocks.length - 1];
        uint256 slot = latest.slot;
        bytes32 parentHash = latest.parentHash;

        blocks.push(BlockInfo({
            proposer: proposer,
            blockHash: bytes32(0),
            parentHash: parentHash,
            slot: slot,
            attestationCount: 0,
            attestationStake: 0,
            humanAttestationCount: 0,
            justified: false,
            finalized: false
        }));
        uint256 blockIndex = blocks.length - 1;
        blocks[blockIndex].blockHash = keccak256(abi.encodePacked(
            blockIndex, proposer, parentHash, slot, currentEpoch, sessionId
        ));

        // Occasionally a bot that attested to canonical block "double votes" on fork (for demo)
        uint256 canonicalIndex = blocks.length - 2;
        if (botDoubleVoteChance > 0 && validatorPool.length > 0) {
            uint256 dvRoll = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, blockIndex))) % 100;
            if (dvRoll < botDoubleVoteChance) {
                for (uint256 i = 0; i < validatorPool.length; i++) {
                    address v = validatorPool[i];
                    if (isBot[v] && !slashed[v] && hasAttestedBlock[sessionId][canonicalIndex][v]) {
                        if (pendingSlash[v].reason == SlashReason.NONE) {
                            pendingSlash[v] = SlashEvidence({
                                reason: SlashReason.DOUBLE_VOTE,
                                blockIndex: blockIndex,
                                slot: slot,
                                expectedHash: bytes32(0),
                                attestedHash: bytes32(0),
                                firstBlock: canonicalIndex,
                                secondBlock: blockIndex
                            });
                            emit SlashEvidenceSubmitted(v, SlashReason.DOUBLE_VOTE, blockIndex);
                        }
                        break;
                    }
                }
            }
        }

        _checkJustification(blockIndex);
        _checkFinality();

        emit BlockProposed(blockIndex, proposer, currentEpoch);
        return proposer;
    }

    // ==================== ATTESTATION ====================

    function attest(uint256 blockIndex, bytes32 claimedHash) external onlyInPool notSlashedMod {
        require(sessionState == SessionState.ACTIVE, "Session not active");
        require(blockIndex < blocks.length, "Invalid block");
        require(!hasAttestedBlock[sessionId][blockIndex][msg.sender], "Already attested");

        BlockInfo storage b = blocks[blockIndex];
        require(_isInCommitteeForSlot(msg.sender, b.slot), "Not in committee for this slot");

        // 1. Wrong hash -> store evidence, do not apply, return (report-based slash)
        if (claimedHash != b.blockHash) {
            pendingSlash[msg.sender] = SlashEvidence({
                reason: SlashReason.WRONG_HASH,
                blockIndex: blockIndex,
                slot: b.slot,
                expectedHash: b.blockHash,
                attestedHash: claimedHash,
                firstBlock: 0,
                secondBlock: 0
            });
            emit SlashEvidenceSubmitted(msg.sender, SlashReason.WRONG_HASH, blockIndex);
            return;
        }

        // 2. Double vote -> store evidence, do not apply, return
        uint256 prevStored = attestedSlotToBlock[msg.sender][b.slot];
        if (prevStored != 0) {
            uint256 prevBlock = prevStored - 1;
            if (prevBlock != blockIndex) {
                pendingSlash[msg.sender] = SlashEvidence({
                    reason: SlashReason.DOUBLE_VOTE,
                    blockIndex: blockIndex,
                    slot: b.slot,
                    expectedHash: bytes32(0),
                    attestedHash: bytes32(0),
                    firstBlock: prevBlock,
                    secondBlock: blockIndex
                });
                emit SlashEvidenceSubmitted(msg.sender, SlashReason.DOUBLE_VOTE, blockIndex);
                return;
            }
        }

        _applyAttestation(msg.sender, blockIndex, b.slot);
        _checkJustification(blockIndex);
        _checkFinality();
    }

    function _applyAttestation(address validator, uint256 blockIndex, uint256 slot) internal {
        hasAttestedBlock[sessionId][blockIndex][validator] = true;
        attestedSlotToBlock[validator][slot] = blockIndex + 1;
        blocks[blockIndex].attestationCount++;
        blocks[blockIndex].attestationStake += stakes[validator];
        if (!isBot[validator]) {
            blocks[blockIndex].humanAttestationCount++;
        }
        emit Attested(validator, blockIndex);
    }

    function _checkJustification(uint256 blockIndex) internal {
        if (blocks[blockIndex].justified) return;
        if (totalStaked == 0) return;

        if (requireHumanAttestation && blocks[blockIndex].humanAttestationCount < 1) return;

        uint256 quorum = (totalStaked * QUORUM_NUMERATOR) / QUORUM_DENOMINATOR;
        if (blocks[blockIndex].attestationStake >= quorum) {
            blocks[blockIndex].justified = true;
            emit BlockJustified(blockIndex);
        }
    }

    function _findBlockIndexByHash(bytes32 hash) internal view returns (uint256) {
        for (uint256 i = 0; i < blocks.length; i++) {
            if (blocks[i].blockHash == hash) return i;
        }
        return type(uint256).max;
    }

    function _checkFinality() internal {
        if (blocks.length < 2 * blocksPerEpoch) return;
        uint256 latest = blocks.length - 1;
        if (!blocks[latest].justified) return;

        // Casper FFG: checkpoint = last block of each epoch (indices 31, 63, 95, ... for blocksPerEpoch=32)
        // When current and previous epoch checkpoints are justified, finalize the older one
        uint256 currentCheckpoint = ((latest + 1) / blocksPerEpoch) * blocksPerEpoch - 1;
        uint256 prevCheckpoint = currentCheckpoint - blocksPerEpoch;

        if (!blocks[currentCheckpoint].justified) return;
        if (!blocks[prevCheckpoint].justified) return;

        uint256 toFinalize = prevCheckpoint;
        if (blocks[toFinalize].finalized) return;
        blocks[toFinalize].finalized = true;
        lastFinalizedIndex = toFinalize;
        emit BlockFinalized(toFinalize);
        // Transitive: finalize any justified ancestors on canonical chain that are not yet finalized
        while (toFinalize > 0) {
            bytes32 ph = blocks[toFinalize].parentHash;
            if (ph == bytes32(0)) break;
            uint256 prev = _findBlockIndexByHash(ph);
            if (prev == type(uint256).max) break;
            if (!blocks[prev].justified || blocks[prev].finalized) break;
            blocks[prev].finalized = true;
            lastFinalizedIndex = prev;
            emit BlockFinalized(prev);
            toFinalize = prev;
        }
    }

    // ==================== REPORT-BASED SLASHING ====================

    function processSlash(address validator) external {
        SlashEvidence storage ev = pendingSlash[validator];
        require(ev.reason != SlashReason.NONE, "No pending slash");
        require(!slashed[validator], "Already slashed");
        require(stakes[validator] > 0, "No stake");

        uint256 penalty = (stakes[validator] * SLASH_PENALTY_PERCENT) / 100;
        uint256 reward = (penalty * WHISTLEBLOWER_REWARD_PERCENT) / 100;

        stakes[validator] -= penalty;
        totalStaked -= penalty;
        slashed[validator] = true;

        if (ev.reason == SlashReason.WRONG_HASH) {
            emit WrongAttestationSlashed(validator, ev.blockIndex, ev.expectedHash, ev.attestedHash);
            emit Slashed(validator, penalty, "Wrong block hash");
        } else {
            emit DoubleVoteSlashed(validator, ev.slot, ev.firstBlock, ev.secondBlock);
            emit Slashed(validator, penalty, "Double vote");
        }

        delete pendingSlash[validator];

        if (reward > 0 && msg.sender != address(0)) {
            (bool ok,) = msg.sender.call{value: reward}("");
            if (ok) emit SlashReported(msg.sender, validator, reward);
        }
    }

    function slash(address validator, string calldata reason) external onlyInstructor {
        require(inPool[validator], "Not in pool");
        require(!slashed[validator], "Already slashed");
        require(stakes[validator] > 0, "No stake");

        uint256 penalty = (stakes[validator] * SLASH_PENALTY_PERCENT) / 100;
        stakes[validator] -= penalty;
        totalStaked -= penalty;
        slashed[validator] = true;

        emit Slashed(validator, penalty, reason);
    }

    // ==================== VIEW FUNCTIONS ====================

    function getCommittee() external view returns (address[] memory) {
        return validatorPool;
    }

    function getCommitteeForSlot(uint256 epoch, uint256 slotIndex) external view returns (address[] memory) {
        address[] memory members = new address[](validatorsPerCommittee);
        for (uint256 k = 0; k < validatorsPerCommittee; k++) {
            members[k] = committeeMember[epoch][slotIndex][k];
        }
        return members;
    }

    function getBlockInfo(uint256 index) external view returns (
        address proposer,
        bytes32 blockHash,
        bytes32 parentHash,
        uint256 slot,
        uint256 attestationCount,
        uint256 attestationStake,
        uint256 humanAttestationCount,
        bool justified,
        bool finalized
    ) {
        require(index < blocks.length, "Invalid block");
        BlockInfo storage b = blocks[index];
        return (b.proposer, b.blockHash, b.parentHash, b.slot, b.attestationCount, b.attestationStake, b.humanAttestationCount, b.justified, b.finalized);
    }

    function getSessionState() external view returns (SessionState) {
        return sessionState;
    }

    function getCommitteeSize() external view returns (uint256) {
        return validatorPool.length;
    }

    function getValidatorStats(address validator) external view returns (
        uint256 stakeAmount,
        bool isBotValidator,
        bool isSlashed
    ) {
        return (stakes[validator], isBot[validator], slashed[validator]);
    }

    function getQuorumThreshold() external view returns (uint256) {
        return (totalStaked * QUORUM_NUMERATOR) / QUORUM_DENOMINATOR;
    }

    function getBlocksLength() external view returns (uint256) {
        return blocks.length;
    }

    function hasAttested(address validator, uint256 blockIndex) external view returns (bool) {
        return hasAttestedBlock[sessionId][blockIndex][validator];
    }

    function hasPendingSlash(address validator) external view returns (bool) {
        return pendingSlash[validator].reason != SlashReason.NONE;
    }

    function getPoolSize() external view returns (uint256) {
        return poolSize;
    }

    receive() external payable {}
}
