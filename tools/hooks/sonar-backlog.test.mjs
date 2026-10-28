// Tests for tools/sonar-backlog.mjs, with a stand-in for SonarCloud so nothing reaches the network.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { backlog } from "../sonar-backlog.mjs";

const ROOT = path.resolve(import.meta.dirname, "..", "..");
const KEY = "astevegreen_blockchain-technology-course";

const PUBLIC = {
  status: 200,
  body: { component: { key: KEY, visibility: "public", analysisDate: "2026-10-22T19:36:53+0000" } },
};
const issue = (over = {}) => ({
  rule: "python:S1192",
  severity: "CRITICAL",
  type: "CODE_SMELL",
  component: `${KEY}:tools/check.py`,
  line: 52,
  message: "Define a constant instead of duplicating this literal.",
  ...over,
});
const found = (issues, total = issues.length) => ({ status: 200, body: { total, issues } });

// A stand-in for SonarCloud: answers the two calls backlog() makes and records every URL.
function fakeSonar({ project = PUBLIC, search = found([]) } = {}) {
  const urls = [];
  const get = async (url) => {
    urls.push(url);
    return url.includes("/components/show") ? project : search;
  };
  return { get, urls, params: () => new URL(urls.find((u) => u.includes("/issues/search"))).searchParams };
}

test("by default it lists the BLOCKER and CRITICAL issues on main, worst first, one line each, with the total", async () => {
  const { get, params } = fakeSonar({
    search: found(
      [
        issue({ severity: "BLOCKER", type: "VULNERABILITY", rule: "secrets:S6706", component: `${KEY}:dynamic-labs/a.pem`, line: 1, message: "Remove this key." }),
        issue(),
        issue({ line: undefined, message: "A file-level issue." }),
      ],
      390,
    ),
  });
  const r = await backlog([], { get });
  assert.equal(r.code, 0, r.out);
  assert.equal(
    r.out,
    [
      "SonarCloud, main branch, last analyzed 2026-10-22 19:36 UTC: 390 open issues BLOCKER and CRITICAL",
      "BLOCKER  VULNERABILITY  secrets:S6706  dynamic-labs/a.pem:1  Remove this key.",
      "CRITICAL  CODE_SMELL  python:S1192  tools/check.py:52  Define a constant instead of duplicating this literal.",
      "CRITICAL  CODE_SMELL  python:S1192  tools/check.py  A file-level issue.",
      "387 more not shown. Narrow it with --files, or raise --limit (up to 200).",
    ].join("\n"),
  );
  const p = params();
  assert.equal(p.get("componentKeys"), KEY);
  assert.equal(p.get("resolved"), "false");
  assert.equal(p.get("branch"), "main");
  assert.equal(p.get("severities"), "BLOCKER,CRITICAL");
  assert.equal(p.get("s"), "SEVERITY");
  assert.equal(p.get("asc"), "false");
  assert.equal(p.get("ps"), "40");
});

test("--files asks for just those files, of any severity, and --limit sets how many lines come back", async () => {
  const { get, params } = fakeSonar({ search: found([issue({ severity: "MINOR" })]) });
  const abs = path.join(ROOT, "tools", "hooks", "gate.mjs");
  const r = await backlog(["--files", "tools\\check.py", "./CLAUDE.md", abs, "--limit", "7"], { get });
  assert.equal(r.code, 0, r.out);
  assert.match(r.out.split("\n")[0], /: 1 open issues in tools\/check\.py, CLAUDE\.md, tools\/hooks\/gate\.mjs$/);
  assert.match(r.out, /\nMINOR {2}CODE_SMELL {2}python:S1192 {2}tools\/check\.py:52 {2}Define a constant/);
  const p = params();
  assert.equal(p.get("componentKeys"), `${KEY}:tools/check.py,${KEY}:CLAUDE.md,${KEY}:tools/hooks/gate.mjs`);
  assert.equal(p.get("severities"), null);
  assert.equal(p.get("s"), "FILE_LINE");
  assert.equal(p.get("ps"), "7");
});

test("it only reads: anonymous GETs of SonarCloud's two read endpoints, and the script has no way to send a token", async () => {
  const { get, urls } = fakeSonar();
  await backlog([], { get });
  await backlog(["--files", "tools/check.py"], { get });
  assert.ok(urls.length >= 4);
  for (const u of urls) assert.match(u, /^https:\/\/sonarcloud\.io\/api\/(components\/show|issues\/search)\?/, u);
  const src = readFileSync(path.join(ROOT, "tools", "sonar-backlog.mjs"), "utf8");
  assert.doesNotMatch(src, /process\.env|authorization|SONAR_TOKEN|SONARCLOUD_TOKEN|method:|body:/i);
});

test("when the project is no longer public it says so and never asks for issues", async () => {
  for (const project of [
    { status: 404, body: { errors: [{ msg: "Project doesn't exist" }] } },
    { status: 401, body: null },
    { status: 403, body: null },
    { status: 200, body: { component: { visibility: "private" } } },
  ]) {
    const { get, urls } = fakeSonar({ project });
    const r = await backlog([], { get });
    assert.equal(r.code, 1);
    assert.match(r.out, /gone private or been renamed.*never uses a token, so ask the owner/);
    assert.equal(urls.length, 1, "it asked for issues of a project it cannot see");
  }
});

test("when the issues call fails it passes SonarCloud's message on and fails", async () => {
  const bad = { status: 400, body: { errors: [{ msg: "Bad request" }, { msg: "Too many keys" }] } };
  const r = await backlog([], { get: fakeSonar({ search: bad }).get });
  assert.equal(r.code, 1);
  assert.equal(r.out, "sonar-backlog: SonarCloud answered 400: Bad request; Too many keys");
});

test("when SonarCloud cannot be reached it says so and fails", async () => {
  const get = async () => {
    throw new Error("fetch failed");
  };
  const r = await backlog([], { get });
  assert.equal(r.code, 1);
  assert.equal(r.out, "sonar-backlog: could not reach SonarCloud: fetch failed");
});

test("with nothing open it says 0, and for files it warns that an unanalyzed file shows 0 too", async () => {
  const none = await backlog([], { get: fakeSonar().get });
  assert.equal(none.code, 0);
  assert.match(none.out, /^SonarCloud, main branch.*: 0 open issues BLOCKER and CRITICAL$/);
  const files = await backlog(["--files", "tools/new.mjs"], { get: fakeSonar().get });
  assert.match(files.out, /: 0 open issues in tools\/new\.mjs\nA file SonarCloud has not analyzed yet/);
});

test("a long or multi-line message is cut to one short line", async () => {
  const long = `First line.\n   second   line ${"x".repeat(400)}`;
  const r = await backlog([], { get: fakeSonar({ search: found([issue({ message: long })]) }).get });
  const row = r.out.split("\n")[1];
  assert.ok(row.endsWith("…"), row);
  assert.ok(!row.includes("\n") && row.includes("First line. second line "), row);
  assert.ok(row.length < 260, `row is ${row.length} characters`);
});

test("a path outside the repository is refused before anything is asked", async () => {
  for (const bad of ["../elsewhere.txt", "tools/../../x", path.resolve(ROOT, "..", "x.txt"), "a,b.txt"]) {
    const { get, urls } = fakeSonar();
    const r = await backlog(["--files", bad], { get });
    assert.equal(r.code, 1, bad);
    assert.match(r.out, /^Not a path inside this repository: /);
    assert.equal(urls.length, 0);
  }
});

test("bad arguments print how to use it and fail without asking SonarCloud", async () => {
  const usage = /^usage: node tools\/sonar-backlog\.mjs \[--files <path>\.\.\.\] \[--limit <n>\]$/;
  for (const args of [["--files"], ["tools/check.py"], ["--nope"], ["--files", "--limit", "5"]]) {
    const { get, urls } = fakeSonar();
    const r = await backlog(args, { get });
    assert.equal(r.code, 1, args.join(" "));
    assert.match(r.out, usage, args.join(" "));
    assert.equal(urls.length, 0);
  }
  for (const args of [["--limit"], ["--limit", "0"], ["--limit", "201"], ["--limit", "ten"]]) {
    const r = await backlog(args, { get: fakeSonar().get });
    assert.equal(r.code, 1, args.join(" "));
    assert.equal(r.out, "--limit takes a number from 1 to 200");
  }
  const many = await backlog(["--files", ...Array.from({ length: 41 }, (_, i) => `f${i}.txt`)], { get: fakeSonar().get });
  assert.equal(many.out, "--files takes at most 40 paths");
});

test("run as a command, bad arguments print the usage and exit 1", () => {
  const r = spawnSync(process.execPath, [path.join(ROOT, "tools", "sonar-backlog.mjs"), "--files"], {
    encoding: "utf8",
    windowsHide: true,
  });
  assert.equal(r.status, 1);
  assert.match(r.stdout, /usage: node tools\/sonar-backlog\.mjs/);
});
