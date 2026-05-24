#!/usr/bin/env node
/**
 * One-command start for Beacon Chain Lab: chain + deploy + frontend
 * Usage: npm run beacon-lab
 */

const { spawn } = require("child_process");
const http = require("http");
const path = require("path");

const RPC_URL = "http://127.0.0.1:8545";
const RPC_PORT = 8545;
const WAIT_MS = 500;
const MAX_ATTEMPTS = 60;

function waitForRpc() {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const tryConnect = () => {
      const req = http.request(
        RPC_URL,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        },
        (res) => {
          let body = "";
          res.on("data", (c) => (body += c));
          res.on("end", () => {
            try {
              const j = JSON.parse(body);
              if (j.result !== undefined) {
                resolve();
                return;
              }
            } catch (_) {}
            attempts++;
            if (attempts >= MAX_ATTEMPTS) return reject(new Error("RPC timeout"));
            setTimeout(tryConnect, WAIT_MS);
          });
        }
      );
      req.on("error", () => {
        attempts++;
        if (attempts >= MAX_ATTEMPTS) return reject(new Error("RPC not ready"));
        setTimeout(tryConnect, WAIT_MS);
      });
      req.write(JSON.stringify({ jsonrpc: "2.0", method: "eth_blockNumber", params: [], id: 1 }));
      req.end();
    };
    tryConnect();
  });
}

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const cwd = opts.cwd || path.join(__dirname, "..");
    const child = spawn(cmd, args, {
      cwd,
      stdio: opts.silent ? "pipe" : "inherit",
      shell: true,
      ...opts,
    });
    child.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`Exit ${code}`))));
    child.on("error", reject);
  });
}

async function main() {
  const children = [];

  // Check if chain already running
  let chainAlreadyUp = false;
  try {
    await new Promise((res, rej) => {
      const req = http.request(
        RPC_URL,
        { method: "POST", headers: { "Content-Type": "application/json" } },
        (r) => {
          let b = "";
          r.on("data", (c) => (b += c));
          r.on("end", () => {
            try {
              if (JSON.parse(b).result !== undefined) res();
            } catch (_) {}
            rej();
          });
        }
      );
      req.on("error", rej);
      req.write(JSON.stringify({ jsonrpc: "2.0", method: "eth_blockNumber", params: [], id: 1 }));
      req.end();
    });
    chainAlreadyUp = true;
    console.log("\n   ✓ Chain already running\n");
  } catch (_) {}

  if (!chainAlreadyUp) {
    console.log("\n⛓  Starting Hardhat node...");
    const chain = spawn("npx", ["hardhat", "node", "--hostname", "0.0.0.0"], {
      cwd: path.join(__dirname, ".."),
      stdio: "pipe",
      shell: true,
    });
    children.push(chain);
    chain.stdout?.on("data", (d) => process.stdout.write(d));
    chain.stderr?.on("data", (d) => process.stderr.write(d));

    await waitForRpc();
    console.log("   ✓ Chain ready\n");
  }

  console.log("📜 Deploying Beacon Chain Lab...");
  await run("npx", ["hardhat", "run", "scripts/deploy-beacon-lab.js", "--network", "localhost"], {
    cwd: path.join(__dirname, ".."),
  });
  console.log("");

  console.log("🌐 Starting frontend...");
  console.log("   Open: http://localhost:5173/?view=beacon-lab\n");
  const web = spawn("npm", ["run", "web"], {
    cwd: path.join(__dirname, ".."),
    stdio: "inherit",
    shell: true,
  });
  children.push(web);

  const cleanup = () => {
    console.log("\nShutting down...");
    children.forEach((c) => {
      try {
        c.kill("SIGTERM");
      } catch (_) {}
    });
    process.exit(0);
  };
  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  web.on("close", (code) => {
    children.forEach((c) => {
      try {
        c.kill("SIGTERM");
      } catch (_) {}
    });
    process.exit(code ?? 0);
  });
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
