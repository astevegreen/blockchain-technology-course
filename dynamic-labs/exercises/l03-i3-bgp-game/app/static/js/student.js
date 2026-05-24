(function () {
  const state = {
    snapshot: null,
    error: "",
    connected: false,
    desiredMode: "collab",
    graphStage: 1,
    stage3ShowHonestEdges: false,
    stage3ShowMaliciousEdges: false,
    graphSelection: null,
    graphRoomId: null,
    soloDraft: {
      size: 8,
      numTraitors: 2,
    },
    pendingSelfServiceConflict: null,
  };

  const refs = {
    connectionPill: document.getElementById("connection-pill"),
    roomPill: document.getElementById("room-pill"),
    playerPill: document.getElementById("player-pill"),
    phasePill: document.getElementById("phase-pill"),
    alert: document.getElementById("student-alert"),
    stage: document.getElementById("student-stage"),
    side: document.getElementById("student-side-content"),
    subtitle: document.getElementById("student-subtitle"),
    debriefPanel: document.getElementById("student-debrief-panel"),
    graphRoomPill: document.getElementById("student-graph-room-pill"),
    graphSummary: document.getElementById("student-graph-summary"),
    graphCanvas: document.getElementById("student-graph-canvas"),
    graphControls: document.getElementById("student-graph-controls"),
    graphDetails: document.getElementById("student-graph-details"),
  };

  function getPlayerUuid() {
    const url = new URL(window.location.href);
    const existing = url.searchParams.get("uuid");
    if (existing) {
      return existing;
    }
    const created = window.crypto && window.crypto.randomUUID
      ? window.crypto.randomUUID()
      : `bgp-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    url.searchParams.set("uuid", created);
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    return created;
  }

  function getDesiredMode() {
    const url = new URL(window.location.href);
    const raw = url.searchParams.get("mode");
    const mode = raw === "single" ? "single" : "collab";
    if (raw !== mode) {
      url.searchParams.set("mode", mode);
      window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    }
    return mode;
  }

  function setDesiredMode(mode) {
    const normalizedMode = mode === "single" ? "single" : "collab";
    const url = new URL(window.location.href);
    url.searchParams.set("mode", normalizedMode);
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    state.desiredMode = normalizedMode;
    if (state.connected) {
      socket.emit("register", { uuid: playerUuid, mode: normalizedMode });
    }
    render();
  }

  const playerUuid = getPlayerUuid();
  state.desiredMode = getDesiredMode();
  let studentGraphNetwork = null;
  let currentGraphData = null;
  const socket = io({
    path: window.SOCKETIO_PATH || "/socket.io",
  });

  function setAlert(message) {
    state.error = message || "";
    refs.alert.textContent = state.error;
    refs.alert.classList.toggle("hidden", !state.error);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function badgeClassForRole(role) {
    if (role === "traitor") {
      return "pill pill-bad";
    }
    return "pill pill-good";
  }

  function roleLabel(role) {
    return role === "traitor" ? "MALICIOUS" : "HONEST";
  }

  function valueBadge(value) {
    const className = value === "Attack"
      ? "order-pill order-attack"
      : value === "Retreat"
        ? "order-pill order-retreat"
        : "order-pill order-neutral";
    return `<span class="${className}">${escapeHtml(value || "-")}</span>`;
  }

  function mathStatus(size, traitors) {
    const faultTolerant = (3 * traitors + 1) <= size;
    return {
      text: faultTolerant
        ? `Fault tolerant: ${size} >= 3*${traitors} + 1`
        : `Consensus at risk: ${size} < 3*${traitors} + 1`,
      className: faultTolerant ? "math-badge math-good" : "math-badge math-bad",
    };
  }

  function computeLocalConsensusState(initialValue, peerValues, uncertaintySeed) {
    const attackVotes = peerValues.filter((value) => value === "Attack").length;
    const retreatVotes = peerValues.filter((value) => value === "Retreat").length;
    if (attackVotes > retreatVotes) {
      return { value: "Attack", isTie: false };
    }
    if (retreatVotes > attackVotes) {
      return { value: "Retreat", isTie: false };
    }
    const seedValue = Number.isFinite(Number(uncertaintySeed)) ? Number(uncertaintySeed) : 0;
    const shouldFlip = Math.abs(seedValue) % 100 < 50;
    return {
      value: shouldFlip ? oppositeValue(initialValue) : initialValue,
      isTie: true,
    };
  }

  function localConsensusState(snapshot) {
    return computeLocalConsensusState(
      snapshot.player.initial_value,
      snapshot.messages.map((message) => message.value),
      snapshot.player.uncertainty_seed,
    );
  }

  function oppositeValue(value) {
    return value === "Attack" ? "Retreat" : "Attack";
  }

  function visibleEdgesForStage(debrief, stage) {
    if (!debrief) {
      return [];
    }
    if (stage === 1) {
      return debrief.edges.filter((edge) => edge.sender_role === "honest");
    }
    if (stage === 2) {
      return debrief.edges.filter((edge) => edge.sender_role === "traitor");
    }
    if (stage === 3) {
      return debrief.edges.filter((edge) => {
        if (edge.sender_role === "honest") {
          return state.stage3ShowHonestEdges;
        }
        if (edge.sender_role === "traitor") {
          return state.stage3ShowMaliciousEdges;
        }
        return false;
      });
    }
    return [];
  }

  function graphStageLabel(stage) {
    if (stage === 1) {
      return "Honest";
    }
    if (stage === 2) {
      return "Dishonest";
    }
    return "Summary";
  }

  function inspectorEdgesForStage(debrief, stage) {
    if (stage === 3) {
      return debrief ? debrief.edges : [];
    }
    return visibleEdgesForStage(debrief, stage);
  }

  function renderNodeTraffic(debrief, nodeId, stage) {
    const stageEdges = inspectorEdgesForStage(debrief, stage);
    const sentMessages = stageEdges.filter((edge) => edge.from === nodeId);
    const receivedMessages = stageEdges.filter((edge) => edge.to === nodeId);
    const stageLabel = stage === 3 ? "In This Round" : "In This Stage";
    const sentMarkup = sentMessages.length
      ? sentMessages.map((edge) => `
          <div class="message-card">
            <strong>To Node ${escapeHtml(edge.to)}</strong>
            <span>${escapeHtml(edge.value)} | ${escapeHtml(roleLabel(edge.sender_role))}</span>
          </div>
        `).join("")
      : `<div class="message-card">No outbound messages are visible ${stage === 3 ? "for this node in the round" : "in this stage"}.</div>`;
    const receivedMarkup = receivedMessages.length
      ? receivedMessages.map((edge) => `
          <div class="message-card">
            <strong>From Node ${escapeHtml(edge.from)}</strong>
            <span>${escapeHtml(edge.value)} | ${escapeHtml(roleLabel(edge.sender_role))}</span>
          </div>
        `).join("")
      : `<div class="message-card">No inbound messages are visible ${stage === 3 ? "for this node in the round" : "in this stage"}.</div>`;

    return `
      <h4>Sent ${stageLabel}</h4>
      <div class="message-list">${sentMarkup}</div>
      <h4>Received ${stageLabel}</h4>
      <div class="message-list">${receivedMarkup}</div>
    `;
  }

  function shouldShowDebriefExplorer(snapshot) {
    return Boolean(snapshot && snapshot.view === "debrief" && snapshot.debrief);
  }

  function graphFit() {
    if (!studentGraphNetwork) {
      return;
    }
    studentGraphNetwork.fit({
      animation: {
        duration: 220,
        easingFunction: "easeInOutQuad",
      },
    });
  }

  function graphZoom(multiplier) {
    if (!studentGraphNetwork) {
      return;
    }
    const scale = studentGraphNetwork.getScale();
    studentGraphNetwork.moveTo({
      scale: Math.max(0.35, Math.min(scale * multiplier, 2.6)),
      animation: {
        duration: 180,
        easingFunction: "easeInOutQuad",
      },
    });
  }

  function nodeColor(player, stage, correctConsensus) {
    if (stage >= 3 && player.role !== "traitor") {
      return player.survived ? "#20654a" : "#a53a2f";
    }
    if (stage >= 2 && player.role === "traitor") {
      return "#7a5330";
    }
    return "#b9ac95";
  }

  function buildEdgePresentation(edge) {
    const isHonest = edge.sender_role === "honest";
    return {
      idPrefix: isHonest ? "honest" : "traitor",
      title: isHonest
        ? `${edge.from} -> ${edge.to}: ${edge.value}`
        : `${edge.from} -> ${edge.to}: ${edge.value} (malicious message)`,
      color: isHonest ? "#20654a" : edge.value === "Attack" ? "#bf4732" : "#2c6e95",
      dashes: !isHonest,
      width: isHonest ? 3 : 5,
      smoothType: isHonest ? "curvedCW" : "curvedCCW",
      roundness: isHonest ? 0.18 : 0.24,
    };
  }

  function nodeLabel(player, stage) {
    if (stage >= 3) {
      return `${player.node_id}\n${player.final_vote || "-"}`;
    }
    if (stage >= 2) {
      return player.role === "traitor"
        ? `${player.node_id}\nmalicious`
        : `${player.node_id}\n${player.initial_value}`;
    }
    return `${player.node_id}\n${player.initial_value}`;
  }

  function buildGraphData(debrief, stage) {
    const radius = Math.max(260, Math.min(420, 120 + debrief.players.length * 22));
    const nodes = debrief.players.map((player, index) => {
      const angle = (Math.PI * 2 * index) / Math.max(debrief.players.length, 1);
      const title = stage >= 3
        ? `Node ${player.node_id}: ${player.label} | role: ${roleLabel(player.role)} | initial: ${player.initial_value} | local consensus: ${player.local_consensus || "-"} | final: ${player.final_vote || "-"}`
        : `Node ${player.node_id}: ${player.label} | role: ${roleLabel(player.role)} | initial broadcast: ${player.initial_value}`;
      return {
        id: player.node_id,
        label: nodeLabel(player, stage),
        x: Math.round(Math.cos(angle) * radius),
        y: Math.round(Math.sin(angle) * radius),
        physics: false,
        fixed: true,
        shape: "dot",
        size: 36,
        title,
        inspect: player,
        color: {
          background: nodeColor(player, stage, debrief.correct_consensus),
          border: "#3d3121",
        },
        font: {
          color: "#251d13",
          size: 20,
          face: "Avenir Next",
          multi: true,
        },
      };
    });

    const edges = visibleEdgesForStage(debrief, stage).map((edge, index) => {
      const presentation = buildEdgePresentation(edge);
      return {
        id: `${presentation.idPrefix}-${edge.from}-${edge.to}-${index}`,
        from: edge.from,
        to: edge.to,
        label: edge.value,
        arrows: "to",
        title: presentation.title,
        inspect: edge,
        color: { color: presentation.color },
        dashes: presentation.dashes,
        width: presentation.width,
        smooth: { type: presentation.smoothType, roundness: presentation.roundness },
        font: {
          size: 18,
          face: "Avenir Next",
          background: "rgba(255, 252, 246, 0.86)",
          strokeWidth: 0,
        },
      };
    });

    return { nodes, edges };
  }

  function updateGraphSummary(debrief) {
    if (!debrief) {
      refs.graphSummary.textContent = "The debrief explorer will appear here once your room is complete and revealed.";
      return;
    }

    if (state.graphStage === 1) {
      refs.graphSummary.innerHTML = `
        <strong>Honest View:</strong> All nodes are visible, but only honest-message edges are shown so you can isolate the consistent broadcasts.
      `;
      return;
    }

    if (state.graphStage === 2) {
      refs.graphSummary.innerHTML = `
        <strong>Dishonest View:</strong> All nodes remain visible, but only malicious-message edges are shown so the conflicting broadcasts stand out clearly.
      `;
      return;
    }

    const honestPlayers = debrief.players.filter((player) => player.role !== "traitor");
    const survived = honestPlayers.filter((player) => player.final_vote === debrief.correct_consensus).length;
    refs.graphSummary.innerHTML = `
      <strong>Summary View:</strong> Links are hidden by default so you can focus on each node's final decision. Use the Honest Edges and Dishonest Edges switches above if you want to overlay the message paths again. Honest nodes are green if they matched the correct honest consensus of <strong>${debrief.correct_consensus}</strong> and red if they were tricked.
      <div class="room-meta">
        <span class="pill pill-good">Honest nodes aligned: ${survived}</span>
        <span class="pill pill-bad">Honest nodes tricked: ${honestPlayers.length - survived}</span>
      </div>
    `;
  }

  function renderGraphDetails(debrief) {
    if (!refs.graphDetails) {
      return;
    }

    if (!debrief) {
      refs.graphDetails.innerHTML = `
        <h3>Inspector</h3>
        <p>The debrief explorer will appear here once your room is complete and revealed.</p>
      `;
      return;
    }

    if (!state.graphSelection || !currentGraphData) {
      refs.graphDetails.innerHTML = `
        <h3>Inspector</h3>
        <p>Use the mouse wheel or trackpad to zoom, drag to pan, and click a node or edge for details.</p>
        <div class="graph-detail-card">
          <div class="graph-detail-row"><strong>Room</strong> ${escapeHtml(debrief.room_id)}</div>
          <div class="graph-detail-row"><strong>View</strong> ${escapeHtml(graphStageLabel(state.graphStage))}</div>
          <div class="graph-detail-row"><strong>Consensus</strong> ${escapeHtml(debrief.correct_consensus)}</div>
        </div>
        <p class="graph-caption">Fit View recenters the room after stage changes or manual zooming.</p>
      `;
      return;
    }

    if (state.graphSelection.type === "node") {
      const node = currentGraphData.nodes.find((entry) => entry.id === state.graphSelection.id);
      const player = node ? node.inspect : null;
      if (!player) {
        refs.graphDetails.innerHTML = `
          <h3>Inspector</h3>
          <p>The selected node is no longer available in this view.</p>
        `;
        return;
      }

      const controller = player.origin === "bot"
        ? "Server bot"
        : player.was_disconnect_takeover
          ? "Human — bot took over after disconnect"
          : player.was_taken_over
            ? "Human — bot took over by instructor"
            : "Human player";
      const outcome = player.role === "traitor"
        ? "Malicious node"
        : player.final_vote === debrief.correct_consensus
          ? "Matched honest consensus"
          : "Tricked away from consensus";
      const voteBehavior = player.local_tie
        ? "Tie broken by a human choice"
        : player.final_vote === player.local_consensus
          ? "Matched this node's local consensus"
          : "Did not match this node's local consensus";
      const decisionRows = state.graphStage >= 3
        ? `
          <div class="graph-detail-row"><strong>Local Consensus</strong> ${escapeHtml(player.local_consensus || "Pending")}</div>
          <div class="graph-detail-row"><strong>Final Vote</strong> ${escapeHtml(player.final_vote || "Pending")}</div>
          <div class="graph-detail-row"><strong>Vote Behavior</strong> ${escapeHtml(voteBehavior)}</div>
          <div class="graph-detail-row"><strong>Outcome</strong> ${escapeHtml(outcome)}</div>
        `
        : "";

      refs.graphDetails.innerHTML = `
        <h3>Inspector</h3>
        <p><strong>Node ${escapeHtml(player.node_id)}</strong> is currently selected.</p>
        <div class="graph-detail-card">
          <div class="graph-detail-row"><strong>Label</strong> ${escapeHtml(player.label)}</div>
          <div class="graph-detail-row"><strong>Role</strong> ${escapeHtml(roleLabel(player.role))}</div>
          <div class="graph-detail-row"><strong>Controlled By</strong> ${escapeHtml(controller)}</div>
          <div class="graph-detail-row"><strong>Initial Order</strong> ${escapeHtml(player.initial_value)}</div>
          <div class="graph-detail-row"><strong>Broadcast</strong> ${escapeHtml(player.role === "honest" ? player.initial_value : "Varies by recipient")}</div>
          ${decisionRows}
        </div>
        ${renderNodeTraffic(debrief, player.node_id, state.graphStage)}
        <p class="graph-caption">Summary view colors honest nodes green when they matched the correct consensus and red when they did not.</p>
      `;
      return;
    }

    const edge = currentGraphData.edges.find((entry) => entry.id === state.graphSelection.id);
    const message = edge ? edge.inspect : null;
    if (!message) {
      refs.graphDetails.innerHTML = `
        <h3>Inspector</h3>
        <p>The selected message is no longer visible in this stage.</p>
      `;
      return;
    }

    const deliveryStyle = message.sender_role === "traitor"
      ? `Conflicting malicious message (${message.value})`
      : `Consistent honest order (${message.value})`;

    refs.graphDetails.innerHTML = `
      <h3>Inspector</h3>
      <p><strong>Message ${escapeHtml(message.from)} -> ${escapeHtml(message.to)}</strong> is selected.</p>
      <div class="graph-detail-card">
        <div class="graph-detail-row"><strong>Value Sent</strong> ${escapeHtml(message.value)}</div>
        <div class="graph-detail-row"><strong>Sender Role</strong> ${escapeHtml(roleLabel(message.sender_role))}</div>
        <div class="graph-detail-row"><strong>Style</strong> ${escapeHtml(deliveryStyle)}</div>
        <div class="graph-detail-row"><strong>Bot Routed</strong> ${escapeHtml(message.via_bot ? "Yes" : "No")}</div>
      </div>
      <p class="graph-caption">Malicious edges are dashed and color-coded so conflicting orders stand out immediately.</p>
    `;
  }

  function renderStudentGraph(snapshot) {
    const showGraph = shouldShowDebriefExplorer(snapshot);
    refs.debriefPanel.classList.toggle("hidden", !showGraph);

    if (!showGraph) {
      if (studentGraphNetwork) {
        studentGraphNetwork.destroy();
        studentGraphNetwork = null;
      }
      currentGraphData = null;
      refs.graphRoomPill.textContent = "No Room Selected";
      refs.graphSummary.textContent = "Finish a self-service room to unlock the full debrief explorer.";
      refs.graphCanvas.innerHTML = "";
      renderGraphDetails(null);
      return;
    }

    const debrief = snapshot.debrief;
    refs.graphRoomPill.textContent = debrief.room_id;
    document.querySelectorAll("#student-graph-controls .button-stage").forEach((button) => {
      button.classList.toggle("is-active", Number(button.dataset.stage) === state.graphStage);
    });
    document.querySelectorAll("#student-graph-controls [data-edge-toggle]").forEach((button) => {
      const isVisible = Boolean(debrief) && state.graphStage === 3;
      const toggleType = button.dataset.edgeToggle;
      const isActive = toggleType === "honest" ? state.stage3ShowHonestEdges : state.stage3ShowMaliciousEdges;
      button.classList.toggle("hidden", !isVisible);
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
    updateGraphSummary(debrief);
    currentGraphData = buildGraphData(debrief, state.graphStage);
    if (
      state.graphSelection &&
      !(
        (state.graphSelection.type === "node" && currentGraphData.nodes.some((entry) => entry.id === state.graphSelection.id)) ||
        (state.graphSelection.type === "edge" && currentGraphData.edges.some((entry) => entry.id === state.graphSelection.id))
      )
    ) {
      state.graphSelection = null;
    }

    if (!window.vis || !window.vis.Network) {
      if (studentGraphNetwork) {
        studentGraphNetwork.destroy();
        studentGraphNetwork = null;
      }
      currentGraphData = null;
      refs.graphCanvas.innerHTML = `
        <div class="empty-state">Vis.js did not load, so the graph cannot render. The summary above still reflects the room outcome.</div>
      `;
      renderGraphDetails(debrief);
      return;
    }

    if (studentGraphNetwork) {
      studentGraphNetwork.destroy();
    }

    studentGraphNetwork = new window.vis.Network(
      refs.graphCanvas,
      {
        nodes: new window.vis.DataSet(currentGraphData.nodes),
        edges: new window.vis.DataSet(currentGraphData.edges),
      },
      {
        autoResize: true,
        interaction: {
          dragNodes: false,
          dragView: true,
          zoomView: true,
          hover: true,
          hoverConnectedEdges: true,
          selectConnectedEdges: false,
          keyboard: {
            enabled: true,
            bindToWindow: false,
          },
        },
        physics: false,
        nodes: {
          borderWidth: 2,
        },
        edges: {
          selectionWidth: 6,
        },
      }
    );

    studentGraphNetwork.on("selectNode", function (params) {
      state.graphSelection = params.nodes.length ? { type: "node", id: params.nodes[0] } : null;
      renderGraphDetails(debrief);
    });
    studentGraphNetwork.on("selectEdge", function (params) {
      const selectedNodes = studentGraphNetwork ? studentGraphNetwork.getSelectedNodes() : [];
      state.graphSelection = selectedNodes.length
        ? { type: "node", id: selectedNodes[0] }
        : params.edges.length
          ? { type: "edge", id: params.edges[0] }
          : null;
      renderGraphDetails(debrief);
    });
    studentGraphNetwork.on("deselectNode", function () {
      const selectedEdges = studentGraphNetwork ? studentGraphNetwork.getSelectedEdges() : [];
      state.graphSelection = selectedEdges.length ? { type: "edge", id: selectedEdges[0] } : null;
      renderGraphDetails(debrief);
    });
    studentGraphNetwork.on("deselectEdge", function () {
      const selectedNodes = studentGraphNetwork ? studentGraphNetwork.getSelectedNodes() : [];
      state.graphSelection = selectedNodes.length ? { type: "node", id: selectedNodes[0] } : null;
      renderGraphDetails(debrief);
    });

    window.requestAnimationFrame(function () {
      graphFit();
      renderGraphDetails(debrief);
    });
  }

  function selfServiceEnabled(snapshot) {
    return Boolean(snapshot && snapshot.settings && snapshot.settings.self_service_enabled);
  }

  function renderModeSwitch(snapshot) {
    const enabled = selfServiceEnabled(snapshot);
    if (!enabled) {
      return "";
    }
    return `
      <div class="button-row">
        <button id="switch-collab-button" class="button ${state.desiredMode === "collab" ? "button-strong" : ""}" type="button">Collaborative Lobby</button>
        <button id="switch-single-button" class="button ${state.desiredMode === "single" ? "button-strong" : ""}" type="button">Self-Service Mode</button>
      </div>
    `;
  }

  function renderProgress(current, total) {
    const percentage = total ? Math.round((current / total) * 100) : 0;
    return `
      <div class="progress-row">
        <span>${current} of ${total} locked in</span>
        <span>${percentage}%</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${percentage}%"></div>
      </div>
    `;
  }

  function renderQueue(snapshot) {
    if (selfServiceEnabled(snapshot) && snapshot.player.lobby_mode === "single") {
      const size = state.soloDraft.size;
      const numTraitors = Math.min(state.soloDraft.numTraitors, Math.max(size - 1, 0));
      const status = mathStatus(size, numTraitors);
      const conflictNotice = state.pendingSelfServiceConflict
        ? `
          <div class="alert">
            <p><strong>Active self-service room:</strong> ${state.pendingSelfServiceConflict.room_id}</p>
            <p>Your current self-service room is still active in phase ${state.pendingSelfServiceConflict.phase_label}. You can abandon it and start this new room, or cancel and keep the current room.</p>
            <div class="button-row">
              <button id="abandon-current-room-button" class="button button-strong" type="button">Abandon Current Room</button>
              <button id="cancel-abandon-room-button" class="button" type="button">Cancel</button>
            </div>
          </div>
        `
        : "";
      return `
        <div class="stage-card">
          <div class="summary-row">
            <h3>Lobby</h3>
            <span class="pill pill-muted">${snapshot.player.label}</span>
          </div>
          ${renderModeSwitch(snapshot)}
          <p>Self-Service Mode is configured from within the lobby. Pick your room size and malicious node count, then start immediately.</p>
          ${conflictNotice}
          <div class="form-field">
            <span>Nodes in your room (n)</span>
            <input id="solo-room-size-input" type="number" min="1" max="26" value="${size}">
          </div>
          <div class="form-field">
            <span>Number of malicious nodes (m)</span>
            <input id="solo-traitor-input" type="number" min="0" max="${Math.max(size - 1, 0)}" value="${numTraitors}">
          </div>
          <div id="solo-math-badge" class="${status.className}">${status.text}</div>
          <div class="button-row">
            <button id="create-single-room-button" class="button button-strong" type="button">Start Self-Service Session</button>
          </div>
        </div>
      `;
    }

    return `
      <div class="stage-card">
        <div class="summary-row">
          <h3>Lobby</h3>
          <span class="pill pill-muted">Position ${snapshot.queue_position || "-"}</span>
        </div>
        ${renderModeSwitch(snapshot)}
        <p>You are checked in. Keep this tab open while the instructor assigns rooms.</p>
        <div class="info-card">
          <p><strong>Students waiting:</strong> ${snapshot.queue_count}</p>
          <p class="code-note">Your session UUID is stored in the URL so refreshes and reconnects restore your place.</p>
        </div>
      </div>
    `;
  }

  function renderBroadcast(snapshot) {
    const player = snapshot.player;
    const room = snapshot.room;
    const honestOrder = player.initial_value;
    const manipulatedOrder = oppositeValue(honestOrder);
    const peerChoices = room.peer_nodes.map((peer) => `
      <div class="decision-row">
        <span class="decision-node">Node ${peer.node_id}</span>
        <label class="choice choice-attack">
          <input type="radio" name="target-${peer.node_id}" value="${honestOrder}" checked>
          <span>${honestOrder}${honestOrder === player.initial_value ? " (honest order)" : ""}</span>
        </label>
        <label class="choice choice-retreat">
          <input type="radio" name="target-${peer.node_id}" value="${manipulatedOrder}">
          <span>${manipulatedOrder} (manipulated)</span>
        </label>
      </div>
    `).join("");

    if (snapshot.control_locked) {
      return `
        <div class="stage-card">
          <div class="summary-row">
            <h3>Bot Takeover Active</h3>
            <span class="pill pill-bad">Node ${player.node_id}</span>
          </div>
          <p>The instructor transferred your node to bot control so the room could keep moving. You are now observing this round.</p>
          ${renderProgress(room.broadcast_complete, room.total_players)}
        </div>
      `;
    }

    if (player.role === "honest") {
      return `
        <div class="stage-card">
          <div class="summary-row">
            <h3>Broadcast Phase</h3>
            <span class="${badgeClassForRole(player.role)}">Role: ${roleLabel(player.role)}</span>
          </div>
          <p>You are Node <strong>${player.node_id}</strong>. Your order is <strong>${player.initial_value}</strong>.</p>
          <p>Honest nodes send the same order to every peer.</p>
          <div class="button-row">
            <button id="broadcast-honest-button" class="button button-strong">Broadcast to Peers</button>
          </div>
        </div>
      `;
    }

    return `
      <div class="stage-card">
        <div class="summary-row">
          <h3>Broadcast Phase</h3>
          <span class="${badgeClassForRole(player.role)}">Role: ${roleLabel(player.role)}</span>
        </div>
        <p>You are Node <strong>${player.node_id}</strong>. Your assigned honest order is <strong>${honestOrder}</strong>.</p>
        <div class="info-card">
          <p><strong>How to play the malicious role:</strong> an honest version of your node would send <strong>${honestOrder}</strong> to every peer. As a malicious node, you can keep that order for some peers and flip it to <strong>${manipulatedOrder}</strong> for others.</p>
        </div>
        <p>Choose what each peer will receive below.</p>
        <div class="decision-grid">${peerChoices}</div>
        <div class="button-row">
          <button id="broadcast-traitor-button" class="button button-strong">Send Malicious Messages</button>
        </div>
      </div>
    `;
  }

  function renderBroadcastWait(snapshot) {
    return `
      <div class="stage-card">
        <div class="summary-row">
          <h3>Awaiting Network Traffic</h3>
          <span class="pill pill-muted">${snapshot.player.has_broadcast ? "Broadcast Locked" : "Observer"}</span>
        </div>
        <p>Your outbound messages are recorded. The room will advance once every node is locked in.</p>
        ${renderProgress(snapshot.room.broadcast_complete, snapshot.room.total_players)}
      </div>
    `;
  }

  function renderTally(snapshot) {
    const consensusState = localConsensusState(snapshot);
    const consensusVote = consensusState.value;
    const localResultLabel = consensusState.isTie ? "Tie" : consensusVote;
    const messageList = snapshot.messages.length
      ? snapshot.messages.map((message) => `
          <div class="message-card">
            <strong>Node ${message.sender}</strong>
            <span>sent ${message.value}</span>
          </div>
        `).join("")
      : '<div class="message-card">No peer messages arrived.</div>';

    if (snapshot.control_locked) {
      return `
        <div class="stage-card">
          <div class="summary-row">
            <h3>Tally Locked</h3>
            <span class="pill pill-bad">Bot Controlled</span>
          </div>
          <p>A bot is finishing the vote for this node. You can still watch the room state below.</p>
          ${messageList}
        </div>
      `;
    }

    if (snapshot.player.role === "honest") {
      if (consensusState.isTie) {
        return `
          <div class="stage-card">
            <div class="summary-row">
              <h3>Tally Phase</h3>
              <span class="pill pill-good">Role: ${roleLabel(snapshot.player.role)}</span>
            </div>
            <p><strong>Your received messages are perfectly tied, so you must choose how this honest node breaks the tie.</strong></p>
            <div class="info-card">
              <p><strong>Your original order:</strong> ${snapshot.player.initial_value}</p>
              <p><strong>Your local result:</strong> ${localResultLabel}</p>
            </div>
            <div class="message-list">${messageList}</div>
            <div class="info-card">
              <p><strong>Tie rule:</strong> local consensus uses only received messages. When those are perfectly tied, you decide the final vote.</p>
            </div>
            <div class="decision-grid">
              <label class="choice choice-attack">
                <input type="radio" name="final-vote-choice" value="Attack">
                <span>Attack</span>
              </label>
              <label class="choice choice-retreat">
                <input type="radio" name="final-vote-choice" value="Retreat">
                <span>Retreat</span>
              </label>
            </div>
            <div class="button-row">
              <button id="submit-final-vote-button" class="button button-strong" type="button">Submit Tie-Break Vote</button>
            </div>
          </div>
        `;
      }

      return `
        <div class="stage-card">
          <div class="summary-row">
            <h3>Tally Phase</h3>
            <span class="pill pill-good">Role: ${roleLabel(snapshot.player.role)}</span>
          </div>
          <p><strong>Use only the messages you received to determine the majority. When there is a clear result, honest nodes must follow it.</strong></p>
          <div class="info-card">
            <p><strong>Your original order:</strong> ${snapshot.player.initial_value}</p>
            <p><strong>Your local consensus:</strong> ${consensusVote}</p>
          </div>
          <div class="message-list">${messageList}</div>
          <div class="info-card">
            <p><strong>Lock-in rule:</strong> honest nodes confirm the client-computed local consensus rather than choosing any value freely.</p>
          </div>
          <div class="button-row">
            <button id="submit-final-vote-button" class="button button-strong" type="button">Confirm ${consensusVote}</button>
          </div>
        </div>
      `;
    }

    return `
      <div class="stage-card">
        <div class="summary-row">
          <h3>Tally Phase</h3>
          <span class="pill pill-bad">Role: ${roleLabel(snapshot.player.role)}</span>
        </div>
        <p><strong>Use only the messages you received to determine the majority. Malicious nodes may still choose any final vote.</strong></p>
        <div class="info-card">
          <p><strong>Your original order:</strong> ${snapshot.player.initial_value}</p>
          <p><strong>Your local result:</strong> ${localResultLabel}</p>
        </div>
        <div class="message-list">${messageList}</div>
        <div class="info-card">
          <p><strong>Malicious node rule:</strong> ${consensusState.isTie ? "your view is tied, so choose whichever final vote you want to submit." : "your local consensus is shown as the default, but you may override it before submitting."}</p>
        </div>
        <div class="decision-grid">
          <label class="choice choice-attack">
            <input type="radio" name="final-vote-choice" value="Attack" ${!consensusState.isTie && consensusVote === "Attack" ? "checked" : ""}>
            <span>Attack</span>
          </label>
          <label class="choice choice-retreat">
            <input type="radio" name="final-vote-choice" value="Retreat" ${!consensusState.isTie && consensusVote === "Retreat" ? "checked" : ""}>
            <span>Retreat</span>
          </label>
        </div>
        <div class="vote-buttons">
          <button id="submit-final-vote-button" class="button button-strong" type="button">Submit Final Vote</button>
        </div>
      </div>
    `;
  }

  function renderTallyWait(snapshot) {
    return `
      <div class="stage-card">
        <div class="summary-row">
          <h3>Vote Submitted</h3>
          <span class="pill pill-muted">${snapshot.player.final_vote || "Awaiting Bot Vote"}</span>
        </div>
        <p>Your node is locked. The instructor will reveal the room debrief after everyone is tallied.</p>
        ${renderProgress(snapshot.room.vote_complete, snapshot.room.total_players)}
      </div>
    `;
  }

  function renderAwaitDebrief(snapshot) {
    return `
      <div class="stage-card">
        <div class="summary-row">
          <h3>Awaiting Debrief</h3>
          <span class="pill pill-muted">Room ${snapshot.room.room_id}</span>
        </div>
        <p>All final votes are in. Any student in the room can reveal the debrief for everyone. Use the explorer below to step through the full message graph.</p>
        <div class="info-card">
          <p><strong>Your final vote:</strong> ${snapshot.player.final_vote || "Pending bot decision"}</p>
        </div>
        <div class="button-row">
          <button id="reveal-room-debrief-button" class="button button-strong" type="button">Reveal Room Debrief</button>
        </div>
      </div>
    `;
  }

  function renderDebrief(snapshot) {
    const debrief = snapshot.debrief;
    const playerResult = debrief.players.find((entry) => entry.uuid === snapshot.player.uuid);
    const playerStatusLabel = playerResult.role === "traitor"
      ? "Malicious Node"
      : playerResult.survived
        ? "Stayed Honest"
        : "Tricked";
    const playerStatusClass = playerResult.role === "traitor"
      ? "pill pill-traitor"
      : playerResult.survived
        ? "pill pill-good"
        : "pill pill-bad";
    const resultText = playerResult.role === "traitor"
      ? "You were the malicious node in this room."
      : playerResult.final_vote === debrief.correct_consensus
        ? "Your honest node stayed aligned with the correct consensus."
        : "Your node was pulled away from the correct honest consensus.";

    const roster = debrief.players.map((entry) => {
      const statusLabel = entry.role === "traitor"
        ? "Malicious"
        : entry.survived
          ? "Stayed Honest"
          : "Tricked";
      const rolePillClass = entry.role === "traitor" ? "pill pill-traitor" : "pill pill-good";
      const statusPillClass = entry.role === "traitor"
        ? "pill pill-traitor"
        : entry.survived
          ? "pill pill-good"
          : "pill pill-bad";
      const cardClass = entry.role === "traitor"
        ? "debrief-node-card is-malicious"
        : entry.survived
          ? "debrief-node-card is-aligned"
          : "debrief-node-card is-tricked";
      return `
        <div class="${cardClass}">
          <div class="debrief-node-header">
            <div>
              <strong>Node ${entry.node_id}</strong>
              <div class="debrief-node-pills">
                <span class="${rolePillClass}">${roleLabel(entry.role)}</span>
                <span class="${statusPillClass}">${statusLabel}</span>
              </div>
            </div>
          </div>
          <div class="debrief-node-values">
            <div class="debrief-value-row">
              <span>Initial</span>
              ${valueBadge(entry.initial_value)}
            </div>
            <div class="debrief-value-row">
              <span>Local</span>
              ${valueBadge(entry.local_consensus)}
            </div>
            <div class="debrief-value-row">
              <span>Final</span>
              ${valueBadge(entry.final_vote)}
            </div>
          </div>
        </div>
      `;
    }).join("");

    return `
      <div class="stage-card">
        <div class="summary-row">
          <h3>Debrief Ready</h3>
          <span class="${playerStatusClass}">
            ${playerStatusLabel}
          </span>
        </div>
        <div class="debrief-overview">
          <div class="debrief-summary-card">
            <span class="debrief-summary-label">Correct Honest Consensus</span>
            ${valueBadge(debrief.correct_consensus)}
          </div>
          <div class="debrief-summary-card">
            <span class="debrief-summary-label">Your Result</span>
            <span class="${playerStatusClass}">${playerStatusLabel}</span>
          </div>
        </div>
        <p>${resultText}</p>
        <p><strong>Use the Debrief Explorer below</strong> to step through honest broadcasts, malicious lies, and final outcomes.</p>
        <div class="debrief-node-grid">${roster}</div>
        <div class="button-row">
          <button class="button button-strong" type="button" data-student-reset="true">Restart Exercise</button>
        </div>
      </div>
    `;
  }

  function renderSide(snapshot) {
    if (!snapshot || snapshot.view === "queue") {
      if (snapshot && selfServiceEnabled(snapshot) && snapshot.player.lobby_mode === "single") {
        return `
          <div class="info-card">
            <h3>Self-Service Lobby</h3>
            <p>You are not in the collaborative queue. Design your own room here, and the server will start it immediately with bots filling the remaining seats.</p>
          </div>
        `;
      }
      return `
        <div class="info-card">
          <h3>What happens next?</h3>
          <p>The instructor groups students into rooms and sets the number of malicious nodes.</p>
        </div>
      `;
    }

    const room = snapshot.room;
    const player = snapshot.player;
    const peers = room.peer_nodes.map((peer) => `
      <div class="message-card">
        <strong>Node ${peer.node_id}</strong>
        <span>${peer.label}</span>
      </div>
    `).join("");

    return `
      <div class="info-card">
        <h3>Node Status</h3>
        <p><strong>Room:</strong> ${room.room_id}</p>
        <p><strong>Mode:</strong> ${room.mode === "single" ? "Self-Service" : "Collaborative"}</p>
        <p><strong>Your node:</strong> ${player.node_id}</p>
      </div>
      <div class="info-card">
        <h3>Peers</h3>
        <div class="message-list">${peers || '<div class="message-card">No peers listed.</div>'}</div>
      </div>
    `;
  }

  function render() {
    const snapshot = state.snapshot;
    refs.connectionPill.textContent = state.connected ? "Connected" : "Disconnected";
    refs.connectionPill.className = state.connected ? "pill pill-good" : "pill pill-bad";
    setAlert(state.error);

    if (!snapshot) {
      refs.stage.innerHTML = `
        <div class="empty-state">Connecting to the simulation server...</div>
      `;
      refs.side.innerHTML = "";
      renderStudentGraph(null);
      return;
    }

    if (snapshot.view === "queue") {
      refs.roomPill.textContent = "Lobby";
      refs.playerPill.textContent = snapshot.player.label;
      refs.phasePill.textContent = "Lobby";
      refs.subtitle.textContent = snapshot.player.lobby_mode === "single"
        ? "Self-Service Mode is selected. Configure your room here from the lobby and the server will start it immediately."
        : "The lobby is live. Your URL carries your student identity so the server can restore your state after refresh.";
      refs.stage.innerHTML = renderQueue(snapshot);
      refs.side.innerHTML = renderSide(snapshot);
      wireActions(snapshot);
      renderStudentGraph(snapshot);
      return;
    }

    refs.roomPill.textContent = snapshot.room.room_id;
    refs.playerPill.textContent = `Node ${snapshot.player.node_id}`;
    refs.phasePill.textContent = snapshot.room.phase_label;
    refs.subtitle.textContent = snapshot.view === "debrief"
        ? "Your debrief is live. Use the explorer below to inspect honest broadcasts, malicious lies, and final outcomes."
        : snapshot.player.role === "traitor"
        ? "Your job is to fracture the room's confidence without showing your hand."
        : "Stay consistent, tally carefully, and see whether consensus survives.";

    const viewMap = {
      broadcast: renderBroadcast,
      broadcast_wait: renderBroadcastWait,
      tally: renderTally,
      tally_wait: renderTallyWait,
      await_debrief: renderAwaitDebrief,
      debrief: renderDebrief,
    };
    refs.stage.innerHTML = viewMap[snapshot.view](snapshot);
    refs.side.innerHTML = renderSide(snapshot);
    wireActions(snapshot);
    renderStudentGraph(snapshot);
  }

  function wireActions(snapshot) {
    const switchCollabButton = document.getElementById("switch-collab-button");
    if (switchCollabButton) {
      switchCollabButton.addEventListener("click", function () {
        setDesiredMode("collab");
      });
    }

    const switchSingleButton = document.getElementById("switch-single-button");
    if (switchSingleButton) {
      switchSingleButton.addEventListener("click", function () {
        setDesiredMode("single");
      });
    }

    const soloRoomSizeInput = document.getElementById("solo-room-size-input");
    const soloTraitorInput = document.getElementById("solo-traitor-input");
    const soloMathBadge = document.getElementById("solo-math-badge");
    if (soloRoomSizeInput && soloTraitorInput && soloMathBadge) {
      const updateSoloMath = function () {
        state.soloDraft.size = Math.max(1, Math.min(26, Number(soloRoomSizeInput.value || 8)));
        soloRoomSizeInput.value = String(state.soloDraft.size);
        soloTraitorInput.max = String(Math.max(state.soloDraft.size - 1, 0));
        state.soloDraft.numTraitors = Math.max(0, Math.min(Math.max(state.soloDraft.size - 1, 0), Number(soloTraitorInput.value || 0)));
        soloTraitorInput.value = String(state.soloDraft.numTraitors);
        const status = mathStatus(state.soloDraft.size, state.soloDraft.numTraitors);
        soloMathBadge.className = status.className;
        soloMathBadge.textContent = status.text;
      };
      soloRoomSizeInput.addEventListener("input", updateSoloMath);
      soloTraitorInput.addEventListener("input", updateSoloMath);
      updateSoloMath();
    }

    const createSingleRoomButton = document.getElementById("create-single-room-button");
    if (createSingleRoomButton) {
      createSingleRoomButton.addEventListener("click", function () {
        socket.emit("create_single_player_room", {
          size: state.soloDraft.size,
          num_traitors: state.soloDraft.numTraitors,
          abandon_existing: false,
        });
      });
    }

    const abandonCurrentRoomButton = document.getElementById("abandon-current-room-button");
    if (abandonCurrentRoomButton) {
      abandonCurrentRoomButton.addEventListener("click", function () {
        socket.emit("create_single_player_room", {
          size: state.soloDraft.size,
          num_traitors: state.soloDraft.numTraitors,
          abandon_existing: true,
        });
      });
    }

    const cancelAbandonRoomButton = document.getElementById("cancel-abandon-room-button");
    if (cancelAbandonRoomButton) {
      cancelAbandonRoomButton.addEventListener("click", function () {
        state.pendingSelfServiceConflict = null;
        render();
      });
    }

    const revealRoomDebriefButton = document.getElementById("reveal-room-debrief-button");
    if (revealRoomDebriefButton) {
      revealRoomDebriefButton.addEventListener("click", function () {
        socket.emit("reveal_room_debrief");
      });
    }

    document.querySelectorAll("[data-student-reset]").forEach((button) => {
      button.addEventListener("click", function () {
        const url = new URL(window.location.href);
        url.searchParams.delete("uuid");
        url.searchParams.delete("mode");
        window.location.assign(`${url.pathname}${url.search}${url.hash}`);
      });
    });

    const honestButton = document.getElementById("broadcast-honest-button");
    if (honestButton) {
      honestButton.addEventListener("click", function () {
        socket.emit("submit_broadcast", { messages: {} });
      });
    }

    const traitorButton = document.getElementById("broadcast-traitor-button");
    if (traitorButton) {
      traitorButton.addEventListener("click", function () {
        const messages = {};
        snapshot.room.peer_nodes.forEach((peer) => {
          const checked = document.querySelector(`input[name="target-${peer.node_id}"]:checked`);
          messages[peer.node_id] = checked ? checked.value : "Attack";
        });
        socket.emit("submit_broadcast", { messages });
      });
    }

    const submitFinalVoteButton = document.getElementById("submit-final-vote-button");
    if (submitFinalVoteButton) {
      submitFinalVoteButton.addEventListener("click", function () {
        const consensusState = localConsensusState(snapshot);
        let value = consensusState.value;
        const checked = document.querySelector('input[name="final-vote-choice"]:checked');
        if (snapshot.player.role !== "honest" || consensusState.isTie) {
          if (consensusState.isTie && !checked) {
            setAlert("Choose Attack or Retreat to resolve the tie before submitting.");
            return;
          }
          value = checked ? checked.value : value;
        }
        setAlert("");
        socket.emit("submit_final_vote", { value });
      });
    }
  }

  function handleSnapshot(snapshot) {
    const nextGraphRoomId = shouldShowDebriefExplorer(snapshot) ? snapshot.debrief.room_id : null;
    if (nextGraphRoomId !== state.graphRoomId) {
      state.graphRoomId = nextGraphRoomId;
      state.graphStage = 1;
      state.stage3ShowHonestEdges = false;
      state.stage3ShowMaliciousEdges = false;
      state.graphSelection = null;
    }
    state.snapshot = snapshot;
    state.error = "";
    if (snapshot.view !== "queue" || snapshot.player.lobby_mode !== "single") {
      state.pendingSelfServiceConflict = null;
    }
    render();
  }

  refs.graphControls.addEventListener("click", function (event) {
    const actionButton = event.target.closest("[data-graph-action]");
    if (actionButton) {
      const action = actionButton.dataset.graphAction;
      if (action === "fit") {
        graphFit();
      } else if (action === "zoom-in") {
        graphZoom(1.2);
      } else if (action === "zoom-out") {
        graphZoom(0.82);
      } else if (action === "clear-selection") {
        state.graphSelection = null;
        if (studentGraphNetwork) {
          studentGraphNetwork.unselectAll();
        }
        renderGraphDetails(state.snapshot && state.snapshot.debrief ? state.snapshot.debrief : null);
      }
      return;
    }

    const edgeToggleButton = event.target.closest("[data-edge-toggle]");
    if (edgeToggleButton) {
      const toggleType = edgeToggleButton.dataset.edgeToggle;
      if (toggleType === "honest") {
        state.stage3ShowHonestEdges = !state.stage3ShowHonestEdges;
      } else if (toggleType === "malicious") {
        state.stage3ShowMaliciousEdges = !state.stage3ShowMaliciousEdges;
      }
      renderStudentGraph(state.snapshot);
      return;
    }

    const button = event.target.closest("[data-stage]");
    if (!button) {
      return;
    }
    state.graphStage = Number(button.dataset.stage);
    state.graphSelection = null;
    renderStudentGraph(state.snapshot);
  });

  socket.on("connect", function () {
    state.connected = true;
    render();
    socket.emit("register", { uuid: playerUuid, mode: state.desiredMode });
  });

  socket.on("disconnect", function () {
    state.connected = false;
    render();
  });

  ["restore_state", "phase_1_start", "phase_2_start", "room_update", "debrief_ready"].forEach((eventName) => {
    socket.on(eventName, function (payload) {
      if (payload && payload.view) {
        handleSnapshot(payload);
      }
    });
  });

  socket.on("server_error", function (payload) {
    setAlert(payload.message || "An unexpected server error occurred.");
  });

  socket.on("self_service_room_conflict", function (payload) {
    state.pendingSelfServiceConflict = payload || null;
    state.error = "";
    render();
  });

  render();
})();
