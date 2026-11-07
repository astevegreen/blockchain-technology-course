import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, readFileSync } from "node:fs";
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

test("warns when Python lacks a package the lab and quiz-engine tests need", () => {
  // A flask.py first on PYTHONPATH that refuses to import stands in for Flask not being installed.
  const shadow = tempRepo({ "flask.py": "raise ImportError('Flask is not installed')\n" });
  const r = start({ ANTHROPIC_API_KEY: "", PYTHONPATH: shadow });
  assert.match(r.json?.systemMessage ?? "", /requirements-dev\.txt/);
});

test("probes an import for every package in requirements-dev.txt", () => {
  const importName = { pyyaml: "yaml", beautifulsoup4: "bs4" };
  const root = path.resolve(import.meta.dirname, "..", "..");
  const wanted = readFileSync(path.join(root, "requirements-dev.txt"), "utf8").split(/\r?\n/)
    .map((line) => line.replace(/#.*/, "").trim()).filter(Boolean)
    .map((line) => line.match(/^[A-Za-z0-9_.-]+/)[0].toLowerCase())
    .map((name) => importName[name] ?? name);
  const probe = readFileSync(path.join(import.meta.dirname, "env-check.mjs"), "utf8").match(/DEV_IMPORTS = "([^"]*)"/);
  assert.ok(probe, "env-check.mjs names its imports in DEV_IMPORTS");
  assert.deepEqual(wanted.filter((m) => !probe[1].split(/,\s*/).includes(m)), []);
});
