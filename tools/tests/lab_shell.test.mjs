// The prediction-lab shell's pure parts (blockchain-course/assets/labs/shared/shell.js).
// Run: node --test tools/tests/lab_shell.test.mjs (test_lab_shared.py runs it inside the python suite).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const LabShell = require("../../blockchain-course/assets/labs/shared/shell.js");

const good = () => ({
  id: "make-change",
  title: "Make change",
  slide: { title: "A slide", href: "/lessons/x.html#/a-slide" },
  steps: {
    case: { html: "<p>case</p>" },
    commit: { question: "q?", choices: ["a", "b"] },
    do: { render() {} },
    name: { term: "change", parts: "change", plain: "plain" },
    explorer: { html: "<p>x</p>" },
    twist: { html: "<p>t</p>", question: "q?", choices: ["a", "b"], answer: 1, why: "w" },
    tell: { prompt: "<p>p</p>" },
  },
});

test("the seven steps, in the review's order", () => {
  assert.deepEqual(LabShell.STEPS.map((s) => s.key), ["case", "commit", "do", "name", "explorer", "twist", "tell"]);
});

test("a complete config has no problems", () => {
  assert.deepEqual(LabShell.validate(good()), []);
});

test("a missing step is named", () => {
  const c = good();
  delete c.steps.twist;
  assert.ok(LabShell.validate(c).some((p) => p.startsWith("steps.twist")));
});

test("an unknown step is refused", () => {
  const c = good();
  c.steps.quiz = {};
  assert.ok(LabShell.validate(c).some((p) => p.includes("not one of the seven")));
});

test("one new term per step", () => {
  const c = good();
  c.steps.name.term = "nonce, hash";
  assert.ok(LabShell.validate(c).some((p) => p.includes("one new term")));
});

test("a term needs its parts", () => {
  const c = good();
  delete c.steps.name.parts;
  assert.ok(LabShell.validate(c).some((p) => p.includes("needs parts")));
});

test("the twist's answer must be one of its choices", () => {
  const c = good();
  c.steps.twist.answer = 2;
  assert.ok(LabShell.validate(c).some((p) => p.includes("answer must index")));
});

test("a question needs two choices", () => {
  const c = good();
  c.steps.commit.choices = ["only"];
  assert.ok(LabShell.validate(c).some((p) => p.startsWith("steps.commit")));
});

test("a bad id is refused", () => {
  const c = good();
  c.id = "Make Change";
  assert.ok(LabShell.validate(c).some((p) => p.startsWith("id")));
});

test("verdict: held, missed, a costly miss at High, and no single outcome", () => {
  assert.deepEqual(LabShell.verdict({ choice: 1, conf: "low" }, 1), { held: true, costly: false });
  assert.deepEqual(LabShell.verdict({ choice: 0, conf: "moderate" }, 1), { held: false, costly: false });
  assert.deepEqual(LabShell.verdict({ choice: 0, conf: "high" }, 1), { held: false, costly: true });
  assert.deepEqual(LabShell.verdict({ choice: 0, conf: "high" }, null), { held: null, costly: false });
});

test("confidence words are whole words", () => {
  assert.equal(LabShell.findConfidence("Moderate confidence: it is change."), "moderate");
  assert.equal(LabShell.findConfidence("HIGH"), "high");
  assert.equal(LabShell.findConfidence("a slow, highly likely payment"), null);
  assert.equal(LabShell.findConfidence(""), null);
});

test("short() keeps both ends of a long value", () => {
  assert.equal(LabShell.short("3f9a1c0d77b2e8f1c4a9e04b"), "3f9a1c…a9e04b");
  assert.equal(LabShell.short("abc"), "abc");
});
