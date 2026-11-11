/* Shared by the team page and the instructor page of "Hide and trace" (docs/lab-cards/hide-and-trace.md):
   small DOM helpers, the API call, and the reveal (each team's move log beside the calls on its trail, the scores
   and the class table). The pages hold no answer: the server sends the move logs only after the reveal opens. */
var HT = (function () {
  "use strict";
  var EXPLORER = "/labs/hide-and-trace/mempool";

  function el(tag, attrs) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "text") n.textContent = attrs[k];
      else if (attrs[k] !== null && attrs[k] !== undefined && attrs[k] !== false) n.setAttribute(k, attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c === null || c === undefined || c === false) continue;
      if (Array.isArray(c)) c.forEach(function (x) { if (x) n.appendChild(typeof x === "string" ? document.createTextNode(x) : x); });
      else n.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
    }
    return n;
  }

  function api(path, opts, headers) {
    opts = opts || {};
    var h = Object.assign({ "Content-Type": "application/json" }, headers || {});
    return fetch(path, { method: opts.method || "GET", headers: h, credentials: "same-origin",
                         body: opts.body ? JSON.stringify(opts.body) : undefined })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (data) {
          if (!r.ok) throw new Error(data.error || ("The game server said " + r.status + "."));
          return data;
        });
      });
  }

  function btc(sats) { return (sats / 1e8).toFixed(8).replace(/0{1,4}$/, "") + " BTC"; }
  function short(s) { s = String(s || ""); return s.length > 20 ? s.slice(0, 10) + "…" + s.slice(-6) : s; }
  function txOf(outpoint) { return String(outpoint).split(":")[0]; }

  function txLink(txid, label) {
    return el("a", { href: EXPLORER + "/tx/" + txid, target: "_blank", rel: "noopener", class: "hash" }, label || short(txid));
  }
  function outLink(outpoint) {
    var p = String(outpoint).split(":");
    return el("a", { href: EXPLORER + "/tx/" + p[0] + "#vout=" + p[1], target: "_blank", rel: "noopener", class: "hash" },
      short(p[0]) + ":" + p[1]);
  }
  function addrLink(a) {
    return el("a", { href: EXPLORER + "/address/" + a, target: "_blank", rel: "noopener", class: "addr" }, short(a));
  }
  function word(w) {
    if (!w) return el("span", null, "struck: no reason");
    if (w === "undetermined") return el("span", null, "Undetermined");
    return el("span", { class: "conf", "data-level": w }, w.charAt(0).toUpperCase() + w.slice(1));
  }

  var MOVE_NAMES = { peel: "Peel", split: "Split", merge: "Merge", wait: "Wait", coinjoin: "CoinJoin",
                     mixer: "Mixer", cashout: "Cash out", deadline: "Deadline deposit" };

  function moveRow(m) {
    var outs = (m.outputs || []).map(function (o) { return el("div", null, outLink(o.outpoint), " ", btc(o.sats)); });
    (m.payouts || []).forEach(function (o) { outs.push(el("div", null, "paid out: ", outLink(o.outpoint), " ", btc(o.sats))); });
    return el("tr", null,
      el("td", null, m.n ? String(m.n) : "–"),
      el("td", null, "block " + m.game_block),
      el("td", null, MOVE_NAMES[m.kind] || m.kind),
      el("td", null, m.txid ? txLink(m.txid) : "no transaction", m.payout_txid ? el("div", null, "payout ", txLink(m.payout_txid)) : null),
      el("td", null, outs.length ? outs : "–"),
      el("td", null, m.note || ""));
  }

  function moveTable(moves, caption) {
    return el("table", { class: "class-table" }, caption ? el("caption", null, caption) : null,
      el("thead", null, el("tr", null, ["Move", "When", "What", "Transaction", "Coins made", "Note"].map(function (h) { return el("th", null, h); }))),
      el("tbody", null, moves.map(moveRow)));
  }

  function reasonText(c) {
    return (c.reasons || []).map(function (r) {
      var dropped = (c.dropped || []).some(function (d) { return d.kind === r.kind && d.txid === r.txid; });
      return el("div", null, r.kind + " in ", txLink(r.txid), dropped ? " (not counted: a CoinJoin's inputs are many people's)" : "");
    });
  }

  function callTable(calls, caption, showTracer) {
    var head = (showTracer ? ["Tracer", "Target"] : []).concat(["Output", "Said", "Scored as", "Reasons", "Owner", "Points"]);
    return el("table", { class: "class-table" }, caption ? el("caption", null, caption) : null,
      el("thead", null, el("tr", null, head.map(function (h) { return el("th", null, h); }))),
      el("tbody", null, calls.map(function (c) {
        var right = c.word === "undetermined" ? null : c.right;
        return el("tr", { class: c.struck ? "struck" : null },
          showTracer ? el("td", null, c.tracer) : null,
          showTracer ? el("td", null, c.target) : null,
          el("td", null, outLink(c.outpoint)),
          el("td", null, word(c.word)),
          el("td", null, c.struck ? "struck: no reason" : word(c.capped),
             !c.struck && c.capped && c.capped !== c.word ? el("div", null, "(capped: the reasons allow no more)") : null),
          el("td", null, reasonText(c), c.note ? el("div", null, "“" + c.note + "”") : null),
          el("td", { class: right === null ? null : (right ? "right" : "wrong") },
             right === null ? "–" : (right ? "right: the target's" : "wrong: not the target's")),
          el("td", null, String(c.points)));
      })));
  }

  function renderReveal(box, rv) {
    box.innerHTML = "";
    box.appendChild(el("h2", null, "The reveal"));
    box.appendChild(el("table", { class: "class-table" }, el("caption", null, "Scores (time breaks ties only)"),
      el("thead", null, el("tr", null, el("th", null, "Place"), el("th", null, "Team"), el("th", null, "Calls"), el("th", null, "Points"))),
      el("tbody", null, rv.scores.map(function (s, i) {
        return el("tr", null, el("td", null, String(i + 1)), el("td", null, s.team), el("td", null, String(s.calls)), el("td", null, String(s.score)));
      }))));

    var c = rv.counts;
    box.appendChild(el("h3", null, "The class table: every High call"));
    box.appendChild(el("p", null, "High calls: " + c.high + ". High calls on amount or timing alone: " + c.amount_or_timing_alone +
      ", and " + c.amount_or_timing_alone_wrong + " of them wrong."));
    if (rv.class_table.length) {
      var groups = {};
      rv.class_table.forEach(function (h) { (groups[h.evidence] = groups[h.evidence] || []).push(h); });
      Object.keys(groups).sort().forEach(function (g) {
        box.appendChild(callTable(groups[g], "Evidence given: " + g, true));
      });
    } else {
      box.appendChild(el("p", null, "No team made a High call."));
    }

    box.appendChild(el("h3", null, "Each team's trail"));
    rv.teams.forEach(function (t) {
      var sec = el("section", { class: "lab-step" });
      sec.appendChild(el("h3", null, t.name + "'s moves, traced by " + t.traced_by));
      sec.appendChild(el("p", null, "Start: ", outLink(t.start.outpoint), " (" + btc(t.start.sats) + "). Its exchange deposit address: ", addrLink(t.deposit), "."));
      sec.appendChild(moveTable(t.moves, "The move log, from the game server"));
      sec.appendChild(t.calls.length ? callTable(t.calls, t.traced_by + "'s calls on this trail") : el("p", null, t.traced_by + " made no call on this trail."));
      if (t.stop) {
        sec.appendChild(el("p", null, "Where " + t.traced_by + " said the trace stops: ", txLink(t.stop.txid), " (" + t.stop.kind + "). ",
          t.stop.struck ? "Struck: no reason given." : (t.stop.right ? "Right: that move ended the trace (+2)." : "Not a move that ended this trail (0).")));
      }
      box.appendChild(sec);
    });
  }

  return { el: el, api: api, btc: btc, short: short, txOf: txOf, txLink: txLink, outLink: outLink, addrLink: addrLink,
           word: word, moveTable: moveTable, callTable: callTable, renderReveal: renderReveal, MOVE_NAMES: MOVE_NAMES,
           EXPLORER: EXPLORER };
})();
