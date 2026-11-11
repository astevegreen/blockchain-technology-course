/* The prediction-lab shell (lab plan, Stage 2: "One shell for prediction labs").
 *
 * A lab page links look.css and this file, then calls LabShell.start(config). The shell draws the bar, the
 * seven named steps, the buttons and the student's commitments; the lab supplies only its content and the one
 * interactive part ("Do it"). The seven steps are fixed, in order (docs/analysis/2026-11-static-labs-review.md,
 * "A new job for static labs"):
 *
 *   case      A case: one concrete situation in plain words, no terms yet.
 *   commit    Commit: an answer and a confidence; the page will not go on until both are picked.
 *   do        Do it: the lab's own interaction; it calls api.finish({ choice, note }) when the result is in.
 *   name      Name it: one term, its parts, its plain meaning (one new term per step).
 *   explorer  What the explorer shows: the same thing as an analyst meets it.
 *   twist     Change one thing: one fact changed; predict again, then the answer is shown.
 *   tell      Tell an agent: one sentence with a confidence word, said to a neighbour (confidence: false drops the
 *             word, for a fact read straight off the record).
 * commit and twist take an optional reason (a prompt): a written reason, required before the pick locks.
 *
 * Works offline and from a plain file: a classic script, no modules, no network, no Pyodide. Progress is kept
 * in the browser so a reload resumes; Restart clears it, so a student can repeat the lab alone later.
 * The design card for each lab (docs/lab-cards/) maps one-to-one onto this config.
 */
(function (root) {
  "use strict";

  var STEPS = [
    { key: "case", label: "A case" },
    { key: "commit", label: "Commit" },
    { key: "do", label: "Do it" },
    { key: "name", label: "Name it" },
    { key: "explorer", label: "The explorer" },
    { key: "twist", label: "Change one thing" },
    { key: "tell", label: "Tell an agent" }
  ];
  var LEVELS = ["low", "moderate", "high"];
  var LEVEL_WORD = { low: "Low", moderate: "Moderate", high: "High" };

  // ---------- Pure helpers (tested in tools/tests/lab_shell.test.mjs) ----------

  /** Every problem with a lab config, as plain sentences; an empty list means the config is usable. */
  function validate(config) {
    var problems = [];
    if (!config || typeof config !== "object") return ["LabShell.start needs a config object."];
    if (!/^[a-z0-9-]+$/.test(config.id || "")) problems.push("id: lower-case letters, digits and - only.");
    if (!config.title) problems.push("title: missing.");
    if (!config.slide || !config.slide.title || !config.slide.href) {
      problems.push("slide: needs { title, href } for the slide that opens the lab.");
    }
    var steps = config.steps || {};
    STEPS.forEach(function (s) { if (!steps[s.key]) problems.push("steps." + s.key + ": missing."); });
    Object.keys(steps).forEach(function (k) {
      if (!STEPS.some(function (s) { return s.key === k; })) problems.push("steps." + k + ": not one of the seven steps.");
    });
    if (steps["case"] && !steps["case"].html) problems.push("steps.case: needs html.");
    checkQuestion(steps.commit, "commit", problems);
    if (steps["do"] && typeof steps["do"].render !== "function") problems.push("steps.do: needs render(el, api).");
    if (steps.name) {
      if (typeof steps.name.term !== "string" || !steps.name.term) problems.push("steps.name: needs one term.");
      else if (/[,;]/.test(steps.name.term)) problems.push("steps.name: one new term per step, not a list.");
      if (!steps.name.parts) problems.push("steps.name: needs parts (where the word comes from).");
      if (!steps.name.plain) problems.push("steps.name: needs plain (the meaning in plain words).");
    }
    if (steps.explorer && !steps.explorer.html && typeof steps.explorer.render !== "function") {
      problems.push("steps.explorer: needs html or render(el).");
    }
    if (steps.twist) {
      if (!steps.twist.html) problems.push("steps.twist: needs html (the case with one fact changed).");
      checkQuestion(steps.twist, "twist", problems);
      var n = (steps.twist.choices || []).length;
      if (!(steps.twist.answer >= 0 && steps.twist.answer < n)) problems.push("steps.twist: answer must index a choice.");
      if (!steps.twist.why) problems.push("steps.twist: needs why (shown with the answer).");
    }
    if (steps.tell && !steps.tell.prompt) problems.push("steps.tell: needs prompt.");
    return problems;
  }

  function checkQuestion(step, key, problems) {
    if (!step) return;
    if (!step.question) problems.push("steps." + key + ": needs question.");
    if (!Array.isArray(step.choices) || step.choices.length < 2) problems.push("steps." + key + ": needs two or more choices.");
  }

  /** How a commitment fared against what happened. held is null when the lab reports no single outcome. */
  function verdict(commitment, actualChoice) {
    if (!commitment || actualChoice === null || actualChoice === undefined) return { held: null, costly: false };
    var held = commitment.choice === actualChoice;
    return { held: held, costly: !held && commitment.conf === "high" };
  }

  /** The confidence word a sentence uses, or null. Whole words only: "slow" is not "low". */
  function findConfidence(text) {
    var m = /\b(high|moderate|low)\b/i.exec(text || "");
    return m ? m[1].toLowerCase() : null;
  }

  /** A long hex value shortened in the middle, as explorers show it: 3f9a1c…e04b. */
  function short(value, keep) {
    var k = keep || 6;
    var s = String(value);
    return s.length <= k * 2 + 1 ? s : s.slice(0, k) + "…" + s.slice(-k);
  }

  // ---------- Browser part ----------

  var store = {
    get: function (key) { try { return JSON.parse(root.localStorage.getItem(key)); } catch (e) { return null; } },
    set: function (key, value) { try { root.localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private window */ } },
    drop: function (key) { try { root.localStorage.removeItem(key); } catch (e) { /* private window */ } }
  };

  /** Build an element: el("p", { class: "x" }, "text", child). Strings become text, never HTML. */
  function el(tag, attrs) {
    var node = root.document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "html") node.innerHTML = attrs[k];
      else if (k.slice(0, 2) === "on") node.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] !== null && attrs[k] !== undefined) node.setAttribute(k, attrs[k] === true ? "" : attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c === null || c === undefined || c === false) continue;
      node.appendChild(typeof c === "string" || typeof c === "number" ? root.document.createTextNode(String(c)) : c);
    }
    return node;
  }

  var ROLE_WORD = { input: "input", output: "output", change: "change", fee: "fee" };

  /** A coin in the shared look: coin({ role: "input" | "output" | "change" | "fee", amount, who }). */
  function coin(o) {
    var said = ROLE_WORD[o.role] ? ROLE_WORD[o.role] + (o.spent ? ", spent" : "") + ": " : null;
    return el("span", { class: "coin " + (o.role || "") + (o.spent ? " spent" : "") },
      said ? el("span", { class: "vh" }, said) : null, el("span", { class: "amount" }, o.amount), o.who ? el("span", { class: "who" }, o.who) : null);
  }

  /** A confidence word in the shared look. */
  function conf(level) { return el("span", { class: "conf", "data-level": level }, LEVEL_WORD[level] || level); }

  /** A colour from look.css, for labs that draw on a canvas or in SVG: color("change"). */
  function color(name) {
    return root.getComputedStyle(root.document.documentElement).getPropertyValue("--" + name).trim();
  }

  function setDisplay(mode) {
    var html = root.document.documentElement;
    if (mode === "projector") html.setAttribute("data-display", "projector");
    else html.removeAttribute("data-display");
    store.set("lab:display", mode);
  }

  function start(config) {
    var doc = root.document;
    var mount = doc.querySelector("[data-lab-root]") || doc.body;
    var problems = validate(config);
    if (problems.length) {
      mount.appendChild(el("pre", { class: "lab-error", role: "alert" }, "This lab's config has problems:\n- " + problems.join("\n- ")));
      return null;
    }
    var key = "lab:" + config.id;
    var blank = function () { return { at: 0, commit: null, outcome: null, twist: null, sentence: "", finished: false }; };
    var state = store.get(key) || blank();
    var save = function () { store.set(key, state); };

    var wanted = /[?&]display=projector\b/.test(root.location.search) ? "projector" : store.get("lab:display");
    setDisplay(wanted === "projector" ? "projector" : "laptop");
    doc.title = config.title;

    var projectorBtn = el("button", { class: "btn", type: "button", "aria-pressed": "false",
      onclick: function () { toggleProjector(); } }, "Projector (P)");
    var restartBtn = el("button", { class: "btn", type: "button", onclick: restart }, "Restart");
    var stepList = el("ol", { class: "lab-steps", "aria-label": "Steps" });
    var body = el("section", { class: "lab-step" });
    var moved = false; // set by go(): the next draw puts keyboard focus on the step's heading
    var status = el("p", { class: "lab-status", role: "status" });
    var backBtn = el("button", { class: "btn", type: "button", onclick: function () { go(state.at - 1); } }, "Back");
    var nextBtn = el("button", { class: "btn primary", type: "button", onclick: next }, "Next");

    mount.appendChild(el("main", { class: "lab" },
      el("header", { class: "lab-bar" },
        el("h1", null, config.title), projectorBtn, restartBtn,
        el("p", { class: "from" }, "Opened from the slide ", el("a", { href: config.slide.href }, "“" + config.slide.title + "”"))),
      stepList, body, status, el("nav", { class: "lab-nav" }, backBtn, nextBtn)));

    doc.addEventListener("keydown", function (e) {
      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target && e.target.tagName) || "") && e.target.type !== "radio";
      if (!typing && !e.ctrlKey && !e.metaKey && !e.altKey && (e.key === "p" || e.key === "P")) toggleProjector();
    });

    function toggleProjector() {
      var on = doc.documentElement.getAttribute("data-display") !== "projector";
      setDisplay(on ? "projector" : "laptop");
      projectorBtn.setAttribute("aria-pressed", on ? "true" : "false");
    }
    projectorBtn.setAttribute("aria-pressed", doc.documentElement.getAttribute("data-display") === "projector" ? "true" : "false");

    function restart() {
      if (!root.confirm("Start this lab again from the first step? Your answers here are cleared.")) return;
      state = blank();
      store.drop(key);
      go(0);
    }

    function go(i) {
      state.at = Math.max(0, Math.min(STEPS.length - 1, i));
      save();
      moved = true;
      draw();
    }

    function next() {
      var k = STEPS[state.at].key;
      if (k === "commit" && !state.commit) { lockQuestion("commit"); return; }
      if (k === "twist" && !state.twist) { lockQuestion("twist"); return; }
      if (k === "tell") { state.finished = true; save(); draw(); return; }
      go(state.at + 1);
    }

    // A question step keeps the student's picks in the form until they lock them in.
    var pending = { choice: null, conf: null, reason: "" };

    function lockQuestion(k) {
      if (pending.choice === null || pending.conf === null) return;
      if (config.steps[k].reason && !pending.reason.trim()) return;
      state[k] = { choice: pending.choice, conf: pending.conf };
      if (config.steps[k].reason) state[k].reason = pending.reason.trim();
      save();
      draw();
    }

    function draw() {
      var k = STEPS[state.at].key;
      var step = config.steps[k];
      stepList.innerHTML = "";
      STEPS.forEach(function (s, i) {
        stepList.appendChild(el("li", { "data-state": i < state.at ? "done" : i === state.at ? "now" : "todo",
          "aria-current": i === state.at ? "step" : false }, s.label));
      });
      body.innerHTML = "";
      status.textContent = "";
      pending = { choice: null, conf: null, reason: "" };
      backBtn.disabled = state.at === 0;
      nextBtn.disabled = false;
      nextBtn.textContent = "Next";
      var heading = el("h2", { tabindex: "-1" }, STEPS[state.at].label);
      body.appendChild(heading);
      if (moved) { moved = false; heading.focus(); }

      if (k === "case") body.appendChild(el("div", { html: step.html }));
      if (k === "commit") drawQuestion(step, "commit");
      if (k === "do") drawDo(step);
      if (k === "name") {
        body.appendChild(el("p", { class: "term" }, step.term));
        if (step.parts) body.appendChild(el("p", { class: "term-parts" }, step.parts));
        body.appendChild(el("p", { html: step.plain }));
      }
      if (k === "explorer") {
        if (step.html) body.appendChild(el("div", { html: step.html }));
        if (typeof step.render === "function") { var box = el("div"); body.appendChild(box); step.render(box, api()); }
      }
      if (k === "twist") {
        body.appendChild(el("div", { html: step.html }));
        drawQuestion(step, "twist");
        if (state.twist) {
          var v = verdict(state.twist, step.answer);
          body.appendChild(verdictBox(v, state.twist, step.choices[step.answer], step.why));
        }
      }
      if (k === "tell") drawTell(step);
    }

    function drawQuestion(step, k) {
      var done = state[k];
      var pick = el("fieldset", { class: "choices" + (done ? " locked" : "") }, el("legend", null, step.question));
      step.choices.forEach(function (text, i) {
        pick.appendChild(el("label", { class: "choice" },
          el("input", { type: "radio", name: k + "-choice", value: i, checked: done ? done.choice === i : false,
            disabled: !!done, onchange: function () { pending.choice = i; ready(); } }),
          el("span", null, text)));
      });
      var sure = el("fieldset", { class: "choices conf-row" + (done ? " locked" : "") }, el("legend", null, "How sure are you?"));
      LEVELS.forEach(function (level) {
        sure.appendChild(el("label", { class: "choice" },
          el("input", { type: "radio", name: k + "-conf", value: level, checked: done ? done.conf === level : false,
            disabled: !!done, onchange: function () { pending.conf = level; ready(); } }),
          conf(level)));
      });
      body.appendChild(pick);
      body.appendChild(sure);
      // Optional: step.reason is a prompt for a short written reason, kept with the pick (a game may score it).
      if (step.reason) {
        var why = el("textarea", { class: "sentence reason", "aria-label": step.reason, disabled: !!done,
          oninput: function () { pending.reason = why.value; ready(); } });
        why.value = done ? done.reason || "" : "";
        body.appendChild(el("label", { class: "reason-label" }, step.reason));
        body.appendChild(why);
      }
      if (done) {
        status.textContent = "Locked in. Your answer stays as you gave it.";
        return;
      }
      nextBtn.textContent = "Lock in my answer";
      nextBtn.disabled = true;
      status.textContent = step.reason
        ? "Pick an answer and how sure you are, and give your reason. The lab goes on once all three are in."
        : "Pick an answer and how sure you are. The lab goes on once both are picked.";
      function ready() {
        nextBtn.disabled = pending.choice === null || pending.conf === null || (!!step.reason && !pending.reason.trim());
        if (!nextBtn.disabled) status.textContent = "Ready. Lock it in when you are sure of your pick.";
      }
    }

    function drawDo(step) {
      var stage = el("div");
      body.appendChild(stage);
      var result = el("div");
      body.appendChild(result);
      nextBtn.disabled = !state.outcome;
      if (state.outcome) showOutcome(result, state.outcome);
      else status.textContent = "Work through it; Next opens when the result is in.";
      step.render(stage, api(function (outcome) {
        state.outcome = { choice: outcome && outcome.choice !== undefined ? outcome.choice : null,
          note: (outcome && outcome.note) || "" };
        save();
        result.innerHTML = "";
        showOutcome(result, state.outcome);
        nextBtn.disabled = false;
        status.textContent = "";
      }));
    }

    function showOutcome(box, outcome) {
      var c = config.steps.commit;
      var v = verdict(state.commit, outcome.choice);
      var happened = outcome.choice !== null ? c.choices[outcome.choice] : null;
      box.appendChild(verdictBox(v, state.commit, happened, outcome.note));
    }

    function verdictBox(v, commitment, happened, note) {
      var box = el("div", { class: "verdict", "data-held": v.held === null ? false : v.held ? "yes" : "no" });
      if (v.held !== null) {
        box.appendChild(el("p", null, el("strong", null, v.held ? "Your prediction held." : "Your prediction did not hold."),
          " You said ", conf(commitment.conf), "."));
        if (happened) box.appendChild(el("p", null, "What happened: " + happened));
        if (v.costly) box.appendChild(el("p", null, "High is for two or more independent lines of evidence that agree."));
      }
      if (note) box.appendChild(el("div", { html: note }));
      return box;
    }

    function drawTell(step) {
      body.appendChild(el("div", { html: step.prompt }));
      var hint = el("p", { class: "lab-status" });
      var area = el("textarea", { class: "sentence", "aria-label": "Your sentence to the agent",
        oninput: function () { state.sentence = area.value; save(); check(); } });
      area.value = state.sentence || "";
      body.appendChild(area);
      body.appendChild(hint);
      if (step.example) body.appendChild(el("details", null, el("summary", null, "One way to say it"), el("p", { html: step.example })));
      nextBtn.textContent = state.finished ? "Done" : "Finish";
      if (state.finished) body.appendChild(summary());
      function check() {
        // step.confidence === false: a fact read straight off the record takes no confidence word.
        if (step.confidence === false) { hint.textContent = "Now say it to your neighbour."; return; }
        var level = findConfidence(area.value);
        hint.innerHTML = "";
        if (level) hint.append("Confidence word: ", conf(level), ". Now say it to your neighbour.");
        else hint.textContent = "Name how sure you are: High, Moderate or Low.";
      }
      check();
    }

    function summary() {
      var box = el("div", { class: "verdict", "data-held": false });
      box.appendChild(el("p", null, el("strong", null, "Finished."), " Restart to run it again on your own."));
      var first = verdict(state.commit, state.outcome && state.outcome.choice);
      var second = verdict(state.twist, config.steps.twist.answer);
      var line = function (label, v) {
        return el("p", null, label + ": " + (v.held === null ? "no single answer" : v.held ? "held" : "did not hold"));
      };
      box.appendChild(line("First prediction", first));
      box.appendChild(line("After the change", second));
      return box;
    }

    function api(finish) {
      return {
        finish: finish || function () {},
        commitment: state.commit,
        el: el, coin: coin, conf: conf, color: color, short: short,
        say: function (text) { status.textContent = text; }
      };
    }

    draw();
    return { state: function () { return state; } };
  }

  var LabShell = { start: start, validate: validate, verdict: verdict, findConfidence: findConfidence, short: short,
    el: el, coin: coin, conf: conf, color: color, STEPS: STEPS };
  if (typeof module !== "undefined" && module.exports) module.exports = LabShell;
  else root.LabShell = LabShell;
})(typeof window !== "undefined" ? window : globalThis);
