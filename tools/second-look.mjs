// `node tools/second-look.mjs "<the owner's request>"`: a second review of the current change by another model,
// through agy (headless and read-only), run beside the reviewer agent. It reviews everything since origin/main:
// commits, uncommitted edits and new files. It prints the findings: a valid [blocker] holds the change like a
// reviewer's blocker, and its notes never do. When no model answers, its first line is "Second look: retry": no
// verdict, so the change waits for a run that answers and never ships on it (owner's policy, 28 Oct 2026: machine
// failures retry). A change that touches a rail also gets the rail audit (tools/rail-audit.mjs), a deep review of
// one question by Argon, Opus or Flash (never Sonnet), whose first line says whether the rail change ships, is held
// for the owner, or runs again.
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { ORDER, askFirstAvailable, askModel, buildPrompt, byLine, diffStats, pickDepth } from "./agy.mjs";
import { RAILS, RAIL_MODELS, couldNotRun, railAction, railDiff, railFiles, railVerdict } from "./rail-audit.mjs";

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

// One agy review of the material, with the prompt in tools/<promptFile>, by the first of `models` that answers.
function review(promptFile, material, models, tmp) {
  const prompt = buildPrompt(readFileSync(path.join(ROOT, "tools", promptFile), "utf8"), material);
  return askFirstAvailable(models, (model) =>
    askModel((args) => run("agy", args), prompt, model, ["--add-dir", tmp]),
  );
}

function look(material, pick, tmp) {
  try {
    const answer = review("second-look.md", material, ORDER[pick.depth], tmp);
    return `Second look by ${byLine({ ...answer, ...pick })}\n\n${answer.response}`;
  } catch (err) {
    return couldNotRun("Second look", "The change", err.message);
  }
}

// The rail files' diff alone, always deep, answered by Argon, Opus or Flash, in that order (RAIL_MODELS). A rail
// ships only on a clear no; with none of them answering, the audit runs again later, and the rail change waits
// unpushed.
function railAudit(request, diff, stats, rails, tmp) {
  const pick = pickDepth({ kind: "change", ...stats }, RAILS);
  const touches = `It touches ${rails.join(", ")}.`;
  const material = path.join(tmp, "rails.md");
  writeFileSync(
    material,
    `# The owner's request\n\n${request}\n\n# The change to the rails\n\n\`\`\`diff\n${railDiff(diff)}\`\`\`\n`,
  );
  try {
    const answer = review("rail-audit.md", material, RAIL_MODELS, tmp);
    return `${railAction(railVerdict(answer.response))}\n${touches} Rail audit by ${byLine({ ...answer, ...pick })}\n\n${answer.response}`;
  } catch (err) {
    return `${couldNotRun("Rail audit", "The rail change", err.message)}\n${touches}`;
  }
}

function secondLook(request, tmp) {
  const { base, diff } = change();
  if (!diff.trim()) return "Second look skipped: nothing has changed since origin/main.";
  const stats = diffStats(diff);
  const pick = pickDepth({ kind: "change", ...stats }, DEEP_PATHS);
  const shown =
    diff.length > MAX_DIFF ? `${diff.slice(0, MAX_DIFF)}\n... (diff truncated; read the rest from disk)\n` : diff;
  const material = path.join(tmp, "material.md");
  writeFileSync(
    material,
    `# The owner's request\n\n${request}\n\n# The change since ${base.slice(0, 8)}, with uncommitted edits and new files\n\n\`\`\`diff\n${shown}\`\`\`\n`,
  );
  const out = [look(material, pick, tmp)];
  const rails = railFiles(stats.files);
  if (rails.length > 0) out.push(railAudit(request, diff, stats, rails, tmp));
  return out.join("\n\n");
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
