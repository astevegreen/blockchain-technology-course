# Technical Details: Web Frontend ↔ RPC Server

How the browser-based React app talks to the blockchain (Hardhat) RPC server.

---

## Protocol and Port

| Aspect | Detail |
|--------|--------|
| **Protocol** | **HTTP** (plain). No TLS/SSL by default. |
| **Port** | **8545** (Hardhat default). Not 443. |
| **URL form** | `http://<host>:8545` (e.g. `http://127.0.0.1:8545`, `http://192.168.1.100:8545`). |

- The app does **not** use port 443 or HTTPS for the RPC connection unless you explicitly set an RPC URL that uses `https://` (e.g. an ngrok HTTPS URL or a hosted RPC).
- The **web app itself** may be served over HTTPS (e.g. GitHub Pages at `https://alld0wnh1ll.github.io/ethereum-lab/` or `https://your-ngrok-url.ngrok-free.app`). That is separate from the RPC: the browser then makes **HTTP** (or HTTPS, if the RPC URL is https) requests from the page to the RPC endpoint.

---

## How the Frontend Connects

1. **User enters RPC URL** in the connection area (e.g. `http://127.0.0.1:8545` or instructor’s `http://<instructor-ip>:8545`). It’s stored in React state and optionally in `localStorage` under `custom_rpc`.

2. **`RpcClient.setRpcUrl(url)`** is called with that string (see `frontend/src/lib/RpcClient.js`):
   - It creates an **`ethers.JsonRpcProvider(sanitized)`**.
   - No custom headers, no WebSockets, no special options — just the URL.

3. **ethers v6 `JsonRpcProvider`**:
   - Uses the **Fetch API** in the browser to send **HTTP POST** requests to the given URL.
   - Body: JSON payload with method and params (e.g. `eth_blockNumber`, `eth_getBalance`, `eth_sendRawTransaction`).
   - Content-Type: `application/json`.
   - One HTTP request per JSON-RPC call (no long-lived connection; no built-in WebSocket in this path).

4. **Hardhat node** (started with `npm run chain` → `hardhat node --hostname 0.0.0.0`):
   - Listens on **TCP 8545**, **HTTP**.
   - Accepts JSON-RPC 2.0 over HTTP POST.
   - No TLS in default setup.

So: **browser → HTTP POST to `http://<host>:8545` → Hardhat node**. No 443, no HTTPS, unless the RPC URL you paste is itself `https://...`.

---

## Default RPC URL Logic (App.jsx)

- **Local:** `http://127.0.0.1:8545`
- **Remote (same host as the app, not ngrok):** `http://${window.location.hostname}:8545`
- **Ngrok:** Default left empty so user pastes something like `https://your-rpc.ngrok-free.app` (then the frontend would use HTTPS for RPC because the URL says so).

So 443 / HTTPS only come in if the **RPC URL** is an `https://` URL (e.g. ngrok or a cloud RPC). The app does not force 443 or TLS.

---

## CORS

- The RPC endpoint is often on a **different origin** than the page (e.g. page at `https://alld0wnh1ll.github.io`, RPC at `http://192.168.1.100:8545`).
- The browser sends **cross-origin** fetch requests. The Hardhat node must respond with **CORS headers** that allow the frontend’s origin (e.g. `Access-Control-Allow-Origin: *` or the page’s origin).
- Hardhat’s dev node typically allows cross-origin requests. If you use another RPC server, it must send appropriate CORS headers or the browser will block the requests.

---

## Summary

| Question | Answer |
|----------|--------|
| Does the web app use port 443 for RPC? | **No.** It uses whatever port is in the RPC URL (default **8545**). |
| HTTP or HTTPS for RPC? | **HTTP** by default (`http://...:8545`). **HTTPS** only if the RPC URL is `https://...` (e.g. ngrok). |
| Anything special (TLS, WebSockets)? | **No.** Plain JSON-RPC over HTTP (fetch POST). |
| Where is the connection code? | `frontend/src/lib/RpcClient.js`: `new ethers.JsonRpcProvider(url)`. |

So: the web portion talks to the RPC server over **plain HTTP on port 8545** (or whatever host:port you put in the RPC URL), with no 443 or special protocol unless you use an HTTPS RPC URL.

---

## How "Updates" Reach Clients (Instructor Node → Students)

**Short answer:** The instructor node **does not push** updates to clients. Each client **polls** the node over HTTP. There is no WebSocket, no server-sent events, and no persistent connection from node to browser.

### Pull-only model

1. **BlockchainSync** (`frontend/src/lib/BlockchainSync.js`):
   - Runs **in each student’s (and instructor’s) browser**.
   - Every **1 second** it calls the RPC endpoint: `getBlockNumber()`, `getCode()`, then fetches PoS data (total staked, validators, messages, etc.) via JSON-RPC.
   - If the aggregated data hash changed, it notifies in-app listeners (React state), so the UI updates.
   - All traffic is **client → HTTP request → instructor node → HTTP response → client**. No reverse push.

2. **Live view polling** (`App.jsx`):
   - When the Live view is active, an extra **setInterval** runs (every 2 seconds for stake info, every ~10 seconds for tx history).
   - Each tick triggers `fetchStakeInfo()` / `fetchTxHistory()` (and possibly `syncBlockchainData()`), which again **send HTTP requests** to the RPC URL (instructor node).
   - So again: client pulls; node only responds.

3. **After a user action** (e.g. send chat, stake, send ETH):
   - The app sends the transaction to the node (HTTP POST with `eth_sendRawTransaction` or contract call).
   - To show the new state, the app either calls `blockchainSync.forceRefresh()` / `syncBlockchainData()` (which do another HTTP round-trip) or waits for the next poll. No push from node.

### Why polling instead of push?

- **BlockchainSync** comments: *"WebSocket connections may not be available"* in classroom setups (firewalls, one-way NAT, etc.).
- HTTP polling works from any environment that can open the RPC URL; no need for the node to open a connection back to the client.
- The instructor node is a standard Hardhat JSON-RPC server: it does not implement WebSockets or any “broadcast to clients” logic. It only answers requests.

### Summary

| Question | Answer |
|----------|--------|
| Does the instructor node send updates to clients? | **No.** It only responds to HTTP requests. |
| How do clients get new state? | **Polling:** each client periodically (e.g. every 1–2 s) sends HTTP requests to the RPC URL and updates the UI if the response changed. |
| WebSockets or push? | **No.** Plain HTTP request/response only. |
| Where is the polling logic? | `BlockchainSync` (1 s interval) and Live view `setInterval` in `App.jsx` (2 s / 10 s). |
