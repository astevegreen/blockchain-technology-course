// Helpers shared by the Claude Code hook scripts. No dependencies; Node built-ins only.
import { spawnSync } from "node:child_process";
import { existsSync, realpathSync, statSync } from "node:fs";
import path from "node:path";

export async function readInput() {
  let raw = "";
  for await (const chunk of process.stdin) raw += chunk;
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

export function toPosix(p) {
  return p.replace(/\\/g, "/");
}

export function git(args, cwd) {
  const r = spawnSync("git", args, { cwd, encoding: "utf8", windowsHide: true });
  return r.status === 0 ? r.stdout.trim() : null;
}

// Resolve symlinks and Windows short names (C:\Users\RUNNER~1) in the part of `p` that exists,
// so paths compare equal to the long form git reports.
export function canonical(p) {
  let dir = path.resolve(p);
  const rest = [];
  while (!existsSync(dir)) {
    const up = path.dirname(dir);
    if (up === dir) break;
    rest.unshift(path.basename(dir));
    dir = up;
  }
  try { dir = realpathSync.native(dir); } catch {}
  return path.join(dir, ...rest);
}

function existingDir(p) {
  let dir = path.resolve(p);
  while (!(existsSync(dir) && statSync(dir).isDirectory())) {
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  return dir;
}

// The git root that owns `target`: the worktree's own root inside a worktree.
// Outside any repository it returns `fallback`, or null when no fallback is given.
export function repoRootFor(target, fallback) {
  const root = git(["rev-parse", "--show-toplevel"], existingDir(target)) ?? fallback;
  return root ? canonical(root) : null;
}

// The Python interpreter: `python`, else the `py` launcher. Never `python3`, the Microsoft Store stub here.
let python;
export function pythonCommand() {
  if (python !== undefined) return python;
  python = ["python", "py"].find((cmd) =>
    spawnSync(cmd, ["-c", "import sys; sys.exit(0)"], { encoding: "utf8", windowsHide: true, timeout: 15_000 }).status === 0) ?? null;
  return python;
}

// Run a repo Python script; returns { status, output } with ANSI codes stripped.
export function runPython(args, { cwd, timeout = 60_000 } = {}) {
  const py = pythonCommand();
  if (!py) return { status: null, output: "Python was not found on PATH (tried python, py).", missing: true };
  const r = spawnSync(py, args, {
    cwd, encoding: "utf8", timeout, windowsHide: true,
    env: { ...process.env, FORCE_COLOR: "0", NO_COLOR: "1", PYTHONIOENCODING: "utf-8" },
  });
  const output = r.error?.code === "ETIMEDOUT"
    ? `timed out after ${Math.round(timeout / 1000)}s`
    : `${r.stdout ?? ""}\n${r.stderr ?? ""}`.replace(/\x1b\[[0-9;?]*[A-Za-z]/g, "").trim();
  return { status: r.status, output };
}

export function limitLines(text, max) {
  const lines = text.trimEnd().split(/\r?\n/);
  if (lines.length <= max) return lines.join("\n");
  return [...lines.slice(0, max - 1), `... (${lines.length - max + 1} more lines)`].join("\n");
}
