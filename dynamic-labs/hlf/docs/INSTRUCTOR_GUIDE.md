# Instructor Guide — Hyperledger Fabric Long Lab

Pedagogical plan and teaching notes. For the operational side (setup,
live ops, resets, troubleshooting) see
[CLASSROOM_OPERATIONS.md](CLASSROOM_OPERATIONS.md).

## Learning objectives

By the end of the lab students should be able to:

- Explain the roles of **peers**, **orderer**, **channels**, and
  **chaincode** in a permissioned Fabric network.
- Issue a real credential (a diploma) from their own org's peer and
  verify it from another org on the same shared ledger.
- Read blocks and transactions in the explorer and connect them to the
  **propose → endorse → order → validate → commit** lifecycle.
- Predict and observe the consequences of **peer outages**, **orderer
  outages**, and **endorsement policy violations**.
- Describe how **MSP identity**, **endorsement policy**, and **channel
  governance** control who can do what, and why "permissioned" doesn't
  mean "centralised".
- Apply the same infrastructure to a consortium with **competing
  interests** (trade finance).

## Classroom topology

This is a multi-tenant classroom lab, not a single-user sandbox. Every
student has:

- Their own **org** and **peer** (`peer0.studentNN.example.com`).
- Their own admin **MSP** identity — they cannot act as another student.
- Their own per-student exercise surface at `/labs/hlf/c/<uuid>/…`.
- A shell (`ttyd`) scoped to their own peer.

All students share:

- One **ledger** on the channel `diplomas`.
- Four **consortium peers** (Cascadia State, Chesapeake Canoe University, South
  Hudson, Maple Leaf) under 3-of-4 MAJORITY endorsement.
- One **orderer**.

Writes made by one student show up in every other student's explorer.
That is pedagogically load-bearing — Chapter 1 is about seeing
classmates' diplomas appear on the same ledger.

## Recommended flow (90 minutes)

### 0. Before you start (5 min, before class)

- Start the network from the instructor console.
- Set pool size to ~20% of class size.
- Post the claim URL (`/labs/hlf/claim`) where students can find it.

### 1. Orientation — Chapter 0 (10 min)

- Have everyone hit `/labs/hlf/claim`. Watch the lane grid fill in.
- Walk through the lesson UI: sidebar TOC, current exercise card, the
  explorer button, the student console button.
- Call out that each student has their own org and peer, but the ledger
  is shared — classmates' transactions will appear in their explorer.

### 2. Chapter 1 — Issue & Verify a Diploma (25 min)

- Students issue a diploma from their own peer. Have them use a name
  they'll recognise so they can pick it out of the explorer.
- Open the explorer as a class — watch diplomas stream in from every
  student.
- Pair students: A's diploma is verified from B's explorer view as
  though B were a prospective employer.

Teaching moment: **who signed this?** The transaction detail shows the
endorsing peer's MSP identity. A diploma issued by Cascadia State shows
a Cascadia State signature — you can't fake that from Chesapeake Canoe's peer.

### 3. Chapter 2 — How That Transaction Worked (15 min)

- Drill into one student's diploma transaction.
- Walk the five lifecycle stages: propose (client → their peer),
  endorse (their peer signs), order (orderer batches into a block),
  validate (every peer validates the policy), commit (state updates).
- Block view vs. world state view — both come from the same chain.

### 4. Chapter 3 — What Happens When Things Break (15 min)

- Use **Scenario Controls** → Peer outage: Cascadia State. Ask a
  student whose org isn't Cascadia to issue a diploma. It should still
  succeed — 3-of-4 MAJORITY holds.
- Recover Cascadia. Then drop two peers (Endorsement policy demo).
  Attempt a write. It fails with ENDORSEMENT\_POLICY\_FAILURE.
- Recover, then drop the orderer. Reads still work; new writes stall.
- Framing: peer outages are about **availability**, orderer outages are
  about **commit ordering**, policy violations are about **integrity**.

### 5. Chapter 4 — Who Controls the Network (10 min)

- Open the governance panel. MSPs, policies, admin identities.
- Ask: "who could issue a diploma as Cascadia State?" Answer: only an
  identity signed by Cascadia's CA. That's the MSP doing its job.
- Contrast with Bitcoin/Ethereum: there, anyone with the right signature
  can write. Here, the signer must be a recognised member.
- Use Meridian (Org5) as the pedagogical anchor: it is a channel member
  with a full ledger mirror but is deliberately *absent* from the
  Endorsement / LifecycleEndorsement policies. Every student org sits in
  exactly the same posture — members who can read and propose, but who
  cannot themselves endorse a write. That separation between "channel
  membership" and "endorsement authority" is the governance lever worth
  dwelling on here.

### 6. Chapter 5 — Credentials to Consortium (10 min)

- Trade finance capstone. Same infrastructure, competing interests.
- Discuss role-tagged assets (exporter/importer/bank/customs metadata)
  and how they map to organization identity.

### 7. Wrap-up (5 min)

- What persists, what doesn't: ledger survives peer reset; peer state
  survives claim release under `sticky`; nothing survives Reset Network.
- What's real vs. presentation: see the "Infrastructure Notes" panel on
  the instructor console for the honest list.

## Per-chapter instructor notes

**Chapter 0 (Orientation).** The claim flow is the quiet star — 20
students hit it in the first minute and the lane grid lights up. If
students can't reach the URL, the usual problem is the outer router
isn't up (`docker compose -f router up -d`).

**Chapter 1 (Issue & Verify).** The first write from a student's peer is
slow (~10s) because the peer is still catching up on the channel. By
the second write it's snappy. Warn them before they think the lab is
broken.

**Chapter 2 (Lifecycle).** Best moment to pull up the transaction detail
screen and show the endorsing peer's certificate fingerprint. It's the
concrete "who signed this" anchor.

**Chapter 3 (Faults).** If you trigger a consortium peer outage, expect
the lane grid to _not_ change colour — student peers are still up. The
outage is on a consortium peer, visible in Node Overview and Scenario
Controls. If you want to drop a specific student's peer to show local
vs. global failure, use the per-lane **Stop** button on that lane.

**Chapter 4 (Governance).** The Governance panel is cached ~15s, so if
you make a live policy change don't panic if the UI lags.

**Chapter 5 (Trade finance).** If you want a concrete demo, seed some
trade-finance-shaped assets first (the role-tags-on-assets pattern).
The instructor panel's Seed Sample Transactions currently seeds
diplomas; extend `seed_routes` / `hlf_service.seed_*` if you want a
second preset for trade finance.

## Guided Teaching Prompts panel

Bottom of the instructor console. Pulls live exercise state for the
current class, including per-exercise "live checks" (e.g. "did anyone
issue a diploma yet?"). Good for glancing at progress without
interrupting students.

## Operational reminders

- **Per-lane Reset** wipes one student's peer. Shared ledger is fine.
- **Reset Network** wipes everything. Use between classes, not during.
- **Pause sweeper** during exams so idle students don't get auto-released.
- **Release** on a claim hands the lane back to the pool per the current
  policy (`sticky` = keep peer state; `wipe` = reset back to clean).

## Pre-class checklist

- [ ] Host has ≥16 GB RAM free for 20 students + consortium
- [ ] Shared router up (`docker compose -f router ps`)
- [ ] HLF lab up (`./lab-manager.sh status hlf`)
- [ ] Instructor credentials set and tested (yellow banner gone)
- [ ] Network started from instructor console
- [ ] Pool size set appropriately
- [ ] Claim URL posted for the class
- [ ] Seeded baseline transactions if you want a non-empty opening ledger

## Post-class checklist

- [ ] Release any idle claims (or let sweeper do it)
- [ ] **Reset Network** if you want a clean slate for the next class
- [ ] Rotate `INSTRUCTOR_AUTH_KEY` if policy dictates
- [ ] `docker system prune -f` if disk is getting tight

## Debug logging

All backend + lab-manager tracing is off by default to reduce noise.
Enable by setting `HLF_DEBUG=1` in the `hlf-runner` environment and
restarting the service. Logs land at:

- Host: `runtime/debug.log`
- In-container debug sink: `/fabric-samples/test-network/runtime-debug.log`

Use it when tracking:

- Chaincode deploy failures (`ENDORSEMENT_POLICY_FAILURE` at commit)
- Intermittent invoke/query failures
- Network health mismatches across the classroom

## Further reading

- [CLASSROOM_OPERATIONS.md](CLASSROOM_OPERATIONS.md) — runbook
- [STUDENT_GUIDE.md](STUDENT_GUIDE.md) — what students see
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — common issues
- [../../hlf-phase7-classroom-plan.md](../../../hlf-phase7-classroom-plan.md) — multi-tenant design
