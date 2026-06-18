# Byzantine Generals Simulation App Design Document

## 1. Document Intent

This document is the product and system handoff for an engineer building the Byzantine Generals Simulation App from scratch.

It describes:

- what the app is for
- what behaviors are required
- what state the system must manage
- how the major flows should work
- what constraints matter for implementation

## 2. Product Overview

The app is a single-player, self-study simulation of the Byzantine Generals Problem. A student plays one node in a small consensus round, while the server plays every other node. Some nodes are honest and some are malicious. Each node has only a local view of the network, and the network may fail to reach reliable consensus.

Educational goals:

- Each node acts on incomplete local information.
- Malicious participants can send conflicting messages to different peers.
- The `n >= 3m + 1` bound matters for whether honest consensus can survive.
- A local majority rule can succeed or fail depending on room composition and adversarial behavior.
- After the round, a stepped graph view makes the message flow inspectable.

There is no instructor role and no multi-student classroom mode. Earlier iterations included a collaborative lobby; it added complexity without improving the learning experience and has been removed.

## 3. Product Scope

There is one user role: the student. The student opens the page, configures a room, plays a single round, and inspects the debrief. The session is private — there is no shared lobby and no observer view.

## 4. Core Product Requirements

### Student capabilities

The student must be able to:

- open the app without creating an account
- receive a reconnect-safe identity that survives page refresh
- configure a room: total node count `n` and malicious node count `m`
- start a session immediately, with bots filling every non-human seat
- participate in the broadcast phase (honest or malicious, depending on assigned role)
- inspect received messages during tally
- submit a final vote based on the node's local consensus
- reveal the debrief once the round is complete
- step through the staged debrief graph (honest, dishonest, summary) and inspect individual nodes and edges
- abandon an active room from the lobby in order to start a new one
- restart back to the lobby after viewing the debrief

## 5. Operating Constraints

- The app is a short-lived self-study simulation, not a long-term persistent system.
- All state is in-memory.
- Restarting the server clears all active rooms and sessions.
- The app must support real-time updates.
- Browser refresh and reconnect must not reset a student's identity or room state.

## 6. State Model

### Player

A `Player` represents either a connected human (one per session) or a server-controlled bot. Fields:

- `uuid` — durable identity (also used to reconnect across refreshes)
- `label` — display name (`Student N` for humans, `Bot <node_id>` for bots)
- `sid` — current Socket.IO session id, or null if disconnected
- `room_id` — assigned room, or null if waiting in the lobby
- `node_id` — alphabetic identifier inside the room
- `role` — `honest` or `traitor`
- `initial_value` — the room's initial order assigned to this node
- `uncertainty_seed` — seeded tie-break input for honest nodes
- `inbox` — messages received from peers in the broadcast phase
- `final_vote` — submitted vote in the tally phase
- `is_bot` / `origin` — bot flag (origin is always `human` for the player, `bot` for synthetic peers)
- `connected` — current connection status
- `has_broadcast` / `broadcast_payload` — whether the broadcast has been submitted, and what was sent

### Room

A `Room` represents a single self-study round. Fields:

- `room_id` — sequential identifier (`BGP-0001`)
- `phase` — one of broadcast, tally, awaiting debrief, debrief
- `size` — total node count
- `num_traitors` — number of malicious nodes
- `initial_order` — the honest order for this room (`Attack` or `Retreat`), chosen randomly
- `players` / `ordered_player_ids` — the human plus every bot, in node-id order
- `broadcast_log` — record of every message sent during the broadcast phase
- `debrief_revealed` — whether the debrief has been revealed

### GameState

A single in-memory `GameState` holds:

- `rooms` and `players` by uuid
- `uuid_to_sid` / `sid_to_uuid` mappings for routing real-time events
- monotonic counters for student labels and room ids
- a seeded `random.Random` for reproducible-ish tie-break and role assignment

## 7. Flows

### Lobby

On first connect the student is registered (a new `Player` is created if the uuid is new) and the page renders the lobby form: total nodes and malicious nodes inputs, fault-tolerance badge, and a Start Session button.

If the student already has an active room (e.g. they refreshed mid-game), the lobby form is replaced by whatever room phase the session is in. If the student attempts to start a new room while one is already active, the server emits `room_conflict` and the UI offers to abandon the current room and start fresh.

### Room creation

The server creates the room, assigns the student node ID `A`, creates bot players for every other seat, picks `num_traitors` role targets uniformly at random, gives each node a fresh `uncertainty_seed`, and immediately runs every bot's broadcast turn. If only the human's broadcast is missing, the room stays in the broadcast phase until they submit.

### Broadcast

- Honest nodes send their `initial_value` to every peer.
- Malicious nodes choose what to send to each peer individually.
- Honest votes are forced server-side; malicious payloads must include `Attack` or `Retreat` for every peer.

Bots use the same `apply_broadcast` path the human uses, so all messages flow through the same `BroadcastRecord` log.

### Tally

- Honest nodes compute local consensus from received messages: majority wins, ties are broken by the seeded `seeded_tie_break_vote`.
- The honest human must submit the consensus value; ties allow free choice.
- Malicious nodes may submit either value.
- Bots vote automatically when the tally phase opens.

Once every vote is in, the room moves to `awaiting debrief`.

### Debrief

The student reveals the debrief, which transitions the room to the `debrief` phase. The reveal payload contains every player's role/initial/local-consensus/final-vote/survival, plus the full message log. The student sees an outcome summary, per-node cards, and the interactive Vis.js graph.

Graph controls:

- Stage buttons: Honest, Dishonest, Summary
- Summary-stage edge toggles for overlaying honest or malicious edges
- Fit View — recenters the canvas
- Clear Selection — drops any selected node/edge
- (No zoom controls — zoom is disabled to keep the layout stable.)

### Restart

From the debrief view, the student presses Restart Exercise. This drops the current room (bots are deleted, the human is reset) and the student returns to the lobby with the same uuid, ready to configure another round.

## 8. Architecture

### Server

- Flask app with Flask-SocketIO (eventlet async worker)
- `app/app.py` — application factory; registers `/` (the student page) and `/healthz`
- `app/state/game_state.py` — the entire simulation state machine plus the singleton `game_state`
- `app/sockets/events.py` — Socket.IO handlers: `register`, `create_room`, `submit_broadcast`, `submit_final_vote`, `reveal_room_debrief`, `restart_to_lobby`, `disconnect`

Because all state is in memory, the app must run as a single Gunicorn worker. Restarting the process clears every session.

### Client

- `app/templates/index.html` — the single-page student template
- `app/static/js/student.js` — view rendering, socket wiring, debrief graph (Vis.js)
- `app/static/css/style.css` — shared styling

The page generates and persists a uuid in the URL on first load, so a refresh restores the same session. The client tracks the current snapshot from the server and re-renders the entire stage on every server event.

## 9. Out-of-Scope

The following are intentionally not part of this design:

- multi-student classroom mode
- instructor authentication, instructor dashboards, instructor takeover
- shared lobbies or queues
- horizontal scaling, multi-worker deployments, or external state stores
- persistent storage of past rounds
