import { test } from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { runHook, tempRepo, writeFiles, sh } from "./test-helpers.mjs";

// A stub tools/check.py in each temp repo: logs each run, then passes or fails on FAKE_CHECK.
const log = path.join(mkdtempSync(path.join(os.tmpdir(), "bc-fake-check-")), "runs.log");
const STUB = {
  "tools/check.py": `import os, sys
with open(${JSON.stringify(log)}, "a") as f:
    f.write(" ".join(sys.argv[1:]) + "\\n")
if os.environ.get("FAKE_CHECK") == "fail":
    print("[lesson lint]\\n  blockchain-course/lessons/a.qmd:12: div {.notes} is never closed\\ncheck: FAILED")
    sys.exit(1)
print("check: passed (1 checks, 0.1s)")
`,
};

const runs = () => (existsSync(log) ? readFileSync(log, "utf8").split("\n").filter(Boolean).length : 0);
const stop = (cwd, session_id, FAKE_CHECK = "pass", stop_hook_active = false) =>
  runHook("gate.mjs", { cwd, session_id, hook_event_name: "Stop", stop_hook_active }, { env: { FAKE_CHECK } });

test("finishes instantly when nothing changed", () => {
  const repo = tempRepo(STUB);
  const before = runs();
  const r = stop(repo, randomUUID());
  assert.equal(r.status, 0);
  assert.equal(r.stdout + r.stderr, "");
  assert.equal(runs(), before, "the check should not run");
});

test("finishes instantly outside a git repository", () => {
  const r = stop(mkdtempSync(path.join(os.tmpdir(), "bc-nogit-")), randomUUID());
  assert.equal(r.status, 0);
});

test("runs the check with --stamped when there are changes, and skips a repeat run on the same changes", () => {
  const repo = tempRepo(STUB);
  const id = randomUUID();
  writeFiles(repo, { "blockchain-course/lessons/a.qmd": "v1\n" });
  const before = runs();
  assert.equal(stop(repo, id).status, 0);
  assert.equal(runs(), before + 1);
  assert.match(readFileSync(log, "utf8"), /--stamped\r?\n$/);
  assert.equal(stop(repo, id).status, 0);
  assert.equal(runs(), before + 1, "unchanged since the last green run");
  writeFiles(repo, { "blockchain-course/lessons/a.qmd": "v2\n" });
  assert.equal(stop(repo, id).status, 0);
  assert.equal(runs(), before + 2, "changed again, so it runs again");
});

test("runs the check for commits not yet on main", () => {
  const repo = tempRepo(STUB);
  const before = runs();
  writeFiles(repo, { "quizes/quiz_json/b.json": "{}\n" });
  sh("git", ["switch", "-q", "-c", "task/1"], repo);
  sh("git", ["add", "-A"], repo);
  sh("git", ["commit", "-q", "-m", "b"], repo);
  assert.equal(stop(repo, randomUUID()).status, 0);
  assert.equal(runs(), before + 1);
});

test("blocks finishing with the failures, then gives up after 5 blocks", () => {
  const repo = tempRepo(STUB);
  const id = randomUUID();
  for (let i = 1; i <= 4; i++) {
    writeFiles(repo, { "blockchain-course/lessons/a.qmd": `broken ${i}\n` });
    const r = stop(repo, id, "fail");
    assert.equal(r.status, 2);
    assert.match(r.stderr, new RegExp(`attempt ${i} of 5`));
    assert.match(r.stderr, /blockchain-course\/lessons\/a\.qmd:12: div \{\.notes\} is never closed/);
  }
  const fifth = stop(repo, id, "fail");
  assert.equal(fifth.status, 2);
  assert.match(fifth.stderr, /failed 5 times in a row\. Stop working on it now/);
  assert.equal(stop(repo, id, "fail").status, 0, "the sixth stop is allowed");
});

test("a retried stop with nothing changed reuses the failure instead of rerunning the check", () => {
  const repo = tempRepo(STUB);
  const id = randomUUID();
  writeFiles(repo, { "blockchain-course/lessons/a.qmd": "broken\n" });
  const before = runs();
  assert.equal(stop(repo, id, "fail").status, 2);
  const retry = stop(repo, id, "fail", true);
  assert.equal(retry.status, 2);
  assert.match(retry.stderr, /attempt 2 of 5/);
  assert.match(retry.stderr, /never closed/);
  assert.equal(runs(), before + 1, "same tree, so the check ran once");
  writeFiles(repo, { "blockchain-course/lessons/a.qmd": "fixed\n" });
  assert.equal(stop(repo, id, "pass", true).status, 0);
  assert.equal(runs(), before + 2, "the fix is checked");
});

test("a green run resets the block count", () => {
  const repo = tempRepo(STUB);
  const id = randomUUID();
  writeFiles(repo, { "blockchain-course/lessons/a.qmd": "v1\n" });
  stop(repo, id, "fail");
  writeFiles(repo, { "blockchain-course/lessons/a.qmd": "v2\n" });
  stop(repo, id, "fail");
  assert.equal(stop(repo, id, "pass").status, 0);
  writeFiles(repo, { "blockchain-course/lessons/a.qmd": "v3\n" });
  assert.match(stop(repo, id, "fail").stderr, /attempt 1 of 5/);
});

test("without tools/check.py it warns the owner instead of blocking", () => {
  const repo = tempRepo();
  writeFiles(repo, { "a.txt": "x\n" });
  const r = stop(repo, randomUUID());
  assert.equal(r.status, 0);
  assert.match(r.json?.systemMessage ?? "", /Gate not run: tools\/check\.py is missing/);
});
