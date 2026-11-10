// The control page: lists the labs and drives /api/ (docs/student-launcher-design.md section 5).
"use strict";

const STATE_WORDS = {
  "not-downloaded": "Not downloaded yet",
  "downloaded": "Ready to start",
  "starting": "Starting",
  "running": "Running",
  "stopped": "Stopped (your work is kept)",
  "error": "Didn't start",
  "unavailable": "Not available on this computer",
};
const polling = new Set();
const notes = {};
let actionTimer = null;

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  for (const child of children) if (child !== null && child !== undefined) node.append(child);
  return node;
}

async function api(method, path) {
  try {
    const resp = await fetch("/api/" + path, { method, headers: { "Content-Type": "application/json" } });
    const body = await resp.json().catch(() => ({}));
    return { ok: resp.ok, status: resp.status, body };
  } catch (err) {
    return { ok: false, status: 0, body: { message: "The control page lost touch with Docker. If you pressed Stop " +
      "Course Labs, that's expected; otherwise double-click Start Course Labs again." } };
  }
}

function size(mb) {
  if (!mb) return "";
  return mb >= 1024 ? (mb / 1024).toFixed(1).replace(/\.0$/, "") + " GB" : mb + " MB";
}

function showProblem(text) {
  const box = document.getElementById("problem");
  box.textContent = text || "";
  box.hidden = !text;
}

function labCard(lab) {
  const facts = [];
  if (lab.day) facts.push("Day " + lab.day);
  if (lab.approx_download_mb && lab.state === "not-downloaded") {
    facts.push("about " + size(lab.approx_download_mb) + " to download");
  }
  if (lab.memory_mb) facts.push("needs " + size(lab.memory_mb) + " of memory");
  const card = el("article", { class: "lab", id: "lab-" + lab.id },
    el("div", { class: "lab-head" }, el("h2", {}, lab.title),
      el("span", { class: "state " + lab.state }, STATE_WORDS[lab.state] || lab.state)),
    el("p", { class: "facts" }, facts.join(" · ")));
  const busy = lab.action && lab.action.phase === "running";
  const finished = lab.action && !busy ? lab.action.message : null;
  const message = lab.unavailable_reason || lab.message || notes[lab.id] || finished;
  if (message) card.append(el("p", { class: "message" }, message));
  if (busy) {
    const minutes = Math.floor(lab.action.elapsed_s / 60);
    card.append(el("progress", {}));
    card.append(el("p", { class: "message muted" }, lab.action.label + "… This can take up to 10 minutes. Leave " +
      "this page open" + (minutes ? " (" + minutes + (minutes === 1 ? " minute" : " minutes") + " so far)." : ".")));
  }
  if (lab.state === "starting") {
    card.append(el("progress", { id: "bar-" + lab.id }));
    card.append(el("p", { class: "message muted", id: "phase-" + lab.id }, "Getting ready…"));
    watch(lab.id);
  }
  const buttons = el("div", { class: "buttons" });
  if (lab.state === "running") {
    buttons.append(el("a", { class: "button", href: lab.entry_url, target: "_blank", rel: "noopener" }, "Open"));
    for (const action of lab.actions || []) {
      const attrs = { class: "secondary", onclick: (e) => runAction(lab, action, e.target) };
      if (busy) attrs.disabled = "";
      buttons.append(el("button", attrs, action.label));
    }
    buttons.append(el("button", { class: "secondary", onclick: () => press(lab, "stop") }, "Stop"));
  } else if (lab.state !== "starting" && lab.state !== "unavailable") {
    buttons.append(el("button", { onclick: () => press(lab, "start") }, "Start"));
  }
  if (["running", "stopped", "error"].includes(lab.state)) {
    buttons.append(el("button", { class: "danger", onclick: () => confirmReset(lab) }, "Reset"));
  }
  card.append(buttons);
  return card;
}

async function refresh() {
  const result = await api("GET", "labs");
  const section = document.getElementById("labs");
  if (!result.ok) {
    showProblem(result.body.message);
    // Before any lab is listed the section still says "Looking at this computer…": not under a problem.
    if (!section.querySelector(".lab")) section.replaceChildren();
    return;
  }
  showProblem("");
  section.replaceChildren(...result.body.labs.map(labCard));
  if (!result.body.labs.length) section.append(el("p", { class: "muted" }, "No labs in this release."));
  // A button that takes minutes: look again every few seconds until it finishes.
  const anyBusy = result.body.labs.some((lab) => lab.action && lab.action.phase === "running");
  if (anyBusy && !actionTimer) actionTimer = setTimeout(() => { actionTimer = null; refresh(); }, 3000);
}

async function press(lab, verb) {
  delete notes[lab.id];
  const result = await api("POST", "labs/" + lab.id + "/" + verb);
  if (!result.ok) notes[lab.id] = result.body.message;
  await refresh();
}

async function runAction(lab, action, button) {
  button.disabled = true;
  button.textContent = action.label + "…";
  delete notes[lab.id];
  const result = await api("POST", "labs/" + lab.id + "/actions/" + action.id);
  if (!result.ok) notes[lab.id] = result.body.message;
  await refresh();
}

function confirmReset(lab) {
  const dialog = document.getElementById("confirm");
  document.getElementById("confirm-text").textContent = "Reset puts " + lab.title + " back to how it was at the " +
    "start of the course. Everything you did in this lab is deleted.";
  dialog.onclose = () => { if (dialog.returnValue === "reset") press(lab, "reset"); };
  dialog.showModal();
}

function watch(id) {
  if (polling.has(id)) return;
  polling.add(id);
  const tick = async () => {
    const result = await api("GET", "labs/" + id + "/progress");
    const p = result.body;
    if (!result.ok || p.phase === "running" || p.phase === "error") {
      polling.delete(id);
      await refresh();
      return;
    }
    const bar = document.getElementById("bar-" + id);
    const phase = document.getElementById("phase-" + id);
    if (bar && p.phase === "pulling" && p.total_mb) {
      bar.max = p.total_mb;
      bar.value = p.pulled_mb;
    } else if (bar) {
      bar.removeAttribute("value");
    }
    if (phase) {
      phase.textContent = p.phase === "pulling"
        ? "Downloading" + (p.total_mb ? ": about " + (size(p.pulled_mb) || "0 MB") + " of " + size(p.total_mb) : "…")
        : "Starting the lab…";
    }
    setTimeout(tick, 1000);
  };
  setTimeout(tick, 1000);
}

async function showSystem() {
  const result = await api("GET", "system");
  if (!result.ok) return;
  const s = result.body;
  const docker = s.docker && s.docker.running
    ? "Running" + (s.docker.version ? " (version " + s.docker.version + ")" : "")
    : "Not running";
  const rows = [
    ["Docker", docker],
    ["Memory for Docker", s.memory_mb ? size(s.memory_mb) : "Unknown"],
    ["Processor", s.arch_name || s.arch || "Unknown"],
    ["Internet", s.internet ? "Connected" : "Not connected"],
  ];
  const busy = Object.entries(s.ports || {}).filter(([, v]) => v === "busy").map(([p]) => p);
  rows.push(["Ports in use by other programs", busy.length ? busy.join(", ") : "None"]);
  document.getElementById("system").replaceChildren(...rows.flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));
  if (s.docker && !s.docker.running) {
    showProblem("Docker isn't running. Open Docker Desktop, wait until it says it is running, then reload this page.");
  }
}

async function boot() {
  const health = await api("GET", "health");
  if (health.ok) document.getElementById("version").textContent = "Release " + health.body.version;
  await refresh();
  const update = await api("GET", "update");
  document.getElementById("update").hidden = !(update.ok && update.body.available);
  document.getElementById("about").addEventListener("toggle", (e) => { if (e.target.open) showSystem(); });
  setInterval(() => { if (!polling.size && !document.querySelector("dialog[open]")) refresh(); }, 10000);
}

boot();
