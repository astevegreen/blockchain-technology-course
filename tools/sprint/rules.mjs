// The sprint's queue rules (docs/sprint.md), held in one place: which issue a lane works on next, whose comment
// counts as the owner's, when held work is retried, what an issue waits for, whether a session has work, and the
// sprint log's status block, and the window `/sprint-start` opens on cue. The skills ask tools/sprint/queue.mjs,
// which gathers the world with gh and git and calls `run` here; the rules read only what they are given. Ported
// from YODC's October sprint, without its research lane; the cue from Terminal Dusk's.
import { resumeAfter } from "./usage-limit.mjs";

// Sprint sessions comment as the bot; only the owner's own account answers for the owner.
export const OWNER = "astevegreen";
export const BOT = "greenbeanbot";
// tools/gemini-audit.mjs starts every comment with this. An audit is a note for the plan session and the
// implementer, posted as the bot: never an answer, a send-back or a sprint step, so the rules skip it.
export const AUDIT = "<!-- gemini-audit -->";
// Under this, the supervisor starts nothing; over it, a lane retries work the machine failed. Quarto renders are
// the heavy part.
export const MEMORY_FLOOR_MB = 4096;
// What a session the supervisor started this run counts as using before it shows in free memory.
export const SESSION_MB = 1536;
// The labels that say where a sprint issue stands. `move` keeps one of them on each issue.
export const STATES = ["sprint-ready", "in-progress", "to-integrate", "held", "blocked"];
// Session titles start with this, so the supervisor never mistakes another project's sessions for the course's.
export const TITLE = "Course";

const STOP = "Stop and report this output on the sprint log issue. Never work out the queue by hand.";

// A failure: `error` says what went wrong, `do` what the session does next.
export class QueueError extends Error {
  constructor(message, todo = STOP, code = 1) {
    super(message);
    this.do = todo;
    this.code = code;
  }
}
// A move the rules don't allow: the session acts on `do` and carries on.
const refuse = (message, todo) => new QueueError(message, todo, 2);

// --- docs/sprint.md ----------------------------------------------------------------------------------------------

const stamp = (s) => new Date(`${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}T${s.slice(9, 11)}:${s.slice(11, 13)}:00Z`);

// Ranges such as `L3–L6` name each ID between.
function idRefs(text) {
  const ids = new Set();
  for (const m of text.matchAll(/\b([A-Z]+)(\d+)\s*[–-]\s*(?:\1)?(\d+)\b/g)) {
    for (let n = Number(m[2]); n <= Number(m[3]); n++) ids.add(`${m[1]}${n}`);
  }
  for (const m of text.matchAll(/\b([A-Z]+\d+[a-z]?)\b/g)) ids.add(m[1]);
  return [...ids];
}
const issueRefs = (text) => [...text.matchAll(/#(\d+)/g)].map((m) => Number(m[1]));

// The text of a "Depends on" or "Waits for" up to its first full stop; "none" and "nothing" name nothing.
function firstSentence(text) {
  if (/^(none|nothing)\b/i.test(text)) return "";
  const end = text.search(/\.(\s|$)/);
  return end >= 0 ? text.slice(0, end) : text;
}

// The lanes, sprint log issue, pre-sprint tag, environment and backlog that docs/sprint.md declares. The
// environment is null until setup day replaces its `env_…` placeholder. The window is null too: `/sprint-start`
// opens it on this computer (withLocalWindow), unless the file names one on a `**Window (UTC):**` line.
export function parseSprintDoc(text) {
  const window = /\*\*Window \(UTC\):\*\*\s*`(\d{8}T\d{4})`\s*to\s*`(\d{8}T\d{4})`/.exec(text);
  const lanes = [...text.matchAll(/^\|\s*`([a-z]+)`\s*\|\s*`lane:\1`\s*\|\s*`([^`]+)`/gm)].map((m) => ({ name: m[1], worktree: m[2] }));
  if (lanes.length === 0) throw new QueueError("docs/sprint.md has no Lanes table rows (| `<lane>` | `lane:<lane>` | `<worktree>` |)");
  const log = /#(\d+) "Sprint log"/.exec(text);
  if (!log) throw new QueueError('docs/sprint.md names no sprint log issue (#<n> "Sprint log")');

  const backlog = {};
  const start = text.search(/^## Backlog\s*$/m);
  if (start < 0) throw new QueueError('docs/sprint.md has no "## Backlog" section');
  let lane = null;
  let item = null;
  for (const line of text.slice(start).split(/\r?\n/).slice(1)) {
    if (/^## /.test(line)) break;
    const heading = /^### ([a-z]+)\b/.exec(line);
    if (heading) {
      lane = heading[1];
      backlog[lane] = [];
      item = null;
      continue;
    }
    const entry = /^- \*\*([A-Z]+\d+[a-z]?)\*\*\s*(.*)$/.exec(line);
    if (entry && lane) {
      item = { id: entry[1], text: entry[2] };
      backlog[lane].push(item);
    } else if (item && /^\s+\S/.test(line)) {
      item.text += ` ${line.trim()}`;
    } else {
      item = null;
    }
  }
  for (const items of Object.values(backlog)) {
    for (const it of items) {
      const waits = /Waits for:\s*(.*)$/i.exec(it.text);
      const said = waits ? firstSentence(waits[1].trim()) : "";
      it.waits = [...idRefs(said).map((id) => ({ id })), ...issueRefs(said).map((issue) => ({ issue }))];
    }
  }
  return {
    window: window ? { start: stamp(window[1]), end: stamp(window[2]) } : null,
    lanes,
    logIssue: Number(log[1]),
    preSprintTag: /`(pre-sprint-[\w-]+)`/.exec(text)?.[1] ?? null,
    environment: /\*\*Environment:\*\*\s*`(env_\w+)`/.exec(text)?.[1] ?? null,
    backlog,
  };
}

// --- issues ------------------------------------------------------------------------------------------------------

// The backlog ID in a title `[task] <ID>: …`, or null.
export function taskId(title) {
  return /^\[task\]\s+([A-Z]+\d+[a-z]?):/.exec(title)?.[1] ?? null;
}

// gh's JSON for `issue list --json number,title,body,labels,state,comments,closedAt,createdAt`.
export function normalizeIssues(raw) {
  return raw.map((i) => ({
    number: i.number,
    title: i.title,
    id: taskId(i.title),
    body: i.body ?? "",
    open: String(i.state).toUpperCase() === "OPEN",
    labels: (i.labels ?? []).map((l) => l.name),
    closedAt: i.closedAt ? new Date(i.closedAt) : null,
    createdAt: i.createdAt ? new Date(i.createdAt) : null,
    comments: (i.comments ?? [])
      .map((c) => ({ author: c.author?.login ?? "", body: c.body ?? "", at: new Date(c.createdAt) }))
      .filter((c) => !c.body.startsWith(AUDIT))
      .sort((a, b) => a.at - b.at),
  }));
}

// `L1` is the issue `[task] L1:` or a split of it, `[task] L1a:`; never `[task] L10:`.
export function matchesId(issue, id) {
  return issue.id === id || (/[a-z]$/.test(issue.id ?? "") && issue.id.slice(0, -1) === id);
}

// The issue numbers a body's "Depends on" and "Waits for" lines name, read up to their first full stop.
export function bodyRefs(body) {
  const lines = body.split(/\r?\n/);
  const refs = new Set();
  lines.forEach((line, k) => {
    const m = /^[\s>*#-]*(?:depends on|waits for)\s*(?:\*\*)?\s*:?\s*(?:\*\*)?\s*(.*)$/i.exec(line);
    if (!m) return;
    const text = m[1].trim() || (lines.slice(k + 1).find((l) => l.trim()) ?? "").trim();
    for (const n of issueRefs(firstSentence(text))) refs.add(n);
  });
  return [...refs];
}

const oneLine = (s, max = 300) => {
  const flat = s.replace(/\s+/g, " ").trim();
  return flat.length > max ? `${flat.slice(0, max - 1)}…` : flat;
};
const short = (i) => i.id ?? oneLine(i.title.replace(/^\[task\]\s*/, ""), 40);
const name = (i) => `#${i.number} ${short(i)}`;
const findLast = (xs, f) => [...xs].reverse().find(f) ?? null;

// The owner's newest comment after the bot's newest one: an answer the lanes may act on.
export function ownerReply(issue) {
  const lastBot = findLast(issue.comments, (c) => c.author === BOT);
  return findLast(issue.comments, (c) => c.author === OWNER && (!lastBot || c.at > lastBot.at));
}

// Whether a lane retries a held issue now. Only the owner's and the bot's comments count; the newest one decides:
// an owner reply, the integrator sending it back, or a machine failure once memory is over the floor. Anything
// else (the lane's own note, an answer relayed by the bot) waits for the owner.
export function heldRetry(issue, freeMb) {
  const last = findLast(issue.comments, (c) => c.author === OWNER || c.author === BOT);
  if (!last) return { retry: false, why: "no comment says why it is held" };
  const concerns = oneLine(last.body);
  if (last.author === OWNER) return { retry: true, why: "the owner replied", concerns };
  if (last.body.startsWith("Integrator:")) return { retry: true, why: "the integrator sent it back", concerns };
  if (last.body.startsWith("Implementer: machine")) {
    return freeMb > MEMORY_FLOOR_MB
      ? { retry: true, why: `the machine failed it and ${freeMb} MB is free now`, concerns }
      : { retry: false, why: `the machine failed it and ${freeMb} MB free is not over ${MEMORY_FLOOR_MB} MB` };
  }
  return { retry: false, why: `waits for the owner; newest comment: "${oneLine(last.body, 100)}"` };
}

const byNumber = (world, n) => world.issues.find((i) => i.number === n);

// What a wait names is over: an issue closed, or every issue of a backlog ID closed (and one exists).
function refOver(world, ref) {
  if ("issue" in ref) return byNumber(world, ref.issue)?.open === false;
  const issues = world.issues.filter((i) => matchesId(i, ref.id));
  return issues.length > 0 && issues.every((i) => !i.open);
}
const refName = (world, ref) => {
  if ("id" in ref) return ref.id;
  const i = byNumber(world, ref.issue);
  return i ? name(i) : `#${ref.issue} (no such issue)`;
};
// The waits not over yet: the issue body's "Depends on" and "Waits for" lines, and its backlog line's "Waits for:".
function unmet(world, issue, lane) {
  const item = (world.doc.backlog[lane] ?? []).find((it) => issue.id && matchesId(issue, it.id));
  return [...(item?.waits ?? []), ...bodyRefs(issue.body).map((n) => ({ issue: n }))].filter((r) => !refOver(world, r));
}

// Backlog order: the ID's place in its lane's list, then its letter; issues with no listed ID after.
function backlogOrder(items) {
  const ids = items.map((it) => it.id);
  const key = (i) => {
    const base = ids.includes(i.id) ? i.id : i.id?.replace(/[a-z]$/, "");
    const at = base ? ids.indexOf(base) : -1;
    return at >= 0 ? [0, at, i.id, i.number] : [1, 0, "", i.number];
  };
  return (a, b) => {
    const [x, y] = [key(a), key(b)];
    return x[0] - y[0] || x[1] - y[1] || (x[2] < y[2] ? -1 : x[2] > y[2] ? 1 : 0) || x[3] - y[3];
  };
}

const laneLabel = (issue) => issue.labels.find((l) => l.startsWith("lane:"))?.slice(5) ?? null;

// --- next --------------------------------------------------------------------------------------------------------

// A lane's next job and why each other open issue waits. Jobs, in order: work a stopped session left in progress
// (resume when its branch has commits, else build it again); held work the rules retry; then ready issues, and
// blocked ones the owner answered, in backlog order.
export function laneQueue(world, lane, taken = []) {
  const label = `lane:${lane}`;
  const issues = world.issues.filter((i) => i.open && i.labels.includes(label)).sort(backlogOrder(world.doc.backlog[lane] ?? []));
  const jobs = [];
  const waiting = [];
  const job = (rank, mode, i, reason, concerns = null) => jobs.push({ rank, job: { mode, issue: i.number, concerns, reason } });
  for (const i of issues) {
    const has = (l) => i.labels.includes(l);
    // `held` and `blocked` beat a leftover `in-progress`: they are the builder's own verdict.
    if (taken.includes(i.number)) {
      waiting.push(`${name(i)} was taken this session`);
    } else if (has("to-integrate")) {
      waiting.push(`${name(i)} is the integrator's`);
    } else if (has("held")) {
      const r = heldRetry(i, world.freeMb);
      if (r.retry) job(1, "fix", i, `${name(i)} is held and ${r.why}`, r.concerns);
      else waiting.push(`${name(i)} is held: ${r.why}`);
    } else if (has("in-progress") && !has("blocked")) {
      const ahead = world.branchAhead(i.number);
      if (ahead > 0) job(0, "resume", i, `${name(i)} was in progress when its session stopped; sprint/${i.number} has ${ahead} commit(s) to review`);
      else job(0, "build", i, `${name(i)} was in progress when its session stopped, with no commits on sprint/${i.number}`);
    } else if (has("blocked") || has("sprint-ready")) {
      const blocked = has("blocked");
      const waits = unmet(world, i, lane);
      if (blocked && !ownerReply(i)) waiting.push(`${name(i)} is blocked: no owner reply yet`);
      else if (waits.length > 0) waiting.push(`${name(i)} waits for ${waits.map((r) => refName(world, r)).join(", ")}`);
      else job(2, "build", i, blocked ? `${name(i)}: the owner answered its question` : `${name(i)} is ready`);
    }
  }
  jobs.sort((a, b) => a.rank - b.rank);
  return { job: jobs[0]?.job ?? null, waiting };
}

// `next <lane>`: the job, or null.
export function nextJob(world, lane, taken = []) {
  laneOf(world, lane);
  return laneQueue(world, lane, taken).job;
}

function laneOf(world, lane) {
  if (!world.doc.lanes.some((l) => l.name === lane)) {
    throw refuse(`unknown lane "${lane}"`, `Use a lane from the Lanes table in docs/sprint.md: ${world.doc.lanes.map((l) => l.name).join(", ")}.`);
  }
}

// --- has-work ----------------------------------------------------------------------------------------------------

// The session titles the supervisor keeps running: a lane and a plan session per lane, and one integrator.
export function sessionTitles(doc) {
  const lanes = doc.lanes.map((l) => l.name);
  return [...lanes.map((l) => `${TITLE} lane: ${l}`), ...lanes.map((l) => `${TITLE} plan: ${l}`), `${TITLE} integrate`];
}

// Whether a fresh session with this title would find work. Extra fields: `todo` and `ready` for a plan, `issues`
// to integrate. `started` sessions the supervisor created this run each count SESSION_MB against free memory:
// they are not using it yet when it is read.
export function hasWork(world, title, started = 0) {
  knownTitle(world.doc, title);
  const free = world.freeMb - SESSION_MB * started;
  const counting = started ? `, counting ${SESSION_MB} MB for each of the ${started} sessions started this run` : "";
  const floor = free < MEMORY_FLOOR_MB ? `memory: ${free} MB free, under the ${MEMORY_FLOOR_MB} MB floor${counting}` : null;
  let answer;
  if (title === `${TITLE} integrate`) {
    const issues = world.issues.filter((i) => i.open && i.labels.includes("to-integrate")).map((i) => i.number).sort((a, b) => a - b);
    answer = {
      start: issues.length > 0,
      reason: issues.length ? `to integrate: ${issues.map((n) => `#${n}`).join(", ")}` : "no open issue is labelled to-integrate",
      issues,
    };
  } else if (title.startsWith(`${TITLE} plan: `)) {
    const lane = title.slice(`${TITLE} plan: `.length);
    const ready = world.issues.filter((i) => i.open && i.labels.includes(`lane:${lane}`) && i.labels.includes("sprint-ready")).length;
    const todo = (world.doc.backlog[lane] ?? []).map((it) => it.id).filter((id) => !world.issues.some((i) => matchesId(i, id)));
    const start = ready < 3 && todo.length > 0;
    const reason = todo.length === 0
      ? "every backlog item has an issue"
      : `${ready} open sprint-ready${ready < 3 ? ", under 3" : ", 3 or more"}; not yet filed: ${todo.join(", ")}`;
    answer = { start, reason, ready, todo };
  } else {
    const q = laneQueue(world, title.slice(`${TITLE} lane: `.length));
    const reason = q.job ? q.job.reason : q.waiting.length ? `nothing to do: ${q.waiting.join("; ")}` : "nothing to do: no open issue";
    answer = { start: q.job !== null, reason };
  }
  return floor ? { ...answer, start: false, reason: floor } : answer;
}

// --- move --------------------------------------------------------------------------------------------------------

const RETRY = "Leave it, and run `next` for the next job.";

// The labels and the standard comment a move makes, or a refusal saying what to do instead.
export function planMove(world, number, to, note = null) {
  const issue = byNumber(world, number);
  if (!issue) throw refuse(`no issue #${number}`, "Use the issue number `next` printed.");
  if (!issue.open) throw refuse(`#${number} is closed`, RETRY);
  const targets = ["in-progress", "to-integrate", "held", "blocked"];
  if (!targets.includes(to)) throw refuse(`a lane cannot move an issue to "${to}"`, `Move it to one of: ${targets.join(", ")}.`);
  const has = STATES.filter((s) => issue.labels.includes(s));
  // A lane's claim (`in-progress`) is what it moves on, even beside a label the builder added.
  const from = has.includes("in-progress") ? "in-progress" : has.length === 1 ? has[0] : has.length === 0 ? "none" : has.join("+");
  const text = note ? note.replace(/\\n/g, "\n").trim() : null;
  const plan = (comment) => ({ issue: number, from, to, comment, add: has.includes(to) ? [] : [to], remove: has.filter((s) => s !== to) });

  if (from === "to-integrate") throw refuse(`#${number} is to-integrate: the integrator's, not the lane's`, RETRY);
  if (from === "none" || from.includes("+")) {
    throw refuse(`#${number} has ${from === "none" ? "no state label" : `the state labels ${has.join(" and ")}`}`,
      "Report it on the sprint log issue for the owner, then run `next`.");
  }
  if (to === "in-progress") {
    if (from === "in-progress") return plan("Lane: re-queued, the previous lane session stopped.");
    if (from === "held") {
      const r = heldRetry(issue, world.freeMb);
      if (!r.retry) throw refuse(`#${number} is held and ${r.why}`, RETRY);
      return plan(null);
    }
    if (from === "blocked" && !ownerReply(issue)) throw refuse(`#${number} is blocked and the owner has not replied`, RETRY);
    const waits = unmet(world, issue, laneLabel(issue));
    if (waits.length > 0) throw refuse(`#${number} waits for ${waits.map((r) => refName(world, r)).join(", ")}`, RETRY);
    return plan(from === "blocked" ? "Lane: unblocked by the owner's answer; the implementer reads it as part of the spec." : null);
  }
  if (from === to) return { issue: number, from, to, comment: null, add: [], remove: [] };
  if (from !== "in-progress") throw refuse(`#${number} is ${from}; only work in progress moves to ${to}`, RETRY);
  if (to === "to-integrate") {
    if (!text) throw refuse("ready to integrate needs a note", "Run it again with --note '<WHAT CHANGED and STUDENT-VISIBLE lines from the hand-back>'.");
    if (world.branchAhead(number) === 0) {
      throw refuse(`sprint/${number} has no commits ahead of origin/main`, "Nothing to integrate: move it to held with a --note saying why.");
    }
    return plan(`Lane: ready to integrate, branch sprint/${number}.\n${text}`);
  }
  return plan(text ? `Lane: ${to}. ${text}` : null);
}

// --- status ------------------------------------------------------------------------------------------------------

function fmt(d) {
  return `${d.toISOString().slice(0, 10)} ${d.toISOString().slice(11, 16)}Z`;
}
const needKey = (line) => /^#(\d+) \[(\w+)\]/.exec(line)?.[0] ?? line;

// The sprint log's body: per lane, the open issues by state label and those closed since the window opened; main's
// head and the last Lab Tests run (a push deploys nothing: the owner publishes); free memory; and "Needs you" (a
// blocked question with no owner reply, held work the lanes won't retry, then `also`: stuck sessions, failed
// starts). `new` lists the "Needs you" items the old body didn't have.
export function statusBlock(world, { also = [], oldBody = "" } = {}) {
  const lines = [`Status at ${fmt(world.now)}. The supervisor rewrites this every hour; the comments hold the history.`, ""];
  lines.push("**Lanes** (open issues by label; closed since the window opened)");
  for (const { name: lane } of world.doc.lanes) {
    const mine = world.issues.filter((i) => i.labels.includes(`lane:${lane}`));
    const counts = STATES.map((s) => `${mine.filter((i) => i.open && i.labels.includes(s)).length} ${s}`).join(", ");
    const closed = mine
      .filter((i) => !i.open && i.closedAt && world.doc.window && i.closedAt >= world.doc.window.start)
      .sort((a, b) => a.closedAt - b.closedAt)
      .map(name);
    lines.push(`- ${lane}: ${counts}; closed: ${closed.length ? closed.join(", ") : "none"}`);
  }
  const m = world.mainHead;
  const t = world.lastLabTests;
  lines.push(
    "",
    m ? `**Main:** ${m.sha.slice(0, 8)} "${oneLine(m.subject, 80)}"` : "**Main:** unknown",
    t ? `**Lab Tests:** last run ${t.conclusion || t.status} at ${t.headSha.slice(0, 8)} ${t.url}` : "**Lab Tests:** no run found",
    `**Free memory:** ${world.freeMb} MB`,
  );
  const needs = [];
  for (const i of world.issues.filter((x) => x.open && x.labels.some((l) => l.startsWith("lane:"))).sort((a, b) => a.number - b.number)) {
    if (i.labels.includes("blocked") && !ownerReply(i)) needs.push(`#${i.number} [blocked] ${short(i)}: waiting for your answer`);
    if (i.labels.includes("held")) {
      const r = heldRetry(i, world.freeMb);
      if (!r.retry) needs.push(`#${i.number} [held] ${short(i)}: ${r.why}`);
    }
  }
  needs.push(...also.map((a) => oneLine(a)));
  lines.push("", "**Needs you**", ...(needs.length ? needs.map((n) => `- ${n}`) : ["- nothing"]));

  const old = oldBody.split(/\r?\n/);
  const at = old.findIndex((l) => l.trim() === "**Needs you**");
  const before = new Set(at < 0 ? [] : old.slice(at + 1).filter((l) => l.startsWith("- ")).map((l) => needKey(l.slice(2))));
  return { body: lines.join("\n"), needsYou: needs, new: needs.filter((n) => !before.has(needKey(n))) };
}

// --- the triggers the supervisor started -------------------------------------------------------------------------

// RemoteTrigger `list` returns only the account's newest 20 triggers, and other projects' sprints share the
// account, so a course trigger soon drops off it. The supervisor records each trigger it creates (`started`) and
// reads them back (`sessions`) from a file in the main checkout's git folder: never committed, shared by every
// worktree, and kept to the newest 500 records.
const TRIGGER_ID = /^trig_\w+$/;
const ENVIRONMENT_ID = /^env_\w+$/;
const KEEP_TRIGGERS = 500;

function knownTitle(doc, title) {
  if (!sessionTitles(doc).includes(title)) {
    throw refuse(`unknown session title "${title}"`, `Use one of: ${sessionTitles(doc).map((t) => `"${t}"`).join(", ")}.`);
  }
}

// The records with this start added: {title, id, at}. Terminal Dusk keeps the same ledger.
export function recordStarted(doc, records, title, id, now) {
  knownTitle(doc, title);
  if (!TRIGGER_ID.test(id ?? "")) throw refuse(`not a trigger id: "${id}"`, "Run it again with the id `create` returned (trig_…).");
  if (!inWindow(doc, now)) throw refuse("no window is open", "Start no sessions; report it.");
  return [...records, { title, id, at: now.toISOString() }].slice(-KEEP_TRIGGERS);
}

// The trigger recorded last for each session title since the window opened (null: none yet); with `all`, every
// record since the window opened, newest first.
export function sessionTriggers(doc, records, { all = false } = {}) {
  const titles = sessionTitles(doc);
  const since = doc.window?.start.getTime() ?? Infinity;
  // Reversed first, so that of two records in the same second the later one counts as newer.
  const recent = records
    .filter((r) => titles.includes(r?.title) && TRIGGER_ID.test(r?.id ?? "") && Date.parse(r?.at) >= since)
    .reverse()
    .sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
  if (all) return recent;
  return Object.fromEntries(titles.map((t) => [t, recent.find((r) => r.title === t)?.id ?? null]));
}

// --- the window --------------------------------------------------------------------------------------------------

// `/sprint-start [hours]` opens the window when the owner cues it, and `/sprint-stop` ends it early. The window
// and the ids of the scheduled tasks /sprint-start makes are kept beside the ledger, in sprint-window.json:
// {start, end, environment, supervisor, archiver, wake, stoppedBy}. A cue never waits for a push, and a window left
// in this file is never a fact a later sprint inherits. Terminal Dusk's design (24 Oct). The environment is the one
// /sprint-start found in list_environments: its id changes whenever `claude rc` restarts, so the doc's line is only
// a fallback.
export const DEFAULT_HOURS = 38;
export const MAX_HOURS = 96;
const HOUR_MS = 3600000;

export const inWindow = (doc, now) => Boolean(doc.window) && now >= doc.window.start && now < doc.window.end;
const toMinute = (d) => new Date(Math.floor(d.getTime() / 60000) * 60000);
const isoMinute = (d) => d.toISOString().replace(/:\d{2}\.\d{3}Z$/, "Z");

// "Wed 28 Oct 20:00": the owner's clock, on which usage limits reset too.
export function newYork(d) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "America/New_York", hourCycle: "h23", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  }).formatToParts(d);
  const get = (type) => parts.find((p) => p.type === type).value;
  return `${get("weekday")} ${get("day")} ${get("month")} ${get("hour")}:${get("minute")}`;
}

// The doc's facts with this computer's window (sprint-window.json, or null) in place of any Window line, and its
// environment, when the cue named one, in place of the doc's.
export function withLocalWindow(doc, local) {
  if (!local) return { ...doc, supervisor: null, archiver: null, wake: null, stoppedBy: null };
  const start = new Date(local.start ?? Number.NaN);
  const end = new Date(local.end ?? Number.NaN);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) {
    throw new QueueError("sprint-window.json has no start and end", "Stop and report it on the sprint log issue: the owner fixes or deletes the file.");
  }
  return {
    ...doc, window: { start, end }, environment: local.environment ?? doc.environment,
    supervisor: local.supervisor ?? null, archiver: local.archiver ?? null,
    wake: local.wake ?? null, stoppedBy: local.stoppedBy ?? null,
  };
}

// Where now falls against the window, "none" (none opened yet), "before", "open" or "after", with the lanes, the
// sprint log issue, the scheduled tasks' ids, and `stoppedBy`: "sprint-stop" when /sprint-stop ended the window
// early, so a supervisor reports the owner's pause as a stop, never as a fault (YODC called one "a machinery bug").
export function windowState(doc, now) {
  const w = doc.window;
  let state = "none";
  if (inWindow(doc, now)) state = "open";
  else if (w) state = now < w.start ? "before" : "after";
  return {
    state,
    ...(w && { start: isoMinute(w.start), end: isoMinute(w.end), newYork: `${newYork(w.start)} to ${newYork(w.end)}` }),
    lanes: doc.lanes,
    log: doc.logIssue,
    supervisor: doc.supervisor ?? null,
    archiver: doc.archiver ?? null,
    wake: doc.wake ?? null,
    stoppedBy: doc.stoppedBy ?? null,
  };
}

const WINDOW_USAGE = "Use `window`, `window start [hours] [--environment <env_…>] [--dry-run]`, `window ids --supervisor <id> --archiver <id> --wake <id>`, `window stop` or `window archived`.";

// `window …`: { out, write }, `write` being the sprint-window.json to save, or null. `doc` holds the window the
// file names already; `local` is the file as read.
export function windowCommand(doc, local, words, f, now) {
  const [sub, hours] = words;
  const state = (w) => windowState(withLocalWindow(doc, w), now);
  const open = inWindow(doc, now);
  // A Window line in docs/sprint.md is a fallback the cue never writes, so only the owner changes it.
  const cued = () => {
    if (!open) throw refuse("no window is open", sub === "stop" ? "Nothing to stop; report it." : "Run `window start` first.");
    if (!local) throw refuse("the open window is the Window line of docs/sprint.md, not one /sprint-start opened", "Report it: the owner edits that line.");
  };
  if (sub === undefined) return { out: windowState(doc, now), write: null };
  if (sub === "start") {
    if (open) throw refuse(`a window is already open, until ${isoMinute(doc.window.end)}`, "Report it; /sprint-stop ends it.");
    // The last window's archiver clears its id once it has switched itself off; until then its sessions may run.
    if (local?.archiver) {
      throw refuse(`the last window's archiver ${local.archiver} is still on record, so its sessions may still be running`,
        "RemoteTrigger get it. Disabled: run `window archived`, then start again. Enabled: report it; it switches itself off once none of them runs.");
    }
    const h = Number(hours ?? DEFAULT_HOURS);
    if (!Number.isInteger(h) || h < 1 || h > MAX_HOURS) {
      throw refuse(`the window is a whole number of hours from 1 to ${MAX_HOURS}, not "${hours}"`, `Run it again with a number of hours, or none for ${DEFAULT_HOURS}.`);
    }
    const environment = f.environment?.at(-1) ?? null;
    if (environment !== null && !ENVIRONMENT_ID.test(environment)) {
      throw refuse(`--environment "${environment}" is not an environment id`, "Run it again with the id list_environments gave (env_…).");
    }
    // Every sprint session posts on the log, so a window without one would fail at its first comment. A dry run
    // refuses too: the cue is only proved once the log exists.
    if (!doc.logIssue) throw refuse("docs/sprint.md names no sprint log yet (#0); setup day makes it", "Start nothing; report it.");
    const start = toMinute(now);
    // The wake is one standing one-shot, moved rather than made again, so a new window keeps its id.
    const w = {
      start: start.toISOString(), end: new Date(start.getTime() + h * HOUR_MS).toISOString(), environment,
      supervisor: null, archiver: null, wake: local?.wake ?? null, stoppedBy: null,
    };
    return { out: state(w), write: f["dry-run"] ? null : w };
  }
  if (sub === "ids") {
    cued();
    const w = { ...local };
    for (const task of ["supervisor", "archiver", "wake"]) {
      const id = f[task]?.at(-1);
      if (id === undefined) continue;
      if (!TRIGGER_ID.test(id)) throw refuse(`--${task} "${id}" is not a trigger id`, "Run it again with the id create_trigger returned (trig_…).");
      w[task] = id;
    }
    if (w.supervisor === local.supervisor && w.archiver === local.archiver && w.wake === local.wake) throw refuse("no new id given", WINDOW_USAGE);
    return { out: state(w), write: w };
  }
  if (sub === "stop") {
    cued();
    const w = { ...local, end: toMinute(now).toISOString(), stoppedBy: "sprint-stop" };
    return { out: state(w), write: w };
  }
  if (sub === "archived") {
    if (open) throw refuse("the window is still open", "Leave the archiver on until the window ends.");
    if (!local?.archiver) return { out: windowState(doc, now), write: null };
    const w = { ...local, archiver: null };
    return { out: state(w), write: w };
  }
  throw refuse(`unknown window command "${sub}"`, WINDOW_USAGE);
}

// --- the wake after a usage limit ------------------------------------------------------------------------------

// While a usage limit is on, a scheduled supervisor run fails before it starts, so lanes a limit stopped would wait
// for the next hourly run. Each supervisor run moves one standing one-shot of itself to the reset + 2 minutes, from
// its own session's rate_limit_info.resetsAt (epoch seconds). Not when that falls in the 15 minutes up to the
// hourly run at minute 42, which covers it: two supervisors at once could start a lane twice.
export const SUPERVISOR_MINUTE = 42;
const WAKE_AFTER_MS = 2 * 60000;

export function wakePlan(doc, resetsAt, now) {
  const base = { wake: doc.wake ?? null };
  if (!inWindow(doc, now)) return { ...base, arm: false, reason: "no window is open" };
  if (resetsAt === undefined || resetsAt === "" || !/^\d{9,11}$/.test(String(resetsAt))) {
    return { ...base, arm: false, reason: "no resetsAt", log: "no usage-limit reset time in get_session, so no wake is armed this run" };
  }
  const at = new Date(Math.ceil((Number(resetsAt) * 1000 + WAKE_AFTER_MS) / 60000) * 60000);
  const runOnceAt = isoMinute(at);
  if (at <= now) return { ...base, arm: false, runOnceAt, reason: "the reset has passed" };
  if (at >= doc.window.end) return { ...base, arm: false, runOnceAt, reason: "the reset falls after the window ends" };
  const m = at.getUTCMinutes();
  if (m >= SUPERVISOR_MINUTE - 15 && m <= SUPERVISOR_MINUTE) {
    return { ...base, arm: false, runOnceAt, reason: `the hourly run at :${SUPERVISOR_MINUTE} covers ${runOnceAt}` };
  }
  return { ...base, arm: true, runOnceAt, reason: base.wake ? "move the wake" : "create the wake, then record it with window ids --wake" };
}

// --- the supervisor's lock ---------------------------------------------------------------------------------------

// One supervisor run at a time: the hourly one and one a stopping session fired would otherwise both start a
// session for one title. A run takes minutes, so a lock older than this was left by a run that died.
export const LOCK_STALE_MS = 20 * 60000;

// `lock` once the atomic claim failed: `held` is the lock file's content.
export function lockCommand(held, now) {
  const at = new Date(held?.at ?? NaN);
  if (!Number.isNaN(at.getTime()) && now - at < LOCK_STALE_MS) {
    throw refuse(`another supervisor run holds the lock, since ${isoMinute(at)}`,
      "Stop now: start, update and comment nothing, since that run covers this one.");
  }
  return { ok: true, stale: Number.isNaN(at.getTime()) ? String(held?.at ?? "unreadable") : isoMinute(at) };
}

// --- the command line --------------------------------------------------------------------------------------------

const USAGE = "Usage: queue.mjs has-work \"<session title>\" [--started <k>] | next <lane> [--taken <n,n>] | move <n> <state> [--note '<text>'] | status [--write] [--also '<line>']... | env | window [start [hours] [--environment <env_…>] [--dry-run] | ids --supervisor <id> --archiver <id> --wake <id> | stop | archived] | started \"<session title>\" <trigger id> | wake [--resets-at <epoch s>] | sessions [--all] | lock | unlock | identity | resume --log <file> --last-event <ISO>";
const ISSUE_FIELDS = "number,title,body,labels,state,comments,closedAt,createdAt";

// Flags after the positional words: `--name value`, repeatable.
function flags(args) {
  const words = [];
  const out = {};
  for (let k = 0; k < args.length; k++) {
    const a = args[k];
    if (a === "--write") out.write = true;
    else if (a === "--all") out.all = true;
    else if (a === "--dry-run") out["dry-run"] = true;
    else if (a.startsWith("--")) {
      if (k + 1 >= args.length) throw refuse(`${a} needs a value`, USAGE);
      (out[a.slice(2)] ??= []).push(args[++k]);
    } else words.push(a);
  }
  return { words, flags: out };
}

// Runs one command against `io` (gh, git, the sprint doc, free memory, the clock) and returns the one line of JSON
// to print, with the exit code: 0 done, 2 refused (act on `do`), 1 failed (stop).
export function run(argv, io) {
  try {
    const [command, ...rest] = argv;
    const { words, flags: f } = flags(rest);
    const shapes = {
      "has-work": words.length === 1,
      next: words.length === 1,
      move: words.length === 2 && /^\d+$/.test(words[0] ?? ""),
      status: words.length === 0,
      env: words.length === 0,
      window: words.length <= 2,
      started: words.length === 2,
      sessions: words.length === 0,
      resume: words.length === 0,
      lock: words.length === 0,
      unlock: words.length === 0,
      identity: words.length === 0,
      wake: words.length === 0,
    };
    if (!shapes[command]) throw refuse(`unknown command: ${argv.join(" ") || "(none)"}`, USAGE);
    if (command === "lock") {
      const mine = { at: io.now().toISOString() };
      if (io.claimLock(mine)) return { code: 0, line: JSON.stringify({ ok: true }) };
      const out = lockCommand(io.readLock(), io.now());
      io.writeLock(mine);
      return { code: 0, line: JSON.stringify(out) };
    }
    if (command === "unlock") {
      io.removeLock();
      return { code: 0, line: JSON.stringify({ ok: true }) };
    }
    // Sprint comments must come from the bot: the queue counts the owner's comments as answers.
    if (command === "identity") {
      const login = io.gh(["api", "user", "--jq", ".login"]).trim();
      return { code: 0, line: JSON.stringify({ login, ok: login === BOT }) };
    }
    if (command === "resume") {
      // The log comes in a file: the guard runs a queue call alone, so it cannot arrive on a pipe or heredoc.
      const log = f.log?.at(-1);
      if (!log) throw refuse("resume needs --log <file>", "Save the end of the run's log with the Write tool under .sprint/, then pass that file.");
      const text = io.readLog(log);
      try {
        return { code: 0, line: JSON.stringify(resumeAfter(text, { lastEventAt: f["last-event"]?.at(-1), now: io.now() })) };
      } catch (e) {
        throw refuse(e.message, "Run it again with --last-event set to the run's last_event_at.");
      }
    }
    const local = io.readWindow();
    const doc = withLocalWindow(parseSprintDoc(io.sprintDoc()), local);
    if (command === "window") {
      const { out, write } = windowCommand(doc, local, words, f, io.now());
      if (write) io.writeWindow(write);
      return { code: 0, line: JSON.stringify({ ...out, ...(words[0] === "start" && { dryRun: Boolean(f["dry-run"]) }) }) };
    }
    if (command === "wake") return { code: 0, line: JSON.stringify(wakePlan(doc, f["resets-at"]?.at(-1), io.now())) };
    if (command === "started") {
      const records = recordStarted(doc, io.readTriggers(), words[0], words[1], io.now());
      io.writeTriggers(records);
      return { code: 0, line: JSON.stringify({ recorded: records.at(-1) }) };
    }
    if (command === "sessions") return { code: 0, line: JSON.stringify(sessionTriggers(doc, io.readTriggers(), { all: Boolean(f.all) })) };
    if (command === "env") {
      if (!doc.environment) {
        throw refuse("no environment yet: the window has none from /sprint-start, and docs/sprint.md's **Environment:** line is the placeholder",
          "Start nothing this run; report it. /sprint-start names the environment when it opens the window.");
      }
      return { code: 0, line: JSON.stringify({ environment_id: doc.environment }) };
    }
    const world = {
      doc,
      issues: normalizeIssues(JSON.parse(io.gh(["issue", "list", "--state", "all", "--limit", "1000", "--json", ISSUE_FIELDS]))),
      now: io.now(),
      freeMb: io.freeMb(),
      branchAhead: io.branchAhead,
      mainHead: null,
      lastLabTests: null,
    };
    let out;
    if (command === "has-work") {
      const started = Number(f.started?.at(-1) ?? 0);
      if (!Number.isInteger(started) || started < 0) throw refuse("--started takes the number of sessions created this run (0 or more)", USAGE);
      out = hasWork(world, words[0], started);
    } else if (command === "next") {
      const taken = (f.taken ?? []).flatMap((t) => t.split(",")).filter(Boolean).map(Number);
      if (taken.some((n) => !Number.isInteger(n))) throw refuse("--taken takes issue numbers, comma-separated", USAGE);
      out = nextJob(world, words[0], taken);
    } else if (command === "move") {
      const m = planMove(world, Number(words[0]), words[1], f.note?.at(-1) ?? null);
      if (m.comment) io.gh(["issue", "comment", String(m.issue), "--body", m.comment]);
      if (m.add.length || m.remove.length) {
        io.gh(["issue", "edit", String(m.issue), ...m.add.flatMap((l) => ["--add-label", l]), ...(m.remove.length ? ["--remove-label", m.remove.join(",")] : [])]);
      }
      out = { ok: true, issue: m.issue, from: m.from, to: m.to, changed: Boolean(m.comment || m.add.length || m.remove.length), comment: m.comment };
    } else {
      if (f.write && doc.logIssue === 0) {
        throw refuse("docs/sprint.md names no sprint log issue yet (#0)", "Create the Sprint log issue on setup day and put its number in docs/sprint.md; run `status` without --write until then.");
      }
      const runs = JSON.parse(io.gh(["run", "list", "--workflow", "lab-tests.yml", "--branch", "main", "--limit", "1", "--json", "headSha,status,conclusion,url"]));
      world.lastLabTests = runs[0] ?? null;
      world.mainHead = io.mainHead();
      const oldBody = byNumber(world, doc.logIssue)?.body ?? "";
      const s = statusBlock(world, { also: f.also ?? [], oldBody });
      if (f.write) io.gh(["issue", "edit", String(doc.logIssue), "--body-file", "-"], s.body);
      out = { ...s, written: Boolean(f.write) };
    }
    return { code: 0, line: JSON.stringify(out) };
  } catch (e) {
    if (e instanceof QueueError) return { code: e.code, line: JSON.stringify({ error: e.message, do: e.do }) };
    return { code: 1, line: JSON.stringify({ error: String(e?.stack ?? e), do: STOP }) };
  }
}
