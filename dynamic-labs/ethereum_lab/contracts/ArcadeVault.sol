// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

interface IArcadeTokenBurnFrom {
    function burnFrom(address account, uint256 amount) external;
}

/**
 * @title ArcadeVault
 * @dev Burns one ARC to authorize one off-chain arcade game session, then
 * records client-attested scores for that burned session.
 */
contract ArcadeVault is ReentrancyGuard {
    uint256 public constant PLAY_COST = 1 ether;
    uint256 public constant MAX_SCORE = 1_000_000;

    IArcadeTokenBurnFrom public immutable token;
    mapping(address => uint256) public sessionNonce;
    mapping(address => mapping(uint256 => uint8)) public sessionGame;
    mapping(address => mapping(uint256 => bool)) public scoreSubmitted;

    struct ScoreRecord {
        address player;
        uint8 gameId;
        uint256 nonce;
        uint256 score;
        uint256 elapsedMs;
        uint256 timestamp;
    }

    mapping(address => mapping(uint8 => ScoreRecord)) public personalBest;
    mapping(uint8 => ScoreRecord) public highScore;

    event SessionStarted(address indexed player, uint8 indexed gameId, uint256 nonce, uint256 timestamp);
    event ScoreSubmitted(
        address indexed player,
        uint8 indexed gameId,
        uint256 indexed nonce,
        uint256 score,
        uint256 elapsedMs,
        uint256 timestamp,
        bool personalBest,
        bool globalBest
    );

    constructor(IArcadeTokenBurnFrom token_) {
        require(address(token_) != address(0), "ArcadeVault: token required");
        token = token_;
    }

    function playGame(uint8 gameId) external nonReentrant {
        require(gameId > 0, "ArcadeVault: game required");
        token.burnFrom(msg.sender, PLAY_COST);
        uint256 nonce = ++sessionNonce[msg.sender];
        sessionGame[msg.sender][nonce] = gameId;
        emit SessionStarted(msg.sender, gameId, nonce, block.timestamp);
    }

    function submitScore(uint8 gameId, uint256 nonce, uint256 score, uint256 elapsedMs) external nonReentrant {
        require(gameId > 0, "ArcadeVault: game required");
        require(nonce > 0 && nonce <= sessionNonce[msg.sender], "ArcadeVault: unknown session");
        require(sessionGame[msg.sender][nonce] == gameId, "ArcadeVault: wrong game");
        require(!scoreSubmitted[msg.sender][nonce], "ArcadeVault: score already submitted");
        require(score > 0 && score <= MAX_SCORE, "ArcadeVault: score out of range");

        scoreSubmitted[msg.sender][nonce] = true;

        bool isPersonalBest = _isBetter(score, elapsedMs, personalBest[msg.sender][gameId]);
        bool isGlobalBest = _isBetter(score, elapsedMs, highScore[gameId]);
        ScoreRecord memory record = ScoreRecord({
            player: msg.sender,
            gameId: gameId,
            nonce: nonce,
            score: score,
            elapsedMs: elapsedMs,
            timestamp: block.timestamp
        });

        if (isPersonalBest) {
            personalBest[msg.sender][gameId] = record;
        }
        if (isGlobalBest) {
            highScore[gameId] = record;
        }

        emit ScoreSubmitted(msg.sender, gameId, nonce, score, elapsedMs, block.timestamp, isPersonalBest, isGlobalBest);
    }

    function _isBetter(uint256 score, uint256 elapsedMs, ScoreRecord memory current) private pure returns (bool) {
        if (current.score == 0) {
            return true;
        }
        if (score > current.score) {
            return true;
        }
        return score == current.score && elapsedMs > 0 && (current.elapsedMs == 0 || elapsedMs < current.elapsedMs);
    }
}
