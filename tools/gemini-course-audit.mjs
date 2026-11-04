// Gemini's adversarial audit of the whole course, run headless through agy, one scope at a time:
//   node tools/gemini-course-audit.mjs                 every day, then the assessments, then the synthesis
//   node tools/gemini-course-audit.mjs --only d3 ...   just the scopes named (d1..d10, assessments, README)
//   node tools/gemini-course-audit.mjs --force         redo scopes whose report already exists
//   node tools/gemini-course-audit.mjs --dry           list each scope's files and material size; call no model
// Reports go to docs/analysis/gemini-audit/. A scope whose report exists is skipped, so a stopped run restarts
// where it left off. Headless agy can read files but run no command, and each read costs about 20 seconds, so
// each scope gets one material file holding everything it needs, line-numbered for `path:line` citations.
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FLASH, askFirstAvailable, askModel, buildPrompt, modelName } from "./agy.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "docs", "analysis", "gemini-audit");
const RUN_SHEET = "quizes/run-sheet/RUN_SHEET.md";
// Flash only: the owner's default for Gemini, and a Claude model answering would not be Gemini's view.
const MODELS = [FLASH];

const read = (rel) => readFileSync(path.join(ROOT, rel), "utf8").replace(/\r\n/g, "\n");
const isFile = (rel) => existsSync(path.join(ROOT, rel)) && !rel.endsWith("/");

function run(cmd, args) {
  return spawnSync(cmd, args, {
    cwd: ROOT,
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 64 * 1024 * 1024,
    timeout: 11 * 60_000,
  });
}

// A file as `path:line| text`, with hidden slides (pandoc divs carrying .content-hidden) left out.
function numbered(rel) {
  const lines = read(rel).split("\n");
  const out = [];
  let depth = 0;
  lines.forEach((text, i) => {
    if (depth === 0 && /^:{3,}\s*\{[^}]*\.content-hidden/.test(text)) depth = 1;
    else if (depth > 0) {
      if (/^:{3,}\s*\S/.test(text)) depth++;
      else if (/^:{3,}\s*$/.test(text)) depth--;
    } else out.push(`${rel}:${i + 1}| ${text}`);
  });
  return `\n## File: ${rel}\n\n${out.join("\n")}\n`;
}

// A quiz bank cut to the fields a reviewer needs, one item per block, cited by bank and item id.
function bank(rel) {
  const data = JSON.parse(read(rel));
  const items = Array.isArray(data) ? data : (data.questions ?? Object.values(data).find(Array.isArray) ?? []);
  const keep = ["id", "day", "concept", "question_type", "question_stem", "correct_answer", "incorrect_answers",
    "explanation", "difficulty_level", "lesson_block", "specific_source"];
  const lines = items.map((q) =>
    keep.filter((k) => q[k] !== undefined && q[k] !== null && q[k] !== "")
      .map((k) => `${k}: ${typeof q[k] === "string" ? q[k] : JSON.stringify(q[k])}`).join("\n"));
  return `\n## Bank: ${rel} (${items.length} items; cite as ${path.basename(rel)} <id>)\n\n${lines.join("\n\n")}\n`;
}

// The run sheet's opening (the day's shape, marking) and each day's section.
function runSheet() {
  const text = read(RUN_SHEET);
  const parts = text.split(/^(?=## Day \d+)/m);
  const days = {};
  for (const p of parts.slice(1)) days[Number(/^## Day (\d+)/.exec(p)[1])] = p.split(/^## (?!Day)/m)[0];
  return { intro: parts[0], days };
}

// Every repo file a day's run-sheet section names, plus each started lab's student pages.
function dayFiles(n, section) {
  const named = [...section.matchAll(/`([^`\s]+\.(?:qmd|md|html))`/g)].map((m) => m[1]).filter(isFile);
  const labs = [...section.matchAll(/lab-manager\.sh start ([\w-]+)/g)].map((m) => m[1]);
  const pages = [];
  for (const lab of labs) {
    const walk = (dir) => {
      if (!existsSync(path.join(ROOT, dir))) return;
      for (const e of readdirSync(path.join(ROOT, dir), { withFileTypes: true })) {
        const rel = `${dir}/${e.name}`;
        if (e.isDirectory() && !["node_modules", "runtime", "fallback"].includes(e.name)) walk(rel);
        else if (/\/static\/lab\/(?:[\w-]+\/)?index\.html$/.test(rel)) pages.push(rel);
      }
    };
    walk(`dynamic-labs/${lab}`);
  }
  // The Tron lab serves day 5 and day 9: give each day only its own page.
  const own = pages.filter((p) => (n === 9 ? !p.includes("/tron/") || p.includes("/d9/") : !p.includes("/d9/")));
  return [...new Set([...named, ...own])];
}

const frame = (intro, extra) =>
  `# Material\n\n## File: CLAUDE.md (the owner's rules)\n\n${read("CLAUDE.md")}\n` +
  `\n## File: docs/quality-rubric.md (the adopted rubric)\n\n${read("docs/quality-rubric.md")}\n` +
  `\n## File: ${RUN_SHEET} (opening)\n\n${intro}\n${extra}`;

const REPORT = (id, title, lines) => `Write the report in Markdown, under ${lines} lines, starting with the line
"# ${title}". Sections, in order:
1. **Verdict**: two or three sentences.
2. **Scorecard**: a table with one row per lesson, lab or bank in the material: file, Sound, Shaky or Failing, and
   the finding IDs behind it.
3. **Findings**: a table with columns ID (${id}-1, ${id}-2…), Severity, Type, Lens, Finding (one sentence),
   Evidence, Why it matters to students, Smallest fix. Order by severity.
4. **What holds up**: up to five things you attacked and could not break, a line each.
5. **Patterns to check elsewhere**: weaknesses you expect on other days, a line each.
6. **Could not check**: what you would need to settle each unverified finding.`;

function scopes() {
  const { intro, days } = runSheet();
  const list = [];
  for (const [n, section] of Object.entries(days)) {
    const title = /^## (Day \d+: .*)$/m.exec(section)[1];
    const files = dayFiles(Number(n), section);
    list.push({
      name: `d${n}`,
      material: () => frame(intro, `\n## File: ${RUN_SHEET} (${title})\n\n${section}\n`) + files.map(numbered).join(""),
      task: `Your scope is ${title}: its lessons, its lab and anything else the run sheet section names, all in the
material. Students have had days 1 to ${Number(n) - 1} before it. Judge every lens but 5 here; the assessments get
their own audit.\n\n${REPORT(`D${n}`, title, 140)}`,
    });
  }
  const banks = [
    ...readdirSync(path.join(ROOT, "quizes/quiz_json")).filter((f) => /^(daily_|weekone).*\.json$/.test(f))
      .map((f) => `quizes/quiz_json/${f}`),
    "quizes/pretest/pretest_week1-quiz-bank.json",
    "quizes/pretest/pretest_week2-quiz-bank.json",
    "quizes/posttest/posttest_day10-quiz-bank.json",
  ].filter(isFile);
  list.push({
    name: "assessments",
    material: () => frame(intro, "") + numbered("docs/alignment-map.md").split("\n").slice(0, 400).join("\n") +
      numbered("quizes/challenge/challenge-bank.md") + banks.map(bank).join(""),
    task: `Your scope is the course's assessments: every daily quiz bank, the week-one check, both pretests, the
post-test and the challenge bank, plus the alignment map's opening (the 42 Role Concepts, each concept's level and
where it is taught and tested). Lab graded points are marked by the run sheet's rules, in its opening. Judge lens 5
above all, and lens 2 and 3 where an item's stem or key shows it. Also judge: is every Role Concept tested at its
level, and could a student earn the certificate while missing a whole outcome?\n\n${REPORT("A", "Assessments", 140)}`,
  });
  list.push({
    name: "README",
    needsAll: true,
    material: () => {
      const mine = readdirSync(OUT).filter((f) => f.endsWith(".md") && f !== "README.md").sort((a, b) =>
        a.localeCompare(b, "en", { numeric: true }));
      const claude = ["docs/analysis/pattern-audit/README.md", "docs/analysis/pattern-audit/week1.md"].filter(isFile);
      return `# Material\n\n# Part 1: your audit, scope by scope\n${mine.map((f) =>
        `\n## Report: docs/analysis/gemini-audit/${f}\n\n${read(`docs/analysis/gemini-audit/${f}`)}`).join("\n")}` +
        `\n\n# Part 2: Claude's separate audit (read only for section 6)\n${claude.map(numbered).join("")}`;
    },
    task: `You audited this course scope by scope; your reports are Part 1 of the material. Write the synthesis,
in Markdown, under 220 lines, starting with "# Gemini's adversarial audit: synthesis". Sections, in order:
1. **Verdict**: will this course, as built, produce the promised graduate? What is the biggest reason it might
   not? Three sentences at most.
2. **Top ten**: the findings that matter most across the course, by their report IDs, one line each.
3. **Course scorecard**: one row per day and one for the assessments: Sound, Shaky or Failing, and why in a few
   words.
4. **Patterns**: each weakness seen in two or more scopes, ranked by how much it costs a first-time student, with
   the IDs that show it and one proposed course-wide fix each.
5. **What holds up**: up to ten things, a line each.
6. **Where I disagree with Claude's audit** (Part 2; it covers week 2, and week 1 if present): your findings it
   missed, its marks or patterns you think are wrong, with your evidence, and anything it rates far higher or lower
   than you do. Do not change your findings to match it.
7. **Could not check**: the evidence that would settle the unverified findings.
Use only the reports' findings; read no lesson for this.`,
  });
  return list;
}

function main() {
  const args = process.argv.slice(2);
  const force = args.includes("--force");
  const dry = args.includes("--dry");
  const only = args.includes("--only") ? args.slice(args.indexOf("--only") + 1).filter((a) => !a.startsWith("--")) : null;
  mkdirSync(OUT, { recursive: true });
  const head = run("git", ["rev-parse", "--short", "HEAD"]).stdout.trim();
  const prompt = readFileSync(path.join(ROOT, "tools", "gemini-course-audit.md"), "utf8");
  const tmp = mkdtempSync(path.join(os.tmpdir(), "gemini-course-audit-"));
  let failed = 0;
  try {
    const list = scopes();
    for (const scope of list) {
      if (only && !only.includes(scope.name)) continue;
      const out = path.join(OUT, `${scope.name}.md`);
      if (existsSync(out) && !force) {
        console.log(`${scope.name}: exists, skipped`);
        continue;
      }
      const missing = list.filter((s) => s !== scope && !existsSync(path.join(OUT, `${s.name}.md`)));
      if (scope.needsAll && missing.length && !dry) {
        failed++;
        console.log(`${scope.name}: waits for ${missing.map((s) => s.name).join(", ")}; run again once they exist`);
        continue;
      }
      const material = path.join(tmp, `${scope.name}-material.md`);
      writeFileSync(material, scope.material());
      if (dry) {
        const text = readFileSync(material, "utf8");
        const files = [...text.matchAll(/^## (?:File|Bank|Report): (\S+)/gm)].map((m) => m[1]);
        console.log(`${scope.name}: ${Math.round(text.length / 1024)} KB: ${files.join(", ")}`);
        continue;
      }
      const started = Date.now();
      try {
        const answer = askFirstAvailable(MODELS, (model) =>
          askModel((a) => run("agy", a), buildPrompt(`${prompt}\n\n## Your task\n\n${scope.task}`, material), model,
            ["--add-dir", tmp]));
        const stamp = `> Gemini's adversarial audit: ${modelName(answer.model)}, ${new Date().toISOString().slice(0, 10)}, ` +
          `on ${head}, by \`node tools/gemini-course-audit.mjs\`. Its findings are inputs to check, not verified facts.\n\n`;
        writeFileSync(out, stamp + answer.response.replace(/\r\n/g, "\n") + "\n");
        console.log(`${scope.name}: written (${Math.round((Date.now() - started) / 1000)} s)`);
      } catch (err) {
        failed++;
        console.log(`${scope.name}: FAILED, retry later: ${err.message}`);
      }
    }
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
  process.exit(failed ? 1 : 0);
}

main();
