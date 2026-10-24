// `node tools/sprint/ci-watch.mjs <sha>`: waits for the Lab Tests run on a commit pushed to main and prints one line
// of JSON, {workflow, sha, run, conclusion, url, failed}. The integrator runs it after a push that changed
// dynamic-labs/, tools/lab_tests.py or the workflow (docs/sprint.md, Flow). Exits 0 when the run passed, 2 when it
// failed or was cancelled (act on `do`: revert the batch), 1 when it could not tell (`do` says whether to run it
// again or stop and report). It only reads:
// `gh run list` and `gh run view`.
import { spawnSync } from "node:child_process";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "..", "..");
export const WORKFLOW = "lab-tests.yml";
const USAGE = "usage: node tools/sprint/ci-watch.mjs <commit sha>";
// GitHub starts a run a few seconds after the push; a lab job may take its full 30 minutes, and jobs queue. Each
// wait stays under an hour: the archiver archives a session with no event in 60 minutes, so a longer run is
// watched again.
const FIND_FOR_MS = 3 * 60 * 1000;
const WAIT_FOR_MS = 45 * 60 * 1000;
const POLL_MS = 30 * 1000;
const STOP = "Stop and report this output on the sprint log issue.";

function runGh(args) {
  const r = spawnSync("gh", args, { cwd: ROOT, encoding: "utf8", windowsHide: true }); // NOSONAR (javascript:S4036)
  if (r.error) throw new Error(`could not start gh: ${r.error.message}`);
  if (r.status !== 0) throw new Error(`gh ${args.slice(0, 2).join(" ")} failed: ${(r.stderr || r.stdout).trim().split(/\r?\n/)[0]}`);
  return r.stdout;
}
const sleep = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

export function watch(sha, { gh = runGh, wait = sleep, now = Date.now } = {}) {
  const out = (code, fields) => ({ code, line: JSON.stringify({ workflow: WORKFLOW, sha, ...fields }) });
  if (!/^[0-9a-f]{7,40}$/i.test(sha ?? "")) return { code: 1, line: JSON.stringify({ error: USAGE, do: STOP }) };
  try {
    const start = now();
    let found = null;
    for (;;) {
      const runs = JSON.parse(gh(["run", "list", "--workflow", WORKFLOW, "--commit", sha, "--json", "databaseId,status,conclusion,url,headSha"]));
      found = runs[0] ?? null; // newest first
      if (found || now() - start >= FIND_FOR_MS) break;
      wait(10 * 1000);
    }
    if (!found) {
      return out(1, {
        run: null,
        conclusion: "none",
        url: null,
        failed: [],
        do: `No ${WORKFLOW} run started for this commit within 3 minutes. Check that the push changed dynamic-labs/, tools/lab_tests.py or the workflow; if it did, ${STOP.charAt(0).toLowerCase()}${STOP.slice(1)}`,
      });
    }
    let view;
    for (;;) {
      view = JSON.parse(gh(["run", "view", String(found.databaseId), "--json", "status,conclusion,url,jobs"]));
      if (view.status === "completed") break;
      if (now() - start >= WAIT_FOR_MS) {
        return out(1, { run: found.databaseId, conclusion: "timed out", url: view.url, failed: [], do: "The run had not finished after 45 minutes: run this again, up to 3 times, then stop and report this output on the sprint log issue." });
      }
      wait(POLL_MS);
    }
    const failed = (view.jobs ?? []).filter((j) => j.conclusion && !["success", "skipped", "neutral"].includes(j.conclusion)).map((j) => j.name);
    if (view.conclusion === "success") return out(0, { run: found.databaseId, conclusion: "success", url: view.url, failed });
    return out(2, {
      run: found.databaseId,
      conclusion: view.conclusion || "unknown",
      url: view.url,
      failed,
      do: "Main is red: revert the batch (sprint-integrate, When main goes red), then send the issues back.",
    });
  } catch (e) {
    return { code: 1, line: JSON.stringify({ workflow: WORKFLOW, sha, error: e.message, do: STOP }) };
  }
}

if (import.meta.main) {
  const r = watch(process.argv[2]);
  process.stdout.write(`${r.line}\n`);
  process.exitCode = r.code;
}
