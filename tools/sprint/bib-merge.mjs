// Git merge driver for the bibliography (docs/sprint.md, Machinery): merges a .bib file entry by entry, so two
// branches that each add sources at the end of Blockchain.bib land without a conflict. Git's own `union` driver
// joins the two sides line by line, and when both end their new entry with `}` it keeps one brace for the two: the
// first entry loses its last field and its close. .gitattributes names this driver; each clone opts in once with
//   git config merge.bib.driver "node tools/sprint/bib-merge.mjs %O %A %B"
// (worktrees share the clone's config). Without that, git merges the file line by line as before.
// Writes the merge to %A and exits 0. When both sides changed or added the same entry differently, it leaves git's
// own line merge in %A, conflict markers and all, and exits 1, so the cherry-pick stops as any conflict does.
import { readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

export const DRIVER = "node tools/sprint/bib-merge.mjs %O %A %B";

// The text before the first entry, and each entry from its `@` to the next one (as tools/check.py reads them).
export function parse(text) {
  const starts = [...text.matchAll(/^@\w+\s*\{\s*([^,\s]+)\s*,/gm)];
  return {
    preamble: text.slice(0, starts[0]?.index ?? text.length),
    list: starts.map((m, i) => ({ key: m[1].toLowerCase(), text: text.slice(m.index, starts[i + 1]?.index ?? text.length) })),
  };
}

const norm = (t) => t?.trimEnd();

// The merged text, or null when the two sides changed the same thing differently. Ours keeps its order; entries
// only theirs added follow it, in their order.
export function merge(base, ours, theirs) {
  const [O, A, B] = [base, ours, theirs].map(parse);
  const maps = [O, A, B].map((p) => new Map(p.list.map((e) => [e.key, e.text])));
  // A key twice in one side: leave it to git's line merge, and to the check's duplicate-key failure.
  if (maps.some((m, i) => m.size !== [O, A, B][i].list.length)) return null;
  const [o, a, b] = maps;
  let preamble = A.preamble;
  if (norm(A.preamble) === norm(O.preamble)) preamble = B.preamble;
  else if (norm(B.preamble) !== norm(O.preamble) && norm(B.preamble) !== norm(A.preamble)) return null;

  const kept = [];
  for (const [k, at] of a) {
    const ot = o.get(k);
    const bt = b.get(k);
    if (norm(bt) === norm(at) || norm(bt) === norm(ot)) kept.push(at); // theirs left it, or made the same change
    else if (norm(at) === norm(ot)) { if (bt !== undefined) kept.push(bt); } // only theirs changed or deleted it
    else return null; // both changed it, or ours changed what theirs deleted
  }
  const added = [];
  for (const [k, bt] of b) {
    if (a.has(k)) continue;
    const ot = o.get(k);
    if (ot === undefined) added.push(bt); // theirs added it
    else if (norm(bt) !== norm(ot)) return null; // ours deleted what theirs changed
  }

  let text = preamble + kept.join("");
  for (const t of added) {
    if (text.trim()) text = text.replace(/\s*$/, "\n\n");
    text += t;
  }
  return text.endsWith("\n") || !text ? text : `${text}\n`;
}

if (import.meta.main) {
  const [base, ours, theirs] = process.argv.slice(2);
  if (!theirs) {
    process.stderr.write("usage: node tools/sprint/bib-merge.mjs <base> <ours> <theirs> (git runs it: .gitattributes)\n");
    process.exit(2);
  }
  const merged = merge(...[base, ours, theirs].map((f) => readFileSync(f, "utf8")));
  if (merged !== null) {
    writeFileSync(ours, merged);
    process.exit(0);
  }
  const r = spawnSync("git", ["merge-file", "-L", "ours", "-L", "base", "-L", "theirs", ours, base, theirs], { windowsHide: true }); // NOSONAR (javascript:S4036)
  process.exit(r.status === 0 ? 0 : 1);
}
