# Archived dynamic labs

Docker labs taken out of what students receive at steps 7 and 9 of the lab plan (11 Nov 2026), and after it, kept here
so they can be looked at or restored. Nothing was deleted. The owner's decisions are in `docs/analysis/2026-11-lab-plan.md`
("Decided so far" and "Stage 1"); what each step moved is recorded near the end of that file ("Step 7: archived", "Step 9: Chain Graph review", "Cryptography Lab archived").

Students receive only `blockchain-course/` and `dynamic-labs/` (CLAUDE.md rule 1), so nothing in this folder
reaches the site, the `src.zip`, the student VM or the student images.

Every file keeps its old path under `archive/`: `dynamic-labs/p2p_trust/` is now
`archive/dynamic-labs/p2p_trust/`, and the lab's lane-service module, router route and tests sit at the same
relative paths below this folder.

## The labs

| Lab | What moved here | Why it was archived | What replaces it |
| --- | --- | --- | --- |
| P2P Trust (`p2p_trust`) | the lab; `lane-service/labs/p2p_trust*.py` and `p2p_trust_catalog.yaml`; `router/routes/p2p_trust.conf`; its automated and agent tests | Owner, 10 Nov: archive | No lab: the owner archived it outright |
| Ethereum Lab (`ethereum_lab`) | the lab; `lane-service/labs/ethereum*.py`; `router/routes/ethereum.conf`; its automated and agent tests; `dynamic-labs/tests/test_ethereum_lab_docker_context.py` | Owner, 10 Nov: archive all but its DeFi-risk contracts | Day 8's exploit part, "Name the money and the flaw" (`dynamic-labs/cross-chain/exploit/`), which holds its own copies of those contracts |
| Bitcoin Forensics 1 to 3 (labs 3-5 of the bitcoin lab) | `bitcoin-forensics/` (the class chain, its seeder and answer keys); `bitcoin/forensics-*.md` and `docs/plans/forensics-v2-curriculum-draft.md` (design notes); the labs' intro, chapters and exercises with their solutions, cut from `lane-service/labs/bitcoin_catalog.yaml` into `lane-service/labs/bitcoin_forensics_catalog.yaml` | Lab plan, Stage 1: archive | Day 6's decoy cases (`docs/lab-cards/bitcoin-trace-decoys.md`, built in 75f9584) |
| Chain Graph (`bitcoin-graph`, an instructor-switched tool in the bitcoin lab) | `bitcoin-graph/` (its Neo4j loader, web app, design notes and smoke test) | Owner, 11 Nov: archive, after the step 9 review found no lesson or card uses it | Days 6 and 7's traces in the mempool explorer (`docs/lab-cards/bitcoin-trace-decoys.md`, `docs/lab-cards/hide-and-trace.md`) |
| Cryptography Lab (`cryptography`) | the lab (with `solution.md`, its instructor guide); `lane-service/labs/cryptography*.py` and `lane-service/cryptography_admin.html`; `router/routes/cryptography.conf`; its automated and agent tests | Owner, 11 Nov: archive, once `merkle-trees` had its proof step | Prove it is in the block (`blockchain-course/assets/labs/merkle-trees/`, ceb5088c) for the Merkle proof; its weak-hash collision and weak-seed parts have no lab |

## What changed where they were wired in

- `lab-manager.sh`: the two labs' targets, networks and `--p2p-trust-student-capacity` /
  `--ethereum-student-capacity` options are gone (the generated regions come from `tools/lab_manifest.py`).
- The lane service no longer registers either lab; the router no longer includes their routes or joins their
  networks; the instructor login page no longer links them.
- `tools/lab_tests.py` no longer runs their tests; `.github/dependabot.yml` no longer watches the Ethereum Lab's
  npm folders; `dynamic-labs/student-exclude.txt` and `tools/check.py` no longer list their files.
- The student VM installs heimdall-rs straight from its upstream release (the same checksum-verified binary)
  instead of copying it out of the Ethereum Lab's image.
- GitHub's dependency graph still reads the archived Ethereum Lab's lockfile, so its `package.json` pins
  `tmp` at 0.2.7 and `minimatch` at 11.0.1 or later through `overrides` (Dependabot alerts 275 and 194).

- Bitcoin Forensics: the lane service drops its deploy, local-load, solution and show-solutions routes and the
  per-part solution toggles; the instructor console drops the deploy button, the three solution buttons and the
  solution-key panel; the router drops `/api/bitcoin/forensics/deploy`; the bitcoin lab's launcher button "Load the
  forensics chain" is gone. The launcher image (`lane-service/Dockerfile.launcher`) no longer bakes the chain, so
  `launcher_bake.py` only strips solutions. `vm-build.yml` checks out without Git LFS (the chain was the only LFS
  data under `dynamic-labs/`), `.gitattributes` drops its forensics line, and `student-exclude.txt`,
  `tools/check.py` and `tools/lab_tests.py` no longer list its files. The lab reset (nuke) stays.
- Chain Graph: the bitcoin lab's compose files drop the `graph` service, so the lab reset (nuke) no longer
  removes or restarts `bitcoin-graph-1`; the lane service drops the student panel's Graph button and the
  instructor-only rebuild and enable routes; the instructor console drops the Graph Tool and Rebuild Graph
  buttons; the router drops `/labs/bitcoin/graph/`. The student release no longer builds or records
  `base-bitcoin-graph` (`student-release.yml`, `tools/student_release.py`, `bitcoin/lab.yaml` and the
  generated `student-release-images.json`), and `tools/lab_tests.py` no longer lists it as untested.

- Cryptography Lab: `lab-manager.sh` drops its target and its two networks (`crypto-student-net`,
  `crypto-instructor-net`); the lane service no longer registers it, mounts `../cryptography` or copies its admin
  page; the router no longer includes its route or joins its networks; the instructor login page and the course
  site's link list no longer link it. The student release no longer builds `CRYPTOGRAPHY_STUDENT_IMAGE` (the
  generated `student-release-images.json` and its test stub), the VM no longer bundles its image, and
  `student-exclude.txt`, `tools/check.py` (`VM_RUNTIME_KEYS` and the instructor-container files),
  `tools/lab_tests.py`, `tools/lab_manifest.py` and the regression scripts no longer list it.

## To restore one

Move its folders back with `git mv` (each to the path without the leading `archive/`), then revert the wiring
changes for that lab in its step's commit (`git log -- archive/dynamic-labs/<lab>` finds it) and run
`python tools/lab_manifest.py --write`.
