# Student guide: Live tab and hands-on labs

This walkthrough matches the **Ethereum Trainer** web app: button names, sidebar labels, and the order that usually works in class.

---

## 1. Open Live mode

1. At the **top of the left sidebar**, find the four big mode buttons: **Learn**, **Live**, **CLI**, and (for instructors only) **Instructor**.
2. Click **Live** (green tab, globe icon).

You stay in “Live Network” mode until you click **Learn** or **CLI** again. From **Learn**, you can also use **Go to Live Network →** in the sidebar.

---

## 2. Connect to the chain (do this before labs)

On the **Live** main page, scroll to the **Connection Setup** card (gear icon).

1. **Blockchain RPC URL**  
   Enter the URL your instructor gives you. Typical patterns:
   - `http://<INSTRUCTOR_IP>:8080/rpc` (when the app is behind port 8080)
   - `http://<INSTRUCTOR_IP>:8545` (direct JSON-RPC)
   In some classroom setups the URL is filled in automatically from server config—if it already looks correct, leave it.

2. **Contract Address (from instructor)**  
   Paste the **PoS / class contract** address the instructor shares (starts with `0x`, 42 characters). Without it, parts of Live (staking, class roster integration) may not work.

3. Watch the **connection line** under those fields:
   - **Connected to blockchain** (green) means your RPC is reachable.
   - If it says **Not connected**, fix the RPC URL or ask the instructor if the node is up.

**Search Chain** lives in the same **Connection Setup** area—use it later to look up transactions and addresses once you are connected.

---

## 3. Create or choose a wallet

### If you see “Create your first wallet”

Some setups require a wallet before funding. Click **Create or import wallet**. That opens **My Account**, where you can:

- **Generate New Wallet**: enter a nickname (e.g. your name), then **Generate Wallet**.  
  A modal shows your **address** and **private key**—save both; you need the private key to use this wallet again in another browser or after clearing storage.
- Or **Import Existing Wallet** with a private key your instructor gave you.

### Wallet controls in the left sidebar (Live mode)

Under **Your Account**:

- Use the **dropdown** to pick which saved wallet is active.
- **Import** — paste a private key (`0x` + 64 hex).
- **New** — create another wallet (you will be prompted for a nickname).
- **Export** — copy your private key (keep it secret).

You can also use **Account** on the blue wallet banner (main area) for a short reminder about nicknames and addresses.

---

## 4. Request test ETH (instructor funds you)

There is **no public faucet** in this lab. Only the instructor sends test ETH.

1. After your wallet has an address, check your **ETH balance** on the blue wallet card.
2. If balance is **0**, find the yellow **Test ETH** box. It says only the instructor can issue funds.
3. You can:
   - **Copy** your full address and send it to the instructor (chat, LMS, etc.), or  
   - Click **Request funds** (paper-plane icon). That sends a notice to the instructor via the lab API (`/lab-api/fund-request`). If the API is off, use copy-and-message instead.
4. Wait until your balance is above **0** before transactions that need **gas** (deploy, stake, send).

---

## 5. Class list and public addresses on the left

In **Live** mode, the sidebar has **Classmates** (with a count).

- Each row is a **public address** (short form like `0x1234…abcd`). **Click a row** to copy that address—useful when a lab asks for a partner’s wallet.
- Set **Your Nickname** (purple box) so others recognize you; click the text to edit, then ✓ to save.
- If you are not listed yet, click **Join Class List** so your address appears (you may need a small amount of ETH for the on-chain step—get funded first if it fails).

This list is for **public addresses only**. Never put private keys in chat.

---

## 6. Open the hands-on labs

Same labs appear in two places; use whichever is easier.

### In the left sidebar (under “Hands-On Labs”)

- **Beacon Chain Lab** — staking, committees, attestations (consensus-style exercise).
- **Contract Builder Lab** — write, compile, deploy, and interact with contracts step by step.
- **Tokenization Lab** — ERC-721 NFT flow (mint, metadata, transfer, sale).

### On the Live main page (quick buttons)

- **Beacon Lab** and **Contract Lab** (same as Beacon Chain Lab and Contract Builder Lab).
- In the **Tokenization Lab** promo card, **Open Tokenization Lab →**.

The **Do This First** checklist (expandable near the top of Live) also links to Beacon and the contract lab; it calls the contract lab **“Smart Contract Lab”**—that is the same as **Contract Builder Lab** / **Contract Lab**.

---

## 7. What to do inside each lab (short map)

| Lab | You typically need |
|-----|---------------------|
| **Beacon Chain Lab** | RPC connected, wallet with enough test ETH to **stake** (lab uses a reduced stake vs mainnet). Follow the lab panel: join pool, wait for instructor to run the session if required, then **attest** when prompted. |
| **Contract Builder Lab** | RPC + wallet + ETH. Use the **Lab Terminal** button (top of the page) when the steps tell you to run scripts or `hardhat compile`. |
| **Tokenization Lab** | Same as above. If you see “Connect to the chain first,” return to **Live**, fix **Connection Setup**, and ensure your wallet is active. |

---

## 8. Helpful extras (same app)

- **Lab Terminal** / **+ New** (top bar)—opens a terminal in a new window; RPC can be passed for your session.
- **Diagnostics** (sidebar)—connectivity checks if something won’t connect.
- **3D Chain Explorer** (sidebar)—visual explorer; optional.
- **❓ Help** on the Live wallet banner—opens in-app Live help.

---

## 9. If something goes wrong

- **Disconnected** — RPC URL wrong, firewall, or instructor node stopped. Confirm the URL and port.
- **No ETH** — you cannot deploy or join some activities until the instructor funds you; use **Request funds** or copy your address.
- **Wrong wallet** — use the **Your Account** dropdown in the sidebar to switch wallets.
- **Lost keys** — without the private key, that wallet cannot be recovered. Generate a new wallet and ask the instructor to fund the new address.

When in doubt, tell your instructor your **public address** (never your private key) and what you see under **Connection Setup** (connected or not) and your **balance**.
