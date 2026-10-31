// Runs the wallet page's own derivation code (gateway/static/wallet/derive.js) in node and compares every key,
// address and descriptor it produces with the frozen chain's facts.json. run.sh runs it in node:22-alpine.
//   node regression-tests/automated/wallet/derive_check.cjs   (from dynamic-labs/)
const assert = require("node:assert/strict");
const path = require("node:path");
const lab = path.join(__dirname, "..", "..", "..", "wallet");
const ethers = require(path.join(lab, "gateway/static/vendor/ethers/ethers.umd.min.js"));
const derive = require(path.join(lab, "gateway/static/wallet/derive.js"))(ethers);
const facts = require(path.join(lab, "quizes/facts.json"));

const PHRASES = {
  A: "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
  B: "legal winner thank year wave sausage worth useful legal winner thank yellow",
  C: "letter advice cage absurd amount doctor acoustic avoid letter advice cage above",
};
let checks = 0;
const eq = (actual, expected, what) => { assert.equal(actual, expected, what); checks++; };

const dana = derive.single(PHRASES.A, "", 24, 2);
eq(dana.xpub, facts.dana.xpub, "Dana's account xpub");
for (const [i, addr] of Object.entries(facts.dana.receiving)) eq(dana.receiving[i].address, addr, `receiving ${i}`);
for (const [i, addr] of Object.entries(facts.dana.change)) eq(dana.change[i].address, addr, `change ${i}`);
// BIP 84's published test vectors for this phrase.
eq(dana.zpub, "zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD9xYYfG1m4wAcvPhXNfE3EfH1r1ADqtfSdVCToUG868RvUUkgDKf31mGDtKsAYz2oz2AGutZYs", "BIP 84 zpub");
eq(dana.receiving[0].address, "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu", "BIP 84 first receiving address");
eq(dana.change[0].address, "bc1q8c6fshw2dlwun7ekn9qwf37cu2rn755upcp6el", "BIP 84 first change address");
// A passphrase makes a different wallet.
assert.notEqual(derive.single(PHRASES.A, "TREZOR", 1, 0).receiving[0].address, dana.receiving[0].address); checks++;
assert.throws(() => derive.single(PHRASES.A.replace("about", "above"), "", 1, 0), "a bad checksum is refused"); checks++;

const keys = ["A", "B", "C"].map((k) => derive.key48(PHRASES[k], ""));
["A", "B", "C"].forEach((k, n) => {
  eq(keys[n].fingerprint, facts.treasury.keys[k].fingerprint, `key ${k} fingerprint`);
  eq(keys[n].xpub, facts.treasury.keys[k].xpub, `key ${k} xpub`);
});
const recv = derive.multisig(keys, 0, 0);
eq(recv.address, facts.treasury.receiving0, "treasury receiving 0");
eq(recv.descriptor, facts.treasury.descriptor, "treasury descriptor and checksum");
eq(derive.multisig(keys, 1, 0).address, facts.treasury.change0, "treasury change 0");
console.log(`derive_check: ${checks} checks passed`);
