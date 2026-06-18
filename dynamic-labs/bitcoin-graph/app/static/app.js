/* Chain Graph frontend. All graph layout runs here in the browser —
 * the server only ships bounded nodes/edges JSON per request, so 30
 * students share one read-only backend cheaply.
 *
 * Views:
 *  - force:    cose layout, free pan/zoom (investigation board)
 *  - timeline: block height = horizontal position (oldest left). A tx
 *              sits in its block's column; an address that only FEEDS a
 *              block sits just left of it, one that only RECEIVES sits
 *              just right, and a bridging address sits between its two
 *              blocks. Canvas grows rightward inside a scrollable wrap.
 *
 * Recursive expand: "Expand flows" follows N hops outward via repeated
 * bounded /address calls (client-side BFS), capped so a hub can't melt
 * the browser or hammer the server.
 *
 * Pathfinder: From + To address → /api/paths → linear (timeline) view.
 * Trim: right-click a node to drop it and everything downstream.
 * Labels: client-side annotations in localStorage (no database).
 */
(function () {
  "use strict";

  // Served at <base>/, assets at <base>/static/ — derive base from URL.
  var BASE = location.pathname.replace(/\/$/, "");
  var API = BASE + "/api";

  var statusChip = document.getElementById("status-chip");
  var panelEmpty = document.getElementById("panel-empty");
  var panelBody = document.getElementById("panel-body");
  var banner = document.getElementById("banner");
  var cyWrap = document.getElementById("cy-wrap");
  var cyEl = document.getElementById("cy");
  var chainRange = null;        // {t_min, t_max} from /api/status
  var currentDepth = 20;        // hops for "Expand flows" — deep enough to chase a full trail to its end
  var expandDir = "forward";    // "both" | "forward" (spent) | "back" (source) — default to future/downstream
  var txNeighbors = {};         // txid -> {ins:[…], outs:[…]} for tx expansion
  var pendingAuto = null;       // deferred URL auto-draw, fired once graph is ready
  var expandAbort = false;      // set by the Stop control to cancel a running recursive expansion

  // Recursion guards: keep the browser responsive and server load bounded.
  var MAX_FRONTIER = 40;   // addresses expanded per hop
  var MAX_NODES = 2000;    // hard ceiling on graph size

  // Node labels (annotations). Client-side only — kept in localStorage,
  // keyed by node id (address or txid), so no server/database is involved.
  // Persists across reloads and rebuilds on this browser; per-browser, so
  // labels don't follow a student to another machine.
  var LABEL_KEY = "chaingraph_labels";
  function loadLabels() {
    try { return JSON.parse(localStorage.getItem(LABEL_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function saveLabels() {
    try { localStorage.setItem(LABEL_KEY, JSON.stringify(LABELS)); } catch (e) {}
  }
  var LABELS = loadLabels();

  // ---------------------------------------------------------------- utils

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function fmtBtc(v) {
    return (Math.round((v || 0) * 1e8) / 1e8) + " BTC";
  }
  function fmtTime(t) {
    return t ? new Date(t * 1000).toLocaleString() : "—";
  }
  function shorten(s, n) {
    n = n || 14;
    return s.length <= n * 2 + 1 ? s : s.slice(0, n) + "…" + s.slice(-6);
  }
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function showBanner(text, cls) {
    banner.textContent = text;
    banner.className = cls || "";
    banner.style.display = "";
    clearTimeout(showBanner._t);
    showBanner._t = setTimeout(function () { banner.style.display = "none"; }, 5000);
  }

  // A persistent banner (no auto-hide) carrying a Stop button, shown while a
  // recursive expansion runs so the user can cancel a slow/large traversal.
  function showExpanding(text) {
    clearTimeout(showBanner._t);
    banner.className = "";
    banner.innerHTML = escapeHtml(text) +
      " <button id='expand-stop' style='margin-left:10px'>Stop</button>";
    banner.style.display = "";
  }
  banner.addEventListener("click", function (ev) {
    if (ev.target && ev.target.id === "expand-stop") {
      expandAbort = true;
      ev.target.textContent = "Stopping…";
    }
  });

  // Deterministic cluster color: golden-angle hue walk. Singleton
  // clusters stay gray so only real co-spend groups pop.
  function clusterColor(node) {
    if (!node || node.cluster_size < 2) return "#8b949e";
    var hue = (node.cluster_id * 137.508) % 360;
    return "hsl(" + hue.toFixed(1) + ", 62%, 58%)";
  }

  function api(path) {
    return fetch(API + path, { credentials: "same-origin" }).then(function (r) {
      if (!r.ok) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          throw new Error(j.detail || j.error || ("HTTP " + r.status));
        });
      }
      return r.json();
    });
  }

  // ---------------------------------------------------------------- filters

  function localToEpoch(value) {
    if (!value) return null;
    var ms = new Date(value).getTime();
    return isNaN(ms) ? null : Math.floor(ms / 1000);
  }
  function epochToLocal(t) {
    var d = new Date(t * 1000);
    var pad = function (n) { return String(n).padStart(2, "0"); };
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate())
      + "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
  }
  function filterQuery() {
    var parts = [];
    var from = localToEpoch(document.getElementById("f-from").value);
    var to = localToEpoch(document.getElementById("f-to").value);
    var minv = parseFloat(document.getElementById("f-minv").value);
    if (from !== null) parts.push("tfrom=" + from);
    if (to !== null) parts.push("tto=" + to);
    if (minv > 0) parts.push("minv=" + minv);
    return parts.length ? "?" + parts.join("&") : "";
  }

  // ---------------------------------------------------------------- cytoscape

  var cy = cytoscape({
    container: cyEl,
    wheelSensitivity: 0.25,
    style: [
      { selector: "node[kind='address']",
        style: {
          shape: "ellipse",
          width: "data(size)", height: "data(size)",
          "background-color": "data(color)",
          label: "data(label)",
          color: "#c9d1d9", "font-size": 9,
          "text-valign": "bottom", "text-margin-y": 4,
          "border-width": 1.5, "border-color": "#30363d",
        } },
      { selector: "node[kind='tx']",
        style: {
          shape: "round-rectangle", width: 14, height: 14,
          "background-color": "#21262d",
          "border-width": 1.5, "border-color": "#484f58",
          label: "data(label)", color: "#8b949e", "font-size": 8,
          "text-valign": "bottom", "text-margin-y": 3,
        } },
      { selector: "node[?is_root]",
        style: { "border-color": "#58a6ff", "border-width": 4 } },
      // User-labeled (annotated) nodes: gold accent + bright bold text.
      { selector: "node[?userLabel]",
        style: { "border-color": "#d29922", "border-width": 3,
                 color: "#f0d75a", "font-weight": "bold" } },
      // Column header markers, timeline view only.
      { selector: "node[kind='colhead']",
        style: {
          shape: "rectangle", width: 1, height: 1,
          "background-opacity": 0, "border-width": 0,
          label: "data(label)", color: "#8b949e",
          "font-size": 11, "font-weight": "bold",
          "text-valign": "center", "text-halign": "center",
        } },
      { selector: "node:selected",
        style: { "border-color": "#e6edf3", "border-width": 3 } },
      { selector: "edge",
        style: {
          width: "data(width)",
          "line-color": "#3d444d", "target-arrow-color": "#3d444d",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier", "arrow-scale": 0.8,
          label: "data(label)", "font-size": 8, color: "#8b949e",
          "text-rotation": "autorotate", "text-background-color": "#0d1117",
          "text-background-opacity": 0.8, "text-background-padding": 1,
        } },
    ],
  });

  function edgeWidth(value) {
    return Math.max(1, Math.min(8, 1 + Math.log10(1 + (value || 0)) * 2.2));
  }
  function addrSize(node) {
    var vol = (node.total_in || 0) + (node.total_out || 0);
    return Math.max(16, Math.min(56, 16 + Math.log10(1 + vol) * 9));
  }

  // Merge server elements into the graph WITHOUT laying out (recursive
  // expand merges several responses, then lays out once). Returns the
  // freshly added address ids so the BFS knows the next frontier.
  function addElements(data) {
    var added = 0;
    var newAddrs = [];
    cy.startBatch();
    data.nodes.forEach(function (n) {
      if (cy.getElementById(n.id).nonempty()) return;
      var d = Object.assign({}, n);
      if (n.kind === "address") {
        d.color = clusterColor(n);
        d.size = addrSize(n);
        d.label = shorten(n.addr, 8);
        newAddrs.push(n.addr);
      } else if (n.kind === "tx") {
        d.label = "block " + n.height;
      }
      if (LABELS[n.id]) { d.userLabel = LABELS[n.id]; d.label = LABELS[n.id]; }
      cy.add({ group: "nodes", data: d });
      added++;
    });
    data.edges.forEach(function (e) {
      if (cy.getElementById(e.id).nonempty()) return;
      cy.add({ group: "edges", data: Object.assign({}, e, {
        width: edgeWidth(e.value),
        label: fmtBtc(e.value).replace(" BTC", ""),
      }) });
      added++;
    });
    cy.endBatch();
    if (data.truncated) {
      showBanner("A node hit the server cap — narrow the time window or raise min value.", "warn");
    }
    return { added: added, newAddrs: newAddrs };
  }

  // ---------------------------------------------------------------- layouts

  var viewMode = "force";

  function setCanvasSize(w, h) {
    cyEl.style.width = w ? w + "px" : "100%";
    cyEl.style.height = h ? h + "px" : "100%";
    cy.resize();
  }

  function applyLayout() {
    if (viewMode === "timeline") layoutTimeline();
    else layoutForce();
  }

  function layoutForce() {
    cy.nodes("[kind='colhead']").remove();
    setCanvasSize(null, null);
    cy.userPanningEnabled(true);
    cy.userZoomingEnabled(true);
    if (cy.nodes().length) {
      cy.layout({ name: "cose", animate: false, padding: 40,
                  nodeRepulsion: 9000, idealEdgeLength: 70 }).run();
      cy.fit(undefined, 40);
    }
  }

  // Layered timeline. Each node gets a half-column "bucket": a tx sits in
  // its block's bucket, an address that only FEEDS a block in the bucket
  // just left of it, one that only RECEIVES just right, a bridging address
  // between its two blocks. Buckets render left→right as variable-width
  // slots; a bucket with more than MAX_ROWS nodes wraps into a grid (extra
  // sub-columns) so a busy block can't tower vertically — the chart grows
  // rightward and scrolls instead. Vertical order within a bucket comes
  // from a few barycenter sweeps to reduce edge crossings.
  var TL_MAX_ROWS = 5;     // a column wraps into a new sub-column past this
  function layoutTimeline() {
    cy.nodes("[kind='colhead']").remove();
    var txs = cy.nodes("[kind='tx']");
    var addrs = cy.nodes("[kind='address']");
    if (!txs.length && !addrs.length) { setCanvasSize(null, null); return; }

    var ROW_H = 46, SUBCOL_W = 44, MIN_SLOT_W = 150, SLOT_GAP = 22, TOP = 80, LEFT = 70;

    // 1. block columns, oldest → newest, left → right.
    var present = {};
    txs.forEach(function (n) { present[n.data("height")] = true; });
    var heights = Object.keys(present).map(Number).sort(function (a, b) { return a - b; });
    var colOf = {};
    heights.forEach(function (h, i) { colOf[h] = i; });

    // 2. horizontal coordinate per node (column units → half-col bucket).
    var xc = {};
    txs.forEach(function (n) { xc[n.id()] = colOf[n.data("height")]; });
    addrs.forEach(function (n) {
      var produced = [], consumed = [];   // cols of paying / funded txs
      n.connectedEdges().forEach(function (e) {
        var src = e.data("source"), tgt = e.data("target");
        if (tgt === n.id()) {              // tx → addr : address received
          var tp = cy.getElementById(src);
          if (tp.data("kind") === "tx") produced.push(colOf[tp.data("height")]);
        } else if (src === n.id()) {        // addr → tx : address funded
          var tc = cy.getElementById(tgt);
          if (tc.data("kind") === "tx") consumed.push(colOf[tc.data("height")]);
        }
      });
      var x;
      if (produced.length && consumed.length) {
        x = (Math.max.apply(null, produced) + Math.min.apply(null, consumed)) / 2;
      } else if (consumed.length) {
        x = Math.min.apply(null, consumed) - 0.5;   // pure source: left of block
      } else if (produced.length) {
        x = Math.max.apply(null, produced) + 0.5;   // pure sink: right of block
      } else {
        x = 0;
      }
      xc[n.id()] = x;
    });
    function bucket(id) { return Math.round(xc[id] * 2); }

    // 3. vertical order: barycenter sweeps, re-ranked per bucket (1-D order).
    var nodes = cy.nodes("[kind!='colhead']");
    var y = {};
    nodes.forEach(function (n, i) { y[n.id()] = i; });
    for (var iter = 0; iter < 4; iter++) {
      nodes.forEach(function (n) {
        var nb = n.connectedEdges().connectedNodes("[kind!='colhead']");
        if (nb.length) {
          var s = 0; nb.forEach(function (m) { s += y[m.id()]; });
          y[n.id()] = s / nb.length;
        }
      });
      var buckets = {};
      nodes.forEach(function (n) {
        var k = bucket(n.id());
        (buckets[k] = buckets[k] || []).push(n.id());
      });
      Object.keys(buckets).forEach(function (k) {
        buckets[k].sort(function (a, b) { return y[a] - y[b]; });
        buckets[k].forEach(function (id, idx) { y[id] = idx; });
      });
    }

    // 4. lay buckets out left→right as variable-width slots; wide buckets
    //    wrap into a grid (cols × ≤TL_MAX_ROWS). Slot width grows with the
    //    grid so adjacent slots never overlap.
    var byBucket = {};
    nodes.forEach(function (n) {
      var k = bucket(n.id());
      (byBucket[k] = byBucket[k] || []).push(n.id());
    });
    var keys = Object.keys(byBucket).map(Number).sort(function (a, b) { return a - b; });

    var cursorX = LEFT, maxRow = 0, headerX = {};
    cy.startBatch();
    keys.forEach(function (k) {
      var ids = byBucket[k];
      ids.sort(function (a, b) { return y[a] - y[b]; });
      var cols = Math.max(1, Math.ceil(ids.length / TL_MAX_ROWS));
      var slotW = Math.max(MIN_SLOT_W, cols * SUBCOL_W);
      var centerX = cursorX + slotW / 2;
      var gridW = (cols - 1) * SUBCOL_W;
      ids.forEach(function (id, i) {
        var subcol = Math.floor(i / TL_MAX_ROWS);
        var subrow = i % TL_MAX_ROWS;
        cy.getElementById(id).position({
          x: centerX - gridW / 2 + subcol * SUBCOL_W,
          y: TOP + subrow * ROW_H,
        });
        if (subrow > maxRow) maxRow = subrow;
      });
      headerX[k] = centerX;
      cursorX += slotW + SLOT_GAP;
    });

    // block headers above each tx bucket (tx bucket key = 2 * column index).
    heights.forEach(function (h) {
      var k = 2 * colOf[h];
      if (headerX[k] === undefined) return;
      cy.add({ group: "nodes",
               data: { id: "colhead-" + h, kind: "colhead", label: "block " + h },
               position: { x: headerX[k], y: 36 } });
    });
    cy.endBatch();

    // 5. size canvas → scrollbars in #cy-wrap.
    setCanvasSize(cursorX + LEFT, Math.max(TOP + (maxRow + 2) * ROW_H, cyWrap.clientHeight || 600));
    cy.userPanningEnabled(false);
    cy.userZoomingEnabled(false);
    cy.zoom(1);
    cy.pan({ x: 0, y: 0 });
  }

  function setView(mode) {
    viewMode = mode;
    document.getElementById("view-force").classList.toggle("active", mode === "force");
    document.getElementById("view-timeline").classList.toggle("active", mode === "timeline");
    applyLayout();
  }

  // ---------------------------------------------------------------- expand

  // Direction slice: trim a 1-hop neighborhood to one flow direction so
  // expansion follows a trail without fanning the other way.
  //   "forward" (spent)  — keep the seed, the txs it FUNDS, and those txs'
  //                        OUTPUT addresses (where its money went).
  //   "back" (source)    — keep the seed, the txs that PAY it, and those
  //                        txs' INPUT addresses (where its money came from).
  //   "both"             — unchanged.
  // Edge ids encode direction (in:addr:tx / out:tx:addr); we confirm via
  // the node kind map.
  function directionSlice(data, seed, dir) {
    if (dir === "both") return data;
    var fwd = (dir === "forward");
    var kind = {};
    data.nodes.forEach(function (n) { kind[n.id] = n.kind; });
    // Transactions one hop along the chosen direction from the seed.
    var keepTx = {};
    data.edges.forEach(function (e) {
      if (fwd) {                         // seed -IN-> tx : seed funded this tx
        if (e.source === seed && kind[e.source] === "address" && kind[e.target] === "tx") keepTx[e.target] = true;
      } else {                           // tx -OUT-> seed : this tx paid the seed
        if (e.target === seed && kind[e.source] === "tx" && kind[e.target] === "address") keepTx[e.source] = true;
      }
    });
    var keep = {};
    keep[seed] = true;
    var edges = data.edges.filter(function (e) {
      if (fwd) {
        if (e.source === seed && keepTx[e.target]) { keep[e.target] = true; return true; }         // seed -> tx
        if (keepTx[e.source] && kind[e.target] === "address") { keep[e.source] = true; keep[e.target] = true; return true; } // tx -> out addr
      } else {
        if (keepTx[e.source] && e.target === seed) { keep[e.source] = true; return true; }          // tx -> seed
        if (kind[e.source] === "address" && keepTx[e.target]) { keep[e.source] = true; keep[e.target] = true; return true; } // in addr -> tx
      }
      return false;
    });
    return {
      nodes: data.nodes.filter(function (n) { return keep[n.id]; }),
      edges: edges,
      truncated: data.truncated,
    };
  }

  // BFS outward from one or more seed addresses. Each hop fetches its
  // frontier in parallel (bounded calls), merges, lays out once at the
  // end. depth 1 from a single seed == "expand this node one hop". dir
  // ("both" | "forward" | "back") limits which side of each node is drawn
  // and chased — forward follows where money went, back its source.
  function expandSeeds(seeds, depth, markId, dir) {
    dir = dir || "both";
    seeds = [].concat(seeds);
    if (!seeds.length) return Promise.resolve();
    expandAbort = false;
    var visited = {};
    seeds.forEach(function (s) { visited[s] = true; });
    var frontier = seeds.slice();
    var remaining = depth, capped = false;
    var dirNote = dir === "forward" ? " (downstream only)"
                : dir === "back" ? " (source only)" : "";

    function hop() {
      if (expandAbort || !frontier.length || remaining <= 0 || cy.nodes().length >= MAX_NODES) {
        return Promise.resolve();
      }
      remaining--;
      var batch = frontier;
      if (batch.length > MAX_FRONTIER) { batch = batch.slice(0, MAX_FRONTIER); capped = true; }
      frontier = [];
      showExpanding("Expanding hop " + (depth - remaining) + " — " +
                    batch.length + " address" + (batch.length === 1 ? "" : "es") + dirNote +
                    "… (" + cy.nodes("[kind!='colhead']").length + " nodes so far)");
      return Promise.all(batch.map(function (addr) {
        return api("/address/" + encodeURIComponent(addr) + filterQuery())
          .then(function (data) {
            var slice = directionSlice(data, addr, dir);
            addElements(slice);
            // Advance the BFS through the chosen-direction counterparties —
            // INCLUDING any already on the canvas — so the trail keeps going
            // instead of dead-ending the moment a neighbour is already drawn.
            slice.nodes.forEach(function (n) {
              if (n.kind === "address" && n.addr !== addr && !visited[n.addr]) {
                visited[n.addr] = true; frontier.push(n.addr);
              }
            });
          })
          .catch(function () {});
      })).then(hop);
    }

    return hop().then(function () {
      applyLayout();
      if (markId) {
        var node = cy.getElementById(markId);
        if (node.nonempty()) { node.data("is_root", true); node.select(); showDetails(node.data()); }
      }
      if (expandAbort) {
        showBanner("Expansion stopped — " + cy.nodes("[kind!='colhead']").length + " nodes shown.", "warn");
      } else if (cy.nodes().length >= MAX_NODES) {
        showBanner("Reached the " + MAX_NODES + "-node display cap — expansion stopped.", "warn");
      } else if (capped) {
        showBanner("Stopped fanning out past " + MAX_FRONTIER +
                   " addresses per hop — raise Min value to focus the trail.", "warn");
      } else {
        showBanner("Expanded — " + cy.nodes("[kind!='colhead']").length + " nodes shown.");
      }
    });
  }

  function expandOne(addr, mark) { return expandSeeds([addr], 1, mark ? addr : null, "both"); }

  // ---------------------------------------------------------------- paths

  function findPaths() {
    var from = document.getElementById("path-from").value.trim();
    var to = document.getElementById("path-to").value.trim();
    var hops = clamp(parseInt(document.getElementById("path-hops").value, 10) || 5, 1, 50);
    if (!from || !to) { showBanner("Enter both a From and a To address.", "warn"); return; }
    if (from === to) { showBanner("From and To must be different addresses.", "warn"); return; }
    syncUrl({ from: from, to: to, hops: hops });
    showBanner("Finding flows " + shorten(from) + " → " + shorten(to) + "…");
    api("/paths?src=" + encodeURIComponent(from) + "&dst=" + encodeURIComponent(to) + "&maxhops=" + hops)
      .then(function (d) {
        if (!d.nodes.length) {
          showBanner("No money-flow path found within " + hops + " hops.", "warn");
          return;
        }
        addElements(d);
        [from, to].forEach(function (id) {
          var n = cy.getElementById(id);
          if (n.nonempty()) n.data("is_root", true);
        });
        setView("timeline");
        cyWrap.scrollLeft = 0;
        showBanner("Showing " + d.paths + (d.truncated ? "+" : "") +
                   " path(s) between the two addresses.");
      })
      .catch(function (err) { showBanner(err.message, "err"); });
  }

  // Attach a second source wallet to the current investigation: forward-BFS
  // from `addr` (downstream) until it reaches a node ALREADY on the canvas,
  // drawing the connector. Answers "does this wallet flow into anything I'm
  // looking at?" — e.g. a second victim's lead feeding the same merge.
  function pathIntoGraph(addr) {
    addr = (addr || "").trim();
    if (!addr) { showBanner("Enter an address in the 'from' box first.", "warn"); return; }
    var preexisting = {};
    cy.nodes("[kind!='colhead']").forEach(function (n) { preexisting[n.id()] = true; });
    if (!Object.keys(preexisting).length) {
      showBanner("Graph is empty — search or Find paths first, then attach a wallet.", "warn");
      return;
    }
    if (preexisting[addr]) {
      var ex = cy.getElementById(addr);
      if (ex.nonempty()) { ex.select(); showDetails(ex.data()); }
      showBanner("That address is already on the graph.", "warn");
      return;
    }
    expandAbort = false;
    var visited = {}; visited[addr] = true;
    var frontier = [addr];
    var maxHops = clamp(currentDepth, 1, 50), hops = 0, hit = false;
    function step() {
      if (expandAbort || hit || !frontier.length || hops >= maxHops || cy.nodes().length >= MAX_NODES) {
        return Promise.resolve();
      }
      hops++;
      var batch = frontier.slice(0, MAX_FRONTIER);
      frontier = [];
      showExpanding("Searching for a path from " + shorten(addr, 10) + " into the graph — hop " + hops + "…");
      return Promise.all(batch.map(function (a) {
        return api("/address/" + encodeURIComponent(a) + filterQuery())
          .then(function (data) {
            var slice = directionSlice(data, a, "forward");
            addElements(slice);
            slice.nodes.forEach(function (n) {
              if (n.id !== a && preexisting[n.id]) hit = true;          // reached a node already on the graph
              if (n.kind === "address" && n.addr !== a && !visited[n.addr]) {
                visited[n.addr] = true; frontier.push(n.addr);
              }
            });
          })
          .catch(function () {});
      })).then(step);
    }
    return step().then(function () {
      applyLayout();
      var node = cy.getElementById(addr);
      if (node.nonempty()) { node.data("is_root", true); node.select(); showDetails(node.data()); }
      if (hit) showBanner("Connected — drew a path from " + shorten(addr, 10) + " into the current graph.", "ok");
      else if (expandAbort) showBanner("Search stopped.", "warn");
      else showBanner("No path from " + shorten(addr, 10) + " into the graph within " + maxHops + " hops.", "warn");
    });
  }

  // ---------------------------------------------------------------- trim

  // Right-click trims the node plus everything reachable downstream of it
  // (its child branches), condensing the view. Reversible by re-expanding.
  cyEl.addEventListener("contextmenu", function (ev) { ev.preventDefault(); });
  cy.on("cxttap", "node", function (ev) {
    var n = ev.target;
    if (n.data("kind") === "colhead") return;
    var doomed = n.successors().add(n);
    var count = doomed.nodes("[kind!='colhead']").length;
    doomed.remove();
    showBanner("Trimmed " + count + " node" + (count === 1 ? "" : "s") + " downstream.");
    if (cy.nodes("[kind!='colhead']").length) applyLayout();
    else { panelBody.style.display = "none"; panelEmpty.style.display = ""; }
  });

  // ---------------------------------------------------------------- labels

  function setLabel(id, text) {
    text = (text || "").trim().slice(0, 60);
    if (text) LABELS[id] = text; else delete LABELS[id];
    saveLabels();
    var node = cy.getElementById(id);
    if (node.nonempty()) {
      if (text) {
        node.data("userLabel", text);
        node.data("label", text);
      } else {
        node.removeData("userLabel");
        node.data("label", node.data("kind") === "tx"
          ? "block " + node.data("height")
          : shorten(node.data("addr"), 8));
      }
    }
  }

  function labelEditorHtml(id) {
    return "<h3>Label</h3><div class='label-edit'>" +
      "<input id='node-label-input' type='text' maxlength='60' " +
      "placeholder='Annotate this node…' value='" + escapeHtml(LABELS[id] || "") + "'>" +
      "<button data-act='savelabel' data-id='" + escapeHtml(id) + "'>Save</button>" +
      "</div><div class='hint'>Saved in this browser only.</div>";
  }

  function dirOption(val, label) {
    return "<option value='" + val + "'" + (expandDir === val ? " selected" : "") + ">" + label + "</option>";
  }

  function expandControlsHtml(act, id) {
    return "<div class='actions'>" +
      "<button data-act='" + act + "' data-id='" + escapeHtml(id) + "'>Expand flows</button>" +
      "<label class='depth-inline'>hops <input id='node-depth' type='number' " +
      "min='1' max='50' value='" + currentDepth + "'></label>" +
      "<label class='dir-inline' title='Which way to follow the money'>trace " +
      "<select id='node-dir'>" +
      dirOption("both", "both ways") +
      dirOption("forward", "forward (spent)") +
      dirOption("back", "back (source)") +
      "</select></label>";
  }

  // ---------------------------------------------------------------- details

  function row(k, v) {
    return "<tr><td>" + k + "</td><td>" + v + "</td></tr>";
  }

  // Aggregated 1-hop counterparties for an address: who funded the txs that
  // paid it (sources) and who its txs paid (destinations), ranked by value.
  // Fetched async and appended to the address detail; rows reuse the
  // existing goto handler so a click navigates to that counterparty.
  function loadCounterparties(addr) {
    function list(title, rows) {
      if (!rows || !rows.length) return "";
      return "<h3>" + title + "</h3><div class='flow-list'>" + rows.map(function (r) {
        return "<div class='flow-row' data-act='goto' data-id='" + escapeHtml(r.addr) + "'>" +
          "<span>" + shorten(r.addr, 12) + "</span>" +
          "<span class='val'>" + fmtBtc(r.value) + " · " + r.txs + "tx</span></div>";
      }).join("") + "</div>";
    }
    api("/address/" + encodeURIComponent(addr) + "/counterparties")
      .then(function (j) {
        var sec = document.getElementById("cp-section");
        if (!sec) return;
        var html = list("Top sources (1 hop)", j.senders) +
                   list("Top destinations (1 hop)", j.receivers);
        sec.className = "";
        sec.innerHTML = html;
      })
      .catch(function () {
        var sec = document.getElementById("cp-section");
        if (sec) sec.innerHTML = "";
      });
  }

  function showDetails(d) {
    panelEmpty.style.display = "none";
    panelBody.style.display = "";
    if (d.kind === "address") {
      panelBody.innerHTML =
        "<h3>Address</h3><div class='mono'>" + escapeHtml(d.addr) + "</div>" +
        "<table>" +
        row("Received", fmtBtc(d.total_in)) +
        row("Spent", fmtBtc(d.total_out)) +
        row("Balance", fmtBtc((d.total_in || 0) - (d.total_out || 0))) +
        row("Transactions", d.n_tx) +
        row("First seen", fmtTime(d.first_seen)) +
        row("Last seen", fmtTime(d.last_seen)) +
        row("Cluster", "#" + d.cluster_id + " (" + d.cluster_size +
            " address" + (d.cluster_size === 1 ? "" : "es") + ")") +
        "</table>" +
        expandControlsHtml("expand", d.addr) +
        (d.cluster_size > 1
          ? "<button data-act='cluster' data-id='" + d.cluster_id + "'>Show cluster</button>"
          : "") +
        "</div>" +
        "<div id='cp-section' class='cp-loading'>Loading top counterparties…</div>" +
        labelEditorHtml(d.addr);
      loadCounterparties(d.addr);
    } else {
      api("/tx/" + d.txid).then(function (info) {
        var tx = info.tx;
        txNeighbors[tx.txid] = {
          ins: info.inputs.map(function (f) { return f.addr; }),
          outs: info.outputs.map(function (f) { return f.addr; }),
        };
        var flows = function (list, title) {
          if (!list.length) return "";
          return "<h3>" + title + "</h3><div class='flow-list'>" +
            list.map(function (f) {
              return "<div class='flow-row' data-act='goto' data-id='" +
                escapeHtml(f.addr) + "'><span>" + shorten(f.addr, 12) +
                "</span><span class='val'>" + fmtBtc(f.value) + "</span></div>";
            }).join("") + "</div>";
        };
        panelBody.innerHTML =
          "<h3>Transaction</h3><div class='mono'>" + escapeHtml(tx.txid) + "</div>" +
          "<table>" +
          row("Block", tx.height) +
          row("Time", fmtTime(tx.time)) +
          row("Fee", tx.is_coinbase ? "coinbase" : fmtBtc(tx.fee)) +
          row("Inputs / Outputs", tx.n_in + " / " + tx.n_out) +
          "</table>" +
          (tx.op_return
            ? "<h3>OP_RETURN</h3><div class='opret'>" + escapeHtml(tx.op_return) + "</div>"
            : "") +
          expandControlsHtml("expand-tx", tx.txid) + "</div>" +
          flows(info.inputs, "From") +
          flows(info.outputs, "To") +
          labelEditorHtml(tx.txid);
      }).catch(function (err) { showBanner(err.message, "err"); });
    }
  }

  // Keep the expand settings synced with whichever panel is on screen.
  panelBody.addEventListener("input", function (ev) {
    if (ev.target.id === "node-depth") {
      currentDepth = clamp(parseInt(ev.target.value, 10) || 1, 1, 6);
    }
  });
  panelBody.addEventListener("change", function (ev) {
    if (ev.target.id === "node-dir") { expandDir = ev.target.value; }
  });

  // Enter in the label field saves (the id rides on the Save button).
  panelBody.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter" || ev.target.id !== "node-label-input") return;
    var btn = panelBody.querySelector("[data-act='savelabel']");
    if (!btn) return;
    setLabel(btn.dataset.id, ev.target.value);
    showBanner(ev.target.value.trim() ? "Label saved" : "Label cleared");
  });

  panelBody.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-act]");
    if (!t) return;
    var id = t.dataset.id;
    if (t.dataset.act === "expand") {
      expandSeeds([id], currentDepth, id, expandDir);
    } else if (t.dataset.act === "expand-tx") {
      var nb = txNeighbors[id] || { ins: [], outs: [] };
      // From a tx: forward = its outputs onward, back = its inputs, both = either.
      var seeds = expandDir === "forward" ? nb.outs
                : expandDir === "back" ? nb.ins
                : nb.ins.concat(nb.outs);
      if (!seeds.length) { showBanner("No counterparties to expand.", "warn"); return; }
      expandSeeds(seeds, currentDepth, null, expandDir);
    } else if (t.dataset.act === "goto") {
      var node = cy.getElementById(id);
      if (node.nonempty()) {
        node.select();
        if (viewMode === "force") cy.animate({ center: { eles: node }, duration: 250 });
        showDetails(node.data());
      } else {
        expandOne(id, false);
      }
    } else if (t.dataset.act === "savelabel") {
      var input = document.getElementById("node-label-input");
      setLabel(id, input ? input.value : "");
      showBanner((input && input.value.trim()) ? "Label saved" : "Label cleared");
    } else if (t.dataset.act === "cluster") {
      api("/cluster/" + id).then(function (info) {
        panelBody.innerHTML =
          "<h3>Cluster #" + info.cluster_id + "</h3>" +
          "<p class='muted' style='font-size:12px'>Addresses spending together " +
          "(common-input-ownership heuristic)" +
          (info.truncated ? " — truncated to 500" : "") + ":</p>" +
          "<div class='flow-list'>" +
          info.addresses.map(function (a) {
            return "<div class='flow-row' data-act='goto' data-id='" +
              escapeHtml(a.addr) + "'><span>" + shorten(a.addr, 12) +
              "</span><span class='val'>" + a.n_tx + " tx</span></div>";
          }).join("") + "</div>";
      }).catch(function (err) { showBanner(err.message, "err"); });
    }
  });

  cy.on("tap", "node", function (ev) {
    if (ev.target.data("kind") === "colhead") return;
    showDetails(ev.target.data());
  });
  cy.on("dbltap", "node[kind='address']", function (ev) {
    expandOne(ev.target.data("addr"), false);
  });

  // ---------------------------------------------------------------- search

  var searchInput = document.getElementById("search");
  var searchResults = document.getElementById("search-results");
  var searchTimer = null;

  function renderMatches(matches) {
    if (!matches.length) {
      searchResults.innerHTML = "<div class='search-row'><span class='tag'>no matches</span></div>";
    } else {
      searchResults.innerHTML = matches.map(function (m) {
        return "<div class='search-row' data-id='" + escapeHtml(m.id) +
          "' data-kind='" + m.kind + "'><span>" + shorten(m.id, 18) +
          "</span><span class='tag'>" +
          (m.kind === "tx" ? "tx" : (m.n_tx + " tx")) + "</span></div>";
      }).join("");
    }
    searchResults.classList.add("show");
  }

  searchInput.addEventListener("input", function () {
    clearTimeout(searchTimer);
    var q = searchInput.value.trim();
    if (q.length < 3) { searchResults.classList.remove("show"); return; }
    searchTimer = setTimeout(function () {
      api("/search?q=" + encodeURIComponent(q))
        .then(function (j) { renderMatches(j.matches); })
        .catch(function () {});
    }, 250);
  });

  searchResults.addEventListener("click", function (ev) {
    var rowEl = ev.target.closest(".search-row[data-id]");
    if (!rowEl) return;
    searchResults.classList.remove("show");
    searchInput.value = rowEl.dataset.id;
    if (rowEl.dataset.kind === "tx") {
      showDetails({ kind: "tx", txid: rowEl.dataset.id });
    } else {
      syncUrl({ start: rowEl.dataset.id, depth: currentDepth > 1 ? currentDepth : "",
                dir: expandDir !== "both" ? expandDir : "" });
      expandSeeds([rowEl.dataset.id], currentDepth, rowEl.dataset.id, expandDir);
    }
  });

  document.addEventListener("click", function (ev) {
    if (!searchResults.contains(ev.target) && ev.target !== searchInput) {
      searchResults.classList.remove("show");
    }
  });

  searchInput.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter") return;
    var q = searchInput.value.trim();
    if (!q) return;
    searchResults.classList.remove("show");
    if (q.length === 64 && /^[0-9a-fA-F]+$/.test(q)) {
      showDetails({ kind: "tx", txid: q.toLowerCase() });
    } else {
      syncUrl({ start: q, depth: currentDepth > 1 ? currentDepth : "",
                dir: expandDir !== "both" ? expandDir : "" });
      expandSeeds([q], currentDepth, q, expandDir);
    }
  });

  // ---------------------------------------------------------------- toolbar

  document.getElementById("view-force").addEventListener("click", function () { setView("force"); });
  document.getElementById("view-timeline").addEventListener("click", function () { setView("timeline"); });
  document.getElementById("btn-paths").addEventListener("click", findPaths);
  document.getElementById("btn-into-graph").addEventListener("click", function () {
    pathIntoGraph(document.getElementById("path-from").value);
  });
  document.getElementById("btn-fit").addEventListener("click", function () {
    if (viewMode === "timeline") { cyWrap.scrollLeft = 0; cyWrap.scrollTop = 0; }
    else cy.fit(undefined, 40);
  });
  document.getElementById("btn-clear").addEventListener("click", function () {
    cy.elements().remove();
    panelBody.style.display = "none";
    panelEmpty.style.display = "";
    applyLayout();
  });

  // Full-screen just the canvas (no header/side panel — only the graph).
  // Exit with Esc. Re-fit after the transition so it uses the new space.
  var fsBtn = document.getElementById("btn-fullscreen");
  function inFullscreen() { return !!document.fullscreenElement; }
  fsBtn.addEventListener("click", function () {
    if (inFullscreen()) {
      if (document.exitFullscreen) document.exitFullscreen();
    } else if (cyWrap.requestFullscreen) {
      cyWrap.requestFullscreen().catch(function () {});
    }
  });
  document.addEventListener("fullscreenchange", function () {
    fsBtn.textContent = inFullscreen() ? "Exit full screen" : "Full screen";
    setTimeout(function () {
      cy.resize();
      if (viewMode === "timeline") applyLayout(); else cy.fit(undefined, 40);
    }, 120);
  });

  // Export: a PNG of the whole graph, or a CSV of the visible nodes + flows.
  function download(href, name) {
    var a = document.createElement("a");
    a.href = href; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
  }
  document.getElementById("btn-png").addEventListener("click", function () {
    if (!cy.nodes().length) { showBanner("Nothing to export yet.", "warn"); return; }
    var bg = getComputedStyle(document.body).backgroundColor || "#0d1117";
    download(cy.png({ full: true, scale: 2, bg: bg }), "chaingraph.png");
  });
  document.getElementById("btn-csv").addEventListener("click", function () {
    if (!cy.nodes().length) { showBanner("Nothing to export yet.", "warn"); return; }
    function q(s) { s = String(s == null ? "" : s); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
    var rows = ["record,id,kind,label,a,b,c"];
    cy.nodes("[kind!='colhead']").forEach(function (n) {
      var d = n.data();
      if (d.kind === "address") {
        rows.push(["node", q(d.addr), "address", q(LABELS[d.addr] || ""),
                   "recv=" + (d.total_in || 0), "spent=" + (d.total_out || 0),
                   "cluster=" + d.cluster_id].join(","));
      } else {
        rows.push(["node", q(d.txid), "tx", q(LABELS[d.txid] || ""),
                   "block=" + d.height, "time=" + d.time, ""].join(","));
      }
    });
    cy.edges().forEach(function (e) {
      var d = e.data();
      rows.push(["edge", q(d.id), "flow", "", "from=" + q(d.source), "to=" + q(d.target),
                 "value=" + (d.value || 0)].join(","));
    });
    download("data:text/csv;charset=utf-8," + encodeURIComponent(rows.join("\n")), "chaingraph.csv");
  });

  // ---------------------------------------------------------------- url state

  // Reflect the current query into the address bar (no history spam) so a
  // view is copy-pasteable. Empty/null values are dropped.
  function syncUrl(obj) {
    var p = new URLSearchParams();
    Object.keys(obj).forEach(function (k) {
      if (obj[k] !== "" && obj[k] != null) p.set(k, obj[k]);
    });
    var qs = p.toString();
    history.replaceState(null, "", qs ? (location.pathname + "?" + qs) : location.pathname);
  }

  // Read params on load: ?start auto-expands one address; ?from&?to auto-runs
  // the pathfinder. Companions: ?hops (path), ?depth (expand), ?forward.
  // Auto-draw is deferred to pendingAuto and fired once the graph is ready;
  // if both a start and a from/to pair are given, fields are filled but
  // nothing is drawn (ambiguous which view was intended).
  function initFromUrl() {
    var p = new URLSearchParams(location.search);
    var start = (p.get("start") || "").trim();
    var from = (p.get("from") || "").trim();
    var to = (p.get("to") || "").trim();
    if (p.get("hops")) {
      document.getElementById("path-hops").value = clamp(parseInt(p.get("hops"), 10) || 5, 1, 50);
    }
    if (p.get("depth")) currentDepth = clamp(parseInt(p.get("depth"), 10) || 1, 1, 6);
    // dir=forward|back|both; legacy forward=1 maps to forward.
    var dirParam = (p.get("dir") || "").toLowerCase();
    if (dirParam === "forward" || dirParam === "back" || dirParam === "both") expandDir = dirParam;
    else if (p.get("forward") != null && /^(1|true|yes|on)$/i.test(p.get("forward"))) expandDir = "forward";
    if (from) document.getElementById("path-from").value = from;
    if (to) document.getElementById("path-to").value = to;
    if (start) document.getElementById("search").value = start;

    var hasStart = !!start, hasPath = !!(from && to);
    if (hasStart && !hasPath) {
      pendingAuto = function () { expandSeeds([start], currentDepth, start, expandDir); };
    } else if (hasPath && !hasStart) {
      pendingAuto = function () { findPaths(); };
    }
  }

  // ---------------------------------------------------------------- status

  function refreshStatus() {
    api("/status").then(function (s) {
      if (!s.enabled) {
        statusChip.textContent = "tool disabled";
        statusChip.className = "status warn";
      } else if (s.state === "ready") {
        statusChip.textContent = "evidence graph @ block " + s.height +
          " · " + s.n_addr + " addresses · " + s.n_tx + " txs";
        statusChip.className = "status ok";
        if (!chainRange && s.t_min) {
          chainRange = { t_min: s.t_min, t_max: s.t_max };
          var f = document.getElementById("f-from");
          var t = document.getElementById("f-to");
          if (!f.value) f.value = epochToLocal(s.t_min);
          if (!t.value) t.value = epochToLocal(s.t_max + 60);
        }
        if (pendingAuto) { var run = pendingAuto; pendingAuto = null; run(); }
      } else if (s.state === "building") {
        var pct = "";
        if (s.blocks_total) {
          pct = " " + Math.round(100 * s.blocks_done / s.blocks_total) + "%";
        } else if (s.rows_total) {
          pct = " " + Math.round(100 * s.rows_done / s.rows_total) + "%";
        }
        statusChip.textContent = "rebuilding" + pct + " (" + (s.phase || s.detail || "…") + ")";
        statusChip.className = "status warn";
      } else {
        statusChip.textContent = "graph " + (s.state || "empty");
        statusChip.className = "status";
      }
    }).catch(function () {
      statusChip.textContent = "unreachable";
      statusChip.className = "status";
    });
  }
  initFromUrl();
  refreshStatus();
  setInterval(refreshStatus, 5000);
})();
