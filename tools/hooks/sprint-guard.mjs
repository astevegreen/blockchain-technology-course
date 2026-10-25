// PreToolUse guard for the unattended sprint (docs/sprint.md). Permission rules match only a command's prefix;
// this reads every part of a chained command line. Ported from YODC's October sprint.
//   --lane        Bash|PowerShell: no push (lane, plan, supervisor and implementer); lab tests and Docker only in
//                 the labs worktree
//   --integrator  Bash|PowerShell: pushes only `git push origin HEAD:main`; never runs lab tests or Docker
//   --read-only   Bash|PowerShell: inspection commands only (the reviewer)
//   --file-lock   Edit|Write: the sprint never edits its own machinery, the owner's files or generated files
// --lane and --integrator refuse new dependencies and git writes to the main checkout (only fetch, worktree and
// `merge --ff-only` touch it), and run the sprint queue (tools/sprint/queue.mjs) only on its own. Both read the
// command a wrapper runs (env, nice, timeout, xargs, find -exec, wsl, ...) and refuse a command string they can't
// read (sh -c, pwsh -Command, cmd, eval), a command or git subcommand held in a variable or a substitution, and git
// aliases. Every Bash mode also refuses what no unattended session may do: skip hooks, force or delete on the
// remote, discard work, change gh auth, or fetch from the web. It reads commands, not programs: a script or
// `node -e` that runs git itself is out of its sight (.githooks/pre-push still refuses its push from a lane's worktree).
// How the shell reads a line is shell-reader.mjs, shared with YODC and Terminal Dusk; the rules here are the course's.
import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { cmdName, gitSub, readCommand, Unreadable } from "./shell-reader.mjs";

const MODE = ["--lane", "--integrator", "--read-only", "--file-lock"].find((m) => process.argv.includes(m));
const input = JSON.parse(readFileSync(0, "utf8") || "{}");

function deny(reason) {
  process.stderr.write(`sprint-guard: ${reason} (docs/sprint.md, "What still stops a task")\n`);
  process.exit(2);
}

// The one worktree where lab tests and Docker run: `--fresh-start` wipes every lab's containers, so two sessions
// running them at once break each other.
const LAB_WORKTREE = "bc-lane-labs";

// Paths the sprint never edits, relative to the repo or worktree root.
const LOCKED = [
  /^\.claude\//, /^\.githooks\//, /^\.github\//, /^\.gitattributes$/, /^docs\/sprint\.md$/, /^CLAUDE\.md$/,
  /^tools\/sprint\//, /^tools\/hooks\//, /^tools\/check\.py$/,
  // Generated: they change only by running their scripts (CLAUDE.md, hard rule 2).
  /^blockchain-course\/glossary\/(slide-index\.yml|terms\.yml|terms\.json|duplicates\.md|index\.qmd|index\.pdf)$/,
  /^quizes\/dist\//, /^blockchain-course\/_site\//,
];

if (MODE === "--file-lock") {
  const file = path.resolve(String(input.cwd ?? process.cwd()), String(input.tool_input?.file_path ?? ""));
  // The checkout holding the file: a linked worktree has a `.git` file, the main checkout a `.git` folder.
  let root = path.dirname(file);
  while (!existsSync(path.join(root, ".git")) && path.dirname(root) !== root) root = path.dirname(root);
  const dotGit = path.join(root, ".git");
  if (!existsSync(dotGit)) deny(`${file} is outside every checkout`);
  if (statSync(dotGit).isDirectory()) deny(`${file} is in the main checkout; edit in your lane's worktree`);
  const rel = path.relative(root, file).split(path.sep).join("/");
  if (LOCKED.some((re) => re.test(rel))) deny(`${rel} is locked during the sprint`);
  process.exit(0);
}

const command = String(input.tool_input?.command ?? "");
// text: message values blanked (a commit message or queue note naming `git push --force` isn't one); literalsBlank:
// every literal blanked; textRead: the words as the shell reads them (`--no-ver""ify` is --no-verify); parts: the
// simple commands, a substitution's among them.
const read = readCommand(command, input.tool_name === "PowerShell" ? "powershell" : "bash");
const { text, textRead, literalsBlank, parts, words } = read;
// The commands one simple command runs, a wrapper's among them; one the reader can't read (`sh -c`, `eval`, a
// command held in a variable) is refused.
function commandsIn(w) {
  try {
    return read.commandsIn(w);
  } catch (e) {
    if (e instanceof Unreadable) deny(e.message);
    throw e;
  }
}
// In every mode: a command named by a variable or a substitution (`& $g push`, `$(which git) push`).
if (read.refusal) deny(read.refusal);

const ALWAYS = [
  [/--no-verify\b|\bSKIP_HOOKS\b|core\.hooksPath/, "hooks are never skipped"],
  [/\bgh\s+(auth|secret|api|workflow|release|repo|label\s+delete|issue\s+delete)\b/, "that gh command is the owner's"],
  [/\bgit\b[^\n]*\bpush\b[^\n]*(\s-f\b|--force|--delete|\s-d\b|\s\+\S|\s:\S)/, "no force-push or remote delete"],
  [/\bgit\b[^\n]*\b(reset\s+--hard|clean\s+-\S*f|branch\s+-D|tag\s+-[df]|update-ref\s+-d|filter-branch|filter-repo)\b/, "that discards work"],
];
// Read as written and as the shell reads its words: `--no-ver""ify` skips hooks too.
for (const [re, why] of ALWAYS) if (re.test(text) || re.test(textRead)) deny(why);
// These two read only the command line outside text strings; --lane and --integrator also check each command's name.
const DELETES = /\brm\s+-\S*r|\bremove-item\b[^\n]*-recurse|\brmdir\b|\brd\s+\/s/i;
const WEB = new Set(["curl", "wget", "invoke-webrequest", "iwr", "invoke-restmethod", "irm"]);
if (DELETES.test(literalsBlank)) deny("no recursive delete");
const recursiveDelete = (w) => (w[0] === "rm" && w.some((x) => /^-\w*r|^--recursive$/i.test(x)))
  || (w[0] === "remove-item" && w.some((x) => /^-recurse/i.test(x))) || w[0] === "rmdir" || (w[0] === "rd" && w.includes("/s"));
if (/\b(curl|wget|invoke-webrequest|iwr|invoke-restmethod|irm)\b/i.test(literalsBlank)) deny("no web fetches");

const isPush = (w) => w[0] === "git" && w.includes("push") && !w.includes("stash");
// Git Bash on Windows writes C:/x as /c/x, and WSL as /mnt/c/x; elsewhere they are real paths.
const native = (p) => (process.platform === "win32" ? p.replace(/^\/(?:mnt\/)?([a-z])(\/|$)/i, "$1:/") : p);
// The main checkout has a `.git` folder; a linked worktree has a `.git` file.
function isMainCheckout(dir) {
  let root = path.resolve(dir);
  while (!existsSync(path.join(root, ".git")) && path.dirname(root) !== root) root = path.dirname(root);
  const dotGit = path.join(root, ".git");
  return existsSync(dotGit) && statSync(dotGit).isDirectory();
}
// Git subcommands that change a checkout's branch, index or files. Run against the main checkout they would move
// the owner's working copy; only fetch, worktree and `merge --ff-only` go there.
const GIT_WRITES = new Set(["switch", "checkout", "commit", "rebase", "reset", "restore", "stash", "cherry-pick",
  "revert", "merge", "pull", "add", "rm", "mv", "am", "apply"]);

// A shell given a lab script runs it (`bash run.sh`, `wsl -d Ubuntu -- bash …/run.sh`).
const SHELLS = new Set(["sh", "bash", "zsh", "dash", "ksh", "fish"]);
// A lab test or a Docker command: Docker itself, or any script under dynamic-labs/ (a lab's run.sh, the lab manager,
// a lab's own lab.sh), named with or without its folder.
const LAB_SCRIPT = /(^|[\\/])(dynamic-labs[\\/].+|run|lab|lab-manager|deploy-cloud|smoke-test|local-validation-runner)\.sh$/;
// Returns the script a lab run starts (null for Docker itself), or undefined when the command is no lab run.
// Reading a script (`cat run.sh`) is no run: only a shell given it, or the script run as the command.
function labRun({ w, at }) {
  if (["docker", "docker-compose", "podman"].includes(w[0])) return null;
  if (LAB_SCRIPT.test(at)) return at;
  return SHELLS.has(w[0]) ? w.slice(1).find((x) => LAB_SCRIPT.test(x)) : undefined;
}
const inLabWorktree = (dir) => path.resolve(dir).split(path.sep).includes(LAB_WORKTREE);

// The queue writes labels and comments, and a settings rule may allow it by prefix: a call chained, piped,
// redirected or backgrounded could carry another command through, so it runs alone.
const isQueue = (w) => w[0] === "node" && /(^|[\\/])tools[\\/]sprint[\\/]queue\.mjs$/.test(w[1] ?? "");
if ((MODE === "--lane" || MODE === "--integrator") && parts.some((p) => isQueue(words(p)))) {
  const unquoted = command.replace(/"[^"]*"|'[^']*'/g, '""');
  if (parts.length !== 1 || /[<>&]/.test(unquoted)) {
    deny("run `node <checkout>/tools/sprint/queue.mjs …` on its own: no chaining, pipe, redirect or `&`");
  }
}

const PIP = (w) => (["pip", "pip3"].includes(w[0]) && /^(install|uninstall)$/.test(w[1] ?? ""))
  || (["python", "py", "python3"].includes(w[0]) && w.slice(1, 4).join(" ").match(/-m pip (install|uninstall)\b/));

if (MODE === "--lane" || MODE === "--integrator") {
  let cwd = String(input.cwd ?? process.cwd());
  // Git config set from the environment can define an alias that runs any command.
  if (/\bGIT_CONFIG_(PARAMETERS|COUNT|KEY_\d+)\b/.test(text)) deny("no git config from the environment");
  // Git's subcommand or checkout in a variable or a substitution (`git $p`, `git $(echo push)`, `git -C "$d" commit`,
  // PowerShell's `git @a`) can't be read.
  if (read.gitHidden) {
    deny("git's subcommand and checkout are written out in the sprint, not held in a variable or a substitution");
  }
  for (const p of parts) {
    const top = words(p);
    if (["cd", "set-location", "sl", "pushd"].includes(cmdName(top[0])) && top[1]) cwd = path.resolve(cwd, native(top[1]));
    for (const cmd of commandsIn(top)) {
      const { w, fromArgs, repl } = cmd;
      if (WEB.has(w[0])) deny("no web fetches");
      if (recursiveDelete(w)) deny("no recursive delete");
      if (MODE === "--lane" && isPush(w)) deny("only the integrator pushes");
      if (w[0] === "gh" && w[1] === "pr" && w[2] === "merge") deny("only the integrator lands work");
      if (w[0] === "npm" && /^(i|in|install|add|un|uninstall|rm|remove|r|up|update|upgrade)$/.test(w[1] ?? "")) {
        deny("no new or changed dependencies; `npm ci` installs the locked ones");
      }
      if (PIP(w)) deny("no new or changed dependencies");
      const script = labRun(cmd);
      if (script !== undefined) {
        if (MODE === "--integrator") deny("the integrator never runs lab tests or Docker: it waits for the Lab Tests run (tools/sprint/ci-watch.mjs)");
        const at = script && path.isAbsolute(native(script)) ? native(script) : cwd;
        if (!inLabWorktree(at)) {
          deny(`lab tests and Docker run only in C:/Antigravity/${LAB_WORKTREE}, the labs lane's worktree: \`cd\` there first`);
        }
      }
      if (w[0] !== "git") continue;
      const sub = gitSub(w);
      // find and xargs add words: `xargs git` or `-exec git {}` takes its subcommand from them, and
      // `-exec git -C {}` its checkout.
      const filled = (x) => x === undefined || x.includes("{}") || (repl && x.includes(repl));
      const at = w.indexOf("-C");
      if (fromArgs && (filled(sub) || (at >= 0 && filled(w[at + 1])))) {
        deny("git run by find or xargs must name its subcommand and checkout");
      }
      // An alias (`-c alias.x='!git push'`, `git config alias.x`) runs any command under a new name.
      if (w.some((x) => /^(--config-env=)?alias\./i.test(x))) deny("no git aliases: run the git command itself");
      // Git config is shared by the main checkout and every worktree, and --global is the computer's: the sprint
      // reads it and never writes it.
      if (sub === "config") {
        const args = w.slice(w.indexOf("config") + 1);
        const named = args.filter((x) => !x.startsWith("-"));
        if (args.some((x) => /^(--(global|system|add|unset|unset-all|replace-all|rename-section|remove-section|edit)|-e)$/.test(x))
          || /^(set|unset|edit|rename-section|remove-section)$/.test(named[0] ?? "")
          || (named.length >= 2 && !/^(get|list)$/.test(named[0]))) {
          deny("git config is read-only in the sprint: it is shared with the main checkout, and --global is the computer's");
        }
      }
      if ((sub === "rebase" && w.some((x) => /^(-x|--exec)(=|$)/.test(x)))
        || (sub === "submodule" && w.includes("foreach")) || (sub === "bisect" && w.includes("run"))) {
        deny(`\`git ${sub}\` would run a command string the guard can't read`);
      }
      const dir = at >= 0 && w[at + 1] ? path.resolve(cwd, native(w[at + 1])) : cwd;
      const ffOnly = sub === "merge" && w.includes("--ff-only");
      if (GIT_WRITES.has(sub) && !ffOnly && isMainCheckout(dir)) {
        deny(`\`git ${sub}\` would change the main checkout; work in your worktree with \`git -C <worktree>\``);
      }
    }
  }
}

if (MODE === "--integrator") {
  for (const p of parts) {
    for (const cmd of commandsIn(words(p))) {
      const all = cmd.w.filter((x, i, ws) => !(ws[i - 1] === "-C" || x === "-C"));
      // `> push.txt 2>&1` saves the output; it is not part of the push.
      const cut = all.findIndex((x) => /^(\d?>>?|&>)/.test(x));
      const w = cut >= 0 ? all.slice(0, cut) : all;
      if (isPush(w) && w.slice(w.indexOf("push")).join(" ") !== "push origin HEAD:main") {
        deny("the integrator pushes only with `git push origin HEAD:main`");
      }
    }
  }
}

if (MODE === "--read-only") {
  // A `>` inside quotes is text (a grep pattern), not a redirect.
  const unquoted = command.replace(/"[^"]*"|'[^']*'/g, '""');
  if (/(^|[^0-9&])>{1,2}(?!\s*(&1|\/dev\/null|\$null))/.test(unquoted)) deny("the reviewer writes no files");
  const ALLOWED = [
    ["git", "diff"], ["git", "log"], ["git", "show"], ["git", "status"], ["git", "merge-base"],
    ["git", "rev-parse"], ["git", "branch", "--list"], ["git", "ls-files"], ["git", "ls-tree"], ["git", "grep"],
    ["git", "fetch"], ["gh", "issue", "view"], ["gh", "pr", "view"], ["cd"],
    ["cat"], ["head"], ["tail"], ["grep"], ["rg"], ["ls"], ["wc"], ["sort"], ["uniq"], ["date"], ["echo"], ["pwd"],
  ];
  // `check.py --slides` reads slide counts and titles from a revision with `git show`, and writes nothing.
  const slides = (w) => ["python", "py"].includes(cmdName(w[0])) && /(^|[\\/])tools[\\/]check\.py$/.test(w[1] ?? "") && w[2] === "--slides";
  for (const p of parts) {
    const w = words(p).filter((x, i, all) => !(x === "-C" || all[i - 1] === "-C" || x === "--no-pager"));
    // A refspec with `:` (main:main) writes a local branch; a plain fetch updates only origin's.
    if (w[0] === "git" && w[1] === "fetch" && w.some((x) => x.includes(":"))) deny("the reviewer fetches only origin's branches");
    const ok = ALLOWED.some((a) => a.every((x, i) => w[i] === x)) || (w[0] === "sed" && w[1] === "-n") || slides(w);
    if (!ok) deny(`the reviewer runs inspection commands only, not \`${w.slice(0, 3).join(" ")}\``);
  }
}

process.exit(0);
