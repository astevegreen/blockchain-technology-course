// The rail audit (tools/rail-audit.mjs): which files are rails, how its verdict is read, and that the second look runs
// it deep on a rail change. Owner's policy, 28 Oct 2026: "rails: Auto; audit holds loosening".
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { pickDepth } from "../agy.mjs";
import { RAILS, railAction, railDiff, railFiles, railVerdict } from "../rail-audit.mjs";

const ROOT = path.resolve(import.meta.dirname, "..", "..");

test("the rails are the hooks, the check, the git hooks, the workflows and the settings", () => {
  assert.deepEqual(
    railFiles([
      "tools/hooks/sprint-guard.mjs", "tools/check.py", ".githooks/pre-commit", ".github/workflows/check.yml",
      ".claude/settings.json", ".claude/settings.local.json",
      ".claude/skills/lesson/SKILL.md", "tools/sprint/rules.mjs", "blockchain-course/lessons/x.qmd", "CLAUDE.md",
    ]),
    ["tools/hooks/sprint-guard.mjs", "tools/check.py", ".githooks/pre-commit", ".github/workflows/check.yml",
     ".claude/settings.json", ".claude/settings.local.json"],
  );
});

test("the audit reads only the rail files' part of the diff", () => {
  const part = (file) => `diff --git a/${file} b/${file}\nindex 1..2 100644\n--- a/${file}\n+++ b/${file}\n@@ -1 +1 @@\n-a\n+b\n`;
  const diff = part("docs/sprint.md") + part(".claude/settings.json") + part("tools/sprint/rules.mjs") + part(".github/workflows/check.yml");
  assert.equal(railDiff(diff), part(".claude/settings.json") + part(".github/workflows/check.yml"));
  assert.equal(railDiff(part("CLAUDE.md")), "");
});

test("a rail change is always reviewed deep, whatever its size", () => {
  assert.equal(pickDepth({ kind: "change", files: [".githooks/pre-push"], lines: 2 }, RAILS).depth, "deep");
});

test("only a clear no ships; a yes or no verdict at all holds for the owner", () => {
  assert.equal(railVerdict("LOOSENS: no\nIt adds a CI job."), false);
  assert.equal(railVerdict("**LOOSENS: yes**\n.claude/settings.json:107 - edits no longer ask"), true);
  assert.equal(railVerdict("Here is my review.\n\nLOOSENS: Yes"), true);
  assert.equal(railVerdict("No findings."), null);
  assert.equal(railVerdict(undefined), null);
  assert.match(railAction(false), /ships like any other/);
  assert.match(railAction(true), /^Rail audit: LOOSENS\. Hold .* for the owner/);
  assert.match(railAction(null), /no verdict\. Hold .* for the owner/);
});

test("the second look runs the rail audit on a rail change, with the audit's own prompt", () => {
  const script = readFileSync(path.join(ROOT, "tools", "second-look.mjs"), "utf8");
  assert.match(script, /railFiles\(stats\.files\)/);
  assert.match(script, /review\("rail-audit\.md"/);
  assert.match(script, /railDiff\(diff\)/);
  const prompt = readFileSync(path.join(ROOT, "tools", "rail-audit.md"), "utf8");
  assert.match(prompt.replace(/\s+/g, " "), /does this change loosen, bypass or disable any check, guard, gate, hook or required review\?/);
  assert.match(prompt, /`LOOSENS: yes` or `LOOSENS: no`/);
});
