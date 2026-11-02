// Optional flag self-check for the week-2 labs (one identical copy per lab).
// A flag form holds only the SHA-256 of "course-flag:" + the flag in canonical form, never the flag itself:
//   <form class="flag" data-kind="address|amount" data-decimals="8" data-sha256="..."> <input> <button> <output>
// Canonical form: spaces, commas, underscores and quotes removed. An amount drops a leading sign ($, ~) and a
// trailing unit word (BTC, USDT, ETH), and is rounded half up to data-decimals places. An address that starts
// 0x, bc1, tb1 or bcrt1 is lowercased; a base58 address (1..., 3..., T...) is kept as typed.
// Nothing is sent anywhere and nothing is graded.
// SHA-256 is written out here because crypto.subtle is missing on a plain-HTTP page.
(function () {
  "use strict";

  var K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }

  function sha256(text) {
    var bytes = Array.from(new TextEncoder().encode(text));
    var bitLength = bytes.length * 8;
    bytes.push(0x80);
    while (bytes.length % 64 !== 56) { bytes.push(0); }
    for (var s = 56; s >= 0; s -= 8) { bytes.push(s >= 32 ? 0 : (bitLength >>> s) & 0xff); }
    var h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var w = new Array(64);
    for (var off = 0; off < bytes.length; off += 64) {
      for (var i = 0; i < 16; i++) {
        var j = off + i * 4;
        w[i] = (bytes[j] << 24) | (bytes[j + 1] << 16) | (bytes[j + 2] << 8) | bytes[j + 3];
      }
      for (i = 16; i < 64; i++) {
        var s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
        var s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0;
      }
      var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], k = h[7];
      for (i = 0; i < 64; i++) {
        var t1 = (k + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) | 0;
        var t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) | 0;
        k = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      h = [h[0] + a, h[1] + b, h[2] + c, h[3] + d, h[4] + e, h[5] + f, h[6] + g, h[7] + k].map(function (v) { return v | 0; });
    }
    return h.map(function (v) { return ("0000000" + (v >>> 0).toString(16)).slice(-8); }).join("");
  }

  // "0.5" with 8 places -> "0.50000000"; "1234.5678" with 2 -> "1234.57"; null if not a number.
  function amount(text, decimals) {
    var m = /^(\d*)(?:\.(\d*))?$/.exec(text.replace(/^[^\d.]+/, "").replace(/[a-z]+$/i, ""));
    if (!m || (m[1] + (m[2] || "")) === "") { return null; }
    var frac = ((m[2] || "") + "0".repeat(decimals + 1)).slice(0, decimals + 1);
    var digits = ((m[1] || "0") + frac.slice(0, decimals)).split("").map(Number);
    if (frac[decimals] >= "5") {
      var i = digits.length - 1;
      while (i >= 0 && digits[i] === 9) { digits[i] = 0; i--; }
      if (i < 0) { digits.unshift(1); } else { digits[i] += 1; }
    }
    var whole = digits.slice(0, digits.length - decimals).join("").replace(/^0+(?=\d)/, "");
    return decimals ? whole + "." + digits.slice(digits.length - decimals).join("") : whole;
  }

  function canonical(raw, kind, decimals) {
    var text = raw.replace(/[\s,_"'`]/g, "");
    if (kind === "amount") { return amount(text, decimals); }
    return /^(0x|bc1|tb1|bcrt1)/i.test(text) ? text.toLowerCase() : text;
  }

  document.querySelectorAll("form.flag").forEach(function (form) {
    var input = form.querySelector("input");
    var result = form.querySelector("output");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var value = canonical(input.value, form.dataset.kind, Number(form.dataset.decimals || 0));
      if (!input.value.trim()) { result.textContent = ""; return; }
      if (value === null) { result.textContent = "Not an amount: type digits, with a decimal point if needed."; return; }
      var right = sha256("course-flag:" + value) === form.dataset.sha256;
      result.textContent = right ? "Correct: that is the flag." : "Not the flag. Check the hop or the row and try again.";
      result.className = right ? "flag-right" : "flag-wrong";
    });
  });

  window.courseFlag = { sha256: sha256, canonical: canonical };
}());
