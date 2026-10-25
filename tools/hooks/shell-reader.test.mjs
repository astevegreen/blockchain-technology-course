// The shell reader the sprint guard reads commands with (shell-reader.mjs beside this file). YODC, Terminal Dusk
// and the blockchain course carry identical copies; shell-reader.cases.json holds the cases all three must pass.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { readCommand, Unreadable } from "./shell-reader.mjs";

const cases = JSON.parse(readFileSync(new URL("./shell-reader.cases.json", import.meta.url), "utf8"));

// What a guard sees: whether the reader refuses the line, and whether any command it runs is a git push.
function seen({ shell, command }) {
  const read = readCommand(command, shell);
  let refused = read.refusal !== null || read.gitHidden;
  let pushes = false;
  for (const part of read.parts) {
    try {
      for (const { w } of read.commandsIn(read.words(part))) {
        if (w[0] === "git" && w.includes("push") && !w.includes("stash")) pushes = true;
      }
    } catch (e) {
      if (!(e instanceof Unreadable)) throw e;
      refused = true;
    }
  }
  return { refused, pushes };
}
const label = (c) => `[${c.shell}] ${c.command.replace(/\n/g, "\\n")}`;

for (const c of cases.push) test(`sees the push in ${label(c)}`, () => {
  const { refused, pushes } = seen(c);
  assert.ok(refused || pushes);
});
for (const c of cases.refused) test(`refuses ${label(c)}`, () => assert.ok(seen(c).refused));
for (const c of cases.clean) test(`reads ${label(c)} as no push`, () => assert.deepEqual(seen(c), { refused: false, pushes: false }));
for (const c of cases.reads) test(`reads the words of ${label(c)}`, () => {
  const read = readCommand(c.command, c.shell);
  if (c.textReadHas) assert.ok(read.textRead.includes(c.textReadHas), read.textRead);
  if (c.textLacks) assert.ok(!read.text.includes(c.textLacks), read.text);
  if (c.literalsLack) assert.ok(!read.literalsBlank.includes(c.literalsLack), read.literalsBlank);
  if (c.literalsHas) assert.ok(read.literalsBlank.includes(c.literalsHas), read.literalsBlank);
  if (c.at) assert.equal(read.commandsIn(read.words(read.parts[0] ?? ""))[0]?.at, c.at);
});
