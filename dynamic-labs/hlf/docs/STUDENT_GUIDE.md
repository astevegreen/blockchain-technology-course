---
title: "Hyperledger Fabric Lab — Permissioned Ledger Trust (Student Guide)"
format:
  html:
    theme: cosmo
    css: custom.css
    toc: true
    toc-depth: 3
    number-sections: false
---

This lab gives you a **hands-on Hyperledger Fabric environment** where you
will issue a real credential on a live blockchain, verify a classmate's
credential as though you were a prospective employer, and then learn —
piece by piece — how every component of the network made that possible.

You are not alone in this lab. Your whole class is on **one shared
ledger**. You have your own organization and your own peer, but every
transaction you commit is visible to every other student, and theirs to
you. That multi-party, multi-organization reality is the whole point of a
permissioned blockchain — and the lab is built so you experience it
directly instead of reading about it.

## Your Lane

Before you can do anything, you need a lane. A lane is your private
slice of the classroom: your own peer, your own admin identity, your own
shell.

1. Open the URL your instructor posted — it will look like
   `/labs/hlf/claim`.
2. The claim manager assigns you the lowest free student id (e.g.
   `s07`), mints a session cookie, and redirects you to your lesson
   home.
3. Keep that tab open. If you lose it, reopening the claim URL from the
   same browser resumes your lane. Opening it from a different browser
   or incognito window will create a *new* claim, so stick with one
   browser for the session.

Your student id (`s01`, `s02`, …) is also your org. When you issue a
diploma it is signed by **your** org's peer, not by the university next
to you.

## Where Everything Lives

The lab is served under `/labs/hlf/`. The main routes you'll use:

| Route | What it is |
| --- | --- |
| `/labs/hlf/claim` | **Claim a station** — do this once at the start. |
| `/labs/hlf/c/<uuid>/` | **Your lesson home** — chapter navigation, current exercise, progress. This is your main workspace. |
| `/labs/hlf/s/<sid>/` | **Your peer surface** — the explorer, your console, your per-student views, all scoped to your lane. |
| `/labs/hlf/explorer/` | **Shared explorer** — blocks, transactions, world state, node health, chaincode. Shows the ledger everyone is writing to. |
| `/labs/hlf/explorer/governance/` | **Governance drilldown** — policies, MSP identities, who controls the channel. |

The lab runs locally in your VM or cloud deployment. Once staged, it
does not depend on external CDNs or internet access.

---

## How to Use This Lab

### The lesson page is your home base

Keep your `/labs/hlf/c/<uuid>/` tab open throughout the lab. It shows:

- **The current exercise** — what to do, what question to answer, and
  what to look for.
- **A progress bar** — where you are in the overall lesson.
- **Previous / Next controls** — move between exercises at your own pace.
- **A sidebar table of contents** — click "Lesson Nav" to see all
  chapters and exercises, or jump to any step.

### The explorer is a shared window

The explorer shows the shared ledger. Blocks, transactions, and world
state are **global** — everyone in class writes to the same chain, and
everyone sees every write. When your classmate issues a diploma, it
shows up in your explorer within a few seconds.

That is working as intended. Seeing everyone's transactions is how you
understand that this is one shared source of truth, not 20 private
databases.

### Your console is your org

Your console is a real shell inside your peer. You are logged in as
**your org's admin**. You can issue transactions, query the ledger, and
inspect files — but only as yourself. You cannot impersonate another
student's org, and they cannot impersonate yours. That is MSP doing its
job.

Your org is a **channel member** — you hold a full copy of the ledger
and can read and propose any transaction — but you are **not** named in
the channel's endorsement policy. Writes you submit are endorsed by the
four consortium orgs (Cascadia State, Chesapeake Canoe University, South
Hudson, Maple Leaf), not by your peer. In other words: your console
lets you write, but the consortium gets to decide whether your write is
valid. Meridian Industries (Org5) sits in exactly the same posture — a
channel member with a ledger mirror, excluded from endorsement.

Helper commands available inside the console:

| Command | What it does |
| --- | --- |
| `hlf-help` | Show available helper commands. |
| `hlf-peerenv` | Display peer environment variables and identity context. |
| `hlf-files` | List key directories: MSP, TLS, ledger storage. |

### The CLI commands

Chaincode operations run from your console. The `invoke` and `query`
helpers wrap the Fabric `peer` CLI and fill in your org's identity and
endorsement targets for you:

| Command | Description |
| --- | --- |
| `invoke init-ledger` | Load starter records (instructor usually does this). |
| `invoke create <id> <type> <level> <owner> <value> [fieldOfStudy] [degreeType]` | Create a new asset. For diplomas: `type=credential`, `level` is the degree level (2=bachelor, 4=master), `value` is the graduation year. Last two args fill field of study / degree type. |
| `invoke transfer <id> <newOwner>` | Transfer ownership of an asset (e.g. hand a diploma to an employer or a shipment to an importer). |
| `invoke update <id> <type> <level> <owner> <value> [fieldOfStudy] [degreeType]` | Replace an asset's fields. |
| `invoke delete <id>` | Remove an asset from current state. |
| `query all` | List all assets on the shared ledger — yours, classmates', everyone's. |
| `query <id>` | Read one asset by ID. |
| `peer channel getinfo -c diplomas` | Show channel height and latest block info. |

---

## Learning Goals (60-90 min)

By the end of this lab, you will be able to:

- **Issue and verify a credential** on a live permissioned blockchain
- Explain how **permissioned** blockchains differ from public ones
  (Bitcoin, Ethereum)
- Describe what a **block** is and how transactions move through the
  **endorsement lifecycle** (propose, endorse, order, validate, commit)
- Explain the role of **peers**, **orderer**, **MSP**, **endorsement
  policies**, **channels**, and **chaincode**
- Distinguish between **availability**, **integrity**, and **governance**
  failures
- Explain why known institutions still need a shared ledger for
  coordination, even when they know each other

---

## What is Hyperledger Fabric?

[Hyperledger Fabric](https://hyperledger-fabric.readthedocs.io/en/latest/)
is an open-source **permissioned** distributed ledger platform. Unlike
public blockchains (Bitcoin, Ethereum), Fabric networks restrict
participation to **known, identified organizations**. That enables
higher throughput, lower latency, and privacy without proof-of-work
mining.

Fabric uses **chaincode** (smart contracts) to define how participants
read and update shared state. Transactions follow a structured
lifecycle: **proposed, endorsed, ordered, validated, committed**. Every
change is auditable and requires agreement from the right organizations.

For more background, see the Fabric docs on [permissioned vs
permissionless blockchains](https://hyperledger-fabric.readthedocs.io/en/latest/whatis.html#permissioned-vs-permissionless-blockchains).

---

## Lesson Narrative

The lesson is organized into chapters. Work through them in order.

### Chapter 0: Orientation

Claim your lane, get the feel of the lesson UI, and understand the
landscape: who you are, who your classmates are, and which parts of the
network are shared vs private.

- **Your org / your peer** — your own slice of the network, named after
  your student id (e.g. `s07` → `peer0.student07.example.com`).
- **The consortium** — four named orgs (Cascadia State, Chesapeake Canoe
  University, South Hudson, Maple Leaf) run by the classroom. They are
  the always-on peers that make the endorsement policy work.
- **The orderer** — the service that sequences transactions into
  blocks. One orderer, shared by everyone.

### Chapter 1: Issue and Verify a Diploma

You issue a diploma on the shared ledger from your own peer. Then you
pair with a classmate: they issue one too, and you verify *their*
diploma from your explorer — as a prospective employer would check a
candidate's claimed credentials.

**What you will run.** From your console:

```bash
invoke create diploma-<yourid>-001 credential 4 "George Washington" 2024 "Computer Science" "Master of Science"
```

Use `<yourid>` (your lane id, like `s07`) so your record is easy to find
among classmates'. The seven positional arguments: asset ID, asset type
(`credential`), degree level (4 = master, 2 = bachelor), owner name,
graduation year, field of study, and degree type. The last two are
optional but make the record self-describing in the explorer.

Then open the explorer and find a classmate's diploma. Click through to
its transaction detail. The endorsing peer's MSP identity is right
there: a diploma issued by student `s12`'s peer has `s12`'s signature on
it. You couldn't have produced that signature from your own peer —
that's the point.

### Chapter 2: How That Transaction Actually Worked

After your diploma is on the ledger, look under the hood. You'll learn
what a block is, how transactions move through the endorsement lifecycle
(propose, endorse, order, validate, commit), and why each step exists.
The explorer block view and the transaction detail screen are the two
main tools here.

### Chapter 3: What Happens When Things Break

Your instructor triggers failures from the scenario panel and you
observe what breaks and what survives.

- **Consortium peer outage** — one of the four named orgs goes down.
  With 3-of-4 MAJORITY endorsement, writes still succeed. Availability
  degraded, integrity intact.
- **Endorsement policy demo** — two consortium peers drop at once.
  Writes fail with `ENDORSEMENT_POLICY_FAILURE`. The rule that "enough
  orgs must agree" is now enforcing itself in front of you.
- **Orderer outage** — the orderer goes down. Reads keep working
  (every peer still has its copy), but new commits stall. Ordering is
  the commit-path bottleneck.

If your own peer is reset during this chapter (or your instructor drops
a specific lane), you'll briefly see your local state go empty while
your peer catches up from the rest of the network. Blocks aren't lost;
they're being replayed.

### Chapter 4: Who Controls the Network

You explore the identity and governance layer:

- **MSP (Membership Service Provider)** — the certificate-based identity
  system that proves which organization each node belongs to. Without a
  valid MSP identity, a node cannot participate at all. Your console
  has *your* org's admin cert, which is why you can sign as yourself and
  not as anyone else.
- **Endorsement policy** — the rule that specifies which organizations
  must approve a transaction before it can be committed. In this lab:
  3-of-4 MAJORITY across the consortium.
- **Governance** — the rules about rules. Who can add a new
  organization? Who can change the endorsement policy? Governance is
  the most powerful layer because it controls everything else.

### Chapter 5: From Credentials to Consortium

After mastering the credential scenario, apply the same infrastructure
to **trade finance** — a scenario where institutions have competing
financial interests but still need a shared, tamper-evident record.
Same ledger, same endorsement mechanics, different trust context.

The same `create` command serves both stories — the diploma narrative
uses the optional field-of-study and degree-type arguments; the shipment
narrative relies only on the first five:

```bash
# Exporter records a shipment
invoke create shipment-<yourid>-001 cargo 10 "<yourid>-Exporter" 50000

# Later, transfer receipt to an importer role
invoke transfer shipment-<yourid>-001 "<yourid>-Importer"
```

Here `type=cargo`, `level` is a handling/priority tier, and `value` is
shipment value in dollars. One contract, two scenarios, same trust
mechanics.

---

## Working Through the Exercises

Each exercise on the lesson page gives you:

1. **A question** — the thing you are trying to answer.
2. **A prediction prompt** — what you should guess before you look.
3. **Your steps** — what to do, and which tools to open.
4. **Why this matters** — the trust concept the exercise is teaching.
5. **Coming next** — what the next exercise will build on.

Use **Previous / Next** or the **Lesson Nav** sidebar to move between
exercises. The progress bar at the top of the lesson card tracks your
position.

### Starting the network

Your instructor controls the network lifecycle. If the lesson page
shows "Network Stopped," wait — your instructor will start it. Once
running, the claim flow and exercises become interactive.

### Tips

- **Read the question first.** Each exercise starts with a question.
  Think about it before opening any tools.
- **Predict before you look.** Making a wrong prediction is more useful
  than skipping the step.
- **Expect to see classmates' data.** The shared ledger is the point.
  If you see records you didn't create, that's not a bug.
- **Use the explorer for inspection, the console for action.** Explorer
  is read-focused and global; console is write-focused and scoped to
  your org.
- **Exercises that mention "the instructor" mean** your instructor will
  trigger a scenario from their panel. You don't need to do anything on
  the instructor surface — just watch what happens in your explorer.

---

## Quick Reference: Key Concepts

| Concept | What it means in this lab |
| --- | --- |
| **Peer** | A node that holds the ledger and endorses transactions. You have one; the consortium has four; your classmates each have their own. |
| **Orderer** | Sequences endorsed transactions into blocks. Does not endorse — it coordinates commit. |
| **Channel** | A shared ledger subnet. This lab uses one channel (`diplomas`) that every student and every consortium peer is on. |
| **Chaincode** | Smart contract code defining how shared state is read and written. |
| **MSP** | Membership Service Provider — the identity framework. Your admin cert proves you are your org; nothing proves you are anyone else. |
| **Endorsement policy** | 3-of-4 MAJORITY across the consortium. Why fake credentials are hard. |
| **World state** | The current key-value state of the ledger (what assets exist right now). |
| **Block** | A batch of ordered, validated transactions appended to the ledger. |

---

## If Something Doesn't Work

- **Lesson shows "Network Stopped."** Your instructor hasn't started
  the network yet, or has reset it. Wait for the status to clear.
- **Your peer shows as `starting` for a while.** First boot replays
  the channel ledger from gossip. Give it up to a minute.
- **Your world state looks empty but classmates have data.** Your peer
  was recently reset and is catching up. Refresh the explorer; state
  will fill in.
- **Your console is unresponsive.** Refresh the lesson page to get a
  fresh ttyd session.
- **You lost your claim.** Reopen `/labs/hlf/claim` in the same browser
  — you should resume the same lane. If you're in a different browser
  or incognito, tell your instructor; they can release and re-issue.

If something else is off, flag your instructor — the instructor console
shows lane health at a glance.

---

## Lab Summary

You issued a diploma from your own peer, verified a classmate's diploma
as an employer would, watched faults ripple through the network, and
applied the same mechanics to trade finance. Here is what each piece
taught you:

- **Peers** — The computers that hold the ledger and endorse
  transactions. Each organization runs its own, which is why no single
  party can rewrite history unilaterally.
- **Orderer** — The coordination service that sequences endorsed
  transactions into blocks. It handles ordering and delivery, not
  content validation.
- **MSP** — The certificate-based identity system. It's why you sign as
  your org and not as anyone else's, and why "permissioned" actually
  means something.
- **Endorsement policy** — The rule that makes mutual oversight
  mechanical. 3-of-4 MAJORITY in this lab. You watched it hold under
  one outage and fail under two.
- **Governance** — The rules about rules. Governance controls who can
  join, who can change policies, and who has admin authority.
- **Blocks** — Sealed, numbered containers of transactions. Once
  committed, transactions cannot be silently removed.
- **Channels** — Shared ledger subnets. Only channel members see and
  write the data.
- **Failure classification** — Different failures damage different trust
  properties. Peer outages affect availability. Orderer outages halt
  commit. Governance compromise is the most dangerous because it can
  change the rules themselves.

### Check your understanding

1. **Diploma issuance** — When you issued your diploma, which peers
   endorsed it, and why was your own peer's signature not sufficient on
   its own?
2. **Verification** — Why does an employer query their own node
   instead of asking the issuing university directly? What trust
   property does this independent verification provide?
3. **Blocks** — Why does the network batch transactions into blocks
   rather than recording each individually? What does the block
   sequence guarantee?
4. **Peer outage** — When a consortium peer goes down, what is lost and
   what is preserved? Is that an integrity failure or an availability
   failure?
5. **Orderer outage** — Why can you still read state but not commit new
   transactions when the orderer is offline? What does this tell you
   about the orderer's role?
6. **MSP** — What stops a rogue computer from joining the network and
   pretending to be a legitimate organization — or pretending to be
   *your* org?
7. **Endorsement policy** — How did 3-of-4 MAJORITY behave when one
   consortium peer went down versus when two went down? Why is that
   gap important?
8. **Governance** — Which is more dangerous: a peer crashing for an
   hour, or an attacker gaining control of an organization's admin
   certificate? Why?
9. **Trade finance** — Why do known institutions with competing
   interests still need a shared ledger instead of bilateral contracts?

---

## References

- [Hyperledger Fabric documentation (main)](https://hyperledger-fabric.readthedocs.io/en/latest/)
- [Permissioned vs permissionless blockchains](https://hyperledger-fabric.readthedocs.io/en/latest/whatis.html#permissioned-vs-permissionless-blockchains)
- [Smart contracts (chaincode)](https://hyperledger-fabric.readthedocs.io/en/latest/whatis.html#smart-contracts)
- [Channels](https://hyperledger-fabric.readthedocs.io/en/latest/channels.html)
- [Chaincode lifecycle](https://hyperledger-fabric.readthedocs.io/en/latest/chaincode_lifecycle.html)
