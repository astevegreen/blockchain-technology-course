import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ethers } from 'ethers'
import { connectWallet, checkNodeStatus, getGuestWallet, getWalletInfo, importWallet, generateNewWallet, setWalletNickname, getWalletList, setActiveWallet, addWallet } from './web3'
import PoSABI from './PoS.json'
import { InstructorView } from './views/InstructorView'
import { DiagnosticsView } from './views/DiagnosticsView'
import { TokenConceptsView } from './views/TokenConceptsView'
import { BeaconChainLabView } from './views/BeaconChainLabView'
import { ContractBuilderLabView } from './views/ContractBuilderLabView'
import { TokenizationLabView } from './views/TokenizationLabView'
import { LABS, INITIAL_SETUP, getLabById } from './constants/labs'
import { ROLE_CONTRACT_TEMPLATES } from './constants/roleContractTemplates'
import LabDetailView from './components/LabDetailView'
import ContractLab from './components/ContractLab'
import { blockchainSync } from './lib/BlockchainSync'
import { copyToClipboard } from './lib/clipboard'
import { resolveRpcUrl, rpcClient } from './lib/RpcClient'
import AccountManager from './components/AccountManager'
import InlineTerminal from './components/InlineTerminal'
import NodeGraph from './components/NodeGraph'
import { ChainSearch } from './components/ChainSearch'
import { RoleHub } from './components/RoleHub'
import { PoSLeaderboard } from './components/PoSLeaderboard'
import { ErrorBoundary } from './components/ErrorBoundary'
import {
  BlockchainVisualizer,
  AddressDecoder,
  StakingRewards,
  ValidatorProbability,
  SlashingPenalty,
  AttackCost,
} from './components/mini-labs'
import './index.css'

// Open Lab Terminal in new window/tab (each call opens a new one for multiple terminals).
// rpcUrl is browser-facing; terminalRpcUrl is an optional shell-only override.
function openLabTerminal(rpcUrl, terminalRpcUrl = '') {
  const base = (typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/';
  let path = base.replace(/\/$/, '') + '/terminal';
  if (rpcUrl && rpcUrl.trim()) {
    path += '?rpc=' + encodeURIComponent(rpcUrl.trim());
  }
  if (terminalRpcUrl && terminalRpcUrl.trim()) {
    path += (path.includes('?') ? '&' : '?') + 'trpc=' + encodeURIComponent(terminalRpcUrl.trim());
  }
  window.open(path, 'lab-terminal-' + Date.now(), 'noopener,noreferrer,width=1000,height=700,scrollbars=yes');
}

const SHAREABLE_QUERY_VIEWS = new Set([
  'live',
  'diagnostics',
  'beacon-lab',
  'contract-builder-lab',
  'tokenization-lab',
])

// Account 0 = deployer = bank/faucet (Hardhat's first test account).
// The deployer holds onlyInstructor privileges; the bank sends test ETH to students.
// ============= KM METADATA & PROVENANCE =============
const CONTENT_METADATA = {
    version: "1.1.3",
    lastUpdated: "March 27 2026",
    author: "Ethereum Lab Development Team",
    sources: [
        "Ethereum Foundation Documentation",
        "ethereum.org/staking",
        "Vitalik Buterin's Blog",
        "EIP-3675 (The Merge)"
    ],
    reviewedBy: "Academic Review Committee",
    accuracy: "Content verified against Ethereum mainnet specifications"
};

// Provenance Badge Component
const ProvenanceBadge = ({ showFull = false }) => (
    <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        padding: showFull ? '12px 16px' : '6px 12px',
        background: 'rgba(34, 197, 94, 0.1)',
        border: '1px solid rgba(34, 197, 94, 0.3)',
        borderRadius: '8px',
        fontSize: showFull ? '0.85rem' : '0.75rem',
        color: '#86efac'
    }}>
        <span style={{color: '#22c55e'}}>✓</span>
        <span>Verified Content</span>
        {showFull && (
            <span style={{color: '#64748b', marginLeft: '8px'}}>
                | Updated {CONTENT_METADATA.lastUpdated} | v{CONTENT_METADATA.version}
            </span>
        )}
    </div>
);

// Feedback Component
const FeedbackButton = ({ section, onFeedback }) => {
    const [showForm, setShowForm] = useState(false);
    const [feedback, setFeedback] = useState('');
    const [rating, setRating] = useState(0);
    const [submitted, setSubmitted] = useState(false);
    
    const handleSubmit = () => {
        // Save feedback to localStorage
        let existingFeedback = [];
        try {
            existingFeedback = JSON.parse(localStorage.getItem('lab_feedback') || '[]');
            if (!Array.isArray(existingFeedback)) existingFeedback = [];
        } catch {
            existingFeedback = [];
        }
        existingFeedback.push({
            section,
            rating,
            feedback,
            timestamp: Date.now()
        });
        localStorage.setItem('lab_feedback', JSON.stringify(existingFeedback));
        setSubmitted(true);
        setTimeout(() => {
            setShowForm(false);
            setSubmitted(false);
            setFeedback('');
            setRating(0);
        }, 2000);
    };
    
    if (submitted) {
        return (
            <div style={{
                padding: '12px 16px',
                background: 'rgba(34, 197, 94, 0.2)',
                borderRadius: '8px',
                color: '#86efac',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }}>
                ✅ Thank you for your feedback!
            </div>
        );
    }
    
    if (!showForm) {
        return (
            <button
                onClick={() => setShowForm(true)}
                style={{
                    padding: '8px 16px',
                    background: 'transparent',
                    border: '1px solid #475569',
                    borderRadius: '6px',
                    color: '#94a3b8',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                    e.target.style.borderColor = '#3b82f6';
                    e.target.style.color = '#93c5fd';
                }}
                onMouseOut={(e) => {
                    e.target.style.borderColor = '#475569';
                    e.target.style.color = '#94a3b8';
                }}
            >
                💬 Give Feedback
            </button>
        );
    }
    
    return (
        <div style={{
            padding: '16px',
            background: '#1e293b',
            borderRadius: '12px',
            border: '1px solid #334155'
        }}>
            <div style={{marginBottom: '12px', color: '#e2e8f0', fontWeight: '600'}}>
                How helpful was this section?
            </div>
            <div style={{display: 'flex', gap: '8px', marginBottom: '12px'}}>
                {[1, 2, 3, 4, 5].map(star => (
                    <button
                        key={star}
                        onClick={() => setRating(star)}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            fontSize: '1.5rem',
                            cursor: 'pointer',
                            opacity: star <= rating ? 1 : 0.3,
                            transition: 'opacity 0.2s'
                        }}
                    >
                        ⭐
                    </button>
                ))}
            </div>
            <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="What could be improved? (optional)"
                style={{
                    width: '100%',
                    padding: '10px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#e2e8f0',
                    fontSize: '0.9rem',
                    minHeight: '60px',
                    resize: 'vertical',
                    marginBottom: '12px'
                }}
            />
            <div style={{display: 'flex', gap: '8px'}}>
                <button
                    onClick={handleSubmit}
                    disabled={rating === 0}
                    style={{
                        padding: '8px 16px',
                        background: rating > 0 ? '#3b82f6' : '#374151',
                        border: 'none',
                        borderRadius: '6px',
                        color: 'white',
                        cursor: rating > 0 ? 'pointer' : 'not-allowed',
                        fontWeight: '600',
                        fontSize: '0.85rem'
                    }}
                >
                    Submit
                </button>
                <button
                    onClick={() => setShowForm(false)}
                    style={{
                        padding: '8px 16px',
                        background: 'transparent',
                        border: '1px solid #475569',
                        borderRadius: '6px',
                        color: '#94a3b8',
                        cursor: 'pointer',
                        fontSize: '0.85rem'
                    }}
                >
                    Cancel
                </button>
            </div>
        </div>
    );
};

// Social Proof Component - Shows community activity (compact, expandable)
const SocialProof = ({ validators, messages, stakersCount }) => {
    const [expanded, setExpanded] = useState(false);
    const [localStats, setLocalStats] = useState({ quizzes: 0, sessions: 0 });
    
    useEffect(() => {
        // Get aggregated local stats
        let feedback = [];
        let savedScores = {};
        try {
            feedback = JSON.parse(localStorage.getItem('lab_feedback') || '[]');
            if (!Array.isArray(feedback)) feedback = [];
        } catch {
            feedback = [];
        }
        try {
            savedScores = JSON.parse(localStorage.getItem('quiz_scores') || '{}') || {};
            if (savedScores === null || typeof savedScores !== 'object' || Array.isArray(savedScores)) {
                savedScores = {};
            }
        } catch {
            savedScores = {};
        }
        const sessionStart = localStorage.getItem('session_start');
        
        setLocalStats({
            quizzes: Object.keys(savedScores).length,
            sessions: sessionStart ? 1 : 0,
            feedbackCount: feedback.length
        });
    }, []);
    
    const activeStudents = validators?.length || 0;
    const totalMessages = messages?.length || 0;
    const participantCount = activeStudents || stakersCount || 0;
    
    return (
        <div style={{
            padding: '0.4rem 0.65rem',
            marginBottom: '0.75rem',
            background: 'rgba(59, 130, 246, 0.05)',
            borderRadius: '0.35rem',
            border: '1px solid rgba(59, 130, 246, 0.2)'
        }}>
            <button
                onClick={() => setExpanded(!expanded)}
                style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    padding: 0
                }}
            >
                <span>{expanded ? '▼' : '▶'}</span>
                <span>{participantCount} participants</span>
                {totalMessages > 0 && <span style={{color: '#64748b'}}>· {totalMessages} messages</span>}
            </button>
            {expanded && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(59,130,246,0.15)' }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                background: 'rgba(34, 197, 94, 0.1)',
                borderRadius: '20px'
            }}>
                <span style={{fontSize: '1.1rem'}}>👥</span>
                <span style={{color: '#86efac', fontWeight: '600', fontSize: '0.9rem'}}>
                    {activeStudents} Active {activeStudents === 1 ? 'Student' : 'Students'}
                </span>
            </div>
            
            {totalMessages > 0 && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    background: 'rgba(139, 92, 246, 0.1)',
                    borderRadius: '20px'
                }}>
                    <span style={{fontSize: '1.1rem'}}>💬</span>
                    <span style={{color: '#a78bfa', fontWeight: '600', fontSize: '0.9rem'}}>
                        {totalMessages} {totalMessages === 1 ? 'Message' : 'Messages'} Shared
                    </span>
                </div>
            )}
            
            {stakersCount > 0 && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    background: 'rgba(251, 191, 36, 0.1)',
                    borderRadius: '20px'
                }}>
                    <span style={{fontSize: '1.1rem'}}>🏦</span>
                    <span style={{color: '#fcd34d', fontWeight: '600', fontSize: '0.9rem'}}>
                        {stakersCount} {stakersCount === 1 ? 'Validator' : 'Validators'} Staking
                    </span>
                </div>
            )}
            
            {localStats.quizzes > 0 && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 10px',
                    background: 'rgba(236, 72, 153, 0.1)',
                    borderRadius: '0.35rem',
                    fontSize: '0.8rem'
                }}>
                    <span>✅</span>
                    <span style={{color: '#f472b6', fontWeight: '600'}}>{localStats.quizzes} Quizzes</span>
                </div>
            )}
        </div>
            )}
        </div>
    );
};


// --- ORIENTATION CONTENT ---
const INTRO_SECTIONS = [
    {
        title: "🌐 What is Ethereum?",
        bullets: [
            "Ethereum is not just money—it's a global, shared computer that no one owns",
            "Decentralized: Runs on thousands of computers (nodes) simultaneously worldwide",
            "Immutable: Once data is written to the blockchain, it cannot be erased or altered",
            "Programmable: You can write code (smart contracts) that executes automatically"
        ]
    },
    {
        title: "🎯 Why This Lab Exists",
        bullets: [
            "Experience a complete Ethereum stack without cloud services or real money",
            "Understand how the world's second-largest blockchain actually works",
            "Practice safely in a classroom environment before touching production networks",
            "See firsthand why Ethereum switched from Proof-of-Work to Proof-of-Stake"
        ]
    },
    {
        title: "📚 What You'll Learn",
        bullets: [
            "How Ethereum's Proof-of-Stake consensus keeps the network secure",
            "Why validators stake 32 ETH and how they earn rewards",
            "What 'slashing' means and why it prevents attacks",
            "How DeFi protocols use staking beyond just validation",
            "The real economics: why a 51% attack costs $51 billion"
        ]
    },
    {
        title: "🛠️ What You'll Do",
        bullets: [
            "Generate your own wallet and receive test ETH from your instructor",
            "Send transactions to classmates and watch blocks confirm",
            "Stake ETH to become a validator and earn rewards",
            "Participate in the class chat (stored on-chain!)",
            "Experience the validator selection algorithm in action"
        ]
    },
    {
        title: "👥 Classroom Setup",
        bullets: [
            "Instructor runs a local Ethereum node with deployed smart contracts",
            "Students connect via web browser—no installation required",
            "Everyone shares the same blockchain producing blocks every ~12 seconds",
            "All transactions are real (but using test ETH with no real-world value)"
        ]
    }
]

const CONCEPT_CARDS = [
    {
        title: "🔐 Wallet Anatomy",
        description: "A wallet is cryptographic math, not a physical container. Your private key is everything.",
        highlight: [
            "Private key (64 hex chars) → signs transactions to prove you own the account",
            "Public address (0x + 40 hex chars) → your identity on Ethereum, derived from public key",
            "Never share your private key—anyone with it controls your funds",
            "Addresses start with '0x' and use hexadecimal (0-9, a-f)"
        ],
        // VIDEO PLACEHOLDER: Add YouTube URL explaining crypto wallets
        // Example: video: "https://www.youtube.com/embed/VIDEO_ID"
        video: "https://www.youtube.com/embed/qLZ1IoezucE"
    },
    {
        title: "⛽ Gas & Transaction Fees",
        description: "Every operation on Ethereum costs 'gas'—computational work measured in ETH.",
        highlight: [
            "Gas limit: Maximum gas you're willing to use (prevents infinite loops)",
            "Base fee: Burned (destroyed) ETH—reduces supply, can cause deflation",
            "Tip (priority fee): Goes to validator—higher tip = faster inclusion",
            "Simple ETH transfer: ~21,000 gas | Complex smart contract: 100k+ gas"
        ],
        // VIDEO PLACEHOLDER: Add YouTube URL explaining gas fees
        video: "https://www.youtube.com/embed/3ehaSqwUZ0s"
    },
    {
        title: "🧱 Blocks & Finality",
        description: "Ethereum produces a new block every ~12 seconds containing batched transactions.",
        highlight: [
            "Block = batch of transactions + cryptographic hash linking to previous block",
            "Block number (height) = total blocks since genesis (July 30, 2015)",
            "Finality: After ~15 minutes (64 blocks), blocks are irreversible",
            "Each block has a proposer (validator) who earns fees + rewards"
        ],
        // VIDEO PLACEHOLDER: Add YouTube URL explaining blockchain blocks
        video: "https://www.youtube.com/embed/eq1oRGLEG3Y"
    },
    {
        title: "🤝 Proof-of-Stake Consensus",
        description: "How 8,600+ validators worldwide agree on the state of Ethereum without a central authority.",
        highlight: [
            "Validators stake 32 ETH as collateral to participate",
            "Every 12 seconds, one validator is pseudo-randomly selected to propose a block",
            "Other validators attest (vote) that the block is valid",
            "Honest validators earn ~4-5% annual return; dishonest ones get slashed",
            "Replaced Proof-of-Work in Sept 2022, cutting energy use by 99.95%"
        ],
        diagram: true,
        fullWidth: true,
        // VIDEO PLACEHOLDER: Add YouTube URL explaining Proof of Stake (PRIORITY - core concept)
        video: null
    },
    {
        title: "💎 Ether (ETH)",
        description: "The native cryptocurrency of Ethereum—required for all transactions and staking.",
        highlight: [
            "Market cap: 2nd largest crypto after Bitcoin (~$200B+)",
            "Total supply: ~120 million ETH (no hard cap, but issuance is low)",
            "Uses: Pay gas fees, stake to become validator, collateral in DeFi",
            "Units: 1 ETH = 1,000,000,000 Gwei = 10¹⁸ Wei"
        ],
        // VIDEO PLACEHOLDER: Add YouTube URL explaining what ETH is
        video: null
    },
    {
        title: "📜 Smart Contracts",
        description: "Self-executing code deployed to Ethereum that anyone can interact with.",
        highlight: [
            "Written in Solidity, compiled to EVM bytecode",
            "Immutable: Once deployed, code cannot be changed",
            "Powers DeFi, NFTs, DAOs, games, and more",
            "Our lab uses a PoS simulator contract for staking and chat"
        ],
        // VIDEO PLACEHOLDER: Add YouTube URL explaining smart contracts
        video: null
    }
]

const EXPLORE_MISSIONS = [
    {
        title: "🔗 Understanding Staking",
        video: "https://www.youtube.com/embed/ja_Irb5LS1k",
        category: "Proof of Stake",
        action: "What is staking and why do validators lock up their ETH?",
        details: [
            "Staking means depositing ETH as collateral to become a validator",
            "Minimum stake on Ethereum: 32 ETH (our lab uses 1 ETH for learning)",
            "Staked ETH is locked—you can't spend it while validating",
            "Purpose: Creates 'skin in the game' so validators act honestly",
            "Honest validators earn rewards; dishonest ones get slashed"
        ],
        miniLab: 'staking-rewards',
        // VIDEO PLACEHOLDER: Add YouTube embed URL for staking explanation (PRIORITY)
        // Example: video: "https://www.youtube.com/embed/VIDEO_ID"
   
        quiz: {
            question: "Why must validators stake ETH?",
            options: [
                "To prove they have money",
                "To create economic incentive for honest behavior",
                "To pay for electricity",
                "Just for fun"
            ],
            correct: 1,
            explanation: "Staking creates 'skin in the game.' By locking up valuable ETH as collateral, validators have a financial incentive to act honestly. If they misbehave, they lose their stake. This economic mechanism aligns individual incentives with network security—honest behavior is profitable, dishonest behavior is costly."
        }
    },
    {
        title: "👮 Validator Responsibilities",
        category: "Network Security",
        action: "Learn what validators do to keep Ethereum secure",
        details: [
            "Propose new blocks when selected by the algorithm",
            "Verify (attest to) blocks proposed by other validators",
            "Must be online 24/7 with stable internet",
            "Run honest software—no cheating or double-signing",
            "Earn transaction fees + block rewards for good work"
        ],
        video: "https://www.youtube.com/embed/b9mNgGqxhJ8",
        miniLab: 'validator-probability',
        // VIDEO PLACEHOLDER: Add YouTube embed URL for validator duties explanation
        
        quiz: {
            question: "What happens if a validator goes offline?",
            options: [
                "Nothing, they just miss rewards",
                "They lose all their staked ETH",
                "They get small penalties (inactivity leak)",
                "They get a warning email"
            ],
            correct: 2,
            explanation: "The 'inactivity leak' gradually reduces offline validators' stakes. This is gentler than slashing—you won't lose everything for going offline, but you'll steadily lose ETH until you come back online. This encourages high uptime without being unfairly punishing for temporary outages."
        }
    },
    {
        title: "⚔️ Slashing: The Penalty System",
        category: "Network Security",
        action: "Understand how Ethereum punishes bad actors",
        details: [
            "Slashing = Burning (destroying) a validator's staked ETH",
            "Triggers: Double-signing blocks, or proposing contradictory data",
            "Penalty: Lose up to 100% of staked ETH (usually ~1 ETH minimum)",
            "Purpose: Make attacks extremely expensive (would need 51% of stake)",
            "Slashed validators are forcibly ejected from the network"
        ],
        miniLab: 'slashing-penalty',
        video: "https://www.youtube.com/embed/z7XUgjzvfCQ",
        quiz: {
            question: "What is slashing designed to prevent?",
            options: [
                "Validators taking vacations",
                "Network attacks and dishonest behavior",
                "Too many validators joining",
                "Gas fees from rising"
            ],
            correct: 1,
            explanation: "Slashing creates a strong economic deterrent against malicious behavior. If a validator tries to double-sign or propose conflicting blocks, they lose a significant portion of their staked ETH. This makes attacks extremely expensive—you can't 'try and walk away' like you could with rented mining equipment."
        }
    },
    {
        title: "🏦 DeFi: Staking Beyond Validation",
        category: "DeFi Applications",
        action: "Explore how staking powers decentralized finance",
        details: [
            "Liquid Staking: Deposit ETH, get stETH token, still earn rewards",
            "Example: Lido, Rocket Pool let you stake without 32 ETH",
            "Yield Farming: Stake tokens in protocols to earn interest",
            "Governance: Staked tokens often give voting rights in DAOs",
            "Risk: Smart contract bugs or protocol failures"
        ],
        // VIDEO PLACEHOLDER: Add YouTube embed URL for DeFi/liquid staking
        video: "https://www.youtube.com/embed/e9Eg0CmboFU",
        quiz: {
            question: "What is 'liquid staking'?",
            options: [
                "Staking water molecules",
                "Getting a tradable token while your ETH is staked",
                "Staking in a pool of liquid",
                "Only available for liquids"
            ],
            correct: 1,
            explanation: "Liquid staking solves the 'locked capital' problem. Services like Lido let you stake ETH and receive stETH in return—a token that still earns staking rewards but can be traded or used in DeFi. You get the benefits of staking without completely locking your funds."
        }
    },
    {
        title: "💰 Staking Rewards Economics",
        category: "Economics",
        action: "Calculate the incentives for running a validator",
        details: [
            "Base reward: ~4-5% annual return on staked ETH",
            "Higher when fewer validators are online",
            "Transaction fees (tips) add extra income",
            "MEV (Maximal Extractable Value): Advanced validators earn more",
            "Costs: Hardware, electricity, internet, downtime risks"
        ],
        // VIDEO PLACEHOLDER: Add YouTube embed URL for staking economics
        video: "https://www.youtube.com/embed/ja_Irb5LS1k",
        quiz: {
            question: "Why would someone run a validator?",
            options: [
                "Just to help the network (no rewards)",
                "Earn passive income on their ETH",
                "Get free NFTs",
                "To mine Bitcoin"
            ],
            correct: 1,
            explanation: "Validators earn ~4-5% APY on their staked ETH through block rewards and transaction fees. This creates a sustainable economic model—validators are incentivized to secure the network because they profit from doing so. It's passive income with the added benefit of supporting decentralization."
        }
    },
    {
        title: "🎯 Real-World Scenario: Attack Cost",
        category: "Network Security",
        
        action: "Calculate how expensive it is to attack Ethereum",
        details: [
            "To control 51% of validators, need 51% of all staked ETH",
            "Currently ~34 million ETH staked on Ethereum",
            "51% attack needs: ~17 million ETH",
            "At $3,000/ETH: $51 BILLION dollars needed",
            "And you'd LOSE it all via slashing if caught!",
            "Compare to Bitcoin: Rent mining hardware temporarily for attack"
        ],
        miniLab: 'attack-cost',
        video: "https://www.youtube.com/embed/8jOacOeGNSE",
        // VIDEO PLACEHOLDER: Add YouTube embed URL for 51% attack explanation
        
        quiz: {
            question: "Why is PoS more secure than PoW against attacks?",
            options: [
                "It's faster",
                "Attackers must BUY and LOSE massive amounts of ETH",
                "It uses less electricity",
                "Smart contracts protect it"
            ],
            correct: 1,
            explanation: "In Proof-of-Work, attackers can rent mining power temporarily, attack, and return the hardware. In Proof-of-Stake, attackers must actually OWN billions of dollars worth of ETH—and they'll LOSE it if caught. This 'nothing at stake' vs 'everything at stake' difference makes PoS economically more secure."
        }
    },
    {
        title: "🔄 Observe the Chain",
        category: "Hands-On",
        video: "https://www.youtube.com/embed/SSo_EIwHSd4",
        action: "Watch how blocks are linked together in a real blockchain.",
        details: [
            "Ethereum produces a block every ~12 seconds",
            "Each block contains many transactions",
            "Block number = blockchain 'height'",
            "Each block references the previous block's hash",
            "This creates an immutable chain - changing one block breaks all following blocks"
        ],
        miniLab: 'blockchain-visualizer'
    },
    {
        title: "🔑 Decode an Address",
        category: "Hands-On",
        action: "Learn how Ethereum addresses work and practice reading them.",
        details: [
            "Addresses start with '0x' (hexadecimal notation)",
            "42 characters total (0x + 40 hex digits)",
            "Derived from your public key using Keccak-256 hash",
            "Shorthand: 0x1234...5678 helps in class/chat",
            "Your address = your public identity on Ethereum"
        ],
        miniLab: 'address-decoder'
    }
]

// LESSONS removed - content now covered in INTRO_SECTIONS and CONCEPT_CARDS

// --- COMPONENT: CLI LABS VIEW ---

const CLI_SECTIONS = [
    { id: 'available-labs', title: 'Available Labs', category: 'Getting Started', keywords: ['labs', 'lab list', 'house sale', 'ransomware', 'voting', 'crowdfunding', 'tickets', 'vehicle', 'classroom', 'token'] },
    { id: 'initial-setup', title: 'Initial Setup', category: 'Getting Started', keywords: ['install', 'npm', 'setup', 'connection', 'RPC', 'environment', 'configure', 'terminal', 'start', 'begin', 'cli'] },
    { id: 'menu-options', title: 'Menu Options', category: 'Getting Started', keywords: ['menu', 'options', 'interactive', 'CLI', 'list', 'commands', 'playground', 'builder', 'account'] },
    { id: 'playground', title: 'Playground Mode', category: 'Getting Started', keywords: ['playground', 'console', 'JavaScript', 'REPL', 'analyst', 'interactive', 'JS', 'eval', 'help'] },
    { id: 'deploy-share', title: 'Deploy & Share: Working as a Team', category: 'Smart Contracts', keywords: ['deploy', 'share', 'connect', 'classmate', 'team', 'address', 'collaborate', 'ABI', 'dashboard', 'other students'] },
    { id: 'individual-labs', title: 'Individual Lab Scripts', category: 'Getting Started', keywords: ['lab', 'script', 'forensics', 'explore', 'transaction', 'blockchain basics', 'sign', 'interact'] },
    { id: 'contract-builder', title: 'Smart Contract Builder', category: 'Smart Contracts', keywords: ['template', 'builder', 'house', 'voting', 'tickets', 'crowdfunding', 'vehicle', 'classroom', 'option 9'] },
    { id: 'forensics-labs', title: 'Forensics Labs (Ransomware)', category: 'Forensics', keywords: ['ransomware', 'forensics-setup', '6-ransomware', '7-ransomware', 'investigation', 'scenario', 'tumbler', 'victim'] },
    { id: 'walkthroughs', title: 'Forensics Walkthroughs', category: 'Forensics', keywords: ['address', 'trace', 'scan', 'blocks', 'investigation', 'events', 'suspicious', 'money flow', 'walkthrough', 'example'] },
    { id: 'test-accounts', title: 'Test Accounts', category: 'Getting Started', keywords: ['accounts', 'addresses', 'private key', 'hardhat', 'default', '10000 ETH', 'shared'] },
];

const CLI_CATEGORIES = ['All', 'Getting Started', 'Smart Contracts', 'Forensics'];

function CLILabsView({ isInstructor = false, rpcUrl = '', terminalRpcUrl = '' }) {
    const [copiedCommand, setCopiedCommand] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeCategory, setActiveCategory] = useState('All');
    const [activeSection, setActiveSection] = useState(null);
    const [selectedLabId, setSelectedLabId] = useState(null);
    const sectionRefs = useRef({});
    const navRef = useRef(null);

    const selectedLab = selectedLabId ? getLabById(selectedLabId) : null;

    // Filter sections based on search query and category
    const filteredSections = CLI_SECTIONS.filter(section => {
        const matchesCategory = activeCategory === 'All' || section.category === activeCategory;
        if (!searchQuery.trim()) return matchesCategory;
        const q = searchQuery.toLowerCase();
        const matchesSearch = section.title.toLowerCase().includes(q) ||
            section.keywords.some(k => k.toLowerCase().includes(q)) ||
            section.category.toLowerCase().includes(q);
        return matchesSearch && matchesCategory;
    });

    const visibleIds = new Set(filteredSections.map(s => s.id));

    // Scroll to section
    const scrollToSection = (id) => {
        const el = sectionRefs.current[id];
        if (el) {
            const navHeight = navRef.current?.offsetHeight || 0;
            const top = el.getBoundingClientRect().top + window.scrollY - navHeight - 16;
            window.scrollTo({ top, behavior: 'smooth' });
        }
    };

    // IntersectionObserver for active section highlighting
    useEffect(() => {
        const observers = [];
        const ids = CLI_SECTIONS.map(s => s.id);
        ids.forEach(id => {
            const el = sectionRefs.current[id];
            if (!el) return;
            const observer = new IntersectionObserver(
                ([entry]) => {
                    if (entry.isIntersecting) setActiveSection(id);
                },
                { rootMargin: '-120px 0px -60% 0px', threshold: 0 }
            );
            observer.observe(el);
            observers.push(observer);
        });
        return () => observers.forEach(o => o.disconnect());
    }, []);

    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopiedCommand(id);
        setTimeout(() => setCopiedCommand(null), 2000);
    };

    const CodeBlock = ({ code, id, label }) => (
        <div style={{
            background: '#0f172a',
            borderRadius: '0.5rem',
            overflow: 'hidden',
            border: '1px solid #334155',
            marginBottom: '0.75rem'
        }}>
            {label && (
                <div style={{
                    padding: '0.5rem 1rem',
                    background: 'rgba(59, 130, 246, 0.1)',
                    borderBottom: '1px solid #334155',
                    color: '#93c5fd',
                    fontSize: '0.85rem',
                    fontWeight: '600'
                }}>
                    {label}
                </div>
            )}
            <div style={{display: 'flex', alignItems: 'stretch'}}>
                <pre style={{
                    flex: 1,
                    margin: 0,
                    padding: '1rem',
                    color: '#fbbf24',
                    fontFamily: "'Fira Code', 'Monaco', 'Consolas', monospace",
                    fontSize: '0.9rem',
                    lineHeight: '1.5',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap'
                }}>{code}</pre>
                <button
                    onClick={() => copyToClipboard(code, id)}
                    style={{
                        padding: '0.5rem 1rem',
                        background: copiedCommand === id ? '#22c55e' : '#334155',
                        border: 'none',
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                        transition: 'background 0.2s'
                    }}
                >
                    {copiedCommand === id ? '✓' : '📋'}
                </button>
            </div>
        </div>
    );

    // Lab detail view - full instructions from docs/**/*.md (identical content, user chooses GUI or MD)
    if (selectedLab) {
        const basePath = typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL ? import.meta.env.BASE_URL.replace(/\/$/, '') : '';
        return (
            <LabDetailView
                lab={selectedLab}
                onBack={() => setSelectedLabId(null)}
                basePath={basePath}
                studentOnly={!isInstructor}
            />
        );
    }

    const menuOptions = [
        { num: '1', label: 'Network info', desc: 'View blockchain connection status (chain ID, block number, gas price)' },
        { num: '2', label: 'Block details', desc: 'Explore block data, timestamps, and transactions within a block' },
        { num: '3', label: 'Account balances', desc: 'Check ETH balances for all test accounts at once' },
        { num: '4', label: 'Transaction lookup', desc: 'Find and analyze transactions by hash — see sender, recipient, value, gas' },
        { num: '5', label: 'Select account', desc: 'Switch between test accounts or import your own private key' },
        { num: '6', label: 'Send ETH', desc: 'Transfer ETH between accounts — practice real transaction mechanics' },
        { num: '7', label: 'Contract interaction', desc: 'Call PoS contract functions (stake, unstake, check rewards)' },
        { num: '8', label: 'Playground (Analyst Console)', desc: 'Interactive JavaScript console for freeform blockchain forensics', highlight: true },
        { num: '9', label: 'Contract Builder Lab', desc: 'Build, compile, and deploy smart contracts from 6 templates', highlight2: true },
        { num: '10', label: 'Account Manager', desc: 'Generate new wallets, import keys, fund student accounts' }
    ];

    return (
        <div style={{maxWidth: '900px', margin: '0 auto', padding: '2rem'}}>
            {/* Header */}
            <div style={{marginBottom: '0.5rem'}}>
                <h2 style={{color: '#f8fafc', margin: '0 0 0.5rem 0', fontSize: '1.8rem'}}>
                    🔍 Blockchain Forensics CLI
                </h2>
                <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                    Interactive tools for blockchain analysis and investigation
                </p>
                <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '1rem', flexWrap: 'wrap'}}>
                    <button
                        onClick={() => openLabTerminal(rpcUrl, terminalRpcUrl)}
                        style={{
                            padding: '0.5rem 1rem',
                            background: 'linear-gradient(135deg, #334155, #1e293b)',
                            border: '1px solid #475569',
                            borderRadius: '0.5rem',
                            color: '#e2e8f0',
                            fontSize: '0.9rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <span>🖥️</span>
                        <span>Open Lab Terminal</span>
                    </button>
                    <button
                        onClick={() => openLabTerminal(rpcUrl, terminalRpcUrl)}
                        style={{
                            padding: '0.35rem 0.65rem',
                            background: 'rgba(139, 92, 246, 0.15)',
                            border: '1px solid rgba(139, 92, 246, 0.35)',
                            borderRadius: '0.35rem',
                            color: '#c4b5fd',
                            fontSize: '0.8rem',
                            cursor: 'pointer'
                        }}
                    >
                        + Another
                    </button>
                    <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                        Run interactive.js, Contract Builder, labs — each opens a new terminal
                    </span>
                </div>
            </div>

            {/* ====== STICKY SEARCH + NAV BAR ====== */}
            <div ref={navRef} style={{
                position: 'sticky',
                top: 0,
                zIndex: 50,
                background: 'linear-gradient(180deg, #0f172a 85%, transparent)',
                paddingTop: '0.75rem',
                paddingBottom: '1rem',
                marginBottom: '1rem'
            }}>
                {/* Search Input */}
                <div style={{
                    display: 'flex',
                    gap: '0.5rem',
                    marginBottom: '0.75rem'
                }}>
                    <div style={{
                        flex: 1,
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center'
                    }}>
                        <span style={{
                            position: 'absolute', left: '0.75rem',
                            color: '#64748b', fontSize: '1rem', pointerEvents: 'none'
                        }}>&#128269;</span>
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            placeholder="Search guides... (e.g. deploy, compile, forensics, ABI)"
                            style={{
                                width: '100%',
                                padding: '0.6rem 2.25rem 0.6rem 2.25rem',
                                background: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '0.5rem',
                                color: '#f8fafc',
                                fontSize: '0.9rem',
                                outline: 'none'
                            }}
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                style={{
                                    position: 'absolute', right: '0.5rem',
                                    background: '#334155', border: 'none', borderRadius: '50%',
                                    width: '22px', height: '22px', color: '#94a3b8',
                                    cursor: 'pointer', fontSize: '0.75rem',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                                }}
                            >&times;</button>
                        )}
                    </div>
                </div>

                {/* Category Pills */}
                <div style={{
                    display: 'flex',
                    gap: '0.375rem',
                    flexWrap: 'wrap',
                    marginBottom: '0.6rem'
                }}>
                    {CLI_CATEGORIES.map(cat => (
                        <button
                            key={cat}
                            onClick={() => setActiveCategory(cat)}
                            style={{
                                padding: '0.3rem 0.75rem',
                                borderRadius: '999px',
                                border: activeCategory === cat ? 'none' : '1px solid #475569',
                                background: activeCategory === cat ? '#3b82f6' : '#334155',
                                color: activeCategory === cat ? 'white' : '#e2e8f0',
                                cursor: 'pointer',
                                fontSize: '0.8rem',
                                fontWeight: activeCategory === cat ? '600' : '500',
                                transition: 'all 0.15s'
                            }}
                        >{cat}</button>
                    ))}
                    {(searchQuery || activeCategory !== 'All') && (
                        <button
                            onClick={() => { setSearchQuery(''); setActiveCategory('All'); }}
                            style={{
                                padding: '0.3rem 0.75rem',
                                borderRadius: '999px',
                                border: '1px solid rgba(239, 68, 68, 0.4)',
                                background: 'rgba(239, 68, 68, 0.1)',
                                color: '#fca5a5',
                                cursor: 'pointer',
                                fontSize: '0.8rem',
                                marginLeft: '0.25rem'
                            }}
                        >Clear Filters</button>
                    )}
                </div>

                {/* TOC Jump Links */}
                <div style={{
                    display: 'flex',
                    gap: '0.25rem',
                    flexWrap: 'wrap',
                    overflowX: 'auto'
                }}>
                    {filteredSections.map(s => (
                        <button
                            key={s.id}
                            onClick={() => scrollToSection(s.id)}
                            style={{
                                padding: '0.2rem 0.6rem',
                                borderRadius: '0.375rem',
                                border: activeSection === s.id ? 'none' : '1px solid #475569',
                                background: activeSection === s.id ? 'rgba(59, 130, 246, 0.35)' : '#334155',
                                color: activeSection === s.id ? '#93c5fd' : '#cbd5e1',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                fontWeight: activeSection === s.id ? '600' : '500',
                                whiteSpace: 'nowrap',
                                transition: 'all 0.15s'
                            }}
                        >{s.title}</button>
                    ))}
                </div>
            </div>

            {/* No results message */}
            {filteredSections.length === 0 && (
                <div style={{
                    textAlign: 'center',
                    padding: '3rem 1.5rem',
                    color: '#94a3b8'
                }}>
                    <div style={{fontSize: '2.5rem', marginBottom: '1rem'}}>&#128270;</div>
                    <h3 style={{color: '#f8fafc', margin: '0 0 0.5rem 0'}}>No matching guides found</h3>
                    <p style={{margin: '0 0 1rem 0'}}>
                        No results for "<strong style={{color: '#fbbf24'}}>{searchQuery}</strong>"
                        {activeCategory !== 'All' && <> in <strong style={{color: '#93c5fd'}}>{activeCategory}</strong></>}
                    </p>
                    <button
                        onClick={() => { setSearchQuery(''); setActiveCategory('All'); }}
                        style={{
                            padding: '0.5rem 1.25rem',
                            background: '#3b82f6',
                            border: 'none',
                            borderRadius: '0.5rem',
                            color: 'white',
                            cursor: 'pointer',
                            fontSize: '0.9rem'
                        }}
                    >Show All Guides</button>
                </div>
            )}

            {/* Available Labs - Lab list from docs */}
            {visibleIds.has('available-labs') && (
            <div id="cli-available-labs" ref={el => sectionRefs.current['available-labs'] = el}>
            <div style={{
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1))',
                border: '2px solid rgba(59, 130, 246, 0.4)',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem'
            }}>
                <h3 style={{color: '#93c5fd', margin: '0 0 0.5rem 0'}}>📚 Available Labs</h3>
                <p style={{color: '#94a3b8', margin: '0 0 1rem 0', fontSize: '0.95rem'}}>
                    Click a lab to see the full instructions. Content is identical to <code style={{color: '#fbbf24'}}>docs/**/*.md</code> — use the GUI or open the markdown file directly, whichever you prefer.
                </p>
                <div style={{display: 'grid', gap: '0.75rem'}}>
                    {LABS.map(lab => (
                        <button
                            key={lab.id}
                            onClick={() => setSelectedLabId(lab.id)}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                gap: '1rem',
                                padding: '1rem 1.25rem',
                                background: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '0.75rem',
                                color: '#f8fafc',
                                cursor: 'pointer',
                                textAlign: 'left',
                                transition: 'all 0.2s'
                            }}
                            onMouseOver={e => {
                                e.currentTarget.style.background = '#334155';
                                e.currentTarget.style.borderColor = '#475569';
                            }}
                            onMouseOut={e => {
                                e.currentTarget.style.background = '#1e293b';
                                e.currentTarget.style.borderColor = '#334155';
                            }}
                        >
                            <div style={{flex: 1}}>
                                <div style={{fontWeight: '600', marginBottom: '0.25rem', fontSize: '1rem'}}>{lab.title}</div>
                                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>{lab.description}</div>
                                <div style={{display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap'}}>
                                    <span style={{background: '#334155', padding: '0.15rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', color: '#94a3b8'}}>{lab.duration}</span>
                                    <span style={{background: '#334155', padding: '0.15rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', color: '#94a3b8'}}>{lab.difficulty}</span>
                                    <span style={{background: 'rgba(251, 191, 36, 0.2)', padding: '0.15rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', color: '#fbbf24'}}>
                                        {lab.terminalsNeeded} terminal{lab.terminalsNeeded > 1 ? 's' : ''}
                                    </span>
                                </div>
                            </div>
                            <span style={{color: '#64748b', fontSize: '1.25rem'}}>→</span>
                        </button>
                    ))}
                </div>
            </div>
            </div>)}

            {/* Initial Setup */}
            {visibleIds.has('initial-setup') && (
            <div id="cli-initial-setup" ref={el => sectionRefs.current['initial-setup'] = el}>
            <div style={{
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(59, 130, 246, 0.15))',
                border: '2px solid rgba(34, 197, 94, 0.4)',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem'
            }}>
                <h3 style={{color: '#86efac', margin: '0 0 1rem 0'}}>🚀 Initial Setup</h3>
                <p style={{color: '#94a3b8', margin: '0 0 1rem 0', fontSize: '0.9rem'}}>
                    {INITIAL_SETUP.description}
                </p>

                <div style={{display: 'grid', gap: '1rem'}}>
                    {INITIAL_SETUP.steps.map((s, i) => (
                        <div key={i} style={{marginBottom: i < INITIAL_SETUP.steps.length - 1 ? '0' : '0'}}>
                            <p style={{color: '#e2e8f0', margin: '0 0 0.5rem 0', fontWeight: '600'}}>
                                {i + 1}. {s.title}
                            </p>
                            <p style={{color: '#94a3b8', margin: '0 0 0.25rem 0', fontSize: '0.85rem'}}>{s.instruction}</p>
                            <CodeBlock code={s.code} id={`initial-setup-${i}`} />
                        </div>
                    ))}
                </div>

                <p style={{color: '#94a3b8', margin: '1rem 0 0 0', fontSize: '0.85rem'}}>
                    Multi-role labs need separate shells—use <strong>Open Lab Terminal</strong> in the header for an extra window. Pick labs from <strong>Available Labs</strong> or from the menu after <code style={{background: '#0f172a', padding: '2px 6px', borderRadius: '4px'}}>npm start</code>.
                </p>

                {/* Optional env for instructor-hosted chain */}
                <details style={{
                    background: '#0f172a',
                    borderRadius: '0.5rem',
                    padding: '0.75rem 1rem',
                    marginTop: '1rem',
                    border: '1px solid #334155'
                }}>
                    <summary style={{color: '#94a3b8', cursor: 'pointer', fontSize: '0.9rem'}}>Optional: RPC and contract env vars (instructor node)</summary>
                    <div style={{marginTop: '0.75rem'}}>
                        <CodeBlock code="cd scripts/cli-labs/standalone" id="cd-local" />
                        <CodeBlock code="npm install" id="npm-install" label="First time only" />
                        <CodeBlock 
                            code={`# Windows PowerShell:
$env:RPC_URL="http://INSTRUCTOR_IP:8545"
$env:CONTRACT_ADDRESS="0x..."

# Mac / Linux / Codespaces:
export RPC_URL="http://INSTRUCTOR_IP:8545"
export CONTRACT_ADDRESS="0x..."`} 
                            id="env"
                            label="Set environment variables (get values from instructor)"
                        />
                        <CodeBlock code="npm start" id="npm-start-local" />
                    </div>
                </details>
            </div>
            </div>)}

            {/* Menu Options */}
            {visibleIds.has('menu-options') && (
            <div id="cli-menu-options" ref={el => sectionRefs.current['menu-options'] = el}>
            <div style={{
                background: '#1e293b',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem',
                border: '1px solid #334155'
            }}>
                <h3 style={{color: '#f8fafc', margin: '0 0 1rem 0'}}>📋 Menu Options</h3>
                <p style={{color: '#94a3b8', margin: '0 0 1rem 0'}}>
                    After running <code style={{background: '#0f172a', padding: '2px 6px', borderRadius: '4px'}}>npm start</code>, 
                    you'll see this menu:
                </p>
                
                <div style={{display: 'grid', gap: '0.5rem'}}>
                    {menuOptions.map(opt => {
                        const isHighlighted = opt.highlight || opt.highlight2;
                        const accentColor = opt.highlight ? '#fbbf24' : opt.highlight2 ? '#a78bfa' : '#3b82f6';
                        const bgColor = opt.highlight ? 'rgba(251, 191, 36, 0.15)' : opt.highlight2 ? 'rgba(167, 139, 250, 0.15)' : 'rgba(15, 23, 42, 0.5)';
                        const borderColor = opt.highlight ? 'rgba(251, 191, 36, 0.4)' : opt.highlight2 ? 'rgba(167, 139, 250, 0.4)' : 'transparent';
                        return (
                        <div 
                            key={opt.num}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '1rem',
                                padding: '0.75rem 1rem',
                                background: bgColor,
                                borderRadius: '0.5rem',
                                border: `1px solid ${borderColor}`
                            }}
                        >
                            <span style={{
                                width: '32px',
                                height: '32px',
                                borderRadius: '50%',
                                background: accentColor,
                                color: isHighlighted ? '#0f172a' : 'white',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontWeight: 'bold',
                                fontSize: '0.85rem',
                                flexShrink: 0
                            }}>
                                {opt.num}
                            </span>
                            <div style={{flex: 1}}>
                                <div style={{color: isHighlighted ? accentColor : '#f8fafc', fontWeight: '600'}}>
                                    {opt.label}
                                </div>
                                <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>
                                    {opt.desc}
                                </div>
                            </div>
                            {opt.highlight && (
                                <span style={{
                                    background: '#fbbf24',
                                    color: '#0f172a',
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '999px',
                                    fontSize: '0.75rem',
                                    fontWeight: 'bold',
                                    flexShrink: 0
                                }}>
                                    FORENSICS
                                </span>
                            )}
                            {opt.highlight2 && (
                                <span style={{
                                    background: '#a78bfa',
                                    color: '#0f172a',
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '999px',
                                    fontSize: '0.75rem',
                                    fontWeight: 'bold',
                                    flexShrink: 0
                                }}>
                                    CONTRACTS
                                </span>
                            )}
                        </div>
                        );
                    })}
                </div>
            </div>
            </div>)}

            {/* Playground Section */}
            {visibleIds.has('playground') && (
            <div id="cli-playground" ref={el => sectionRefs.current['playground'] = el}>
            <div style={{
                background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.1))',
                border: '2px solid rgba(251, 191, 36, 0.4)',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem'
            }}>
                <h3 style={{color: '#fbbf24', margin: '0 0 1rem 0'}}>🎮 Playground Mode (Option 8)</h3>
                <p style={{color: '#e2e8f0', margin: '0 0 1rem 0'}}>
                    The Playground is an interactive JavaScript console designed for blockchain forensics. 
                    <strong> Variables persist between commands</strong> using the ctx object.
                </p>

                <div style={{
                    background: '#0f172a',
                    borderRadius: '0.5rem',
                    padding: '1rem',
                    marginBottom: '1rem',
                    fontFamily: "'Fira Code', monospace",
                    fontSize: '0.85rem'
                }}>
                    <div style={{color: '#22c55e', marginBottom: '0.5rem'}}>&gt; ctx.target = '0xf39F...'</div>
                    <div style={{color: '#22c55e', marginBottom: '0.5rem'}}>&gt; ctx.balance = await provider.getBalance(ctx.target)</div>
                    <div style={{color: '#22c55e', marginBottom: '0.5rem'}}>&gt; console.log(formatEth(ctx.balance), 'ETH')</div>
                    <div style={{color: '#94a3b8'}}>9998.5 ETH</div>
                </div>

                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem'}}>
                    <div style={{background: '#1e293b', padding: '0.75rem', borderRadius: '0.5rem'}}>
                        <div style={{color: '#93c5fd', fontWeight: '600', marginBottom: '0.25rem'}}>💡 help</div>
                        <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Show quick examples</div>
                    </div>
                    <div style={{background: '#1e293b', padding: '0.75rem', borderRadius: '0.5rem'}}>
                        <div style={{color: '#93c5fd', fontWeight: '600', marginBottom: '0.25rem'}}>💡 help forensics</div>
                        <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Address & transaction analysis</div>
                    </div>
                    <div style={{background: '#1e293b', padding: '0.75rem', borderRadius: '0.5rem'}}>
                        <div style={{color: '#93c5fd', fontWeight: '600', marginBottom: '0.25rem'}}>💡 help investigate</div>
                        <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Full investigation workflows</div>
                    </div>
                    <div style={{background: '#1e293b', padding: '0.75rem', borderRadius: '0.5rem'}}>
                        <div style={{color: '#93c5fd', fontWeight: '600', marginBottom: '0.25rem'}}>💡 vars</div>
                        <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Show stored variables</div>
                    </div>
                </div>
            </div>
            </div>)}

            {/* ====== DEPLOY & SHARE: Core Collaborative Workflow ====== */}
            {visibleIds.has('deploy-share') && (
            <div id="cli-deploy-share" ref={el => sectionRefs.current['deploy-share'] = el}>
            <div style={{
                background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(168, 85, 247, 0.12))',
                border: '2px solid rgba(14, 165, 233, 0.5)',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem'
            }}>
                <h3 style={{color: '#38bdf8', margin: '0 0 0.25rem 0', fontSize: '1.3rem'}}>
                    🤝 Deploy &amp; Share: Working with Contracts as a Team
                </h3>
                <p style={{color: '#e2e8f0', margin: '0 0 1.5rem 0'}}>
                    In this lab, one person <strong>deploys</strong> a smart contract and then <strong>shares the address</strong> with classmates so everyone can interact with the same contract on the shared blockchain.
                </p>

                {/* PART A: Deploy a Contract */}
                <div style={{
                    background: '#0f172a',
                    borderRadius: '0.75rem',
                    padding: '1.25rem',
                    marginBottom: '1.5rem',
                    border: '1px solid #334155'
                }}>
                    <h4 style={{color: '#38bdf8', margin: '0 0 0.75rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                        <span style={{
                            background: '#38bdf8', color: '#0f172a', width: '24px', height: '24px',
                            borderRadius: '50%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            fontWeight: 'bold', fontSize: '0.85rem'
                        }}>A</span>
                        Deploy a Smart Contract (the Creator)
                    </h4>
                    <p style={{color: '#94a3b8', margin: '0 0 1rem 0', fontSize: '0.9rem'}}>
                        Use the Contract Builder to pick a template, customize it, and deploy it to the blockchain.
                    </p>

                    <div style={{display: 'grid', gap: '0.75rem'}}>
                        {[
                            { step: '1', title: 'Launch the Contract Builder', detail: 'From the Interactive CLI, choose option 9, or run directly:', code: 'cd scripts/cli-labs/standalone\nnpm start\n# Then select option 9\n\n# Or run directly:\nnode 5-contract-builder.js' },
                            { step: '2', title: 'Pick a template and customize', detail: 'Choose from 6 templates (House Sale, Vehicle Title, Event Tickets, Voting, Crowdfunding, Classroom Vote). Fill in the custom fields or press Enter to use defaults.' },
                            { step: '3', title: 'Review, compile, and deploy', detail: 'The builder shows you the generated Solidity code, compiles it with Hardhat, and deploys it. When deployment succeeds, you\'ll see:' , code: '✅ Contract deployed!\n📍 Address: 0x5FbDB2315678afecb367f032d93F642f64180aa3\n📝 Transaction: 0xabc123...' },
                            { step: '4', title: 'Share the contract address with your classmates', detail: 'Copy the address (starts with 0x, 42 characters). Everyone on the same network can interact with your contract using this address. Also share the template type (e.g. "houseSale", "classroomVote") so they know the ABI.' }
                        ].map(s => (
                            <div key={s.step} style={{
                                background: 'rgba(30, 41, 59, 0.5)',
                                borderRadius: '0.5rem',
                                padding: '0.75rem 1rem',
                                borderLeft: '3px solid #38bdf8'
                            }}>
                                <div style={{display: 'flex', gap: '0.5rem', alignItems: 'baseline', marginBottom: '0.25rem'}}>
                                    <span style={{color: '#38bdf8', fontWeight: 'bold'}}>Step {s.step}:</span>
                                    <span style={{color: '#e2e8f0', fontWeight: '600'}}>{s.title}</span>
                                </div>
                                <p style={{color: '#94a3b8', margin: '0.25rem 0 0 0', fontSize: '0.85rem'}}>{s.detail}</p>
                                {s.code && (
                                    <pre style={{
                                        background: '#020617', borderRadius: '0.375rem', padding: '0.75rem',
                                        margin: '0.5rem 0 0 0', color: '#fbbf24',
                                        fontFamily: "'Fira Code', monospace", fontSize: '0.85rem',
                                        overflow: 'auto', whiteSpace: 'pre-wrap'
                                    }}>{s.code}</pre>
                                )}
                            </div>
                        ))}
                    </div>

                    <div style={{
                        background: 'rgba(251, 191, 36, 0.1)',
                        border: '1px solid rgba(251, 191, 36, 0.3)',
                        borderRadius: '0.5rem',
                        padding: '0.75rem 1rem',
                        marginTop: '1rem'
                    }}>
                        <p style={{color: '#fcd34d', margin: 0, fontSize: '0.85rem'}}>
                            <strong>After deploying</strong>, you can immediately interact with your contract through the builder's interactive menu. 
                            It will list all available functions (labeled <span style={{color: '#86efac'}}>[view]</span>, <span style={{color: '#60a5fa'}}>[write]</span>, or <span style={{color: '#fcd34d'}}>[payable]</span>) 
                            and prompt you for any required parameters.
                        </p>
                    </div>
                </div>

                {/* PART B: Connect to Someone Else's Contract */}
                <div style={{
                    background: '#0f172a',
                    borderRadius: '0.75rem',
                    padding: '1.25rem',
                    border: '1px solid #334155'
                }}>
                    <h4 style={{color: '#a78bfa', margin: '0 0 0.75rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                        <span style={{
                            background: '#a78bfa', color: '#0f172a', width: '24px', height: '24px',
                            borderRadius: '50%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            fontWeight: 'bold', fontSize: '0.85rem'
                        }}>B</span>
                        Connect to a Classmate's Contract (Everyone Else)
                    </h4>
                    <p style={{color: '#94a3b8', margin: '0 0 0.5rem 0', fontSize: '0.9rem'}}>
                        <strong>What you need from the person who deployed:</strong>
                    </p>
                    <div style={{display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem'}}>
                        <span style={{background: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem', padding: '0.5rem 0.75rem', color: '#e2e8f0', fontSize: '0.85rem'}}>
                            <strong style={{color: '#38bdf8'}}>1.</strong> Contract Address <span style={{color: '#94a3b8'}}>(0x...)</span>
                        </span>
                        <span style={{background: '#1e293b', border: '1px solid #475569', borderRadius: '0.5rem', padding: '0.5rem 0.75rem', color: '#e2e8f0', fontSize: '0.85rem'}}>
                            <strong style={{color: '#38bdf8'}}>2.</strong> Template Type <span style={{color: '#94a3b8'}}>(e.g. "classroomVote", "houseSale")</span>
                        </span>
                    </div>

                    {/* Method 1: Playground (CLI) */}
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        borderRadius: '0.5rem',
                        padding: '1rem',
                        marginBottom: '0.75rem',
                        borderLeft: '3px solid #a78bfa'
                    }}>
                        <div style={{color: '#c4b5fd', fontWeight: '600', marginBottom: '0.5rem'}}>
                            Method 1: CLI Playground (Option 8) — Full Control
                        </div>
                        <p style={{color: '#94a3b8', margin: '0 0 0.5rem 0', fontSize: '0.85rem'}}>
                            Use the Playground's JavaScript console to connect to any contract. You can read state, call functions, and send transactions.
                        </p>
                        <pre style={{
                            background: '#020617', borderRadius: '0.375rem', padding: '0.75rem',
                            margin: '0 0 0.5rem 0', color: '#fbbf24',
                            fontFamily: "'Fira Code', monospace", fontSize: '0.85rem',
                            overflow: 'auto', whiteSpace: 'pre-wrap'
                        }}>{`// === Connect to a classmate's Classroom Vote contract ===
// ctx is provided by Playground; ensure it exists if running elsewhere:
if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};
const ctx = globalThis.ctx;

// Step 1: Define the ABI (what functions the contract has)
ctx.abi = [
  'function question() view returns (string)',
  'function optionA() view returns (string)',
  'function optionB() view returns (string)',
  'function votesForA() view returns (uint256)',
  'function votesForB() view returns (uint256)',
  'function votingOpen() view returns (bool)',
  'function vote(bool voteForA)',
  'function getResults() view returns (string, string, uint256, string, uint256, uint256, bool)'
]

// Step 2: Connect using the address your classmate shared
ctx.vote = new ethers.Contract('0xPASTE_ADDRESS_HERE', ctx.abi, wallet)

// Step 3: Read the current state
console.log('Question:', await ctx.vote.question())
console.log('Option A:', await ctx.vote.optionA())
console.log('Option B:', await ctx.vote.optionB())
console.log('Votes A:', (await ctx.vote.votesForA()).toString())
console.log('Votes B:', (await ctx.vote.votesForB()).toString())

// Step 4: Cast your vote! (true = Option A, false = Option B)
await ctx.vote.vote(true)
console.log('Vote cast!')`}</pre>
                        <div style={{
                            background: 'rgba(59, 130, 246, 0.1)',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            borderRadius: '0.375rem',
                            padding: '0.5rem 0.75rem'
                        }}>
                            <p style={{color: '#93c5fd', margin: 0, fontSize: '0.8rem'}}>
                                <strong>Note:</strong> Use <code style={{color: '#fbbf24'}}>provider</code> instead of <code style={{color: '#fbbf24'}}>wallet</code> in Step 2 if you only need to <em>read</em> data. 
                                Use <code style={{color: '#fbbf24'}}>wallet</code> when you need to <em>write</em> (send transactions like voting or staking).
                            </p>
                        </div>
                    </div>

                    {/* Method 2: Web Dashboard */}
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        borderRadius: '0.5rem',
                        padding: '1rem',
                        marginBottom: '0.75rem',
                        borderLeft: '3px solid #a78bfa'
                    }}>
                        <div style={{color: '#c4b5fd', fontWeight: '600', marginBottom: '0.5rem'}}>
                            Method 2: Web Dashboard — Visual Interface
                        </div>
                        <p style={{color: '#94a3b8', margin: '0 0 0.5rem 0', fontSize: '0.85rem'}}>
                            Open the standalone dashboard page in your browser. It provides a visual interface for viewing contract state.
                        </p>
                        <pre style={{
                            background: '#020617', borderRadius: '0.375rem', padding: '0.75rem',
                            margin: '0 0 0.5rem 0', color: '#fbbf24',
                            fontFamily: "'Fira Code', monospace", fontSize: '0.85rem',
                            overflow: 'auto', whiteSpace: 'pre-wrap'
                        }}>{`# Open in your browser:
http://localhost:5173/dashboard.html

# Or if using your instructor's URL:
http://INSTRUCTOR_IP:5173/dashboard.html`}</pre>
                        <p style={{color: '#94a3b8', margin: '0.5rem 0 0 0', fontSize: '0.85rem'}}>
                            On the dashboard page:
                        </p>
                        <ol style={{color: '#cbd5e1', margin: '0.25rem 0 0 0', paddingLeft: '1.5rem', fontSize: '0.85rem'}}>
                            <li>Enter the RPC URL (e.g. <code style={{color: '#fbbf24'}}>http://INSTRUCTOR_IP:8545</code>)</li>
                            <li>Click <strong>"Add Contract"</strong></li>
                            <li>Paste the <strong>contract address</strong> your classmate shared</li>
                            <li>Enter the <strong>template type</strong> (e.g. <code style={{color: '#fbbf24'}}>classroomVote</code>, <code style={{color: '#fbbf24'}}>houseSale</code>, <code style={{color: '#fbbf24'}}>voting</code>, <code style={{color: '#fbbf24'}}>crowdfunding</code>, <code style={{color: '#fbbf24'}}>vehicleTitle</code>, <code style={{color: '#fbbf24'}}>eventTickets</code>)</li>
                            <li>Give it a name and the dashboard will display its live state with auto-refresh</li>
                        </ol>
                    </div>

                    {/* ABI Reference */}
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        borderRadius: '0.5rem',
                        padding: '1rem',
                        borderLeft: '3px solid #a78bfa'
                    }}>
                        <div style={{color: '#c4b5fd', fontWeight: '600', marginBottom: '0.5rem'}}>
                            ABI Quick Reference (for the Playground)
                        </div>
                        <p style={{color: '#94a3b8', margin: '0 0 0.75rem 0', fontSize: '0.85rem'}}>
                            The ABI tells ethers.js what functions a contract has. Copy the one matching your classmate's template type:
                        </p>
                        <div style={{display: 'grid', gap: '0.5rem'}}>
                            {[
                                { label: '🎓 classroomVote', code: `if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};\nconst ctx = globalThis.ctx;\nctx.abi = ['function question() view returns (string)','function optionA() view returns (string)','function optionB() view returns (string)','function votesForA() view returns (uint256)','function votesForB() view returns (uint256)','function votingOpen() view returns (bool)','function vote(bool voteForA)','function openVoting()','function closeVoting()','function getResults() view returns (string, string, uint256, string, uint256, uint256, bool)']` },
                                { label: '🗳️ voting', code: `if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};\nconst ctx = globalThis.ctx;\nctx.abi = ['function votingTitle() view returns (string)','function votingClosed() view returns (bool)','function getTotalVotes() view returns (uint256)','function getAllResults() view returns (string[] memory, uint256[] memory)','function vote(uint256 optionIndex)','function closeVoting()','function extendDeadline(uint256 additionalDays)']` },
                                { label: '💸 crowdfunding', code: `if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};\nconst ctx = globalThis.ctx;\nctx.abi = ['function campaignName() view returns (string)','function goalAmount() view returns (uint256)','function totalRaised() view returns (uint256)','function goalReached() view returns (bool)','function contribute() payable','function claimRefund()','function creatorWithdraw()','function getCampaignStatus() view returns (string, uint256, uint256, uint256, uint256, bool, bool)']` },
                                { label: '🏠 houseSale', code: `if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};\nconst ctx = globalThis.ctx;\nctx.abi = ['function propertyAddress() view returns (string)','function salePrice() view returns (uint256)','function seller() view returns (address)','function buyer() view returns (address)','function currentState() view returns (uint8)','function payDeposit() payable','function passInspection()','function payBalance() payable','function confirmTransfer()','function cancelSale()']` },
                                { label: '🚗 vehicleTitle', code: `if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};\nconst ctx = globalThis.ctx;\nctx.abi = ['function vin() view returns (string)','function currentOwner() view returns (address)','function getVehicleInfo() view returns (string, string, string, uint256, address, uint8)','function transferOwnership(address newOwner)','function updateMileage(uint256 miles)','function updateTitleStatus(uint8 status)']` },
                                { label: '🎟️ eventTickets', code: `if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};\nconst ctx = globalThis.ctx;\nctx.abi = ['function eventName() view returns (string)','function ticketsSold() view returns (uint256)','function maxSupply() view returns (uint256)','function getEventInfo() view returns (string, string, uint256, uint256, uint256, bool)','function buyTicket() payable','function transferTicket(address to)','function checkIn(address attendee)','function cancelEvent()']` }
                            ].map(a => (
                                <details key={a.label} style={{
                                    background: '#020617',
                                    borderRadius: '0.375rem',
                                    border: '1px solid #1e293b'
                                }}>
                                    <summary style={{
                                        padding: '0.5rem 0.75rem',
                                        color: '#e2e8f0',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem',
                                        fontWeight: '600'
                                    }}>{a.label}</summary>
                                    <pre style={{
                                        padding: '0.5rem 0.75rem',
                                        margin: 0,
                                        color: '#fbbf24',
                                        fontFamily: "'Fira Code', monospace",
                                        fontSize: '0.8rem',
                                        overflow: 'auto',
                                        whiteSpace: 'pre-wrap',
                                        borderTop: '1px solid #1e293b'
                                    }}>{a.code}</pre>
                                </details>
                            ))}
                        </div>
                        <div style={{
                            background: 'rgba(59, 130, 246, 0.1)',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            borderRadius: '0.375rem',
                            padding: '0.5rem 0.75rem',
                            marginTop: '0.75rem'
                        }}>
                            <p style={{color: '#93c5fd', margin: 0, fontSize: '0.8rem'}}>
                                <strong>After pasting the ABI</strong>, connect with: <code style={{color: '#fbbf24'}}>ctx.c = new ethers.Contract('0xADDRESS', ctx.abi, wallet)</code><br/>
                                Then call functions: <code style={{color: '#fbbf24'}}>await ctx.c.functionName()</code>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            </div>)}

            {/* Individual Labs */}
            {visibleIds.has('individual-labs') && (
            <div id="cli-individual-labs" ref={el => sectionRefs.current['individual-labs'] = el}>
            <div style={{
                background: '#1e293b',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem',
                border: '1px solid #334155'
            }}>
                <h3 style={{color: '#f8fafc', margin: '0 0 0.5rem 0'}}>📚 Individual Lab Scripts</h3>
                <p style={{color: '#94a3b8', margin: '0 0 1.5rem 0'}}>
                    Each lab is a standalone guided exercise. Labs 4 and 5 are also in the Interactive CLI menu (option 8 and 9). Run from <code style={{color: '#fbbf24'}}>scripts/cli-labs/standalone</code> (see Initial Setup).
                </p>
                
                <div style={{display: 'grid', gap: '1.5rem'}}>
                    {/* Lab 1 */}
                    <div>
                        <CodeBlock code={`cd scripts/cli-labs/standalone
node 1-explore-blockchain.js`} id="lab1" label="Lab 1: Explore the Blockchain" />
                        <div style={{padding: '0 0.5rem', color: '#cbd5e1', fontSize: '0.9rem'}}>
                            <p style={{margin: '0.25rem 0 0.5rem 0'}}>
                                <strong>What you'll do:</strong> Connect to the blockchain and run your first queries — get the current block number, 
                                inspect block details (timestamp, miner, transactions), and check account balances.
                            </p>
                            <p style={{margin: 0, color: '#94a3b8', fontSize: '0.85rem'}}>
                                <strong>Key concepts:</strong> JSON-RPC connection, blocks, block height, accounts, wei vs ETH
                            </p>
                        </div>
                    </div>

                    {/* Lab 2 */}
                    <div>
                        <CodeBlock code={`cd scripts/cli-labs/standalone
node 2-sign-transaction.js`} id="lab2" label="Lab 2: Sign & Send Transactions" />
                        <div style={{padding: '0 0.5rem', color: '#cbd5e1', fontSize: '0.9rem'}}>
                            <p style={{margin: '0.25rem 0 0.5rem 0'}}>
                                <strong>What you'll do:</strong> Create a transaction from scratch, sign it with a private key, broadcast it to the network, 
                                and watch it get mined into a block. You'll see exactly how gas fees are calculated and deducted.
                            </p>
                            <p style={{margin: 0, color: '#94a3b8', fontSize: '0.85rem'}}>
                                <strong>Key concepts:</strong> Private key signing, nonce, gas limit, gas price, transaction lifecycle
                            </p>
                        </div>
                    </div>

                    {/* Lab 3 */}
                    <div>
                        <CodeBlock code={`cd scripts/cli-labs/standalone
node 3-interact-contract.js`} id="lab3" label="Lab 3: Interact with Smart Contracts" />
                        <div style={{padding: '0 0.5rem', color: '#cbd5e1', fontSize: '0.9rem'}}>
                            <p style={{margin: '0.25rem 0 0.5rem 0'}}>
                                <strong>What you'll do:</strong> Connect to the deployed PoS contract, read its state (total staked, your balance), 
                                send transactions to stake/unstake ETH, and listen for real-time events. Requires <code style={{color: '#fbbf24'}}>CONTRACT_ADDRESS</code> env variable.
                            </p>
                            <p style={{margin: 0, color: '#94a3b8', fontSize: '0.85rem'}}>
                                <strong>Key concepts:</strong> ABI, contract instance, read vs write calls, events, transaction receipts
                            </p>
                        </div>
                    </div>

                    {/* Lab 4 */}
                    <div>
                        <CodeBlock code={`cd scripts/cli-labs/standalone
node 4-forensics.js`} id="lab4" label="Lab 4: Blockchain Forensics" />
                        <div style={{padding: '0 0.5rem', color: '#cbd5e1', fontSize: '0.9rem'}}>
                            <p style={{margin: '0.25rem 0 0.5rem 0'}}>
                                <strong>What you'll do:</strong> Five guided forensics exercises — analyze addresses (EOA vs contract), trace transactions, 
                                scan blocks for patterns, query contract events, and generate investigation reports. Also available as Interactive CLI option 8.
                            </p>
                            <p style={{margin: 0, color: '#94a3b8', fontSize: '0.85rem'}}>
                                <strong>Key concepts:</strong> Address classification, receipt analysis, block scanning, event filtering, money flow tracking
                            </p>
                        </div>
                    </div>

                    {/* Lab 5 */}
                    <div>
                        <CodeBlock code={`cd scripts/cli-labs/standalone
node 5-contract-builder.js`} id="lab5" label="Lab 5: Smart Contract Builder" />
                        <div style={{padding: '0 0.5rem', color: '#cbd5e1', fontSize: '0.9rem'}}>
                            <p style={{margin: '0.25rem 0 0.5rem 0'}}>
                                <strong>What you'll do:</strong> Select from 6 real-world contract templates (house sale, vehicle title, event tickets, voting, 
                                crowdfunding, classroom voting), customize fields, compile with Hardhat, deploy to the blockchain, then interact with your contract. 
                                Also available as Interactive CLI option 9.
                            </p>
                            <p style={{margin: 0, color: '#94a3b8', fontSize: '0.85rem'}}>
                                <strong>Key concepts:</strong> Solidity, compilation, deployment, contract roles (admin/buyer/seller), view vs write functions
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            </div>)}

            {/* Forensics Labs (Ransomware Investigation) */}
            {visibleIds.has('forensics-labs') && (
            <div id="cli-forensics-labs" ref={el => sectionRefs.current['forensics-labs'] = el}>
            <div style={{
                background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.1))',
                border: '2px solid rgba(251, 191, 36, 0.4)',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem'
            }}>
                <h3 style={{color: '#fbbf24', margin: '0 0 0.5rem 0'}}>🔬 Forensics Labs: Ransomware Investigation</h3>
                <p style={{color: '#e2e8f0', margin: '0 0 1rem 0'}}>
                    Interactive labs where you trace simulated ransomware payments through tumbler networks. You need <strong>two terminals</strong>: one for the lab, one for the Hardhat console to investigate.
                </p>

                <div style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    borderRadius: '0.5rem',
                    padding: '0.75rem 1rem',
                    marginBottom: '1rem'
                }}>
                    <p style={{color: '#fca5a5', fontWeight: '600', margin: 0, fontSize: '0.9rem'}}>⚠️ Run forensics-setup.js first</p>
                    <p style={{color: '#94a3b8', margin: '0.25rem 0 0 0', fontSize: '0.85rem'}}>
                        Without setup, Technique 1 returns no results. Run <code style={{color: '#fbbf24'}}>node forensics-setup.js</code> (or <code style={{color: '#fbbf24'}}>forensics-setup-advanced.js</code>) after any blockchain reset.
                    </p>
                </div>

                <div style={{display: 'grid', gap: '1rem'}}>
                    <div style={{
                        background: '#1e293b',
                        borderRadius: '0.75rem',
                        padding: '1rem',
                        border: '1px solid #334155'
                    }}>
                        <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0', fontSize: '0.95rem'}}>Basic Ransomware Lab</h4>
                        <p style={{color: '#94a3b8', margin: '0 0 0.75rem 0', fontSize: '0.85rem'}}>
                            Trace a single victim's ransom through attacker wallet and tumblers to the final destination.
                        </p>
                        <CodeBlock code={`cd scripts/cli-labs/standalone
node forensics-setup.js           # Generate scenario first
node 6-ransomware-investigation.js`} id="forensics-basic" label="Terminal 1: Run the lab" />
                        <p style={{color: '#64748b', margin: '0.5rem 0 0 0', fontSize: '0.8rem'}}>
                            Terminal 2: <code style={{color: '#fbbf24'}}>npx hardhat console --network localhost</code> for investigation.
                        </p>
                    </div>

                    <div style={{
                        background: '#1e293b',
                        borderRadius: '0.75rem',
                        padding: '1rem',
                        border: '1px solid #334155'
                    }}>
                        <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0', fontSize: '0.95rem'}}>Advanced Ransomware Lab</h4>
                        <p style={{color: '#94a3b8', margin: '0 0 0.75rem 0', fontSize: '0.85rem'}}>
                            Multi-victim scenario with a coordinated attack and more complex tumbler network.
                        </p>
                        <CodeBlock code={`cd scripts/cli-labs/standalone
node forensics-setup-advanced.js   # Generate advanced scenario first
node 7-ransomware-advanced.js`} id="forensics-advanced" label="Terminal 1: Run the advanced lab" />
                    </div>
                </div>

                <p style={{color: '#94a3b8', margin: '1rem 0 0 0', fontSize: '0.85rem'}}>
                    Setup creates <code style={{color: '#fbbf24'}}>forensics-case.json</code> (student starting point) and <code style={{color: '#fbbf24'}}>.forensics-scenario.json</code> (answer key — keep private).
                </p>
            </div>
            </div>)}

            {/* Smart Contract Builder Guide */}
            {visibleIds.has('contract-builder') && (
            <div id="cli-contract-builder" ref={el => sectionRefs.current['contract-builder'] = el}>
            <div style={{
                background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.1), rgba(139, 92, 246, 0.1))',
                border: '2px solid rgba(167, 139, 250, 0.4)',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem'
            }}>
                <h3 style={{color: '#a78bfa', margin: '0 0 0.5rem 0'}}>🏗️ Smart Contract Builder (Option 9)</h3>
                <p style={{color: '#e2e8f0', margin: '0 0 1.25rem 0'}}>
                    Build and deploy real smart contracts from templates. Choose a use-case, customize fields, then compile and deploy to the live blockchain.
                </p>

                {/* Step-by-step workflow */}
                <div style={{
                    background: '#0f172a',
                    borderRadius: '0.75rem',
                    padding: '1.25rem',
                    marginBottom: '1.25rem',
                    border: '1px solid #334155'
                }}>
                    <h4 style={{color: '#c4b5fd', margin: '0 0 1rem 0', fontSize: '0.95rem'}}>Step-by-Step Workflow</h4>
                    <div style={{display: 'grid', gap: '0.75rem'}}>
                        {[
                            { step: '1', text: 'Select a template', detail: 'Choose from 6 real-world contract types (house sale, voting, tickets, etc.)' },
                            { step: '2', text: 'Customize fields', detail: 'Set names, prices, addresses, durations — or use defaults to get started quickly' },
                            { step: '3', text: 'Review the Solidity code', detail: 'See the generated .sol file with your custom values baked in' },
                            { step: '4', text: 'Compile with Hardhat', detail: 'The builder runs Hardhat compile automatically — look for "Compiled successfully"' },
                            { step: '5', text: 'Deploy to blockchain', detail: 'Your contract goes live! You\'ll get a contract address (save this!)' },
                            { step: '6', text: 'Interact via menu', detail: 'Call view functions (free) and write functions (cost gas) through the guided menu' }
                        ].map(s => (
                            <div key={s.step} style={{display: 'flex', gap: '0.75rem', alignItems: 'flex-start'}}>
                                <span style={{
                                    width: '26px', height: '26px', borderRadius: '50%',
                                    background: '#a78bfa', color: '#0f172a',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontWeight: 'bold', fontSize: '0.8rem', flexShrink: 0, marginTop: '2px'
                                }}>{s.step}</span>
                                <div>
                                    <div style={{color: '#e2e8f0', fontWeight: '600'}}>{s.text}</div>
                                    <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>{s.detail}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Contract Templates */}
                <h4 style={{color: '#c4b5fd', margin: '0 0 0.75rem 0', fontSize: '0.95rem'}}>Available Templates</h4>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem'}}>
                    {[
                        { icon: '🏠', name: 'House / Property Sale', desc: 'Real estate escrow with deposit, inspection period, and title transfer. Roles: Admin, Seller, Buyer.', fields: 'Address, price, deposit %, inspection days' },
                        { icon: '🚗', name: 'Vehicle Title Transfer', desc: 'Ownership registry with VIN tracking, title status (clean/salvage/rebuilt), and mileage history.', fields: 'VIN, make, model, year, owner' },
                        { icon: '🎟️', name: 'Event Tickets', desc: 'Limited-supply ticket sales with purchases, transfers, check-in verification, and refunds on cancellation.', fields: 'Event name, max supply, price, date' },
                        { icon: '🗳️', name: 'Voting System', desc: 'Multi-option voting with deadlines. Track votes, tally results, extend deadlines if needed.', fields: 'Title, options, duration, admin' },
                        { icon: '💸', name: 'Crowdfunding Campaign', desc: 'Fundraising with goal amounts and deadlines. Auto-refund if goal not met; creator withdraws when reached.', fields: 'Campaign name, goal, duration, min contribution' },
                        { icon: '🎓', name: 'Classroom Voting Demo', desc: 'Simple A/B voting. Deployer opens/closes voting; voters use wallets; dashboard shows live results.', fields: 'Question, Option A, Option B' }
                    ].map(t => (
                        <div key={t.name} style={{
                            background: '#1e293b',
                            borderRadius: '0.75rem',
                            padding: '1rem',
                            border: '1px solid #334155'
                        }}>
                            <div style={{fontSize: '1.5rem', marginBottom: '0.5rem'}}>{t.icon}</div>
                            <div style={{color: '#e2e8f0', fontWeight: '600', marginBottom: '0.25rem'}}>{t.name}</div>
                            <div style={{color: '#94a3b8', fontSize: '0.85rem', marginBottom: '0.5rem'}}>{t.desc}</div>
                            <div style={{color: '#818cf8', fontSize: '0.8rem'}}>
                                <strong>Customize:</strong> {t.fields}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            </div>)}

            {/* Expanded Playground Examples */}
            {visibleIds.has('walkthroughs') && (
            <div id="cli-walkthroughs" ref={el => sectionRefs.current['walkthroughs'] = el}>
            <div style={{
                background: '#1e293b',
                borderRadius: '1rem',
                padding: '1.5rem',
                marginBottom: '2rem',
                border: '1px solid #334155'
            }}>
                <h3 style={{color: '#f8fafc', margin: '0 0 0.5rem 0'}}>🔬 Playground Forensics Walkthroughs</h3>
                <p style={{color: '#94a3b8', margin: '0 0 1.25rem 0'}}>
                    Copy these complete workflows into the Playground (Option 8) to practice real forensics techniques.
                </p>

                {/* Walkthrough 1: Full Address Investigation */}
                <div style={{marginBottom: '1.25rem'}}>
                    <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0', fontSize: '0.95rem'}}>
                        Walkthrough 1: Full Address Investigation
                    </h4>
                    <p style={{color: '#94a3b8', fontSize: '0.85rem', margin: '0 0 0.75rem 0'}}>
                        Analyze an unknown address — determine its type, check balance, review activity, and check staking status.
                    </p>
                    <CodeBlock id="wt1" code={`// Step 1: Pick a target address (ctx is provided by Playground; ensure it exists if running elsewhere)
if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};
const ctx = globalThis.ctx;
ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'

// Step 2: Is it a wallet or a contract?
ctx.code = await provider.getCode(ctx.target)
console.log('Type:', ctx.code === '0x' ? 'Wallet (EOA)' : 'Smart Contract')

// Step 3: Check the balance
ctx.balance = await provider.getBalance(ctx.target)
console.log('Balance:', formatEth(ctx.balance), 'ETH')

// Step 4: How many transactions has it sent?
ctx.nonce = await provider.getTransactionCount(ctx.target)
console.log('Transactions sent:', ctx.nonce)

// Step 5: Check staking status (if contract is available)
ctx.stake = await contract.getStake(ctx.target)
console.log('Staked:', formatEth(ctx.stake), 'ETH')`} />
                </div>

                {/* Walkthrough 2: Trace a Transaction */}
                <div style={{marginBottom: '1.25rem'}}>
                    <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0', fontSize: '0.95rem'}}>
                        Walkthrough 2: Trace a Suspicious Transaction
                    </h4>
                    <p style={{color: '#94a3b8', fontSize: '0.85rem', margin: '0 0 0.75rem 0'}}>
                        Given a transaction hash, extract every detail — who sent it, where it went, how much gas was burned, and what events fired.
                    </p>
                    <CodeBlock id="wt2" code={`// Step 1: Get a recent transaction hash from a block
if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};
const ctx = globalThis.ctx;
ctx.block = await provider.getBlock('latest', true)
ctx.hash = ctx.block.prefetchedTransactions[0]?.hash
console.log('Investigating tx:', ctx.hash)

// Step 2: Pull the full transaction object
ctx.tx = await provider.getTransaction(ctx.hash)
console.log('From:', ctx.tx.from)
console.log('To:', ctx.tx.to)
console.log('Value:', formatEth(ctx.tx.value), 'ETH')
console.log('Gas limit:', ctx.tx.gasLimit.toString())

// Step 3: Get the execution receipt
ctx.receipt = await provider.getTransactionReceipt(ctx.hash)
console.log('Status:', ctx.receipt.status === 1 ? 'SUCCESS' : 'FAILED')
console.log('Gas used:', ctx.receipt.gasUsed.toString())
console.log('Events emitted:', ctx.receipt.logs.length)

// Step 4: Calculate the actual fee
ctx.fee = ctx.receipt.gasUsed * ctx.receipt.gasPrice
console.log('Fee paid:', formatEth(ctx.fee), 'ETH')`} />
                </div>

                {/* Walkthrough 3: Scan blocks for activity */}
                <div style={{marginBottom: '1.25rem'}}>
                    <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0', fontSize: '0.95rem'}}>
                        Walkthrough 3: Scan Recent Blocks for Activity
                    </h4>
                    <p style={{color: '#94a3b8', fontSize: '0.85rem', margin: '0 0 0.75rem 0'}}>
                        Scan the last 10 blocks, count transactions, find the most active block, and identify high-value transfers.
                    </p>
                    <CodeBlock id="wt3" code={`// Scan the last 10 blocks
if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};
const ctx = globalThis.ctx;
ctx.latest = await provider.getBlockNumber()
ctx.start = Math.max(0, ctx.latest - 10)
ctx.summary = []

for (let i = ctx.start; i <= ctx.latest; i++) {
  const b = await provider.getBlock(i, true)
  const txCount = b.prefetchedTransactions?.length || 0
  const totalValue = b.prefetchedTransactions?.reduce(
    (sum, tx) => sum + tx.value, 0n) || 0n
  ctx.summary.push({
    block: i,
    txs: txCount,
    totalETH: formatEth(totalValue),
    time: toDate(b.timestamp)
  })
}
console.table(ctx.summary)`} />
                </div>

                {/* Walkthrough 4: Contract interaction from Playground */}
                <div>
                    <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0', fontSize: '0.95rem'}}>
                        Walkthrough 4: Interact with a Deployed Contract
                    </h4>
                    <p style={{color: '#94a3b8', fontSize: '0.85rem', margin: '0 0 0.75rem 0'}}>
                        Connect to any deployed contract (including ones you built) from the Playground using its address and ABI.
                    </p>
                    <CodeBlock id="wt4" code={`// Connect to the PoS contract (already available as 'contract')
if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};
const ctx = globalThis.ctx;
ctx.totalStaked = await contract.totalStaked()
console.log('Network total staked:', formatEth(ctx.totalStaked), 'ETH')

// Query all staking events
ctx.events = await contract.queryFilter('Staked', 0)
console.log('Total staking events:', ctx.events.length)

// Show who staked and how much
ctx.events.forEach(e => {
  console.log(formatAddr(e.args[0]), 'staked', formatEth(e.args[1]), 'ETH')
})

// Connect to a CUSTOM contract (e.g. one you deployed):
// ctx.myContract = new ethers.Contract(
//   '0xYOUR_CONTRACT_ADDRESS',
//   ['function getTitle() view returns (string)', 
//    'function vote(uint option)'],
//   wallet
// )`} />
                </div>
            </div>
            </div>)}

            {/* Test Accounts */}
            {visibleIds.has('test-accounts') && (
            <div id="cli-test-accounts" ref={el => sectionRefs.current['test-accounts'] = el}>
            <div style={{
                background: '#1e293b',
                borderRadius: '1rem',
                padding: '1.5rem',
                border: '1px solid #334155'
            }}>
                <h3 style={{color: '#f8fafc', margin: '0 0 1rem 0'}}>👥 Test Accounts</h3>
                <p style={{color: '#94a3b8', margin: '0 0 1rem 0'}}>
                    All students share these test accounts (Hardhat defaults). Each starts with 10,000 ETH. You can also generate your own wallet using Account Manager (Option 10).
                </p>
                
                <div style={{
                    background: '#0f172a',
                    borderRadius: '0.5rem',
                    padding: '1rem',
                    fontFamily: "'Fira Code', monospace",
                    fontSize: '0.8rem',
                    overflow: 'auto'
                }}>
                    <div style={{display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1rem'}}>
                        <span style={{color: '#94a3b8'}}>Account 0:</span>
                        <span style={{color: '#fbbf24'}}>0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266</span>
                        <span style={{color: '#94a3b8'}}>Account 1:</span>
                        <span style={{color: '#fbbf24'}}>0x70997970C51812dc3A010C7d01b50e0d17dc79C8</span>
                        <span style={{color: '#94a3b8'}}>Account 2:</span>
                        <span style={{color: '#fbbf24'}}>0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC</span>
                        <span style={{color: '#94a3b8'}}>Account 3:</span>
                        <span style={{color: '#fbbf24'}}>0x90F79bf6EB2c4f870365E785982E1f101E93b906</span>
                        <span style={{color: '#94a3b8'}}>Account 4:</span>
                        <span style={{color: '#fbbf24'}}>0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65</span>
                    </div>
                </div>

                <div style={{
                    background: 'rgba(251, 191, 36, 0.08)',
                    border: '1px solid rgba(251, 191, 36, 0.2)',
                    borderRadius: '0.5rem',
                    padding: '0.75rem 1rem',
                    marginTop: '0.75rem'
                }}>
                    <p style={{color: '#fcd34d', margin: 0, fontSize: '0.85rem'}}>
                        <strong>Important:</strong> These are shared test accounts — everyone on the network can see and use them. 
                        For your own private wallet, use Account Manager (Option 10) to generate a new keypair. Never use test private keys on mainnet!
                    </p>
                </div>
            </div>
            </div>)}
        </div>
    );
}

// --- COMPONENT: EXPLORE VIEW ---
const EXPLORE_BEACON_IDS = [
    'eth-explore-staking',
    'eth-explore-validators',
    'eth-explore-slashing',
    'eth-explore-defi',
    'eth-explore-rewards',
    'eth-explore-attack-cost',
    'eth-explore-chain',
    'eth-explore-address',
];

function ExploreView({ missions, exploreProgress, setExploreProgress, onBack, onContinue, fireProgressBeacon }) {
    const [expandedMission, setExpandedMission] = useState(null);
    const [quizAnswers, setQuizAnswers] = useState({});

    const toggleMission = (idx) => {
        const opening = expandedMission !== idx;
        setExpandedMission(opening ? idx : null);
        if (opening && fireProgressBeacon && !missions[idx].quiz) {
            fireProgressBeacon(EXPLORE_BEACON_IDS[idx]);
        }
    };

    const handleQuizAnswer = (missionIdx, answerIdx) => {
        const mission = missions[missionIdx];
        if (!mission.quiz) return;

        const isCorrect = answerIdx === mission.quiz.correct;
        setQuizAnswers({ ...quizAnswers, [missionIdx]: { selected: answerIdx, correct: isCorrect } });

        if (isCorrect) {
            const next = [...exploreProgress];
            next[missionIdx] = true;
            setExploreProgress(next);
            if (fireProgressBeacon) fireProgressBeacon(EXPLORE_BEACON_IDS[missionIdx]);
        }
    };

    const completedCount = exploreProgress.filter(Boolean).length;
    const totalCount = missions.length;

    return (
        <div className="explore-view">
            <div className="explore-header">
                <h2>🛰 Deep Dive: Staking, Validators & DeFi</h2>
                <p style={{fontSize: '1.1rem', color: '#cbd5e1', marginBottom: '1rem'}}>
                    Explore advanced Ethereum concepts through interactive missions
                </p>
                <div style={{
                    background: 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.2))',
                    padding: '1rem',
                    borderRadius: '0.75rem',
                    marginTop: '1rem'
                }}>
                    <strong style={{fontSize: '1.2rem'}}>Progress: {completedCount}/{totalCount} missions completed</strong>
                </div>
            </div>

            <div style={{marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
                {missions.map((mission, idx) => {
                    const isExpanded = expandedMission === idx;
                    const isCompleted = exploreProgress[idx];
                    const quizState = quizAnswers[idx];

                    return (
                        <div 
                            key={idx}
                            style={{
                                background: isCompleted ? 'rgba(34,197,94,0.1)' : '#1e293b',
                                border: `2px solid ${isCompleted ? '#22c55e' : '#334155'}`,
                                borderRadius: '1rem',
                                overflow: 'hidden',
                                transition: 'all 0.3s'
                            }}
                        >
                            {/* Mission Header */}
                            <div 
                                onClick={() => toggleMission(idx)}
                                style={{
                                    padding: '1.5rem',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    background: isExpanded ? 'rgba(0,0,0,0.2)' : 'transparent'
                                }}
                            >
                                <div style={{flex: 1}}>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem'}}>
                                        <span style={{
                                            background: isCompleted ? '#22c55e' : '#64748b',
                                            color: 'white',
                                            width: '32px',
                                            height: '32px',
                                            borderRadius: '50%',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontWeight: 'bold'
                                        }}>
                                            {isCompleted ? '✓' : idx + 1}
                                        </span>
                                        <h3 style={{margin: 0, fontSize: '1.3rem', color: '#f8fafc'}}>{mission.title}</h3>
                                    </div>
                                    {mission.category && (
                                        <span style={{
                                            fontSize: '0.75rem',
                                            background: '#3b82f6',
                                            color: 'white',
                                            padding: '0.25rem 0.75rem',
                                            borderRadius: '999px',
                                            marginLeft: '48px'
                                        }}>
                                            {mission.category}
                                        </span>
                                    )}
                                    <p style={{margin: '0.75rem 0 0 48px', color: '#94a3b8'}}>{mission.action}</p>
                                </div>
                                <span style={{fontSize: '1.5rem', transition: 'transform 0.3s', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0)'}}>
                                    ▼
                                </span>
                            </div>

                            {/* Mission Content (Expanded) */}
                            {isExpanded && (
                                <div style={{
                                    padding: '1.5rem',
                                    background: '#0f172a',
                                    borderTop: '1px solid #334155',
                                    animation: 'fadein 0.3s',
                                    color: '#e2e8f0'
                                }}>
                                    {mission.miniLab && (
                                        <div style={{marginBottom: '2rem'}}>
                                            {mission.miniLab === 'blockchain-visualizer' && <BlockchainVisualizer />}
                                            {mission.miniLab === 'address-decoder' && <AddressDecoder />}
                                            {mission.miniLab === 'staking-rewards' && <StakingRewards />}
                                            {mission.miniLab === 'validator-probability' && <ValidatorProbability />}
                                            {mission.miniLab === 'slashing-penalty' && <SlashingPenalty />}
                                            {mission.miniLab === 'attack-cost' && <AttackCost />}
                                        </div>
                                    )}
                                    
                                    {/* VIDEO EMBED - Shows when video URL is provided */}
                                    {mission.video && (
                                        <div style={{
                                            marginBottom: '2rem',
                                            borderRadius: '0.75rem',
                                            overflow: 'hidden',
                                            background: '#0f172a',
                                            border: '2px solid #10b981'
                                        }}>
                                            <div style={{
                                                padding: '0.75rem 1rem',
                                                background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                                color: 'white',
                                                fontWeight: 'bold',
                                                fontSize: '0.9rem',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px'
                                            }}>
                                                🎬 Watch: {mission.title}
                                            </div>
                                            <div style={{position: 'relative', paddingBottom: '56.25%', height: 0}}>
                                                <iframe
                                                    src={mission.video}
                                                    title={`Video: ${mission.title}`}
                                                    style={{
                                                        position: 'absolute',
                                                        top: 0,
                                                        left: 0,
                                                        width: '100%',
                                                        height: '100%',
                                                        border: 'none'
                                                    }}
                                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                    allowFullScreen
                                                />
                                            </div>
                                        </div>
                                    )}
                                    
                                    {mission.details && (
                                        <ul style={{
                                            listStyle: 'none',
                                            padding: 0,
                                            margin: '0 0 1.5rem 0'
                                        }}>
                                            {mission.details.map((detail, dIdx) => (
                                                <li key={dIdx} style={{
                                                    padding: '0.75rem',
                                                    marginBottom: '0.5rem',
                                                    background: 'rgba(59,130,246,0.1)',
                                                    borderLeft: '3px solid #3b82f6',
                                                    borderRadius: '0.25rem',
                                                    color: '#e2e8f0',
                                                    fontSize: '1rem',
                                                    lineHeight: '1.6'
                                                }}>
                                                    💡 {detail}
                                                </li>
                                            ))}
                                        </ul>
                                    )}

                                    {mission.quiz && (
                                        <div style={{
                                            background: 'rgba(139,92,246,0.1)',
                                            padding: '1.5rem',
                                            borderRadius: '0.75rem',
                                            border: '1px solid rgba(139,92,246,0.3)'
                                        }}>
                                            <h4 style={{color: '#a78bfa', marginTop: 0}}>🎯 Quick Quiz</h4>
                                            <p style={{color: '#e2e8f0', fontSize: '1.05rem', fontWeight: 'bold', marginBottom: '1rem'}}>
                                                {mission.quiz.question}
                                            </p>
                                            <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
                                                {mission.quiz.options.map((option, oIdx) => {
                                                    const isSelected = quizState?.selected === oIdx;
                                                    const isCorrectAnswer = oIdx === mission.quiz.correct;
                                                    const showResult = quizState !== undefined;

                                                    let bgColor = '#1e293b';
                                                    let borderColor = '#475569';
                                                    let textColor = '#e2e8f0';

                                                    if (showResult) {
                                                        if (isCorrectAnswer) {
                                                            bgColor = 'rgba(34,197,94,0.2)';
                                                            borderColor = '#22c55e';
                                                            textColor = '#86efac';
                                                        } else if (isSelected && !isCorrectAnswer) {
                                                            bgColor = 'rgba(239,68,68,0.2)';
                                                            borderColor = '#ef4444';
                                                            textColor = '#fca5a5';
                                                        }
                                                    } else if (isSelected) {
                                                        bgColor = 'rgba(59,130,246,0.2)';
                                                        borderColor = '#3b82f6';
                                                    }

                                                    return (
                                                        <button
                                                            key={oIdx}
                                                            onClick={() => !quizState && handleQuizAnswer(idx, oIdx)}
                                                            disabled={quizState !== undefined}
                                                            style={{
                                                                padding: '1rem',
                                                                background: bgColor,
                                                                border: `2px solid ${borderColor}`,
                                                                borderRadius: '0.5rem',
                                                                color: textColor,
                                                                cursor: quizState ? 'default' : 'pointer',
                                                                textAlign: 'left',
                                                                fontSize: '1rem',
                                                                transition: 'all 0.2s',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                gap: '0.75rem'
                                                            }}
                                                        >
                                                            <span style={{
                                                                width: '24px',
                                                                height: '24px',
                                                                borderRadius: '50%',
                                                                background: 'rgba(255,255,255,0.1)',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                                fontWeight: 'bold'
                                                            }}>
                                                                {String.fromCharCode(65 + oIdx)}
                                                            </span>
                                                            {option}
                                                            {showResult && isCorrectAnswer && ' ✓'}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                            {quizState && (
                                                <div style={{marginTop: '1rem'}}>
                                                    <div style={{
                                                        padding: '1rem',
                                                        background: quizState.correct ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)',
                                                        borderRadius: quizState.correct && mission.quiz.explanation ? '0.5rem 0.5rem 0 0' : '0.5rem',
                                                        color: quizState.correct ? '#86efac' : '#fca5a5',
                                                        fontWeight: 'bold'
                                                    }}>
                                                        {quizState.correct ? '✅ Correct! Mission completed.' : '❌ Not quite. Try again!'}
                                                    </div>
                                                    {/* EXPLANATION - Shows after correct answer */}
                                                    {quizState.correct && mission.quiz.explanation && (
                                                        <div style={{
                                                            padding: '1rem 1.25rem',
                                                            background: 'rgba(59, 130, 246, 0.1)',
                                                            borderRadius: '0 0 0.5rem 0.5rem',
                                                            borderTop: '1px solid rgba(59, 130, 246, 0.3)',
                                                            borderLeft: '3px solid #3b82f6'
                                                        }}>
                                                            <div style={{
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                gap: '8px',
                                                                marginBottom: '0.5rem',
                                                                color: '#93c5fd',
                                                                fontSize: '0.85rem',
                                                                fontWeight: '600'
                                                            }}>
                                                                💡 Why This Matters
                                                            </div>
                                                            <p style={{
                                                                margin: 0,
                                                                color: '#cbd5e1',
                                                                fontSize: '0.95rem',
                                                                lineHeight: '1.6',
                                                                fontWeight: 'normal'
                                                            }}>
                                                                {mission.quiz.explanation}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {!mission.quiz && (
                                        <button
                                            onClick={() => {
                                                const next = [...exploreProgress];
                                                next[idx] = !next[idx];
                                                setExploreProgress(next);
                                            }}
                                            style={{
                                                marginTop: '1rem',
                                                padding: '0.75rem 1.5rem',
                                                background: isCompleted ? '#64748b' : '#22c55e',
                                                border: 'none',
                                                borderRadius: '0.5rem',
                                                color: 'white',
                                                fontWeight: 'bold',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            {isCompleted ? 'Mark Incomplete' : 'Mark Complete ✓'}
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="concept-actions" style={{marginTop: '2rem'}}>
                <button onClick={onBack}>← Back to Basics</button>
                <button
                    className="primary-btn"
                    onClick={onContinue}
                >
                    Continue to Practice →
                </button>
            </div>
        </div>
    );
}

// --- COMPONENT: COMPREHENSIVE PoS VALIDATOR SIMULATION ---
// Based on Ethereum PoS research synthesis covering: validator lifecycle, consensus mechanics,
// randomness beacons, network modeling, incentives, attack vectors, and metrics collection

// =============================================================================
// EDUCATIONAL STORY MODE: "The Trust Problem"
// A beginner-friendly guided journey that builds understanding step-by-step
// =============================================================================

function PoSValidatorSim({ onComplete }) {
    // === LEARNING MODE STATE ===
    const [learningMode, setLearningMode] = useState('story'); // 'story' = guided chapters, 'sandbox' = full simulator
    const [chapter, setChapter] = useState(1); // 1-7 chapters
    const [chapterStep, setChapterStep] = useState(0);
    const [userChoices, setUserChoices] = useState({});
    const [showReveal, setShowReveal] = useState(false);
    const [animationPhase, setAnimationPhase] = useState(0);
    const [earnedBadges, setEarnedBadges] = useState([]);
    
    // === SIMULATOR STATE ===
    const [activeModule, setActiveModule] = useState('overview'); // overview, selection, attestation, finality, attacks, economics, metrics
    const [validators, setValidators] = useState([
        { id: 1, name: "Alice", stake: 32, status: 'active', attestations: 0, missedAttestations: 0, blocksProposed: 0, rewards: 0, slashed: false, color: "#3b82f6", activationEpoch: 0, emoji: "👩‍💼", personality: "Always follows the rules" },
        { id: 2, name: "Bob", stake: 64, status: 'active', attestations: 0, missedAttestations: 0, blocksProposed: 0, rewards: 0, slashed: false, color: "#8b5cf6", activationEpoch: 0, emoji: "👨‍💻", personality: "Tech-savvy, big investor" },
        { id: 3, name: "Carol", stake: 16, status: 'active', attestations: 0, missedAttestations: 0, blocksProposed: 0, rewards: 0, slashed: false, color: "#ec4899", activationEpoch: 1, emoji: "👩‍🔬", personality: "Small but dedicated" },
        { id: 4, name: "Dave", stake: 128, status: 'active', attestations: 0, missedAttestations: 0, blocksProposed: 0, rewards: 0, slashed: false, color: "#10b981", activationEpoch: 0, emoji: "🐋", personality: "Wealthy, lots at stake" },
        { id: 5, name: "Mallory", stake: 32, status: 'active', attestations: 0, missedAttestations: 0, blocksProposed: 0, rewards: 0, slashed: false, color: "#ef4444", activationEpoch: 0, emoji: "😈", personality: "Looking for shortcuts..." }
    ]);
    
    // Simulation state
    const [epoch, setEpoch] = useState(0);
    const [slot, setSlot] = useState(0);
    const [isRunning, setIsRunning] = useState(false);
    const [simulationSpeed, setSimulationSpeed] = useState(1000);
    const [blocks, setBlocks] = useState([]);
    const [attestations, setAttestations] = useState([]);
    const [finalizedEpoch, setFinalizedEpoch] = useState(-1);
    const [justifiedEpoch, setJustifiedEpoch] = useState(-1);
    const [networkLatency, setNetworkLatency] = useState(100); // ms
    const [forkEvents, setForkEvents] = useState([]);
    const [selectedProposer, setSelectedProposer] = useState(null);
    const [randaoReveal, setRandaoReveal] = useState('0x' + Math.random().toString(16).slice(2, 18));
    
    // Attack simulation state
    const [attackMode, setAttackMode] = useState(null); // null, 'long-range', 'bouncing', 'censorship'
    const [attackLog, setAttackLog] = useState([]);
    
    // Interactive Slashing Scenario State
    const [slashingScenario, setSlashingScenario] = useState({
        active: false,
        step: 0, // 0: ready, 1: attacking, 2: detected, 3: slashed
        attacker: null,
        attackType: null,
        detectionProgress: 0,
        slashAmount: 0,
        eventLog: []
    });
    
    // Metrics
    const [metrics, setMetrics] = useState({
        avgFinalityLatency: 0,
        forkRate: 0,
        throughput: 0,
        totalRewards: 0,
        totalPenalties: 0,
        giniCoefficient: 0
    });
    
    const SLOTS_PER_EPOCH = 32;
    const totalStake = validators.filter(v => v.status === 'active' && !v.slashed).reduce((sum, v) => sum + v.stake, 0);
    
    // === CORE SIMULATOR FUNCTIONS ===
    
    // 1. Proposer Selection (RANDAO-weighted)
    const selectProposer = useCallback(() => {
        const activeValidators = validators.filter(v => v.status === 'active' && !v.slashed);
        if (activeValidators.length === 0) return null;
        
        // Calculate total stake of active validators
        const activeStake = activeValidators.reduce((sum, v) => sum + v.stake, 0);
        if (activeStake === 0) return null;
        
        // Generate fresh random value for RANDAO visualization
        const randBytes = new Uint32Array(4);
        crypto.getRandomValues(randBytes);
        const newRandao = '0x' + Array.from(randBytes).map(b => b.toString(16).padStart(8, '0')).join('');
        setRandaoReveal(newRandao);
        
        // Weighted random selection using Math.random() for reliability
        const rand = Math.random() * activeStake;
        let cumulative = 0;
        
        for (let v of activeValidators) {
            cumulative += v.stake;
            if (rand < cumulative) {
                return v;
            }
        }
        // Fallback (should never reach here)
        return activeValidators[activeValidators.length - 1];
    }, [validators]);
    
    // 2. Attestation Generation
    const generateAttestations = useCallback((blockSlot) => {
        const activeValidators = validators.filter(v => v.status === 'active' && !v.slashed);
        const attestingValidators = [];
        
        activeValidators.forEach(v => {
            // Simulate network delay affecting attestation timing
            const willAttest = Math.random() > (networkLatency / 10000);
            if (willAttest) {
                attestingValidators.push({
                    validatorId: v.id,
                    validatorName: v.name,
                    slot: blockSlot,
                    epoch: Math.floor(blockSlot / SLOTS_PER_EPOCH),
                    targetEpoch: Math.floor(blockSlot / SLOTS_PER_EPOCH),
                    sourceEpoch: justifiedEpoch,
                    timestamp: Date.now()
                });
            }
        });
        
        return attestingValidators;
    }, [validators, networkLatency, justifiedEpoch]);
    
    // 3. Fork Choice (LMD GHOST simplified)
    const evaluateForkChoice = useCallback(() => {
        // Simplified LMD GHOST: count attestations per block head
        const headVotes = {};
        attestations.forEach(att => {
            const key = `${att.slot}`;
            headVotes[key] = (headVotes[key] || 0) + 1;
        });
        return Object.entries(headVotes).sort((a, b) => b[1] - a[1])[0]?.[0] || slot;
    }, [attestations, slot]);
    
    // 4. Finality Check (Casper FFG simplified)
    const checkFinality = useCallback(() => {
        const currentEpoch = Math.floor(slot / SLOTS_PER_EPOCH);
        const epochAttestations = attestations.filter(a => a.epoch === currentEpoch - 1);
        const attestingStake = epochAttestations.reduce((sum, a) => {
            const validator = validators.find(v => v.id === a.validatorId);
            return sum + (validator?.stake || 0);
        }, 0);
        
        // 2/3 threshold for justification
        if (attestingStake >= (totalStake * 2 / 3)) {
            if (justifiedEpoch === currentEpoch - 2) {
                setFinalizedEpoch(currentEpoch - 2);
            }
            setJustifiedEpoch(currentEpoch - 1);
        }
    }, [slot, attestations, validators, totalStake, justifiedEpoch]);
    
    // 5. Reward/Penalty Calculation
    const calculateRewards = useCallback(() => {
        const baseReward = 0.0001; // ETH per attestation
        setValidators(prev => prev.map(v => {
            if (v.status !== 'active' || v.slashed) return v;
            
            const validatorAttestations = attestations.filter(a => a.validatorId === v.id);
            const newRewards = validatorAttestations.length * baseReward * (v.stake / 32);
            const missedPenalty = v.missedAttestations * baseReward * 0.5;
            
            return {
                ...v,
                rewards: v.rewards + newRewards - missedPenalty
            };
        }));
    }, [attestations]);
    
    // 6. Simulation Step
    const simulationStep = useCallback(() => {
        // Select proposer
        const proposer = selectProposer();
        setSelectedProposer(proposer);
        
        if (proposer) {
            // Create block
            const newBlock = {
                slot: slot,
                epoch: Math.floor(slot / SLOTS_PER_EPOCH),
                proposer: proposer.name,
                proposerId: proposer.id,
                timestamp: Date.now(),
                attestations: attestations.filter(a => a.slot === slot - 1).length
            };
            setBlocks(prev => [...prev.slice(-50), newBlock]);
            
            // Update proposer stats
            setValidators(prev => prev.map(v => 
                v.id === proposer.id 
                    ? { ...v, blocksProposed: v.blocksProposed + 1, rewards: v.rewards + 0.001 }
                    : v
            ));
            
            // Generate attestations for this slot
            const newAttestations = generateAttestations(slot);
            setAttestations(prev => [...prev.slice(-200), ...newAttestations]);
            
            // Update validator attestation counts
            setValidators(prev => prev.map(v => {
                const didAttest = newAttestations.some(a => a.validatorId === v.id);
                if (v.status === 'active' && !v.slashed) {
                    return {
                        ...v,
                        attestations: didAttest ? v.attestations + 1 : v.attestations,
                        missedAttestations: didAttest ? v.missedAttestations : v.missedAttestations + 1
                    };
                }
                return v;
            }));
        }
        
        // Check epoch boundary
        if ((slot + 1) % SLOTS_PER_EPOCH === 0) {
            checkFinality();
            calculateRewards();
            
            // Activate pending validators
            const newEpoch = Math.floor((slot + 1) / SLOTS_PER_EPOCH);
            setValidators(prev => prev.map(v => 
                v.status === 'pending' && v.activationEpoch <= newEpoch
                    ? { ...v, status: 'active' }
                    : v
            ));
            
            setEpoch(newEpoch);
        }
        
        setSlot(s => s + 1);
        
        // Update metrics
        setMetrics(prev => ({
            ...prev,
            throughput: blocks.length / Math.max(1, slot / SLOTS_PER_EPOCH),
            forkRate: forkEvents.length / Math.max(1, slot),
            totalRewards: validators.reduce((sum, v) => sum + v.rewards, 0),
            avgFinalityLatency: finalizedEpoch >= 0 ? (epoch - finalizedEpoch) * 2 : 0
        }));
    }, [slot, epoch, selectProposer, generateAttestations, checkFinality, calculateRewards, blocks, forkEvents, validators, attestations, finalizedEpoch]);
    
    // Auto-run simulation
    useEffect(() => {
        if (!isRunning) return;
        const timer = setInterval(simulationStep, simulationSpeed);
        return () => clearInterval(timer);
    }, [isRunning, simulationSpeed, simulationStep]);
    
    // Calculate Gini coefficient for stake distribution
    useEffect(() => {
        const stakes = validators.map(v => v.stake).sort((a, b) => a - b);
        const n = stakes.length;
        const sumOfDiffs = stakes.reduce((acc, stake, i) => 
            acc + stakes.slice(i + 1).reduce((sum, s) => sum + Math.abs(stake - s), 0), 0);
        const gini = sumOfDiffs / (n * n * (totalStake / n || 1));
        setMetrics(prev => ({ ...prev, giniCoefficient: gini }));
    }, [validators, totalStake]);
    
    // === INTERACTIVE SLASHING SCENARIO ===
    const runSlashingScenario = useCallback((attackerId, attackType) => {
        const attacker = validators.find(v => v.id === attackerId);
        if (!attacker || attacker.slashed) return;
        
        const SLASH_PENALTY_PERCENT = 5;
        const slashAmount = attacker.stake * (SLASH_PENALTY_PERCENT / 100);
        
        // Reset scenario
        setSlashingScenario({
            active: true,
            step: 0,
            attacker: attacker,
            attackType: attackType,
            detectionProgress: 0,
            slashAmount: slashAmount,
            eventLog: []
        });
        
        // Step 1: Attack begins (after 500ms)
        setTimeout(() => {
            setSlashingScenario(prev => ({
                ...prev,
                step: 1,
                eventLog: [...prev.eventLog, {
                    time: Date.now(),
                    type: 'attack',
                    message: `🚨 ${attacker.name} initiates ${attackType}!`,
                    details: attackType === 'double-sign' 
                        ? `Signing conflicting blocks at slot ${slot}: Block A (0x${Math.random().toString(16).slice(2,10)}) and Block B (0x${Math.random().toString(16).slice(2,10)})`
                        : attackType === 'surround-vote'
                        ? `Casting attestation that surrounds a previous vote: source=${justifiedEpoch-1}→target=${epoch+1} surrounds source=${justifiedEpoch}→target=${epoch}`
                        : `Going offline intentionally to harm network finality`
                }]
            }));
        }, 500);
        
        // Step 2: Detection (progressive from 1s to 3s)
        let progress = 0;
        const detectionInterval = setInterval(() => {
            progress += 10;
            setSlashingScenario(prev => ({
                ...prev,
                detectionProgress: progress,
                eventLog: progress === 50 ? [...prev.eventLog, {
                    time: Date.now(),
                    type: 'detection',
                    message: `🔍 Network nodes detecting anomaly...`,
                    details: `Other validators noticed conflicting signatures from ${attacker.name}`
                }] : prev.eventLog
            }));
            
            if (progress >= 100) {
                clearInterval(detectionInterval);
                
                // Step 3: Detection complete
                setSlashingScenario(prev => ({
                    ...prev,
                    step: 2,
                    eventLog: [...prev.eventLog, {
                        time: Date.now(),
                        type: 'detected',
                        message: `⚠️ VIOLATION CONFIRMED!`,
                        details: `Slashing condition met: ${attackType === 'double-sign' ? 'PROPOSER_SLASHING' : attackType === 'surround-vote' ? 'ATTESTER_SLASHING' : 'INACTIVITY_LEAK'} triggered`
                    }]
                }));
                
                // Step 4: Slash executed (after 1s more)
                setTimeout(() => {
                    // Actually slash the validator
                    setValidators(prev => prev.map(v => 
                        v.id === attackerId 
                            ? { 
                                ...v, 
                                slashed: true, 
                                stake: v.stake - slashAmount,
                                rewards: v.rewards - slashAmount,
                                status: 'slashed'
                            }
                            : v
                    ));
                    
                    setSlashingScenario(prev => ({
                        ...prev,
                        step: 3,
                        eventLog: [...prev.eventLog, {
                            time: Date.now(),
                            type: 'slashed',
                            message: `⚔️ ${attacker.name} SLASHED!`,
                            details: `Penalty: -${slashAmount.toFixed(2)} ETH (${SLASH_PENALTY_PERCENT}% of stake). Validator ejected from active set. Funds locked in withdrawal queue.`
                        }]
                    }));
                }, 1000);
            }
        }, 200);
        
    }, [validators, slot, epoch, justifiedEpoch]);
    
    const resetSlashingScenario = useCallback(() => {
        setSlashingScenario({
            active: false,
            step: 0,
            attacker: null,
            attackType: null,
            detectionProgress: 0,
            slashAmount: 0,
            eventLog: []
        });
    }, []);
    
    // === RENDER ===
    const moduleButtons = [
        { id: 'overview', label: '📊 Overview', desc: 'Simulator Dashboard' },
        { id: 'selection', label: '🎲 Selection', desc: 'Proposer Election' },
        { id: 'attestation', label: '✅ Attestation', desc: 'Voting & Finality' },
        { id: 'economics', label: '💰 Economics', desc: 'Rewards & Penalties' },
        { id: 'attacks', label: '⚔️ Attacks', desc: 'Security Scenarios' },
        { id: 'metrics', label: '📈 Metrics', desc: 'Performance Data' }
    ];
    
    // === STORY MODE CHAPTERS ===
    // Each chapter builds ONE concept through discovery, not lecture
    const CHAPTERS = {
        1: {
            title: "The Trust Problem",
            subtitle: "Why do we need this at all?",
            icon: "🤔"
        },
        2: {
            title: "Meet the Validators",
            subtitle: "Who keeps the network honest?",
            icon: "👥"
        },
        3: {
            title: "Skin in the Game",
            subtitle: "Why staking changes everything",
            icon: "💰"
        },
        4: {
            title: "Fair Selection",
            subtitle: "How validators are chosen",
            icon: "🎲"
        },
        5: {
            title: "Catching Cheaters",
            subtitle: "What happens when someone breaks the rules",
            icon: "⚔️"
        },
        6: {
            title: "Agreement",
            subtitle: "How everyone agrees on the truth",
            icon: "🤝"
        },
        7: {
            title: "Final Quiz",
            subtitle: "Test your knowledge",
            icon: "📝"
        },
        8: {
            title: "Scaling & Layer 2",
            subtitle: "How Ethereum scales with rollups",
            icon: "📈"
        },
        9: {
            title: "Graduation",
            subtitle: "You now understand Proof of Stake!",
            icon: "🎓"
        }
    };
    
    // === QUIZ STATE ===
    const [quizQuestions, setQuizQuestions] = useState([]);
    const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
    const [quizAnswers, setQuizAnswers] = useState({});
    const [quizSubmitted, setQuizSubmitted] = useState(false);
    const [quizScore, setQuizScore] = useState(0);
    
    // === QUIZ BANK - ALIGNED WITH COURSE CONTENT ===
    // Each question maps to specific chapter content to ensure fairness
    const QUIZ_BANK = [
        // === CHAPTER 1: THE TRUST PROBLEM (50 questions) ===
        // These questions test concepts from the "village ledger" analogy and why decentralization matters
        { id: 1, q: "What fundamental problem does blockchain solve?", a: ["Fast payments", "Trust without central authority", "Free transactions", "Anonymous browsing"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 2, q: "In traditional finance, who verifies that transactions are legitimate?", a: ["The sender", "The receiver", "Banks and financial institutions", "Nobody"], correct: 2, category: "Ch1: Trust", chapter: 1 },
        { id: 3, q: "What is the main drawback of relying on banks for trust?", a: ["They charge fees", "They can freeze accounts, make mistakes, or get hacked", "They're too slow", "They only work on weekdays"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 4, q: "In the village ledger thought experiment, how is truth established?", a: ["The chief decides", "Everyone keeps the same copy of the ledger", "The richest person decides", "Voting once per year"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 5, q: "What happens when two people in a decentralized system disagree about a transaction?", a: ["The richest person decides", "A central authority decides", "The network reaches consensus", "The transaction is cancelled"], correct: 2, category: "Ch1: Trust", chapter: 1 },
        { id: 6, q: "Why is 'trustless' considered a positive term in blockchain?", a: ["You don't need friends", "You don't need to trust any single entity", "Nobody can be trusted", "Trust is bad"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 7, q: "In the village ledger analogy, what problem does Mallory represent?", a: ["Slow transactions", "Someone trying to cheat the system", "High fees", "Technical errors"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 8, q: "What would happen if everyone kept their own ledger without coordination?", a: ["Perfect harmony", "Conflicting records and chaos", "Faster transactions", "Lower fees"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 9, q: "Which approach does Ethereum use to solve the trust problem?", a: ["Trust the government", "Voting + wealth-weighted + randomness + punishment", "Ask the user", "Single authority"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 10, q: "In the village ledger, what happens when Alice pays Bob?", a: ["Only Alice records it", "Only Bob records it", "Everyone in the village records it", "The bank records it"], correct: 2, category: "Ch1: Trust", chapter: 1 },
        { id: 11, q: "What is a 'single point of failure'?", a: ["A broken computer", "One entity whose failure breaks the whole system", "A software bug", "A network timeout"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 12, q: "Why do banks represent a single point of failure?", a: ["They're too big", "If they fail or act maliciously, your money is at risk", "They have too many employees", "They're open 24/7"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 13, q: "What is the core question Chapter 1 asks?", a: ["How fast is blockchain?", "How do we trust without a central authority?", "How much does it cost?", "Who invented Bitcoin?"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 14, q: "What does 'decentralized' mean in the context of blockchain?", a: ["One computer runs everything", "Many independent participants share control", "Government-controlled", "Only available in certain countries"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 15, q: "In the village ledger analogy, why does everyone need the same copy?", a: ["To save paper", "So no single person can lie about transactions", "It's cheaper", "Legal requirement"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 16, q: "What happens if Mallory tries to claim Alice paid her when she didn't?", a: ["It works", "Everyone else's ledger shows she's lying", "The bank investigates", "Nothing"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 17, q: "Why can't you trust a single company with all financial records?", a: ["They're too expensive", "They can make mistakes, get hacked, or act maliciously", "They're too slow", "They don't want to"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 18, q: "What is the key insight from the village ledger thought experiment?", a: ["Banks are bad", "Shared records prevent any single party from cheating", "Villages are better than cities", "Paper is better than digital"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 19, q: "According to Chapter 1, Ethereum combines which four ideas?", a: ["Speed, size, color, shape", "Voting, wealth-weighting, randomness, and punishment", "Banks, government, corporations, individuals", "Morning, noon, evening, night"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        { id: 20, q: "What does 'trustless' mean in blockchain?", a: ["Nobody can be trusted", "You don't need to trust any single entity to participate", "The system doesn't work", "Only criminals use it"], correct: 1, category: "Ch1: Trust", chapter: 1 },
        
        // === CATEGORY: VALIDATORS (Questions 26-75) ===
        { id: 26, q: "What is a validator in Ethereum?", a: ["A type of token", "A participant who verifies and proposes blocks", "A smart contract", "A wallet type"], correct: 1, category: "validators" },
        { id: 27, q: "How many validators are currently on Ethereum mainnet (approximately)?", a: ["About 100", "About 8,000", "About 500,000+", "About 10 million"], correct: 2, category: "validators" },
        { id: 28, q: "What is the minimum ETH required to become a solo validator?", a: ["1 ETH", "16 ETH", "32 ETH", "100 ETH"], correct: 2, category: "validators" },
        { id: 29, q: "What do validators receive in exchange for honest work?", a: ["NFTs", "Block rewards and transaction fees", "Governance tokens", "Nothing"], correct: 1, category: "validators" },
        { id: 30, q: "What is a validator's 'attestation'?", a: ["A certificate", "A vote confirming a block is valid", "A signature", "A deposit"], correct: 1, category: "validators" },
        { id: 31, q: "How often must validators attest?", a: ["Once per day", "Every epoch (approximately every 6.4 minutes)", "Once per year", "Whenever they want"], correct: 1, category: "validators" },
        { id: 32, q: "What happens if a validator misses their attestation duty?", a: ["Nothing", "A small penalty is applied", "Immediate slashing", "Account deletion"], correct: 1, category: "validators" },
        { id: 33, q: "What's the difference between a validator and a miner?", a: ["Nothing", "Validators stake ETH; miners use computing power", "Miners are newer", "Validators are older"], correct: 1, category: "validators" },
        { id: 34, q: "Can one person run multiple validators?", a: ["No, strictly one per person", "Yes, with separate 32 ETH stakes each", "Only up to 3", "Only corporations can"], correct: 1, category: "validators" },
        { id: 35, q: "What is a 'staking pool'?", a: ["A swimming pool", "A group pooling ETH to run validators together", "A trading platform", "A lending service"], correct: 1, category: "validators" },
        { id: 36, q: "Why would someone use a staking pool instead of solo staking?", a: ["Higher rewards", "Less than 32 ETH required, less technical knowledge needed", "Faster unstaking", "No penalties"], correct: 1, category: "validators" },
        { id: 37, q: "What is Lido in the context of staking?", a: ["A beach", "A popular liquid staking protocol", "A hardware wallet", "An exchange"], correct: 1, category: "validators" },
        { id: 38, q: "What is 'liquid staking'?", a: ["Staking while swimming", "Receiving tradeable tokens representing staked ETH", "Fast staking", "Emergency staking"], correct: 1, category: "validators" },
        { id: 39, q: "What do you receive when staking through Lido?", a: ["LIDO tokens", "stETH (staked ETH tokens)", "Nothing", "Governance votes"], correct: 1, category: "validators" },
        { id: 40, q: "What hardware is needed to run a validator?", a: ["Specialized ASICs", "A regular computer with good internet", "Supercomputer", "Quantum computer"], correct: 1, category: "validators" },
        { id: 41, q: "What is the 'beacon chain'?", a: ["A navigation tool", "The consensus layer coordinating validators", "A sidechain", "A bridge"], correct: 1, category: "validators" },
        { id: 42, q: "When did Ethereum transition to Proof of Stake?", a: ["2015", "2020", "September 2022 (The Merge)", "2025"], correct: 2, category: "validators" },
        { id: 43, q: "What was 'The Merge'?", a: ["Company merger", "Transition from PoW to PoS", "Chain split", "Hard fork"], correct: 1, category: "validators" },
        { id: 44, q: "What happens during a 'validator exit'?", a: ["The validator quits immediately", "A queue process to withdraw stake", "Funds are burned", "Account is deleted"], correct: 1, category: "validators" },
        { id: 45, q: "Why is there an exit queue for validators?", a: ["To annoy users", "To maintain network stability", "Legal requirement", "Technical limitation"], correct: 1, category: "validators" },
        { id: 46, q: "What is 'validator effective balance'?", a: ["Total ETH owned", "The balance counted for rewards (max 32 ETH)", "Pending balance", "Borrowed balance"], correct: 1, category: "validators" },
        { id: 47, q: "Why is effective balance capped at 32 ETH?", a: ["Arbitrary rule", "To encourage decentralization", "Technical limitation", "Legal requirement"], correct: 1, category: "validators" },
        { id: 48, q: "What is a 'validator index'?", a: ["A rating", "A unique ID number for each validator", "A score", "A ranking"], correct: 1, category: "validators" },
        { id: 49, q: "Can validators communicate directly with each other?", a: ["Yes, through email", "Yes, through the P2P gossip network", "No, never", "Only through Ethereum Foundation"], correct: 1, category: "validators" },
        { id: 50, q: "What is 'validator client' software?", a: ["A customer", "Software that runs validator operations", "A web browser", "A mobile app"], correct: 1, category: "validators" },
        
        // === CATEGORY: STAKING ECONOMICS (Questions 51-100) ===
        { id: 51, q: "What is 'stake' in Proof of Stake?", a: ["A wooden post", "ETH locked as collateral", "A type of meat", "A game"], correct: 1, category: "economics" },
        { id: 52, q: "Why must validators lock up ETH?", a: ["To prove they're rich", "To create economic incentive for honest behavior", "Tax purposes", "Tradition"], correct: 1, category: "economics" },
        { id: 53, q: "What is the approximate APY for ETH staking?", a: ["0.1%", "3-5%", "50%", "100%"], correct: 1, category: "economics" },
        { id: 54, q: "Why does staking APY vary?", a: ["Random", "It depends on total ETH staked network-wide", "Exchange manipulation", "Government regulation"], correct: 1, category: "economics" },
        { id: 55, q: "If more people stake, what happens to individual rewards?", a: ["They increase", "They decrease (dilution)", "They stay the same", "They become random"], correct: 1, category: "economics" },
        { id: 56, q: "What is 'issuance' in Ethereum?", a: ["Printing newspapers", "New ETH created as block rewards", "Token burning", "Transaction fees"], correct: 1, category: "economics" },
        { id: 57, q: "How did The Merge affect Ethereum's energy consumption?", a: ["Increased 10x", "Decreased ~99.95%", "No change", "Increased slightly"], correct: 1, category: "economics" },
        { id: 58, q: "What is EIP-1559?", a: ["A phone model", "Fee market change that burns base fees", "A validator rule", "A staking pool"], correct: 1, category: "economics" },
        { id: 59, q: "What does 'ultrasound money' refer to?", a: ["Sound effects", "ETH potentially becoming deflationary", "A podcast", "Audio NFTs"], correct: 1, category: "economics" },
        { id: 60, q: "When is ETH deflationary?", a: ["Always", "When burn rate exceeds issuance rate", "Never", "Only on weekends"], correct: 1, category: "economics" },
        { id: 61, q: "What is the 'base fee' in Ethereum transactions?", a: ["Fixed cost", "Dynamic fee that gets burned", "Optional tip", "Gas limit"], correct: 1, category: "economics" },
        { id: 62, q: "What is the 'priority fee' (tip)?", a: ["Mandatory fee", "Optional payment to validators for faster inclusion", "Burned fee", "Network fee"], correct: 1, category: "economics" },
        { id: 63, q: "Where do validator tips go?", a: ["Ethereum Foundation", "Directly to the block proposer", "Burned", "Staking pools"], correct: 1, category: "economics" },
        { id: 64, q: "What is MEV (Maximal Extractable Value)?", a: ["A token", "Extra profit from transaction ordering", "A staking method", "A wallet type"], correct: 1, category: "economics" },
        { id: 65, q: "How can validators extract MEV?", a: ["Hacking", "Reordering, inserting, or censoring transactions", "Printing money", "Voting"], correct: 1, category: "economics" },
        { id: 66, q: "Is MEV extraction considered ethical?", a: ["Always ethical", "Controversial - some forms harm users", "Always unethical", "Not relevant"], correct: 1, category: "economics" },
        { id: 67, q: "What is a 'block builder' in PBS (Proposer-Builder Separation)?", a: ["Construction worker", "Entity that assembles transaction bundles", "Validator type", "Developer"], correct: 1, category: "economics" },
        { id: 68, q: "Why was PBS introduced?", a: ["To increase fees", "To democratize MEV and reduce centralization", "To slow down blocks", "Legal compliance"], correct: 1, category: "economics" },
        { id: 69, q: "What is 'validator effective stake'?", a: ["Total holdings", "The stake amount counted for protocol purposes", "Pending stake", "Delegated stake"], correct: 1, category: "economics" },
        { id: 70, q: "What happens to rewards if a validator goes offline briefly?", a: ["Full slashing", "Small inactivity penalty", "Reward bonus", "Nothing"], correct: 1, category: "economics" },
        { id: 71, q: "What is the 'inactivity leak'?", a: ["Data breach", "Accelerated penalties during finality failure", "Memory leak", "Gas leak"], correct: 1, category: "economics" },
        { id: 72, q: "When does the inactivity leak activate?", a: ["Every block", "When the chain fails to finalize for >4 epochs", "Never", "Daily"], correct: 1, category: "economics" },
        { id: 73, q: "What's the purpose of the inactivity leak?", a: ["Punishment", "To restore finality by reducing inactive stake", "Revenue generation", "Testing"], correct: 1, category: "economics" },
        { id: 74, q: "How long is the unbonding period for validators?", a: ["Instant", "About 27 hours minimum (256 epochs)", "1 year", "Forever"], correct: 1, category: "economics" },
        { id: 75, q: "Why is there an unbonding period?", a: ["To annoy users", "Security - ensures accountability for past actions", "Technical limitation", "Tradition"], correct: 1, category: "economics" },
        
        // === CATEGORY: VALIDATOR SELECTION (Questions 76-125) ===
        { id: 76, q: "How is a block proposer selected in Ethereum PoS?", a: ["First come first serve", "Weighted random selection based on stake", "Highest stake always wins", "Alphabetical order"], correct: 1, category: "selection" },
        { id: 77, q: "What is RANDAO?", a: ["A company", "Randomness beacon using validator reveals", "A token", "A wallet"], correct: 1, category: "selection" },
        { id: 78, q: "Why is randomness important in validator selection?", a: ["Entertainment", "Prevents manipulation and ensures fairness", "Faster processing", "Lower fees"], correct: 1, category: "selection" },
        { id: 79, q: "Can a validator predict when they'll be selected?", a: ["Yes, exactly", "Partially - they know their slot assignment one epoch ahead", "Never", "Always"], correct: 1, category: "selection" },
        { id: 80, q: "What is a 'slot' in Ethereum?", a: ["A casino game", "A 12-second window for block production", "A validator type", "A transaction"], correct: 1, category: "selection" },
        { id: 81, q: "What is an 'epoch'?", a: ["A time period", "32 slots (~6.4 minutes)", "A validator group", "A block type"], correct: 1, category: "selection" },
        { id: 82, q: "How many slots are in one epoch?", a: ["10", "32", "100", "256"], correct: 1, category: "selection" },
        { id: 83, q: "What is a 'committee' in Ethereum PoS?", a: ["A board meeting", "A group of validators assigned to attest to a slot", "A staking pool", "A governance body"], correct: 1, category: "selection" },
        { id: 84, q: "How are validators assigned to committees?", a: ["They choose", "Pseudo-random shuffling each epoch", "First come first serve", "Alphabetically"], correct: 1, category: "selection" },
        { id: 85, q: "What is the 'beacon block root'?", a: ["A plant", "Hash linking to the beacon chain state", "A validator ID", "A transaction"], correct: 1, category: "selection" },
        { id: 86, q: "If Alice has 64 ETH staked (2 validators) and Bob has 32 ETH (1 validator), what's Alice's relative selection probability?", a: ["Same as Bob", "Twice as likely as Bob", "Three times as likely", "Half as likely"], correct: 1, category: "selection" },
        { id: 87, q: "What prevents a wealthy attacker from controlling validator selection?", a: ["Nothing", "Randomness combined with economic penalties", "Government oversight", "Community voting"], correct: 1, category: "selection" },
        { id: 88, q: "What is 'grinding' in the context of RANDAO?", a: ["Coffee preparation", "Attempting to manipulate randomness by skipping blocks", "Mining", "Staking"], correct: 1, category: "selection" },
        { id: 89, q: "Why is RANDAO grinding costly?", a: ["High fees", "Proposer forfeits block reward when skipping", "Legal penalties", "Community shame"], correct: 1, category: "selection" },
        { id: 90, q: "What is VDF (Verifiable Delay Function)?", a: ["A formula", "Future randomness improvement requiring time to compute", "A token", "A validator type"], correct: 1, category: "selection" },
        { id: 91, q: "What is 'single secret leader election' (SSLE)?", a: ["A voting method", "Hiding proposer identity until block publication", "A staking pool", "A governance method"], correct: 1, category: "selection" },
        { id: 92, q: "Why would SSLE be beneficial?", a: ["Faster blocks", "Prevents targeted DoS attacks on proposers", "Higher rewards", "Lower stake requirement"], correct: 1, category: "selection" },
        { id: 93, q: "What happens if the selected proposer is offline?", a: ["Chain halts", "The slot is skipped, next proposer continues", "Emergency election", "Backup proposer"], correct: 1, category: "selection" },
        { id: 94, q: "How does stake weight affect attestation duties?", a: ["No effect", "Higher stake = more attestation assignments", "Lower stake = more duties", "Random"], correct: 1, category: "selection" },
        { id: 95, q: "What is 'sync committee' duty?", a: ["Tech support", "Special validator group helping light clients", "Debugging", "Testing"], correct: 1, category: "selection" },
        { id: 96, q: "How often are sync committees rotated?", a: ["Every block", "Every ~27 hours (256 epochs)", "Never", "Daily"], correct: 1, category: "selection" },
        { id: 97, q: "What rewards do sync committee members receive?", a: ["Nothing extra", "Higher rewards for the duty period", "Lower rewards", "Negative rewards"], correct: 1, category: "selection" },
        { id: 98, q: "Can the same validator be on multiple committees simultaneously?", a: ["Never", "Yes, potentially", "Only if staking 64+ ETH", "Only institutions"], correct: 1, category: "selection" },
        { id: 99, q: "What is 'proposer boost'?", a: ["Energy drink", "Extra weight given to timely block proposals in fork choice", "Faster hardware", "Higher stake"], correct: 1, category: "selection" },
        { id: 100, q: "Why was proposer boost introduced?", a: ["To favor rich validators", "To prevent balancing attacks and strengthen fork choice", "To slow down blocks", "Cosmetic change"], correct: 1, category: "selection" },
        
        // === CATEGORY: SLASHING (Questions 101-150) ===
        { id: 101, q: "What is slashing?", a: ["Price reduction", "Penalty destroying validator stake for misbehavior", "A trading strategy", "Account deletion"], correct: 1, category: "slashing" },
        { id: 102, q: "What is 'double signing' (equivocation)?", a: ["Signing twice", "Signing two conflicting blocks/attestations for same slot", "Using two keys", "Multi-sig"], correct: 1, category: "slashing" },
        { id: 103, q: "Why is double signing slashable?", a: ["It's annoying", "It's an attempt to create conflicting chain history", "It wastes energy", "It's slow"], correct: 1, category: "slashing" },
        { id: 104, q: "What is a 'surround vote'?", a: ["Voting method", "Attestation that wraps around (surrounds) a previous one", "Election", "Consensus rule"], correct: 1, category: "slashing" },
        { id: 105, q: "Why are surround votes slashable?", a: ["They're confusing", "They attempt to finalize conflicting checkpoints", "They're slow", "They waste gas"], correct: 1, category: "slashing" },
        { id: 106, q: "What's the minimum slashing penalty?", a: ["0%", "1/32 of stake (about 1 ETH)", "50%", "100%"], correct: 1, category: "slashing" },
        { id: 107, q: "What is the 'correlation penalty'?", a: ["Statistical measure", "Extra slashing if many validators slash together", "Reward bonus", "Network metric"], correct: 1, category: "slashing" },
        { id: 108, q: "Why does correlation penalty exist?", a: ["To punish individuals", "To heavily penalize coordinated attacks", "Revenue generation", "Random rule"], correct: 1, category: "slashing" },
        { id: 109, q: "If 1/3 of validators are slashed simultaneously, what's the penalty?", a: ["1/32", "Full stake (100%)", "Nothing", "Half"], correct: 1, category: "slashing" },
        { id: 110, q: "What is the 'slasher' client?", a: ["A weapon", "Software monitoring for slashable offenses", "A validator", "A wallet"], correct: 1, category: "slashing" },
        { id: 111, q: "Who can submit slashing evidence?", a: ["Only Ethereum Foundation", "Any network participant", "Only validators", "Only exchanges"], correct: 1, category: "slashing" },
        { id: 112, q: "What reward does the slashing reporter receive?", a: ["Nothing", "A portion of the slashed stake", "The full stake", "Negative reward"], correct: 1, category: "slashing" },
        { id: 113, q: "What is 'slashing protection'?", a: ["Insurance", "Database preventing accidental self-slashing", "Legal protection", "Community guidelines"], correct: 1, category: "slashing" },
        { id: 114, q: "Why might a validator accidentally double-sign?", a: ["They're malicious", "Running same keys on two machines simultaneously", "Bad luck", "Network error"], correct: 1, category: "slashing" },
        { id: 115, q: "What happens to slashed validators?", a: ["They continue normally", "Forced exit with penalties over time", "Immediate removal", "Account freeze"], correct: 1, category: "slashing" },
        { id: 116, q: "How long after slashing can a validator withdraw remaining funds?", a: ["Immediately", "After about 36 days (8192 epochs)", "Never", "1 year"], correct: 1, category: "slashing" },
        { id: 117, q: "Can a slashed validator ever validate again with the same keys?", a: ["Yes, after appeal", "No, those keys are permanently exited", "Yes, after paying fee", "Depends on offense"], correct: 1, category: "slashing" },
        { id: 118, q: "What is 'doppelganger detection'?", a: ["Clone finding", "Protection against running duplicate validators", "Attack type", "Network monitoring"], correct: 1, category: "slashing" },
        { id: 119, q: "Is slashing automatic or does it require human intervention?", a: ["Requires court order", "Automatic via protocol rules", "Community vote", "Foundation approval"], correct: 1, category: "slashing" },
        { id: 120, q: "What makes slashing 'credible'?", a: ["Threats", "It's actually enforced by code, not promises", "Legal backing", "Insurance"], correct: 1, category: "slashing" },
        { id: 121, q: "Can validators be slashed for being offline?", a: ["Yes, immediately", "No, only inactivity penalties (not slashing)", "Yes, after 1 day", "Random"], correct: 1, category: "slashing" },
        { id: 122, q: "What's the difference between slashing and inactivity penalty?", a: ["Same thing", "Slashing is for malicious acts; inactivity is for being offline", "Slashing is smaller", "No difference"], correct: 1, category: "slashing" },
        { id: 123, q: "What is 'weak subjectivity'?", a: ["Philosophical concept", "Nodes need recent checkpoint to avoid long-range attacks", "Network weakness", "User interface"], correct: 1, category: "slashing" },
        { id: 124, q: "How does slashing protect against long-range attacks?", a: ["It doesn't", "Old attackers would have been slashed, making keys worthless", "Through encryption", "Via backups"], correct: 1, category: "slashing" },
        { id: 125, q: "Why is the slashing penalty designed to be proportional to other slashings?", a: ["Fairness", "Disincentivizes coordinated attacks more than accidents", "Revenue optimization", "Random choice"], correct: 1, category: "slashing" },
        
        // === CATEGORY: CONSENSUS & FINALITY (Questions 126-175) ===
        { id: 126, q: "What is 'consensus' in blockchain?", a: ["Agreement on valid state", "A conference", "A voting app", "A token"], correct: 0, category: "consensus" },
        { id: 127, q: "What is Ethereum's consensus mechanism called?", a: ["Nakamoto Consensus", "Gasper (LMD GHOST + Casper FFG)", "Tendermint", "Raft"], correct: 1, category: "consensus" },
        { id: 128, q: "What does LMD GHOST stand for?", a: ["A horror movie", "Latest Message Driven Greediest Heaviest Observed SubTree", "A validator name", "A token"], correct: 1, category: "consensus" },
        { id: 129, q: "What does LMD GHOST do?", a: ["Ghost hunting", "Fork choice - picks the chain with most support", "Block production", "Slashing"], correct: 1, category: "consensus" },
        { id: 130, q: "What is Casper FFG?", a: ["A ghost", "Finality gadget that makes blocks permanent", "A validator", "A wallet"], correct: 1, category: "consensus" },
        { id: 131, q: "What does FFG stand for?", a: ["Fast Finality Guarantee", "Friendly Finality Gadget", "Final Fork Guard", "First-come First-go"], correct: 1, category: "consensus" },
        { id: 132, q: "What is a 'checkpoint' in Casper?", a: ["A save point", "First block of each epoch used for finality", "A validator ID", "A transaction type"], correct: 1, category: "consensus" },
        { id: 133, q: "What is 'justification'?", a: ["Legal defense", "When 2/3 of stake attests to a checkpoint", "Account verification", "Fee payment"], correct: 1, category: "consensus" },
        { id: 134, q: "What is 'finalization'?", a: ["Ending something", "When a justified block's child is also justified", "Block deletion", "Transaction completion"], correct: 1, category: "consensus" },
        { id: 135, q: "How much stake must attest for justification?", a: ["50%", "66.7% (2/3)", "90%", "100%"], correct: 1, category: "consensus" },
        { id: 136, q: "Why 2/3 threshold specifically?", a: ["Arbitrary", "Byzantine fault tolerance requires >2/3 honest majority", "Marketing", "Tradition"], correct: 1, category: "consensus" },
        { id: 137, q: "Can a finalized block ever be reverted?", a: ["Yes, easily", "Only with 1/3 stake slashed (economic finality)", "Never under any circumstances", "Daily resets"], correct: 1, category: "consensus" },
        { id: 138, q: "What is 'economic finality'?", a: ["Financial term", "Reversal requires destroying significant stake value", "Budget planning", "Fee structure"], correct: 1, category: "consensus" },
        { id: 139, q: "How long until a transaction is finalized?", a: ["Instant", "About 12-15 minutes (2-3 epochs)", "1 hour", "1 day"], correct: 1, category: "consensus" },
        { id: 140, q: "What is a 'fork' in blockchain?", a: ["Eating utensil", "Chain split where two valid blocks exist", "A transaction", "A validator"], correct: 1, category: "consensus" },
        { id: 141, q: "What causes forks?", a: ["Bugs only", "Network delays, simultaneous proposals, or attacks", "User error", "Hardware failure"], correct: 1, category: "consensus" },
        { id: 142, q: "How does LMD GHOST resolve forks?", a: ["Random selection", "Following the subtree with most recent attestations", "Oldest block wins", "Smallest block wins"], correct: 1, category: "consensus" },
        { id: 143, q: "What is a 'reorg' (reorganization)?", a: ["Company restructuring", "Chain switching to a different fork as canonical", "Block deletion", "Account merge"], correct: 1, category: "consensus" },
        { id: 144, q: "Are reorgs normal in Ethereum?", a: ["Never happen", "Small reorgs (1-2 blocks) happen, deep reorgs are rare", "Every block", "Only during attacks"], correct: 1, category: "consensus" },
        { id: 145, q: "What is 'probabilistic finality'?", a: ["Statistics", "Confidence increasing over time (PoW style)", "Random finality", "Maybe-finality"], correct: 1, category: "consensus" },
        { id: 146, q: "How does Ethereum's finality differ from Bitcoin's?", a: ["Same", "Ethereum has deterministic finality; Bitcoin has probabilistic", "Bitcoin is faster", "No difference"], correct: 1, category: "consensus" },
        { id: 147, q: "What is 'safety' in consensus?", a: ["Security guards", "Honest nodes agree on same blocks", "Password protection", "Insurance"], correct: 1, category: "consensus" },
        { id: 148, q: "What is 'liveness' in consensus?", a: ["Being alive", "Network continues making progress", "User activity", "Online status"], correct: 1, category: "consensus" },
        { id: 149, q: "What's the tradeoff between safety and liveness?", a: ["No tradeoff", "Prioritizing one may temporarily sacrifice the other", "Both always optimal", "Neither matters"], correct: 1, category: "consensus" },
        { id: 150, q: "What does Ethereum prioritize: safety or liveness?", a: ["Liveness always", "Safety during normal operation, liveness recovery via inactivity leak", "Neither", "Both equally always"], correct: 1, category: "consensus" },
        
        // === CATEGORY: ATTACKS & SECURITY (Questions 151-200) ===
        { id: 151, q: "What is a '51% attack'?", a: ["Discount sale", "Controlling majority of network power/stake", "A game", "A token"], correct: 1, category: "attacks" },
        { id: 152, q: "How much would a 51% attack on Ethereum cost?", a: ["$1,000", "Tens of billions of dollars", "$1 million", "Free"], correct: 1, category: "attacks" },
        { id: 153, q: "Why is 51% attack harder in PoS than PoW?", a: ["Same difficulty", "Attacker must OWN stake vs rent mining power", "PoS is weaker", "More validators"], correct: 1, category: "attacks" },
        { id: 154, q: "What is a 'long-range attack'?", a: ["Distance running", "Creating alternative history from old blocks", "Network attack", "DDoS"], correct: 1, category: "attacks" },
        { id: 155, q: "How does PoS defend against long-range attacks?", a: ["Can't defend", "Weak subjectivity checkpoints and slashing", "More validators", "Encryption"], correct: 1, category: "attacks" },
        { id: 156, q: "What is a 'nothing at stake' problem?", a: ["Poverty", "PoS validators can vote on multiple forks costlessly", "Empty wallets", "No rewards"], correct: 1, category: "attacks" },
        { id: 157, q: "How does Ethereum solve nothing at stake?", a: ["Can't solve", "Slashing penalties for conflicting votes", "Ignoring it", "Community rules"], correct: 1, category: "attacks" },
        { id: 158, q: "What is a 'balancing attack'?", a: ["Gymnastics", "Keeping the network split between two forks", "Budget attack", "Token manipulation"], correct: 1, category: "attacks" },
        { id: 159, q: "What defends against balancing attacks?", a: ["Nothing", "Proposer boost and attestation deadlines", "More validators", "Higher fees"], correct: 1, category: "attacks" },
        { id: 160, q: "What is a 'grinding attack' on randomness?", a: ["Coffee making", "Manipulating RANDAO by selective block production", "Hardware attack", "Spam attack"], correct: 1, category: "attacks" },
        { id: 161, q: "What is a 'censorship attack'?", a: ["Book banning", "Validators refusing to include certain transactions", "Network filtering", "Content moderation"], correct: 1, category: "attacks" },
        { id: 162, q: "How does Ethereum resist censorship?", a: ["Can't resist", "Decentralization and proposer rotation", "Legal protection", "Community guidelines"], correct: 1, category: "attacks" },
        { id: 163, q: "What is 'OFAC compliance' controversy?", a: ["Tax rule", "US sanctions and whether validators must censor", "Protocol upgrade", "Governance vote"], correct: 1, category: "attacks" },
        { id: 164, q: "What percentage of blocks complied with OFAC after The Merge (peak)?", a: ["0%", "Over 70% at peak", "100%", "25%"], correct: 1, category: "attacks" },
        { id: 165, q: "What is a 'finality delay attack'?", a: ["Slow finality", "Preventing network from reaching finality", "Transaction delay", "Upgrade delay"], correct: 1, category: "attacks" },
        { id: 166, q: "What triggers inactivity leak as defense?", a: ["User request", "Chain not finalizing for 4+ epochs", "Daily schedule", "Random"], correct: 1, category: "attacks" },
        { id: 167, q: "What is a 'bouncing attack'?", a: ["Ball game", "Repeatedly switching between chain heads", "Network ping", "Token trading"], correct: 1, category: "attacks" },
        { id: 168, q: "What is 'Proposer-Builder Separation' (PBS)?", a: ["Construction term", "Separating who builds vs proposes blocks", "Team structure", "Protocol split"], correct: 1, category: "attacks" },
        { id: 169, q: "How does PBS help decentralization?", a: ["It doesn't", "Separates MEV extraction from validation", "More validators", "Lower stake"], correct: 1, category: "attacks" },
        { id: 170, q: "What is a 'sandwich attack'?", a: ["Food", "Front and back-running a user's trade", "Network attack", "Consensus attack"], correct: 1, category: "attacks" },
        { id: 171, q: "Who typically performs sandwich attacks?", a: ["Hackers", "MEV searchers/bots", "Validators only", "Exchanges"], correct: 1, category: "attacks" },
        { id: 172, q: "What is 'front-running'?", a: ["Racing", "Placing transaction ahead of known pending transaction", "Leading", "First place"], correct: 1, category: "attacks" },
        { id: 173, q: "What is a 'time-bandit attack'?", a: ["Time travel", "Reorganizing chain to steal past MEV", "Schedule attack", "Clock manipulation"], correct: 1, category: "attacks" },
        { id: 174, q: "How does finality protect against time-bandit attacks?", a: ["It doesn't", "Finalized blocks cannot be reorganized economically", "Encryption", "More validators"], correct: 1, category: "attacks" },
        { id: 175, q: "What is 'chain quality' metric?", a: ["Rating", "Fraction of blocks from honest validators", "Block size", "Transaction speed"], correct: 1, category: "attacks" },
        
        // === CATEGORY: ETHEREUM SPECIFICS (Questions 176-225) ===
        { id: 176, q: "Who created Ethereum?", a: ["Satoshi Nakamoto", "Vitalik Buterin (with others)", "Elon Musk", "Mark Zuckerberg"], correct: 1, category: "ethereum" },
        { id: 177, q: "When was Ethereum launched?", a: ["2009", "July 30, 2015", "2020", "2022"], correct: 1, category: "ethereum" },
        { id: 178, q: "What consensus did Ethereum use before The Merge?", a: ["Proof of Stake", "Proof of Work", "Proof of Authority", "Proof of History"], correct: 1, category: "ethereum" },
        { id: 179, q: "What is 'gas' in Ethereum?", a: ["Fuel", "Unit measuring computational work", "A token", "Network speed"], correct: 1, category: "ethereum" },
        { id: 180, q: "What is the 'gas limit'?", a: ["Price cap", "Maximum gas allowed per block", "User setting", "Minimum fee"], correct: 1, category: "ethereum" },
        { id: 181, q: "What happens if a transaction runs out of gas?", a: ["Free execution", "Transaction fails, gas is still consumed", "Automatic refund", "Nothing"], correct: 1, category: "ethereum" },
        { id: 182, q: "What is a 'smart contract'?", a: ["Legal agreement", "Self-executing code on blockchain", "A PDF", "A lawyer"], correct: 1, category: "ethereum" },
        { id: 183, q: "What language are most Ethereum smart contracts written in?", a: ["Python", "Solidity", "JavaScript", "C++"], correct: 1, category: "ethereum" },
        { id: 184, q: "What is the 'EVM'?", a: ["Electric vehicle", "Ethereum Virtual Machine - smart contract runtime", "Token type", "Wallet"], correct: 1, category: "ethereum" },
        { id: 185, q: "What is 'state' in Ethereum?", a: ["Country", "All account balances and contract storage", "Network status", "Transaction list"], correct: 1, category: "ethereum" },
        { id: 186, q: "What is a 'nonce' in Ethereum transactions?", a: ["A word", "Transaction counter preventing replay", "A token", "A fee"], correct: 1, category: "ethereum" },
        { id: 187, q: "What is the difference between ETH and ERC-20 tokens?", a: ["Same thing", "ETH is native; ERC-20 are smart contract tokens", "ERC-20 is newer", "ETH is token"], correct: 1, category: "ethereum" },
        { id: 188, q: "What is an 'EOA'?", a: ["Organization", "Externally Owned Account (user wallet)", "Token type", "Contract type"], correct: 1, category: "ethereum" },
        { id: 189, q: "How is an Ethereum address derived?", a: ["Random", "Hash of public key (last 20 bytes)", "Sequential", "User chosen"], correct: 1, category: "ethereum" },
        { id: 190, q: "What is 'account abstraction'?", a: ["Art concept", "Making smart contracts act as accounts", "Privacy feature", "Scaling solution"], correct: 1, category: "ethereum" },
        { id: 191, q: "What is EIP-4844 (Proto-Danksharding)?", a: ["A game", "Blob transactions for L2 scaling", "Token standard", "Wallet feature"], correct: 1, category: "ethereum" },
        { id: 192, q: "What are 'blobs' in EIP-4844?", a: ["Fish", "Large data chunks for rollups with separate fee market", "Tokens", "Blocks"], correct: 1, category: "ethereum" },
        { id: 193, q: "What is 'Danksharding'?", a: ["Person's name", "Full data availability sharding (future)", "Current feature", "Token"], correct: 1, category: "ethereum" },
        { id: 194, q: "What is a 'rollup'?", a: ["Exercise", "L2 scaling executing transactions off-chain", "Token type", "Consensus type"], correct: 1, category: "ethereum" },
        { id: 195, q: "What's the difference between optimistic and ZK rollups?", a: ["Speed only", "Fraud proofs vs validity proofs", "Same thing", "Token type"], correct: 1, category: "ethereum" },
        { id: 196, q: "What is 'data availability' in rollups?", a: ["Uptime", "Ensuring L1 has data to verify L2 transactions", "Storage", "Bandwidth"], correct: 1, category: "ethereum" },
        { id: 197, q: "What is the 'execution layer'?", a: ["Management", "Part of Ethereum processing transactions", "Token layer", "Storage"], correct: 1, category: "ethereum" },
        { id: 198, q: "What is the 'consensus layer'?", a: ["Agreement level", "Part of Ethereum running PoS consensus", "Marketing layer", "User layer"], correct: 1, category: "ethereum" },
        { id: 199, q: "What clients can run the consensus layer?", a: ["Only one", "Prysm, Lighthouse, Teku, Nimbus, Lodestar", "Chrome", "MetaMask"], correct: 1, category: "ethereum" },
        { id: 200, q: "Why is client diversity important?", a: ["Aesthetics", "Prevents bugs in one client from causing consensus failures", "Speed", "Cost"], correct: 1, category: "ethereum" },
        
        // === CATEGORY: REAL-WORLD APPLICATIONS (Questions 201-250) ===
        { id: 201, q: "What is DeFi?", a: ["Defiance", "Decentralized Finance - financial services on blockchain", "A token", "A company"], correct: 1, category: "applications" },
        { id: 202, q: "What is a DEX?", a: ["Dinosaur", "Decentralized Exchange", "A wallet", "A token"], correct: 1, category: "applications" },
        { id: 203, q: "What is Uniswap?", a: ["A swap meet", "Popular DEX using automated market makers", "A token", "A wallet"], correct: 1, category: "applications" },
        { id: 204, q: "What is 'liquidity' in DeFi?", a: ["Water", "Available assets for trading in pools", "A token", "Speed"], correct: 1, category: "applications" },
        { id: 205, q: "What is 'yield farming'?", a: ["Agriculture", "Earning rewards by providing liquidity/staking", "A game", "Mining"], correct: 1, category: "applications" },
        { id: 206, q: "What is an NFT?", a: ["Token type", "Non-Fungible Token - unique digital asset", "A coin", "A contract"], correct: 1, category: "applications" },
        { id: 207, q: "What makes NFTs 'non-fungible'?", a: ["Price", "Each token is unique and not interchangeable", "Material", "Size"], correct: 1, category: "applications" },
        { id: 208, q: "What is a DAO?", a: ["Chinese word", "Decentralized Autonomous Organization", "A token", "A wallet"], correct: 1, category: "applications" },
        { id: 209, q: "How do DAOs typically make decisions?", a: ["CEO decides", "Token holder voting", "Random", "AI"], correct: 1, category: "applications" },
        { id: 210, q: "What is 'governance' in crypto?", a: ["Government", "Decision-making process for protocol changes", "Regulation", "Control"], correct: 1, category: "applications" },
        { id: 211, q: "What is a 'lending protocol'?", a: ["Bank", "DeFi service for borrowing/lending crypto", "Email service", "Game"], correct: 1, category: "applications" },
        { id: 212, q: "What is Aave?", a: ["A greeting", "Popular DeFi lending protocol", "A token only", "An exchange"], correct: 1, category: "applications" },
        { id: 213, q: "What is 'collateral' in DeFi lending?", a: ["Jewelry", "Assets locked to secure a loan", "A fee", "A reward"], correct: 1, category: "applications" },
        { id: 214, q: "What is a 'stablecoin'?", a: ["Horse coin", "Crypto pegged to stable asset like USD", "Boring coin", "Small coin"], correct: 1, category: "applications" },
        { id: 215, q: "What is USDC?", a: ["Currency", "USD Coin - centralized stablecoin", "US Dollar Crypto", "A bank"], correct: 1, category: "applications" },
        { id: 216, q: "What is DAI?", a: ["Japanese word", "Decentralized stablecoin by MakerDAO", "A greeting", "A game"], correct: 1, category: "applications" },
        { id: 217, q: "What is a 'bridge' in crypto?", a: ["Structure", "Protocol moving assets between blockchains", "A game", "A wallet"], correct: 1, category: "applications" },
        { id: 218, q: "Why are bridges often targeted by hackers?", a: ["Easy to find", "They hold large amounts of locked assets", "Poor security always", "Government target"], correct: 1, category: "applications" },
        { id: 219, q: "What is an 'oracle' in blockchain?", a: ["Fortune teller", "Service providing external data to smart contracts", "A token", "A validator"], correct: 1, category: "applications" },
        { id: 220, q: "What is Chainlink?", a: ["Chain store", "Popular decentralized oracle network", "A game", "A wallet"], correct: 1, category: "applications" },
        { id: 221, q: "What is 'TVL' (Total Value Locked)?", a: ["TV channel", "Metric showing assets deposited in DeFi protocols", "A token", "A rating"], correct: 1, category: "applications" },
        { id: 222, q: "What is an 'airdrop'?", a: ["Delivery service", "Free token distribution to wallet holders", "A game", "A fee"], correct: 1, category: "applications" },
        { id: 223, q: "What is 'token burning'?", a: ["Fire", "Permanently removing tokens from circulation", "A game", "A reward"], correct: 1, category: "applications" },
        { id: 224, q: "What is 'vesting' in crypto?", a: ["Clothing", "Gradual release of locked tokens over time", "A fee", "A reward"], correct: 1, category: "applications" },
        { id: 225, q: "What is a 'snapshot' for airdrops?", a: ["Photo", "Recording of wallet balances at specific time", "A game", "A token"], correct: 1, category: "applications" },
        
        // === CATEGORY: WALLETS & SECURITY (Questions 226-275) ===
        { id: 226, q: "What is a 'private key'?", a: ["Password", "Secret number controlling wallet access", "A token", "A fee"], correct: 1, category: "wallets" },
        { id: 227, q: "What is a 'public key'?", a: ["Public information", "Cryptographic key derived from private key", "A token", "An address"], correct: 1, category: "wallets" },
        { id: 228, q: "What is a 'seed phrase' (mnemonic)?", a: ["Plant seeds", "12-24 words that can restore a wallet", "A password", "A username"], correct: 1, category: "wallets" },
        { id: 229, q: "Should you ever share your seed phrase?", a: ["Yes, with friends", "Never - it gives full access to funds", "Only with exchanges", "Sometimes"], correct: 1, category: "wallets" },
        { id: 230, q: "What is MetaMask?", a: ["A mask", "Popular browser-based Ethereum wallet", "A game", "A token"], correct: 1, category: "wallets" },
        { id: 231, q: "What is a 'hardware wallet'?", a: ["Computer", "Physical device storing keys offline", "Software", "A token"], correct: 1, category: "wallets" },
        { id: 232, q: "What are Ledger and Trezor?", a: ["Games", "Popular hardware wallet brands", "Exchanges", "Tokens"], correct: 1, category: "wallets" },
        { id: 233, q: "What is a 'hot wallet'?", a: ["Warm wallet", "Wallet connected to the internet", "A new wallet", "Fast wallet"], correct: 1, category: "wallets" },
        { id: 234, q: "What is a 'cold wallet'?", a: ["Frozen wallet", "Wallet kept offline for security", "Old wallet", "Slow wallet"], correct: 1, category: "wallets" },
        { id: 235, q: "Why are cold wallets more secure?", a: ["They're newer", "Not connected to internet, harder to hack remotely", "They're expensive", "Government backed"], correct: 1, category: "wallets" },
        { id: 236, q: "What is a 'multi-sig' wallet?", a: ["Many signatures", "Wallet requiring multiple keys to authorize transactions", "A new wallet", "A fast wallet"], correct: 1, category: "wallets" },
        { id: 237, q: "What is a '2-of-3 multi-sig'?", a: ["Math problem", "Requires 2 of 3 keyholders to sign", "A game", "A fee structure"], correct: 1, category: "wallets" },
        { id: 238, q: "What is 'transaction signing'?", a: ["Writing", "Using private key to authorize a transaction", "A fee", "A reward"], correct: 1, category: "wallets" },
        { id: 239, q: "What is a 'phishing attack'?", a: ["Fishing", "Fake website/message tricking users to reveal keys", "A game", "A token"], correct: 1, category: "wallets" },
        { id: 240, q: "How can you identify phishing attempts?", a: ["You can't", "Check URLs carefully, never click suspicious links", "Trust all emails", "Call support"], correct: 1, category: "wallets" },
        { id: 241, q: "What is a 'rug pull'?", a: ["Home decor", "Scam where developers abandon project with funds", "A game", "A reward"], correct: 1, category: "wallets" },
        { id: 242, q: "What is 'address poisoning'?", a: ["Toxic address", "Sending tiny amounts from similar-looking addresses to trick users", "A fee", "A reward"], correct: 1, category: "wallets" },
        { id: 243, q: "Why should you verify addresses before sending?", a: ["Courtesy", "Transactions are irreversible, mistakes lose funds", "Speed", "Fees"], correct: 1, category: "wallets" },
        { id: 244, q: "What is 'infinite approval' risk?", a: ["Math error", "Giving contracts unlimited access to your tokens", "A game", "A reward"], correct: 1, category: "wallets" },
        { id: 245, q: "What is 'revoke.cash'?", a: ["A game", "Tool to check and revoke token approvals", "An exchange", "A wallet"], correct: 1, category: "wallets" },
        { id: 246, q: "What is a 'dusting attack'?", a: ["Cleaning", "Sending tiny amounts to track wallet activity", "A game", "A reward"], correct: 1, category: "wallets" },
        { id: 247, q: "What is 'social engineering' in crypto scams?", a: ["Building", "Manipulating people to reveal sensitive information", "A job", "A reward"], correct: 1, category: "wallets" },
        { id: 248, q: "What is a 'honeypot' scam?", a: ["Bee product", "Token that can be bought but not sold", "A game", "A reward"], correct: 1, category: "wallets" },
        { id: 249, q: "What should you do if you think your wallet is compromised?", a: ["Nothing", "Move funds to a new secure wallet immediately", "Wait and see", "Call police"], correct: 1, category: "wallets" },
        { id: 250, q: "What is a 'paper wallet'?", a: ["Paper money", "Private key printed on paper for offline storage", "A document", "A fee"], correct: 1, category: "wallets" },
        
        // === CATEGORY: ADVANCED CONCEPTS (Questions 251-300) ===
        { id: 251, q: "What is 'sharding' in Ethereum's roadmap?", a: ["Breaking", "Splitting network into parallel processing chains", "A game", "A token"], correct: 1, category: "advanced" },
        { id: 252, q: "What is 'data availability sampling'?", a: ["Statistics", "Verifying data exists without downloading all of it", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 253, q: "What are 'KZG commitments'?", a: ["Company initials", "Cryptographic scheme for data availability proofs", "A token", "A wallet"], correct: 1, category: "advanced" },
        { id: 254, q: "What is a 'zero-knowledge proof'?", a: ["No proof", "Proving something true without revealing details", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 255, q: "What is a 'SNARK'?", a: ["Comment", "Succinct Non-interactive Argument of Knowledge", "A game", "A token"], correct: 1, category: "advanced" },
        { id: 256, q: "What is a 'STARK'?", a: ["Character", "Scalable Transparent Argument of Knowledge", "A game", "A token"], correct: 1, category: "advanced" },
        { id: 257, q: "What's the main difference between SNARKs and STARKs?", a: ["Nothing", "STARKs don't need trusted setup, are quantum-resistant", "Speed only", "Cost only"], correct: 1, category: "advanced" },
        { id: 258, q: "What is 'recursive proving'?", a: ["Repetition", "Proofs that verify other proofs for scalability", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 259, q: "What is 'enshrined PBS'?", a: ["Religion", "Proposer-Builder Separation built into protocol", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 260, q: "What is 'single slot finality'?", a: ["Fast finality", "Finalizing blocks in one slot instead of epochs", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 261, q: "What is 'Verkle trees'?", a: ["Plants", "More efficient state storage structure than Merkle trees", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 262, q: "What is 'state expiry'?", a: ["Death", "Removing old unused state to reduce bloat", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 263, q: "What is 'statelessness' in Ethereum?", a: ["No states", "Nodes validating without full state storage", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 264, q: "What is 'proof of custody'?", a: ["Legal term", "Proving validators actually store required data", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 265, q: "What is 'distributed validator technology' (DVT)?", a: ["Delivery", "Running one validator across multiple machines", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 266, q: "What is the purpose of DVT?", a: ["Speed", "Improving validator resilience and decentralization", "Cost savings", "Simplicity"], correct: 1, category: "advanced" },
        { id: 267, q: "What is 'restaking'?", a: ["Resting", "Using staked ETH as security for other protocols", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 268, q: "What is EigenLayer?", a: ["A game", "Popular restaking protocol", "A wallet", "A token"], correct: 1, category: "advanced" },
        { id: 269, q: "What is 'superfluid staking'?", a: ["Liquid diet", "Staked assets remaining liquid for other uses", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 270, q: "What is 'maximal decentralization'?", a: ["Politics", "Design goal minimizing any single point of control", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 271, q: "What is 'credible neutrality'?", a: ["Politics", "Protocol treating all users fairly by design", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 272, q: "What is 'enshrined' in Ethereum context?", a: ["Religious", "Built into base protocol rather than added layer", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 273, q: "What is 'social consensus'?", a: ["Party agreement", "Community agreement on protocol rules beyond code", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 274, q: "What is a 'contentious hard fork'?", a: ["Utensil", "Upgrade where community disagrees, chain splits", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 275, q: "What is EIP process?", a: ["Pain", "Ethereum Improvement Proposal - formal change process", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 276, q: "What is 'protocol ossification'?", a: ["Bone disease", "When a protocol becomes resistant to changes", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 277, q: "What is 'mechanism design'?", a: ["Engineering", "Creating incentive structures for desired outcomes", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 278, q: "What is 'cryptoeconomics'?", a: ["Currency", "Using economic incentives to secure cryptographic systems", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 279, q: "What is 'game theory' in blockchain?", a: ["Video games", "Analyzing strategic decision-making of participants", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 280, q: "What is a 'dominant strategy' in game theory?", a: ["Best game", "Optimal choice regardless of others' actions", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 281, q: "What is 'Nash equilibrium'?", a: ["Movie", "State where no player benefits from changing strategy alone", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 282, q: "What is 'Sybil resistance'?", a: ["Disease", "Preventing one entity from creating many fake identities", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 283, q: "How does staking provide Sybil resistance?", a: ["It doesn't", "Each validator requires real economic cost (32 ETH)", "Through names", "Via KYC"], correct: 1, category: "advanced" },
        { id: 284, q: "What is 'honest majority assumption'?", a: ["Politics", "Security assuming >50% or >66% of stake is honest", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 285, q: "What is 'synchrony assumption'?", a: ["Timing", "Assuming messages are delivered within time bounds", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 286, q: "What is 'partial synchrony'?", a: ["Half sync", "Network eventually becomes synchronous after unknown delay", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 287, q: "What is 'light client'?", a: ["Small computer", "Node verifying chain with minimal data", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 288, q: "What is 'stateless client'?", a: ["No states", "Node validating without storing full state", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 289, q: "What is 'proof size' concern in ZK systems?", a: ["Paper size", "Computational and storage cost of proofs", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 290, q: "What is 'prover time' in ZK systems?", a: ["Test time", "Time required to generate a proof", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 291, q: "What is 'verifier time' in ZK systems?", a: ["Check time", "Time required to verify a proof", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 292, q: "What is 'trusted setup'?", a: ["Installation", "Initial ceremony creating cryptographic parameters", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 293, q: "Why is trusted setup controversial?", a: ["Cost", "If compromised, fake proofs could be generated", "Slow", "Boring"], correct: 1, category: "advanced" },
        { id: 294, q: "What is 'powers of tau' ceremony?", a: ["Chinese ceremony", "Multi-party trusted setup for ZK systems", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 295, q: "What is 'quantum resistance'?", a: ["Physics", "Security against quantum computer attacks", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 296, q: "Are current Ethereum signatures quantum-resistant?", a: ["Yes", "No, but it's on the roadmap to address", "Partially", "Unknown"], correct: 1, category: "advanced" },
        { id: 297, q: "What is 'post-quantum cryptography'?", a: ["Time travel", "Algorithms secure against quantum computers", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 298, q: "What is 'aggregate signature'?", a: ["Total sign", "Combining multiple signatures into one for efficiency", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 299, q: "What is BLS signature scheme?", a: ["Initials", "Boneh-Lynn-Shacham - allows signature aggregation", "A game", "A fee"], correct: 1, category: "advanced" },
        { id: 300, q: "Why does Ethereum use BLS signatures?", a: ["Marketing", "Efficient aggregation reduces block size and verification time", "Tradition", "Cost"] , correct: 1, category: "advanced" }
    ];
    
    // Generate quiz questions (random 15 from bank)
    const generateQuiz = useCallback(() => {
        const shuffled = [...QUIZ_BANK].sort(() => Math.random() - 0.5);
        setQuizQuestions(shuffled.slice(0, 15));
        setCurrentQuizIndex(0);
        setQuizAnswers({});
        setQuizSubmitted(false);
        setQuizScore(0);
    }, []);
    
    // Initialize quiz when entering chapter 7
    useEffect(() => {
        if (chapter === 7 && quizQuestions.length === 0) {
            generateQuiz();
        }
    }, [chapter, generateQuiz, quizQuestions.length]);
    
    // Submit quiz and calculate score
    const submitQuiz = useCallback(() => {
        let score = 0;
        quizQuestions.forEach((q, idx) => {
            if (quizAnswers[idx] === q.correct) {
                score++;
            }
        });
        setQuizScore(score);
        setQuizSubmitted(true);
    }, [quizQuestions, quizAnswers]);
    
    // Story Mode Next Chapter Handler
    const nextChapter = () => {
        if (chapter < 9) {
            setChapter(chapter + 1);
            setChapterStep(0);
            setShowReveal(false);
            setUserChoices({});
            setAnimationPhase(0);
            // Award badge for completing chapter
            if (!earnedBadges.includes(chapter)) {
                setEarnedBadges([...earnedBadges, chapter]);
            }
        } else {
            setLearningMode('sandbox');
        }
    };
    
    // =====================================================================
    // STORY MODE RENDERING
    // =====================================================================
    if (learningMode === 'story') {
        return (
            <div style={{maxWidth: '900px', margin: '0 auto'}}>
                {/* Progress Bar */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '2rem',
                    padding: '1rem',
                    background: 'rgba(30, 41, 59, 0.8)',
                    borderRadius: '1rem',
                    border: '1px solid #334155'
                }}>
                    {Object.entries(CHAPTERS).map(([num, ch]) => (
                        <div key={num} style={{
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '4px'
                        }}>
                            <div style={{
                                width: '36px',
                                height: '36px',
                                borderRadius: '50%',
                                background: parseInt(num) < chapter ? 'linear-gradient(135deg, #10b981, #34d399)' :
                                           parseInt(num) === chapter ? 'linear-gradient(135deg, #8b5cf6, #a78bfa)' :
                                           'rgba(51, 65, 85, 0.8)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: parseInt(num) < chapter ? '1rem' : '0.9rem',
                                color: 'white',
                                fontWeight: 'bold',
                                transition: 'all 0.3s',
                                border: parseInt(num) === chapter ? '2px solid #c4b5fd' : '2px solid transparent'
                            }}>
                                {parseInt(num) < chapter ? '✓' : earnedBadges.includes(parseInt(num)) ? ch.icon : num}
                            </div>
                            <div style={{
                                fontSize: '0.65rem',
                                color: parseInt(num) === chapter ? '#a78bfa' : '#64748b',
                                textAlign: 'center',
                                maxWidth: '80px',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis'
                            }}>
                                {ch.title.split(' ')[0]}
                            </div>
                        </div>
                    ))}
                    <div style={{display: 'flex', gap: '0.5rem'}}>
                        <button
                            onClick={() => { setChapter(7); generateQuiz(); }}
                            style={{
                                padding: '8px 12px',
                                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(167, 139, 250, 0.2) 100%)',
                                border: '1px solid #8b5cf6',
                                borderRadius: '6px',
                                color: '#c4b5fd',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                whiteSpace: 'nowrap',
                                fontWeight: 'bold'
                            }}
                        >
                            📝 Take Quiz
                        </button>
                        <button
                            onClick={() => setLearningMode('sandbox')}
                            style={{
                                padding: '8px 12px',
                                background: 'rgba(59, 130, 246, 0.2)',
                                border: '1px solid #3b82f6',
                                borderRadius: '6px',
                                color: '#93c5fd',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                whiteSpace: 'nowrap'
                            }}
                        >
                            Sandbox →
                        </button>
                    </div>
                </div>
                
                {/* ========== CHAPTER 1: THE TRUST PROBLEM ========== */}
                {chapter === 1 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(59, 130, 246, 0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>🤔</div>
                            <h1 style={{color: '#f8fafc', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 1: The Trust Problem
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                Before we learn HOW it works, let's understand WHY we need it
                            </p>
                        </div>
                        
                        {chapterStep === 0 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <div style={{
                                    fontSize: '1.2rem',
                                    color: '#e2e8f0',
                                    lineHeight: '1.8',
                                    marginBottom: '2rem'
                                }}>
                                    <p style={{marginTop: 0}}>
                                        <span style={{fontSize: '1.5rem'}}>🌍</span> Imagine you want to send <strong style={{color: '#fbbf24'}}>$100</strong> to someone on the other side of the world.
                                    </p>
                                    <p>
                                        Right now, you'd use a <strong style={{color: '#60a5fa'}}>bank</strong>. The bank keeps track of everyone's money and makes sure no one cheats.
                                    </p>
                                    <p style={{
                                        background: 'rgba(251, 191, 36, 0.1)',
                                        padding: '1rem',
                                        borderRadius: '0.5rem',
                                        border: '1px solid rgba(251, 191, 36, 0.3)'
                                    }}>
                                        <strong style={{color: '#fcd34d'}}>But here's the thing:</strong> You have to <em>trust</em> the bank. What if the bank makes a mistake? What if it gets hacked? What if it decides to freeze your account?
                                    </p>
                                </div>
                                
                                <div style={{
                                    background: 'rgba(139, 92, 246, 0.1)',
                                    padding: '1.5rem',
                                    borderRadius: '0.75rem',
                                    border: '2px solid rgba(139, 92, 246, 0.4)',
                                    marginBottom: '1.5rem'
                                }}>
                                    <h3 style={{color: '#a78bfa', margin: '0 0 1rem 0'}}>💭 Think About It:</h3>
                                    <p style={{color: '#e2e8f0', fontSize: '1.1rem', margin: 0}}>
                                        What if there was a way to send money <strong>without needing to trust any single company or government?</strong>
                                    </p>
                                </div>
                                
                                <button
                                    onClick={() => setChapterStep(1)}
                                    style={{
                                        width: '100%',
                                        padding: '1.25rem',
                                        background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                        border: 'none',
                                        borderRadius: '0.75rem',
                                        color: 'white',
                                        fontSize: '1.1rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >
                                    That sounds impossible... how? →
                                </button>
                            </div>
                        )}
                        
                        {chapterStep === 1 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <h3 style={{color: '#f8fafc', marginTop: 0}}>
                                    🏘️ The Village Ledger Thought Experiment
                                </h3>
                                
                                <div style={{
                                    fontSize: '1.1rem',
                                    color: '#cbd5e1',
                                    lineHeight: '1.8',
                                    marginBottom: '1.5rem'
                                }}>
                                    <p>Imagine a small village with no bank. Instead, <strong style={{color: '#60a5fa'}}>everyone keeps their own copy of a ledger</strong> that tracks all transactions.</p>
                                    <p>When Alice pays Bob $10, she announces it to the whole village. Everyone writes it down in their ledger.</p>
                                </div>
                                
                                {/* Interactive Village Visualization */}
                                <div style={{
                                    background: 'rgba(0,0,0,0.3)',
                                    padding: '1.5rem',
                                    borderRadius: '0.75rem',
                                    marginBottom: '1.5rem'
                                }}>
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-around',
                                        alignItems: 'center',
                                        marginBottom: '1rem'
                                    }}>
                                        {['👩‍💼 Alice', '👨‍💻 Bob', '👩‍🔬 Carol', '🐋 Dave'].map((person, idx) => (
                                            <div key={idx} style={{
                                                textAlign: 'center',
                                                padding: '1rem',
                                                background: 'rgba(59, 130, 246, 0.1)',
                                                borderRadius: '0.5rem',
                                                border: '1px solid rgba(59, 130, 246, 0.3)'
                                            }}>
                                                <div style={{fontSize: '2rem'}}>{person.split(' ')[0]}</div>
                                                <div style={{fontSize: '0.85rem', color: '#94a3b8'}}>{person.split(' ')[1]}</div>
                                                <div style={{fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem'}}>📒 Has ledger</div>
                                            </div>
                                        ))}
                                    </div>
                                    <div style={{
                                        textAlign: 'center',
                                        padding: '1rem',
                                        background: 'rgba(16, 185, 129, 0.1)',
                                        borderRadius: '0.5rem',
                                        border: '1px solid rgba(16, 185, 129, 0.3)',
                                        color: '#86efac'
                                    }}>
                                        ✅ Everyone has the same record. No single person controls the truth!
                                    </div>
                                </div>
                                
                                <div style={{
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    padding: '1.5rem',
                                    borderRadius: '0.75rem',
                                    border: '2px solid rgba(239, 68, 68, 0.4)',
                                    marginBottom: '1.5rem'
                                }}>
                                    <h4 style={{color: '#fca5a5', margin: '0 0 1rem 0'}}>😈 But wait... what if someone tries to CHEAT?</h4>
                                    <p style={{color: '#fed7aa', margin: 0}}>
                                        What if <strong>Mallory</strong> announces "Alice paid me $100" when Alice never did?
                                        Or writes something different in her ledger?
                                    </p>
                                </div>
                                
                                <button
                                    onClick={() => setChapterStep(2)}
                                    style={{
                                        width: '100%',
                                        padding: '1.25rem',
                                        background: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)',
                                        border: 'none',
                                        borderRadius: '0.75rem',
                                        color: 'white',
                                        fontSize: '1.1rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >
                                    How do we stop cheaters? →
                                </button>
                            </div>
                        )}
                        
                        {chapterStep === 2 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <h3 style={{color: '#f8fafc', marginTop: 0}}>
                                    🎯 Your First Challenge
                                </h3>
                                
                                <p style={{color: '#cbd5e1', fontSize: '1.1rem', lineHeight: '1.7'}}>
                                    In our village, we need a way to decide what's TRUE when people disagree.
                                    <br/><br/>
                                    <strong style={{color: '#a78bfa'}}>How should the village solve this?</strong>
                                </p>
                                
                                <div style={{display: 'grid', gap: '1rem', marginTop: '1.5rem'}}>
                                    {[
                                        { id: 'vote', label: 'Let everyone vote on what\'s true', icon: '🗳️', result: 'good' },
                                        { id: 'trust', label: 'Trust the richest person to decide', icon: '💰', result: 'partial' },
                                        { id: 'random', label: 'Pick someone at random to decide', icon: '🎲', result: 'partial' },
                                        { id: 'punish', label: 'Make lying very expensive', icon: '⚖️', result: 'best' }
                                    ].map(option => (
                                        <button
                                            key={option.id}
                                            onClick={() => {
                                                setUserChoices({...userChoices, solution: option.id});
                                                setShowReveal(true);
                                            }}
                                            disabled={showReveal}
                                            style={{
                                                padding: '1.25rem',
                                                background: userChoices.solution === option.id 
                                                    ? option.result === 'best' ? 'rgba(16, 185, 129, 0.2)' :
                                                      option.result === 'good' ? 'rgba(59, 130, 246, 0.2)' :
                                                      'rgba(251, 191, 36, 0.2)'
                                                    : 'rgba(51, 65, 85, 0.5)',
                                                border: userChoices.solution === option.id
                                                    ? option.result === 'best' ? '2px solid #10b981' :
                                                      option.result === 'good' ? '2px solid #3b82f6' :
                                                      '2px solid #f59e0b'
                                                    : '2px solid #475569',
                                                borderRadius: '0.75rem',
                                                cursor: showReveal ? 'default' : 'pointer',
                                                textAlign: 'left',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '1rem',
                                                opacity: showReveal && userChoices.solution !== option.id ? 0.5 : 1
                                            }}
                                        >
                                            <span style={{fontSize: '2rem'}}>{option.icon}</span>
                                            <span style={{color: '#e2e8f0', fontSize: '1rem'}}>{option.label}</span>
                                        </button>
                                    ))}
                                </div>
                                
                                {showReveal && (
                                    <div style={{
                                        marginTop: '1.5rem',
                                        padding: '1.5rem',
                                        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(34, 197, 94, 0.1) 100%)',
                                        borderRadius: '0.75rem',
                                        border: '2px solid #10b981'
                                    }}>
                                        <h4 style={{color: '#86efac', margin: '0 0 1rem 0'}}>
                                            💡 Great thinking! Here's the insight:
                                        </h4>
                                        <p style={{color: '#e2e8f0', fontSize: '1rem', lineHeight: '1.7', margin: 0}}>
                                            <strong>Ethereum uses ALL of these ideas together!</strong>
                                            <br/><br/>
                                            • <strong style={{color: '#86efac'}}>Voting</strong> — Validators vote on what's true
                                            <br/>
                                            • <strong style={{color: '#fbbf24'}}>Wealth-weighted</strong> — More stake = more voting power
                                            <br/>
                                            • <strong style={{color: '#60a5fa'}}>Randomness</strong> — Random selection prevents gaming
                                            <br/>
                                            • <strong style={{color: '#f472b6'}}>Punishment</strong> — Cheaters lose their money (slashing)
                                            <br/><br/>
                                            This combination is called <strong style={{color: '#a78bfa'}}>Proof of Stake</strong>. 
                                            Let's learn how each piece works!
                                        </p>
                                        
                                        <button
                                            onClick={nextChapter}
                                            style={{
                                                marginTop: '1.5rem',
                                                width: '100%',
                                                padding: '1.25rem',
                                                background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                                border: 'none',
                                                borderRadius: '0.75rem',
                                                color: 'white',
                                                fontSize: '1.1rem',
                                                fontWeight: 'bold',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            🎉 I get it! Next chapter →
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
                
                {/* ========== CHAPTER 2: MEET THE VALIDATORS ========== */}
                {chapter === 2 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(139, 92, 246, 0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>👥</div>
                            <h1 style={{color: '#f8fafc', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 2: Meet the Validators
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                The people who keep Ethereum honest
                            </p>
                        </div>
                        
                        <div style={{
                            background: '#1e293b',
                            borderRadius: '1rem',
                            padding: '2rem',
                            border: '1px solid #334155',
                            marginBottom: '1.5rem'
                        }}>
                            <p style={{color: '#cbd5e1', fontSize: '1.1rem', lineHeight: '1.7', marginTop: 0}}>
                                In Ethereum, special participants called <strong style={{color: '#a78bfa'}}>validators</strong> are responsible for:
                            </p>
                            
                            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', margin: '1.5rem 0'}}>
                                {[
                                    { icon: '✅', title: 'Checking transactions', desc: 'Making sure nobody spends money they don\'t have' },
                                    { icon: '📦', title: 'Creating blocks', desc: 'Bundling transactions together' },
                                    { icon: '🗳️', title: 'Voting on truth', desc: 'Agreeing which blocks are valid' }
                                ].map((item, idx) => (
                                    <div key={idx} style={{
                                        padding: '1.25rem',
                                        background: 'rgba(139, 92, 246, 0.1)',
                                        borderRadius: '0.75rem',
                                        border: '1px solid rgba(139, 92, 246, 0.3)',
                                        textAlign: 'center'
                                    }}>
                                        <div style={{fontSize: '2rem', marginBottom: '0.5rem'}}>{item.icon}</div>
                                        <div style={{color: '#a78bfa', fontWeight: 'bold', marginBottom: '0.25rem'}}>{item.title}</div>
                                        <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>{item.desc}</div>
                                    </div>
                                ))}
                            </div>
                            
                            <h3 style={{color: '#f8fafc'}}>🎭 Meet our cast of validators:</h3>
                            
                            <div style={{display: 'grid', gap: '1rem', marginTop: '1rem'}}>
                                {validators.map(v => (
                                    <div key={v.id} style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '1rem',
                                        padding: '1rem',
                                        background: `linear-gradient(135deg, ${v.color}15 0%, ${v.color}05 100%)`,
                                        borderRadius: '0.75rem',
                                        border: `2px solid ${v.color}40`
                                    }}>
                                        <div style={{
                                            width: '60px',
                                            height: '60px',
                                            borderRadius: '50%',
                                            background: v.color,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: '1.8rem'
                                        }}>
                                            {v.emoji}
                                        </div>
                                        <div style={{flex: 1}}>
                                            <div style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.5rem',
                                                marginBottom: '0.25rem'
                                            }}>
                                                <span style={{color: '#f8fafc', fontWeight: 'bold', fontSize: '1.1rem'}}>{v.name}</span>
                                                {v.name === 'Mallory' && <span style={{fontSize: '0.75rem', background: '#ef4444', color: 'white', padding: '2px 8px', borderRadius: '10px'}}>Watch this one...</span>}
                                            </div>
                                            <div style={{color: '#94a3b8', fontSize: '0.9rem'}}>{v.personality}</div>
                                        </div>
                                        <div style={{textAlign: 'right'}}>
                                            <div style={{color: v.color, fontWeight: 'bold', fontSize: '1.25rem'}}>{v.stake} ETH</div>
                                            <div style={{color: '#64748b', fontSize: '0.8rem'}}>staked</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            
                            <div style={{
                                marginTop: '1.5rem',
                                padding: '1rem',
                                background: 'rgba(251, 191, 36, 0.1)',
                                borderRadius: '0.5rem',
                                border: '1px solid rgba(251, 191, 36, 0.3)'
                            }}>
                                <p style={{color: '#fcd34d', margin: 0, fontSize: '0.95rem'}}>
                                    <strong>💡 Notice:</strong> They all have different amounts "staked." 
                                    That number is SUPER important. Let's find out why...
                                </p>
                            </div>
                            
                            <button
                                onClick={nextChapter}
                                style={{
                                    marginTop: '1.5rem',
                                    width: '100%',
                                    padding: '1.25rem',
                                    background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                    border: 'none',
                                    borderRadius: '0.75rem',
                                    color: 'white',
                                    fontSize: '1.1rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer'
                                }}
                            >
                                Why does stake matter? →
                            </button>
                        </div>
                    </div>
                )}
                
                {/* ========== CHAPTER 3: SKIN IN THE GAME ========== */}
                {chapter === 3 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(251, 191, 36, 0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>💰</div>
                            <h1 style={{color: '#f8fafc', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 3: Skin in the Game
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                Why would anyone be honest? Money.
                            </p>
                        </div>
                        
                        {chapterStep === 0 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <p style={{color: '#cbd5e1', fontSize: '1.1rem', lineHeight: '1.7', marginTop: 0}}>
                                    Here's the genius of Proof of Stake:
                                </p>
                                
                                <div style={{
                                    background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.1) 100%)',
                                    padding: '2rem',
                                    borderRadius: '1rem',
                                    border: '2px solid rgba(251, 191, 36, 0.4)',
                                    textAlign: 'center',
                                    margin: '1.5rem 0'
                                }}>
                                    <div style={{fontSize: '3rem', marginBottom: '1rem'}}>🔒</div>
                                    <p style={{color: '#fcd34d', fontSize: '1.25rem', fontWeight: 'bold', margin: 0}}>
                                        To become a validator, you must LOCK UP your own money.
                                    </p>
                                    <p style={{color: '#fde68a', fontSize: '1rem', margin: '1rem 0 0 0'}}>
                                        On real Ethereum: <strong>32 ETH minimum</strong> (~$100,000!)
                                    </p>
                                </div>
                                
                                <h3 style={{color: '#f8fafc'}}>🤔 Quick Quiz: Why does this matter?</h3>
                                
                                <div style={{display: 'grid', gap: '0.75rem', marginTop: '1rem'}}>
                                    {[
                                        { id: 'a', text: 'Rich people are more trustworthy' },
                                        { id: 'b', text: 'If you cheat, you LOSE your locked money' },
                                        { id: 'c', text: 'It\'s just for show' }
                                    ].map(opt => (
                                        <button
                                            key={opt.id}
                                            onClick={() => {
                                                setUserChoices({...userChoices, whyStake: opt.id});
                                                if (opt.id === 'b') setShowReveal(true);
                                            }}
                                            disabled={showReveal}
                                            style={{
                                                padding: '1rem',
                                                background: userChoices.whyStake === opt.id 
                                                    ? opt.id === 'b' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'
                                                    : 'rgba(51, 65, 85, 0.5)',
                                                border: userChoices.whyStake === opt.id
                                                    ? opt.id === 'b' ? '2px solid #10b981' : '2px solid #ef4444'
                                                    : '2px solid #475569',
                                                borderRadius: '0.75rem',
                                                cursor: showReveal ? 'default' : 'pointer',
                                                textAlign: 'left',
                                                color: '#e2e8f0',
                                                fontSize: '1rem'
                                            }}
                                        >
                                            {opt.text}
                                            {showReveal && userChoices.whyStake === opt.id && (
                                                <span style={{marginLeft: '1rem'}}>
                                                    {opt.id === 'b' ? '✅' : '❌'}
                                                </span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                                
                                {showReveal && (
                                    <div style={{marginTop: '1.5rem'}}>
                                        <div style={{
                                            padding: '1.5rem',
                                            background: 'rgba(16, 185, 129, 0.15)',
                                            borderRadius: '0.75rem',
                                            border: '2px solid #10b981'
                                        }}>
                                            <h4 style={{color: '#86efac', margin: '0 0 1rem 0'}}>🎯 Exactly right!</h4>
                                            <p style={{color: '#e2e8f0', margin: 0, lineHeight: '1.7'}}>
                                                This is called having <strong style={{color: '#fbbf24'}}>"skin in the game"</strong>.
                                                <br/><br/>
                                                If you try to cheat (like approving fake transactions), the network will detect it and <strong style={{color: '#ef4444'}}>DESTROY part of your stake</strong>.
                                                <br/><br/>
                                                Would YOU risk losing $100,000 to try to steal $50?
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => { setChapterStep(1); setShowReveal(false); }}
                                            style={{
                                                marginTop: '1rem',
                                                width: '100%',
                                                padding: '1.25rem',
                                                background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                                border: 'none',
                                                borderRadius: '0.75rem',
                                                color: 'white',
                                                fontSize: '1.1rem',
                                                fontWeight: 'bold',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            Show me how this works →
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                        
                        {chapterStep === 1 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <h3 style={{color: '#f8fafc', marginTop: 0}}>⚖️ The Risk/Reward Calculation</h3>
                                
                                <p style={{color: '#cbd5e1', fontSize: '1.05rem'}}>
                                    Let's look at this from a cheater's perspective:
                                </p>
                                
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: '1fr 1fr',
                                    gap: '1rem',
                                    margin: '1.5rem 0'
                                }}>
                                    <div style={{
                                        padding: '1.5rem',
                                        background: 'rgba(239, 68, 68, 0.1)',
                                        borderRadius: '0.75rem',
                                        border: '2px solid rgba(239, 68, 68, 0.4)'
                                    }}>
                                        <div style={{color: '#fca5a5', fontWeight: 'bold', marginBottom: '1rem'}}>
                                            😈 If Mallory Cheats:
                                        </div>
                                        <div style={{color: '#fed7aa', fontSize: '0.95rem', lineHeight: '1.6'}}>
                                            • Could gain: <span style={{color: '#fbbf24'}}>~$1,000</span> (fake tx)
                                            <br/>
                                            • Will lose: <span style={{color: '#ef4444'}}>$5,000+</span> (5% of stake)
                                            <br/>
                                            • Probability caught: <span style={{color: '#ef4444'}}>~100%</span>
                                            <br/><br/>
                                            <strong>Expected value: NEGATIVE</strong>
                                        </div>
                                    </div>
                                    
                                    <div style={{
                                        padding: '1.5rem',
                                        background: 'rgba(16, 185, 129, 0.1)',
                                        borderRadius: '0.75rem',
                                        border: '2px solid rgba(16, 185, 129, 0.4)'
                                    }}>
                                        <div style={{color: '#86efac', fontWeight: 'bold', marginBottom: '1rem'}}>
                                            😇 If Mallory is Honest:
                                        </div>
                                        <div style={{color: '#d1fae5', fontSize: '0.95rem', lineHeight: '1.6'}}>
                                            • Earns: <span style={{color: '#22c55e'}}>~5% APY</span> on stake
                                            <br/>
                                            • Risk: <span style={{color: '#22c55e'}}>Near zero</span>
                                            <br/>
                                            • Keep: <span style={{color: '#22c55e'}}>All stake + rewards</span>
                                            <br/><br/>
                                            <strong>Expected value: POSITIVE</strong>
                                        </div>
                                    </div>
                                </div>
                                
                                <div style={{
                                    padding: '1.5rem',
                                    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(167, 139, 250, 0.1) 100%)',
                                    borderRadius: '0.75rem',
                                    border: '2px solid rgba(139, 92, 246, 0.4)',
                                    textAlign: 'center'
                                }}>
                                    <div style={{fontSize: '2rem', marginBottom: '0.5rem'}}>💡</div>
                                    <p style={{color: '#c4b5fd', fontSize: '1.1rem', fontWeight: 'bold', margin: 0}}>
                                        Being honest is the PROFITABLE choice.
                                    </p>
                                    <p style={{color: '#a78bfa', fontSize: '0.9rem', margin: '0.5rem 0 0 0'}}>
                                        This is the economic security model of Proof of Stake.
                                    </p>
                                </div>
                                
                                <button
                                    onClick={nextChapter}
                                    style={{
                                        marginTop: '1.5rem',
                                        width: '100%',
                                        padding: '1.25rem',
                                        background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                        border: 'none',
                                        borderRadius: '0.75rem',
                                        color: 'white',
                                        fontSize: '1.1rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >
                                    Got it! But who gets to propose blocks? →
                                </button>
                            </div>
                        )}
                    </div>
                )}
                
                {/* ========== CHAPTER 4: FAIR SELECTION ========== */}
                {chapter === 4 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(59, 130, 246, 0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>🎲</div>
                            <h1 style={{color: '#f8fafc', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 4: Fair Selection
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                Who gets to create the next block?
                            </p>
                        </div>
                        
                        {chapterStep === 0 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <p style={{color: '#cbd5e1', fontSize: '1.1rem', lineHeight: '1.7', marginTop: 0}}>
                                    Every 12 seconds, Ethereum needs to pick ONE validator to create the next block.
                                    <br/><br/>
                                    <strong style={{color: '#60a5fa'}}>How should we pick?</strong>
                                </p>
                                
                                <div style={{
                                    background: 'rgba(0,0,0,0.3)',
                                    padding: '1.5rem',
                                    borderRadius: '0.75rem',
                                    margin: '1.5rem 0'
                                }}>
                                    <h4 style={{color: '#94a3b8', margin: '0 0 1rem 0'}}>🎯 Make a prediction:</h4>
                                    <p style={{color: '#e2e8f0', margin: '0 0 1rem 0'}}>
                                        If we pick based on stake, who do you think gets chosen MOST often?
                                    </p>
                                    
                                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem'}}>
                                        {validators.filter(v => v.name !== 'Mallory').map(v => (
                                            <button
                                                key={v.id}
                                                onClick={() => {
                                                    setUserChoices({...userChoices, prediction: v.name});
                                                    setShowReveal(true);
                                                }}
                                                disabled={showReveal}
                                                style={{
                                                    padding: '1rem',
                                                    background: userChoices.prediction === v.name ? `${v.color}30` : 'rgba(51, 65, 85, 0.5)',
                                                    border: `2px solid ${userChoices.prediction === v.name ? v.color : '#475569'}`,
                                                    borderRadius: '0.75rem',
                                                    cursor: showReveal ? 'default' : 'pointer',
                                                    textAlign: 'center'
                                                }}
                                            >
                                                <div style={{fontSize: '1.5rem'}}>{v.emoji}</div>
                                                <div style={{color: '#e2e8f0', fontWeight: 'bold'}}>{v.name}</div>
                                                <div style={{color: v.color, fontSize: '0.9rem'}}>{v.stake} ETH</div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                
                                {showReveal && (
                                    <div style={{
                                        padding: '1.5rem',
                                        background: 'rgba(16, 185, 129, 0.15)',
                                        borderRadius: '0.75rem',
                                        border: '2px solid #10b981',
                                        marginBottom: '1rem'
                                    }}>
                                        <h4 style={{color: '#86efac', margin: '0 0 1rem 0'}}>
                                            {userChoices.prediction === 'Dave' ? '🎯 Perfect!' : '🤔 Close!'} Here's how it works:
                                        </h4>
                                        <p style={{color: '#e2e8f0', margin: 0, lineHeight: '1.7'}}>
                                            Selection is <strong style={{color: '#fbbf24'}}>weighted by stake</strong>, but still <strong style={{color: '#60a5fa'}}>random</strong>.
                                            <br/><br/>
                                            Think of it like a lottery where you get more tickets if you have more stake:
                                        </p>
                                        
                                        <div style={{marginTop: '1rem'}}>
                                            {validators.filter(v => v.name !== 'Mallory').map(v => {
                                                const totalStake = 32 + 64 + 16 + 128;
                                                const pct = (v.stake / totalStake * 100).toFixed(1);
                                                return (
                                                    <div key={v.id} style={{marginBottom: '0.75rem'}}>
                                                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px'}}>
                                                            <span style={{color: '#e2e8f0'}}>{v.emoji} {v.name}</span>
                                                            <span style={{color: v.color, fontWeight: 'bold'}}>{pct}% chance</span>
                                                        </div>
                                                        <div style={{
                                                            height: '12px',
                                                            background: 'rgba(0,0,0,0.3)',
                                                            borderRadius: '6px',
                                                            overflow: 'hidden'
                                                        }}>
                                                            <div style={{
                                                                width: `${pct}%`,
                                                                height: '100%',
                                                                background: v.color,
                                                                borderRadius: '6px'
                                                            }}></div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                        
                                        <p style={{color: '#86efac', marginTop: '1rem', fontSize: '0.95rem'}}>
                                            <strong>🐋 Dave</strong> has the most stake (128 ETH), so he gets selected ~53% of the time.
                                            But even <strong>👩‍🔬 Carol</strong> with just 16 ETH still gets ~7% of blocks!
                                        </p>
                                    </div>
                                )}
                                
                                {showReveal && (
                                    <button
                                        onClick={() => { setChapterStep(1); setShowReveal(false); }}
                                        style={{
                                            width: '100%',
                                            padding: '1.25rem',
                                            background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                            border: 'none',
                                            borderRadius: '0.75rem',
                                            color: 'white',
                                            fontSize: '1.1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        Let me try the selection! →
                                    </button>
                                )}
                            </div>
                        )}
                        
                        {chapterStep === 1 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <h3 style={{color: '#f8fafc', marginTop: 0}}>🎰 Try It: Run the Selection</h3>
                                <p style={{color: '#94a3b8'}}>Click "Select Proposer" multiple times and watch who gets chosen:</p>
                                
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(4, 1fr)',
                                    gap: '1rem',
                                    margin: '1.5rem 0'
                                }}>
                                    {validators.filter(v => v.name !== 'Mallory').map(v => (
                                        <div key={v.id} style={{
                                            padding: '1rem',
                                            background: animationPhase === v.id ? `${v.color}40` : 'rgba(0,0,0,0.2)',
                                            borderRadius: '0.75rem',
                                            border: `3px solid ${animationPhase === v.id ? v.color : 'transparent'}`,
                                            textAlign: 'center',
                                            transition: 'all 0.3s',
                                            transform: animationPhase === v.id ? 'scale(1.05)' : 'scale(1)'
                                        }}>
                                            <div style={{fontSize: '2rem'}}>{v.emoji}</div>
                                            <div style={{color: '#e2e8f0', fontWeight: 'bold'}}>{v.name}</div>
                                            <div style={{color: v.color}}>{v.blocksProposed} blocks</div>
                                        </div>
                                    ))}
                                </div>
                                
                                <button
                                    onClick={() => {
                                        // Weighted random selection
                                        const active = validators.filter(v => v.name !== 'Mallory');
                                        const total = active.reduce((s, v) => s + v.stake, 0);
                                        const rand = Math.random() * total;
                                        let cum = 0;
                                        let selected = active[0];
                                        for (let v of active) {
                                            cum += v.stake;
                                            if (rand < cum) { selected = v; break; }
                                        }
                                        setAnimationPhase(selected.id);
                                        setValidators(prev => prev.map(v => 
                                            v.id === selected.id ? {...v, blocksProposed: v.blocksProposed + 1} : v
                                        ));
                                    }}
                                    style={{
                                        width: '100%',
                                        padding: '1.25rem',
                                        background: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)',
                                        border: 'none',
                                        borderRadius: '0.75rem',
                                        color: 'white',
                                        fontSize: '1.1rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >
                                    🎲 Select Proposer
                                </button>
                                
                                {validators.reduce((s, v) => s + v.blocksProposed, 0) >= 5 && (
                                    <div style={{
                                        marginTop: '1.5rem',
                                        padding: '1.5rem',
                                        background: 'rgba(16, 185, 129, 0.15)',
                                        borderRadius: '0.75rem',
                                        border: '2px solid #10b981'
                                    }}>
                                        <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0'}}>🎉 You see the pattern!</h4>
                                        <p style={{color: '#e2e8f0', margin: 0}}>
                                            Dave gets picked most often, but it's not guaranteed. This balance of 
                                            "more stake = more chances" while "still random" is key to keeping 
                                            the network fair AND secure.
                                        </p>
                                        <button
                                            onClick={nextChapter}
                                            style={{
                                                marginTop: '1rem',
                                                width: '100%',
                                                padding: '1rem',
                                                background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                                border: 'none',
                                                borderRadius: '0.75rem',
                                                color: 'white',
                                                fontSize: '1rem',
                                                fontWeight: 'bold',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            Next: What happens to cheaters? →
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
                
                {/* ========== CHAPTER 5: CATCHING CHEATERS ========== */}
                {chapter === 5 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #450a0a 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(239, 68, 68, 0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>⚔️</div>
                            <h1 style={{color: '#fca5a5', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 5: Catching Cheaters
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                Watch what happens when Mallory breaks the rules
                            </p>
                        </div>
                        
                        {chapterStep === 0 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '1rem',
                                    padding: '1.5rem',
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    borderRadius: '0.75rem',
                                    border: '2px solid rgba(239, 68, 68, 0.4)',
                                    marginBottom: '1.5rem'
                                }}>
                                    <div style={{fontSize: '3rem'}}>😈</div>
                                    <div>
                                        <div style={{color: '#fca5a5', fontWeight: 'bold', fontSize: '1.1rem'}}>
                                            Mallory is about to cheat!
                                        </div>
                                        <div style={{color: '#fed7aa', fontSize: '0.95rem'}}>
                                            She's going to "double sign" — creating two different blocks for the same slot.
                                            This is like trying to spend the same $100 twice.
                                        </div>
                                    </div>
                                </div>
                                
                                <h3 style={{color: '#f8fafc'}}>🤔 Before we watch, predict what happens:</h3>
                                
                                <div style={{display: 'grid', gap: '0.75rem', marginTop: '1rem'}}>
                                    {[
                                        { id: 'nothing', text: 'Nothing — nobody notices', icon: '🤷' },
                                        { id: 'warning', text: 'She gets a warning', icon: '⚠️' },
                                        { id: 'slash', text: 'She loses part of her stake automatically', icon: '💸' },
                                        { id: 'ban', text: 'Admins ban her account', icon: '🚫' }
                                    ].map(opt => (
                                        <button
                                            key={opt.id}
                                            onClick={() => {
                                                setUserChoices({...userChoices, slashPrediction: opt.id});
                                                setShowReveal(true);
                                            }}
                                            disabled={showReveal}
                                            style={{
                                                padding: '1rem',
                                                background: userChoices.slashPrediction === opt.id 
                                                    ? opt.id === 'slash' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'
                                                    : 'rgba(51, 65, 85, 0.5)',
                                                border: userChoices.slashPrediction === opt.id
                                                    ? opt.id === 'slash' ? '2px solid #10b981' : '2px solid #ef4444'
                                                    : '2px solid #475569',
                                                borderRadius: '0.75rem',
                                                cursor: showReveal ? 'default' : 'pointer',
                                                textAlign: 'left',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '1rem',
                                                color: '#e2e8f0'
                                            }}
                                        >
                                            <span style={{fontSize: '1.5rem'}}>{opt.icon}</span>
                                            {opt.text}
                                        </button>
                                    ))}
                                </div>
                                
                                {showReveal && (
                                    <div style={{marginTop: '1.5rem'}}>
                                        <div style={{
                                            padding: '1.5rem',
                                            background: userChoices.slashPrediction === 'slash' 
                                                ? 'rgba(16, 185, 129, 0.15)' 
                                                : 'rgba(251, 191, 36, 0.15)',
                                            borderRadius: '0.75rem',
                                            border: `2px solid ${userChoices.slashPrediction === 'slash' ? '#10b981' : '#f59e0b'}`
                                        }}>
                                            <h4 style={{color: userChoices.slashPrediction === 'slash' ? '#86efac' : '#fcd34d', margin: '0 0 1rem 0'}}>
                                                {userChoices.slashPrediction === 'slash' ? '🎯 Exactly!' : '💡 Close — here\'s what actually happens:'}
                                            </h4>
                                            <p style={{color: '#e2e8f0', margin: 0, lineHeight: '1.7'}}>
                                                The network detects the cheating <strong>automatically</strong> and <strong style={{color: '#ef4444'}}>burns 5% of Mallory's stake</strong>.
                                                <br/><br/>
                                                <strong>Key insight:</strong> There are NO admins. The punishment is enforced by the protocol itself — by math and code, not people.
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => { setChapterStep(1); setShowReveal(false); }}
                                            style={{
                                                marginTop: '1rem',
                                                width: '100%',
                                                padding: '1.25rem',
                                                background: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)',
                                                border: 'none',
                                                borderRadius: '0.75rem',
                                                color: 'white',
                                                fontSize: '1.1rem',
                                                fontWeight: 'bold',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            🎬 Watch Mallory get slashed →
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                        
                        {chapterStep === 1 && (
                            <div style={{
                                background: '#1e293b',
                                borderRadius: '1rem',
                                padding: '2rem',
                                border: '1px solid #334155'
                            }}>
                                <h3 style={{color: '#fca5a5', marginTop: 0}}>⚔️ Live Slashing Demonstration</h3>
                                
                                {/* This reuses the slashing scenario from the attacks module */}
                                {!slashingScenario.active ? (
                                    <div>
                                        <div style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '1rem',
                                            padding: '1.5rem',
                                            background: 'rgba(239, 68, 68, 0.1)',
                                            borderRadius: '0.75rem',
                                            marginBottom: '1.5rem'
                                        }}>
                                            <div style={{
                                                width: '60px',
                                                height: '60px',
                                                borderRadius: '50%',
                                                background: '#ef4444',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: '2rem'
                                            }}>
                                                😈
                                            </div>
                                            <div>
                                                <div style={{color: '#fca5a5', fontWeight: 'bold', fontSize: '1.1rem'}}>Mallory</div>
                                                <div style={{color: '#e2e8f0'}}>Current stake: <strong>32 ETH</strong></div>
                                                <div style={{color: '#f87171', fontSize: '0.9rem'}}>About to attempt double-signing...</div>
                                            </div>
                                        </div>
                                        
                                        <button
                                            onClick={() => runSlashingScenario(5, 'double-sign')}
                                            style={{
                                                width: '100%',
                                                padding: '1.5rem',
                                                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                                                border: 'none',
                                                borderRadius: '0.75rem',
                                                color: 'white',
                                                fontSize: '1.2rem',
                                                fontWeight: 'bold',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            😈 Make Mallory Cheat →
                                        </button>
                                    </div>
                                ) : (
                                    <div>
                                        {/* Show slashing scenario progress */}
                                        <div style={{
                                            background: 'rgba(0,0,0,0.3)',
                                            borderRadius: '0.75rem',
                                            padding: '1.5rem',
                                            marginBottom: '1.5rem'
                                        }}>
                                            {/* Progress steps */}
                                            <div style={{display: 'flex', justifyContent: 'space-around', marginBottom: '1.5rem'}}>
                                                {[
                                                    { step: 1, label: 'Cheating', icon: '😈' },
                                                    { step: 2, label: 'Detected', icon: '🔍' },
                                                    { step: 3, label: 'Slashed', icon: '⚔️' }
                                                ].map(s => (
                                                    <div key={s.step} style={{textAlign: 'center'}}>
                                                        <div style={{
                                                            width: '50px',
                                                            height: '50px',
                                                            borderRadius: '50%',
                                                            background: slashingScenario.step >= s.step 
                                                                ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                                                                : '#334155',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontSize: '1.5rem',
                                                            margin: '0 auto 0.5rem',
                                                            border: slashingScenario.step >= s.step ? '3px solid #fca5a5' : '3px solid #475569'
                                                        }}>
                                                            {slashingScenario.step >= s.step ? s.icon : s.step}
                                                        </div>
                                                        <div style={{color: slashingScenario.step >= s.step ? '#fca5a5' : '#64748b', fontSize: '0.85rem'}}>
                                                            {s.label}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            
                                            {/* Detection progress bar */}
                                            {slashingScenario.step >= 1 && slashingScenario.step < 3 && (
                                                <div style={{marginBottom: '1rem'}}>
                                                    <div style={{display: 'flex', justifyContent: 'space-between', color: '#f59e0b', fontSize: '0.9rem', marginBottom: '0.25rem'}}>
                                                        <span>🔍 Network detecting violation...</span>
                                                        <span>{slashingScenario.detectionProgress}%</span>
                                                    </div>
                                                    <div style={{height: '8px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', overflow: 'hidden'}}>
                                                        <div style={{
                                                            width: `${slashingScenario.detectionProgress}%`,
                                                            height: '100%',
                                                            background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                                                            transition: 'width 0.2s'
                                                        }}></div>
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {/* Event log */}
                                            <div style={{
                                                background: 'rgba(0,0,0,0.4)',
                                                borderRadius: '0.5rem',
                                                padding: '1rem',
                                                fontFamily: 'monospace',
                                                fontSize: '0.85rem',
                                                maxHeight: '150px',
                                                overflowY: 'auto'
                                            }}>
                                                {slashingScenario.eventLog.map((event, idx) => (
                                                    <div key={idx} style={{marginBottom: '0.75rem'}}>
                                                        <div style={{
                                                            color: event.type === 'slashed' ? '#ef4444' : 
                                                                   event.type === 'detected' ? '#fbbf24' : '#f59e0b',
                                                            fontWeight: 'bold'
                                                        }}>
                                                            {event.message}
                                                        </div>
                                                        <div style={{color: '#94a3b8', fontSize: '0.8rem'}}>{event.details}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        
                                        {slashingScenario.step >= 3 && (
                                            <div style={{
                                                padding: '1.5rem',
                                                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(34, 197, 94, 0.1) 100%)',
                                                borderRadius: '0.75rem',
                                                border: '2px solid #10b981'
                                            }}>
                                                <h4 style={{color: '#86efac', margin: '0 0 1rem 0'}}>🎓 What You Just Witnessed:</h4>
                                                <ul style={{color: '#e2e8f0', margin: 0, paddingLeft: '1.25rem', lineHeight: '1.8'}}>
                                                    <li>Mallory tried to double-sign (create conflicting blocks)</li>
                                                    <li>Other validators <strong>automatically detected</strong> the conflicting signatures</li>
                                                    <li>The protocol <strong>burned 5% of her stake</strong> (~1.6 ETH)</li>
                                                    <li><strong>No human intervention needed</strong> — pure math and code</li>
                                                </ul>
                                                
                                                <div style={{
                                                    marginTop: '1rem',
                                                    padding: '1rem',
                                                    background: 'rgba(139, 92, 246, 0.15)',
                                                    borderRadius: '0.5rem',
                                                    border: '1px solid rgba(139, 92, 246, 0.4)'
                                                }}>
                                                    <p style={{color: '#c4b5fd', margin: 0, fontSize: '0.95rem'}}>
                                                        💡 <strong>This is trustless security.</strong> We don't need to trust that validators are good people — 
                                                        we've made cheating so expensive that rational actors won't do it.
                                                    </p>
                                                </div>
                                                
                                                <button
                                                    onClick={() => { resetSlashingScenario(); nextChapter(); }}
                                                    style={{
                                                        marginTop: '1rem',
                                                        width: '100%',
                                                        padding: '1.25rem',
                                                        background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                                        border: 'none',
                                                        borderRadius: '0.75rem',
                                                        color: 'white',
                                                        fontSize: '1.1rem',
                                                        fontWeight: 'bold',
                                                        cursor: 'pointer'
                                                    }}
                                                >
                                                    Amazing! How do validators agree? →
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
                
                {/* ========== CHAPTER 6: AGREEMENT ========== */}
                {chapter === 6 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(16, 185, 129, 0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>🤝</div>
                            <h1 style={{color: '#f8fafc', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 6: Agreement (Consensus)
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                How thousands of validators agree on the truth
                            </p>
                        </div>
                        
                        <div style={{
                            background: '#1e293b',
                            borderRadius: '1rem',
                            padding: '2rem',
                            border: '1px solid #334155'
                        }}>
                            <p style={{color: '#cbd5e1', fontSize: '1.1rem', lineHeight: '1.7', marginTop: 0}}>
                                You've learned how validators are selected and punished. But how do they all <strong style={{color: '#60a5fa'}}>agree on the same truth</strong>?
                            </p>
                            
                            <div style={{
                                background: 'rgba(16, 185, 129, 0.1)',
                                padding: '1.5rem',
                                borderRadius: '0.75rem',
                                border: '2px solid rgba(16, 185, 129, 0.4)',
                                margin: '1.5rem 0'
                            }}>
                                <h4 style={{color: '#86efac', margin: '0 0 1rem 0'}}>🗳️ The Simple Answer: Voting</h4>
                                <ol style={{color: '#e2e8f0', margin: 0, paddingLeft: '1.5rem', lineHeight: '1.8'}}>
                                    <li>A validator proposes a new block</li>
                                    <li>Other validators <strong>vote</strong> ("attest") that they agree with it</li>
                                    <li>When <strong style={{color: '#fbbf24'}}>2/3 of all staked ETH</strong> votes for a block, it becomes "justified"</li>
                                    <li>After two justified blocks in a row, the first becomes <strong style={{color: '#22c55e'}}>"finalized"</strong> — permanent and unchangeable</li>
                                </ol>
                            </div>
                            
                            {/* Visual representation */}
                            <div style={{
                                background: 'rgba(0,0,0,0.3)',
                                padding: '1.5rem',
                                borderRadius: '0.75rem',
                                marginBottom: '1.5rem'
                            }}>
                                <h4 style={{color: '#94a3b8', margin: '0 0 1rem 0'}}>📊 Finality in Action:</h4>
                                <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center', justifyContent: 'center'}}>
                                    {['Block 1', 'Block 2', 'Block 3', 'Block 4'].map((block, idx) => (
                                        <div key={idx} style={{display: 'flex', alignItems: 'center'}}>
                                            <div style={{
                                                padding: '1rem',
                                                background: idx < 2 ? 'linear-gradient(135deg, #10b981, #34d399)' :
                                                            idx === 2 ? 'linear-gradient(135deg, #f59e0b, #fbbf24)' :
                                                            '#334155',
                                                borderRadius: '0.5rem',
                                                textAlign: 'center',
                                                minWidth: '80px'
                                            }}>
                                                <div style={{color: 'white', fontWeight: 'bold', fontSize: '0.85rem'}}>{block}</div>
                                                <div style={{color: 'rgba(255,255,255,0.8)', fontSize: '0.7rem'}}>
                                                    {idx < 2 ? '✅ Finalized' : idx === 2 ? '⏳ Justified' : '🔄 Pending'}
                                                </div>
                                            </div>
                                            {idx < 3 && <div style={{color: '#64748b', margin: '0 0.25rem'}}>→</div>}
                                        </div>
                                    ))}
                                </div>
                                <p style={{color: '#94a3b8', textAlign: 'center', marginTop: '1rem', marginBottom: 0, fontSize: '0.9rem'}}>
                                    Finalized blocks are <strong>permanent</strong>. Even if every validator wanted to, they couldn't change them.
                                </p>
                            </div>
                            
                            <div style={{
                                padding: '1.5rem',
                                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(167, 139, 250, 0.1) 100%)',
                                borderRadius: '0.75rem',
                                border: '2px solid rgba(139, 92, 246, 0.4)'
                            }}>
                                <h4 style={{color: '#c4b5fd', margin: '0 0 1rem 0'}}>💡 Why This Matters to YOU:</h4>
                                <p style={{color: '#e2e8f0', margin: 0, lineHeight: '1.7'}}>
                                    When you send crypto to someone and it gets <strong style={{color: '#22c55e'}}>"finalized"</strong>:
                                    <br/><br/>
                                    • It's as permanent as if you handed them physical cash<br/>
                                    • No bank can reverse it<br/>
                                    • No government can undo it<br/>
                                    • Not even the validators can change it<br/>
                                    <br/>
                                    <strong>This is true digital ownership.</strong>
                                </p>
                            </div>
                            
                            <button
                                onClick={nextChapter}
                                style={{
                                    marginTop: '1.5rem',
                                    width: '100%',
                                    padding: '1.25rem',
                                    background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                    border: 'none',
                                    borderRadius: '0.75rem',
                                    color: 'white',
                                    fontSize: '1.1rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer'
                                }}
                            >
                                📝 Ready for the Final Quiz! →
                            </button>
                        </div>
                    </div>
                )}
                
                {/* ========== CHAPTER 7: FINAL QUIZ ========== */}
                {chapter === 7 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(139, 92, 246, 0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>📝</div>
                            <h1 style={{color: '#f8fafc', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 7: Final Quiz
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                Test your knowledge - 15 questions randomly selected
                            </p>
                        </div>
                        
                        <div style={{
                            background: '#1e293b',
                            borderRadius: '1rem',
                            padding: '2rem',
                            border: '1px solid #334155'
                        }}>
                            {!quizSubmitted ? (
                                <>
                                    {/* Progress indicator */}
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        marginBottom: '1.5rem',
                                        padding: '1rem',
                                        background: 'rgba(0,0,0,0.2)',
                                        borderRadius: '0.75rem'
                                    }}>
                                        <div style={{color: '#94a3b8'}}>
                                            Question <strong style={{color: '#a78bfa'}}>{currentQuizIndex + 1}</strong> of <strong>{quizQuestions.length}</strong>
                                        </div>
                                        <div style={{display: 'flex', gap: '4px'}}>
                                            {quizQuestions.map((_, idx) => (
                                                <div key={idx} style={{
                                                    width: '24px',
                                                    height: '8px',
                                                    borderRadius: '4px',
                                                    background: quizAnswers[idx] !== undefined 
                                                        ? '#8b5cf6' 
                                                        : idx === currentQuizIndex 
                                                            ? '#475569'
                                                            : '#1e293b',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s'
                                                }}
                                                onClick={() => setCurrentQuizIndex(idx)}
                                                />
                                            ))}
                                        </div>
                                        <div style={{
                                            padding: '0.5rem 1rem',
                                            background: 'rgba(139, 92, 246, 0.2)',
                                            borderRadius: '20px',
                                            fontSize: '0.85rem',
                                            color: '#a78bfa'
                                        }}>
                                            {Object.keys(quizAnswers).length}/15 answered
                                        </div>
                                    </div>
                                    
                                    {/* Current Question */}
                                    {quizQuestions[currentQuizIndex] && (
                                        <div>
                                            <div style={{
                                                padding: '0.5rem 1rem',
                                                background: 'rgba(59, 130, 246, 0.1)',
                                                borderRadius: '20px',
                                                display: 'inline-block',
                                                marginBottom: '1rem',
                                                fontSize: '0.8rem',
                                                color: '#60a5fa',
                                                textTransform: 'uppercase'
                                            }}>
                                                {quizQuestions[currentQuizIndex].category}
                                            </div>
                                            
                                            <h3 style={{
                                                color: '#f8fafc',
                                                fontSize: '1.3rem',
                                                marginTop: 0,
                                                marginBottom: '1.5rem',
                                                lineHeight: '1.5'
                                            }}>
                                                {quizQuestions[currentQuizIndex].q}
                                            </h3>
                                            
                                            <div style={{display: 'grid', gap: '0.75rem'}}>
                                                {quizQuestions[currentQuizIndex].a.map((answer, idx) => (
                                                    <button
                                                        key={idx}
                                                        onClick={() => {
                                                            setQuizAnswers({...quizAnswers, [currentQuizIndex]: idx});
                                                        }}
                                                        style={{
                                                            padding: '1rem 1.25rem',
                                                            background: quizAnswers[currentQuizIndex] === idx 
                                                                ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(167, 139, 250, 0.2) 100%)'
                                                                : 'rgba(51, 65, 85, 0.5)',
                                                            border: quizAnswers[currentQuizIndex] === idx 
                                                                ? '2px solid #8b5cf6'
                                                                : '2px solid #475569',
                                                            borderRadius: '0.75rem',
                                                            cursor: 'pointer',
                                                            textAlign: 'left',
                                                            color: quizAnswers[currentQuizIndex] === idx ? '#e2e8f0' : '#cbd5e1',
                                                            fontSize: '1rem',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '1rem',
                                                            transition: 'all 0.2s'
                                                        }}
                                                    >
                                                        <div style={{
                                                            width: '28px',
                                                            height: '28px',
                                                            borderRadius: '50%',
                                                            background: quizAnswers[currentQuizIndex] === idx ? '#8b5cf6' : '#334155',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontWeight: 'bold',
                                                            fontSize: '0.9rem',
                                                            flexShrink: 0
                                                        }}>
                                                            {String.fromCharCode(65 + idx)}
                                                        </div>
                                                        {answer}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Navigation */}
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        marginTop: '2rem',
                                        gap: '1rem'
                                    }}>
                                        <button
                                            onClick={() => setCurrentQuizIndex(Math.max(0, currentQuizIndex - 1))}
                                            disabled={currentQuizIndex === 0}
                                            style={{
                                                padding: '1rem 1.5rem',
                                                background: currentQuizIndex === 0 ? '#334155' : 'rgba(59, 130, 246, 0.2)',
                                                border: '1px solid #3b82f6',
                                                borderRadius: '0.75rem',
                                                color: currentQuizIndex === 0 ? '#64748b' : '#93c5fd',
                                                cursor: currentQuizIndex === 0 ? 'not-allowed' : 'pointer',
                                                fontWeight: 'bold'
                                            }}
                                        >
                                            ← Previous
                                        </button>
                                        
                                        {currentQuizIndex < quizQuestions.length - 1 ? (
                                            <button
                                                onClick={() => setCurrentQuizIndex(currentQuizIndex + 1)}
                                                style={{
                                                    padding: '1rem 1.5rem',
                                                    background: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)',
                                                    border: 'none',
                                                    borderRadius: '0.75rem',
                                                    color: 'white',
                                                    cursor: 'pointer',
                                                    fontWeight: 'bold'
                                                }}
                                            >
                                                Next →
                                            </button>
                                        ) : (
                                            <button
                                                onClick={submitQuiz}
                                                disabled={Object.keys(quizAnswers).length < 15}
                                                style={{
                                                    padding: '1rem 2rem',
                                                    background: Object.keys(quizAnswers).length < 15 
                                                        ? '#334155' 
                                                        : 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                                    border: 'none',
                                                    borderRadius: '0.75rem',
                                                    color: Object.keys(quizAnswers).length < 15 ? '#64748b' : 'white',
                                                    cursor: Object.keys(quizAnswers).length < 15 ? 'not-allowed' : 'pointer',
                                                    fontWeight: 'bold',
                                                    fontSize: '1rem'
                                                }}
                                            >
                                                {Object.keys(quizAnswers).length < 15 
                                                    ? `Answer all questions (${Object.keys(quizAnswers).length}/15)`
                                                    : '✅ Submit Quiz'}
                                            </button>
                                        )}
                                    </div>
                                </>
                            ) : (
                                /* Quiz Results */
                                <div>
                                    <div style={{
                                        textAlign: 'center',
                                        padding: '2rem',
                                        background: quizScore >= 12 
                                            ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(34, 197, 94, 0.1) 100%)'
                                            : quizScore >= 9
                                                ? 'linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(245, 158, 11, 0.1) 100%)'
                                                : 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%)',
                                        borderRadius: '1rem',
                                        border: `2px solid ${quizScore >= 12 ? '#10b981' : quizScore >= 9 ? '#f59e0b' : '#ef4444'}`,
                                        marginBottom: '2rem'
                                    }}>
                                        <div style={{fontSize: '4rem', marginBottom: '1rem'}}>
                                            {quizScore >= 12 ? '🏆' : quizScore >= 9 ? '👍' : '📚'}
                                        </div>
                                        <h2 style={{
                                            color: quizScore >= 12 ? '#86efac' : quizScore >= 9 ? '#fcd34d' : '#fca5a5',
                                            margin: '0 0 0.5rem 0',
                                            fontSize: '2rem'
                                        }}>
                                            {quizScore >= 12 ? 'Excellent!' : quizScore >= 9 ? 'Good Job!' : 'Keep Learning!'}
                                        </h2>
                                        <p style={{color: '#e2e8f0', fontSize: '1.2rem', margin: 0}}>
                                            You scored <strong style={{color: quizScore >= 12 ? '#22c55e' : quizScore >= 9 ? '#f59e0b' : '#ef4444'}}>{quizScore}</strong> out of <strong>15</strong> ({Math.round(quizScore/15*100)}%)
                                        </p>
                                        <p style={{color: '#94a3b8', margin: '1rem 0 0 0', fontSize: '0.95rem'}}>
                                            {quizScore >= 12 
                                                ? 'You have a strong understanding of Proof of Stake!' 
                                                : quizScore >= 9 
                                                    ? 'You understand the basics well. Review the topics you missed.' 
                                                    : 'Consider reviewing the chapters before trying again.'}
                                        </p>
                                    </div>
                                    
                                    {/* Review Answers */}
                                    <h3 style={{color: '#f8fafc', marginBottom: '1rem'}}>📋 Review Your Answers:</h3>
                                    <div style={{display: 'grid', gap: '1rem', maxHeight: '400px', overflowY: 'auto', paddingRight: '0.5rem'}}>
                                        {quizQuestions.map((q, idx) => {
                                            const isCorrect = quizAnswers[idx] === q.correct;
                                            return (
                                                <div key={idx} style={{
                                                    padding: '1rem',
                                                    background: isCorrect ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                                                    borderRadius: '0.75rem',
                                                    border: `1px solid ${isCorrect ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                                                }}>
                                                    <div style={{display: 'flex', alignItems: 'flex-start', gap: '1rem'}}>
                                                        <div style={{
                                                            width: '28px',
                                                            height: '28px',
                                                            borderRadius: '50%',
                                                            background: isCorrect ? '#10b981' : '#ef4444',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontSize: '1rem',
                                                            flexShrink: 0
                                                        }}>
                                                            {isCorrect ? '✓' : '✗'}
                                                        </div>
                                                        <div style={{flex: 1}}>
                                                            <div style={{color: '#e2e8f0', marginBottom: '0.5rem', fontSize: '0.95rem'}}>
                                                                <strong>Q{idx + 1}:</strong> {q.q}
                                                            </div>
                                                            <div style={{fontSize: '0.9rem'}}>
                                                                <span style={{color: '#94a3b8'}}>Your answer: </span>
                                                                <span style={{color: isCorrect ? '#86efac' : '#fca5a5'}}>
                                                                    {q.a[quizAnswers[idx]]}
                                                                </span>
                                                            </div>
                                                            {!isCorrect && (
                                                                <div style={{fontSize: '0.9rem', marginTop: '0.25rem'}}>
                                                                    <span style={{color: '#94a3b8'}}>Correct: </span>
                                                                    <span style={{color: '#86efac'}}>{q.a[q.correct]}</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    
                                    {/* Action Buttons */}
                                    <div style={{display: 'flex', gap: '1rem', marginTop: '2rem'}}>
                                        <button
                                            onClick={generateQuiz}
                                            style={{
                                                flex: 1,
                                                padding: '1rem',
                                                background: 'rgba(59, 130, 246, 0.2)',
                                                border: '1px solid #3b82f6',
                                                borderRadius: '0.75rem',
                                                color: '#93c5fd',
                                                cursor: 'pointer',
                                                fontWeight: 'bold'
                                            }}
                                        >
                                            🔄 Try New Questions
                                        </button>
                                        {quizScore >= 9 && (
                                            <button
                                                onClick={nextChapter}
                                                style={{
                                                    flex: 1,
                                                    padding: '1rem',
                                                    background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                                    border: 'none',
                                                    borderRadius: '0.75rem',
                                                    color: 'white',
                                                    cursor: 'pointer',
                                                    fontWeight: 'bold'
                                                }}
                                            >
                                                🎓 Claim Your Certificate →
                                            </button>
                                        )}
                                    </div>
                                    
                                    {quizScore < 9 && (
                                        <div style={{
                                            marginTop: '1.5rem',
                                            padding: '1rem',
                                            background: 'rgba(251, 191, 36, 0.1)',
                                            borderRadius: '0.5rem',
                                            border: '1px solid rgba(251, 191, 36, 0.3)',
                                            textAlign: 'center'
                                        }}>
                                            <p style={{color: '#fcd34d', margin: 0, fontSize: '0.95rem'}}>
                                                💡 Score 60% or higher (9/15) to proceed to graduation. 
                                                Don't worry - you can try again with new questions!
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                )}
                
                {/* ========== CHAPTER 8: SCALING & LAYER 2 ========== */}
                {chapter === 8 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
                            borderRadius: '1rem',
                            padding: '2.5rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(0,255,204,0.3)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>📈</div>
                            <h1 style={{color: '#f8fafc', fontSize: '2rem', margin: '0 0 0.5rem 0'}}>
                                Chapter 8: Scaling & Layer 2
                            </h1>
                            <p style={{color: '#94a3b8', fontSize: '1.1rem', margin: 0}}>
                                How Ethereum scales with rollups
                            </p>
                        </div>
                        
                        <div style={{
                            background: '#1e293b',
                            borderRadius: '1rem',
                            padding: '2rem',
                            border: '1px solid #334155'
                        }}>
                            {chapterStep === 0 && (
                                <>
                                    <p style={{color: '#cbd5e1', fontSize: '1.1rem', lineHeight: 1.7, marginTop: 0}}>
                                        L1 Ethereum is secure but limited — more users mean higher fees and slower confirmation. <strong style={{color: '#60a5fa'}}>Layer 2</strong> solves this.
                                    </p>
                                    <div style={{
                                        background: 'rgba(0,255,204,0.1)',
                                        padding: '1.5rem',
                                        borderRadius: '0.75rem',
                                        border: '2px solid rgba(0,255,204,0.4)',
                                        margin: '1.5rem 0'
                                    }}>
                                        <h4 style={{color: '#00ffcc', margin: '0 0 1rem 0'}}>What is Layer 2?</h4>
                                        <p style={{color: '#e2e8f0', margin: 0, lineHeight: 1.7}}>
                                            L2 chains (Optimism, Arbitrum, Base) execute transactions off L1, then post data or proofs to L1. They inherit L1 security while scaling throughput. <strong>Rollups</strong> batch many L2 transactions and post compressed data to L1.
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => setChapterStep(1)}
                                        style={{
                                            marginTop: '1.5rem',
                                            width: '100%',
                                            padding: '1.25rem',
                                            background: 'linear-gradient(135deg, #00b894 0%, #00ffcc 100%)',
                                            border: 'none',
                                            borderRadius: '0.75rem',
                                            color: '#0f172a',
                                            fontSize: '1.1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        Connect to an L2 chain →
                                    </button>
                                </>
                            )}
                            {chapterStep === 1 && (
                                <>
                                    <h4 style={{color: '#00ffcc', margin: '0 0 1rem 0'}}>Connect to an L2 chain</h4>
                                    <p style={{color: '#cbd5e1', fontSize: '1rem', lineHeight: 1.7, marginBottom: '1rem'}}>
                                        L2 rollups are <strong>separate chains</strong>. You connect to them via their own RPC URL. Get a public RPC from{' '}
                                        <a href="https://optimism.io/developers" target="_blank" rel="noreferrer" style={{color: '#00ffcc'}}>Optimism</a> or{' '}
                                        <a href="https://arbitrum.io/developers" target="_blank" rel="noreferrer" style={{color: '#00ffcc'}}>Arbitrum</a>, then paste it in the 3D Chain Explorer.
                                    </p>
                                    <Link
                                        to="/chain-3d?mode=layer2"
                                        style={{
                                            display: 'inline-block',
                                            padding: '1rem 2rem',
                                            background: 'linear-gradient(135deg, rgba(0,255,204,0.3) 0%, rgba(0,255,204,0.2) 100%)',
                                            border: '2px solid rgba(0,255,204,0.5)',
                                            borderRadius: '0.75rem',
                                            color: '#00ffcc',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            textDecoration: 'none',
                                            marginBottom: '1rem'
                                        }}
                                    >
                                        Open 3D Chain Explorer (L2 mode)
                                    </Link>
                                    <p style={{color: '#64748b', fontSize: '0.9rem', marginBottom: '1rem'}}>
                                        Paste an L2 RPC URL (e.g. https://mainnet.optimism.io), click Connect, then return here.
                                    </p>
                                    <button
                                        onClick={() => setChapterStep(2)}
                                        style={{
                                            marginTop: '1rem',
                                            width: '100%',
                                            padding: '1.25rem',
                                            background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                            border: 'none',
                                            borderRadius: '0.75rem',
                                            color: 'white',
                                            fontSize: '1.1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        I&apos;ve connected — Continue →
                                    </button>
                                </>
                            )}
                            {chapterStep === 2 && (
                                <>
                                    <div style={{
                                        background: 'rgba(16, 185, 129, 0.1)',
                                        padding: '1.5rem',
                                        borderRadius: '0.75rem',
                                        border: '2px solid rgba(16, 185, 129, 0.4)',
                                        marginBottom: '1.5rem'
                                    }}>
                                        <h4 style={{color: '#86efac', margin: '0 0 0.5rem 0'}}>You connected to an L2 by entering its RPC URL</h4>
                                        <p style={{color: '#e2e8f0', margin: 0, lineHeight: 1.6}}>
                                            That&apos;s how L2 is a distinct network — separate chain, own RPC, batches transactions, posts to L1 for security.
                                        </p>
                                    </div>
                                    <button
                                        onClick={nextChapter}
                                        style={{
                                            marginTop: '1rem',
                                            width: '100%',
                                            padding: '1.25rem',
                                            background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                            border: 'none',
                                            borderRadius: '0.75rem',
                                            color: 'white',
                                            fontSize: '1.1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        Continue to Graduation →
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                )}
                
                {/* ========== CHAPTER 9: GRADUATION ========== */}
                {chapter === 9 && (
                    <div style={{animation: 'fadeIn 0.5s ease'}}>
                        <div style={{
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 50%, #1a1a2e 100%)',
                            borderRadius: '1rem',
                            padding: '3rem',
                            marginBottom: '1.5rem',
                            border: '2px solid rgba(251, 191, 36, 0.4)',
                            textAlign: 'center'
                        }}>
                            <div style={{fontSize: '5rem', marginBottom: '1rem'}}>🎓</div>
                            <h1 style={{
                                color: '#fcd34d',
                                fontSize: '2.5rem',
                                margin: '0 0 0.5rem 0',
                                textShadow: '0 0 20px rgba(251, 191, 36, 0.5)'
                            }}>
                                Congratulations!
                            </h1>
                            <p style={{color: '#fde68a', fontSize: '1.2rem', margin: 0}}>
                                You now understand how Ethereum Proof of Stake works
                            </p>
                        </div>
                        
                        <div style={{
                            background: '#1e293b',
                            borderRadius: '1rem',
                            padding: '2rem',
                            border: '1px solid #334155',
                            marginBottom: '1.5rem'
                        }}>
                            <h3 style={{color: '#f8fafc', marginTop: 0}}>📜 What You Mastered:</h3>
                            
                            <div style={{display: 'grid', gap: '1rem', marginTop: '1rem'}}>
                                {[
                                    { icon: '🤔', title: 'The Problem', desc: 'How to have trust without a central authority' },
                                    { icon: '👥', title: 'Validators', desc: 'Special participants who verify transactions' },
                                    { icon: '💰', title: 'Staking', desc: 'Locking money creates "skin in the game"' },
                                    { icon: '🎲', title: 'Selection', desc: 'Weighted random selection keeps it fair' },
                                    { icon: '⚔️', title: 'Slashing', desc: 'Automatic punishment for cheaters' },
                                    { icon: '🤝', title: 'Consensus', desc: '2/3 voting creates permanent agreement' },
                                    { icon: '📝', title: 'Final Quiz', desc: `Passed with ${quizScore}/15 (${Math.round(quizScore/15*100)}%)` },
                                    { icon: '📈', title: 'Scaling & L2', desc: 'L2 rollups are separate chains; connect via RPC URL' }
                                ].map((item, idx) => (
                                    <div key={idx} style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '1rem',
                                        padding: '1rem',
                                        background: 'rgba(16, 185, 129, 0.1)',
                                        borderRadius: '0.75rem',
                                        border: '1px solid rgba(16, 185, 129, 0.3)'
                                    }}>
                                        <div style={{fontSize: '2rem'}}>{item.icon}</div>
                                        <div>
                                            <div style={{color: '#86efac', fontWeight: 'bold'}}>{item.title}</div>
                                            <div style={{color: '#cbd5e1', fontSize: '0.9rem'}}>{item.desc}</div>
                                        </div>
                                        <div style={{marginLeft: 'auto', color: '#22c55e', fontSize: '1.5rem'}}>✓</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        <div style={{
                            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(59, 130, 246, 0.1) 100%)',
                            borderRadius: '1rem',
                            padding: '2rem',
                            border: '2px solid rgba(139, 92, 246, 0.4)',
                            textAlign: 'center'
                        }}>
                            <h3 style={{color: '#a78bfa', margin: '0 0 1rem 0'}}>🚀 Ready for More?</h3>
                            <p style={{color: '#cbd5e1', margin: '0 0 1.5rem 0'}}>
                                Now you can explore the full simulator sandbox or try the Live Network!
                            </p>
                            
                            <div style={{display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap'}}>
                                <button
                                    onClick={() => setLearningMode('sandbox')}
                                    style={{
                                        padding: '1rem 2rem',
                                        background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                        border: 'none',
                                        borderRadius: '0.75rem',
                                        color: 'white',
                                        fontSize: '1rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >
                                    🔬 Open Full Simulator
                                </button>
                                <Link
                                    to="/chain-3d?mode=layer2"
                                    style={{
                                        padding: '1rem 2rem',
                                        background: 'linear-gradient(135deg, rgba(0,255,204,0.3) 0%, rgba(0,255,204,0.2) 100%)',
                                        border: '2px solid rgba(0,255,204,0.5)',
                                        borderRadius: '0.75rem',
                                        color: '#00ffcc',
                                        fontSize: '1rem',
                                        fontWeight: 'bold',
                                        textDecoration: 'none',
                                        display: 'inline-block'
                                    }}
                                >
                                    📈 Explore Layer 2
                                </Link>
                                <button
                                    onClick={onComplete}
                                    style={{
                                        padding: '1rem 2rem',
                                        background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                        border: 'none',
                                        borderRadius: '0.75rem',
                                        color: 'white',
                                        fontSize: '1rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >
                                    🌐 Go to Live Network
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    }
    
    // =====================================================================
    // SANDBOX MODE (FULL SIMULATOR) - Original complex interface
    // =====================================================================
    return (
        <div style={{maxWidth: '1200px', margin: '0 auto'}}>
            {/* Mode Switcher */}
            <div style={{
                display: 'flex',
                justifyContent: 'flex-end',
                marginBottom: '1rem'
            }}>
                <button
                    onClick={() => setLearningMode('story')}
                    style={{
                        padding: '8px 16px',
                        background: 'rgba(139, 92, 246, 0.2)',
                        border: '1px solid #8b5cf6',
                        borderRadius: '6px',
                        color: '#a78bfa',
                        cursor: 'pointer',
                        fontSize: '0.85rem'
                    }}
                >
                    ← Back to Guided Learning
                </button>
            </div>
            {/* === HEADER === */}
            <div style={{
                background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 50%, #1a1a2e 100%)',
                padding: '2rem 2.5rem',
                borderRadius: '1rem',
                marginBottom: '1.5rem',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                position: 'relative',
                overflow: 'hidden'
            }}>
                <div style={{
                    position: 'absolute',
                    top: '-50px',
                    right: '-50px',
                    width: '200px',
                    height: '200px',
                    background: 'radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%)',
                    pointerEvents: 'none'
                }}></div>
                
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem'}}>
                    <div>
                        <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            background: 'rgba(139, 92, 246, 0.2)',
                            padding: '6px 14px',
                            borderRadius: '20px',
                            marginBottom: '0.75rem',
                            border: '1px solid rgba(139, 92, 246, 0.4)'
                        }}>
                            <span style={{fontSize: '0.8rem', color: '#a78bfa', fontWeight: '600'}}>
                                ETHEREUM CONSENSUS SIMULATOR
                            </span>
                        </div>
                        <h2 style={{
                            margin: 0,
                            fontSize: '1.75rem',
                            color: '#f8fafc',
                            fontWeight: '700'
                        }}>
                            🔬 Proof-of-Stake Laboratory
                        </h2>
                        <p style={{margin: '0.5rem 0 0 0', color: '#94a3b8', fontSize: '0.95rem'}}>
                            Interactive simulation of Gasper consensus (LMD GHOST + Casper FFG)
                        </p>
                    </div>
                    
                    {/* Live Status */}
                    <div style={{
                        display: 'flex',
                        gap: '1rem',
                        background: 'rgba(0,0,0,0.3)',
                        padding: '1rem 1.5rem',
                        borderRadius: '0.75rem',
                        border: '1px solid #334155'
                    }}>
                        <div style={{textAlign: 'center'}}>
                            <div style={{fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase'}}>Epoch</div>
                            <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#a78bfa'}}>{epoch}</div>
                        </div>
                        <div style={{width: '1px', background: '#334155'}}></div>
                        <div style={{textAlign: 'center'}}>
                            <div style={{fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase'}}>Slot</div>
                            <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#60a5fa'}}>{slot}</div>
                        </div>
                        <div style={{width: '1px', background: '#334155'}}></div>
                        <div style={{textAlign: 'center'}}>
                            <div style={{fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase'}}>Finalized</div>
                            <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: finalizedEpoch >= 0 ? '#22c55e' : '#64748b'}}>
                                {finalizedEpoch >= 0 ? finalizedEpoch : '—'}
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Simulation Controls */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    marginTop: '1.5rem',
                    padding: '1rem',
                    background: 'rgba(0,0,0,0.2)',
                    borderRadius: '0.75rem'
                }}>
                    <button
                        onClick={() => setIsRunning(!isRunning)}
                        style={{
                            padding: '0.75rem 1.5rem',
                            background: isRunning 
                                ? 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)'
                                : 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                            border: 'none',
                            borderRadius: '0.5rem',
                            color: 'white',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '0.95rem'
                        }}
                    >
                        {isRunning ? '⏸️ Pause' : '▶️ Run'} Simulation
                    </button>
                    
                    <button
                        onClick={simulationStep}
                        disabled={isRunning}
                        style={{
                            padding: '0.75rem 1.25rem',
                            background: isRunning ? '#374151' : 'rgba(59, 130, 246, 0.2)',
                            border: '1px solid #3b82f6',
                            borderRadius: '0.5rem',
                            color: isRunning ? '#6b7280' : '#93c5fd',
                            cursor: isRunning ? 'not-allowed' : 'pointer',
                            fontWeight: '600',
                            fontSize: '0.9rem'
                        }}
                    >
                        ⏭️ Step
                    </button>
                    
                    <div style={{flex: 1}}></div>
                    
                    <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                        <span style={{fontSize: '0.85rem', color: '#94a3b8'}}>Speed:</span>
                        <input
                            type="range"
                            min="100"
                            max="2000"
                            value={2100 - simulationSpeed}
                            onChange={(e) => setSimulationSpeed(2100 - parseInt(e.target.value))}
                            style={{width: '100px'}}
                        />
                        <span style={{fontSize: '0.8rem', color: '#64748b', minWidth: '50px'}}>
                            {(1000 / simulationSpeed).toFixed(1)}x
                        </span>
                    </div>
                    
                    <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                        <span style={{fontSize: '0.85rem', color: '#94a3b8'}}>Latency:</span>
                        <input
                            type="range"
                            min="0"
                            max="500"
                            value={networkLatency}
                            onChange={(e) => setNetworkLatency(parseInt(e.target.value))}
                            style={{width: '80px'}}
                        />
                        <span style={{fontSize: '0.8rem', color: '#64748b', minWidth: '45px'}}>{networkLatency}ms</span>
                    </div>
                </div>
            </div>
            
            {/* === MODULE TABS === */}
            <div style={{
                display: 'flex',
                gap: '0.5rem',
                marginBottom: '1.5rem',
                flexWrap: 'wrap'
            }}>
                {moduleButtons.map(mod => (
                    <button
                        key={mod.id}
                        onClick={() => setActiveModule(mod.id)}
                        style={{
                            padding: '0.75rem 1.25rem',
                            background: activeModule === mod.id 
                                ? 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)'
                                : '#1e293b',
                            border: activeModule === mod.id 
                                ? 'none' 
                                : '1px solid #334155',
                            borderRadius: '0.5rem',
                            color: activeModule === mod.id ? 'white' : '#94a3b8',
                            cursor: 'pointer',
                            fontWeight: activeModule === mod.id ? 'bold' : 'normal',
                            fontSize: '0.9rem',
                            transition: 'all 0.2s'
                        }}
                    >
                        <div>{mod.label}</div>
                        <div style={{fontSize: '0.7rem', opacity: 0.8}}>{mod.desc}</div>
                    </button>
                ))}
            </div>
            
            {/* === MODULE CONTENT === */}
            <div style={{
                background: '#1e293b',
                borderRadius: '1rem',
                padding: '1.5rem',
                border: '1px solid #334155',
                minHeight: '500px'
            }}>
                {/* OVERVIEW MODULE */}
                {activeModule === 'overview' && (
                    <div>
                        <h3 style={{color: '#f8fafc', marginTop: 0}}>📊 Simulation Overview</h3>
                        
                        {/* Validator Cards Grid */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: '1rem',
                            marginTop: '1rem'
                        }}>
                            {validators.map(v => (
                                <div key={v.id} style={{
                                    padding: '1rem',
                                    background: `linear-gradient(135deg, ${v.color}15, ${v.color}05)`,
                                    border: `2px solid ${v.slashed ? '#ef4444' : v.status === 'active' ? v.color : '#64748b'}`,
                                    borderRadius: '0.75rem',
                                    opacity: v.slashed ? 0.5 : 1
                                }}>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.75rem'}}>
                                        <div style={{
                                            width: '36px',
                                            height: '36px',
                                            borderRadius: '50%',
                                            background: v.color,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontWeight: 'bold'
                                        }}>
                                            {v.name[0]}
                                        </div>
                                        <div>
                                            <div style={{fontWeight: 'bold', color: '#f8fafc'}}>{v.name}</div>
                                            <div style={{fontSize: '0.75rem', color: v.status === 'active' ? '#22c55e' : '#f59e0b'}}>
                                                {v.slashed ? '🔴 SLASHED' : v.status.toUpperCase()}
                                            </div>
                                        </div>
                                    </div>
                                    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem'}}>
                                        <div>
                                            <div style={{color: '#64748b'}}>Stake</div>
                                            <div style={{color: '#e2e8f0', fontWeight: '600'}}>{v.stake} ETH</div>
                                        </div>
                                        <div>
                                            <div style={{color: '#64748b'}}>Rewards</div>
                                            <div style={{color: '#86efac', fontWeight: '600'}}>+{v.rewards.toFixed(4)}</div>
                                        </div>
                                        <div>
                                            <div style={{color: '#64748b'}}>Attestations</div>
                                            <div style={{color: '#e2e8f0'}}>{v.attestations}</div>
                                        </div>
                                        <div>
                                            <div style={{color: '#64748b'}}>Blocks</div>
                                            <div style={{color: '#e2e8f0'}}>{v.blocksProposed}</div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        
                        {/* Recent Blocks */}
                        <h4 style={{color: '#a78bfa', marginTop: '1.5rem'}}>🧱 Recent Blocks</h4>
                        <div style={{
                            display: 'flex',
                            gap: '0.5rem',
                            overflowX: 'auto',
                            padding: '0.5rem 0'
                        }}>
                            {blocks.slice(-12).map((block, idx) => {
                                const proposer = validators.find(v => v.id === block.proposerId);
                                return (
                                    <div key={idx} style={{
                                        minWidth: '80px',
                                        padding: '0.75rem',
                                        background: proposer?.color + '20',
                                        border: `2px solid ${proposer?.color || '#64748b'}`,
                                        borderRadius: '0.5rem',
                                        textAlign: 'center'
                                    }}>
                                        <div style={{fontSize: '0.7rem', color: '#64748b'}}>Slot {block.slot}</div>
                                        <div style={{fontSize: '0.9rem', fontWeight: 'bold', color: proposer?.color}}>
                                            {block.proposer[0]}
                                        </div>
                                        <div style={{fontSize: '0.7rem', color: '#94a3b8'}}>{block.attestations} att.</div>
                                    </div>
                                );
                            })}
                            {blocks.length === 0 && (
                                <div style={{color: '#64748b', fontStyle: 'italic'}}>
                                    No blocks yet. Start the simulation!
                                </div>
                            )}
                        </div>
                        
                        {/* Current Proposer */}
                        {selectedProposer && (
                            <div style={{
                                marginTop: '1rem',
                                padding: '1rem',
                                background: 'rgba(139, 92, 246, 0.15)',
                                borderRadius: '0.75rem',
                                border: '2px solid rgba(139, 92, 246, 0.4)'
                            }}>
                                <div style={{color: '#a78bfa', fontWeight: 'bold'}}>
                                    🎯 Current Proposer: {selectedProposer.name}
                                </div>
                                <div style={{color: '#cbd5e1', fontSize: '0.9rem', marginTop: '0.25rem'}}>
                                    Selection probability: {((selectedProposer.stake / totalStake) * 100).toFixed(1)}% (stake: {selectedProposer.stake} ETH)
                                </div>
                            </div>
                        )}
                    </div>
                )}
                
                {/* SELECTION MODULE */}
                {activeModule === 'selection' && (
                    <div>
                        <h3 style={{color: '#f8fafc', marginTop: 0}}>🎲 Validator Selection Algorithm</h3>
                        <p style={{color: '#94a3b8'}}>
                            Ethereum uses <strong style={{color: '#a78bfa'}}>RANDAO</strong> for randomness and 
                            <strong style={{color: '#60a5fa'}}> weighted random selection</strong> based on stake.
                        </p>
                        
                        {/* RANDAO Visualization */}
                        <div style={{
                            padding: '1rem',
                            background: 'rgba(59, 130, 246, 0.1)',
                            borderRadius: '0.75rem',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            marginTop: '1rem'
                        }}>
                            <div style={{color: '#93c5fd', fontWeight: 'bold', marginBottom: '0.5rem'}}>
                                🔮 RANDAO Beacon (Current Mix)
                            </div>
                            <code style={{
                                fontFamily: 'monospace',
                                fontSize: '1.1rem',
                                color: '#fbbf24',
                                background: 'rgba(0,0,0,0.3)',
                                padding: '0.5rem 1rem',
                                borderRadius: '0.25rem',
                                display: 'block'
                            }}>
                                {randaoReveal}
                            </code>
                            <p style={{fontSize: '0.85rem', color: '#64748b', marginTop: '0.5rem', marginBottom: 0}}>
                                Each proposer contributes to this mix by revealing their pre-committed random value.
                            </p>
                        </div>
                        
                        {/* Selection Probability Visualization */}
                        <h4 style={{color: '#a78bfa', marginTop: '1.5rem'}}>📊 Selection Probabilities</h4>
                        <div style={{marginTop: '0.75rem'}}>
                            {validators.filter(v => v.status === 'active' && !v.slashed).map(v => {
                                const prob = (v.stake / totalStake) * 100;
                                return (
                                    <div key={v.id} style={{marginBottom: '0.75rem'}}>
                                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px'}}>
                                            <span style={{color: '#e2e8f0', fontWeight: '600'}}>{v.name}</span>
                                            <span style={{color: v.color, fontWeight: 'bold'}}>{prob.toFixed(1)}%</span>
                                        </div>
                                        <div style={{
                                            height: '24px',
                                            background: 'rgba(0,0,0,0.3)',
                                            borderRadius: '4px',
                                            overflow: 'hidden'
                                        }}>
                                            <div style={{
                                                width: `${prob}%`,
                                                height: '100%',
                                                background: `linear-gradient(90deg, ${v.color}, ${v.color}88)`,
                                                borderRadius: '4px',
                                                display: 'flex',
                                                alignItems: 'center',
                                                paddingLeft: '8px',
                                                color: 'white',
                                                fontSize: '0.75rem',
                                                fontWeight: 'bold'
                                            }}>
                                                {v.stake} ETH
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        
                        <div style={{
                            marginTop: '1.5rem',
                            padding: '1rem',
                            background: 'rgba(251, 191, 36, 0.1)',
                            borderRadius: '0.75rem',
                            border: '1px solid rgba(251, 191, 36, 0.3)'
                        }}>
                            <div style={{color: '#fcd34d', fontWeight: 'bold'}}>💡 Key Insight</div>
                            <p style={{color: '#fde68a', fontSize: '0.9rem', margin: '0.5rem 0 0 0'}}>
                                Higher stake = higher probability, but selection is never guaranteed.
                                Even small validators can be selected, maintaining decentralization.
                            </p>
                        </div>
                    </div>
                )}
                
                {/* ATTESTATION MODULE */}
                {activeModule === 'attestation' && (
                    <div>
                        <h3 style={{color: '#f8fafc', marginTop: 0}}>✅ Attestation & Finality (Casper FFG)</h3>
                        <p style={{color: '#94a3b8'}}>
                            Validators vote on blocks. When 2/3+ stake agrees, epochs become 
                            <strong style={{color: '#fbbf24'}}> justified</strong>, then 
                            <strong style={{color: '#22c55e'}}> finalized</strong>.
                        </p>
                        
                        {/* Finality Status */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(3, 1fr)',
                            gap: '1rem',
                            marginTop: '1rem'
                        }}>
                            <div style={{
                                padding: '1rem',
                                background: 'rgba(139, 92, 246, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(139, 92, 246, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#a78bfa', fontSize: '0.8rem', marginBottom: '0.5rem'}}>CURRENT EPOCH</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#a78bfa'}}>{epoch}</div>
                            </div>
                            <div style={{
                                padding: '1rem',
                                background: 'rgba(251, 191, 36, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(251, 191, 36, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#fcd34d', fontSize: '0.8rem', marginBottom: '0.5rem'}}>JUSTIFIED EPOCH</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#fcd34d'}}>
                                    {justifiedEpoch >= 0 ? justifiedEpoch : '—'}
                                </div>
                            </div>
                            <div style={{
                                padding: '1rem',
                                background: 'rgba(34, 197, 94, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(34, 197, 94, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#22c55e', fontSize: '0.8rem', marginBottom: '0.5rem'}}>FINALIZED EPOCH</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#22c55e'}}>
                                    {finalizedEpoch >= 0 ? finalizedEpoch : '—'}
                                </div>
                            </div>
                        </div>
                        
                        {/* Attestation Stats */}
                        <h4 style={{color: '#60a5fa', marginTop: '1.5rem'}}>📝 Validator Attestation Performance</h4>
                        <div style={{marginTop: '0.75rem'}}>
                            {validators.filter(v => v.status === 'active').map(v => (
                                <div key={v.id} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '1rem',
                                    padding: '0.75rem',
                                    background: 'rgba(0,0,0,0.2)',
                                    borderRadius: '0.5rem',
                                    marginBottom: '0.5rem'
                                }}>
                                    <div style={{
                                        width: '32px',
                                        height: '32px',
                                        borderRadius: '50%',
                                        background: v.color,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        fontSize: '0.9rem'
                                    }}>
                                        {v.name[0]}
                                    </div>
                                    <div style={{flex: 1}}>
                                        <div style={{color: '#e2e8f0', fontWeight: '600'}}>{v.name}</div>
                                    </div>
                                    <div style={{textAlign: 'center', minWidth: '80px'}}>
                                        <div style={{fontSize: '0.7rem', color: '#64748b'}}>Attested</div>
                                        <div style={{color: '#22c55e', fontWeight: 'bold'}}>{v.attestations}</div>
                                    </div>
                                    <div style={{textAlign: 'center', minWidth: '80px'}}>
                                        <div style={{fontSize: '0.7rem', color: '#64748b'}}>Missed</div>
                                        <div style={{color: '#ef4444', fontWeight: 'bold'}}>{v.missedAttestations}</div>
                                    </div>
                                    <div style={{textAlign: 'center', minWidth: '80px'}}>
                                        <div style={{fontSize: '0.7rem', color: '#64748b'}}>Rate</div>
                                        <div style={{color: '#fbbf24', fontWeight: 'bold'}}>
                                            {((v.attestations / Math.max(1, v.attestations + v.missedAttestations)) * 100).toFixed(0)}%
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                
                {/* ECONOMICS MODULE */}
                {activeModule === 'economics' && (
                    <div>
                        <h3 style={{color: '#f8fafc', marginTop: 0}}>💰 Staking Economics</h3>
                        <p style={{color: '#94a3b8'}}>
                            Validators earn rewards for participating honestly and face penalties for misbehavior.
                        </p>
                        
                        {/* Reward/Penalty Leaderboard */}
                        <div style={{marginTop: '1rem'}}>
                            {validators.sort((a, b) => b.rewards - a.rewards).map((v, idx) => (
                                <div key={v.id} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '1rem',
                                    padding: '1rem',
                                    background: idx === 0 ? 'rgba(251, 191, 36, 0.1)' : 'rgba(0,0,0,0.2)',
                                    border: idx === 0 ? '2px solid rgba(251, 191, 36, 0.4)' : '1px solid transparent',
                                    borderRadius: '0.75rem',
                                    marginBottom: '0.75rem'
                                }}>
                                    <div style={{
                                        width: '30px',
                                        fontSize: '1.2rem',
                                        fontWeight: 'bold',
                                        color: idx === 0 ? '#fbbf24' : '#64748b'
                                    }}>
                                        #{idx + 1}
                                    </div>
                                    <div style={{
                                        width: '40px',
                                        height: '40px',
                                        borderRadius: '50%',
                                        background: v.color,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: 'white',
                                        fontWeight: 'bold'
                                    }}>
                                        {v.name[0]}
                                    </div>
                                    <div style={{flex: 1}}>
                                        <div style={{fontWeight: 'bold', color: '#f8fafc'}}>{v.name}</div>
                                        <div style={{fontSize: '0.85rem', color: '#94a3b8'}}>
                                            {v.stake} ETH staked • {v.blocksProposed} blocks proposed
                                        </div>
                                    </div>
                                    <div style={{textAlign: 'right'}}>
                                        <div style={{
                                            fontSize: '1.25rem',
                                            fontWeight: 'bold',
                                            color: v.rewards >= 0 ? '#22c55e' : '#ef4444'
                                        }}>
                                            {v.rewards >= 0 ? '+' : ''}{v.rewards.toFixed(4)} ETH
                                        </div>
                                        <div style={{fontSize: '0.8rem', color: '#64748b'}}>
                                            {((v.rewards / v.stake) * 100).toFixed(2)}% return
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        
                        {/* Slash a Validator Button */}
                        <div style={{
                            marginTop: '1.5rem',
                            padding: '1rem',
                            background: 'rgba(239, 68, 68, 0.1)',
                            borderRadius: '0.75rem',
                            border: '1px solid rgba(239, 68, 68, 0.3)'
                        }}>
                            <div style={{color: '#fca5a5', fontWeight: 'bold', marginBottom: '0.75rem'}}>
                                ⚔️ Simulate Slashing Event
                            </div>
                            <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                                {validators.filter(v => !v.slashed && v.status === 'active').map(v => (
                                    <button
                                        key={v.id}
                                        onClick={() => {
                                            setValidators(prev => prev.map(val => 
                                                val.id === v.id 
                                                    ? { ...val, slashed: true, stake: val.stake * 0.95, rewards: val.rewards - (val.stake * 0.05) }
                                                    : val
                                            ));
                                        }}
                                        style={{
                                            padding: '0.5rem 1rem',
                                            background: v.color,
                                            border: 'none',
                                            borderRadius: '0.25rem',
                                            color: 'white',
                                            cursor: 'pointer',
                                            fontWeight: '600',
                                            fontSize: '0.85rem'
                                        }}
                                    >
                                        Slash {v.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
                
                {/* ATTACKS MODULE */}
                {activeModule === 'attacks' && (
                    <div>
                        <h3 style={{color: '#f8fafc', marginTop: 0}}>⚔️ Attack Scenarios & Slashing</h3>
                        <p style={{color: '#94a3b8'}}>
                            Watch validators misbehave, get detected, and face automatic penalties.
                        </p>
                        
                        {/* === INTERACTIVE SLASHING DEMO === */}
                        <div style={{
                            padding: '1.5rem',
                            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%)',
                            borderRadius: '1rem',
                            border: '2px solid rgba(239, 68, 68, 0.4)',
                            marginBottom: '1.5rem'
                        }}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1rem'}}>
                                <span style={{fontSize: '2rem'}}>🎮</span>
                                <div>
                                    <h4 style={{margin: 0, color: '#fca5a5', fontSize: '1.2rem'}}>Interactive Slashing Demo</h4>
                                    <p style={{margin: 0, color: '#fecaca', fontSize: '0.85rem'}}>
                                        Choose a validator to misbehave and watch the protocol respond
                                    </p>
                                </div>
                            </div>
                            
                            {!slashingScenario.active ? (
                                <>
                                    {/* Select Attacker */}
                                    <div style={{marginBottom: '1rem'}}>
                                        <div style={{color: '#f87171', fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem'}}>
                                            1️⃣ Choose a Malicious Validator:
                                        </div>
                                        <div style={{display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                                            {validators.filter(v => v.status === 'active' && !v.slashed).map(v => (
                                                <button
                                                    key={v.id}
                                                    onClick={() => runSlashingScenario(v.id, 'double-sign')}
                                                    style={{
                                                        padding: '0.75rem 1.25rem',
                                                        background: `linear-gradient(135deg, ${v.color}40 0%, ${v.color}20 100%)`,
                                                        border: `2px solid ${v.color}`,
                                                        borderRadius: '0.5rem',
                                                        color: 'white',
                                                        cursor: 'pointer',
                                                        fontWeight: 'bold',
                                                        fontSize: '0.9rem',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: '8px',
                                                        transition: 'all 0.2s'
                                                    }}
                                                    onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                                                    onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                                                >
                                                    <div style={{
                                                        width: '24px',
                                                        height: '24px',
                                                        borderRadius: '50%',
                                                        background: v.color,
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        fontSize: '0.7rem'
                                                    }}>{v.name[0]}</div>
                                                    {v.name} ({v.stake} ETH)
                                                </button>
                                            ))}
                                        </div>
                                        {validators.filter(v => v.status === 'active' && !v.slashed).length === 0 && (
                                            <div style={{color: '#fca5a5', fontStyle: 'italic', padding: '1rem'}}>
                                                All validators have been slashed! Reset the simulation to try again.
                                            </div>
                                        )}
                                    </div>
                                    
                                    {/* Attack Type Info */}
                                    <div style={{
                                        padding: '1rem',
                                        background: 'rgba(0,0,0,0.2)',
                                        borderRadius: '0.75rem',
                                        fontSize: '0.9rem'
                                    }}>
                                        <div style={{color: '#f87171', fontWeight: 'bold', marginBottom: '0.75rem'}}>
                                            📚 Slashable Offenses in Ethereum:
                                        </div>
                                        <div style={{display: 'grid', gap: '0.75rem'}}>
                                            <div style={{display: 'flex', gap: '10px'}}>
                                                <span style={{fontSize: '1.2rem'}}>✍️</span>
                                                <div>
                                                    <strong style={{color: '#fca5a5'}}>Double Signing</strong>
                                                    <span style={{color: '#cbd5e1'}}> — Proposing two different blocks for the same slot</span>
                                                </div>
                                            </div>
                                            <div style={{display: 'flex', gap: '10px'}}>
                                                <span style={{fontSize: '1.2rem'}}>🔄</span>
                                                <div>
                                                    <strong style={{color: '#fca5a5'}}>Surround Voting</strong>
                                                    <span style={{color: '#cbd5e1'}}> — Casting an attestation that surrounds or is surrounded by a previous one</span>
                                                </div>
                                            </div>
                                            <div style={{display: 'flex', gap: '10px'}}>
                                                <span style={{fontSize: '1.2rem'}}>🔕</span>
                                                <div>
                                                    <strong style={{color: '#fca5a5'}}>Inactivity Leak</strong>
                                                    <span style={{color: '#cbd5e1'}}> — Extended offline period when finality is stalled (gradual penalty)</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                /* Active Slashing Scenario Display */
                                <div style={{
                                    background: 'rgba(0,0,0,0.3)',
                                    borderRadius: '0.75rem',
                                    padding: '1.25rem',
                                    border: '1px solid rgba(239, 68, 68, 0.3)'
                                }}>
                                    {/* Scenario Header */}
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '1rem',
                                        marginBottom: '1rem',
                                        paddingBottom: '1rem',
                                        borderBottom: '1px solid rgba(255,255,255,0.1)'
                                    }}>
                                        <div style={{
                                            width: '50px',
                                            height: '50px',
                                            borderRadius: '50%',
                                            background: slashingScenario.attacker?.color,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontWeight: 'bold',
                                            fontSize: '1.5rem',
                                            border: slashingScenario.step >= 3 ? '3px solid #ef4444' : 'none',
                                            opacity: slashingScenario.step >= 3 ? 0.5 : 1,
                                            position: 'relative'
                                        }}>
                                            {slashingScenario.attacker?.name[0]}
                                            {slashingScenario.step >= 3 && (
                                                <div style={{
                                                    position: 'absolute',
                                                    top: '-5px',
                                                    right: '-5px',
                                                    background: '#ef4444',
                                                    borderRadius: '50%',
                                                    width: '20px',
                                                    height: '20px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontSize: '0.8rem'
                                                }}>⚔️</div>
                                            )}
                                        </div>
                                        <div>
                                            <div style={{
                                                fontSize: '1.1rem',
                                                fontWeight: 'bold',
                                                color: slashingScenario.step >= 3 ? '#ef4444' : '#f8fafc'
                                            }}>
                                                {slashingScenario.attacker?.name} 
                                                {slashingScenario.step >= 3 && <span style={{color: '#ef4444'}}> — SLASHED</span>}
                                            </div>
                                            <div style={{fontSize: '0.85rem', color: '#94a3b8'}}>
                                                Attack: {slashingScenario.attackType === 'double-sign' ? 'Double Signing' : 
                                                         slashingScenario.attackType === 'surround-vote' ? 'Surround Voting' : 'Inactivity'}
                                            </div>
                                        </div>
                                        <div style={{marginLeft: 'auto', textAlign: 'right'}}>
                                            <div style={{fontSize: '0.75rem', color: '#64748b'}}>Stake at Risk</div>
                                            <div style={{
                                                fontSize: '1.25rem',
                                                fontWeight: 'bold',
                                                color: slashingScenario.step >= 3 ? '#ef4444' : '#fbbf24'
                                            }}>
                                                {slashingScenario.step >= 3 ? '-' : ''}{slashingScenario.slashAmount.toFixed(2)} ETH
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {/* Progress Steps */}
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        marginBottom: '1rem',
                                        position: 'relative'
                                    }}>
                                        {/* Progress Line */}
                                        <div style={{
                                            position: 'absolute',
                                            top: '15px',
                                            left: '15%',
                                            right: '15%',
                                            height: '4px',
                                            background: '#334155',
                                            borderRadius: '2px'
                                        }}>
                                            <div style={{
                                                height: '100%',
                                                width: `${Math.min(100, (slashingScenario.step / 3) * 100)}%`,
                                                background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                                                borderRadius: '2px',
                                                transition: 'width 0.5s ease'
                                            }}></div>
                                        </div>
                                        
                                        {[
                                            { label: 'Attack', icon: '🚨', step: 1 },
                                            { label: 'Detected', icon: '🔍', step: 2 },
                                            { label: 'Slashed', icon: '⚔️', step: 3 }
                                        ].map((s, idx) => (
                                            <div key={idx} style={{
                                                display: 'flex',
                                                flexDirection: 'column',
                                                alignItems: 'center',
                                                zIndex: 1
                                            }}>
                                                <div style={{
                                                    width: '36px',
                                                    height: '36px',
                                                    borderRadius: '50%',
                                                    background: slashingScenario.step >= s.step 
                                                        ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                                                        : '#334155',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontSize: '1.1rem',
                                                    transition: 'all 0.3s',
                                                    border: slashingScenario.step >= s.step ? '2px solid #fca5a5' : '2px solid #475569'
                                                }}>
                                                    {slashingScenario.step >= s.step ? s.icon : idx + 1}
                                                </div>
                                                <div style={{
                                                    marginTop: '0.5rem',
                                                    fontSize: '0.8rem',
                                                    color: slashingScenario.step >= s.step ? '#fca5a5' : '#64748b',
                                                    fontWeight: slashingScenario.step >= s.step ? 'bold' : 'normal'
                                                }}>
                                                    {s.label}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    
                                    {/* Detection Progress Bar (during step 1-2) */}
                                    {slashingScenario.step >= 1 && slashingScenario.step < 3 && (
                                        <div style={{marginBottom: '1rem'}}>
                                            <div style={{
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                fontSize: '0.8rem',
                                                color: '#f59e0b',
                                                marginBottom: '0.25rem'
                                            }}>
                                                <span>🔍 Detecting violation...</span>
                                                <span>{slashingScenario.detectionProgress}%</span>
                                            </div>
                                            <div style={{
                                                height: '8px',
                                                background: 'rgba(0,0,0,0.3)',
                                                borderRadius: '4px',
                                                overflow: 'hidden'
                                            }}>
                                                <div style={{
                                                    height: '100%',
                                                    width: `${slashingScenario.detectionProgress}%`,
                                                    background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                                                    transition: 'width 0.2s ease'
                                                }}></div>
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Event Log */}
                                    <div style={{
                                        background: 'rgba(0,0,0,0.4)',
                                        borderRadius: '0.5rem',
                                        padding: '1rem',
                                        maxHeight: '200px',
                                        overflowY: 'auto',
                                        fontFamily: 'monospace',
                                        fontSize: '0.85rem'
                                    }}>
                                        <div style={{color: '#64748b', marginBottom: '0.5rem'}}>📜 Event Log:</div>
                                        {slashingScenario.eventLog.length === 0 ? (
                                            <div style={{color: '#475569', fontStyle: 'italic'}}>Waiting for events...</div>
                                        ) : (
                                            slashingScenario.eventLog.map((event, idx) => (
                                                <div key={idx} style={{
                                                    marginBottom: '0.75rem',
                                                    paddingBottom: '0.75rem',
                                                    borderBottom: idx < slashingScenario.eventLog.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none'
                                                }}>
                                                    <div style={{
                                                        color: event.type === 'attack' ? '#f59e0b' :
                                                               event.type === 'detection' ? '#60a5fa' :
                                                               event.type === 'detected' ? '#fbbf24' :
                                                               '#ef4444',
                                                        fontWeight: 'bold'
                                                    }}>
                                                        {event.message}
                                                    </div>
                                                    <div style={{color: '#94a3b8', fontSize: '0.8rem', marginTop: '0.25rem'}}>
                                                        {event.details}
                                                    </div>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                    
                                    {/* Result Summary (when slashed) */}
                                    {slashingScenario.step >= 3 && (
                                        <div style={{
                                            marginTop: '1rem',
                                            padding: '1rem',
                                            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%)',
                                            borderRadius: '0.75rem',
                                            border: '2px solid #ef4444'
                                        }}>
                                            <div style={{
                                                fontSize: '1.1rem',
                                                fontWeight: 'bold',
                                                color: '#fca5a5',
                                                marginBottom: '0.75rem'
                                            }}>
                                                ⚖️ Slashing Complete
                                            </div>
                                            <div style={{display: 'grid', gap: '0.5rem', fontSize: '0.9rem'}}>
                                                <div style={{color: '#e2e8f0'}}>
                                                    <span style={{color: '#64748b'}}>Penalty Applied:</span> 
                                                    <span style={{color: '#ef4444', fontWeight: 'bold'}}> -{slashingScenario.slashAmount.toFixed(2)} ETH</span>
                                                </div>
                                                <div style={{color: '#e2e8f0'}}>
                                                    <span style={{color: '#64748b'}}>Remaining Stake:</span> 
                                                    <span style={{color: '#fbbf24', fontWeight: 'bold'}}> {(slashingScenario.attacker?.stake || 0).toFixed(2)} ETH</span>
                                                </div>
                                                <div style={{color: '#e2e8f0'}}>
                                                    <span style={{color: '#64748b'}}>Status:</span> 
                                                    <span style={{color: '#ef4444', fontWeight: 'bold'}}> Ejected from validator set</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={resetSlashingScenario}
                                                style={{
                                                    marginTop: '1rem',
                                                    padding: '0.75rem 1.5rem',
                                                    background: 'rgba(59, 130, 246, 0.2)',
                                                    border: '1px solid #3b82f6',
                                                    borderRadius: '0.5rem',
                                                    color: '#93c5fd',
                                                    cursor: 'pointer',
                                                    fontWeight: 'bold',
                                                    fontSize: '0.9rem'
                                                }}
                                            >
                                                🔄 Try Another Scenario
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                        
                        {/* Educational Info Cards */}
                        <div style={{display: 'grid', gap: '1rem', marginTop: '1rem'}}>
                            {/* Long-Range Attack */}
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(239, 68, 68, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(239, 68, 68, 0.3)'
                            }}>
                                <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.75rem'}}>
                                    <span style={{fontSize: '1.5rem'}}>🕰️</span>
                                    <h4 style={{margin: 0, color: '#fca5a5'}}>Long-Range Attack</h4>
                                </div>
                                <p style={{color: '#fed7aa', fontSize: '0.9rem', marginBottom: '0.75rem'}}>
                                    Attacker acquires old validator keys and creates an alternative chain from the past.
                                    <strong> Defense:</strong> Checkpointing and weak subjectivity period.
                                </p>
                                <div style={{
                                    padding: '0.75rem',
                                    background: 'rgba(0,0,0,0.2)',
                                    borderRadius: '0.5rem',
                                    fontSize: '0.85rem',
                                    color: '#94a3b8'
                                }}>
                                    <strong style={{color: '#22c55e'}}>Current Protection:</strong> Finalized checkpoint at epoch {finalizedEpoch >= 0 ? finalizedEpoch : 'N/A'}
                                </div>
                            </div>
                            
                            {/* Probabilistic Bouncing Attack */}
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(251, 191, 36, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(251, 191, 36, 0.3)'
                            }}>
                                <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.75rem'}}>
                                    <span style={{fontSize: '1.5rem'}}>🏀</span>
                                    <h4 style={{margin: 0, color: '#fcd34d'}}>Probabilistic Bouncing Attack</h4>
                                </div>
                                <p style={{color: '#fef3c7', fontSize: '0.9rem', marginBottom: '0.75rem'}}>
                                    Attacker strategically withholds votes to prevent finality indefinitely.
                                    <strong> Defense:</strong> Inactivity leak drains non-participating validators.
                                </p>
                                <div style={{
                                    padding: '0.75rem',
                                    background: 'rgba(0,0,0,0.2)',
                                    borderRadius: '0.5rem',
                                    fontSize: '0.85rem',
                                    color: '#94a3b8'
                                }}>
                                    <strong style={{color: '#fbbf24'}}>Network Latency Impact:</strong> {networkLatency}ms — Higher latency increases attack surface
                                </div>
                            </div>
                            
                            {/* 51% Attack Economics */}
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(139, 92, 246, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(139, 92, 246, 0.3)'
                            }}>
                                <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.75rem'}}>
                                    <span style={{fontSize: '1.5rem'}}>💸</span>
                                    <h4 style={{margin: 0, color: '#c4b5fd'}}>51% Attack Cost</h4>
                                </div>
                                <p style={{color: '#ddd6fe', fontSize: '0.9rem', marginBottom: '0.75rem'}}>
                                    To control this network, attacker needs {Math.ceil(totalStake * 0.51)} ETH (51% of {totalStake} total stake).
                                </p>
                                <div style={{
                                    padding: '0.75rem',
                                    background: 'rgba(0,0,0,0.2)',
                                    borderRadius: '0.5rem',
                                    fontSize: '0.85rem',
                                    color: '#94a3b8'
                                }}>
                                    <strong style={{color: '#ef4444'}}>At $3,000/ETH:</strong> ${(Math.ceil(totalStake * 0.51) * 3000).toLocaleString()} cost
                                    <br/>
                                    <strong style={{color: '#22c55e'}}>Real Ethereum:</strong> ~$51 billion needed (34M ETH staked)
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                
                {/* METRICS MODULE */}
                {activeModule === 'metrics' && (
                    <div>
                        <h3 style={{color: '#f8fafc', marginTop: 0}}>📈 Performance Metrics</h3>
                        <p style={{color: '#94a3b8'}}>
                            Real-time measurements of consensus performance and network health.
                        </p>
                        
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                            gap: '1rem',
                            marginTop: '1rem'
                        }}>
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(59, 130, 246, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(59, 130, 246, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#93c5fd', fontSize: '0.8rem', marginBottom: '0.5rem'}}>BLOCKS PRODUCED</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#60a5fa'}}>{blocks.length}</div>
                            </div>
                            
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(34, 197, 94, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(34, 197, 94, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#86efac', fontSize: '0.8rem', marginBottom: '0.5rem'}}>ATTESTATIONS</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#22c55e'}}>{attestations.length}</div>
                            </div>
                            
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(251, 191, 36, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(251, 191, 36, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#fcd34d', fontSize: '0.8rem', marginBottom: '0.5rem'}}>FINALITY LATENCY</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b'}}>
                                    {metrics.avgFinalityLatency.toFixed(1)}
                                </div>
                                <div style={{fontSize: '0.7rem', color: '#64748b'}}>epochs</div>
                            </div>
                            
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(139, 92, 246, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(139, 92, 246, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#c4b5fd', fontSize: '0.8rem', marginBottom: '0.5rem'}}>GINI COEFFICIENT</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#a78bfa'}}>
                                    {metrics.giniCoefficient.toFixed(3)}
                                </div>
                                <div style={{fontSize: '0.7rem', color: '#64748b'}}>stake inequality</div>
                            </div>
                            
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(236, 72, 153, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(236, 72, 153, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#f9a8d4', fontSize: '0.8rem', marginBottom: '0.5rem'}}>TOTAL REWARDS</div>
                                <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#ec4899'}}>
                                    +{metrics.totalRewards.toFixed(4)}
                                </div>
                                <div style={{fontSize: '0.7rem', color: '#64748b'}}>ETH distributed</div>
                            </div>
                            
                            <div style={{
                                padding: '1.25rem',
                                background: 'rgba(16, 185, 129, 0.1)',
                                borderRadius: '0.75rem',
                                border: '1px solid rgba(16, 185, 129, 0.3)',
                                textAlign: 'center'
                            }}>
                                <div style={{color: '#6ee7b7', fontSize: '0.8rem', marginBottom: '0.5rem'}}>NETWORK LATENCY</div>
                                <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#10b981'}}>{networkLatency}</div>
                                <div style={{fontSize: '0.7rem', color: '#64748b'}}>ms simulated</div>
                            </div>
                        </div>
                        
                        {/* Stake Distribution */}
                        <h4 style={{color: '#a78bfa', marginTop: '1.5rem'}}>📊 Stake Distribution</h4>
                        <div style={{
                            padding: '1rem',
                            background: 'rgba(0,0,0,0.2)',
                            borderRadius: '0.75rem',
                            marginTop: '0.75rem'
                        }}>
                            <div style={{display: 'flex', height: '40px', borderRadius: '0.25rem', overflow: 'hidden'}}>
                                {validators.filter(v => !v.slashed).map(v => (
                                    <div
                                        key={v.id}
                                        style={{
                                            width: `${(v.stake / totalStake) * 100}%`,
                                            background: v.color,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontSize: '0.75rem',
                                            fontWeight: 'bold',
                                            minWidth: '30px'
                                        }}
                                        title={`${v.name}: ${v.stake} ETH (${((v.stake / totalStake) * 100).toFixed(1)}%)`}
                                    >
                                        {v.name[0]}
                                    </div>
                                ))}
                            </div>
                            <div style={{fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem', textAlign: 'center'}}>
                                Total Staked: {totalStake} ETH across {validators.filter(v => !v.slashed && v.status === 'active').length} active validators
                            </div>
                        </div>
                    </div>
                )}
            </div>
            
            {/* === CONTINUE BUTTON === */}
            <div style={{marginTop: '1.5rem', textAlign: 'center'}}>
                <button
                    onClick={onComplete}
                    style={{
                        padding: '1rem 2.5rem',
                        background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                        border: 'none',
                        borderRadius: '0.75rem',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        cursor: 'pointer',
                        boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)'
                    }}
                >
                    Continue to Live Network 🌐
                </button>
                <p style={{marginTop: '0.75rem', color: '#64748b', fontSize: '0.9rem'}}>
                    Now experience these concepts on a real blockchain!
                </p>
            </div>
        </div>
    );
}

// --- COMPONENT: SIMULATION MODE (Legacy wallet practice) ---
function SimulationMode({ onComplete }) {
    const [simStep, setSimStep] = useState(1);

    return (
        <div className="simulation-container">
            <h2>🧪 Practice Lab (Fake Mode)</h2>
            
            {simStep === 1 && (
                <div className="sim-step">
                    <h3>Step 1: Generate a Wallet</h3>
                    <p>Click the button to create a random key pair locally.</p>
                    <button onClick={() => setSimStep(2)}>Generate Keys 🎲</button>
                </div>
            )}

            {simStep === 2 && (
                <div className="sim-step">
                    <h3>Step 2: Review Credentials</h3>
                    <div className="fake-wallet">
                        <p><strong>Private Key:</strong> 0x4c0883a69102937d6231471b5dbb6204</p>
                        <p><strong>Address:</strong> 0x71C7656EC7ab88b098defB751B7401B5f6d8976F</p>
                    </div>
                    <p>In the real world, you would save the Private Key securely!</p>
                    <button onClick={() => setSimStep(3)}>I saved it ✅</button>
                </div>
            )}

            {simStep === 3 && (
                <div className="sim-step">
                    <h3>Step 3: Craft a Transaction</h3>
                    <p>Let's simulate sending 1.0 ETH to Alice.</p>
                    <div className="fake-tx-form">
                        <label>To:</label>
                        <input disabled value="0xAlice..." />
                        <label>Amount:</label>
                        <input disabled value="1.0 ETH" />
                        <label>Gas Fee:</label>
                        <input disabled value="0.00042 ETH" />
                    </div>
                    <button onClick={() => setSimStep(4)}>Sign & Send ✍️</button>
                </div>
            )}

             {simStep === 4 && (
                <div className="sim-step">
                    <h3>Step 4: Confirmed!</h3>
                    <p>Your transaction was included in Block #492.</p>
                    <div className="success-icon">🎉</div>
                    <button className="primary-btn" onClick={onComplete}>Go to Live Network 🚀</button>
                </div>
            )}
        </div>
    )
}

// --- MAIN APP COMPONENT ---
function App() {
  const navigate = useNavigate()
  // Check URL params for instructor mode and student (live) view
  const urlParams = new URLSearchParams(window.location.search)
  const urlWantsInstructor = urlParams.get('mode') === 'instructor'
  const viewFromUrl = urlParams.get('view')

  // Session from Lab API: isInstructor (IP-checked), hasCreatedWallet (per-IP)
  const [session, setSession] = useState({ isInstructor: false, hasCreatedWallet: true, loading: true })
  useEffect(() => {
    fetch(import.meta.env.BASE_URL + 'lab-api/session').then(r => r.ok ? r.json() : null).then(data => {
      if (data) setSession({ isInstructor: data.isInstructor, hasCreatedWallet: data.hasCreatedWallet, loading: false })
      else setSession(prev => ({ ...prev, loading: false, hasCreatedWallet: true })) // Lab API unavailable: permissive
    }).catch(() => setSession(prev => ({ ...prev, loading: false, hasCreatedWallet: true })))
  }, [])

  // Only allow instructor view if URL has mode=instructor AND session confirms instructor IP
  const isInstructor = urlWantsInstructor && session.isInstructor && !session.loading

  const [view, setView] = useState(
    urlWantsInstructor ? 'instructor'
      : viewFromUrl === 'live' ? 'live'
      : viewFromUrl === 'diagnostics' ? 'diagnostics'
      : viewFromUrl === 'beacon-lab' ? 'beacon-lab'
      : viewFromUrl === 'contract-builder-lab' ? 'contract-builder-lab'
      : viewFromUrl === 'tokenization-lab' ? 'tokenization-lab'
      : 'intro'
  ); // intro -> concepts -> explore -> sim -> live -> diagnostics -> beacon-lab -> contract-builder-lab -> tokenization-lab -> cli | instructor
  const [appMode, setAppMode] = useState('learning'); // 'learning' | 'live' | 'cli' | 'instructor' - top-level mode separation

  useEffect(() => {
    if (typeof window === 'undefined') return
    const u = new URL(window.location.href)
    const nextView = SHAREABLE_QUERY_VIEWS.has(view) ? view : null
    if (nextView) {
      if (u.searchParams.get('view') === nextView) return
      u.searchParams.set('view', nextView)
      window.history.replaceState({}, '', u.toString())
      return
    }
    if (!u.searchParams.has('view')) return
    u.searchParams.delete('view')
    window.history.replaceState({}, '', u.toString())
  }, [view])

  // When session loads: if URL has ?mode=instructor but IP not allowed, strip param and redirect
  useEffect(() => {
    if (session.loading) return
    if (urlWantsInstructor && !session.isInstructor) {
      const u = new URL(window.location.href)
      u.searchParams.delete('mode')
      window.history.replaceState({}, '', u.toString())
      setView(
        viewFromUrl === 'live' ? 'live'
          : viewFromUrl === 'diagnostics' ? 'diagnostics'
          : viewFromUrl === 'beacon-lab' ? 'beacon-lab'
          : viewFromUrl === 'contract-builder-lab' ? 'contract-builder-lab'
          : viewFromUrl === 'tokenization-lab' ? 'tokenization-lab'
          : 'intro'
      )
    }
  }, [session.loading, session.isInstructor, urlWantsInstructor, viewFromUrl])
  
  // --- LIVE MODE STATE ---
  const isRemote = !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1')
  const port = typeof window !== 'undefined' ? window.location.port : ''
  const defaultRpcUrl = port === '5173'
    ? resolveRpcUrl('/rpc-proxy')
    : resolveRpcUrl('/rpc')
  
  // Check for student mode and auto-load config
  const isStudentMode = localStorage.getItem('student_mode') === 'true'
  const customRpc = localStorage.getItem('custom_rpc')

  const [trail, setTrail] = useState(() => {
    try {
        return JSON.parse(localStorage.getItem('learning_trail')) || { intro: false, concepts: false, explore: false }
    } catch {
        return { intro: false, concepts: false, explore: false }
    }
  })

  const [exploreProgress, setExploreProgress] = useState(() => {
    try {
        return JSON.parse(localStorage.getItem('explore_progress')) || [false, false, false]
    } catch {
        return [false, false, false]
    }
  })

  const [navHint, setNavHint] = useState('')
  
  const [rpcUrl, setRpcUrl] = useState(customRpc || defaultRpcUrl)
  const [terminalRpcUrl, setTerminalRpcUrl] = useState('')
  const [showRpcConfig, setShowRpcConfig] = useState(isRemote || isStudentMode) // Show config for remote users and students
  const [provider, setProvider] = useState(null)
  const [nodeStatus, setNodeStatus] = useState({ connected: false, blockNumber: 0 })
  const [wallet, setWallet] = useState({ address: null, signer: null, balance: '0', mode: null, nickname: 'My Wallet' })
  const [showAccountManager, setShowAccountManager] = useState(false)
  const [showLiveHelp, setShowLiveHelp] = useState(false)
  const [newWalletModal, setNewWalletModal] = useState(null) // { address, privateKey } when showing new wallet credentials
  const [posAddress, setPosAddress] = useState(() => {
    const stored = localStorage.getItem("pos_addr");
    if (stored && stored.length === 42) return stored;
    return "0xB7f8BC63BbcaD18155201308C8f3540b07f84F5e";
  })
  
  // Auto-load contract address and RPC URL from deploy config under the current base path.
  useEffect(() => {
    const loadConfig = async () => {
      // Try Docker/sandbox config first (has rpcUrl + mode), then deploy-generated
      for (const url of [
        import.meta.env.BASE_URL + 'api/config.json',
        import.meta.env.BASE_URL + 'contract-config.json',
      ]) {
        try {
          const response = await fetch(url);
          if (!response.ok) continue;
          const config = await response.json();
          const isStudent = config.mode === 'student' || config.role === 'student';
          const isInstructor = config.mode === 'instructor' || config.role === 'instructor';
          // Auto-set contract address
          if (config.contractAddress && config.contractAddress.length === 42) {
            const current = localStorage.getItem("pos_addr");
            if (current !== config.contractAddress) {
              console.log('[Config] Updating contract address:', current, '->', config.contractAddress);
              setPosAddress(config.contractAddress);
              localStorage.setItem("pos_addr", config.contractAddress);
            }
          }
          // Auto-set RPC URL for both student and instructor (virtualized sandbox auto-config)
          if (config.rpcUrl && (isStudent || isInstructor)) {
            setRpcUrl(config.rpcUrl);
            localStorage.setItem("custom_rpc", config.rpcUrl);
            console.log('[Config] RPC URL set from config:', config.rpcUrl, 'mode:', config.mode || config.role);
          }
          if (config.terminalRpcUrl && (isStudent || isInstructor)) {
            setTerminalRpcUrl(config.terminalRpcUrl);
            console.log('[Config] Terminal RPC URL set from config:', config.terminalRpcUrl);
          }
          // Auto-import pre-assigned wallet (lane containers inject a
          // per-station funded address so students skip manual wallet
          // creation and the Live Network badge shows "Connected").
          if (config.assignedPrivateKey && config.assignedPrivateKey.length === 66) {
            const nickname = config.station ? `Station ${config.station}` : 'Assigned Wallet';
            const result = addWallet(config.assignedPrivateKey, nickname);
            if (result.success) {
              fetch(import.meta.env.BASE_URL + 'lab-api/register-wallet', { method: 'POST' }).catch(() => {});
              setSession(prev => ({ ...prev, hasCreatedWallet: true }));
              console.log('[Config] Auto-imported assigned wallet:', result.address);
            }
          }
          if (config.contractAddress && config.contractAddress.length === 42) return;
        } catch (e) { /* config not available */ }
      }
      console.log('[Config] No deploy config found (using localStorage or fallback)');
    };
    loadConfig();
  }, [])
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState("")
  const [validators, setValidators] = useState([]) // Note: This includes all participants (stakers + chatters)
  const [actualValidatorCount, setActualValidatorCount] = useState(0) // Actual stakers from contract
  const [statusMsg, setStatusMsg] = useState('')
  const [isSyncing, setIsSyncing] = useState(false)
  const hasAutoJoined = useRef(false) // Track if we've auto-joined this session
  
  // Nickname system - store nicknames for classmates
  const [nicknames, setNicknames] = useState(() => {
    try {
      const stored = localStorage.getItem("classmate_nicknames");
      return stored ? JSON.parse(stored) : {};
    } catch { return {}; }
  });
  const [myNickname, setMyNickname] = useState(() => localStorage.getItem("my_nickname") || "");
  const [editingNickname, setEditingNickname] = useState(false);
  const [nicknameInput, setNicknameInput] = useState("");
  const [sessionStart] = useState(() => {
      const stored = localStorage.getItem("session_start")
      if (!stored) {
          const now = Date.now()
          localStorage.setItem("session_start", now.toString())
          return now
      }
      return parseInt(stored)
  })

  // Peer To Peer Send State
  const [recipient, setRecipient] = useState("")
  const [sendAmount, setSendAmount] = useState("")
  
  // Staking State (32 ETH = Ethereum mainnet validator minimum)
  const [stakeAmount, setStakeAmount] = useState("32")
  
  // Transaction History
  const [txHistory, setTxHistory] = useState([])
  const [myStake, setMyStake] = useState(() => {
    const storedRole = localStorage.getItem('scenario_role') || '';
    return {
      amount: '0',
      reward: '0',
      slashCount: 0,
      blocksProposed: 0,
      missedAttestations: 0,
      unbondingTime: 0,
      minStakeDuration: 0,
      hasAttestedThisEpoch: false,
      unbondingStartTime: 0,
      lastProposedBlockNumber: 0,
      role: storedRole
    };
  })
  
  // Enhanced PoS State
  const [currentEpoch, setCurrentEpoch] = useState(1)
  const [timeUntilNextEpoch, setTimeUntilNextEpoch] = useState(0)
  const [currentAPY, setCurrentAPY] = useState(5)
  const [withdrawalRequested, setWithdrawalRequested] = useState(false)
  
  // Sync status indicator
  const [lastSyncTime, setLastSyncTime] = useState(Date.now())
  const lastSyncRef = useRef(Date.now())
  const prevRoleRef = useRef('')
  const [roleAssignedBanner, setRoleAssignedBanner] = useState(false)
  const [roleContractInput, setRoleContractInput] = useState('')
  const [roleContractRegistering, setRoleContractRegistering] = useState(false)
  const [deployRoleInProgress, setDeployRoleInProgress] = useState(false)
  const [roleTemplateExpanded, setRoleTemplateExpanded] = useState(false)

  // Ransomware scenario (Phase 7)
  const [ransomContractAddress, setRansomContractAddress] = useState(localStorage.getItem('ransom_addr') || '')
  const [ransomAmount, setRansomAmount] = useState('0.1')
  const [artifactsOpen, setArtifactsOpen] = useState(true)

  // Script Playground (Phase 6: Web Playground)
  const [scriptPlaygroundOpen, setScriptPlaygroundOpen] = useState(false)
  const [livePageBlocksOpen, setLivePageBlocksOpen] = useState({
    yourWalletBanner: true,
    roleAssigned: true,
    identityStrip: true,
    socialProof: true,
    createWalletBanner: true,
    walletAndRole: true,
    quickActions: true,
    assetsCard: true,
    sendCard: true,
    beaconPromoCard: true,
    contractPromoCard: true,
    tokenPromoCard: true,
    connectionCard: true,
    txHistoryCard: true,
    classChat: true,
    evidenceSection: true,
    ransomSection: true,
    embeddedContractLab: true,
    labTerminalSection: true,
    labProgress: true,
  })
  const toggleLivePageBlock = (key) => {
    setLivePageBlocksOpen((prev) => ({ ...prev, [key]: !prev[key] }))
  }
  const [loadCodeForConsole, setLoadCodeForConsole] = useState('')
  const [scriptCode, setScriptCode] = useState(`// Run ethers.js against PoS and contracts
// Available: provider, ethers, wallet, posAddress, PoSABI
const c = new ethers.Contract(posAddress, PoSABI, wallet.signer);
const total = await c.totalStaked();
return ethers.formatEther(total) + ' ETH staked';`)
  const [scriptOutput, setScriptOutput] = useState('')
  const [scriptRunning, setScriptRunning] = useState(false)

  const saveTrail = (next) => {
    setTrail(next)
    localStorage.setItem('learning_trail', JSON.stringify(next))
  }

  // Notify when role is newly assigned
  useEffect(() => {
    const role = myStake.role || ''
    if (role && !prevRoleRef.current) {
      setRoleAssignedBanner(true)
    }
    prevRoleRef.current = role
  }, [myStake.role])

  // Extract artifacts from chat (instructor posts [ARTIFACT:...] for scenario clues)
  const artifacts = (messages || [])
    .filter(m => m.text && typeof m.text === 'string' && m.text.startsWith('[ARTIFACT:'))
    .map(m => ({ content: m.text.slice(10).replace(/\]$/, ''), timestamp: m.timestamp, sender: m.sender }))

  // Shared helper: parse messages for role assignment
  const parseRoleFromMessages = useCallback((msgList, address, validatorList) => {
    if (!msgList?.length || !address) return null;
    const myAddr = address.toLowerCase();
    let assignedRole = null;
    let latestTimestamp = 0;
    console.log('[Role] Parsing', msgList.length, 'messages for', myAddr.slice(0, 10) + '...');
    for (const m of msgList) {
      const text = (m?.text ?? m?.message ?? '').trim();
      if (!text || typeof text !== 'string') continue;
      // [SCENARIO:Name:Role1,Role2,...] — assign by participant index (sorted by address)
      const scenarioMatch = text.match(/\[SCENARIO:([^:]+):([^\]]+)\]/);
      if (scenarioMatch) {
        const roles = scenarioMatch[2].split(',').map(r => r.trim()).filter(Boolean);
        if (roles.length === 0) continue;
        const participants = [...(validatorList || [])].map(a => (typeof a === 'string' ? a : a?.address)?.toLowerCase?.()).filter(Boolean);
        if (!participants.includes(myAddr)) participants.push(myAddr);
        const sorted = [...new Set(participants)].sort();
        const idx = sorted.indexOf(myAddr);
        if (idx >= 0) {
          const role = roles[idx % roles.length];
          if (role && (m.timestamp || 0) >= latestTimestamp) {
            assignedRole = role;
            latestTimestamp = m.timestamp || 0;
          }
        }
      }
      // [ROLES:addr1:Role1;addr2:Role2;...] — direct assignment
      const rolesMatch = text.match(/\[ROLES:([^\]]+)\]/);
      if (rolesMatch) {
        console.log('[Role] Found ROLES message:', text.slice(0, 80) + '...');
        const pairs = rolesMatch[1].split(';');
        for (const p of pairs) {
          if (p.length < 44) { console.log('[Role] Skipping short pair:', p); continue; }
          const addr = p.slice(0, 42).toLowerCase();
          const sep = p[42];
          if (sep !== ':') { console.log('[Role] Bad separator at pos 42:', sep, 'pair:', p.slice(0, 50)); continue; }
          const role = p.slice(43).trim();
          console.log('[Role] Checking', addr.slice(0, 10), '===', myAddr.slice(0, 10), '?', addr === myAddr, 'role:', role);
          if (addr === myAddr && role && (m.timestamp || 0) >= latestTimestamp) {
            assignedRole = role;
            latestTimestamp = m.timestamp || 0;
          }
        }
      }
    }
    return assignedRole;
  }, []);

  // Parse chat for [SCENARIO:...] and [ROLES:...] — frontend-only role assignment
  useEffect(() => {
    if (!messages?.length || !wallet.address) return;
    const assignedRole = parseRoleFromMessages(messages, wallet.address, validators);
    if (assignedRole) {
      localStorage.setItem('scenario_role', assignedRole);
      setMyStake(prev => ({ ...prev, role: assignedRole }));
      console.log('[Role] useEffect assigned:', assignedRole);
    } else {
      console.log('[Role] useEffect: no role found. messages:', messages.length, 'wallet:', wallet.address?.slice(0, 10));
    }
  }, [messages, wallet.address, validators, parseRoleFromMessages])

  // Run script in Playground (Phase 6)
  const runScript = useCallback(async () => {
    if (!provider || !wallet?.signer || !posAddress) {
      setScriptOutput('❌ Need provider, wallet, and PoS address. Connect first.')
      return
    }
    setScriptRunning(true)
    setScriptOutput('⏳ Running...')
    try {
      const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor
      const fn = new AsyncFunction('provider', 'ethers', 'wallet', 'posAddress', 'PoSABI', scriptCode)
      const result = await fn(provider, ethers, wallet, posAddress, PoSABI)
      setScriptOutput(result !== undefined ? String(result) : '✓ (no return value)')
    } catch (e) {
      setScriptOutput('❌ ' + (e.reason || e.message || String(e)))
    } finally {
      setScriptRunning(false)
    }
  }, [provider, wallet, posAddress, scriptCode])

  // Reset entire session - clears all user data and creates fresh start
  const resetSession = () => {
    if (!window.confirm('🔄 Reset your session?\n\nThis will:\n• Create a new wallet identity\n• Clear all progress\n• Clear chat nickname\n\nYour test ETH will be lost. Continue?')) {
      return;
    }
    
    // Clear all localStorage keys
    const keysToRemove = [
      'eth_lab_wallet_pk',      // Wallet private key
      'learning_trail',         // Learning progress
      'explore_progress',       // Explore section progress
      'lab_feedback',           // Feedback data
      'quiz_scores',            // Quiz scores
      'session_start',          // Session start time
      'classmate_nicknames',    // Classmate nicknames
      'pos_addr',               // Contract address (will reload default)
      'my_nickname',            // User's own nickname
      'scenario_role',          // Frontend-only role assignment
      'ransom_addr',
      'car_sale_addr',
      'marketplace_addr',
    ];
    
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    // Clear sessionStorage too
    sessionStorage.removeItem('guest_sk');
    
    // Reset React state
    setTrail({ intro: false, concepts: false, explore: false });
    setExploreProgress([false, false, false]);
    setWallet({ address: null, signer: null, balance: '0', mode: null });
    setMessages([]);
    setValidators([]);
    setTxHistory([]);
    setMyStake({ 
      amount: '0', 
      reward: '0',
      slashCount: 0,
      blocksProposed: 0,
      missedAttestations: 0,
      unbondingTime: 0,
      minStakeDuration: 0,
      hasAttestedThisEpoch: false,
      unbondingStartTime: 0,
      lastProposedBlockNumber: 0,
      role: ''
    });
    setNicknames({});
    setMyNickname('');
    setWithdrawalRequested(false);
    hasAutoJoined.current = false;
    
    // Record new session start
    localStorage.setItem('session_start', Date.now().toString());
    
    // Reload the page to ensure clean state
    setStatusMsg('🔄 Session reset! Reloading...');
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  };

  const markStageComplete = (stage) => {
    if (trail[stage]) return
    const updated = { ...trail, [stage]: true }
    saveTrail(updated)
  }

  useEffect(() => {
    localStorage.setItem('explore_progress', JSON.stringify(exploreProgress))
  }, [exploreProgress])

  const unlocks = {
    intro: true,
    concepts: true, // Always unlocked
    explore: true, // Always unlocked
    sim: true, // Always unlocked - Explore flows directly to Sim
    live: true, // Always unlocked - students can go straight to live network
    cli: true // Always unlocked - CLI labs
  }

  const fireProgressBeacon = (routeId) => {
    if (!routeId) return;
    const key = `eth_progress_${routeId}`;
    const now = Date.now();
    const last = parseInt(sessionStorage.getItem(key) || '0', 10);
    if (now - last < 5000) return;
    sessionStorage.setItem(key, String(now));
    fetch('/api/ethereum/progress/touch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ route_id: `exercise:${routeId}` }),
      keepalive: true,
    }).catch(() => {});
  };

  const VIEW_BEACON_MAP = {
    intro: 'eth-trail-intro',
    concepts: 'eth-trail-concepts',
    explore: 'eth-trail-explore',
    sim: 'eth-sim',
    live: 'eth-live',
    tokens: 'eth-tokens',
    cli: 'eth-cli',
    diagnostics: 'eth-diagnostics',
    'beacon-lab': 'eth-beacon-lab',
    'contract-builder-lab': 'eth-contract-write',
    'tokenization-lab': 'eth-token-erc721',
  };

  useEffect(() => {
    fireProgressBeacon(VIEW_BEACON_MAP[view]);
  }, [view]);

  useEffect(() => {
    fetch('/api/ethereum/progress/touch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ route_id: 'home' }),
      keepalive: true,
    }).catch(() => {});
  }, []);

  const requestView = (target) => {
        setView(target)
        setNavHint('')
  }

  // 0. Save default contract address to localStorage if not already saved
  useEffect(() => {
    if (posAddress && posAddress.length === 42 && !localStorage.getItem("pos_addr")) {
      localStorage.setItem("pos_addr", posAddress);
    }
  }, [posAddress]);

  // 1. Initialize Provider (use staticNetwork to avoid "network does not support ENS" on local/custom chains)
  useEffect(() => {
    const sanitizedUrl = (rpcUrl || "").trim()
    if (!sanitizedUrl) {
        setProvider(null)
        setNodeStatus({ connected: false, blockNumber: 0 })
        return
    }
    const resolvedUrl = resolveRpcUrl(sanitizedUrl)
    let cancelled = false
    const init = async () => {
      try {
        const temp = new ethers.JsonRpcProvider(resolvedUrl)
        let chainId = 31337
        try {
          const network = await temp.getNetwork()
          if (cancelled) return
          chainId = Number(network.chainId)
        } catch (_) {
          // RPC may not be ready; use 31337 for local Hardhat
          if (/localhost|127\.0\.0\.1|8545|\/rpc-proxy|\/rpc/.test(sanitizedUrl)) chainId = 31337
        }
        if (cancelled) return
        const staticNet = ethers.Network.from(chainId)
        const newProvider = new ethers.JsonRpcProvider(resolvedUrl, staticNet, { staticNetwork: staticNet })
        setProvider(newProvider)
      } catch (e) {
        if (!cancelled) {
          console.error("Invalid RPC URL:", e)
          setProvider(null)
          setNodeStatus({ connected: false, blockNumber: 0 })
        }
      }
    }
    init()
    return () => { cancelled = true }
  }, [rpcUrl])

  // Sync RpcClient with app rpcUrl so InstructorView, faucet, etc. use same chain
  useEffect(() => {
    if (rpcUrl?.trim()) rpcClient.setRpcUrl(rpcUrl);
  }, [rpcUrl]);

  // 2. Auto-Connect Logic (Live Mode and Token Concepts need wallet for deploy/interact)
  // Skip auto-wallet if new student (by IP) must create first — no auto-EOA
  const hasLocalWallet = getWalletList().length > 0
  const mustCreateWalletFirst = !session.hasCreatedWallet && !hasLocalWallet && !session.loading

  useEffect(() => {
    if ((view !== 'live' && view !== 'tokens') || !provider || wallet.mode === 'metamask') return;
    if (mustCreateWalletFirst) return; // Show create flow, don't auto-create

    let cancelled = false

    const check = async () => {
      try {
        const bn = await provider.getBlockNumber()
        if (!cancelled) {
        setNodeStatus({ connected: true, blockNumber: bn })
        }
      } catch (e) { 
        if (!cancelled) {
            setNodeStatus({ connected: false, blockNumber: 0 })
        }
      }
    }
    check();
    const interval = setInterval(check, 2000);

    const hydrateGuestWallet = async () => {
        try {
        const { mode, signer } = getGuestWallet()
            const addr = await signer.getAddress()
             const connectedSigner = signer.connect(provider)
             const bal = await provider.getBalance(addr).catch(() => 0n)
             // Get wallet nickname from storage
             const walletInfo = getWalletInfo()
             const nickname = walletInfo?.nickname || 'My Wallet'
            if (!cancelled) {
                setWallet(prev => ({
                    ...prev,
                    address: addr,
                    signer: connectedSigner,
                    balance: ethers.formatEther(bal),
                    mode: mode || 'guest',
                    nickname: nickname
                }))
                // Register wallet creation with Lab API (per-IP) so future visits don't require create-first
                if (!session.hasCreatedWallet) {
                  fetch(import.meta.env.BASE_URL + 'lab-api/register-wallet', { method: 'POST' }).catch(() => {})
                  setSession(prev => ({ ...prev, hasCreatedWallet: true }))
                }
            }
        } catch (err) {
            console.error("Guest wallet init failed:", err)
        }
    }

    hydrateGuestWallet()

    const onWalletSwitched = () => hydrateGuestWallet()
    window.addEventListener('walletSwitched', onWalletSwitched)

    return () => {
        cancelled = true
        clearInterval(interval)
        window.removeEventListener('walletSwitched', onWalletSwitched)
    }
  }, [provider, view, wallet.mode, mustCreateWalletFirst, session.hasCreatedWallet]);

  // 3. Auto-Join Class List when wallet is ready
  useEffect(() => {
    // Reset auto-join flag when leaving live view
    if (view !== 'live') {
      hasAutoJoined.current = false;
      return;
    }
    
    // Only auto-join with valid wallet and contract
    if (!wallet.address || !wallet.signer || !posAddress || posAddress.length !== 42) return;
    // Don't re-join if already in validators list or already attempted this session
    if (validators.includes(wallet.address) || hasAutoJoined.current) return;
    
    const autoJoinClass = async () => {
      hasAutoJoined.current = true; // Mark as attempted
      console.log("[AutoJoin] Joining class as:", wallet.address);
      
      try {
        // Check if wallet has funds - can't join without gas
        const balance = await provider.getBalance(wallet.address);
        if (balance === 0n) {
          console.log("[AutoJoin] Wallet has no funds, skipping auto-join (user needs funds from instructor first)");
          hasAutoJoined.current = false; // Allow retry after they get funds
          return;
        }
        
        // Verify contract exists before trying to join
        const code = await provider.getCode(posAddress);
        if (code === '0x' || code === '0x0') {
          console.log("[AutoJoin] Contract not deployed yet, skipping auto-join");
          hasAutoJoined.current = false; // Allow retry when contract is ready
          return;
        }
        
        setStatusMsg("👋 Joining class...");
        const contract = new ethers.Contract(posAddress, PoSABI, wallet.signer);
        const tx = await contract.sendMessage("👋 Joined the class!");
        await tx.wait();
        console.log("[AutoJoin] Successfully joined class");
        setStatusMsg("✅ Joined class!");
        
        // Refresh data to show in classmates list  
        blockchainSync.forceRefresh();
        
        setTimeout(() => setStatusMsg(""), 2000);
      } catch (err) {
        console.error("[AutoJoin] Failed:", err);
        // Don't show error to user - they can manually join if needed
        hasAutoJoined.current = false; // Allow retry on next attempt
      }
    };
    
    // Delay auto-join to ensure wallet is fully initialized
    const timer = setTimeout(autoJoinClass, 1500);
    return () => clearTimeout(timer);
  }, [view, wallet.address, wallet.signer, posAddress, validators]);

  // Real-time balance updates and transaction history
  useEffect(() => {
    if (!provider || !wallet.address || view !== 'live') return;
    
    const updateBalance = async () => {
      try {
        const bal = await provider.getBalance(wallet.address)
        setWallet(prev => ({ ...prev, balance: ethers.formatEther(bal) }))
      } catch (e) {
        console.error("Balance update error:", e)
      }
    }
    
    const fetchTxHistory = async () => {
      try {
        const currentBlock = await provider.getBlockNumber()
        const history = []
        
        // Get last 50 blocks of transactions (reduced for performance)
        const startBlock = Math.max(0, currentBlock - 50);
        for (let i = startBlock; i <= currentBlock; i++) {
          try {
            const block = await provider.getBlock(i, true) // true = prefetchedTransactions
            if (block && block.prefetchedTransactions) {
              // Ethers v6 uses prefetchedTransactions
              for (const tx of block.prefetchedTransactions) {
                const fromAddr = tx.from?.toLowerCase();
                const toAddr = tx.to?.toLowerCase();
                const myAddr = wallet.address?.toLowerCase();
                
                if (fromAddr === myAddr || toAddr === myAddr) {
                  history.push({
                    hash: tx.hash,
                    from: tx.from,
                    to: tx.to || 'Contract Creation',
                    value: ethers.formatEther(tx.value || 0n),
                    blockNumber: i,
                    timestamp: Number(block.timestamp),
                    type: fromAddr === myAddr ? 'sent' : 'received'
                  })
                }
              }
            }
          } catch (blockErr) {
            // Skip individual block errors
            console.debug(`Skipping block ${i}:`, blockErr.message);
          }
        }
        
        if (history.length > 0) {
          setTxHistory(history.sort((a, b) => b.timestamp - a.timestamp).slice(0, 20))
        }
      } catch (e) {
        console.error("Transaction history error:", e)
      }
    }
    
    // Live tab: only fetch role/roleContract (staking is in Beacon Lab)
    const fetchRoleInfo = async () => {
      if (!posAddress || posAddress.length !== 42) return
      try {
        const code = await provider.getCode(posAddress)
        if (code === '0x' || code === '0x0') return
        const contract = new ethers.Contract(posAddress, PoSABI, provider)
        const roleContract = await contract.roleContractAddress(wallet.address)
        const role = localStorage.getItem('scenario_role') || ''
        setMyStake(prev => ({
          ...prev,
          role: role || prev.role || '',
          roleContract: roleContract && roleContract !== ethers.ZeroAddress ? roleContract : prev.roleContract || null
        }))
        lastSyncRef.current = Date.now()
        setLastSyncTime(Date.now())
      } catch (e) {
        if (!e.message?.includes('BAD_DATA') && !e.message?.includes('could not decode')) {
          console.error("Role info error:", e)
        }
      }
    }
    
    // Initial updates
    updateBalance()
    fetchTxHistory()
    fetchRoleInfo()
    
    // Fast polling for balance, role, tx history (no stake data on Live)
    let pollCount = 0;
    const interval = setInterval(() => {
      pollCount++;
      updateBalance();
      if (pollCount % 2 === 0) fetchRoleInfo();
      if (pollCount % 5 === 0) fetchTxHistory();
    }, 1000);
    
    return () => clearInterval(interval);
  }, [provider, wallet.address, view, posAddress])

  // Handle account change from AccountManager
  const handleAccountChange = async (newWalletInfo) => {
    // Handle logout case - user logged out, refresh to get new guest wallet
    if (!newWalletInfo) {
      setStatusMsg('🔄 Logging out... Creating new wallet');
      setShowAccountManager(false);
      
      // Trigger re-initialization of guest wallet by resetting wallet state
      setWallet({ address: null, signer: null, balance: '0', mode: null, nickname: 'My Wallet' });
      hasAutoJoined.current = false;
      
      // The useEffect that runs hydrateGuestWallet will create a new wallet
      setTimeout(() => {
        window.location.reload();
      }, 500);
      return;
    }
    
    if (!newWalletInfo.address) return;
    
    try {
      // Create a new signer from the private key
      const newWallet = new ethers.Wallet(newWalletInfo.privateKey);
      const connectedSigner = newWallet.connect(provider);
      const bal = await provider.getBalance(newWalletInfo.address).catch(() => 0n);
      
      setWallet({
        address: newWalletInfo.address,
        signer: connectedSigner,
        balance: ethers.formatEther(bal),
        mode: 'imported',
        nickname: newWalletInfo.nickname || 'My Wallet'
      });
      
      // Reset auto-join flag so the new wallet can join the class
      hasAutoJoined.current = false;
      
      setStatusMsg(`✅ Account switched to ${newWalletInfo.nickname || newWalletInfo.address.slice(0,8)}`);
      setTimeout(() => setStatusMsg(''), 3000);
      setShowAccountManager(false);
    } catch (err) {
      console.error("Account switch failed:", err);
      setStatusMsg("❌ Failed to switch account: " + err.message);
    }
  };

  // Helpers - No faucet; instructor funds students via Instructor dashboard

  const sendEthToPeer = async () => {
      if(!ethers.isAddress(recipient)) return setStatusMsg("Invalid Recipient Address")
      if(!sendAmount) return setStatusMsg("Enter amount")
      
      // Prevent double-sending
      if (statusMsg.includes("Sending ETH")) {
          return setStatusMsg("Transaction already in progress...")
      }
      
      try {
          setStatusMsg("Sending ETH...")
          const tx = await wallet.signer.sendTransaction({
              to: recipient,
              value: ethers.parseEther(sendAmount)
          })
          const receipt = await tx.wait()
          setStatusMsg(`Sent ${sendAmount} ETH to ${recipient.slice(0,6)}!`)
          
          // Immediately add to transaction history
          setTxHistory(prev => [{
            hash: tx.hash,
            from: wallet.address,
            to: recipient,
            value: sendAmount,
            blockNumber: receipt.blockNumber,
            timestamp: Math.floor(Date.now() / 1000),
            type: 'sent'
          }, ...prev].slice(0, 20))
          
          setSendAmount("")
          setRecipient("") // Clear recipient after successful send
          
          // Update balance immediately
          const bal = await provider.getBalance(wallet.address)
          setWallet(prev => ({ ...prev, balance: ethers.formatEther(bal) }))
          
          // Clear status after 3 seconds
          setTimeout(() => setStatusMsg(""), 3000)
      } catch (e) { 
          setStatusMsg("Transfer Failed: " + e.message)
          setTimeout(() => setStatusMsg(""), 5000)
      }
  }
  
  // Data Sync
  const syncBlockchainData = async () => {
      if (!posAddress || posAddress.length !== 42 || !provider) return
      setIsSyncing(true)
      try {
        // Verify contract exists before querying
        const code = await provider.getCode(posAddress)
        if (code === '0x' || code === '0x0') {
          setIsSyncing(false)
          return // Contract not deployed yet
        }
        
        const contract = new ethers.Contract(posAddress, PoSABI, provider)
        
        // Chat
        const chatEvents = await contract.queryFilter("NewMessage", 0)
        const formattedChat = chatEvents.map(e => {
          const a = e.args || []
          return {
            sender: a[0] ?? a.sender,
            text: a[1] ?? a.message ?? '',
            timestamp: Number(a[2] ?? a.timestamp ?? 0)
          }
        }).sort((a,b) => a.timestamp - b.timestamp)
        setMessages(formattedChat)

        // Inline role parsing right after fetching messages
        if (wallet.address && formattedChat.length > 0) {
          const role = parseRoleFromMessages(formattedChat, wallet.address, validators);
          if (role) {
            console.log('[syncBlockchainData] Inline role found:', role);
            localStorage.setItem('scenario_role', role);
            setMyStake(prev => ({ ...prev, role }));
          }
        }

        // Roster Logic: Anyone who Staked OR Chatted is a "Participant"
        const stakeEvents = await contract.queryFilter("Staked", 0)
        const msgEvents = await contract.queryFilter("NewMessage", 0)
        const allAddrs = [
          ...stakeEvents.map(e => (e.args && (e.args[0] ?? e.args.validator))),
          ...msgEvents.map(e => (e.args && (e.args[0] ?? e.args.sender)))
        ].filter(Boolean)
        const uniqueAddrs = [...new Set(allAddrs)]
        
        // Only update if we have addresses (don't replace with empty)
        if (uniqueAddrs.length > 0) {
          setValidators(prev => {
            const combined = [...new Set([...prev, ...uniqueAddrs])];
            return combined;
          });
        }
        
        // Get actual validator count from contract (only those currently staking)
        const validatorCount = await contract.getValidatorCount()
        setActualValidatorCount(Number(validatorCount))

      } catch (e) {
        console.warn("syncBlockchainData error:", e);
      }
      setIsSyncing(false)
  }

   // Send chat message - accepts optional direct message to avoid state race conditions
   const sendChatMessage = async (directMessage = null) => {
      // If directMessage is an Event object (from onClick), ignore it and use chatInput
      const messageToSend = (typeof directMessage === 'string') ? directMessage : chatInput;
      if(!messageToSend?.trim()) {
          console.log("[Chat] No message to send");
          return false;
      }
      if(!posAddress || posAddress.length !== 42) {
          setStatusMsg("❌ Invalid Contract Address");
          return false;
      }
      if(!rpcUrl) {
          setStatusMsg("❌ No RPC URL configured");
          return false;
      }
      if(!wallet.signer) {
          setStatusMsg("❌ Wallet not ready. Please wait...");
          return false;
      }
      
      try {
          // Verify contract exists
          const code = await provider.getCode(posAddress);
          if (code === '0x' || code === '0x0') {
              setStatusMsg("❌ Contract not deployed. Is the instructor's node running?");
              return false;
          }
          
          setStatusMsg("📤 Sending message...");
          
          // Use the user's wallet to send the message (so sender is correctly recorded)
          const contract = new ethers.Contract(posAddress, PoSABI, wallet.signer);
          
          console.log("[Chat] Sending as:", wallet.address, "Message:", messageToSend);
          const tx = await contract.sendMessage(messageToSend);
          
          // Clear input if we used the chatInput state (not a direct string message)
          if (typeof directMessage !== 'string') {
              setChatInput("");
          }
          
          setStatusMsg("⏳ Confirming...");
          await tx.wait();
          
          console.log("[Chat] Message confirmed");
          setStatusMsg("✅ Message sent!");
          
          // Trigger sync to update classmates list
          syncBlockchainData();
          blockchainSync.forceRefresh();
          
          setTimeout(() => setStatusMsg(""), 2000);
          return true;
          
      } catch (err) { 
          console.error("[Chat] Error:", err);
          const reason = err.reason || err.message || "Unknown error";
          setStatusMsg("❌ Chat failed: " + reason);
          return false;
      }
  }

  // "I am Here" Button - joins the class by sending a message
  const broadcastPresence = async () => {
      // Pass message directly to avoid React state race condition
      const nickname = myNickname ? ` [NICK:${myNickname}]` : "";
      const success = await sendChatMessage(`👋 Joined the class!${nickname}`);
      if (success) {
          // Force immediate refresh of validators list
          setTimeout(() => {
              syncBlockchainData();
              blockchainSync.forceRefresh();
          }, 500);
      }
  }
  
  // Set and broadcast nickname
  const saveNickname = async (newNickname) => {
    const trimmed = newNickname.trim().slice(0, 20); // Max 20 chars
    if (!trimmed) return;
    
    setMyNickname(trimmed);
    localStorage.setItem("my_nickname", trimmed);
    setEditingNickname(false);
    
    // Also save to local nicknames map for own address
    if (wallet.address) {
      setNicknames(prev => {
        const updated = { ...prev, [wallet.address.toLowerCase()]: trimmed };
        localStorage.setItem("classmate_nicknames", JSON.stringify(updated));
        return updated;
      });
    }
    
    // Broadcast to blockchain if connected
    if (wallet.signer && posAddress) {
      try {
        const success = await sendChatMessage(`📛 Set nickname: ${trimmed} [NICK:${trimmed}]`);
        if (success) {
          setStatusMsg(`✅ Nickname "${trimmed}" saved & broadcast!`);
          setTimeout(() => setStatusMsg(""), 3000);
        }
      } catch (err) {
        console.error("Failed to broadcast nickname:", err);
        // Still saved locally, just not broadcast
        setStatusMsg(`✅ Nickname saved locally`);
        setTimeout(() => setStatusMsg(""), 2000);
      }
    }
  };
  
  // Helper to get display name for an address
  const getDisplayName = (address) => {
    if (!address) return "Unknown";
    const lowerAddr = address.toLowerCase();
    const nickname = nicknames[lowerAddr];
    const shortAddr = `${address.slice(0,6)}...${address.slice(-4)}`;
    return nickname ? `${nickname} (${shortAddr})` : shortAddr;
  };

  const copyAddress = async (addr) => {
      const ok = await copyToClipboard(addr);
      setStatusMsg(ok ? `Copied ${addr.slice(0,6)}...` : 'Copy failed — try selecting the address manually');
  }

  const getSessionAge = () => {
      const minutes = Math.floor((Date.now() - sessionStart) / 60000)
      return minutes
  }
  
  // Refresh sync indicator every second
  const [, forceUpdate] = useState(0);
  useEffect(() => {
    if (view === 'live') {
      const timer = setInterval(() => forceUpdate(n => n + 1), 1000);
      return () => clearInterval(timer);
    }
  }, [view]);

  // Enhanced blockchain sync using centralized service
  useEffect(() => {
    if (view === 'live' && posAddress.length === 42 && provider) {
      // Initialize the sync service
      blockchainSync.init(provider, posAddress);
      
      // Subscribe to updates from centralized sync
      const unsubscribe = blockchainSync.subscribe((data) => {
        if (data.error) {
          console.warn('[App] Sync error:', data.error);
          return;
        }
        
        // Update messages (only if we have messages)
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
          
          // Inline role parsing — don't wait for useEffect
          if (wallet.address) {
            const role = parseRoleFromMessages(data.messages, wallet.address, data.validators || []);
            if (role) {
              console.log('[App] Subscriber: inline role =', role);
              localStorage.setItem('scenario_role', role);
              setMyStake(prev => ({ ...prev, role }));
            }
          }
          
          // Parse messages for nickname announcements (format: [NICK:NickName])
          const newNicknames = {};
          data.messages.forEach(msg => {
            const text = msg?.text ?? msg?.message ?? '';
            const nickMatch = text.match?.(/\[NICK:([^\]]+)\]/);
            if (nickMatch) {
              newNicknames[(msg.sender || '').toLowerCase()] = nickMatch[1].trim();
            }
          });
          if (Object.keys(newNicknames).length > 0) {
            setNicknames(prev => {
              const merged = { ...prev, ...newNicknames };
              localStorage.setItem("classmate_nicknames", JSON.stringify(merged));
              return merged;
            });
          }
        }
        
        // Update validators list (merge with existing, don't replace with empty)
        if (data.validators && data.validators.length > 0) {
          setValidators(prev => {
            const combined = [...new Set([...prev, ...data.validators])];
            return combined;
          });
        }
        
        // Update network stats (skip on Live - staking is in Beacon Lab)
        if (data.network && view !== 'live') {
          setCurrentEpoch(data.network.currentEpoch);
          setTimeUntilNextEpoch(data.network.timeUntilNextEpoch);
          setCurrentAPY(data.network.currentAPY);
          setActualValidatorCount(data.network.validatorCount || 0);
        }
        
        console.log('[App] Sync update - Block:', data.blockNumber, 'Validators:', data.validators?.length || 0);
      });
      
      return () => {
        unsubscribe();
      };
    }
  }, [posAddress, provider, view])


  // Compute current mode from view
  const currentMode = ['intro', 'concepts', 'explore', 'sim', 'tokens'].includes(view) 
    ? 'learning' 
    : ['live', 'diagnostics', 'beacon-lab', 'contract-builder-lab', 'tokenization-lab'].includes(view)
      ? 'live' 
      : view === 'cli' 
        ? 'cli' 
        : 'instructor';

  return (
    <div className="app-layout">
        {/* NAVIGATION SIDEBAR */}
        <aside className="nav-sidebar">
            <h1>Ethereum Trainer</h1>
            
            {/* ============= MODE SWITCHER (TOP-LEVEL TABS) ============= */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '8px',
                marginBottom: '1.5rem',
                background: 'rgba(0,0,0,0.3)',
                padding: '8px',
                borderRadius: '12px'
            }}>
                <button 
                    onClick={() => { setView('intro'); }}
                    style={{
                        padding: '12px 8px',
                        background: currentMode === 'learning' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
                        border: currentMode === 'learning' ? 'none' : '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: currentMode === 'learning' ? 'white' : '#94a3b8',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        fontWeight: currentMode === 'learning' ? 'bold' : 'normal',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '4px',
                        transition: 'all 0.2s'
                    }}
                >
                    <span style={{fontSize: '1.2rem'}}>📚</span>
                    Learn
                </button>
                <button 
                    onClick={() => { setView('live'); }}
                    style={{
                        padding: '12px 8px',
                        background: currentMode === 'live' ? 'linear-gradient(135deg, #10b981 0%, #34d399 100%)' : 'transparent',
                        border: currentMode === 'live' ? 'none' : '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: currentMode === 'live' ? 'white' : '#94a3b8',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        fontWeight: currentMode === 'live' ? 'bold' : 'normal',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '4px',
                        transition: 'all 0.2s'
                    }}
                >
                    <span style={{fontSize: '1.2rem'}}>🌐</span>
                    Live
                </button>
                <button 
                    onClick={() => { setView('cli'); }}
                    style={{
                        padding: '12px 8px',
                        background: currentMode === 'cli' ? 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)' : 'transparent',
                        border: currentMode === 'cli' ? 'none' : '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: currentMode === 'cli' ? '#1e293b' : '#94a3b8',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        fontWeight: currentMode === 'cli' ? 'bold' : 'normal',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '4px',
                        transition: 'all 0.2s'
                    }}
                >
                    <span style={{fontSize: '1.2rem'}}>💻</span>
                    CLI
                </button>
                {isInstructor && (
                    <button 
                        onClick={() => { setView('instructor'); }}
                        style={{
                            padding: '12px 8px',
                            background: currentMode === 'instructor' ? 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)' : 'transparent',
                            border: currentMode === 'instructor' ? 'none' : '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '8px',
                            color: currentMode === 'instructor' ? 'white' : '#94a3b8',
                            cursor: 'pointer',
                            fontSize: '0.85rem',
                            fontWeight: currentMode === 'instructor' ? 'bold' : 'normal',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '4px',
                            transition: 'all 0.2s'
                        }}
                    >
                        <span style={{fontSize: '1.2rem'}}>🎓</span>
                        Instructor
                    </button>
                )}
            </div>
            
            {/* ============= LEARNING MODE SIDEBAR ============= */}
            {currentMode === 'learning' && (
                <nav>
                    <div style={{
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginBottom: '0.75rem',
                        paddingLeft: '0.5rem'
                    }}>
                        Learning Path
                    </div>
                    <div className="learning-roadmap">
                        <button className={`roadmap-step ${view === 'intro' ? 'active' : ''} ${trail.intro ? 'done' : ''}`} onClick={() => requestView('intro')}>
                            <span>1</span> Orientation
                        </button>
                        <button className={`roadmap-step ${view === 'concepts' ? 'active' : ''} ${trail.concepts ? 'done' : ''} ${!unlocks.concepts ? 'locked' : ''}`} onClick={() => requestView('concepts')}>
                            <span>2</span> Basics
                        </button>
                        <button className={`roadmap-step ${view === 'explore' ? 'active' : ''} ${trail.explore ? 'done' : ''} ${!unlocks.explore ? 'locked' : ''}`} onClick={() => requestView('explore')}>
                            <span>3</span> Explore
                        </button>
                        <button className={`roadmap-step ${view === 'sim' ? 'active' : ''} ${!unlocks.sim ? 'locked' : ''}`} onClick={() => requestView('sim')}>
                            <span>4</span> Test Your Knowledge
                        </button>
                        <button className={`roadmap-step ${view === 'tokens' ? 'active' : ''}`} onClick={() => setView('tokens')}>
                            <span>5</span> Token Concepts (FT vs NFT)
                        </button>
                    </div>
                    {navHint && <p className="nav-hint">{navHint}</p>}
                    
                    <div style={{
                        marginTop: '1.5rem',
                        padding: '1rem',
                        background: 'rgba(16,185,129,0.1)',
                        borderRadius: '0.75rem',
                        border: '1px solid rgba(16,185,129,0.3)'
                    }}>
                        <div style={{fontSize: '0.8rem', color: '#6ee7b7', marginBottom: '0.5rem'}}>
                            Ready for hands-on?
                        </div>
                        <button 
                            onClick={() => setView('live')}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                border: 'none',
                                borderRadius: '0.5rem',
                                color: 'white',
                                fontWeight: 'bold',
                                cursor: 'pointer',
                                fontSize: '0.9rem'
                            }}
                        >
                            Go to Live Network →
                        </button>
                    </div>
                </nav>
            )}
            
            {/* ============= LIVE NETWORK MODE SIDEBAR ============= */}
            {currentMode === 'live' && (
                <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
                    <div style={{
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginBottom: '0.75rem',
                        paddingLeft: '0.5rem'
                    }}>
                        Live Network
                    </div>
                    
                    {/* Connection Status Mini */}
                    <div style={{
                        padding: '0.75rem',
                        background: nodeStatus.connected ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        borderRadius: '0.5rem',
                        marginBottom: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <div style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            background: nodeStatus.connected ? '#10b981' : '#ef4444',
                            animation: nodeStatus.connected ? 'pulse 2s infinite' : 'none'
                        }}></div>
                        <span style={{
                            fontSize: '0.8rem',
                            color: nodeStatus.connected ? '#34d399' : '#fca5a5',
                            fontWeight: 'bold'
                        }}>
                            {nodeStatus.connected ? `Block #${nodeStatus.blockNumber}` : 'Disconnected'}
                        </span>
                    </div>
                    
                    {/* Account Switcher */}
                    <div style={{
                        padding: '0.75rem',
                        background: 'rgba(59, 130, 246, 0.15)',
                        borderRadius: '0.5rem',
                        marginBottom: '1rem',
                        border: '1px solid rgba(59, 130, 246, 0.3)'
                    }}>
                        <div style={{fontSize: '0.75rem', color: '#60a5fa', marginBottom: '0.5rem'}}>
                            👤 Your Account
                        </div>
                        <div style={{fontSize: '0.8rem', color: '#f1f5f9', marginBottom: '0.5rem'}}>
                            {(() => {
                                const wallets = getWalletList();
                                const activeInfo = getWalletInfo();
                                if (wallets.length === 0) return <span style={{fontFamily: 'monospace', color: '#64748b'}}>No wallet</span>;
                                return (
                                    <select
                                        value={activeInfo?.address || ''}
                                        onChange={(e) => {
                                            const w = wallets.find(x => x.address === e.target.value);
                                            if (w) setActiveWallet(w.id);
                                        }}
                                        style={{
                                            width: '100%',
                                            padding: '0.35rem',
                                            background: 'rgba(0,0,0,0.3)',
                                            border: '1px solid rgba(59, 130, 246, 0.4)',
                                            borderRadius: '0.25rem',
                                            color: '#f1f5f9',
                                            fontSize: '0.8rem',
                                            fontFamily: 'monospace'
                                        }}
                                    >
                                        {wallets.map((w) => (
                                            <option key={w.id} value={w.address}>
                                                {w.nickname} ({w.address.slice(0,6)}...{w.address.slice(-4)}) {w.address === wallet?.address ? '● Active' : ''}
                                            </option>
                                        ))}
                                    </select>
                                );
                            })()}
                        </div>
                        <div style={{display: 'flex', gap: '0.5rem', flexWrap: 'wrap'}}>
                            <button
                                onClick={() => {
                                    let key = prompt('Enter private key (0x...) to import:');
                                    if (!key) return;
                                    key = key.trim();
                                    if (!key.startsWith('0x') && key.length === 64) key = '0x' + key;
                                    if (key.startsWith('0x') && key.length === 66) {
                                        const result = importWallet(key, 'Imported Wallet');
                                        if (result.success) {
                                            window.dispatchEvent(new CustomEvent('walletSwitched'));
                                        } else {
                                            alert('Import failed. Please check your private key.');
                                        }
                                    } else {
                                        alert(`Invalid key format. Expected: 66 chars starting with 0x. Got: ${key.length}`);
                                    }
                                }}
                                style={{
                                    flex: 1,
                                    padding: '0.5rem',
                                    background: 'rgba(34, 197, 94, 0.2)',
                                    border: '1px solid rgba(34, 197, 94, 0.4)',
                                    borderRadius: '0.35rem',
                                    color: '#86efac',
                                    cursor: 'pointer',
                                    fontSize: '0.75rem',
                                    fontWeight: '600'
                                }}
                            >
                                📥 Import
                            </button>
                            <button
                                onClick={() => {
                                    const nickname = prompt('Enter a nickname for your new wallet:') || 'My Wallet';
                                    const newWallet = generateNewWallet(nickname);
                                    setNewWalletModal({ address: newWallet.address, privateKey: newWallet.privateKey });
                                    window.dispatchEvent(new CustomEvent('walletSwitched'));
                                }}
                                style={{
                                    flex: 1,
                                    padding: '0.5rem',
                                    background: 'rgba(59, 130, 246, 0.2)',
                                    border: '1px solid rgba(59, 130, 246, 0.4)',
                                    borderRadius: '0.35rem',
                                    color: '#93c5fd',
                                    cursor: 'pointer',
                                    fontSize: '0.75rem',
                                    fontWeight: '600'
                                }}
                            >
                                🔑 New
                            </button>
                            <button
                                onClick={() => {
                                    const walletInfo = getWalletInfo();
                                    if (walletInfo) {
                                        const show = confirm(`Your Private Key:\n\n${walletInfo.privateKey}\n\nClick OK to copy to clipboard`);
                                        if (show) {
                                            navigator.clipboard.writeText(walletInfo.privateKey);
                                            alert('Private key copied to clipboard!\n\n⚠️ Keep it safe and never share it!');
                                        }
                                    } else {
                                        alert('No wallet found');
                                    }
                                }}
                                style={{
                                    flex: 1,
                                    padding: '0.5rem',
                                    background: 'rgba(251, 191, 36, 0.2)',
                                    border: '1px solid rgba(251, 191, 36, 0.4)',
                                    borderRadius: '0.35rem',
                                    color: '#fcd34d',
                                    cursor: 'pointer',
                                    fontSize: '0.75rem',
                                    fontWeight: '600'
                                }}
                            >
                                🔐 Export
                            </button>
                        </div>
                    </div>

                    {/* Diagnostics quick access */}
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                        <button
                            onClick={() => setView('diagnostics')}
                            disabled={view === 'diagnostics'}
                            style={{
                                flex: 1,
                                padding: '0.6rem',
                                borderRadius: '0.5rem',
                                border: '1px solid rgba(59,130,246,0.35)',
                                background: view === 'diagnostics' ? 'rgba(59,130,246,0.25)' : 'rgba(59,130,246,0.12)',
                                color: '#bfdbfe',
                                fontWeight: 'bold',
                                cursor: view === 'diagnostics' ? 'not-allowed' : 'pointer',
                                fontSize: '0.8rem'
                            }}
                            title="Run safe connectivity checks"
                        >
                            🧪 Diagnostics
                        </button>
                        {view !== 'live' && (
                            <button
                                onClick={() => setView('live')}
                                style={{
                                    padding: '0.6rem 0.7rem',
                                    borderRadius: '0.5rem',
                                    border: '1px solid rgba(255,255,255,0.12)',
                                    background: 'rgba(0,0,0,0.2)',
                                    color: '#e2e8f0',
                                    fontWeight: 'bold',
                                    cursor: 'pointer',
                                    fontSize: '0.8rem'
                                }}
                                title="Back to Live Network"
                            >
                                ↩ Live
                            </button>
                        )}
                    </div>

                    {/* Labs Section */}
                    <div style={{
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginBottom: '0.5rem',
                        paddingLeft: '0.5rem'
                    }}>
                        Hands-On Labs
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1rem' }}>
                        <button
                            onClick={() => setView('beacon-lab')}
                            style={{
                                width: '100%',
                                padding: '0.7rem',
                                background: view === 'beacon-lab' ? 'rgba(139,92,246,0.3)' : 'rgba(139,92,246,0.12)',
                                border: view === 'beacon-lab' ? '1px solid rgba(139,92,246,0.6)' : '1px solid rgba(139,92,246,0.3)',
                                borderRadius: '0.5rem',
                                color: '#c4b5fd',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: view === 'beacon-lab' ? 'bold' : 'normal',
                                textAlign: 'left'
                            }}
                        >
                            ⛓ Beacon Chain Lab
                        </button>
                        <button
                            onClick={() => setView('contract-builder-lab')}
                            style={{
                                width: '100%',
                                padding: '0.7rem',
                                background: view === 'contract-builder-lab' ? 'rgba(14,165,233,0.3)' : 'rgba(14,165,233,0.12)',
                                border: view === 'contract-builder-lab' ? '1px solid rgba(14,165,233,0.6)' : '1px solid rgba(14,165,233,0.3)',
                                borderRadius: '0.5rem',
                                color: '#7dd3fc',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: view === 'contract-builder-lab' ? 'bold' : 'normal',
                                textAlign: 'left'
                            }}
                        >
                            🏗 Contract Builder Lab
                        </button>
                        <button
                            onClick={() => setView('tokenization-lab')}
                            style={{
                                width: '100%',
                                padding: '0.7rem',
                                background: view === 'tokenization-lab' ? 'rgba(245,158,11,0.3)' : 'rgba(245,158,11,0.12)',
                                border: view === 'tokenization-lab' ? '1px solid rgba(245,158,11,0.6)' : '1px solid rgba(245,158,11,0.3)',
                                borderRadius: '0.5rem',
                                color: '#fcd34d',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: view === 'tokenization-lab' ? 'bold' : 'normal',
                                textAlign: 'left'
                            }}
                        >
                            🪙 Tokenization Lab
                        </button>
                    </div>

                    {/* 3D Chain Explorer */}
                    <button
                        onClick={() => navigate('/chain-3d')}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            marginBottom: '1rem',
                            background: 'rgba(34,255,136,0.15)',
                            border: '1px solid rgba(34,255,136,0.35)',
                            borderRadius: '0.5rem',
                            color: '#22ff88',
                            cursor: 'pointer',
                            fontSize: '0.9rem',
                            fontWeight: 'bold'
                        }}
                        title="3D Gibson-style blockchain visualization"
                    >
                        🎮 3D Chain Explorer
                    </button>

                    {/* Classmates Roster */}
                    <div className="roster-panel" style={{flex: 1}}>
                        <h3>👥 Classmates ({validators.filter(v => v && typeof v === 'string').length})</h3>
                        <p className="roster-hint">Click to copy/send</p>
                        
                        {/* Your Nickname Section */}
                        {wallet.address && (
                          <div style={{
                            padding: '0.75rem',
                            background: 'rgba(139, 92, 246, 0.15)',
                            borderRadius: '0.5rem',
                            marginBottom: '0.75rem',
                            border: '1px solid rgba(139, 92, 246, 0.3)'
                          }}>
                            <div style={{fontSize: '0.75rem', color: '#a78bfa', marginBottom: '0.5rem'}}>
                              📛 Your Nickname
                            </div>
                            {editingNickname ? (
                              <div style={{display: 'flex', gap: '0.5rem'}}>
                                <input
                                  type="text"
                                  value={nicknameInput}
                                  onChange={e => setNicknameInput(e.target.value)}
                                  onKeyDown={e => e.key === 'Enter' && saveNickname(nicknameInput)}
                                  placeholder="Enter nickname..."
                                  maxLength={20}
                                  autoFocus
                                  style={{
                                    flex: 1,
                                    padding: '0.4rem',
                                    background: 'rgba(0,0,0,0.3)',
                                    border: '1px solid #8b5cf6',
                                    borderRadius: '0.25rem',
                                    color: '#f8fafc',
                                    fontSize: '0.85rem'
                                  }}
                                />
                                <button
                                  onClick={() => saveNickname(nicknameInput)}
                                  style={{
                                    padding: '0.4rem 0.6rem',
                                    background: '#8b5cf6',
                                    border: 'none',
                                    borderRadius: '0.25rem',
                                    color: 'white',
                                    cursor: 'pointer',
                                    fontSize: '0.8rem'
                                  }}
                                >✓</button>
                                <button
                                  onClick={() => { setEditingNickname(false); setNicknameInput(myNickname); }}
                                  style={{
                                    padding: '0.4rem 0.6rem',
                                    background: 'rgba(255,255,255,0.1)',
                                    border: 'none',
                                    borderRadius: '0.25rem',
                                    color: '#94a3b8',
                                    cursor: 'pointer',
                                    fontSize: '0.8rem'
                                  }}
                                >✕</button>
                              </div>
                            ) : (
                              <div 
                                onClick={() => { setNicknameInput(myNickname); setEditingNickname(true); }}
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '0.5rem',
                                  cursor: 'pointer',
                                  padding: '0.4rem',
                                  background: 'rgba(0,0,0,0.2)',
                                  borderRadius: '0.25rem'
                                }}
                              >
                                <span style={{color: myNickname ? '#f8fafc' : '#64748b', fontWeight: myNickname ? '600' : '400'}}>
                                  {myNickname || 'Click to set nickname...'}
                                </span>
                                <span style={{marginLeft: 'auto', fontSize: '0.7rem', color: '#64748b'}}>✏️</span>
                              </div>
                            )}
                          </div>
                        )}
                        
                        <ul>
                            {validators.filter(v => v && typeof v === 'string').map(v => {
                                const nickname = nicknames[v.toLowerCase()];
                                const isYou = v === wallet.address;
                                return (
                                  <li key={v} onClick={() => copyAddress(v)} title={`Click to Copy: ${v}`}>
                                      <div className="avatar" style={{background: `#${v.slice(2,8)}`}}>
                                        {nickname ? nickname[0].toUpperCase() : ''}
                                      </div>
                                      <div className="roster-item-content">
                                          {nickname && (
                                            <span style={{fontWeight: '600', color: '#f8fafc'}}>{nickname}</span>
                                          )}
                                          <span style={{fontSize: nickname ? '0.75rem' : '0.9rem', color: nickname ? '#94a3b8' : '#f8fafc'}}>
                                            {v.slice(0,6)}...{v.slice(-4)}
                                          </span>
                                          {isYou && <span className="you-badge">(You)</span>}
                                      </div>
                                  </li>
                                );
                            })}
                        </ul>
                        {!validators.includes(wallet.address) && wallet.address && (
                            <button 
                                className="secondary-btn small-btn" 
                                onClick={broadcastPresence}
                                disabled={statusMsg.includes("Sending") || statusMsg.includes("Confirming")}
                                style={{
                                    opacity: (statusMsg.includes("Sending") || statusMsg.includes("Confirming")) ? 0.6 : 1,
                                    cursor: (statusMsg.includes("Sending") || statusMsg.includes("Confirming")) ? 'wait' : 'pointer'
                                }}
                            >
                                {statusMsg.includes("Sending") || statusMsg.includes("Confirming") 
                                    ? "⏳ Joining..." 
                                    : "👋 Join Class List"}
                            </button>
                        )}
                        {validators.includes(wallet.address) && (
                            <div style={{
                                padding: '0.5rem',
                                background: 'rgba(34, 197, 94, 0.2)',
                                borderRadius: '0.5rem',
                                fontSize: '0.8rem',
                                color: '#22c55e',
                                textAlign: 'center'
                            }}>
                                ✅ You're in the class!
                            </div>
                        )}
                        <div className="session-info">
                            <small>Your Session: {getSessionAge()} min</small>
                        </div>
                    </div>
                    
                    {/* Back to Learning Link */}
                    <div style={{
                        marginTop: 'auto',
                        padding: '1rem',
                        background: 'rgba(139,92,246,0.1)',
                        borderRadius: '0.75rem',
                        border: '1px solid rgba(139,92,246,0.3)'
                    }}>
                        <div style={{fontSize: '0.8rem', color: '#a78bfa', marginBottom: '0.5rem'}}>
                            📚 Need to review concepts?
                        </div>
                        <button 
                            onClick={() => setView('explore')}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                background: 'transparent',
                                border: '1px solid #8b5cf6',
                                borderRadius: '0.5rem',
                                color: '#a78bfa',
                                fontWeight: 'bold',
                                cursor: 'pointer',
                                fontSize: '0.85rem'
                            }}
                        >
                            ← Back to Learning
                        </button>
                    </div>
                </div>
            )}
            
            {/* ============= CLI MODE SIDEBAR ============= */}
            {currentMode === 'cli' && (
                <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
                    <div style={{
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginBottom: '0.75rem',
                        paddingLeft: '0.5rem'
                    }}>
                        CLI Labs
                    </div>
                    
                    <div style={{
                        padding: '1rem',
                        background: 'rgba(251, 191, 36, 0.1)',
                        borderRadius: '0.75rem',
                        border: '1px solid rgba(251, 191, 36, 0.3)',
                        marginBottom: '1rem'
                    }}>
                        <div style={{fontSize: '1rem', fontWeight: 'bold', color: '#fbbf24', marginBottom: '0.5rem'}}>
                            💻 Terminal Required
                        </div>
                        <p style={{fontSize: '0.85rem', color: '#cbd5e1', margin: 0}}>
                            These labs require command-line access. Start with <strong>Available Labs</strong> for step-by-step instructions.
                        </p>
                    </div>
                    
                    <div style={{
                        marginTop: 'auto',
                        padding: '1rem',
                        background: 'rgba(59,130,246,0.1)',
                        borderRadius: '0.75rem',
                        border: '1px solid rgba(59,130,246,0.3)'
                    }}>
                        <button 
                            onClick={() => setView('live')}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                border: 'none',
                                borderRadius: '0.5rem',
                                color: 'white',
                                fontWeight: 'bold',
                                cursor: 'pointer',
                                fontSize: '0.85rem'
                            }}
                        >
                            🌐 Go to Live Network
                        </button>
                    </div>
                </div>
            )}
            
            {/* ============= INSTRUCTOR MODE SIDEBAR ============= */}
            {currentMode === 'instructor' && (
                <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
                    <div style={{
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginBottom: '0.75rem',
                        paddingLeft: '0.5rem'
                    }}>
                        Instructor Tools
                    </div>
                    
                    <div style={{
                        padding: '1rem',
                        background: 'rgba(236, 72, 153, 0.1)',
                        borderRadius: '0.75rem',
                        border: '1px solid rgba(236, 72, 153, 0.3)',
                        marginBottom: '1rem'
                    }}>
                        <div style={{fontSize: '1rem', fontWeight: 'bold', color: '#f472b6', marginBottom: '0.5rem'}}>
                            🎓 Instructor Mode
                        </div>
                        <p style={{fontSize: '0.85rem', color: '#cbd5e1', margin: 0}}>
                            Monitor students, control epochs, and manage the network.
                        </p>
                    </div>
                    
                    {!isInstructor && (
                        <div style={{
                            padding: '1rem',
                            background: 'rgba(239, 68, 68, 0.2)',
                            borderRadius: '0.5rem',
                            color: '#fca5a5',
                            fontSize: '0.85rem'
                        }}>
                            ⚠️ Add <code>?mode=instructor</code> to URL for full access
                        </div>
                    )}
                </div>
            )}
            
            {/* Reset Session Button - Always visible at bottom */}
            <div style={{
                marginTop: 'auto',
                padding: '1rem',
                borderTop: '1px solid rgba(255,255,255,0.1)'
            }}>
                <button
                    onClick={resetSession}
                    style={{
                        width: '100%',
                        padding: '0.75rem',
                        background: 'transparent',
                        border: '1px solid rgba(239, 68, 68, 0.4)',
                        borderRadius: '0.5rem',
                        color: '#94a3b8',
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                        e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.6)';
                        e.currentTarget.style.color = '#f87171';
                    }}
                    onMouseOut={(e) => {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                        e.currentTarget.style.color = '#94a3b8';
                    }}
                >
                    🔄 Reset My Session
                </button>
            </div>
        </aside>

        {/* MAIN CONTENT AREA */}
        <main className="main-content">
            {/* ========== LAB TERMINAL - TOP BAR (always visible) ========== */}
            <div style={{
                position: 'sticky',
                top: 0,
                zIndex: 100,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0',
                marginBottom: '1rem',
                background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(15, 23, 42, 0.95) 100%)',
                borderBottom: '1px solid rgba(71, 85, 105, 0.5)',
                flexWrap: 'wrap'
            }}>
                <button
                    onClick={() => openLabTerminal(rpcUrl, terminalRpcUrl)}
                    style={{
                        padding: '0.5rem 1rem',
                        background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                        border: 'none',
                        borderRadius: '0.5rem',
                        color: 'white',
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        boxShadow: '0 2px 8px rgba(139, 92, 246, 0.3)'
                    }}
                >
                    <span>🖥️</span>
                    <span>Lab Terminal</span>
                </button>
                <button
                    onClick={() => openLabTerminal(rpcUrl, terminalRpcUrl)}
                    style={{
                        padding: '0.35rem 0.65rem',
                        background: 'rgba(139, 92, 246, 0.25)',
                        border: '1px solid rgba(139, 92, 246, 0.5)',
                        borderRadius: '0.35rem',
                        color: '#c4b5fd',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                    }}
                >
                    + New
                </button>
                <span style={{ fontSize: '0.85rem', color: '#64748b', marginLeft: '0.25rem' }}>
                    Deploy contracts, run CLI — opens in new window
                </span>
            </div>
            
            {/* 0. ORIENTATION VIEW */}
            {view === 'intro' && (
                <div className="intro-view" style={{maxWidth: '1200px', margin: '0 auto'}}>
                    {/* ========== COURSE HEADER ========== */}
                    <div style={{
                        background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 50%, #1a1a2e 100%)',
                        borderRadius: '1rem',
                        padding: '2.5rem',
                        marginBottom: '2rem',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        position: 'relative',
                        overflow: 'hidden'
                    }}>
                        <div style={{
                            position: 'absolute',
                            top: 0,
                            right: 0,
                            width: '300px',
                            height: '300px',
                            background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
                            pointerEvents: 'none'
                        }}></div>
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '2rem'}}>
                            <div style={{flex: '1 1 500px'}}>
                                <div style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    background: 'rgba(59, 130, 246, 0.2)',
                                    padding: '6px 14px',
                                    borderRadius: '20px',
                                    marginBottom: '1rem',
                                    border: '1px solid rgba(59, 130, 246, 0.4)'
                                }}>
                                    <span style={{fontSize: '0.8rem', color: '#60a5fa', fontWeight: '600', letterSpacing: '0.05em'}}>
                                        BLOCKCHAIN FUNDAMENTALS
                                    </span>
                                </div>
                                
                                <h1 style={{
                                    fontSize: '2.5rem',
                                    fontWeight: '700',
                                    margin: '0 0 1rem 0',
                                    background: 'linear-gradient(135deg, #fff 0%, #93c5fd 100%)',
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent',
                                    lineHeight: '1.2'
                                }}>
                                    Ethereum Proof-of-Stake Laboratory
                                </h1>
                                
                                <p style={{fontSize: '1.15rem', color: '#cbd5e1', lineHeight: '1.7', marginBottom: '1rem', maxWidth: '600px'}}>
                                    Master the fundamentals of Ethereum's consensus mechanism through hands-on interaction 
                                    with a live blockchain environment. This lab provides practical experience with staking, 
                                    validation, and network security concepts.
                                </p>
                                
                                {/* Skip to Live - Classroom mode */}
                                <button
                                    onClick={() => setView('live')}
                                    style={{
                                        padding: '0.75rem 1.5rem',
                                        background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                        border: 'none',
                                        borderRadius: '0.5rem',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        fontSize: '0.95rem',
                                        cursor: 'pointer',
                                        marginBottom: '1rem',
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '0.5rem',
                                    }}
                                >
                                    I&apos;m in a class — take me to the lab →
                                </button>
                                
                                {/* PROVENANCE BADGE - Trust indicator */}
                                <div style={{marginBottom: '1.5rem'}}>
                                    <ProvenanceBadge showFull={true} />
                                </div>
                                
                                <div style={{display: 'flex', flexWrap: 'wrap', gap: '1.5rem', marginTop: '1rem'}}>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                                        <div style={{width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                                            <span style={{fontSize: '1.2rem'}}>⏱️</span>
                                        </div>
                                        <div>
                                            <div style={{fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase'}}>Duration</div>
                                            <div style={{fontSize: '1rem', color: '#e2e8f0', fontWeight: '600'}}>45-60 minutes</div>
                                        </div>
                                    </div>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                                        <div style={{width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                                            <span style={{fontSize: '1.2rem'}}>📊</span>
                                        </div>
                                        <div>
                                            <div style={{fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase'}}>Level</div>
                                            <div style={{fontSize: '1rem', color: '#e2e8f0', fontWeight: '600'}}>Beginner</div>
                                        </div>
                                    </div>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                                        <div style={{width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(251, 191, 36, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                                            <span style={{fontSize: '1.2rem'}}>🎯</span>
                                        </div>
                                        <div>
                                            <div style={{fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase'}}>Format</div>
                                            <div style={{fontSize: '1rem', color: '#e2e8f0', fontWeight: '600'}}>Interactive Lab</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div style={{
                                flex: '0 0 auto',
                                background: 'rgba(15, 23, 42, 0.6)',
                                borderRadius: '1rem',
                                padding: '1.5rem',
                                border: '1px solid rgba(71, 85, 105, 0.5)',
                                minWidth: '280px'
                            }}>
                                <div style={{fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem', fontWeight: '600'}}>
                                    PREREQUISITES
                                </div>
                                <ul style={{listStyle: 'none', padding: 0, margin: 0, fontSize: '0.95rem'}}>
                                    <li style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.75rem', color: '#e2e8f0'}}>
                                        <span style={{color: '#22c55e'}}>✓</span> Basic understanding of cryptocurrency
                                    </li>
                                    <li style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.75rem', color: '#e2e8f0'}}>
                                        <span style={{color: '#22c55e'}}>✓</span> Web browser (Chrome/Firefox)
                                    </li>
                                    <li style={{display: 'flex', alignItems: 'center', gap: '10px', color: '#e2e8f0'}}>
                                        <span style={{color: '#22c55e'}}>✓</span> Network access to instructor's node
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    {/* ========== LEARNING OBJECTIVES ========== */}
                    <div style={{
                        background: '#1e293b',
                        borderRadius: '1rem',
                        padding: '2rem',
                        marginBottom: '2rem',
                        border: '1px solid #334155'
                    }}>
                        <div style={{display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1.5rem'}}>
                            <div style={{
                                width: '48px',
                                height: '48px',
                                borderRadius: '12px',
                                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '1.5rem'
                            }}>🎯</div>
                            <div>
                                <h2 style={{margin: 0, fontSize: '1.4rem', color: '#f8fafc'}}>Learning Objectives</h2>
                                <p style={{margin: 0, fontSize: '0.9rem', color: '#94a3b8'}}>Upon completion, you will be able to:</p>
                            </div>
                        </div>
                        
                        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem'}}>
                            {[
                                {icon: '🔐', text: 'Explain how Ethereum wallets and addresses work using public-key cryptography'},
                                {icon: '⛽', text: 'Calculate and interpret gas fees for blockchain transactions'},
                                {icon: '🔗', text: 'Describe how blocks are linked to form an immutable chain'},
                                {icon: '🏦', text: 'Demonstrate the staking process and validator selection algorithm'},
                                {icon: '⚔️', text: 'Identify conditions that trigger slashing penalties'},
                                {icon: '💰', text: 'Analyze the economic incentives of Proof-of-Stake consensus'}
                            ].map((obj, idx) => (
                                <div key={idx} style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '12px',
                                    padding: '1rem',
                                    background: 'rgba(59, 130, 246, 0.08)',
                                    borderRadius: '0.75rem',
                                    border: '1px solid rgba(59, 130, 246, 0.2)'
                                }}>
                                    <span style={{fontSize: '1.3rem', flexShrink: 0}}>{obj.icon}</span>
                                    <span style={{color: '#e2e8f0', fontSize: '0.95rem', lineHeight: '1.5'}}>{obj.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* ========== COURSE MODULES ========== */}
                    <div style={{
                        background: '#1e293b',
                        borderRadius: '1rem',
                        padding: '2rem',
                        marginBottom: '2rem',
                        border: '1px solid #334155'
                    }}>
                        <div style={{display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1.5rem'}}>
                            <div style={{
                                width: '48px',
                                height: '48px',
                                borderRadius: '12px',
                                background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '1.5rem'
                            }}>📚</div>
                            <div>
                                <h2 style={{margin: 0, fontSize: '1.4rem', color: '#f8fafc'}}>Course Modules</h2>
                                <p style={{margin: 0, fontSize: '0.9rem', color: '#94a3b8'}}>4 modules • Progressive learning path</p>
                            </div>
                        </div>
                        
                        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                            {[
                                {num: 1, title: 'Core Concepts', desc: 'Wallets, Gas, Blocks, Consensus Mechanisms', time: '10 min', icon: '🧱', view: 'concepts'},
                                {num: 2, title: 'Deep Dive', desc: 'Staking, Validators, Slashing, DeFi Economics', time: '15 min', icon: '🛰', view: 'explore'},
                                {num: 3, title: 'Simulation', desc: 'Interactive Validator Selection Algorithm', time: '10 min', icon: '🎮', view: 'sim'},
                                {num: 4, title: 'Live Network', desc: 'Real Transactions, Staking, Rewards', time: '15 min', icon: '🌐', view: 'live'}
                            ].map((mod, idx) => (
                                <div 
                                    key={idx} 
                                    onClick={() => {
                                        markStageComplete('intro');
                                        setView(mod.view);
                                    }}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '1rem',
                                        padding: '1.25rem',
                                        background: idx === 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(0,0,0,0.2)',
                                        borderRadius: '0.75rem',
                                        border: idx === 0 ? '2px solid #10b981' : '1px solid #334155',
                                        transition: 'all 0.2s',
                                        cursor: 'pointer'
                                    }}
                                    onMouseOver={(e) => {
                                        e.currentTarget.style.background = 'rgba(59, 130, 246, 0.15)';
                                        e.currentTarget.style.borderColor = '#3b82f6';
                                        e.currentTarget.style.transform = 'translateX(8px)';
                                    }}
                                    onMouseOut={(e) => {
                                        e.currentTarget.style.background = idx === 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(0,0,0,0.2)';
                                        e.currentTarget.style.borderColor = idx === 0 ? '#10b981' : '#334155';
                                        e.currentTarget.style.transform = 'translateX(0)';
                                    }}
                                >
                                    <div style={{
                                        width: '50px',
                                        height: '50px',
                                        borderRadius: '12px',
                                        background: idx === 0 ? '#10b981' : '#334155',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '1.5rem',
                                        flexShrink: 0
                                    }}>
                                        {mod.icon}
                                    </div>
                                    <div style={{flex: 1}}>
                                        <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px'}}>
                                            <span style={{
                                                fontSize: '0.75rem',
                                                color: '#64748b',
                                                fontWeight: '600'
                                            }}>MODULE {mod.num}</span>
                                            {idx === 0 && <span style={{
                                                fontSize: '0.7rem',
                                                background: '#10b981',
                                                color: 'white',
                                                padding: '2px 8px',
                                                borderRadius: '10px',
                                                fontWeight: '600'
                                            }}>START HERE</span>}
                                        </div>
                                        <div style={{fontSize: '1.1rem', color: '#f8fafc', fontWeight: '600'}}>{mod.title}</div>
                                        <div style={{fontSize: '0.9rem', color: '#94a3b8'}}>{mod.desc}</div>
                                    </div>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                                        <div style={{
                                            fontSize: '0.85rem',
                                            color: '#64748b',
                                            background: 'rgba(0,0,0,0.3)',
                                            padding: '6px 12px',
                                            borderRadius: '20px',
                                            whiteSpace: 'nowrap'
                                        }}>
                                            ⏱️ {mod.time}
                                        </div>
                                        <div style={{
                                            fontSize: '1.2rem',
                                            color: '#3b82f6',
                                            transition: 'transform 0.2s'
                                        }}>
                                            →
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <p style={{
                            marginTop: '1rem',
                            fontSize: '0.85rem',
                            color: '#64748b',
                            textAlign: 'center',
                            fontStyle: 'italic'
                        }}>
                            💡 Click any module to jump directly to that section
                        </p>
                    </div>

                    {/* ========== CONTENT SOURCES - Trust & Transparency ========== */}
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        borderRadius: '0.75rem',
                        padding: '1.25rem',
                        marginBottom: '2rem',
                        border: '1px solid #334155'
                    }}>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            marginBottom: '0.75rem',
                            color: '#94a3b8',
                            fontSize: '0.85rem',
                            fontWeight: '600'
                        }}>
                            <span>📚</span> Content Sources & Verification
                        </div>
                        <div style={{display: 'flex', flexWrap: 'wrap', gap: '8px'}}>
                            {CONTENT_METADATA.sources.map((source, idx) => (
                                <span key={idx} style={{
                                    padding: '4px 10px',
                                    background: 'rgba(59, 130, 246, 0.1)',
                                    borderRadius: '12px',
                                    fontSize: '0.8rem',
                                    color: '#93c5fd'
                                }}>
                                    {source}
                                </span>
                            ))}
                        </div>
                        <p style={{
                            margin: '0.75rem 0 0 0',
                            fontSize: '0.8rem',
                            color: '#64748b',
                            fontStyle: 'italic'
                        }}>
                            Last updated: {CONTENT_METADATA.lastUpdated} • Version {CONTENT_METADATA.version}
                        </p>
                    </div>

                    {/* ========== START BUTTON ========== */}
                    <div style={{textAlign: 'center', marginTop: '2rem'}}>
                        <button 
                            onClick={() => {
                                // Track session start for analytics
                                localStorage.setItem('session_start', Date.now().toString());
                                markStageComplete('intro')
                                setView('concepts')
                            }}
                            style={{
                                padding: '1.25rem 3rem',
                                fontSize: '1.15rem',
                                fontWeight: '700',
                                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                                border: 'none',
                                borderRadius: '0.75rem',
                                color: 'white',
                                cursor: 'pointer',
                                boxShadow: '0 4px 20px rgba(59, 130, 246, 0.4)',
                                transition: 'all 0.3s',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '10px'
                            }}
                            onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                            onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
                        >
                            Begin Course <span style={{fontSize: '1.3rem'}}>→</span>
                        </button>
                        <p style={{marginTop: '1rem', fontSize: '0.9rem', color: '#64748b'}}>
                            Estimated completion time: 45-60 minutes
                        </p>
                    </div>
                    
                    {/* ========== FEEDBACK SECTION ========== */}
                    <div style={{
                        marginTop: '2rem',
                        padding: '1.5rem',
                        background: 'rgba(15, 23, 42, 0.5)',
                        borderRadius: '0.75rem',
                        border: '1px solid #334155',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '1rem'
                    }}>
                        <div>
                            <div style={{color: '#94a3b8', fontSize: '0.9rem'}}>
                                📣 Help us improve this lab
                            </div>
                            <div style={{color: '#64748b', fontSize: '0.8rem'}}>
                                Your feedback shapes future versions
                            </div>
                        </div>
                        <FeedbackButton section="orientation" />
                    </div>
                </div>
            )}

            {/* 1. BASIC CONCEPTS VIEW */}
            {view === 'concepts' && (
                <div className="concepts-view">
                    <h2>🔍 Core Concepts</h2>
                    <p className="section-subtitle">Skim each card and hover to expand the mental models you'll need later.</p>
                    <div className="concepts-grid">
                        {CONCEPT_CARDS.map(card => (
                            <div 
                                className="concept-card" 
                                key={card.title}
                                style={card.fullWidth ? {gridColumn: '1 / -1'} : {}}
                            >
                                <h3>{card.title}</h3>
                                <p>{card.description}</p>
                                <ul>
                                    {card.highlight.map(point => <li key={point}>{point}</li>)}
                                </ul>
                                {/* VIDEO EMBED - Shows when video URL is provided */}
                                {card.video && (
                                    <div style={{
                                        marginTop: '1.5rem',
                                        borderRadius: '0.75rem',
                                        overflow: 'hidden',
                                        background: '#0f172a',
                                        border: '2px solid #3b82f6'
                                    }}>
                                        <div style={{
                                            padding: '0.75rem 1rem',
                                            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                                            color: 'white',
                                            fontWeight: 'bold',
                                            fontSize: '0.9rem'
                                        }}>
                                            🎬 Video Tutorial
                                        </div>
                                        <div style={{position: 'relative', paddingBottom: '56.25%', height: 0}}>
                                            <iframe
                                                src={card.video}
                                                title={`Video: ${card.title}`}
                                                style={{
                                                    position: 'absolute',
                                                    top: 0,
                                                    left: 0,
                                                    width: '100%',
                                                    height: '100%',
                                                    border: 'none'
                                                }}
                                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                allowFullScreen
                                            />
                                        </div>
                                    </div>
                                )}
                                {card.diagram && (
                                    <div style={{marginTop: '1.5rem', padding: '1.5rem', background: 'white', borderRadius: '0.75rem', border: '2px solid #e2e8f0'}}>
                                        <h4 style={{marginTop: 0, marginBottom: '1rem', color: '#1e293b', textAlign: 'center', fontSize: '1.3rem'}}>
                                            📊 The Validation Cycle
                                        </h4>
                                        <div style={{maxWidth: '900px', margin: '0 auto'}}>
                                            <img 
                                                src="pos-diagram.svg" 
                                                alt="Proof of Stake Validation Flow" 
                                                style={{width: '100%', display: 'block', height: 'auto'}}
                                            />
                                        </div>
                                        <div style={{marginTop: '1.5rem', padding: '1rem', background: '#f1f5f9', borderRadius: '0.5rem', maxWidth: '900px', margin: '1.5rem auto 0'}}>
                                            <p style={{margin: 0, fontSize: '0.95rem', color: '#475569', lineHeight: '1.7'}}>
                                                <strong style={{color: '#1e293b', display: 'block', marginBottom: '0.5rem'}}>How it works:</strong>
                                                <span style={{color: '#1e293b'}}>①</span> Validator stakes ETH → 
                                                <span style={{color: '#1e293b'}}> ②</span> Algorithm selects validator → 
                                                <span style={{color: '#1e293b'}}> ③</span> Selected validator proposes block → 
                                                <span style={{color: '#1e293b'}}> ④</span> Others verify → 
                                                <span style={{color: '#1e293b'}}> ⑤</span> Block added to chain → 
                                                <span style={{color: '#1e293b'}}> ⑥</span> Validator earns rewards
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                    <div className="concept-actions">
                        <button onClick={() => setView('intro')}>← Back to Orientation</button>
                        <button className="primary-btn" onClick={() => {
                            markStageComplete('concepts')
                            setView('explore')
                        }}>I'm ready to explore →</button>
                    </div>
                </div>
            )}

            {/* 2. EXPLORATION VIEW */}
            {view === 'explore' && (
                <ExploreView
                    missions={EXPLORE_MISSIONS}
                    exploreProgress={exploreProgress}
                    setExploreProgress={setExploreProgress}
                    onBack={() => setView('concepts')}
                    onContinue={() => { saveTrail({ ...trail, explore: true }); setView('sim'); }}
                    fireProgressBeacon={fireProgressBeacon}
                />
            )}

            {/* SIMULATION VIEW - Practice PoS concepts */}
            {view === 'sim' && (
                <PoSValidatorSim onComplete={() => setView('live')} />
            )}

            {/* TOKEN CONCEPTS VIEW - FT vs NFT Learning */}
            {view === 'tokens' && (
                <TokenConceptsView
                    onComplete={() => setView('concepts')}
                    onGoToLive={() => setView('live')}
                    provider={provider}
                    wallet={wallet}
                    rpcUrl={rpcUrl}
                />
            )}

            {/* 3. LIVE NETWORK VIEW */}
            {view === 'live' && (
                <div className="live-dashboard">
                    {/* Goal banner + Do This First */}
                    <div style={{
                        marginBottom: '1rem',
                        padding: '1rem 1.25rem',
                        background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(59, 130, 246, 0.15) 100%)',
                        borderRadius: '0.75rem',
                        border: '1px solid rgba(34, 197, 94, 0.4)',
                    }}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('yourWalletBanner')}
                            style={{ marginBottom: livePageBlocksOpen.yourWalletBanner ? '0.5rem' : 0 }}
                        >
                            <span style={{ fontWeight: 'bold', fontSize: '1.05rem', color: '#86efac' }}>Your Wallet</span>
                            <span style={{ color: '#93c5fd', fontSize: '0.9rem' }}>{livePageBlocksOpen.yourWalletBanner ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.yourWalletBanner && (
                        <>
                        <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: '0 0 0.75rem 0' }}>
                            Connect, get test ETH, send transactions. Use Beacon Chain Lab for staking and Smart Contract Lab for building and deploying.
                        </p>
                        <details style={{ fontSize: '0.85rem', color: '#94a3b8' }} open>
                            <summary style={{ cursor: 'pointer', color: '#93c5fd' }}>Do This First</summary>
                            <ul style={{ margin: '0.5rem 0 0 1rem', paddingLeft: 0, listStyle: 'none' }}>
                                <li>{wallet?.address ? '✅' : '☐'} Connect wallet</li>
                                <li>{parseFloat(wallet?.balance || 0) > 0 ? '✅' : '☐'} Get test ETH (from instructor)</li>
                                <li>
                                    <button
                                        type="button"
                                        onClick={() => setView('beacon-lab')}
                                        style={{
                                            background: 'none',
                                            border: 'none',
                                            padding: 0,
                                            color: '#93c5fd',
                                            cursor: 'pointer',
                                            fontSize: 'inherit',
                                            textDecoration: 'underline',
                                            textAlign: 'left'
                                        }}
                                    >
                                        ☐ Stake & attest → Beacon Chain Lab
                                    </button>
                                </li>
                                <li>
                                    <button
                                        type="button"
                                        onClick={() => setView('contract-builder-lab')}
                                        style={{
                                            background: 'none',
                                            border: 'none',
                                            padding: 0,
                                            color: '#93c5fd',
                                            cursor: 'pointer',
                                            fontSize: 'inherit',
                                            textDecoration: 'underline',
                                            textAlign: 'left'
                                        }}
                                    >
                                        ☐ Build & deploy → Smart Contract Lab
                                    </button>
                                </li>
                            </ul>
                        </details>
                        </>
                        )}
                    </div>
                    {/* Role assignment notification - shown when newly assigned */}
                    {roleAssignedBanner && myStake.role && (
                        <div style={{
                            marginBottom: '1rem',
                            padding: '1rem 1.25rem',
                            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(167, 139, 250, 0.2) 100%)',
                            border: '2px solid #8b5cf6',
                            borderRadius: '0.75rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.5rem'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                                <button
                                    type="button"
                                    className="live-page-block-header"
                                    onClick={() => toggleLivePageBlock('roleAssigned')}
                                    style={{ flex: 1, margin: 0, alignItems: 'flex-start' }}
                                >
                                    <div>
                                        <div style={{fontSize: '1.1rem', fontWeight: 'bold', color: '#c4b5fd', marginBottom: '0.25rem'}}>
                                            🎭 You've been assigned: {myStake.role}
                                        </div>
                                        {!livePageBlocksOpen.roleAssigned && (
                                            <div style={{fontSize: '0.75rem', color: '#94a3b8'}}>Click to expand details</div>
                                        )}
                                    </div>
                                    <span style={{ color: '#c4b5fd', fontSize: '0.9rem', flexShrink: 0 }}>{livePageBlocksOpen.roleAssigned ? '▼' : '▶'}</span>
                                </button>
                                <button
                                    onClick={() => setRoleAssignedBanner(false)}
                                    style={{
                                        padding: '0.25rem 0.5rem',
                                        background: 'rgba(255,255,255,0.2)',
                                        border: '1px solid rgba(255,255,255,0.3)',
                                        borderRadius: '0.25rem',
                                        color: '#e2e8f0',
                                        cursor: 'pointer',
                                        fontSize: '0.8rem',
                                        flexShrink: 0
                                    }}
                                >
                                    Dismiss
                                </button>
                            </div>
                            {livePageBlocksOpen.roleAssigned && (
                                <div style={{fontSize: '0.9rem', color: '#a78bfa'}}>
                                    Check your Role Hub below for goals, tasks, and quick actions.
                                </div>
                            )}
                        </div>
                    )}
                    {/* Active Identity - Compact */}
                    <div style={{
                        padding: '0.4rem 0.65rem',
                        marginBottom: '0.75rem',
                        background: 'rgba(30, 41, 59, 0.95)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: '0.35rem',
                        fontSize: '0.8rem'
                    }}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('identityStrip')}
                            style={{ margin: 0, padding: '0.15rem 0' }}
                        >
                            <span style={{ color: '#94a3b8', fontWeight: 600 }}>You &amp; class contract</span>
                            <span style={{ color: '#64748b' }}>{livePageBlocksOpen.identityStrip ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.identityStrip && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center', marginTop: '0.35rem' }}>
                        <span style={{color: '#94a3b8'}}>You:</span>
                        <span style={{fontFamily: 'monospace', color: '#e2e8f0'}}>
                            {wallet?.address ? `${wallet.address.slice(0,6)}...${wallet.address.slice(-4)}` : 'No wallet'}
                        </span>
                        {wallet?.address && (
                        <button onClick={() => copyAddress(wallet.address)} style={{padding: '0.2rem 0.4rem', fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', border: '1px solid #334155', borderRadius: '0.25rem', color: '#94a3b8', cursor: 'pointer'}}>Copy</button>
                        )}
                        <span style={{color: '#64748b'}}>|</span>
                        <span style={{color: '#94a3b8'}}>Contract:</span>
                        <span style={{fontFamily: 'monospace', color: '#e2e8f0'}}>
                            {posAddress && posAddress.length === 42 ? `${posAddress.slice(0,8)}...` : 'Not set'}
                        </span>
                        {posAddress && posAddress.length === 42 && (
                            <button onClick={() => copyAddress(posAddress)} style={{padding: '0.2rem 0.4rem', fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', border: '1px solid #334155', borderRadius: '0.25rem', color: '#94a3b8', cursor: 'pointer'}}>Copy</button>
                        )}
                        </div>
                        )}
                    </div>
                    
                    {/* Social Proof Banner - Community Activity */}
                    <div style={{marginBottom: '1rem'}}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('socialProof')}
                            style={{
                                marginBottom: livePageBlocksOpen.socialProof ? '0.5rem' : 0,
                                padding: '0.5rem 0.65rem',
                                background: 'rgba(30, 41, 59, 0.6)',
                                borderRadius: '0.35rem',
                                border: '1px solid rgba(71, 85, 105, 0.5)',
                            }}
                        >
                            <span style={{ fontWeight: 600, color: '#e2e8f0' }}>👥 Class activity</span>
                            <span style={{ color: '#94a3b8' }}>{livePageBlocksOpen.socialProof ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.socialProof && (
                        <SocialProof 
                            validators={validators} 
                            messages={messages}
                            stakersCount={0}
                        />
                        )}
                    </div>

                    {/* Create your first wallet (new students by IP) */}
                    {mustCreateWalletFirst && (
                        <div style={{
                            marginBottom: '1rem',
                            padding: '1.5rem',
                            background: 'linear-gradient(135deg, #1e3a5f 0%, #312e81 100%)',
                            border: '2px solid #3b82f6',
                            borderRadius: '0.75rem',
                            color: 'white',
                            textAlign: 'center'
                        }}>
                            <button
                                type="button"
                                className="live-page-block-header"
                                onClick={() => toggleLivePageBlock('createWalletBanner')}
                                style={{ marginBottom: livePageBlocksOpen.createWalletBanner ? '0.5rem' : 0, color: 'white' }}
                            >
                                <span style={{fontSize: '1.25rem', fontWeight: 'bold'}}>👛 Create your first wallet</span>
                                <span style={{ color: '#93c5fd' }}>{livePageBlocksOpen.createWalletBanner ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.createWalletBanner && (
                            <>
                            <p style={{margin: '0 0 1rem 0', opacity: 0.9, fontSize: '0.9rem'}}>
                                New students must create a wallet before receiving test ETH. You can create additional wallets later.
                            </p>
                            <div style={{display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap'}}>
                                <button
                                    onClick={() => setShowAccountManager(true)}
                                    style={{
                                        padding: '0.6rem 1.25rem',
                                        background: '#3b82f6',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '0.5rem',
                                        cursor: 'pointer',
                                        fontWeight: 'bold',
                                        fontSize: '0.95rem'
                                    }}
                                >
                                    Create or import wallet
                                </button>
                            </div>
                            </>
                            )}
                        </div>
                    )}

                    {/* Wallet Header - Compact (hidden when must create first) */}
                    {!mustCreateWalletFirst && (
                    <div style={{
                        background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                        padding: '1rem',
                        borderRadius: '0.75rem',
                        marginBottom: '1rem',
                        color: 'white'
                    }}>
                        <button
                            type="button"
                            onClick={() => toggleLivePageBlock('walletAndRole')}
                            style={{
                                width: '100%',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                background: 'rgba(0,0,0,0.2)',
                                border: 'none',
                                borderRadius: '0.5rem',
                                color: 'white',
                                cursor: 'pointer',
                                padding: '0.5rem 0.75rem',
                                marginBottom: '0.75rem',
                                fontSize: '0.9rem',
                                fontWeight: '600',
                            }}
                        >
                            <span>
                                {wallet.nickname || 'My Wallet'}
                                <span style={{ opacity: 0.88, fontWeight: 400, marginLeft: '0.5rem' }}>
                                    · {parseFloat(wallet.balance || 0).toFixed(4)} ETH
                                </span>
                                {!livePageBlocksOpen.walletAndRole && wallet.address && (
                                    <span style={{ fontFamily: 'monospace', fontSize: '0.78rem', opacity: 0.9 }}>{' '}· {wallet.address.slice(0, 6)}…{wallet.address.slice(-4)}</span>
                                )}
                            </span>
                            <span style={{ opacity: 0.9 }}>{livePageBlocksOpen.walletAndRole ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.walletAndRole && (
                        <>
                        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem'}}>
                            <div>
                                <div style={{fontSize: '0.85rem', opacity: 0.9, marginBottom: '0.5rem'}}>
                                    <span 
                                        className={`dot ${nodeStatus.connected ? 'green' : 'red'}`} 
                                        style={{
                                            marginRight: '0.5rem',
                                            animation: nodeStatus.connected ? 'pulse 2s infinite' : 'none'
                                        }}
                                    ></span>
                            {nodeStatus.connected ? `Block #${nodeStatus.blockNumber}` : 'Connecting...'}
                                    {nodeStatus.connected && (
                                        <span style={{
                                            marginLeft: '8px',
                                            fontSize: '0.7rem',
                                            color: '#22d3ee',
                                            opacity: 0.8
                                        }}>
                                            • Live {Math.floor((Date.now() - lastSyncTime) / 1000) < 2 ? '🟢' : '⏳'}
                                        </span>
                                    )}
                        </div>
                                <div style={{fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.25rem'}}>
                                    {wallet.nickname || 'My Wallet'}
                                </div>
                                <div style={{fontSize: '0.9rem', opacity: 0.8, fontFamily: 'monospace'}}>
                                    {wallet.address ? `${wallet.address.slice(0,6)}...${wallet.address.slice(-4)}` : 'No Wallet'}
                        </div>
                            </div>
                            <div style={{display: 'flex', gap: '0.5rem', alignItems: 'center'}}>
                                <button 
                                    onClick={() => copyAddress(wallet.address)}
                                    style={{padding: '0.4rem 0.65rem', fontSize: '0.8rem', background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '0.35rem', color: 'white', cursor: 'pointer'}}
                                >
                                    📋 Copy
                                </button>
                                <button 
                                    onClick={() => {
                                        const walletInfo = getWalletInfo();
                                        if (walletInfo) {
                                            alert(`Your Account:\n\nNickname: ${walletInfo.nickname}\nAddress: ${walletInfo.address}\n\nUse the sidebar buttons to Import/Export/Create accounts.`);
                                        }
                                    }}
                                    style={{padding: '0.4rem 0.65rem', fontSize: '0.8rem', background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '0.35rem', color: 'white', cursor: 'pointer'}}
                                >
                                    ⚙️ Account
                                </button>
                                <button 
                                    onClick={() => setShowLiveHelp(true)}
                                    style={{padding: '0.4rem 0.65rem', fontSize: '0.8rem', background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '0.35rem', color: 'white', cursor: 'pointer'}}
                                >
                                    ❓ Help
                                </button>
                            </div>
                        </div>
                        
                        <div style={{textAlign: 'center', padding: '1rem 0'}}>
                            <div style={{fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.25rem'}}>
                                {parseFloat(wallet.balance || 0).toFixed(4)} ETH
                            </div>
                            <div style={{fontSize: '0.9rem', opacity: 0.9}}>
                                ≈ ${(parseFloat(wallet.balance || 0) * 3000).toFixed(2)} USD
                            </div>
                        </div>
                        
                        {!myStake.role && (
                            <div style={{
                                marginTop: '0.75rem',
                                padding: '0.75rem 1rem',
                                background: 'rgba(148, 163, 184, 0.12)',
                                borderRadius: '0.35rem',
                                border: '1px solid rgba(148, 163, 184, 0.25)',
                                fontSize: '0.85rem',
                                color: '#94a3b8'
                            }}>
                                <div style={{fontWeight: '600', color: '#cbd5e1', marginBottom: '0.35rem'}}>🎭 No role yet</div>
                                <p style={{margin: 0, lineHeight: 1.5}}>
                                    Your instructor assigns roles via chat. Stake or send a message so you appear in the list, then wait for a line like <code style={{background: 'rgba(0,0,0,0.3)', padding: '0.1rem 0.3rem', borderRadius: 3}}>[ROLES:your-address:Victim]</code> (role depends on the scenario).
                                </p>
                            </div>
                        )}
                        {myStake.role && (
                            <>
                                <RoleHub
                                    role={myStake.role}
                                    myStake={myStake}
                                    wallet={wallet}
                                    ransomAddr={ransomContractAddress}
                                    onRansomAddrChange={(v) => { localStorage.setItem('ransom_addr', v); setRansomContractAddress(v); }}
                                    onLoadScript={(code) => {
                                      setScriptCode(code);
                                      setLoadCodeForConsole(code);
                                      setScriptPlaygroundOpen(true);
                                      setStatusMsg('✓ Script loaded! Lab Terminal expanded below — code will appear when the Hardhat prompt is ready.');
                                      setTimeout(() => setStatusMsg(''), 4000);
                                      setTimeout(() => document.getElementById('lab-terminal-section')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
                                    }}
                                    onExpandConsole={setScriptPlaygroundOpen}
                                    setStatusMsg={setStatusMsg}
                                />
                                {/* Deploy & Register section */}
                                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(139, 92, 246, 0.3)' }}>
                                    <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#a78bfa' }}>
                                        📋 Deploy & Register
                                    </div>
                                    <div style={{
                                        padding: '0.75rem',
                                        background: myStake.roleContract ? 'rgba(34, 197, 94, 0.1)' : 'rgba(0,0,0,0.2)',
                                        borderRadius: '0.5rem',
                                        border: myStake.roleContract ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(139, 92, 246, 0.2)',
                                    }}>
                                        <div style={{ fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.4rem', color: myStake.roleContract ? '#34d399' : '#e2e8f0' }}>
                                            {(myStake.roleContract ? '✅' : '1️⃣') + ' Deploy your contract'}
                                        </div>
                                        {myStake.roleContract ? (
                                            <div style={{ fontSize: '0.8rem', color: '#34d399', fontFamily: 'monospace' }}>
                                                {String(myStake.roleContract).slice(0, 14)}...{String(myStake.roleContract).slice(-10)}
                                            </div>
                                        ) : (
                                            <div>
                                                {ROLE_CONTRACT_TEMPLATES[myStake.role] && (
                                                    <>
                                                        <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0 0 0.5rem 0' }}>
                                                            {ROLE_CONTRACT_TEMPLATES[myStake.role].description}
                                                        </p>
                                                        {ROLE_CONTRACT_TEMPLATES[myStake.role].name && (
                                                        <button
                                                            onClick={async () => {
                                                                const tmpl = ROLE_CONTRACT_TEMPLATES[myStake.role];
                                                                if (!tmpl?.name) return;
                                                                setDeployRoleInProgress(true);
                                                                setStatusMsg('🚀 Deploying ' + tmpl.name + '...');
                                                                try {
                                                                    const res = await fetch(import.meta.env.BASE_URL + `artifacts/${tmpl.name}.json`);
                                                                    if (!res.ok) throw new Error('Artifact not found: ' + tmpl.name);
                                                                    const artifact = await res.json();
                                                                    const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet.signer);
                                                                    const needsArgs = artifact.abi.some(x => x.type === 'constructor' && x.inputs?.length > 0);
                                                                    let contract;
                                                                    if (needsArgs) {
                                                                        const argStr = window.prompt('Constructor argument needed (paste address from instructor if prompted):');
                                                                        if (!argStr) { setStatusMsg('Cancelled.'); setDeployRoleInProgress(false); return; }
                                                                        contract = await factory.deploy(argStr.trim());
                                                                    } else {
                                                                        contract = await factory.deploy();
                                                                    }
                                                                    await contract.waitForDeployment();
                                                                    const addr = await contract.getAddress();
                                                                    setStatusMsg('✅ Deployed! Registering with class...');
                                                                    const pos = new ethers.Contract(posAddress, PoSABI, wallet.signer);
                                                                    const tx = await pos.registerRoleContract(addr);
                                                                    await tx.wait();
                                                                    setMyStake(prev => ({ ...prev, roleContract: addr }));
                                                                    setStatusMsg('✅ Contract deployed & registered! Share address with instructor: ' + addr.slice(0, 10) + '...');
                                                                    setTimeout(() => setStatusMsg(''), 6000);
                                                                } catch (e) {
                                                                    setStatusMsg('❌ ' + (e.reason || e.message));
                                                                    setTimeout(() => setStatusMsg(''), 5000);
                                                                } finally {
                                                                    setDeployRoleInProgress(false);
                                                                }
                                                            }}
                                                            disabled={!wallet.signer || deployRoleInProgress}
                                                            style={{
                                                                padding: '0.5rem 1rem',
                                                                background: deployRoleInProgress ? '#475569' : 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                                                                color: 'white',
                                                                border: 'none',
                                                                borderRadius: '0.5rem',
                                                                cursor: (!wallet.signer || deployRoleInProgress) ? 'wait' : 'pointer',
                                                                fontWeight: 'bold',
                                                                fontSize: '0.85rem',
                                                                width: '100%',
                                                                marginBottom: '0.5rem',
                                                                opacity: deployRoleInProgress ? 0.9 : 1
                                                            }}
                                                        >
                                                            {deployRoleInProgress ? '⏳ Deploying...' : '🚀 Deploy ' + ROLE_CONTRACT_TEMPLATES[myStake.role].name + ' (one click)'}
                                                        </button>
                                                        )}
                                                        {deployRoleInProgress && (
                                                            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
                                                                ⏳ Deploying to blockchain, then registering with class...
                                                            </div>
                                                        )}
                                                        {statusMsg && (statusMsg.includes('Deploy') || statusMsg.includes('deployed') || statusMsg.includes('Register') || statusMsg.includes('❌')) && !deployRoleInProgress && (
                                                            <div style={{
                                                                marginTop: '0.5rem',
                                                                padding: '0.5rem 0.75rem',
                                                                borderRadius: '0.35rem',
                                                                fontSize: '0.85rem',
                                                                background: statusMsg.includes('❌') ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                                                                border: `1px solid ${statusMsg.includes('❌') ? 'rgba(239, 68, 68, 0.4)' : 'rgba(34, 197, 94, 0.4)'}`,
                                                                color: statusMsg.includes('❌') ? '#fca5a5' : '#86efac'
                                                            }}>
                                                                {statusMsg}
                                                            </div>
                                                        )}
                                                    </>
                                                )}
                                                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Or paste address:</div>
                                                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.35rem' }}>
                                                    <input
                                                        placeholder="0x..."
                                                        value={roleContractInput}
                                                        onChange={e => setRoleContractInput(e.target.value)}
                                                        style={{
                                                            flex: 1,
                                                            padding: '0.4rem 0.6rem',
                                                            background: '#0f172a',
                                                            border: '1px solid #475569',
                                                            borderRadius: '0.35rem',
                                                            color: '#e2e8f0',
                                                            fontSize: '0.8rem',
                                                            fontFamily: 'monospace'
                                                        }}
                                                    />
                                                    <button
                                                        onClick={async () => {
                                                            const addr = roleContractInput.trim();
                                                            if (!addr || !addr.startsWith('0x') || addr.length !== 42) {
                                                                setStatusMsg('❌ Enter a valid contract address');
                                                                return;
                                                            }
                                                            try {
                                                                setRoleContractRegistering(true);
                                                                const c = new ethers.Contract(posAddress, PoSABI, wallet.signer);
                                                                const tx = await c.registerRoleContract(addr);
                                                                await tx.wait();
                                                                setMyStake(prev => ({ ...prev, roleContract: addr }));
                                                                setRoleContractInput('');
                                                                setStatusMsg('✅ Contract registered!');
                                                                setTimeout(() => setStatusMsg(''), 3000);
                                                            } catch (e) {
                                                                setStatusMsg('❌ ' + (e.reason || e.message));
                                                            } finally {
                                                                setRoleContractRegistering(false);
                                                            }
                                                        }}
                                                        disabled={roleContractRegistering || !roleContractInput.trim()}
                                                        style={{
                                                            padding: '0.4rem 0.75rem',
                                                            background: !roleContractInput.trim() ? '#475569' : '#10b981',
                                                            color: 'white',
                                                            border: 'none',
                                                            borderRadius: '0.35rem',
                                                            cursor: !roleContractInput.trim() ? 'not-allowed' : 'pointer',
                                                            fontWeight: 'bold',
                                                            fontSize: '0.8rem'
                                                        }}
                                                    >
                                                        {roleContractRegistering ? '...' : 'Register'}
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    <a href="/walkthrough.html" target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.8rem', color: '#60a5fa', marginTop: '0.5rem', display: 'inline-block' }}>
                                        Open full walkthrough →
                                    </a>
                                    {ROLE_CONTRACT_TEMPLATES[myStake.role]?.template && (
                                        <div style={{ marginTop: '0.5rem' }}>
                                            <button
                                                onClick={() => setRoleTemplateExpanded(!roleTemplateExpanded)}
                                                style={{
                                                    background: 'transparent',
                                                    border: '1px solid rgba(139, 92, 246, 0.3)',
                                                    color: '#94a3b8',
                                                    padding: '0.3rem 0.6rem',
                                                    borderRadius: '0.25rem',
                                                    cursor: 'pointer',
                                                    fontSize: '0.75rem'
                                                }}
                                            >
                                                {roleTemplateExpanded ? '▼ Hide Solidity source' : '▶ View Solidity source'}
                                            </button>
                                            {roleTemplateExpanded && (
                                                <pre style={{
                                                    marginTop: '0.5rem',
                                                    padding: '0.75rem',
                                                    background: '#0f172a',
                                                    borderRadius: '0.5rem',
                                                    fontSize: '0.75rem',
                                                    overflow: 'auto',
                                                    maxHeight: '240px',
                                                    color: '#94a3b8'
                                                }}>
                                                    {ROLE_CONTRACT_TEMPLATES[myStake.role].template}
                                                </pre>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </>
                        )}
                        </>
                        )}
                    </div>
                    )}

                    {/* Quick Actions - No faucet; instructor funds students (hidden when must create wallet first) */}
                    {!mustCreateWalletFirst && (
                    <div style={{ marginBottom: '1.5rem' }}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('quickActions')}
                            style={{
                                marginBottom: livePageBlocksOpen.quickActions ? '0.75rem' : 0,
                                padding: '0.5rem 0.75rem',
                                background: 'rgba(30, 41, 59, 0.85)',
                                borderRadius: '0.5rem',
                                border: '1px solid rgba(71, 85, 105, 0.6)',
                            }}
                        >
                            <span style={{ fontWeight: 700, color: '#e2e8f0' }}>⚡ Quick actions</span>
                            <span style={{ color: '#94a3b8' }}>{livePageBlocksOpen.quickActions ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.quickActions && (
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '1rem',
                    }}>
                        <div style={{
                            gridColumn: '1 / -1',
                            padding: '1rem 1.25rem',
                            background: parseFloat(wallet.balance || 0) === 0 ? 'rgba(251, 191, 36, 0.25)' : 'rgba(251, 191, 36, 0.15)',
                            borderRadius: '0.75rem',
                            border: '1px solid rgba(251, 191, 36, 0.4)',
                            color: '#fcd34d',
                            fontSize: '0.95rem'
                        }}>
                            <strong>💰 Test ETH:</strong> Only the instructor can issue funds.
                            {parseFloat(wallet.balance || 0) === 0 && wallet.address && (
                                <div style={{marginTop: '0.75rem', fontSize: '0.9rem'}}>
                                    <span style={{opacity: 0.95}}>No gas yet? Copy your address and share with your instructor:</span>
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.5rem',
                                        marginTop: '0.5rem',
                                        background: 'rgba(0,0,0,0.2)',
                                        padding: '0.5rem 0.75rem',
                                        borderRadius: '0.5rem',
                                        fontFamily: 'monospace',
                                        fontSize: '0.8rem',
                                        wordBreak: 'break-all'
                                    }}>
                                        <span style={{color: '#e2e8f0'}}>{wallet.address}</span>
                                        <button
                                            onClick={async () => {
                                                const ok = await copyToClipboard(wallet.address);
                                                setStatusMsg(ok ? '✅ Address copied! Share with instructor.' : 'Copy failed — select address manually');
                                                setTimeout(() => setStatusMsg(''), 2000);
                                            }}
                                            style={{
                                                padding: '0.25rem 0.5rem',
                                                background: '#3b82f6',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '0.25rem',
                                                cursor: 'pointer',
                                                fontSize: '0.75rem',
                                                whiteSpace: 'nowrap'
                                            }}
                                        >
                                            📋 Copy
                                        </button>
                                        <button
                                            onClick={async () => {
                                                try {
                                                    const r = await fetch(import.meta.env.BASE_URL + 'lab-api/fund-request', {
                                                        method: 'POST',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({ address: wallet.address, nickname: wallet.nickname || myNickname })
                                                    });
                                                    if (r.ok) {
                                                        setStatusMsg('✅ Fund request sent! Instructor will be notified.');
                                                    } else {
                                                        setStatusMsg('Request failed — try copying your address.');
                                                    }
                                                } catch {
                                                    setStatusMsg('Request failed — Lab API may be offline.');
                                                }
                                                setTimeout(() => setStatusMsg(''), 3000);
                                            }}
                                            style={{
                                                padding: '0.25rem 0.5rem',
                                                background: '#10b981',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '0.25rem',
                                                cursor: 'pointer',
                                                fontSize: '0.75rem',
                                                whiteSpace: 'nowrap'
                                            }}
                                        >
                                            📤 Request funds
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                        <button
                            onClick={() => document.getElementById('send-section').scrollIntoView({behavior: 'smooth'})}
                            style={{
                                background: '#3b82f6',
                                color: 'white',
                                border: 'none',
                                padding: '1.25rem',
                                borderRadius: '0.75rem',
                                cursor: 'pointer',
                                fontSize: '1rem',
                                fontWeight: 'bold',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}
                        >
                            <span style={{fontSize: '2rem'}}>📤</span>
                            Send
                        </button>
                        
                        <button
                            onClick={() => setView('beacon-lab')}
                            style={{
                                background: '#8b5cf6',
                                color: 'white',
                                border: 'none',
                                padding: '1.25rem',
                                borderRadius: '0.75rem',
                                cursor: 'pointer',
                                fontSize: '1rem',
                                fontWeight: 'bold',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}
                        >
                            <span style={{fontSize: '2rem'}}>⛓️</span>
                            Beacon Lab
                        </button>
                        <button
                            onClick={() => setView('contract-builder-lab')}
                            style={{
                                background: '#0ea5e9',
                                color: 'white',
                                border: 'none',
                                padding: '1.25rem',
                                borderRadius: '0.75rem',
                                cursor: 'pointer',
                                fontSize: '1rem',
                                fontWeight: 'bold',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}
                        >
                            <span style={{fontSize: '2rem'}}>📜</span>
                            Contract Lab
                        </button>
                    </div>
                        )}
                    </div>
                    )}

                    <div className="live-grid">
                        {/* Assets / Portfolio */}
                        <section className="card">
                            <button type="button" className="live-page-block-header" onClick={() => toggleLivePageBlock('assetsCard')}>
                                <h3>💼 Your Assets</h3>
                                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>{livePageBlocksOpen.assetsCard ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.assetsCard && (
                            <div style={{display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: 0}}>
                                {/* ETH Balance */}
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: '1rem',
                                    background: 'rgba(59,130,246,0.1)',
                                    borderRadius: '0.5rem',
                                    border: '1px solid rgba(59,130,246,0.3)'
                                }}>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                                        <div style={{
                                            width: '40px',
                                            height: '40px',
                                            borderRadius: '50%',
                                            background: 'linear-gradient(135deg, #627eea 0%, #8a92b2 100%)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: '1.2rem'
                                        }}>
                                            Ξ
                                        </div>
                                        <div>
                                            <div style={{fontWeight: 'bold', color: '#f8fafc'}}>Ethereum</div>
                                            <div style={{fontSize: '0.85rem', color: '#94a3b8'}}>ETH</div>
                                        </div>
                                    </div>
                                    <div style={{textAlign: 'right'}}>
                                        <div style={{fontWeight: 'bold', color: '#f8fafc'}}>{parseFloat(wallet.balance || 0).toFixed(4)} ETH</div>
                                        <div style={{fontSize: '0.85rem', color: '#94a3b8'}}>${(parseFloat(wallet.balance || 0) * 3000).toFixed(2)}</div>
                                    </div>
                                </div>
                            </div>
                            )}
                        </section>

                        {/* Send Transaction */}
                        <section className="card" id="send-section">
                            <button type="button" className="live-page-block-header" onClick={() => toggleLivePageBlock('sendCard')}>
                                <h3>📤 Send Transaction</h3>
                                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>{livePageBlocksOpen.sendCard ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.sendCard && (
                            <div style={{display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: 0}}>
                                <div>
                                    <label style={{display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#cbd5e1'}}>
                                        Recipient Address
                                    </label>
                                <input 
                                        placeholder="0x... or click classmate in sidebar" 
                                    value={recipient}
                                    onChange={e => setRecipient(e.target.value)}
                                        style={{width: '100%'}}
                                    />
                                </div>
                                
                                <div>
                                    <label style={{display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#cbd5e1'}}>
                                        Amount (ETH)
                                    </label>
                                <input 
                                        placeholder="0.0" 
                                    type="number"
                                        step="0.01"
                                    value={sendAmount}
                                    onChange={e => setSendAmount(e.target.value)}
                                        style={{width: '100%'}}
                                />
                                </div>
                                
                                <button 
                                    onClick={sendEthToPeer}
                                    disabled={statusMsg.includes("Sending ETH") || !recipient || !sendAmount}
                                    style={{
                                        width: '100%',
                                        padding: '1rem',
                                        background: (statusMsg.includes("Sending ETH") || !recipient || !sendAmount) ? '#64748b' : '#3b82f6',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '0.5rem',
                                        fontSize: '1rem',
                                        fontWeight: 'bold',
                                        cursor: (statusMsg.includes("Sending ETH") || !recipient || !sendAmount) ? 'not-allowed' : 'pointer'
                                    }}
                                >
                                    {statusMsg.includes("Sending ETH") ? "⏳ Sending..." : "📤 Send Transaction"}
                                </button>
                            </div>
                            )}
                        </section>

                        {/* Beacon Chain Lab - staking moved here */}
                        <section className="card" id="stake-section">
                            <button type="button" className="live-page-block-header" onClick={() => toggleLivePageBlock('beaconPromoCard')}>
                                <h3>⛓️ Beacon Chain Lab</h3>
                                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>{livePageBlocksOpen.beaconPromoCard ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.beaconPromoCard && (
                            <>
                            <p style={{fontSize: '14px', color: '#cbd5e1', marginBottom: '15px'}}>
                                Stake, attest, and experience consensus. Use the Beacon Chain Lab for validator activities.
                            </p>
                            <button
                                onClick={() => setView('beacon-lab')}
                                style={{
                                    width: '100%',
                                    padding: '1rem',
                                    background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '0.5rem',
                                    fontSize: '1rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer'
                                }}
                            >
                                Open Beacon Chain Lab →
                            </button>
                            </>
                            )}
                        </section>

                        {/* Smart Contract Lab */}
                        <section className="card">
                            <button type="button" className="live-page-block-header" onClick={() => toggleLivePageBlock('contractPromoCard')}>
                                <h3>📜 Smart Contract Lab</h3>
                                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>{livePageBlocksOpen.contractPromoCard ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.contractPromoCard && (
                            <>
                            <p style={{fontSize: '14px', color: '#cbd5e1', marginBottom: '15px'}}>
                                Build, compile, and deploy smart contracts from templates. Deploy and share with classmates.
                            </p>
                            <button
                                onClick={() => setView('contract-builder-lab')}
                                style={{
                                    width: '100%',
                                    padding: '1rem',
                                    background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '0.5rem',
                                    fontSize: '1rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer'
                                }}
                            >
                                Open Smart Contract Lab →
                            </button>
                            </>
                            )}
                        </section>

                        {/* Tokenization Lab */}
                        <section className="card">
                            <button type="button" className="live-page-block-header" onClick={() => toggleLivePageBlock('tokenPromoCard')}>
                                <h3>🪙 Tokenization Lab</h3>
                                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>{livePageBlocksOpen.tokenPromoCard ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.tokenPromoCard && (
                            <>
                            <p style={{fontSize: '14px', color: '#cbd5e1', marginBottom: '15px'}}>
                                Learn ERC-721 NFTs end to end (mint, metadata, transfer), then sell an NFT for native ETH — fungible payment for a non-fungible asset.
                            </p>
                            <button
                                onClick={() => setView('tokenization-lab')}
                                style={{
                                    width: '100%',
                                    padding: '1rem',
                                    background: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
                                    color: '#1e293b',
                                    border: 'none',
                                    borderRadius: '0.5rem',
                                    fontSize: '1rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer'
                                }}
                            >
                                Open Tokenization Lab →
                            </button>
                            </>
                            )}
                        </section>

                        {/* Contract Config */}
                        <section className="card">
                            <button type="button" className="live-page-block-header" onClick={() => toggleLivePageBlock('connectionCard')}>
                                <h3>⚙️ Connection Setup</h3>
                                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>{livePageBlocksOpen.connectionCard ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.connectionCard && (
                            <>
                            {isRemote && (
                                <div className="remote-warning">
                                    📡 Remote Access Detected - Configure your connection below
                                </div>
                            )}
                            <div className="config-field">
                                <label>Contract Address (from instructor):</label>
                                <input 
                                    placeholder="0x..." 
                                    value={posAddress}
                                    onChange={e => {
                                        setPosAddress(e.target.value);
                                        localStorage.setItem("pos_addr", e.target.value);
                                    }}
                                />
                            </div>
                            <div className="config-field">
                                <label>Blockchain RPC URL:</label>
                                <input 
                                    placeholder={defaultRpcUrl}
                                    value={rpcUrl}
                                    onChange={e => {
                                        const v = e.target.value;
                                        setRpcUrl(v);
                                        if (v?.trim()) localStorage.setItem("custom_rpc", v);
                                        else localStorage.removeItem("custom_rpc");
                                    }}
                                />
                                {isRemote && (
                                    <small className="config-hint">
                                        💡 Ask instructor for the RPC URL if the auto-detected same-origin proxy does not work. Common values are the shared app path ending in <code>/rpc</code> or a direct <code>http://[instructor-ip]:8545</code>.
                                    </small>
                                )}
                            </div>
                            <div className="connection-status">
                                {nodeStatus.connected ? (
                                    <span className="status-ok">✅ Connected to blockchain</span>
                                ) : (
                                    <span className="status-error">❌ Not connected - check RPC URL</span>
                                )}
                            </div>
                            <NodeGraph
                                validators={validators}
                                myAddress={wallet?.address}
                                rpcUrl={rpcUrl}
                            />
                            <ChainSearch provider={provider} rpcUrl={rpcUrl} />
                            </>
                            )}
                        </section>

                        {/* Transaction History */}
                        <section className="card full-width">
                            <button
                                type="button"
                                className="live-page-block-header"
                                onClick={() => toggleLivePageBlock('txHistoryCard')}
                            >
                                <h3>📜 Transaction History</h3>
                                <span style={{fontSize: '0.9rem', color: '#94a3b8'}}>{livePageBlocksOpen.txHistoryCard ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.txHistoryCard && (
                            <div style={{marginTop: '1rem'}}>
                                {txHistory.length === 0 ? (
                                    <div style={{textAlign: 'center', padding: '2rem', color: '#64748b'}}>
                                        No transactions yet. Send or receive ETH to see your history here.
                                    </div>
                                ) : (
                                    <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
                                        {txHistory.map((tx, idx) => (
                                            <div key={idx} style={{
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'center',
                                                padding: '1rem',
                                                background: tx.type === 'sent' ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)',
                                                borderLeft: `4px solid ${tx.type === 'sent' ? '#ef4444' : '#22c55e'}`,
                                                borderRadius: '0.5rem'
                                            }}>
                                                <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                                                    <div style={{
                                                        width: '40px',
                                                        height: '40px',
                                                        borderRadius: '50%',
                                                        background: tx.type === 'sent' ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        fontSize: '1.2rem'
                                                    }}>
                                                        {tx.type === 'sent' ? '📤' : '📥'}
                                                    </div>
                                                    <div>
                                                        <div style={{fontWeight: 'bold', color: '#f8fafc'}}>
                                                            {tx.label || (tx.type === 'sent' ? 'Sent' : 'Received')}
                                                        </div>
                                                        <div style={{fontSize: '0.85rem', color: '#94a3b8', fontFamily: 'monospace'}}>
                                                            {tx.type === 'sent' 
                                                              ? `To: ${tx.to?.slice(0,6)}...${tx.to?.slice(-4)}` 
                                                              : `From: ${tx.from?.slice(0,6)}...${tx.from?.slice(-4)}`}
                                                        </div>
                                                        <div style={{fontSize: '0.75rem', color: '#64748b'}}>
                                                            Block #{tx.blockNumber} • {new Date(tx.timestamp * 1000).toLocaleString()}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div style={{textAlign: 'right'}}>
                                                    <div style={{
                                                        fontWeight: 'bold',
                                                        fontSize: '1.1rem',
                                                        color: tx.type === 'sent' ? '#fca5a5' : '#86efac'
                                                    }}>
                                                        {tx.type === 'sent' ? '-' : '+'}{parseFloat(tx.value).toFixed(4)} ETH
                                                    </div>
                                                    <button
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(tx.hash);
                                                            setStatusMsg(`Copied tx hash: ${tx.hash.slice(0,10)}...`);
                                                            setTimeout(() => setStatusMsg(''), 2000);
                                                        }}
                                                        style={{
                                                            background: 'transparent',
                                                            border: '1px solid #475569',
                                                            color: '#94a3b8',
                                                            padding: '0.25rem 0.5rem',
                                                            borderRadius: '0.25rem',
                                                            fontSize: '0.75rem',
                                                            cursor: 'pointer',
                                                            marginTop: '0.25rem'
                                                        }}
                                                    >
                                                        📋 Copy Hash
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            )}
                        </section>

                        {/* Global Chat */}
                        <section className="card full-width">
                            <button type="button" className="live-page-block-header" onClick={() => toggleLivePageBlock('classChat')}>
                                <h3>💬 Class Chat</h3>
                                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>{livePageBlocksOpen.classChat ? '▼' : '▶'}</span>
                            </button>
                            {livePageBlocksOpen.classChat && (
                            <>
                            <div className="chat-window">
                                {messages.length === 0 ? (
                                    <div style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        height: '100%',
                                        color: '#64748b',
                                        textAlign: 'center',
                                        gap: '0.5rem'
                                    }}>
                                        <span style={{fontSize: '2rem'}}>💬</span>
                                        <span>No messages yet</span>
                                        <span style={{fontSize: '0.8rem', color: '#475569'}}>
                                            Be the first to say hello!
                                        </span>
                                    </div>
                                ) : (
                                    messages
                                        .filter(msg => !msg.text || !msg.text.startsWith('[ARTIFACT:'))
                                        .map((msg, i) => (
                                        <div key={i} className={`msg ${msg.sender === wallet.address ? 'my-msg' : ''}`}>
                                            <div className="msg-header">
                                                <span className="sender-name" onClick={() => {setRecipient(msg.sender); copyAddress(msg.sender)}}>
                                                    {msg.sender.slice(0,6)}
                                                </span>
                                                <span className="time">{new Date(msg.timestamp * 1000).toLocaleTimeString()}</span>
                                            </div>
                                            {msg.text}
                                        </div>
                                    ))
                                )}
                            </div>
                            <div className="input-group">
                                <input 
                                    placeholder="Type message..."
                                    value={chatInput}
                                    onChange={e => setChatInput(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendChatMessage()}
                                    disabled={!wallet.signer}
                                />
                                <button 
                                    onClick={() => sendChatMessage()}
                                    disabled={!wallet.signer || !chatInput.trim()}
                                    style={{
                                        opacity: (!wallet.signer || !chatInput.trim()) ? 0.5 : 1,
                                        cursor: (!wallet.signer || !chatInput.trim()) ? 'not-allowed' : 'pointer'
                                    }}
                                >
                                    Post
                                </button>
                            </div>
                            {!wallet.signer && (
                                <p style={{fontSize: '0.8rem', color: '#f59e0b', margin: '0.5rem 0 0 0'}}>
                                    ⚠️ Wallet loading... please wait
                                </p>
                            )}
                            </>
                            )}
                        </section>
                    </div>
                    
                    {/* ========== EVIDENCE / ARTIFACTS (scenario clues) ========== */}
                    {(artifacts.length > 0 || myStake.role) && (
                    <div style={{
                        marginTop: '2rem',
                        padding: '1.5rem',
                        background: '#1e293b',
                        borderRadius: '1rem',
                        border: '1px solid #334155'
                    }}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('evidenceSection')}
                            style={{ marginBottom: livePageBlocksOpen.evidenceSection ? '0.5rem' : 0, color: '#f8fafc' }}
                        >
                            <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>📂 Evidence &amp; Artifacts</span>
                            <span style={{ color: '#94a3b8' }}>{livePageBlocksOpen.evidenceSection ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.evidenceSection && (
                        <>
                        <button
                            type="button"
                            onClick={() => setArtifactsOpen(!artifactsOpen)}
                            style={{
                                width: '100%',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                background: 'transparent',
                                border: 'none',
                                color: '#f8fafc',
                                fontSize: '1.1rem',
                                cursor: 'pointer',
                                padding: '0.5rem 0'
                            }}
                        >
                            <span>Artifact list {artifacts.length > 0 && <span style={{fontSize: '0.8rem', color: '#94a3b8'}}>({artifacts.length})</span>}</span>
                            <span>{artifactsOpen ? '▼' : '▶'}</span>
                        </button>
                        {artifactsOpen && (
                            <div style={{marginTop: '1rem'}}>
                                <p style={{fontSize: '0.9rem', color: '#94a3b8', marginBottom: '0.75rem'}}>
                                    <strong style={{color: '#e2e8f0'}}>{"What this is: "}</strong>
                                    {"Your instructor posts clues in class chat using "}
                                    <code style={{background: '#334155', padding: '0.1rem 0.3rem', borderRadius: '4px', fontSize: '0.8rem'}}>[ARTIFACT:...]</code>
                                    {". Those messages appear here so you can review them together."}
                                </p>
                                <p style={{fontSize: '0.85rem', color: '#64748b', marginBottom: '0.75rem'}}>
                                    <strong>{"Ransomware / investigations: "}</strong>
                                    {"Your instructor may post ledger hints or hashes to trace on-chain flow. "}
                                    <strong>{"Other scenarios: "}</strong>
                                    {"Use artifacts as in-character clues for role-play labs."}
                                </p>
                                {artifacts.length === 0 ? (
                                    <div style={{padding: '1rem', background: '#0f172a', borderRadius: '0.5rem', color: '#64748b', fontSize: '0.9rem'}}>
                                        No artifacts yet. Your instructor will post clues in chat as the scenario unfolds.
                                    </div>
                                ) : (
                                    <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
                                        {artifacts.map((a, i) => (
                                            <div key={i} style={{
                                                padding: '1rem',
                                                background: '#0f172a',
                                                borderRadius: '0.5rem',
                                                border: '1px solid #334155',
                                                fontSize: '0.9rem',
                                                color: '#e2e8f0'
                                            }}>
                                                <div style={{fontSize: '0.75rem', color: '#64748b', marginBottom: '0.5rem'}}>
                                                    Artifact #{i + 1} · {new Date(a.timestamp * 1000).toLocaleString()}
                                                </div>
                                                {a.content}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                        </>
                        )}
                    </div>
                    )}

                    {/* ========== RANSOMWARE SCENARIO (Phase 7) ========== */}
                    <div style={{
                        marginTop: '2rem',
                        padding: '1.5rem',
                        background: '#1e293b',
                        borderRadius: '1rem',
                        border: '1px solid #334155'
                    }}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('ransomSection')}
                            style={{ marginBottom: livePageBlocksOpen.ransomSection ? '0.5rem' : 0, color: '#f8fafc' }}
                        >
                            <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>🔐 Ransomware Forensics Scenario</span>
                            <span style={{ color: '#94a3b8' }}>{livePageBlocksOpen.ransomSection ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.ransomSection && (
                            <div style={{marginTop: '1rem'}}>
                                <p style={{fontSize: '0.9rem', color: '#94a3b8', marginBottom: '0.75rem'}}>
                                    Victims pay ETH through the Ransom contract. Investigators trace the flow. Instructor deploys via Contract Builder and shares the address.
                                </p>
                                <div style={{display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap'}}>
                                    <input
                                        placeholder="Ransom contract address (0x...)"
                                        value={ransomContractAddress}
                                        onChange={e => {
                                            setRansomContractAddress(e.target.value);
                                            localStorage.setItem('ransom_addr', e.target.value);
                                        }}
                                        style={{
                                            flex: 1,
                                            minWidth: '200px',
                                            padding: '0.5rem',
                                            background: '#0f172a',
                                            border: '1px solid #475569',
                                            borderRadius: '0.5rem',
                                            color: '#e2e8f0',
                                            fontFamily: 'monospace',
                                            fontSize: '0.85rem'
                                        }}
                                    />
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        placeholder="ETH"
                                        value={ransomAmount}
                                        onChange={e => setRansomAmount(e.target.value)}
                                        style={{
                                            width: '80px',
                                            padding: '0.5rem',
                                            background: '#0f172a',
                                            border: '1px solid #475569',
                                            borderRadius: '0.5rem',
                                            color: '#e2e8f0'
                                        }}
                                    />
                                    <button
                                        onClick={async () => {
                                            if (!ransomContractAddress || ransomContractAddress.length !== 42) {
                                                setStatusMsg('❌ Enter valid Ransom contract address');
                                                return;
                                            }
                                            if (!wallet.signer) {
                                                setStatusMsg('❌ Wallet not ready');
                                                return;
                                            }
                                            try {
                                                const RansomABI = [{ inputs: [], name: 'payRansom', outputs: [], stateMutability: 'payable', type: 'function' }];
                                                const c = new ethers.Contract(ransomContractAddress, RansomABI, wallet.signer);
                                                const tx = await c.payRansom({ value: ethers.parseEther(ransomAmount) });
                                                await tx.wait();
                                                setStatusMsg('✅ Ransom paid. Investigators trace the flow!');
                                                setTimeout(() => setStatusMsg(''), 3000);
                                            } catch (e) {
                                                setStatusMsg('❌ ' + (e.reason || e.message));
                                            }
                                        }}
                                        disabled={!wallet.signer || !ransomContractAddress}
                                        style={{
                                            padding: '0.5rem 1rem',
                                            background: (!wallet.signer || !ransomContractAddress) ? '#475569' : '#ef4444',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '0.5rem',
                                            cursor: (!wallet.signer || !ransomContractAddress) ? 'not-allowed' : 'pointer',
                                            fontWeight: 'bold'
                                        }}
                                    >
                                        💸 Pay Ransom
                                    </button>
                                </div>
                                <p style={{fontSize: '0.75rem', color: '#64748b'}}>
                                    Instructor: Deploy via Contract Builder → Ransomware Payment. Set attacker address. Share contract address with class.
                                </p>
                            </div>
                        )}
                    </div>
                    
                    {/* ========== CONTRACT LAB ========== */}
                    <div style={{
                        marginTop: '2rem',
                        padding: '1.5rem',
                        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(99, 102, 241, 0.1))',
                        borderRadius: '1rem',
                        border: '1px solid rgba(139, 92, 246, 0.3)'
                    }}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('embeddedContractLab')}
                            style={{ marginBottom: livePageBlocksOpen.embeddedContractLab ? '0.5rem' : 0, color: '#f8fafc' }}
                        >
                            <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>🏗️ Contract Lab</span>
                            <span style={{ color: '#94a3b8' }}>{livePageBlocksOpen.embeddedContractLab ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.embeddedContractLab && (
                            <div style={{marginTop: '1rem'}}>
                                <ContractLab
                                    provider={provider}
                                    rpcUrl={rpcUrl}
                                    wallet={wallet}
                                    posAddress={posAddress}
                                    onLoadScript={(code) => {
                                      setScriptCode(code);
                                      setLoadCodeForConsole(code);
                                      setScriptPlaygroundOpen(true);
                                      setStatusMsg('✓ Script loaded! Lab Terminal expanded below — code will appear when the Hardhat prompt is ready.');
                                      setTimeout(() => setStatusMsg(''), 4000);
                                      setTimeout(() => document.getElementById('lab-terminal-section')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
                                    }}
                                    setStatusMsg={setStatusMsg}
                                />
                            </div>
                        )}
                    </div>
                    
                    {/* ========== SCRIPT PLAYGROUND (Phase 6) ========== */}
                    {/* ========== BLOCKCHAIN CONSOLE (REPL) ========== */}
                    <div
                        id="lab-terminal-section"
                        style={{
                            marginTop: '2rem',
                            padding: '1rem 1.25rem',
                            background: '#1a1a2e',
                            borderRadius: '0.75rem',
                            border: '1px solid #1e293b',
                        }}
                    >
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('labTerminalSection')}
                            style={{ marginBottom: livePageBlocksOpen.labTerminalSection ? '0.5rem' : 0, color: '#f8fafc' }}
                        >
                            <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>🖥️ Lab Terminal</span>
                            <span style={{ color: '#94a3b8' }}>{livePageBlocksOpen.labTerminalSection ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.labTerminalSection && (
                        <>
                        <button
                            type="button"
                            onClick={() => setScriptPlaygroundOpen(!scriptPlaygroundOpen)}
                            style={{
                                width: '100%',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                background: 'rgba(0,0,0,0.25)',
                                border: '1px solid #334155',
                                borderRadius: scriptPlaygroundOpen ? '0.5rem 0.5rem 0 0' : '0.5rem',
                                color: '#f8fafc',
                                fontSize: '0.95rem',
                                cursor: 'pointer',
                                padding: '0.65rem 1rem'
                            }}
                        >
                            <span>Terminal session</span>
                            <span style={{fontSize: '0.8rem', color: '#64748b'}}>{scriptPlaygroundOpen ? '▼ collapse' : '▶ expand'}</span>
                        </button>
                        {scriptPlaygroundOpen && (
                            <InlineTerminal
                                loadCode={loadCodeForConsole}
                                onLoadCodeConsumed={() => setLoadCodeForConsole('')}
                                rpcUrl={rpcUrl}
                                terminalRpcUrl={terminalRpcUrl}
                                autoStartHardhat={false}
                            />
                        )}
                        </>
                        )}
                    </div>
                    
                    {/* ========== LAB COMPLETION & FEEDBACK SECTION ========== */}
                    <div style={{
                        marginTop: '2rem',
                        padding: '1.5rem',
                        background: '#1e293b',
                        borderRadius: '1rem',
                        border: '1px solid #334155'
                    }}>
                        <button
                            type="button"
                            className="live-page-block-header"
                            onClick={() => toggleLivePageBlock('labProgress')}
                            style={{ marginBottom: livePageBlocksOpen.labProgress ? '0.75rem' : 0, color: '#f8fafc', alignItems: 'flex-start' }}
                        >
                            <div style={{ flex: 1 }}>
                                <h3 style={{margin: 0, color: '#f8fafc'}}>🎯 Lab Progress</h3>
                                <p style={{margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: '#94a3b8'}}>
                                    Complete hands-on activities to finish the lab
                                </p>
                            </div>
                            <span style={{ color: '#94a3b8', flexShrink: 0 }}>{livePageBlocksOpen.labProgress ? '▼' : '▶'}</span>
                        </button>
                        {livePageBlocksOpen.labProgress && (
                        <>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'flex-end',
                            marginBottom: '1rem',
                            flexWrap: 'wrap',
                            gap: '1rem'
                        }}>
                            <FeedbackButton section="live-network" />
                        </div>
                        
                        {/* Progress Checklist */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: '0.75rem',
                            marginTop: 0
                        }}>
                            {[
                                { label: 'Received funds from instructor', done: parseFloat(wallet.balance) > 0 },
                                { label: 'Sent a transaction', done: txHistory.some(tx => tx.type === 'sent') },
                                { label: 'Posted in class chat', done: messages.some(m => m.sender === wallet.address) },
                            ].map((item, idx) => (
                                <div key={idx} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    padding: '0.75rem',
                                    background: item.done ? 'rgba(34, 197, 94, 0.1)' : 'rgba(0,0,0,0.2)',
                                    borderRadius: '0.5rem',
                                    border: item.done ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid transparent'
                                }}>
                                    <span style={{
                                        fontSize: '1.2rem',
                                        color: item.done ? '#22c55e' : '#64748b'
                                    }}>
                                        {item.done ? '✅' : '⬜'}
                                    </span>
                                    <span style={{
                                        color: item.done ? '#86efac' : '#94a3b8',
                                        fontSize: '0.9rem'
                                    }}>
                                        {item.label}
                                    </span>
                                </div>
                            ))}
                        </div>
                        </>
                        )}
                    </div>
                    
                    {statusMsg && (
                        <div className="status-footer" style={{
                            background: statusMsg.includes('❌') ? 'rgba(239, 68, 68, 0.2)' : 
                                       statusMsg.includes('✅') ? 'rgba(34, 197, 94, 0.2)' :
                                       statusMsg.includes('⚠️') ? 'rgba(251, 191, 36, 0.2)' :
                                       'rgba(59, 130, 246, 0.2)',
                            borderColor: statusMsg.includes('❌') ? 'rgba(239, 68, 68, 0.4)' : 
                                        statusMsg.includes('✅') ? 'rgba(34, 197, 94, 0.4)' :
                                        statusMsg.includes('⚠️') ? 'rgba(251, 191, 36, 0.4)' :
                                        'rgba(59, 130, 246, 0.4)'
                        }}>
                            {statusMsg}
                        </div>
                    )}
                    
                    {/* New Wallet Credentials Modal - copyable address & private key */}
                    {newWalletModal && (
                        <div
                            style={{
                                position: 'fixed',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                background: 'rgba(0,0,0,0.85)',
                                zIndex: 10001,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                padding: '2rem'
                            }}
                            onClick={() => setNewWalletModal(null)}
                        >
                            <div
                                style={{
                                    background: '#1e293b',
                                    borderRadius: '1rem',
                                    padding: '1.5rem 2rem',
                                    border: '2px solid #3b82f6',
                                    maxWidth: '500px',
                                    width: '100%'
                                }}
                                onClick={(e) => e.stopPropagation()}
                            >
                                <h3 style={{ margin: '0 0 1rem 0', color: '#f8fafc', fontSize: '1.25rem' }}>
                                    ✅ New Wallet Created
                                </h3>
                                <p style={{ color: '#94a3b8', marginBottom: '1rem', fontSize: '0.9rem' }}>
                                    Save these credentials. You need the private key to access this wallet later.
                                </p>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{display: 'block', color: '#94a3b8', fontSize: '0.8rem', marginBottom: '0.35rem'}}>Address</label>
                                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                        <input
                                            readOnly
                                            value={newWalletModal.address}
                                            style={{
                                                flex: 1,
                                                padding: '0.5rem',
                                                background: 'rgba(0,0,0,0.3)',
                                                border: '1px solid rgba(59, 130, 246, 0.4)',
                                                borderRadius: '0.35rem',
                                                color: '#f1f5f9',
                                                fontFamily: 'monospace',
                                                fontSize: '0.85rem'
                                            }}
                                        />
                                        <button
                                            onClick={async () => { await copyToClipboard(newWalletModal.address); }}
                                            style={{
                                                padding: '0.5rem 1rem',
                                                background: 'rgba(59, 130, 246, 0.3)',
                                                border: '1px solid rgba(59, 130, 246, 0.5)',
                                                borderRadius: '0.35rem',
                                                color: '#93c5fd',
                                                cursor: 'pointer',
                                                fontSize: '0.85rem'
                                            }}
                                        >
                                            📋 Copy
                                        </button>
                                    </div>
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{display: 'block', color: '#fbbf24', fontSize: '0.8rem', marginBottom: '0.35rem'}}>⚠️ Private Key (NEVER share)</label>
                                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                        <input
                                            readOnly
                                            value={newWalletModal.privateKey}
                                            style={{
                                                flex: 1,
                                                padding: '0.5rem',
                                                background: 'rgba(0,0,0,0.3)',
                                                border: '1px solid rgba(251, 191, 36, 0.4)',
                                                borderRadius: '0.35rem',
                                                color: '#f1f5f9',
                                                fontFamily: 'monospace',
                                                fontSize: '0.85rem'
                                            }}
                                        />
                                        <button
                                            onClick={async () => { await copyToClipboard(newWalletModal.privateKey); }}
                                            style={{
                                                padding: '0.5rem 1rem',
                                                background: 'rgba(251, 191, 36, 0.2)',
                                                border: '1px solid rgba(251, 191, 36, 0.5)',
                                                borderRadius: '0.35rem',
                                                color: '#fcd34d',
                                                cursor: 'pointer',
                                                fontSize: '0.85rem'
                                            }}
                                        >
                                            📋 Copy
                                        </button>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setNewWalletModal(null)}
                                    style={{
                                        width: '100%',
                                        padding: '0.6rem',
                                        background: 'rgba(34, 197, 94, 0.2)',
                                        border: '1px solid rgba(34, 197, 94, 0.5)',
                                        borderRadius: '0.35rem',
                                        color: '#86efac',
                                        cursor: 'pointer',
                                        fontSize: '1rem'
                                    }}
                                >
                                    Got it — I've saved my credentials
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Help Guide Overlay */}
                    {showLiveHelp && (
                        <div 
                            style={{
                                position: 'fixed',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                background: 'rgba(0,0,0,0.9)',
                                zIndex: 10000,
                                overflow: 'auto',
                                padding: '2rem'
                            }}
                            onClick={() => setShowLiveHelp(false)}
                        >
                            <div 
                                style={{
                                    maxWidth: '900px',
                                    margin: '0 auto',
                                    background: '#1e293b',
                                    borderRadius: '1rem',
                                    padding: '2rem',
                                    border: '2px solid #3b82f6'
                                }}
                                onClick={(e) => e.stopPropagation()}
                            >
                                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem'}}>
                                    <h2 style={{margin: 0, color: '#f8fafc', fontSize: '1.5rem'}}>📖 Live Network Guide</h2>
                                    <button
                                        onClick={() => setShowLiveHelp(false)}
                                        style={{
                                            background: 'rgba(239, 68, 68, 0.2)',
                                            border: '1px solid rgba(239, 68, 68, 0.4)',
                                            color: '#fca5a5',
                                            padding: '0.5rem 1rem',
                                            borderRadius: '0.5rem',
                                            cursor: 'pointer',
                                            fontSize: '1rem'
                                        }}
                                    >
                                        ✕ Close
                                    </button>
                                </div>
                                
                                <p style={{color: '#94a3b8', marginBottom: '2rem', fontSize: '1rem', lineHeight: 1.6}}>
                                    Welcome to the Live Network! This is your hands-on blockchain experience where you can send real transactions, 
                                    stake ETH, and interact with classmates.
                                </p>
                                
                                {/* Feature Guide Sections */}
                                <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
                                    
                                    {/* Wallet Header */}
                                    <div style={{background: 'rgba(59, 130, 246, 0.1)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(59, 130, 246, 0.3)'}}>
                                        <h3 style={{color: '#60a5fa', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>💳 Wallet Header (Blue Section)</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>Connection Status:</strong> Shows if you're connected to the blockchain and the current block number</li>
                                            <li><strong>Your Nickname:</strong> Your display name visible to classmates</li>
                                            <li><strong>Your Address:</strong> Your unique blockchain address (like an account number)</li>
                                            <li><strong>Balance:</strong> How much ETH you have in your wallet</li>
                                            <li><strong>📋 Copy:</strong> Copy your address to share with others</li>
                                            <li><strong>⚙️ Account:</strong> View your account details</li>
                                        </ul>
                                    </div>
                                    
                                    {/* Quick Actions */}
                                    <div style={{background: 'rgba(16, 185, 129, 0.1)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(16, 185, 129, 0.3)'}}>
                                        <h3 style={{color: '#34d399', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>⚡ Quick Action Buttons</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>💰 Test ETH:</strong> Ask your instructor for test ETH. Only the instructor can issue funds.</li>
                                            <li><strong>📤 Send:</strong> Jump to the Send ETH section to transfer funds</li>
                                            <li><strong>📥 Stake:</strong> Jump to the Staking section to participate in staking</li>
                                        </ul>
                                    </div>
                                    
                                    {/* Send ETH */}
                                    <div style={{background: 'rgba(139, 92, 246, 0.1)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(139, 92, 246, 0.3)'}}>
                                        <h3 style={{color: '#a78bfa', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>📤 Send ETH Section</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>Recipient Address:</strong> Paste the address of who you want to send ETH to</li>
                                            <li><strong>Amount:</strong> Enter how much ETH to send</li>
                                            <li><strong>Quick Amounts:</strong> Click preset amounts (0.1, 0.5, 1.0 ETH) for convenience</li>
                                            <li><strong>Send Button:</strong> Executes the transaction on the blockchain</li>
                                            <li><em>Tip: Click a classmate's name in the sidebar to auto-fill their address!</em></li>
                                        </ul>
                                    </div>
                                    
                                    {/* Staking */}
                                    <div style={{background: 'rgba(251, 191, 36, 0.1)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(251, 191, 36, 0.3)'}}>
                                        <h3 style={{color: '#fbbf24', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>🥩 Staking Pool Section</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>Pool Stats:</strong> Shows total ETH staked and number of participants</li>
                                            <li><strong>Your Stake:</strong> How much you've staked and rewards earned</li>
                                            <li><strong>Stake Button:</strong> Lock up ETH to earn rewards (like a savings account)</li>
                                            <li><strong>Unstake:</strong> Request to withdraw your staked ETH (has unbonding period)</li>
                                            <li><strong>Claim Rewards:</strong> Collect your earned staking rewards</li>
                                            <li><em>Staking demonstrates how Proof of Stake consensus works!</em></li>
                                        </ul>
                                    </div>
                                    
                                    {/* Transaction History */}
                                    <div style={{background: 'rgba(236, 72, 153, 0.1)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(236, 72, 153, 0.3)'}}>
                                        <h3 style={{color: '#f472b6', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>📜 Transaction History</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>Sent/Received:</strong> Shows all your incoming and outgoing transactions</li>
                                            <li><strong>Block Number:</strong> Which block the transaction was included in</li>
                                            <li><strong>Copy Hash:</strong> Copy the transaction ID to look it up</li>
                                            <li><em>This is your permanent, immutable record on the blockchain!</em></li>
                                        </ul>
                                    </div>
                                    
                                    {/* Class Chat */}
                                    <div style={{background: 'rgba(6, 182, 212, 0.1)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(6, 182, 212, 0.3)'}}>
                                        <h3 style={{color: '#22d3ee', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>💬 Class Chat</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>Messages:</strong> Chat messages from all classmates</li>
                                            <li><strong>Click Names:</strong> Click a sender's name to copy their address</li>
                                            <li><strong>Post Message:</strong> Send a message that gets recorded on the blockchain</li>
                                            <li><em>Every message is a real blockchain transaction!</em></li>
                                        </ul>
                                    </div>
                                    
                                    {/* Sidebar */}
                                    <div style={{background: 'rgba(100, 116, 139, 0.2)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(100, 116, 139, 0.4)'}}>
                                        <h3 style={{color: '#94a3b8', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>📋 Left Sidebar</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>Connection Status:</strong> Green = connected, Red = disconnected</li>
                                            <li><strong>Your Account:</strong> Import/Export/Create wallets</li>
                                            <li><strong>Your Nickname:</strong> Set how you appear to classmates</li>
                                            <li><strong>Classmates List:</strong> See who's in the class - click to send them ETH</li>
                                            <li><strong>🧪 Diagnostics:</strong> Troubleshoot connection issues</li>
                                        </ul>
                                    </div>
                                    
                                    {/* Lab Progress */}
                                    <div style={{background: 'rgba(34, 197, 94, 0.1)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(34, 197, 94, 0.3)'}}>
                                        <h3 style={{color: '#22c55e', margin: '0 0 0.75rem 0', fontSize: '1.1rem'}}>🎯 Lab Progress (Bottom)</h3>
                                        <ul style={{color: '#cbd5e1', margin: 0, paddingLeft: '1.25rem', lineHeight: 1.8}}>
                                            <li><strong>Progress Checklist:</strong> Track what activities you've completed</li>
                                            <li><strong>Checkmarks:</strong> ✅ = completed, ⬜ = not yet done</li>
                                            <li><em>Complete activities to finish the lab!</em></li>
                                        </ul>
                                    </div>
                                    
                                </div>
                                
                                <div style={{marginTop: '2rem', padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '0.5rem', textAlign: 'center'}}>
                                    <p style={{color: '#93c5fd', margin: 0, fontSize: '0.9rem'}}>
                                        💡 <strong>Pro Tip:</strong> Click anywhere outside this guide to close it, or press the ✕ button above.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* 3b. DIAGNOSTICS VIEW */}
            {view === 'diagnostics' && (
                <DiagnosticsView
                    rpcUrl={rpcUrl}
                    provider={provider}
                    wallet={wallet}
                    posAddress={posAddress}
                    PoSABI={PoSABI}
                />
            )}
            
            {/* CLI LABS VIEW */}
            {view === 'cli' && (
                <CLILabsView isInstructor={isInstructor} rpcUrl={rpcUrl} terminalRpcUrl={terminalRpcUrl} />
            )}
            
            {/* INSTRUCTOR VIEW */}
            {view === 'instructor' && (
                <div className="instructor-view">
                    {!posAddress && (
                        <div className="instructor-setup">
                            <h2>🎓 Instructor Dashboard Setup</h2>
                            <div className="setup-card">
                                <label>Enter PoS Contract Address:</label>
                                <input 
                                    placeholder="0x..." 
                                    value={posAddress}
                                    onChange={e => {
                                        setPosAddress(e.target.value);
                                        localStorage.setItem("pos_addr", e.target.value);
                                    }}
                                />
                                <small>This address was displayed when you ran the deployment script</small>
                                <small>Also saved in CONTRACT_ADDRESS.txt</small>
                            </div>
                        </div>
                    )}
                    {posAddress && (
                        <InstructorView 
                            provider={provider}
                            posAddress={posAddress}
                            rpcUrl={rpcUrl}
                            wallet={wallet}
                            onOpenTerminal={() => openLabTerminal(rpcUrl, terminalRpcUrl)}
                        />
                    )}
                </div>
            )}

            {/* BEACON CHAIN LAB */}
            {view === 'beacon-lab' && (
                <ErrorBoundary>
                    <BeaconChainLabView provider={provider} wallet={wallet} rpcUrl={rpcUrl} />
                </ErrorBoundary>
            )}
            {view === 'contract-builder-lab' && (
                <ErrorBoundary>
                    <ContractBuilderLabView provider={provider} wallet={wallet} rpcUrl={rpcUrl} terminalRpcUrl={terminalRpcUrl} fireProgressBeacon={fireProgressBeacon} />
                </ErrorBoundary>
            )}
            {view === 'tokenization-lab' && (
                <ErrorBoundary>
                    <TokenizationLabView provider={provider} wallet={wallet} rpcUrl={rpcUrl} terminalRpcUrl={terminalRpcUrl} fireProgressBeacon={fireProgressBeacon} />
                </ErrorBoundary>
            )}
        </main>
    </div>
  )
}

export default App
