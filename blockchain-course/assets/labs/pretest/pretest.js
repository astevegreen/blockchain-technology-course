/* The pretest page: shows the items in items.js, keeps the answers in this browser, and sends them to the
 * instructor as a block of text (email, copy or download). The page never knows the answers: the instructor
 * marks the block with quizes/pretest/mark_pretest.py, which reads the block format written by answerText below.
 *
 * The link from the joining instructions may end in a fragment: #to=<instructor email>, and &week=1 (or 2) to
 * show one week's items. A fragment never leaves the browser, so the address is not sent to the site.
 * Works offline and from a plain file: a classic script, no modules, no network.
 */
(function (root) {
  "use strict";

  var BEGIN = "----- BEGIN PRETEST ANSWERS -----";
  var END = "----- END PRETEST ANSWERS -----";
  var STORE_KEY = "bia-pretest-v1";
  var MAILTO_MAX = 1800; // some mail programs drop a longer mailto link
  var EMAIL = /^[^\s@<>"',;]+@[^\s@<>"',;]+\.[^\s@<>"',;]+$/;

  // ---------- Pure helpers (tested in tools/tests/test_pretest_page.py, through node) ----------

  /** The link's fragment: { to: an email address or "", week: 1, 2 or null }. */
  function readFragment(hash) {
    var out = { to: "", week: null };
    String(hash || "").replace(/^#/, "").split("&").forEach(function (pair) {
      var at = pair.indexOf("=");
      if (at < 0) return;
      var key = pair.slice(0, at), value;
      try { value = decodeURIComponent(pair.slice(at + 1).replace(/\+/g, " ")).trim(); } catch (e) { return; }
      if (key === "to" && EMAIL.test(value)) out.to = value;
      if (key === "week" && (value === "1" || value === "2")) out.week = Number(value);
    });
    return out;
  }

  /** The items to show: every item, or one week's. */
  function pick(items, week) {
    return week ? items.filter(function (i) { return i.week === week; }) : items.slice();
  }

  function answered(item, answers) {
    var a = answers[item.id];
    if (!a) return false;
    if (item.options) return item.options.some(function (o) { return o.id === a; });
    return String(a).trim() !== "";
  }

  /** Keep only answers that still fit the items (an option removed since leaves its question blank). */
  function clean(items, answers) {
    var out = {};
    items.forEach(function (item) {
      if (answered(item, answers || {})) out[item.id] = answers[item.id];
    });
    return out;
  }

  function oneLine(text) { return String(text || "").replace(/\s+/g, " ").trim(); }

  /** The text the instructor receives. mark_pretest.py reads it; change both together. */
  function answerText(form, items, state) {
    var answers = state.answers || {};
    var name = oneLine(state.name) || "(no name given)";
    var count = items.filter(function (i) { return answered(i, answers); }).length;
    var lines = [
      "Pretest answers from " + name + ".",
      "Leave everything between the two marker lines as it is.",
      "",
      BEGIN,
      "form: " + form,
      "name: " + name,
      "answered: " + count + " of " + items.length
    ];
    items.forEach(function (item) {
      if (!answered(item, answers)) { lines.push(item.id + ": -"); return; }
      if (item.options) { lines.push(item.id + ": " + answers[item.id]); return; }
      lines.push(item.id + ":");
      String(answers[item.id]).replace(/\r\n?/g, "\n").replace(/\s+$/, "").split("\n").forEach(function (l) {
        lines.push("    " + l.replace(/\s+$/, ""));
      });
    });
    lines.push(END);
    return lines.join("\n");
  }

  function subject(state) { return "Pretest answers: " + (oneLine(state.name) || "(no name given)"); }

  /** The downloaded file's name, with the student's name in it so the instructor's folder keeps every reply. */
  function fileName(name) {
    var slug = oneLine(name).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40);
    return "pretest-answers" + (slug ? "-" + slug : "") + ".txt";
  }

  /** A mailto link with the answers in the body, or with a "paste here" body when the answers are too long. */
  function mailto(to, subj, body) {
    var make = function (b) {
      return "mailto:" + encodeURIComponent(to) + "?subject=" + encodeURIComponent(subj) +
        "&body=" + encodeURIComponent(b);
    };
    var full = make(body);
    if (full.length <= MAILTO_MAX) return { href: full, whole: true };
    return { href: make("Paste your answers here (press Ctrl+V), then send.\n"), whole: false };
  }

  var api = { readFragment: readFragment, pick: pick, answered: answered, clean: clean, answerText: answerText,
              subject: subject, mailto: mailto, fileName: fileName, BEGIN: BEGIN, END: END, MAILTO_MAX: MAILTO_MAX };
  root.Pretest = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document === "undefined") return;

  // ---------- The page ----------

  var store = {
    get: function () { try { return JSON.parse(root.localStorage.getItem(STORE_KEY)); } catch (e) { return null; } },
    set: function (v) { try { root.localStorage.setItem(STORE_KEY, JSON.stringify(v)); } catch (e) { /* private window */ } },
    drop: function () { try { root.localStorage.removeItem(STORE_KEY); } catch (e) { /* private window */ } }
  };

  function el(tag, props, kids) {
    var node = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) {
      if (k === "text") node.textContent = props[k];
      else if (k === "class") node.className = props[k];
      else if (k.slice(0, 2) === "on") node.addEventListener(k.slice(2), props[k]);
      else node.setAttribute(k, props[k]);
    });
    (kids || []).forEach(function (kid) { if (kid) node.appendChild(kid); });
    return node;
  }

  /** A paragraph with `inline code` drawn as code; text only, never HTML. */
  function para(text) {
    var p = el("p");
    String(text).split("`").forEach(function (part, n) {
      p.appendChild(n % 2 ? el("code", { text: part }) : document.createTextNode(part));
    });
    return p;
  }

  function start() {
    var data = root.PRETEST;
    var mount = document.getElementById("pretest");
    if (!data || !mount) {
      if (mount) mount.appendChild(el("p", { class: "lab-error", text: "The questions did not load. Keep items.js beside this page." }));
      return;
    }
    var link = readFragment(root.location.hash);
    var items = pick(data.items, link.week);
    var saved = store.get() || {};
    var state = { name: saved.name || "", answers: clean(data.items, saved.answers) };
    var save = function () { store.set(state); };
    var status = el("p", { class: "lab-status", "aria-live": "polite" });
    var preview = el("textarea", { class: "pretest-preview", readonly: "readonly", rows: "8", "aria-label": "Your answers, as they will be sent" });

    function refresh() {
      var n = items.filter(function (i) { return answered(i, state.answers); }).length;
      status.textContent = "You have answered " + n + " of " + items.length + " questions." +
        (oneLine(state.name) ? "" : " Add your name before you send.");
      preview.value = answerText(data.form, items, state);
    }

    // Intro and name.
    var nameBox = el("input", { id: "pretest-name", type: "text", autocomplete: "name", value: state.name,
      oninput: function () { state.name = nameBox.value; save(); refresh(); } });
    mount.appendChild(el("section", { class: "lab-step" }, [
      el("h2", { text: "Before you start" }),
      el("p", { text: "This pretest counts for nothing. Your instructor reads it to choose how you start each day's lab: with a worked example, or straight at the problem." }),
      el("p", { text: "Answer on your own, without looking anything up. If you don't know an answer, leave it blank: a lucky guess could have you offered a problem you're not ready for." }),
      el("p", { text: "Your answers are saved in this browser as you go, so you can close the page and come back on the same computer. Nothing is sent until you press Email my answers at the end." }),
      el("label", { for: "pretest-name", class: "pretest-label", text: "Your name, as your instructor knows it" }),
      nameBox
    ]));

    // The items, a section per day.
    var number = 0;
    var days = [];
    items.forEach(function (i) { if (days.indexOf(i.day) < 0) days.push(i.day); });
    days.forEach(function (day) {
      var section = el("section", { class: "lab-step" }, [el("h2", { text: "Day " + day })]);
      items.filter(function (i) { return i.day === day; }).forEach(function (item) {
        number += 1;
        var box = el("div", { class: "pretest-item", id: "item-" + item.id });
        box.appendChild(el("h3", { text: "Question " + number }));
        item.stem.forEach(function (b) {
          box.appendChild(b.code !== undefined ? el("pre", { class: "pretest-code" }, [el("code", { text: b.code })]) : para(b.p));
        });
        if (item.options) {
          var set = el("fieldset", { class: "choices" }, [el("legend", { class: "vh", text: "Question " + number + " options" })]);
          item.options.forEach(function (o) {
            var input = el("input", { type: "radio", name: "opt-" + item.id, value: o.id,
              onchange: function () { state.answers[item.id] = o.id; save(); refresh(); } });
            if (state.answers[item.id] === o.id) input.checked = true;
            set.appendChild(el("label", { class: "choice" }, [input, el("span", { text: o.text })]));
          });
          box.appendChild(set);
          box.appendChild(el("button", { type: "button", class: "btn pretest-clear", text: "Clear my choice",
            onclick: function () {
              delete state.answers[item.id];
              set.querySelectorAll("input").forEach(function (i) { i.checked = false; });
              save(); refresh();
            } }));
        } else {
          var area = el("textarea", { rows: "7", class: "pretest-written", "aria-label": "Your answer to question " + number,
            oninput: function () {
              if (area.value.trim()) state.answers[item.id] = area.value; else delete state.answers[item.id];
              save(); refresh();
            } });
          area.value = state.answers[item.id] || "";
          box.appendChild(area);
        }
        section.appendChild(box);
      });
      mount.appendChild(section);
    });

    // Send.
    var note = el("p", { class: "lab-status" });
    var copy = function () {
      preview.focus(); preview.select();
      var done = function (ok) {
        note.textContent = ok ? "Your answers are copied. Paste them into an email to your instructor."
          : "Select the answers in the box below, copy them, and paste them into an email to your instructor.";
      };
      if (root.navigator.clipboard && root.isSecureContext) {
        return root.navigator.clipboard.writeText(preview.value).then(function () { done(true); return true; },
          function () { var ok = false; try { ok = document.execCommand("copy"); } catch (e) { /* old browser */ } done(ok); return ok; });
      }
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { /* old browser */ }
      done(ok);
      return Promise.resolve(ok);
    };
    var sendTo = link.to
      ? el("p", {}, [document.createTextNode("Your answers go to "), el("strong", { text: link.to }), document.createTextNode(".")])
      : el("p", { text: "Your joining instructions give the address to send your answers to. Email my answers opens a new email for you to address." });
    var details = el("details", {}, [el("summary", { text: "See what will be sent" }), preview]);
    mount.appendChild(el("section", { class: "lab-step" }, [
      el("h2", { text: "Send your answers" }),
      status,
      sendTo,
      el("div", { class: "lab-nav pretest-send" }, [
        el("button", { type: "button", class: "btn primary", text: "Email my answers", onclick: function () {
          refresh();
          var m = mailto(link.to, subject(state), preview.value);
          if (m.whole) {
            note.textContent = "Your email program should open with your answers in a new email. Press Send there. If nothing opens, use Copy my answers.";
            root.location.href = m.href;
            return;
          }
          copy().then(function (ok) {
            note.textContent = ok ? "Your answers are too long to fit into the email for you, so they are copied: paste them into the new email (Ctrl+V), then press Send."
              : "Your answers are too long to fit into the email for you. Open See what will be sent, copy everything in the box, and paste it into the new email.";
            root.location.href = m.href;
          });
        } }),
        el("button", { type: "button", class: "btn", text: "Copy my answers", onclick: function () { refresh(); copy(); } }),
        el("button", { type: "button", class: "btn", text: "Download my answers", onclick: function () {
          refresh();
          var blob = new Blob([preview.value.replace(/\n/g, "\r\n")], { type: "text/plain" });
          var file = fileName(state.name);
          var a = el("a", { href: URL.createObjectURL(blob), download: file });
          document.body.appendChild(a); a.click(); a.remove();
          note.textContent = "Saved as " + file + ". Attach it to an email to your instructor.";
        } })
      ]),
      note,
      details,
      el("p", { class: "pretest-restart" }, [el("button", { type: "button", class: "btn", text: "Clear all my answers", onclick: function () {
        if (!root.confirm("Clear every answer and your name from this browser?")) return;
        store.drop();
        root.location.reload();
      } })])
    ]));
    refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})(typeof window !== "undefined" ? window : globalThis);
