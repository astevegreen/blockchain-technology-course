// Tests for tools/sonar.mjs, with a stand-in for gh so nothing reaches GitHub.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { report } from "../sonar.mjs";

const ROOT = path.resolve(import.meta.dirname, "..", "..");

const SHA = "71883034921adc52a93a073e2986ba22aa773a9d";
const summary = (issues) =>
  `Issues  \n![](https://x/passed.svg '') [${issues} New issues](https://sonarcloud.io/a)  \n` +
  "![](https://x/accepted.svg '') [0 Accepted issues](https://sonarcloud.io/b)\n\nMeasures  \n" +
  "![](https://x/passed.svg '') [0 Security Hotspots](https://sonarcloud.io/c)  \n" +
  "![](https://x/passed.svg '') [0.0% Coverage on New Code](https://sonarcloud.io/d)  \n  \n" +
  "[See analysis details on SonarQube Cloud](https://sonarcloud.io/e)\n\n";
// A failed gate as SonarCloud wrote it for this repository, links shortened.
const FAILED =
  "Failed conditions  \n![](https://x/failed.svg '') [D Reliability Rating on New Code](https://sonarcloud.io/a) (required ≥ A)  \n" +
  "![](https://x/failed.svg '') [B Security Rating on New Code](https://sonarcloud.io/b) (required ≥ A)  \n  \n" +
  "[See analysis details on SonarQube Cloud](https://sonarcloud.io/c)\n\n##   \n" +
  "![](https://x/light_bulb.svg '') Catch issues before they fail your Quality Gate with our IDE extension " +
  "![](https://x/sonarlint.svg '') [SonarQube for IDE](https://www.sonarsource.com/products/sonarlint/)\n\n";

const sonarRun = ({ issues = 0, ...over } = {}) => ({
  id: 7,
  name: "SonarCloud Code Analysis",
  app: { slug: "sonarqubecloud" },
  status: "completed",
  conclusion: "success",
  output: { title: "Quality Gate passed", summary: summary(issues) },
  ...over,
});
const finding = (file, title, line = 0, key = "K1") => ({
  path: file,
  start_line: line,
  title,
  message: `\nSee more on https://sonarcloud.io/project/issues?id=p&issues=${key}&open=${key}&pullRequest=12`,
});

// A stand-in for gh: answers the three calls report() makes and records them.
function fakeGh({ findings = [], runs = [sonarRun({ issues: findings.length })], fail } = {}) {
  const calls = [];
  const gh = (args) => {
    calls.push(args);
    if (fail) throw new Error(fail);
    if (args[0] === "pr") return JSON.stringify({ number: 12, headRefOid: SHA });
    if (args.some((a) => a.includes("/check-runs?")))
      return JSON.stringify({ check_runs: [{ id: 1, name: "build", app: { slug: "github-actions" } }, ...runs] });
    return findings.map((f) => JSON.stringify(f)).join("\n");
  };
  return { gh, calls };
}

test("a finished check prints the quality gate, the counts and every finding grouped by message", () => {
  const { gh } = fakeGh({
    findings: [
      finding("tools/hooks/a.test.mjs", "Add some tests to this file or delete it.", 0, "A1"),
      finding("tools/check.py", "Define a constant instead of duplicating this literal.", 12, "B1"),
      finding("tools/hooks/b.test.mjs", "Add some tests to this file or delete it.", 0, "A2"),
    ],
  });
  const r = report("12", { gh });
  assert.equal(r.code, 0, r.out);
  assert.equal(
    r.out,
    [
      "SonarCloud on PR #12 (commit 7188303): Quality Gate passed",
      "3 New issues · 0 Accepted issues · 0 Security Hotspots · 0.0% Coverage on New Code",
      "",
      "2 × Add some tests to this file or delete it.",
      "  tools/hooks/a.test.mjs  (issue A1)",
      "  tools/hooks/b.test.mjs  (issue A2)",
      "1 × Define a constant instead of duplicating this literal.",
      "  tools/check.py:12  (issue B1)",
    ].join("\n"),
  );
});

test("a failed gate lists each failed condition with what it needed, and drops the IDE advert", () => {
  const run = sonarRun({ conclusion: "failure", output: { title: "Quality Gate failed", summary: FAILED } });
  const r = report("12", fakeGh({ runs: [run] }));
  assert.equal(r.code, 0, r.out);
  assert.deepEqual(r.out.split("\n").slice(0, 2), [
    "SonarCloud on PR #12 (commit 7188303): Quality Gate failed",
    "D Reliability Rating on New Code (required ≥ A) · B Security Rating on New Code (required ≥ A)",
  ]);
});

test("it asks gh for the PR's latest commit, that commit's checks, and every page of findings, and only reads", () => {
  const { gh, calls } = fakeGh();
  report("#12", { gh });
  assert.deepEqual(calls[0], ["pr", "view", "12", "--json", "number,headRefOid"]);
  assert.deepEqual(calls[1], ["api", `repos/{owner}/{repo}/commits/${SHA}/check-runs?per_page=100`]);
  assert.deepEqual(calls[2], [
    "api",
    "--paginate",
    "repos/{owner}/{repo}/check-runs/7/annotations?per_page=100",
    "--jq",
    ".[]",
  ]);
  assert.ok(calls.every((c) => !c.some((a) => /^(-X|--method|-f|-F|--field|--raw-field|--input)$/.test(a))));
});

test("when GitHub holds fewer findings than SonarCloud counted, it says the list is incomplete", () => {
  const r = report("12", fakeGh({ runs: [sonarRun({ issues: 5 })], findings: [finding("a.mjs", "Fix this.")] }));
  assert.equal(r.code, 0);
  assert.match(r.out, /\n\nGitHub has 1 of SonarCloud's 5 new issues\. The rest are only on sonarcloud\.io/);
});

test("with no findings it says so", () => {
  const r = report("12", fakeGh());
  assert.equal(r.code, 0);
  assert.match(r.out, /Quality Gate passed\n.*\n\nNo findings\.$/);
});

test("stray brackets before a count neither swallow it nor slow the read down", () => {
  const stray = "[".repeat(20000);
  const run = sonarRun({ output: { title: "Quality Gate passed", summary: `${stray}[1 New issue](https://x)` } });
  const r = report("12", fakeGh({ runs: [run], findings: [finding("a.mjs", "Fix this.")] }));
  assert.equal(r.out.split("\n")[1], "1 New issue");
});

test("when SonarCloud ran more than once on the commit, the newest run counts", () => {
  const old = sonarRun({ id: 5, output: { title: "Quality Gate failed", summary: "" } });
  const r = report("12", fakeGh({ runs: [old, sonarRun({ id: 9 })] }));
  assert.match(r.out, /Quality Gate passed/);
});

test("while SonarCloud is still running it says so and fails", () => {
  const r = report("12", fakeGh({ runs: [sonarRun({ status: "in_progress", conclusion: null })] }));
  assert.equal(r.code, 1);
  assert.match(r.out, /still running on PR #12 \(in_progress\)/);
});

test("with no SonarCloud check on the PR's latest commit it says so and fails", () => {
  const r = report("12", fakeGh({ runs: [] }));
  assert.equal(r.code, 1);
  assert.match(r.out, /No SonarCloud check on PR #12's latest commit 7188303/);
});

test("when gh fails it passes gh's message on and fails", () => {
  const r = report("999", fakeGh({ fail: "no pull requests found" }));
  assert.equal(r.code, 1);
  assert.equal(r.out, "sonar: no pull requests found");
});

test("Claude runs it without a prompt: node tools/* is allowed and no ask or deny rule covers it", () => {
  const { allow, ask, deny } = JSON.parse(readFileSync(path.join(ROOT, ".claude/settings.json"), "utf8")).permissions;
  assert.ok(allow.includes("Bash(node tools/*)"), "node tools/* is not on the allow list");
  for (const rule of [...ask, ...deny]) assert.doesNotMatch(rule, /^Bash\(node/, rule);
});

test("without a pull request number it prints how to use it and fails", () => {
  for (const args of [[], ["main"], ["12a"]]) {
    const r = spawnSync(process.execPath, [path.join(ROOT, "tools", "sonar.mjs"), ...args], {
      encoding: "utf8",
      windowsHide: true,
    });
    assert.equal(r.status, 1, args.join(" "));
    assert.match(r.stdout, /usage: node tools\/sonar\.mjs <pull request number>/);
  }
});
