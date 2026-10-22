# Classroom Operations Runbook

End-to-end guide for running the HLF lab as a live classroom. Covers
provisioning, roster distribution, live ops, resets, and troubleshooting.

If you only need a 30-second version, read the **How to Run a Class**
panel at the bottom of `/labs/hlf/hlf_instructor.html` — this doc is the
long form.

---

## 1. One-time provisioning

The VM / host needs to have the managed lab image built and the shared
router up. From `dynamic-labs/`:

```bash
./lab-manager.sh deploy --mode student --no-tls
./lab-manager.sh start hlf
```

That boots:

- the shared outer nginx router
- the HLF frontend (`hlf`)
- the HLF control plane (`hlf-runner`)
- the orderer + 4 consortium peers (Cascadia State, Chesapeake Canoe University,
  South Hudson, Maple Leaf) + Meridian (Org5, read-only), each with
  built-in ttyd (via `hlf-peer-ttyd` / `hlf-orderer-ttyd` images)
- the channel `diplomas` + committed chaincode

No student peers are running yet. They come up on demand.

### Instructor credentials

There is no default login. `./lab-manager.sh deploy` generates a username
and password for this deployment the first time it runs and keeps them in
`dynamic-labs/.runtime/instructor-credentials.txt` (readable by its owner
only, git-ignored, and left out of the student download). Read them with:

```bash
cat dynamic-labs/.runtime/instructor-credentials.txt
```

To choose your own, set `INSTRUCTOR_AUTH_USER` and `INSTRUCTOR_AUTH_KEY` in
`dynamic-labs/.runtime/runtime-secrets.env`. To get fresh generated ones,
redeploy with `ROTATE_RUNTIME_CREDENTIALS=1`. If neither is set, the auth
service refuses to start. `HLF_INSTRUCTOR_USER` and `HLF_INSTRUCTOR_KEY` still
work as compatibility fallbacks, but should not be used in new deployments.

### Capacity

Default is 20 lanes (`HLF_STUDENT_COUNT=20`). The configured platform
limit is 40 lanes for larger hosts. Each active student peer costs
~300–400 MB RAM; a full class of 20 on top of the shared 4 consortium
peers fits in ~16 GB, while 40 lanes should be reserved for hosts with
substantially more memory and CPU headroom.

---

## 2. Before class

Open the instructor console:

1. `/instructor/` → log in → **HLF — Instructor Console**.
2. **Start Network** at the top. Wait until "status: running" is green
   and the Node Overview shows the orderer + 4 consortium peers.
3. (Optional) **Seed Sample Transactions** if you want learners to see a
   ledger that isn't empty from block 1 — e.g. two sample diplomas and a
   transfer. Good for opening-act demos, not required.
4. In the **Classroom (Lanes & Claims)** panel, set:
   - **Pool Size** = ~20% of expected class size (4 for 20 students; 8
     for 40). Sets how many peers sit pre-warmed so the first wave of
     students gets a hot peer with zero boot wait. More peers warm = more
     RAM, so don't over-set.
   - **Policy** — `wipe` if students should start with a clean peer state
     on reuse; `sticky` if their peer state should survive reconnects.
     For the very first session of a new class, `wipe` is the safer
     default.
   - **Sweeper** should be `active`. Idle timeout defaults to 20 min
     (`HLF_LANE_IDLE_TIMEOUT=1200`).

### Distribute the claim URL

Give the class exactly one URL:

```
http://<your-host>:<port>/labs/hlf/claim
```

Every student hits that once. The claim manager assigns the lowest free
lane (`s01`, `s02`, …), mints a UUID, sets an `hlf_session` cookie, and
redirects them to `/labs/hlf/c/<uuid>/`. If they reopen the same URL
from the same browser, they resume their lane. Different browser /
incognito = new claim.

---

## 3. During class

The lane grid is the single-glance situational awareness surface.

### Colour key

| Color | Meaning |
| --- | --- |
| Green | Peer is running, healthy |
| Amber | Peer is `starting` or `stopping` (transient state — wait) |
| Red | Peer is in `error` — check `last_message` in the cell |
| Grey | `stopped` — lane is idle or not yet claimed |

Each cell shows:

- Lane id (`s01`, `s02`, …)
- Status and the time since last activity
- The claim's UUID prefix (or `unclaimed`)
- Buttons: **Start**, **Stop**, **Reset**, and **Release** when claimed

Each running lane is a peer that the claimed student's org uses as a
**channel member** — full ledger mirror, can query and propose — not as
an endorser. Endorsement stays with the four consortium peers regardless
of how many lanes are green. A green grid tells you all configured students can
read and transact; it does not change who gets to sign writes.

### Common live actions

**Nudge a stuck student.** Ask them to reload first. If that doesn't
help, hit **Reset** on their lane. That wipes _their_ peer + volume and
restarts it — their local state is lost but the shared ledger is
untouched. The peer will resync from the orderer in ~10–30s.

**Release a walked-away student.** Hit **Release** on their claim. In
`wipe` policy the peer is reset back to pool-clean; in `sticky` it's
returned to the pool with state intact for the next claim on that lane.

**Demo a fault.** In the Scenario Controls panel (above the classroom
grid):

- Peer outages (Cascadia / Chesapeake Canoe / South Hudson / Maple Leaf) — Stop
  one consortium peer. With 3-of-4 MAJORITY endorsement, the lab keeps
  writing — good for the "availability vs. integrity" moment.
- Orderer outage — Stop the orderer. Reads keep working, new commits
  stall. Good for the "ordering is the write path's bottleneck" moment.
- Endorsement policy demo — Stops two consortium peers to drop below
  quorum, triggers an attempted write, captures the
  `ENDORSEMENT_POLICY_FAILURE`.

Scenario cards only render for peers that are actually live in the
current topology — if a peer's container isn't present you won't see its
card.

**Pause the sweeper during an exam.** Click **Pause/Resume Sweeper**.
No student gets auto-released for going quiet. Remember to flip it back
on afterward, or idle students will pile up.

**Adjust the pool size.** If students are piling up faster than the pool
is refilling (amber cells), bump the pool size. If RAM's getting tight
and you have lots of unused hot peers, drop it.

---

## 4. End of class

1. If you set policy to `sticky` during class, switch back to `wipe`.
2. Let the sweeper clear idle claims, or click **Release** on each
   claimed lane manually.
3. For a hard between-class reset, click **Reset Network** at the top.
   That tears down every container, including the shared consortium,
   regenerates crypto material and the genesis block, and redeploys the
   chaincode. Fresh classroom ready. Takes ~2 minutes.

The per-lane **Reset** is for one student. The top-level **Reset
Network** is for the whole lab.

---

## 5. Troubleshooting

### A lane stays `error`

Check the `last_message` on the lane cell — it's the tail line from
`docker compose up` for that peer. Most common causes:

- Port conflict (another ttyd is already on the lane's port) — stop the
  lane, then start again.
- Volume from a previous run is in a weird state — **Reset** the lane
  and retry.
- Missing crypto material — this means the lab bootstrap was incomplete.
  Try **Reset Network** at the top to regenerate from genesis.

### A lane stays `starting` for > 60s

The peer is probably replaying the channel ledger from gossip. It's slow
on first boot for lanes that were reset, because they need to catch up
from block 0. Give it another minute. If it never transitions, check
`docker logs peer0.studentNN.example.com` and **Reset** if you see
certificate or gossip errors.

### Students see each other's transactions

That's working as intended — there's one shared ledger. If they see
_stale_ state relative to what their classmates just committed, their
peer is lagging in block replay. Explorer will show their `world state`
catching up over the next few seconds.

### Students can't see anything in the explorer

Check:

- Is the shared network running? (Node Overview up top.)
- Is their lane `running`?
- If the student's peer was recently reset, the world state is temporarily
  empty while it replays blocks. It'll catch up.

### The instructor auth service won't start

It has no built-in password and stops if `INSTRUCTOR_AUTH_KEY` is empty.
Run `./lab-manager.sh deploy` (it generates the value into
`dynamic-labs/.runtime/runtime-secrets.env`), or set `INSTRUCTOR_AUTH_USER`
and `INSTRUCTOR_AUTH_KEY` there yourself, then restart the auth service.
Do not start it with a bare `docker compose` that skips that file.

```bash
docker compose -f dynamic-labs/instructor_auth_service/docker-compose.yml restart instructor-auth-service
```

### The whole instructor console is gone / you're staring at a login loop

Check the nginx `auth_request` wiring at
`dynamic-labs/router/routes/hlf.conf` and
`dynamic-labs/router/routes.conf`. The instructor cookie (`hlf_instructor`)
is path-scoped to `/`, so it must be visible at both `/instructor/…` and
`/labs/hlf/…`. If it only works at one place, check the cookie path in
the Flask login handler.

### Lab won't start at all

Run `docker compose -f dynamic-labs/hlf/docker-compose.yml ps` — anything
unhealthy? Also `docker network ls | grep router-net` — the outer router
must be up first.

Full diagnostics:

```bash
docker logs orderer.example.com --tail 100
docker logs peer0.cascadiastate.example.com --tail 100
docker logs hlf-hlf-runner-1 --tail 100
```

---

## 6. Between classes

Default decision: the ledger does **not** persist across classes. Each
new class starts from a fresh genesis. That's what **Reset Network**
gets you. If a future class wants to reuse a ledger, skip the reset —
the consortium + chaincode will come back up against the existing
persistent volumes.

Worth doing between classes whether or not you reset:

- Rotate `INSTRUCTOR_AUTH_KEY` if your threat model calls for it.
- Review `runtime/lanes.json` — it shouldn't have stale claims after a
  reset, but it's a good sanity check.
- Prune unused docker resources if you've been iterating:
  ```bash
  docker system prune -f
  ```
