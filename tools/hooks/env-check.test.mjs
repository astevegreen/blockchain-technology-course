import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { runHook, sh, tempRepo } from "./test-helpers.mjs";

const start = (env = {}, cwd) => runHook("env-check.mjs", { hook_event_name: "SessionStart", source: "startup", cwd }, { env });

test("warns the owner when ANTHROPIC_API_KEY is set", () => {
  const r = start({ ANTHROPIC_API_KEY: "dummy" });
  assert.equal(r.status, 0);
  assert.match(r.json?.systemMessage ?? "", /ANTHROPIC_API_KEY is set/);
});

test("only ever prints a systemMessage, never plain text for Claude's context", () => {
  const r = start({ ANTHROPIC_API_KEY: "" });
  assert.equal(r.status, 0);
  if (r.stdout.trim()) assert.deepEqual(Object.keys(r.json ?? {}), ["systemMessage"]);
});

test("says how to turn the git hooks on when a clone has them off", () => {
  const repo = tempRepo();
  mkdirSync(path.join(repo, ".githooks"));
  assert.match(start({ ANTHROPIC_API_KEY: "" }, repo).json?.systemMessage ?? "", /git config core\.hooksPath \.githooks/);
  sh("git", ["config", "core.hooksPath", ".githooks"], repo);
  assert.doesNotMatch(start({ ANTHROPIC_API_KEY: "" }, repo).stdout, /hooksPath/);
});
