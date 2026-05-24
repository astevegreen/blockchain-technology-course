# Student Home VM Harness

This harness creates a nested-Docker VM simulator for validating the
host-mounted student-home disk path locally.

Use it when you want to test the privileged deployment behavior without
changing the real host:

- passwordless `sudo`
- sparse image creation
- `mkfs.ext4`
- loopback mounts
- nested `docker compose`
- `lab-manager` behavior inside a VM-like environment

This is for local testing only. It is not part of the normal lab
runtime or CI deployment path.

## Why this harness exists

The student-home disk feature relies on host-level operations. A normal
helper container talking to the host Docker socket does not emulate that
cleanly because the mount namespace is wrong. This harness instead runs
its own Docker daemon inside a privileged container, so the nested
environment behaves more like the real deployment VM.

## What it provides

- a privileged nested-Docker container
- a `student` user with passwordless `sudo`
- the host repo root mounted read-only at `/src`
- an isolated copied working tree at `/workspace`
- inner router ports exposed on host `8080` and `8443` by default
- a reusable command wrapper in `run.sh`
- default student-mode lane count of `5` in this harness so browser/MCP
  checks and manual review can happen in parallel
- shared labs still run as single containers; the harness lane-count
  override only changes claim-based labs

## Quick start

```bash
cd regression-tests/infrastructure/student-home-vm
./run.sh smoke
./run.sh up
./run.sh sync
./run.sh reset-claims --wipe
./run.sh exec 'cd /workspace/dynamic-labs && bash ./lab-manager.sh deploy --mode student'
./run.sh exec 'cd /workspace/dynamic-labs && STUDENT_HOME_DISKS_MODE=auto bash ./lab-manager.sh start consensus'
```

Open the inner router at:

- `http://localhost:8080`
- `https://localhost:8443`

## Useful commands

```bash
./run.sh up
./run.sh sync
./run.sh reset-claims --wipe
./run.sh shell
./run.sh root-shell
./run.sh exec 'cd /workspace/dynamic-labs && bash ./lab-manager.sh status all'
./run.sh exec 'cd /workspace/dynamic-labs && bash ./lab-manager.sh cleanup student-home-disks'
./run.sh down
```

## Notes

- The nested Docker daemon stores its own images and containers in the
  named volume `student-home-vm-docker`.
- The working copy lives in the named volume
  `student-home-vm-workspace`, so tests can write inside
  `/workspace/dynamic-labs` without dirtying the host checkout.
- The host repo is mounted read-only at `/src`. Run `./run.sh sync`
  after host-side edits if you want to refresh the copied tree inside
  the running VM harness.
- Run `./run.sh reset-claims --wipe` before MCP/browser phases on
  claim-limited labs so stale student claims do not exhaust the warm
  pool and turn browser claim checks into misleading `503` failures.
  The command auto-discovers a reachable nested router URL and uses the
  nested environment's instructor credentials.
- If you want different outer ports, set
  `STUDENT_HOME_VM_HTTP_PORT` and `STUDENT_HOME_VM_HTTPS_PORT` before
  running `./run.sh up`.
- If you want a different student lane count in this harness, set
  `STUDENT_HOME_VM_MAX_CAPACITY` before `./run.sh up`. For backward
  compatibility, `STUDENT_HOME_VM_STUDENT_COUNT` is still accepted as an
  alias. This changes claim-based lane capacity only.
- If you want a different HLF warm-pool size in this harness, set
  `STUDENT_HOME_VM_HLF_WARM_POOL_SIZE` before `./run.sh up`.
