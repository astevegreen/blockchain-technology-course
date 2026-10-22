# HLF Reset And Startup

This document describes the optional fresh-start procedure for the HLF
regression suite.

This is not the default entry path. The default case is to run against
the existing live environment without wiping it first.

Goal:

- make the HLF environment feel like a fresh lab boot
- preserve built Docker images
- discard HLF runtime state, claims, generated student material,
  containers, and volumes

Important:

- this is optional and used only when fresh-start coverage is requested
- preserve images
- do not preserve container writable state
- do not preserve named volumes
- do not preserve `hlf/runtime`
- preserve `hlf/managed_runtime`, which contains checked-in bootstrap
  templates and topology files required for startup

## Default Entry Path

The default regression run should not wipe the environment.

If the environment is already live, the normal starting point is:

```bash
./lab-manager.sh start hlf
./lab-manager.sh status hlf
```

Use the fresh-start procedure below only when explicitly requested or
when the current HLF environment is not trustworthy.

## Optional Fresh-Start Reset

Run these steps from the repo root.

### 1. Stop the HLF lab

```bash
./lab-manager.sh stop hlf || true
```

### 2. Tear down the HLF compose project and volumes

```bash
cd hlf
docker compose --env-file ../.runtime/runtime-secrets.env down -v --remove-orphans || true
cd ..
```

The compose file refuses to read without the generated secrets, so the
`--env-file` is needed here; without it the command fails and the `|| true`
hides that nothing was torn down.

### 3. Clear generated HLF runtime state

```bash
rm -rf hlf/runtime/*
```

This preserves the checked-in source tree and built images while wiping
the generated network runtime, claims, progress state, and container
state. Do not delete `hlf/managed_runtime`; it is part of the source
tree for this lab, not disposable runtime state.

## Fresh-Start Startup

### 1. Start the HLF lab again

```bash
./lab-manager.sh start hlf
```

### 2. Confirm expected services are up

```bash
./lab-manager.sh status hlf
```

## Minimum Post-Boot Smoke

Before deeper regression checks, verify these routes respond through the
shared router:

- `/labs/hlf/`
- `/labs/hlf/claim`
- `/labs/hlf/instructor/`
- `/labs/hlf/explorer/`
- `/labs/hlf/peer/org5/`

The automated suite should prefer Python `requests` for these checks.

## Generated Secrets Smoke

The Fabric Certificate Authority admin password and the peers' CouchDB
password are generated, not built in. After a fresh start, on the Docker
host:

- `dynamic-labs/.runtime/runtime-secrets.env` contains both
  `HLF_CA_ADMIN_PASSWORD` and `HLF_COUCHDB_PASSWORD` (check the names only;
  do not print the values).
- Enrollment finished: the test network's `organizations/peerOrganizations`
  and `organizations/ordererOrganizations` folders hold the generated MSP
  material. This proves `registerEnroll.sh` signed in to each Certificate
  Authority with the generated password.
- The peers reached CouchDB: the peer logs show no `401` or authentication
  errors from the state database.
- The upstream default no longer works: enrolling against a Certificate
  Authority with the old built-in admin password is rejected.
- `hlf/lab.sh down` and `hlf/lab.sh watch logs` work even in a shell where
  the two variables are unset.
- Unsetting either variable and running `hlf/lab.sh up` stops at once with a
  message naming the missing variable.
