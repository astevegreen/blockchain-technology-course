#!/usr/bin/env node
// The sprint queue (docs/sprint.md, Machinery): the skills ask it instead of applying the queue rules by hand.
// Prints one line of JSON and exits 0 (done), 2 (refused: act on `do`) or 1 (failed: stop).
//
//   has-work "<session title>"         {start, reason}; a plan adds {ready, todo}, integrate {issues}
//   next <lane> [--taken <n,n>]        {mode, issue, concerns, reason} or null
//   move <n> <state> [--note '<text>'] the labels and the standard "Lane:" comment
//   status [--write] [--also '<line>'] the sprint log's status block and its "Needs you" list
//   env                                {environment_id}, the computer sessions start on (Machinery)
//   started "<session title>" <trig_…> records a trigger the supervisor created, in sprint-triggers.json
//   sessions [--all]                   the trigger recorded last for each title since the window opened
//
// It reads docs/sprint.md as pushed (origin/main), so every session and worktree reads one list, and runs gh and
// git in this checkout whatever the caller's folder. sprint-triggers.json sits in this checkout's git folder,
// shared by its worktrees and never committed. The rules: rules.mjs.
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { freemem } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { QueueError, run } from "./rules.mjs";

const ROOT = fileURLToPath(new URL("../..", import.meta.url));

function exec(file, args, input) {
  const r = spawnSync(file, args, { cwd: ROOT, encoding: "utf8", input, maxBuffer: 256 * 1024 * 1024, windowsHide: true }); // NOSONAR (javascript:S4036)
  return { status: r.error ? -1 : (r.status ?? -1), stdout: r.stdout ?? "", stderr: r.stderr || r.error?.message || "" };
}
const firstLine = (s) => s.trim().split(/\r?\n/)[0] ?? "";

function triggersFile() {
  const r = exec("git", ["rev-parse", "--git-common-dir"]);
  if (r.status !== 0) throw new QueueError(`git rev-parse --git-common-dir failed: ${firstLine(r.stderr)}`);
  return path.resolve(ROOT, r.stdout.trim(), "sprint-triggers.json");
}

const io = {
  sprintDoc() {
    const r = exec("git", ["show", "origin/main:docs/sprint.md"]);
    if (r.status !== 0) throw new QueueError(`git show origin/main:docs/sprint.md failed: ${firstLine(r.stderr)}`);
    return r.stdout;
  },
  gh(args, input) {
    const r = exec("gh", args, input);
    if (r.status !== 0) throw new QueueError(`gh ${args.slice(0, 2).join(" ")} failed: ${firstLine(r.stderr)}`);
    return r.stdout;
  },
  branchAhead(n) {
    const branch = `refs/heads/sprint/${n}`;
    if (exec("git", ["rev-parse", "--verify", "--quiet", branch]).status !== 0) return 0;
    const r = exec("git", ["rev-list", "--count", `origin/main..${branch}`]);
    if (r.status !== 0) throw new QueueError(`git rev-list origin/main..sprint/${n} failed: ${firstLine(r.stderr)}`);
    return Number(r.stdout.trim());
  },
  mainHead() {
    const r = exec("git", ["log", "-1", "--format=%H%x09%s", "origin/main"]);
    if (r.status !== 0) return null;
    const [sha, ...subject] = r.stdout.trim().split("\t");
    return sha ? { sha, subject: subject.join("\t") } : null;
  },
  readTriggers() {
    const file = triggersFile();
    if (!existsSync(file)) return [];
    let records;
    try {
      records = JSON.parse(readFileSync(file, "utf8"));
    } catch (e) {
      throw new QueueError(`${file} is not JSON: ${e.message}`);
    }
    if (!Array.isArray(records)) throw new QueueError(`${file} is not a list`);
    return records;
  },
  writeTriggers(records) {
    const file = triggersFile();
    writeFileSync(`${file}.tmp`, `${JSON.stringify(records, null, 1)}\n`);
    renameSync(`${file}.tmp`, file);
  },
  freeMb: () => Math.floor(freemem() / 1048576),
  now: () => new Date(),
};

const { code, line } = run(process.argv.slice(2), io);
process.stdout.write(`${line}\n`);
process.exitCode = code;
