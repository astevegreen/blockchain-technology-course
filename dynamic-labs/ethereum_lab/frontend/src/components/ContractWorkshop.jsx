// GUI smart-contract workflow: pick/edit a contract, compile (backend solc),
// deploy from the student's wallet, and interact via auto-generated forms — no
// terminal/Hardhat. Deployed contracts are shared via lab-api so any student on
// the network can open and interact with them.
import { useState, useEffect, useCallback, useMemo } from 'react';
import { ethers } from 'ethers';
import { registerSource } from '../lib/contractSources';
import { registerKnownContract } from '../lib/abiRegistry';
import { fetchSessionState, patchSessionNamespace } from '../lib/sessionState';
import { InteractPanel, coerceArg, describeError } from './InteractPanel';

const API = (import.meta.env.BASE_URL || '/') + 'lab-api/';
const chainContractUrls = () => {
  const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
  return [`${base}/chain-state?contracts=1`, `${base}/lab-api/chain/state?contracts=1`, `${base}/lab-api/chain/contracts`];
};
const contractRegistrationUrls = () => {
  const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
  return [`${base}/chain-state`, `${base}/lab-api/contracts`];
};

async function fetchChainContracts() {
  for (const url of chainContractUrls()) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) continue;
      const j = await r.json();
      const scan = j?.smartContracts || j;
      if (scan && Array.isArray(scan.contracts)) return scan;
    } catch { /* try next route */ }
  }
  return null;
}

async function registerDeployedContract(contract) {
  for (const url of contractRegistrationUrls()) {
    try {
      const body = url.endsWith('/chain-state')
        ? { kind: 'register-contract', registerContract: contract }
        : contract;
      const r = await fetch(url, {
        method: 'POST',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (r.ok) return true;
    } catch { /* try next route */ }
  }
  return false;
}

const CATALOG = [
  {
    id: 'blank', name: '✍️ Write your own', desc: 'Start from a bare-bones contract',
    source: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// Rename MyContract and add your own state + functions, then Compile and Deploy.
contract MyContract {
    // State variable (stored on-chain):
    uint256 public myNumber;

    event NumberChanged(uint256 oldNumber, uint256 newNumber, address changedBy);

    // Write function (changes state — costs gas, use "Send"):
    function setNumber(uint256 newNumber) public {
        uint256 oldNumber = myNumber;
        myNumber = newNumber;
        emit NumberChanged(oldNumber, newNumber, msg.sender);
    }

    // Read function ("view" — free, use "Read"):
    function getNumber() public view returns (uint256) {
        return myNumber;
    }
}`,
  },
  {
    id: 'simple-storage', name: 'SimpleStorage', desc: 'Store and read a single number',
    source: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleStorage {
    uint256 public value;

    event ValueChanged(uint256 oldValue, uint256 newValue, address changedBy);

    function set(uint256 newValue) public {
        uint256 oldValue = value;
        value = newValue;
        emit ValueChanged(oldValue, newValue, msg.sender);
    }

    function get() public view returns (uint256) {
        return value;
    }
}`,
  },
  {
    id: 'counter', name: 'Counter', desc: 'Increment / decrement a counter',
    source: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Counter {
    int256 public count;

    event CountChanged(int256 oldCount, int256 newCount, address changedBy, string action);

    function increment() public {
        int256 oldCount = count;
        count += 1;
        emit CountChanged(oldCount, count, msg.sender, "increment");
    }

    function decrement() public {
        int256 oldCount = count;
        count -= 1;
        emit CountChanged(oldCount, count, msg.sender, "decrement");
    }

    function reset() public {
        int256 oldCount = count;
        count = 0;
        emit CountChanged(oldCount, count, msg.sender, "reset");
    }
}`,
  },
  {
    id: 'greeter', name: 'Greeter', desc: 'Set and read a greeting string',
    source: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Greeter {
    string public greeting = "Hello, class!";

    event GreetingChanged(string oldGreeting, string newGreeting, address changedBy);

    function setGreeting(string memory g) public {
        string memory oldGreeting = greeting;
        greeting = g;
        emit GreetingChanged(oldGreeting, g, msg.sender);
    }
}`,
  },
  {
    id: 'tip-jar', name: 'TipJar', desc: 'Accept ETH tips; owner withdraws',
    source: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract TipJar {
    address public owner;
    uint256 public totalTips;

    constructor() { owner = msg.sender; }

    event Tipped(address from, uint256 amount, uint256 totalTips);
    event Withdrawn(address owner, uint256 amount);

    function tip() public payable {
        totalTips += msg.value;
        emit Tipped(msg.sender, msg.value, totalTips);
    }

    function balance() public view returns (uint256) {
        return address(this).balance;
    }

    function withdraw() public {
        require(msg.sender == owner, "only owner");
        uint256 amount = address(this).balance;
        payable(owner).transfer(amount);
        emit Withdrawn(owner, amount);
    }
}`,
  },
  {
    id: 'class-poll', name: 'ClassPoll', desc: 'One-vote-each yes/no poll',
    source: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ClassPoll {
    string public question;
    uint256 public yesVotes;
    uint256 public noVotes;
    mapping(address => bool) public hasVoted;

    constructor(string memory _question) { question = _question; }

    event VoteCast(address voter, bool yes, uint256 yesVotes, uint256 noVotes);

    function vote(bool yes) public {
        require(!hasVoted[msg.sender], "already voted");
        hasVoted[msg.sender] = true;
        if (yes) { yesVotes += 1; } else { noVotes += 1; }
        emit VoteCast(msg.sender, yes, yesVotes, noVotes);
    }
}`,
  },
];

const box = { background: 'var(--card)', border: '1px solid var(--border, #334155)', borderRadius: '0.6rem', padding: '1rem' };
const btn = (enabled, primary) => ({
  padding: '0.55rem 1rem', borderRadius: '0.5rem', border: 'none', fontWeight: 700, fontSize: '0.9rem',
  cursor: enabled ? 'pointer' : 'not-allowed', opacity: enabled ? 1 : 0.5,
  background: primary ? 'var(--primary, #2563eb)' : 'var(--panel, #1e293b)', color: primary ? '#fff' : 'var(--text, #e2e8f0)',
});
const inputStyle = { padding: '0.4rem 0.55rem', background: 'var(--panel, #0f172a)', border: '1px solid var(--border, #334155)', borderRadius: '0.4rem', color: 'var(--text, #e2e8f0)', fontFamily: 'monospace', fontSize: '0.82rem' };
const muted = { color: 'var(--muted, #94a3b8)' };

const short = (s) => (s ? `${String(s).slice(0, 10)}…${String(s).slice(-4)}` : '—');

const CONTRACT_TASKS = [
  { id: 'write', route: 'eth-contract-write', title: 'Choose or write a contract' },
  { id: 'compile', route: 'eth-contract-compile', title: 'Compile it successfully' },
  { id: 'deploy', route: 'eth-contract-deploy', title: 'Deploy a contract to the chain' },
  { id: 'review', route: 'eth-contract-review-class-contracts', title: 'Review class contracts on-chain' },
  { id: 'interact', route: 'eth-contract-interact', title: 'Interact with a deployed contract' },
  { id: 'peer-open', route: 'eth-contract-peer-open', title: 'Find a peer contract' },
  { id: 'peer-interact', route: 'eth-contract-peer-interact', title: 'Interact with a peer contract' },
  { id: 'event-receipt', route: 'eth-contract-event-receipt', title: 'Inspect an event in a transaction receipt' },
  { id: 'bytecode', route: 'eth-contract-bytecode', title: 'Inspect raw bytecode in Explorer' },
  { id: 'disasm', route: 'eth-contract-disasm', title: 'Inspect disassembly in Explorer' },
];

export function ContractWorkshop({ wallet, rpcUrl, fireProgressBeacon }) {
  const signer = wallet?.signer || null;
  const provider = wallet?.signer?.provider || null;

  const [templateId, setTemplateId] = useState(CATALOG[0].id);
  const [source, setSource] = useState(CATALOG[0].source);
  const [status, setStatus] = useState('');
  const [compiling, setCompiling] = useState(false);
  const [compiled, setCompiled] = useState(null); // { contractName, abi, bytecode, warnings }
  const [ctorArgs, setCtorArgs] = useState({});
  const [deploying, setDeploying] = useState(false);
  const [active, setActive] = useState(null); // { address, abi, name } currently being interacted with
  const [deployedList, setDeployedList] = useState([]);
  const [chainContracts, setChainContracts] = useState([]);
  const [chainContractsStatus, setChainContractsStatus] = useState('Click "find contracts" to load the cached class contract list.');
  const [loadingChainContracts, setLoadingChainContracts] = useState(false);
  const [taskCompleted, setTaskCompleted] = useState(() => new Set());

  useEffect(() => {
    let cancelled = false;
    fetchSessionState()
      .then((data) => {
        if (cancelled) return;
        const items = data?.state?.['contract-builder']?.taskCompleted;
        setTaskCompleted(new Set(Array.isArray(items) ? items : []));
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const ctor = useMemo(() => (compiled?.abi || []).find((x) => x.type === 'constructor'), [compiled]);
  const isPeerContract = useCallback((contract) => {
    return !!(contract?.deployer && wallet?.address && contract.deployer.toLowerCase() !== wallet.address.toLowerCase());
  }, [wallet?.address]);

  const completeTask = useCallback((taskId) => {
    const task = CONTRACT_TASKS.find((t) => t.id === taskId);
    setTaskCompleted((prev) => {
      if (prev.has(taskId)) return prev;
      const next = new Set(prev);
      next.add(taskId);
      patchSessionNamespace('contract-builder', { taskCompleted: [...next] }).catch(() => {});
      if (task?.route) fireProgressBeacon?.(task.route);
      return next;
    });
  }, [fireProgressBeacon]);

  useEffect(() => {
    const onExplorerTask = (event) => {
      if (event.detail?.kind === 'bytecode') completeTask('bytecode');
      if (event.detail?.kind === 'disasm') completeTask('disasm');
      if (event.detail?.kind === 'event-receipt') completeTask('event-receipt');
    };
    window.addEventListener('contract-builder-explorer-task', onExplorerTask);
    return () => window.removeEventListener('contract-builder-explorer-task', onExplorerTask);
  }, [completeTask]);

  const loadTemplate = (id) => {
    const t = CATALOG.find((c) => c.id === id);
    if (!t) return;
    setTemplateId(id);
    setSource(t.source);
    setCompiled(null);
    setStatus('');
    completeTask('write');
  };

  const compile = useCallback(async () => {
    setCompiling(true);
    setStatus('Compiling…');
    setCompiled(null);
    try {
      const r = await fetch(API + 'compile', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source }),
      }).then((x) => x.json());
      if (!r.ok) { setStatus('❌ ' + (r.errors || ['Compile failed']).join('\n')); return; }
      setCompiled(r);
      setStatus(`✅ Compiled ${r.contractName}` + (r.warnings?.length ? ` (${r.warnings.length} warning(s))` : ''));
      completeTask('write');
      completeTask('compile');
    } catch (e) {
      setStatus('❌ Compile request failed: ' + (e.message || e));
    } finally {
      setCompiling(false);
    }
  }, [source]);

  const deploy = useCallback(async () => {
    if (!compiled || !signer) { setStatus('❌ Compile first and connect a wallet.'); return; }
    setDeploying(true);
    setStatus('Deploying from your wallet…');
    try {
      const args = (ctor?.inputs || []).map((inp, i) => coerceArg(inp.type, ctorArgs[i] ?? ''));
      const factory = new ethers.ContractFactory(compiled.abi, compiled.bytecode, signer);
      const contract = await factory.deploy(...args);
      const deployTx = contract.deploymentTransaction?.();
      let deployReceipt = null;
      if (deployTx) deployReceipt = await deployTx.wait();
      else await contract.waitForDeployment();
      const address = await contract.getAddress();
      registerSource(address, { name: compiled.contractName, source, abi: compiled.abi });
      registerKnownContract(address, compiled.abi, compiled.contractName);
      registerDeployedContract({
        address,
        name: compiled.contractName,
        abi: compiled.abi,
        source,
        deployer: wallet?.address,
        txHash: deployTx?.hash,
        blockNumber: deployReceipt?.blockNumber,
      }).catch(() => {});
      setActive({ address, abi: compiled.abi, name: compiled.contractName, deployer: wallet?.address?.toLowerCase?.() });
      setStatus(`✅ Deployed ${compiled.contractName} to ${address}`);
      completeTask('deploy');
      loadDeployed();
    } catch (e) {
      console.warn('[ContractWorkshop] deploy error:', e);
      setStatus('❌ Deploy failed: ' + describeError(e));
    } finally {
      setDeploying(false);
    }
  }, [compiled, signer, ctor, ctorArgs, source, wallet?.address, completeTask]);

  const loadDeployed = useCallback(async () => {
    try {
      const r = await fetch(API + 'contracts').then((x) => x.json());
      const contracts = r.contracts || [];
      for (const c of contracts) registerKnownContract(c.address, c.abi, c.name);
      setDeployedList(contracts);
      if (contracts.length > 0) completeTask('review');
    } catch { /* ignore */ }
  }, [completeTask]);
  useEffect(() => { loadDeployed(); }, [loadDeployed]);

  const loadChainContracts = useCallback(async () => {
    setLoadingChainContracts(true);
    setChainContractsStatus('Searching the chain...');
    try {
      const scan = await fetchChainContracts();
      if (!scan) {
        setChainContractsStatus('Contract list is not ready yet.');
        return;
      }
      const contracts = scan.contracts || [];
      for (const c of contracts) {
        if (c.address && Array.isArray(c.abi)) registerKnownContract(c.address, c.abi, c.name);
      }
      setChainContracts(contracts);
      if (contracts.length > 0) completeTask('review');
      setChainContractsStatus(`Found ${contracts.length} contract${contracts.length === 1 ? '' : 's'} on chain.`);
    } catch (e) {
      setChainContractsStatus('Could not load contract list: ' + (e.message || String(e)));
    } finally {
      setLoadingChainContracts(false);
    }
  }, [completeTask]);
  const openContract = useCallback((contract) => {
    setActive({ address: contract.address, abi: contract.abi, name: contract.name, deployer: contract.deployer });
    completeTask('review');
    if (isPeerContract(contract)) completeTask('peer-open');
  }, [completeTask, isPeerContract]);

  const handleInteract = useCallback(() => {
    completeTask('interact');
    if (isPeerContract(active)) completeTask('peer-interact');
  }, [active, completeTask, isPeerContract]);

  const completedCount = CONTRACT_TASKS.filter((task) => taskCompleted.has(task.id)).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={box}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
          <strong>Smart Contract Lab Path</strong>
          <span style={{ ...muted, fontSize: '0.85rem' }}>{completedCount}/{CONTRACT_TASKS.length}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.45rem', marginBottom: '0.9rem' }}>
          {CONTRACT_TASKS.map((task) => {
            const done = taskCompleted.has(task.id);
            return (
              <div key={task.id} style={{ padding: '0.45rem 0.55rem', background: done ? 'rgba(34,197,94,0.12)' : 'var(--panel, #0f172a)', border: `1px solid ${done ? 'rgba(34,197,94,0.35)' : 'var(--border, #334155)'}`, borderRadius: '0.45rem', fontSize: '0.82rem', color: done ? '#86efac' : 'var(--muted, #94a3b8)' }}>
                {done ? '✓' : '☐'} {task.title}
              </div>
            );
          })}
        </div>
        <div style={{ borderTop: '1px solid var(--border, #334155)', paddingTop: '0.75rem' }}>
          <div style={{ ...muted, fontSize: '0.8rem', marginBottom: '0.45rem' }}>Contracts deployed on this chain</div>
          {deployedList.length === 0 ? (
            <div style={muted}>No contracts deployed yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {deployedList.map((c) => {
                const peer = isPeerContract(c);
                return (
                  <div key={`path-${c.address}`} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', fontSize: '0.85rem' }}>
                    <span><strong>{c.name}</strong> <span style={{ ...muted, fontFamily: 'monospace', fontSize: '0.78rem' }}>{short(c.address)}</span> <span style={{ color: peer ? '#fcd34d' : '#86efac', fontSize: '0.78rem' }}>{peer ? 'Peer' : 'Mine/class'}</span></span>
                    <button onClick={() => openContract(c)} disabled={!c.abi} style={btn(!!c.abi, false)}>Interact</button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div style={box}>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
          <strong>1. Choose a contract</strong>
          <select value={templateId} onChange={(e) => loadTemplate(e.target.value)} style={inputStyle}>
            {CATALOG.map((c) => <option key={c.id} value={c.id}>{c.name} — {c.desc}</option>)}
          </select>
        </div>
        <textarea
          value={source}
          onChange={(e) => { setSource(e.target.value); setCompiled(null); completeTask('write'); }}
          spellCheck={false}
          style={{ width: '100%', minHeight: '240px', padding: '0.75rem', background: '#0c0c0c', border: '1px solid #334155', borderRadius: '0.5rem', color: '#86efac', fontFamily: 'monospace', fontSize: '0.82rem', lineHeight: 1.5, resize: 'vertical' }}
        />
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', marginTop: '0.75rem', flexWrap: 'wrap' }}>
          <button onClick={compile} disabled={compiling} style={btn(!compiling, false)}>{compiling ? 'Compiling…' : '⚙️ Compile'}</button>

          {ctor?.inputs?.length > 0 && (
            <span style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={muted}>constructor:</span>
              {ctor.inputs.map((inp, i) => (
                <input key={i} placeholder={`${inp.type} ${inp.name || ''}`} value={ctorArgs[i] ?? ''}
                  onChange={(e) => setCtorArgs((a) => ({ ...a, [i]: e.target.value }))} style={{ ...inputStyle, width: '150px' }} />
              ))}
            </span>
          )}

          <button onClick={deploy} disabled={!compiled || deploying || !signer} style={btn(!!compiled && !deploying && !!signer, true)}>
            {deploying ? 'Deploying…' : '🚀 Deploy from my wallet'}
          </button>
        </div>
        {status && <pre style={{ whiteSpace: 'pre-wrap', margin: '0.75rem 0 0', fontSize: '0.82rem', color: status.startsWith('❌') ? '#fca5a5' : '#86efac' }}>{status}</pre>}
        {!signer && <div style={{ ...muted, marginTop: '0.5rem', fontSize: '0.82rem' }}>Connect/await your wallet on the Dashboard to deploy.</div>}
      </div>

      {active && <InteractPanel key={active.address} address={active.address} abi={active.abi} name={active.name} signer={signer} provider={provider} onInteract={handleInteract} />}

      <div style={box}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <strong>Deployed on this network</strong>
          <button onClick={loadDeployed} style={{ ...muted, background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>↻ refresh</button>
        </div>
        {deployedList.length === 0 ? <div style={muted}>No contracts deployed yet. Deploy one above — it’ll appear here for the whole class.</div> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {deployedList.map((c) => (
              <div key={c.address} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', alignItems: 'center', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)', flexWrap: 'wrap' }}>
                <span><strong>{c.name}</strong> <span style={{ ...muted, fontFamily: 'monospace', fontSize: '0.8rem' }}>{short(c.address)}</span></span>
                <span style={{ ...muted, fontSize: '0.78rem' }}>by {short(c.deployer)}</span>
                <button onClick={() => openContract(c)} disabled={!c.abi} style={btn(!!c.abi, false)}>Interact</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={box}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', gap: '0.75rem', flexWrap: 'wrap' }}>
          <strong>All smart contracts on chain</strong>
          <button onClick={loadChainContracts} disabled={loadingChainContracts} style={{ ...muted, background: 'none', border: 'none', cursor: loadingChainContracts ? 'not-allowed' : 'pointer', textDecoration: 'underline', opacity: loadingChainContracts ? 0.65 : 1 }}>
            {loadingChainContracts ? 'searching...' : 'find contracts'}
          </button>
        </div>
        {chainContractsStatus && <div style={{ ...muted, fontSize: '0.82rem', marginBottom: '0.55rem' }}>{chainContractsStatus}</div>}
        {chainContracts.length === 0 ? <div style={muted}>No contracts found yet.</div> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {chainContracts.map((c) => {
              const canInteract = Array.isArray(c.abi);
              const peer = isPeerContract(c);
              return (
                <div key={`chain-${c.address}`} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', alignItems: 'center', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)', flexWrap: 'wrap' }}>
                  <span>
                    <strong>{c.name || 'Unknown contract'}</strong>{' '}
                    <span style={{ ...muted, fontFamily: 'monospace', fontSize: '0.8rem' }}>{short(c.address)}</span>{' '}
                    <span style={{ color: canInteract ? '#86efac' : '#fcd34d', fontSize: '0.78rem' }}>{canInteract ? 'ABI saved' : 'ABI unavailable'}</span>
                    {peer && <span style={{ color: '#fcd34d', fontSize: '0.78rem' }}> · Peer</span>}
                  </span>
                  <span style={{ ...muted, fontSize: '0.78rem' }}>{c.blockNumber != null ? `block #${c.blockNumber}` : 'block unknown'}</span>
                  <button onClick={() => openContract(c)} disabled={!canInteract} style={btn(canInteract, false)}>Interact</button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
