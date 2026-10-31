// The mint page: one call to the badge contract, built, signed and sent in plain sight, and the
// worksheet's read-only questions asked with eth_call. Every node call goes through rpc() so the
// log shows the whole conversation with the node.
"use strict";

// Anvil's public test phrase. Accounts 10..49 hold 100 ETH at genesis; seat N uses 9 + N.
const PHRASE = "test test test test test test test test test test test junk";
const CHAIN_ID = 31337n;
// The contracts chain/build-chain.sh created (chain/addresses.env; the tests check they match).
const DOLLAR = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";
const BADGE = "0x0116686E2291dbd5e317F47faDBFb43B599786Ef";
const GAS_LIMIT = 1500000n; // storing the metadata costs about 20,000 gas per 32 bytes
const dollar = new ethers.Interface([
  "function balanceOf(address) view returns (uint256)",
  "function isBlackListed(address) view returns (bool)",
]);
const badge = new ethers.Interface([
  "function mint(address to, string uri) returns (uint256)",
  "function ownerOf(uint256) view returns (address)",
  "function tokenURI(uint256) view returns (string)",
  "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)",
]);
const $ = (id) => document.getElementById(id);

let wallet = null;
let uri = "";
let callId = 0;

async function rpc(method, params) {
  const body = { jsonrpc: "2.0", id: ++callId, method, params };
  const entry = document.createElement("li");
  entry.textContent = `→ ${method} ${JSON.stringify(params)}`;
  $("log").append(entry);
  const reply = await fetch("/rpc", {
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

function say(text) {
  $("status").textContent = text;
}

function fail(err) {
  say("Stopped: " + err.message);
}

// The badge's picture: an SVG with the badge's name on it, written into the metadata itself.
function picture(name, seat) {
  const safe = name.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">' +
    '<rect width="200" height="200" rx="24" fill="#1d3557"/><circle cx="100" cy="90" r="48" fill="#f1c40f"/>' +
    `<text x="100" y="104" font-family="sans-serif" font-size="32" font-weight="bold" text-anchor="middle" fill="#1d3557">${seat}</text>` +
    `<text x="100" y="172" font-family="sans-serif" font-size="14" text-anchor="middle" fill="#ffffff">${safe}</text></svg>`;
}

// Metadata in the shape ERC-721 wallets read: a name, a description and an image.
function metadata(name, description, seat) {
  const svg = picture(name, seat);
  const image = "data:image/svg+xml;base64," + btoa(String.fromCharCode(...new TextEncoder().encode(svg)));
  return "data:application/json," + JSON.stringify({ name, description, image });
}

function image(tokenUri) {
  const img = document.createElement("img");
  img.alt = "the badge's image";
  img.width = 120;
  img.height = 120;
  img.src = JSON.parse(tokenUri.slice("data:application/json,".length)).image;
  return img;
}

$("load").addEventListener("click", async () => {
  try {
    const seat = Number($("seat").value);
    if (!Number.isInteger(seat) || seat < 1 || seat > 40) throw new Error("enter a seat number from 1 to 40");
    wallet = ethers.HDNodeWallet.fromPhrase(PHRASE, undefined, `m/44'/60'/0'/0/${9 + seat}`);
    wallet.seat = seat;
    const balance = await rpc("eth_getBalance", [wallet.address, "latest"]);
    $("addr").textContent = wallet.address;
    $("balance").textContent = ethers.formatEther(balance) + " ETH";
    $("account").hidden = false;
    $("build").disabled = false;
    say("");
  } catch (err) {
    fail(err);
  }
});

$("build").addEventListener("click", () => {
  try {
    const name = $("name").value.trim() || "Course Badge";
    uri = metadata(name, $("description").value.trim(), wallet.seat);
    const data = badge.encodeFunctionData("mint", [wallet.address, uri]);
    $("picture").replaceChildren(image(uri));
    rows($("call"), [
      ["To (the badge contract)", BADGE],
      ["Function", "mint(address to, string uri)"],
      ["to", wallet.address],
      ["uri (the metadata)", uri],
      ["Input data (what the explorer shows)", data],
      ["Function selector (first 4 bytes)", data.slice(0, 10)],
    ]);
    $("preview").hidden = false;
    $("send").disabled = false;
    $("minted").hidden = true;
    say("");
  } catch (err) {
    fail(err);
  }
});

$("send").addEventListener("click", async () => {
  try {
    $("send").disabled = true;
    const [nonce, block] = await Promise.all([
      rpc("eth_getTransactionCount", [wallet.address, "pending"]),
      rpc("eth_getBlockByNumber", ["latest", false]),
    ]);
    const tip = ethers.parseUnits("1", "gwei");
    const tx = ethers.Transaction.from({
      type: 2,
      chainId: CHAIN_ID,
      nonce: Number(nonce),
      to: BADGE,
      value: 0n,
      gasLimit: GAS_LIMIT,
      maxPriorityFeePerGas: tip,
      maxFeePerGas: 2n * BigInt(block.baseFeePerGas) + tip,
      data: badge.encodeFunctionData("mint", [wallet.address, uri]),
    });
    tx.signature = wallet.signingKey.sign(tx.unsignedHash);
    const hash = await rpc("eth_sendRawTransaction", [tx.serialized]);
    say(`Sent. ${hash} is waiting for the next block...`);
    let receipt = null;
    while (!receipt) {
      await new Promise((done) => setTimeout(done, 2000));
      receipt = await rpc("eth_getTransactionReceipt", [hash]);
    }
    if (receipt.status !== "0x1") throw new Error(`the mint failed in block ${BigInt(receipt.blockNumber)}`);
    const log = receipt.logs.map((l) => badge.parseLog(l)).find((l) => l && l.name === "Transfer");
    const id = log.args.tokenId;
    const stored = badge.decodeFunctionResult("tokenURI",
      await rpc("eth_call", [{ to: BADGE, data: badge.encodeFunctionData("tokenURI", [id]) }, "latest"]))[0];
    const link = Object.assign(document.createElement("a"), { href: `/tx/${hash}`, textContent: hash });
    rows($("minted"), [
      ["Transaction", link],
      ["Block", BigInt(receipt.blockNumber).toString()],
      ["Badge number", id.toString()],
      ["Transfer log", `from ${log.args.from} to ${log.args.to}, badge ${id}`],
      ["tokenURI, read back from the contract", stored],
      ["Same as what you sent?", stored === uri ? "yes" : "no"],
      ["The image, from the contract", image(stored)],
    ]);
    say(`Mined in block ${BigInt(receipt.blockNumber)}. Open the transaction in the explorer to answer part 2.`);
    $("arg").value = id.toString();
    $("question").value = "tokenURI";
  } catch (err) {
    fail(err);
  }
});

$("ask").addEventListener("click", async () => {
  try {
    const fn = $("question").value;
    const onBadge = fn === "ownerOf" || fn === "tokenURI";
    const contract = onBadge ? badge : dollar;
    const arg = $("arg").value.trim();
    const data = contract.encodeFunctionData(fn, [onBadge ? BigInt(arg) : ethers.getAddress(arg)]);
    const raw = await rpc("eth_call", [{ to: onBadge ? BADGE : DOLLAR, data }, "latest"]);
    let value = contract.decodeFunctionResult(fn, raw)[0];
    if (fn === "balanceOf") value = `${value} (${ethers.formatUnits(value, 6)} cUSD: the token has 6 decimals)`;
    rows($("answer"), [
      ["Asked", `${onBadge ? "Course Badge" : "Course Dollar"} ${fn}(${arg})`],
      ["Sent to", onBadge ? BADGE : DOLLAR],
      ["Input data", data],
      ["Raw answer", raw],
      ["Decoded", String(value)],
    ]);
  } catch (err) {
    rows($("answer"), [["Answer", "the contract refused: " + (err.shortMessage || err.message)]]);
  }
});
