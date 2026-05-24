/**
 * TokenConceptsView - Interactive Token Concepts Learning Module
 * 
 * Teaches the difference between Fungible and Non-Fungible Tokens
 * through interactive quizzes, categorization exercises, and visualizations.
 * Section 4: Deploy real FT/NFT contracts (browser or CLI) for hands-on learning.
 */

import { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { FungibleTokenVisualizer } from '../components/mini-labs/FungibleTokenVisualizer';
import { NonFungibleTokenVisualizer } from '../components/mini-labs/NonFungibleTokenVisualizer';

const ACCOUNT_1 = '0x70997970C51812dc3A010C7d01b50e0d17dc79C8';
const sameAddress = (a, b) => a && b && String(a).toLowerCase() === String(b).toLowerCase();

const SECTIONS = [
  { id: 1, title: 'What is a Token?', video: "https://www.youtube.com/embed/aLh8jlYYvZA" },      // VIDEO PLACEHOLDER: Add YouTube embed URL for "What is a token?"
  { id: 2, title: 'FT vs NFT', video: "https://www.youtube.com/embed/OXCJxy0f4Ic" },              // VIDEO PLACEHOLDER: Add YouTube embed URL for fungible vs non-fungible
  { id: 3, title: 'Categorization', video: "https://www.youtube.com/embed/cioayqZnTOU" },         // VIDEO PLACEHOLDER: Add YouTube embed URL for token categorization
  { id: 4, title: 'How Tokens Work', video: null },         // VIDEO PLACEHOLDER: Add YouTube embed URL for how tokens work on blockchain
  { id: 5, title: 'Scenarios', video: null },              // VIDEO PLACEHOLDER: Add YouTube embed URL for real-world token scenarios
  { id: 6, title: 'Summary', video: null }                  // VIDEO PLACEHOLDER: Add YouTube embed URL for token concepts summary (optional)
  // Example: video: "https://www.youtube.com/embed/VIDEO_ID"
];

const VideoEmbed = ({ url, title }) => {
  if (!url) return null;
  return (
    <div style={{
      marginBottom: '1.5rem',
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
        🎬 Video Tutorial
      </div>
      <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
        <iframe
          src={url}
          title={title || 'Video tutorial'}
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
  );
};

const CATEGORIZATION_ITEMS = [
  { name: 'Bitcoin', answer: 'ft', hint: 'Is one Bitcoin different from another Bitcoin?' },
  { name: 'A CryptoKitty (#12345)', answer: 'nft', hint: 'Is each CryptoKitty unique with different traits?' },
  { name: 'Gift card balance ($50)', answer: 'ft', hint: 'Does it matter which $50 you spend from the card?' },
  { name: 'Your driver\'s license', answer: 'nft', hint: 'Can someone else use your specific license?' },
  { name: 'Airline miles', answer: 'ft', hint: 'Is mile #500 different from mile #501?' },
  { name: 'A Bored Ape NFT (#3749)', answer: 'nft', hint: 'Does each Bored Ape look the same?' },
  { name: 'Starbucks stars', answer: 'ft', hint: 'Does it matter which stars you redeem?' },
  { name: 'Your house title/deed', answer: 'nft', hint: 'Can your neighbor\'s deed be used for your house?' }
];

export function TokenConceptsView({ onComplete, onGoToLive, provider, wallet, rpcUrl }) {
  const [currentSection, setCurrentSection] = useState(1);
  const [score, setScore] = useState(0);
  const [answeredQuestions, setAnsweredQuestions] = useState({});
  const [categorizationAnswers, setCategorizationAnswers] = useState({});
  const [showHint, setShowHint] = useState(null);

  // Section 4: Deploy state
  const [prereqOk, setPrereqOk] = useState(false);
  const [prereqCheck, setPrereqCheck] = useState({ wallet: false, balance: false, rpc: false });
  const [ftAddress, setFtAddress] = useState('');
  const [ftDeploying, setFtDeploying] = useState(false);
  const [ftDeployError, setFtDeployError] = useState('');
  const [useSimulators, setUseSimulators] = useState(false);
  const [ftTxPending, setFtTxPending] = useState('');
  const [ftReads, setFtReads] = useState({ totalSupply: null, myBalance: null, account1Balance: null });
  const [ftMinted, setFtMinted] = useState(false);
  const [ftTransferred, setFtTransferred] = useState(false);

  // Section 4: NFT deploy state
  const [nftAddress, setNftAddress] = useState('');
  const [nftDeploying, setNftDeploying] = useState(false);
  const [nftDeployError, setNftDeployError] = useState('');
  const [nftTxPending, setNftTxPending] = useState('');
  const [nftError, setNftError] = useState('');
  const [nftReads, setNftReads] = useState({ ownerOf1: null, myBalance: null, account1Balance: null });
  const [nftMinted, setNftMinted] = useState(false);
  const [nftTransferred, setNftTransferred] = useState(false);
  const [cliExpanded, setCliExpanded] = useState(false);

  // Prerequisite check for Section 4
  useEffect(() => {
    if (currentSection !== 4) return;
    const check = async () => {
      const hasWallet = !!(wallet?.address && wallet?.signer);
      const hasRpc = !!provider;
      let hasBalance = false;
      if (hasWallet && provider) {
        try {
          const bal = await provider.getBalance(wallet.address);
          hasBalance = bal >= ethers.parseEther('0.1');
        } catch (_) {}
      }
      setPrereqCheck({ wallet: hasWallet, balance: hasBalance, rpc: hasRpc });
      setPrereqOk(hasWallet && hasBalance && hasRpc);
    };
    check();
  }, [currentSection, provider, wallet]);

  const handleQuizAnswer = (questionId, selectedAnswer, correctAnswer, points) => {
    if (answeredQuestions[questionId]) return;
    
    const isCorrect = selectedAnswer === correctAnswer;
    setAnsweredQuestions(prev => ({
      ...prev,
      [questionId]: { selected: selectedAnswer, correct: isCorrect }
    }));
    
    if (isCorrect) {
      setScore(prev => prev + points);
    }
  };

  const handleCategorization = (itemName, answer) => {
    if (categorizationAnswers[itemName]) return;
    
    const item = CATEGORIZATION_ITEMS.find(i => i.name === itemName);
    const isCorrect = answer === item.answer;
    
    setCategorizationAnswers(prev => ({
      ...prev,
      [itemName]: { selected: answer, correct: isCorrect }
    }));
    
    if (isCorrect) {
      setScore(prev => prev + 5);
    }
  };

  const QuizQuestion = ({ id, question, options, correctIndex, points, explanation }) => {
    const answered = answeredQuestions[id];
    const correctLetter = String.fromCharCode(65 + correctIndex);
    
    return (
      <div style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: '0.5rem',
        padding: '1.25rem',
        marginBottom: '1rem'
      }}>
        <div style={{ color: '#f8fafc', fontSize: '1rem', marginBottom: '1rem' }}>
          {question}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {options.map((opt, i) => {
            const letter = String.fromCharCode(65 + i);
            const isSelected = answered?.selected === letter;
            const isCorrect = i === correctIndex;
            
            let bgColor = 'rgba(71, 85, 105, 0.3)';
            let borderColor = '#475569';
            
            if (answered) {
              if (isCorrect) {
                bgColor = 'rgba(16, 185, 129, 0.2)';
                borderColor = '#10b981';
              } else if (isSelected && !isCorrect) {
                bgColor = 'rgba(239, 68, 68, 0.2)';
                borderColor = '#ef4444';
              }
            }
            
            return (
              <button
                key={i}
                onClick={() => handleQuizAnswer(id, letter, correctLetter, points)}
                disabled={!!answered}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  background: bgColor,
                  border: `2px solid ${borderColor}`,
                  borderRadius: '0.375rem',
                  color: '#f8fafc',
                  cursor: answered ? 'default' : 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s'
                }}
              >
                <span style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  background: isSelected ? (isCorrect ? '#10b981' : '#ef4444') : '#334155',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '0.9rem'
                }}>
                  {letter}
                </span>
                <span>{opt}</span>
              </button>
            );
          })}
        </div>
        {answered && (
          <div
            role="status"
            aria-live="polite"
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              background: answered.correct ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              borderRadius: '0.375rem',
              color: answered.correct ? '#10b981' : '#ef4444',
              fontSize: '0.9rem'
            }}
          >
            {answered.correct ? '✓ Correct!' : `✗ Incorrect. The answer was ${correctLetter}.`}
            {explanation && (
              <div style={{ color: '#94a3b8', marginTop: '0.5rem' }}>{explanation}</div>
            )}
          </div>
        )}
      </div>
    );
  };

  const YesNoQuestion = ({ id, question, correctAnswer, points, hint }) => {
    const answered = answeredQuestions[id];
    
    return (
      <div style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '0.75rem'
      }}>
        <div style={{ color: '#f8fafc', fontSize: '0.95rem', marginBottom: '0.75rem' }}>
          {question}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {['yes', 'no'].map(answer => {
            const isSelected = answered?.selected === answer;
            const isCorrect = answer === correctAnswer;
            
            let bgColor = '#334155';
            if (answered) {
              if (isCorrect) bgColor = '#10b981';
              else if (isSelected) bgColor = '#ef4444';
            }
            
            return (
              <button
                key={answer}
                onClick={() => handleQuizAnswer(id, answer, correctAnswer, points)}
                disabled={!!answered}
                style={{
                  flex: 1,
                  padding: '0.6rem',
                  background: bgColor,
                  border: 'none',
                  borderRadius: '0.375rem',
                  color: '#f8fafc',
                  fontWeight: 'bold',
                  cursor: answered ? 'default' : 'pointer',
                  textTransform: 'uppercase',
                  fontSize: '0.85rem'
                }}
              >
                {answer}
              </button>
            );
          })}
        </div>
        {!answered && hint && (
          <button
            onClick={() => setShowHint(showHint === id ? null : id)}
            style={{
              marginTop: '0.5rem',
              background: 'none',
              border: 'none',
              color: '#fbbf24',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            {showHint === id ? 'Hide hint' : 'Need a hint?'}
          </button>
        )}
        {showHint === id && !answered && (
          <div style={{
            marginTop: '0.5rem',
            padding: '0.5rem',
            background: 'rgba(251, 191, 36, 0.1)',
            borderRadius: '0.25rem',
            color: '#fbbf24',
            fontSize: '0.85rem'
          }}>
            Hint: {hint}
          </div>
        )}
        {answered && (
          <div role="status" aria-live="polite" style={{
            marginTop: '0.5rem',
            fontSize: '0.9rem',
            color: answered.correct ? '#10b981' : '#ef4444'
          }}>
            {answered.correct ? '✓ Correct!' : '✗ Incorrect.'}
          </div>
        )}
      </div>
    );
  };

  const renderSection1 = () => (
    <div>
      <h3 style={{ color: '#3b82f6', marginBottom: '1rem' }}>What is a Token?</h3>
      <VideoEmbed url={SECTIONS[0].video} title="What is a Token?" />
      
      <div style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        borderRadius: '0.75rem',
        padding: '1.5rem',
        marginBottom: '1.5rem'
      }}>
        <p style={{ color: '#cbd5e1', lineHeight: 1.7, marginTop: 0 }}>
          A token is a <strong style={{ color: '#3b82f6' }}>digital representation</strong> of something that exists on the blockchain.
        </p>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1rem',
          marginTop: '1.5rem',
          marginBottom: '1.5rem'
        }}>
          {[
            { icon: '💰', label: 'VALUE', desc: '(money)' },
            { icon: '🏠', label: 'OWNERSHIP', desc: '(property)' },
            { icon: '🎫', label: 'ACCESS', desc: '(tickets)' }
          ].map(item => (
            <div key={item.label} style={{
              background: 'rgba(0,0,0,0.3)',
              borderRadius: '0.5rem',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{item.icon}</div>
              <div style={{ color: '#f8fafc', fontWeight: 'bold' }}>{item.label}</div>
              <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>{item.desc}</div>
            </div>
          ))}
        </div>
        
        <div style={{ color: '#cbd5e1' }}>
          <p style={{ marginBottom: '0.75rem' }}>Tokens live on the blockchain and can be:</p>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', lineHeight: 1.8 }}>
            <li><strong style={{ color: '#10b981' }}>Created</strong> (minted)</li>
            <li><strong style={{ color: '#10b981' }}>Owned</strong> (held in a wallet)</li>
            <li><strong style={{ color: '#10b981' }}>Transferred</strong> (sent to another wallet)</li>
            <li><strong style={{ color: '#10b981' }}>Destroyed</strong> (burned)</li>
          </ul>
        </div>
      </div>
      
      <h4 style={{ color: '#fbbf24', marginBottom: '1rem' }}>Quiz Time!</h4>
      
      <QuizQuestion
        id="q1-1"
        question="Which of these is NOT something tokens can represent?"
        options={['Money or currency', 'Concert tickets', 'Your private thoughts', 'Property ownership']}
        correctIndex={2}
        points={10}
        explanation="Tokens represent things that can be verified and transferred on a blockchain."
      />
      
      <QuizQuestion
        id="q1-2"
        question='What happens when a token is "minted"?'
        options={['It is destroyed', 'A new token is created', 'It is transferred', 'It is hidden']}
        correctIndex={1}
        points={10}
        explanation="Minting creates new tokens, similar to how a government prints new money."
      />
    </div>
  );

  const renderSection2 = () => (
    <div>
      <h3 style={{ color: '#3b82f6', marginBottom: '1rem' }}>Fungible vs Non-Fungible</h3>
      <VideoEmbed url={SECTIONS[1].video} title="FT vs NFT" />
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div style={{
          background: 'rgba(16, 185, 129, 0.1)',
          border: '2px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '0.75rem',
          padding: '1.25rem'
        }}>
          <h4 style={{ color: '#10b981', marginTop: 0 }}>FUNGIBLE (Interchangeable)</h4>
          <div style={{
            display: 'flex',
            gap: '0.5rem',
            marginBottom: '1rem',
            justifyContent: 'center'
          }}>
            {['$1', '$1', '$1', '$1', '$1'].map((d, i) => (
              <div key={i} style={{
                width: '36px',
                height: '36px',
                background: '#10b981',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#000',
                fontWeight: 'bold',
                fontSize: '0.8rem'
              }}>{d}</div>
            ))}
          </div>
          <ul style={{ color: '#cbd5e1', paddingLeft: '1.25rem', margin: 0, lineHeight: 1.7 }}>
            <li>Any $1 = Any $1</li>
            <li>Can split: $1 = 4 quarters</li>
            <li>Examples: US Dollars, Loyalty points, Arcade tokens</li>
          </ul>
        </div>
        
        <div style={{
          background: 'rgba(139, 92, 246, 0.1)',
          border: '2px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '0.75rem',
          padding: '1.25rem'
        }}>
          <h4 style={{ color: '#8b5cf6', marginTop: 0 }}>NON-FUNGIBLE (Unique)</h4>
          <div style={{
            display: 'flex',
            gap: '0.5rem',
            marginBottom: '1rem',
            justifyContent: 'center'
          }}>
            {['A', 'B', 'C', 'D'].map((letter, i) => (
              <div key={i} style={{
                width: '36px',
                height: '36px',
                background: '#8b5cf6',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 'bold'
              }}>{letter}</div>
            ))}
          </div>
          <ul style={{ color: '#cbd5e1', paddingLeft: '1.25rem', margin: 0, lineHeight: 1.7 }}>
            <li>Each one is different</li>
            <li>Cannot split artwork in half</li>
            <li>Examples: House deed, Concert ticket (seat 5A)</li>
          </ul>
        </div>
      </div>
      
      <div style={{
        background: 'rgba(251, 191, 36, 0.1)',
        border: '1px solid rgba(251, 191, 36, 0.3)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div style={{ color: '#fbbf24', fontWeight: 'bold', marginBottom: '0.5rem' }}>KEY DIFFERENCE:</div>
        <p style={{ color: '#cbd5e1', margin: 0 }}>
          <strong style={{ color: '#10b981' }}>Fungible:</strong> "Do you have 10?" - Any 10 will do<br/>
          <strong style={{ color: '#8b5cf6' }}>Non-Fungible:</strong> "Do you have #5?" - Only that specific one
        </p>
      </div>
      
      <h4 style={{ color: '#fbbf24', marginBottom: '1rem' }}>Quiz Time!</h4>
      
      <YesNoQuestion
        id="q2-1"
        question="If Alice has 10 FT tokens and Bob has 10 FT tokens of the same type, do they have the same thing?"
        correctAnswer="yes"
        points={5}
        hint="Think about if you both have $10 bills - are they equivalent?"
      />
      
      <YesNoQuestion
        id="q2-2"
        question="If Alice has NFT #5 and Bob has NFT #10, do they have the same thing?"
        correctAnswer="no"
        points={5}
        hint="Think about if you have ticket to seat 5A and someone else has seat 10B."
      />
      
      <YesNoQuestion
        id="q2-3"
        question="Can you send half of an NFT to someone?"
        correctAnswer="no"
        points={5}
        hint="Can you give someone half of a concert ticket?"
      />
      
      <YesNoQuestion
        id="q2-4"
        question="Can you send half of your FT balance to someone?"
        correctAnswer="yes"
        points={5}
        hint="Can you give someone half of your money?"
      />
    </div>
  );

  const renderSection3 = () => (
    <div>
      <h3 style={{ color: '#3b82f6', marginBottom: '1rem' }}>Categorization Exercise</h3>
      <VideoEmbed url={SECTIONS[2].video} title="Token Categorization" />
      
      <p style={{ color: '#cbd5e1', marginBottom: '1.5rem' }}>
        For each item below, decide if it's <strong style={{ color: '#10b981' }}>Fungible (F)</strong> or{' '}
        <strong style={{ color: '#8b5cf6' }}>Non-Fungible (NF)</strong>. Click to categorize!
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {CATEGORIZATION_ITEMS.map((item, i) => {
          const answered = categorizationAnswers[item.name];
          
          return (
            <div key={i} style={{
              background: 'rgba(0,0,0,0.2)',
              borderRadius: '0.5rem',
              padding: '1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem'
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ color: '#f8fafc', fontWeight: 'bold' }}>{item.name}</div>
                {!answered && (
                  <button
                    onClick={() => setShowHint(showHint === item.name ? null : item.name)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#fbbf24',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      padding: 0,
                      marginTop: '0.25rem'
                    }}
                  >
                    {showHint === item.name ? 'Hide hint' : 'Hint?'}
                  </button>
                )}
                {showHint === item.name && !answered && (
                  <div style={{ color: '#fbbf24', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                    {item.hint}
                  </div>
                )}
              </div>
              
              {!answered ? (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => handleCategorization(item.name, 'ft')}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#10b981',
                      border: 'none',
                      borderRadius: '0.375rem',
                      color: '#fff',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    Fungible
                  </button>
                  <button
                    onClick={() => handleCategorization(item.name, 'nft')}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#8b5cf6',
                      border: 'none',
                      borderRadius: '0.375rem',
                      color: '#fff',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    Non-Fungible
                  </button>
                </div>
              ) : (
                <div
                  role="status"
                  aria-live="polite"
                  style={{
                    padding: '0.5rem 1rem',
                    background: answered.correct ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                    borderRadius: '0.375rem',
                    color: answered.correct ? '#10b981' : '#ef4444',
                    fontWeight: 'bold'
                  }}
                >
                  {answered.correct ? '✓' : '✗'} {item.answer === 'ft' ? 'Fungible' : 'Non-Fungible'}
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {Object.keys(categorizationAnswers).length === CATEGORIZATION_ITEMS.length && (
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '0.5rem'
        }}>
          <div style={{ color: '#93c5fd', fontWeight: 'bold', marginBottom: '0.5rem' }}>Summary:</div>
          <p style={{ color: '#cbd5e1', margin: 0, fontSize: '0.9rem' }}>
            <strong style={{ color: '#10b981' }}>Fungible:</strong> Bitcoin, Gift card balance, Airline miles, Starbucks stars<br/>
            <strong style={{ color: '#8b5cf6' }}>Non-Fungible:</strong> CryptoKitty, Driver's license, Bored Ape, House deed
          </p>
        </div>
      )}
    </div>
  );

  const handleDeployFT = async () => {
    if (!wallet?.signer || !provider) return;
    setFtDeployError('');
    setFtDeploying(true);
    try {
      let artifact;
      try {
        artifact = (await import('../contracts/SimpleFT.json')).default;
      } catch (_) {
        setFtDeployError('SimpleFT artifact not found. Run from project root: npm run copy-token-artifacts');
        return;
      }
      const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet.signer);
      const contract = await factory.deploy('LearningToken', 'LTK');
      await contract.waitForDeployment();
      const addr = await contract.getAddress();
      setFtAddress(addr);
    } catch (e) {
      setFtDeployError(e.message || 'Deploy failed');
    } finally {
      setFtDeploying(false);
    }
  };

  const getFtContract = () => {
    if (!ftAddress || !wallet?.signer) return null;
    try {
      const abi = [
        'function mint(address to, uint256 amount)',
        'function transfer(address to, uint256 amount)',
        'function balanceOf(address) view returns (uint256)',
        'function totalSupply() view returns (uint256)'
      ];
      return new ethers.Contract(ftAddress, abi, wallet.signer);
    } catch (_) { return null; }
  };

  const handleMintFT = async () => {
    const c = getFtContract();
    if (!c) return;
    setFtTxPending('mint');
    try {
      const tx = await c.mint(wallet.address, 100n);
      await tx.wait();
      setFtMinted(true);
      setFtReads(prev => ({ ...prev, totalSupply: '100', myBalance: '100', account1Balance: '0' }));
    } catch (e) {
      console.error(e);
    } finally {
      setFtTxPending('');
    }
  };

  const handleTransferFT = async () => {
    const c = getFtContract();
    if (!c) return;
    setFtTxPending('transfer');
    try {
      const tx = await c.transfer(ACCOUNT_1, 30n);
      await tx.wait();
      setFtTransferred(true);
      setFtReads(prev => ({ ...prev, totalSupply: '100', myBalance: '70', account1Balance: '30' }));
    } catch (e) {
      console.error(e);
    } finally {
      setFtTxPending('');
    }
  };

  const handleReadFT = async () => {
    const c = getFtContract();
    if (!c || !provider) return;
    try {
      const [supply, myBal, acc1Bal] = await Promise.all([
        c.totalSupply(),
        c.balanceOf(wallet.address),
        c.balanceOf(ACCOUNT_1)
      ]);
      setFtReads({
        totalSupply: supply.toString(),
        myBalance: myBal.toString(),
        account1Balance: acc1Bal.toString()
      });
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeployNFT = async () => {
    if (!wallet?.signer || !provider) return;
    setNftDeployError('');
    setNftError('');
    setNftDeploying(true);
    try {
      let artifact;
      try {
        artifact = (await import('../contracts/SimpleNFT.json')).default;
      } catch (_) {
        setNftDeployError('SimpleNFT artifact not found. Run from project root: npm run copy-token-artifacts');
        return;
      }
      const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet.signer);
      const contract = await factory.deploy('EventTicket', 'TKT');
      await contract.waitForDeployment();
      const addr = await contract.getAddress();
      setNftAddress(addr);
    } catch (e) {
      setNftDeployError(e.message || 'Deploy failed');
    } finally {
      setNftDeploying(false);
    }
  };

  const getNftContract = () => {
    if (!nftAddress || !wallet?.signer) return null;
    try {
      const abi = [
        'function mint(address to) returns (uint256)',
        'function mintBatch(address to, uint256 count) returns (uint256[])',
        'function transfer(address to, uint256 tokenId)',
        'function ownerOf(uint256 tokenId) view returns (address)',
        'function balanceOf(address) view returns (uint256)'
      ];
      return new ethers.Contract(nftAddress, abi, wallet.signer);
    } catch (_) { return null; }
  };

  const handleMintNFT = async () => {
    const c = getNftContract();
    if (!c) {
      setNftError('Wallet not connected. Use Account Manager in the Live tab to create/select a wallet, then return here.');
      return;
    }
    setNftError('');
    setNftTxPending('mint');
    try {
      const tx = await c.mintBatch(wallet.address, 3);
      await tx.wait();
      setNftMinted(true);
      setNftReads(prev => ({ ...prev, ownerOf1: wallet.address, myBalance: '3', account1Balance: '0' }));
    } catch (e) {
      setNftError(e.message || 'Mint failed');
      console.error(e);
    } finally {
      setNftTxPending('');
    }
  };

  const handleTransferNFT = async () => {
    const c = getNftContract();
    if (!c) {
      setNftError('Wallet not connected.');
      return;
    }
    setNftError('');
    setNftTxPending('transfer');
    try {
      const tx = await c.transfer(ACCOUNT_1, 1n);
      await tx.wait();
      setNftTransferred(true);
      setNftReads(prev => ({ ...prev, ownerOf1: ACCOUNT_1, myBalance: '2', account1Balance: '1' }));
    } catch (e) {
      setNftError(e.message || 'Transfer failed');
      console.error(e);
    } finally {
      setNftTxPending('');
    }
  };

  const handleReadNFT = async () => {
    const c = getNftContract();
    if (!c || !provider) return;
    try {
      const [owner1, myBal, acc1Bal] = await Promise.all([
        c.ownerOf(1n),
        c.balanceOf(wallet.address),
        c.balanceOf(ACCOUNT_1)
      ]);
      setNftReads({
        ownerOf1: owner1,
        myBalance: myBal.toString(),
        account1Balance: acc1Bal.toString()
      });
    } catch (e) {
      console.error(e);
    }
  };

  const renderSection4 = () => {
    const showDeploy = prereqOk && !useSimulators;
    const showFallback = !prereqOk || useSimulators;

    return (
      <div>
        <h3 style={{ color: '#3b82f6', marginBottom: '1rem' }}>How Tokens Work on Blockchain</h3>
        <VideoEmbed url={SECTIONS[3].video} title="How Tokens Work" />

        <p style={{ color: '#cbd5e1', marginBottom: '1rem' }}>
          Explore the interactive visualizers below to see how FT and NFT transfers work differently!
        </p>

        <FungibleTokenVisualizer />
        <div style={{ marginTop: '1.5rem' }} />
        <NonFungibleTokenVisualizer />


        <h4 style={{ color: '#fbbf24', marginTop: '2rem', marginBottom: '1rem' }}>Quiz Time!</h4>
        <QuizQuestion
          id="q4-1"
          question="After Alice (100 FT) transfers 30 to Bob (50 FT), what is Alice's new balance?"
          options={['100', '70', '130', '50']}
          correctIndex={1}
          points={10}
          explanation="100 - 30 = 70. Alice sends 30 tokens, so her balance decreases by 30."
        />
        <QuizQuestion
          id="q4-2"
          question="If Alice owns NFT #1 and #3, and sends #1 to Bob, how many NFTs does Alice have now?"
          options={['0', '1', '2', '3']}
          correctIndex={1}
          points={10}
          explanation="Alice had 2 NFTs (#1 and #3), sent away #1, so she now has only #3."
        />
        <QuizQuestion
          id="q4-3"
          question="What stays the same when FTs are transferred?"
          options={['Individual balances', 'Total supply', 'Token owner', 'Token ID']}
          correctIndex={1}
          points={10}
          explanation="No new tokens are created during a transfer - total supply remains constant."
        />
      </div>
    );
  };

  const renderSection5 = () => (
    <div>
      <h3 style={{ color: '#3b82f6', marginBottom: '1rem' }}>Real-World Scenarios</h3>
      <VideoEmbed url={SECTIONS[4].video} title="Real-World Token Scenarios" />
      
      <p style={{ color: '#cbd5e1', marginBottom: '1.5rem' }}>
        Which token type would work best for each scenario?
      </p>
      
      <div style={{
        background: 'rgba(251, 191, 36, 0.05)',
        border: '1px solid rgba(251, 191, 36, 0.2)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{ color: '#fbbf24', fontWeight: 'bold', marginBottom: '0.5rem' }}>SCENARIO 1: Coffee Shop Rewards</div>
        <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
          A coffee shop wants to create a digital rewards program where customers earn points and redeem them for drinks.
          100 points = 100 points (interchangeable). Points can be partially redeemed (use 50 of your 100).
        </p>
      </div>
      
      <QuizQuestion
        id="q5-1"
        question="Which token type should the coffee shop use?"
        options={['Fungible Token (FT)', 'Non-Fungible Token (NFT)']}
        correctIndex={0}
        points={10}
        explanation="Reward points are interchangeable and can be partially redeemed - perfect for FT!"
      />
      
      <div style={{
        background: 'rgba(251, 191, 36, 0.05)',
        border: '1px solid rgba(251, 191, 36, 0.2)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{ color: '#fbbf24', fontWeight: 'bold', marginBottom: '0.5rem' }}>SCENARIO 2: Digital Art Gallery</div>
        <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
          An artist wants to sell 10 unique digital paintings. Each painting is different and has proof of ownership.
          Painting #1 is NOT the same as Painting #2. You can't buy "half" of a painting.
        </p>
      </div>
      
      <QuizQuestion
        id="q5-2"
        question="Which token type should the artist use?"
        options={['Fungible Token (FT)', 'Non-Fungible Token (NFT)']}
        correctIndex={1}
        points={10}
        explanation="Each painting is unique and indivisible - perfect for NFT!"
      />
      
      <div style={{
        background: 'rgba(251, 191, 36, 0.05)',
        border: '1px solid rgba(251, 191, 36, 0.2)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{ color: '#fbbf24', fontWeight: 'bold', marginBottom: '0.5rem' }}>SCENARIO 3: Company Stock</div>
        <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
          A company wants to issue shares of stock to employees. All shares have equal value and voting rights.
          1 share = 1 share (all identical). Can own fractional shares (0.5 shares).
        </p>
      </div>
      
      <QuizQuestion
        id="q5-3"
        question="Which token type should the company use?"
        options={['Fungible Token (FT)', 'Non-Fungible Token (NFT)']}
        correctIndex={0}
        points={10}
        explanation="All shares are identical and divisible - perfect for FT!"
      />
      
      <div style={{
        background: 'rgba(251, 191, 36, 0.05)',
        border: '1px solid rgba(251, 191, 36, 0.2)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{ color: '#fbbf24', fontWeight: 'bold', marginBottom: '0.5rem' }}>SCENARIO 4: Concert Tickets</div>
        <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
          A concert venue wants to sell tickets with assigned seats. Each ticket corresponds to a specific seat (Row A, Seat 5).
          Seat A5 is NOT the same as Seat B10. You can't have "half" a seat.
        </p>
      </div>
      
      <QuizQuestion
        id="q5-4"
        question="Which token type should the venue use?"
        options={['Fungible Token (FT)', 'Non-Fungible Token (NFT)']}
        correctIndex={1}
        points={10}
        explanation="Each seat is unique and indivisible - perfect for NFT!"
      />
    </div>
  );

  const renderSection6 = () => {
    const maxScore = 150;
    const percentage = Math.round((score / maxScore) * 100);
    const totalAnswered = Object.keys(answeredQuestions).length + Object.keys(categorizationAnswers).length;
    const totalQuestions = 13 + CATEGORIZATION_ITEMS.length;
    const correctCount = 
      Object.values(answeredQuestions).filter(a => a.correct).length +
      Object.values(categorizationAnswers).filter(a => a.correct).length;
    
    let grade, gradeColor, feedback;
    if (percentage >= 90) {
      grade = 'Excellent!';
      gradeColor = '#10b981';
      feedback = 'You have a strong understanding of token concepts!';
    } else if (percentage >= 70) {
      grade = 'Good Job!';
      gradeColor = '#10b981';
      feedback = 'You understand the key differences between FT and NFT.';
    } else if (percentage >= 50) {
      grade = 'Pass';
      gradeColor = '#fbbf24';
      feedback = 'Review the sections you struggled with and try again.';
    } else {
      grade = 'Keep Learning';
      gradeColor = '#ef4444';
      feedback = 'Re-read the material and practice with the visualizers.';
    }
    
    return (
      <div>
        <h3 style={{ color: '#3b82f6', marginBottom: '1.5rem', textAlign: 'center' }}>
          Lab Complete!
        </h3>
        <VideoEmbed url={SECTIONS[5].video} title="Token Concepts Summary" />
        
        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
          borderRadius: '0.75rem',
          padding: '2rem',
          textAlign: 'center',
          marginBottom: '1.5rem'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '0.5rem' }}>
            {percentage >= 70 ? '🎉' : percentage >= 50 ? '👍' : '📚'}
          </div>
          
          <div style={{ color: gradeColor, fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            {grade}
          </div>
          
          <div style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
            {feedback}
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '1rem'
          }}>
            <div style={{
              background: 'rgba(0,0,0,0.2)',
              borderRadius: '0.5rem',
              padding: '1rem'
            }}>
              <div style={{ color: '#fbbf24', fontSize: '1.5rem', fontWeight: 'bold' }}>
                {score}/{maxScore}
              </div>
              <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Points Earned</div>
            </div>
            
            <div style={{
              background: 'rgba(0,0,0,0.2)',
              borderRadius: '0.5rem',
              padding: '1rem'
            }}>
              <div style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 'bold' }}>
                {correctCount}/{totalQuestions}
              </div>
              <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Correct Answers</div>
            </div>
            
            <div style={{
              background: 'rgba(0,0,0,0.2)',
              borderRadius: '0.5rem',
              padding: '1rem'
            }}>
              <div style={{ color: gradeColor, fontSize: '1.5rem', fontWeight: 'bold' }}>
                {percentage}%
              </div>
              <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Score</div>
            </div>
          </div>
        </div>
        
        <div style={{
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          marginBottom: '1.5rem'
        }}>
          <h4 style={{ color: '#10b981', marginTop: 0, marginBottom: '1rem' }}>Key Takeaways</h4>
          <ul style={{ color: '#cbd5e1', margin: 0, paddingLeft: '1.5rem', lineHeight: 1.8 }}>
            <li><strong style={{ color: '#10b981' }}>Fungible tokens</strong> are interchangeable (like money)</li>
            <li><strong style={{ color: '#8b5cf6' }}>Non-fungible tokens</strong> are unique (like property deeds)</li>
            <li>FTs track <strong>balances</strong> per address</li>
            <li>NFTs track <strong>ownership</strong> of unique items by ID</li>
            <li>Both live on the blockchain and can be transferred</li>
          </ul>
        </div>
        
        <div style={{
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '0.75rem',
          padding: '1.5rem'
        }}>
          <h4 style={{ color: '#93c5fd', marginTop: 0, marginBottom: '1rem' }}>Real-World Examples</h4>
          <p style={{ color: '#cbd5e1', margin: 0 }}>
            <strong style={{ color: '#10b981' }}>Fungible Tokens:</strong> USDC, Bitcoin, loyalty points, game currencies<br/>
            <strong style={{ color: '#8b5cf6' }}>Non-Fungible Tokens:</strong> CryptoKitties, ENS domains, digital art, POAPs
          </p>
        </div>
        
        {onComplete && (
          <button
            onClick={onComplete}
            style={{
              width: '100%',
              marginTop: '2rem',
              padding: '1rem',
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              color: '#fff',
              border: 'none',
              borderRadius: '0.5rem',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            Continue Learning
          </button>
        )}
      </div>
    );
  };

  const renderCurrentSection = () => {
    switch (currentSection) {
      case 1: return renderSection1();
      case 2: return renderSection2();
      case 3: return renderSection3();
      case 4: return renderSection4();
      case 5: return renderSection5();
      case 6: return renderSection6();
      default: return null;
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
        borderRadius: '0.75rem',
        padding: '1.5rem',
        marginBottom: '1.5rem',
        textAlign: 'center'
      }}>
        <h2 style={{ color: '#fff', margin: 0, marginBottom: '0.5rem' }}>
          Token Concepts: FT vs NFT
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.8)', margin: 0 }}>
          Learn the difference between Fungible and Non-Fungible Tokens
        </p>
      </div>
      
      {/* Progress Bar */}
      {(() => {
        const totalQuestions = 13 + CATEGORIZATION_ITEMS.length;
        const totalAnswered = Object.keys(answeredQuestions).length + Object.keys(categorizationAnswers).length;
        return (
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '0.5rem 1rem',
            marginBottom: '1rem'
          }}>
            <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Section <strong style={{ color: '#f8fafc' }}>{currentSection}</strong> of {SECTIONS.length}
            </span>
            <div style={{
              flex: 1,
              minWidth: '120px',
              height: '8px',
              background: '#334155',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${(currentSection / SECTIONS.length) * 100}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%)',
                transition: 'width 0.3s'
              }} />
            </div>
            <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Questions: <strong style={{ color: '#10b981' }}>{totalAnswered}</strong>/{totalQuestions}
            </span>
            <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Score: <strong style={{ color: '#fbbf24' }}>{score}</strong>
            </span>
          </div>
        );
      })()}
      
      {/* Section Navigation */}
      <div
        role="tablist"
        aria-label="Lab sections"
        style={{
          display: 'flex',
          gap: '0.5rem',
          marginBottom: '1.5rem',
          overflowX: 'auto',
          paddingBottom: '0.5rem'
        }}
      >
        {SECTIONS.map(section => (
          <button
            key={section.id}
            role="tab"
            aria-selected={currentSection === section.id}
            aria-current={currentSection === section.id ? 'step' : undefined}
            onClick={() => setCurrentSection(section.id)}
            style={{
              padding: '0.5rem 1rem',
              background: currentSection === section.id
                ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
                : '#334155',
              color: '#fff',
              border: 'none',
              borderRadius: '0.375rem',
              fontSize: '0.85rem',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.2s'
            }}
          >
            {section.id}. {section.title}
          </button>
        ))}
      </div>
      
      {/* Content */}
      <div style={{
        background: '#1e293b',
        borderRadius: '0.75rem',
        padding: '1.5rem',
        minHeight: '400px'
      }}>
        {renderCurrentSection()}
      </div>
      
      {/* Navigation Buttons */}
      {(() => {
        const totalAnswered = Object.keys(answeredQuestions).length + Object.keys(categorizationAnswers).length;
        const canViewResults = totalAnswered > 0;
        const nextDisabled = currentSection === SECTIONS.length || (currentSection === SECTIONS.length - 1 && !canViewResults);
        const onSummary = currentSection === SECTIONS.length;
        return (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '1rem',
              gap: '1rem'
            }}
            role="navigation"
            aria-label="Lab section navigation"
          >
            <button
              onClick={() => setCurrentSection(prev => Math.max(1, prev - 1))}
              disabled={currentSection === 1}
              aria-label={currentSection === 1 ? 'Previous section (disabled)' : 'Go to previous section'}
              style={{
                padding: '0.75rem 1.5rem',
                background: currentSection === 1 ? '#475569' : '#334155',
                color: currentSection === 1 ? '#64748b' : '#f8fafc',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: currentSection === 1 ? 'not-allowed' : 'pointer'
              }}
            >
              Previous
            </button>
            {currentSection === SECTIONS.length - 1 && !canViewResults && (
              <span style={{ color: '#fbbf24', fontSize: '0.85rem' }} role="status">
                Answer at least one question to view results
              </span>
            )}
            {!onSummary && (
              <button
                onClick={() => setCurrentSection(prev => Math.min(SECTIONS.length, prev + 1))}
                disabled={nextDisabled}
                aria-label={nextDisabled ? 'Next section (disabled)' : currentSection === SECTIONS.length - 1 ? 'View results' : 'Go to next section'}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: nextDisabled ? '#475569' : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                  color: nextDisabled ? '#64748b' : '#fff',
                  border: 'none',
                  borderRadius: '0.375rem',
                  cursor: nextDisabled ? 'not-allowed' : 'pointer'
                }}
              >
                {currentSection === SECTIONS.length - 1 ? 'View Results' : 'Next'}
              </button>
            )}
          </div>
        );
      })()}
    </div>
  );
}

export default TokenConceptsView;
