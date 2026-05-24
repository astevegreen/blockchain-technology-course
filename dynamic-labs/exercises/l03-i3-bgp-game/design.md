# Byzantine Generals Simulation App Design Document

## 1. Document Intent

This document is the product and system handoff for an engineer building the Byzantine Generals Simulation App from scratch.

Its purpose is to describe:

- what the app is for
- what behaviors are required
- what state the system must manage
- how the major flows should work
- what constraints matter for implementation

This document is intentionally organized so that:

- the main sections describe authoritative product requirements
- implementation suggestions are separated from core requirements
- repeated requirements are minimized
- an engineer can distinguish required behavior from optional technical choices

## 2. Product Overview

The app is a real-time classroom simulation of the Byzantine Generals Problem. It is meant to help students understand distributed consensus by participating directly in a scenario where some nodes are honest, some are malicious, each node has only a local view of the network, and the network may fail to reach reliable consensus.

The product must support two teaching contexts:

- instructor-led collaborative classroom sessions
- self-directed student exploration

The educational goals are:

- Students should understand that each node acts on incomplete local information.
- Students should see how malicious participants can send conflicting messages to different peers.
- Students should understand the relationship between total nodes `n` and malicious nodes `m`, especially the `n >= 3m + 1` bound.
- Students should see how a local majority rule can succeed or fail depending on room composition and adversarial behavior.
- Instructors should be able to explain the round after the fact with a clear visual debrief.

## 3. Product Scope

The application has two primary user roles:

- Student
- Instructor

The application has two operating modes:

- `Collaborative Mode`: students join a shared lobby, and the instructor organizes rooms
- `Self-Service Mode`: a student creates and runs their own room without needing instructor intervention

Self-Service Mode is a feature that the instructor can enable or disable. It is not assumed to be permanently available.

## 4. Core Product Requirements

### Student capabilities

Students must be able to:

- join the app without creating an account
- receive a reconnect-safe identity
- refresh or reconnect without losing their current session
- join the collaborative lobby when in Collaborative Mode
- enter Self-Service Mode only when the instructor has enabled it
- configure their own self-service room, including participant count and number of malicious nodes
- start a self-service session without waiting for the instructor
- participate in the broadcast phase
- inspect received messages during tally
- submit a final vote based on their node's local consensus
- reveal the debrief once their room is complete
- view the debrief once it has been revealed

Students in Self-Service Mode must also be able to:

- choose the number of malicious nodes in their room
- explore the debrief with the same review controls the instructor uses for step-through analysis

### Instructor capabilities

Instructors must be able to:

- access a protected instructor dashboard
- observe the live collaborative lobby
- configure collaborative room generation
- choose the number of malicious nodes per room
- choose the number of bots to add to each collaborative room
- launch collaborative rooms
- monitor room progress
- take over stalled human nodes so a room can continue
- inspect room debriefs
- toggle whether Self-Service Mode is available to students

## 5. Operating Constraints

The following constraints are part of the product, not optional implementation details:

- The app is a short-lived classroom simulation, not a long-term persistent system.
- In-memory state is acceptable for the initial version.
- Restarting the server may clear all active rooms and sessions.
- The product must support real-time updates.
- Browser refresh and reconnect must not reset a student's identity or room state.
- The app must run in Docker.
- The app must work behind an Nginx reverse proxy.

## 6. Canonical Terminology

Use the following terms consistently throughout the product and implementation:

- `Collaborative Mode`: instructor-led, shared-lobby mode
- `Self-Service Mode`: student-run mode where one human starts a room and bots fill the rest
- `malicious node`: the product-facing term for what the implementation may internally call a traitor or Byzantine participant
- `honest node`: a non-malicious participant
- `room`: a single simulation instance
- `debrief`: the post-round revealed state and visualization

Avoid mixing `single-player`, `solo`, `individual`, and `self-serve` in the implementation-facing specification unless a separate glossary is provided. The user-facing product can still choose different labels later, but the engineering document should use one canonical term.

## 7. Domain Model

The system should be designed around four conceptual entities:

- `Player`
- `Room`
- `GlobalState`
- `Settings`

### Player

A player represents either:

- a connected human student
- a bot created to fill a room
- a previously human-controlled node that has been taken over

A player record should be able to represent:

- stable identity
- current connection state
- assigned room
- assigned node ID
- honest or malicious role
- initial order
- received messages
- final vote
- whether the node is currently bot-controlled
- whether the node originated as human or bot
- recent activity timestamps

Important semantic rules:

- a human taken over for inactivity remains a human-origin participant but becomes bot-controlled
- connection state and control state are separate concerns
- player identity must outlive a socket connection

### Room

A room represents one simulation run.

A room should be able to represent:

- operating mode
- current phase
- configured participant count
- configured malicious node count
- whether the session has started
- ordered participant list
- message history
- whether the debrief has been revealed

### GlobalState

Global state should be able to represent:

- the collaborative lobby queue
- all current players
- all current rooms
- socket-to-player mappings
- instructor connections
- a monotonically incrementing room ID counter for assigning unique room identifiers

### Settings

A separate settings object should exist rather than embedding all feature toggles into unrelated state.

At minimum, settings should include:

- `self_service_enabled: bool`

Optional settings that may be useful if the team wants them:

- default collaborative room size
- default self-service room size
- default malicious node count
- maximum allowed room size

## 8. Identity and Reconnection Model

Students should have a stable identity that survives refreshes and reconnects without requiring an account system.

Required behavior:

- each student receives a stable identifier encoded in the URL
- reconnecting with the same identifier restores the same player
- if the player is in a room — whether a collaborative room or a self-service room — the student is restored into that room's current state
- if the player is still in the collaborative lobby, the student should return to the lobby
- self-service rooms have no lobby phase; a self-service student who reconnects is treated as reconnecting to an in-progress room

This identity model exists to support classroom usage on laptops and mobile browsers where refreshes and tab switches are common.

Identity tokens are stored only in the URL. No session cookies or local storage are used to track player identity. Each browser tab that navigates to the base URL without an existing token receives a new, distinct identity. Refreshing or navigating within the same tab preserves identity through the URL. Two tabs open simultaneously are treated as two separate players, even on the same device.

## 9. Lobby and Availability Rules

### Student entry point

When a student first loads the app, their experience depends on the current Self-Service Mode setting:

- if Self-Service Mode is disabled, the student is placed directly into the collaborative lobby queue without a mode selection step
- if Self-Service Mode is enabled, the student sees a mode selection screen and chooses between Collaborative Mode and Self-Service Mode before proceeding

In both cases, the student lands in the lobby view. The mode selection (when shown) is presented from within the lobby, not as a separate pre-lobby screen.

### Collaborative lobby

The collaborative lobby is the waiting area for students participating in instructor-led sessions.

Required behavior:

- students in Collaborative Mode join the lobby
- the instructor sees current lobby membership
- students see their own queue status
- disconnected students should not be removed immediately
- a student in the lobby should be removed after 60 seconds with no active socket

The 60-second timeout applies only to students who are still in the lobby and have not yet been assigned to a room.

### Self-Service Mode availability

Self-Service Mode must be controlled by the instructor.

Required behavior:

- the instructor can enable or disable Self-Service Mode from the dashboard
- when disabled, students must not be able to start self-service rooms
- when disabled, students are placed directly into the collaborative lobby without a mode selection screen
- when enabled, students see the mode selection screen described in the entry point section above

The system behavior must be enforced on the server regardless of what the client displays.

## 10. Mode Flows

### Collaborative Mode flow

The collaborative flow should work like this:

1. Students enter the collaborative lobby.
2. The instructor previews room groupings from the available lobby participants.
3. For each room, the instructor sets:
   - malicious node count
   - bot count
4. The system validates and displays the fault-tolerance math for each room.
5. The instructor launches the rooms.
6. Each room progresses through broadcast, tally, awaiting debrief, and debrief.
7. The instructor or any student assigned to the completed room can reveal the debrief.

### Self-Service Mode flow

The self-service flow should work like this:

1. A student enters Self-Service Mode.
2. The student chooses:
   - total participants
   - number of malicious nodes
3. The UI displays the Byzantine fault-tolerance math state.
4. The student clicks start.
5. The system immediately creates a room for that student.
6. Bots automatically fill the remaining seats.
7. The room starts without instructor action.
8. Once the room is complete, the student can reveal and inspect the debrief independently.

## 11. Room Configuration Rules

The system must support configurable room composition.

### Collaborative Mode room configuration

For each collaborative room:

- the number of human students comes from the lobby grouping
- the instructor may add zero or more bots; bot count must be a non-negative integer
- total participant count equals human count plus bot count
- malicious node count must be less than total participants

### Self-Service Mode room configuration

For each self-service room:

- there is exactly one human participant
- the student chooses total participants
- the student chooses the number of malicious nodes
- bots fill all remaining seats automatically
- malicious node count must be less than total participants

A student may have at most one active self-service room at a time. Because each browser tab generates a distinct player identity, this constraint is per-tab. A student who attempts to create a second self-service room while one is still active should be warned and offered the choice to abandon the current room or cancel.

### Byzantine math validation

The app should display whether a room is fault tolerant under the standard condition:

- fault tolerant when `n >= 3m + 1`
- consensus at risk when `n < 3m + 1`

This validation is instructional. It should inform the user, but it does not have to block room creation.

## 12. Simulation Rules

### Role assignment

When a room is created:

- each participant receives a node ID
- a subset of nodes are assigned as malicious
- the remaining nodes are honest
- each room receives a single original order of `Attack` or `Retreat`, and every node starts from that same initial order
- human participants may be assigned as malicious nodes; role assignment is random
- a student is notified of their assigned role (honest or malicious) when the room starts

### Broadcast phase

Honest node behavior:

- an honest node sends the same value to every peer
- that value must match the node's own initial order

Malicious node behavior:

- a malicious node may send different values to different peers

Human malicious node behavior:

- a human assigned as a malicious node is presented with a per-peer message selection UI during broadcast
- for each peer, the human independently chooses to send `Attack` or `Retreat`
- the UI must make clear that the student is playing a malicious role and that per-peer choices are intentional

Bot behavior:

- bots do not connect via WebSocket; all bot actions are executed server-side without socket input
- bot actions (broadcast submissions and final votes) are processed through the same phase-advance logic as human submissions; state updates are emitted to room participants as normal so all clients remain in sync
- honest bots send their own initial order consistently
- malicious bots always act maliciously: they send the dishonest answer to every peer, using the value opposite to the room's correct honest consensus

### Tally phase

Each node computes its local result from:

- all received peer messages

The local voting rule is:

- take the majority of the received values visible to that node
- if a bot-controlled node is perfectly tied, break the tie with a seeded 50/50 choice between the two possible final values
- tie-break randomness for bot-controlled nodes should come from distinct per-node seeds derived from a single session seed so all views stay consistent

### Final vote restriction

This is a core product rule for honest nodes.

Required behavior for honest human nodes:

- the client computes the node's local result from the received message set
- if there is a clear majority, the UI presents the computed result and the student confirms it rather than freely choosing `Attack` or `Retreat`
- if the node's visible values are perfectly tied, the UI must surface that tie and let the human choose the final vote manually
- tally computation runs on the client; server-side re-verification is not required
- this prevents students playing honest nodes from using privileged knowledge to deliberately break the exercise

Required behavior for malicious human nodes:

- no vote restriction applies; malicious nodes are not expected to act consistently
- the final vote is still derived from the node's received peer messages using the same local majority rule, but the student is not prevented from overriding it
- the debrief must reflect what the malicious node actually submitted

## 13. Phase Model

The product should use a clear, finite phase model.

The product uses the following canonical phases:

- `Queue`: a collaborative room that has been configured by the instructor but not yet launched; self-service rooms skip this phase and enter `Broadcast` immediately upon creation
- `Broadcast`: participants submit their messages to peers
- `Tally`: participants compute local consensus from received messages
- `Awaiting Debrief`: all votes are in; the room is waiting for reveal
- `Debrief`: the debrief has been revealed and is visible to participants

Required progression behavior:

- a room enters `Broadcast` once the session starts
- a room enters `Tally` once all participants — including bots and any bot-taken-over nodes — have submitted a broadcast; bot broadcasts are submitted server-side immediately when the room enters `Broadcast`
- a room enters `Awaiting Debrief` once all participants have a final vote; bots compute and submit their votes server-side immediately when the room enters `Tally`
- a room enters `Debrief` once the debrief is revealed

The implementation may use different internal numeric representations, but the product behavior must match this model.

## 14. Disconnect, Timeout, and Takeover Behavior

These three behaviors are distinct and must be treated separately.

### Disconnect

If a student's socket drops after joining a room, the node is immediately transitioned to bot control:

- the room does not pause or wait for the disconnected student
- the bot algorithm takes over pending phase actions for that node (broadcast or vote, depending on current phase)
- the student's player identity and room assignment are preserved in server state
- if the student reconnects using the same URL before the room completes, they return to the room in observer mode for the current phase
- whether a reconnecting student can reclaim active control of a bot-taken-over node mid-round is an open question (see Section 23); the safe default is observer mode for the remainder of that phase

### Lobby timeout

If a student disconnects while still in the collaborative lobby:

- they should remain eligible for restoration briefly
- they should be removed after 60 seconds with no active socket

### Takeover (instructor-initiated)

Takeover is a separate mechanism from disconnect-triggered bot control. It applies to nodes that are connected but unresponsive — the instructor's judgement call.

If a room is stalled because a connected human is not acting:

- the instructor manually triggers takeover for the specific node from the dashboard
- there is no automatic stall detection or stall timeout; the instructor decides when to act
- the node transitions to bot control and the bot completes any pending phase actions
- the control change must be visible in the room state and in the debrief

## 15. Debrief Model

The debrief is the revealed post-round view of the full room state.

The system should support:

- revealing the debrief
- transmitting the revealed room state to clients
- visually reviewing the round

### Reveal permissions

Once a room reaches `Awaiting Debrief`:

- the instructor can reveal any completed room individually from the dashboard; there is no global reveal-all action
- any student assigned to that room can reveal it

Revealing the debrief should make it visible to:

- the instructor dashboard
- students assigned to that room

### Student debrief experience

All students — both collaborative and Self-Service Mode — receive the full interactive debrief explorer. The instructor also has access to the full explorer. There is no separate simplified summary view for any user type.

## 16. Debrief Visualization Requirements

The debrief visualization is a core teaching tool.

At a minimum, it should support:

- a graph of the room participants
- a visual distinction between honest and malicious behavior
- node and edge inspection
- zoom
- pan
- staged explanation of what happened

The staged explanation should support:

- Stage 1: show honest broadcasts clearly
- Stage 2: show malicious broadcasts clearly
- Stage 3: show which honest nodes aligned with the correct honest consensus

The visualization should help answer these questions:

- What was each node's initial order?
- Which nodes were malicious?
- What did each sender tell each recipient?
- Which final votes matched the correct honest consensus?
- Which honest nodes were misled?

Self-Service Mode students must have access to these review controls. Instructors must also have access to them.

All students (collaborative and self-service) and the instructor receive these full review controls. See Section 15 ("Student debrief experience").

## 17. Student UI Requirements

The student UI should be a state-driven interface, not a client-authoritative simulation.

That means:

- the server is the source of truth for room phase and player state
- the client renders based on server snapshots
- the client should not independently decide room progression

The student UI must support at least these high-level states:

- collaborative lobby
- self-service room configuration
- broadcast
- waiting for others during broadcast
- tally
- waiting for debrief
- debrief
- observer mode when bot takeover occurs

The exact number of frontend view components is an implementation choice.

## 18. Instructor UI Requirements

The instructor dashboard must support:

- seeing lobby membership
- previewing collaborative rooms
- editing malicious node count per room
- editing bot count per room
- toggling Self-Service Mode availability
- launching rooms
- monitoring room progress
- forcing stalled rooms forward
- inspecting room debriefs

The dashboard should be optimized for classroom use, including projection or screen sharing.

## 19. Security and Authorization Requirements

Required authorization rules:

- instructor-only actions must be protected
- student-only room actions must be limited to students assigned to the relevant room
- self-service availability must be enforced on the server, not just hidden in the UI

The instructor interface must be protected with HTTP Basic Auth. Credentials are configured via environment variables. If the environment variables are not set, the app must default to `admin:admin`. This default is acceptable for classroom use but should be documented as insecure for any public-facing deployment.

Student access may remain anonymous if reconnect-safe identity is still provided.

## 20. Deployment Requirements

The application must:

- run locally for development
- run in Docker
- work behind Nginx
- correctly support WebSocket traffic through the reverse proxy
- serve required frontend dependencies reliably in deployment environments

Because the initial product is in-memory:

- a single-process deployment model is acceptable and likely preferable
- multi-worker or horizontally scaled deployment should not be assumed without shared state redesign

## 21. Non-Goals

The initial version does not need to provide:

- persistent user accounts
- durable historical storage
- multi-day room recovery
- horizontal scaling across multiple app instances
- generalized consensus simulation beyond the Byzantine Generals exercise

## 22. Acceptance Criteria

The implementation should be considered complete when all of the following are true:

- Students can join Collaborative Mode and be grouped into rooms by the instructor.
- The instructor can choose malicious node count and bot count per collaborative room before launch.
- The instructor can enable or disable Self-Service Mode for students.
- A student cannot start Self-Service Mode when it is disabled.
- A Self-Service Mode student can choose total participants and malicious node count, then start immediately.
- Self-Service Mode rooms are automatically filled with bots.
- Honest node broadcasts are always consistent with the sender's initial order.
- Malicious nodes can send conflicting messages.
- Human players can be assigned as malicious nodes.
- A human playing a malicious node is presented with per-peer message selection during broadcast.
- Honest human final votes are constrained to the node's computed local consensus.
- Malicious human final votes are not restricted.
- A disconnected lobby student is removed after 60 seconds of no active socket.
- A student who disconnects from an active room has their node immediately taken over by a bot.
- A reconnecting student returns to their room in observer mode.
- The instructor can force progress on a connected-but-unresponsive node via manual takeover.
- Both disconnect-triggered and instructor-triggered bot takeover are visible in the debrief.
- Any student assigned to a completed room can reveal the debrief.
- The debrief becomes visible to both the assigned students and the instructor.
- All users — instructors, collaborative students, and Self-Service Mode students — can inspect debriefs using the full interactive debrief explorer.
- The application runs correctly in Docker and behind Nginx.

## 23. Open Questions

The following questions are not blockers for understanding the product, but they should be resolved before or during implementation planning so engineers do not make inconsistent assumptions.

### 23.1 Reconnect after bot takeover — can the student reclaim control?

Decision needed:

- If a student's node was taken over by a bot due to disconnect, and the student reconnects before the room completes, can they reclaim active control of their node for the remainder of the current phase?

Recommended default:

- the student returns in observer mode for the remainder of the current phase
- if the room has not yet advanced to the next phase (i.e., the bot has not yet completed the node's pending action), reclaim may be allowed as an optional enhancement

Reason:

- observer mode on reconnect is the simpler and safer implementation; mid-phase control handoff requires careful state coordination

### 23.2 Configuration limits

Decision needed:

- What maximum room size should the product support in practice?

Recommended default:

- keep the implementation bounded by a single alphabet-based node ID set unless there is a clear teaching need for larger rooms

Reason:

- larger rooms complicate the graph and the classroom experience faster than they increase educational value

### 23.3 Instructor defaults

Decision needed:

- Should the app remember instructor-selected defaults such as room size, bot count, or Self-Service Mode availability across restarts?

Recommended default:

- no persistence for the initial version

Reason:

- it aligns with the in-memory classroom-session model and keeps the first implementation simpler

## 24. Risks and Engineering Considerations

The following risks are the most likely to cause incorrect behavior, confusing UX, or implementation churn.

### 24.1 State drift between server and client

Risk:

- if the client starts making phase decisions locally, the UI can diverge from the actual room state

Mitigation:

- keep the server authoritative for room phase, control lock state, and debrief availability
- render clients from snapshots instead of local simulation logic

### 24.2 Reconnect complexity

Risk:

- reconnect-safe identity can become inconsistent if player identity is tied too closely to the current socket

Mitigation:

- treat socket connections as ephemeral
- treat player identity and room assignment as longer-lived server-side state
- make reconnection restore a full state snapshot rather than partial UI hints

### 24.3 In-memory architecture limitations

Risk:

- engineers may accidentally deploy with multiple workers or assume persistent state

Mitigation:

- document clearly that this version is single-process and in-memory
- enforce conservative deployment defaults
- keep this limitation visible in deployment documentation

### 24.4 Bot and takeover edge cases

Risk:

- disconnect-triggered takeover, instructor-triggered takeover, and reconnect behavior can interact in confusing ways

Mitigation:

- treat the two takeover paths (disconnect vs. instructor-initiated) as separate code paths with separate audit trails in the debrief
- ensure both takeover types are visible in room state and debrief data
- test takeover during both broadcast and tally phases
- test reconnect behavior for nodes that were taken over mid-phase

### 24.5 Overly coupled frontend states

Risk:

- a frontend that encodes too many assumptions about mode-specific behavior becomes brittle as product requirements change

Mitigation:

- drive the UI from a small set of server-declared views or state descriptors
- avoid duplicating simulation rules in the browser

### 24.6 Deployment-time dependency failures

Risk:

- graphing or socket client libraries may fail in restricted networks if they are pulled from external CDNs

Mitigation:

- package required frontend libraries with the deployed app
- test the app in a containerized environment without external CDN reliance

## 25. Implementation Milestones

The project will be easier to deliver if it is built in coherent vertical slices rather than as isolated frontend and backend pieces.

### Milestone 1: Core scaffolding and state model

Goals:

- establish the app shell
- define the core domain model
- create the centralized server state object
- support student registration and instructor authentication

Deliverables:

- application boot path
- student and instructor routes
- core `Player`, `Room`, `GlobalState`, and `Settings` model
- reconnect-safe identity registration

Definition of done:

- a student can connect and be represented in server state
- an instructor can access the dashboard

### Milestone 2: Collaborative lobby and room launch

Goals:

- support collaborative student queueing
- support instructor room previewing and launch
- support malicious-node and bot-count configuration

Deliverables:

- collaborative lobby
- lobby timeout behavior
- room preview UI and server logic
- instructor Self-Service Mode toggle
- collaborative room launch flow

Definition of done:

- students can queue
- instructor can preview and launch mixed human-plus-bot rooms
- disabled Self-Service Mode is enforced

### Milestone 3: Core gameplay loop

Goals:

- implement broadcast and tally
- enforce honest and malicious behavior correctly
- enforce the final-vote rule

Deliverables:

- broadcast submission flow
- bot broadcasting logic
- tally flow
- local-consensus vote enforcement
- room phase progression

Definition of done:

- a room can complete a full round from launch through awaiting debrief

### Milestone 4: Resilience and takeover

Goals:

- handle disconnects predictably
- support takeover for stalled rooms
- preserve room continuity through reconnects

Deliverables:

- reconnect restore behavior
- lobby inactivity pruning
- instructor takeover controls
- correct human-origin versus bot-origin tracking

Definition of done:

- a stalled room can be completed without manual state repair
- a reconnecting student returns to the correct room state

### Milestone 5: Debrief and visualization

Goals:

- reveal and inspect completed rooms
- provide the core educational review tools

Deliverables:

- debrief payload construction
- instructor debrief visualization
- Self-Service Mode student debrief explorer
- collaborative student debrief experience per chosen product decision

Definition of done:

- completed rooms can be revealed and reviewed clearly

### Milestone 6: Deployment hardening

Goals:

- package the app for realistic classroom deployment
- validate reverse-proxy compatibility

Deliverables:

- Docker packaging
- local static dependency packaging
- Nginx-compatible WebSocket deployment
- deployment documentation

Definition of done:

- the app runs correctly in Docker and through an Nginx reverse proxy

## 26. Suggested Reference Implementation Notes

This section is intentionally non-authoritative. It suggests a reasonable implementation approach, but the behavior above is what matters.

### 26.1 Reasonable stack

- Python 3.10+
- Flask
- Flask-SocketIO
- Eventlet
- Vanilla JavaScript
- HTML/CSS
- a graphing library such as Vis Network

### 26.2 Reasonable architecture

- server-rendered HTML shells
- WebSocket-driven state updates
- centralized in-memory game state object
- a state-serialization layer for student and instructor snapshots

### 26.3 Reasonable project layout

- `app/app.py`
- `app/config.py`
- `app/state/game_state.py`
- `app/sockets/events.py`
- `app/templates/`
- `app/static/`
- `requirements.txt`
- `Dockerfile`
- `README.md`

### 26.4 Reasonable event model

An implementation will likely need real-time events for:

- registration
- room preview
- room launch
- broadcast submission
- final vote submission
- force takeover
- debrief reveal
- dashboard state refresh
- student state restoration

Exact event names are intentionally not prescribed here. The team should choose names that are consistent and easy to reason about.

## 27. One-Sentence Summary

This product is a real-time Byzantine consensus teaching simulator that supports instructor-led collaborative play and instructor-governed self-service exploration, with reconnect-safe identity, bot-backed room completion, and a visual debrief designed for learning.
