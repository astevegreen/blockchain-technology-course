# Instructor Guide — Hyperledger Fabric

Instructor-only: this file is left out of the student site and the
student VM. For the operational side (setup, live ops, resets,
troubleshooting) see [CLASSROOM_OPERATIONS.md](CLASSROOM_OPERATIONS.md).

Day 5 runs this lab as a **30-minute demo that the instructor drives**. Students watch
the projected screen; nobody claims a lane. The longer student lab (about 90
minutes) is described after the demo for a later run.

## Day 5 demo: watch the gatekeeper work (about 30 minutes)

The demo pairs with the slide "Fabric demo: watch the gatekeeper work" in
`blockchain-course/lessons/permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd`.
That slide hands students three questions, and each beat below answers one:

1. **Who signed it?** Beat 1, the forged diploma.
2. **Who decides?** Beat 2, the endorsement policy with two peers down.
3. **Who can see it?** Beat 3, Meridian (Org5), the member that never endorses.

The outputs below were captured from the live network on 31 Oct 2026
(Fabric test network, channel `diplomas`, chaincode `basic`). Your ids,
transaction ids and timestamps will differ; the messages will not. If the
network will not start in class, project these outputs instead: they are the
demo's fallback.

### Before class (about 10 minutes, not counted in the 30)

1. Bring up the core network only (the four consortium peers, Meridian and the
   orderer), with no student lanes to fill. From `dynamic-labs/`:

   ```bash
   ./lab-manager.sh deploy --mode instructor --hlf-student-capacity 1
   ./lab-manager.sh start hlf
   ```

   Capacity 1 is the smallest the lab manager accepts. It provisions one
   student lane that nobody claims, so the network stays small enough for a
   laptop. You don't need the 16 GB host the student lab requires.
2. Log in at `/instructor/` and open `/labs/hlf/hlf_instructor.html`. Wait
   until the network shows as up.
3. Press **Seed Sample Transactions** so the ledger is not empty. The
   endorsement-policy scenario in beat 2 needs at least one diploma on the ledger.
4. From the instructor console's node links, open three consoles in separate
   tabs: **Org1 · Cascadia State**, **Org2 · Chesapeake Canoe** and
   **Org5 · Meridian**. Each one is a shell that signs as that organization.
   Also open **Open Explorer**.
5. Pick a short tag for today's ids, such as the date (`1031` below). A diploma
   id can be used only once on a ledger, so use a new tag for each class unless
   you ran **Reset Network** afterwards.

### Beat 1: who signed it? (8 minutes)

In the **Org2 · Chesapeake Canoe** console, try to issue a diploma in
Cascadia State's name:

```
invoke create diploma-1031-forgery credential 4 "George Washington" 2024 "History" "Bachelor of Arts" "Cascadia State"
```

Expected output:

```
Error: endorsement failure during invoke. response: status:500 message:"Issuer forgery rejected: transaction signed by Org2MSP (Chesapeake Canoe University) but the credential claims to be issued by \"Cascadia State\" (Org1MSP). A school can only issue diplomas under its own MSP."
```

Now issue the same diploma honestly, from the **Org1 · Cascadia State** console:

```
invoke create diploma-1031-honest credential 4 "George Washington" 2024 "History" "Bachelor of Arts" "Cascadia State"
```

Expected output (the lines that matter):

```
... txid [77017d18...] committed with status (VALID) at peer0.mapleleaf.example.com:13051
... txid [77017d18...] committed with status (VALID) at peer0.southhudson.example.com:11051
... txid [77017d18...] committed with status (VALID) at peer0.chesapeakecanoe.example.com:9051
... txid [77017d18...] committed with status (VALID) at peer0.cascadiastate.example.com:7051
... Chaincode invoke successful. result: status:200 payload:"{...\"IssuerMSP\":\"Org1MSP\",\"Issuer\":\"Cascadia State\"...}"
```

Read it back from the Chesapeake Canoe console, the school that just failed to
forge it:

```
query diploma-1031-honest
```

```
{
  "DegreeType": "Bachelor of Arts",
  "FieldOfStudy": "History",
  "ID": "diploma-1031-honest",
  "Issuer": "Cascadia State",
  "IssuerMSP": "Org1MSP",
  ...
}
```

What to say: Chesapeake Canoe held a valid identity and the consortium peers
would endorse its transactions, but the chaincode reads the signer's
organization from the certificate on the proposal, which cannot be typed in,
and refuses a diploma in another school's name. The forged record never
reached a block. `IssuerMSP` on the honest diploma came from that same
certificate. The `Issuer` text is just a display name. The peers that endorsed
it show only as the four `committed with status (VALID)` lines: the Explorer
does not yet name endorsing organizations.

### Beat 2: who decides? (8 minutes)

First show the rule. The channel's endorsement policy, as written in the
network's configuration
(`dynamic-labs/hlf/managed_runtime/configtx-4org-students.yaml`, `Endorsement`
under `Application`), is:

```
OutOf(3, 'Org1MSP.peer', 'Org2MSP.peer', 'Org3MSP.peer', 'Org4MSP.peer')
```

Any three of the four consortium schools must sign a write. Meridian and the
student organizations are not in the list. On screen, beat 1's four
`committed with status (VALID)` lines show the consortium peers that took part.

Then, in **Scenario Controls**, press **Activate** on **Endorsement policy demo**.
It stops two consortium peers, Chesapeake Canoe and Maple Leaf, which leaves two
of the four. The console reports:

```
Triggered endorsement-policy demo (stopped 2 peers) and captured a failed write probe.
```

From the **Org1 · Cascadia State** console, try an honest write:

```
invoke create diploma-1031-two credential 4 "George Washington" 2024 "History" "Bachelor of Arts" "Cascadia State"
```

Expected output:

```
[hlf] Only 2 of 4 peers are reachable.
[hlf] The channel endorsement policy requires 3-of-4 peers to sign, so this transaction would fail at commit validation.
[hlf] Refusing to submit. Ask the instructor to recover at least one more peer, then retry.
ENDORSEMENT_POLICY_FAILURE: insufficient live peers (2/4, need 3)
```

Say it plainly: the lab's console helper counts the live peers and stops here.
A production client would usually fail to gather enough endorsements and
never submit, and one that submitted anyway would see the write marked invalid
at validation, because it would carry two signatures where the policy needs
three. Either way it never changes the ledger, even though Cascadia State is
the honest issuer. Press **Restore** on the same card before beat 3:

```
Recovered Chesapeake Canoe + Maple Leaf peers for endorsement-policy scenario.
```

### Beat 3: who can see it? (8 minutes)

In the **Org5 · Meridian** console:

```
query all
```

Every diploma on the ledger comes back, including `diploma-1031-honest` from
beat 1. Meridian is a channel member: its peer holds every block, though it is
in no endorsement rule.

In the Explorer, open **Governance**. The organizations listed are the
channel's members: Org1MSP to Org4MSP, Org5MSP (Meridian), and one MSP per
student lane provisioned (`StudentNNMSP`). Being on this
list is what lets a peer receive blocks at all. An organization that is not
listed has no certificate the channel recognizes, so it has no copy to read.

If someone asks whether Meridian can write, show them. From the Meridian
console:

```
invoke create diploma-1031-meridian credential 4 "Ada Lovelace" 2024 "Mathematics" "Bachelor of Science"
```

It succeeds (`committed with status (VALID)` at the four consortium peers,
`"IssuerMSP":"Org5MSP"`). Membership lets Meridian read and propose. Only the
four schools can endorse, and the chaincode stamps Meridian's own name on
whatever it proposes. The "read-only" label in the console means "never
endorses", not "cannot propose".

**Who can change the rules.** Every policy on the Governance page is listed
"via `Admins`": that is its `mod_policy`, the rule for changing it. For the application policies, including `Endorsement`,
that means a majority of the member organizations' admins must sign a
configuration update (`MAJORITY Admins` in the same file). Meridian cannot
endorse a diploma, but it counts toward that majority. Each change is itself a
block: the Governance page's config history lists the `CONFIG` blocks that
built the channel.

### Close (6 minutes)

Ask the slide's three questions aloud and take answers before you show the
ones below.

### Answers to the slide's three questions

Confidence words follow the course's scale (`docs/build-spec.md`, "Confidence
scale").

1. **Who signed it?** Cascadia State (Org1MSP) issued `diploma-1031-honest`.
   Chesapeake Canoe (Org2MSP) tried to issue the same diploma in Cascadia's
   name and was refused, so no forged record exists. *High confidence:* two
   kinds of evidence agree. The chaincode read the signer from the certificate
   (the refusal names the real signer and the claimed one, and `IssuerMSP` on
   the honest record was set the same way, not typed), and the four consortium
   peers independently validated and committed the honest diploma.
2. **Who decides?** The four consortium schools: any three of Org1 to Org4
   must endorse a write. With two of them down, even an honest write did not
   go through. *High confidence:* the policy text in the channel configuration
   names them, and the outage behaved as that policy predicts.
3. **Who can see it?** Every channel member, including Meridian, which endorses
   nothing: its `query all` returned the whole ledger. *High confidence:* we
   watched it, and the channel configuration gives Meridian a `Readers` policy
   (`configtx-4org-students.yaml`, `Org5`) while leaving it out of
   `Endorsement`. That an organization outside the member list sees nothing is
   *moderate confidence* from this demo alone: we read it from the member list
   and Fabric's design but did not show an outsider being turned away.
   **Who can change the rules?** A majority of the member organizations'
   admins, through a configuration update that is itself recorded as a block.

## The student lab (about 90 minutes, not on the current day map)

The full lab gives each student a lane: their own organization, peer, MSP
identity and console on one shared ledger (channel `diplomas`), endorsed by
the four consortium peers. Its chapters, and the exercise ids in the lesson
UI, are:

- Chapter 0, orientation (`orientation`, `meet-the-players`).
- Chapter 1, issue and verify a diploma (`issue-diploma`, `verify-diploma`).
- Chapter 2, how the transaction worked (`anatomy-of-a-block`,
  `endorsement-lifecycle`).
- Chapter 3, faults: peer outage, orderer outage (`peer-outage`,
  `orderer-outage`).
- Chapter 4, who controls the network (`what-is-msp`, `endorsement-policy`,
  `forge-a-diploma`, `governance`).
- Chapter 5, trade finance (`trade-finance-consortium`); Chapter 6, the
  Westview used-car exchange (`westview-*`).

Each exercise card carries its own instructor actions and expected
observations (`web_service/hlf_service.py`), and the notes below cover the
classroom side. Deploy with one lane per student (`--hlf-student-capacity N`)
and post the claim URL `/labs/hlf/claim`.

### Per-chapter instructor notes

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
the lane grid to _not_ change color — student peers are still up. The
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

### Guided Teaching Prompts panel

Bottom of the instructor console. Pulls live exercise state for the
current class, including per-exercise "live checks" (e.g. "did anyone
issue a diploma yet?"). Good for glancing at progress without
interrupting students.

### Operational reminders

- **Per-lane Reset** wipes one student's peer. Shared ledger is fine.
- **Reset Network** wipes everything. Use between classes, not during.
- **Pause sweeper** during exams so idle students don't get auto-released.
- **Release** on a claim hands the lane back to the pool per the current
  policy (`sticky` = keep peer state; `wipe` = reset back to clean).

### Pre-class checklist

- [ ] Host has ≥16 GB RAM free for 20 students + consortium
- [ ] Shared router up (`docker compose -f router ps`)
- [ ] HLF lab up (`./lab-manager.sh status hlf`)
- [ ] Instructor credentials set and tested (yellow banner gone)
- [ ] Network started from instructor console
- [ ] Pool size set appropriately
- [ ] Claim URL posted for the class
- [ ] Seeded baseline transactions if you want a non-empty opening ledger

### Post-class checklist

- [ ] Release any idle claims (or let sweeper do it)
- [ ] **Reset Network** if you want a clean slate for the next class
- [ ] Rotate `INSTRUCTOR_AUTH_KEY` if policy dictates
- [ ] `docker system prune -f` if disk is getting tight

### Debug logging

All backend + lab-manager tracing is off by default to reduce noise.
Enable by setting `HLF_DEBUG=1` in the `hlf-runner` environment and
restarting the service. Logs land at:

- Host: `runtime/debug.log`
- In-container debug sink: `/fabric-samples/test-network/runtime-debug.log`

Use it when tracking:

- Chaincode deploy failures (`ENDORSEMENT_POLICY_FAILURE` at commit)
- Intermittent invoke/query failures
- Network health mismatches across the classroom

### Further reading

- [CLASSROOM_OPERATIONS.md](CLASSROOM_OPERATIONS.md) — runbook
- [STUDENT_GUIDE.md](STUDENT_GUIDE.md) — what students see
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — common issues
- [../../hlf-phase7-classroom-plan.md](../../../hlf-phase7-classroom-plan.md) — multi-tenant design
