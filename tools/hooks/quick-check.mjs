// PostToolUse (Edit|Write): fast checks on the one file just edited. No rendering: it must take seconds.
// Lints lessons (tools/qmd_lint.py), verifies quiz banks and syntax-checks Python.
// Silent when everything passes; otherwise up to 20 lines go back to Claude (exit 2).
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { readInput, repoRootFor, canonical, toPosix, limitLines, runPython } from "./shared.mjs";

const input = await readInput();
const file = input.tool_input?.file_path;
if (!file || !existsSync(file)) process.exit(0);

// Only files inside the repository are checked; files elsewhere, such as Claude's scratchpad, pass silently.
const root = repoRootFor(file);
if (!root) process.exit(0);
const rel = toPosix(path.relative(root, canonical(file)));
if (rel.startsWith("../") || path.isAbsolute(rel)) process.exit(0);
const problems = [];

const failed = ({ status, missing }) => !missing && status !== 0;

// 1. Lessons: the lesson linter.
if (/^blockchain-course\/lessons\/.*\.qmd$/i.test(rel) && !rel.includes("/references/") && existsSync(path.join(root, "tools", "qmd_lint.py"))) {
  const r = runPython(["tools/qmd_lint.py", rel], { cwd: root, timeout: 30_000 });
  if (failed(r)) problems.push(...r.output.split(/\r?\n/));
}

// 2. Quiz banks: must parse, then pass the distractor-length verifier.
if (/^quizes\/quiz_json\/[^/]+\.json$/i.test(rel)) {
  const text = readFileSync(file, "utf8");
  try {
    JSON.parse(text);
    if (existsSync(path.join(root, "quizes", "verify_single_quiz.py"))) {
      const r = runPython(["quizes/verify_single_quiz.py", "--file", rel], { cwd: root, timeout: 30_000 });
      if (failed(r)) problems.push(...r.output.split(/\r?\n/).filter((l) => /violation|FAIL|Error|Target|count:/i.test(l)));
    }
  } catch (err) {
    const pos = /position (\d+)/.exec(err.message);
    const line = pos ? text.slice(0, Number(pos[1])).split("\n").length : 1;
    problems.push(`${rel}:${line} ${err.message}`);
  }
}

// 3. Python: compiles (without writing __pycache__).
if (/\.py$/i.test(rel)) {
  const r = runPython(["-c", "import sys; compile(open(sys.argv[1], 'rb').read(), sys.argv[1], 'exec')", rel], { cwd: root, timeout: 15_000 });
  if (failed(r)) problems.push(...r.output.split(/\r?\n/).filter((l) => l.trim()).slice(-4));
}

if (problems.length) {
  process.stderr.write(limitLines(`quick-check found problems in ${rel}:\n${problems.join("\n")}`, 20) + "\n");
  process.exit(2);
}
