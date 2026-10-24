import { test } from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdtempSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { runHook, tempRepo, writeFiles } from "./test-helpers.mjs";

const owner = (text) => ({ type: "user", message: { content: text } });
const said = (tokens, content = [{ type: "text", text: "Done." }]) => ({
  type: "assistant",
  timestamp: new Date().toISOString(),
  message: { content, usage: { input_tokens: 5, cache_read_input_tokens: tokens - 5, cache_creation_input_tokens: 0 } },
});
const toolUse = (id, name, input) => ({ type: "tool_use", id, name, input });
const result = (id, text) => ({ type: "user", message: { content: [{ type: "tool_result", tool_use_id: id, content: text }] } });
const notification = (id) =>
  owner(`<task-notification>\n<tool-use-id>${id}</tool-use-id>\n<status>completed</status>\n</task-notification>`);

function stop(entries, { session = randomUUID(), window = "200000" } = {}) {
  const transcript = path.join(mkdtempSync(path.join(os.tmpdir(), "bc-handoff-")), "t.jsonl");
  writeFileSync(transcript, entries.map((e) => JSON.stringify(e)).join("\n"));
  return runHook("handoff-nudge.mjs", { hook_event_name: "Stop", session_id: session, transcript_path: transcript, cwd: os.tmpdir() }, {
    env: { CLAUDE_CODE_AUTO_COMPACT_WINDOW: window },
  });
}

test("stays quiet below 60% of the auto-compact window", () => {
  const r = stop([owner("Rework the mining slide."), said(119_000)]);
  assert.equal(r.status, 0);
  assert.equal(r.stdout + r.stderr, "");
});

test("past the line, sends Claude back to write the handoff, once per session", () => {
  const session = randomUUID();
  const r = stop([owner("Rework the mining slide."), said(125_000)], { session });
  assert.equal(r.status, 2);
  assert.match(r.stderr, /125k tokens, past the handoff line \(120k/);
  assert.match(r.stderr, /\/handoff/);
  assert.equal(stop([owner("Go on."), said(130_000)], { session }).status, 0, "already asked in this session");
});

test("asks again after a compaction brings the context back under the line", () => {
  const session = randomUUID();
  assert.equal(stop([owner("a"), said(125_000)], { session }).status, 2);
  assert.equal(stop([owner("b"), said(40_000)], { session }).status, 0);
  assert.equal(stop([owner("c"), said(125_000)], { session }).status, 2);
});

test("a sprint session is never sent to write a handoff: it reports on its issues", () => {
  assert.equal(stop([owner("/sprint-lane lessons"), said(125_000)]).status, 0);
  const expanded = "<command-message>sprint-integrate</command-message>\n<command-name>/sprint-integrate</command-name>";
  const r = stop([owner(expanded), said(125_000)]);
  assert.equal(r.status, 0);
  assert.equal(r.stderr, "");
  assert.equal(stop([owner("Run /sprint-status for me."), said(125_000)]).status, 2, "the owner's own session still is");
});

test("the line follows the auto-compact window setting", () => {
  assert.equal(stop([owner("a"), said(59_000)], { window: "100000" }).status, 0);
  assert.equal(stop([owner("a"), said(61_000)], { window: "100000" }).status, 2);
});

test("waits for background work to finish, then asks on the turn after its notification", () => {
  const session = randomUUID();
  const launched = [
    owner("Render the site."),
    said(125_000, [toolUse("toolu_A1", "Bash", { command: "quarto render", run_in_background: true })]),
    result("toolu_A1", "Command running in background with ID: b1"),
    said(125_000),
  ];
  assert.equal(stop(launched, { session }).status, 0, "the render is still going");
  assert.equal(stop([...launched, notification("toolu_A1"), said(126_000)], { session }).status, 2);
});

test("a foreground command whose output mentions background work doesn't hold it", () => {
  const r = stop([
    owner("Search the logs."),
    said(125_000, [toolUse("toolu_B1", "Bash", { command: "grep background log.txt" })]),
    result("toolu_B1", "Command running in background with ID: old"),
    said(125_000),
  ]);
  assert.equal(r.status, 2);
});

test("doesn't ask when this turn already saved a handoff", () => {
  const r = stop([
    owner("/handoff"),
    said(125_000, [toolUse("toolu_C1", "Bash", { command: "node tools/handoff-notes.mjs save .handoff/slide-edit.md" })]),
    result("toolu_C1", "saved 2026-10-17-1405-slide-edit.md"),
    said(125_000),
  ]);
  assert.equal(r.status, 0);
});

test("finishes quietly on input it can't read", () => {
  const missing = runHook("handoff-nudge.mjs", { hook_event_name: "Stop", session_id: "x", transcript_path: path.join(os.tmpdir(), "no-such.jsonl") });
  assert.equal(missing.status, 0);
  assert.equal(runHook("handoff-nudge.mjs", {}).status, 0);
});

const sessionStart = (cwd) => runHook("handoff-nudge.mjs", { hook_event_name: "SessionStart", source: "clear", cwd });

test("at session start, tells the owner about open notes and how to resume them", () => {
  const repo = tempRepo({ ".gitignore": ".handoff/\n" });
  assert.equal(sessionStart(repo).stdout, "", "no notes, no message");

  writeFiles(repo, {
    ".handoff/2026-10-17-1405-slide-edit.md": "# Handoff: slide edit\nheader\n",
    ".handoff/done/2026-10-16-0900-old.md": "# Handoff: old\nheader\nResumed: 2026-10-16 10:00\n",
  });
  assert.equal(sessionStart(repo).json?.systemMessage, "Open handoff note: 2026-10-17-1405-slide-edit.md. Type /handoff resume to continue it.");

  writeFiles(repo, { ".handoff/2026-10-17-1530-glossary.md": "# Handoff: glossary\nheader\n" });
  assert.match(sessionStart(repo).json?.systemMessage, /^2 open handoff notes, newest 2026-10-17-1530-glossary\.md\. Type \/handoff resume/);
});

test("at session start, tells Claude the sprint file overrides CLAUDE.md only inside its window", () => {
  const HOUR = 60 * 60 * 1000;
  const stamp = (ms) => new Date(Date.now() + ms).toISOString().slice(0, 16).replace(/[-:]/g, "");
  const repo = tempRepo({ ".gitignore": ".handoff/\n" });
  const context = () => sessionStart(repo).json?.hookSpecificOutput?.additionalContext;
  const sprint = (line) => writeFiles(repo, { "docs/sprint.md": `# Sprint\n\n${line}\n` });
  const window = (from, to) => `**Window (UTC):** \`${stamp(from)}\` to \`${stamp(to)}\` (the owner's).`;

  assert.equal(context(), undefined, "no docs/sprint.md");
  sprint("No window line here.");
  assert.equal(context(), undefined);
  const end = stamp(HOUR);
  sprint(`**Window (UTC):** \`${stamp(-HOUR)}\` to \`${end}\` (the owner's).`);
  assert.equal(context(), `Sprint window open until ${end} UTC: \`docs/sprint.md\` overrides CLAUDE.md where ` +
    "they conflict. Lab tests and Docker run only in the labs lane's worktree: `--fresh-start` here would wipe its containers.");
  assert.equal(sessionStart(path.join(repo, "docs")).json?.hookSpecificOutput?.hookEventName, "SessionStart", "from a subfolder");
  sprint(window(-2 * HOUR, -HOUR));
  assert.equal(context(), undefined, "closed");
  sprint(window(HOUR, 2 * HOUR));
  assert.equal(context(), undefined, "not open yet");
  sprint("**Window (UTC):** `20260101T0000` to `20260101T0000` (placeholder).");
  assert.equal(context(), undefined, "the placeholder");

  sprint(window(-HOUR, HOUR));
  writeFiles(repo, { ".handoff/2026-10-17-1405-slide-edit.md": "# Handoff: slide edit\nheader\n" });
  const both = sessionStart(repo).json;
  assert.match(both.systemMessage, /^Open handoff note/);
  assert.match(both.hookSpecificOutput.additionalContext, /^Sprint window open/);
});

test("at session start outside a git repository, says nothing", () => {
  const r = sessionStart(mkdtempSync(path.join(os.tmpdir(), "bc-nogit-")));
  assert.equal(r.status, 0);
  assert.equal(r.stdout, "");
});
