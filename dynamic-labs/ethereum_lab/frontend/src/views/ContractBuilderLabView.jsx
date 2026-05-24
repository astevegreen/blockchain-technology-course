/**
 * ContractBuilderLabView - Step-through lab: build, deploy, share, interact with another student.
 * Step 1: Edit any Solidity contract in editor (SimpleStorage pre-filled), Save writes it to contracts/ and prompts compile.
 * Steps 2+: Prerequisites, Deploy, Share, Interact, Verify — all adapt to the detected contract name.
 */
import { useState, useMemo, useEffect } from 'react';
import InlineTerminal from '../components/InlineTerminal';
import { ChainSearch } from '../components/ChainSearch';

const DEFAULT_SIMPLE_STORAGE = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleStorage {
    uint256 private storedValue;
    address public owner;
    
    event ValueChanged(uint256 oldValue, uint256 newValue, address changedBy);
    
    constructor() {
        owner = msg.sender;
    }
    
    function set(uint256 _value) public {
        uint256 oldValue = storedValue;
        storedValue = _value;
        emit ValueChanged(oldValue, _value, msg.sender);
    }
    
    function get() public view returns (uint256) {
        return storedValue;
    }
}
`;

const STEPS = [
  {
    id: 1,
    title: 'Write Your Contract',
    isEditorStep: true,
  },
  {
    id: 2,
    title: 'Prerequisites',
  },
  {
    id: 3,
    title: 'Deploy',
  },
  {
    id: 4,
    title: 'Share',
  },
  {
    id: 5,
    title: 'Interact (Partner)',
    isEditableCode: true,
  },
  {
    id: 6,
    title: 'Verify',
    isEditableCode: true,
  },
];

function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <div style={{ position: 'relative', marginTop: '0.75rem' }}>
      <pre
        style={{
          margin: 0,
          padding: '1rem',
          background: '#0c0c0c',
          border: '1px solid #334155',
          borderRadius: '0.5rem',
          color: '#86efac',
          fontSize: '0.85rem',
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}
      >
        {code}
      </pre>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <button
          type="button"
          onClick={copy}
          style={{
            padding: '0.35rem 0.75rem',
            background: '#334155',
            border: 'none',
            borderRadius: '0.35rem',
            color: '#94a3b8',
            fontSize: '0.8rem',
            cursor: 'pointer',
          }}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
    </div>
  );
}

const codeTextareaStyle = {
  width: '100%',
  minHeight: '180px',
  padding: '1rem',
  background: '#0c0c0c',
  border: '1px solid #334155',
  borderRadius: '0.5rem',
  color: '#86efac',
  fontSize: '0.85rem',
  fontFamily: '"Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", monospace',
  resize: 'vertical',
  lineHeight: 1.5,
};

function buildSaveScript(contractCode, contractName) {
  const filename = `contracts/${contractName}.sol`;
  const base64 = btoa(unescape(encodeURIComponent(contractCode)));
  return `node -e "require('fs').writeFileSync('${filename}', Buffer.from('${base64}','base64').toString()); console.log('Saved to ${filename}');"`;
}

function makeDeployCode(contractName) {
  return `// Deploy — paste this into Hardhat console
const contract = await ethers.deployContract("contracts/${contractName}.sol:${contractName}");
await contract.waitForDeployment();
const addr = await contract.getAddress();
console.log("Deployed to:", addr);
console.log("Share this address with your partner!");`;
}

function parseFunctions(solidityCode) {
  const fns = [];
  const re = /function\s+(\w+)\s*\(([^)]*)\)[^{]*?(public|external)[^{]*?(view|pure)?[^{]*?(returns\s*\(([^)]*)\))?/g;
  let m;
  while ((m = re.exec(solidityCode)) !== null) {
    const name = m[1];
    const rawParams = m[2].trim();
    const isView = !!m[4];
    const returnType = (m[6] || '').trim();
    const params = rawParams ? rawParams.split(',').map(p => {
      const parts = p.trim().split(/\s+/);
      const type = parts[0];
      const pName = parts[parts.length - 1];
      return { type, name: pName };
    }) : [];
    fns.push({ name, params, isView, returnType });
  }
  return fns;
}

function exampleArg(type) {
  if (type.startsWith('uint') || type.startsWith('int')) return '1';
  if (type === 'string') return '"hello"';
  if (type === 'address') return '"0x0000000000000000000000000000000000000001"';
  if (type === 'bool') return 'true';
  if (type.startsWith('bytes')) return '"0x00"';
  return '0';
}

function makeInteractDefault(contractName, addr, solidityCode) {
  const fqn = `contracts/${contractName}.sol:${contractName}`;
  const fns = parseFunctions(solidityCode || '');
  const views = fns.filter(f => f.isView);
  const writes = fns.filter(f => !f.isView);

  if (fns.length === 0) {
    return `// Interact with contract
const addr = '${addr || '0x...'}';
const c = await ethers.getContractAt("${fqn}", addr);
// Edit: call your contract's functions
// e.g. await c.someFunction(arg);`;
  }

  let lines = [`// Interact with contract`, `const addr = '${addr || '0x...'}';`, `const c = await ethers.getContractAt("${fqn}", addr);`];

  if (writes.length > 0) {
    const w = writes[0];
    const args = w.params.map(p => exampleArg(p.type)).join(', ');
    lines.push(``, `// Write: ${w.name}`);
    lines.push(`await c.${w.name}(${args});`);
    lines.push(`console.log("${w.name} called successfully");`);
  }

  if (views.length > 0) {
    const v = views[0];
    const args = v.params.map(p => exampleArg(p.type)).join(', ');
    lines.push(``, `// Read: ${v.name}`);
    lines.push(`const result = await c.${v.name}(${args});`);
    lines.push(`console.log("${v.name}:", result.toString());`);
  }

  if (views.length > 1 || writes.length > 1) {
    lines.push(``, `// Other available functions:`);
    for (const f of fns.slice(0, 8)) {
      const args = f.params.map(p => `${p.name}`).join(', ');
      lines.push(`// ${f.isView ? '(view)' : '(write)'} c.${f.name}(${args})`);
    }
  }

  return lines.join('\n');
}

function makeVerifyDefault(contractName, addr, solidityCode) {
  const fqn = `contracts/${contractName}.sol:${contractName}`;
  const fns = parseFunctions(solidityCode || '');
  const views = fns.filter(f => f.isView);

  if (views.length === 0) {
    return `// Quick verify
const addr = '${addr || '0x...'}';
const c = await ethers.getContractAt("${fqn}", addr);
// Edit: call a read function to verify state
// e.g. console.log(await c.someView());`;
  }

  let lines = [`// Quick verify`, `const addr = '${addr || '0x...'}';`, `const c = await ethers.getContractAt("${fqn}", addr);`];

  for (const v of views.slice(0, 4)) {
    const args = v.params.map(p => exampleArg(p.type)).join(', ');
    lines.push(`console.log("${v.name}:", (await c.${v.name}(${args})).toString());`);
  }

  return lines.join('\n');
}

const CONTRACT_BEACON_IDS = {
  1: 'eth-contract-write',
  2: 'eth-contract-prereqs',
  3: 'eth-contract-deploy',
  4: 'eth-contract-share',
  5: 'eth-contract-interact',
  6: 'eth-contract-verify',
};

export function ContractBuilderLabView({ provider, wallet, rpcUrl, terminalRpcUrl = '', onLoadCode, onExpandTerminal, fireProgressBeacon }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [loadCode, setLoadCode] = useState('');
  const [loadFeedback, setLoadFeedback] = useState('');
  const [contractCode, setContractCode] = useState(DEFAULT_SIMPLE_STORAGE);
  const [step1Saved, setStep1Saved] = useState(false);
  const [contractAddress, setContractAddress] = useState('');
  const [interactCode, setInteractCode] = useState('');
  const [verifyCode, setVerifyCode] = useState('');
  const [interactEdited, setInteractEdited] = useState(false);
  const [verifyEdited, setVerifyEdited] = useState(false);

  const contractName = useMemo(() => {
    const match = contractCode.match(/contract\s+(\w+)/);
    return match?.[1] || 'SimpleStorage';
  }, [contractCode]);

  const deployCode = useMemo(() => makeDeployCode(contractName), [contractName]);

  useEffect(() => {
    if (!interactEdited) {
      setInteractCode(makeInteractDefault(contractName, contractAddress, contractCode));
    }
  }, [contractName, contractAddress, interactEdited, contractCode]);

  useEffect(() => {
    if (!verifyEdited) {
      setVerifyCode(makeVerifyDefault(contractName, contractAddress, contractCode));
    }
  }, [contractName, contractAddress, verifyEdited, contractCode]);

  useEffect(() => {
    if (fireProgressBeacon) fireProgressBeacon(CONTRACT_BEACON_IDS[currentStep]);
  }, [currentStep]);

  const step = STEPS.find((s) => s.id === currentStep);

  const handleLoadCode = (code) => {
    setLoadCode(code);
    onLoadCode?.(code);
    onExpandTerminal?.();
    setTerminalOpen(true);
    setLoadFeedback('Code loaded into the terminal. Scroll down to the Lab Terminal to run it.');
    setTimeout(() => setLoadFeedback(''), 5000);
    setTimeout(() => {
      document.querySelector('[data-lab-terminal]')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
  };

  const handleStep1Save = () => {
    const saveScript = buildSaveScript(contractCode, contractName);
    handleLoadCode(saveScript);
    setStep1Saved(true);
    setLoadFeedback(`Save script loaded! Run it in the terminal to write contracts/${contractName}.sol.`);
    setTimeout(() => setLoadFeedback(''), 6000);
  };

  const resetInteract = () => {
    setInteractCode(makeInteractDefault(contractName, contractAddress, contractCode));
    setInteractEdited(false);
  };

  const resetVerify = () => {
    setVerifyCode(makeVerifyDefault(contractName, contractAddress, contractCode));
    setVerifyEdited(false);
  };

  const renderStep = () => {
    if (step.isEditorStep) {
      return (
        <>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Edit the contract below. SimpleStorage is pre-filled as a starting point — you can customize it or replace it entirely with your own contract. Hit <strong>Save</strong> to write it to disk and see compile steps; deploy is in Step 3.
          </p>
          <div style={{ marginTop: '0.5rem', padding: '0.5rem 0.75rem', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '0.35rem', fontSize: '0.8rem', color: '#93c5fd' }}>
            Detected contract name: <strong style={{ color: '#e2e8f0' }}>{contractName}</strong> — this is used for the filename, deploy, and interact scripts.
          </div>
          <div style={{ marginTop: '0.75rem' }}>
            <textarea
              value={contractCode}
              onChange={(e) => setContractCode(e.target.value)}
              spellCheck={false}
              style={{
                width: '100%',
                minHeight: '280px',
                padding: '1rem',
                background: '#0c0c0c',
                border: '1px solid #334155',
                borderRadius: '0.5rem',
                color: '#86efac',
                fontSize: '0.85rem',
                fontFamily: '"Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", monospace',
                resize: 'vertical',
                lineHeight: 1.5,
              }}
            />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
            <button
              type="button"
              onClick={handleStep1Save}
              style={{
                padding: '0.5rem 1.25rem',
                background: 'var(--primary)',
                border: 'none',
                borderRadius: '0.5rem',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => {
                navigator.clipboard?.writeText(contractCode);
                setLoadFeedback('Contract code copied to clipboard');
                setTimeout(() => setLoadFeedback(''), 2000);
              }}
              style={{
                padding: '0.5rem 1rem',
                background: '#334155',
                border: 'none',
                borderRadius: '0.5rem',
                color: '#94a3b8',
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              Copy code
            </button>
          </div>
          {step1Saved && (
            <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid #334155' }}>
              <div style={{ fontSize: '0.9rem', color: '#86efac', marginBottom: '0.5rem', fontWeight: 600 }}>
                Save and compile
              </div>
              <ol style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.75rem', lineHeight: 1.7, paddingLeft: '1.25rem' }}>
                <li>Run the save script in the Lab Terminal (it was loaded) to write <code>contracts/{contractName}.sol</code>.</li>
                <li>Compile in the <strong>shell</strong> (project root): <code style={{ background: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>npx hardhat compile</code></li>
              </ol>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.6, marginBottom: '0.5rem' }}>
                Click <strong>Next</strong> for Step 2 (Prerequisites), then Step 3 (Deploy) — that step has the deploy snippet for the Hardhat console.
              </p>
            </div>
          )}
        </>
      );
    }

    if (step.id === 2) {
      return (
        <>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Ensure the chain is running, RPC URL is set in Connection Setup, and your wallet is connected. You need ETH to deploy.
          </p>
          <div style={{ marginTop: '0.75rem', padding: '0.75rem 1rem', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '0.5rem', fontSize: '0.85rem', color: '#93c5fd', lineHeight: 1.7 }}>
            <strong style={{ color: '#e2e8f0' }}>In the Lab Terminal:</strong>
            <ol style={{ margin: '0.35rem 0 0 1rem', padding: 0 }}>
              <li>Start Hardhat console: <code>npx hardhat console --network localhost</code> (or <code>--network instructor</code> for remote RPC)</li>
              <li>Paste the verify script below to check your address and balance.</li>
              <li>Type <code>.exit</code> to return to the shell when done.</li>
            </ol>
          </div>
          <CodeBlock code={`// Verify connection (paste into Hardhat console)
const [signer] = await ethers.getSigners();
const bal = await ethers.provider.getBalance(signer.address);
console.log('Address:', signer.address);
console.log('Balance:', ethers.formatEther(bal), 'ETH');`} />
        </>
      );
    }

    if (step.id === 3) {
      return (
        <>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Deploy your <strong>{contractName}</strong> contract using the Hardhat console (no .js script needed).
          </p>
          <p style={{ color: '#64748b', fontSize: '0.8rem', lineHeight: 1.6, marginTop: '0.35rem' }}>
            Paste the deploy snippet below <strong>once</strong> per console session. If you already ran it and only need the address again, use the existing <code style={{ background: '#1e293b', padding: '0.1rem 0.3rem', borderRadius: '0.2rem' }}>addr</code> variable, or type <code style={{ background: '#1e293b', padding: '0.1rem 0.3rem', borderRadius: '0.2rem' }}>.exit</code> and start a fresh console before pasting again.
          </p>
          <div style={{ marginTop: '0.75rem', padding: '0.75rem 1rem', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '0.5rem', fontSize: '0.85rem', color: '#93c5fd', lineHeight: 1.7 }}>
            <strong style={{ color: '#e2e8f0' }}>In the Lab Terminal (shell at project root):</strong>
            <ol style={{ margin: '0.35rem 0 0 1rem', padding: 0 }}>
              <li>Compile: <code style={{ background: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>npx hardhat compile</code></li>
              <li>Start Hardhat console: <code style={{ background: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>npx hardhat console --network localhost</code> (or <code style={{ background: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>--network instructor</code> for remote RPC)</li>
              <li>Paste the deploy code below.</li>
              <li>Copy the deployed address. Type <code>.exit</code> to return to the shell.</li>
            </ol>
          </div>
          <CodeBlock code={deployCode} />
        </>
      );
    }

    if (step.id === 4) {
      return (
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
          Share your contract address with your partner. Post it in Class Chat, or send it another way. Your partner needs this address to interact with your <strong>{contractName}</strong> contract.
        </p>
      );
    }

    if (step.id === 5) {
      return (
        <>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
            As the partner: paste the contract address your partner shared (from Step 4) below, then edit the script to call the right functions for the contract you&apos;re interacting with. Copy the script and paste it into Hardhat console.
          </p>
          <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '0.35rem', fontSize: '0.8rem', color: '#93c5fd' }}>
            Start the Hardhat console if not already in it: <code>npx hardhat console --network localhost</code> (or <code>--network instructor</code> for remote)
          </div>
          <div style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>
              Contract address (from your partner)
            </label>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.35rem' }}>
              Your partner shares this from Step 4 (Share). Paste the address they deployed in Step 3.
            </div>
            <input
              type="text"
              value={contractAddress}
              onChange={(e) => setContractAddress(e.target.value)}
              placeholder="0x..."
              style={{
                width: '100%',
                maxWidth: '420px',
                padding: '0.5rem 0.75rem',
                background: '#0c0c0c',
                border: '1px solid #334155',
                borderRadius: '0.35rem',
                color: '#e2e8f0',
                fontSize: '0.9rem',
                fontFamily: 'monospace',
              }}
            />
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.35rem' }}>
            Edit the script below to match your contract&apos;s functions. The template uses <strong>{contractName}</strong> — change it if interacting with a different contract.
          </div>
          <textarea
            value={interactCode}
            onChange={(e) => { setInteractCode(e.target.value); setInteractEdited(true); }}
            spellCheck={false}
            style={codeTextareaStyle}
          />
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              onClick={() => {
                navigator.clipboard?.writeText(interactCode);
                setLoadFeedback('Interact script copied!');
                setTimeout(() => setLoadFeedback(''), 2000);
              }}
              style={{ padding: '0.35rem 0.75rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', fontSize: '0.8rem', cursor: 'pointer' }}
            >
              Copy
            </button>
            {interactEdited && (
              <button
                type="button"
                onClick={resetInteract}
                style={{ padding: '0.35rem 0.75rem', background: '#475569', border: 'none', borderRadius: '0.35rem', color: '#e2e8f0', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                Reset to default
              </button>
            )}
          </div>
        </>
      );
    }

    if (step.id === 6) {
      return (
        <>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Use Search Chain (below) to look up the contract by address. Or paste the address below, edit the verify script, and run it in Hardhat console.
          </p>
          <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '0.35rem', fontSize: '0.8rem', color: '#93c5fd' }}>
            Start the Hardhat console if not already in it: <code>npx hardhat console --network localhost</code> (or <code>--network instructor</code> for remote)
          </div>
          <div style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem' }}>
              Contract address (from Step 4 — shared by deployer)
            </label>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.35rem' }}>
              The address of the deployed contract. Use Search Chain, or paste the address your partner shared.
            </div>
            <input
              type="text"
              value={contractAddress}
              onChange={(e) => setContractAddress(e.target.value)}
              placeholder="0x..."
              style={{
                width: '100%',
                maxWidth: '420px',
                padding: '0.5rem 0.75rem',
                background: '#0c0c0c',
                border: '1px solid #334155',
                borderRadius: '0.35rem',
                color: '#e2e8f0',
                fontSize: '0.9rem',
                fontFamily: 'monospace',
              }}
            />
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.35rem' }}>
            Edit the script below to call the right read function for your contract.
          </div>
          <textarea
            value={verifyCode}
            onChange={(e) => { setVerifyCode(e.target.value); setVerifyEdited(true); }}
            spellCheck={false}
            style={{ ...codeTextareaStyle, minHeight: '120px' }}
          />
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              onClick={() => {
                navigator.clipboard?.writeText(verifyCode);
                setLoadFeedback('Verify script copied!');
                setTimeout(() => setLoadFeedback(''), 2000);
              }}
              style={{ padding: '0.35rem 0.75rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', fontSize: '0.8rem', cursor: 'pointer' }}
            >
              Copy
            </button>
            {verifyEdited && (
              <button
                type="button"
                onClick={resetVerify}
                style={{ padding: '0.35rem 0.75rem', background: '#475569', border: 'none', borderRadius: '0.35rem', color: '#e2e8f0', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                Reset to default
              </button>
            )}
          </div>
        </>
      );
    }

    return null;
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem' }}>
      <h1 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Contract Builder Lab</h1>
      {!provider && (
        <div style={{ padding: '1rem', background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.4)', borderRadius: '0.5rem', color: '#fde047', marginBottom: '1rem' }}>
          Connect to the chain first: go to <strong>Live</strong> tab, set RPC URL, and connect your wallet.
        </div>
      )}
      <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
        Build any smart contract, deploy it to the chain, and interact with another student. SimpleStorage is pre-filled as a starting point — replace it with your own contract if you like.
      </p>

      <a
        href="/docs/guides/CHAIN_INTERACTION_GUIDE.md"
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: 'var(--primary)', fontSize: '0.9rem', marginBottom: '1rem', display: 'inline-block' }}
      >
        Read: How to interact with the chain via code
      </a>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {STEPS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setCurrentStep(s.id)}
            style={{
              padding: '0.4rem 0.8rem',
              background: currentStep === s.id ? 'var(--primary)' : '#334155',
              color: '#fff',
              border: 'none',
              borderRadius: '0.5rem',
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            {s.id}. {s.title}
          </button>
        ))}
      </div>

      <div
        style={{
          padding: '1.5rem',
          background: 'var(--card)',
          borderRadius: '0.75rem',
          border: '1px solid #475569',
          marginBottom: '1.5rem',
        }}
      >
        <h2 style={{ color: '#e2e8f0', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
          Step {step.id}: {step.title}
        </h2>
        {renderStep()}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          type="button"
          onClick={() => setCurrentStep((p) => Math.max(1, p - 1))}
          disabled={currentStep <= 1}
          style={{
            padding: '0.5rem 1rem',
            background: currentStep <= 1 ? '#334155' : '#475569',
            color: '#fff',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: currentStep <= 1 ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem',
          }}
        >
          Previous
        </button>
        <button
          type="button"
          onClick={() => setCurrentStep((p) => Math.min(STEPS.length, p + 1))}
          disabled={currentStep >= STEPS.length}
          style={{
            padding: '0.5rem 1rem',
            background: currentStep >= STEPS.length ? '#334155' : 'var(--primary)',
            color: '#fff',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: currentStep >= STEPS.length ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem',
          }}
        >
          Next
        </button>
      </div>

      <ChainSearch provider={provider} rpcUrl={rpcUrl} />

      {loadFeedback && (
        <div style={{ padding: '0.75rem 1rem', background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.4)', borderRadius: '0.5rem', color: '#86efac', marginBottom: '1rem', fontSize: '0.9rem' }}>
          {loadFeedback}
        </div>
      )}

      <div style={{ marginTop: '1.5rem' }} data-lab-terminal>
        <div style={{
          padding: '1rem',
          background: 'rgba(59,130,246,0.1)',
          border: '1px solid rgba(59,130,246,0.3)',
          borderRadius: '0.5rem',
          marginBottom: '0.75rem',
          fontSize: '0.9rem',
          color: '#93c5fd',
        }}>
          <strong style={{ color: '#e2e8f0' }}>Lab Terminal instructions</strong>
          <p style={{ margin: '0.5rem 0 0.35rem 0', color: '#cbd5e1', fontSize: '0.85rem' }}>
            <strong>Easiest way:</strong> Click the <strong>Start Hardhat</strong> button in the terminal status bar to enter the Hardhat console (no typing required).
          </p>
          <ul style={{ margin: '0.5rem 0 0 1.25rem', padding: 0, lineHeight: 1.7 }}>
            <li>If you&apos;re new to the terminal: type a command and press <strong>Enter</strong>. The prompt changes to <code>&gt;</code> when you&apos;re in Hardhat. Paste scripts there, then type <code>.exit</code> to leave.</li>
            <li><strong>Directory:</strong> The terminal starts in the <strong>project root</strong> (where <code>package.json</code>, <code>contracts/</code>, and <code>scripts/</code> live). No need to <code>cd</code>.</li>
            <li><strong>Compile:</strong> <code style={{ background: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>npx hardhat compile</code> — run this in the shell before deploying.</li>
            <li><strong>Enter Hardhat console (local):</strong> <code style={{ background: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>npx hardhat console --network localhost</code></li>
            <li><strong>Enter Hardhat console (remote):</strong> <code style={{ background: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>npx hardhat console --network instructor</code></li>
            <li><strong>Exit Hardhat console:</strong> Type <code>.exit</code> or press <code>Ctrl+C</code> twice to return to the shell.</li>
          </ul>
          <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.25)', borderRadius: '0.375rem' }}>
            <strong style={{ color: '#fde047', fontSize: '0.85rem' }}>Connecting to a remote / instructor-hosted RPC</strong>
            <p style={{ color: '#cbd5e1', fontSize: '0.85rem', margin: '0.4rem 0 0.4rem 0', lineHeight: 1.6 }}>
              If the blockchain is running on a different machine or behind a shared reverse proxy, set the <code style={{ background: '#1e293b', padding: '0.1rem 0.3rem', borderRadius: '0.2rem' }}>RPC_URL</code> environment variable before starting the Hardhat console:
            </p>
            <div style={{ background: '#0f172a', padding: '0.5rem 0.75rem', borderRadius: '0.35rem', fontFamily: 'monospace', fontSize: '0.8rem', color: '#e2e8f0', lineHeight: 1.6, overflowX: 'auto' }}>
              <div style={{ color: '#64748b' }}># Windows (PowerShell)</div>
              <div>$env:RPC_URL=&quot;http://INSTRUCTOR_IP:8545&quot;</div>
              <div>npx hardhat console --network instructor</div>
              <div style={{ marginTop: '0.5rem', color: '#64748b' }}># Mac / Linux</div>
              <div>RPC_URL=&quot;http://INSTRUCTOR_IP:8545&quot; npx hardhat console --network instructor</div>
              <div style={{ marginTop: '0.5rem', color: '#64748b' }}># If the instructor shares a proxied lab URL</div>
              <div>RPC_URL=&quot;http://INSTRUCTOR_HOST:8081/labs/ethereum_lab/rpc&quot; npx hardhat console --network instructor</div>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.8rem', margin: '0.4rem 0 0 0', lineHeight: 1.5 }}>
              Replace <code style={{ fontSize: '0.8rem' }}>INSTRUCTOR_IP</code> with the actual IP address or hostname provided by your instructor. The <code style={{ fontSize: '0.8rem' }}>instructor</code> network in <code style={{ fontSize: '0.8rem' }}>hardhat.config.js</code> reads from this variable automatically.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setTerminalOpen(!terminalOpen)}
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '0.75rem 1rem',
            background: '#1a1a2e',
            border: '1px solid #1e293b',
            borderRadius: terminalOpen ? '0.75rem 0.75rem 0 0' : '0.75rem',
            color: '#f8fafc',
            fontSize: '1.1rem',
            cursor: 'pointer',
          }}
        >
          <span>Lab Terminal</span>
          <span>{terminalOpen ? '▼' : '▶'}</span>
        </button>
        {terminalOpen && (
          <div style={{ border: '1px solid #1e293b', borderTop: 'none', borderRadius: '0 0 0.75rem 0.75rem', overflow: 'hidden' }}>
            <InlineTerminal
              loadCode={loadCode}
              onLoadCodeConsumed={() => setLoadCode('')}
              rpcUrl={rpcUrl}
              terminalRpcUrl={terminalRpcUrl}
              autoStartHardhat={false}
            />
          </div>
        )}
      </div>
    </div>
  );
}
