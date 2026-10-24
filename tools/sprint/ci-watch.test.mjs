// Tests for tools/sprint/ci-watch.mjs, with a stand-in for gh and the clock so nothing reaches GitHub or waits.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { watch } from "./ci-watch.mjs";

const SHA = "be34383f0aa1";

// gh answers `run list` with `lists` in turn and `run view` with `views` in turn; each wait moves the clock on.
function fake({ lists = [[]], views = [] } = {}) {
  let t = 0;
  const calls = [];
  const gh = (args) => {
    calls.push(args.slice(0, 2).join(" "));
    if (args[1] === "list") return JSON.stringify(lists.length > 1 ? lists.shift() : lists[0]);
    return JSON.stringify(views.length > 1 ? views.shift() : views[0]);
  };
  return { io: { gh, wait: (ms) => { t += ms; }, now: () => t }, calls };
}
const listed = [{ databaseId: 42, status: "in_progress", conclusion: "", url: "https://x/42", headSha: `${SHA}0000` }];
const done = (conclusion, jobs = []) => ({ status: "completed", conclusion, url: "https://x/42", jobs });

test("waits for the run to appear and to finish, and reports a pass", () => {
  const { io, calls } = fake({ lists: [[], [], listed], views: [{ status: "in_progress", url: "https://x/42" }, done("success", [{ name: "pick", conclusion: "success" }])] });
  const r = watch(SHA, io);
  assert.equal(r.code, 0);
  assert.deepEqual(JSON.parse(r.line), { workflow: "lab-tests.yml", sha: SHA, run: 42, conclusion: "success", url: "https://x/42", failed: [] });
  assert.deepEqual(calls, ["run list", "run list", "run list", "run view", "run view"]);
});

test("a failed run exits 2, names the failed jobs and says to revert", () => {
  const jobs = [{ name: "pick", conclusion: "success" }, { name: "lab (bitcoin)", conclusion: "failure" }, { name: "lab (hlf)", conclusion: "skipped" }];
  const r = watch(SHA, fake({ lists: [listed], views: [done("failure", jobs)] }).io);
  assert.equal(r.code, 2);
  const out = JSON.parse(r.line);
  assert.deepEqual(out.failed, ["lab (bitcoin)"]);
  assert.match(out.do, /revert the batch/);
});

test("no run within 3 minutes is reported, not taken as a pass", () => {
  const r = watch(SHA, fake().io);
  assert.equal(r.code, 1);
  assert.equal(JSON.parse(r.line).conclusion, "none");
});

test("a run still going after 45 minutes is reported as timed out, to be watched again", () => {
  const r = watch(SHA, fake({ lists: [listed], views: [{ status: "in_progress", url: "https://x/42" }] }).io);
  assert.equal(r.code, 1);
  assert.equal(JSON.parse(r.line).conclusion, "timed out");
  assert.match(JSON.parse(r.line).do, /after 45 minutes: run this again, up to 3 times/);
});

test("a failing gh is an error that says stop", () => {
  const r = watch(SHA, { gh: () => { throw new Error("gh run list failed: HTTP 502"); }, wait: () => {}, now: () => 0 });
  assert.equal(r.code, 1);
  assert.match(JSON.parse(r.line).do, /^Stop and report/);
});

test("anything but a commit sha is refused before gh runs", () => {
  let ran = false;
  const r = watch("main; rm x", { gh: () => { ran = true; return "[]"; }, wait: () => {}, now: () => 0 });
  assert.equal(r.code, 1);
  assert.match(JSON.parse(r.line).error, /^usage/);
  assert.equal(ran, false);
  const cli = spawnSync(process.execPath, [path.join(import.meta.dirname, "ci-watch.mjs")], { encoding: "utf8", windowsHide: true });
  assert.equal(cli.status, 1);
  assert.match(cli.stdout, /usage: node tools\/sprint\/ci-watch\.mjs/);
});
