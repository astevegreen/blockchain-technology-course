#!/usr/bin/env node
/**
 * Beacon Chain Lab conductor.
 *
 * Drives a continuous, self-running Proof-of-Stake simulation so students can
 * drop in at any time and be seated within a few seconds:
 *   - starts a bots-only session if the contract is still in the lobby,
 *   - proposes a block on a fixed cadence (stake-weighted proposer, bots auto-attest),
 *   - keeps the validator pool full of bots (humans evict a bot when they join),
 *   - occasionally forks to demonstrate double-vote slashing, and
 *   - processes any pending slash evidence (whistleblower path).
 *
 * It uses the instructor key (Hardhat account #0 by default) and talks straight
 * to the local RPC, so it survives with no instructor browser tab open.
 *
 * Env:
 *   RPC_URL          default http://127.0.0.1:8545
 *   INSTRUCTOR_KEY   default Hardhat account #0 private key
 *   BEACON_BLOCK_MS  default 6000 (ms between proposed blocks; classroom-friendly slot cadence)
 *   BEACON_FORK_EVERY default 9 (propose a fork every N blocks for a slashing demo)
 */

const fs = require("fs");
const path = require("path");
const { ethers } = require("ethers");

const RPC_URL = process.env.RPC_URL || "http://127.0.0.1:8545";
// Hardhat account #0 (deployer == instructor) from the standard test mnemonic.
const INSTRUCTOR_KEY =
  process.env.INSTRUCTOR_KEY ||
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
const BLOCK_MS = parseInt(process.env.BEACON_BLOCK_MS || "6000", 10);
const FORK_EVERY = parseInt(process.env.BEACON_FORK_EVERY || "12", 10);
// Rotate slashed validators out (and fresh bots in) every few blocks so the slashing
// demo never accumulates past 1/3 of stake and stalls justification.
const ROTATE_EVERY = parseInt(process.env.BEACON_ROTATE_EVERY || "4", 10);
// Offer a human in the pool the proposer duty every Nth block, then wait this long for
// them to choose an MEV block before falling back to a bot (a "missed proposal").
const PROPOSE_HUMAN_EVERY = parseInt(process.env.BEACON_PROPOSE_HUMAN_EVERY || "3", 10);
const PROPOSAL_WINDOW_MS = parseInt(process.env.BEACON_PROPOSAL_WINDOW_MS || "15000", 10);
// If the human's proposal transaction is already sitting in the delayed-mining
// mempool, do not immediately fall back to a bot just because contract state has
// not changed yet. This avoids racing the classroom mining delay.
const PROPOSAL_PENDING_GRACE_MS = parseInt(process.env.BEACON_PROPOSAL_PENDING_GRACE_MS || "9000", 10);
const PROPOSAL_BUNDLES_PATH = process.env.BEACON_PROPOSAL_BUNDLES_PATH || "/tmp/beacon-proposal-bundles.json";
const MEMPOOL_STATE_URL = process.env.BEACON_MEMPOOL_STATE_URL || `http://127.0.0.1:${process.env.FRONTEND_PORT || "5173"}/mempool-state`;
const BUNDLE_MAX_TXS = Math.max(1, parseInt(process.env.BEACON_BUNDLE_MAX_TXS || "12", 10));
const BUNDLE_GAS_TARGET = BigInt(process.env.BEACON_BUNDLE_GAS_TARGET || "30000000");
// Explicit gas (skip estimateGas) for block-production txs so a student joining mid-tick
// can't make the conductor's gas estimate go stale and stall block production.
const TXOPTS = { gasLimit: 15_000_000n };
const MNEMONIC = "test test test test test test test test test test test junk";

const ROOT = path.join(__dirname, "..");
const CONFIG_PATH = path.join(ROOT, "frontend", "public", "beacon-lab-config.json");
const ABI_PATH = path.join(
  ROOT,
  "artifacts",
  "contracts",
  "BeaconChainLab.sol",
  "BeaconChainLab.json"
);

const log = (msg) => console.log(`[beacon-conductor] ${msg}`);

function loadJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function writeJsonAtomic(p, value) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  const tmp = `${p}.tmp`;
  fs.writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(tmp, p);
}

function hexToBigInt(value, fallback = 0n) {
  if (value == null) return fallback;
  try {
    if (typeof value === "bigint") return value;
    if (typeof value === "number" && Number.isFinite(value)) return BigInt(Math.max(0, Math.floor(value)));
    if (typeof value === "string" && value.trim()) return BigInt(value);
  } catch (_) {}
  return fallback;
}

function decimalUnitsToBigInt(value, decimals, fallback = 0n) {
  if (value == null) return fallback;
  try {
    if (typeof value === "bigint") return value;
    const raw = String(value).trim().replace(/,/g, "");
    if (!raw) return fallback;
    if (/^-?\d+$/.test(raw)) return BigInt(raw) * (10n ** BigInt(decimals));
    const match = raw.match(/^(-?)(\d*)\.(\d*)$/);
    if (!match) return fallback;
    const [, sign, wholeRaw, fracRaw] = match;
    const whole = wholeRaw ? BigInt(wholeRaw) : 0n;
    const fracText = fracRaw.slice(0, decimals).padEnd(decimals, "0");
    const frac = fracText ? BigInt(fracText) : 0n;
    const valueInt = whole * (10n ** BigInt(decimals)) + frac;
    return sign === "-" ? -valueInt : valueInt;
  } catch (_) {
    return fallback;
  }
}

function formatWei(value) {
  try { return ethers.formatEther(value); } catch (_) { return "0.0"; }
}

function formatGwei(value) {
  try { return ethers.formatUnits(value, "gwei"); } catch (_) { return "0"; }
}

function txDataOf(tx) {
  return String(tx?.input || tx?.data || "0x");
}

async function main() {
  const config = loadJson(CONFIG_PATH);
  const abi = loadJson(ABI_PATH).abi;
  const botAddresses = config.botAddresses || [];

  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const baseWallet = new ethers.Wallet(INSTRUCTOR_KEY, provider);
  // NonceManager tracks the nonce locally (incrementing per send) instead of
  // re-fetching "pending" each time — Hardhat's pending count can briefly lag a
  // just-mined tx, which caused "nonce has already been used". On any failure we
  // reset() so the next send re-syncs from chain. Combined with the serializer
  // below (one tx at a time), this keeps the single instructor account clean.
  const wallet = new ethers.NonceManager(baseWallet);
  const resetNonce = () => { try { wallet.reset(); } catch (_) {} };
  const contract = new ethers.Contract(config.contractAddress, abi, wallet);

  log(`contract ${config.contractAddress}`);
  log(`instructor ${baseWallet.address}, bots ${botAddresses.length}, cadence ${BLOCK_MS}ms`);

  // SINGLE SERIAL SENDER: only the tick loop sends transactions, and `tickRunning`
  // guarantees one tick at a time. Slash evidence is collected from events into a
  // queue and drained *inside* the tick — so every tx from the instructor account
  // goes out strictly one-at-a-time. With NonceManager tracking the nonce locally
  // (no re-fetching Hardhat's laggy "pending" count), nonces never collide.
  const pendingSlash = new Set();
  let lastActivityMs = Date.now(); // last time a student was seen active (drives idle pause)

  // Reset-safe event ingestion. We deliberately AVOID contract.on(...) filter subscriptions:
  // ethers v6 throws "results is not iterable" the moment an evm_revert (our prune) invalidates
  // the node's filter id — which spams the logs and can wedge the provider's poller. Instead we
  // poll queryFilter over the new-block range each tick; eth_getLogs has no persistent filter to
  // go stale across a prune.
  let lastEventBlock = await provider.getBlockNumber().catch(() => 0);
  async function pollContractEvents() {
    let head;
    try { head = await provider.getBlockNumber(); } catch (_) { return; }
    if (head < lastEventBlock) lastEventBlock = head; // chain was reverted (prune) — resync forward
    const from = lastEventBlock + 1;
    if (from > head) return;
    try {
      const slashLogs = await contract.queryFilter(contract.filters.SlashEvidenceSubmitted(), from, head);
      for (const lg of slashLogs) { if (lg.args && lg.args[0]) pendingSlash.add(lg.args[0]); }
      const joinLogs = await contract.queryFilter(contract.filters.Joined(), from, head);
      if (joinLogs.length) lastActivityMs = Date.now(); // a human joining = "student is here"
      lastEventBlock = head;
    } catch (_) {
      // transient (e.g. mid-revert) — retry next tick without advancing the cursor
    }
  }

  // Endless supply of fresh bot addresses (virtual stake, so they need no real ETH).
  // Start at a high derivation index to avoid student (#0-#7), bank (#9) and the
  // initial bot accounts (#10-#19+).
  let freshCursor = 1000;
  const freshBots = (n) => {
    const out = [];
    for (let k = 0; k < n; k++) {
      out.push(ethers.HDNodeWallet.fromPhrase(MNEMONIC, undefined, `m/44'/60'/0'/0/${freshCursor++}`).address);
    }
    return out;
  };

  async function ensureActive() {
    const state = Number(await contract.getSessionState());
    if (state === 0) {
      const tx = await contract.fillBotsAndStart(botAddresses, false);
      await tx.wait();
      log("session started (bots-only)");
      try {
        const t = await contract.setBotMisbehaviorChance(2, 5);
        await t.wait();
      } catch (e) {
        log(`setBotMisbehaviorChance warn: ${e.shortMessage || e.message}`);
      }
      try {
        // "Attest or lose stake": humans who skip their attestation duty leak a little.
        const t2 = await contract.setInactivityPenaltyEnabled(true);
        await t2.wait();
      } catch (e) {
        log(`setInactivityPenaltyEnabled warn: ${e.shortMessage || e.message}`);
      }
    } else if (state === 2) {
      log("session FINISHED; conductor idle");
      return false;
    }
    return true;
  }

  // Drain queued slash evidence. processSlash reverts harmlessly if the validator
  // was already processed/rotated out — that reverts at estimateGas, so no tx is
  // sent and no nonce is consumed.
  async function drainSlashes() {
    for (const v of [...pendingSlash]) {
      pendingSlash.delete(v);
      try {
        // Skip validators already processed or rotated out — calling processSlash on
        // them reverts at estimateGas, which silently drifts the NonceManager. A cheap
        // read avoids that entirely.
        if (!(await contract.hasPendingSlash(v))) continue;
        const tx = await contract.processSlash(v);
        await tx.wait();
        log(`processed slash for ${v.slice(0, 10)}...`);
      } catch (e) {
        resetNonce(); // a send raced a rotation — resync from chain
      }
    }
  }

  async function rotateSlashed() {
    const tx = await contract.rotateSlashed(freshBots(16));
    await tx.wait();
  }

  async function keepPoolFull() {
    const size = Number(await contract.getCommitteeSize());
    const poolSize = Number(await contract.getPoolSize());
    if (size < poolSize) {
      const tx = await contract.refillBots(botAddresses);
      await tx.wait();
    }
  }

  let active = await ensureActive();
  let blockCount = 0;
  let tickRunning = false;
  let proposalOpenedAtMs = 0; // wall-clock time we opened a human proposal slot
  let offerOpen = false;      // true while we're waiting on a human's proposal choice
  let proposalGraceLogged = false;
  const proposalSelector = ethers.id("proposeAsProposer(uint8)").slice(0, 10).toLowerCase();
  const contractAddress = String(config.contractAddress).toLowerCase();

  // Pick a human in the pool to offer the proposer duty to (varied by head block).
  async function pickHumanProposer() {
    try {
      const pool = await contract.getCommittee();
      const humans = [];
      for (const a of pool) {
        const s = await contract.getValidatorStats(a);
        if (!s[1] && s[0] > 0n) humans.push(a); // !isBot, has stake
      }
      if (humans.length === 0) return null;
      const head = await provider.getBlockNumber();
      return humans[head % humans.length];
    } catch { return null; }
  }

  async function hasPendingProposalChoice(proposer) {
    const expectedFrom = String(proposer || '').toLowerCase();
    if (!expectedFrom) return false;
    try {
      const pending = await provider.send('eth_getBlockByNumber', ['pending', true]);
      const txs = Array.isArray(pending?.transactions) ? pending.transactions : [];
      return txs.some((tx) => {
        if (!tx || typeof tx !== 'object') return false;
        const from = String(tx.from || '').toLowerCase();
        const to = String(tx.to || '').toLowerCase();
        const input = String(tx.input || tx.data || '').toLowerCase();
        return from === expectedFrom && to === contractAddress && input.startsWith(proposalSelector);
      });
    } catch (_) {
      return false;
    }
  }

  function normalizeBundleTx(tx, index) {
    if (!tx || typeof tx !== "object" || !tx.hash) return null;
    const hash = String(tx.hash).toLowerCase();
    if (!/^0x[0-9a-f]{64}$/.test(hash)) return null;
    const from = String(tx.from || "").toLowerCase();
    const to = tx.to ? String(tx.to).toLowerCase() : null;
    // The conductor's own Beacon txs are system traffic. They should not become
    // student-facing "bundle" candidates.
    if (from === baseWallet.address.toLowerCase() && to === contractAddress) return null;

    const gasLimit = hexToBigInt(tx.gas ?? tx.gasLimit, 0n);
    const gasPrice = tx.gasPriceGwei != null
      ? decimalUnitsToBigInt(tx.gasPriceGwei, 9, 0n)
      : hexToBigInt(tx.gasPrice ?? tx.maxFeePerGas ?? tx.maxPriorityFeePerGas, 0n);
    const feeWei = tx.estimatedFeeWei != null
      ? hexToBigInt(tx.estimatedFeeWei, gasLimit * gasPrice)
      : tx.estimatedFeeEth != null
        ? decimalUnitsToBigInt(tx.estimatedFeeEth, 18, gasLimit * gasPrice)
        : gasLimit * gasPrice;
    const data = txDataOf(tx);
    return {
      hash,
      from,
      to,
      nonce: tx.nonce == null ? null : Number(hexToBigInt(tx.nonce, 0n)),
      valueWei: tx.valueEth != null ? decimalUnitsToBigInt(tx.valueEth, 18, 0n) : hexToBigInt(tx.value ?? tx.valueWei, 0n),
      gasLimit,
      gasPrice,
      feeWei,
      selector: data && data !== "0x" && data.length >= 10 ? data.slice(0, 10).toLowerCase() : null,
      dataBytes: data && data !== "0x" ? Math.ceil((data.length - 2) / 2) : 0,
      observedIndex: index,
    };
  }

  async function pendingBundleTransactions() {
    let timeout = null;
    try {
      const controller = new AbortController();
      timeout = setTimeout(() => controller.abort(), 1200);
      const response = await fetch(MEMPOOL_STATE_URL, { signal: controller.signal });
      if (response.ok) {
        const state = await response.json();
        const txs = Array.isArray(state?.pendingTransactions) ? state.pendingTransactions : [];
        const normalized = txs
          .map((tx, index) => normalizeBundleTx(tx, index))
          .filter(Boolean)
          .slice(0, BUNDLE_MAX_TXS);
        if (normalized.length > 0) return normalized;
      }
    } catch (_) {
      // Fall through to direct pending-block sampling if the cache endpoint is not ready.
    } finally {
      if (timeout) clearTimeout(timeout);
    }
    try {
      const pending = await provider.send("eth_getBlockByNumber", ["pending", true]);
      const txs = Array.isArray(pending?.transactions) ? pending.transactions : [];
      return txs
        .map((tx, index) => normalizeBundleTx(tx, index))
        .filter(Boolean)
        .slice(0, BUNDLE_MAX_TXS);
    } catch (_) {
      return [];
    }
  }

  function chooseUnderGasTarget(ordered) {
    const out = [];
    let gasUsed = 0n;
    for (const tx of ordered) {
      const nextGas = gasUsed + tx.gasLimit;
      if (out.length > 0 && nextGas > BUNDLE_GAS_TARGET) continue;
      out.push(tx);
      gasUsed = nextGas;
    }
    return out.length ? out : ordered.slice(0, 1);
  }

  function bundleRoot(txs) {
    const payload = txs.map((tx) => tx.hash).join(":") || "empty";
    return ethers.id(payload);
  }

  function publicBundleTx(tx, position) {
    return {
      position,
      hash: tx.hash,
      from: tx.from,
      to: tx.to,
      nonce: tx.nonce,
      selector: tx.selector,
      valueEth: formatWei(tx.valueWei),
      gasLimit: tx.gasLimit.toString(),
      gasPriceGwei: formatGwei(tx.gasPrice),
      estimatedFeeEth: formatWei(tx.feeWei),
      dataBytes: tx.dataBytes,
      observedIndex: tx.observedIndex,
    };
  }

  function makeBundleCandidate(id, name, description, ordered) {
    const txs = chooseUnderGasTarget(ordered);
    const feeWei = txs.reduce((sum, tx) => sum + tx.feeWei, 0n);
    const gasLimit = txs.reduce((sum, tx) => sum + tx.gasLimit, 0n);
    const root = bundleRoot(txs);
    return {
      id,
      name,
      description,
      root,
      txCount: txs.length,
      feeWei,
      estimatedFeeEth: formatWei(feeWei),
      gasLimit: gasLimit.toString(),
      transactions: txs.map(publicBundleTx),
    };
  }

  function buildBundleCandidates(txs) {
    if (txs.length === 0) {
      return [{
        id: "empty",
        name: "Empty block",
        description: "No pending user transactions were visible when this proposal slot opened.",
        root: bundleRoot([]),
        txCount: 0,
        feeWei: 0n,
        estimatedFeeEth: "0.0",
        gasLimit: "0",
        transactions: [],
      }];
    }
    if (txs.length === 1) {
      return [makeBundleCandidate(
        "single-pending",
        "Single pending transaction",
        "Only one user transaction was pending, so there is only one realistic block candidate.",
        txs,
      )];
    }

    const orders = [
      {
        id: "observed-order",
        name: "Observed mempool order",
        description: "Preserve the order returned by the pending block cache.",
        txs: [...txs],
      },
      {
        id: "fee-max",
        name: "Highest fee first",
        description: "Sort by estimated fee contribution to maximize proposer revenue under the gas target.",
        txs: [...txs].sort((a, b) => (a.feeWei === b.feeWei ? a.observedIndex - b.observedIndex : (a.feeWei > b.feeWei ? -1 : 1))),
      },
      {
        id: "low-fee-first",
        name: "Lowest fee first",
        description: "Prioritize low-fee transactions first; useful for comparing revenue tradeoffs.",
        txs: [...txs].sort((a, b) => (a.feeWei === b.feeWei ? a.observedIndex - b.observedIndex : (a.feeWei < b.feeWei ? -1 : 1))),
      },
      {
        id: "reverse-order",
        name: "Reverse mempool order",
        description: "Reverse the observed ordering to show that ordering can change the candidate block.",
        txs: [...txs].reverse(),
      },
    ];

    const seen = new Set();
    const candidates = [];
    for (const order of orders) {
      const candidate = makeBundleCandidate(order.id, order.name, order.description, order.txs);
      const key = candidate.transactions.map((tx) => tx.hash).join(":");
      if (seen.has(key)) continue;
      seen.add(key);
      candidates.push(candidate);
      if (candidates.length >= 3) break;
    }
    return candidates.length ? candidates : [makeBundleCandidate("observed-order", "Observed mempool order", "Pending transactions in observed order.", txs)];
  }

  async function buildProposalBundles(proposer) {
    const pendingTxs = await pendingBundleTransactions();
    const candidates = buildBundleCandidates(pendingTxs).slice(0, 3);
    const paddedOptions = [0n, 0n, 0n];
    const paddedRoots = [ethers.ZeroHash, ethers.ZeroHash, ethers.ZeroHash];
    candidates.forEach((candidate, index) => {
      paddedOptions[index] = candidate.feeWei;
      paddedRoots[index] = candidate.root;
    });
    return {
      proposer,
      optionCount: candidates.length,
      options: paddedOptions,
      roots: paddedRoots,
      candidates,
      source: {
        pendingTxCount: pendingTxs.length,
        maxTxs: BUNDLE_MAX_TXS,
        gasTarget: BUNDLE_GAS_TARGET.toString(),
        capturedAt: new Date().toISOString(),
      },
    };
  }

  function bundleStoreKey(proposer, slot, roots) {
    return `${String(proposer).toLowerCase()}:${Number(slot)}:${roots.join(":").toLowerCase()}`;
  }

  function saveProposalBundles(slot, bundleSet) {
    const key = bundleStoreKey(bundleSet.proposer, slot, bundleSet.roots);
    const payload = {
      key,
      proposer: bundleSet.proposer,
      slot: Number(slot),
      optionCount: bundleSet.optionCount,
      roots: bundleSet.roots,
      options: bundleSet.options.map((v) => v.toString()),
      candidates: bundleSet.candidates.map((candidate, index) => ({
        ...candidate,
        choice: index,
        feeWei: candidate.feeWei.toString(),
      })),
      source: bundleSet.source,
      updatedAt: new Date().toISOString(),
    };
    writeJsonAtomic(PROPOSAL_BUNDLES_PATH, payload);
  }

  // ---- Chain pruning -------------------------------------------------------
  // The conductor mines a block every few seconds, so the Hardhat node's in-memory
  // chain (and the contract's blocks[] array) grow without bound and eventually take
  // the backend offline. We snapshot the clean post-bootstrap state and evm_revert
  // back to it — reclaiming node RAM + resetting the contract while KEEPING the same
  // contract addresses. Triggers: idle (no students) every 5 min, a hard size cap,
  // and an instructor "reset" button (signaled via a flag file the lab-api writes).
  const RESET_FLAG = '/tmp/beacon-reset-request';
  const AUTO_ACTIVITY_PATH = process.env.BEACON_AUTO_ACTIVITY_PATH || '/tmp/beacon-auto-activity.json';
  const LEGACY_TOKENIZATION_MODE_FLAG = '/tmp/tokenization-mode';
  const autoActivityEnabled = () => {
    try {
      if (!fs.existsSync(AUTO_ACTIVITY_PATH)) return true;
      const state = JSON.parse(fs.readFileSync(AUTO_ACTIVITY_PATH, 'utf8'));
      return state?.enabled !== false;
    } catch (_) {
      return true;
    }
  };
  try { fs.unlinkSync(LEGACY_TOKENIZATION_MODE_FLAG); } catch (_) {}
  let wasAutoActivity = autoActivityEnabled();
  const PRUNE_INTERVAL_MS = 5 * 60 * 1000;
  const AUTO_PRUNE = String(process.env.BEACON_AUTO_PRUNE || '0') === '1';
  const HARD_CAP_BLOCKS = parseInt(process.env.BEACON_PRUNE_HARD_CAP || '0', 10);
  const SCAN_BLOCKS = 150;
  // Idle pause: stop producing blocks when no student has been active for a while, so the
  // node's in-memory chain doesn't grow during the (long) gaps between classes — that
  // unbounded idle growth is what drove the node to ~13GB and OOM-killed the host.
  const IDLE_PAUSE_MS = parseInt(process.env.BEACON_IDLE_PAUSE_MS || '180000', 10);
  const BANK_ADDR = '0xa0Ee7A142d267C1f36714E4a8F75612F20a79720'.toLowerCase();
  let snapshot = await provider.send('evm_snapshot', []);
  log(`prune snapshot taken (id ${snapshot}); hard cap ${HARD_CAP_BLOCKS} blocks`);

  async function poolHasHumans() {
    try {
      const pool = await contract.getCommittee();
      for (const a of pool) { const s = await contract.getValidatorStats(a); if (!s[1]) return true; } // !isBot
      return false;
    } catch { return true; } // on error, assume not idle (don't prune)
  }
  async function recentStudentActivity() {
    try {
      const head = await provider.getBlockNumber();
      const sys = new Set([baseWallet.address.toLowerCase(), BANK_ADDR]);
      for (let n = head; n > Math.max(0, head - SCAN_BLOCKS); n--) {
        const b = await provider.getBlock(n, true).catch(() => null);
        if (!b) continue;
        for (const t of (b.prefetchedTransactions || [])) {
          if (t.from && !sys.has(t.from.toLowerCase())) return true; // a non-system (student) tx
        }
      }
      return false;
    } catch { return true; }
  }
  // Cheap "is a student active right now?" check — scans only the last few blocks for a
  // non-system tx. Used by the idle-pause gate (the full 150-block scan is for pruning).
  async function studentActiveRecently() {
    try {
      const head = await provider.getBlockNumber();
      const sys = new Set([baseWallet.address.toLowerCase(), BANK_ADDR]);
      for (let n = head; n > Math.max(0, head - 25); n--) {
        const b = await provider.getBlock(n, true).catch(() => null);
        if (!b) continue;
        for (const t of (b.prefetchedTransactions || [])) {
          if (t.from && !sys.has(t.from.toLowerCase())) return true;
        }
      }
      return false;
    } catch { return true; } // on error, assume active (keep mining)
  }
  async function prune(reason) {
    if (tickRunning) return false; // let the in-flight tick finish; retry next cycle
    tickRunning = true; // also blocks ticks while we revert
    try {
      log(`pruning chain (${reason})...`);
      await provider.send('evm_revert', [snapshot]);
      snapshot = await provider.send('evm_snapshot', []); // evm_revert consumes it; re-take
      resetNonce();
      blockCount = 0;
      offerOpen = false;
      proposalGraceLogged = false;
      pendingSlash.clear();
      lastEventBlock = await provider.getBlockNumber().catch(() => 0); // resync event cursor to post-revert head
      active = await ensureActive(); // snapshot was post-bootstrap, so session is already ACTIVE
      log(`prune complete; head now ${await provider.getBlockNumber()}`);
      return true;
    } catch (e) {
      log(`prune warn: ${e.shortMessage || e.message}`);
      resetNonce();
      return false;
    } finally {
      tickRunning = false;
    }
  }
  async function maintenance() {
    const auto = autoActivityEnabled();
    if (auto !== wasAutoActivity) {
      log(auto ? 'auto beacon activity ON — synthetic blocks resumed' : 'auto beacon activity OFF — Beacon remains available, synthetic traffic paused');
      wasAutoActivity = auto;
    }
    try {
      if (fs.existsSync(RESET_FLAG)) { fs.unlinkSync(RESET_FLAG); await prune('instructor reset'); return; }
    } catch (_) {}
    const head = await provider.getBlockNumber().catch(() => 0);
    if (HARD_CAP_BLOCKS > 0 && head >= HARD_CAP_BLOCKS) await prune(`hard cap ${head} >= ${HARD_CAP_BLOCKS}`);
  }
  async function idlePrune() {
    if (!AUTO_PRUNE) return;
    const head = await provider.getBlockNumber().catch(() => 0);
    if (head < 50) return; // nothing meaningful to prune yet
    if (!(await poolHasHumans()) && !(await recentStudentActivity())) await prune('idle: no students');
  }

  const tick = async () => {
    if (tickRunning) return; // only one tick (one sender) at a time
    tickRunning = true;
    try {
      await pollContractEvents(); // refresh pendingSlash + lastActivityMs (reset-safe, no filters)
      if (!autoActivityEnabled()) return; // Beacon remains online; only synthetic conductor traffic pauses.
      if (!active) {
        active = await ensureActive();
        if (!active) return;
      }
      // Idle pause: if no student has been active for a while, stop producing blocks so the
      // node's in-memory chain (and RAM) doesn't grow during the long gaps between classes.
      // A cheap recent-tx recheck keeps mining alive while students are attesting/joining.
      if (Date.now() - lastActivityMs > IDLE_PAUSE_MS) {
        if (await studentActiveRecently()) lastActivityMs = Date.now();
        else return; // idle — produce no block this tick (maintenance + idlePrune still run)
      }
      await drainSlashes();

      // Human proposer duty: if a slot is currently open for a human, wait for them
      // to choose an MEV block. Only fall back (bot proposes + miss penalty) once the
      // window has elapsed. proposeBlock() itself clears the pending slot + penalizes.
      const ps = await contract.getProposalState(); // [pending, proposer, slot, options]
      if (ps[0]) {
        const elapsed = Date.now() - proposalOpenedAtMs;
        if (elapsed >= PROPOSAL_WINDOW_MS) {
          const missed = ps[1];
          if (elapsed < PROPOSAL_WINDOW_MS + PROPOSAL_PENDING_GRACE_MS) {
            const pendingChoice = await hasPendingProposalChoice(missed);
            if (!proposalGraceLogged) {
              log(pendingChoice
                ? `proposal choice pending for ${missed.slice(0, 10)} — waiting for delayed mining`
                : `proposal window elapsed for ${missed.slice(0, 10)} — grace period before bot fallback`);
              proposalGraceLogged = true;
            }
            return;
          }
          if (await hasPendingProposalChoice(missed)) {
            log(`proposal choice pending for ${missed.slice(0, 10)} — waiting for delayed mining`);
            return;
          }
          await (await contract.proposeBlock(TXOPTS)).wait(); // fallback: penalizes the miss
          blockCount++;
          offerOpen = false;
          proposalGraceLogged = false;
          log(`proposal window expired for ${missed.slice(0, 10)} — bot fallback proposed`);
          if (blockCount % ROTATE_EVERY === 0) await rotateSlashed();
        }
        return; // keep waiting for the human (don't produce a block this tick)
      }
      // The slot cleared while we were waiting → the human proposed their own block.
      // Count it and pause one tick so cadence holds, without re-offering immediately.
      if (offerOpen) {
        offerOpen = false;
        blockCount++;
        log('human proposed their block');
        if (blockCount % ROTATE_EVERY === 0) await rotateSlashed();
        return;
      }

      // No slot open. Periodically offer the proposer duty to a human (if one is in the
      // pool); otherwise the conductor proposes (bots) or forks for the slashing demo.
      const doFork = blockCount > 0 && blockCount % FORK_EVERY === 0;
      if (!doFork && blockCount > 0 && blockCount % PROPOSE_HUMAN_EVERY === 0) {
        const human = await pickHumanProposer();
        if (human) {
          const slot = Number(await contract.currentSlot());
          const bundleSet = await buildProposalBundles(human);
          await (await contract.openProposalSlotWithBundles(
            human,
            bundleSet.optionCount,
            bundleSet.options,
            bundleSet.roots,
            TXOPTS,
          )).wait();
          saveProposalBundles(slot, bundleSet);
          proposalOpenedAtMs = Date.now();
          offerOpen = true;
          proposalGraceLogged = false;
          log(`opened proposal slot for human ${human.slice(0, 10)} with ${bundleSet.optionCount} bundle option(s) (window ${PROPOSAL_WINDOW_MS}ms)`);
          return; // wait for the human to choose
        }
      }
      const tx = doFork ? await contract.proposeBlockFork(TXOPTS) : await contract.proposeBlock(TXOPTS);
      await tx.wait();
      blockCount++;
      if (blockCount % ROTATE_EVERY === 0) await rotateSlashed();
      if (blockCount % FORK_EVERY === 1) await keepPoolFull();
    } catch (e) {
      const m = e.shortMessage || e.message || String(e);
      // "could not coalesce error" is how ethers wraps a node nonce error — reset the
      // NonceManager so it re-syncs from chain on any nonce drift.
      if (/nonce|coalesce/i.test(m)) resetNonce();
      if (/Session not active|Not active/.test(m)) active = false;
      else log(`tick warn: ${m}`);
    } finally {
      tickRunning = false;
    }
  };

  setInterval(tick, BLOCK_MS);
  tick(); // kick off immediately

  setInterval(maintenance, 5000);          // fast: instructor reset flag + hard size cap
  setInterval(idlePrune, PRUNE_INTERVAL_MS); // every 5 min: prune if no students online
}

main().catch((err) => {
  console.error(`[beacon-conductor] fatal: ${err.message || err}`);
  process.exit(1);
});
