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
        uint256 epoch;
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
    mapping(address => uint256) public joinedAtBlock; // first block index a validator is responsible for
    address[] public knownValidators;
    mapping(address => bool) public knownValidator;
    uint256 public totalStaked;

    // Committee assignment: epoch => committeeIndex => validatorIndex => address
    mapping(uint256 => mapping(uint256 => mapping(uint256 => address))) public committeeMember;
    mapping(uint256 => uint256) public lastAssignedEpoch;

    // Blocks
    BlockInfo[] public blocks;
    uint256 public sessionId;
    mapping(uint256 => mapping(uint256 => mapping(address => bool))) public hasAttestedBlock;
    // validator => epoch/slot key => block index + 1. Slots repeat every epoch.
    mapping(address => mapping(uint256 => uint256)) public attestedSlotToBlock;

    uint256 public currentEpoch;
    uint256 public currentSlot;
    uint256 public lastFinalizedIndex;

    // Practice attestation
    bool public requireHumanAttestation;

    // Inactivity penalty (small penalty for missed attestations)
    bool public inactivityPenaltyEnabled;

    // Pivotal mode: bots auto-attest only up to just below the 2/3 quorum, so a
    // human's attestation is the one that crosses the threshold and justifies the
    // block. If no human attests within the slot, the held-back bots finish the job
    // on the next slot (fallback) so an idle/bots-only chain still finalizes.
    bool public pivotalMode = true;

    // Bot misbehavior (educational: bots occasionally try slashable offenses)
    uint256 public botWrongHashChance = 5;   // 5% chance per block a bot tries wrong hash
    uint256 public botDoubleVoteChance = 10; // 10% chance when fork proposed a bot double-votes

    // Report-based slashing
    mapping(address => SlashEvidence) public pendingSlash;

    uint256 public constant MIN_STAKE = 32 ether;
    uint256 public constant SLASH_PENALTY_PERCENT = 5;
    uint256 public constant WHISTLEBLOWER_REWARD_PERCENT = 10;
    uint256 public constant BLOCK_REWARD = 0.01 ether;
    uint256 public constant ATTESTATION_REWARD = 0.002 ether;
    uint256 public constant INACTIVITY_PENALTY = 0.001 ether;
    uint256 public constant QUORUM_NUMERATOR = 2;
    uint256 public constant QUORUM_DENOMINATOR = 3;
    uint256 public constant MISSED_PROPOSAL_PENALTY = 0.1 ether;

    // ---- Human proposer duty (MEV / PBS) ----
    // When a human is assigned the next slot, the conductor "opens" a proposal slot
    // with 1-3 candidate block configurations. The human picks one
    // within a short window via proposeAsProposer(); if they miss it, the conductor
    // fallback-proposes with a bot and the human takes a missed-proposal penalty.
    bool public proposalPending;
    address public scheduledProposer;
    uint256 public proposalSlot;
    uint8 public proposalOptionCount;
    uint256[3] public mevOptions; // estimated fee/reward value of each candidate block
    bytes32[3] public proposalBundleRoots; // hashes of the candidate tx ordering metadata

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
    event BotEvicted(address indexed bot, address indexed replacedBy);
    event ProposalSlotOpened(address indexed proposer, uint256 slot, uint256 opt0, uint256 opt1, uint256 opt2);
    event ProposalBundlesOpened(address indexed proposer, uint256 slot, uint8 optionCount, uint256 opt0, uint256 opt1, uint256 opt2, bytes32 root0, bytes32 root1, bytes32 root2);
    event ProposalChosen(address indexed proposer, uint256 indexed blockIndex, uint8 choice, uint256 mevReward);
    event ProposalMissed(address indexed proposer, uint256 slot, uint256 penalty);
    event BotsRefilled(uint256 count, uint256 poolFilled);

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
        require(!exited[msg.sender], "Use rejoin");

        // Bots fill the pool; when it is full, evict one bot so a human can always
        // take a seat. Bot stake is virtual, so eviction is just bookkeeping.
        if (validatorPool.length >= poolSize) {
            require(_evictOneBot(msg.sender), "Pool full");
        }

        _rememberValidator(msg.sender);
        stakes[msg.sender] = msg.value;
        totalStaked += msg.value;
        validatorPool.push(msg.sender);
        inPool[msg.sender] = true;
        isBot[msg.sender] = false;
        joinedAtBlock[msg.sender] = blocks.length; // responsible from the next block on

        // If a session is live, re-shuffle THIS epoch's committees right away so the
        // joiner can attest to the very next block (instead of waiting a full epoch
        // to be seated). Already-cast attestations are unaffected.
        if (sessionState == SessionState.ACTIVE) {
            lastAssignedEpoch[currentEpoch] = 0;
            _assignCommitteesForEpoch(currentEpoch);
        }

        emit Joined(msg.sender, msg.value);
    }

    function _rememberValidator(address validator) internal {
        if (!knownValidator[validator]) {
            knownValidator[validator] = true;
            knownValidators.push(validator);
        }
    }

    function _removeValidatorFromPool(address validator) internal {
        uint256 i = 0;
        while (i < validatorPool.length) {
            if (validatorPool[i] == validator) {
                validatorPool[i] = validatorPool[validatorPool.length - 1];
                validatorPool.pop();
            } else {
                i++;
            }
        }
    }

    /**
     * @notice Evict one bot from the pool (swap-pop). Bot stake is virtual, so no refund.
     * @param replacedBy The human taking the freed seat (for event logging only).
     */
    function _evictOneBot(address replacedBy) internal returns (bool) {
        for (uint256 i = validatorPool.length; i > 0; i--) {
            address v = validatorPool[i - 1];
            if (isBot[v]) {
                uint256 amt = stakes[v];
                if (amt > 0) {
                    totalStaked -= amt;
                    stakes[v] = 0;
                }
                inPool[v] = false;
                isBot[v] = false;
                exited[v] = false;
                validatorPool[i - 1] = validatorPool[validatorPool.length - 1];
                validatorPool.pop();
                emit BotEvicted(v, replacedBy);
                return true;
            }
        }
        return false;
    }

    /**
     * @notice Top the pool back up to poolSize with bots (instructor/conductor only).
     *         Used to keep the simulation full as humans exit or bots are evicted.
     */
    function refillBots(address[] calldata botAddresses) external onlyInstructor {
        require(sessionState == SessionState.ACTIVE || sessionState == SessionState.LOBBY, "Session closed");
        uint256 added = 0;
        for (uint256 i = 0; i < botAddresses.length && validatorPool.length < poolSize; i++) {
            address bot = botAddresses[i];
            if (bot == address(0) || inPool[bot]) continue;

            uint256 r = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, bot, i))) % 33;
            uint256 botStake = MIN_STAKE + r * 1 ether;
            _rememberValidator(bot);
            stakes[bot] = botStake;
            totalStaked += botStake;
            validatorPool.push(bot);
            inPool[bot] = true;
            isBot[bot] = true;
            exited[bot] = false;
            slashed[bot] = false;
            delete pendingSlash[bot];
            added++;
        }
        if (added > 0 && sessionState == SessionState.ACTIVE) {
            _assignCommitteesForEpoch(currentEpoch);
        }
        emit BotsRefilled(added, validatorPool.length);
    }

    /**
     * @notice Rotate slashed validators out of the pool and replace them with fresh bots.
     *         Keeps the active (non-slashed) stake above the 2/3 quorum so the chain keeps
     *         justifying even after the slashing demo punishes misbehaving bots. The slash
     *         event itself has already been emitted, so the lesson is preserved.
     */
    function rotateSlashed(address[] calldata freshBots) external onlyInstructor {
        require(sessionState == SessionState.ACTIVE || sessionState == SessionState.LOBBY, "Session closed");

        // Remove every slashed validator (swap-pop). Their stake was already penalized;
        // drop the remainder from totalStaked so quorum is computed on healthy stake only.
        uint256 i = 0;
        uint256 removed = 0;
        while (i < validatorPool.length) {
            address v = validatorPool[i];
            if (slashed[v]) {
                uint256 amt = stakes[v];
                if (amt > 0) {
                    totalStaked -= amt;
                    stakes[v] = 0;
                }
                inPool[v] = false;
                isBot[v] = false;
                slashed[v] = false;
                delete pendingSlash[v];
                validatorPool[i] = validatorPool[validatorPool.length - 1];
                validatorPool.pop();
                removed++;
                // do not advance i: re-check the element swapped into this slot
            } else {
                i++;
            }
        }

        // Backfill with fresh bots up to poolSize.
        uint256 added = 0;
        for (uint256 j = 0; j < freshBots.length && validatorPool.length < poolSize; j++) {
            address bot = freshBots[j];
            if (bot == address(0) || inPool[bot]) continue;

            uint256 r = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, bot, j))) % 33;
            uint256 botStake = MIN_STAKE + r * 1 ether;
            _rememberValidator(bot);
            stakes[bot] = botStake;
            totalStaked += botStake;
            validatorPool.push(bot);
            inPool[bot] = true;
            isBot[bot] = true;
            exited[bot] = false;
            slashed[bot] = false;
            delete pendingSlash[bot];
            added++;
        }

        if ((removed > 0 || added > 0) && sessionState == SessionState.ACTIVE) {
            _assignCommitteesForEpoch(currentEpoch);
        }
        emit BotsRefilled(added, validatorPool.length);
    }

    /**
     * @notice Instructor fills pool with bots and starts the session
     */
    function fillBotsAndStart(address[] calldata botAddresses, bool _requireHumanAttestation) external onlyInstructor {
        require(sessionState == SessionState.LOBBY, "Not in lobby");
        // A conductor may start a bots-only simulation that humans drop into later,
        // so an empty human pool is allowed.

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
            _rememberValidator(bot);
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

    function setPivotalMode(bool _enabled) external onlyInstructor {
        pivotalMode = _enabled;
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
        _removeValidatorFromPool(msg.sender);
        if (sessionState == SessionState.ACTIVE) {
            lastAssignedEpoch[currentEpoch] = 0;
            _assignCommitteesForEpoch(currentEpoch);
        }

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

        if (validatorPool.length >= poolSize) {
            require(_evictOneBot(msg.sender), "Pool full");
        }

        _rememberValidator(msg.sender);
        stakes[msg.sender] = msg.value;
        totalStaked += msg.value;
        validatorPool.push(msg.sender);
        inPool[msg.sender] = true;
        exited[msg.sender] = false;
        isBot[msg.sender] = false;
        joinedAtBlock[msg.sender] = blocks.length;

        // Seat the rejoiner into the current epoch immediately (see join()).
        if (sessionState == SessionState.ACTIVE) {
            lastAssignedEpoch[currentEpoch] = 0;
            _assignCommitteesForEpoch(currentEpoch);
        }
        emit Joined(msg.sender, msg.value);
    }

    function resetSession() external onlyInstructor {
        require(sessionState != SessionState.LOBBY, "Already in lobby");

        uint256 len = knownValidators.length;
        for (uint256 i = 0; i < len; i++) {
            address member = knownValidators[i];
            uint256 amt = stakes[member];
            if (amt > 0) {
                stakes[member] = 0;
                if (!isBot[member]) {
                    (bool ok,) = member.call{value: amt}("");
                    require(ok, "Refund failed");
                }
            }
            inPool[member] = false;
            exited[member] = false;
            isBot[member] = false;
            slashed[member] = false;
            knownValidator[member] = false;
            delete pendingSlash[member];
            for (uint256 j = 0; j < blocks.length; j++) {
                attestedSlotToBlock[member][_attestedSlotKey(blocks[j].epoch, blocks[j].slot)] = 0;
            }
        }

        while (validatorPool.length > 0) validatorPool.pop();
        while (knownValidators.length > 0) knownValidators.pop();
        while (blocks.length > 0) blocks.pop();
        for (uint256 e = 1; e <= currentEpoch; e++) {
            delete lastAssignedEpoch[e];
        }

        totalStaked = 0;
        currentEpoch = 1;
        currentSlot = 1;
        lastFinalizedIndex = 0;
        sessionId++;
        proposalPending = false;
        scheduledProposer = address(0);
        proposalSlot = 0;
        proposalOptionCount = 0;
        delete mevOptions;
        delete proposalBundleRoots;
        sessionState = SessionState.LOBBY;

        emit SessionReset(sessionId);
    }

    // ==================== COMMITTEE ASSIGNMENT ====================

    function _assignCommitteesForEpoch(uint256 epoch) internal {
        if (lastAssignedEpoch[epoch] != 0) return;
        lastAssignedEpoch[epoch] = block.timestamp;
        uint256 n = validatorPool.length;
        for (uint256 c = 0; c < committeesPerEpoch; c++) {
            for (uint256 k = 0; k < validatorsPerCommittee; k++) {
                delete committeeMember[epoch][c][k];
            }
        }
        if (n == 0) return;
        uint256 idx = 0;
        for (uint256 i = 0; i < n && idx < committeesPerEpoch * validatorsPerCommittee; i++) {
            address v = validatorPool[i];
            if (!inPool[v] || exited[v] || slashed[v] || stakes[v] == 0) continue;
            uint256 c = idx % committeesPerEpoch;
            uint256 k = idx / committeesPerEpoch;
            if (k < validatorsPerCommittee) committeeMember[epoch][c][k] = v;
            idx++;
        }
        emit CommitteesAssigned(epoch);
    }

    function _isInCommittee(address validator, uint256 epoch, uint256 slot) internal view returns (bool) {
        // The block stores its own epoch; deriving it from the (per-epoch) slot is wrong
        // because slot resets each epoch, which would lock attestation to epoch 1 only.
        if (!inPool[validator] || exited[validator] || slashed[validator] || stakes[validator] == 0) return false;
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

        // A human's proposal slot expired without a choice: penalize the miss and
        // fall back to a bot proposer so block production keeps flowing.
        if (proposalPending) {
            address missed = scheduledProposer;
            proposalPending = false;
            scheduledProposer = address(0);
            proposalOptionCount = 0;
            delete mevOptions;
            delete proposalBundleRoots;
            if (missed != address(0) && !isBot[missed] && !slashed[missed] && stakes[missed] >= MISSED_PROPOSAL_PENALTY) {
                stakes[missed] -= MISSED_PROPOSAL_PENALTY;
                totalStaked -= MISSED_PROPOSAL_PENALTY;
                emit ProposalMissed(missed, proposalSlot, MISSED_PROPOSAL_PENALTY);
            }
        }

        address proposer = _selectProposer(true); // bots propose the auto path; humans propose interactively
        _createBlock(proposer, 0);
        return proposer;
    }

    /**
     * @notice Conductor opens a proposal slot for a human, presenting candidate blocks
     *         of differing fee/MEV value. The human picks one via proposeAsProposer() before
     *         the window closes; otherwise proposeBlock() fallback-proposes.
     */
    function openProposalSlot(address proposer) external onlyInstructor {
        uint256 seed = uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrandao, proposer, blocks.length)));
        uint256[3] memory options = [
            uint256(0.02 ether + (seed % 31) * 0.001 ether),
            uint256(0.05 ether + ((seed >> 8) % 81) * 0.001 ether),
            uint256(0.04 ether + ((seed >> 16) % 161) * 0.001 ether)
        ];
        bytes32[3] memory roots = [bytes32(0), bytes32(0), bytes32(0)];
        _openProposalSlot(proposer, 3, options, roots);
    }

    function openProposalSlotWithBundles(address proposer, uint8 optionCount, uint256[3] calldata options, bytes32[3] calldata roots) external onlyInstructor {
        _openProposalSlot(proposer, optionCount, options, roots);
    }

    function _openProposalSlot(address proposer, uint8 optionCount, uint256[3] memory options, bytes32[3] memory roots) internal {
        require(sessionState == SessionState.ACTIVE, "Session not active");
        require(!proposalPending, "Proposal already pending");
        require(inPool[proposer] && !isBot[proposer] && !slashed[proposer] && !exited[proposer], "Not an eligible human");
        require(optionCount >= 1 && optionCount <= 3, "Invalid option count");
        scheduledProposer = proposer;
        proposalPending = true;
        proposalSlot = currentSlot;
        proposalOptionCount = optionCount;
        for (uint8 i = 0; i < 3; i++) {
            mevOptions[i] = options[i];
            proposalBundleRoots[i] = roots[i];
        }
        emit ProposalSlotOpened(proposer, currentSlot, mevOptions[0], mevOptions[1], mevOptions[2]);
        emit ProposalBundlesOpened(proposer, currentSlot, optionCount, mevOptions[0], mevOptions[1], mevOptions[2], roots[0], roots[1], roots[2]);
    }

    /**
     * @notice Scheduled human proposer builds the block by choosing one of the 3 MEV
     *         candidates. Earns BLOCK_REWARD plus the chosen block's MEV value.
     */
    function proposeAsProposer(uint8 choice) external returns (uint256) {
        require(sessionState == SessionState.ACTIVE, "Session not active");
        require(proposalPending && msg.sender == scheduledProposer, "Not your proposal slot");
        require(choice < proposalOptionCount, "Invalid choice");
        uint256 bonus = mevOptions[choice];
        proposalPending = false;
        scheduledProposer = address(0);
        proposalOptionCount = 0;
        delete mevOptions;
        delete proposalBundleRoots;
        uint256 idx = _createBlock(msg.sender, bonus);
        emit ProposalChosen(msg.sender, idx, choice, bonus);
        return idx;
    }

    function getProposalState() external view returns (bool pending, address proposer, uint256 slot, uint256[3] memory options) {
        return (proposalPending, scheduledProposer, proposalSlot, mevOptions);
    }

    function getProposalDetails() external view returns (bool pending, address proposer, uint256 slot, uint8 optionCount, uint256[3] memory options, bytes32[3] memory roots) {
        return (proposalPending, scheduledProposer, proposalSlot, proposalOptionCount, mevOptions, proposalBundleRoots);
    }

    function _selectProposer(bool botsOnly) internal view returns (address) {
        address[] memory eligible = new address[](validatorPool.length);
        uint256 eligibleCount = 0;
        uint256 eligibleStake = 0;
        for (uint256 i = 0; i < validatorPool.length; i++) {
            address v = validatorPool[i];
            if (!exited[v] && !slashed[v] && stakes[v] > 0 && (!botsOnly || isBot[v])) {
                eligible[eligibleCount] = v;
                eligibleCount++;
                eligibleStake += stakes[v];
            }
        }
        if (eligibleCount == 0 || eligibleStake == 0) return instructor;
        uint256 random = uint256(keccak256(abi.encodePacked(
            block.timestamp, block.prevrandao, totalStaked, blocks.length
        ))) % eligibleStake;
        uint256 cumulative = 0;
        for (uint256 i = 0; i < eligibleCount; i++) {
            cumulative += stakes[eligible[i]];
            if (random < cumulative) return eligible[i];
        }
        return eligible[0];
    }

    function _createBlock(address proposer, uint256 mevBonus) internal returns (uint256) {
        // Assign committees for new epoch if needed
        if (currentSlot == 1) {
            _assignCommitteesForEpoch(currentEpoch);
        }

        if (proposer != instructor && inPool[proposer]) {
            stakes[proposer] += BLOCK_REWARD + mevBonus;
            totalStaked += BLOCK_REWARD + mevBonus;
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
            finalized: false,
            epoch: currentEpoch
        }));
        uint256 blockIndex = blocks.length - 1;
        blocks[blockIndex].blockHash = keccak256(abi.encodePacked(
            blockIndex, proposer, parentHash, slot, currentEpoch, sessionId
        ));

        // Bots in committee for this slot auto-attest (occasionally one tries wrong hash for demo).
        // In pivotal mode they stop just below the 2/3 quorum, leaving the block for a human to
        // justify; the fallback pass (next block) lets bots finish if no human attested in time.
        uint256 committeeIndex = (slot - 1) % committeesPerEpoch;
        uint256 quorum = (totalStaked * QUORUM_NUMERATOR) / QUORUM_DENOMINATOR;
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
                    // Pivotal holdback: don't let bots cross 2/3 — leave the deciding vote to a human.
                    if (pivotalMode && blocks[blockIndex].attestationStake + stakes[v] >= quorum) {
                        continue;
                    }
                    _applyAttestation(v, blockIndex, slot);
                }
            }
        }

        // Inactivity penalty: a human committee member who failed to attest the
        // PREVIOUS block (their duty, with a one-slot grace to actually click) loses a
        // small amount. Skipped for validators who joined after that block and across
        // epoch boundaries (committee membership is only stable within an epoch).
        if (inactivityPenaltyEnabled && blockIndex > 0) {
            uint256 prevIndex = blockIndex - 1;
            if (blocks[prevIndex].epoch == currentEpoch) {
                uint256 prevCommittee = (blocks[prevIndex].slot - 1) % committeesPerEpoch;
                for (uint256 k = 0; k < validatorsPerCommittee; k++) {
                    address v = committeeMember[currentEpoch][prevCommittee][k];
                    if (v != address(0) && !isBot[v] && !slashed[v] && !exited[v]
                        && stakes[v] >= INACTIVITY_PENALTY
                        && joinedAtBlock[v] <= prevIndex
                        && !hasAttestedBlock[sessionId][prevIndex][v]) {
                        stakes[v] -= INACTIVITY_PENALTY;
                        totalStaked -= INACTIVITY_PENALTY;
                        emit InactivityPenalty(v, prevIndex, INACTIVITY_PENALTY);
                    }
                }
            }
        }

        // Pivotal fallback: the previous block was held just below quorum so a human could
        // be the deciding vote. If it's still un-justified now (no human attested in its
        // slot), the held-back bots attest so the chain still finalizes when idle.
        if (pivotalMode && blockIndex > 0 && !blocks[blockIndex - 1].justified) {
            uint256 prevIdx = blockIndex - 1;
            uint256 prevEpoch = blocks[prevIdx].epoch;
            uint256 prevCommittee = (blocks[prevIdx].slot - 1) % committeesPerEpoch;
            uint256 prevQuorum = (totalStaked * QUORUM_NUMERATOR) / QUORUM_DENOMINATOR;
            for (uint256 k = 0; k < validatorsPerCommittee && blocks[prevIdx].attestationStake < prevQuorum; k++) {
                address v = committeeMember[prevEpoch][prevCommittee][k];
                if (v != address(0) && isBot[v] && !slashed[v] && stakes[v] > 0 && !hasAttestedBlock[sessionId][prevIdx][v]) {
                    _applyAttestation(v, prevIdx, blocks[prevIdx].slot);
                }
            }
            _checkJustification(prevIdx);
        }

        uint256 blockEpoch = blocks[blockIndex].epoch;

        if (currentSlot >= blocksPerEpoch) {
            currentSlot = 1;
            currentEpoch++;
            emit EpochAdvanced(currentEpoch);
        } else {
            currentSlot++;
        }

        _checkJustification(blockIndex);
        _checkFinality();

        emit BlockProposed(blockIndex, proposer, blockEpoch);
        return blockIndex;
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
        uint256 forkEpoch = latest.epoch;

        blocks.push(BlockInfo({
            proposer: proposer,
            blockHash: bytes32(0),
            parentHash: parentHash,
            slot: slot,
            attestationCount: 0,
            attestationStake: 0,
            humanAttestationCount: 0,
            justified: false,
            finalized: false,
            epoch: forkEpoch
        }));
        uint256 blockIndex = blocks.length - 1;
        blocks[blockIndex].blockHash = keccak256(abi.encodePacked(
            blockIndex, proposer, parentHash, slot, forkEpoch, sessionId
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

        emit BlockProposed(blockIndex, proposer, forkEpoch);
        return proposer;
    }

    // ==================== ATTESTATION ====================

    function attest(uint256 blockIndex, bytes32 claimedHash) external onlyInPool notSlashedMod {
        require(sessionState == SessionState.ACTIVE, "Session not active");
        require(blockIndex < blocks.length, "Invalid block");
        require(!hasAttestedBlock[sessionId][blockIndex][msg.sender], "Already attested");

        BlockInfo storage b = blocks[blockIndex];
        require(_isInCommittee(msg.sender, b.epoch, b.slot), "Not in committee for this slot");

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
        uint256 epochSlotKey = _attestedSlotKey(b.epoch, b.slot);
        uint256 prevStored = attestedSlotToBlock[msg.sender][epochSlotKey];
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
        attestedSlotToBlock[validator][_attestedSlotKey(blocks[blockIndex].epoch, slot)] = blockIndex + 1;
        blocks[blockIndex].attestationCount++;
        blocks[blockIndex].attestationStake += stakes[validator];
        if (!isBot[validator]) {
            blocks[blockIndex].humanAttestationCount++;
            // Reward human attesters so attesting visibly grows their stake (in real
            // Ethereum attesters earn the bulk of rewards). Backed by the reward pool.
            stakes[validator] += ATTESTATION_REWARD;
            totalStaked += ATTESTATION_REWARD;
        }
        emit Attested(validator, blockIndex);
    }

    function _attestedSlotKey(uint256 epoch, uint256 slot) internal pure returns (uint256) {
        return (epoch << 128) | slot;
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

    function _findJustifiedCheckpoint(uint256 epoch) internal view returns (uint256) {
        if (epoch == 0) return type(uint256).max;
        for (uint256 i = blocks.length; i > 0; i--) {
            uint256 idx = i - 1;
            if (blocks[idx].epoch == epoch && blocks[idx].slot == blocksPerEpoch && blocks[idx].justified) {
                return idx;
            }
        }
        return type(uint256).max;
    }

    function _checkFinality() internal {
        if (blocks.length < 2 * blocksPerEpoch) return;

        // Casper FFG: checkpoint = last slot of each epoch. Do not derive checkpoints
        // from array indexes: fork-demo blocks can add extra entries with duplicate slots.
        uint256 currentCheckpoint = type(uint256).max;
        uint256 prevCheckpoint = type(uint256).max;
        for (uint256 i = blocks.length; i > 0; i--) {
            uint256 idx = i - 1;
            if (blocks[idx].slot != blocksPerEpoch || !blocks[idx].justified) continue;
            uint256 epoch = blocks[idx].epoch;
            if (epoch <= 1) continue;
            uint256 prev = _findJustifiedCheckpoint(epoch - 1);
            if (prev != type(uint256).max) {
                currentCheckpoint = idx;
                prevCheckpoint = prev;
                break;
            }
        }

        if (currentCheckpoint == type(uint256).max || prevCheckpoint == type(uint256).max) return;

        uint256 toFinalize = prevCheckpoint;
        if (blocks[toFinalize].finalized) return;
        blocks[toFinalize].finalized = true;
        if (toFinalize > lastFinalizedIndex) lastFinalizedIndex = toFinalize;
        emit BlockFinalized(toFinalize);
        // Transitive: finalize any justified ancestors on canonical chain that are not yet finalized
        while (toFinalize > 0) {
            bytes32 ph = blocks[toFinalize].parentHash;
            if (ph == bytes32(0)) break;
            uint256 prev = _findBlockIndexByHash(ph);
            if (prev == type(uint256).max) break;
            if (!blocks[prev].justified || blocks[prev].finalized) break;
            blocks[prev].finalized = true;
            if (prev > lastFinalizedIndex) lastFinalizedIndex = prev;
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
        bool finalized,
        uint256 epoch
    ) {
        require(index < blocks.length, "Invalid block");
        BlockInfo storage b = blocks[index];
        return (b.proposer, b.blockHash, b.parentHash, b.slot, b.attestationCount, b.attestationStake, b.humanAttestationCount, b.justified, b.finalized, b.epoch);
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
