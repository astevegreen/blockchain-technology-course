// `node tools/second-look.mjs "<the owner's request>"`: a second review of the current change by another model,
// through agy (headless and read-only), run beside the reviewer agent. It reviews everything since origin/main:
// commits, uncommitted edits and new files. It prints the findings, or one "skipped" line, and never fails the task.
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { ORDER, TIMEOUT, askFirstAvailable, buildPrompt, byLine, diffStats, parseReply, pickDepth } from "./agy.mjs";

const ROOT = path.resolve(import.meta.dirname, "..");
const USAGE = 'usage: node tools/second-look.mjs "<the owner\'s request>"';
const MAX_DIFF = 200_000;
// Where a mistake reaches students or breaks a hard rule: the quiz banks and their answers, what the Pages and VM
// workflows pack for students, the sources every claim cites, and the checks. A change touching one gets the
// deep review.
const DEEP_PATHS = [
  "quizes/",
  ".github/workflows/pages.yml",
  ".github/workflows/vm-build.yml",
  "blockchain-course/lessons/references/Blockchain.bib",
  "tools/check.py",
  "tools/hooks/",
];

function run(cmd, args) {
  return spawnSync(cmd, args, {
    cwd: ROOT,
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 64 * 1024 * 1024,
    timeout: 11 * 60_000,
  });
}
const git = (...args) => run("git", args).stdout ?? "";

// The diff from where this branch left origin/main to the working tree, then each new file as an added one.
function change() {
  const base = git("merge-base", "origin/main", "HEAD").trim() || "HEAD";
  let diff = git("diff", "--no-ext-diff", base);
  for (const file of git("ls-files", "--others", "--exclude-standard", "-z").split("\0").filter(Boolean))
    diff += git("diff", "--no-ext-diff", "--no-index", "--", "/dev/null", file);
  return { base, diff };
}

function secondLook(request, tmp) {
  const { base, diff } = change();
  if (!diff.trim()) return "Second look skipped: nothing has changed since origin/main.";
  const pick = pickDepth({ kind: "change", ...diffStats(diff) }, DEEP_PATHS);
  const shown =
    diff.length > MAX_DIFF ? `${diff.slice(0, MAX_DIFF)}\n... (diff truncated; read the rest from disk)\n` : diff;
  const material = path.join(tmp, "material.md");
  writeFileSync(
    material,
    `# The owner's request\n\n${request}\n\n# The change since ${base.slice(0, 8)}, with uncommitted edits and new files\n\n\`\`\`diff\n${shown}\`\`\`\n`,
  );
  const prompt = buildPrompt(readFileSync(path.join(ROOT, "tools", "second-look.md"), "utf8"), material);
  try {
    const answer = askFirstAvailable(ORDER[pick.depth], (model) =>
      parseReply(
        run("agy", [
          "-p",
          prompt,
          "--output-format",
          "json",
          "--model",
          model,
          "--print-timeout",
          TIMEOUT,
          "--add-dir",
          tmp,
        ]),
      ),
    );
    return `Second look by ${byLine({ ...answer, ...pick })}\n\n${answer.response}`;
  } catch (err) {
    return `Second look skipped: ${err.message}`;
  }
}

const request = process.argv.slice(2).join(" ").trim();
if (!request) {
  console.error(USAGE);
  process.exit(2);
}
const tmp = mkdtempSync(path.join(os.tmpdir(), "second-look-"));
try {
  console.log(secondLook(request, tmp));
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
