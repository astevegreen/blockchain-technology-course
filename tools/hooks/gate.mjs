// Stop: run `python tools/check.py` before Claude may finish.
// 1. Skips at once when the session changed nothing, or nothing since the last green run.
// 2. On failure, blocks finishing (exit 2) with at most 40 lines of failures.
// 3. A stop retried with nothing changed since the last failure (stop_hook_active) reuses that failure
//    instead of rerunning a check that renders lessons. A time-out is never reused: a busy computer, not the
//    change, may have caused it, so the next stop runs the check again.
// 4. After 5 blocks in a row it tells Claude to report the failure, then lets it stop.
// It never changes files in the repository.
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { readInput, git, limitLines, runPython } from "./shared.mjs";

const MAX_BLOCKS = 5;
const TIMED_OUT = /timed out after \d+s/; // runPython's own time-out, or one inside check.py
const input = await readInput();
const cwd = input.cwd ?? process.cwd();
const root = git(["rev-parse", "--show-toplevel"], cwd);
if (!root) process.exit(0); // not a git repository: nothing to check

const stateDir = path.join(os.tmpdir(), "blockchain-course-gate");
mkdirSync(stateDir, { recursive: true });
const key = createHash("sha256").update(`${input.session_id ?? "none"}|${input.agent_id ?? ""}|${root}`).digest("hex").slice(0, 16);
const stateFile = path.join(stateDir, `${key}.json`);
const state = (() => {
  try { return JSON.parse(readFileSync(stateFile, "utf8")); } catch { return { blocks: 0, green: null }; }
})();
const save = () => writeFileSync(stateFile, JSON.stringify(state));

// What the session changed: uncommitted work, plus commits not yet on origin/main.
const status = git(["status", "--porcelain", "--untracked-files=all"], root) ?? "";
const head = git(["rev-parse", "--verify", "-q", "HEAD"], root);
const base = ["origin/main", "main"].find((b) => git(["rev-parse", "--verify", "-q", b], root));
const ahead = head && base ? Number(git(["rev-list", "--count", `${base}..HEAD`], root) ?? 0) : head ? 1 : 0;
if (!status && !ahead) process.exit(0);

// Skip when nothing changed since the last green run (questions asked mid-task stay instant).
const fingerprint = (() => {
  const h = createHash("sha256").update(`${head}\n${status}\n`);
  h.update(git(["diff", "HEAD", "--no-ext-diff", "--binary"], root) ?? "");
  for (const line of status.split("\n").filter((l) => l.startsWith("??"))) {
    const f = path.join(root, line.slice(3));
    try { const s = statSync(f); h.update(`${f}:${s.size}:${s.mtimeMs}\n`); } catch {}
  }
  return h.digest("hex");
})();
if (state.green === fingerprint) process.exit(0);

if (state.blocks >= MAX_BLOCKS) {
  state.blocks = 0;
  save();
  process.exit(0);
}

if (!existsSync(path.join(root, "tools", "check.py"))) {
  process.stdout.write(JSON.stringify({ systemMessage: "Gate not run: tools/check.py is missing. Changes in this session are unchecked." }));
  process.exit(0);
}

let output;
if (input.stop_hook_active && state.failed === fingerprint && state.output) {
  output = state.output; // nothing changed since the last block: same failure
} else {
  const r = runPython(["tools/check.py", "--stamped"], { cwd: root, timeout: 570_000 });
  if (r.missing) {
    process.stdout.write(JSON.stringify({ systemMessage: `Gate not run: ${r.output} Changes in this session are unchecked.` }));
    process.exit(0);
  }
  if (r.status === 0) {
    state.blocks = 0;
    state.green = fingerprint;
    state.failed = null;
    state.output = null;
    save();
    process.exit(0);
  }
  output = r.output || "python tools/check.py failed with no output.";
}

state.blocks += 1;
state.failed = TIMED_OUT.test(output) ? null : fingerprint;
state.output = output;
save();
const header = state.blocks >= MAX_BLOCKS
  ? `The check has failed ${MAX_BLOCKS} times in a row. Stop working on it now: report the failures below to the owner under Unsure about.`
  : `python tools/check.py failed (attempt ${state.blocks} of ${MAX_BLOCKS}); you can't finish until it passes. Fix your change, not the check.`;
process.stderr.write(`${header}\n${limitLines(output, 40)}\n`);
process.exit(2);
