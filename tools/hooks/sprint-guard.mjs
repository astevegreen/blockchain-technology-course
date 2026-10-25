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
import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

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

// PowerShell's escape character is a backtick, where bash's is a backslash and a backtick runs a command.
const PS = input.tool_name === "PowerShell";
// An escape before a newline joins the two lines into one command: `git \⏎push` pushes in bash, `git `⏎push` in
// PowerShell.
const command = String(input.tool_input?.command ?? "").replace(PS ? /`\r?\n/g : /\\\r?\n/g, " ");
// Simple commands: split on control operators, keeping the words of each. Inside quotes, |, ;, &, ), $ and a
// backtick are text (a search pattern such as "a\|b", a note naming `a.qmd`), except inside a `$(…)` or backticks
// in double quotes, which run a command there. So are |, ;, & and ) escaped with a backslash outside quotes
// (`sed -n 1p\;9p`, find's `\;`).
const MASK = { "|": "\u0001", ";": "\u0002", "&": "\u0003", ")": "\u0004", "`": "\u0005", $: "\u0006" };
const UNMASK = Object.fromEntries(Object.entries(MASK).map(([k, v]) => [v, k]));
// Rebuilds a command line, handing each quoted string (quotes included) to `quoted` and each backslash-escaped
// character outside quotes to `escaped`.
function mapQuoted(s, quoted, escaped = (x) => `\\${x}`) {
  let out = "";
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === "\\") { out += escaped(s[i + 1] ?? ""); i++; continue; }
    if (c !== '"' && c !== "'") { out += c; continue; }
    let j = i + 1;
    while (j < s.length && s[j] !== c) j += c === '"' && s[j] === "\\" ? 2 : 1;
    out += quoted(s.slice(i, j + 1), out);
    i = j;
  }
  return out;
}
const runsInside = (q) => q[0] === '"' && /[$`]/.test(q);
// In double quotes that can run a command, only `$(…)` and bash's backticks hold one: |, ;, & and ) elsewhere in
// them are text (`--body "Done; $n left"`), while `"a; $(echo hi; git push)"` still splits inside the substitution.
function textOutsideRuns(q) {
  const esc = PS ? "`" : "\\";
  let out = "";
  let depth = 0;
  let tick = false;
  for (let k = 0; k < q.length; k++) {
    const c = q[k];
    if (c === esc) { out += c + (q[k + 1] ?? ""); k++; continue; }
    if (c === "$" && q[k + 1] === "(") { depth++; out += "$("; k++; continue; }
    if (c === "(" && depth) depth++;
    else if (c === ")" && depth) { depth--; out += c; continue; }
    else if (c === "`" && !PS) tick = !tick;
    out += !depth && !tick && "|;&)".includes(c) ? MASK[c] : c;
  }
  return out;
}
const maskQuoted = (s) => mapQuoted(s,
  (q) => (runsInside(q) ? textOutsideRuns(q) : q.replace(/[|;&)`$]/g, (x) => MASK[x])),
  (x) => `\\${"|;&)".includes(x) && x ? MASK[x] : x}`);
// The command line with its text strings emptied: a note or comment may name curl or `rm -r` without running it.
const literalsBlank = mapQuoted(command, (q) => (runsInside(q) ? q : "''"));
// The command line with only message values emptied: a commit message, an issue body or a queue note is text the
// command stores and never runs, so one naming `git push --force` or --no-verify isn't read as one. A quoted word
// anywhere else is an argument (`git push '--force'` forces), and a value in double quotes holding $ or a
// backtick runs that command: both are read as written.
const TEXT_FLAG = /(^|\s)(--note|--also|--body|--comment|--title|--message|-m)(=|\s+)$/;
const text = mapQuoted(command, (q, before) => (!runsInside(q) && TEXT_FLAG.test(before) ? "''" : q));
const masked = maskQuoted(command);
// A lone & ends a command (bash's background) or starts one (PowerShell's call operator); `2>&1` and `&>` are
// redirects.
const parts = masked
  .split(PS ? /&&|\|\||(?<!>)&(?!>)|[;|\n]|\$\(|\)/ : /&&|\|\||(?<!>)&(?!>)|[;|\n`]|\$\(|\)/)
  .map((p) => p.replace(/[\u0001-\u0006]/g, (c) => UNMASK[c]).trim())
  .filter(Boolean);
// A word as the shell reads it: its quoted and unquoted pieces joined (`git "pu"sh` is git push, and `X="a b"` is one
// word), without the quotes, and without an escape character outside single quotes (bash's `\`, PowerShell's `).
const unescape = (s, inDouble) => (PS ? s.replace(/`(.)/g, "$1") : s.replace(inDouble ? /\\([$`"\\])/g : /\\(.)/g, "$1"));
const words = (s) => s.match(/(?:[^\s"']+|"(?:[^"\\]|\\.)*"|'[^']*'|["'])+/g)?.map((w) =>
  w.replace(/"((?:[^"\\]|\\.)*)"|'([^']*)'|["']|[^"']+/g, (piece, dq, sq) =>
    sq ?? (dq !== undefined ? unescape(dq, true) : /^["']$/.test(piece) ? "" : unescape(piece, false)))) ?? [];

// Commands the guard can't read, in every mode. PowerShell's call operator and dot-source run what a variable or an
// expression names (`& $g push`, `& (Get-Command git) push`, `. $x`); in bash, `& $g` backgrounds one command and
// runs a variable's. `2>&1` and `&&` are not that &.
if (/(?<![>&])&(?![&>])\s*([$(]|"[^"]*\$)|(^|[;|\n{(&])\s*\.\s+([$(]|"[^"]*\$)/.test(masked)) {
  deny("`& $x`, `& (…)` and `. $x` run a command the guard can't read; run it by name");
}
// In bash, a command named by a substitution (`$(which git) push`, `"$(which git)" push`, `` `which git` push ``)
// runs what it prints.
if (!PS && /(^|[;|&\n({!]|\b(then|do|else)\s)\s*"?(\$\(|`)/.test(masked)) {
  deny("a command named by `$(…)` or backticks runs what it prints, which the guard can't read; run it by name");
}

const ALWAYS = [
  [/--no-verify\b|\bSKIP_HOOKS\b|core\.hooksPath/, "hooks are never skipped"],
  [/\bgh\s+(auth|secret|api|workflow|release|repo|label\s+delete|issue\s+delete)\b/, "that gh command is the owner's"],
  [/\bgit\b[^\n]*\bpush\b[^\n]*(\s-f\b|--force|--delete|\s-d\b|\s\+\S|\s:\S)/, "no force-push or remote delete"],
  [/\bgit\b[^\n]*\b(reset\s+--hard|clean\s+-\S*f|branch\s+-D|tag\s+-[df]|update-ref\s+-d|filter-branch|filter-repo)\b/, "that discards work"],
];
// Read as written and as the shell reads its words: `--no-ver""ify` skips hooks too.
const textRead = words(text).join(" ");
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

// A command's name as the shell runs it: `/usr/bin/git`, `git.exe` and `Git` are all git.
const cmdName = (x) => path.posix.basename(String(x ?? "").replace(/\\/g, "/")).toLowerCase().replace(/\.(exe|cmd|bat)$/, "");
// Words before the command itself: shell keywords, grouping, PowerShell's call operator and dot-source (`then git
// push`, `(git push`, `& git push`, `. { git push }`).
const LEAD = new Set(["!", "{", "(", "&", ".", "if", "then", "else", "elif", "do", "while", "until"]);
// PowerShell's casts and arrays around a command: `[void](git push`, `@(git push`, `[void] (git push`.
const PS_PREFIX = /^(?:\[[\w.]+\])*@?[({]+|^(?:\[[\w.]+\])+$/;
const ASSIGN = /^[A-Za-z_]\w*=/;
// PowerShell saves a command's output with `$x = git push`, `$x=git push`, `[string]$x += git push` or
// `$o.p[0] = git push`.
const PS_ASSIGN = /^(?:\[[^\]]*\])*\$(?:\{[^}]*\}|[\w:]+)(?:\.\w+|\[[^\]]*\])*(?:([-+*/%]?=)(.*))?$/;
const PS_OP = /^[-+*/%]?=/;
function leadStripped(raw) {
  const w = [...raw];
  for (;;) {
    while (w.length && LEAD.has(w[0])) w.shift();
    if (w[0]) w[0] = w[0].replace(PS_PREFIX, "");
    if (w.length && !w[0]) { w.shift(); continue; }
    if (w.length && ASSIGN.test(w[0])) { w.shift(); continue; }
    const ps = w[0]?.match(PS_ASSIGN);
    if (ps?.[1]) { w.splice(0, 1, ...(ps[2] ? [ps[2]] : [])); continue; }
    if (ps && PS_OP.test(w[1] ?? "")) { const rest = w[1].replace(PS_OP, ""); w.splice(0, 2, ...(rest ? [rest] : [])); continue; }
    return w;
  }
}
// Wrappers that run the rest of their words as a command, and their options that take a value.
const PREFIX = {
  env: ["-u", "--unset", "-C", "--chdir"], command: [], nice: ["-n", "--adjustment"],
  timeout: ["-s", "--signal", "-k", "--kill-after"], nohup: [], exec: ["-a"], time: [], stdbuf: ["-i", "-o", "-e"],
  setsid: [], xargs: ["-I", "-L", "-n", "-P", "-d", "-E", "-s", "-a", "--arg-file", "--delimiter", "--max-args",
    "--max-procs", "--max-chars", "--process-slot-var"],
  // The lab tests run as `wsl -d Ubuntu -- bash dynamic-labs/regression-tests/automated/<lab>/run.sh`.
  wsl: ["-d", "--distribution", "-u", "--user", "--cd"],
};
const SHELLS = new Set(["sh", "bash", "zsh", "dash", "ksh", "fish"]);
const STRING_RUNNERS = new Set(["cmd", "eval", "invoke-expression", "iex", "invoke-command", "icm"]);
const GIT_VALUED = new Set(["-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"]);
const gitSub = (w) => {
  for (let i = 1; i < w.length; i++) {
    if (GIT_VALUED.has(w[i])) i++;
    else if (!w[i].startsWith("-")) return w[i];
  }
  return undefined;
};

// The commands one simple command runs: itself, and what a wrapper (env, nice, xargs, find -exec, wsl, ...) runs
// from its words. Lane and integrator rules apply to each. A wrapper that runs a string (sh -c, cmd, eval) can't
// be read word by word, so it is refused. `fromArgs`: find or xargs adds words to it.
function commandsIn(raw, fromArgs = false, repl = null, depth = 0) {
  if (depth > 4) deny("too many nested wrappers to read");
  const w = leadStripped(raw);
  if (!w.length || !w[0]) return [];
  if (w[0].startsWith("$")) {
    // PowerShell shows a value here (`$x`, `$x.Count`, `$x | …`) and runs one only through & or `.`, refused above;
    // bash runs the command the variable holds (`$g push`, `"$g" push`, `${g} push`).
    if (PS) return [];
    deny(`\`${w[0]}\` runs a command held in a variable, which the guard can't read; run it by name`);
  }
  const name = cmdName(w[0]);
  const self = { w: [name, ...w.slice(1)], at: w[0], fromArgs, repl };
  const inner = (rest, args = fromArgs, r = repl) => commandsIn(rest, args, r, depth + 1);

  if (name in PREFIX) {
    const valued = new Set(PREFIX[name]);
    let i = 1;
    let xrepl = null;
    for (; i < w.length; i++) {
      const t = w[i];
      if (t === "--") { i++; break; }
      if (name === "wsl" && (t === "-e" || t === "--exec")) { i++; break; }
      if (name === "env" && (t === "-" || ASSIGN.test(t))) continue;
      if (name === "env" && /^(-S|--split-string)/.test(t)) deny("`env -S` runs a string the guard can't read");
      if (!t.startsWith("-") || t === "-") break;
      if (name === "xargs" && /^(-I|-i|--replace)/.test(t)) xrepl = t === "-I" ? w[i + 1] : t.replace(/^(-I|-i|--replace=?)/, "") || "{}";
      if (valued.has(t)) i++;
    }
    if (name === "timeout") i++; // the duration
    const rest = w.slice(i);
    if (name === "xargs") return [self, ...(rest.length ? inner(rest, true, xrepl) : [])];
    return [self, ...inner(rest)];
  }
  if (name === "find") {
    const out = [self];
    for (let i = 1; i < w.length; i++) {
      if (!/^-(exec|execdir|ok|okdir)$/.test(w[i])) continue;
      let j = i + 1;
      while (j < w.length && !/^(\\?;|\+)$/.test(w[j])) j++;
      out.push(...inner(w.slice(i + 1, j), true, "{}"));
      i = j;
    }
    return out;
  }
  if (SHELLS.has(name)) {
    let script = false;
    for (let i = 1; i < w.length; i++) {
      const t = w[i];
      if (/^\d*<+$/.test(t)) { i++; continue; }
      if (/^\d*</.test(t)) continue;
      if (t === "--") { script = i + 1 < w.length; break; }
      if (/^-[A-Za-z]*[cs][A-Za-z]*$/.test(t) || t === "--command") deny(`\`${name} -c\` runs a string the guard can't read; run the command itself`);
      if (/^[-+][oO]$|^--(rcfile|init-file)$/.test(t)) { i++; continue; }
      if (/^[-+]/.test(t)) continue;
      script = true;
      break;
    }
    if (!script) deny(`\`${name}\` with no script reads its commands from input, which the guard can't read`);
    return [self];
  }
  if (name === "pwsh" || name === "powershell") {
    // Parameters may be shortened (-c, -com, -e, -f) and start with -, -- or /.
    const params = [];
    for (let i = 1; i < w.length; i++) if (/^(--?|\/)[A-Za-z]+$/.test(w[i])) params.push([w[i].replace(/^(--?|\/)/, "").toLowerCase(), i]);
    const file = params.find(([p]) => "file".startsWith(p));
    if (params.some(([p]) => p.startsWith("c") || p === "ec" || "encodedcommand".startsWith(p)) || !file || w[file[1] + 1] === "-") {
      deny(`\`${name}\` runs only with -File here: a -Command string can't be read by the guard`);
    }
    return [self];
  }
  if (STRING_RUNNERS.has(name)) deny(`\`${name}\` runs a string the guard can't read; run the command itself`);
  if (["start-process", "start", "saps"].includes(name)) {
    const runs = w.slice(1).flatMap((t) => t.split(",")).map((t) => cmdName(t.replace(/^['"]|['"]$/g, "")));
    if (runs.some((r) => r === "git" || r === "docker" || r === "wsl" || SHELLS.has(r) || STRING_RUNNERS.has(r) || r === "pwsh" || r === "powershell" || WEB.has(r))) {
      deny(`\`${name}\` may not start git, Docker, WSL, a shell or a web fetch; run the command itself`);
    }
  }
  return [self];
}

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
  if (/(?<![\w.-])git(?:\.exe)?["']?(?:\s+(?:-C|-c|--git-dir|--work-tree|--namespace|--config-env)\s+\S+|\s+-\S+)*\s+["']?[$`@]/i.test(masked)) {
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
