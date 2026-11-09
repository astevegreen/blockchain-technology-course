# Security alert triage

Every open GitHub security alert on `main`, sorted by lab and by whether it reaches students, with a mark per group:
**fix now**, **dismiss** (with the reason to give GitHub) or **defer** (to the planned student-VM and lab-image rebuild
on Ubuntu 24.04 / Debian 13 / Python 3.12 in `docs/follow-ups.md`). Read 8 Nov 2026 with `gh api` (Dependabot and
code-scanning alerts, `state=open`). The owner approved the dismiss list on 9 Nov 2026; see "Owner decisions".

**Totals (as of 8 Nov 2026):** 182 Dependabot alerts (7 critical, 96 high, 66 medium, 13 low) and 149 CodeQL alerts.
The groups below cover all of them: Dependabot 6 + 52 + 69 + 31 + 1 + 23 = 182; CodeQL 11 + 70 + 21 + 17 + 6 + 10 +
2 + 3 + 4 + 3 + 2 = 149.

| Mark | Dependabot | CodeQL | Groups |
|------|-----------:|-------:|--------|
| Fix now | 150 | 11 | D1, D2, D3, D6, C1 |
| Dismiss | 1 | 138 | D5, C2-C11 |
| Defer | 31 | 0 | D4 |

## Where alerts can reach students

- **Lab images.** The VM build loads every lab image (`vm-build/ubuntu-lab.pkr.hcl`, the `docker load` loop), so a
  package inside an image ships in the student VM. Lab services listen only on the classroom network or inside the
  student's own VM, behind the nginx router; none faces the internet unless an instructor runs `deploy-cloud.sh`.
- **`src.zip` and the VM's `/opt/dynamic-labs`** carry lockfiles and source as files. A lockfile there is not
  installed or run, so it adds nothing beyond what the images already hold.
- **The Pages site** serves `blockchain-course/assets/vendor/` (KaTeX, MathJax) to students' browsers.
- **Not shipped:** `tools/` (the repo's own hooks and checks) is in neither the site, `src.zip` nor the VM.

## Dependabot (182)

Dependabot's *security* updates are off for this repo (`automated-security-fixes`: `enabled: false`), and its weekly
version updates bump only direct dependencies, minor and patch grouped. That is why the transitive npm alerts and the
two major bumps (gunicorn 21 to 22+, Pillow 10 to 12+) have no PR.

| Group | Lab, manifest | Alerts (severity) | Reaches students | Mark |
|-------|---------------|-------------------|------------------|------|
| D1 | gunicorn 21.2.0 in `exercises/l03-i3-bgp-game`, `exercises/l03-i3-trust-game` and `instructor_auth_service` `requirements.txt` | 6 (6 high) | Yes: the server in three images, reached through the router | **Fix now** |
| D2 | Pillow 10.4.0 in `exercises/l03-i3-trust-game/requirements.txt` | 52 (4 critical, 33 high, 15 medium) | Ships in the trust-game image; not reachable | **Fix now** |
| D3 | `ethereum_lab/package-lock.json`, cleared by a lockfile refresh | 69 (3 critical, 37 high, 24 medium, 5 low) | Ships in the Ethereum lab image; mostly not reachable | **Fix now** |
| D4 | `ethereum_lab/package-lock.json`, held back by Hardhat 2's own ranges | 31 (11 high, 15 medium, 5 low) | Ships in the Ethereum lab image; not reachable | **Defer** |
| D5 | elliptic 6.6.1 in `ethereum_lab/package-lock.json` | 1 (low) | Ships; no patched version exists | **Dismiss** |
| D6 | `ethereum_lab/frontend/package-lock.json` | 23 (9 high, 12 medium, 2 low) | Build-only, except fflate, which is bundled into the page | **Fix now** |

- **D1, fix now.** gunicorn below 22.0.0 has request-smuggling advisories, and all three services run behind nginx,
  which is the setup those advisories describe. `instructor_auth_service` is the instructors' login. The fix is one
  pin per file. The BGP and trust games run gunicorn's eventlet worker, so rerun the `exercises` lab tests, plus a lab
  whose test signs in as instructor. Alerts 198, 200, 208, 210, 268, 269.
- **D2, fix now.** Pillow's advisories are about decoding untrusted images. The trust game uses Pillow only through
  `qrcode.make(join_url)` (`app.py:1218`), drawing a QR code from a URL the server builds, so none is reachable. It
  ships in a student-facing image, and the bump fits in the same rebuild and test as D1. Bump to the first release
  the alerts list as clearing every advisory (13.0.0), or to the latest release supporting Python 3.11. GitHub files the
  same package under two names: 31 alerts say `Pillow` and 21 say `pillow`. Alerts 212, 214-217, 221-267.
- **D3, fix now.** The Ethereum image runs `npm ci` without `--omit=dev` (`ethereum_lab/Dockerfile`, Stage 4)
  because the lab runs `hardhat node` and `hardhat run` at start, so Hardhat's whole tool tree ships even though
  GitHub calls most of it "development". For these 69, the lockfile's declared ranges already allow the patched
  version, so `npm update` in `dynamic-labs/ethereum_lab` (no major bumps, no `--force`) should clear them; this is an
  estimate from the ranges, and npm's result may differ by a few. The packages: axios 25 (Hardhat's gas reporter),
  fast-uri 11, handlebars 10 (the 3 critical, via solidity-coverage), js-yaml 8, immutable 3, tmp 2, minimatch 2,
  brace-expansion 2, path-to-regexp 2, form-data 1, follow-redirects 1, ws 1, picomatch 1. Two are reachable from a
  student's request: path-to-regexp (Express routing in `server/lab-api.js` and `server/frontend-server.js`) and
  ws 7.x (Hardhat node's WebSocket RPC). The rest sit in tools the lab never runs (coverage, gas reporting, contract
  verification). Rerun the `ethereum_lab` lab tests after the refresh.
  **Done 8 Nov 2026** (`npm update`, no major bumps, no `--force`): all the packages named above are now on patched
  versions (axios 1.21.0, handlebars 4.7.10, ws 8.22.2, path-to-regexp 8.4.2, tmp 0.2.6), and the `ethereum_lab` lab
  tests pass. `npm audit` on 8 Nov 2026 went from 54 findings (1 critical, 29 high, 11 moderate, 13 low) to 40 (0
  critical, 19 high, 8 moderate, 13 low). `npm audit` counts packages and GitHub counts advisories per package, so the
  two cannot be compared one to one, but the 3 critical and every D3 package are gone. The 40 left are all Hardhat 2
  and toolbox 6 chains (npm's only fix for each is Hardhat 3 or toolbox 7, a major move) and match D4 and D5 (undici,
  adm-zip, serialize-javascript, lodash, tmp via solc, uuid, cookie, @fastify/busboy, elliptic and the ethers v5 tree),
  plus solidity-coverage and hardhat-gas-reporter, which `npm audit` reports through their own dependencies. Dependabot
  will confirm the alert count on its next scan.
- **D4, defer.** These versions are pinned by Hardhat 2 and its plugins, so only the Hardhat 3 move clears them, and
  that move is already a follow-up for the lab's next rebuild (toolbox 7). Packages: undici 12, adm-zip 4,
  serialize-javascript 3, minimatch 2, brace-expansion 2, lodash 2, tmp 1, @fastify/busboy 1, ws 1, uuid 1,
  picomatch 1, cookie 1. None is reached by a student's request. They run only for compiler downloads (offline in
  the image), test runs and plugin tasks. Alerts 42, 47, 59, 62, 64, 65, 71, 84, 102, 103, 114, 116, 118, 119, 122, 126,
  141-143, 156, 158, 159, 163, 168, 178, 188, 190-192, 194, 275.
- **D5, dismiss as "tolerable risk".** elliptic sits under ethers v5 inside `@nomicfoundation/hardhat-verify`, which
  the lab never runs, and no fixed version is published. Hardhat 3 drops it. Alert 44.
- **D6, fix now.** vite, rollup, postcss, Babel, browserslist and their helpers run only in the image's build stage;
  the final image serves the built `dist/` through `server/frontend-server.js`, so the Vite dev server never runs.
  fflate (2 alerts, via three-stdlib) is bundled into the page but only decompresses the lab's own 3D assets. A
  lockfile refresh clears all 23, and it goes in the same change and test as D3. Alerts 1, 3-7, 16-18, 20, 25, 26,
  30, 32-41.
  **Done 8 Nov 2026:** `npm update` in `ethereum_lab/frontend`; `npm audit` went from 10 findings (7 high) to 0.

## CodeQL (149)

| Group | Rule, where | Alerts | Mark | Reason to give GitHub |
|-------|-------------|-------:|------|-----------------------|
| C1 | `js/incomplete-html-attribute-sanitization` (`bitcoin-graph/app/static/app.js` 7, `lane-service/wrapper.html` 2), `js/xss-through-exception` (`ethereum_lab/frontend/public/progress-display.html`), `js/insecure-randomness` (`exercises/l03-i3-bgp-game/app/static/js/student.js`) | 11 | **Fix now** | (fixed, not dismissed) |
| C2 | `py/stack-trace-exposure`, `quiz-engine-v2` (instructor 61, student 9) | 70 | **Dismiss** | False positive |
| C3 | `py/stack-trace-exposure`, `hlf` 16 and `lane-service` 5 | 21 | **Dismiss** | Won't fix |
| C4 | `py/path-injection` (`hlf` 5, `lane-service` 7), `js/path-injection` (`ethereum_lab/server/lab-api.js` 5) | 17 | **Dismiss** | False positive |
| C5 | `py/command-line-injection` (critical), `py/sql-injection`, `py/reflective-xss`, `py/cookie-injection` 2, `py/url-redirection` | 6 | **Dismiss** | False positive |
| C6 | `js/incomplete-sanitization` 9 and `js/incomplete-multi-character-sanitization` 1 in `blockchain-course/assets/vendor/` (KaTeX 0.17.0, MathJax 2.7.9) | 10 | **Dismiss** | Won't fix |
| C7 | `js/incomplete-sanitization`, `ethereum_lab/frontend` `TerminalPopup.jsx:133` and `InlineTerminal.jsx:164` | 2 | **Dismiss** | False positive |
| C8 | `js/xss-through-dom`, `dex/gateway/static/sign/swap.js:81`, `tokens/gateway/static/sign/mint.js:55,94` | 3 | **Dismiss** | False positive |
| C9 | `js/missing-rate-limiting`, `ethereum_lab/server/lab-api.js` 3 and `frontend-server.js` 1 | 4 | **Dismiss** | Won't fix |
| C10 | Lab behaviour by design: `py/bind-socket-all-network-interfaces` (`bitcoin/workstation/agent.py:175`), `py/clear-text-logging-sensitive-data` (`cryptography/lab_cli.py:112`), `py/clear-text-storage-sensitive-data` (`lane-service/labs/ethereum.py:266`) | 3 | **Dismiss** | Won't fix |
| C11 | `js/redos`, `tools/hooks/shell-reader.mjs:31` | 2 | **Dismiss** | Won't fix |

- **C1, fix now: the only real CodeQL findings, all small. The 9 escaping alerts were fixed on 8 Nov 2026**
  (both helpers now escape `"` and `'`; the other C1 alerts remain). The two `escapeHtml` helpers (`bitcoin-graph/app/static/app.js:72`,
  `lane-service/wrapper.html:690`) escape `&`, `<` and `>` but not quotes, and their output goes into quoted HTML
  attributes. Today's values are Bitcoin addresses, txids and the lab's own exercise titles, which hold no quotes,
  and the one free-text value (a node label) is the student's own, saved in their own browser. So nothing is
  exploitable today, but one more escape per helper (`"` and `'`) closes it. `progress-display.html:265` put an
  error message into `innerHTML`; it now uses `textContent` (done 8 Nov 2026). `student.js:49` falls back to `Math.random()` for the player's
  id when `crypto.randomUUID` is missing, and `crypto.randomUUID` works only in secure contexts, so on a no-TLS
  classroom LAN the fallback is what runs and another student could guess a player's id. `crypto.getRandomValues`
  works without TLS. All of these files reach students. Alerts 115, 131-139, 149. Rerun the bitcoin-graph, lane and
  `exercises` lab tests.
- **C2, false positive.** Each alert returns `str(exc)` for one of the engine's own error classes (`AttemptError`,
  `GradingError`, `QuizVersionError`, `TemplateError` and others), messages the code writes for the user. No stack
  trace is returned. Alerts 41-110.
- **C3, won't fix.** These do return the text of a caught exception (`Exception` in 4, `OSError` and subprocess errors
  in others), or a Fabric CLI result in the 13 `hlf_router.py` alerts, but never a traceback. The Fabric lab shows
  peer CLI output on purpose, the routes serve the lab's own network, and the text adds nothing a student can't see
  in their own lab terminal. Alerts 20-40.
- **C4, false positive.** Each path is built from a session id that is checked as a UUID first: `is_valid_uuid` in
  `hlf/web_service/claims.py:59`, used by `progress_routes.py:44,95` and `claim_routes.py`; `_require_active_session`
  in `lane-service/labs/ethereum.py:215`, which also requires a live claim; and `isUuid` in `lab-api.js:116` with
  `SESSION_NS_RE` for the namespace (`lab-api.js:597`). `hlf/web_service/lanes.py:390` builds its path from a lane id
  that `_valid` checked. Alerts 4-15, 140-144.
- **C5, false positive.** `hlf/web_service/lanes.py:163` (the critical) runs `docker compose` as an argument list, with
  no shell, and a lane id that `_valid` checked. The cookie, redirect and reflected-XSS alerts in
  `hlf/web_service/claim_routes.py:112-115` and `lane-service/lab_blueprint.py:346-349` carry a UUID that passed
  `is_valid_uuid` first. `quiz-engine-v2/app/migrate.py:212` takes table names from a fixed list (`IMPORT_ORDER`)
  and refuses any column not in the table's schema (`migrate.py:200`); the values are bound parameters. Alerts 3,
  19, 111-114.
- **C6, won't fix.** Upstream KaTeX and MathJax code, vendored unchanged (including KaTeX's `src/` files). Change it
  only by upgrading the library. Alerts 119-128.
- **C7, false positive.** The value is the lab's own RPC URL from its runtime config, written into a command the page
  types into the student's own terminal. A student can type the same thing themselves. Alerts 129, 130.
- **C8, false positive.** `swap.js` and `mint.js:55` append a DOM node, not HTML. `mint.js:94` sets an `<img>` source from
  the badge's token URI, and an image source does not run script. Alerts 116-118.
- **C9, won't fix.** Lab services on the classroom network. Two of the routes are instructor-only
  (`/beacon/reset`, `/beacon/tokenization-mode`), one resets the caller's own session, and one is the static-file
  fallback. Alerts 145-148.
- **C10, won't fix.** The Bitcoin workstation agent must accept peers on its container's interfaces; the
  cryptography lab prints the message a student has just decrypted, which is the exercise; the arcade signing secret
  is a server-side key file in the lane service's runtime folder, like any key file. Alerts 16-18.
- **C11, won't fix.** Repo tooling, not shipped: the hook reads the agent's own shell commands, and the worst case is a
  slow hook. Alerts 150, 151.

## ## Owner decisions

- **The dismiss list** (D5 and C2-C11: 1 Dependabot and 138 CodeQL alerts): approved as written by the owner and
  dismissed on 9 Nov 2026, each alert with its group's reason and a comment naming the group and this file. Open
  after that: the 11 C1 alerts and 181 Dependabot alerts (fix now and defer).
- **Dependabot security updates**: turned on by the owner's decision on 9 Nov 2026, so transitive fixes like D3 and
  D6 now arrive as PRs, one per advisory, as new advisories land.
