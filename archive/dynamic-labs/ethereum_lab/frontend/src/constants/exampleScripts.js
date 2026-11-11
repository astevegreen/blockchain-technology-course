/**
 * Example scripts for Contract Lab → Example Scripts → Load.
 * Pasted into Hardhat console (Lab Terminal). Repo root = project root.
 *
 * PoS ABI: try artifacts (after compile), then ./abi/PoS.json (Docker image), then
 * ./frontend/src/PoS.json (full checkout). Same contract as Live → Connection Setup.
 * When `livePosAddress` is passed from the app, it is embedded so students need not paste.
 */

import { ethers } from 'ethers';

const POS_ADDR_HINT =
  "Replace PASTE_POSE_ADDRESS with your PoS address from Live → Connection Setup (42 chars, 0x…).";

const POS_ABI_MISSING_HINT =
  "PoS ABI not found. From project root run: npx hardhat compile. Lab Docker includes ./abi/PoS.json; full repo can use ./frontend/src/PoS.json.";

const PLACEHOLDER_POS = 'PASTE_POSE_ADDRESS';

/** Generic placeholder when no address is available to embed (bytecode + SimpleStorage scripts). */
const PLACEHOLDER_CONTRACT = 'PASTE_CONTRACT_ADDRESS';

const BYTECODE_TARGET_HINT =
  'Enter a classmate contract address in Contract Lab (Script 4 field), or set Live → Connection Setup (defaults to PoS), or replace PASTE_CONTRACT_ADDRESS with a full 0x… (42 chars).';

const SIMPLE_STORAGE_TARGET_HINT =
  'Enter Script 6 address in Contract Lab, or Deploy SimpleStorage / set Connect & Interact, then Load again — or replace PASTE_CONTRACT_ADDRESS with your SimpleStorage 0x… (42 chars).';

/** @param {string | undefined | null} addr */
function embedOrPlaceholder(addr, placeholder) {
  return addr && ethers.isAddress(addr) ? addr : placeholder;
}

/** @param {string | undefined | null} livePosAddress - from Live → Connection Setup when set */
function posSetupLines(livePosAddress) {
  const raw =
    livePosAddress && ethers.isAddress(livePosAddress) ? livePosAddress : PLACEHOLDER_POS;
  return `let PoSABI;
try {
  PoSABI = require('./artifacts/contracts/PoS.sol/PoSSimulator.json').abi;
} catch (_e) {
  try {
    const _raw = require('./abi/PoS.json');
    PoSABI = Array.isArray(_raw) ? _raw : _raw.abi;
  } catch (_e2) {
    try {
      const _raw = require('./frontend/src/PoS.json');
      PoSABI = Array.isArray(_raw) ? _raw : _raw.abi;
    } catch (_e3) {
      throw new Error(${JSON.stringify(POS_ABI_MISSING_HINT)});
    }
  }
}
if (!Array.isArray(PoSABI) || PoSABI.length === 0) throw new Error(${JSON.stringify(POS_ABI_MISSING_HINT)});
const _rawPos = ${JSON.stringify(raw)};
if (!/^0x[a-fA-F0-9]{40}$/.test(_rawPos.trim())) throw new Error(${JSON.stringify(POS_ADDR_HINT)});
// Hardhat's provider does not implement ENS resolveName(); ethers v6 only skips that if the
// target is a normalized hex address — trim + getAddress avoids mistaken ENS resolution.
const posAddress = ethers.getAddress(_rawPos.trim());`;
}

/**
 * @param {string | object | undefined | null} livePosAddressOrOpts
 *   Shorthand: pass a string (PoS address) for backward compatibility.
 *   Preferred: `{ livePosAddress, labClassmateBytecodeAddress, labScriptSixAddress, labDeployedAddress, labConnectAddress }` from Contract Lab.
 */
export function getExampleScripts(livePosAddressOrOpts) {
  const opts =
    livePosAddressOrOpts === undefined || livePosAddressOrOpts === null
      ? {}
      : typeof livePosAddressOrOpts === 'object' && !Array.isArray(livePosAddressOrOpts)
        ? livePosAddressOrOpts
        : { livePosAddress: livePosAddressOrOpts };
  const {
    livePosAddress,
    labClassmateBytecodeAddress,
    labScriptSixAddress,
    labDeployedAddress,
    labConnectAddress
  } = opts;

  const setup = () => posSetupLines(livePosAddress);
  // Script 4: classmate field wins; else PoS from Connection Setup; else placeholder.
  const classmateTrim = (labClassmateBytecodeAddress || '').trim();
  const bytecodePick =
    classmateTrim && ethers.isAddress(classmateTrim)
      ? classmateTrim
      : livePosAddress && ethers.isAddress(livePosAddress)
        ? livePosAddress
        : null;
  const bytecodeTargetRaw = embedOrPlaceholder(bytecodePick, PLACEHOLDER_CONTRACT);
  // Script 6: explicit field first, then last deploy, then Connect tab.
  const scriptSixTrim = (labScriptSixAddress || '').trim();
  const simpleStoragePick =
    scriptSixTrim && ethers.isAddress(scriptSixTrim)
      ? scriptSixTrim
      : labDeployedAddress && ethers.isAddress(labDeployedAddress)
        ? labDeployedAddress
        : labConnectAddress && ethers.isAddress(labConnectAddress)
          ? labConnectAddress
          : null;
  const simpleStorageTargetRaw = embedOrPlaceholder(simpleStoragePick, PLACEHOLDER_CONTRACT);

  return [
  {
    name: '1. Verify connection',
    description: 'Check you can read from the PoS contract',
    code: `${setup()}
const posC = new ethers.Contract(posAddress, PoSABI, ethers.provider);
const [total, epoch] = await Promise.all([posC.totalStaked(), posC.currentEpoch()]);
if (total == null || epoch == null) throw new Error('Unexpected null from PoS — wrong contract address or not a PoS deployment?');
\`✓ Connected! Total staked: \${ethers.formatEther(total)} ETH, Epoch: \${String(epoch)}\``
  },
  {
    name: '2. Check my balance',
    description: 'Get the default Hardhat account balance',
    code: `const [signer] = await ethers.getSigners();
const bal = await ethers.provider.getBalance(signer.address);
\`Your balance: \${ethers.formatEther(bal)} ETH (\${signer.address})\``
  },
  {
    name: '3. Read total staked',
    description: 'Get network staking stats',
    code: `${setup()}
const posC = new ethers.Contract(posAddress, PoSABI, ethers.provider);
const total = await posC.totalStaked();
const count = await posC.getValidatorCount();
\`Total staked: \${ethers.formatEther(total)} ETH across \${count} validators\``
  },
  {
    name: '4. Connect to a classmate\'s contract',
    description: 'Read bytecode — use Script 4 field below for a classmate, or defaults to PoS',
    code: `const _rawBytecode = ${JSON.stringify(bytecodeTargetRaw)};
if (!/^0x[a-fA-F0-9]{40}$/.test(_rawBytecode.trim())) throw new Error(${JSON.stringify(BYTECODE_TARGET_HINT)});
const _bcAddr = ethers.getAddress(_rawBytecode.trim());
const code = await ethers.provider.getCode(_bcAddr);
let _bytecodeResult;
if (!code || code === '0x') {
  _bytecodeResult = 'No contract at that address';
} else {
  _bytecodeResult = 'Contract exists at ' + _bcAddr.slice(0, 10) + '...';
}
_bytecodeResult`
  },
  {
    name: '5. List recent chat senders',
    description: 'Recent NewMessage events on PoS',
    code: `${setup()}
const posC = new ethers.Contract(posAddress, PoSABI, ethers.provider);
const latest = await ethers.provider.getBlockNumber();
const from = Math.max(0, latest - 1000);
const events = await posC.queryFilter(posC.filters.NewMessage(), from, latest);
const senders = [...new Set(events.map((e) => e.args[0]))];
\`\${senders.length} participants: \${senders.slice(0, 5).map((a) => a.slice(0, 10) + '...').join(', ')}\``
  },
  {
    name: '6. Call view on custom contract',
    description: 'Read SimpleStorage get/owner — use Script 6 field, or Deploy / Connect',
    code: `const _ssRaw = ${JSON.stringify(simpleStorageTargetRaw)};
if (!/^0x[a-fA-F0-9]{40}$/.test(_ssRaw.trim())) throw new Error(${JSON.stringify(SIMPLE_STORAGE_TARGET_HINT)});
const _ssAddr = ethers.getAddress(_ssRaw.trim());
const _ssAbi = ['function get() view returns (uint256)', 'function owner() view returns (address)'];
const _ssCtr = new ethers.Contract(_ssAddr, _ssAbi, ethers.provider);
const [_ssVal, _ssOwner] = await Promise.all([_ssCtr.get(), _ssCtr.owner()]);
\`Value: \${_ssVal}, Owner: \${_ssOwner}\``
  }
  ];
}

/** Default scripts (placeholder PoS address — prefer getExampleScripts from Contract Lab when Live address is known). */
export const EXAMPLE_SCRIPTS = getExampleScripts(undefined);
