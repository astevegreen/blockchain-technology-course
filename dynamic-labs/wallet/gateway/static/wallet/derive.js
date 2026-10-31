// Wallet derivation for the wallet page: seed phrase -> keys -> addresses, all in the browser.
// It takes ethers (vendor/ethers, MIT) as a parameter so the regression suite can run the same code in node
// and compare it with the frozen chain's facts.json.
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory;
  else root.walletDerive = factory;
})(this, function (ethers) {
  const BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l";

  const bytes = (hex) => ethers.getBytes(hex);
  const hex = (b) => ethers.hexlify(b).slice(2);
  const hash160 = (b) => ethers.ripemd160(ethers.sha256(b));

  // BIP 173: a version 0 witness address.
  function bech32Polymod(values) {
    const gen = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];
    let chk = 1;
    for (const v of values) {
      const top = chk >>> 25;
      chk = ((chk & 0x1ffffff) << 5) ^ v;
      for (let i = 0; i < 5; i++) if ((top >>> i) & 1) chk ^= gen[i];
    }
    return chk >>> 0;
  }
  function segwitAddress(program) {
    const hrp = "bc";
    const data = [0];
    let acc = 0, bits = 0;
    for (const b of bytes(program)) {
      acc = (acc << 8) | b;
      bits += 8;
      while (bits >= 5) { bits -= 5; data.push((acc >>> bits) & 31); }
    }
    if (bits) data.push((acc << (5 - bits)) & 31);
    const expand = [...hrp].map((c) => c.charCodeAt(0) >> 5).concat([0], [...hrp].map((c) => c.charCodeAt(0) & 31));
    const mod = bech32Polymod(expand.concat(data, [0, 0, 0, 0, 0, 0])) ^ 1;
    const check = [0, 1, 2, 3, 4, 5].map((i) => (mod >>> (5 * (5 - i))) & 31);
    return hrp + "1" + data.concat(check).map((d) => BECH32[d]).join("");
  }

  // BIP 380: the eight-character checksum after a descriptor's "#".
  function descriptorChecksum(desc) {
    const input = "0123456789()[],'/*abcdefgh@:$%{}IJKLMNOPQRSTUVWXYZ&+-.;<=>?!^_|~ijklmnopqrstuvwxyzABCDEFGH`#\"\\ ";
    const gen = [0xf5dee51989n, 0xa9fdca3312n, 0x1bab10e32dn, 0x3706b1677an, 0x644d626ffdn];
    const step = (c, v) => {
      const top = c >> 35n;
      c = ((c & 0x7ffffffffn) << 5n) ^ BigInt(v);
      for (let i = 0; i < 5; i++) if ((top >> BigInt(i)) & 1n) c ^= gen[i];
      return c;
    };
    let c = 1n, cls = 0, count = 0;
    for (const ch of desc) {
      const pos = input.indexOf(ch);
      c = step(c, pos & 31);
      cls = cls * 3 + (pos >> 5);
      if (++count === 3) { c = step(c, cls); cls = 0; count = 0; }
    }
    if (count) c = step(c, cls);
    for (let i = 0; i < 8; i++) c = step(c, 0);
    c ^= 1n;
    let out = "";
    for (let j = 0; j < 8; j++) out += BECH32[Number((c >> BigInt(5 * (7 - j))) & 31n)];
    return out;
  }

  // The same extended public key with SLIP-132 version bytes 04b24746 ("zpub", which wallets use for BIP 84).
  function zpub(xpub) {
    const raw = bytes(ethers.toBeHex(ethers.decodeBase58(xpub), 82)).slice(0, 78);
    raw.set([0x04, 0xb2, 0x47, 0x46], 0);
    const check = bytes(ethers.sha256(ethers.sha256(raw))).slice(0, 4);
    return ethers.encodeBase58(ethers.concat([raw, check]));
  }

  // BIP 39 phrase (and optional passphrase) -> BIP 32 master key. Throws on a wrong word or checksum.
  function master(phrase, passphrase) {
    const words = phrase.trim().toLowerCase().split(/\s+/).join(" ");
    const mnemonic = ethers.Mnemonic.fromPhrase(words, passphrase || "");
    return ethers.HDNodeWallet.fromSeed(mnemonic.computeSeed());
  }
  const pub = (node) => node.publicKey.slice(2);

  // BIP 84 single-signature wallet, account 0: receiving chain /0/i and change chain /1/i.
  function single(phrase, passphrase, receiving, change) {
    const root = master(phrase, passphrase);
    const path = "m/84'/0'/0'";
    const acct = root.derivePath(path);
    const list = (chain, n) => Array.from({ length: n }, (_, i) => {
      const child = acct.deriveChild(chain).deriveChild(i);
      return { index: i, path: `${path}/${chain}/${i}`, pubkey: pub(child), address: segwitAddress(hash160(child.publicKey)) };
    });
    const xpub = acct.neuter().extendedKey;
    return { fingerprint: root.fingerprint.slice(2), path, xpub, zpub: zpub(xpub),
      receiving: list(0, receiving), change: list(1, change) };
  }

  // BIP 48 multisig key for native SegWit (script type 2'), account 0.
  function key48(phrase, passphrase) {
    const root = master(phrase, passphrase);
    const path = "m/48'/0'/0'/2'";
    const node = root.derivePath(path);
    return { fingerprint: root.fingerprint.slice(2), path, xpub: node.neuter().extendedKey, node };
  }

  // 2-of-3 P2WSH with BIP 67 sorted keys: wsh(sortedmulti(2, ...)), at chain/index for every key.
  function multisig(keys, chain, index) {
    const pubkeys = keys.map((k) => pub(k.node.deriveChild(chain).deriveChild(index)));
    const sorted = [...pubkeys].sort();
    const script = "52" + sorted.map((p) => "21" + p).join("") + "53ae";
    const asm = ["OP_PUSHNUM_2", ...sorted.map((p) => "OP_PUSHBYTES_33 " + p), "OP_PUSHNUM_3", "OP_CHECKMULTISIG"].join(" ");
    const origin = (k) => `[${k.fingerprint}/48h/0h/0h/2h]${k.xpub}/${chain}/*`;
    const body = `wsh(sortedmulti(2,${keys.map(origin).join(",")}))`;
    return { pubkeys, sorted, script, asm, address: segwitAddress(ethers.sha256("0x" + script)),
      descriptor: `${body}#${descriptorChecksum(body)}` };
  }

  return { single, key48, multisig, segwitAddress, descriptorChecksum, zpub, hex };
});
