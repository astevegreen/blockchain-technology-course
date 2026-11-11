/**
 * ContractLab - Deploy, connect, and interact with contracts from the GUI.
 * Students can write Solidity, compile, deploy templates, and connect to classmate's contracts.
 */

import { useEffect, useMemo, useState } from 'react';
import { ethers } from 'ethers';
import { loadSolc } from 'web-solc';

/** Local solc-bin mirror layout under `frontend/public/vendor/solc`. */
const SOLC_VENDOR_BASE = `${import.meta.env.BASE_URL || '/'}vendor/solc`.replace(/\/$/, '');
const SOLC_VERSION = '0.8.26';
const SOLC_VENDOR_PATH = `${SOLC_VENDOR_BASE}/bin/soljson-v0.8.26+commit.8a97fa7a.js`;

/** Loads the vendored in-browser compiler. */
async function fetchAndLoadSolcWithFallback() {
  const response = await fetch(SOLC_VENDOR_PATH);
  if (!response.ok) {
    throw new Error(`Could not load vendored solc ${SOLC_VERSION}: ${response.status} ${response.statusText}`);
  }
  const soljson = await response.text();
  const inst = await loadSolc(soljson);
  return { inst, label: `vendored solc ${SOLC_VERSION}` };
}
import { ChainExplorer } from './ChainExplorer';
import { getExampleScripts } from '../constants/exampleScripts';
import SimpleStorageArtifact from '../contracts/SimpleStorage.json';
import ClassVoteArtifact from '../contracts/ClassVote.json';
import PoSABI from '../PoS.json';

/** web-solc rejects with ErrorEvent on worker failures; String(e) is useless */
function formatCompileFailure(e) {
  if (e == null) return 'Unknown error';
  if (typeof e === 'string') return e;
  if (e instanceof Error) return e.stack || e.message;
  const err = typeof e === 'object' && e && 'error' in e ? e.error : null;
  if (err instanceof Error) return err.message || String(err);
  const msg = typeof e === 'object' && e && typeof e.message === 'string' ? e.message : '';
  if (msg) return msg;
  const type = typeof e === 'object' && e && e.type;
  if (type === 'error' || (typeof ErrorEvent !== 'undefined' && e instanceof ErrorEvent)) {
    const loc =
      e.filename != null ? ` (${e.filename}:${e.lineno ?? '?'})` : '';
    return (
      (msg || 'Browser compiler worker failed') +
      loc +
      '. Often: the vendored Solidity compiler asset is missing or blocked. Rebuild the frontend assets, or compile with npx hardhat compile in the project root.'
    );
  }
  if (typeof Event !== 'undefined' && e instanceof Event) {
    return `Worker "${e.type}" event (no details). Same fixes as above: confirm the vendored compiler exists, or use Hardhat compile locally.`;
  }
  try {
    return JSON.stringify(e);
  } catch {
    return String(e);
  }
}

function formatSolcErrors(errors) {
  if (!Array.isArray(errors) || !errors.length) return '';
  return errors
    .map((err) => err.formattedMessage || err.message || JSON.stringify(err))
    .join('\n');
}

function ExampleScriptCard({ script, onLoad }) {
  const [showCode, setShowCode] = useState(false);
  return (
    <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#0f172a', borderRadius: '0.5rem', border: '1px solid #334155' }}>
      <div style={{ fontSize: '0.95rem', color: '#c4b5fd', marginBottom: '0.25rem' }}>{script.name}</div>
      <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.5rem' }}>{script.description}</div>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          onClick={onLoad}
          style={{
            padding: '0.4rem 0.9rem',
            background: '#6366f1',
            color: 'white',
            border: 'none',
            borderRadius: '0.35rem',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: 'bold'
          }}
        >
          Load
        </button>
        <button
          onClick={() => setShowCode(!showCode)}
          style={{
            padding: '0.4rem 0.9rem',
            background: 'transparent',
            color: '#94a3b8',
            border: '1px solid #475569',
            borderRadius: '0.35rem',
            cursor: 'pointer',
            fontSize: '0.85rem'
          }}
        >
          {showCode ? 'Hide code' : 'Show full code'}
        </button>
      </div>
      {showCode && (
        <pre style={{
          marginTop: '0.75rem',
          padding: '0.75rem',
          background: '#020617',
          borderRadius: '0.35rem',
          color: '#86efac',
          fontSize: '0.8rem',
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          maxHeight: '200px',
          border: '1px solid #334155'
        }}>
          {script.code}
        </pre>
      )}
    </div>
  );
}

function DeployedHelp() {
  const [open, setOpen] = useState(true);
  return (
    <div style={{ marginTop: '1rem', borderTop: '1px solid #334155', paddingTop: '0.75rem' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          background: 'none', border: 'none', color: '#93c5fd', cursor: 'pointer', fontSize: '0.85rem',
          display: 'flex', alignItems: 'center', gap: '0.35rem', padding: 0
        }}
      >
        {open ? '▼' : '▶'} How do I check my account balance?
      </button>
      {open && (
        <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.5 }}>
          <p style={{ margin: '0 0 0.5rem 0' }}><strong style={{ color: '#e2e8f0' }}>ETH balance:</strong> Your wallet balance appears in the card at the top right. Or use the Lab Terminal below—run <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>npm run console</code> and query the chain.</p>
          <p style={{ margin: '0 0 0.5rem 0' }}><strong style={{ color: '#e2e8f0' }}>Token balance:</strong> If your contract has <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>balanceOf</code>, go to the <strong>Connect & Interact</strong> tab, paste your contract address, and call <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>balanceOf(yourAddress)</code>.</p>
        </div>
      )}
    </div>
  );
}

const DEFAULT_SOLIDITY = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MyContract {
    uint256 public value;
    
    function set(uint256 _value) external {
        value = _value;
    }
    
    function get() external view returns (uint256) {
        return value;
    }
}`;

const TEMPLATES = [
  { id: 'SimpleStorage', name: 'SimpleStorage', artifact: SimpleStorageArtifact, constructorArgs: [], deployable: true },
  { id: 'ClassVote', name: 'Class Vote (Voting)', artifact: ClassVoteArtifact, constructorArgs: [], deployable: true },
  {
    id: 'PoS',
    name: 'PoS Simulator (Lab)',
    artifact: { abi: Array.isArray(PoSABI) ? PoSABI : PoSABI.abi, bytecode: '0x' },
    constructorArgs: [],
    deployable: false
  }
];

const DEPLOY_TEMPLATES = TEMPLATES.filter((t) => t.deployable !== false);

/** Map form text → JS value for ethers. Handles common ABI types; arrays/tuples as JSON. */
function parseAbiArgInput(inp, raw) {
  const t = inp.type || '';
  const label = inp.name || t;
  const v = raw === undefined || raw === null ? '' : String(raw).trim();
  const blank = v === '';

  if (t === 'address') {
    if (blank) return ethers.ZeroAddress;
    return ethers.getAddress(v);
  }
  if (t === 'bool') {
    if (blank) return false;
    const l = v.toLowerCase();
    if (l === 'true' || v === '1' || l === 'yes') return true;
    if (l === 'false' || v === '0' || l === 'no') return false;
    throw new Error(`${label}: use true/false`);
  }
  if (t === 'string') return blank ? '' : v;

  if (t.startsWith('bytes') && t !== 'bytes') {
    const n = parseInt(t.replace('bytes', ''), 10) || 32;
    if (blank) return ethers.zeroPadValue('0x00', n);
    const h = ethers.isHexString(v) ? v : ethers.hexlify(ethers.toUtf8Bytes(v));
    return ethers.zeroPadValue(h, n);
  }
  if (t === 'bytes') {
    if (blank) return '0x';
    return ethers.isHexString(v) ? v : ethers.hexlify(ethers.toUtf8Bytes(v));
  }
  if (t.includes('uint')) {
    if (blank) return 0n;
    return BigInt(v);
  }
  if (/^int\d+$/.test(t) || (t.includes('int') && !t.includes('uint'))) {
    if (blank) return 0n;
    return BigInt(v);
  }
  if (t.includes(']')) {
    if (blank) throw new Error(`${label}: provide a JSON array`);
    const parsed = JSON.parse(v);
    if (!Array.isArray(parsed)) throw new Error(`${label}: must be a JSON array`);
    return parsed;
  }
  if (t.includes('(')) {
    if (blank) throw new Error(`${label}: tuple — paste JSON array matching field order`);
    return JSON.parse(v);
  }
  return blank ? '' : v;
}

function formatCallResult(value) {
  if (value == null) return '';
  if (typeof value === 'bigint') return value.toString();
  if (Array.isArray(value)) {
    return value.map((x) => formatCallResult(x)).join(', ');
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, (_, x) => (typeof x === 'bigint' ? x.toString() : x));
    } catch {
      return String(value);
    }
  }
  return String(value);
}

function ContractLab({ provider, rpcUrl, wallet, posAddress, onLoadScript, setStatusMsg }) {
  const [activeTab, setActiveTab] = useState('examples');
  const [solidityCode, setSolidityCode] = useState(DEFAULT_SOLIDITY);
  const [contractName, setContractName] = useState('MyContract');
  const [compileOutput, setCompileOutput] = useState('');
  const [compiling, setCompiling] = useState(false);
  const [deployTemplate, setDeployTemplate] = useState('SimpleStorage');
  const [deployArgs, setDeployArgs] = useState({});
  const [deploying, setDeploying] = useState(false);
  const [deployedAddress, setDeployedAddress] = useState('');
  const [connectAddress, setConnectAddress] = useState('');
  const [connectTemplate, setConnectTemplate] = useState('SimpleStorage');
  const [pastedAbiJson, setPastedAbiJson] = useState('');
  const [pastedAbi, setPastedAbi] = useState(null);
  const [connectMode, setConnectMode] = useState('read');
  const [callResult, setCallResult] = useState('');
  const [calling, setCalling] = useState(false);
  const [connectFnFilter, setConnectFnFilter] = useState('');
  const [connectSnapshot, setConnectSnapshot] = useState({ codeLen: '', balance: '', loading: false });
  const [eventName, setEventName] = useState('');
  const [eventPreview, setEventPreview] = useState('');
  const [eventLoading, setEventLoading] = useState(false);
  /** Optional 0x… for example script 4 (classmate contract); overrides PoS default when valid */
  const [classmateBytecodeAddress, setClassmateBytecodeAddress] = useState('');
  /** Optional 0x… for script 6 (SimpleStorage get/owner); overrides Deploy/Connect when valid */
  const [scriptSixStorageAddress, setScriptSixStorageAddress] = useState('');

  const exampleScripts = useMemo(
    () =>
      getExampleScripts({
        livePosAddress: posAddress,
        labClassmateBytecodeAddress: classmateBytecodeAddress,
        labScriptSixAddress: scriptSixStorageAddress,
        labDeployedAddress: deployedAddress,
        labConnectAddress: connectAddress
      }),
    [posAddress, classmateBytecodeAddress, scriptSixStorageAddress, deployedAddress, connectAddress]
  );

  const connectAbi = useMemo(() => {
    if (connectTemplate === '__pasted__' && pastedAbi) return pastedAbi;
    if (connectTemplate === '__custom__' && typeof window !== 'undefined' && window.__lastCompiled) {
      return window.__lastCompiled.abi;
    }
    return TEMPLATES.find((t) => t.id === connectTemplate)?.artifact?.abi;
  }, [connectTemplate, pastedAbi]);

  useEffect(() => {
    if (activeTab !== 'connect' || !provider || !connectAddress || !ethers.isAddress(connectAddress)) {
      setConnectSnapshot({ codeLen: '', balance: '', loading: false });
      return;
    }
    let cancelled = false;
    setConnectSnapshot((s) => ({ ...s, loading: true }));
    (async () => {
      try {
        const [code, bal] = await Promise.all([
          provider.getCode(connectAddress),
          provider.getBalance(connectAddress)
        ]);
        if (cancelled) return;
        const byteLen = code && code !== '0x' ? Math.floor((code.length - 2) / 2) : 0;
        setConnectSnapshot({
          codeLen: byteLen ? `${byteLen} bytes on-chain` : 'no contract bytecode (EOA or empty)',
          balance: `${ethers.formatEther(bal)} ETH`,
          loading: false
        });
      } catch {
        if (!cancelled) {
          setConnectSnapshot({ codeLen: '—', balance: '—', loading: false });
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeTab, provider, connectAddress]);

  useEffect(() => {
    const evs = (connectAbi || []).filter((x) => x.type === 'event' && x.name);
    if (!evs.length) {
      setEventName('');
      return;
    }
    setEventName((prev) => (prev && evs.some((e) => e.name === prev) ? prev : evs[0].name));
  }, [connectAbi]);

  const loadExample = (script) => {
    onLoadScript?.(script.code);
    // Parent handles status when onLoadScript is provided (expands terminal, shows feedback)
    if (!onLoadScript) {
      setStatusMsg?.('✓ Script loaded. Expand Lab Terminal to run it.');
      setTimeout(() => setStatusMsg?.(''), 3000);
    }
  };

  const handleDeploy = async () => {
    if (!wallet?.signer) {
      setStatusMsg?.('❌ Connect wallet first');
      return;
    }
    let abi, bytecode;
    if (deployTemplate === '__custom__' && window.__lastCompiled) {
      abi = window.__lastCompiled.abi;
      bytecode = window.__lastCompiled.bytecode;
    } else {
      const t = DEPLOY_TEMPLATES.find((x) => x.id === deployTemplate);
      if (!t) return;
      abi = t.artifact.abi;
      bytecode = t.artifact.bytecode;
    }
    setDeploying(true);
    setStatusMsg?.('📤 Deploying...');
    try {
      const factory = new ethers.ContractFactory(abi, bytecode, wallet.signer);
      const instance = await factory.deploy();
      const deployTx = instance.deploymentTransaction?.();
      if (deployTx) await deployTx.wait();
      else await instance.waitForDeployment();
      setDeployedAddress(instance.target);
      setStatusMsg?.('✅ Deployed! Address: ' + instance.target);
      setTimeout(() => setStatusMsg?.(''), 4000);
    } catch (e) {
      setStatusMsg?.('❌ ' + (e.reason || e.message));
    } finally {
      setDeploying(false);
    }
  };

  const handleCall = async (fn, isView, args = [], options = {}) => {
    const valueEth = typeof options.valueEth === 'string' ? options.valueEth : '';
    if (!connectAddress || !ethers.isAddress(connectAddress)) {
      setCallResult('❌ Enter a valid contract address (0x...) above first.');
      return;
    }
    const abi = connectAbi;
    if (!abi) {
      setCallResult('❌ Select a contract type or compile one in Write tab first.');
      return;
    }
    const signer = isView ? provider : wallet?.signer;
    if (!signer) {
      setCallResult(isView ? '❌ Connect to blockchain (set RPC URL in config) to read.' : '❌ Connect wallet to send transactions.');
      return;
    }
    setCalling(true);
    setCallResult('⏳ Calling...');
    try {
      const c = new ethers.Contract(connectAddress, abi, signer);
      const overrides = {};
      if (fn.stateMutability === 'payable' && valueEth.trim()) {
        overrides.value = ethers.parseEther(valueEth.trim());
      }
      const hasOverrides = Object.keys(overrides).length > 0;
      let result;
      if (args.length === 0 && !hasOverrides) {
        result = await c[fn.name]();
      } else if (args.length === 0 && hasOverrides) {
        result = await c[fn.name](overrides);
      } else if (hasOverrides) {
        result = await c[fn.name](...args, overrides);
      } else {
        result = await c[fn.name](...args);
      }
      setCallResult(formatCallResult(result));
    } catch (e) {
      setCallResult('❌ ' + (e.reason || e.message || String(e)));
    } finally {
      setCalling(false);
    }
  };

  const handleQueryEvents = async () => {
    if (!provider || !connectAddress || !ethers.isAddress(connectAddress)) {
      setEventPreview('❌ Set a valid contract address.');
      return;
    }
    if (!connectAbi?.length || !eventName) {
      setEventPreview('❌ Select an ABI with events and pick an event name.');
      return;
    }
    setEventLoading(true);
    setEventPreview('⏳ Querying…');
    try {
      const iface = new ethers.Interface(connectAbi);
      const c = new ethers.Contract(connectAddress, connectAbi, provider);
      const latest = await provider.getBlockNumber();
      const from = Math.max(0, latest - 4999);
      const logs = await c.queryFilter(eventName, from, latest);
      const slice = logs.slice(-25);
      const lines = slice.map((log) => {
        try {
          const parsed = iface.parseLog(log);
          const parts = [];
          for (let i = 0; i < parsed.args.length; i++) {
            const a = parsed.args[i];
            parts.push(typeof a === 'bigint' ? a.toString() : String(a));
          }
          return `block ${log.blockNumber} · ${parsed.name}(${parts.join(', ')})`;
        } catch {
          return `block ${log.blockNumber} · ${log.transactionHash?.slice(0, 12)}…`;
        }
      });
      setEventPreview(
        lines.length
          ? `Last ${lines.length} (newest) in ~last 5000 blocks:\n` + lines.join('\n')
          : 'No matching logs in the last ~5000 blocks.'
      );
    } catch (e) {
      setEventPreview('❌ ' + (e.reason || e.message || String(e)));
    } finally {
      setEventLoading(false);
    }
  };

  const getFunctions = (abi) => {
    return (abi || []).filter(x => x.type === 'function' && x.name !== '');
  };

  const boxStyle = {
    padding: '1rem',
    background: 'rgba(30, 41, 59, 0.9)',
    borderRadius: '0.5rem',
    border: '1px solid #334155',
    marginBottom: '1rem'
  };

  return (
    <div style={{ maxWidth: '800px' }}>
      <h3 style={{ marginBottom: '1rem', color: '#a78bfa' }}>🏗️ Contract Lab</h3>
      <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '1rem' }}>
        Deploy templates, connect to classmate's contracts, and run example scripts to verify your setup.
      </p>

      <ChainExplorer provider={provider} rpcUrl={rpcUrl} signer={wallet?.signer} cacheOnly />

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {['examples', 'write', 'deploy', 'connect'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '0.5rem 1rem',
              background: activeTab === tab ? '#8b5cf6' : '#334155',
              color: 'white',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            {tab === 'examples' ? 'Example Scripts' : tab === 'write' ? 'Write & Compile' : tab === 'deploy' ? 'Deploy' : 'Connect & Interact'}
          </button>
        ))}
      </div>

      {activeTab === 'examples' && (
        <div style={boxStyle}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.75rem', color: '#e2e8f0' }}>Verification scripts</div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
            Click <strong>Load</strong> to paste into the <strong>Lab Terminal</strong> (Hardhat console). Run from the <strong>project root</strong>.
            {posAddress && ethers.isAddress(posAddress) ? (
              <>
                Your PoS address from <strong>Live → Connection Setup</strong> is <strong>already inserted</strong> into scripts 1, 3, 4 (bytecode check), and 5.
              </>
            ) : (
              <>
                Replace <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>PASTE_POSE_ADDRESS</code> in PoS scripts with your PoS address, or set it in Connection Setup and click Load again.
              </>
            )}
            {(scriptSixStorageAddress && ethers.isAddress(scriptSixStorageAddress.trim())) ||
            (deployedAddress && ethers.isAddress(deployedAddress)) ||
            (connectAddress && ethers.isAddress(connectAddress)) ? (
              <>
                {' '}
                Script 6 can use the <strong>Script 6</strong> field below, or your <strong>Deploy</strong> / <strong>Connect &amp; Interact</strong> address when set.
              </>
            ) : null}{' '}
            Paste the <strong>entire</strong> block at once. PoS ABI loads from Hardhat <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>artifacts/</code> when present, else <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>./abi/PoS.json</code> (lab Docker) or <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>./frontend/src/PoS.json</code> (full checkout). Scripts use <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>ethers.getAddress</code> so Hardhat does not treat the target as ENS (<code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>resolveName</code> is not implemented there). Use <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>console.log(...)</code> if you want explicit output; the last expression prints in the REPL.
          </p>
          <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>
            <strong style={{ color: '#e2e8f0' }}>Script 4 — classmate contract address</strong> (optional)
          </label>
          <input
            type="text"
            spellCheck={false}
            autoComplete="off"
            placeholder="0x… paste a classmate’s deployed contract; leave empty to use PoS from Connection Setup"
            value={classmateBytecodeAddress}
            onChange={(e) => setClassmateBytecodeAddress(e.target.value)}
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '0.5rem 0.65rem',
              marginBottom: '0.35rem',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '0.35rem',
              color: '#e2e8f0',
              fontFamily: 'monospace',
              fontSize: '0.8rem'
            }}
          />
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '1rem', lineHeight: 1.45 }}>
            Script 4 uses this field when it is a valid <code style={{ background: '#1e293b', padding: '0.05rem 0.2rem', borderRadius: 3 }}>0x…</code> address; if you leave it empty, script 4 falls back to your PoS from Connection Setup (or the placeholder so you can edit the pasted code).
          </p>
          <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>
            <strong style={{ color: '#e2e8f0' }}>Script 6 — SimpleStorage contract address</strong> (optional)
          </label>
          <input
            type="text"
            spellCheck={false}
            autoComplete="off"
            placeholder="0x… your deployed SimpleStorage; leave empty to use Deploy tab or Connect & Interact address"
            value={scriptSixStorageAddress}
            onChange={(e) => setScriptSixStorageAddress(e.target.value)}
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '0.5rem 0.65rem',
              marginBottom: '0.35rem',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '0.35rem',
              color: '#e2e8f0',
              fontFamily: 'monospace',
              fontSize: '0.8rem'
            }}
          />
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '1rem', lineHeight: 1.45 }}>
            Script 6 calls <code style={{ background: '#1e293b', padding: '0.05rem 0.2rem', borderRadius: 3 }}>get()</code> and <code style={{ background: '#1e293b', padding: '0.05rem 0.2rem', borderRadius: 3 }}>owner()</code> on a SimpleStorage contract. Use this field first; otherwise the last <strong>Deploy</strong> or <strong>Connect</strong> address is embedded (must be SimpleStorage).
          </p>
          {exampleScripts.map((s, i) => (
            <ExampleScriptCard key={i} script={s} onLoad={() => loadExample(s)} />
          ))}
        </div>
      )}

      {activeTab === 'write' && (
        <div style={boxStyle}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.75rem', color: '#e2e8f0' }}>Write Solidity</div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
            Write your contract, compile, then deploy. Contract name must match the contract in code.
          </p>
          <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.75rem', lineHeight: 1.5 }}>
            <strong style={{ color: '#cbd5e1' }}>Easiest:</strong> skip browser compile and use the <strong>Deploy</strong> tab with <strong>SimpleStorage</strong> or <strong>Class Vote</strong>, or paste an ABI from <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>artifacts/</code> after{' '}
            <code style={{ background: '#1e293b', padding: '0.1rem 0.25rem', borderRadius: 3 }}>npx hardhat compile</code>.
            {' '}The in-browser compiler uses the vendored Solidity compiler bundled with this lab.
          </p>
          <input
            placeholder="Contract name (e.g. MyContract)"
            value={contractName}
            onChange={e => setContractName(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem', background: '#0f172a', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0' }}
          />
          <textarea
            value={solidityCode}
            onChange={e => setSolidityCode(e.target.value)}
            style={{
              width: '100%',
              minHeight: '200px',
              padding: '0.75rem',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '0.35rem',
              color: '#e2e8f0',
              fontFamily: 'monospace',
              fontSize: '0.85rem'
            }}
            spellCheck={false}
          />
          <button
            onClick={async () => {
              setCompiling(true);
              setCompileOutput('⏳ Loading vendored compiler...');
              let solcInstance = null;
              try {
                try {
                  const { inst, label } = await fetchAndLoadSolcWithFallback();
                  solcInstance = inst;
                  setCompileOutput(`⏳ Compiling… (loaded ${label})`);
                } catch (fetchErr) {
                  console.error('[ContractLab] fetchAndLoadSolcWithFallback', fetchErr);
                  setCompileOutput(
                    '❌ Could not load the vendored Solidity compiler.\n' +
                      formatCompileFailure(fetchErr) +
                      '\n\nUse the Deploy tab with a built-in template, or run npx hardhat compile and paste ABI/bytecode.'
                  );
                  return;
                }
                const input = {
                  language: 'Solidity',
                  sources: { 'contract.sol': { content: solidityCode } },
                  settings: {
                    outputSelection: { '*': { '*': ['abi', 'evm.bytecode'] } }
                  }
                };
                let output;
                try {
                  output = await solcInstance.compile(input);
                } catch (compileErr) {
                  console.error('[ContractLab] compile()', compileErr);
                  setCompileOutput(
                    '❌ Compile worker error:\n' +
                      formatCompileFailure(compileErr) +
                      '\n\nIf this persists, use Deploy → SimpleStorage / Class Vote, or run npx hardhat compile and paste ABI + bytecode.'
                  );
                  return;
                }
                if (!output || typeof output !== 'object') {
                  setCompileOutput('❌ Compiler returned an empty or invalid response. See browser console.');
                  console.error('[ContractLab] unexpected output', output);
                  return;
                }
                if (output.errors?.length) {
                  const errs = output.errors.filter((e) => e.severity === 'error');
                  if (errs.length) {
                    setCompileOutput('Compile errors:\n' + formatSolcErrors(errs));
                    return;
                  }
                  const warns = output.errors.filter((e) => e.severity === 'warning');
                  if (warns.length) {
                    setCompileOutput('Warnings (still compiling…):\n' + formatSolcErrors(warns));
                  }
                }
                const contract = output.contracts?.['contract.sol']?.[contractName];
                if (!contract) {
                  setCompileOutput(
                    'Contract "' +
                      contractName +
                      '" not found in output. Match the name in the box to `contract Name` in code, or check compile messages above.'
                  );
                  return;
                }
                const abi = contract.abi;
                const obj = contract.evm?.bytecode?.object;
                if (!obj || typeof obj !== 'string' || obj.length < 4) {
                  setCompileOutput(
                    'No deployable bytecode (library, abstract contract, or only interfaces). Solc output:\n' +
                      formatSolcErrors(output.errors || [])
                  );
                  return;
                }
                const bytecode = obj.startsWith('0x') ? obj : '0x' + obj;
                setCompileOutput('✓ Compiled! Go to Deploy tab → select "My compiled contract" → Deploy.');
                setDeployTemplate('__custom__');
                setActiveTab('deploy');
                window.__lastCompiled = { abi, bytecode };
              } catch (e) {
                console.error('[ContractLab] compile pipeline', e);
                setCompileOutput('❌ ' + formatCompileFailure(e));
              } finally {
                if (solcInstance) {
                  try {
                    solcInstance.stopWorker();
                  } catch (sw) {
                    console.warn('[ContractLab] stopWorker', sw);
                  }
                }
                setCompiling(false);
              }
            }}
            disabled={compiling}
            style={{
              marginTop: '0.75rem',
              padding: '0.5rem 1rem',
              background: compiling ? '#475569' : '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: compiling ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {compiling ? '⏳ Compiling...' : 'Compile'}
          </button>
          {compileOutput && (
            <pre style={{ marginTop: '1rem', padding: '0.75rem', background: '#0f172a', borderRadius: '0.35rem', color: '#94a3b8', fontSize: '0.85rem', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
              {compileOutput}
            </pre>
          )}
        </div>
      )}

      {activeTab === 'deploy' && (
        <div style={boxStyle}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.75rem', color: '#e2e8f0' }}>Deploy a template</div>
          <select
            value={deployTemplate}
            onChange={e => setDeployTemplate(e.target.value)}
            style={{ padding: '0.5rem', marginBottom: '0.75rem', background: '#1e293b', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0' }}
          >
            {DEPLOY_TEMPLATES.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
            <option value="__custom__">My compiled contract (from Write tab)</option>
          </select>
          <button
            onClick={handleDeploy}
            disabled={deploying || !wallet?.signer}
            style={{
              padding: '0.5rem 1rem',
              background: (deploying || !wallet?.signer) ? '#475569' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: (deploying || !wallet?.signer) ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {deploying ? '⏳ Deploying...' : 'Deploy'}
          </button>
          {deployedAddress && (
            <div style={{ marginTop: '1rem', padding: '0.5rem', background: '#0f172a', borderRadius: '0.35rem', fontSize: '0.85rem' }}>
              <div style={{ color: '#34d399' }}>✓ Deployed: {deployedAddress}</div>
              <button
                onClick={() => navigator.clipboard.writeText(deployedAddress)}
                style={{ marginTop: '0.35rem', padding: '0.25rem 0.5rem', background: '#475569', color: 'white', border: 'none', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
              >
                Copy address
              </button>
              <DeployedHelp />
            </div>
          )}
        </div>
      )}

      {activeTab === 'connect' && (
        <div style={boxStyle}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.75rem', color: '#e2e8f0' }}>Connect to a contract</div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
            Paste any contract address, pick a built-in ABI (including <strong>PoS Simulator</strong>) or <strong>Paste ABI</strong>, then read/write functions. Use the filter to find a function on large ABIs. Payable writes can include ETH. Query recent <strong>events</strong> below.
          </p>

          {!provider && (
            <div style={{ padding: '0.75rem', marginBottom: '1rem', background: 'rgba(251, 191, 36, 0.15)', borderRadius: '0.5rem', border: '1px solid rgba(251, 191, 36, 0.4)', color: '#fde047', fontSize: '0.9rem' }}>
              ⚠️ Connect to blockchain first: Set RPC URL in the config panel (top right) and connect to your node.
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Contract address</label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                placeholder="0x..."
                value={connectAddress}
                onChange={e => setConnectAddress(e.target.value)}
                style={{ flex: 1, padding: '0.6rem 0.75rem', background: '#0f172a', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0', fontFamily: 'monospace', fontSize: '0.9rem' }}
              />
              {deployedAddress && (
                <button
                  type="button"
                  onClick={() => setConnectAddress(deployedAddress)}
                  style={{ padding: '0.5rem 0.75rem', background: '#334155', color: '#94a3b8', border: '1px solid #475569', borderRadius: '0.35rem', cursor: 'pointer', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                >
                  Use deployed
                </button>
              )}
              {posAddress && ethers.isAddress(posAddress) && (
                <button
                  type="button"
                  onClick={() => setConnectAddress(posAddress)}
                  style={{ padding: '0.5rem 0.75rem', background: '#334155', color: '#94a3b8', border: '1px solid #475569', borderRadius: '0.35rem', cursor: 'pointer', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                >
                  Use PoS (Live)
                </button>
              )}
            </div>
            {connectAddress && ethers.isAddress(connectAddress) && provider && (
              <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.75rem', padding: '0.5rem 0.65rem', background: '#020617', borderRadius: '0.35rem', border: '1px solid #334155' }}>
                {connectSnapshot.loading ? 'Checking on-chain…' : (
                  <>
                    <span style={{ color: '#94a3b8' }}>Bytecode: </span>
                    <span style={{ color: '#e2e8f0' }}>{connectSnapshot.codeLen || '—'}</span>
                    <span style={{ margin: '0 0.75rem', color: '#475569' }}>|</span>
                    <span style={{ color: '#94a3b8' }}>Balance: </span>
                    <span style={{ color: '#e2e8f0' }}>{connectSnapshot.balance || '—'}</span>
                  </>
                )}
              </div>
            )}
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Contract type</label>
            <select
              value={connectTemplate}
              onChange={e => { setConnectTemplate(e.target.value); if (e.target.value !== '__pasted__') setPastedAbi(null); }}
              style={{ width: '100%', padding: '0.6rem', background: '#1e293b', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0', fontSize: '0.9rem' }}
            >
              {TEMPLATES.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
              <option value="__custom__">My contract (use last compiled ABI)</option>
              <option value="__pasted__">Paste ABI (any contract)</option>
            </select>
            {connectTemplate === '__pasted__' && (
              <div style={{ marginTop: '0.75rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Paste contract ABI (JSON array from artifacts/*.json)</label>
                <textarea
                  placeholder='[{"inputs":[],"name":"get","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},...]'
                  value={pastedAbiJson}
                  onChange={e => setPastedAbiJson(e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: '120px',
                    padding: '0.6rem',
                    background: '#0f172a',
                    border: '1px solid #475569',
                    borderRadius: '0.35rem',
                    color: '#e2e8f0',
                    fontSize: '0.8rem',
                    fontFamily: 'monospace'
                  }}
                />
                <button
                  onClick={() => {
                    try {
                      const parsed = typeof pastedAbiJson === 'string' ? JSON.parse(pastedAbiJson) : pastedAbiJson;
                      const arr = Array.isArray(parsed) ? parsed : (parsed?.abi || parsed?.ABI);
                      if (!Array.isArray(arr) || arr.length === 0) throw new Error('ABI must be a non-empty array');
                      setPastedAbi(arr);
                      setStatusMsg?.('✓ ABI applied. All functions detected.');
                      setTimeout(() => setStatusMsg?.(''), 3000);
                    } catch (e) {
                      setStatusMsg?.('❌ Invalid ABI: ' + (e.message || 'parse error'));
                      setPastedAbi(null);
                    }
                  }}
                  style={{
                    marginTop: '0.5rem',
                    padding: '0.4rem 1rem',
                    background: '#6366f1',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.35rem',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: 'bold'
                  }}
                >
                  Apply ABI
                </button>
                {pastedAbi && (
                  <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', color: '#34d399' }}>
                    ✓ {pastedAbi.filter(x => x.type === 'function').length} functions
                  </span>
                )}
              </div>
            )}
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Filter functions by name</label>
            <input
              placeholder="e.g. stake, vote, get — narrows the lists below"
              value={connectFnFilter}
              onChange={(e) => setConnectFnFilter(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.65rem',
                background: '#0f172a',
                border: '1px solid #475569',
                borderRadius: '0.35rem',
                color: '#e2e8f0',
                fontSize: '0.85rem',
                fontFamily: 'inherit'
              }}
            />
          </div>

          {/* Etherscan-style: Read Contract | Write Contract */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <button
              onClick={() => setConnectMode('read')}
              style={{
                padding: '0.5rem 1rem',
                background: connectMode === 'read' ? '#3b82f6' : '#334155',
                color: 'white',
                border: 'none',
                borderRadius: '0.35rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: connectMode === 'read' ? 'bold' : 'normal'
              }}
            >
              Read Contract
            </button>
            <button
              onClick={() => setConnectMode('write')}
              style={{
                padding: '0.5rem 1rem',
                background: connectMode === 'write' ? '#f59e0b' : '#334155',
                color: 'white',
                border: 'none',
                borderRadius: '0.35rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: connectMode === 'write' ? 'bold' : 'normal'
              }}
            >
              Write Contract
            </button>
          </div>

          {connectMode === 'read' && (
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.75rem' }}>
                View functions (no gas). Arrays / tuples: JSON. Empty address → zero address.
              </div>
              {(getFunctions(connectAbi) || [])
                .filter(
                  (f) =>
                    (f.stateMutability === 'view' || f.stateMutability === 'pure') &&
                    (!connectFnFilter.trim() ||
                      (f.name && f.name.toLowerCase().includes(connectFnFilter.trim().toLowerCase())))
                )
                .map((fn, fnIndex) => {
                  const inputs = fn.inputs || [];
                  return (
                    <div
                      key={`read-${fn.name}-${fnIndex}`}
                      style={{ marginBottom: '1rem', padding: '0.75rem', background: '#0f172a', borderRadius: '0.35rem', border: '1px solid #334155' }}
                    >
                      <div style={{ fontSize: '0.9rem', color: '#93c5fd', marginBottom: '0.5rem', fontFamily: 'monospace' }}>
                        {fn.name}({inputs.map((i) => i.name || i.type).join(', ')}) → {fn.outputs?.map((o) => o.type || o.internalType).join(', ') || '?'}
                      </div>
                      {inputs.length > 0 && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          {inputs.map((inp, i) => (
                            <input
                              key={i}
                              placeholder={(inp.name || `arg${i}`) + (inp.type ? ` (${inp.type})` : '')}
                              id={`read-${fnIndex}-${i}`}
                              style={{
                                width: '100%',
                                padding: '0.4rem 0.5rem',
                                marginBottom: '0.5rem',
                                background: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '0.25rem',
                                color: '#e2e8f0',
                                fontSize: '0.85rem',
                                fontFamily: 'monospace'
                              }}
                            />
                          ))}
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            const args = inputs.map((inp, i) =>
                              parseAbiArgInput(inp, document.getElementById(`read-${fnIndex}-${i}`)?.value)
                            );
                            await handleCall(fn, true, args);
                          } catch (err) {
                            setCallResult('❌ ' + (err instanceof Error ? err.message : String(err)));
                          }
                        }}
                        disabled={calling}
                        style={{
                          padding: '0.4rem 1rem',
                          background: calling ? '#475569' : '#3b82f6',
                          color: 'white',
                          border: 'none',
                          borderRadius: '0.35rem',
                          cursor: calling ? 'not-allowed' : 'pointer',
                          fontSize: '0.85rem',
                          fontWeight: 'bold'
                        }}
                      >
                        {calling ? 'Querying...' : 'Query'}
                      </button>
                    </div>
                  );
                })}
              {(getFunctions(connectAbi) || []).filter((f) => f.stateMutability === 'view' || f.stateMutability === 'pure').length === 0 && (
                <div style={{ color: '#64748b', fontSize: '0.85rem' }}>No read functions in this ABI (or select template / paste ABI).</div>
              )}
            </div>
          )}

          {connectMode === 'write' && (
            <div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.75rem' }}>
                Write functions (wallet + gas). <strong style={{ color: '#cbd5e1' }}>Payable</strong>: set ETH on the line below the args.
              </div>
              {(getFunctions(connectAbi) || [])
                .filter(
                  (f) =>
                    f.stateMutability !== 'view' &&
                    f.stateMutability !== 'pure' &&
                    (!connectFnFilter.trim() ||
                      (f.name && f.name.toLowerCase().includes(connectFnFilter.trim().toLowerCase())))
                )
                .map((fn, fnIndex) => {
                  const inputs = fn.inputs || [];
                  const payable = fn.stateMutability === 'payable';
                  return (
                    <div
                      key={`write-${fn.name}-${fnIndex}`}
                      style={{ marginBottom: '1rem', padding: '0.75rem', background: '#0f172a', borderRadius: '0.35rem', border: '1px solid #334155' }}
                    >
                      <div style={{ fontSize: '0.9rem', color: '#fbbf24', marginBottom: '0.5rem', fontFamily: 'monospace' }}>
                        {fn.name}({inputs.map((i) => i.name || i.type).join(', ')})
                        {payable ? ' payable' : ''}
                      </div>
                      {inputs.length > 0 && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          {inputs.map((inp, i) => (
                            <input
                              key={i}
                              placeholder={(inp.name || `arg${i}`) + (inp.type ? ` (${inp.type})` : '')}
                              id={`write-${fnIndex}-${i}`}
                              style={{
                                width: '100%',
                                padding: '0.4rem 0.5rem',
                                marginBottom: '0.5rem',
                                background: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '0.25rem',
                                color: '#e2e8f0',
                                fontSize: '0.85rem',
                                fontFamily: 'monospace'
                              }}
                            />
                          ))}
                        </div>
                      )}
                      {payable && (
                        <input
                          id={`write-pay-${fnIndex}`}
                          placeholder="ETH to send (e.g. 0.1) — payable only"
                          style={{
                            width: '100%',
                            padding: '0.4rem 0.5rem',
                            marginBottom: '0.5rem',
                            background: '#1e293b',
                            border: '1px solid #78350f',
                            borderRadius: '0.25rem',
                            color: '#fde68a',
                            fontSize: '0.85rem',
                            fontFamily: 'monospace'
                          }}
                        />
                      )}
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            const args = inputs.map((inp, i) =>
                              parseAbiArgInput(inp, document.getElementById(`write-${fnIndex}-${i}`)?.value)
                            );
                            const valueEth =
                              payable && document.getElementById(`write-pay-${fnIndex}`)?.value
                                ? String(document.getElementById(`write-pay-${fnIndex}`).value)
                                : '';
                            await handleCall(fn, false, args, { valueEth });
                          } catch (err) {
                            setCallResult('❌ ' + (err instanceof Error ? err.message : String(err)));
                          }
                        }}
                        disabled={calling || !wallet?.signer}
                        style={{
                          padding: '0.4rem 1rem',
                          background: calling || !wallet?.signer ? '#475569' : '#f59e0b',
                          color: 'white',
                          border: 'none',
                          borderRadius: '0.35rem',
                          cursor: calling || !wallet?.signer ? 'not-allowed' : 'pointer',
                          fontSize: '0.85rem',
                          fontWeight: 'bold'
                        }}
                      >
                        {calling ? 'Sending...' : 'Write'}
                      </button>
                    </div>
                  );
                })}
              {(getFunctions(connectAbi) || []).filter((f) => f.stateMutability !== 'view' && f.stateMutability !== 'pure').length === 0 && (
                <div style={{ color: '#64748b', fontSize: '0.85rem' }}>No write functions in this ABI.</div>
              )}
            </div>
          )}

          <div style={{ marginTop: '1.25rem', marginBottom: '1.25rem', padding: '1rem', background: '#0f172a', borderRadius: '0.5rem', border: '1px solid #334155', minHeight: '60px' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Call result</div>
            <pre style={{ margin: 0, color: callResult?.startsWith('❌') ? '#fca5a5' : '#86efac', fontSize: '0.9rem', overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {callResult || '—'}
            </pre>
          </div>

          <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#020617', borderRadius: '0.5rem', border: '1px solid #334155' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#e2e8f0', fontSize: '0.9rem' }}>Recent events (~5000 blocks)</div>
            <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.75rem' }}>
              Picks up to 25 newest logs. Overloaded events may need the console.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
              <select
                value={eventName}
                onChange={(e) => setEventName(e.target.value)}
                style={{ flex: 1, minWidth: '180px', padding: '0.45rem', background: '#1e293b', border: '1px solid #475569', borderRadius: '0.35rem', color: '#e2e8f0' }}
              >
                {(connectAbi || [])
                  .filter((x) => x.type === 'event' && x.name)
                  .map((ev) => (
                    <option key={ev.name} value={ev.name}>
                      {ev.name}
                    </option>
                  ))}
              </select>
              <button
                type="button"
                onClick={() => void handleQueryEvents()}
                disabled={eventLoading || !provider || !connectAbi?.length}
                style={{
                  padding: '0.45rem 0.9rem',
                  background: eventLoading || !provider ? '#475569' : '#6366f1',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.35rem',
                  cursor: eventLoading || !provider ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                  fontSize: '0.85rem'
                }}
              >
                {eventLoading ? 'Querying…' : 'Query logs'}
              </button>
            </div>
            {eventPreview && (
              <pre style={{ margin: 0, color: '#94a3b8', fontSize: '0.8rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '220px', overflow: 'auto' }}>
                {eventPreview}
              </pre>
            )}
          </div>
        </div>
      )}

      <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '1rem' }}>
        <strong>Any contract:</strong> Use <strong>Paste ABI</strong> with the <code>abi</code> array from <code>artifacts/…/Contract.json</code>, or pick <strong>PoS Simulator</strong> for the class lab contract. <strong>My contract</strong> uses the last Write-tab compile.
      </div>
    </div>
  );
}

export default ContractLab;
