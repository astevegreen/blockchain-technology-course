// The Pool trading game page: each round the student works out what 1 ETH buys, picks the least they
// will accept, and the page sends their swap in their own block. Then they say whether they were
// sandwiched, and the page checks the call against the block itself. Every node call except the
// once-a-second block check goes through rpc() and shows in the log.
"use strict";

// Anvil's public test phrase. Accounts 10..49 hold 100 ETH at genesis; seat N uses 9 + N.
const PHRASE = "test test test test test test test test test test test junk";
const L1 = { path: "/rpc", chainId: 31337n };
// The contracts chain/build-chain.sh created (chain/addresses.env; the tests check they match).
const DOLLAR = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
const WETH = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";
const PAIR = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0";
const ROUTER = "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9";
// The instructor's account (Anvil's account 9). Its marker transaction opens each round:
// a transaction to itself whose input data reads "pool-trading round R seats F-L".
const INSTRUCTOR = "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720";
const MARKER = "pool-trading round ";
const AMOUNT_IN = ethers.parseEther("1");
const token = new ethers.Interface(["function balanceOf(address) view returns (uint256)"]);
const pair = new ethers.Interface([
  "function getReserves() view returns (uint112, uint112, uint32)",
  "event Swap(address indexed sender, uint256 amount0In, uint256 amount1In, uint256 amount0Out, uint256 amount1Out, address indexed to)",
]);
const router = new ethers.Interface([
  "function getAmountsOut(uint256 amountIn, address[] path) view returns (uint256[])",
  "function swapExactETHForTokens(uint256 amountOutMin, address[] path, address to, uint256 deadline) payable returns (uint256[])",
  "function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] path, address to, uint256 deadline) returns (uint256[])",
]);
const BUY = router.getFunction("swapExactETHForTokens").selector;
const SELL = router.getFunction("swapExactTokensForTokens").selector;
const $ = (id) => document.getElementById(id);
const cusd = (v) => `${Number(ethers.formatUnits(v, 6)).toLocaleString("en-US", { maximumFractionDigits: 2 })} cUSD`;
const pause = (ms) => new Promise((done) => setTimeout(done, ms));
const same = (a, b) => (a || "").toLowerCase() === (b || "").toLowerCase();

let wallet = null;
let seat = 0;
let round = null; // { number, marker, first, last }
let snapshot = null; // the reserves the student read: [cUSD, WETH]
let callId = 0;

async function rpc(chain, method, params, quiet = false) {
  const body = { jsonrpc: "2.0", id: ++callId, method, params };
  let entry = null;
  if (!quiet) {
    entry = document.createElement("li");
    entry.textContent = `→ ${chain.path} ${method} ${JSON.stringify(params)}`;
    $("log").append(entry);
  }
  const reply = await fetch(chain.path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => r.json());
  if (entry) {
    const answer = document.createElement("div");
    answer.textContent = "← " + JSON.stringify(reply.error ?? reply.result);
    entry.append(answer);
  }
  if (reply.error) throw new Error(reply.error.message);
  return reply.result;
}

async function call(to, iface, fn, args = [], block = "latest") {
  const raw = await rpc(L1, "eth_call", [{ to, data: iface.encodeFunctionData(fn, args) }, block]);
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

const link = (path, text) => Object.assign(document.createElement("a"), { href: path, textContent: text, target: "_blank" });
const say = (id, text, kind) => { $(id).textContent = text; $(id).className = kind || ""; };

async function latest() {
  return Number(await rpc(L1, "eth_blockNumber", [], true));
}

// Why a transaction reverted: the contract's require message, read through Otterscan's own method.
async function revertReason(hash) {
  const data = await rpc(L1, "ots_getTransactionError", [hash]);
  if (!data.startsWith("0x08c379a0")) return "no reason given";
  return ethers.AbiCoder.defaultAbiCoder().decode(["string"], "0x" + data.slice(10))[0];
}

// What the pool pays for amountIn: the router's getAmountOut, Uniswap v2's formula.
function amountOut(amountIn, reserveIn, reserveOut) {
  const withFee = amountIn * 997n;
  return (withFee * reserveOut) / (reserveIn * 1000n + withFee);
}

// ---- What this seat has done, per round, kept in this browser ----
const store = () => `pool-trading:seat:${seat}`;
function load() {
  try { return JSON.parse(localStorage.getItem(store())) || {}; } catch { return {}; }
}
function record(number) {
  return load()[number] || {};
}
function keep(number, part, value) {
  const all = load();
  all[number] = Object.assign(all[number] || {}, { [part]: value });
  try { localStorage.setItem(store(), JSON.stringify(all)); } catch { /* a private window keeps nothing */ }
  drawScore();
}

function drawScore() {
  const all = load();
  const table = $("score");
  table.replaceChildren();
  const head = table.insertRow();
  for (const h of ["Round", "Prediction", "Limit", "Call", "Total", "Call locked at"]) {
    const th = document.createElement("th");
    th.textContent = h;
    head.append(th);
  }
  let sum = 0;
  for (const number of Object.keys(all).sort()) {
    const r = all[number];
    const points = [r.predict?.score, r.limit?.score, r.call?.score];
    const total = points.reduce((a, b) => a + (b || 0), 0);
    sum += total;
    const tr = table.insertRow();
    for (const v of [number, ...points.map((p) => (p === undefined ? "" : String(p))), String(total),
      r.call ? new Date(r.call.at).toLocaleTimeString() : ""]) tr.insertCell().textContent = v;
  }
  const tr = table.insertRow();
  tr.insertCell().textContent = "All rounds";
  for (let i = 0; i < 3; i++) tr.insertCell();
  tr.insertCell().textContent = String(sum);
  tr.insertCell();
}

// ---- The round: found from the instructor's marker transaction ----
// Seat N trades in block marker + 1 + (N - first). If the instructor gave the round make-up turns (the marker
// ends "make-up"), a seat that missed its block has a second one, one round of seats later.
function turns() {
  const seats = round.last - round.first + 1;
  const turn = round.marker + 1 + seat - round.first;
  return { turn, makeUp: round.makeUp ? turn + seats : null, end: round.marker + (round.makeUp ? 2 : 1) * seats };
}
const plays = () => round && seat >= round.first && seat <= round.last;

// The newest marker: page back through the instructor's transactions with Otterscan's own search.
async function findRound() {
  let before = 0;
  for (let pages = 0; pages < 20; pages++) {
    const page = await rpc(L1, "ots_searchTransactionsBefore", [INSTRUCTOR, before, 25]);
    for (const tx of page.txs) {
      if (!same(tx.to, INSTRUCTOR)) continue;
      let text = "";
      try { text = ethers.toUtf8String(tx.input); } catch { continue; }
      if (!text.startsWith(MARKER)) continue;
      const [number, , span, extra] = text.slice(MARKER.length).split(" ");
      const [first, last] = span.split("-").map(Number);
      return { number: Number(number), marker: Number(tx.blockNumber), first, last, makeUp: extra === "make-up" };
    }
    if (page.lastPage || page.txs.length === 0) return null;
    before = Number(page.txs[page.txs.length - 1].blockNumber);
  }
  return null;
}

function setRound(found) {
  const changed = !round || !found || found.number !== round.number || found.marker !== round.marker;
  round = found;
  if (!changed) return;
  snapshot = null;
  for (const id of ["predict", "working", "why-limit", "before", "after", "why-call"]) $(id).value = "";
  for (const input of document.querySelectorAll("input[type=radio]")) input.checked = false;
  for (const id of ["predicted", "limited", "status", "called"]) say(id, "");
  for (const id of ["reserves", "traded"]) $(id).hidden = true;
  restore();
}

// Put back what this seat already locked this round, and open the next thing to do.
function restore() {
  const r = round ? record(round.number) : {};
  const open = plays();
  $("read").disabled = !open || !!r.predict;
  for (const id of ["predict", "working", "lock-predict"]) $(id).disabled = !open || !!r.predict || !snapshot;
  if (r.predict) say("predicted", predictText(r.predict), r.predict.score ? "good" : "bad");
  const limitOpen = open && !!r.predict && !r.limit;
  $("limits").disabled = !limitOpen;
  $("why-limit").disabled = !limitOpen;
  $("lock-limit").disabled = !limitOpen;
  if (r.limit) say("limited", limitText(r.limit), r.limit.score ? "good" : "bad");
  $("arm").disabled = !(open && r.limit && !r.trade);
  if (r.trade) showTrade(r.trade);
  const callOpen = open && !!r.trade && !r.call;
  for (const id of ["calls", "before", "after", "why-call", "lock-call"]) $(id).disabled = !callOpen;
  if (r.call) say("called", r.call.text, r.call.score > 0 ? "good" : "bad");
}

async function watchRounds() {
  let seen = null;
  for (;;) {
    try {
      const nonce = await rpc(L1, "eth_getTransactionCount", [INSTRUCTOR, "latest"], true);
      const now = await latest();
      if (nonce !== seen && (!round || now > turns().end)) {
        setRound(await findRound());
      }
      seen = nonce;
      drawRound(now);
    } catch (err) {
      say("round", "Cannot reach the node: " + err.message);
    }
    await pause(3000);
  }
}

function drawRound(now) {
  if (!round) {
    say("round", `Block ${now}. Waiting for your instructor to open a round.`);
    return;
  }
  const { turn, makeUp, end } = turns();
  const head = `Round ${round.number}: seats ${round.first} to ${round.last}, opened in block ${round.marker}. ` +
    `Now block ${now}. `;
  if (now > end) say("round", head + "This round is over. Wait for the next one.");
  else if (!plays()) say("round", head + `Your seat does not play this round; it ends after block ${end}.`);
  else say("round", head + `Your turn is block ${turn}` + (makeUp ? ` (make-up turn: block ${makeUp})` : "") +
    `. The round ends after block ${end}.`);
}

// ---- Step 3: the prediction ----
$("read").addEventListener("click", guard("predicted", async () => {
  const [dollars, weth] = await call(PAIR, pair, "getReserves");
  snapshot = [dollars, weth];
  rows($("reserves"), [
    ["x: WETH in the pool", ethers.formatEther(weth)],
    ["y: cUSD in the pool", ethers.formatUnits(dollars, 6)],
    ["a: what you put in", "1 WETH (the router wraps your 1 ETH)"],
    ["Read in block", String(await latest())],
  ]);
  restore();
}));

function predictText(p) {
  return `You said ${p.value} cUSD. The formula on the pool you read gives ${p.formula} cUSD. ` +
    (p.score ? "+1: within 1%, with your working." : "0: the point needs an answer within 1% of the formula, and your working.");
}

$("lock-predict").addEventListener("click", guard("predicted", async () => {
  const value = Number($("predict").value.replace(/,/g, ""));
  if (!Number.isFinite(value) || value <= 0) throw new Error("enter what 1 ETH buys, in cUSD");
  const formula = Number(ethers.formatUnits(amountOut(AMOUNT_IN, snapshot[1], snapshot[0]), 6));
  const working = $("working").value.trim();
  const score = Math.abs(value - formula) <= formula / 100 && working.length >= 3 ? 1 : 0;
  keep(round.number, "predict", { value, working, formula: formula.toFixed(2), score, at: Date.now() });
  restore();
}));

// ---- Step 4: the limit ----
const LIMITS = { 0: "none", 500: "5% below the quote", 50: "0.5% below the quote" };
function limitText(l) {
  return `Limit: ${LIMITS[l.bps]}. ` + (l.score ? "+1: a limit with its reason." : "0: the point needs a reason.");
}

$("lock-limit").addEventListener("click", guard("limited", async () => {
  const picked = document.querySelector("input[name=limit]:checked");
  if (!picked) throw new Error("pick a limit");
  const why = $("why-limit").value.trim();
  keep(round.number, "limit", { bps: Number(picked.value), why, score: why.length >= 3 ? 1 : 0, at: Date.now() });
  restore();
}));

// ---- Step 5: the trade, in the student's own block ----
$("arm").addEventListener("click", guard("status", async () => {
  $("arm").disabled = true;
  const number = round.number;
  const { turn, makeUp } = turns();
  let target = null;
  while (target === null) {
    const now = await latest();
    if (now === turn - 1) target = turn;
    else if (makeUp && now === makeUp - 1) target = makeUp;
    else if (!makeUp && now >= turn) throw new Error(`your turn, block ${turn}, has passed. Ask your instructor.`);
    else if (now >= makeUp) throw new Error(`your make-up turn, block ${makeUp}, has passed. Ask your instructor.`);
    else if (now >= turn) say("status", `Your turn, block ${turn}, has passed. Waiting for your make-up turn, block ${makeUp} (now block ${now})...`);
    else say("status", `Waiting for your turn, block ${turn} (now block ${now}). Keep this page open.`);
    if (target === null) await pause(1000);
  }
  const trade = await swap(number, target);
  keep(number, "trade", trade);
  restore();
}));

async function swap(number, target) {
  const bps = BigInt(record(number).limit.bps);
  const [amounts] = await call(ROUTER, router, "getAmountsOut", [AMOUNT_IN, [WETH, DOLLAR]]);
  const quote = amounts[1];
  const min = bps === 0n ? 0n : (quote * (10000n - bps)) / 10000n;
  const block = await rpc(L1, "eth_getBlockByNumber", ["latest", false]);
  const deadline = BigInt(block.timestamp) + 600n; // ten minutes of chain time
  const data = router.encodeFunctionData("swapExactETHForTokens", [min, [WETH, DOLLAR], wallet.address, deadline]);
  const tip = ethers.parseUnits("1", "gwei");
  const tx = ethers.Transaction.from({
    type: 2, chainId: L1.chainId, to: ROUTER, value: AMOUNT_IN, data, gasLimit: 300000n,
    nonce: Number(await rpc(L1, "eth_getTransactionCount", [wallet.address, "pending"])),
    maxPriorityFeePerGas: tip, maxFeePerGas: 2n * BigInt(block.baseFeePerGas) + tip,
  });
  tx.signature = wallet.signingKey.sign(tx.unsignedHash);
  const hash = await rpc(L1, "eth_sendRawTransaction", [tx.serialized]);
  say("status", `Sent ${hash} for block ${target}. Waiting for the block (one every 12 seconds)...`);
  let receipt = null;
  while (!receipt) {
    await pause(2000);
    receipt = await rpc(L1, "eth_getTransactionReceipt", [hash]);
  }
  const trade = { hash, block: Number(receipt.blockNumber), target, quote: String(quote), min: String(min),
    ok: receipt.status === "0x1", got: "0", reason: "" };
  if (trade.ok) {
    const swapLog = receipt.logs.map((l) => (same(l.address, PAIR) ? pair.parseLog(l) : null)).find((l) => l && l.name === "Swap");
    trade.got = String(swapLog.args.amount0Out);
  } else {
    trade.reason = await revertReason(hash);
  }
  say("status", "");
  return trade;
}

function showTrade(t) {
  const quote = BigInt(t.quote);
  const got = BigInt(t.got);
  rows($("traded"), [
    ["Your transaction", link(`/tx/${t.hash}`, t.hash)],
    ["Your block", link(`/block/${t.block}`, `${t.block}: open it and read the transactions in order`)],
    ["The router's quote when you sent", cusd(quote)],
    ["The least you would accept", t.min === "0" ? "nothing: no limit" : cusd(BigInt(t.min))],
    t.ok ? ["You received", `${cusd(got)} (${(Number((got * 10000n) / quote) / 100).toFixed(2)}% of the quote)`]
      : ["Refused", `"${t.reason}": you keep your 1 ETH, less the fee for the failed transaction`],
  ]);
}

// ---- Step 6: the call, checked against the block ----
async function truth(trade) {
  const block = await rpc(L1, "eth_getBlockByNumber", [ethers.toQuantity(trade.block), true]);
  const txs = block.transactions;
  const i = txs.findIndex((t) => same(t.hash, trade.hash));
  const before = txs[i - 1];
  const after = txs[i + 1];
  if (!before || !after || !same(before.from, after.from) || same(before.from, wallet.address)) return null;
  if (!same(before.to, ROUTER) || !same(after.to, ROUTER)) return null;
  if (!before.input.startsWith(BUY) || !after.input.startsWith(SELL)) return null;
  const [r1, r2] = await Promise.all([before.hash, after.hash].map((h) => rpc(L1, "eth_getTransactionReceipt", [h])));
  return r1.status === "0x1" && r2.status === "0x1" ? { before: before.hash, after: after.hash } : null;
}

$("lock-call").addEventListener("click", guard("called", async () => {
  const picked = document.querySelector("input[name=call]:checked");
  if (!picked) throw new Error("pick yes or no");
  const number = round.number;
  const sandwich = await truth(record(number).trade);
  let score = 0;
  let text = "";
  if (picked.value === "yes") {
    const before = $("before").value.trim();
    const after = $("after").value.trim();
    if (!sandwich) {
      score = -2;
      text = "−2: no one bought just before your trade and sold just after it, so there was no sandwich.";
    } else if (same(before, sandwich.before) && same(after, sandwich.after)) {
      score = 2;
      text = "+2: sandwiched, and those are the two transactions.";
    } else {
      text = "0: you were sandwiched, but those are not the transactions just before and just after yours.";
    }
  } else {
    const why = $("why-call").value.trim();
    if (sandwich) text = "0: you were sandwiched. Read the transactions just before and just after yours again.";
    else if (why.length < 3) text = "0: right, but the point needs your reason.";
    else { score = 2; text = "+2: no sandwich, with your reason."; }
  }
  keep(number, "call", { call: picked.value, score, text, at: Date.now() });
  restore();
}));

// ---- The class's balances: shown in seat order, never ranked ----
$("balances").addEventListener("click", guard("called", async () => {
  const [dollars, weth] = await call(PAIR, pair, "getReserves");
  const price = Number(ethers.formatUnits(dollars, 6)) / Number(ethers.formatEther(weth));
  const root = ethers.HDNodeWallet.fromPhrase(PHRASE, undefined, "m/44'/60'/0'/0");
  const table = $("class");
  table.replaceChildren();
  const head = table.insertRow();
  for (const h of ["Seat", "ETH", "cUSD", `Together, at the pool's price (${price.toFixed(2)} cUSD per ETH)`]) {
    const th = document.createElement("th");
    th.textContent = h;
    head.append(th);
  }
  for (let n = 1; n <= 40; n++) {
    const address = root.deriveChild(9 + n).address;
    const [eth, [held]] = await Promise.all([
      rpc(L1, "eth_getBalance", [address, "latest"]),
      call(DOLLAR, token, "balanceOf", [address]),
    ]);
    const ether = Number(ethers.formatEther(eth));
    const tr = table.insertRow();
    for (const v of [String(n), ether.toFixed(4), cusd(held), cusd(BigInt(Math.round((ether * price) * 1e6)) + held)]) {
      tr.insertCell().textContent = v;
    }
  }
  table.hidden = false;
}));

function guard(where, fn) {
  return async () => {
    try {
      await fn();
    } catch (err) {
      say(where, "Stopped: " + (err.shortMessage || err.message), "bad");
      restore();
    }
  };
}

$("load").addEventListener("click", guard("round", async () => {
  const n = Number($("seat").value);
  if (!Number.isInteger(n) || n < 1 || n > 40) throw new Error("enter a seat number from 1 to 40");
  seat = n;
  wallet = ethers.HDNodeWallet.fromPhrase(PHRASE, undefined, `m/44'/60'/0'/0/${9 + seat}`);
  const [eth, [held]] = await Promise.all([
    rpc(L1, "eth_getBalance", [wallet.address, "latest"]),
    call(DOLLAR, token, "balanceOf", [wallet.address]),
  ]);
  rows($("account"), [
    ["Seat", String(seat)],
    ["Address", wallet.address],
    ["ETH", ethers.formatEther(eth) + " ETH"],
    ["cUSD", cusd(held)],
  ]);
  $("load").disabled = true;
  $("seat").disabled = true;
  drawScore();
  setRound(await findRound());
  watchRounds();
}));
