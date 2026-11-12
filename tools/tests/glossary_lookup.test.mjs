// The slides' glossary lookup: its pure parts, and the terms.json it reads
// (blockchain-course/_extensions/aci/_extensions/glossary-lookup/glossary-lookup.js).
// Run: node --test tools/tests/glossary_lookup.test.mjs (test_glossary_lookup.py runs it inside the python suite).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const G = require("../../blockchain-course/_extensions/aci/_extensions/glossary-lookup/glossary-lookup.js");
const TERMS = new URL("../../blockchain-course/glossary/terms.json", import.meta.url);

const term = (display, definition = "", aliases = []) => ({ display, definition, aliases, source: {} });
const names = (found) => found.names.map((t) => t.display);
const defs = (found) => found.definitions.map((t) => t.display);

test("normalize folds case, accents, curly quotes and spaces", () => {
  assert.equal(G.normalize("  Café  ‘Proof’\n of   Work "), "cafe 'proof' of work");
  assert.equal(G.normalize(undefined), "");
});

test("variants add the singular of the last word", () => {
  assert.deepEqual(G.variants("Transactions"), ["transactions", "transaction"]);
  assert.deepEqual(G.variants("privacy coins"), ["privacy coins", "privacy coin"]);
  assert.ok(G.variants("addresses").includes("address"));
  assert.ok(G.variants("bounties").includes("bounty"));
  assert.deepEqual(G.variants("hash"), ["hash"]);   // no trailing s
  assert.deepEqual(G.variants("gas"), ["gas"]);     // too short to be a plural
  assert.deepEqual(G.variants("address"), ["address"]); // -ss is not a plural
  assert.deepEqual(G.variants("a"), []);            // too short to search
});

test("names rank exact, then starts-with, then word-start, then contains; display beats alias", () => {
  const index = G.buildIndex([
    term("Sidechain"),
    term("Chain split"),
    term("Hard fork", "", ["chain"]),
    term("Chain"),
    term("Cross-chain bridge"),
  ]);
  assert.deepEqual(names(G.search(index, "chain")),
    ["Chain", "Hard fork", "Chain split", "Cross-chain bridge", "Sidechain"]);
});

test("definition matches are a second group, word starts only, without the named terms", () => {
  const index = G.buildIndex([
    term("Mixer", "Pools funds to break links."),
    term("CoinJoin", "A collaborative transaction; unlike a mixer, no custodian."),
    term("Remixer", "Not related."),
    term("Tumbler", "Another word for a mixer service."),
    term("Premixed", "Contains premixer, which is not a word start."),
  ]);
  const found = G.search(index, "mixer");
  assert.deepEqual(names(found), ["Mixer", "Remixer"]);
  assert.deepEqual(defs(found), ["CoinJoin", "Tumbler"]);
});

test("a plural query finds the singular term", () => {
  const index = G.buildIndex([term("Mixer"), term("Address", "", ["addr"])]);
  assert.deepEqual(names(G.search(index, "mixers")), ["Mixer"]);
  assert.deepEqual(names(G.search(index, "addresses")), ["Address"]);
});

test("a query shorter than two characters finds nothing", () => {
  const index = G.buildIndex([term("X", "x marks it")]);
  assert.deepEqual(G.search(index, "x"), { names: [], definitions: [] });
});

test("regex characters in a query are literal", () => {
  const index = G.buildIndex([term("C++ smart contract"), term("Other", "uses (c++) code"), term("Cxx", "cxx")]);
  const found = G.search(index, "c++");
  assert.deepEqual(names(found), ["C++ smart contract"]);
  assert.deepEqual(defs(found), ["Other"]); // "+" is not "any number of c"
});

test("siteRoot is the folder above lessons/, or the page's own folder", () => {
  assert.equal(G.siteRoot("https://x.github.io/repo/lessons/forensics/06-FO-mixers.html?v=1#/s"),
    "https://x.github.io/repo/");
  assert.equal(G.siteRoot("http://127.0.0.1:8793/lessons/introduction/01-IN-course_welcome.html"),
    "http://127.0.0.1:8793/");
  assert.equal(G.siteRoot("http://127.0.0.1:8793/glossary/index.html"), "http://127.0.0.1:8793/glossary/");
});

test("highlighter marks the longest variant first, case-blind", () => {
  assert.deepEqual("Mixers and a mixer".match(G.highlighter("mixers")), ["Mixers", "mixer"]);
  assert.equal(G.highlighter("a"), null);
});

test("terms.json has what the panel reads", () => {
  const data = JSON.parse(readFileSync(TERMS, "utf-8"));
  assert.ok(Array.isArray(data.terms) && data.terms.length > 0, "terms.json has no terms");
  const broken = data.terms.filter((t) => !t.display || typeof t.definition !== "string"
    || !Array.isArray(t.aliases || []) || !/^\.\.\/lessons\/[^#]+\.html#\/.+/.test(t.source?.href || ""));
  assert.deepEqual(broken.map((t) => t.display), [], "terms without a name, definition or teaching-slide link");
  const index = G.buildIndex(data.terms);
  assert.equal(G.search(index, "mixers").names[0].display, "Mixer");
});
