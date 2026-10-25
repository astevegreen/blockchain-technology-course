// Tests that each sprint skill and agent runs the guard in its own mode, and that only the owner starts a sprint
// skill (the supervisor's trigger types it; no model picks it up on its own).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "..", "..");

function frontmatter(file) {
  const text = readFileSync(path.join(ROOT, file), "utf8").replaceAll("\r\n", "\n");
  const m = /^---\n([\s\S]*?)\n---\n/.exec(text);
  assert.ok(m, `${file} has no frontmatter`);
  return m[1];
}

// [matcher, guard mode] for each PreToolUse hook that runs the guard.
function guards(file) {
  const fm = frontmatter(file);
  return [...fm.matchAll(/matcher: "([^"]+)"\s+hooks:\s+- type: command\s+command: node "\$CLAUDE_PROJECT_DIR\/tools\/hooks\/sprint-guard\.mjs" (--[\w-]+)/g)]
    .map((m) => [m[1], m[2]]);
}

const SHELL = "Bash|PowerShell";
// The GitHub plugin signs in as the owner: sprint skills may only read through it (after-sprint fix 6).
const PLUGIN = ["mcp__plugin_github_github__.*", "--github"];

test("each sprint skill and agent wires the guard in its own mode", () => {
  const want = {
    ".claude/skills/sprint-supervisor/SKILL.md": [[SHELL, "--lane"], PLUGIN],
    ".claude/skills/sprint-lane/SKILL.md": [[SHELL, "--lane"], PLUGIN],
    ".claude/skills/sprint-plan/SKILL.md": [[SHELL, "--lane"], PLUGIN],
    ".claude/skills/sprint-integrate/SKILL.md": [[SHELL, "--integrator"], PLUGIN],
    ".claude/skills/sprint-start/SKILL.md": [[SHELL, "--lane"], PLUGIN],
    ".claude/skills/sprint-stop/SKILL.md": [[SHELL, "--lane"], PLUGIN],
    ".claude/skills/sprint-archive/SKILL.md": [[SHELL, "--lane"], PLUGIN],
    ".claude/agents/implementer.md": [["Edit|Write", "--file-lock"], [SHELL, "--lane"]],
    ".claude/agents/reviewer.md": [[SHELL, "--read-only"]],
  };
  for (const [file, hooks] of Object.entries(want)) assert.deepEqual(guards(file), hooks, file);
});

// The cue and its stop are typed by the owner or the root /sprint-cue; the archiver's trigger types /sprint-archive.
test("the sprint skills start only when typed, and run on the model the supervisor or the cue gives them", () => {
  const want = { supervisor: "sonnet", lane: "sonnet", plan: "opus", integrate: "sonnet", start: "sonnet", stop: "sonnet", archive: "haiku" };
  for (const [name, model] of Object.entries(want)) {
    const fm = frontmatter(`.claude/skills/sprint-${name}/SKILL.md`);
    assert.match(fm, /^disable-model-invocation: true$/m, name);
    assert.match(fm, new RegExp(`^model: ${model}$`, "m"), name);
  }
  assert.doesNotMatch(frontmatter(".claude/skills/sprint-status/SKILL.md"), /disable-model-invocation/,
    "the owner asks for status in plain words");
});
