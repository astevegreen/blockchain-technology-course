# Archived dynamic labs

Docker labs taken out of what students receive at step 7 of the lab plan (11 Nov 2026), kept here so they can be
looked at or restored. Nothing was deleted. The owner's decisions are in `docs/analysis/2026-11-lab-plan.md`
("Decided so far" and "Stage 1"); what this step moved is recorded at the end of that file ("Step 7: archived").

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

## To restore one

Move its folders back with `git mv` (each to the path without the leading `archive/`), then revert the wiring
changes for that lab in the step 7 commit (`git show` the commit that added this README) and run
`python tools/lab_manifest.py --write`.
