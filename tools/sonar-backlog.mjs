// `node tools/sonar-backlog.mjs [--files <path>...] [--limit <n>]`: open SonarCloud issues on main, read from its public API.
// Default: the BLOCKER and CRITICAL issues. With --files: issues of any severity in just those files.
// This only reads: each request is an anonymous GET. It never reads, sends or asks for a token, so if the project
// goes private it stops and says so (SonarCloud answers a private project with "0 issues", which would mislead).
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "..");
const API = "https://sonarcloud.io/api";
const PROJECT = "astevegreen_blockchain-technology-course";
const USAGE = "usage: node tools/sonar-backlog.mjs [--files <path>...] [--limit <n>]";
const DEFAULT_LIMIT = 40;
const MAX_LIMIT = 200;
const MAX_FILES = 40;
const MAX_MESSAGE = 160;

async function httpGet(url) {
  const res = await fetch(url, { headers: { accept: "application/json" }, signal: AbortSignal.timeout(20_000) });
  const text = await res.text();
  let body = null;
  try {
    body = JSON.parse(text);
  } catch {
    // a non-JSON answer (an error page) leaves body null; the status says what happened
  }
  return { status: res.status, body };
}

function parse(argv) {
  const opts = { files: null, limit: DEFAULT_LIMIT };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--files") {
      opts.files = [];
    } else if (arg === "--limit") {
      const n = /^\d+$/.test(argv[i + 1] ?? "") ? Number(argv[++i]) : 0;
      if (n < 1 || n > MAX_LIMIT) return { error: `--limit takes a number from 1 to ${MAX_LIMIT}` };
      opts.limit = n;
    } else if (opts.files && !arg.startsWith("--")) {
      opts.files.push(arg);
    } else {
      return { error: USAGE };
    }
  }
  if (opts.files && (opts.files.length === 0 || opts.files.length > MAX_FILES))
    return { error: opts.files.length ? `--files takes at most ${MAX_FILES} paths` : USAGE };
  return opts;
}

// SonarCloud names a file `<project>:<path from the repository root>`, with forward slashes.
// Returns null for a path outside the repository (or one SonarCloud's comma-separated list could not carry).
function repoPath(file) {
  const rel = (path.isAbsolute(file) ? path.relative(ROOT, file) : file).replaceAll("\\", "/");
  const clean = path.posix.normalize(rel);
  return clean === ".." || clean.startsWith("../") || /^([A-Za-z]:|\/)/.test(clean) || clean.includes(",")
    ? null
    : clean;
}

function line(issue) {
  const file = issue.component.slice(PROJECT.length + 1);
  const where = issue.line > 0 ? `${file}:${issue.line}` : file;
  const text = String(issue.message ?? "(no message)").replaceAll(/\s+/g, " ").trim();
  const message = text.length > MAX_MESSAGE ? `${text.slice(0, MAX_MESSAGE - 1)}…` : text;
  return `${issue.severity}  ${issue.type}  ${issue.rule}  ${where}  ${message}`;
}

const PRIVATE_HINT =
  "SonarCloud no longer shows this project to anonymous readers: it has probably gone private or been renamed. " +
  "This tool never uses a token, so ask the owner.";

export async function backlog(argv, { get = httpGet } = {}) {
  const opts = parse(argv);
  if (opts.error) return { code: 1, out: opts.error };
  let paths = null;
  if (opts.files) {
    paths = opts.files.map(repoPath);
    const outside = opts.files.filter((_, i) => paths[i] === null);
    if (outside.length) return { code: 1, out: `Not a path inside this repository: ${outside.join(" ")}` };
  }
  try {
    const project = await get(`${API}/components/show?component=${PROJECT}`);
    if (project.status !== 200 || project.body?.component?.visibility !== "public")
      return { code: 1, out: `sonar-backlog: ${PRIVATE_HINT} (components/show answered ${project.status})` };

    const query = new URLSearchParams({ resolved: "false", branch: "main", ps: String(opts.limit), p: "1" });
    if (paths) {
      query.set("componentKeys", paths.map((p) => `${PROJECT}:${p}`).join(","));
      query.set("s", "FILE_LINE");
    } else {
      query.set("componentKeys", PROJECT);
      query.set("severities", "BLOCKER,CRITICAL");
      query.set("s", "SEVERITY");
      query.set("asc", "false");
    }
    const found = await get(`${API}/issues/search?${query}`);
    if (found.status !== 200 || !Array.isArray(found.body?.issues)) {
      const msg = found.body?.errors?.map((e) => e.msg).join("; ");
      return { code: 1, out: `sonar-backlog: SonarCloud answered ${found.status}${msg ? `: ${msg}` : ""}` };
    }

    const { total, issues } = found.body;
    const scope = paths ? `in ${paths.join(", ")}` : "BLOCKER and CRITICAL";
    const analysed = String(project.body.component.analysisDate ?? "").slice(0, 16).replace("T", " ");
    const out = [`SonarCloud, main branch, last analysed ${analysed || "(unknown)"} UTC: ${total} open issues ${scope}`];
    if (total === 0 && paths)
      out.push("A file SonarCloud has not analysed yet (new, renamed or unpushed) also shows 0.");
    out.push(...issues.map(line));
    if (total > issues.length)
      out.push(`${total - issues.length} more not shown. Narrow it with --files, or raise --limit (up to ${MAX_LIMIT}).`);
    return { code: 0, out: out.join("\n") };
  } catch (err) {
    return { code: 1, out: `sonar-backlog: could not reach SonarCloud: ${err.message}` };
  }
}

if (import.meta.main) {
  const r = await backlog(process.argv.slice(2));
  process.stdout.write(`${r.out}\n`);
  process.exit(r.code);
}
