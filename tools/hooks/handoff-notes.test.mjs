import { after, test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { claim, close, list, nothingOutstanding, openNotes, recordSession, save, sinceNote, storeDir, sweep } from "../handoff-notes.mjs";
import { canonical, toPosix } from "./shared.mjs";
import { sh, tempRepo, writeFiles } from "./test-helpers.mjs";

const NOW = new Date(2026, 9, 17, 14, 5);
const LATER = new Date(2026, 9, 17, 15, 30);
const DRAFT =
  "# Handoff: slide edit\n(save fills this line)\n\n## Goal\nRework the mining slide.\n\n## Next\n1. Edit blockchain-course/lessons/bitcoin/01-BF-bitcoin_origins_and_mechanics.qmd\n";
const posix = (p) => toPosix(canonical(p));
const repoWithNotes = () => tempRepo({ ".gitignore": ".handoff/\n" });
const lineTwo = (file) => readFileSync(file, "utf8").split("\n")[1];

function saveDraft(cwd, slug, now = NOW, text = DRAFT) {
  writeFiles(cwd, { [`.handoff/${slug}.md`]: text });
  return save(`.handoff/${slug}.md`, { cwd, now });
}

test("save stamps line 2 with the time, branch, HEAD, tree state and folder, and files the note", () => {
  const repo = repoWithNotes();
  writeFiles(repo, { "notes-a.txt": "a\n" });
  const r = saveDraft(repo, "slide-edit");
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /^saved 2026-10-17-1405-slide-edit\.md/);
  const note = path.join(repo, ".handoff", "2026-10-17-1405-slide-edit.md");
  const head = sh("git", ["rev-parse", "--short", "HEAD"], repo);
  assert.equal(lineTwo(note), `2026-10-17 14:05 · branch main · HEAD ${head} · 1 uncommitted · ${posix(repo)}`);
  assert.ok(!existsSync(path.join(repo, ".handoff", "slide-edit.md")), "the draft is filed, not left beside the note");
});

test("a note saved in a worktree goes to the main checkout's .handoff folder", () => {
  const repo = repoWithNotes();
  const wt = path.join(repo, "..", `${path.basename(repo)}-wt`);
  sh("git", ["worktree", "add", "-q", "-b", "task/7", wt], repo);
  assert.equal(saveDraft(wt, "slide-edit").code, 0);
  const note = path.join(repo, ".handoff", "2026-10-17-1405-slide-edit.md");
  assert.ok(existsSync(note), "the note is in the main checkout");
  assert.match(lineTwo(note), new RegExp(`branch task/7 · .* · ${posix(wt).replace(/[.\\]/g, "\\$&")}$`));
  assert.ok(!existsSync(path.join(wt, ".handoff", "slide-edit.md")));
});

test("save refuses a note a cold reader couldn't start from, and files nothing", () => {
  const repo = repoWithNotes();
  const cases = [
    [DRAFT.replace("## Next", "## Later"), /no "## Next" section/],
    [DRAFT.replace("# Handoff: slide edit", "# Card draw"), /line 1 must be/],
    [DRAFT + "x\n".repeat(40), /keep it to 40/],
    [`${DRAFT}Resumed: 2026-10-17 15:30\n`, /write a new note/],
  ];
  for (const [text, why] of cases) {
    const r = saveDraft(repo, "bad", NOW, text);
    assert.equal(r.code, 1);
    assert.match(r.out, why);
  }
  assert.equal(list({ cwd: repo }).out, "no open handoff notes");
});

test("list shows open notes newest first, with their header line, and not claimed ones", () => {
  const repo = repoWithNotes();
  assert.equal(list({ cwd: repo }).out, "no open handoff notes");
  saveDraft(repo, "slide-edit", NOW);
  saveDraft(repo, "glossary", LATER);
  const lines = list({ cwd: repo }).out.split("\n");
  assert.equal(lines.length, 2);
  assert.match(lines[0], /^2026-10-17-1530-glossary.md {2}2026-10-17 15:30 · branch main/);
  assert.match(lines[1], /^2026-10-17-1405-slide-edit\.md/);
  claim("2026-10-17-1530-glossary.md", { cwd: repo, now: LATER });
  assert.match(list({ cwd: repo }).out, /^2026-10-17-1405-slide-edit\.md {2}/);
});

test("claim takes the only open note, marks it Resumed and reports commits made since", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit");
  writeFiles(repo, { "notes-b.txt": "b\n" });
  sh("git", ["add", "-A"], repo);
  sh("git", ["commit", "-q", "-m", "later work"], repo);
  const r = claim(undefined, { cwd: repo, now: LATER });
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /^# Handoff: slide edit\n/);
  assert.match(r.out, /\nResumed: 2026-10-17 15:30\n\n## Since the note\n/);
  assert.match(r.out, /Branch: on main, as the note was\./);
  assert.match(r.out, /Commits on main since the note:\n {2}\w+ later work/);
  assert.ok(existsSync(path.join(repo, ".handoff", "done", "2026-10-17-1405-slide-edit.md")));
  assert.equal(list({ cwd: repo }).out, "no open handoff notes");
});

test("claim with several open notes claims nothing and lists them for the owner to pick", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit", NOW);
  saveDraft(repo, "glossary", LATER);
  const r = claim(undefined, { cwd: repo });
  assert.equal(r.code, 4);
  assert.match(r.out, /2 open notes; ask the owner which one/);
  assert.match(r.out, /glossary.md[\s\S]*slide-edit\.md/);
  assert.equal(list({ cwd: repo }).out.split("\n").length, 2);
});

test("a note another session claimed can't be claimed again", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit");
  const name = "2026-10-17-1405-slide-edit.md";
  assert.equal(claim(name, { cwd: repo }).code, 0);
  const again = claim(name, { cwd: repo });
  assert.equal(again.code, 3);
  assert.match(again.out, /already claimed/);
  assert.equal(readdirSync(path.join(repo, ".handoff", "done")).length, 1);
});

test("claim takes a slug for the open note saved under it, with or without .md or the timestamp", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "kickoff-applied", NOW);
  saveDraft(repo, "glossary", NOW);
  saveDraft(repo, "slide-edit", NOW);
  const done = (name) => existsSync(path.join(repo, ".handoff", "done", name));

  const r = claim("kickoff-applied", { cwd: repo, now: LATER });
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /^# Handoff: slide edit\n/);
  assert.ok(done("2026-10-17-1405-kickoff-applied.md"));
  assert.equal(claim("glossary.md", { cwd: repo }).code, 0);
  assert.ok(done("2026-10-17-1405-glossary.md"));
  assert.equal(claim("2026-10-17-1405-slide-edit", { cwd: repo }).code, 0);
  assert.ok(done("2026-10-17-1405-slide-edit.md"));

  const none = claim("budget", { cwd: repo });
  assert.equal(none.code, 1);
  assert.match(none.out, /no open note named budget/);
});

test("a slug saved twice claims nothing and lists both for the owner to pick", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit", NOW);
  saveDraft(repo, "slide-edit", LATER);
  saveDraft(repo, "glossary", LATER);
  const r = claim("slide-edit", { cwd: repo });
  assert.equal(r.code, 4);
  assert.match(r.out, /^2 open notes named slide-edit; ask the owner which one/);
  assert.match(r.out, /1530-slide-edit\.md[\s\S]*1405-slide-edit\.md/);
  assert.doesNotMatch(r.out, /glossary/);
  assert.equal(list({ cwd: repo }).out.split("\n").length, 3);
});

test("a full file name claims only that note, never a newer one saved under the same slug", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit", NOW);
  const first = "2026-10-17-1405-slide-edit.md";
  assert.equal(claim(first, { cwd: repo }).code, 0);
  saveDraft(repo, "slide-edit", LATER);
  const again = claim(first, { cwd: repo });
  assert.equal(again.code, 3);
  assert.match(again.out, /already claimed/);
  assert.match(list({ cwd: repo }).out, /^2026-10-17-1530-slide-edit\.md/);
});

test("since the note sends the next session to the folder or branch that holds the work", () => {
  const repo = repoWithNotes();
  const wt = path.join(repo, "..", `${path.basename(repo)}-wt2`);
  sh("git", ["worktree", "add", "-q", "-b", "task/9", wt], repo);
  writeFiles(wt, { "notes-c.txt": "c\n" });
  saveDraft(wt, "slide-edit");
  const header = lineTwo(path.join(repo, ".handoff", "2026-10-17-1405-slide-edit.md"));

  const fromMain = sinceNote(header, repo).join("\n");
  assert.match(
    fromMain,
    new RegExp(`task/9 is checked out in ${posix(wt).replace(/[.\\]/g, "\\$&")}\\. Continue there`),
  );
  assert.match(fromMain, /Uncommitted: 1 files in .* now; the note saw 1 uncommitted\./);

  sh("git", ["worktree", "remove", "--force", wt], repo);
  const gone = sinceNote(header, repo).join("\n");
  assert.match(gone, /this folder is on main\. Run `git switch task\/9`/);
  assert.match(gone, /folder .* is gone, and its 1 uncommitted files with it\./);
});

// ---- the session-ids index ---------------------------------------------------------------------

const SCRIPT = path.join(import.meta.dirname, "../handoff-notes.mjs");
const configs = [];
const configDir = () => {
  const dir = mkdtempSync(path.join(os.tmpdir(), "handoff-config-"));
  configs.push(dir);
  return dir;
};
after(() => {
  for (const dir of configs) rmSync(dir, { recursive: true, force: true });
});
const indexOf = (config) => JSON.parse(readFileSync(path.join(config, "session-ids", "handoff.json"), "utf8")).entries;
const run = (args, cwd, env) =>
  spawnSync(process.execPath, [SCRIPT, ...args], { cwd, encoding: "utf8", env: { ...process.env, ...env } });

test("the command line records which session saved and claimed a note, for the session-ids pane", () => {
  const repo = repoWithNotes();
  const config = configDir();
  const env = { CLAUDE_CODE_SESSION_ID: "session-a", CLAUDE_CONFIG_DIR: config };
  writeFiles(repo, { ".handoff/card-draw.md": DRAFT });
  const saved = run(["save", ".handoff/card-draw.md"], repo, env);
  assert.equal(saved.status, 0, saved.stdout);
  const name = /^saved (\S+\.md)/.exec(saved.stdout)[1];
  const claimed = run(["claim", name], repo, { ...env, CLAUDE_CODE_SESSION_ID: "session-b" });
  assert.equal(claimed.status, 0, claimed.stdout);

  const store = posix(path.join(repo, ".handoff"));
  const entries = indexOf(config).map((e) => [e.session, e.kind, e.note, toPosix(canonical(e.store))]);
  assert.deepEqual(entries, [
    ["session-a", "wrote", name, store],
    ["session-b", "resumed", name, store],
  ]);
});

test("outside a session, or on a refused save, nothing is recorded and the output is unchanged", () => {
  const repo = repoWithNotes();
  const config = configDir();
  writeFiles(repo, { ".handoff/card-draw.md": DRAFT });
  const saved = run(["save", ".handoff/card-draw.md"], repo, { CLAUDE_CODE_SESSION_ID: "", CLAUDE_CONFIG_DIR: config });
  assert.equal(saved.status, 0, saved.stdout);
  assert.match(saved.stdout, /^saved \S+\.md in /);
  assert.equal(existsSync(path.join(config, "session-ids")), false);

  writeFiles(repo, { ".handoff/thin.md": "# Handoff: thin\n" });
  const refused = run(["save", ".handoff/thin.md"], repo, { CLAUDE_CODE_SESSION_ID: "session-a", CLAUDE_CONFIG_DIR: config });
  assert.equal(refused.status, 1);
  assert.equal(existsSync(path.join(config, "session-ids")), false);
});

test("recordSession adds to the index, keeps the last 500, and never throws", () => {
  const config = configDir();
  const env = { CLAUDE_CODE_SESSION_ID: "session-a", CLAUDE_CONFIG_DIR: config };
  for (let i = 0; i < 502; i++) assert.equal(recordSession("wrote", `n${i}.md`, "C:\\x\\.handoff", { env, now: NOW }), true);
  const entries = indexOf(config);
  assert.equal(entries.length, 500);
  assert.deepEqual(entries[0], { session: "session-a", note: "n2.md", store: "C:/x/.handoff", kind: "wrote", at: NOW.getTime() });
  // An unwritable config folder (here, a file) is a quiet false.
  const blocked = path.join(config, "session-ids", "handoff.json");
  assert.equal(recordSession("wrote", "n.md", "s", { env: { ...env, CLAUDE_CONFIG_DIR: blocked } }), false);
});

test("an index that won't parse is left as it is, never replaced by one entry", () => {
  const config = configDir();
  const env = { CLAUDE_CODE_SESSION_ID: "session-a", CLAUDE_CONFIG_DIR: config };
  const file = path.join(config, "session-ids", "handoff.json");
  assert.equal(recordSession("wrote", "a.md", "s", { env }), true);
  const half = '{"entries": [{"session": "session-a", "no';
  writeFileSync(file, half);
  assert.equal(recordSession("wrote", "b.md", "s", { env }), false);
  assert.equal(readFileSync(file, "utf8"), half);
});

const FINISHED = DRAFT.replace("1. Edit blockchain-course/lessons/bitcoin/01-BF-bitcoin_origins_and_mechanics.qmd", "Complete");

test("nothingOutstanding: Complete alone, numbered or with trailing words", () => {
  for (const next of ["Complete", "1. Complete", "Complete.", "complete, nothing left"])
    assert.equal(nothingOutstanding(["## Next", next]), true, next);
});

test("nothingOutstanding: open work, or Complete with something pending", () => {
  assert.equal(nothingOutstanding(["## Next", "1. Run the tests"]), false);
  assert.equal(nothingOutstanding(["## Next", "Complete", "", "## Waiting on", "- run 123"]), false);
  assert.equal(nothingOutstanding(["## Decide first", "- merge? - recommend: yes", "## Next", "Complete"]), false);
  assert.equal(nothingOutstanding(["## Next", "Complete", "## Waiting on", ""]), true, "an empty section is no section");
});

test("save refuses a note with nothing outstanding and keeps the draft", () => {
  const repo = repoWithNotes();
  const r = saveDraft(repo, "done-work", NOW, FINISHED);
  assert.equal(r.code, 1);
  assert.match(r.out, /nothing is outstanding.*docs\/follow-ups\.md.*write no note/);
  assert.ok(existsSync(path.join(repo, ".handoff", "done-work.md")), "the draft stays");
  assert.equal(list({ cwd: repo }).out, "no open handoff notes");
});

test("save files a Complete note that still waits on a run or an owner answer", () => {
  const repo = repoWithNotes();
  assert.equal(saveDraft(repo, "waiting", NOW, [FINISHED, "## Waiting on", "- run 42", ""].join("\n")).code, 0);
  const asking = ["## Decide first", "- merge? - recommend: yes", "", "## Next"].join("\n");
  assert.equal(saveDraft(repo, "asking", LATER, FINISHED.replace("## Next", asking)).code, 0);
});

test("close files the note in done/ with its reason, by slug or full name; a second close fails", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit");
  const r = close("slide-edit", "finished in this session", { cwd: repo, now: LATER });
  assert.equal(r.code, 0, r.out);
  const text = readFileSync(path.join(repo, ".handoff", "done", "2026-10-17-1405-slide-edit.md"), "utf8");
  assert.ok(text.endsWith("Closed: 2026-10-17 15:30: finished in this session\n"), text);
  assert.ok(!text.includes("Resumed:"));
  assert.equal(close("2026-10-17-1405-slide-edit.md", "again", { cwd: repo }).code, 3);
  assert.equal(close("slide-edit", "again", { cwd: repo }).code, 1, "no open note of that name");
  saveDraft(repo, "glossary");
  assert.equal(close("glossary", "  ", { cwd: repo }).code, 1, "a reason is required");
  assert.equal(close("glossary", undefined, { cwd: repo }).code, 1);
  assert.equal(close("2026-10-17-1405-glossary.md", "overtaken", { cwd: repo }).code, 0, "full name");
});

test("close of a slug saved twice closes nothing and lists both", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit", NOW);
  saveDraft(repo, "slide-edit", LATER);
  const r = close("slide-edit", "done", { cwd: repo });
  assert.equal(r.code, 4);
  assert.match(r.out, /2 open notes named slide-edit/);
  assert.equal(openNotes(storeDir(repo)).length, 2);
});

test("close from the command line is not recorded in the session-ids index", () => {
  const repo = repoWithNotes();
  saveDraft(repo, "slide-edit");
  const config = mkdtempSync(path.join(os.tmpdir(), "bc-closecfg-"));
  after(() => rmSync(config, { recursive: true, force: true }));
  const run = (...args) =>
    spawnSync(process.execPath, [path.resolve(import.meta.dirname, "..", "handoff-notes.mjs"), ...args], {
      cwd: repo,
      encoding: "utf8",
      env: { ...process.env, CLAUDE_CODE_SESSION_ID: "sess-1", CLAUDE_CONFIG_DIR: config },
    });
  const r = run("close", "slide-edit", "finished", "here");
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /^closed 2026-10-17-1405-slide-edit\.md/);
  assert.ok(readFileSync(path.join(repo, ".handoff", "done", "2026-10-17-1405-slide-edit.md"), "utf8").endsWith(": finished here\n"));
  assert.ok(!existsSync(path.join(config, "session-ids", "handoff.json")), "nothing recorded");
});

test("sweep files Complete notes and lists old ones, leaving them open", () => {
  const repo = repoWithNotes();
  const put = (name, next) =>
    writeFiles(repo, { [`.handoff/${name}`]: ["# Handoff: x", "header", "", "## Goal", "g", "", "## Next", next, ""].join("\n") });
  put("2026-11-08-0900-finished.md", "Complete");
  put("2026-11-01-0900-old-open.md", "1. Still to do");
  put("2026-11-08-0800-fresh-open.md", "1. Still to do");
  const r = sweep({ cwd: repo, now: new Date(2026, 10, 8, 12, 0) });
  assert.deepEqual(r.filed, ["2026-11-08-0900-finished.md"]);
  assert.deepEqual(r.stale, ["2026-11-01-0900-old-open.md"]);
  assert.deepEqual(openNotes(storeDir(repo)).map((n) => n.name), ["2026-11-08-0800-fresh-open.md", "2026-11-01-0900-old-open.md"]);
  assert.match(readFileSync(path.join(repo, ".handoff", "done", "2026-11-08-0900-finished.md"), "utf8"), /swept, nothing outstanding/);
});
