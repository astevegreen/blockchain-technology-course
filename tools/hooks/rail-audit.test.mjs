// The rail audit (tools/rail-audit.mjs): which files are rails, how its verdict is read, and that the second look runs
// it deep on a rail change. Owner's policy, 28 Oct 2026: "rails: Auto; audit holds loosening".
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { ARGON, FLASH, OPUS, SONNET, askFirstAvailable, pickDepth } from "../agy.mjs";
import { RAILS, RAIL_MODELS, couldNotRun, railAction, railDiff, railFiles, railVerdict } from "../rail-audit.mjs";

const ROOT = path.resolve(import.meta.dirname, "..", "..");

test("the rails are the hooks, settings, sprint skills and agents, git hooks, workflows, the check, the queue and the review", () => {
  const rails = [
    "tools/hooks/sprint-guard.mjs", ".claude/settings.json", ".claude/settings.local.json", ".claude/skills/sprint-lane/SKILL.md",
    ".claude/agents/implementer.md", ".claude/agents/reviewer.md", ".githooks/pre-commit", ".github/workflows/check.yml",
    "tools/check.py", "tools/qmd_lint.py", "tools/tests/test_check.py", "tools/tests/test_qmd_lint.py",
    "quizes/verify_single_quiz.py", "blockchain-course/glossary/scripts/validate_glossary.py", "tools/sprint/rules.mjs",
    "tools/agy.mjs", "tools/second-look.mjs", "tools/second-look.md", "tools/rail-audit.mjs", "tools/rail-audit.md", "GEMINI.md",
  ];
  const others = [
    ".claude/skills/lesson/SKILL.md", ".claude/agents/scout.md", ".claude/rules/ci.md", "blockchain-course/lessons/x.qmd",
    "CLAUDE.md", "docs/sprint.md", "tools/lab_tests.py", "tools/tests/test_lab_tests.py", "tools/gemini-audit.mjs",
    "quizes/quiz_json/x-quiz-bank.json", "blockchain-course/glossary/terms.yml",
  ];
  assert.deepEqual(railFiles([...rails, ...others]), rails);
  for (const rail of RAILS) assert.ok(rails.some((f) => f.startsWith(rail)), `a sample for ${rail}`);
});

test("the audit reads only the rail files' part of the diff", () => {
  const part = (file) => `diff --git a/${file} b/${file}\nindex 1..2 100644\n--- a/${file}\n+++ b/${file}\n@@ -1 +1 @@\n-a\n+b\n`;
  const diff = part("docs/sprint.md") + part(".claude/settings.json") + part("blockchain-course/lessons/x.qmd") + part(".github/workflows/check.yml");
  assert.equal(railDiff(diff), part(".claude/settings.json") + part(".github/workflows/check.yml"));
  assert.equal(railDiff(part("CLAUDE.md")), "");
});

test("a rail change is always reviewed deep, whatever its size", () => {
  assert.equal(pickDepth({ kind: "change", files: [".githooks/pre-push"], lines: 2 }, RAILS).depth, "deep");
});

test("only a clear no ships; a yes, or an answer with no verdict, holds for the owner", () => {
  assert.equal(railVerdict("LOOSENS: no\nIt adds a CI job."), false);
  assert.equal(railVerdict("**LOOSENS: yes**\n.claude/settings.json:107 - edits no longer ask"), true);
  assert.equal(railVerdict("Here is my review.\n\nLOOSENS: Yes"), true);
  assert.equal(railVerdict("No findings."), null);
  assert.equal(railVerdict(undefined), null);
  assert.match(railAction(false), /ships like any other/);
  assert.match(railAction(true), /^Rail audit: LOOSENS\. Hold .* for the owner/);
  assert.match(railAction(null), /no verdict\. Hold .* for the owner/);
});

// Owner's policy, 28 Oct 2026: a review no model answered is the machine's failure. It never ships the change, and
// never holds it for the owner: it runs again.
test("a second look or rail audit that could not run says retry: nothing ships on it, and the owner isn't asked", () => {
  for (const [review, covers] of [["Second look", "The change"], ["Rail audit", "The rail change"]]) {
    const line = couldNotRun(review, covers, "no model answered: Gemini 4 Argon (high) was too busy");
    assert.match(line, new RegExp(`^${review}: retry\\. It could not run, so it gave no verdict`));
    assert.match(line, new RegExp(`${covers} does not ship until it answers, and is not held for the owner`));
    assert.doesNotMatch(line, /skipped|ships like any other/);
  }
  const script = readFileSync(path.join(ROOT, "tools", "second-look.mjs"), "utf8");
  assert.match(script, /couldNotRun\("Second look"/);
  assert.match(script, /couldNotRun\("Rail audit"/);
  assert.doesNotMatch(script, /Second look skipped: \$\{err/, "a failed look is no skip");
});

// Owner, 28 Oct 2026: the rail audit never waits on the deep models' usage, and never asks Sonnet (the Claude
// reviewer covers that family). With all three out, no model answered, and the audit is retried.
test("the rail audit asks Argon, then Opus, then Flash, and never Sonnet", () => {
  assert.deepEqual(RAIL_MODELS, [ARGON, OPUS, FLASH]);
  const flash = (model) => {
    if (model !== FLASH) throw new Error("Individual quota reached. Resets in 2h0m0s.");
    return "LOOSENS: no\nIt adds a check.";
  };
  const free = { outUntil: () => null, markOut: () => {} };
  assert.deepEqual(askFirstAvailable(RAIL_MODELS, flash, free, () => 0).model, FLASH, "Flash answers when Argon and Opus are out");
  const asked = [];
  const busy = (model) => {
    asked.push(model);
    throw new Error("Quota exceeded for quota metric per minute");
  };
  const none = { outUntil: () => null, markOut: () => {} };
  assert.throws(() => askFirstAvailable(RAIL_MODELS, busy, none, () => 0), /no model answered/);
  assert.deepEqual(asked, [ARGON, OPUS, FLASH]);
  assert.ok(!asked.includes(SONNET));
  const script = readFileSync(path.join(ROOT, "tools", "second-look.mjs"), "utf8");
  assert.match(script, /review\("rail-audit\.md", material, RAIL_MODELS, tmp\)/);
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
