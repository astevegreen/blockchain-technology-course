# Clear the follow-ups list (orchestrator prompt)

A prompt for one session that starts child sessions to clear `docs/follow-ups.md`, as it stood on 31 Oct 2026
(61 items). Start that session **in the desktop app, on Opus, medium effort**: a session cannot start a child on a
pricier model or a higher effort than its own, and the app refuses session starts typed over Remote Control.
Everything below the line is the prompt.

---

## Your job

You orchestrate. Start the child sessions below, in the order below, and relay their results to the owner. Do no
item's work yourself: no edits, no commits. Each brief under "Child briefs" is the child's whole prompt: pass it
as `prompt` with "Rules for every child" appended, word for word.

The owner's words, to quote in `Requested:` trailers:
- On 31 Oct 2026 the owner asked: "How many sessions and what model/effort level would be the most efficient in
  resolving all outstanding items I. The follow-ups?"
- Then, on the plan: "Yes to both and the cloud DNS." "Both" means: write these briefs, and fence the lab tests
  from students in session 8. "The cloud DNS" means: do the cloud DNS items (session 7).

## How to start each child

- Call `mcp__ccd_session__start_session` with `initiation: "user_asked"`, `context: "fresh"`, and the `model`,
  `effort` and `use_worktree` the brief gives. A hook refuses a start with no model or effort.
- If the app refuses because the message came over Remote Control, tell the owner in one line and start the children
  on their next message typed in the desktop app.
- Before starting several at once, call `mcp__ccd_session__mark_chapter` with a short title for the batch.

## Order

1. **Lane A, now, side by side:** sessions 1 to 4. Session 1 works in the main checkout (it renders lessons, and
   Quarto fails under `.claude/worktrees`). Sessions 2 to 4 change only `quizes/`, so they each get a worktree.
2. **Lane B, one at a time, in the main checkout:** sessions 5, 6, 7 and 8. Start 5 once session 1 has pushed.
   Start each of the others once the one before it has pushed. They run Docker lab tests with `--fresh-start`, which
   wipes every lab's containers, so two must never overlap.
3. **Session 9:** once sessions 2 and 5 have pushed. Worktree.
4. **Session 10:** last, once every other session has pushed and none is running. Main checkout.

## When a child reports

- Check before relaying: `git fetch` and `git log origin/main` shows its commits, and the bullets it fixed are gone
  from `docs/follow-ups.md` on `origin/main`. A report alone is not proof.
- Relay to the owner in two or three lines: what landed, and what the child left open or flagged.
- A child asks a question: answer it if this prompt or `CLAUDE.md` settles it. A content decision (CLAUDE.md
  rule 4) goes to the owner, with the child's recommendation.
- A child fails, or reports it could not finish at medium effort: do not retry at high (you cannot start one).
  Tell the owner what failed. They can restart it at high from the desktop.
- When session 10 has pushed, give the owner a final table: each session, its commits, and what is still on
  `docs/follow-ups.md`. These are expected to remain, waiting on the owner: assigned readings for 04-FO, 05-FO and
  01-PC; trying the exchange and bridge lab with a real class; the `CourseTokens.sol` comment, which waits for the
  next chain rebuild.

## Rules for every child

(Append this section to every brief.)

> You are clearing items from `docs/follow-ups.md`. Read each bullet named below in that file before you start: it
> names the file, the lines and the problem. `CLAUDE.md` applies in full: the check, rule 4, the `source` skill for
> any fact without a `Blockchain.bib` key, and the Finishing section (the `reviewer` agent and
> `node tools/second-look.mjs` for new or reworked slides and for any quiz-bank edit; the rail audit for any rail).
> Delete each bullet you finish in the same commit as its fix. If an item turns out to need an owner decision,
> rewrite its bullet to say so and tell the orchestrator. One commit per item or per closely related group. Each
> commit's `Requested:` trailer quotes the owner: "How many sessions and what model/effort level would be the most
> efficient in resolving all outstanding items I. The follow-ups?" (session 7's DNS commits and session 8's
> fencing commit add "Yes to both and the cloud DNS."). In a worktree: commit on your branch, then
> `git fetch && git rebase origin/main && git push origin HEAD:main`. If the check has to render a lesson there and
> fails with "Unable to read the extension 'aci'", robocopy the worktree (minus `_site`, `.quarto`,
> `node_modules`) to `C:\tmp\<name>`, commit from that copy, and push from the worktree. In the main checkout:
> stage only your own files. Another session may be working there. End with the CLAUDE.md summary.

## Child briefs

### Session 1: student-site fixes
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: false`.

> Fix these lesson and page bullets in `docs/follow-ups.md`:
> - Lessons: the 01-EF gas slides' "block proposer" tip wording; `06-BF` line 95 speaker notes (signature order);
>   `02-FO` part 1's "day 3" pointers (that bullet, plus the duplicate under Labs that starts
>   "`lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd` (about lines 61, 372, 554)"); 01-FO's BTC-e
>   slide context line (cited, through the `source` skill); the `{dot}` cell options (`#|` to `//|`) and the
>   three-digit fill colours in 02-BF, 02-DS, 04-AS, 05-AS, 02-FO, 06-FO and 07-FO.
> - Quizzes section, lesson half only: 06-EF's DAO fork block and 02-EF's "withdraw" wording. Leave quiz files to
>   the other sessions.
> - Labs section: the `01-CM` line 525 "In a memo" wording; the `01-PC` line 306 "delegated Energy" wording; the
>   tamper-ledger focus bug; the signatures page's "Browser note".
> - Notion and documents: `docs/build-spec.md` line 83's token lesson.
> After the `{dot}` change, render each of the seven lessons and check every changed diagram slide in a browser for
> overflow (Playwright MCP over `python -m http.server --directory blockchain-course/_site`; `file:` URLs are
> refused). Slides fit 1280x800 with the body under 700px. Run the `reviewer` agent and `second-look.mjs`.

### Session 2: existing quiz banks
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: true`.

> Fix these Quizzes bullets in `docs/follow-ups.md`, following `quizes/QUIZ_BANK_GENERATION_GUIDE.md`,
> `quizes/LESSON_SYNTHESIS_GUIDE.md` and `quizes/QUIZ_ENGINE_JSON_SPEC.md`:
> - the 01-FO bank and syntheses (questions on the nine new slides, retrace or retire q10, drop Ronin);
> - the 02-IN bank only (retrace q1; a question on "A blockchain is a record, not a currency"). Leave the day 2
>   daily quiz to session 9, and rewrite the bullet so only that part is left;
> - the 03-EF bank and synthesis "compensates the proposer" wording, and 03-EF questions on the DEX,
>   sandwich-attack and look-alike slides;
> - 02-AS questions that lean on the four slides hidden as moved to 01-PC;
> - the 04-BF and 01-FO syntheses that describe hidden slides;
> - the 02-BF question on reading the mempool view.
> Every answer traces to a visible slide. Leave the 04-FO/05-FO/01-PC reading-deck bullet: it waits on the owner.
> Rebuild `quizes/dist/` only with its script. Run the `reviewer` agent and `second-look.mjs`.

### Session 3: new forensics banks, part 1
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: true`.

> Write a quiz bank and a lesson synthesis for each of 03-FO, 06-FO and 07-FO (their three bullets under Quizzes in
> `docs/follow-ups.md`), per `quizes/QUIZ_BANK_GENERATION_GUIDE.md`, `quizes/LESSON_SYNTHESIS_GUIDE.md` and
> `quizes/QUIZ_ENGINE_JSON_SPEC.md`. Model them on an existing forensics bank of the same shape. Cover visible
> slides only. Every answer traces to a slide. Read each lesson by offset: they run long. Rebuild `quizes/dist/` only
> with its script. Run the `reviewer` agent and `second-look.mjs`.

### Session 4: new forensics banks, part 2
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: true`.

> As session 3's brief, for 08-FO, 09-FO and 10-FO (their three bullets under Quizzes in `docs/follow-ups.md`).
> Write a quiz bank and a lesson synthesis for each, per `quizes/QUIZ_BANK_GENERATION_GUIDE.md`,
> `quizes/LESSON_SYNTHESIS_GUIDE.md` and `quizes/QUIZ_ENGINE_JSON_SPEC.md`. Model them on an existing forensics bank.
> Cover visible slides only. Every answer traces to a slide. Rebuild `quizes/dist/` only with its script. Run the
> `reviewer` agent and `second-look.mjs`.

### Session 5: lab tooling and playbook walks
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: false`.

> Fix these Labs bullets in `docs/follow-ups.md`: the `run.sh` fresh-start lists missing `explorer` and `tokens`
> (two bullets); `lab-manager.sh` line 931 `force_rebuild`; `course-site` serving a stale site until rebuilt (pick
> the fix and say why); `vm-build/prepare-docker-image-bundles.sh` missing `dex` and `tokens`; pinning mempool and
> electrs in `dynamic-labs/bitcoin/mempool/Dockerfile` (see `docs/spikes/mempool.md`). Then walk the Bitcoin trace
> and CoinJoin trace browser playbooks (`dynamic-labs/regression-tests/agent/<lab>/`) on this desktop and fix what
> they find. Docker: start Docker Desktop, check `docker ps` first (`--fresh-start` wipes every lab), and run each
> changed lab's suite in WSL as CLAUDE.md says. Paste the results. After the push, watch the Lab Tests run.

### Session 6: Fabric lab
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Fix the five HLF bullets under Labs in `docs/follow-ups.md`: the peer and orderer outages trusting the cached
> status; the transaction detail's null `msp_id` ("Endorsed by: none"); Meridian (Org5) labelled "read-only" in
> about 20 places (relabel "member, not an endorser"); `run.sh --fresh-start` deleting the tracked
> `install-fabric.sh`; `run.sh` line 113's `--network bridge` default. If the runtime is already missing, restore
> it with `git checkout` and `HLF_ALLOW_RUNTIME_DOWNLOADS=1`. Prove each fix live, with
> `wsl -d Ubuntu -- bash dynamic-labs/regression-tests/automated/hlf/run.sh --fresh-start` (check `docker ps`
> first). Paste the results. After the push, watch the Lab Tests run.

### Session 7: lab security, routing and cloud DNS
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Fix these Labs bullets in `docs/follow-ups.md`:
> - The gateway passes signed transactions from the cUSD issuer, bridge owner and relayer keys (exchange and bridge
>   lab), and from the token lab's issuer: refuse those senders at the gateway.
> - `/labs/explorer/`, `/labs/tokens/` and `/labs/dex/` redirect to a subdomain, which fails when students reach
>   the site by bare IP (`dynamic-labs/router/routes.conf`): make them work by IP too.
> - Cloud DNS (the owner said yes): make `dynamic-labs/deploy-cloud.sh` request one certificate covering
>   `$DOMAIN`, `explorer.`, `tokens.`, `dex.` and `dex-l2.` before it calls certbot. Have it check that each name
>   resolves to this host, and if not, print the DNS records the deployer must create. Document those records in
>   `dynamic-labs/README.md`. Creating the records stays with whoever deploys, at their DNS provider: say so.
> - Simulate a whole class on the exchange and bridge lab: 40 seats swapping against one pool in one L1 block, with
>   the relayer finalizing their deposits (`dynamic-labs/dex/relayer/relayer.py`). Fix what breaks. Rewrite that
>   bullet so it says what the simulation showed and that a real class is still untried.
> Leave the `CourseTokens.sol` bullet: it waits for the next chain rebuild. Run each changed lab's suite in WSL with
> `--fresh-start` (check `docker ps` first). Paste the results. After the push, watch the Lab Tests run.

### Session 8: rails (CI coverage, reviewer, fencing tests from students)
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Fix these bullets in `docs/follow-ups.md`:
> - CI Lab Tests: the explorer, token, exchange and bridge, wallet, Tron, Bitcoin trace and CoinJoin trace labs are
>   not in `.github/workflows/lab-tests.yml` / `tools/lab_tests.py`. Add each one the runner can carry. Note in
>   `tools/lab_tests.py` why any is left out (image size, run time).
> - `.claude/agents/reviewer.md`'s "product first" lab bullet: match `.claude/skills/lab/SKILL.md` (questions first).
> - Fence from students (the owner said yes: "Yes to both and the cloud DNS."): `dynamic-labs/regression-tests/`
>   (automated suites and agent playbooks) and the explorer lab's chain build scripts. Per CLAUDE.md rule 1, add
>   `-x` entries in `.github/workflows/pages.yml` and removals in `.github/workflows/vm-build.yml` in the same
>   change, and confirm nothing students run needs them. This settles the three "students receive" bullets.
> These are rails: run `second-look.mjs` and follow its rail-audit verdict as CLAUDE.md says. After the push, watch
> the Lab Tests run until every added lab passes on GitHub. Paste the result.

### Session 9: quiz questions on the labs
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: true`.

> Add quiz questions for what the labs teach (the "No quiz questions test the ..." bullets in `docs/follow-ups.md`):
> the exchange and bridge lab, the wallet lab, the Tron lab, the Bitcoin trace lab and the CoinJoin trace lab. Also
> add the day 2 daily quiz question on "A blockchain is a record, not a currency". Put each in the daily bank of the
> day the lab runs (`docs/build-spec.md` has the day map), per `quizes/QUIZ_BANK_GENERATION_GUIDE.md`. Every answer
> traces to what the lab shows, as recorded in its `quizes/facts.json` or worksheet. Pitch difficulty to match the
> existing daily banks. If the guide does not settle a question's difficulty, ask the orchestrator. Rebuild
> `quizes/dist/` only with its script. Run the `reviewer` agent and `second-look.mjs`.

### Session 10: line endings
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: false`.

> Clear the CRLF bullet under Labs in `docs/follow-ups.md` (about 1,700 files outside `dynamic-labs/`; check with
> `git ls-files --eol`). `dynamic-labs/` was fixed on 31 Oct by rewriting the working copies, not with
> `checkout-index`. First find out whether the index or only this checkout holds CRLF, and fix it at that level so
> it stays fixed (`.gitattributes` if needed). Confirm `git status` is clean before you start: no other session may
> have work in progress. Run `python tools/check.py --all --render` in the background and paste the result.
