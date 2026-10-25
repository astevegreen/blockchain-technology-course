#!/usr/bin/env node
// The sprint queue (docs/sprint.md, Machinery): the skills ask it instead of applying the queue rules by hand.
// Prints one line of JSON and exits 0 (done), 2 (refused: act on `do`) or 1 (failed: stop).
//
//   has-work "<session title>" [--started <k>]  {start, reason}; a plan adds {ready, todo}, integrate {issues};
//                                      k sessions created this run count against free memory
//   next <lane> [--taken <n,n>]        {mode, issue, concerns, reason} or null
//   move <n> <state> [--note '<text>'] the labels and the standard "Lane:" comment
//   status [--write] [--also '<line>'] the sprint log's status block and its "Needs you" list
//   env                                {environment_id}, the computer sessions start on: the window's, else the doc's
//   window                             {state none|before|open|after, start, end, newYork, lanes, log, supervisor, archiver,
//                                      wake, stoppedBy}: stoppedBy is "sprint-stop" when /sprint-stop ended it
//   window start [hours] [--environment <env_…>] [--dry-run]   opens the window now, for 38 hours unless told (1-96),
//                                      in sprint-window.json, with the environment /sprint-start found
//   window ids --supervisor <trig_…> --archiver <trig_…> --wake <trig_…>   records the scheduled tasks made
//   window stop                        ends the open window now, as /sprint-stop's (stoppedBy: "sprint-stop")
//   window archived                    clears the last window's archiver, once it is switched off
//   wake [--resets-at <epoch s>]       {arm, runOnceAt, wake, reason, log?}: where the supervisor moves its wake
//   started "<session title>" <trig_…> records a trigger the supervisor created, in sprint-triggers.json
//   sessions [--all]                   the trigger recorded last for each title since the window opened
//   lock | unlock                      one supervisor run at a time (sprint-supervisor.lock; stale after 20 minutes)
//   identity                           {login, ok}: gh is signed in as the bot, whose comments the queue reads as its own
//   resume --log <file> --last-event <ISO>   {start, reason, after?, restartAt?}: whether a run that stopped on a
//                                      usage limit may start again, from the end of its log (usage-limit.mjs)
//
// It reads docs/sprint.md as pushed (origin/main), so every session and worktree reads one list, and runs gh and
// git in this checkout whatever the caller's folder. sprint-triggers.json, sprint-window.json and the lock sit in this
// checkout's git folder, shared by its worktrees and never committed. The rules: rules.mjs.
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
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

// A file in the main checkout's git folder, which every worktree shares.
function stateFile(name) {
  const r = exec("git", ["rev-parse", "--git-common-dir"]);
  if (r.status !== 0) throw new QueueError(`git rev-parse --git-common-dir failed: ${firstLine(r.stderr)}`);
  return path.resolve(ROOT, r.stdout.trim(), name);
}
function readJson(file) {
  if (!existsSync(file)) return null;
  try {
    return JSON.parse(readFileSync(file, "utf8"));
  } catch (e) {
    throw new QueueError(`${file} is not JSON: ${e.message}`);
  }
}
// Written whole and renamed into place, so no reader sees half a file; the temporary name is this process's own.
function writeJson(file, value) {
  const tmp = `${file}.${process.pid}.tmp`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 1)}\n`);
  renameSync(tmp, file);
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
    const file = stateFile("sprint-triggers.json");
    const records = readJson(file) ?? [];
    if (!Array.isArray(records)) throw new QueueError(`${file} is not a list`);
    return records;
  },
  writeTriggers: (records) => writeJson(stateFile("sprint-triggers.json"), records),
  readWindow() {
    const file = stateFile("sprint-window.json");
    const w = readJson(file);
    if (w !== null && (typeof w !== "object" || Array.isArray(w))) throw new QueueError(`${file} is not an object`);
    return w;
  },
  writeWindow: (w) => writeJson(stateFile("sprint-window.json"), w),
  // Created only if absent, so two runs taking the lock at once cannot both have it.
  claimLock(value) {
    try {
      writeFileSync(stateFile("sprint-supervisor.lock"), JSON.stringify(value), { flag: "wx" });
      return true;
    } catch (e) {
      if (e.code === "EEXIST") return false;
      throw new QueueError(`cannot take the supervisor lock: ${e.message}`);
    }
  },
  readLock() {
    try {
      return JSON.parse(readFileSync(stateFile("sprint-supervisor.lock"), "utf8"));
    } catch {
      return null;
    }
  },
  writeLock: (value) => writeJson(stateFile("sprint-supervisor.lock"), value),
  removeLock: () => rmSync(stateFile("sprint-supervisor.lock"), { force: true }),
  // A path relative to this checkout, where the supervisor saved it (.sprint/run-<trigger id>.txt).
  readLog(file) {
    try {
      return readFileSync(path.resolve(ROOT, file), "utf8");
    } catch (e) {
      throw new QueueError(`cannot read ${file}: ${e.message}`);
    }
  },
  freeMb: () => Math.floor(freemem() / 1048576),
  now: () => new Date(),
};

const { code, line } = run(process.argv.slice(2), io);
process.stdout.write(`${line}\n`);
process.exitCode = code;
