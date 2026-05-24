(function () {
  const state = {
    dashboard: null,
    preview: null,
    selectedDebrief: null,
    selectedRoomId: null,
    stage: 1,
    stage3ShowHonestEdges: false,
    stage3ShowMaliciousEdges: false,
    graphSelection: null,
    error: "",
  };

  const refs = {
    queuePill: document.getElementById("queue-pill"),
    dashboardPill: document.getElementById("dashboard-pill"),
    alert: document.getElementById("instructor-alert"),
    previewForm: document.getElementById("preview-form"),
    roomSizeInput: document.getElementById("room-size-input"),
    previewGrid: document.getElementById("preview-grid"),
    queueList: document.getElementById("queue-list"),
    roomList: document.getElementById("room-list"),
    launchButton: document.getElementById("launch-button"),
    graphRoomPill: document.getElementById("graph-room-pill"),
    graphSummary: document.getElementById("graph-summary"),
    graphCanvas: document.getElementById("graph-canvas"),
    graphControls: document.getElementById("graph-controls"),
    graphDetails: document.getElementById("graph-details"),
  };

  let graphNetwork = null;
  let currentGraphData = null;
  const socket = io({
    path: window.SOCKETIO_PATH || "/socket.io",
  });

  function selectedMode() {
    return "collab";
  }

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

  function roleLabel(role) {
    return role === "traitor" ? "MALICIOUS" : "HONEST";
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

  function graphFit() {
    if (!graphNetwork) {
      return;
    }
    graphNetwork.fit({
      animation: {
        duration: 220,
        easingFunction: "easeInOutQuad",
      },
    });
  }

  function graphZoom(multiplier) {
    if (!graphNetwork) {
      return;
    }
    const scale = graphNetwork.getScale();
    graphNetwork.moveTo({
      scale: Math.max(0.35, Math.min(scale * multiplier, 2.6)),
      animation: {
        duration: 180,
        easingFunction: "easeInOutQuad",
      },
    });
  }

  function renderGraphDetails() {
    if (!refs.graphDetails) {
      return;
    }

    if (!state.selectedDebrief) {
      refs.graphDetails.innerHTML = `
        <h3>Inspector</h3>
        <p>Select a completed room to inspect the message flow and outcome.</p>
        <p class="graph-caption">Once a room is selected, you can zoom, pan, and click any node or edge for details.</p>
      `;
      return;
    }

    if (!state.graphSelection || !currentGraphData) {
      refs.graphDetails.innerHTML = `
        <h3>Inspector</h3>
        <p>Use the mouse wheel or trackpad to zoom, drag to pan, and click a node or edge for details.</p>
        <div class="graph-detail-card">
          <div class="graph-detail-row"><strong>Room</strong> ${escapeHtml(state.selectedDebrief.room_id)}</div>
          <div class="graph-detail-row"><strong>View</strong> ${escapeHtml(graphStageLabel(state.stage))}</div>
          <div class="graph-detail-row"><strong>Consensus</strong> ${escapeHtml(state.selectedDebrief.correct_consensus)}</div>
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
        : player.final_vote === state.selectedDebrief.correct_consensus
          ? "Matched honest consensus"
          : "Tricked away from consensus";
      const voteBehavior = player.local_tie
        ? "Tie broken by a human choice"
        : player.final_vote === player.local_consensus
          ? "Matched this node's local consensus"
          : "Did not match this node's local consensus";
      const decisionRows = state.stage >= 3
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
          <div class="graph-detail-row"><strong>Honest Broadcast</strong> ${escapeHtml(player.role === "honest" ? player.initial_value : "Varies by recipient")}</div>
          ${decisionRows}
        </div>
        ${renderNodeTraffic(state.selectedDebrief, player.node_id, state.stage)}
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

  function mathStatus(size, traitors) {
    const faultTolerant = (3 * traitors + 1) <= size;
    return {
      faultTolerant,
      text: faultTolerant
        ? `Fault tolerant: ${size} >= 3*${traitors} + 1`
        : `Consensus at risk: ${size} < 3*${traitors} + 1`,
      className: faultTolerant ? "math-badge math-good" : "math-badge math-bad",
    };
  }

  function renderPreview() {
    const preview = state.preview;
    if (!preview || !preview.rooms.length) {
      refs.previewGrid.innerHTML = `
        <div class="empty-state">No launchable rooms yet. Students must join the queue before you can generate previews.</div>
      `;
      return;
    }

    refs.previewGrid.innerHTML = preview.rooms.map((room) => {
      const status = mathStatus(room.size, room.default_traitors);
      const botControl = room.mode === "collab"
        ? `
          <label class="form-field">
            <span>Bot nodes to add</span>
            <input class="bot-input" type="number" min="0" max="${room.max_bots}" value="${room.bot_count}">
          </label>
        `
        : `
          <div class="info-card">
            <strong>Bots auto-filled:</strong> ${room.bot_count}
          </div>
        `;
      return `
        <div class="preview-row" data-preview-id="${room.preview_id}" data-size="${room.size}" data-human-count="${room.human_count}" data-max-bots="${room.max_bots}" data-participants="${room.participant_uuids.join(",")}">
          <div class="summary-row">
            <h3>${room.room_label}</h3>
            <span class="pill pill-muted">${room.mode === "single" ? "Self-Service" : "Collaborative"}</span>
          </div>
          <div class="preview-meta">
            <span class="pill pill-muted">Humans: ${room.human_count}</span>
            <span class="pill pill-muted bot-count-pill">Bots: ${room.bot_count}</span>
            <span class="pill pill-muted total-nodes-pill">Total Nodes: ${room.size}</span>
          </div>
          ${botControl}
          <label class="form-field">
            <span>Number of malicious nodes (m)</span>
            <input class="traitor-input" type="number" min="0" max="${Math.max(room.size - 1, 0)}" value="${room.default_traitors}">
          </label>
          <div class="${status.className}">${status.text}</div>
          <div class="participant-list">
            ${room.participant_labels.map((label) => `<div class="message-card">${label}</div>`).join("")}
          </div>
        </div>
      `;
    }).join("");
  }

  function renderQueue() {
    if (!state.dashboard || !state.dashboard.queue_players.length) {
      refs.queueList.innerHTML = '<div class="empty-state">No students are waiting yet.</div>';
      return;
    }

    refs.queueList.innerHTML = state.dashboard.queue_players.map((player) => `
      <div class="queue-card">
        <div class="summary-row">
          <h3>${player.label}</h3>
          <span class="${player.connected ? "pill pill-good" : "pill pill-bad"}">${player.connected ? "Connected" : "Offline"}</span>
        </div>
        <div class="queue-meta">
          <span class="pill pill-muted code-note">${player.uuid.slice(0, 12)}</span>
        </div>
      </div>
    `).join("");
  }

  function renderRooms() {
    if (!state.dashboard || !state.dashboard.rooms.length) {
      refs.roomList.innerHTML = '<div class="empty-state">No rooms launched yet.</div>';
      return;
    }

    refs.roomList.innerHTML = state.dashboard.rooms.map((room) => {
      const selectedClass = room.room_id === state.selectedRoomId ? "room-card is-selected" : "room-card";
      const canReveal = room.phase >= 3 || room.debrief_revealed;
      const revealLabel = room.debrief_revealed ? "Inspect Debrief" : "Reveal Debrief";
      const revealAction = room.debrief_revealed ? "inspect-debrief" : "reveal-debrief";
      const progressLabel = room.phase < 2 ? "Broadcast" : "Votes";
      const progressValue = room.phase < 2 ? room.broadcast_complete : room.vote_complete;
      const takeoverTargets = room.players.filter((player) => {
        if (player.origin !== "human" || player.is_bot || !player.connected) {
          return false;
        }
        if (room.phase === 1) {
          return !player.has_broadcast;
        }
        if (room.phase === 2) {
          return !player.final_vote;
        }
        return false;
      });
      return `
        <div class="${selectedClass}" data-room-id="${room.room_id}">
          <div class="summary-row">
            <h3>${room.room_id}</h3>
            <span class="pill pill-muted">${room.phase_label}</span>
          </div>
          <div class="room-meta">
            <span class="pill pill-muted">${room.mode === "single" ? "Self-Service" : "Collaborative"}</span>
            <span class="pill pill-muted">Nodes: ${room.size}</span>
            <span class="pill pill-muted">Malicious Nodes: ${room.num_traitors}</span>
          </div>
          ${renderProgress(progressValue, room.total_players, progressLabel)}
          <div class="player-list">
            ${room.players.map((player) => `
              <div class="message-card">
                <strong>${player.node_id}</strong>
                <span>${player.label}</span>
                <span class="${player.is_bot ? "pill pill-bad" : "pill pill-good"}">${player.is_bot ? (player.origin === "bot" ? "Bot" : player.was_disconnect_takeover ? "Disconnected" : "Taken Over") : "Human"}</span>
                ${takeoverTargets.some((target) => target.uuid === player.uuid)
                  ? `<button type="button" class="button" data-action="force-takeover" data-room-id="${room.room_id}" data-target-uuid="${player.uuid}">Take Over ${player.node_id}</button>`
                  : ""}
              </div>
            `).join("")}
          </div>
          <div class="button-row">
            <button type="button" class="button button-strong" data-action="${revealAction}" data-room-id="${room.room_id}" ${canReveal ? "" : "disabled"}>${revealLabel}</button>
          </div>
        </div>
      `;
    }).join("");
  }

  function renderProgress(current, total, label) {
    const percentage = total ? Math.round((current / total) * 100) : 0;
    return `
      <div class="info-card">
        <div class="summary-row">
          <span>${label}</span>
          <span>${current}/${total}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${percentage}%"></div>
        </div>
      </div>
    `;
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

  function updateGraphSummary() {
    if (!state.selectedDebrief) {
      refs.graphSummary.textContent = "Select a completed room to inspect the message flow and outcome.";
      return;
    }

    if (state.stage === 1) {
      refs.graphSummary.innerHTML = `
        <strong>Honest View:</strong> All nodes are visible, but only honest-message edges are shown so you can isolate the consistent broadcasts.
      `;
      return;
    }

    if (state.stage === 2) {
      refs.graphSummary.innerHTML = `
        <strong>Dishonest View:</strong> All nodes remain visible, but only malicious-message edges are shown so the conflicting broadcasts stand out clearly.
      `;
      return;
    }

    const honestPlayers = state.selectedDebrief.players.filter((player) => player.role !== "traitor");
    const survived = honestPlayers.filter((player) => player.final_vote === state.selectedDebrief.correct_consensus).length;
    refs.graphSummary.innerHTML = `
      <strong>Summary View:</strong> Links are hidden by default so you can focus on each node's final decision. Use the Honest Edges and Dishonest Edges switches above if you want to overlay the message paths again. Honest nodes are green if they matched the correct honest consensus of <strong>${state.selectedDebrief.correct_consensus}</strong> and red if they were tricked.
      <div class="room-meta">
        <span class="pill pill-good">Honest nodes aligned: ${survived}</span>
        <span class="pill pill-bad">Honest nodes tricked: ${honestPlayers.length - survived}</span>
      </div>
    `;
  }

  function renderGraph() {
    refs.graphRoomPill.textContent = state.selectedDebrief ? state.selectedDebrief.room_id : "No Room Selected";
    document.querySelectorAll(".button-stage").forEach((button) => {
      button.classList.toggle("is-active", Number(button.dataset.stage) === state.stage);
    });
    document.querySelectorAll("#graph-controls [data-edge-toggle]").forEach((button) => {
      const isVisible = Boolean(state.selectedDebrief) && state.stage === 3;
      const toggleType = button.dataset.edgeToggle;
      const isActive = toggleType === "honest" ? state.stage3ShowHonestEdges : state.stage3ShowMaliciousEdges;
      button.classList.toggle("hidden", !isVisible);
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });

    if (!state.selectedDebrief) {
      if (graphNetwork) {
        graphNetwork.destroy();
        graphNetwork = null;
      }
      currentGraphData = null;
      state.graphSelection = null;
      refs.graphCanvas.innerHTML = "";
      updateGraphSummary();
      renderGraphDetails();
      return;
    }

    updateGraphSummary();
    currentGraphData = buildGraphData(state.selectedDebrief, state.stage);
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
      if (graphNetwork) {
        graphNetwork.destroy();
        graphNetwork = null;
      }
      currentGraphData = null;
      state.graphSelection = null;
      refs.graphCanvas.innerHTML = `
        <div class="empty-state">Vis.js did not load, so the graph cannot render. The summary above still reflects the room outcome.</div>
      `;
      renderGraphDetails();
      return;
    }

    if (graphNetwork) {
      graphNetwork.destroy();
    }
    graphNetwork = new window.vis.Network(
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

    graphNetwork.on("selectNode", function (params) {
      state.graphSelection = params.nodes.length ? { type: "node", id: params.nodes[0] } : null;
      renderGraphDetails();
    });
    graphNetwork.on("selectEdge", function (params) {
      const selectedNodes = graphNetwork ? graphNetwork.getSelectedNodes() : [];
      state.graphSelection = selectedNodes.length
        ? { type: "node", id: selectedNodes[0] }
        : params.edges.length
          ? { type: "edge", id: params.edges[0] }
          : null;
      renderGraphDetails();
    });
    graphNetwork.on("deselectNode", function () {
      const selectedEdges = graphNetwork ? graphNetwork.getSelectedEdges() : [];
      state.graphSelection = selectedEdges.length ? { type: "edge", id: selectedEdges[0] } : null;
      renderGraphDetails();
    });
    graphNetwork.on("deselectEdge", function () {
      const selectedNodes = graphNetwork ? graphNetwork.getSelectedNodes() : [];
      state.graphSelection = selectedNodes.length ? { type: "node", id: selectedNodes[0] } : null;
      renderGraphDetails();
    });

    window.requestAnimationFrame(function () {
      graphFit();
      renderGraphDetails();
    });
  }

  function renderSelfServiceToggle() {
    const enabled = state.dashboard && state.dashboard.settings && state.dashboard.settings.self_service_enabled;
    const toggleButton = document.getElementById("self-service-toggle");
    if (!toggleButton) {
      return;
    }
    toggleButton.textContent = enabled ? "Disable Self-Service Mode" : "Enable Self-Service Mode";
    toggleButton.className = enabled ? "button button-strong" : "button";
    toggleButton.dataset.enabled = enabled ? "true" : "false";
  }

  function render() {
    refs.dashboardPill.textContent = "Dashboard Live";
    refs.dashboardPill.className = "pill pill-good";
    refs.queuePill.textContent = `Students in Queue: ${state.dashboard ? state.dashboard.queue_count : 0}`;
    setAlert(state.error);
    renderSelfServiceToggle();
    renderPreview();
    renderQueue();
    renderRooms();
    renderGraph();
  }

  function launchSimulation() {
    const rows = Array.from(refs.previewGrid.querySelectorAll(".preview-row"));
    if (!rows.length) {
      setAlert("Generate a room preview before launching.");
      return;
    }

    const rooms = rows.map((row) => {
      const size = Number(row.dataset.size);
      const participantUuids = row.dataset.participants ? row.dataset.participants.split(",").filter(Boolean) : [];
      const traitorInput = row.querySelector(".traitor-input");
      const numTraitors = Number(traitorInput.value);
      return {
        participant_uuids: participantUuids,
        size,
        num_traitors: numTraitors,
      };
    });

    socket.emit("launch_game", {
      mode: selectedMode(),
      rooms,
    });
  }

  const selfServiceToggleButton = document.getElementById("self-service-toggle");
  if (selfServiceToggleButton) {
    selfServiceToggleButton.addEventListener("click", function () {
      const currentlyEnabled = selfServiceToggleButton.dataset.enabled === "true";
      socket.emit("toggle_self_service", { enabled: !currentlyEnabled });
    });
  }

  refs.previewForm.addEventListener("submit", function (event) {
    event.preventDefault();
    socket.emit("preview_rooms", {
      mode: selectedMode(),
      room_size: Number(refs.roomSizeInput.value || 8),
    });
  });

  refs.launchButton.addEventListener("click", launchSimulation);

  refs.previewGrid.addEventListener("input", function (event) {
    if (!event.target.classList.contains("traitor-input") && !event.target.classList.contains("bot-input")) {
      return;
    }
    const row = event.target.closest(".preview-row");
    const humanCount = Number(row.dataset.humanCount || 0);
    const botInput = row.querySelector(".bot-input");
    const botCountPill = row.querySelector(".bot-count-pill");
    const totalNodesPill = row.querySelector(".total-nodes-pill");
    let totalSize = Number(row.dataset.size);
    if (botInput) {
      const maxBots = Number(row.dataset.maxBots || 0);
      const botValue = Math.max(0, Math.min(maxBots, Number(botInput.value || 0)));
      botInput.value = String(botValue);
      totalSize = humanCount + botValue;
      row.dataset.size = String(totalSize);
      if (botCountPill) {
        botCountPill.textContent = `Bots: ${botValue}`;
      }
      if (totalNodesPill) {
        totalNodesPill.textContent = `Total Nodes: ${totalSize}`;
      }
    }
    const traitorInput = row.querySelector(".traitor-input");
    traitorInput.max = String(Math.max(totalSize - 1, 0));
    if (Number(traitorInput.value || 0) > Math.max(totalSize - 1, 0)) {
      traitorInput.value = String(Math.max(totalSize - 1, 0));
    }
    const status = mathStatus(totalSize, Number(traitorInput.value || 0));
    const badge = row.querySelector(".math-badge");
    badge.className = status.className;
    badge.textContent = status.text;
  });

  refs.roomList.addEventListener("click", function (event) {
    const button = event.target.closest("[data-action]");
    if (!button) {
      return;
    }
    const roomId = button.dataset.roomId;
    const action = button.dataset.action;

    if (action === "force-takeover") {
      socket.emit("force_takeover", {
        room_id: roomId,
        target_uuid: button.dataset.targetUuid,
      });
      return;
    }

    if (action === "reveal-debrief") {
      socket.emit("reveal_debrief", { room_id: roomId });
      return;
    }

    if (action === "inspect-debrief" && state.dashboard) {
      const room = state.dashboard.rooms.find((entry) => entry.room_id === roomId);
      if (room && room.debrief) {
        state.selectedDebrief = room.debrief;
        state.selectedRoomId = room.room_id;
        state.stage = 1;
        state.stage3ShowHonestEdges = false;
        state.stage3ShowMaliciousEdges = false;
        state.graphSelection = null;
        render();
      }
    }
  });

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
        if (graphNetwork) {
          graphNetwork.unselectAll();
        }
        renderGraphDetails();
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
      renderGraph();
      return;
    }

    const button = event.target.closest("[data-stage]");
    if (!button) {
      return;
    }
    state.stage = Number(button.dataset.stage);
    state.graphSelection = null;
    renderGraph();
  });

  socket.on("connect", function () {
    refs.dashboardPill.textContent = "Socket Connected";
    refs.dashboardPill.className = "pill pill-good";
    socket.emit("join_instructor");
  });

  socket.on("disconnect", function () {
    refs.dashboardPill.textContent = "Dashboard Offline";
    refs.dashboardPill.className = "pill pill-bad";
  });

  socket.on("dashboard_state", function (payload) {
    state.dashboard = payload;
    state.error = "";
    if (state.selectedRoomId) {
      const selectedRoom = payload.rooms.find((room) => room.room_id === state.selectedRoomId);
      if (selectedRoom && selectedRoom.debrief) {
        state.selectedDebrief = selectedRoom.debrief;
      } else if (!selectedRoom) {
        state.selectedDebrief = null;
        state.selectedRoomId = null;
        state.stage3ShowHonestEdges = false;
        state.stage3ShowMaliciousEdges = false;
        state.graphSelection = null;
      }
    }
    render();
  });

  socket.on("room_preview", function (payload) {
    state.preview = payload;
    state.error = "";
    renderPreview();
  });

  socket.on("launch_result", function () {
    state.preview = null;
    render();
  });

  socket.on("debrief_ready", function (payload) {
    if (!payload || !payload.room_id) {
      return;
    }
    state.selectedDebrief = payload;
    state.selectedRoomId = payload.room_id;
    state.stage = 1;
    state.stage3ShowHonestEdges = false;
    state.stage3ShowMaliciousEdges = false;
    state.graphSelection = null;
    render();
  });

  socket.on("self_service_toggled", function (payload) {
    if (state.dashboard && state.dashboard.settings) {
      state.dashboard.settings.self_service_enabled = payload.self_service_enabled;
    }
    renderSelfServiceToggle();
  });

  socket.on("server_error", function (payload) {
    setAlert(payload.message || "An unexpected server error occurred.");
  });
})();
