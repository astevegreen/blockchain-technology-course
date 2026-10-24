// Tests for .claude/settings.json and the git pre-commit hook wiring.
import { test } from "node:test";
import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { sh, tempRepo, writeFiles } from "./test-helpers.mjs";
import { spawnSync } from "node:child_process";

const ROOT = path.resolve(import.meta.dirname, "..", "..");
const read = (file) => readFileSync(path.join(ROOT, file), "utf8");

function settings() {
  try {
    return JSON.parse(read(".claude/settings.json"));
  } catch (err) {
    throw new Error(`.claude/settings.json is not strict JSON, so Claude Code would ignore it: ${err.message}`, { cause: err });
  }
}

const scripts = (groups = []) => groups.flatMap((g) => g.hooks.map((h) => path.basename(h.args?.[0] ?? h.command)));

test("hooks are wired: env check and handoff note at start, quick check after edits, gate then handoff at stop", () => {
  const { hooks } = settings();
  assert.deepEqual(hooks.SessionStart.map((g) => [g.matcher, scripts([g])]), [
    ["startup", ["env-check.mjs"]],
    ["startup|clear", ["handoff-nudge.mjs"]],
  ]);
  assert.deepEqual(hooks.PostToolUse.map((g) => [g.matcher, scripts([g])]), [["Edit|Write", ["quick-check.mjs"]]]);
  assert.deepEqual(scripts(hooks.Stop), ["gate.mjs", "handoff-nudge.mjs"]);
  for (const g of Object.values(hooks).flat()) for (const h of g.hooks) {
    assert.equal(h.command, "node");
    assert.match(h.args[0], /^\$\{CLAUDE_PROJECT_DIR\}\/tools\/hooks\/[\w-]+\.mjs$/);
  }
});

test("generated and vendored folders can't be read; pushes to main need no prompt; history stays intact", () => {
  const { allow, deny } = settings().permissions;
  for (const rule of ["Read(**/_site/**)", "Read(**/assets/vendor/**)", "Read(**/.agents/**)"]) assert.ok(deny.includes(rule), rule);
  for (const rule of ["Bash(git push)", "Bash(git push origin main)", "Bash(python tools/*)"]) assert.ok(allow.includes(rule), rule);
  for (const rule of ["Bash(git push --force *)", "Bash(git reset --hard *)"]) assert.ok(deny.includes(rule), rule);
});

test("the setup itself, CI and GitHub credentials need the owner's yes", () => {
  const { ask } = settings().permissions;
  for (const rule of ["Edit(/.claude/**)", "Edit(/CLAUDE.md)", "Edit(/.github/**)", "Edit(/tools/hooks/**)",
                      "Edit(/tools/sprint/**)", "Bash(gh secret *)", "Bash(gh auth *)"]) assert.ok(ask.includes(rule), rule);
});

test("unattended sprint sessions run the queue, ci-watch and the integrator's push without a prompt", () => {
  const { allow } = settings().permissions;
  for (const tool of ["Bash", "PowerShell"]) {
    for (const script of ["queue", "ci-watch"]) {
      const rule = `${tool}(node C:/Antigravity/blockchain-technology-course/tools/sprint/${script}.mjs *)`;
      assert.ok(allow.includes(rule), rule);
    }
  }
  assert.ok(allow.includes("Bash(git -C C:/Antigravity/bc-integrate push origin HEAD:main)"));
});

test("history-rewriting git commands are refused in the git -C form the sprint uses, as in the plain form", () => {
  const { deny } = settings().permissions;
  for (const tool of ["Bash", "PowerShell"]) {
    for (const cmd of ["push *--force*", "push -f*", "push * -f*", "push *+*", "reset --hard*", "clean *", "branch -D *", "tag -d *"]) {
      assert.ok(deny.includes(`${tool}(git -C * ${cmd})`), `${tool}(git -C * ${cmd})`);
    }
  }
});

test("the lab tests run in WSL and their CI runs can be watched without a prompt", () => {
  const { allow } = settings().permissions;
  for (const rule of ["Bash(docker version)", "Bash(wsl -d Ubuntu -- bash dynamic-labs/regression-tests/automated/*)",
                      "PowerShell(wsl -d Ubuntu -- bash dynamic-labs/regression-tests/automated/*)",
                      "Bash(gh run list *)", "Bash(gh run view *)", "Bash(gh run watch *)"]) assert.ok(allow.includes(rule), rule);
  assert.ok(settings().permissions.deny.includes("Bash(gh workflow run *)"), "agents still can't start a workflow");
});

test("skipping the pre-commit check needs the owner's yes, in Bash and PowerShell", () => {
  const { ask } = settings().permissions;
  for (const tool of ["Bash", "PowerShell"]) {
    for (const cmd of ["git commit *--no-verify*", "git commit -n*", "git commit * -n*", "git push *--no-verify*",
                       "git -C * commit *--no-verify*", "git -C * commit -n*", "git -C * push *--no-verify*",
                       "git *core.hooksPath*"]) assert.ok(ask.includes(`${tool}(${cmd})`), `${tool}(${cmd})`);
  }
});

test("the model is left to the owner: no model pin, no subagent model", () => {
  const s = settings();
  assert.equal(s.model, undefined);
  assert.equal(s.env?.CLAUDE_CODE_SUBAGENT_MODEL, undefined);
});

// A throwaway repository with this repo's pre-commit hook and a stub check, hooks turned on.
function repoWithHook(checkExit) {
  const repo = tempRepo();
  mkdirSync(path.join(repo, ".githooks"));
  copyFileSync(path.join(ROOT, ".githooks", "pre-commit"), path.join(repo, ".githooks", "pre-commit"));
  writeFiles(repo, { "tools/check.py": `import sys\nprint("check ran:", " ".join(sys.argv[1:]))\nsys.exit(${checkExit})\n` });
  sh("git", ["add", "-A"], repo);
  sh("git", ["commit", "-q", "-m", "stub"], repo);
  sh("git", ["config", "core.hooksPath", ".githooks"], repo);
  return repo;
}
const commit = (repo) => {
  writeFiles(repo, { "a.txt": "change\n" });
  sh("git", ["add", "-A"], repo);
  return spawnSync("git", ["commit", "-q", "-m", "change"], { cwd: repo, encoding: "utf8", windowsHide: true });
};

test("a commit runs `python tools/check.py --stamped` and is refused when it fails", () => {
  const red = commit(repoWithHook(1));
  assert.notEqual(red.status, 0);
  assert.match(red.stdout + red.stderr, /check ran: --stamped/);
  assert.equal(commit(repoWithHook(0)).status, 0);
});

test("the pre-commit hook is committed as executable", () => {
  assert.match(sh("git", ["ls-files", "-s", ".githooks/pre-commit"], ROOT), /^100755 /);
});
