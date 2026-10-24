// SessionStart (startup): check this machine is set up the way the project expects.
// Problems are shown to the owner (systemMessage), never added to Claude's context.
// Docker is not checked: only the desktop runs it, and CLAUDE.md says what to do without it.
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { readInput, git } from "./shared.mjs";

function run(cmd, args) {
  return new Promise((resolve) => {
    const p = spawn(cmd, args, { windowsHide: true, stdio: "ignore" });
    const timer = setTimeout(() => { p.kill(); resolve(false); }, 10_000);
    p.on("error", () => { clearTimeout(timer); resolve(false); });
    p.on("exit", (code) => { clearTimeout(timer); resolve(code === 0); });
  });
}

const input = await readInput();
const problems = [];

if (process.env.ANTHROPIC_API_KEY) {
  problems.push("ANTHROPIC_API_KEY is set, so Claude Code bills the API instead of your plan. Remove it from your environment variables.");
}

if (process.platform === "win32") {
  const bash = [
    process.env.CLAUDE_CODE_GIT_BASH_PATH,
    "C:\\Program Files\\Git\\bin\\bash.exe",
    `${process.env.LOCALAPPDATA}\\Programs\\Git\\bin\\bash.exe`,
  ];
  if (!bash.some((c) => c && existsSync(c))) problems.push("Git Bash was not found. Install Git for Windows (it includes Git Bash).");
  // Where `quarto install tinytex` puts it; the glossary PDF needs it.
  if (!existsSync(path.join(process.env.APPDATA ?? "", "TinyTeX", "bin", "windows"))) {
    problems.push("TinyTeX was not found, so the glossary PDF can't be built. Run: quarto install tinytex");
  }
}

const major = Number(process.versions.node.split(".")[0]);
if (major < 24) problems.push(`Node ${process.versions.node} is too old for the hooks; install Node 24 or newer.`);

const [quarto, python, py, gh, ghAuth] = await Promise.all([
  run("quarto", ["--version"]),
  run("python", ["-c", "import yaml, bs4"]),
  run("py", ["-c", "import yaml, bs4"]),
  run("gh", ["--version"]),
  run("gh", ["auth", "status"]),
]);
if (!quarto) problems.push("Quarto was not found. Install it from quarto.org, then restart the Claude app so it sees the new PATH.");
if (!python && !py) problems.push("Python can't import PyYAML and beautifulsoup4. Run: python -m pip install --user -r requirements-dev.txt");
if (!gh) problems.push("The GitHub CLI (gh) was not found. Install it from cli.github.com.");
else if (!ghAuth) problems.push("The GitHub CLI isn't signed in. Run: gh auth login");

const root = git(["rev-parse", "--show-toplevel"], input.cwd ?? process.cwd());
if (root && existsSync(path.join(root, ".githooks")) && git(["config", "core.hooksPath"], root) !== ".githooks") {
  problems.push("Git hooks are off, so commits skip the check. Run: git config core.hooksPath .githooks");
}

if (problems.length) {
  process.stdout.write(JSON.stringify({ systemMessage: `Blockchain course setup:\n- ${problems.join("\n- ")}` }));
}
