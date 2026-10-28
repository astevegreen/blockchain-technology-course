// The sprint queue (tools/sprint/queue.mjs) on synthetic issues. The cases come from YODC's October sprint,
// where the same rules ran: each test names the failure it stops happening again.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  bodyRefs,
  digestPlan,
  hasWork,
  heldRetry,
  laneQueue,
  matchesId,
  nextJob,
  normalizeIssues,
  ownerReply,
  parseSprintDoc,
  planMove,
  recordStarted,
  run,
  sessionTitles,
  sessionTriggers,
  statusBlock,
} from "./rules.mjs";

const SPRINT_MD = `# Sprint

**Window (UTC):** \`20261102T0800\` to \`20261106T1800\`

Sprint log: #40 "Sprint log". Questions: #41 "Decisions". Tag before the sprint: \`pre-sprint-2026-11-02\`.

- **Environment:** \`env_01AbC\`: the computer sessions start on.

| Lane | Label | Worktree |
| --- | --- | --- |
| \`wk\` | \`lane:wk\` | \`C:/Antigravity/bc-lane-wk\` |
| \`labs\` | \`lane:labs\` | \`C:/Antigravity/bc-lane-labs\` |

## Backlog

### wk

- **L1** 03-BF mempool lesson.
- **L2** 03-FO tracing lesson,
  continued on a second line. Waits for: L1.
- **L3** 04-BF. Waits for: none.

### labs

- **X1** Memo lab. Waits for: L2–L3 and #12.

## Machinery

- **Z9** not a backlog item.
`;
const doc = parseSprintDoc(SPRINT_MD);

const issue = (number, title, labels, { body = "", comments = [], state = "OPEN", closedAt = null } = {}) => ({
  number,
  title,
  body,
  state,
  createdAt: "2026-11-01T00:00:00Z",
  closedAt,
  labels: labels.map((name) => ({ name })),
  comments: comments.map(([login, createdAt, text]) => ({ author: { login }, createdAt, body: text })),
});
const world = (issues, over = {}) => ({
  doc,
  issues: normalizeIssues(issues),
  now: new Date("2026-11-03T12:00:00Z"),
  freeMb: 20_000,
  branchAhead: () => 0,
  mainHead: { sha: "abcdef0123456789", subject: "Add 03-BF" },
  lastLabTests: null,
  ...over,
});
const throwsWith = (f, pattern) => assert.throws(f, (e) => pattern.test(e.message));

// --- docs/sprint.md ------------------------------------------------------------------------------------------------

test("reads the window, lanes, sprint log, tag and each lane's backlog", () => {
  assert.equal(doc.window.start.toISOString(), "2026-11-02T08:00:00.000Z");
  assert.equal(doc.window.end.toISOString(), "2026-11-06T18:00:00.000Z");
  assert.deepEqual(doc.lanes, [
    { name: "wk", worktree: "C:/Antigravity/bc-lane-wk" },
    { name: "labs", worktree: "C:/Antigravity/bc-lane-labs" },
  ]);
  assert.equal(doc.logIssue, 40);
  assert.equal(doc.decisionsIssue, 41);
  assert.equal(doc.preSprintTag, "pre-sprint-2026-11-02");
  assert.deepEqual(doc.backlog.wk.map((i) => i.id), ["L1", "L2", "L3"]);
  assert.deepEqual(Object.keys(doc.backlog), ["wk", "labs"], "the backlog ends at the next ## heading");
});

test("reads each item's Waits for, ranges and continuation lines included; none names nothing", () => {
  const [l1, l2, l3] = doc.backlog.wk;
  assert.deepEqual(l1.waits, []);
  assert.deepEqual(l2.waits, [{ id: "L1" }]);
  assert.deepEqual(l3.waits, []);
  assert.deepEqual(doc.backlog.labs[0].waits, [{ id: "L2" }, { id: "L3" }, { issue: 12 }]);
});

test("reads this checkout's docs/sprint.md, the template the sprint fills in", () => {
  const current = parseSprintDoc(readFileSync(path.join(import.meta.dirname, "../../docs/sprint.md"), "utf8"));
  assert.ok(current.lanes.length > 0);
  assert.ok(current.lanes.some((l) => l.name === "labs" && l.worktree === "C:/Antigravity/bc-lane-labs"), "the labs lane alone runs lab tests");
  assert.ok(sessionTitles(current).includes("Course integrate"));
  for (const lane of current.lanes) assert.ok(current.backlog[lane.name], `the backlog has a ### ${lane.name} list`);
});

test("fails, saying what is missing, rather than guess; a missing window is no window yet", () => {
  assert.equal(parseSprintDoc(SPRINT_MD.replace("**Window (UTC):**", "Window:")).window, null, "/sprint-start opens it");
  throwsWith(() => parseSprintDoc(SPRINT_MD.replace('#40 "Sprint log"', "the log")), /sprint log issue/);
  throwsWith(() => parseSprintDoc(SPRINT_MD.replace("## Backlog", "## Later")), /## Backlog/);
});

// --- what an issue waits for ---------------------------------------------------------------------------------------

test("reads every Depends on and Waits for form, up to the first full stop", () => {
  assert.deepEqual(bodyRefs("**Depends on**: #27 and #48 (the lesson it extends)."), [27, 48]);
  assert.deepEqual(bodyRefs("## Depends on\n\nL1a (issue #58)."), [58]);
  assert.deepEqual(bodyRefs("Depends on: #28. Independent of #35, which can land in any order."), [28]);
  assert.deepEqual(bodyRefs("**Waits for**: #57 and #64 to land."), [57, 64]);
});

test('reads "none" as nothing, whatever follows it', () => {
  assert.deepEqual(bodyRefs("Depends on: none (see #46)."), []);
  assert.deepEqual(bodyRefs("Depends on: none. If #30 lands first, rebase."), []);
});

test("a split counts for its item; a longer number does not", () => {
  const [a, b] = normalizeIssues([issue(1, "[task] L1a: first half", []), issue(2, "[task] L10: other", [])]);
  assert.equal(matchesId(a, "L1"), true);
  assert.equal(matchesId(b, "L1"), false);
  assert.equal(matchesId(b, "L10"), true);
});

test("an issue is not started while the issue it depends on is open (YODC T4b, 21 Oct)", () => {
  const w = world([
    issue(48, "[task] L1: mempool", ["lane:wk", "to-integrate"]),
    issue(49, "[task] L2: tracing", ["lane:wk", "sprint-ready"], { body: "Depends on: #48." }),
  ]);
  const r = hasWork(w, "Course lane: wk");
  assert.equal(r.start, false);
  assert.match(r.reason, /#49 L2 waits for L1, #48 L1/);
  assert.equal(nextJob(w, "wk"), null);
  throwsWith(() => planMove(w, 49, "in-progress"), /#49 waits for/);
  const landed = world([
    issue(48, "[task] L1: mempool", ["lane:wk"], { state: "CLOSED", closedAt: "2026-11-03T00:00:00Z" }),
    issue(49, "[task] L2: tracing", ["lane:wk", "sprint-ready"], { body: "Depends on: #48." }),
  ]);
  assert.deepEqual(nextJob(landed, "wk"), { mode: "build", issue: 49, concerns: null, reason: "#49 L2 is ready" });
});

test("a backlog wait on an ID with no issue yet is not over", () => {
  const w = world([issue(50, "[task] X1: memo lab", ["lane:labs", "sprint-ready"])]);
  assert.match(laneQueue(w, "labs").waiting[0], /#50 X1 waits for L2, L3, #12 \(no such issue\)/);
});

// --- held and blocked ------------------------------------------------------------------------------------------------

test("held with the lane's own comment newest waits for the owner, and says so (YODC T5a, 22 Oct)", () => {
  const w = world([
    issue(58, "[task] L1: mempool", ["lane:wk", "held"], { comments: [["greenbeanbot", "2026-11-03T03:00:00Z", "Lane: held. The render failed twice."]] }),
  ]);
  assert.equal(hasWork(w, "Course lane: wk").start, false);
  assert.deepEqual(statusBlock(w).needsYou, ['#58 [held] L1: waits for the owner; newest comment: "Lane: held. The render failed twice."']);
});

test("an answer relayed by the bot account does not count as the owner's (YODC U3, 21 Oct)", () => {
  const w = world([
    issue(37, "[task] L3: 04-BF", ["lane:wk", "blocked"], {
      comments: [
        ["astevegreen", "2026-11-03T01:00:00Z", "Which case study?"],
        ["greenbeanbot", "2026-11-03T02:00:00Z", "Relayed: the owner says use Colonial."],
      ],
    }),
  ]);
  assert.ok(laneQueue(w, "wk").waiting.includes("#37 L3 is blocked: no owner reply yet"));
  assert.ok(statusBlock(w).needsYou.includes("#37 [blocked] L3: waiting for your answer"));
});

test("held work is retried after an owner reply, with that reply as the concerns", () => {
  const w = world([
    issue(57, "[task] L1: mempool", ["lane:wk", "held"], {
      comments: [["greenbeanbot", "2026-11-03T01:00:00Z", "Lane: held. Which source?"], ["astevegreen", "2026-11-03T02:00:00Z", "Use the BIP."]],
    }),
  ]);
  assert.deepEqual(nextJob(w, "wk"), { mode: "fix", issue: 57, concerns: "Use the BIP.", reason: "#57 L1 is held and the owner replied" });
});

test("held work is retried when the integrator sent it back, and a stranger's comment changes nothing", () => {
  const [i] = normalizeIssues([
    issue(5, "[task] L1: x", ["lane:wk", "held"], {
      comments: [["greenbeanbot", "2026-11-03T10:00:00Z", "Integrator: conflicts with main"], ["someone", "2026-11-03T11:00:00Z", "me too"]],
    }),
  ]);
  assert.equal(heldRetry(i, 8000).retry, true);
  assert.equal(heldRetry(i, 8000).why, "the integrator sent it back");
});

test("a Gemini audit posted after the owner's answer never hides it", () => {
  const [i] = normalizeIssues([
    issue(5, "[task] L1: x", ["lane:wk", "blocked"], {
      comments: [
        ["greenbeanbot", "2026-11-03T10:00:00Z", "Plan: which source?"],
        ["astevegreen", "2026-11-03T11:00:00Z", "Use the BIP."],
        ["greenbeanbot", "2026-11-03T12:00:00Z", "<!-- gemini-audit -->\n**Gemini audit: spec**\n\nNo findings."],
      ],
    }),
  ]);
  assert.equal(ownerReply(i)?.body, "Use the BIP.");
  assert.deepEqual(heldRetry({ ...i, labels: ["lane:wk", "held"] }, 8000), { retry: true, mode: "fix", why: "the owner replied", concerns: "Use the BIP." });
});

test("a machine failure is retried only over the memory floor", () => {
  const [i] = normalizeIssues([
    issue(5, "[task] L1: x", ["lane:wk", "held"], { comments: [["greenbeanbot", "2026-11-03T10:00:00Z", "Implementer: machine. Quarto ran out of memory"]] }),
  ]);
  assert.equal(heldRetry(i, 8000).retry, true);
  assert.equal(heldRetry(i, 3000).retry, false);
});

// #10 X2, 25 Oct: "Implementer: machine" (a Docker Hub pull timed out) was followed a second later by the
// implementer's note on a spec departure, and the queue, reading only the newest comment, waited for the owner.
const masked = [
  ["greenbeanbot", "2026-10-25T21:15:07Z", "Lane: unblocked by the owner's answer; the implementer reads it as part of the spec."],
  ["greenbeanbot", "2026-10-25T21:41:28Z", "Implementer: machine\n\nThe exercises lab tests could not pull python:3.11-slim."],
  ["greenbeanbot", "2026-10-25T21:41:29Z", "Implementer: one departure from the spec, for the reviewer."],
];

test("a machine failure retries by itself even when a later note follows it (#10, 25 Oct)", () => {
  const [i] = normalizeIssues([issue(10, "[task] X2: insider", ["lane:labs", "held"], { comments: masked })]);
  const r = heldRetry(i, 8000);
  assert.equal(r.retry, true);
  assert.equal(r.mode, "fix");
  assert.match(r.why, /the machine failed it/);
  assert.match(r.concerns, /^Implementer: machine The exercises lab tests could not pull/);
});

test("work the machine failed waits for memory, never for the owner, and is not in Needs you", () => {
  const w = world([issue(10, "[task] X2: insider", ["lane:labs", "held"], { comments: masked })], { freeMb: 3000 });
  const r = heldRetry(w.issues[0], 3000);
  assert.deepEqual([r.retry, r.owner], [false, false]);
  assert.match(laneQueue(w, "labs").waiting[0], /#10 X2 is held: the machine failed it and 3000 MB free/);
  assert.deepEqual(statusBlock(w).needsYou, []);
});

test("a machine failure from an attempt already retried does not decide the next hold", () => {
  const [i] = normalizeIssues([
    issue(10, "[task] X2: insider", ["lane:labs", "held"], {
      comments: [
        ...masked,
        ["greenbeanbot", "2026-10-26T00:10:00Z", "Lane: retrying, since the machine failed it and 9000 MB is free now."],
        ["greenbeanbot", "2026-10-26T01:00:00Z", "Lane: held. Blockers left after the second review: 1. [blocker] x.qmd:4 no source"],
      ],
    }),
  ]);
  const r = heldRetry(i, 8000);
  assert.deepEqual([r.retry, r.owner], [false, true]);
  assert.match(r.why, /^waits for the owner/);
});

test("a hold with only minor concerns, from before the 28 Oct policy, is reviewed again and handed over (#7, #12)", () => {
  const minor = issue(12, "[task] X4a: explorer", ["lane:labs", "held"], {
    comments: [["greenbeanbot", "2026-10-25T22:04:37Z", "Lane: held. Second review left one minor concern: no agent/explorer/ browser playbook."]],
  });
  const ahead = world([minor], { branchAhead: () => 2 });
  assert.deepEqual(nextJob(ahead, "labs"), {
    mode: "resume", issue: 12, concerns: "Lane: held. Second review left one minor concern: no agent/explorer/ browser playbook.",
    reason: "#12 X4a is held and its concerns are all minor, which ship with a note",
  });
  assert.equal(nextJob(world([minor]), "labs").mode, "fix", "with no branch, it is built again");
  const blocker = issue(12, "[task] X4a: explorer", ["lane:labs", "held"], {
    comments: [["greenbeanbot", "2026-10-25T22:04:37Z", "Lane: held. 1. [blocker] a.md:1 leaks an answer 2. [minor] b.md:2 wording"]],
  });
  assert.equal(nextJob(world([blocker]), "labs"), null, "a blocker holds");
  assert.deepEqual(statusBlock(world([blocker])).needsYou.length, 1);
});

test("taking up held work starts a new attempt with a comment that says why", () => {
  const w = world([issue(10, "[task] X2: insider", ["lane:labs", "held"], { comments: masked })]);
  const m = planMove(w, 10, "in-progress");
  assert.equal(m.comment, "Lane: retrying, since the machine failed it and 20000 MB is free now.");
  assert.deepEqual([m.add, m.remove], [["in-progress"], ["held"]]);
});

// --- next ------------------------------------------------------------------------------------------------------------

test("takes ready issues in backlog order, not issue number, and IDs not in the backlog last", () => {
  const w = world([
    issue(10, "[task] L9: extra", ["lane:wk", "sprint-ready"]),
    issue(11, "[task] L3: x", ["lane:wk", "sprint-ready"]),
    issue(12, "[task] L1: y", ["lane:wk", "sprint-ready"]),
    issue(13, "[task] L1b: y, part 2", ["lane:wk", "sprint-ready"]),
  ]);
  assert.equal(nextJob(w, "wk").issue, 12);
  assert.equal(nextJob(w, "wk", [12]).issue, 13);
  assert.equal(nextJob(w, "wk", [12, 13]).issue, 11);
  assert.equal(nextJob(w, "wk", [12, 13, 11]).issue, 10);
});

test("picks up a stopped session's work first: review it when its branch has commits, else build it again", () => {
  const issues = [issue(11, "[task] L1: x", ["lane:wk", "sprint-ready"]), issue(12, "[task] L3: y", ["lane:wk", "in-progress"])];
  assert.equal(nextJob(world(issues, { branchAhead: () => 2 }), "wk").mode, "resume");
  assert.deepEqual(nextJob(world(issues), "wk"), {
    mode: "build",
    issue: 12,
    concerns: null,
    reason: "#12 L3 was in progress when its session stopped, with no commits on sprint/12",
  });
});

test("builds a blocked issue the owner answered", () => {
  const w = world([
    issue(11, "[task] L1: x", ["lane:wk", "blocked"], {
      comments: [["greenbeanbot", "2026-11-03T00:10:00Z", "Implementer: which case?"], ["astevegreen", "2026-11-03T00:20:00Z", "(a)"]],
    }),
  ]);
  assert.deepEqual(nextJob(w, "wk"), { mode: "build", issue: 11, concerns: null, reason: "#11 L1: the owner answered its question" });
});

test("an unknown lane is refused, naming the lanes", () => {
  throwsWith(() => nextJob(world([]), "art"), /unknown lane "art"/);
});

// --- has-work --------------------------------------------------------------------------------------------------------

test("covers every session title the supervisor keeps, and refuses others", () => {
  assert.deepEqual(sessionTitles(doc), ["Course lane: wk", "Course lane: labs", "Course plan: wk", "Course plan: labs", "Course integrate"]);
  throwsWith(() => hasWork(world([]), "YODC lane: wk"), /unknown session title/);
});

test("starts nothing under the memory floor", () => {
  const w = world([issue(1, "[task] L1: x", ["lane:wk", "to-integrate"])], { freeMb: 3000 });
  for (const title of sessionTitles(doc)) {
    assert.equal(hasWork(w, title).start, false, title);
    assert.equal(hasWork(w, title).reason, "memory: 3000 MB free, under the 4096 MB floor");
  }
});

test("integrate has work while an issue is labeled to-integrate", () => {
  const w = world([issue(64, "[task] L3: x", ["lane:wk", "to-integrate"]), issue(57, "[task] L1: y", ["lane:wk", "to-integrate"])]);
  assert.deepEqual(hasWork(w, "Course integrate"), { start: true, reason: "to integrate: #57, #64", issues: [57, 64] });
  assert.equal(hasWork(world([]), "Course integrate").start, false);
});

test("plan has work while an item has no issue and the lane has under 3 ready", () => {
  const w = world([issue(1, "[task] L1a: x", ["lane:wk", "to-integrate"])]);
  assert.deepEqual(hasWork(w, "Course plan: wk"), {
    start: true,
    reason: "0 open sprint-ready, under 3; not yet filed: L2, L3",
    ready: 0,
    todo: ["L2", "L3"],
  });
  const filed = world(["L1", "L2", "L3"].map((id, k) => issue(k + 1, `[task] ${id}: x`, ["lane:wk", "sprint-ready"])));
  assert.equal(hasWork(filed, "Course plan: wk").start, false);
  assert.equal(hasWork(filed, "Course plan: wk").reason, "every backlog item has an issue");
});

// --- move ------------------------------------------------------------------------------------------------------------

const one = (labels, over = {}) => world([issue(7, "[task] L1: x", ["lane:wk", ...labels])], over);

test("claims a ready issue with no comment", () => {
  assert.deepEqual(planMove(one(["sprint-ready"]), 7, "in-progress"), {
    issue: 7,
    from: "sprint-ready",
    to: "in-progress",
    comment: null,
    add: ["in-progress"],
    remove: ["sprint-ready"],
  });
});

test("re-queues a stopped session's claim with the standard comment", () => {
  assert.equal(planMove(one(["in-progress"]), 7, "in-progress").comment, "Lane: re-queued, the previous lane session stopped.");
});

test("hands over to the integrator with the standard comment, only with commits and a note", () => {
  const ready = planMove(one(["in-progress"], { branchAhead: () => 1 }), 7, "to-integrate", "WHAT CHANGED: a\\nSTUDENT-VISIBLE: b");
  assert.equal(ready.comment, "Lane: ready to integrate, branch sprint/7.\nWHAT CHANGED: a\nSTUDENT-VISIBLE: b");
  throwsWith(() => planMove(one(["in-progress"]), 7, "to-integrate", "x"), /no commits ahead/);
  throwsWith(() => planMove(one(["in-progress"], { branchAhead: () => 1 }), 7, "to-integrate"), /needs a note/);
});

test("refuses what the rules do not allow, saying what to do instead", () => {
  throwsWith(() => planMove(one(["held"]), 7, "in-progress"), /held and/);
  throwsWith(() => planMove(one(["to-integrate"]), 7, "held"), /integrator's/);
  throwsWith(() => planMove(one(["sprint-ready"]), 7, "held"), /only work in progress/);
  throwsWith(() => planMove(one(["held", "blocked"]), 7, "in-progress"), /state labels held and blocked/);
  throwsWith(() => planMove(one(["blocked"]), 7, "in-progress"), /owner has not replied/);
  throwsWith(() => planMove(one(["in-progress"]), 7, "sprint-ready"), /cannot move an issue to "sprint-ready"/);
  throwsWith(() => planMove(one(["in-progress"]), 8, "held"), /no issue #8/);
});

test("a second move to the same state changes nothing", () => {
  assert.deepEqual(planMove(one(["held"]), 7, "held"), { issue: 7, from: "held", to: "held", comment: null, add: [], remove: [] });
});

// --- status ----------------------------------------------------------------------------------------------------------

test("the status block counts each lane, names main and the last Lab Tests run, and lists what needs the owner", () => {
  const w = world(
    [
      issue(7, "[task] L1: x", ["lane:wk", "in-progress"]),
      issue(8, "[task] L2: y", ["lane:wk"], { state: "CLOSED", closedAt: "2026-11-02T09:00:00Z" }),
      issue(9, "[task] L3: z", ["lane:wk"], { state: "CLOSED", closedAt: "2026-10-30T09:00:00Z" }),
    ],
    { lastLabTests: { headSha: "1234567890ab", status: "completed", conclusion: "success", url: "https://github.com/x/runs/1" } },
  );
  const s = statusBlock(w, { also: ["stuck: Course lane: labs"] });
  assert.match(s.body, /^Status at 2026-11-03 12:00Z\./);
  assert.ok(s.body.includes("- wk: 0 sprint-ready, 1 in-progress, 0 to-integrate, 0 held, 0 blocked; closed: #8 L2"), "closed before the window opened is left out");
  assert.ok(s.body.includes('**Main:** abcdef01 "Add 03-BF"'));
  assert.ok(s.body.includes("**Lab Tests:** last run success at 12345678 https://github.com/x/runs/1"));
  assert.ok(s.body.endsWith("**Needs you**\n- stuck: Course lane: labs"));
  assert.ok(statusBlock(world([])).body.includes("**Lab Tests:** no run found\n"));
  assert.ok(statusBlock(world([])).body.endsWith("- nothing"));
});

// 25-26 Oct: an `also` line worded a little differently each run counted as new, so the owner was pinged hourly.
test("only an issue newly needing the owner is new, and only new held work is a ping", () => {
  const held = issue(8, "[task] L2: y", ["lane:wk", "held"], { comments: [["greenbeanbot", "2026-11-03T01:00:00Z", "Lane: held. 1. [blocker] x"]] });
  const blocked = issue(9, "[task] L3: z", ["lane:wk", "blocked"]);
  const first = statusBlock(world([held, blocked]), { also: ["wake not armed at 11:42Z"] });
  assert.deepEqual(first.new, ['#8 [held] L2: waits for the owner; newest comment: "Lane: held. 1. [blocker] x"', "#9 [blocked] L3: waiting for your answer"]);
  assert.deepEqual(first.ping, [first.new[0]]);
  const again = statusBlock(world([held, blocked]), { also: ["wake not armed at 12:42Z"], oldBody: first.body });
  assert.deepEqual([again.new, again.ping], [[], []]);
});

// --- the Decisions digest ----------------------------------------------------------------------------------------------

const question = (n, at, text = "Plan: which source? a (recommended) or b") =>
  issue(n, `[task] L${n}: x`, ["lane:wk", "blocked"], { comments: [["greenbeanbot", at, text]] });
const decisions = (comments = []) => issue(41, "Decisions", [], { comments });

test("the digest posts once a day, only when a question is new since the last one", () => {
  const first = digestPlan(world([decisions(), question(3, "2026-11-03T01:00:00Z")]));
  assert.equal(first.post, true);
  assert.deepEqual([first.open, first.new], [[3], [3]]);
  assert.match(first.comment, /^@astevegreen Decisions digest, 2026-11-03 12:00Z: 1 content decision wait/);
  assert.ok(first.body.includes("- #3 L3 (new): Plan: which source? a (recommended) or b"));

  const posted = decisions([["greenbeanbot", "2026-11-03T06:00:00Z", first.comment]]);
  const same = digestPlan(world([posted, question(3, "2026-11-03T01:00:00Z")]));
  assert.deepEqual([same.post, same.reason], [false, "no question is new since the last digest"]);
  const soon = digestPlan(world([posted, question(3, "2026-11-03T01:00:00Z"), question(4, "2026-11-03T07:00:00Z")]));
  assert.equal(soon.post, false);
  assert.match(soon.reason, /under a day ago/);
  const nextDay = digestPlan(world([posted, question(3, "2026-11-03T01:00:00Z"), question(4, "2026-11-03T07:00:00Z")], {
    now: new Date("2026-11-04T06:30:00Z"),
  }));
  assert.deepEqual([nextDay.post, nextDay.new], [true, [4]]);
});

test("the digest leaves out answered questions, and a new question on a listed issue counts as new", () => {
  const answered = issue(5, "[task] L5: x", ["lane:wk", "blocked"], {
    comments: [["greenbeanbot", "2026-11-03T01:00:00Z", "Plan: which?"], ["astevegreen", "2026-11-03T02:00:00Z", "a"]],
  });
  const posted = decisions([["greenbeanbot", "2026-11-02T06:00:00Z", "@astevegreen Decisions digest\n- #3 L3: old question"]]);
  const d = digestPlan(world([posted, answered, question(3, "2026-11-03T01:00:00Z", "Plan: a second question")]));
  assert.deepEqual([d.post, d.open, d.new], [true, [3], [3]]);
  assert.equal(digestPlan(world([decisions(), answered])).reason, "no question is open");
});

test("digest --write rewrites the Decisions body and comments once; without a Decisions issue it refuses", () => {
  const { io, writes } = fakeIo([decisions(), question(3, "2026-11-03T01:00:00Z")]);
  const out = JSON.parse(run(["digest", "--write"], io).line);
  assert.equal(out.written, true);
  assert.deepEqual(writes().map((c) => c.args), [["issue", "edit", "41", "--body-file", "-"], ["issue", "comment", "41", "--body-file", "-"]]);
  assert.match(writes()[1].input, /^@astevegreen Decisions digest/);
  const none = fakeIo([decisions()], { sprintDoc: () => SPRINT_MD.replace('#41 "Decisions"', "none") });
  assert.equal(run(["digest"], none.io).code, 2);
});

// --- the command line ------------------------------------------------------------------------------------------------

function fakeIo(issues, over = {}) {
  const calls = [];
  const io = {
    sprintDoc: () => SPRINT_MD,
    gh: (args, input) => {
      calls.push({ args, input });
      if (args[0] === "issue" && args[1] === "list") return JSON.stringify(issues);
      if (args[0] === "run") return JSON.stringify([{ headSha: "be34383f0", status: "completed", conclusion: "success", url: "https://x/1" }]);
      return "";
    },
    branchAhead: () => 1,
    mainHead: () => ({ sha: "be34383f0aa", subject: "Add 03-FO" }),
    freeMb: () => 9000,
    now: () => new Date("2026-11-03T02:00:00Z"),
    ledger: [],
    readTriggers: () => io.ledger,
    writeTriggers: (records) => { io.ledger = records; },
    windowFile: null,
    readWindow: () => io.windowFile,
    writeWindow: (w) => { io.windowFile = w; },
    ...over,
  };
  return { io, writes: () => calls.filter((c) => c.args[1] !== "list" && c.args[0] !== "run") };
}
const cli = [issue(7, "[task] L1: x", ["lane:wk", "in-progress"]), { ...issue(40, "Sprint log", []), body: "**Needs you**\n- #8 [held] L2: old" }];

test("prints one line of JSON per command", () => {
  const out = run(["next", "wk"], fakeIo(cli).io);
  assert.equal(out.code, 0);
  assert.match(out.line, /"mode":"resume","issue":7/);
  assert.deepEqual(run(["next", "wk", "--taken", "7"], fakeIo(cli).io), { code: 0, line: "null" });
  assert.equal(JSON.parse(run(["has-work", "Course integrate"], fakeIo(cli).io).line).start, false);
});

test("move comments first, then sets the labels", () => {
  const { io, writes } = fakeIo(cli);
  assert.equal(run(["move", "7", "to-integrate", "--note", "WHAT CHANGED: a"], io).code, 0);
  assert.deepEqual(writes().map((c) => c.args), [
    ["issue", "comment", "7", "--body", "Lane: ready to integrate, branch sprint/7.\nWHAT CHANGED: a"],
    ["issue", "edit", "7", "--add-label", "to-integrate", "--remove-label", "in-progress"],
  ]);
});

test("a refused move writes nothing and exits 2 with an error and a do line", () => {
  const { io, writes } = fakeIo(cli);
  const out = run(["move", "7", "sprint-ready"], io);
  assert.equal(out.code, 2);
  assert.match(JSON.parse(out.line).do, /Move it to one of/);
  assert.deepEqual(writes(), []);
});

test("status writes the block to the sprint log and lists only the new Needs you items", () => {
  const { io, writes } = fakeIo([...cli, issue(9, "[task] L3: y", ["lane:wk", "blocked"])]);
  const out = JSON.parse(run(["status", "--write", "--also", "stuck: Course lane: labs"], io).line);
  assert.deepEqual(out.new, ["#9 [blocked] L3: waiting for your answer"], "a stuck session is in the block, never new");
  assert.deepEqual(out.ping, [], "a new question waits for the daily digest");
  assert.deepEqual(writes(), [{ args: ["issue", "edit", "40", "--body-file", "-"], input: out.body }]);
  assert.ok(out.body.includes("- wk: 0 sprint-ready, 1 in-progress, 0 to-integrate, 0 held, 1 blocked; closed: none"));
  assert.ok(out.body.includes("**Lab Tests:** last run success at be34383f https://x/1"));
});

test("status --write is refused while docs/sprint.md names no log issue yet", () => {
  const { io, writes } = fakeIo(cli, { sprintDoc: () => SPRINT_MD.replace("#40", "#0") });
  const out = run(["status", "--write"], io);
  assert.equal(out.code, 2);
  assert.match(JSON.parse(out.line).do, /setup day/);
  assert.deepEqual(writes(), []);
  assert.equal(run(["status"], io).code, 0, "reading the status still works");
});

test("a failing gh is an error that says stop", () => {
  const out = run(["next", "wk"], fakeIo(cli, { gh: () => { throw new Error("HTTP 502"); } }).io);
  assert.equal(out.code, 1);
  assert.match(JSON.parse(out.line).do, /^Stop and report/);
});

test("env prints the environment from the doc, and refuses while it is the placeholder", () => {
  const { io, writes } = fakeIo(cli);
  assert.deepEqual(run(["env"], io), { code: 0, line: '{"environment_id":"env_01AbC"}' });
  assert.deepEqual(writes(), []);
  const blank = run(["env"], fakeIo(cli, { sprintDoc: () => SPRINT_MD.replace("env_01AbC", "env_…") }).io);
  assert.equal(blank.code, 2);
  assert.match(JSON.parse(blank.line).do, /^Start nothing/);
});

// RemoteTrigger `list` returns only the account's newest 20 triggers, and three projects' sprints share the
// account (24 Oct review), so the supervisor finds its sessions in this ledger instead.
test("started records each trigger, and sessions reads back the last one per title since the window opened", () => {
  const { io, writes } = fakeIo(cli);
  io.ledger = [{ title: "Course lane: wk", id: "trig_01Old", at: "2026-11-01T09:00:00Z" }];
  const out = run(["started", "Course lane: wk", "trig_01A"], io);
  assert.equal(out.code, 0);
  assert.deepEqual(JSON.parse(out.line), { recorded: { title: "Course lane: wk", id: "trig_01A", at: "2026-11-03T02:00:00.000Z" } });
  io.now = () => new Date("2026-11-03T03:00:00Z");
  run(["started", "Course integrate", "trig_01I"], io);
  run(["started", "Course lane: wk", "trig_01B"], io);
  assert.deepEqual(JSON.parse(run(["sessions"], io).line), {
    "Course lane: wk": "trig_01B",
    "Course lane: labs": null,
    "Course plan: wk": null,
    "Course plan: labs": null,
    "Course integrate": "trig_01I",
  });
  // The record from before the window is left out; --all lists the rest, newest first.
  assert.deepEqual(JSON.parse(run(["sessions", "--all"], io).line).map((r) => r.id), ["trig_01B", "trig_01I", "trig_01A"]);
  assert.deepEqual(writes(), []);
});

test("started refuses an unknown title, a malformed id and a closed window, and records nothing", () => {
  for (const [args, now, pattern] of [
    [["Course lane: night", "trig_01A"], "2026-11-03T02:00:00Z", /unknown session title/],
    [["Course lane: wk", "01A"], "2026-11-03T02:00:00Z", /not a trigger id/],
    [["Course lane: wk", "trig_01A; x"], "2026-11-03T02:00:00Z", /not a trigger id/],
    [["Course lane: wk", "trig_01A"], "2026-11-02T07:59:00Z", /no window is open/],
    [["Course lane: wk", "trig_01A"], "2026-11-06T18:00:00Z", /no window is open/],
  ]) {
    const { io } = fakeIo(cli, { now: () => new Date(now) });
    const out = run(["started", ...args], io);
    assert.equal(out.code, 2, args.join(" "));
    assert.match(JSON.parse(out.line).error, pattern);
    assert.deepEqual(io.ledger, []);
  }
});

test("the ledger keeps its newest 500 records and skips any it cannot read", () => {
  const old = Array.from({ length: 500 }, (_, k) => ({ title: "Course lane: wk", id: `trig_${k}`, at: "2026-11-02T09:00:00Z" }));
  const records = recordStarted(doc, old, "Course lane: wk", "trig_new", new Date("2026-11-03T02:00:00Z"));
  assert.equal(records.length, 500);
  assert.equal(records[0].id, "trig_1");
  assert.equal(records.at(-1).id, "trig_new");
  const messy = [null, { title: "Course lane: wk" }, { title: "Other: x", id: "trig_9", at: "2026-11-03T00:00:00Z" }, ...records];
  assert.equal(sessionTriggers(doc, messy)["Course lane: wk"], "trig_new");
});

test("an unknown command reads nothing and shows the usage", () => {
  let read = false;
  const { io } = fakeIo(cli, { sprintDoc: () => { read = true; return SPRINT_MD; } });
  const out = run(["nxt", "wk"], io);
  assert.equal(out.code, 2);
  assert.match(JSON.parse(out.line).do, /^Usage/);
  assert.equal(read, false);
});

// --- the window /sprint-start opens ----------------------------------------------------------------------------------

// Terminal Dusk's cue (24 Oct): the owner says when, and the window lives in this computer's git folder.
const NO_WINDOW = SPRINT_MD.replace(/\*\*Window \(UTC\):\*\*[^\n]*\n/, "");
const cue = (now, over = {}) => fakeIo(cli, { sprintDoc: () => NO_WINDOW, now: () => new Date(now), ...over }).io;
const json = (out) => JSON.parse(out.line);

test("window start opens the window on the minute, for 38 hours unless told; a dry run writes nothing", () => {
  const io = cue("2026-10-28T23:59:42.123Z");
  assert.deepEqual(json(run(["window"], io)), { state: "none", lanes: doc.lanes, log: 40, supervisor: null, archiver: null, wake: null, stoppedBy: null });
  const dry = run(["window", "start", "12", "--dry-run"], io);
  assert.equal(dry.code, 0);
  assert.deepEqual(json(dry), {
    state: "open", start: "2026-10-28T23:59Z", end: "2026-10-29T11:59Z", newYork: "Wed 28 Oct 19:59 to Thu 29 Oct 07:59",
    lanes: doc.lanes, log: 40, supervisor: null, archiver: null, wake: null, stoppedBy: null, dryRun: true,
  });
  assert.equal(io.windowFile, null);
  assert.equal(run(["window", "start"], io).code, 0);
  assert.deepEqual(io.windowFile, { start: "2026-10-28T23:59:00.000Z", end: "2026-10-30T13:59:00.000Z", environment: null, supervisor: null, archiver: null, wake: null, stoppedBy: null });
  assert.equal(json(run(["window"], io)).newYork, "Wed 28 Oct 19:59 to Fri 30 Oct 09:59");
  const again = run(["window", "start", "4"], io);
  assert.equal(again.code, 2);
  assert.match(json(again).error, /already open, until 2026-10-30T13:59Z/);
  assert.equal(run(["started", "Course lane: wk", "trig_01A"], io).code, 0, "the supervisor may start sessions in it");
});

test("window start takes a whole number of hours from 1 to 96, and a broken window file stops every command", () => {
  for (const hours of ["0", "97", "1.5", "x"]) {
    const io = cue("2026-10-28T20:00:00Z");
    const out = run(["window", "start", hours], io);
    assert.equal(out.code, 2, hours);
    assert.equal(io.windowFile, null, hours);
  }
  for (const file of [{ start: "x", end: "2026-10-30T13:59:00.000Z" }, { end: "2026-10-30T13:59:00.000Z" }]) {
    const io = cue("2026-10-28T20:00:00Z", { windowFile: file });
    io.windowFile = file;
    for (const args of [["window"], ["sessions"], ["has-work", "Course integrate"]]) {
      const out = run(args, io);
      assert.equal(out.code, 1, args.join(" "));
      assert.match(json(out).error, /sprint-window\.json/);
    }
  }
});

// A fresh Sonnet dry run (25 Oct) read `"log": 0` and still printed DRY-RUN OK, so the queue refuses it itself.
test("window start refuses while docs/sprint.md names no sprint log, dry run or not", () => {
  const io = cue("2026-10-28T20:00:00Z", { sprintDoc: () => NO_WINDOW.replace('#40 "Sprint log"', '#0 "Sprint log"') });
  assert.equal(json(run(["window"], io)).log, 0);
  for (const args of [["window", "start", "--dry-run"], ["window", "start", "4"]]) {
    const out = run(args, io);
    assert.equal(out.code, 2, args.join(" "));
    assert.match(json(out).error, /no sprint log yet \(#0\)/);
  }
  assert.equal(io.windowFile, null);
});

// An environment's id changes whenever `claude rc` restarts, so the cue names the one it found: no push first.
test("window start keeps the environment /sprint-start found, which env then prefers to the doc's line", () => {
  const io = cue("2026-10-28T20:00:00Z");
  for (const bad of ["01Xy", "env_01Xy; rm -rf ."]) {
    const out = run(["window", "start", "--environment", bad], io);
    assert.equal(out.code, 2, bad);
    assert.equal(io.windowFile, null, bad);
  }
  assert.equal(run(["window", "start", "--environment", "env_01Xy", "--dry-run"], io).code, 0);
  assert.equal(io.windowFile, null, "a dry run writes nothing");
  assert.equal(json(run(["env"], io)).environment_id, "env_01AbC", "until a window names one, the doc's line");
  assert.equal(run(["window", "start", "--environment", "env_01Xy"], io).code, 0);
  assert.equal(json(run(["env"], io)).environment_id, "env_01Xy");
  run(["window", "ids", "--supervisor", "trig_01S"], io);
  io.now = () => new Date("2026-10-28T21:00:00Z");
  run(["window", "stop"], io);
  assert.equal(io.windowFile.environment, "env_01Xy", "ids and stop keep it");
  const blank = cue("2026-10-28T20:00:00Z", { sprintDoc: () => NO_WINDOW.replace("env_01AbC", "env_…") });
  assert.match(json(run(["env"], blank)).do, /^Start nothing/);
  run(["window", "start", "--environment", "env_01Xy"], blank);
  assert.equal(json(run(["env"], blank)).environment_id, "env_01Xy", "the placeholder line no longer matters");
});

test("window ids records the scheduled tasks /sprint-start made, and refuses anything but a trigger id", () => {
  const io = cue("2026-10-28T20:00:00Z");
  assert.equal(run(["window", "ids", "--supervisor", "trig_01S"], io).code, 2, "no window is open yet");
  run(["window", "start"], io);
  assert.equal(json(run(["window", "ids", "--supervisor", "trig_01S"], io)).supervisor, "trig_01S");
  const both = json(run(["window", "ids", "--archiver", "trig_01R"], io));
  assert.deepEqual([both.supervisor, both.archiver], ["trig_01S", "trig_01R"]);
  for (const args of [["--supervisor", "trig_01S; rm -rf ."], ["--archiver", "01R"], ["--supervisor", "trig_01S"]]) {
    const out = run(["window", "ids", ...args], io);
    assert.equal(out.code, 2, args.join(" "));
  }
  assert.deepEqual([io.windowFile.supervisor, io.windowFile.archiver], ["trig_01S", "trig_01R"]);
});

test("window stop ends it now; the archiver stays on record until it is switched off, and holds the next start", () => {
  const io = cue("2026-10-28T20:00:00Z");
  run(["window", "start"], io);
  run(["window", "ids", "--supervisor", "trig_01S", "--archiver", "trig_01R"], io);
  assert.match(json(run(["window", "archived"], io)).error, /still open/);
  io.now = () => new Date("2026-10-29T09:30:59Z");
  const stopped = json(run(["window", "stop"], io));
  assert.deepEqual([stopped.state, stopped.end, stopped.archiver], ["after", "2026-10-29T09:30Z", "trig_01R"]);
  assert.equal(stopped.stoppedBy, "sprint-stop", "the supervisor reads the owner's stop as a stop, not a fault");
  assert.equal(json(run(["window"], io)).stoppedBy, "sprint-stop");
  assert.match(json(run(["window", "stop"], io)).do, /^Nothing to stop/);
  assert.match(json(run(["started", "Course lane: wk", "trig_01A"], io)).error, /no window is open/);
  const held = run(["window", "start"], io);
  assert.equal(held.code, 2);
  assert.match(json(held).error, /archiver trig_01R is still on record/);
  assert.equal(json(run(["window", "archived"], io)).archiver, null);
  assert.equal(run(["window", "start", "2"], io).code, 0, "a new window once the archiver is off");
  assert.equal(io.windowFile.supervisor, null, "a new window starts with no scheduled tasks");
  assert.equal(io.windowFile.stoppedBy, null, "and is not stopped");
});

test("a window that simply runs out is not recorded as stopped", () => {
  const io = cue("2026-10-28T20:00:00Z");
  run(["window", "start", "2"], io);
  io.now = () => new Date("2026-10-28T23:00:00Z");
  const out = json(run(["window"], io));
  assert.deepEqual([out.state, out.stoppedBy], ["after", null]);
});

// While a usage limit is on, a scheduled run fails before it starts, so the supervisor moves one standing one-shot of
// itself to the reset + 2 minutes (after-sprint fix 1, 25 Oct).
test("wake arms at the reset + 2 minutes, except near the :42 run, after the window or with no reset time", () => {
  const io = cue("2026-10-28T20:00:00Z");
  assert.equal(json(run(["wake", "--resets-at", "1793232000"], io)).reason, "no window is open");
  run(["window", "start", "10"], io);
  const at = (iso) => String(Date.parse(iso) / 1000);
  const first = json(run(["wake", "--resets-at", at("2026-10-28T22:10:30Z")], io));
  assert.deepEqual(first, { wake: null, arm: true, runOnceAt: "2026-10-28T22:13Z", reason: "create the wake, then record it with window ids --wake" });
  assert.equal(json(run(["window", "ids", "--wake", "trig_01W"], io)).wake, "trig_01W");
  const moved = json(run(["wake", "--resets-at", at("2026-10-28T23:00:00Z")], io));
  assert.deepEqual([moved.arm, moved.wake, moved.runOnceAt], [true, "trig_01W", "2026-10-28T23:02Z"]);
  for (const reset of ["2026-10-28T22:25:00Z", "2026-10-28T22:40:00Z"]) {
    const near = json(run(["wake", "--resets-at", at(reset)], io));
    assert.equal(near.arm, false, reset);
    assert.match(near.reason, /:42 covers/);
  }
  assert.equal(json(run(["wake", "--resets-at", at("2026-10-28T22:41:00Z")], io)).arm, true, "22:43 is after the :42 run");
  assert.match(json(run(["wake", "--resets-at", at("2026-10-29T06:00:00Z")], io)).reason, /after the window ends/);
  assert.match(json(run(["wake", "--resets-at", at("2026-10-28T19:00:00Z")], io)).reason, /has passed/);
  for (const args of [[], ["--resets-at", "soon"]]) {
    const none = json(run(["wake", ...args], io));
    assert.equal(none.arm, false);
    assert.match(none.log, /no usage-limit reset time/);
  }
  io.now = () => new Date("2026-10-28T21:00:00Z");
  run(["window", "stop"], io);
  assert.equal(json(run(["wake", "--resets-at", at("2026-10-28T23:00:00Z")], io)).arm, false, "a stopped window arms nothing");
  io.now = () => new Date("2026-10-29T21:00:00Z");
  run(["window", "archived"], io);
  run(["window", "start"], io);
  assert.equal(io.windowFile.wake, "trig_01W", "the wake is one standing trigger, kept across windows");
});

test("a Window line in docs/sprint.md still counts, but the cue neither stops it nor opens a second", () => {
  const { io } = fakeIo(cli);
  assert.equal(json(run(["window"], io)).state, "open");
  assert.match(json(run(["window", "stop"], io)).error, /Window line of docs\/sprint\.md/);
  assert.match(json(run(["window", "start"], io)).error, /already open/);
  assert.equal(io.windowFile, null);
});

test("with no window, every title has no session yet and started is refused", () => {
  const io = cue("2026-10-28T20:00:00Z");
  assert.ok(Object.values(json(run(["sessions"], io))).every((id) => id === null));
  assert.deepEqual(json(run(["sessions", "--all"], io)), []);
  assert.equal(run(["started", "Course lane: wk", "trig_01A"], io).code, 2);
});

test("resume reads the run's log from the file it names, and needs the run's last event", () => {
  const log = "You've hit your session limit · resets 12am (America/New_York) (error type rate_limit, HTTP 429)";
  const read = [];
  const io = cue("2026-10-21T03:02:00Z", { readLog: (f) => (read.push(f), log), sprintDoc: () => { throw new Error("read the doc"); } });
  const out = run(["resume", "--log", ".sprint/run-trig_01A.txt", "--last-event", "2026-10-21T02:11:00Z"], io);
  assert.equal(out.code, 0);
  assert.deepEqual(json(out), { start: false, after: "2026-10-21T04:00Z", restartAt: "2026-10-21T04:02Z", reason: "usage limit; resets 2026-10-21T04:00Z" });
  assert.deepEqual(read, [".sprint/run-trig_01A.txt"]);
  const missing = run(["resume", "--log", "x.txt"], io);
  assert.equal(missing.code, 2);
  assert.match(json(missing).do, /last_event_at/);
  const noLog = run(["resume", "--last-event", "2026-10-21T02:11:00Z"], io);
  assert.equal(noLog.code, 2);
  assert.match(json(noLog).do, /Write tool/);
  assert.equal(run(["resume", "-", "--last-event", "2026-10-21T02:11:00Z"], io).code, 2, "no log on stdin");
});

test("lock lets one supervisor run in at a time, and takes over a lock a dead run left", () => {
  let file = null;
  let now = new Date("2026-10-28T20:42:00Z");
  const io = cue(now, {
    now: () => now,
    claimLock: (v) => (file ? false : ((file = v), true)),
    readLock: () => file,
    writeLock: (v) => { file = v; },
    removeLock: () => { file = null; },
    sprintDoc: () => { throw new Error("read the doc"); },
  });
  assert.deepEqual(json(run(["lock"], io)), { ok: true });
  now = new Date("2026-10-28T20:50:00Z");
  const busy = run(["lock"], io);
  assert.equal(busy.code, 2);
  assert.equal(json(busy).error, "another supervisor run holds the lock, since 2026-10-28T20:42Z");
  assert.match(json(busy).do, /start, update and comment nothing/);
  assert.equal(file.at, "2026-10-28T20:42:00.000Z", "a refused run leaves the lock as it was");
  now = new Date("2026-10-28T21:03:00Z");
  assert.deepEqual(json(run(["lock"], io)), { ok: true, stale: "2026-10-28T20:42Z" });
  assert.equal(file.at, "2026-10-28T21:03:00.000Z");
  assert.deepEqual(json(run(["unlock"], io)), { ok: true });
  assert.equal(file, null);
  assert.deepEqual(json(run(["lock"], io)), { ok: true });
  file = { at: "garbage" };
  assert.deepEqual(json(run(["lock"], io)), { ok: true, stale: "garbage" }, "an unreadable lock counts as stale");
});

test("identity says whether gh is signed in as the bot", () => {
  const as = (login) => json(run(["identity"], fakeIo([], { gh: () => `${login}\n` }).io));
  assert.deepEqual(as("greenbeanbot"), { login: "greenbeanbot", ok: true });
  assert.deepEqual(as("astevegreen"), { login: "astevegreen", ok: false });
});

test("has-work --started counts each session created this run against free memory", () => {
  const io = fakeIo(cli).io; // 9000 MB free; #7 is in progress on wk
  assert.equal(json(run(["has-work", "Course lane: wk", "--started", "3"], io)).start, true, "9000 - 3 x 1536 = 4392 MB");
  const four = json(run(["has-work", "Course lane: wk", "--started", "4"], io));
  assert.equal(four.start, false);
  assert.equal(four.reason, "memory: 2856 MB free, under the 4096 MB floor, counting 1536 MB for each of the 4 sessions started this run");
  for (const k of ["-1", "x", "1.5"]) assert.equal(run(["has-work", "Course lane: wk", "--started", k], io).code, 2, k);
});
