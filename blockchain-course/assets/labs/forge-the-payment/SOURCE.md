# Vendored library: secp256k1 and Keccak-256

- File: `noble-secp256k1-keccak.js`, built 11 Nov 2026 from `@noble/curves` 2.4.0 (`secp256k1.js`) and
  `@noble/hashes` 2.4.0 (`sha3.js`), bundled and minified with esbuild into one script that sets `NobleSecp`.
  Entry file: `import { secp256k1 } from "@noble/curves/secp256k1.js"; import { keccak_256 } from "@noble/hashes/sha3.js";
  globalThis.NobleSecp = { secp256k1, keccak_256 };`
- Source: https://github.com/paulmillr/noble-curves and https://github.com/paulmillr/noble-hashes
- Licence: MIT, Copyright (c) 2022 Paul Miller: `LICENSE-noble.txt` (both packages carry the same text)
- SHA-256 of `noble-secp256k1-keccak.js`: `a3f88e879d35f67a1bbc5a305d13ae27f1f66535b73c48475aec854d4404b760`
- SHA-256 of `LICENSE-noble.txt`: `9bb5bcb5a2a3c859de55b1a0534b4085c2b0e13c3f2be98d1b369f1b052a35d0`
- The lab runs from a plain file with no network. To update, rebuild the bundle from newer releases and update the
  hashes here.
