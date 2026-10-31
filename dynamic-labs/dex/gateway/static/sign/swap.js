// The swap page: a swap on L1, a bridge deposit, and the wait for L2, each call built, signed and
// sent in plain sight, plus the worksheet's read-only questions asked with eth_call. Every node
// call goes through rpc() so the log shows the whole conversation with both nodes.
"use strict";

// Anvil's public test phrase. Accounts 10..49 hold 100 ETH at genesis; seat N uses 9 + N.
const PHRASE = "test test test test test test test test test test test junk";
const L1 = { path: "/rpc", chainId: 31337n };
const L2 = { path: "/rpc-l2", chainId: 31338n };
// The contracts chain/build-chain.sh created (chain/addresses.env; the tests check they match).
const DOLLAR = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
const WETH = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";
const PAIR = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0";
const ROUTER = "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9";
const BRIDGE = "0x7ef8E99980Da5bcEDcF7C10f41E55f759F6A174B"; // the same address on both chains
const BCUSD = "0x61Ab51bE7C866a54B0B442c149d7715367743EfD";
const AMOUNT_IN = ethers.parseEther("0.1");
const token = new ethers.Interface([
  "function balanceOf(address) view returns (uint256)",
  "function approve(address spender, uint256 value) returns (bool)",
  "function isBlackListed(address) view returns (bool)",
  "function owner() view returns (address)",
  "function totalSupply() view returns (uint256)",
]);
const pair = new ethers.Interface(["function getReserves() view returns (uint112, uint112, uint32)"]);
const router = new ethers.Interface([
  "function getAmountsOut(uint256 amountIn, address[] path) view returns (uint256[])",
  "function swapExactETHForTokens(uint256 amountOutMin, address[] path, address to, uint256 deadline) payable returns (uint256[])",
]);
const bridge = new ethers.Interface([
  "function depositERC20To(address l1Token, address to, uint256 amount) returns (uint256)",
  "function owner() view returns (address)",
  "function relayer() view returns (address)",
  "function paused() view returns (bool)",
  "function nextDepositId() view returns (uint256)",
  "function processed(uint256) view returns (bool)",
  "event DepositInitiated(uint256 indexed depositId, address indexed l1Token, address indexed from, address to, uint256 amount)",
  "event DepositFinalized(uint256 indexed depositId, address indexed from, address indexed to, uint256 amount)",
]);
const $ = (id) => document.getElementById(id);
const l2Origin = location.protocol + "//" + location.host.replace(/^dex\./, "dex-l2.");
$("l2-home").href = l2Origin + "/";

let wallet = null;
let quote = 0n;
let received = 0n;
let callId = 0;

async function rpc(chain, method, params) {
  const body = { jsonrpc: "2.0", id: ++callId, method, params };
  const entry = document.createElement("li");
  entry.textContent = `→ ${chain.path} ${method} ${JSON.stringify(params)}`;
  $("log").append(entry);
  const reply = await fetch(chain.path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => r.json());
  const answer = document.createElement("div");
  answer.textContent = "← " + JSON.stringify(reply.error ?? reply.result);
  entry.append(answer);
  if (reply.error) throw new Error(reply.error.message);
  return reply.result;
}

async function call(chain, to, iface, fn, args = []) {
  const raw = await rpc(chain, "eth_call", [{ to, data: iface.encodeFunctionData(fn, args) }, "latest"]);
  return iface.decodeFunctionResult(fn, raw);
}

function rows(table, pairs) {
  table.replaceChildren();
  for (const [name, value] of pairs) {
    const tr = table.insertRow();
    const th = document.createElement("th");
    th.textContent = name;
    tr.append(th);
    const cell = tr.insertCell();
    if (value instanceof Node) {
      cell.append(value);
    } else {
      const code = document.createElement("code");
      code.textContent = value;
      cell.append(code);
    }
  }
  table.hidden = false;
}

function link(origin, hash) {
  return Object.assign(document.createElement("a"), { href: `${origin}/tx/${hash}`, textContent: hash });
}

function say(text) {
  $("status").textContent = text;
}

const cusd = (v) => `${ethers.formatUnits(v, 6)} cUSD`;
const pause = (ms) => new Promise((done) => setTimeout(done, ms));

// cUSD per WETH: the pool's cUSD reserve over its WETH reserve. cUSD is token 0 (the lower address).
async function price() {
  const [r0, r1] = await call(L1, PAIR, pair, "getReserves");
  return Number(ethers.formatUnits(r0, 6)) / Number(ethers.formatEther(r1));
}

// Sign and send one transaction, then wait for its block. Returns the receipt.
async function send(chain, to, data, value, gas, nonce) {
  const block = await rpc(chain, "eth_getBlockByNumber", ["latest", false]);
  const tip = ethers.parseUnits("1", "gwei");
  const tx = ethers.Transaction.from({
    type: 2, chainId: chain.chainId, nonce, to, value, data, gasLimit: gas,
    maxPriorityFeePerGas: tip, maxFeePerGas: 2n * BigInt(block.baseFeePerGas) + tip,
  });
  tx.signature = wallet.signingKey.sign(tx.unsignedHash);
  const hash = await rpc(chain, "eth_sendRawTransaction", [tx.serialized]);
  say(`Sent ${hash}. Waiting for the next block (L1 seals one every 12 seconds)...`);
  let receipt = null;
  while (!receipt) {
    await pause(2000);
    receipt = await rpc(chain, "eth_getTransactionReceipt", [hash]);
  }
  if (receipt.status !== "0x1") throw new Error(`${hash} failed in block ${BigInt(receipt.blockNumber)}`);
  return receipt;
}

async function nonce() {
  return Number(await rpc(L1, "eth_getTransactionCount", [wallet.address, "pending"]));
}

async function showAccount() {
  const [eth, dollars, bridged] = await Promise.all([
    rpc(L1, "eth_getBalance", [wallet.address, "latest"]),
    call(L1, DOLLAR, token, "balanceOf", [wallet.address]),
    call(L2, BCUSD, token, "balanceOf", [wallet.address]),
  ]);
  rows($("account"), [
    ["Address (the same on both chains)", wallet.address],
    ["L1: ETH", ethers.formatEther(eth) + " ETH"],
    ["L1: cUSD", cusd(dollars[0])],
    ["L2: bcUSD", ethers.formatUnits(bridged[0], 6) + " bcUSD"],
  ]);
}

function guard(fn) {
  return async () => {
    try {
      await fn();
    } catch (err) {
      say("Stopped: " + (err.shortMessage || err.message));
    }
  };
}

$("load").addEventListener("click", guard(async () => {
  const seat = Number($("seat").value);
  if (!Number.isInteger(seat) || seat < 1 || seat > 40) throw new Error("enter a seat number from 1 to 40");
  wallet = ethers.HDNodeWallet.fromPhrase(PHRASE, undefined, `m/44'/60'/0'/0/${9 + seat}`);
  await showAccount();
  $("quote").disabled = false;
  say("");
}));

$("quote").addEventListener("click", guard(async () => {
  const [amounts] = await call(L1, ROUTER, router, "getAmountsOut", [AMOUNT_IN, [WETH, DOLLAR]]);
  quote = amounts[1];
  const now = await price();
  rows($("quoted"), [
    ["You pay", "0.1 ETH (the router wraps it into WETH)"],
    ["The router says you get", cusd(quote)],
    ["Your price", `${(Number(ethers.formatUnits(quote, 6)) / 0.1).toFixed(2)} cUSD per WETH`],
    ["The pool's price now (reserve ratio)", `${now.toFixed(2)} cUSD per WETH`],
  ]);
  $("build").disabled = false;
}));

let swapData = "";
$("build").addEventListener("click", guard(async () => {
  const block = await rpc(L1, "eth_getBlockByNumber", ["latest", false]);
  const deadline = BigInt(block.timestamp) + 600n; // ten minutes of chain time
  const min = (quote * 99n) / 100n;
  swapData = router.encodeFunctionData("swapExactETHForTokens", [min, [WETH, DOLLAR], wallet.address, deadline]);
  rows($("call"), [
    ["To (the router)", ROUTER],
    ["Value", "0.1 ETH"],
    ["Function", "swapExactETHForTokens(amountOutMin, path, to, deadline)"],
    ["amountOutMin (99% of the quote)", `${min} (${cusd(min)})`],
    ["path", `WETH ${WETH}, then cUSD ${DOLLAR}`],
    ["to", wallet.address],
    ["deadline", deadline.toString()],
    ["Input data (what the explorer shows)", swapData],
    ["Function selector (first 4 bytes)", swapData.slice(0, 10)],
  ]);
  $("swap").disabled = false;
}));

$("swap").addEventListener("click", guard(async () => {
  $("swap").disabled = true;
  const before = await price();
  const [start] = await call(L1, DOLLAR, token, "balanceOf", [wallet.address]);
  const receipt = await send(L1, ROUTER, swapData, AMOUNT_IN, 300000n, await nonce());
  const [end] = await call(L1, DOLLAR, token, "balanceOf", [wallet.address]);
  received = end - start;
  rows($("swapped"), [
    ["Transaction", link("", receipt.transactionHash)],
    ["Block", BigInt(receipt.blockNumber).toString()],
    ["cUSD received (your balance after minus before)", cusd(received)],
    ["The pool's price before your block", `${before.toFixed(2)} cUSD per WETH`],
    ["The pool's price now", `${(await price()).toFixed(2)} cUSD per WETH`],
  ]);
  say(`Swapped in block ${BigInt(receipt.blockNumber)}. Open the transaction to answer part 2 (a).`);
  await showAccount();
  $("bridge").disabled = false;
}));

$("bridge").addEventListener("click", guard(async () => {
  $("bridge").disabled = true;
  if (received === 0n) throw new Error("swap first: the page bridges the cUSD you bought");
  const n = await nonce();
  await send(L1, DOLLAR, token.encodeFunctionData("approve", [BRIDGE, received]), 0n, 100000n, n);
  const data = bridge.encodeFunctionData("depositERC20To", [DOLLAR, wallet.address, received]);
  const receipt = await send(L1, BRIDGE, data, 0n, 200000n, n + 1);
  const log = receipt.logs.map((l) => bridge.parseLog(l)).find((l) => l && l.name === "DepositInitiated");
  const id = log.args.depositId;
  rows($("deposited"), [
    ["Deposit transaction", link("", receipt.transactionHash)],
    ["L1 block", BigInt(receipt.blockNumber).toString()],
    ["Deposit number (from the DepositInitiated log)", id.toString()],
    ["Locked in the L1 bridge", cusd(log.args.amount)],
    ["To, on L2", log.args.to],
  ]);
  const sent = Date.now();
  say(`Deposit ${id} is on L1. Waiting for the relayer to finalize it on L2...`);
  while (!(await call(L2, BRIDGE, bridge, "processed", [id]))[0]) await pause(2000);
  // Find the L2 transaction: the bridge's latest transactions, read through Otterscan's own method.
  const page = await rpc(L2, "ots_searchTransactionsBefore", [BRIDGE, 0, 10]);
  const topic = ethers.toBeHex(id, 32);
  const done = page.receipts.find((r) => r.logs.some((l) => l.topics[0] === bridge.getEvent("DepositFinalized").topicHash && l.topics[1] === topic));
  const [bridged] = await call(L2, BCUSD, token, "balanceOf", [wallet.address]);
  rows($("arrived"), [
    ["L2 transaction", done ? link(l2Origin, done.transactionHash) : "not in the bridge's last 10"],
    ["L2 block", done ? BigInt(done.blockNumber).toString() : ""],
    ["Sent by (the relayer)", done ? ethers.getAddress(done.from) : ""],
    ["Your bcUSD on L2 now", ethers.formatUnits(bridged, 6) + " bcUSD"],
    ["Seconds this page waited", Math.round((Date.now() - sent) / 1000).toString()],
  ]);
  say(`Deposit ${id} is finalized on L2. Open both transactions to answer part 2 (b) and (c).`);
  await showAccount();
}));

// The worksheet's questions: [label, chain, contract, interface, function, takes an argument, format].
const QUESTIONS = [
  ["L1 cUSD: balanceOf(address)", L1, DOLLAR, token, "balanceOf", "address", cusd],
  ["L1 cUSD: totalSupply()", L1, DOLLAR, token, "totalSupply", null, cusd],
  ["L1 cUSD: owner() (the issuer)", L1, DOLLAR, token, "owner", null],
  ["L1 cUSD: isBlackListed(address)", L1, DOLLAR, token, "isBlackListed", "address"],
  ["L1 pool: getReserves() (cUSD, WETH, time)", L1, PAIR, pair, "getReserves", null],
  ["L1 bridge: owner()", L1, BRIDGE, bridge, "owner", null],
  ["L1 bridge: paused()", L1, BRIDGE, bridge, "paused", null],
  ["L1 bridge: nextDepositId()", L1, BRIDGE, bridge, "nextDepositId", null],
  ["L2 bcUSD: balanceOf(address)", L2, BCUSD, token, "balanceOf", "address", (v) => `${ethers.formatUnits(v, 6)} bcUSD`],
  ["L2 bcUSD: totalSupply()", L2, BCUSD, token, "totalSupply", null, (v) => `${ethers.formatUnits(v, 6)} bcUSD`],
  ["L2 bridge: owner()", L2, BRIDGE, bridge, "owner", null],
  ["L2 bridge: relayer()", L2, BRIDGE, bridge, "relayer", null],
  ["L2 bridge: paused()", L2, BRIDGE, bridge, "paused", null],
  ["L2 bridge: processed(deposit number)", L2, BRIDGE, bridge, "processed", "number"],
];
QUESTIONS.forEach(([label], i) => $("question").append(new Option(label, String(i))));

$("ask").addEventListener("click", async () => {
  const [label, chain, to, iface, fn, kind, format] = QUESTIONS[Number($("question").value)];
  try {
    const arg = $("arg").value.trim();
    const args = kind === "address" ? [ethers.getAddress(arg)] : kind === "number" ? [BigInt(arg)] : [];
    const data = iface.encodeFunctionData(fn, args);
    const raw = await rpc(chain, "eth_call", [{ to, data }, "latest"]);
    const result = iface.decodeFunctionResult(fn, raw);
    const value = result.length > 1 ? result.map(String).join(", ") : String(result[0]);
    rows($("answer"), [
      ["Asked", kind ? `${label.split("(")[0]}(${arg})` : label],
      ["Sent to", `${to} on ${chain === L1 ? "L1" : "L2"}`],
      ["Input data", data],
      ["Raw answer", raw],
      ["Decoded", format ? `${value} (${format(result[0])})` : value],
    ]);
  } catch (err) {
    rows($("answer"), [["No answer", err.shortMessage || err.message]]);
  }
});
