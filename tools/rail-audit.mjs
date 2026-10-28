// The rail audit (owner's policy, 28 Oct 2026: "rails: Auto; audit holds loosening"). A change to the rails, the
// checks that stop a bad change, ships without the owner unless a deep agy review answers yes to one question: does
// it loosen, bypass or disable any check, guard, gate, hook or required review? A loosened gate hides its own
// failure, so only a "no" ships; a "yes", or an answer with no verdict, holds the change for the owner with the
// reason. An audit no model answered is the machine's failure: it runs again, and the rail change waits unpushed.
// tools/second-look.mjs runs it on every change that touches a rail. YODC and Terminal Dusk hold the same rule.
import { ARGON, FLASH, OPUS } from "./agy.mjs";

// The rails, as path prefixes: every file whose content decides whether a change ships. The Claude Code hooks and
// the sprint guard; the settings that wire hooks and hold the permission rules; the sprint skills and agents, which
// wire the guard and say what a blocker is; the git hooks and the workflows; the check, with the lint, quiz and
// glossary checks it runs and its own tests; the sprint queue, which decides what holds and what reaches the
// integrator; and the second look and this audit, with GEMINI.md, which tells agy what a blocker is. The sprint
// guard locks every one of them for the lanes (tools/hooks/sprint-guard.mjs, LOCKED).
export const RAILS = [
  "tools/hooks/",
  ".claude/settings",
  ".claude/skills/sprint-",
  ".claude/agents/implementer.md",
  ".claude/agents/reviewer.md",
  ".githooks/",
  ".github/",
  "tools/check.py",
  "tools/qmd_lint.py",
  "tools/tests/test_check.py",
  "tools/tests/test_qmd_lint.py",
  "quizes/verify_single_quiz.py",
  "blockchain-course/glossary/scripts/validate_glossary.py",
  "tools/sprint/",
  "tools/agy.mjs",
  "tools/second-look",
  "tools/rail-audit",
  "GEMINI.md",
];

// The files of a change that are rails.
export const railFiles = (files) => files.filter((f) => RAILS.some((r) => f.startsWith(r)));

// The models that may audit a rail, in order (owner, 28 Oct 2026): the two deepest readers, then Flash, so the audit
// never waits on the deep models' usage. Never Sonnet: the Claude reviewer already covers that family. With all
// three out, no model answered, and the audit runs again later. Its own order, not agy.mjs's ORDER, whose deep list
// ends in Sonnet (agy.mjs stays identical in the three repos).
export const RAIL_MODELS = [ARGON, OPUS, FLASH];

// The parts of a unified diff that change a rail: the audit judges the rails alone, since the second look already
// reviews the rest of the change.
export function railDiff(diff) {
  return diff
    .split(/^(?=diff --git )/m)
    .filter((part) => railFiles([/^diff --git a\/.+? b\/(.+)$/m.exec(part)?.[1] ?? ""]).length > 0)
    .join("");
}

// The verdict on the answer's first `LOOSENS:` line: true (loosens), false (does not) or null (no verdict).
export function railVerdict(response) {
  const m = /^\W*LOOSENS:\W*(yes|no)\b/im.exec(response ?? "");
  return m ? m[1].toLowerCase() === "yes" : null;
}

// What the session does with it, in one line for the report.
export function railAction(verdict) {
  if (verdict === false) return "Rail audit: no loosening found; the change ships like any other.";
  if (verdict === true) return "Rail audit: LOOSENS. Hold the rail change for the owner with the reasons below; don't push it.";
  return "Rail audit: no verdict. Hold the rail change for the owner (a rail ships only on a clear no); don't push it.";
}

// The first line of a review that could not run (no model answered, agy missing or failing): it gave no verdict, so
// it is retried. Nothing it covers ships meanwhile, and it never waits for the owner: the machine failed, not the
// work. `review` names it ("Second look", "Rail audit"), `covers` what waits for it.
export function couldNotRun(review, covers, message) {
  return `${review}: retry. It could not run, so it gave no verdict: run it again later. ${covers} does not ship until it answers, and is not held for the owner: the machine failed, not the work. (${message})`;
}
