import { test } from "node:test";
import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { runHook, writeFiles } from "./test-helpers.mjs";

// Runs against this repository: the hook only checks files inside a repo, using the repo's own scripts.
const ROOT = path.resolve(import.meta.dirname, "..", "..");
const lesson = path.join(ROOT, "blockchain-course", "lessons", "ethereum", "06-EF-token_based_communities_and_nfts_in_practice.qmd");
const scratch = path.join(ROOT, "blockchain-course", "lessons", "ethereum", `zz-quick-check-probe-${process.pid}.qmd`);
const edit = (file) => runHook("quick-check.mjs", { cwd: ROOT, tool_name: "Edit", tool_input: { file_path: file } });

test("a clean lesson passes silently", () => {
  const r = edit(lesson);
  assert.equal(r.status, 0);
  assert.equal(r.stderr, "");
});

test("an unbalanced div in a lesson goes back to Claude with its line", (t) => {
  t.after(() => rmSync(scratch, { force: true }));
  const text = readFileSync(lesson, "utf8").replace("::: {.notes}", "::: {.notes}\n::: {.callout-note}");
  writeFiles(path.dirname(scratch), { [path.basename(scratch)]: text });
  const r = edit(scratch);
  assert.equal(r.status, 2);
  assert.match(r.stderr, /quick-check found problems in blockchain-course\/lessons\/ethereum\/zz-quick-check-probe/);
  // The notes block's closing fence closes the callout instead, leaving the notes div open at the next slide.
  assert.match(r.stderr, /:\d+: slide heading inside the div opened at line \d+ \(\{\.notes\}\)/);
  assert.equal(r.stderr.trim().split("\n").length, 2, "one problem, reported once");
});

test("a quiz bank that is not valid JSON is reported with its line", (t) => {
  const bank = path.join(ROOT, "quizes", "quiz_json", `zz-probe-${process.pid}.json`);
  t.after(() => rmSync(bank, { force: true }));
  writeFiles(path.dirname(bank), { [path.basename(bank)]: "{\n  \"lesson_id\": \"x\",,\n}\n" });
  const r = edit(bank);
  assert.equal(r.status, 2);
  assert.match(r.stderr, /quizes\/quiz_json\/zz-probe-\d+\.json:2 /);
});

test("a valid quiz bank that breaks the distractor rules is reported", (t) => {
  const source = path.join(ROOT, "quizes", "quiz_json", "bitcoin_01-BF-bitcoin_origins_and_mechanics-quiz-bank.json");
  const bank = path.join(ROOT, "quizes", "quiz_json", `zz-probe-rules-${process.pid}.json`);
  t.after(() => rmSync(bank, { force: true }));
  const data = JSON.parse(readFileSync(source, "utf8"));
  for (const q of data.questions) q.correct_answer = `${q.correct_answer} ${"padding ".repeat(30)}`;
  writeFiles(path.dirname(bank), { [path.basename(bank)]: JSON.stringify(data, null, 2) });
  const r = edit(bank);
  assert.equal(r.status, 2, r.stderr);
});

test("a Python syntax error is reported", (t) => {
  const file = path.join(ROOT, "tools", `zz_probe_${process.pid}.py`);
  t.after(() => rmSync(file, { force: true }));
  writeFiles(path.dirname(file), { [path.basename(file)]: "def broken(:\n    pass\n" });
  const r = edit(file);
  assert.equal(r.status, 2);
  assert.match(r.stderr, /SyntaxError/);
});

test("a deleted or missing file is ignored", () => {
  assert.equal(edit(path.join(ROOT, "nope.qmd")).status, 0);
});

test("a broken lesson outside the repository, such as the scratchpad, is ignored", () => {
  const outside = realpathSync(mkdtempSync(path.join(os.tmpdir(), "bc-outside-")));
  mkdirSync(path.join(outside, "blockchain-course", "lessons"), { recursive: true });
  const file = path.join(outside, "blockchain-course", "lessons", "x.qmd");
  copyFileSync(lesson, file);
  writeFiles(path.dirname(file), { "x.qmd": "::: {.notes}\n" });
  const r = runHook("quick-check.mjs", { cwd: ROOT, tool_input: { file_path: file } },
    { env: { GIT_CEILING_DIRECTORIES: path.dirname(outside) } });
  assert.equal(r.status, 0);
  assert.equal(r.stderr, "");
});
