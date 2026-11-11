# Ethereum Lab — End-to-End Test Playbook (Browser MCP)

> **Who this is for:** An AI agent (mid-tier model is fine, e.g. Gemma-class) that drives a real
> browser through the **browser-puppet MCP** to validate the Ethereum training lab for **both the
> instructor and student roles**, across all four labs (Beacon Chain, Smart Contract, Tokenization,
> NFT Marketplace), the student dashboard, and instructor start/stop controls.
>
> **How to use it:** Work top to bottom. Each test case is self-contained: **Preconditions → Steps
> (exact tool calls) → Expected (exact text to look for) → PASS/FAIL**. Do exactly what each step
> says. After every test, write down PASS or FAIL and (on FAIL) capture a screenshot. Do **not**
> improvise new flows — if a step can't be completed, mark it BLOCKED and move on.
>
> **Golden rules (read once, obey always):**
> 1. **Inspect before you act.** Before clicking, call `get_page_digest` or
>    `find_interactive_candidates` so you click the *right* element. Never blind-click.
> 2. **Verify by visible text.** A step "passes" only when the **exact expected text appears on the
>    page**. Use `extract_text` and check that the expected substring is present.
> 3. **One action at a time, then wait.** Blockchain actions take 2–10 seconds. After a click that
>    sends a transaction, use `wait_for` (or poll `extract_text`) until the success text appears.
> 4. **Dialogs:** This app uses native browser pop-ups (`window.prompt`, `window.confirm`). You MUST
>    use `handle_dialog` for these (see §0.4). If you don't, the action silently cancels.
> 5. **Mode matters:** The Beacon lab and the Tokenization/Marketplace labs **cannot run at the same
>    time** (they share one blockchain). The instructor's **Tokenization Mode** toggle switches
>    between them. Always put the lab in the correct mode before testing it (see §3).

---

## 0. Browser MCP primer (browser-puppet)

All tool names below are prefixed `mcp__browser-puppet__` in the tool interface. The examples omit
the prefix for brevity; call the real (prefixed) tool.

### 0.1 The canonical loop

```
create_context  →  open_page  →  (inspect)  →  (interact)  →  (verify)  →  ... →  close_context
```

### 0.2 Core tools you will use (with the arguments that matter)

| Tool | Call it like | What it does |
|------|--------------|--------------|
| `create_context` | `{ "browser": "chromium" }` | Make a browser. Returns `context_id`. Do this once at the start. |
| `open_page` | `{ "context_id": "<id>", "url": "<url>" }` | Open a URL. Returns `page_id`. |
| `navigate` | `{ "page_id": "<id>", "url": "<url>" }` | Go to a new URL in the same page (used to switch lab views). |
| `get_page_digest` | `{ "page_id": "<id>" }` | High-level summary of the page. Run after every navigation. |
| `extract_text` | `{ "page_id": "<id>", "scope": "visible" }` | Get all visible text. **This is how you verify expected text.** |
| `find_interactive_candidates` | `{ "page_id": "<id>", "intent": "the Join button" }` | Find clickable things by description. Returns `element_id`s. |
| `click` | `{ "page_id": "<id>", "target": { "text": "Join" } }` | Click by visible text (preferred) or by `element_id`. |
| `type_text` | `{ "page_id": "<id>", "target": { "css": "input[placeholder='ETH']" }, "text": "32" }` | Type into a field. |
| `fill_and_click` | `{ "page_id":"<id>", "fields":[{"target":{...},"value":"1.5"}], "click_target":{"text":"List"} }` | Fill field(s) then click in one shot. |
| `wait_for` | `{ "page_id": "<id>", "target": { "text": "Deployed" }, "state": "visible" }` | Wait until text/element appears (or disappears with `"state":"hidden"`). |
| `handle_dialog` | `{ "action": "accept" }` or `{ "action": "accept", "prompt_text": "Tester" }` | Accept/dismiss a native confirm/prompt (see §0.4). |
| `execute_page_js` | `{ "page_id": "<id>", "script": "return await (await fetch('...')).json()" }` | Run JS in the page — used for **API assertions** (see §0.5). |
| `take_screenshot` | `{ "page_id": "<id>" }` | Capture evidence. Do this on every FAIL. |
| `get_console_logs` / `get_page_errors` | `{ "page_id": "<id>" }` | Read JS errors when something looks broken. |
| `close_context` | `{ "context_id": "<id>" }` | Tear down at the very end. |

### 0.3 Clicking and typing — targeting

Prefer **`{ "text": "exact button label" }`** as the target. If text targeting is ambiguous or
fails, call `find_interactive_candidates` with a plain-English `intent`, take the `element_id` from
the result, and pass `{ "element_id": "<id>" }` to `click`/`type_text`.

For typing into the Hardhat terminal (Smart Contract lab, advanced), pass
`"typing_mode": "keystrokes"` to `type_text`.

### 0.4 Native dialogs — CRITICAL

Several actions open a native browser pop-up. Playwright (under browser-puppet) needs a handler.
**Pattern: call `handle_dialog` immediately after the click that triggers the dialog** (the dialog
is queued; `handle_dialog` answers it).

| Action that opens a dialog | Dialog type | How to answer |
|---|---|---|
| Student clicks **Create wallet** / **🔑 New** | `prompt` (nickname) | `handle_dialog { "action": "accept", "prompt_text": "Tester1" }` |
| Instructor clicks **🪙 Tokenization Mode** (turning ON) | `confirm` | `handle_dialog { "action": "accept" }` |
| Instructor clicks **🔄 Reset Chain** | `confirm` | `handle_dialog { "action": "accept" }` |
| Instructor clicks beacon **Reset Lab** | `confirm` | `handle_dialog { "action": "accept" }` |
| `⚙️ Account` / various info buttons | `alert` | `handle_dialog { "action": "accept" }` |

If you intend to **cancel** instead, use `{ "action": "dismiss" }`.

### 0.5 API assertions (makes a mid model reliable)

Besides reading the UI, you can confirm backend state directly. Use `execute_page_js` to `fetch`
the lab API from inside the page (same origin, so it just works). Examples:

```js
// Is tokenization mode ON?  -> { ok, enabled }
return await (await fetch(BASE + 'lab-api/beacon/tokenization-mode', {cache:'no-store'})).json();
// Beacon chain state (sessionState 0=LOBBY,1=ACTIVE,2=FINISHED), committee, blocks
return await (await fetch(BASE + 'beacon-state', {cache:'no-store'})).json();
// Marketplace state: listings, tokensByOwner, nft + marketplace addresses
return await (await fetch(BASE + 'marketplace-state', {cache:'no-store'})).json();
// Tokenization NFT claims/mints
return await (await fetch(BASE + 'lab-api/nft/state', {cache:'no-store'})).json();
```
…where `BASE` is the lab base path ending in `/labs/ethereum_lab/` (see §1). Treat an API assertion
as a strong PASS signal even if the UI text is slightly different from this document.

---

## 1. Environment & access

### 1.1 URLs

| Thing | Value |
|---|---|
| **Lab base URL (production)** | `https://blockchain.training-as-code.com/labs/ethereum_lab/` |
| Local dev (if testing locally) | `http://localhost:5173/` (no `/labs/ethereum_lab/` prefix) |

Throughout this doc, **`BASE`** = the lab base URL **including the trailing slash**. Views are
selected with the `?view=` query parameter appended to `BASE`:

| View | URL |
|---|---|
| Student dashboard ("Live") | `BASE?view=live` |
| Beacon Chain Lab | `BASE?view=beacon-lab` |
| Smart Contract Lab | `BASE?view=contract-builder-lab` |
| Tokenization Lab | `BASE?view=tokenization-lab` |
| NFT Marketplace | `BASE?view=nft-marketplace` |
| Diagnostics | `BASE?view=diagnostics` |
| Instructor dashboard | `BASE?mode=instructor&view=instructor` |

> Switching views: you can either click the left-nav buttons **or** `navigate` directly to the
> `?view=` URL. **Direct navigation is more reliable for automation** — prefer it.

### 1.2 Roles & how to get them

- **Student:** default. Just open `BASE?view=live`. A guest wallet is created automatically (or you
  are prompted to create one — see Test S1).
- **Instructor:** gated. The backend (`isInstructorRequest`) grants instructor powers only when the
  request is **instructor-authenticated**:
  - On the **deployed site**: you must hold the `hlf_instructor` cookie (set by logging into the
    instructor portal). If you are not logged in, `?mode=instructor` is stripped and you land on the
    student dashboard — that means you do not have instructor access; mark instructor tests BLOCKED.
  - On a **standalone/local** deploy: instructor is granted by IP (the instructor's own machine /
    Docker gateway). Locally, `?mode=instructor` usually just works.
  - **Verify you actually have instructor access** with the API assertion:
    `fetch(BASE+'lab-api/session').then(r=>r.json())` → expect `{ "isInstructor": true }`.

### 1.3 Prerequisites checklist (do this before testing)

1. `create_context { "browser": "chromium" }` → save `context_id`.
2. `open_page { context_id, url: BASE + "?view=live" }` → save `page_id`.
3. `get_page_digest { page_id }` → the page title/heading should reference the Ethereum trainer. If
   the page is blank or 5xx, STOP — the lab is down (see Troubleshooting §13).
4. API assertion: `execute_page_js` running
   `return await (await fetch('lab-api/health')).json()` → expect an OK/healthy response.

### 1.4 Two browser contexts (needed for the Marketplace buy test)

Some tests need two different students (a seller and a buyer). Create a **second context** for the
buyer so it gets its own wallet:
`create_context { "browser": "chromium" }` → `context_idB`, then its own `open_page`. Keep the two
contexts separate; never reuse one wallet as both seller and buyer for the buy test.

---

## 2. Test conventions

- **Result log:** Keep a running table: `| Test ID | Title | Result (PASS/FAIL/BLOCKED) | Notes |`.
- **Verifying text:** "page shows X" means: call `extract_text`, confirm the substring **X** is in
  the returned text. Substring match (case-insensitive) is fine; you don't need an exact full-string
  match.
- **On FAIL:** `take_screenshot`, then `get_page_errors` and `get_console_logs`, and record the
  first error. Then continue to the next test (don't get stuck).
- **Waiting:** when told to "wait for X", use `wait_for { target:{text:"X"}, state:"visible" }`. If it
  times out, re-`extract_text` once before declaring FAIL (the text may already be present).
- **Resetting between tests:** to start a lab from a clean wallet, you can create a fresh context
  (new wallet) instead of trying to "log out".

---

## 3. Lab-mode gating (do this FIRST, it controls everything)

The shared chain runs in exactly one of two modes:

| Mode | Beacon lab | Tokenization + Marketplace |
|---|---|---|
| **Tokenization Mode OFF** | ✅ produces blocks, works | ❌ contracts get pruned/frozen out |
| **Tokenization Mode ON** | ⏸ paused (no new blocks) | ✅ NFT mints persist, works |

So the test order is:
1. Instructor tests, including **toggling the mode** (§4).
2. With **mode OFF**: Beacon Chain lab (§6) and Smart Contract lab (§7 — works in either mode, but
   simplest with blocks flowing).
3. With **mode ON**: Tokenization lab (§8) and NFT Marketplace (§9).

**Always assert the mode before a lab test** using the API assertion in §0.5
(`lab-api/beacon/tokenization-mode` → `.enabled`).

---

## 4. INSTRUCTOR ROLE TESTS

> Preconditions for all of §4: you have instructor access (verify per §1.2). If
> `lab-api/session` → `isInstructor:false`, mark **all** of §4 BLOCKED and skip to §5.

### Test I0 — Reach the instructor dashboard
**Steps**
1. `navigate { page_id, url: BASE + "?mode=instructor&view=instructor" }`
2. `get_page_digest { page_id }`
3. `extract_text { page_id }`

**Expected:** page shows **`🎓 Instructor Dashboard`** and a controls section **`🎛️ Instructor
Controls`**. You should see buttons including **`🔄 Reset Chain`** and a **`Tokenization Mode`**
button (label is either `🪙 Tokenization Mode: OFF` or `🔒 Tokenization Mode: ON`).
**PASS** if both headings + the two buttons are present. **FAIL** otherwise.

---

### Test I1 — START the Token/Marketplace labs (Tokenization Mode → ON)
This is the instructor "starting" the tokenization+marketplace labs (and pausing the beacon lab).

**Preconditions:** Tokenization Mode currently OFF (assert: `lab-api/beacon/tokenization-mode` →
`enabled:false`). If already ON, first run Test I2 to turn it off, then come back.

**Steps**
1. Locate the toggle: `find_interactive_candidates { page_id, intent: "the Tokenization Mode toggle button" }`.
2. `click { page_id, target: { text: "Tokenization Mode: OFF" } }`  *(label contains "OFF" right now)*
3. **A confirm dialog appears.** `handle_dialog { "action": "accept" }`
   *(dialog text: "Enable Tokenization mode? This pauses the Beacon lab… stops chain pruning so NFT
   mints persist…")*
4. `wait_for { page_id, target: { text: "Tokenization mode ON" }, state: "visible" }`

**Expected (UI):** a status message **`✅ Tokenization mode ON — Beacon lab paused, chain frozen for
NFT minting.`** and the button now reads **`🔒 Tokenization Mode: ON`**.
**Expected (API assertion — authoritative):** `execute_page_js` →
`return await (await fetch('lab-api/beacon/tokenization-mode',{cache:'no-store'})).json()` →
`{ "ok": true, "enabled": true }`.
**PASS** if the API assertion returns `enabled:true`.

---

### Test I2 — STOP the Token labs / resume Beacon (Tokenization Mode → OFF)
**Preconditions:** Tokenization Mode currently ON.

**Steps**
1. `click { page_id, target: { text: "Tokenization Mode: ON" } }`
2. *(Turning OFF does **not** prompt a confirm — no `handle_dialog` needed. If a dialog does appear,
   accept it.)*
3. `wait_for { page_id, target: { text: "Tokenization mode OFF" }, state: "visible" }`

**Expected (UI):** **`✅ Tokenization mode OFF — Beacon lab resumed.`**, button reads **`🪙
Tokenization Mode: OFF`**.
**Expected (API):** `lab-api/beacon/tokenization-mode` → `enabled:false`.
**PASS** if API returns `enabled:false`.
**Follow-up check (beacon resumes):** wait ~15s, assert `beacon-state` and confirm the block
`currentSlot`/blocks count **increases** on a second read (blocks are flowing again).

---

### Test I3 — Reset the beacon chain
**Preconditions:** Tokenization Mode OFF.

**Steps**
1. Read current height: `execute_page_js` → `return (await (await fetch('beacon-state',{cache:'no-store'})).json()).blocks?.length`
2. `click { page_id, target: { text: "Reset Chain" } }`
3. **Confirm dialog appears.** `handle_dialog { "action": "accept" }`
   *(text: "Reset the beacon chain? This clears all blocks and stakes…")*
4. `wait_for { page_id, target: { text: "Reset requested" }, state: "visible" }`

**Expected (UI):** **`✅ Reset requested — chain will prune within a few seconds.`**
**Expected (API):** after ~10s, `beacon-state` shows the chain reseated (blocks cleared / committee
back to bots; `sessionState` returns to LOBBY `0` or a small fresh committee).
**PASS** if the status text appears AND the post-reset state differs from the pre-reset state.

---

### Test I4 — Approve / dismiss a student fund request
**Setup:** in a **student** context (§5), have the student trigger a fund request (the student UI
sends one when low on ETH / via a "request funds" path). Then return to the instructor page.

**Steps**
1. `navigate` to instructor view; `extract_text`. The fund-requests panel lists pending requests
   with the student address and an amount.
2. `find_interactive_candidates { page_id, intent: "approve or fulfill the fund request" }`, click it.
3. `extract_text` again.

**Expected:** the request disappears from the pending list (it is `DELETE`d via
`lab-api/fund-request/{id}` after fulfillment). The student's balance increases on their dashboard.
**PASS** if the request is removed. (If no fund-request UI is reachable, mark BLOCKED.)

---

### Test I5 — Slash a validator (instructor enforcement)
**Preconditions:** Tokenization Mode OFF; a beacon session is ACTIVE with at least one validator
(run Test I6 first to start a session, or do this after §6).

**Steps**
1. In the instructor **Validator Activity** table, click a student row to select it (or use the
   beacon-lab instructor "Select validator" dropdown).
2. Type a reason into the **Slash reason** field: `type_text { target:{css:"input[placeholder*='reason' i]"}, text:"test slash" }`.
3. `click { target: { text: "Slash" } }`
4. `wait_for { target: { text: "Slashed" }, state: "visible" }`

**Expected:** status **`Slashed!`** (or `Slashed`), and the validator shows as slashed (appears in
"Slashed Validators"). **PASS** if the validator is marked slashed.
**Edge case E-I5a:** selecting an **already-slashed** validator — the dropdown option is disabled and
the **Slash** button stays disabled. Verify you cannot slash twice.

---

### Test I6 — Start a beacon session with bots (instructor)
**Preconditions:** Tokenization Mode OFF, beacon session in LOBBY (`sessionState:0`).

**Steps**
1. `navigate { page_id, url: BASE + "?view=beacon-lab" }` (instructor controls render at the bottom
   when you are an instructor).
2. Optionally set committee size: in **Validators per committee**, `type_text` `8`, click **Set**.
   Expect status like `Set to 8 validators…`.
3. Click **Join & Start** (if the instructor isn't in the pool yet) OR **Fill Bots and Start**.
   - **Join & Start** opens no extra dialog but sends a wallet tx; wait for the session to go ACTIVE.
4. `wait_for { target: { text: "Session started" }, state: "visible" }` (or assert via API).

**Expected (API):** `beacon-state` → `sessionState: 1` (ACTIVE) and `committee` length > 0; within
~15s `blocks` start appearing.
**PASS** if `sessionState` becomes `1` and blocks begin to grow.
**Edge case E-I6a:** clicking **Fill Bots and Start** while the committee is empty → button is
disabled / status warns "Join the pool first…". Verify the guard.

---

### Test I7 — Operator-level start/stop of the whole lab (terminal, not browser)
> This validates "starting and stopping specific labs" at the **operations** level (the instructor's
> server, not the browser UI). Only run if you have shell access to the deploy host. If not, mark
> SKIPPED.

On the deploy host (`ssh ubuntu@blockchain.training-as-code.com`, dir
`~/courseware-builder-pipeline/dynamic-labs`):

```bash
./lab-manager.sh status ethereum_lab     # show current state
./lab-manager.sh stop ethereum_lab        # STOP the ethereum lab (recreates/removes instructor)
./lab-manager.sh start ethereum_lab       # START it again (RESETS the chain)
```
**Expected:** `stop` removes the `ethereum-trainer-instructor` container; `start` recreates it and
the lab becomes reachable again at `BASE`. After `start`, re-run §1.3 pre-flight — it should pass.
**Note:** `start ethereum_lab` **resets the chain** and recreates only the instructor; warm student
lanes may need recycling. There is no `restart` verb — use `stop` then `start`.
**PASS** if the lab is unreachable after `stop` and healthy again after `start`.

---

## 5. STUDENT DASHBOARD / SHELL TESTS

> Use a fresh context so you see the new-student flow. `navigate` to `BASE + "?view=live"`.

### Test S1 — Create the first wallet (native prompt)
**Steps**
1. `extract_text { page_id }`. A brand-new student sees a banner **`👛 Create your first wallet`**
   and a **`Create wallet`** button. (If instead a wallet already exists and balance is shown, this
   student was auto-provisioned; record PASS-by-autocreate and skip to S2.)
2. `click { page_id, target: { text: "Create wallet" } }`
3. **A prompt appears** asking for a nickname.
   `handle_dialog { "action": "accept", "prompt_text": "Tester1" }`
4. `wait_for { page_id, target: { text: "New Wallet Created" }, state: "visible" }`

**Expected:** modal **`✅ New Wallet Created`** with an **Address** and a **`⚠️ Private Key (NEVER
share)`** field, and a dismiss button **`Got it — I've saved my credentials`**. Click it.
**PASS** if the modal appeared with an address.

### Test S2 — Auto-connection & node status
**Steps:** `extract_text`. **Expected:** a connection badge showing **`Block #<number>`** (a real
integer) and/or **`Live 🟢`**. The number should increase on a later read (chain is live).
**Edge E-S2a (RPC down):** if you see **`Disconnected`** / **`❌ Not connected - check RPC URL`**,
the node is down → record and check Diagnostics (S6).
**PASS** if a numeric block height is shown.

### Test S3 — Top off (faucet)
**Steps**
1. `click { page_id, target: { text: "Top off" } }` (the **💰 Top off** button).
2. `wait_for { page_id, target: { text: "Added 10 ETH" }, state: "visible" }`

**Expected:** status **`✅ Added 10 ETH — balance now …`**, and the balance shown in **`💼 Your
Assets`** / wallet header increases.
**Edge E-S3a:** with no wallet, the button is disabled / shows `❌ Create a wallet first.`
**PASS** if balance increases.

### Test S4 — Navigation: every lab tab loads
For each (label → expected heading), `navigate` to the `?view=` URL (per §1.1) and `extract_text`:

| Click / view | Expect heading text contains |
|---|---|
| `🏗 Smart Contract Lab` (`contract-builder-lab`) | `Contract Builder Lab` |
| `⛓ Beacon Chain Lab` (`beacon-lab`) | `Beacon Chain Lab` |
| `🪙 Tokenization Lab` (`tokenization-lab`) | `Claim One Theme` (or `Classroom Contract Setup`) |
| `🛒 NFT Marketplace` (`nft-marketplace`) | `🛒 NFT Marketplace` |

**PASS** if all four headings render. **Note:** `🔎 Forensics Lab` is disabled by config and should
**not** appear in the nav — verify its absence.

### Test S5 — "Your Assets" panel
**Steps:** on `?view=live`, find and expand **`💼 Your Assets`**; `extract_text`.
**Expected:** an ETH balance card (**`Ethereum`** / **`ETH`**). After the student mints NFTs (§8) and
re-checks, an **`NFTs (N)`** sub-grid with thumbnails appears. **PASS** if the ETH card renders.

### Test S6 — Diagnostics
**Steps:** `navigate { url: BASE + "?view=diagnostics" }`; `extract_text`; if there's a run button,
click it. **Expected:** connectivity checks report chainId/block and pass (or clearly explain a
failure). **PASS** if diagnostics render and report a chain connection.

---

## 6. BEACON CHAIN LAB TESTS  *(Tokenization Mode = OFF)*

> **Precondition for all of §6:** assert `lab-api/beacon/tokenization-mode` → `enabled:false`. If ON,
> run Test I2 first. Also ensure a session is ACTIVE (Test I6) so blocks flow; if no instructor
> access, you can still test Join in the LOBBY but attestation needs an ACTIVE session.
> `navigate { url: BASE + "?view=beacon-lab" }`. Make sure the student wallet has ETH (Test S3).

### Test B1 — Join the validator pool
**Steps**
1. `extract_text`. Confirm the lab path heading and a **stake input** (default `32`) + **`Join`**.
2. Set stake: `type_text { target: { css: "input[type='number']" }, text: "32" }`.
3. `click { page_id, target: { text: "Join" } }`.
4. *(If the wallet is short on ETH, the app auto-funds; you'll briefly see `Funding your wallet from
   the class bank...`.)*
5. `wait_for { page_id, target: { text: "Joined" }, state: "visible" }`.

**Expected:** **`✅ Joined! Waiting to be seated in a committee (next slot)…`**, and the progress card
**`1. Join validator pool`** gets a check. **PASS** if "Joined" appears.
**Edge E-B1a:** stake < 32 → **`Minimum stake is 32 ETH`**. **Edge E-B1b:** clicking Join again →
**`Already joined…`**.

### Test B2 — Attest to a block
**Preconditions:** B1 done, session ACTIVE, at least one block exists in your committee.
**Steps**
1. `extract_text`. There's a **Block:** dropdown (auto-targets an attestable block) and an **`Attest`**
   button.
2. `click { page_id, target: { text: "Attest" } }`.
3. `wait_for` for any of: **`Attested to block`**, **`Attestation included`**, or **`deciding vote`**.

**Expected:** one of the success variants, e.g. **`✅ Attested to block #N (+0.002 ETH).`** or **`⚡
Your attestation was the deciding vote …`**. **PASS** if any attestation-success text appears.
**Edge E-B2a:** attesting twice to the same block → **`You already attested to block #N…`** and the
dropdown option shows `(attested)`.
**Edge E-B2b:** **`Attest`** is disabled when you're not in pool, not in the slot's committee, or
slashed — verify it's greyed in those states.

### Test B3 — Observe justification & finality
**Steps:** open the **Latest Blocks** table; `extract_text` / `extract_table_data` on it.
**Expected:** block **Status** values progress **Proposed → Justified → Finalized** over time. The
"Lab Activity" tracker checks **Observe a block become justified** and **…finalized**.
**PASS** if you observe at least one block reach **Justified** (Finalized if you wait long enough).

### Test B4 — Demo slash + report
**Steps**
1. `click { page_id, target: { text: "Demo slash" } }` (attests with a wrong hash on purpose).
2. `wait_for { target: { text: "Violation reported" }, state: "visible" }`.
   Expected: **`⚠️ Attestation rejected (wrong hash). Violation reported — report the slash to earn a
   reward.`** Your validator now shows **`⚠️ Slashed`** and **Attest** is disabled.
3. In **Pending Slashes**, click **Report slash** (earn reward).
   Expected: **`Slash reported! You earned a whistleblower reward.`**
**PASS** if both the violation and the report succeed.

### Test B5 — Block proposer / MEV (opportunistic)
This only fires when your validator is selected as proposer. If a purple panel **`🎲 You're the
block proposer for slot N!`** with a countdown appears:
1. Quickly `click` one of: **`📦 Vanilla block`**, **`🔁 Arbitrage bundle`**, **`🥪 Sandwich bundle`**.
2. `wait_for { target: { text: "You proposed the block" }, state: "visible" }`.
**Expected:** **`⚡ You proposed the block! Earned the block reward + … ETH MEV.`**
**PASS** if a proposal succeeds. If never selected during the session, mark **N/A**.

### Test B6 — Exit and rejoin
**Steps**
1. `click { page_id, target: { text: "Exit validator pool" } }` →
   `wait_for { target: { text: "Stake refunded" } }`. Expected: **`Exited! Stake refunded.`**
2. A **Rejoin** section appears. Set stake `32`, `click { target: { text: "Rejoin" } }` →
   `wait_for { target: { text: "Rejoined" } }`. Expected: **`✅ Rejoined! Waiting to be seated…`**
**Edge E-B6a:** a **slashed** validator cannot exit → **`Slashed validators cannot exit.`**
**PASS** if exit then rejoin both succeed.

### Test B7 — Block detail drill-down
**Steps:** click a row in **Latest Blocks**. Expected: a modal **`Slot N — Block #i`** with
**`Attestations (count)`**, **`Transactions in Chain Block`**, and **`Slashings`** sections.
**PASS** if the modal opens with these sections.

---

## 7. SMART CONTRACT LAB TESTS

> Works in either mode, but run it with the chain live (mode OFF) so deploys confirm quickly.
> `navigate { url: BASE + "?view=contract-builder-lab" }`. Wallet needs ETH (Test S3).
> The simplest path uses the **Contract Workshop** (no terminal): a template dropdown + **Compile** +
> **Deploy from my wallet**.

### Test C1 — Pick a template, compile, deploy
**Steps**
1. `extract_text`. Confirm heading **`Contract Builder Lab`** and the workshop with a template
   selector. Templates: **`SimpleStorage`**, **`Counter`**, **`Greeter`**, **`TipJar`**, **`ClassPoll`**,
   **`✍️ Write your own`**.
2. Select a template (e.g. SimpleStorage): `select_dropdown { target:{css:"select"}, value:"SimpleStorage" }`
   (or click the template card).
3. `click { page_id, target: { text: "Compile" } }` (button shows **`⚙️ Compile`**).
4. `wait_for { target: { text: "Compiled" }, state: "visible" }` → expect **`✅ Compiled SimpleStorage`**.
5. `click { page_id, target: { text: "Deploy from my wallet" } }` (**`🚀 Deploy from my wallet`**).
6. `wait_for { target: { text: "Deployed" }, state: "visible" }` → expect **`✅ Deployed
   SimpleStorage to 0x…`**. **Record the deployed address.**

**PASS** if both compile and deploy succeed and an address is shown.
**Edge E-C1a:** deploy with no wallet/funds → **`❌ Compile first and connect a wallet.`** or an
insufficient-funds error.
**Edge E-C1b:** introduce a syntax error in "Write your own" and Compile → **`❌ …`** compile error.

### Test C2 — Interact (read & write)
**Steps:** after deploy, an **Interact** panel renders auto-generated buttons for the contract's
functions.
1. Call a **write** function (e.g. SimpleStorage `set(uint256)`): type a value into its arg input,
   click the function's send button. `wait_for` a confirmation **`✅ confirmed · 0x…`**.
2. Call the matching **read** function (e.g. `get()` / the public var) → expect the value you set
   (e.g. `→ 42`).
**Edge E-C2a:** write before connecting a wallet → **`❌ Connect your wallet (Dashboard) to send`**.
**PASS** if a write confirms and the read reflects it.

### Test C3 — Chain Explorer verification
**Steps**
1. Scroll to the **Chain Explorer** (bottom of the lab). Search field placeholder: **`Search block #,
   tx hash, or address (0x…)`**.
2. `type_text` the **deployed contract address** from C1, then submit (press Enter or click search).
3. `extract_text`. Expected: an **address view** showing **`Contract · N bytes of code`**, balance,
   nonce, and a **Current state** section reading the contract's view functions.
4. Also search a **tx hash** (from C2's confirmation) → expect a transaction view with **`Success`**
   status and decoded function call + event logs.
**Edge E-C3a:** in **Classroom cache mode**, deep RPC detail lookups may be disabled with the notice
**`Classroom cache mode: recent blocks and transactions load from /chain-state…`** — that's expected,
not a failure.
**PASS** if the address resolves as a contract and the tx shows Success.

---

## 8. TOKENIZATION LAB TESTS  *(Tokenization Mode = ON)*

> **Precondition for all of §8:** assert `lab-api/beacon/tokenization-mode` → `enabled:true` (run
> Test I1 if not). Wallet needs ETH (Test S3). `navigate { url: BASE + "?view=tokenization-lab" }`.

### Test T1 — Contracts are ready
**Steps:** `extract_text`. Expected section **`1. Classroom Contract Setup`** showing
**`Classroom contracts are loaded. Continue by claiming exactly one theme.`** (green).
**Edge E-T1a (mode OFF / not deployed):** **`Classroom contracts are not configured yet. Ask the
instructor to run tokenization setup…`** — if you see this, mode is OFF; fix with Test I1.
**PASS** if contracts are reported loaded.

### Test T2 — Claim a theme
**Steps**
1. Section **`2. Claim One Theme`** shows theme cards each marked **`Available`**, **`Claimed by
   you`**, or **`Claimed by 0x…`**.
2. Click an **Available** theme card, then `click { target: { text: "Claim" } }`.
3. `wait_for { target: { text: "Theme claimed" }, state: "visible" }` → **`Theme claimed. You can now
   mint all five variants as one batch.`** The section then shows **`Theme locked`** with the theme's
   5-image grid.
**Edge E-T2a:** trying to claim a second theme — your wallet is locked; UI says you're locked to your
theme. **Edge E-T2b:** all themes taken → a color-fallback path appears (**`All themes are gone.
Color fallback is available.`**).
**PASS** if a theme is claimed/locked to your wallet.

### Test T3 — Mint exactly five
**Steps**
1. Section **`3. Mint Exactly Five`** shows your 5 variants and a button **`Mint All 5 Variants`**
   (color-fallback variant: **`Mint 5 Color NFTs`**).
2. `click { page_id, target: { text: "Mint All 5 Variants" } }`. Button shows **`Minting 5
   transactions…`** while working.
3. `wait_for { target: { text: "You minted your batch of 5 NFTs" }, state: "visible" }`.

**Expected:** the mint button **disappears** and is replaced by **`✓ You minted your batch of 5 NFTs.
Verify them in section 4 below, or list them for sale in the NFT Marketplace.`**
**Critical check (button must disappear):** after success, confirm there is **no** clickable "Mint"
button anymore (`find_interactive_candidates { intent:"mint button" }` should return nothing for
minting). This was a known bug — verify it's fixed.
**Edge E-T3a:** clicking mint when already minted should never show an error like "Mint unavailable";
the button should simply be gone.
**API assertion:** `lab-api/nft/state` → your address appears under minted batches with 5 token IDs.
**PASS** if 5 NFTs minted, button gone, success text shown.

### Test T4 — Verify ownership & metadata → explorer
**Steps**
1. Section **`4. Verify Ownership and Metadata`**. Click **`Verify ownership`** (shows **`Verifying…`**).
2. `wait_for { target: { text: "Verified ownership and metadata from the classroom chain cache" } }`.
   Each token row shows `#tokenId`, `ownerOf: 0x…`, `tokenURI: …`, and a `transfer tx: 0x…`.
3. Click a token row. Expected: section **`5. Chain Explorer`** opens to that token's **transfer
   transaction** (the mint Transfer from `0x0`), showing the tx detail — **not** the owner's address
   page. This was a known fix — verify the click leads to the **transfer tx**.
**PASS** if verification succeeds and clicking a token opens its transfer tx in the explorer.

---

## 9. NFT MARKETPLACE TESTS  *(Tokenization Mode = ON)*

> **Precondition:** mode ON; the seller wallet already minted NFTs (§8). `navigate { url: BASE +
> "?view=nft-marketplace" }`. For the **buy** test you need a **second** student context (§1.4).

### Test M0 — Marketplace renders & no instructor chrome
**Steps:** `extract_text`. Expected title **`🛒 NFT Marketplace`** and subtitle about listing/buying.
Sections: **`Listings (N)`**, **`Your NFTs (N)`**. **Verify the normal left-nav is present and there
is NO "Instructor Tools" panel** inside the marketplace (known fix). **PASS** if the marketplace
renders with the normal nav and no instructor panel, and there is **no** "Marketplace contract isn't
configured" warning (that warning must be gone in token mode).

### Test M1 — List an NFT for sale
**Steps**
1. In **`Your NFTs (N)`**, each owned token has a price input (placeholder **`ETH`**) and a **`List`**
   button.
2. `fill_and_click { page_id, fields:[{ target:{css:"input[placeholder='ETH']"}, value:"1.5" }],
   click_target:{ text:"List" } }`.
   *(First listing may trigger an approval tx — wait it out; the app calls setApprovalForAll.)*
3. `wait_for { target: { text: "Listed token" }, state: "visible" }` → **`Listed token #N for 1.5
   ETH.`**
**Expected:** the token now appears in **`Listings (N)`** (count increased) and a **`Your Listings
(N)`** section appears. Its image thumbnail renders (not "no image").
**Edge E-M1a:** price ≤ 0 → **`Enter a price in ETH greater than 0.`**
**PASS** if the listing appears in Listings with the correct price and a visible image.

### Test M2 — Images display
**Steps:** in **Listings** and **Your NFTs**, confirm thumbnails render (an `<img>` with a real
source), not the **`no image`** placeholder. Spot-check with
`execute_page_js`: `return [...document.images].filter(i=>i.naturalWidth>0).length` → should be > 0.
**PASS** if listing/asset images have non-zero natural width.

### Test M3 — Buy a listing (use the SECOND context = buyer)
**Steps (in buyer context `page_idB`)**
1. Ensure the buyer wallet has ETH (Test S3 in context B; needs ≥ listing price + gas).
2. `navigate { page_id: page_idB, url: BASE + "?view=nft-marketplace" }`; `extract_text`. Find the
   seller's listing in **Listings**.
3. `click { page_id: page_idB, target: { text: "Buy" } }`.
4. `wait_for { page_id: page_idB, target: { text: "It's now in your wallet" }, state: "visible" }` →
   **`Bought token #N. It's now in your wallet — you can relist it below.`**
**Expected:** the token moves to the buyer's **`Your NFTs`**; the listing disappears from **Listings**.
**API assertion:** `marketplace-state` → `tokensByOwner[buyerAddress]` now includes that token id.
**Edge E-M3a:** buying with insufficient funds → tx reverts, error shown.
**PASS** if ownership transfers to the buyer.

### Test M4 — Relist after buying
**Steps (buyer context):** the bought token now shows in **Your NFTs** with a **List** button. List
it at a new price (e.g. `2.0`), like Test M1. **PASS** if the relisted item appears in Listings.

### Test M5 — Remove / cancel your own listing
**Steps (seller context, on a listing you own):**
1. On your own listing in **Listings**, the button reads **`Remove listing`** (not "Buy").
   `click { target: { text: "Remove listing" } }` → `wait_for { target:{ text:"Cancelled listing" } }`
   → **`Cancelled listing #N.`**
2. Alternatively, in **`Your Listings`**, use the **`Cancel`** button (same effect) or **`Update
   price`** with a new value → **`Updated listing #N to … ETH.`**
**Expected:** the listing leaves **Listings**; the token returns to **Your NFTs**.
**Edge E-M5a:** you only see **Remove listing**/**Cancel** on **your own** listings; others' listings
show **Buy**.
**PASS** if you can remove your own listing and (optionally) update a price.

### Test M6 — Cross-view asset visibility
**Steps:** as a student who owns NFTs, check **both**:
- Marketplace **`Your NFTs (N)`** shows the collection.
- Dashboard **`💼 Your Assets`** (on `?view=live`) shows an **`NFTs (N)`** thumbnail grid.
Both read the same `/marketplace-state` cache (poll ~3–5s), so allow a few seconds to sync.
**PASS** if the same NFTs appear in both places.

---

## 10. CROSS-CUTTING EDGE CASES

| ID | Scenario | How to test | Expected |
|----|----------|-------------|----------|
| X1 | **Two-lab competition** | With mode **ON**, open `?view=beacon-lab` | Beacon shows no new blocks / paused; switching mode OFF resumes it. NFT contracts survive the toggle (mints from §8 still verify in §8/§9). |
| X2 | **Refresh persistence** | On `?view=nft-marketplace`, reload the page (`reload_page`) | You stay on the marketplace (not bounced to dashboard). Same for `?view=tokenization-lab`, `?view=beacon-lab`. |
| X3 | **Cache freshness** | Read `beacon-state` twice ~10s apart while a session is ACTIVE | The `currentSlot` / blocks length increases (instructor poller is alive). |
| X4 | **RPC/cache down** | If `beacon-state` or `marketplace-state` returns non-OK | UI shows graceful "cache unavailable / waiting" text, not a crash/white screen. |
| X5 | **Mint cap** | After minting 5 (§8), try to mint again | No mint button; never an error toast. The wallet is capped at one batch of 5. |
| X6 | **Disabled lab hidden** | Look for `🔎 Forensics Lab` in nav | It must be absent (disabled by config). |

---

## 11. FULL END-TO-END SCENARIO (the "definition of done" flow)

Run this as one continuous story; it exercises instructor + two students + all token/marketplace
pieces. It mirrors the production acceptance criteria.

1. **Instructor:** reach instructor dashboard (I0). Turn **Tokenization Mode ON** (I1). Assert
   `enabled:true`.
2. **Student A (context A):** create wallet (S1), top off (S3). Go to Tokenization lab; claim a theme
   (T2); mint 5 (T3); verify on chain + open a transfer tx (T4).
3. **Student A:** go to Marketplace; list one NFT for `1.5 ETH` (M1); confirm images render (M2).
4. **Student B (context B):** create wallet, top off; go to Marketplace; **buy** Student A's listing
   (M3); assert `tokensByOwner[B]` includes the token.
5. **Student B:** relist the bought NFT at a new price (M4).
6. **Student A & B:** confirm collections in both **Your NFTs** and dashboard **💼 Your Assets** (M6).
7. **Either student:** open the Chain Explorer and find the NFT **Transfer** transaction (the buy) —
   confirm the on-chain transfer is visible (this proves it's really on the blockchain).
8. **Instructor:** turn **Tokenization Mode OFF** (I2); confirm the Beacon lab resumes producing
   blocks (`beacon-state` slot increases).

**PASS** only if every numbered step passes. This is the headline result.

---

## 12. Teardown & reporting

1. `close_context` for every context you created.
2. Produce a final report:
   - The result table (Test ID, Title, PASS/FAIL/BLOCKED, Notes).
   - For each FAIL: the screenshot path + the first console/page error.
   - A one-line verdict per role: **Instructor — PASS/FAIL**, **Student — PASS/FAIL**, and per lab
     (Beacon / Smart Contract / Tokenization / Marketplace).
   - Confirm the lab was left in a sane state (note the final Tokenization Mode value).

---

## 13. Troubleshooting (when a step won't work)

| Symptom | Likely cause | Action |
|---|---|---|
| `?mode=instructor` lands on the student dashboard | Not instructor-authenticated | Confirm via `lab-api/session.isInstructor`. If false, mark all §4 BLOCKED. |
| Tokenization lab says "contracts not configured" | Tokenization Mode is OFF | Run Test I1 (turn mode ON). |
| Beacon lab shows no new blocks | Tokenization Mode is ON (beacon paused) | Run Test I2 (turn mode OFF). |
| "Mint"/"Join"/"Buy" click does nothing | A native dialog is waiting, or wallet has no ETH | Call `handle_dialog`; top off (S3); check `get_page_errors`. |
| Deploy/mint never confirms | Chain not advancing / RPC down | Check `beacon-state` is fresh; check Diagnostics (S6); on the host, `lab-manager.sh status ethereum_lab`. |
| Blank/white page or 5xx | Lab container or router down | On host: `docker ps`; restart with `lab-manager.sh stop/start ethereum_lab`; check the router. |
| Images show "no image" | Metadata/image cache not populated | Re-read `marketplace-state`; confirm the instructor poller resolved token metadata. |

---

## Appendix A — Button / label cheat-sheet (exact visible text)

**Student shell:** `👛 Create your first wallet`, `Create wallet`, `Got it — I've saved my
credentials`, `📋 Copy`, `💰 Top off`, `🔑 New`, `🧪 Diagnostics`, `💼 Your Assets`, `⚙️ Connection
Setup`, `🏗 Smart Contract Lab`, `⛓ Beacon Chain Lab`, `🪙 Tokenization Lab`, `🛒 NFT Marketplace`.

**Instructor:** `🎓 Instructor Dashboard`, `🎛️ Instructor Controls`, `🔄 Reset Chain`,
`🪙 Tokenization Mode: OFF` / `🔒 Tokenization Mode: ON`, `Slash`, `Set`, `Fill Bots and Start`,
`Join & Start`, `End Session`, `Reset Lab`.

**Beacon:** `Join`, `Attest`, `Demo slash`, `Exit validator pool`, `Rejoin`, `Report slash`,
`📦 Vanilla block`, `🔁 Arbitrage bundle`, `🥪 Sandwich bundle`. Headings: `Proof-of-Stake Lab Path`,
`🎛️ Lab Control Pane`, `Validator Pool`, `Latest Blocks`.

**Smart Contract:** `⚙️ Compile`, `🚀 Deploy from my wallet`, templates `SimpleStorage` / `Counter` /
`Greeter` / `TipJar` / `ClassPoll` / `✍️ Write your own`. Steps: `Write Your Contract`,
`Prerequisites`, `Deploy`, `Share`, `Interact (Partner)`, `Verify`. Explorer search placeholder:
`Search block #, tx hash, or address (0x…)`.

**Tokenization:** `1. Classroom Contract Setup`, `2. Claim One Theme`, `3. Mint Exactly Five`,
`4. Verify Ownership and Metadata`, `5. Chain Explorer`, `Claim`, `Mint All 5 Variants`,
`Mint 5 Color NFTs`, `Verify ownership`. Success: `✓ You minted your batch of 5 NFTs…`.

**Marketplace:** `🛒 NFT Marketplace`, `Listings (N)`, `Your NFTs (N)`, `Your Listings (N)`, `List`,
`Buy`, `Remove listing`, `Cancel`, `Update price`.

## Appendix B — Native dialogs (must use `handle_dialog`)

| Trigger | Type | Answer |
|---|---|---|
| Create wallet / 🔑 New | prompt (nickname) | `{ "action":"accept", "prompt_text":"Tester1" }` |
| Tokenization Mode → ON | confirm | `{ "action":"accept" }` |
| Reset Chain | confirm | `{ "action":"accept" }` |
| Beacon Reset Lab | confirm | `{ "action":"accept" }` |
| ⚙️ Account / info | alert | `{ "action":"accept" }` |

## Appendix C — Key API endpoints for assertions (all relative to `BASE`)

| Endpoint | Returns | Use |
|---|---|---|
| `lab-api/health` | health | pre-flight |
| `lab-api/session` | `{ isInstructor, hasCreatedWallet }` | confirm role |
| `lab-api/beacon/tokenization-mode` | `{ ok, enabled }` | confirm mode before lab tests |
| `beacon-state` | sessionState, committee, blocks, slashing | beacon assertions |
| `chain-state` | recent blocks + txs | explorer assertions |
| `marketplace-state` | listings, tokens, tokensByOwner, nft+marketplace addrs | marketplace assertions |
| `lab-api/nft/state` | claims, mintedBatches | tokenization assertions |
| `lab-api/fund-requests` | pending requests (instructor only) | fund-request test |

---

*Generated from a review of the Ethereum lab frontend (`App.jsx`, the four lab views, `InstructorView.jsx`),
the backend (`server/lab-api.js`), and the browser-puppet MCP reference. Strings are matched as
substrings to tolerate minor UI wording changes; when in doubt, trust the API assertions in Appendix C.*
