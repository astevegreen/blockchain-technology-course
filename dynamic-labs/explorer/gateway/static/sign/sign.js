// The signing page: one transaction, built, signed and sent in plain sight. Every node call
// goes through rpc() so the log shows the whole conversation with the node.
"use strict";

// Anvil's public test phrase. Accounts 10..49 hold 100 ETH at genesis; seat N uses 9 + N.
const PHRASE = "test test test test test test test test test test test junk";
const CHAIN_ID = 31337n;
const $ = (id) => document.getElementById(id);

let wallet = null;
let tx = null;
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
    const code = document.createElement("code");
    code.textContent = value;
    tr.append(th);
    tr.insertCell().append(code);
  }
  table.hidden = false;
}

function say(text) {
  $("status").textContent = text;
}

function fail(err) {
  say("Stopped: " + err.message);
}

$("load").addEventListener("click", async () => {
  try {
    const seat = Number($("seat").value);
    if (!Number.isInteger(seat) || seat < 1 || seat > 40) throw new Error("enter a seat number from 1 to 40");
    wallet = ethers.HDNodeWallet.fromPhrase(PHRASE, undefined, `m/44'/60'/0'/0/${9 + seat}`);
    const [balance, nonce] = await Promise.all([
      rpc("eth_getBalance", [wallet.address, "latest"]),
      rpc("eth_getTransactionCount", [wallet.address, "pending"]),
    ]);
    $("addr").textContent = wallet.address;
    $("balance").textContent = ethers.formatEther(balance) + " ETH";
    $("nonce").textContent = BigInt(nonce).toString();
    $("account").hidden = false;
    $("build").disabled = false;
    say("");
  } catch (err) {
    fail(err);
  }
});

$("build").addEventListener("click", async () => {
  try {
    const to = ethers.getAddress($("to").value.trim());
    const value = ethers.parseEther($("amount").value.trim());
    const [nonce, block] = await Promise.all([
      rpc("eth_getTransactionCount", [wallet.address, "pending"]),
      rpc("eth_getBlockByNumber", ["latest", false]),
    ]);
    const tip = ethers.parseUnits("1", "gwei");
    tx = ethers.Transaction.from({
      type: 2,
      chainId: CHAIN_ID,
      nonce: Number(nonce),
      to,
      value,
      gasLimit: 21000n,
      maxPriorityFeePerGas: tip,
      maxFeePerGas: 2n * BigInt(block.baseFeePerGas) + tip,
      data: "0x",
    });
    rows($("unsigned"), [
      ["Type", "2 (fee market)"],
      ["Chain ID", tx.chainId.toString()],
      ["Nonce", tx.nonce.toString()],
      ["To", tx.to],
      ["Value", ethers.formatEther(tx.value) + " ETH"],
      ["Gas limit", tx.gasLimit.toString()],
      ["Max fee per gas", ethers.formatUnits(tx.maxFeePerGas, "gwei") + " Gwei"],
      ["Max priority fee per gas", ethers.formatUnits(tx.maxPriorityFeePerGas, "gwei") + " Gwei"],
      ["From", "(not in the transaction: the signature will prove it)"],
      ["Unsigned bytes", tx.unsignedSerialized],
      ["Hash the key signs", tx.unsignedHash],
    ]);
    $("signed").hidden = true;
    $("sign").disabled = false;
    $("send").disabled = true;
    say("");
  } catch (err) {
    fail(err);
  }
});

$("sign").addEventListener("click", () => {
  try {
    tx.signature = wallet.signingKey.sign(tx.unsignedHash);
    const recovered = ethers.Transaction.from(tx.serialized).from;
    rows($("signed"), [
      ["Signature r", tx.signature.r],
      ["Signature s", tx.signature.s],
      ["Signature yParity", String(tx.signature.yParity)],
      ["Signed bytes (what is sent)", tx.serialized],
      ["Transaction hash", tx.hash],
      ["From, recovered from the signature", recovered],
      ["Matches your address?", recovered === wallet.address ? "yes" : "no"],
    ]);
    $("send").disabled = false;
  } catch (err) {
    fail(err);
  }
});

$("send").addEventListener("click", async () => {
  try {
    $("send").disabled = true;
    $("sign").disabled = true;
    const hash = await rpc("eth_sendRawTransaction", [tx.serialized]);
    const started = Date.now();
    say(`Sent. ${hash} is waiting in the node's mempool for the next block...`);
    for (;;) {
      await new Promise((done) => setTimeout(done, 2000));
      const receipt = await rpc("eth_getTransactionReceipt", [hash]);
      if (receipt) {
        const seconds = Math.round((Date.now() - started) / 1000);
        const block = BigInt(receipt.blockNumber).toString();
        $("status").replaceChildren(
          `Mined in block ${block} after about ${seconds} s in the mempool. `,
          Object.assign(document.createElement("a"), { href: `/tx/${hash}`, textContent: "Open it in the explorer" }),
        );
        return;
      }
      const pending = await rpc("eth_getTransactionByHash", [hash]);
      say(`${hash} is ${pending && pending.blockNumber === null ? "pending: in the mempool, not yet in a block" : "not known to the node yet"}...`);
    }
  } catch (err) {
    fail(err);
  }
});
