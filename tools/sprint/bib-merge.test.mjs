// Tests for tools/sprint/bib-merge.mjs: the entry-by-entry merge, then git running it as the bibliography's
// merge driver in a throwaway repository with this checkout's .gitattributes.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { DRIVER, merge, parse } from "./bib-merge.mjs";
import { sh, tempRepo, writeFiles } from "../hooks/test-helpers.mjs";

const ROOT = path.resolve(import.meta.dirname, "..", "..");
const BIB = "blockchain-course/lessons/references/Blockchain.bib";
const entry = (key, title, extra = "") => `@misc{${key},\n  title = {${title}},${extra}\n  year = {2026}\n}\n`;
const OLD = `${entry("old", "Old")}\n${entry("kept", "Kept")}`;
const keys = (text) => parse(text).list.map((e) => e.key);

test("keeps the entries both sides added at the end, each whole", () => {
  const ours = `${OLD}\n${entry("alpha", "Alpha")}`;
  const theirs = `${OLD}\n${entry("beta", "Beta")}`;
  const out = merge(OLD, ours, theirs);
  assert.equal(out, `${OLD}\n${entry("alpha", "Alpha")}\n${entry("beta", "Beta")}`);
});

test("takes the side that changed an entry, and a deletion the other side left alone", () => {
  const edited = OLD.replace("{Kept}", "{Kept, 2nd edition}");
  assert.equal(merge(OLD, OLD, edited), edited);
  assert.equal(merge(OLD, edited, OLD), edited);
  assert.deepEqual(keys(merge(OLD, OLD, entry("old", "Old"))), ["old"]);
  assert.equal(merge(OLD, edited, edited), edited);
});

test("an entry both sides changed or added differently is left to git as a conflict", () => {
  assert.equal(merge(OLD, OLD.replace("{Kept}", "{A}"), OLD.replace("{Kept}", "{B}")), null);
  assert.equal(merge(OLD, `${OLD}\n${entry("new", "A")}`, `${OLD}\n${entry("new", "B")}`), null);
  assert.equal(merge(OLD, entry("old", "Old"), OLD.replace("{Kept}", "{B}")), null);
  // The same source added on both sides, word for word, lands once.
  const same = `${OLD}\n${entry("new", "A")}`;
  assert.equal(merge(OLD, same, same), same);
  // A key twice on one side is the check's to report (bib keys), not the driver's to choose between.
  assert.equal(merge(OLD, `${OLD}\n${entry("Old", "Again")}`, OLD), null);
});

test("git cherry-picks two branches' new sources without a conflict once the clone sets the driver", () => {
  const repo = tempRepo({
    ".gitattributes": readFileSync(path.join(ROOT, ".gitattributes"), "utf8"),
    "tools/sprint/bib-merge.mjs": readFileSync(path.join(import.meta.dirname, "bib-merge.mjs"), "utf8"),
    [BIB]: OLD,
  });
  sh("git", ["config", "merge.bib.driver", DRIVER], repo);
  const branch = (name, text) => {
    sh("git", ["switch", "-q", "-c", name, "main"], repo);
    writeFiles(repo, { [BIB]: `${OLD}\n${text}` });
    sh("git", ["commit", "-q", "-am", name], repo);
  };
  branch("sprint/1", entry("alpha", "Alpha"));
  branch("sprint/2", entry("beta", "Beta"));
  // The integrator's batch: a worktree on sprint/1, picking sprint/2 from another folder.
  const wt = `${repo}-integrate`;
  sh("git", ["worktree", "add", "-q", wt, "sprint/1"], repo);
  const pick = spawnSync("git", ["-C", wt, "cherry-pick", "sprint/2"], { encoding: "utf8", windowsHide: true });
  assert.equal(pick.status, 0, pick.stderr);
  const merged = readFileSync(path.join(wt, BIB), "utf8");
  assert.deepEqual(keys(merged), ["old", "kept", "alpha", "beta"]);
  assert.match(merged, /@misc\{alpha,\n {2}title = \{Alpha\},\n {2}year = \{2026\}\n\}\n/);

  // Without the driver, the same pick stops on a conflict, as before the sprint.
  sh("git", ["config", "--unset", "merge.bib.driver"], repo);
  sh("git", ["-C", wt, "reset", "-q", "--hard", "sprint/1"], repo);
  const plain = spawnSync("git", ["-C", wt, "cherry-pick", "sprint/2"], { encoding: "utf8", windowsHide: true });
  assert.notEqual(plain.status, 0);
  sh("git", ["-C", wt, "cherry-pick", "--abort"], repo);
});
