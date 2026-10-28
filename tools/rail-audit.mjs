// The rail audit (owner's policy, 28 Oct 2026: "rails: Auto; audit holds loosening"). A change to the rails, the
// checks that stop a bad change, ships without the owner unless a deep agy review answers yes to one question: does
// it loosen, bypass or disable any check, guard, gate, hook or required review? A loosened gate hides its own
// failure, so only a "no" ships; a "yes", or no verdict at all, holds the change for the owner with the reason.
// tools/second-look.mjs runs it on every change that touches a rail. YODC and Terminal Dusk hold the same rule.

// The rails: the Claude Code hooks and the sprint guard, the check, the git hooks, the workflows, and the settings
// that wire the hooks and hold the permission rules.
export const RAILS = ["tools/hooks/", "tools/check.py", ".githooks/", ".github/", ".claude/settings"];

// The files of a change that are rails.
export const railFiles = (files) => files.filter((f) => RAILS.some((r) => f.startsWith(r)));

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
